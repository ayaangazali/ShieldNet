# ShieldNet Backend - Local Setup Guide (No Docker)

This guide will help you set up and run the ShieldNet backend on your local machine without Docker.

## 📋 Prerequisites

### Required
- **Python 3.9+** - [Download Python](https://www.python.org/downloads/)
- **pip** - Usually comes with Python
- **Git** - For cloning the repository

### Optional but Recommended
- **PostgreSQL 13+** - [Download PostgreSQL](https://www.postgresql.org/download/)
  - Alternative: SQLite (included with Python, easier but less performant)

## 🚀 Quick Start (3 Steps)

### Step 1: Run Setup Script

```bash
cd backend
./quickstart.sh
```

This script will:
- Check Python installation
- Create a virtual environment
- Install all dependencies
- Create `.env` configuration file
- Create necessary directories

### Step 2: Configure Environment

Edit the `.env` file:

```bash
nano .env  # or use your preferred editor
```

**For SQLite (Easiest - No PostgreSQL needed):**
```env
DATABASE_URL=sqlite:///./shieldnet.db
ASYNC_DATABASE_URL=sqlite+aiosqlite:///./shieldnet.db
```

**For PostgreSQL (Recommended for production):**
```env
DATABASE_URL=postgresql://yourusername:yourpassword@localhost:5432/shieldnet
ASYNC_DATABASE_URL=postgresql+asyncpg://yourusername:yourpassword@localhost:5432/shieldnet
```

Other important settings:
```env
# Security
SECRET_KEY=your-secret-key-here-change-this

# Locus Wallet (for USDC payments)
LOCUS_WALLET_ADDRESS=0x...
LOCUS_PRIVATE_KEY=your-private-key-here
```

### Step 3: Initialize Database

```bash
source venv/bin/activate
python init_db.py
```

This will create all tables and seed sample data.

### Step 4: Start the Server

```bash
./run.sh
```

Or manually:
```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Access the API:**
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## 📝 Detailed Setup Instructions

### Installing PostgreSQL (Optional)

**macOS (Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15
createdb shieldnet
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb shieldnet
```

**Windows:**
Download from [postgresql.org](https://www.postgresql.org/download/windows/) and use pgAdmin to create database.

### Virtual Environment Setup

If `quickstart.sh` doesn't work, manual setup:

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Environment Variables

Copy and customize the `.env` file:

```bash
cp .env.example .env
```

Key configurations:

```env
# Database - Choose one:
# SQLite (Easy)
DATABASE_URL=sqlite:///./shieldnet.db
ASYNC_DATABASE_URL=sqlite+aiosqlite:///./shieldnet.db

# PostgreSQL (Production)
DATABASE_URL=postgresql://user:pass@localhost:5432/shieldnet
ASYNC_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/shieldnet

# Security
SECRET_KEY=generate-a-long-random-string-here
ALGORITHM=HS256

# Locus Wallet
LOCUS_WALLET_ADDRESS=0x1234567890abcdef1234567890abcdef12345678
LOCUS_PRIVATE_KEY=your-ethereum-private-key
USDC_CONTRACT_ADDRESS=0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
RPC_ENDPOINT=https://eth-mainnet.g.alchemy.com/v2/your-api-key

# CORS (Frontend URLs)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# File Upload
MAX_UPLOAD_SIZE=10485760
UPLOAD_DIR=./uploads

# Fraud Detection
HIGH_CONFIDENCE_THRESHOLD=0.85
LOW_FRAUD_THRESHOLD=0.15
AUTO_PAY_MAX_AMOUNT=2000
```

## 🔧 Common Commands

### Start Server
```bash
./run.sh
# or
uvicorn app.main:app --reload
```

### Initialize Database
```bash
python init_db.py
```

### Run Tests (when implemented)
```bash
pytest
```

### Check Dependencies
```bash
pip list
```

### Update Dependencies
```bash
pip install --upgrade -r requirements.txt
```

## 📊 Testing the API

### Using Interactive Docs
Visit http://localhost:8000/docs and use the built-in interface to test endpoints.

### Using cURL

**Upload Invoice:**
```bash
curl -X POST http://localhost:8000/api/invoices/upload \
  -F "file=@test_invoice.pdf" \
  -F "vendor_id=1"
```

**Get Treasury Overview:**
```bash
curl http://localhost:8000/api/treasury/overview
```

**Get Threat Analytics:**
```bash
curl http://localhost:8000/api/analytics/threats
```

### Using Frontend
If you have the React frontend running:
1. Start backend: `./run.sh`
2. Start frontend: `npm run dev` (in frontend directory)
3. Frontend will connect to backend automatically

## 🗄️ Database Management

### SQLite (Development)

**Pros:**
- No installation needed
- Easy to set up
- Perfect for development/testing
- Single file database

**Cons:**
- Less performant than PostgreSQL
- Limited concurrent write support

**Location:** `shieldnet.db` file in backend directory

**View data:**
```bash
sqlite3 shieldnet.db
.tables
SELECT * FROM invoices;
.quit
```

### PostgreSQL (Production)

**Pros:**
- Better performance
- Concurrent connections
- Advanced features
- Production-ready

**Cons:**
- Requires installation
- More complex setup

**Connect:**
```bash
psql -d shieldnet
\dt  # List tables
SELECT * FROM invoices;
\q
```

### Reset Database

**SQLite:**
```bash
rm shieldnet.db
python init_db.py
```

**PostgreSQL:**
```bash
dropdb shieldnet
createdb shieldnet
python init_db.py
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -ti:8000

# Kill it
kill -9 $(lsof -ti:8000)
```

### Module Not Found Errors
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Database Connection Errors

**SQLite:** Check file permissions and DATABASE_URL in `.env`

**PostgreSQL:**
- Check PostgreSQL is running: `brew services list` (macOS)
- Test connection: `psql -d shieldnet`
- Verify credentials in `.env`

### ImportError for pdfplumber
```bash
# Install system dependencies (macOS)
brew install tesseract poppler

# Ubuntu/Debian
sudo apt install tesseract-ocr poppler-utils
```

### Web3 Connection Errors
- Verify RPC_ENDPOINT is set correctly in `.env`
- Check Alchemy/Infura API key is valid
- Test with a public RPC endpoint first

## 🔒 Security Notes

### For Development
- Use SQLite
- Keep SECRET_KEY simple
- Mock Locus wallet (use test keys)

### For Production
- Use PostgreSQL
- Generate strong SECRET_KEY: `openssl rand -hex 32`
- Never commit `.env` file
- Use environment variables
- Enable HTTPS
- Set DEBUG=False

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py          # FastAPI app
│   ├── models.py        # Database models
│   ├── schemas.py       # Pydantic schemas
│   ├── routers/         # API endpoints
│   └── services/        # Business logic
├── uploads/             # Invoice files
├── logs/               # Server logs
├── venv/               # Virtual environment
├── .env                # Configuration (create this)
├── requirements.txt    # Dependencies
├── init_db.py         # Database setup
├── quickstart.sh      # Setup script
└── run.sh             # Run script
```

## 🎯 Next Steps

1. ✅ Set up environment
2. ✅ Start server
3. 📱 Connect frontend
4. 🧪 Test API endpoints
5. 📊 Upload test invoices
6. 💰 Configure Locus wallet
7. 🚀 Deploy to production

## 📚 Additional Resources

- **API Documentation:** http://localhost:8000/docs
- **Integration Guide:** See `API_INTEGRATION_GUIDE.md`
- **Architecture:** See `ARCHITECTURE.md`
- **API Reference:** See `API_QUICK_REFERENCE.md`

## 💡 Tips

- Use SQLite for quick testing
- Switch to PostgreSQL for serious development
- Keep virtual environment activated when working
- Use `./run.sh` for easy server start
- Check logs in `logs/` directory for debugging
- Use interactive API docs at `/docs` for testing

## 🆘 Getting Help

If you encounter issues:
1. Check this guide's troubleshooting section
2. Review error messages in terminal
3. Check `logs/shieldnet.log` for server logs
4. Verify all environment variables in `.env`
5. Ensure database is created and initialized

## ✅ Verification Checklist

- [ ] Python 3.9+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] `.env` file configured
- [ ] Database created (SQLite or PostgreSQL)
- [ ] Database initialized with `init_db.py`
- [ ] Server starts without errors
- [ ] Can access http://localhost:8000/docs
- [ ] Health check passes: http://localhost:8000/health

---

**Ready to start!** Run `./run.sh` and visit http://localhost:8000/docs to explore the API! 🚀
