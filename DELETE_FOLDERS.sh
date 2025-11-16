#!/bin/bash

# DELETE THESE FOLDERS - NOT NEEDED FOR SMART CONTRACTS

echo "🗑️  DELETE THESE FOLDERS:"
echo ""

cd /Users/ayaangazali/ShieldNet

# Frontend (not needed)
if [ -d "src" ]; then
    echo "❌ src/ (frontend)"
fi

if [ -d "ShieldNet" ]; then
    echo "❌ ShieldNet/ (duplicate folder)"
fi

# Backend unnecessary folders
if [ -d "backend/alembic" ]; then
    echo "❌ backend/alembic/ (database migrations)"
fi

if [ -d "backend/logs" ]; then
    echo "❌ backend/logs/ (old logs)"
fi

if [ -d "backend/test_data" ]; then
    echo "❌ backend/test_data/ (test files)"
fi

if [ -d "backend/uploads" ]; then
    echo "❌ backend/uploads/ (uploaded files)"
fi

if [ -d "backend/venv" ]; then
    echo "❌ backend/venv/ (virtual environment)"
fi

if [ -d "venv" ]; then
    echo "❌ venv/ (virtual environment)"
fi

if [ -d "backend/app/routers" ]; then
    echo "❌ backend/app/routers/ (API endpoints - optional)"
fi

if [ -d "backend/app/schemas" ]; then
    echo "❌ backend/app/schemas/ (old schemas)"
fi

if [ -d "backend/app/services" ]; then
    echo "❌ backend/app/services/ (old services - EMPTY NOW)"
fi

echo ""
echo "✅ KEEP THESE FOLDERS:"
echo ""
echo "✅ smart_contracts/ (JSON contract data)"
echo "✅ backend/app/contracts/ (contract engine)"

echo ""
echo "Run this to delete all:"
echo ""
echo "cd /Users/ayaangazali/ShieldNet"
echo "rm -rf src/ ShieldNet/ venv/ backend/alembic/ backend/logs/ backend/test_data/ backend/uploads/ backend/venv/ backend/app/routers/ backend/app/schemas/ backend/app/services/"
echo ""
