from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List

from app.database import get_db
from app.models import Mandate
from app.schemas import MandateCreate, MandateUpdate, MandateResponse

router = APIRouter(prefix="/api/mandates", tags=["Mandates & Governance"])

@router.post("/", response_model=MandateResponse)
async def create_mandate(
    mandate_data: MandateCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new mandate (AP2-style rule)
    
    Mandates are company-level rules that control:
    - Auto-pay limits
    - Block unknown vendors
    - Hold medium-risk invoices
    - Custom policy conditions
    """
    mandate = Mandate(
        name=mandate_data.name,
        description=mandate_data.description,
        rule_type=mandate_data.rule_type,
        max_amount=mandate_data.max_amount,
        min_confidence_score=mandate_data.min_confidence_score,
        max_fraud_score=mandate_data.max_fraud_score,
        require_po_match=mandate_data.require_po_match,
        require_contract_match=mandate_data.require_contract_match,
        require_trusted_vendor=mandate_data.require_trusted_vendor,
        allowed_vendors=mandate_data.allowed_vendors,
        blocked_vendors=mandate_data.blocked_vendors,
        priority=mandate_data.priority,
        is_active=True
    )
    
    db.add(mandate)
    await db.commit()
    await db.refresh(mandate)
    
    return mandate

@router.get("/", response_model=List[MandateResponse])
async def list_mandates(
    rule_type: str = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List all mandates"""
    query = select(Mandate)
    
    if active_only:
        query = query.where(Mandate.is_active == True)
    
    if rule_type:
        query = query.where(Mandate.rule_type == rule_type)
    
    query = query.order_by(desc(Mandate.priority))
    
    result = await db.execute(query)
    mandates = result.scalars().all()
    
    return mandates

@router.get("/{mandate_id}", response_model=MandateResponse)
async def get_mandate(mandate_id: int, db: AsyncSession = Depends(get_db)):
    """Get mandate by ID"""
    result = await db.execute(
        select(Mandate).where(Mandate.id == mandate_id)
    )
    mandate = result.scalar_one_or_none()
    
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")
    
    return mandate

@router.put("/{mandate_id}", response_model=MandateResponse)
async def update_mandate(
    mandate_id: int,
    mandate_data: MandateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing mandate"""
    result = await db.execute(
        select(Mandate).where(Mandate.id == mandate_id)
    )
    mandate = result.scalar_one_or_none()
    
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")
    
    # Update fields
    update_data = mandate_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(mandate, field, value)
    
    await db.commit()
    await db.refresh(mandate)
    
    return mandate

@router.delete("/{mandate_id}")
async def delete_mandate(mandate_id: int, db: AsyncSession = Depends(get_db)):
    """Delete (deactivate) a mandate"""
    result = await db.execute(
        select(Mandate).where(Mandate.id == mandate_id)
    )
    mandate = result.scalar_one_or_none()
    
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")
    
    # Soft delete by deactivating
    mandate.is_active = False
    await db.commit()
    
    return {"message": "Mandate deleted successfully", "id": mandate_id}

@router.post("/{mandate_id}/toggle")
async def toggle_mandate(mandate_id: int, db: AsyncSession = Depends(get_db)):
    """Toggle mandate active status"""
    result = await db.execute(
        select(Mandate).where(Mandate.id == mandate_id)
    )
    mandate = result.scalar_one_or_none()
    
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")
    
    mandate.is_active = not mandate.is_active
    await db.commit()
    
    return {
        "message": f"Mandate {'activated' if mandate.is_active else 'deactivated'}",
        "id": mandate_id,
        "is_active": mandate.is_active
    }

@router.get("/templates/auto-pay")
async def get_auto_pay_template():
    """Get template for auto-pay mandate"""
    return {
        "name": "Auto-pay for small trusted invoices",
        "description": "Automatically pay invoices ≤ $2000 from trusted vendors with high confidence",
        "rule_type": "auto_pay",
        "max_amount": 2000.0,
        "min_confidence_score": 0.85,
        "max_fraud_score": 0.15,
        "require_trusted_vendor": True,
        "require_po_match": False,
        "priority": 10
    }

@router.get("/templates/block-unknown")
async def get_block_unknown_template():
    """Get template for blocking unknown vendors"""
    return {
        "name": "Block unknown vendors",
        "description": "Block all invoices from vendors not in trusted list",
        "rule_type": "block",
        "require_trusted_vendor": True,
        "priority": 100
    }

@router.get("/templates/hold-high-amount")
async def get_hold_high_amount_template():
    """Get template for holding high-amount invoices"""
    return {
        "name": "Hold high-amount invoices for review",
        "description": "Hold invoices over $10,000 for manual review",
        "rule_type": "hold",
        "max_amount": 10000.0,
        "priority": 50
    }
