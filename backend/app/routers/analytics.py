from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Dict, Any

from app.database import get_db
from app.models import (
    Invoice, ThreatReport, Transaction, Vendor, InvoiceStatus
)
from app.schemas import ThreatAnalytics, FraudGraphResponse, TransactionHistory

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Dashboard"])

@router.get("/threats", response_model=ThreatAnalytics)
async def get_threat_analytics(db: AsyncSession = Depends(get_db)):
    """
    Get comprehensive threat analytics for dashboard
    
    Returns:
    - Total blocked amount (money saved)
    - Total number of threats
    - Threats by type and severity
    - Top risky vendors
    - Recent blocks
    """
    # Get total blocked amount
    result = await db.execute(
        select(func.sum(Invoice.amount)).where(
            Invoice.status == InvoiceStatus.BLOCKED
        )
    )
    total_blocked = result.scalar() or 0.0
    
    # Get total threat count
    result = await db.execute(select(func.count(ThreatReport.id)))
    total_threats = result.scalar() or 0
    
    # Threats by type
    result = await db.execute(
        select(
            ThreatReport.threat_type,
            func.count(ThreatReport.id).label('count')
        ).group_by(ThreatReport.threat_type)
    )
    threats_by_type = {row[0]: row[1] for row in result.all()}
    
    # Threats by severity
    result = await db.execute(
        select(
            ThreatReport.severity,
            func.count(ThreatReport.id).label('count')
        ).group_by(ThreatReport.severity)
    )
    threats_by_severity = {row[0]: row[1] for row in result.all()}
    
    # Top risky vendors (most blocked invoices)
    result = await db.execute(
        select(
            Vendor.id,
            Vendor.name,
            Vendor.risk_score,
            func.count(Invoice.id).label('blocked_count'),
            func.sum(Invoice.amount).label('total_blocked')
        )
        .join(Invoice, Invoice.vendor_id == Vendor.id)
        .where(Invoice.status == InvoiceStatus.BLOCKED)
        .group_by(Vendor.id, Vendor.name, Vendor.risk_score)
        .order_by(desc('blocked_count'))
        .limit(10)
    )
    
    top_risky_vendors = [
        {
            "id": row[0],
            "name": row[1],
            "risk_score": row[2],
            "blocked_count": row[3],
            "total_blocked": float(row[4]) if row[4] else 0.0
        }
        for row in result.all()
    ]
    
    # Recent blocks
    result = await db.execute(
        select(ThreatReport)
        .order_by(desc(ThreatReport.created_at))
        .limit(10)
    )
    recent_blocks = result.scalars().all()
    
    return ThreatAnalytics(
        total_blocked_amount=total_blocked,
        total_threats=total_threats,
        threats_by_type=threats_by_type,
        threats_by_severity=threats_by_severity,
        top_risky_vendors=top_risky_vendors,
        recent_blocks=recent_blocks
    )

@router.get("/fraud-graph", response_model=FraudGraphResponse)
async def get_fraud_graph(db: AsyncSession = Depends(get_db)):
    """
    Get FraudGraph visualization data
    
    Returns nodes (vendors/templates/wallets) with fraud scores
    and edges showing connections between them.
    """
    nodes = []
    edges = []
    
    # Get vendors with fraud scores
    result = await db.execute(
        select(
            Vendor.id,
            Vendor.name,
            Vendor.risk_score,
            func.count(Invoice.id).label('invoice_count')
        )
        .join(Invoice, Invoice.vendor_id == Vendor.id)
        .group_by(Vendor.id, Vendor.name, Vendor.risk_score)
        .having(func.count(Invoice.id) > 0)
    )
    
    vendors = result.all()
    for vendor in vendors:
        nodes.append({
            "id": vendor[0],
            "name": vendor[1],
            "type": "vendor",
            "fraud_score": vendor[2],
            "occurrences": vendor[3],
            "connections": []
        })
    
    # Get template fingerprints with occurrence count
    result = await db.execute(
        select(
            Invoice.template_hash,
            func.count(Invoice.id).label('count'),
            func.avg(Invoice.fraud_score).label('avg_fraud')
        )
        .where(Invoice.template_hash.isnot(None))
        .group_by(Invoice.template_hash)
        .having(func.count(Invoice.id) > 1)  # Only duplicates
    )
    
    templates = result.all()
    template_id_start = 10000
    for idx, template in enumerate(templates):
        nodes.append({
            "id": template_id_start + idx,
            "name": f"Template-{template[0][:8]}",
            "type": "template",
            "fraud_score": float(template[2]) if template[2] else 0.0,
            "occurrences": template[1],
            "connections": []
        })
    
    # Create edges between vendors and templates
    for idx, template in enumerate(templates):
        result = await db.execute(
            select(Invoice.vendor_id)
            .where(Invoice.template_hash == template[0])
            .distinct()
        )
        vendor_ids = [row[0] for row in result.all()]
        
        for vendor_id in vendor_ids:
            edges.append({
                "source": vendor_id,
                "target": template_id_start + idx,
                "type": "uses_template"
            })
    
    return FraudGraphResponse(
        nodes=nodes,
        edges=edges
    )

@router.get("/transactions", response_model=TransactionHistory)
async def get_transaction_history(
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get transaction history with status breakdown
    
    Returns all invoices with their payment status and human-readable reasons.
    """
    query = select(Invoice)
    
    if status:
        query = query.where(Invoice.status == status)
    
    query = query.order_by(desc(Invoice.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    # Get counts
    result = await db.execute(
        select(func.count(Invoice.id)).where(Invoice.status == InvoiceStatus.PAID)
    )
    paid_count = result.scalar() or 0
    
    result = await db.execute(
        select(func.count(Invoice.id)).where(Invoice.status == InvoiceStatus.HELD)
    )
    held_count = result.scalar() or 0
    
    result = await db.execute(
        select(func.count(Invoice.id)).where(Invoice.status == InvoiceStatus.BLOCKED)
    )
    blocked_count = result.scalar() or 0
    
    # Get amounts
    result = await db.execute(
        select(func.sum(Invoice.amount)).where(Invoice.status == InvoiceStatus.PAID)
    )
    total_paid = result.scalar() or 0.0
    
    result = await db.execute(
        select(func.sum(Invoice.amount)).where(Invoice.status == InvoiceStatus.BLOCKED)
    )
    total_blocked = result.scalar() or 0.0
    
    return TransactionHistory(
        invoices=invoices,
        total=len(invoices),
        paid_count=paid_count,
        held_count=held_count,
        blocked_count=blocked_count,
        total_amount_paid=total_paid,
        total_amount_blocked=total_blocked
    )

@router.get("/dashboard-stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Get high-level stats for dashboard overview
    """
    # Invoice counts by status
    result = await db.execute(
        select(
            Invoice.status,
            func.count(Invoice.id).label('count')
        ).group_by(Invoice.status)
    )
    status_counts = {row[0].value: row[1] for row in result.all()}
    
    # Total amounts by status
    result = await db.execute(
        select(
            Invoice.status,
            func.sum(Invoice.amount).label('total')
        ).group_by(Invoice.status)
    )
    status_amounts = {row[0].value: float(row[1]) if row[1] else 0.0 for row in result.all()}
    
    # Average scores
    result = await db.execute(
        select(
            func.avg(Invoice.confidence_score).label('avg_confidence'),
            func.avg(Invoice.fraud_score).label('avg_fraud')
        ).where(Invoice.confidence_score.isnot(None))
    )
    row = result.first()
    avg_confidence = float(row[0]) if row[0] else 0.0
    avg_fraud = float(row[1]) if row[1] else 0.0
    
    return {
        "status_counts": status_counts,
        "status_amounts": status_amounts,
        "average_confidence_score": avg_confidence,
        "average_fraud_score": avg_fraud,
        "total_invoices": sum(status_counts.values()),
        "total_amount": sum(status_amounts.values()),
        "money_saved": status_amounts.get("blocked", 0.0)
    }
