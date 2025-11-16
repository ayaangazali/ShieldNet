#!/bin/bash

# ShieldNet Smart Contracts Cleanup Script
# This script removes ALL files not needed for the smart contracts system
# Keeping ONLY: smart_contracts/ folder and backend/app/contracts/ engine

echo "🧹 ShieldNet Smart Contracts Cleanup"
echo "===================================="
echo ""
echo "This will DELETE all blockchain-related files and keep only:"
echo "  ✅ smart_contracts/ (JSON contract data)"
echo "  ✅ backend/app/contracts/ (contract engine)"
echo "  ✅ backend/test_smart_contracts.py (tests)"
echo "  ✅ SMART_CONTRACTS_IMPLEMENTATION.md (docs)"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Cancelled."
    exit 1
fi

cd /Users/ayaangazali/ShieldNet

echo ""
echo "🗑️  Deleting blockchain/Hardhat files..."

# Delete entire blockchain_deployment folder
if [ -d "blockchain_deployment" ]; then
    rm -rf blockchain_deployment/
    echo "  ✓ Deleted blockchain_deployment/"
fi

# Delete backend/contracts (Hardhat)
if [ -d "backend/contracts" ]; then
    rm -rf backend/contracts/
    echo "  ✓ Deleted backend/contracts/ (Hardhat)"
fi

echo ""
echo "🗑️  Deleting old threat intelligence implementations..."

# Delete old threat store files
if [ -f "backend/app/services/onchain_threat_store.py" ]; then
    rm backend/app/services/onchain_threat_store.py
    echo "  ✓ Deleted onchain_threat_store.py"
fi

if [ -f "backend/app/services/local_threat_intel_store.py" ]; then
    rm backend/app/services/local_threat_intel_store.py
    echo "  ✓ Deleted local_threat_intel_store.py"
fi

if [ -f "backend/app/services/local_threat_store.py" ]; then
    rm backend/app/services/local_threat_store.py
    echo "  ✓ Deleted local_threat_store.py"
fi

if [ -f "backend/app/services/threat_intel_store.py" ]; then
    rm backend/app/services/threat_intel_store.py
    echo "  ✓ Deleted threat_intel_store.py"
fi

if [ -f "backend/app/services/blockchain_threat_intel.py" ]; then
    rm backend/app/services/blockchain_threat_intel.py
    echo "  ✓ Deleted blockchain_threat_intel.py"
fi

if [ -f "backend/app/services/shieldnet_contract_client.py" ]; then
    rm backend/app/services/shieldnet_contract_client.py
    echo "  ✓ Deleted shieldnet_contract_client.py"
fi

echo ""
echo "🗑️  Deleting blockchain documentation files..."

# Delete blockchain docs
blockchain_docs=(
    "backend/BLOCKCHAIN_INTEGRATION_GUIDE.md"
    "backend/BLOCKCHAIN_INTEGRATION_SUMMARY.md"
    "backend/BLOCKCHAIN_README.md"
    "backend/BLOCKCHAIN_TEST_RESULTS.md"
    "backend/LOCAL_MODE_IMPLEMENTATION.md"
    "backend/THREAT_INTEL_QUICK_REF.md"
    "backend/THREAT_INTEL_README.md"
)

for doc in "${blockchain_docs[@]}"; do
    if [ -f "$doc" ]; then
        rm "$doc"
        echo "  ✓ Deleted $(basename $doc)"
    fi
done

echo ""
echo "🗑️  Deleting blockchain test files..."

if [ -f "backend/test_blockchain.py" ]; then
    rm backend/test_blockchain.py
    echo "  ✓ Deleted test_blockchain.py"
fi

if [ -f "backend/test_local_threats.py" ]; then
    rm backend/test_local_threats.py
    echo "  ✓ Deleted test_local_threats.py"
fi

echo ""
echo "🗑️  Cleaning up SQLite database (old threat storage)..."

if [ -f "backend/shieldnet.db" ]; then
    rm backend/shieldnet.db
    echo "  ✓ Deleted shieldnet.db"
fi

echo ""
echo "🗑️  Deleting unused documentation files..."

# Delete redundant docs (keep only SMART_CONTRACTS_IMPLEMENTATION.md)
old_docs=(
    "BACKEND_IMPLEMENTATION_SUMMARY.md"
    "INVOICE_PROCESSING_FEATURE.md"
)

for doc in "${old_docs[@]}"; do
    if [ -f "$doc" ]; then
        rm "$doc"
        echo "  ✓ Deleted $doc"
    fi
done

echo ""
echo "✅ Cleanup Complete!"
echo ""
echo "📁 Remaining structure:"
echo ""
echo "ShieldNet/"
echo "├── smart_contracts/                   # ✅ JSON contract data"
echo "│   ├── PolicyContract.json"
echo "│   ├── ThreatIntelContract.json"
echo "│   ├── TreasuryContract.json"
echo "│   └── README.md"
echo "├── backend/"
echo "│   ├── app/"
echo "│   │   └── contracts/                 # ✅ Contract engine"
echo "│   │       ├── __init__.py"
echo "│   │       ├── contract_engine.py"
echo "│   │       ├── models.py"
echo "│   │       └── utils.py"
echo "│   ├── test_smart_contracts.py        # ✅ Tests"
echo "│   └── requirements.txt               # ✅ Dependencies"
echo "└── SMART_CONTRACTS_IMPLEMENTATION.md  # ✅ Documentation"
echo ""
echo "🎉 Smart contracts system is now standalone!"
echo ""
echo "To verify everything works:"
echo "  cd backend"
echo "  python3 test_smart_contracts.py"
echo ""
