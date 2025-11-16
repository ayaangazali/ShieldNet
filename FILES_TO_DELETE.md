# 🗑️ Files to DELETE - Smart Contracts Only Mode

## Summary

To use ONLY the smart contracts system (no blockchain, no SQLite), delete these files:

## ❌ DELETE: Blockchain Infrastructure

### Hardhat/Solidity Files
```bash
blockchain_deployment/          # Entire folder - Solidity contracts for blockchain
backend/contracts/              # Entire folder - Hardhat deployment files
```

**Why:** These were for deploying to Base blockchain. Smart contracts use JSON files instead.

---

## ❌ DELETE: Old Threat Intelligence System

### Backend Services (Obsolete)
```bash
backend/app/services/onchain_threat_store.py          # Blockchain threat storage (stub)
backend/app/services/local_threat_intel_store.py      # SQLite threat storage
backend/app/services/local_threat_store.py            # Old local storage
backend/app/services/threat_intel_store.py            # Abstract interface (replaced)
backend/app/services/blockchain_threat_intel.py       # Blockchain integration
backend/app/services/shieldnet_contract_client.py     # Smart contract client
```

**Why:** Replaced by `backend/app/contracts/` engine which uses JSON files.

---

## ❌ DELETE: Blockchain Documentation

```bash
backend/BLOCKCHAIN_INTEGRATION_GUIDE.md
backend/BLOCKCHAIN_INTEGRATION_SUMMARY.md
backend/BLOCKCHAIN_README.md
backend/BLOCKCHAIN_TEST_RESULTS.md
backend/LOCAL_MODE_IMPLEMENTATION.md
backend/THREAT_INTEL_QUICK_REF.md
backend/THREAT_INTEL_README.md
```

**Why:** All blockchain documentation is obsolete. Use `smart_contracts/README.md` instead.

---

## ❌ DELETE: Old Test Files

```bash
backend/test_blockchain.py       # Tests for blockchain integration
backend/test_local_threats.py    # Tests for SQLite threat storage
```

**Why:** Replaced by `backend/test_smart_contracts.py`.

---

## ❌ DELETE: SQLite Database

```bash
backend/shieldnet.db             # Old SQLite database for threat storage
```

**Why:** Threats now stored in `smart_contracts/ThreatIntelContract.json`.

---

## ❌ DELETE: Redundant Documentation

```bash
BACKEND_IMPLEMENTATION_SUMMARY.md
INVOICE_PROCESSING_FEATURE.md
```

**Why:** All info consolidated in `SMART_CONTRACTS_IMPLEMENTATION.md`.

---

## ✅ KEEP: Essential Smart Contracts Files

### Contract Data (JSON)
```bash
smart_contracts/
├── PolicyContract.json              # ✅ KEEP - Company policies
├── ThreatIntelContract.json         # ✅ KEEP - Threat intelligence
├── TreasuryContract.json            # ✅ KEEP - Payment ledger
└── README.md                        # ✅ KEEP - Documentation
```

### Contract Engine (Python)
```bash
backend/app/contracts/
├── __init__.py                      # ✅ KEEP - Public API
├── contract_engine.py               # ✅ KEEP - Core engine (620 lines)
├── models.py                        # ✅ KEEP - Pydantic models (230 lines)
└── utils.py                         # ✅ KEEP - Utilities (290 lines)
```

### Tests & Docs
```bash
backend/test_smart_contracts.py      # ✅ KEEP - Test suite
SMART_CONTRACTS_IMPLEMENTATION.md    # ✅ KEEP - Full documentation
```

### Standard Backend Files (Keep if using FastAPI)
```bash
backend/
├── app/
│   ├── main.py                      # ✅ KEEP - FastAPI app
│   ├── config.py                    # ✅ KEEP - Configuration
│   ├── routers/                     # ✅ KEEP - API endpoints
│   └── ...                          # ✅ KEEP - Other app files
├── requirements.txt                 # ✅ KEEP - Python dependencies
├── .env                             # ✅ KEEP - Environment variables
└── ...
```

---

## 🚀 Quick Deletion Commands

### Option 1: Use the Cleanup Script (Recommended)

```bash
cd /Users/ayaangazali/ShieldNet
./cleanup_blockchain_files.sh
```

### Option 2: Manual Deletion

```bash
cd /Users/ayaangazali/ShieldNet

# Delete blockchain infrastructure
rm -rf blockchain_deployment/
rm -rf backend/contracts/

# Delete old threat stores
rm backend/app/services/onchain_threat_store.py
rm backend/app/services/local_threat_intel_store.py
rm backend/app/services/local_threat_store.py
rm backend/app/services/threat_intel_store.py
rm backend/app/services/blockchain_threat_intel.py
rm backend/app/services/shieldnet_contract_client.py

# Delete blockchain docs
rm backend/BLOCKCHAIN_*.md
rm backend/LOCAL_MODE_IMPLEMENTATION.md
rm backend/THREAT_INTEL_*.md

# Delete old tests
rm backend/test_blockchain.py
rm backend/test_local_threats.py

# Delete SQLite database
rm backend/shieldnet.db

# Delete redundant docs
rm BACKEND_IMPLEMENTATION_SUMMARY.md
rm INVOICE_PROCESSING_FEATURE.md
```

---

## ✅ Verify After Deletion

```bash
# Test that smart contracts still work
cd backend
python3 test_smart_contracts.py

# Should see:
# ✅ Utility function tests passed!
# ✅ Policy contract tests passed!
# ✅ Threat intelligence contract tests passed!
# ✅ Treasury contract tests passed!
# 🎉 Smart contract system working perfectly!
```

---

## 📊 Size Reduction

**Before cleanup:**
- ~50+ blockchain-related files
- SQLite database
- Hardhat infrastructure

**After cleanup:**
- 4 JSON files (`smart_contracts/`)
- 4 Python files (`backend/app/contracts/`)
- 1 test file
- 1 documentation file

**Total:** ~10 essential files for smart contracts system!

---

## 🎯 What You Get

After deletion, you'll have a **clean, standalone smart contracts system**:

1. **JSON-based contracts** (no blockchain needed)
2. **Python engine** to read/write contracts
3. **Full test suite** to verify everything works
4. **Complete documentation** for usage

Perfect for hackathons, demos, or production use! 🚀
