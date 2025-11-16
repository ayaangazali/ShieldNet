#!/usr/bin/env python3
"""
ShieldNet Backend Initialization Script

This script sets up the database and creates initial data for the ShieldNet backend.
"""

import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from app.database import Base
from app.models import (
    Vendor, PurchaseOrder, Contract, Mandate, TreasuryWallet, InvoiceProcessing
)
from app.config import settings

async def init_database():
    """Initialize database with tables"""
    print("Creating database tables...")
    
    # Create async engine
    engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Drop all tables (WARNING: This will delete all data!)
        # Comment out in production
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✓ Database tables created successfully")
    
    await engine.dispose()

async def seed_initial_data():
    """Seed database with initial test data"""
    print("\nSeeding initial data...")
    
    from app.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        # Create trusted vendors
        vendors_data = [
            {
                "name": "Acme Corporation",
                "email": "billing@acme.com",
                "phone": "+1-555-0100",
                "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
                "is_trusted": True,
                "risk_score": 0.1
            },
            {
                "name": "TechSupply Inc",
                "email": "invoices@techsupply.com",
                "phone": "+1-555-0200",
                "wallet_address": "0xabcdef1234567890abcdef1234567890abcdef12",
                "is_trusted": True,
                "risk_score": 0.15
            },
            {
                "name": "Global Services LLC",
                "email": "accounts@globalservices.com",
                "phone": "+1-555-0300",
                "wallet_address": "0x9876543210fedcba9876543210fedcba98765432",
                "is_trusted": True,
                "risk_score": 0.2
            },
            {
                "name": "Unknown Vendor Co",
                "email": "contact@unknown.com",
                "is_trusted": False,
                "risk_score": 0.7
            }
        ]
        
        vendors = []
        for vendor_data in vendors_data:
            vendor = Vendor(**vendor_data)
            db.add(vendor)
            vendors.append(vendor)
        
        await db.flush()
        print(f"✓ Created {len(vendors)} vendors")
        
        # Create purchase orders
        pos_data = [
            {
                "po_number": "PO-2024-001",
                "vendor_id": vendors[0].id,
                "amount": 5000.0,
                "currency": "USDC",
                "description": "Software licenses for Q1",
                "issue_date": datetime.now(),
                "expiry_date": datetime.now() + timedelta(days=90),
                "is_active": True
            },
            {
                "po_number": "PO-2024-002",
                "vendor_id": vendors[1].id,
                "amount": 3500.0,
                "currency": "USDC",
                "description": "Hardware equipment",
                "issue_date": datetime.now(),
                "expiry_date": datetime.now() + timedelta(days=60),
                "is_active": True
            }
        ]
        
        for po_data in pos_data:
            po = PurchaseOrder(**po_data)
            db.add(po)
        
        await db.flush()
        print(f"✓ Created {len(pos_data)} purchase orders")
        
        # Create contracts
        contracts_data = [
            {
                "contract_number": "CONTRACT-2024-A",
                "vendor_id": vendors[0].id,
                "value": 50000.0,
                "currency": "USDC",
                "description": "Annual software maintenance",
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=365),
                "is_active": True
            },
            {
                "contract_number": "CONTRACT-2024-B",
                "vendor_id": vendors[1].id,
                "value": 30000.0,
                "currency": "USDC",
                "description": "Quarterly hardware supply",
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=90),
                "is_active": True
            }
        ]
        
        for contract_data in contracts_data:
            contract = Contract(**contract_data)
            db.add(contract)
        
        await db.flush()
        print(f"✓ Created {len(contracts_data)} contracts")
        
        # Create default mandates
        mandates_data = [
            {
                "name": "Auto-pay small trusted invoices",
                "description": "Automatically pay invoices ≤ $2000 from trusted vendors",
                "rule_type": "auto_pay",
                "max_amount": 2000.0,
                "min_confidence_score": 0.85,
                "max_fraud_score": 0.15,
                "require_trusted_vendor": True,
                "priority": 100,
                "is_active": True
            },
            {
                "name": "Block unknown vendors",
                "description": "Block all invoices from untrusted vendors",
                "rule_type": "block",
                "require_trusted_vendor": True,
                "priority": 200,
                "is_active": False  # Disabled by default
            },
            {
                "name": "Hold high-amount invoices",
                "description": "Hold invoices over $10,000 for manual review",
                "rule_type": "hold",
                "max_amount": 10000.0,
                "priority": 50,
                "is_active": True
            }
        ]
        
        for mandate_data in mandates_data:
            mandate = Mandate(**mandate_data)
            db.add(mandate)
        
        await db.flush()
        print(f"✓ Created {len(mandates_data)} mandates")
        
        # Create treasury wallet
        if settings.LOCUS_WALLET_ADDRESS:
            wallet = TreasuryWallet(
                name="Main Treasury Wallet",
                wallet_address=settings.LOCUS_WALLET_ADDRESS,
                balance=0.0,  # Will be updated from blockchain
                currency="USDC",
                is_active=True
            )
            db.add(wallet)
            await db.flush()
            print("✓ Created treasury wallet")
        
        await db.commit()
        print("\n✓ Initial data seeded successfully!")

async def main():
    """Main initialization function"""
    print("=" * 60)
    print("ShieldNet Backend Initialization")
    print("=" * 60)
    
    try:
        # Initialize database
        await init_database()
        
        # Seed initial data
        await seed_initial_data()
        
        print("\n" + "=" * 60)
        print("Initialization completed successfully!")
        print("=" * 60)
        print("\nYou can now start the server with:")
        print("  uvicorn app.main:app --reload")
        print("\nAPI Documentation will be available at:")
        print("  http://localhost:8000/docs")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
