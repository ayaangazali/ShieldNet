from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any

from app.database import get_db
from app.models import Invoice
from app.schemas import (
    TransactionResponse, TreasuryOverview, TreasuryWalletResponse
)
from app.services.treasury import TreasuryService

router = APIRouter(prefix="/api/treasury", tags=["Treasury & Payments"])

@router.post("/pay/{invoice_id}", response_model=Dict[str, Any])
async def pay_invoice(
    invoice_id: int,
    force: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute payment for an approved invoice
    
    Only Treasury Agent can call this endpoint.
    The Treasury Agent uses Locus-controlled USDC wallet.
    Policy-based auto-pay rules are checked before payment.
    """
    treasury_service = TreasuryService(db)
    result = await treasury_service.pay_invoice(invoice_id, force)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result

@router.get("/overview", response_model=TreasuryOverview)
async def get_treasury_overview(db: AsyncSession = Depends(get_db)):
    """
    Get treasury overview for dashboard
    
    Returns:
    - Wallet balance
    - Total paid/held/blocked amounts
    - Risk prevented (USDC saved)
    - Pending and approved invoice counts
    """
    treasury_service = TreasuryService(db)
    overview = await treasury_service.get_treasury_overview()
    
    if "error" in overview:
        raise HTTPException(status_code=404, detail=overview["error"])
    
    return overview

@router.post("/auto-pay")
async def trigger_auto_pay(db: AsyncSession = Depends(get_db)):
    """
    Trigger auto-pay for all approved invoices that meet mandate criteria
    
    This endpoint processes all approved invoices and pays them if:
    - Amount ≤ configured limit (e.g. $2k)
    - High confidence score
    - Low fraud score
    - All mandate rules satisfied
    """
    treasury_service = TreasuryService(db)
    
    # Get all approved invoices
    result = await db.execute(
        select(Invoice).where(Invoice.status == "approved")
    )
    approved_invoices = result.scalars().all()
    
    results = {
        "processed": 0,
        "paid": 0,
        "failed": 0,
        "details": []
    }
    
    for invoice in approved_invoices:
        results["processed"] += 1
        
        pay_result = await treasury_service.pay_invoice(invoice.id, force=False)
        
        if pay_result["success"]:
            results["paid"] += 1
            results["details"].append({
                "invoice_id": invoice.id,
                "status": "paid",
                "tx_hash": pay_result.get("tx_hash"),
                "amount": invoice.amount
            })
        else:
            results["failed"] += 1
            results["details"].append({
                "invoice_id": invoice.id,
                "status": "failed",
                "reason": pay_result.get("error"),
                "amount": invoice.amount
            })
    
    return results

@router.get("/transactions", response_model=Dict[str, Any])
async def get_transactions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get transaction history"""
    from app.models import Transaction
    from sqlalchemy import desc
    
    result = await db.execute(
        select(Transaction)
        .offset(skip)
        .limit(limit)
        .order_by(desc(Transaction.created_at))
    )
    transactions = result.scalars().all()
    
    return {
        "total": len(transactions),
        "transactions": [
            {
                "id": tx.id,
                "invoice_id": tx.invoice_id,
                "tx_hash": tx.tx_hash,
                "from_wallet": tx.from_wallet,
                "to_wallet": tx.to_wallet,
                "amount": tx.amount,
                "currency": tx.currency,
                "status": tx.status,
                "gas_fee": tx.gas_fee,
                "created_at": tx.created_at,
                "confirmed_at": tx.confirmed_at
            }
            for tx in transactions
        ]
    }

@router.get("/balance")
async def get_wallet_balance(db: AsyncSession = Depends(get_db)):
    """Get current wallet balance from blockchain"""
    treasury_service = TreasuryService(db)
    wallet = await treasury_service._get_active_wallet()
    
    if not wallet:
        raise HTTPException(status_code=404, detail="No active wallet found")
    
    balance_check = await treasury_service._check_balance(wallet, 0)
    
    return {
        "wallet_address": wallet.wallet_address,
        "balance": balance_check.get("balance", 0),
        "currency": wallet.currency,
        "last_updated": wallet.updated_at
    }
