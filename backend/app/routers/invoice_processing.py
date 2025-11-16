"""
Invoice Processing Router
API endpoints for multi-agent invoice processing pipeline
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import os
import time
from datetime import datetime

from app.database import get_db
from app.models import InvoiceProcessing, ProcessingStatus, DecisionType
from app.schemas import (
    InvoiceUploadResponse,
    InvoiceStatusResponse,
    InvoiceProcessRequest,
    InvoiceProcessResponse,
    ParsedInvoiceData,
    InjectionDetectionResult,
    RiskAnalysisResult
)
from app.services.parsing_agent import ParsingAgentService
from app.services.injection_detection import PromptInjectionDetectionService
from app.services.risk_analysis import RiskAnalysisService


router = APIRouter(prefix="/api/invoices", tags=["Invoice Processing"])

# Directory for uploaded invoices
UPLOAD_DIR = "uploads/invoices"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=InvoiceUploadResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload an invoice file for processing
    Supports PDF, PNG, JPG formats
    """
    # Validate file type
    allowed_extensions = [".pdf", ".png", ".jpg", ".jpeg"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Save file
    timestamp = int(time.time())
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Create database record
    invoice_record = InvoiceProcessing(
        filename=file.filename,
        file_path=file_path,
        status=ProcessingStatus.UPLOADED
    )
    
    db.add(invoice_record)
    await db.commit()
    await db.refresh(invoice_record)
    
    return InvoiceUploadResponse(
        id=invoice_record.id,
        filename=invoice_record.filename,
        status=invoice_record.status,
        message="Invoice uploaded successfully. Use /process endpoint to start analysis."
    )


@router.get("/{invoice_id}/status", response_model=InvoiceStatusResponse)
async def get_invoice_status(
    invoice_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current processing status of an invoice
    Returns full details including parsing, injection, and risk analysis results
    """
    result = await db.execute(
        select(InvoiceProcessing).where(InvoiceProcessing.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Build response
    response = InvoiceStatusResponse(
        id=invoice.id,
        filename=invoice.filename,
        status=invoice.status,
        parsing_completed=bool(invoice.parsing_completed),
        injection_completed=bool(invoice.injection_completed),
        risk_completed=bool(invoice.risk_completed),
        created_at=invoice.created_at,
        processing_time_ms=invoice.processing_time_ms
    )
    
    # Add parsed data if available
    if invoice.parsed_data:
        response.parsed_data = ParsedInvoiceData(**invoice.parsed_data)
    
    # Add injection detection results if available
    if invoice.injection_threats is not None:
        response.injection_result = InjectionDetectionResult(
            threats_found=len(invoice.injection_threats) if isinstance(invoice.injection_threats, list) else 0,
            threats=invoice.injection_threats if isinstance(invoice.injection_threats, list) else [],
            risk_level=invoice.injection_risk_level or "LOW",
            is_safe=invoice.injection_risk_level == "LOW" or not invoice.injection_threats
        )
    
    # Add risk analysis results if available
    if invoice.fraud_score is not None:
        response.risk_result = RiskAnalysisResult(
            fraud_score=invoice.fraud_score,
            factors=invoice.fraud_factors if invoice.fraud_factors else [],
            decision=invoice.decision or DecisionType.HOLD,
            decision_reason=invoice.decision_reason or "",
            vendor_threat_score=invoice.vendor_threat_score,
            vendor_threat_reasons=invoice.vendor_threat_reasons if invoice.vendor_threat_reasons else []
        )
    
    return response


@router.post("/{invoice_id}/process", response_model=InvoiceProcessResponse)
async def process_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Process an uploaded invoice through the 3-agent pipeline:
    1. Parsing Agent - Extract and validate invoice data
    2. Injection Detection Agent - Scan for malicious content
    3. Risk Analysis Agent - Fraud scoring and decision
    """
    start_time = time.time()
    
    # Get invoice record
    result = await db.execute(
        select(InvoiceProcessing).where(InvoiceProcessing.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.status == ProcessingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Invoice already processed")
    
    try:
        # STEP 1: PARSING AGENT
        invoice.status = ProcessingStatus.PARSING
        await db.commit()
        
        parsed_data = ParsingAgentService.parse_invoice(
            invoice.file_path,
            invoice.filename
        )
        
        invoice.parsed_data = parsed_data.model_dump()
        invoice.parsing_confidence = parsed_data.confidence
        invoice.parsing_completed = True
        await db.commit()
        
        # STEP 2: INJECTION DETECTION AGENT
        invoice.status = ProcessingStatus.CHECKING_INJECTION
        await db.commit()
        
        text_fields = ParsingAgentService.extract_text_fields(parsed_data)
        injection_result = PromptInjectionDetectionService.detect_injections(text_fields)
        
        invoice.injection_threats = [threat.model_dump() for threat in injection_result.threats]
        invoice.injection_risk_level = injection_result.risk_level
        invoice.injection_completed = True
        await db.commit()
        
        # STEP 3: RISK ANALYSIS AGENT
        invoice.status = ProcessingStatus.ANALYZING_RISK
        await db.commit()
        
        risk_result = RiskAnalysisService.analyze_fraud_risk(
            parsed_data,
            injection_result
        )
        
        invoice.fraud_score = risk_result.fraud_score
        invoice.fraud_factors = [factor.model_dump() for factor in risk_result.factors]
        invoice.decision = risk_result.decision
        invoice.decision_reason = risk_result.decision_reason
        invoice.vendor_threat_score = risk_result.vendor_threat_score
        invoice.vendor_threat_reasons = risk_result.vendor_threat_reasons
        invoice.risk_completed = True
        
        # Mark as completed
        invoice.status = ProcessingStatus.COMPLETED
        processing_time = int((time.time() - start_time) * 1000)
        invoice.processing_time_ms = processing_time
        
        await db.commit()
        await db.refresh(invoice)
        
        return InvoiceProcessResponse(
            id=invoice.id,
            status=invoice.status,
            message=f"Invoice processing completed in {processing_time}ms. Decision: {risk_result.decision.value}",
            parsed_data=parsed_data,
            injection_result=injection_result,
            risk_result=risk_result
        )
        
    except Exception as e:
        invoice.status = ProcessingStatus.FAILED
        await db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )


@router.get("/", response_model=List[InvoiceStatusResponse])
async def list_invoices(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List all processed invoices with their status
    """
    result = await db.execute(
        select(InvoiceProcessing)
        .order_by(InvoiceProcessing.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    invoices = result.scalars().all()
    
    response_list = []
    for invoice in invoices:
        response = InvoiceStatusResponse(
            id=invoice.id,
            filename=invoice.filename,
            status=invoice.status,
            parsing_completed=bool(invoice.parsing_completed),
            injection_completed=bool(invoice.injection_completed),
            risk_completed=bool(invoice.risk_completed),
            created_at=invoice.created_at,
            processing_time_ms=invoice.processing_time_ms
        )
        
        # Add parsed data if available
        if invoice.parsed_data:
            response.parsed_data = ParsedInvoiceData(**invoice.parsed_data)
        
        # Add injection detection results if available
        if invoice.injection_threats is not None:
            response.injection_result = InjectionDetectionResult(
                threats_found=len(invoice.injection_threats) if isinstance(invoice.injection_threats, list) else 0,
                threats=invoice.injection_threats if isinstance(invoice.injection_threats, list) else [],
                risk_level=invoice.injection_risk_level or "LOW",
                is_safe=invoice.injection_risk_level == "LOW" or not invoice.injection_threats
            )
        
        # Add risk analysis results if available
        if invoice.fraud_score is not None:
            response.risk_result = RiskAnalysisResult(
                fraud_score=invoice.fraud_score,
                factors=invoice.fraud_factors if invoice.fraud_factors else [],
                decision=invoice.decision or DecisionType.HOLD,
                decision_reason=invoice.decision_reason or "",
                vendor_threat_score=invoice.vendor_threat_score,
                vendor_threat_reasons=invoice.vendor_threat_reasons if invoice.vendor_threat_reasons else []
            )
        
        response_list.append(response)
    
    return response_list


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an invoice record and its file
    """
    result = await db.execute(
        select(InvoiceProcessing).where(InvoiceProcessing.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Delete file if exists
    if os.path.exists(invoice.file_path):
        try:
            os.remove(invoice.file_path)
        except Exception:
            pass  # Ignore file deletion errors
    
    await db.delete(invoice)
    await db.commit()
    
    return {"message": f"Invoice {invoice_id} deleted successfully"}
