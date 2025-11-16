from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Dict, Any
from datetime import datetime
import logging

from app.database import get_db
from app.models import ThreatReport, Invoice, InvoiceStatus
from app.schemas import (
    ThreatReportResponse, ThreatReportCreate, NetworkThreatQuery, NetworkThreatResponse
)
from app.services.fraud_detection import create_fingerprint
from app.config import settings
from app.services.threat_intel_store import ThreatIntelStoreFactory, ThreatFingerprint

logger = logging.getLogger(__name__)

# Initialize threat intelligence store based on configuration
# USE_ONCHAIN_THREATS=false (default): Local SQLite storage
# USE_ONCHAIN_THREATS=true (future): Blockchain storage on Base/L3
threat_store = ThreatIntelStoreFactory.create(use_onchain=settings.USE_ONCHAIN_THREATS)

if settings.USE_ONCHAIN_THREATS:
    logger.info("🔗 Threat Intelligence: ON-CHAIN mode (blockchain integration)")
else:
    logger.info("📊 Threat Intelligence: LOCAL mode (no blockchain required)")
router = APIRouter(prefix="/api/threats", tags=["Threat Intelligence"])

@router.post("/report", response_model=ThreatReportResponse)
async def report_threat(
    threat_data: ThreatReportCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Report a new threat after blocking an invoice
    
    Storage modes:
    - USE_ONCHAIN_THREATS=false (default): Stores threats locally only
    - USE_ONCHAIN_THREATS=true: Stores locally AND submits to Base blockchain
    
    NOTE: Locus is used for USDC payment execution (see treasury.py)
          This endpoint is ONLY for storing fraud threat fingerprints
    """
    # 1. Create threat report (local storage for analytics)
    threat = ThreatReport(
        invoice_id=threat_data.invoice_id,
        threat_type=threat_data.threat_type,
        severity=threat_data.severity,
        vendor_fingerprint=threat_data.vendor_fingerprint,
        wallet_fingerprint=threat_data.wallet_fingerprint,
        template_fingerprint=threat_data.template_fingerprint,
        description=threat_data.description,
        indicators=threat_data.indicators,
        amount_saved=threat_data.amount_saved,
        is_shared=False
    )
    
    db.add(threat)
    await db.commit()
    await db.refresh(threat)
    
    # 2. Save to threat intelligence store (local or blockchain based on config)
    try:
        # Get invoice details for building threat fingerprint
        result = await db.execute(
            select(Invoice).where(Invoice.id == threat_data.invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if invoice:
            # Import hashing utility from local store
            from app.services.local_threat_intel_store import LocalThreatIntelStore
            
            # Build threat fingerprint
            threat_fingerprint = ThreatFingerprint(
                vendor_hash=LocalThreatIntelStore.hash_string(
                    invoice.vendor_id if hasattr(invoice, 'vendor_id') else threat_data.vendor_fingerprint
                ),
                payment_target_hash=LocalThreatIntelStore.hash_string(
                    threat_data.wallet_fingerprint or "0x0"
                ),
                invoice_template_hash=LocalThreatIntelStore.hash_string(
                    threat_data.template_fingerprint or "unknown"
                ),
                amount_bucket=LocalThreatIntelStore.bucket_amount(
                    threat_data.amount_saved or 0.0
                ),
                currency="USD",
                fraud_score=invoice.fraud_score or 75.0,
                reasons=threat_data.indicators or [threat_data.threat_type],
                timestamp=datetime.utcnow(),
                invoice_id=threat_data.invoice_id
            )
            
            # Save using configured threat store (local or onchain)
            threat_id = await threat_store.save_threat(threat_fingerprint, db=db)
            
            if threat_id:
                logger.info(f"✅ Threat {threat.id} saved to threat intel store: {threat_id}")
                threat.is_shared = True  # Mark as shared to threat network
                await db.commit()
            else:
                logger.warning(f"⚠️ Threat {threat.id} not saved to threat store")
            
    except Exception as e:
        logger.error(f"❌ Failed to save to threat intel store: {e}", exc_info=True)
    
    return threat

@router.post("/query", response_model=NetworkThreatResponse)
async def query_threats(
    query: NetworkThreatQuery,
    db: AsyncSession = Depends(get_db)
):
    """
    Query ShieldNet threat database
    
    Check if vendor, wallet, or template has been flagged before.
    This is the core of the network fraud check.
    """
    threats = []
    threat_count = 0
    
    # Build query based on provided criteria
    conditions = []
    
    if query.vendor_fingerprint:
        result = await db.execute(
            select(ThreatReport).where(
                ThreatReport.vendor_fingerprint == query.vendor_fingerprint
            )
        )
        vendor_threats = result.scalars().all()
        threats.extend(vendor_threats)
        threat_count += len(vendor_threats)
    
    if query.wallet_address:
        result = await db.execute(
            select(ThreatReport).where(
                ThreatReport.wallet_fingerprint == query.wallet_address
            )
        )
        wallet_threats = result.scalars().all()
        threats.extend(wallet_threats)
        threat_count += len(wallet_threats)
    
    if query.template_hash:
        result = await db.execute(
            select(ThreatReport).where(
                ThreatReport.template_fingerprint == query.template_hash
            )
        )
        template_threats = result.scalars().all()
        threats.extend(template_threats)
        threat_count += len(template_threats)
    
    # Determine risk level
    risk_level = "low"
    if threat_count > 5:
        risk_level = "critical"
    elif threat_count > 2:
        risk_level = "high"
    elif threat_count > 0:
        risk_level = "medium"
    
    return NetworkThreatResponse(
        is_threat=threat_count > 0,
        threat_count=threat_count,
        threat_details=[
            {
                "id": t.id,
                "type": t.threat_type,
                "severity": t.severity,
                "description": t.description,
                "amount_saved": t.amount_saved,
                "created_at": t.created_at.isoformat()
            }
            for t in threats[:10]  # Limit to 10 most recent
        ],
        risk_level=risk_level
    )

@router.post("/{threat_id}/share")
async def share_threat(
    threat_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Share threat with ShieldNet network
    
    Anonymizes and shares threat data so other companies can benefit.
    First detector may earn micro-rewards when others use this intel.
    """
    result = await db.execute(
        select(ThreatReport).where(ThreatReport.id == threat_id)
    )
    threat = result.scalar_one_or_none()
    
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")
    
    if threat.is_shared:
        return {"message": "Threat already shared"}
    
    # Create anonymized data for network sharing
    anonymized_data = {
        "threat_type": threat.threat_type,
        "severity": threat.severity,
        "vendor_fingerprint": threat.vendor_fingerprint,
        "wallet_fingerprint": threat.wallet_fingerprint,
        "template_fingerprint": threat.template_fingerprint,
        "indicators": threat.indicators,
        "timestamp": threat.created_at.isoformat()
    }
    
    threat.is_shared = True
    threat.anonymized_data = anonymized_data
    
    await db.commit()
    
    # In production, would send to ShieldNet API
    # await send_to_shieldnet_network(anonymized_data)
    
    return {
        "message": "Threat shared successfully",
        "threat_id": threat_id,
        "anonymized": True
    }

@router.get("/list", response_model=List[ThreatReportResponse])
async def list_threats(
    severity: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all threat reports"""
    query = select(ThreatReport)
    
    if severity:
        query = query.where(ThreatReport.severity == severity)
    
    query = query.offset(skip).limit(limit).order_by(desc(ThreatReport.created_at))
    
    result = await db.execute(query)
    threats = result.scalars().all()
    
    return threats

@router.get("/fingerprint/vendor/{vendor_name}")
async def get_vendor_fingerprint(vendor_name: str):
    """Generate vendor fingerprint for fraud detection"""
    return {
        "vendor_name": vendor_name,
        "fingerprint": create_fingerprint(vendor_name)
    }

@router.get("/fingerprint/wallet/{wallet_address}")
async def get_wallet_fingerprint(wallet_address: str):
    """Generate wallet fingerprint for fraud detection"""
    return {
        "wallet_address": wallet_address,
        "fingerprint": create_fingerprint(wallet_address)
    }

@router.get("/analytics")
async def get_threat_analytics(db: AsyncSession = Depends(get_db)):
    """
    Get threat analytics for dashboard
    
    Returns aggregated threat statistics from threat intelligence store.
    Works with both local (default) and on-chain storage.
    """
    try:
        analytics = await threat_store.get_analytics(db=db)
        analytics['blockchain_enabled'] = settings.USE_ONCHAIN_THREATS
        return analytics
    except Exception as e:
        logger.error(f"Failed to get threat analytics: {e}", exc_info=True)
        return {
            'total_threats': 0,
            'total_blocked_amount': 0.0,
            'blocked_count': 0,
            'severity_breakdown': {},
            'recent_threats_7d': 0,
            'storage_type': 'local' if not settings.USE_ONCHAIN_THREATS else 'onchain',
            'blockchain_enabled': settings.USE_ONCHAIN_THREATS,
            'error': str(e)
        }
