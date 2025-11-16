from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
import shutil
from pathlib import Path
from datetime import datetime

from app.database import get_db
from app.models import Invoice, Vendor, InvoiceStatus
from app.schemas import (
    InvoiceResponse, InvoiceAnalysisResponse, InvoiceCreate, 
    ScoringResult
)
from app.services.pdf_parser import pdf_parser
from app.services.verification import VerificationService
from app.services.fraud_detection import FraudDetectionService
from app.config import settings

router = APIRouter(prefix="/api/invoices", tags=["Invoice Intake"])

@router.post("/upload", response_model=InvoiceAnalysisResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    vendor_id: Optional[int] = Form(None),
    vendor_name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and analyze an invoice (PDF or JSON)
    
    This endpoint:
    1. Accepts PDF or JSON invoice files
    2. Parses and extracts structured data
    3. Runs verification checks
    4. Calculates confidence and fraud scores
    5. Makes approve/hold/block decision
    """
    # Validate file type
    if not file.filename.endswith(('.pdf', '.json')):
        raise HTTPException(status_code=400, detail="Only PDF and JSON files are supported")
    
    # Create upload directory if not exists
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = upload_dir / f"{timestamp}_{file.filename}"
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Parse invoice based on file type
        if file.filename.endswith('.pdf'):
            parsed_data = await pdf_parser.parse_pdf(str(file_path))
        else:
            import json
            with file_path.open("r") as f:
                json_data = json.load(f)
            parsed_data = await pdf_parser.parse_json(json_data)
        
        # Get or create vendor
        if vendor_id:
            result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
            vendor = result.scalar_one_or_none()
            if not vendor:
                raise HTTPException(status_code=404, detail="Vendor not found")
        elif vendor_name or parsed_data.get("vendor_name"):
            name = vendor_name or parsed_data.get("vendor_name")
            result = await db.execute(select(Vendor).where(Vendor.name == name))
            vendor = result.scalar_one_or_none()
            
            if not vendor:
                # Create new vendor
                vendor = Vendor(name=name, is_trusted=False, risk_score=0.5)
                db.add(vendor)
                await db.flush()
        else:
            raise HTTPException(status_code=400, detail="vendor_id or vendor_name must be provided")
        
        # Create invoice record
        invoice = Invoice(
            invoice_number=parsed_data.get("invoice_number", f"INV-{timestamp}"),
            vendor_id=vendor.id,
            amount=parsed_data.get("amount", 0.0),
            currency="USDC",
            due_date=parsed_data.get("due_date"),
            issue_date=parsed_data.get("issue_date"),
            po_number=parsed_data.get("po_number"),
            line_items=parsed_data.get("line_items", []),
            raw_data=parsed_data,
            file_path=str(file_path),
            template_hash=parsed_data.get("template_hash"),
            status=InvoiceStatus.PENDING
        )
        
        db.add(invoice)
        await db.flush()
        
        # Run verification
        verification_service = VerificationService(db)
        verification_results = await verification_service.verify_invoice(invoice)
        
        # Update verification flags
        invoice.po_matched = verification_results["po_verification"]["passed"]
        invoice.contract_matched = verification_results["contract_verification"]["passed"]
        invoice.vendor_verified = verification_results["vendor_verification"]["passed"]
        
        # Calculate scores and make decision
        fraud_service = FraudDetectionService(db)
        scoring_result = await fraud_service.calculate_scores(invoice, verification_results)
        
        # Update invoice with scores and decision
        invoice.confidence_score = scoring_result["confidence_score"]
        invoice.fraud_score = scoring_result["fraud_score"]
        invoice.decision = scoring_result["decision"]
        invoice.decision_reason = scoring_result["decision_reason"]
        invoice.processed_at = datetime.now()
        
        # Update status based on decision
        if scoring_result["decision"].value == "approve":
            invoice.status = InvoiceStatus.APPROVED
        elif scoring_result["decision"].value == "block":
            invoice.status = InvoiceStatus.BLOCKED
        else:
            invoice.status = InvoiceStatus.HELD
        
        await db.commit()
        await db.refresh(invoice)
        
        # Return comprehensive response
        return InvoiceAnalysisResponse(
            id=invoice.id,
            invoice_number=invoice.invoice_number,
            vendor_id=invoice.vendor_id,
            amount=invoice.amount,
            currency=invoice.currency,
            due_date=invoice.due_date,
            issue_date=invoice.issue_date,
            po_number=invoice.po_number,
            line_items=invoice.line_items,
            status=invoice.status,
            confidence_score=invoice.confidence_score,
            fraud_score=invoice.fraud_score,
            decision=invoice.decision,
            decision_reason=invoice.decision_reason,
            po_matched=invoice.po_matched,
            contract_matched=invoice.contract_matched,
            vendor_verified=invoice.vendor_verified,
            created_at=invoice.created_at,
            processed_at=invoice.processed_at,
            vendor=None,
            verification_details=verification_results,
            fraud_indicators=scoring_result["risk_factors"],
            recommendation=scoring_result["decision_reason"]
        )
        
    except Exception as e:
        await db.rollback()
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to process invoice: {str(e)}")

@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: int, db: AsyncSession = Depends(get_db)):
    """Get invoice by ID"""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return invoice

@router.get("/", response_model=List[InvoiceResponse])
async def list_invoices(
    status: Optional[str] = None,
    vendor_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List invoices with optional filters"""
    query = select(Invoice)
    
    if status:
        query = query.where(Invoice.status == status)
    if vendor_id:
        query = query.where(Invoice.vendor_id == vendor_id)
    
    query = query.offset(skip).limit(limit).order_by(Invoice.created_at.desc())
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    return invoices

@router.post("/{invoice_id}/reanalyze", response_model=InvoiceAnalysisResponse)
async def reanalyze_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Re-run analysis on an existing invoice"""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Re-run verification
    verification_service = VerificationService(db)
    verification_results = await verification_service.verify_invoice(invoice)
    
    # Re-calculate scores
    fraud_service = FraudDetectionService(db)
    scoring_result = await fraud_service.calculate_scores(invoice, verification_results)
    
    # Update invoice
    invoice.confidence_score = scoring_result["confidence_score"]
    invoice.fraud_score = scoring_result["fraud_score"]
    invoice.decision = scoring_result["decision"]
    invoice.decision_reason = scoring_result["decision_reason"]
    invoice.processed_at = datetime.now()
    
    await db.commit()
    await db.refresh(invoice)
    
    return InvoiceAnalysisResponse(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        vendor_id=invoice.vendor_id,
        amount=invoice.amount,
        currency=invoice.currency,
        due_date=invoice.due_date,
        issue_date=invoice.issue_date,
        po_number=invoice.po_number,
        line_items=invoice.line_items,
        status=invoice.status,
        confidence_score=invoice.confidence_score,
        fraud_score=invoice.fraud_score,
        decision=invoice.decision,
        decision_reason=invoice.decision_reason,
        po_matched=invoice.po_matched,
        contract_matched=invoice.contract_matched,
        vendor_verified=invoice.vendor_verified,
        created_at=invoice.created_at,
        processed_at=invoice.processed_at,
        vendor=None,
        verification_details=verification_results,
        fraud_indicators=scoring_result["risk_factors"],
        recommendation=scoring_result["decision_reason"]
    )
