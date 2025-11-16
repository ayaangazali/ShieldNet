#!/bin/bash

# ShieldNet Backend Setup Script (No Docker Required)

set -e

echo "================================================"
echo "ShieldNet Backend Setup (Local Development)"
echo "================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

echo "✓ pip found"

# Check if PostgreSQL is installed (optional but recommended)
if command -v psql &> /dev/null; then
    echo "✓ PostgreSQL found: $(psql --version | head -n 1)"
else
    echo "⚠️  PostgreSQL not found. You'll need PostgreSQL to run the backend."
    echo "   Install with: brew install postgresql (on macOS)"
    echo "   Or use SQLite by modifying the DATABASE_URL in .env"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing Python dependencies (this may take a few minutes)..."
pip install -r requirements.txt

echo "✓ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo "⚠️  IMPORTANT: Edit .env file with your configuration before running"
else
    echo "✓ .env file already exists"
fi

# Create uploads directory
mkdir -p uploads
echo "✓ Uploads directory created"

# Check if database exists
echo ""
echo "Checking PostgreSQL setup..."
if command -v psql &> /dev/null; then
    if psql -lqt | cut -d \| -f 1 | grep -qw shieldnet; then
        echo "✓ Database 'shieldnet' exists"
    else
        echo "⚠️  Database 'shieldnet' not found"
        read -p "Do you want to create it now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            createdb shieldnet
            echo "✓ Database 'shieldnet' created"
        else
            echo "  You can create it later with: createdb shieldnet"
        fi
    fi
fi

echo ""
echo "================================================"
echo "Setup completed successfully!"
echo "================================================"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Configure your environment:"
echo "   nano .env  (or use your preferred editor)"
echo "   - Set DATABASE_URL to your PostgreSQL connection"
echo "   - Set LOCUS_WALLET_ADDRESS and LOCUS_PRIVATE_KEY"
echo "   - Configure other settings as needed"
echo ""
echo "2. Initialize the database with sample data:"
echo "   source venv/bin/activate"
echo "   python init_db.py"
echo ""
echo "3. Start the development server:"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "4. Access the API:"
echo "   • API Base: http://localhost:8000"
echo "   • Interactive Docs: http://localhost:8000/docs"
echo "   • Alternative Docs: http://localhost:8000/redoc"
echo "   • Health Check: http://localhost:8000/health"
echo ""
echo "💡 Quick commands:"
echo "   • Start server: ./run.sh"
echo "   • Run tests: pytest"
echo "   • Check logs: tail -f logs/shieldnet.log"
echo ""
echo "📚 Documentation:"
echo "   • README.md - Complete setup guide"
echo "   • API_INTEGRATION_GUIDE.md - Frontend integration"
echo "   • ARCHITECTURE.md - System architecture"
echo ""
