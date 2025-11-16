from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List

from app.database import get_db
from app.models import Vendor, Invoice, PurchaseOrder, Contract
from app.schemas import (
    VendorCreate, VendorUpdate, VendorResponse,
    PurchaseOrderCreate, PurchaseOrderResponse,
    ContractCreate, ContractResponse
)

router = APIRouter(prefix="/api/vendors", tags=["Vendor Management"])

# ============= Vendor Endpoints =============
@router.post("/", response_model=VendorResponse)
async def create_vendor(
    vendor_data: VendorCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new vendor"""
    vendor = Vendor(
        name=vendor_data.name,
        wallet_address=vendor_data.wallet_address,
        email=vendor_data.email,
        phone=vendor_data.phone,
        is_trusted=vendor_data.is_trusted,
        risk_score=0.0  # Initial risk score
    )
    
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    
    return vendor

@router.get("/", response_model=List[VendorResponse])
async def list_vendors(
    trusted_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all vendors"""
    query = select(Vendor)
    
    if trusted_only:
        query = query.where(Vendor.is_trusted == True)
    
    query = query.offset(skip).limit(limit).order_by(Vendor.name)
    
    result = await db.execute(query)
    vendors = result.scalars().all()
    
    return vendors

@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(vendor_id: int, db: AsyncSession = Depends(get_db)):
    """Get vendor by ID"""
    result = await db.execute(
        select(Vendor).where(Vendor.id == vendor_id)
    )
    vendor = result.scalar_one_or_none()
    
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return vendor

@router.put("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: int,
    vendor_data: VendorUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update vendor information"""
    result = await db.execute(
        select(Vendor).where(Vendor.id == vendor_id)
    )
    vendor = result.scalar_one_or_none()
    
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    update_data = vendor_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vendor, field, value)
    
    await db.commit()
    await db.refresh(vendor)
    
    return vendor

@router.get("/{vendor_id}/invoices")
async def get_vendor_invoices(
    vendor_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all invoices for a vendor"""
    result = await db.execute(
        select(Invoice)
        .where(Invoice.vendor_id == vendor_id)
        .order_by(desc(Invoice.created_at))
    )
    invoices = result.scalars().all()
    
    # Calculate stats
    total_invoices = len(invoices)
    total_amount = sum(inv.amount for inv in invoices)
    blocked_count = len([inv for inv in invoices if inv.status.value == "blocked"])
    
    return {
        "vendor_id": vendor_id,
        "total_invoices": total_invoices,
        "total_amount": total_amount,
        "blocked_count": blocked_count,
        "invoices": [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "amount": inv.amount,
                "status": inv.status.value,
                "created_at": inv.created_at.isoformat()
            }
            for inv in invoices
        ]
    }

# ============= Purchase Order Endpoints =============
@router.post("/purchase-orders", response_model=PurchaseOrderResponse)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new purchase order"""
    po = PurchaseOrder(
        po_number=po_data.po_number,
        vendor_id=po_data.vendor_id,
        amount=po_data.amount,
        currency=po_data.currency,
        description=po_data.description,
        line_items=po_data.line_items,
        issue_date=po_data.issue_date,
        expiry_date=po_data.expiry_date,
        is_active=True
    )
    
    db.add(po)
    await db.commit()
    await db.refresh(po)
    
    return po

@router.get("/purchase-orders", response_model=List[PurchaseOrderResponse])
async def list_purchase_orders(
    vendor_id: int = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List purchase orders"""
    query = select(PurchaseOrder)
    
    if vendor_id:
        query = query.where(PurchaseOrder.vendor_id == vendor_id)
    
    if active_only:
        query = query.where(PurchaseOrder.is_active == True)
    
    query = query.offset(skip).limit(limit).order_by(desc(PurchaseOrder.created_at))
    
    result = await db.execute(query)
    pos = result.scalars().all()
    
    return pos

# ============= Contract Endpoints =============
@router.post("/contracts", response_model=ContractResponse)
async def create_contract(
    contract_data: ContractCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new vendor contract"""
    contract = Contract(
        contract_number=contract_data.contract_number,
        vendor_id=contract_data.vendor_id,
        value=contract_data.value,
        currency=contract_data.currency,
        description=contract_data.description,
        start_date=contract_data.start_date,
        end_date=contract_data.end_date,
        terms=contract_data.terms,
        is_active=True
    )
    
    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    
    return contract

@router.get("/contracts", response_model=List[ContractResponse])
async def list_contracts(
    vendor_id: int = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List vendor contracts"""
    query = select(Contract)
    
    if vendor_id:
        query = query.where(Contract.vendor_id == vendor_id)
    
    if active_only:
        query = query.where(Contract.is_active == True)
    
    query = query.offset(skip).limit(limit).order_by(desc(Contract.created_at))
    
    result = await db.execute(query)
    contracts = result.scalars().all()
    
    return contracts
