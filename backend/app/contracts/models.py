"""
Contract Models - Pydantic schemas for Smart Contract data structures

This module defines the data models used by the JSON-based smart contract system.
All models are Pydantic BaseModel classes for validation and serialization.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator


# ============================================================================
# POLICY CONTRACT MODELS
# ============================================================================

class Policy(BaseModel):
    """
    Company payment policy for automated invoice decisions
    
    Defines rules for when to auto-pay, hold, or block invoices based on
    amount thresholds, fraud scores, and confidence levels.
    """
    companyId: str
    policyId: str
    name: str
    maxAmount: Optional[float] = None
    minAmount: Optional[float] = None
    minConfidence: float = Field(ge=0.0, le=1.0)
    maxFraudScore: float = Field(ge=0.0, le=1.0)
    autoPay: bool = False
    blockUnknownVendors: bool = False
    requirePO: bool = False
    autoBlock: bool = False
    createdAt: str
    updatedAt: str
    active: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "companyId": "company_1",
                "policyId": "auto_small_invoices",
                "name": "Auto-approve small verified invoices",
                "maxAmount": 2000,
                "minConfidence": 0.9,
                "maxFraudScore": 0.2,
                "autoPay": True,
                "blockUnknownVendors": False,
                "requirePO": False,
                "createdAt": "2025-11-10T12:00:00Z",
                "updatedAt": "2025-11-10T12:00:00Z",
                "active": True
            }
        }


class PolicyContract(BaseModel):
    """Root structure for PolicyContract.json"""
    version: str
    contractType: str = "PolicyContract"
    description: str
    lastUpdated: str
    policies: List[Policy]


# ============================================================================
# THREAT INTEL CONTRACT MODELS
# ============================================================================

class Threat(BaseModel):
    """
    Anonymized threat intelligence fingerprint
    
    Stores hashed vendor/payment information to share fraud patterns across
    the network without revealing sensitive business data.
    """
    threatId: str
    vendorHash: str = Field(..., min_length=64, max_length=64)
    paymentTargetType: Literal["wallet_address", "bank_account"]
    paymentTargetHash: str = Field(..., min_length=64, max_length=64)
    invoiceTemplateHash: str = Field(..., min_length=64, max_length=64)
    amountBucket: str  # e.g., "1k-5k", "5k-20k", "20k-50k", "50k+"
    currency: str
    fraudScore: float = Field(ge=0.0, le=1.0)
    reasons: List[str]
    firstSeenAt: str
    lastSeenAt: str
    timesSeen: int = 1
    reporterId: str
    reporterHash: str
    networkReward: float = 0.0
    verified: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "threatId": "threat_550e8400-e29b-41d4-a716-446655440000",
                "vendorHash": "8f3e5b9c2a1d4f6e7b8a9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f",
                "paymentTargetType": "wallet_address",
                "paymentTargetHash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
                "invoiceTemplateHash": "def456abc789def456abc789def456abc789def456abc789def456abc789def4",
                "amountBucket": "5k-20k",
                "currency": "USDC",
                "fraudScore": 0.91,
                "reasons": ["NO_PO_MATCH", "HOURS_EXCEED_LOGS"],
                "firstSeenAt": "2025-11-10T12:00:00Z",
                "lastSeenAt": "2025-11-10T12:00:00Z",
                "timesSeen": 1,
                "reporterId": "company_1",
                "reporterHash": "970c5fda546a269e8b2c0a3f1e7d9c4b",
                "networkReward": 0,
                "verified": False
            }
        }


class ThreatStatistics(BaseModel):
    """Aggregate statistics for threat intelligence"""
    totalThreats: int = 0
    totalBlockedAmount: float = 0.0
    verifiedReporters: int = 0
    highRiskVendors: int = 0
    lastThreatReported: Optional[str] = None


class ThreatIntelContract(BaseModel):
    """Root structure for ThreatIntelContract.json"""
    version: str
    contractType: str = "ThreatIntelContract"
    description: str
    lastUpdated: str
    threats: List[Threat]
    statistics: ThreatStatistics


# ============================================================================
# TREASURY CONTRACT MODELS
# ============================================================================

class TransactionMeta(BaseModel):
    """Additional metadata for treasury transactions"""
    fraudScore: float
    confidence: float
    policyMatched: Optional[str] = None
    paymentMethod: Optional[str] = None
    paymentAddress: Optional[str] = None
    blockReasons: Optional[List[str]] = None
    threatId: Optional[str] = None
    manualReview: bool = False
    approvedBy: Optional[str] = None
    holdReason: Optional[str] = None
    assignedTo: Optional[str] = None


class Transaction(BaseModel):
    """
    Payment transaction record in the treasury
    
    Tracks invoice payments, blocks, and holds with full metadata.
    """
    txId: str
    invoiceId: str
    vendor: str
    vendorId: str
    amount: float
    currency: str = "USDC"
    status: Literal["PAID", "BLOCKED", "HELD", "PENDING"]
    decision: Literal["APPROVE", "BLOCK", "HOLD"]
    timestamp: str
    meta: TransactionMeta
    
    class Config:
        json_schema_extra = {
            "example": {
                "txId": "tx_001",
                "invoiceId": "INV-001",
                "vendor": "Acme Dev",
                "vendorId": "vendor_123",
                "amount": 3200,
                "currency": "USDC",
                "status": "PAID",
                "decision": "APPROVE",
                "timestamp": "2025-11-10T12:34:56Z",
                "meta": {
                    "fraudScore": 0.05,
                    "confidence": 0.97,
                    "policyMatched": "auto_small_invoices",
                    "paymentMethod": "crypto",
                    "paymentAddress": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
                }
            }
        }


class CompanyTreasury(BaseModel):
    """Treasury state for a single company"""
    companyId: str
    companyName: str
    balance: float
    currency: str = "USDC"
    totalPaid: float = 0.0
    totalBlocked: float = 0.0
    totalHeld: float = 0.0
    createdAt: str
    lastActivity: str
    transactions: List[Transaction] = []


class GlobalTreasuryStats(BaseModel):
    """Global statistics across all companies"""
    totalCompanies: int = 0
    totalBalance: float = 0.0
    totalTransactions: int = 0
    totalPaid: float = 0.0
    totalBlocked: float = 0.0
    totalHeld: float = 0.0
    lastTransaction: Optional[str] = None


class TreasuryContract(BaseModel):
    """Root structure for TreasuryContract.json"""
    version: str
    contractType: str = "TreasuryContract"
    description: str
    lastUpdated: str
    companies: List[CompanyTreasury]
    globalStats: GlobalTreasuryStats
