# ShieldNet Backend

AI-powered invoice fraud detection and payment automation system built with FastAPI.

## 🚀 Quick Start (No Docker Required)

### 1. Setup
```bash
cd backend
./quickstart.sh
```

### 2. Configure
Edit `.env` file with your settings (use SQLite for easy start)

### 3. Initialize Database
```bash
source venv/bin/activate
python init_db.py
```

### 4. Run Server
```bash
./run.sh
```

**Access:** http://localhost:8000/docs

## 📋 Features

### Core Product Features
✅ **Invoice Intake Agent** - Upload/parse invoices (PDF/JSON) with auto-extraction  
✅ **Local Verification** - Cross-check against POs, contracts, and vendor data  
✅ **Network Fraud Check** - Compare against ShieldNet threat intelligence  
✅ **Risk Scoring** - Dual scoring: confidence (legit) + fraud (scammy)  
✅ **3-way Decision Engine** - Approve/Hold/Block classification  
✅ **Treasury Agent** - USDC payments via Locus wallet  
✅ **Policy-Based Auto-Pay** - Rules-driven payment automation  
✅ **Threat Intelligence** - Shared fraud detection network  
✅ **Analytics Dashboard** - Comprehensive reporting  
✅ **Mandates** - Company-level governance rules  

## 🏗️ Architecture

```
Frontend (React) → FastAPI Backend → PostgreSQL/SQLite
                         ↓
                   Business Logic:
                   • PDF Parser
                   • Verification
                   • Fraud Detection
                   • Treasury (Web3)
```

## � API Endpoints (34+)

### Invoice Processing
- `POST /api/invoices/upload` - Upload & analyze invoice
- `GET /api/invoices/` - List invoices
- `GET /api/invoices/{id}` - Get invoice details
- `POST /api/invoices/{id}/reanalyze` - Reanalyze

### Treasury & Payments
- `GET /api/treasury/overview` - Treasury dashboard
- `POST /api/treasury/pay/{id}` - Execute payment
- `POST /api/treasury/auto-pay` - Trigger auto-pay
- `GET /api/treasury/transactions` - Transaction history

### Threat Intelligence
- `POST /api/threats/report` - Report threat
- `POST /api/threats/query` - Query threats
- `POST /api/threats/{id}/share` - Share with network

### Analytics
- `GET /api/analytics/threats` - Threat analytics
- `GET /api/analytics/fraud-graph` - FraudGraph data
- `GET /api/analytics/dashboard-stats` - Dashboard stats

### Governance
- `POST /api/mandates/` - Create mandate
- `GET /api/mandates/` - List mandates
- `PUT /api/mandates/{id}` - Update mandate

### Vendor Management
- `POST /api/vendors/` - Create vendor
- `GET /api/vendors/` - List vendors
- `POST /api/vendors/purchase-orders` - Create PO
- `POST /api/vendors/contracts` - Create contract

## 💻 Technology Stack

- **Framework:** FastAPI 0.104.1
- **Database:** PostgreSQL 13+ or SQLite
- **ORM:** SQLAlchemy 2.0 (async)
- **Validation:** Pydantic 2.5
- **PDF Processing:** pdfplumber, PyPDF2, pytesseract
- **Blockchain:** Web3.py (for USDC payments)
- **Testing:** pytest

## � Installation

### Prerequisites
- Python 3.9+
- PostgreSQL (optional, can use SQLite)

### Automated Setup
```bash
cd backend
./quickstart.sh
```

### Manual Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit configuration

# Initialize database
python init_db.py

# Run server
uvicorn app.main:app --reload
```

## ⚙️ Configuration

Edit `.env` file:

### Database (Choose One)

**SQLite (Easy):**
```env
DATABASE_URL=sqlite:///./shieldnet.db
ASYNC_DATABASE_URL=sqlite+aiosqlite:///./shieldnet.db
```

**PostgreSQL (Recommended):**
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/shieldnet
ASYNC_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/shieldnet
```

### Security
```env
SECRET_KEY=your-secret-key-change-in-production
```

### Locus Wallet (USDC Payments)
```env
LOCUS_WALLET_ADDRESS=0x...
LOCUS_PRIVATE_KEY=your-private-key
USDC_CONTRACT_ADDRESS=0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
RPC_ENDPOINT=https://eth-mainnet.g.alchemy.com/v2/your-api-key
```

### CORS (Frontend)
```env
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

## 🗄️ Database Setup

### Using SQLite (Development)
No installation needed! Just set DATABASE_URL in `.env`:
```env
DATABASE_URL=sqlite:///./shieldnet.db
ASYNC_DATABASE_URL=sqlite+aiosqlite:///./shieldnet.db
```

### Using PostgreSQL (Production)

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
createdb shieldnet
```

**Ubuntu/Debian:**
```bash
sudo apt install postgresql
sudo systemctl start postgresql
sudo -u postgres createdb shieldnet
```

### Initialize Database
```bash
source venv/bin/activate
python init_db.py
```

This creates:
- All database tables
- Sample vendors
- Purchase orders
- Contracts
- Default mandates
- Treasury wallet

## 🚀 Running the Server

### Development Mode
```bash
./run.sh
```

Or manually:
```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📝 Usage Examples

### Upload Invoice
```bash
curl -X POST http://localhost:8000/api/invoices/upload \
  -F "file=@invoice.pdf" \
  -F "vendor_id=1"
```

### Get Treasury Overview
```bash
curl http://localhost:8000/api/treasury/overview
```

### Query Threats
```bash
curl -X POST http://localhost:8000/api/threats/query \
  -H "Content-Type: application/json" \
  -d '{"vendor_fingerprint": "vendor123"}'
```

## 🧪 Testing

```bash
source venv/bin/activate
pytest
```

## 📊 Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Settings
│   ├── database.py          # Database setup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── routers/             # API endpoints
│   │   ├── invoices.py
│   │   ├── treasury.py
│   │   ├── threats.py
│   │   ├── analytics.py
│   │   ├── mandates.py
│   │   └── vendors.py
│   └── services/            # Business logic
│       ├── pdf_parser.py
│       ├── verification.py
│       ├── fraud_detection.py
│       └── treasury.py
├── uploads/                 # Invoice uploads
├── logs/                    # Server logs
├── .env                     # Configuration
├── requirements.txt         # Dependencies
├── init_db.py              # Database init
├── quickstart.sh           # Setup script
└── run.sh                  # Run script
```

## � Security Features

- **CORS Protection** - Whitelist-based origin control
- **Input Validation** - Pydantic schema validation
- **SQL Injection Prevention** - SQLAlchemy ORM
- **Role Separation** - Analysis vs payment control
- **Mandate Policies** - Policy-based governance
- **Audit Logging** - Complete audit trail
- **JWT Ready** - Authentication infrastructure

## 🐛 Troubleshooting

### Port in Use
```bash
kill -9 $(lsof -ti:8000)
```

### Module Not Found
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Database Connection
- **SQLite:** Check DATABASE_URL in `.env`
- **PostgreSQL:** Verify PostgreSQL is running

### PDF Processing Issues
```bash
# macOS
brew install tesseract poppler

# Ubuntu
sudo apt install tesseract-ocr poppler-utils
```

## 📚 Documentation

- **[LOCAL_SETUP_GUIDE.md](LOCAL_SETUP_GUIDE.md)** - Comprehensive local setup
- **[API_INTEGRATION_GUIDE.md](API_INTEGRATION_GUIDE.md)** - Frontend integration
- **[API_QUICK_REFERENCE.md](API_QUICK_REFERENCE.md)** - Quick API reference
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[Interactive API Docs](http://localhost:8000/docs)** - Swagger UI
- **[Alternative Docs](http://localhost:8000/redoc)** - ReDoc

## 🔄 Common Workflows

### 1. Invoice Processing Flow
```
Upload PDF → Parse → Verify → Score → Decide → Store
```

### 2. Payment Flow
```
Approved Invoice → Check Mandates → Verify Balance → Execute Payment → Record Transaction
```

### 3. Threat Detection Flow
```
Blocked Invoice → Generate Fingerprints → Create Threat Report → Share with Network
```

## 🎯 Decision Logic

### Confidence Score (0-1)
- PO matched: +0.2
- Active contract: +0.15
- Trusted vendor: +0.25
- No duplicates: +0.1

### Fraud Score (0-1)
- Duplicate: +0.4
- PO mismatch: +0.25
- Untrusted vendor: +0.3
- Template threat: +0.35

### Decision
- **APPROVE:** confidence ≥ 0.85 AND fraud ≤ 0.15
- **BLOCK:** fraud ≥ 0.7 OR network threat
- **HOLD:** Everything else

## 🌐 Frontend Integration

The backend provides RESTful APIs for the React frontend.

Example connection:
```typescript
const response = await fetch('http://localhost:8000/api/invoices/upload', {
  method: 'POST',
  body: formData
});
```

See [API_INTEGRATION_GUIDE.md](API_INTEGRATION_GUIDE.md) for complete examples.

## 📈 Performance

- **Async Operations** - Non-blocking I/O
- **Connection Pooling** - SQLAlchemy async pool
- **Indexed Queries** - Optimized database queries
- **Pagination** - All list endpoints support pagination

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Run tests
5. Submit pull request

## 📄 License

MIT License

## 🆘 Support

- **Documentation:** Check `docs/` folder
- **API Docs:** http://localhost:8000/docs
- **Issues:** Create GitHub issue
- **Email:** support@shieldnet.com

## ✅ Verification Checklist

- [ ] Python 3.9+ installed
- [ ] Dependencies installed (`./quickstart.sh`)
- [ ] `.env` configured
- [ ] Database initialized (`python init_db.py`)
- [ ] Server starts (`./run.sh`)
- [ ] API docs accessible (http://localhost:8000/docs)
- [ ] Health check passes (http://localhost:8000/health)

## 🚀 Quick Commands

```bash
# Setup
./quickstart.sh

# Initialize DB
python init_db.py

# Run server
./run.sh

# Run tests
pytest

# Check health
curl http://localhost:8000/health
```

---

**Ready to start!** Run `./run.sh` and visit http://localhost:8000/docs 🚀

### Using Docker Compose
```bash
docker-compose up -d
```

## 📊 Database Schema

Key tables:
- `invoices` - Invoice records with scores and decisions
- `vendors` - Vendor information and risk scores
- `purchase_orders` - Purchase orders for verification
- `contracts` - Vendor contracts
- `threat_reports` - Blocked invoice fingerprints
- `transactions` - USDC payment transactions
- `mandates` - Policy rules for auto-pay/hold/block
- `treasury_wallets` - Locus wallet information
- `audit_logs` - Audit trail

## 🤝 Integration with Frontend

The backend exposes RESTful APIs that the React frontend consumes:

1. Frontend uploads invoice via `/api/invoices/upload`
2. Backend parses, verifies, scores, and decides
3. Frontend displays results in real-time
4. Treasury dashboard shows wallet balance and stats
5. Analytics pages query `/api/analytics/*` endpoints

## 📝 Development Workflow

1. **Invoice Processing Flow**
   ```
   Upload → Parse → Verify → Score → Decide → (Auto-Pay or Hold)
   ```

2. **Payment Flow**
   ```
   Approved Invoice → Check Mandates → Treasury Agent → Execute Payment → Record Transaction
   ```

3. **Threat Detection Flow**
   ```
   Blocked Invoice → Generate Fingerprint → Create Threat Report → Share with Network
   ```

## 🐛 Troubleshooting

**Database connection errors:**
- Check PostgreSQL is running
- Verify DATABASE_URL in .env

**PDF parsing issues:**
- Ensure pytesseract is installed
- Install system dependencies: `apt-get install tesseract-ocr poppler-utils`

**Web3 connection errors:**
- Verify RPC_ENDPOINT is correct
- Check private key format

## 📄 License

Proprietary - ShieldNet Inc.

## 👥 Team

Built for the ShieldNet Invoice Protection Platform
