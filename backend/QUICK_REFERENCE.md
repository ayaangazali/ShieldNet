# 🎯 Quick Reference: Local vs Blockchain Mode

## Current Configuration (Demo-Ready)

```bash
# backend/.env
USE_ONCHAIN_THREATS=false  # ✅ Local-only mode
```

**Status:** ✅ Backend runs without blockchain dependencies  
**Ready for:** Demos, development, testing  
**Storage:** Local SQLite database  
**Setup Time:** 0 seconds  

---

## Mode Comparison

| Mode | Setup | Dependencies | Cost | Use Case |
|------|-------|--------------|------|----------|
| **Local-Only** (current) | ❌ None | SQLite only | Free | Demos, dev |
| **Blockchain** (optional) | ✅ Deploy contract | web3, Base RPC | ~$0.03/threat | Production |

---

## Switching Between Modes

### **Stay in Local-Only Mode (Current)**
```bash
# No changes needed! Already configured:
USE_ONCHAIN_THREATS=false
```

### **Enable Blockchain Mode (Future)**
```bash
# 1. Uncomment in requirements.txt
web3>=6.11.3
eth-account>=0.10.0

# 2. Install dependencies
pip install web3 eth-account

# 3. Update .env
USE_ONCHAIN_THREATS=true
BASE_RPC_URL=https://base-mainnet.g.alchemy.com/v2/YOUR_KEY
REPORTER_PRIVATE_KEY=0xYOUR_KEY
SHIELDNET_CONTRACT_ADDRESS=0xDEPLOYED_ADDRESS

# 4. Deploy contract
cd contracts
npx hardhat run scripts/deploy.js --network base

# 5. Restart backend
python3 -m uvicorn app.main:app --reload
```

---

## API Endpoints (Work in Both Modes)

### **Threat Analytics**
```bash
GET /api/threats/analytics
```
**Response:**
```json
{
  "total_threats": 0,
  "total_amount_saved": 0.0,
  "severity_breakdown": {},
  "recent_threats_7d": 0,
  "storage_type": "local",
  "blockchain_enabled": false  ← false = local, true = blockchain
}
```

### **List Threats**
```bash
GET /api/threats/list
```

### **Report Threat**
```bash
POST /api/threats/report
Content-Type: application/json
{
  "invoice_id": 1,
  "threat_type": "FRAUD",
  "severity": "high",
  "vendor_fingerprint": "vendor123",
  "description": "Suspicious invoice"
}
```

### **Query Network Threats**
```bash
POST /api/threats/query
Content-Type: application/json
{
  "vendor_fingerprint": "vendor123"
}
```

---

## Code Changes Summary

### **What Uses Local Storage**
- ✅ `local_threat_store.py` - New local storage module
- ✅ `threats.py` - Threat reporting endpoint
- ✅ `/api/threats/analytics` - Analytics dashboard
- ✅ `/api/threats/list` - List all threats
- ✅ `/api/threats/query` - Query threats by fingerprint

### **What's Behind Feature Flag**
- 🔒 `shieldnet_contract_client.py` - Only loads if `USE_ONCHAIN_THREATS=true`
- 🔒 web3 imports - Conditional import
- 🔒 Base RPC calls - Skipped if flag=false
- 🔒 Smart contract interactions - Disabled by default

---

## Logs to Watch

### **Local-Only Mode (Current)**
```
📊 Local-only threat storage enabled (no blockchain required)
📊 Blockchain client disabled (USE_ONCHAIN_THREATS=false)
✅ Threat saved to local store (fraud_score=92)
📈 Analytics: 5 threats, $45,000.00 saved
```

### **Blockchain Mode (When Enabled)**
```
🔗 Blockchain threat reporting enabled (Base mainnet)
✅ Blockchain client initialized with reporter: 0x...
🔗 Connected to Base mainnet for threat reporting
✅ Threat also reported to Base blockchain: 0xabc123...
```

---

## Troubleshooting

### **"Web3 not available" Warning**
```
⚠️  Web3 not available. USDC payment features will be disabled.
```
**Status:** ✅ Normal in local-only mode  
**Impact:** None - Locus payments still work (separate system)  
**Action:** No action needed for demos

### **Backend Won't Start**
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Reinstall dependencies
pip install -r requirements.txt

# Check .env exists
ls -la backend/.env

# Check USE_ONCHAIN_THREATS is false
grep USE_ONCHAIN_THREATS backend/.env
```

### **Threats Not Saving**
```bash
# Check database
ls -la backend/shieldnet.db

# Check logs
tail -f backend/logs/app.log

# Test analytics endpoint
curl http://127.0.0.1:8000/api/threats/analytics
```

---

## File Structure

```
backend/
├── .env                              ← USE_ONCHAIN_THREATS=false
├── requirements.txt                  ← web3 commented out
├── shieldnet.db                      ← Local threat storage
├── app/
│   ├── config.py                     ← Feature flag config
│   ├── routers/
│   │   └── threats.py                ← Local + optional blockchain
│   └── services/
│       ├── local_threat_store.py     ← NEW: Local storage
│       └── shieldnet_contract_client.py  ← Optional blockchain
└── docs/
    ├── LOCAL_MODE_IMPLEMENTATION.md  ← Full documentation
    └── QUICK_REFERENCE.md            ← This file
```

---

## Testing Checklist

- [x] Backend starts without errors
- [x] No blockchain RPC required
- [x] Threat analytics endpoint works
- [x] List threats endpoint works
- [x] Report threat endpoint works
- [x] Query threats endpoint works
- [x] No web3 import errors
- [x] Graceful fallback to local-only

**Status:** ✅ All tests passed!

---

## Key Files Changed

1. **`.env`** - Added `USE_ONCHAIN_THREATS=false`
2. **`config.py`** - Added feature flag setting
3. **`local_threat_store.py`** - NEW local storage module
4. **`threats.py`** - Conditional blockchain import
5. **`shieldnet_contract_client.py`** - Optional web3 loading
6. **`requirements.txt`** - web3 commented out

---

## Summary

✅ **Current Setup:** Local-only mode (perfect for demos)  
✅ **No blockchain needed:** Zero external dependencies  
✅ **Full functionality:** All features work locally  
✅ **Easy upgrade:** One flag to enable blockchain  
✅ **Zero cost:** No gas fees for local storage  

**Result: ShieldNet backend is demo-ready! 🚀**
