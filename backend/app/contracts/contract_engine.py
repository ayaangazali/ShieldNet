"""
Smart Contract Engine - JSON-based blockchain simulation

This module provides a local, file-based "smart contract" system for ShieldNet.
Instead of deploying contracts to a real blockchain, we simulate contracts using
JSON files stored in the `smart_contracts/` directory.

**ARCHITECTURE:**

1. **ContractBackend (Abstract Interface)**
   - Defines the contract interface for threat intel, policies, and treasury
   - Allows future migration to real blockchain by swapping implementations

2. **JsonContractBackend (Current Implementation)**
   - Implements ContractBackend using JSON files
   - Thread-safe file locking for concurrent access
   - Automatic file creation with default structures
   - Full CRUD operations for all contract types

3. **Future: OnchainContractBackend (TODO)**
   - Would implement ContractBackend using Web3/ethers.js
   - Same interface, different storage layer
   - Zero application code changes required

**BENEFITS:**
- ✅ No blockchain infrastructure needed for demos
- ✅ Instant transactions (no gas, no waiting)
- ✅ Easy to inspect state (just open JSON files)
- ✅ Version controllable (commit contract state to git)
- ✅ Future-proof (clean abstraction for real blockchain later)

**USAGE:**
    from app.contracts.contract_engine import get_contract_backend
    
    backend = get_contract_backend()  # Returns JsonContractBackend
    
    # Read/write policies
    policies = await backend.get_policies("company_1")
    await backend.update_policies("company_1", updated_policies)
    
    # Report threats
    threat = Threat(...)
    await backend.append_threat(threat)
    
    # Record payments
    tx = Transaction(...)
    await backend.record_payment("company_1", tx)
"""

import json
import os
import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime, timezone
import logging
from threading import Lock

from app.contracts.models import (
    Policy,
    PolicyContract,
    Threat,
    ThreatIntelContract,
    ThreatStatistics,
    Transaction,
    CompanyTreasury,
    TreasuryContract,
    GlobalTreasuryStats,
)
from app.contracts.utils import get_iso_timestamp

logger = logging.getLogger(__name__)


# ============================================================================
# ABSTRACT CONTRACT BACKEND INTERFACE
# ============================================================================

class ContractBackend(ABC):
    """
    Abstract interface for smart contract operations
    
    This defines the contract operations that ShieldNet needs. Any implementation
    (JSON, blockchain, database, etc.) must implement these methods.
    
    Future implementations:
    - JsonContractBackend (current) - stores contracts in JSON files
    - OnchainContractBackend (future) - stores contracts on Base L3 blockchain
    - PostgresContractBackend (future) - stores contracts in PostgreSQL
    """
    
    # ========== POLICY CONTRACT ==========
    
    @abstractmethod
    async def get_policies(self, company_id: str) -> List[Policy]:
        """Get all policies for a company"""
        pass
    
    @abstractmethod
    async def get_policy(self, company_id: str, policy_id: str) -> Optional[Policy]:
        """Get a specific policy by ID"""
        pass
    
    @abstractmethod
    async def update_policies(self, company_id: str, policies: List[Policy]) -> None:
        """Update all policies for a company"""
        pass
    
    @abstractmethod
    async def add_policy(self, policy: Policy) -> None:
        """Add a new policy"""
        pass
    
    @abstractmethod
    async def delete_policy(self, company_id: str, policy_id: str) -> bool:
        """Delete a policy"""
        pass
    
    # ========== THREAT INTEL CONTRACT ==========
    
    @abstractmethod
    async def append_threat(self, threat: Threat) -> str:
        """Append a new threat to the intelligence network"""
        pass
    
    @abstractmethod
    async def list_threats(
        self,
        vendor_hash: Optional[str] = None,
        limit: int = 100
    ) -> List[Threat]:
        """List threats, optionally filtered by vendor hash"""
        pass
    
    @abstractmethod
    async def get_threat(self, threat_id: str) -> Optional[Threat]:
        """Get a specific threat by ID"""
        pass
    
    @abstractmethod
    async def get_threat_statistics(self) -> ThreatStatistics:
        """Get aggregate threat intelligence statistics"""
        pass
    
    # ========== TREASURY CONTRACT ==========
    
    @abstractmethod
    async def record_payment(self, company_id: str, transaction: Transaction) -> str:
        """Record a payment transaction"""
        pass
    
    @abstractmethod
    async def get_company_treasury(self, company_id: str) -> CompanyTreasury:
        """Get treasury state for a company"""
        pass
    
    @abstractmethod
    async def list_transactions(
        self,
        company_id: str,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Transaction]:
        """List transactions for a company"""
        pass
    
    @abstractmethod
    async def get_global_treasury_stats(self) -> GlobalTreasuryStats:
        """Get global treasury statistics"""
        pass


# ============================================================================
# JSON-BASED CONTRACT BACKEND IMPLEMENTATION
# ============================================================================

class JsonContractBackend(ContractBackend):
    """
    JSON file-based smart contract implementation
    
    This implementation stores contract state in JSON files in the
    `smart_contracts/` directory at the project root.
    
    **Thread Safety:**
    Uses file locks to ensure safe concurrent access.
    
    **File Locations:**
    - PolicyContract.json - company policies
    - ThreatIntelContract.json - threat intelligence
    - TreasuryContract.json - payment ledger
    """
    
    def __init__(self, contracts_dir: Optional[Path] = None):
        """
        Initialize JSON contract backend
        
        Args:
            contracts_dir: Path to smart_contracts directory.
                          Defaults to <project_root>/smart_contracts
        """
        if contracts_dir is None:
            # Default: <project_root>/smart_contracts
            backend_dir = Path(__file__).parent.parent.parent  # backend/
            project_root = backend_dir.parent  # ShieldNet/
            contracts_dir = project_root / "smart_contracts"
        
        self.contracts_dir = Path(contracts_dir)
        self.contracts_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.policy_file = self.contracts_dir / "PolicyContract.json"
        self.threat_file = self.contracts_dir / "ThreatIntelContract.json"
        self.treasury_file = self.contracts_dir / "TreasuryContract.json"
        
        # Thread-safe locks for each contract file
        self._policy_lock = Lock()
        self._threat_lock = Lock()
        self._treasury_lock = Lock()
        
        # Initialize files if they don't exist
        self._initialize_contracts()
        
        logger.info(f"✅ JsonContractBackend initialized: {self.contracts_dir}")
    
    def _initialize_contracts(self):
        """Create default contract files if they don't exist"""
        
        # Initialize PolicyContract.json
        if not self.policy_file.exists():
            default_policy = PolicyContract(
                version="1.0.0",
                contractType="PolicyContract",
                description="Stores company payment policies and mandate rules",
                lastUpdated=get_iso_timestamp(),
                policies=[]
            )
            self._write_json(self.policy_file, default_policy.model_dump(), self._policy_lock)
            logger.info(f"📝 Created default {self.policy_file.name}")
        
        # Initialize ThreatIntelContract.json
        if not self.threat_file.exists():
            default_threat = ThreatIntelContract(
                version="1.0.0",
                contractType="ThreatIntelContract",
                description="Decentralized threat intelligence network",
                lastUpdated=get_iso_timestamp(),
                threats=[],
                statistics=ThreatStatistics()
            )
            self._write_json(self.threat_file, default_threat.model_dump(), self._threat_lock)
            logger.info(f"📝 Created default {self.threat_file.name}")
        
        # Initialize TreasuryContract.json
        if not self.treasury_file.exists():
            default_treasury = TreasuryContract(
                version="1.0.0",
                contractType="TreasuryContract",
                description="Treasury management and payment ledger",
                lastUpdated=get_iso_timestamp(),
                companies=[],
                globalStats=GlobalTreasuryStats()
            )
            self._write_json(self.treasury_file, default_treasury.model_dump(), self._treasury_lock)
            logger.info(f"📝 Created default {self.treasury_file.name}")
    
    def _read_json(self, file_path: Path, lock: Lock) -> Dict[str, Any]:
        """Thread-safe JSON file read"""
        with lock:
            with open(file_path, 'r') as f:
                return json.load(f)
    
    def _write_json(self, file_path: Path, data: Dict[str, Any], lock: Lock) -> None:
        """Thread-safe JSON file write"""
        with lock:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
    
    # ========== POLICY CONTRACT IMPLEMENTATION ==========
    
    async def get_policies(self, company_id: str) -> List[Policy]:
        """Get all policies for a company"""
        data = self._read_json(self.policy_file, self._policy_lock)
        contract = PolicyContract(**data)
        
        company_policies = [p for p in contract.policies if p.companyId == company_id]
        return company_policies
    
    async def get_policy(self, company_id: str, policy_id: str) -> Optional[Policy]:
        """Get a specific policy by ID"""
        policies = await self.get_policies(company_id)
        for policy in policies:
            if policy.policyId == policy_id:
                return policy
        return None
    
    async def update_policies(self, company_id: str, policies: List[Policy]) -> None:
        """Update all policies for a company"""
        data = self._read_json(self.policy_file, self._policy_lock)
        contract = PolicyContract(**data)
        
        # Remove old policies for this company
        contract.policies = [p for p in contract.policies if p.companyId != company_id]
        
        # Add new policies
        contract.policies.extend(policies)
        contract.lastUpdated = get_iso_timestamp()
        
        self._write_json(self.policy_file, contract.model_dump(), self._policy_lock)
        logger.info(f"📋 Updated {len(policies)} policies for {company_id}")
    
    async def add_policy(self, policy: Policy) -> None:
        """Add a new policy"""
        data = self._read_json(self.policy_file, self._policy_lock)
        contract = PolicyContract(**data)
        
        # Check if policy already exists
        existing = [p for p in contract.policies 
                   if p.companyId == policy.companyId and p.policyId == policy.policyId]
        
        if existing:
            # Update existing policy
            contract.policies = [p for p in contract.policies 
                               if not (p.companyId == policy.companyId and p.policyId == policy.policyId)]
        
        contract.policies.append(policy)
        contract.lastUpdated = get_iso_timestamp()
        
        self._write_json(self.policy_file, contract.model_dump(), self._policy_lock)
        logger.info(f"➕ Added policy {policy.policyId} for {policy.companyId}")
    
    async def delete_policy(self, company_id: str, policy_id: str) -> bool:
        """Delete a policy"""
        data = self._read_json(self.policy_file, self._policy_lock)
        contract = PolicyContract(**data)
        
        original_count = len(contract.policies)
        contract.policies = [p for p in contract.policies 
                            if not (p.companyId == company_id and p.policyId == policy_id)]
        
        if len(contract.policies) < original_count:
            contract.lastUpdated = get_iso_timestamp()
            self._write_json(self.policy_file, contract.model_dump(), self._policy_lock)
            logger.info(f"🗑️  Deleted policy {policy_id} for {company_id}")
            return True
        
        return False
    
    # ========== THREAT INTEL CONTRACT IMPLEMENTATION ==========
    
    async def append_threat(self, threat: Threat) -> str:
        """Append a new threat to the intelligence network"""
        data = self._read_json(self.threat_file, self._threat_lock)
        contract = ThreatIntelContract(**data)
        
        # Check if threat already exists (by threatId)
        existing = [t for t in contract.threats if t.threatId == threat.threatId]
        
        if existing:
            # Update existing threat (increment timesSeen, update lastSeenAt)
            for t in contract.threats:
                if t.threatId == threat.threatId:
                    t.timesSeen += 1
                    t.lastSeenAt = get_iso_timestamp()
                    logger.info(f"🔄 Updated existing threat {threat.threatId} (seen {t.timesSeen}x)")
                    break
        else:
            # Add new threat
            contract.threats.append(threat)
            logger.info(f"🚨 Appended new threat {threat.threatId}")
        
        # Update statistics
        contract.statistics.totalThreats = len(contract.threats)
        contract.statistics.lastThreatReported = get_iso_timestamp()
        contract.statistics.highRiskVendors = len(set(t.vendorHash for t in contract.threats))
        
        # Calculate total blocked amount (estimate from buckets)
        total_blocked = sum(self._estimate_bucket_amount(t.amountBucket) for t in contract.threats)
        contract.statistics.totalBlockedAmount = total_blocked
        
        contract.lastUpdated = get_iso_timestamp()
        
        self._write_json(self.threat_file, contract.model_dump(), self._threat_lock)
        
        return threat.threatId
    
    def _estimate_bucket_amount(self, bucket: str) -> float:
        """Estimate average amount from bucket string"""
        bucket_values = {
            "0-1k": 500,
            "1k-5k": 3000,
            "5k-20k": 12500,
            "20k-50k": 35000,
            "50k-100k": 75000,
            "100k+": 150000,
        }
        return bucket_values.get(bucket, 10000)
    
    async def list_threats(
        self,
        vendor_hash: Optional[str] = None,
        limit: int = 100
    ) -> List[Threat]:
        """List threats, optionally filtered by vendor hash"""
        data = self._read_json(self.threat_file, self._threat_lock)
        contract = ThreatIntelContract(**data)
        
        threats = contract.threats
        
        if vendor_hash:
            threats = [t for t in threats if t.vendorHash == vendor_hash]
        
        # Sort by lastSeenAt (most recent first)
        threats.sort(key=lambda t: t.lastSeenAt, reverse=True)
        
        return threats[:limit]
    
    async def get_threat(self, threat_id: str) -> Optional[Threat]:
        """Get a specific threat by ID"""
        data = self._read_json(self.threat_file, self._threat_lock)
        contract = ThreatIntelContract(**data)
        
        for threat in contract.threats:
            if threat.threatId == threat_id:
                return threat
        
        return None
    
    async def get_threat_statistics(self) -> ThreatStatistics:
        """Get aggregate threat intelligence statistics"""
        data = self._read_json(self.threat_file, self._threat_lock)
        contract = ThreatIntelContract(**data)
        return contract.statistics
    
    # ========== TREASURY CONTRACT IMPLEMENTATION ==========
    
    async def record_payment(self, company_id: str, transaction: Transaction) -> str:
        """Record a payment transaction"""
        data = self._read_json(self.treasury_file, self._treasury_lock)
        contract = TreasuryContract(**data)
        
        # Find or create company treasury
        company_treasury = None
        for company in contract.companies:
            if company.companyId == company_id:
                company_treasury = company
                break
        
        if not company_treasury:
            # Create new company treasury
            company_treasury = CompanyTreasury(
                companyId=company_id,
                companyName=company_id.replace("_", " ").title(),
                balance=100000,  # Default starting balance
                currency=transaction.currency,
                createdAt=get_iso_timestamp(),
                lastActivity=get_iso_timestamp(),
                transactions=[]
            )
            contract.companies.append(company_treasury)
            logger.info(f"🏦 Created treasury for {company_id}")
        
        # Add transaction
        company_treasury.transactions.append(transaction)
        company_treasury.lastActivity = get_iso_timestamp()
        
        # Update balance and totals
        if transaction.status == "PAID":
            company_treasury.balance -= transaction.amount
            company_treasury.totalPaid += transaction.amount
        elif transaction.status == "BLOCKED":
            company_treasury.totalBlocked += transaction.amount
        elif transaction.status == "HELD":
            company_treasury.totalHeld += transaction.amount
        
        # Update global statistics
        contract.globalStats.totalCompanies = len(contract.companies)
        contract.globalStats.totalBalance = sum(c.balance for c in contract.companies)
        contract.globalStats.totalTransactions = sum(len(c.transactions) for c in contract.companies)
        contract.globalStats.totalPaid = sum(c.totalPaid for c in contract.companies)
        contract.globalStats.totalBlocked = sum(c.totalBlocked for c in contract.companies)
        contract.globalStats.totalHeld = sum(c.totalHeld for c in contract.companies)
        contract.globalStats.lastTransaction = get_iso_timestamp()
        
        contract.lastUpdated = get_iso_timestamp()
        
        self._write_json(self.treasury_file, contract.model_dump(), self._treasury_lock)
        
        logger.info(f"💰 Recorded transaction {transaction.txId} for {company_id}: {transaction.status}")
        
        return transaction.txId
    
    async def get_company_treasury(self, company_id: str) -> CompanyTreasury:
        """Get treasury state for a company"""
        data = self._read_json(self.treasury_file, self._treasury_lock)
        contract = TreasuryContract(**data)
        
        for company in contract.companies:
            if company.companyId == company_id:
                return company
        
        # Return default empty treasury if not found
        return CompanyTreasury(
            companyId=company_id,
            companyName=company_id.replace("_", " ").title(),
            balance=0,
            currency="USDC",
            createdAt=get_iso_timestamp(),
            lastActivity=get_iso_timestamp(),
            transactions=[]
        )
    
    async def list_transactions(
        self,
        company_id: str,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Transaction]:
        """List transactions for a company"""
        treasury = await self.get_company_treasury(company_id)
        
        transactions = treasury.transactions
        
        if status:
            transactions = [t for t in transactions if t.status == status]
        
        # Sort by timestamp (most recent first)
        transactions.sort(key=lambda t: t.timestamp, reverse=True)
        
        return transactions[:limit]
    
    async def get_global_treasury_stats(self) -> GlobalTreasuryStats:
        """Get global treasury statistics"""
        data = self._read_json(self.treasury_file, self._treasury_lock)
        contract = TreasuryContract(**data)
        return contract.globalStats


# ============================================================================
# SINGLETON FACTORY
# ============================================================================

_contract_backend_instance: Optional[ContractBackend] = None


def get_contract_backend() -> ContractBackend:
    """
    Get the global contract backend instance (singleton)
    
    Returns:
        ContractBackend instance (currently JsonContractBackend)
    
    Example:
        backend = get_contract_backend()
        policies = await backend.get_policies("company_1")
    """
    global _contract_backend_instance
    
    if _contract_backend_instance is None:
        _contract_backend_instance = JsonContractBackend()
        logger.info("🔧 Initialized global ContractBackend (JSON-based)")
    
    return _contract_backend_instance


def reset_contract_backend(backend: Optional[ContractBackend] = None):
    """
    Reset the global contract backend instance (for testing)
    
    Args:
        backend: New backend instance, or None to clear
    """
    global _contract_backend_instance
    _contract_backend_instance = backend
