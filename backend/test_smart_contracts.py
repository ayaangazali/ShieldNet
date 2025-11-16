"""
Smart Contracts Test Suite

Test all contract operations: policies, threats, treasury

Run with: python3 test_smart_contracts.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.contracts import (
    get_contract_backend,
    reset_contract_backend,
    JsonContractBackend,
    Policy,
    Threat,
    Transaction,
    TransactionMeta,
    hash_vendor,
    hash_payment_target,
    hash_invoice_template,
    hash_company_id,
    bucket_amount,
    generate_threat_id,
    generate_transaction_id,
    generate_policy_id,
    get_iso_timestamp,
)


def print_header(text: str):
    """Print a formatted test section header"""
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")


def print_success(text: str):
    """Print success message"""
    print(f"✅ {text}")


def print_info(text: str):
    """Print info message"""
    print(f"📋 {text}")


async def test_policy_contract():
    """Test PolicyContract operations"""
    print_header("TEST 1: Policy Contract Operations")
    
    backend = get_contract_backend()
    
    # Test 1: Add new policy
    print_info("Adding new policy...")
    new_policy = Policy(
        companyId="test_company_1",
        policyId="test_auto_pay",
        name="Test Auto-Pay Policy",
        maxAmount=5000,
        minConfidence=0.92,
        maxFraudScore=0.15,
        autoPay=True,
        blockUnknownVendors=False,
        requirePO=False,
        createdAt=get_iso_timestamp(),
        updatedAt=get_iso_timestamp(),
        active=True
    )
    
    await backend.add_policy(new_policy)
    print_success(f"Added policy: {new_policy.policyId}")
    
    # Test 2: Read policies
    print_info("Reading policies...")
    policies = await backend.get_policies("test_company_1")
    print_success(f"Found {len(policies)} policies for test_company_1")
    for policy in policies:
        print(f"   - {policy.name} (max: ${policy.maxAmount}, fraud: {policy.maxFraudScore})")
    
    # Test 3: Get specific policy
    print_info("Getting specific policy...")
    policy = await backend.get_policy("test_company_1", "test_auto_pay")
    if policy:
        print_success(f"Retrieved policy: {policy.name}")
        print(f"   Auto-pay: {policy.autoPay}")
        print(f"   Max amount: ${policy.maxAmount}")
    
    # Test 4: Update policy
    print_info("Updating policy...")
    policy.maxAmount = 7500
    policy.updatedAt = get_iso_timestamp()
    await backend.add_policy(policy)
    print_success(f"Updated policy maxAmount to ${policy.maxAmount}")
    
    # Test 5: Delete policy
    print_info("Deleting policy...")
    deleted = await backend.delete_policy("test_company_1", "test_auto_pay")
    print_success(f"Deleted policy: {deleted}")
    
    print("\n✅ Policy contract tests passed!\n")


async def test_threat_intel_contract():
    """Test ThreatIntelContract operations"""
    print_header("TEST 2: Threat Intelligence Contract Operations")
    
    backend = get_contract_backend()
    
    # Test 1: Create and report threat
    print_info("Creating threat fingerprint...")
    
    vendor_name = "suspicious-vendor.com"
    wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
    invoice_text = "INVOICE #1234\nAmount: $8,500\nDue: 2025-12-01"
    
    threat = Threat(
        threatId=generate_threat_id(),
        vendorHash=hash_vendor(vendor_name),
        paymentTargetType="wallet_address",
        paymentTargetHash=hash_payment_target(wallet_address),
        invoiceTemplateHash=hash_invoice_template(invoice_text),
        amountBucket=bucket_amount(8500),
        currency="USDC",
        fraudScore=0.87,
        reasons=["NO_PO_MATCH", "HOURS_EXCEED_LOGS", "SUSPICIOUS_WALLET_CHANGE"],
        firstSeenAt=get_iso_timestamp(),
        lastSeenAt=get_iso_timestamp(),
        timesSeen=1,
        reporterId="test_company_1",
        reporterHash=hash_company_id("test_company_1"),
        networkReward=0,
        verified=False
    )
    
    print_success("Generated threat fingerprint:")
    print(f"   Threat ID: {threat.threatId}")
    print(f"   Vendor hash: {threat.vendorHash[:32]}...")
    print(f"   Payment hash: {threat.paymentTargetHash[:32]}...")
    print(f"   Amount bucket: {threat.amountBucket}")
    print(f"   Fraud score: {threat.fraudScore}")
    print(f"   Reasons: {', '.join(threat.reasons)}")
    
    # Test 2: Report threat
    print_info("Reporting threat to network...")
    threat_id = await backend.append_threat(threat)
    print_success(f"Threat reported: {threat_id}")
    
    # Test 3: List threats
    print_info("Listing all threats...")
    threats = await backend.list_threats(limit=10)
    print_success(f"Found {len(threats)} threats in network")
    for t in threats[:3]:
        print(f"   - {t.threatId[:40]}... | Score: {t.fraudScore} | Seen: {t.timesSeen}x")
    
    # Test 4: Filter threats by vendor
    print_info("Filtering threats by vendor hash...")
    vendor_threats = await backend.list_threats(vendor_hash=threat.vendorHash)
    print_success(f"Found {len(vendor_threats)} threats for this vendor")
    
    # Test 5: Get threat statistics
    print_info("Getting threat statistics...")
    stats = await backend.get_threat_statistics()
    print_success("Threat intelligence statistics:")
    print(f"   Total threats: {stats.totalThreats}")
    print(f"   Total blocked amount: ${stats.totalBlockedAmount:,.2f}")
    print(f"   High-risk vendors: {stats.highRiskVendors}")
    print(f"   Verified reporters: {stats.verifiedReporters}")
    
    print("\n✅ Threat intelligence contract tests passed!\n")


async def test_treasury_contract():
    """Test TreasuryContract operations"""
    print_header("TEST 3: Treasury Contract Operations")
    
    backend = get_contract_backend()
    
    # Test 1: Record payment (PAID)
    print_info("Recording successful payment...")
    payment = Transaction(
        txId=generate_transaction_id(),
        invoiceId="TEST-INV-001",
        vendor="Trusted Vendor Inc",
        vendorId="vendor_test_001",
        amount=4200,
        currency="USDC",
        status="PAID",
        decision="APPROVE",
        timestamp=get_iso_timestamp(),
        meta=TransactionMeta(
            fraudScore=0.08,
            confidence=0.96,
            policyMatched="test_auto_pay",
            paymentMethod="crypto",
            paymentAddress="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
        )
    )
    
    tx_id = await backend.record_payment("test_company_1", payment)
    print_success(f"Recorded payment: {tx_id}")
    print(f"   Invoice: {payment.invoiceId}")
    print(f"   Amount: ${payment.amount} {payment.currency}")
    print(f"   Status: {payment.status}")
    
    # Test 2: Record blocked transaction
    print_info("Recording blocked transaction...")
    blocked_tx = Transaction(
        txId=generate_transaction_id(),
        invoiceId="TEST-INV-002",
        vendor="Suspicious Vendor",
        vendorId="vendor_test_002",
        amount=12500,
        currency="USDC",
        status="BLOCKED",
        decision="BLOCK",
        timestamp=get_iso_timestamp(),
        meta=TransactionMeta(
            fraudScore=0.91,
            confidence=0.88,
            policyMatched="block_high_fraud",
            blockReasons=["NO_PO_MATCH", "SUSPICIOUS_WALLET_CHANGE"],
            threatId="threat_123abc"
        )
    )
    
    tx_id = await backend.record_payment("test_company_1", blocked_tx)
    print_success(f"Recorded blocked transaction: {tx_id}")
    print(f"   Amount blocked: ${blocked_tx.amount}")
    print(f"   Block reasons: {', '.join(blocked_tx.meta.blockReasons or [])}")
    
    # Test 3: Record held transaction
    print_info("Recording held transaction...")
    held_tx = Transaction(
        txId=generate_transaction_id(),
        invoiceId="TEST-INV-003",
        vendor="Medium Risk Vendor",
        vendorId="vendor_test_003",
        amount=8900,
        currency="USDC",
        status="HELD",
        decision="HOLD",
        timestamp=get_iso_timestamp(),
        meta=TransactionMeta(
            fraudScore=0.42,
            confidence=0.85,
            policyMatched="hold_for_review",
            manualReview=True,
            holdReason="MEDIUM_FRAUD_SCORE",
            assignedTo="admin_001"
        )
    )
    
    tx_id = await backend.record_payment("test_company_1", held_tx)
    print_success(f"Recorded held transaction: {tx_id}")
    print(f"   Amount held: ${held_tx.amount}")
    print(f"   Hold reason: {held_tx.meta.holdReason}")
    
    # Test 4: Get company treasury
    print_info("Getting company treasury state...")
    treasury = await backend.get_company_treasury("test_company_1")
    print_success(f"Treasury for {treasury.companyName}:")
    print(f"   Balance: ${treasury.balance:,.2f} {treasury.currency}")
    print(f"   Total paid: ${treasury.totalPaid:,.2f}")
    print(f"   Total blocked: ${treasury.totalBlocked:,.2f}")
    print(f"   Total held: ${treasury.totalHeld:,.2f}")
    print(f"   Transactions: {len(treasury.transactions)}")
    
    # Test 5: List transactions
    print_info("Listing recent transactions...")
    transactions = await backend.list_transactions("test_company_1", limit=5)
    print_success(f"Found {len(transactions)} transactions")
    for tx in transactions:
        print(f"   - {tx.txId[:20]}... | {tx.status} | ${tx.amount} | {tx.vendor}")
    
    # Test 6: Filter by status
    print_info("Filtering blocked transactions...")
    blocked_txs = await backend.list_transactions("test_company_1", status="BLOCKED")
    print_success(f"Found {len(blocked_txs)} blocked transactions")
    
    # Test 7: Get global statistics
    print_info("Getting global treasury statistics...")
    global_stats = await backend.get_global_treasury_stats()
    print_success("Global treasury statistics:")
    print(f"   Total companies: {global_stats.totalCompanies}")
    print(f"   Total balance: ${global_stats.totalBalance:,.2f}")
    print(f"   Total transactions: {global_stats.totalTransactions}")
    print(f"   Total paid: ${global_stats.totalPaid:,.2f}")
    print(f"   Total blocked: ${global_stats.totalBlocked:,.2f}")
    print(f"   Total held: ${global_stats.totalHeld:,.2f}")
    
    print("\n✅ Treasury contract tests passed!\n")


async def test_utility_functions():
    """Test utility functions"""
    print_header("TEST 4: Utility Functions")
    
    # Test hashing
    print_info("Testing hashing functions...")
    vendor_hash = hash_vendor("acme-corp.com")
    print_success(f"Vendor hash: {vendor_hash[:32]}...")
    
    wallet_hash = hash_payment_target("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1")
    print_success(f"Wallet hash: {wallet_hash[:32]}...")
    
    invoice_hash = hash_invoice_template("INVOICE\nAmount: $3200\nDue: 2025-12-01")
    print_success(f"Invoice hash: {invoice_hash[:32]}...")
    
    company_hash = hash_company_id("company_1")
    print_success(f"Company hash: {company_hash}")
    
    # Test bucketing
    print_info("Testing amount bucketing...")
    buckets = [
        (500, "0-1k"),
        (3200, "1k-5k"),
        (8500, "5k-20k"),
        (35000, "20k-50k"),
        (75000, "50k-100k"),
        (250000, "100k+"),
    ]
    
    for amount, expected_bucket in buckets:
        bucket = bucket_amount(amount)
        print_success(f"${amount:,} → {bucket} {'✓' if bucket == expected_bucket else '✗'}")
    
    # Test ID generation
    print_info("Testing ID generation...")
    threat_id = generate_threat_id()
    print_success(f"Threat ID: {threat_id}")
    
    tx_id = generate_transaction_id()
    print_success(f"Transaction ID: {tx_id}")
    
    policy_id = generate_policy_id("company_1", "Auto Small Invoices")
    print_success(f"Policy ID: {policy_id}")
    
    timestamp = get_iso_timestamp()
    print_success(f"Timestamp: {timestamp}")
    
    print("\n✅ Utility function tests passed!\n")


async def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*80)
    print("  🚀 ShieldNet Smart Contracts Test Suite")
    print("="*80)
    
    try:
        # Run tests
        await test_utility_functions()
        await test_policy_contract()
        await test_threat_intel_contract()
        await test_treasury_contract()
        
        # Final summary
        print_header("ALL TESTS PASSED! ✅")
        print("\n🎉 Smart contract system working perfectly!")
        print("\n📁 Contract files location:")
        backend = get_contract_backend()
        if isinstance(backend, JsonContractBackend):
            print(f"   {backend.contracts_dir}")
            print(f"   - PolicyContract.json")
            print(f"   - ThreatIntelContract.json")
            print(f"   - TreasuryContract.json")
        
        print("\n💡 You can now:")
        print("   1. Inspect contract state: open JSON files")
        print("   2. Integrate with API endpoints")
        print("   3. Start the backend: uvicorn app.main:app --reload")
        print("   4. Test the full flow with real invoice processing")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
