# ShieldNet Smart Contracts

## Overview

ShieldNet uses a **JSON-based "smart contract" system** that simulates blockchain functionality without requiring any actual blockchain infrastructure. This approach provides:

- ✅ **Zero blockchain dependencies** - no RPC nodes, no gas fees, no wallet management
- ✅ **Instant transactions** - no waiting for block confirmations
- ✅ **Full transparency** - easily inspect contract state by opening JSON files
- ✅ **Version controllable** - commit contract state to git
- ✅ **Future-proof architecture** - clean abstraction for migrating to real blockchain later

## Architecture

### Three Core Contracts

1. **PolicyContract** (`PolicyContract.json`)
   - Stores company payment policies and mandate rules
   - Controls auto-pay/hold/block decisions based on thresholds
   - Defines fraud score limits, confidence requirements, PO matching rules

2. **ThreatIntelContract** (`ThreatIntelContract.json`)
   - Decentralized threat intelligence network
   - Stores anonymized fraud fingerprints (hashed vendor/payment data)
   - Enables cross-company fraud detection without revealing sensitive information

3. **TreasuryContract** (`TreasuryContract.json`)
   - Payment ledger tracking all transactions
   - Company balances and spending history
   - Global statistics across all companies

### Contract Backend Interface

```
ContractBackend (Abstract Interface)
├── JsonContractBackend (Current - JSON files)
└── OnchainContractBackend (Future - Real blockchain)
```

The `ContractBackend` abstract interface defines all contract operations. This allows us to swap storage implementations without changing application code.

**Current Implementation: JsonContractBackend**
- Stores contracts in JSON files in `smart_contracts/` directory
- Thread-safe file locking for concurrent access
- Automatic file creation with default structures

**Future Implementation: OnchainContractBackend**
- Would store contracts on Base L3 or other blockchain
- Same interface, different storage layer
- Zero application code changes required

## Contract Structures

### PolicyContract.json

```json
{
  "version": "1.0.0",
  "contractType": "PolicyContract",
  "description": "Stores company payment policies and mandate rules",
  "lastUpdated": "2025-11-15T00:00:00Z",
  "policies": [
    {
      "companyId": "company_1",
      "policyId": "auto_small_invoices",
      "name": "Auto-approve small verified invoices",
      "maxAmount": 2000,
      "minConfidence": 0.9,
      "maxFraudScore": 0.2,
      "autoPay": true,
      "blockUnknownVendors": false,
      "requirePO": false,
      "createdAt": "2025-11-10T12:00:00Z",
      "updatedAt": "2025-11-10T12:00:00Z",
      "active": true
    }
  ]
}
```

**Policy Fields:**
- `maxAmount` / `minAmount` - Amount thresholds for policy matching
- `minConfidence` - Minimum AI confidence score required
- `maxFraudScore` - Maximum fraud score allowed
- `autoPay` - Whether to automatically approve and pay
- `blockUnknownVendors` - Block invoices from unrecognized vendors
- `requirePO` - Require purchase order matching
- `autoBlock` - Automatically block without review

### ThreatIntelContract.json

```json
{
  "version": "1.0.0",
  "contractType": "ThreatIntelContract",
  "description": "Decentralized threat intelligence network",
  "lastUpdated": "2025-11-15T00:00:00Z",
  "threats": [
    {
      "threatId": "threat_550e8400-e29b-41d4-a716-446655440000",
      "vendorHash": "8f3e5b9c...d9e0f",
      "paymentTargetType": "wallet_address",
      "paymentTargetHash": "a1b2c3d4...f0a1b2",
      "invoiceTemplateHash": "def456ab...89def4",
      "amountBucket": "5k-20k",
      "currency": "USDC",
      "fraudScore": 0.91,
      "reasons": ["NO_PO_MATCH", "HOURS_EXCEED_LOGS"],
      "firstSeenAt": "2025-11-10T12:00:00Z",
      "lastSeenAt": "2025-11-10T12:00:00Z",
      "timesSeen": 1,
      "reporterId": "company_1",
      "reporterHash": "970c5fda546a269e",
      "networkReward": 0,
      "verified": false
    }
  ],
  "statistics": {
    "totalThreats": 2,
    "totalBlockedAmount": 27000,
    "verifiedReporters": 1,
    "highRiskVendors": 2,
    "lastThreatReported": "2025-11-14T16:45:00Z"
  }
}
```

**Privacy Protection:**
- All vendor names → SHA-256 hashes
- All wallet addresses/bank accounts → SHA-256 hashes
- Invoice templates → normalized and hashed
- Exact amounts → bucketed ranges ("5k-20k")

**Amount Buckets:**
- `0-1k` - $0 - $1,000
- `1k-5k` - $1,001 - $5,000
- `5k-20k` - $5,001 - $20,000
- `20k-50k` - $20,001 - $50,000
- `50k-100k` - $50,001 - $100,000
- `100k+` - $100,001+

### TreasuryContract.json

```json
{
  "version": "1.0.0",
  "contractType": "TreasuryContract",
  "description": "Treasury management and payment ledger",
  "lastUpdated": "2025-11-15T00:00:00Z",
  "companies": [
    {
      "companyId": "company_1",
      "companyName": "Acme Corp",
      "balance": 50000,
      "currency": "USDC",
      "totalPaid": 15400,
      "totalBlocked": 8200,
      "totalHeld": 3500,
      "createdAt": "2025-11-01T00:00:00Z",
      "lastActivity": "2025-11-14T18:30:00Z",
      "transactions": [
        {
          "txId": "tx_001",
          "invoiceId": "INV-001",
          "vendor": "Acme Dev",
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
            "paymentAddress": "0x742d35Cc..."
          }
        }
      ]
    }
  ],
  "globalStats": {
    "totalCompanies": 2,
    "totalBalance": 75000,
    "totalTransactions": 5,
    "totalPaid": 24300,
    "totalBlocked": 10500,
    "totalHeld": 3500,
    "lastTransaction": "2025-11-14T18:30:00Z"
  }
}
```

**Transaction Statuses:**
- `PAID` - Payment approved and executed
- `BLOCKED` - Invoice blocked due to fraud detection
- `HELD` - Invoice held for manual review
- `PENDING` - Payment queued but not processed

## Usage Examples

### Read Policies

```python
from app.contracts import get_contract_backend

backend = get_contract_backend()

# Get all policies for a company
policies = await backend.get_policies("company_1")

# Get specific policy
policy = await backend.get_policy("company_1", "auto_small_invoices")
```

### Update Policies

```python
from app.contracts import get_contract_backend, Policy, get_iso_timestamp

backend = get_contract_backend()

new_policy = Policy(
    companyId="company_1",
    policyId="auto_medium_invoices",
    name="Auto-approve medium trusted vendors",
    maxAmount=10000,
    minConfidence=0.95,
    maxFraudScore=0.15,
    autoPay=True,
    blockUnknownVendors=True,
    requirePO=False,
    createdAt=get_iso_timestamp(),
    updatedAt=get_iso_timestamp(),
    active=True
)

await backend.add_policy(new_policy)
```

### Report Threat

```python
from app.contracts import (
    get_contract_backend,
    Threat,
    hash_vendor,
    hash_payment_target,
    hash_invoice_template,
    bucket_amount,
    generate_threat_id,
    hash_company_id,
    get_iso_timestamp
)

backend = get_contract_backend()

threat = Threat(
    threatId=generate_threat_id(),
    vendorHash=hash_vendor("suspicious-vendor.com"),
    paymentTargetType="wallet_address",
    paymentTargetHash=hash_payment_target("0x123abc..."),
    invoiceTemplateHash=hash_invoice_template(invoice_text),
    amountBucket=bucket_amount(8500),  # Returns "5k-20k"
    currency="USDC",
    fraudScore=0.89,
    reasons=["NO_PO_MATCH", "SUSPICIOUS_WALLET_CHANGE"],
    firstSeenAt=get_iso_timestamp(),
    lastSeenAt=get_iso_timestamp(),
    timesSeen=1,
    reporterId="company_1",
    reporterHash=hash_company_id("company_1"),
    networkReward=0,
    verified=False
)

threat_id = await backend.append_threat(threat)
```

### Query Threats

```python
from app.contracts import get_contract_backend

backend = get_contract_backend()

# List all threats
all_threats = await backend.list_threats()

# Filter by vendor
vendor_threats = await backend.list_threats(
    vendor_hash="8f3e5b9c2a1d4f6e..."
)

# Get statistics
stats = await backend.get_threat_statistics()
print(f"Total threats: {stats.totalThreats}")
print(f"Blocked amount: ${stats.totalBlockedAmount:,.2f}")
```

### Record Payment

```python
from app.contracts import (
    get_contract_backend,
    Transaction,
    TransactionMeta,
    generate_transaction_id,
    get_iso_timestamp
)

backend = get_contract_backend()

transaction = Transaction(
    txId=generate_transaction_id(),
    invoiceId="INV-123",
    vendor="Acme Corp",
    vendorId="vendor_456",
    amount=5400,
    currency="USDC",
    status="PAID",
    decision="APPROVE",
    timestamp=get_iso_timestamp(),
    meta=TransactionMeta(
        fraudScore=0.08,
        confidence=0.96,
        policyMatched="auto_small_invoices",
        paymentMethod="crypto",
        paymentAddress="0x742d35Cc..."
    )
)

tx_id = await backend.record_payment("company_1", transaction)
```

### Get Treasury Info

```python
from app.contracts import get_contract_backend

backend = get_contract_backend()

# Get company treasury
treasury = await backend.get_company_treasury("company_1")
print(f"Balance: ${treasury.balance:,.2f}")
print(f"Total paid: ${treasury.totalPaid:,.2f}")
print(f"Transactions: {len(treasury.transactions)}")

# Get global stats
global_stats = await backend.get_global_treasury_stats()
print(f"Total companies: {global_stats.totalCompanies}")
print(f"Total transactions: {global_stats.totalTransactions}")
```

## Integration with ShieldNet Backend

The smart contract system integrates with existing ShieldNet endpoints:

### Invoice Processing Flow

1. **Invoice Submitted** → AI extracts vendor, amount, confidence
2. **Check Policies** → `backend.get_policies(company_id)` retrieves rules
3. **Check Threats** → Query threats by vendor hash to detect known fraud
4. **Make Decision** → APPROVE / HOLD / BLOCK based on policies + threats
5. **Record Payment** → `backend.record_payment()` adds to treasury ledger
6. **Report Fraud** → If blocked, `backend.append_threat()` shares intelligence

### Modified Endpoints

- **POST /api/threats/report** → Calls `backend.append_threat()`
- **GET /api/threats/analytics** → Calls `backend.get_threat_statistics()`
- **GET /api/policies** → Calls `backend.get_policies()`
- **POST /api/policies** → Calls `backend.add_policy()`
- **POST /api/treasury/payment** → Calls `backend.record_payment()`
- **GET /api/treasury** → Calls `backend.get_company_treasury()`

## Benefits Over Real Blockchain

| Feature | JSON Contracts | Real Blockchain |
|---------|---------------|-----------------|
| **Setup** | Zero config | RPC node, wallet, gas |
| **Speed** | Instant | 1-30s per transaction |
| **Cost** | Free | Gas fees ($0.01-$1.00) |
| **Debugging** | Open JSON file | Block explorer |
| **Testing** | Edit JSON directly | Deploy test contracts |
| **Portability** | Works offline | Needs internet |
| **Version Control** | Git-friendly | On-chain only |

## Migration Path to Real Blockchain

When ready to deploy to a real blockchain (Base L3, Ethereum, etc.):

1. **Implement OnchainContractBackend** in `contract_engine.py`
2. **Use Web3.py** to interact with deployed smart contracts
3. **Update backend initialization** to use `OnchainContractBackend()`
4. **No application code changes required** - same interface!

```python
# Future: Switch to blockchain backend
from app.contracts import reset_contract_backend, OnchainContractBackend

# Initialize blockchain backend
blockchain_backend = OnchainContractBackend(
    rpc_url="https://mainnet.base.org",
    contract_addresses={
        "policy": "0x123abc...",
        "threat": "0x456def...",
        "treasury": "0x789ghi..."
    }
)

reset_contract_backend(blockchain_backend)

# Rest of the app works identically!
backend = get_contract_backend()
policies = await backend.get_policies("company_1")  # Now reads from blockchain
```

## File Locations

```
ShieldNet/
├── smart_contracts/              # JSON contract files
│   ├── PolicyContract.json       # Company policies
│   ├── ThreatIntelContract.json  # Threat intelligence
│   ├── TreasuryContract.json     # Payment ledger
│   └── README.md                 # This file
│
└── backend/
    └── app/
        └── contracts/            # Contract engine code
            ├── __init__.py       # Public exports
            ├── models.py         # Pydantic models
            ├── utils.py          # Helper functions
            └── contract_engine.py # Backend implementation
```

## Thread Safety

All contract operations are thread-safe:
- File-level locking prevents race conditions
- Multiple API requests can safely read/write contracts concurrently
- No data corruption risk

## Backup and Recovery

**Backup:**
```bash
# Backup all contracts
cp -r smart_contracts/ smart_contracts_backup_$(date +%Y%m%d)/

# Commit to git
git add smart_contracts/
git commit -m "Backup contracts state"
```

**Restore:**
```bash
# Restore from backup
cp -r smart_contracts_backup_20251115/ smart_contracts/

# Restore from git
git checkout main smart_contracts/
```

## Testing

```python
# Test contract operations
from app.contracts import get_contract_backend, reset_contract_backend

# Use temporary directory for testing
import tempfile
from pathlib import Path

test_dir = Path(tempfile.mkdtemp())
test_backend = JsonContractBackend(contracts_dir=test_dir)
reset_contract_backend(test_backend)

# Now all operations use test directory
backend = get_contract_backend()
await backend.add_policy(test_policy)

# Cleanup
import shutil
shutil.rmtree(test_dir)
reset_contract_backend()  # Reset to default
```

## Conclusion

ShieldNet's JSON-based smart contract system provides all the benefits of blockchain architecture (immutability, transparency, shared intelligence) without the complexity. The clean abstraction layer means we can migrate to a real blockchain later with zero application code changes - just swap the backend implementation!

**For the hackathon:** This approach lets us demonstrate the full product without blockchain infrastructure.

**For production:** We can deploy real contracts to Base L3 or other networks when ready.

Best of both worlds! 🚀
