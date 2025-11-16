"""
Contract Utilities - Helper functions for smart contract operations

This module provides utility functions for:
- Hashing vendor names, wallet addresses, and invoice templates
- Generating threat fingerprints
- Amount bucketing for privacy
- Transaction ID generation
- Validation helpers
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional


# ============================================================================
# HASHING UTILITIES
# ============================================================================

def hash_vendor(vendor_name: str) -> str:
    """
    Hash a vendor name/domain for privacy-preserving threat intelligence
    
    Args:
        vendor_name: Vendor name or domain (e.g., "acme.com")
    
    Returns:
        64-character SHA-256 hash
    
    Example:
        >>> hash_vendor("acme.com")
        "8f3e5b9c2a1d4f6e7b8a9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f"
    """
    normalized = vendor_name.lower().strip()
    return hashlib.sha256(normalized.encode()).hexdigest()


def hash_payment_target(payment_target: str, target_type: str = "wallet_address") -> str:
    """
    Hash a wallet address or bank account number for privacy
    
    Args:
        payment_target: Wallet address (0x...) or bank account number
        target_type: Type of target ("wallet_address" or "bank_account")
    
    Returns:
        64-character SHA-256 hash
    
    Example:
        >>> hash_payment_target("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1")
        "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
    """
    # Normalize based on type
    if target_type == "wallet_address":
        normalized = payment_target.lower().strip()
    else:
        # For bank accounts, remove spaces and dashes
        normalized = payment_target.replace(" ", "").replace("-", "").strip()
    
    return hashlib.sha256(normalized.encode()).hexdigest()


def hash_invoice_template(invoice_text: str) -> str:
    """
    Generate a template fingerprint from invoice content
    
    Normalizes invoice text by:
    - Converting to lowercase
    - Removing specific amounts/dates/numbers
    - Extracting structural patterns
    
    Args:
        invoice_text: Raw invoice text content
    
    Returns:
        64-character SHA-256 hash of normalized template
    
    Example:
        >>> hash_invoice_template("INVOICE\nAmount: $3200\nDue: 2025-11-30")
        "def456abc789def456abc789def456abc789def456abc789def456abc789def4"
    """
    import re
    
    # Normalize text
    normalized = invoice_text.lower().strip()
    
    # Remove specific numbers (keep structure)
    normalized = re.sub(r'\d{4}-\d{2}-\d{2}', 'DATE', normalized)  # Dates
    normalized = re.sub(r'\$?\d+[,.]?\d*', 'AMOUNT', normalized)  # Amounts
    normalized = re.sub(r'\d+', 'NUM', normalized)  # Other numbers
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return hashlib.sha256(normalized.encode()).hexdigest()


def hash_company_id(company_id: str) -> str:
    """
    Hash a company ID for anonymous threat reporting
    
    Args:
        company_id: Company identifier
    
    Returns:
        32-character truncated SHA-256 hash
    
    Example:
        >>> hash_company_id("company_1")
        "970c5fda546a269e8b2c0a3f1e7d9c4b"
    """
    return hashlib.sha256(company_id.encode()).hexdigest()[:32]


# ============================================================================
# AMOUNT BUCKETING
# ============================================================================

def bucket_amount(amount: float) -> str:
    """
    Convert exact amount to privacy-preserving bucket range
    
    Buckets:
    - "0-1k": $0 - $1,000
    - "1k-5k": $1,001 - $5,000
    - "5k-20k": $5,001 - $20,000
    - "20k-50k": $20,001 - $50,000
    - "50k-100k": $50,001 - $100,000
    - "100k+": $100,001+
    
    Args:
        amount: Invoice amount in dollars
    
    Returns:
        Bucket string
    
    Example:
        >>> bucket_amount(3200)
        "1k-5k"
        >>> bucket_amount(75000)
        "50k-100k"
    """
    if amount <= 1000:
        return "0-1k"
    elif amount <= 5000:
        return "1k-5k"
    elif amount <= 20000:
        return "5k-20k"
    elif amount <= 50000:
        return "20k-50k"
    elif amount <= 100000:
        return "50k-100k"
    else:
        return "100k+"


# ============================================================================
# ID GENERATION
# ============================================================================

def generate_threat_id() -> str:
    """
    Generate unique threat ID
    
    Returns:
        UUID-based threat ID with prefix
    
    Example:
        >>> generate_threat_id()
        "threat_550e8400-e29b-41d4-a716-446655440000"
    """
    return f"threat_{uuid.uuid4()}"


def generate_transaction_id() -> str:
    """
    Generate unique transaction ID
    
    Returns:
        Sequential transaction ID
    
    Example:
        >>> generate_transaction_id()
        "tx_1732492800123"
    """
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
    return f"tx_{timestamp}"


def generate_policy_id(company_id: str, policy_name: str) -> str:
    """
    Generate policy ID from company and policy name
    
    Args:
        company_id: Company identifier
        policy_name: Human-readable policy name
    
    Returns:
        Kebab-case policy ID
    
    Example:
        >>> generate_policy_id("company_1", "Auto Small Invoices")
        "auto_small_invoices"
    """
    import re
    normalized = policy_name.lower().strip()
    normalized = re.sub(r'[^\w\s-]', '', normalized)
    normalized = re.sub(r'[-\s]+', '_', normalized)
    return normalized


# ============================================================================
# TIMESTAMP UTILITIES
# ============================================================================

def get_iso_timestamp() -> str:
    """
    Get current timestamp in ISO 8601 format
    
    Returns:
        ISO timestamp string
    
    Example:
        >>> get_iso_timestamp()
        "2025-11-15T12:34:56Z"
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ============================================================================
# VALIDATION UTILITIES
# ============================================================================

def is_valid_hash(hash_string: str, expected_length: int = 64) -> bool:
    """
    Validate if string is a valid hexadecimal hash
    
    Args:
        hash_string: Hash string to validate
        expected_length: Expected length (64 for SHA-256)
    
    Returns:
        True if valid hash
    
    Example:
        >>> is_valid_hash("abc123def456...", 64)
        True
    """
    if not hash_string or len(hash_string) != expected_length:
        return False
    
    try:
        int(hash_string, 16)
        return True
    except ValueError:
        return False


def normalize_currency(currency: str) -> str:
    """
    Normalize currency code to uppercase
    
    Args:
        currency: Currency code (usd, usdc, eth, etc.)
    
    Returns:
        Uppercase currency code
    
    Example:
        >>> normalize_currency("usdc")
        "USDC"
    """
    return currency.upper().strip()


def calculate_fraud_score_from_reasons(reasons: list[str]) -> float:
    """
    Calculate estimated fraud score based on fraud reasons
    
    Different fraud indicators have different severity weights.
    
    Args:
        reasons: List of fraud reason codes
    
    Returns:
        Fraud score between 0.0 and 1.0
    
    Example:
        >>> calculate_fraud_score_from_reasons(["NO_PO_MATCH", "HOURS_EXCEED_LOGS"])
        0.75
    """
    # Fraud reason severity weights
    WEIGHTS = {
        "SUSPICIOUS_WALLET_CHANGE": 0.9,
        "TEMPLATE_SIMILARITY_KNOWN_FRAUD": 0.85,
        "NO_PO_MATCH": 0.7,
        "HOURS_EXCEED_LOGS": 0.6,
        "ACCOUNT_NUMBER_MISMATCH": 0.8,
        "DUPLICATE_INVOICE": 0.75,
        "VENDOR_NOT_RECOGNIZED": 0.5,
        "UNUSUAL_AMOUNT": 0.4,
        "SUSPICIOUS_TIMING": 0.3,
    }
    
    if not reasons:
        return 0.0
    
    # Take maximum weight from all reasons
    max_weight = max([WEIGHTS.get(reason, 0.5) for reason in reasons])
    
    # If multiple reasons, boost score
    multiplier = 1.0 + (len(reasons) - 1) * 0.1
    
    return min(max_weight * multiplier, 1.0)
