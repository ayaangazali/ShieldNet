# ShieldNet API Quick Reference

## 🚀 Base URL
```
http://localhost:8000
```

## 📋 Quick Reference

### Invoice Intake
```bash
# Upload Invoice (PDF/JSON)
POST /api/invoices/upload
Content-Type: multipart/form-data
Body: file, vendor_id (optional), vendor_name (optional)

# List Invoices
GET /api/invoices?status=pending&vendor_id=1&skip=0&limit=100

# Get Invoice
GET /api/invoices/{id}

# Reanalyze Invoice
POST /api/invoices/{id}/reanalyze
```

### Treasury & Payments
```bash
# Get Treasury Overview
GET /api/treasury/overview

# Pay Invoice
POST /api/treasury/pay/{invoice_id}?force=false

# Trigger Auto-Pay
POST /api/treasury/auto-pay

# Get Transactions
GET /api/treasury/transactions?skip=0&limit=100

# Get Wallet Balance
GET /api/treasury/balance
```

### Threat Intelligence
```bash
# Report Threat
POST /api/threats/report
Body: {
  "invoice_id": 1,
  "threat_type": "fake_vendor",
  "severity": "high",
  "vendor_fingerprint": "abc123",
  "template_fingerprint": "def456",
  "description": "Suspicious invoice",
  "indicators": ["red_flag_1"],
  "amount_saved": 5000.0
}

# Query Threats
POST /api/threats/query
Body: {
  "vendor_fingerprint": "abc123",
  "wallet_address": "0x...",
  "template_hash": "def456"
}

# List Threats
GET /api/threats/list?severity=high&skip=0&limit=100

# Share Threat
POST /api/threats/{id}/share
```

### Analytics
```bash
# Threat Analytics
GET /api/analytics/threats

# Fraud Graph
GET /api/analytics/fraud-graph

# Transaction History
GET /api/analytics/transactions?status=paid&skip=0&limit=100

# Dashboard Stats
GET /api/analytics/dashboard-stats
```

### Mandates
```bash
# Create Mandate
POST /api/mandates
Body: {
  "name": "Auto-pay small invoices",
  "rule_type": "auto_pay",
  "max_amount": 2000,
  "min_confidence_score": 0.85,
  "max_fraud_score": 0.15,
  "require_trusted_vendor": true,
  "priority": 100
}

# List Mandates
GET /api/mandates?rule_type=auto_pay&active_only=true

# Get Mandate
GET /api/mandates/{id}

# Update Mandate
PUT /api/mandates/{id}

# Delete Mandate
DELETE /api/mandates/{id}

# Toggle Mandate
POST /api/mandates/{id}/toggle

# Get Templates
GET /api/mandates/templates/auto-pay
GET /api/mandates/templates/block-unknown
GET /api/mandates/templates/hold-high-amount
```

### Vendor Management
```bash
# Create Vendor
POST /api/vendors
Body: {
  "name": "Acme Corp",
  "email": "billing@acme.com",
  "wallet_address": "0x...",
  "is_trusted": true
}

# List Vendors
GET /api/vendors?trusted_only=true&skip=0&limit=100

# Get Vendor
GET /api/vendors/{id}

# Update Vendor
PUT /api/vendors/{id}

# Get Vendor Invoices
GET /api/vendors/{id}/invoices

# Create Purchase Order
POST /api/vendors/purchase-orders
Body: {
  "po_number": "PO-2024-001",
  "vendor_id": 1,
  "amount": 5000,
  "description": "Software licenses"
}

# List Purchase Orders
GET /api/vendors/purchase-orders?vendor_id=1&active_only=true

# Create Contract
POST /api/vendors/contracts
Body: {
  "contract_number": "CONTRACT-2024-A",
  "vendor_id": 1,
  "value": 50000,
  "description": "Annual maintenance"
}

# List Contracts
GET /api/vendors/contracts?vendor_id=1&active_only=true
```

## 📊 Response Examples

### Invoice Upload Response
```json
{
  "id": 1,
  "invoice_number": "INV-2024-001",
  "vendor_id": 1,
  "amount": 1500.0,
  "currency": "USDC",
  "status": "approved",
  "confidence_score": 0.92,
  "fraud_score": 0.08,
  "decision": "approve",
  "decision_reason": "High confidence, low fraud risk",
  "po_matched": true,
  "contract_matched": true,
  "vendor_verified": true,
  "verification_details": { ... },
  "fraud_indicators": [],
  "recommendation": "Safe to pay"
}
```

### Treasury Overview Response
```json
{
  "wallet_address": "0x123...",
  "balance": 100000.0,
  "currency": "USDC",
  "total_paid": 45000.0,
  "total_held": 5000.0,
  "total_blocked": 12000.0,
  "risk_prevented": 12000.0,
  "pending_invoices": 3,
  "approved_invoices": 2
}
```

### Threat Analytics Response
```json
{
  "total_blocked_amount": 12000.0,
  "total_threats": 8,
  "threats_by_type": {
    "fake_vendor": 3,
    "duplicate_invoice": 2,
    "amount_anomaly": 3
  },
  "threats_by_severity": {
    "high": 4,
    "medium": 3,
    "low": 1
  },
  "top_risky_vendors": [
    {
      "id": 10,
      "name": "Suspicious Co",
      "risk_score": 0.85,
      "blocked_count": 3,
      "total_blocked": 8000.0
    }
  ]
}
```

## 🔑 Decision Logic

### Confidence Score (0-1)
- **Base**: 0.5
- **+0.2**: PO matched
- **+0.15**: Active contract
- **+0.25**: Trusted vendor
- **+0.1**: No duplicates
- **+0.1**: Amount reasonable
- **-0.2**: High vendor risk

### Fraud Score (0-1)
- **+0.4**: Duplicate invoice
- **+0.25**: PO mismatch
- **+0.3**: Untrusted vendor
- **+0.2**: Amount anomaly
- **+0.35**: Template threat
- **+0.4**: Wallet threat

### Decision Types
- **APPROVE**: confidence ≥ 0.85 AND fraud ≤ 0.15
- **BLOCK**: fraud ≥ 0.7 OR network threat OR duplicate
- **HOLD**: Everything else

## 🛡️ Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request
- **404**: Not Found
- **422**: Validation Error
- **500**: Server Error

## 🔧 Common Operations

### Upload and Process Invoice
```bash
curl -X POST http://localhost:8000/api/invoices/upload \
  -F "file=@invoice.pdf" \
  -F "vendor_id=1"
```

### Execute Payment
```bash
curl -X POST http://localhost:8000/api/treasury/pay/1
```

### Get Dashboard Data
```bash
curl http://localhost:8000/api/analytics/dashboard-stats
```

### Create Auto-Pay Mandate
```bash
curl -X POST http://localhost:8000/api/mandates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Auto-pay trusted small invoices",
    "rule_type": "auto_pay",
    "max_amount": 2000,
    "min_confidence_score": 0.85,
    "require_trusted_vendor": true,
    "priority": 100
  }'
```

## 📱 Frontend Integration

```typescript
// Upload invoice
const formData = new FormData();
formData.append('file', file);
formData.append('vendor_id', '1');

const response = await fetch('http://localhost:8000/api/invoices/upload', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result.decision); // approve, hold, or block
```

## 🎯 Key Features

✅ PDF/JSON invoice parsing  
✅ PO & contract verification  
✅ Network fraud detection  
✅ Risk scoring (confidence + fraud)  
✅ 3-way decisions (Approve/Hold/Block)  
✅ USDC payments via Locus  
✅ Auto-pay with mandates  
✅ Threat intelligence sharing  
✅ Analytics & reporting  
✅ Policy governance  

## 🚀 Getting Started

1. Start server: `uvicorn app.main:app --reload`
2. Visit docs: `http://localhost:8000/docs`
3. Upload invoice: Use `/api/invoices/upload`
4. View results: Check analytics endpoints

## 📞 Support

- API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health Check: `http://localhost:8000/health`
