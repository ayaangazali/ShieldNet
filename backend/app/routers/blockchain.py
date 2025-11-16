"""
Blockchain Threat Intelligence Router
API endpoints for decentralized fraud intelligence network
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.blockchain_threat_intel import BlockchainThreatIntelService


router = APIRouter(prefix="/api/blockchain", tags=["Blockchain Threat Intel"])


# Pydantic models
class ThreatReportRequest(BaseModel):
    vendor_identifier: str = Field(..., description="Vendor domain or email")
    wallet_address: Optional[str] = Field(None, description="Payment wallet address")
    invoice_template: Optional[str] = Field(None, description="Invoice template text/HTML")
    amount: float = Field(..., description="Invoice amount")
    currency: str = Field(default="USDC", description="Currency code")
    fraud_score: float = Field(..., ge=0.0, le=1.0, description="Fraud score 0-1")
    reasons: List[str] = Field(..., description="List of fraud reason codes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "vendor_identifier": "scam-vendor.com",
                "wallet_address": "0xabc123...",
                "invoice_template": "<html>...</html>",
                "amount": 15000.00,
                "currency": "USDC",
                "fraud_score": 0.91,
                "reasons": ["NO_PO_MATCH", "HOURS_EXCEED_LOGS", "MATCHES_KNOWN_SCAM_TEMPLATE"]
            }
        }


class ThreatReportResponse(BaseModel):
    success: bool
    threat_id: str
    vendor_hash: str
    transaction_hash: Optional[str] = None
    message: str


class VendorQueryRequest(BaseModel):
    vendor_identifier: str = Field(..., description="Vendor domain or email to check")


class VendorStatusResponse(BaseModel):
    vendor_identifier: str
    vendor_hash: str
    has_threats: bool
    threat_count: int
    max_fraud_score: float
    is_blocked: bool
    threats: List[Dict[str, Any]] = []
    recommendation: str


@router.post("/threat/submit", response_model=ThreatReportResponse)
async def submit_threat_report(request: ThreatReportRequest):
    """
    Submit a fraud/threat report to the blockchain network
    
    This endpoint allows companies to report fraudulent vendors/invoices
    to the decentralized ShieldNet intelligence network on Base blockchain.
    
    The data is hashed before submission to protect privacy while enabling
    pattern matching across the network.
    """
    try:
        service = BlockchainThreatIntelService()
        
        # Create threat report
        threat_report = service.create_threat_report_json(
            vendor_identifier=request.vendor_identifier,
            wallet_address=request.wallet_address,
            invoice_template=request.invoice_template,
            amount=request.amount,
            currency=request.currency,
            fraud_score=request.fraud_score,
            reasons=request.reasons
        )
        
        # Submit to blockchain
        receipt = service.submit_threat_to_blockchain(threat_report)
        
        return ThreatReportResponse(
            success=receipt.get("success", False),
            threat_id=threat_report["threatId"],
            vendor_hash=threat_report["vendorHash"],
            transaction_hash=receipt.get("transactionHash"),
            message=receipt.get("message", "Threat report submitted successfully")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit threat: {str(e)}")


@router.post("/vendor/check", response_model=VendorStatusResponse)
async def check_vendor_threats(request: VendorQueryRequest):
    """
    Check if a vendor has any fraud reports on the blockchain network
    
    Query the decentralized ShieldNet network to see if other companies
    have reported this vendor as fraudulent. This provides the first line
    of defense before processing an invoice.
    """
    try:
        service = BlockchainThreatIntelService()
        
        # Query blockchain
        status = service.check_vendor_status(request.vendor_identifier)
        vendor_hash = service.hash_vendor(request.vendor_identifier)
        
        # Generate recommendation
        if status["isBlocked"]:
            recommendation = "🚫 BLOCK - Vendor has high fraud score. Do not process payment."
        elif status["hasThreats"]:
            recommendation = "⚠️ HOLD - Vendor has fraud reports. Requires manual review."
        else:
            recommendation = "✅ CLEAR - No fraud reports found on network."
        
        return VendorStatusResponse(
            vendor_identifier=request.vendor_identifier,
            vendor_hash=vendor_hash,
            has_threats=status["hasThreats"],
            threat_count=status["threatCount"],
            max_fraud_score=status["maxFraudScore"],
            is_blocked=status["isBlocked"],
            threats=status.get("threats", []),
            recommendation=recommendation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query vendor: {str(e)}")


@router.get("/wallet/check/{wallet_address}")
async def check_wallet_threats(wallet_address: str):
    """
    Check if a wallet address has any fraud reports
    
    Useful for verifying payment destinations before sending USDC.
    """
    try:
        service = BlockchainThreatIntelService()
        
        threats = service.query_wallet_threats(wallet_address)
        wallet_hash = service.hash_wallet(wallet_address)
        
        return {
            "wallet_address": wallet_address[:10] + "...",  # Partial for privacy
            "wallet_hash": wallet_hash,
            "has_threats": len(threats) > 0,
            "threat_count": len(threats),
            "threats": threats,
            "is_safe": len(threats) == 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query wallet: {str(e)}")


@router.get("/network/status")
async def get_network_status():
    """
    Get status of blockchain connection and network statistics
    
    Returns connection info, block number, and network health.
    """
    try:
        service = BlockchainThreatIntelService()
        
        connection_status = service.test_connection()
        
        return {
            "blockchain": "Base Mainnet",
            "provider": "Alchemy",
            "connection": connection_status,
            "contract_address": service.contract_address,
            "company_id": service.company_hash,
            "features": [
                "Submit threat reports",
                "Query vendor threats",
                "Query wallet threats",
                "Check fraud status"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get network status: {str(e)}")


@router.get("/")
async def blockchain_info():
    """Get information about the blockchain threat intelligence system"""
    return {
        "name": "ShieldNet Blockchain Threat Intelligence",
        "description": "Decentralized fraud intelligence network for invoice fraud prevention",
        "blockchain": "Base (Ethereum L2)",
        "provider": "Alchemy",
        "features": {
            "privacy": "All vendor/wallet data is hashed (SHA-256) before storage",
            "decentralized": "Fraud reports stored on-chain, accessible to all network participants",
            "real_time": "Instant queries against global threat database",
            "incentivized": "Future: Companies earn rewards for contributing threat data"
        },
        "endpoints": {
            "submit": "POST /api/blockchain/threat/submit",
            "check_vendor": "POST /api/blockchain/vendor/check",
            "check_wallet": "GET /api/blockchain/wallet/check/{address}",
            "status": "GET /api/blockchain/network/status"
        },
        "smart_contract": {
            "name": "ShieldNetThreatIntel.sol",
            "location": "/backend/contracts/ShieldNetThreatIntel.sol",
            "status": "Ready to deploy",
            "functions": [
                "submitThreatReport",
                "updateThreatReport",
                "queryVendorThreats",
                "queryWalletThreats",
                "checkVendorStatus"
            ]
        }
    }
