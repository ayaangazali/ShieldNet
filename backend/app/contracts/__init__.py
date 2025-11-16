"""
Contract module for ShieldNet Smart Contracts

This package provides a JSON-based "smart contract" system that simulates
blockchain functionality locally without requiring any blockchain infrastructure.

Modules:
- models.py - Pydantic models for all contract data structures
- utils.py - Utility functions for hashing, bucketing, ID generation
- contract_engine.py - Main contract backend implementation

Usage:
    from app.contracts import get_contract_backend
    
    backend = get_contract_backend()
    policies = await backend.get_policies("company_1")
"""

from app.contracts.contract_engine import (
    ContractBackend,
    JsonContractBackend,
    get_contract_backend,
    reset_contract_backend,
)

from app.contracts.models import (
    Policy,
    PolicyContract,
    Threat,
    ThreatIntelContract,
    ThreatStatistics,
    Transaction,
    TransactionMeta,
    CompanyTreasury,
    TreasuryContract,
    GlobalTreasuryStats,
)

from app.contracts.utils import (
    hash_vendor,
    hash_payment_target,
    hash_invoice_template,
    hash_company_id,
    bucket_amount,
    generate_threat_id,
    generate_transaction_id,
    generate_policy_id,
    get_iso_timestamp,
    is_valid_hash,
    normalize_currency,
    calculate_fraud_score_from_reasons,
)

__all__ = [
    # Backend
    "ContractBackend",
    "JsonContractBackend",
    "get_contract_backend",
    "reset_contract_backend",
    # Models
    "Policy",
    "PolicyContract",
    "Threat",
    "ThreatIntelContract",
    "ThreatStatistics",
    "Transaction",
    "TransactionMeta",
    "CompanyTreasury",
    "TreasuryContract",
    "GlobalTreasuryStats",
    # Utils
    "hash_vendor",
    "hash_payment_target",
    "hash_invoice_template",
    "hash_company_id",
    "bucket_amount",
    "generate_threat_id",
    "generate_transaction_id",
    "generate_policy_id",
    "get_iso_timestamp",
    "is_valid_hash",
    "normalize_currency",
    "calculate_fraud_score_from_reasons",
]
