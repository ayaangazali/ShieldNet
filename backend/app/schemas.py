from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models import InvoiceStatus, DecisionType

# ============= Vendor Schemas =============
class VendorBase(BaseModel):
    name: str
    wallet_address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_trusted: bool = False

class VendorCreate(VendorBase):
    pass

class VendorUpdate(BaseModel):
    name: Optional[str] = None
    wallet_address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_trusted: Optional[bool] = None

class VendorResponse(VendorBase):
    id: int
    risk_score: float
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# ============= Invoice Schemas =============
class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float

class InvoiceBase(BaseModel):
    invoice_number: str
    amount: float
    currency: str = "USDC"
    due_date: Optional[datetime] = None
    issue_date: Optional[datetime] = None
    po_number: Optional[str] = None
    line_items: Optional[List[LineItem]] = None

class InvoiceCreate(InvoiceBase):
    vendor_id: int

class InvoiceUpload(BaseModel):
    vendor_id: Optional[int] = None
    vendor_name: Optional[str] = None

class InvoiceResponse(InvoiceBase):
    id: int
    vendor_id: int
    status: InvoiceStatus
    confidence_score: Optional[float] = None
    fraud_score: Optional[float] = None
    decision: Optional[DecisionType] = None
    decision_reason: Optional[str] = None
    po_matched: bool
    contract_matched: bool
    vendor_verified: bool
    created_at: datetime
    processed_at: Optional[datetime] = None
    vendor: Optional[VendorResponse] = None
    
    class Config:
        from_attributes = True

class InvoiceAnalysisResponse(InvoiceResponse):
    verification_details: Dict[str, Any]
    fraud_indicators: List[str]
    recommendation: str

# ============= Purchase Order Schemas =============
class PurchaseOrderBase(BaseModel):
    po_number: str
    amount: float
    currency: str = "USDC"
    description: Optional[str] = None
    line_items: Optional[List[LineItem]] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    vendor_id: int

class PurchaseOrderResponse(PurchaseOrderBase):
    id: int
    vendor_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============= Contract Schemas =============
class ContractBase(BaseModel):
    contract_number: str
    value: Optional[float] = None
    currency: str = "USDC"
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    terms: Optional[Dict[str, Any]] = None

class ContractCreate(ContractBase):
    vendor_id: int

class ContractResponse(ContractBase):
    id: int
    vendor_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============= Threat Report Schemas =============
class ThreatReportBase(BaseModel):
    threat_type: str
    severity: str
    description: str
    indicators: List[str]
    amount_saved: float

class ThreatReportCreate(ThreatReportBase):
    invoice_id: int
    vendor_fingerprint: str
    wallet_fingerprint: Optional[str] = None
    template_fingerprint: str

class ThreatReportResponse(ThreatReportBase):
    id: int
    invoice_id: int
    vendor_fingerprint: str
    wallet_fingerprint: Optional[str]
    template_fingerprint: str
    is_shared: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============= Transaction Schemas =============
class TransactionBase(BaseModel):
    amount: float
    currency: str = "USDC"
    to_wallet: str

class TransactionCreate(TransactionBase):
    invoice_id: int

class TransactionResponse(TransactionBase):
    id: int
    invoice_id: int
    tx_hash: Optional[str]
    from_wallet: str
    status: str
    gas_fee: Optional[float]
    block_number: Optional[int]
    created_at: datetime
    confirmed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# ============= Mandate Schemas =============
class MandateBase(BaseModel):
    name: str
    description: Optional[str] = None
    rule_type: str  # auto_pay, block, hold, alert
    max_amount: Optional[float] = None
    min_confidence_score: Optional[float] = None
    max_fraud_score: Optional[float] = None
    require_po_match: bool = False
    require_contract_match: bool = False
    require_trusted_vendor: bool = False
    allowed_vendors: Optional[List[int]] = None
    blocked_vendors: Optional[List[int]] = None
    priority: int = 0

class MandateCreate(MandateBase):
    pass

class MandateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rule_type: Optional[str] = None
    max_amount: Optional[float] = None
    min_confidence_score: Optional[float] = None
    max_fraud_score: Optional[float] = None
    require_po_match: Optional[bool] = None
    require_contract_match: Optional[bool] = None
    require_trusted_vendor: Optional[bool] = None
    allowed_vendors: Optional[List[int]] = None
    blocked_vendors: Optional[List[int]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None

class MandateResponse(MandateBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# ============= Treasury Schemas =============
class TreasuryWalletResponse(BaseModel):
    id: int
    name: str
    wallet_address: str
    balance: float
    currency: str
    total_paid: float
    total_held: float
    total_blocked: float
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class TreasuryOverview(BaseModel):
    wallet_address: str
    balance: float
    total_paid: float
    total_held: float
    total_blocked: float
    risk_prevented: float
    pending_invoices: int
    approved_invoices: int

# ============= Analytics Schemas =============
class ThreatAnalytics(BaseModel):
    total_blocked_amount: float
    total_threats: int
    threats_by_type: Dict[str, int]
    threats_by_severity: Dict[str, int]
    top_risky_vendors: List[Dict[str, Any]]
    recent_blocks: List[ThreatReportResponse]

class FraudGraphNode(BaseModel):
    id: int
    name: str
    type: str  # vendor, template, wallet
    fraud_score: float
    occurrences: int
    connections: List[int]

class FraudGraphResponse(BaseModel):
    nodes: List[FraudGraphNode]
    edges: List[Dict[str, Any]]

class TransactionHistory(BaseModel):
    invoices: List[InvoiceResponse]
    total: int
    paid_count: int
    held_count: int
    blocked_count: int
    total_amount_paid: float
    total_amount_blocked: float

# ============= Scoring Schemas =============
class ScoringResult(BaseModel):
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    fraud_score: float = Field(..., ge=0.0, le=1.0)
    decision: DecisionType
    decision_reason: str
    risk_factors: List[str]
    verification_passed: bool

# ============= Network Intel Schemas =============
class NetworkThreatQuery(BaseModel):
    vendor_fingerprint: Optional[str] = None
    wallet_address: Optional[str] = None
    template_hash: Optional[str] = None

class NetworkThreatResponse(BaseModel):
    is_threat: bool
    threat_count: int
    threat_details: List[Dict[str, Any]]
    risk_level: str

# ============= Invoice Processing Schemas (Multi-Agent Pipeline) =============
class ProcessingStatus(str):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    CHECKING_INJECTION = "checking_injection"
    ANALYZING_RISK = "analyzing_risk"
    COMPLETED = "completed"
    FAILED = "failed"

class InvoiceLineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total: float

class ParsedInvoiceData(BaseModel):
    invoice_number: str
    vendor_name: str
    vendor_email: Optional[str] = None
    date: str
    due_date: Optional[str] = None
    subtotal: float
    tax: float
    total_amount: float
    line_items: List[InvoiceLineItem]
    purchase_order: Optional[str] = None
    payment_terms: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)

class InjectionThreat(BaseModel):
    field: str
    threat_type: str
    severity: str
    description: str
    matched_pattern: Optional[str] = None

class InjectionDetectionResult(BaseModel):
    threats_found: int
    threats: List[InjectionThreat]
    risk_level: str
    is_safe: bool

class FraudFactor(BaseModel):
    category: str
    score: float
    reason: str
    details: Dict[str, Any]

class RiskAnalysisResult(BaseModel):
    fraud_score: float = Field(ge=0.0, le=1.0)
    factors: List[FraudFactor]
    decision: DecisionType
    decision_reason: str
    vendor_threat_score: float = Field(ge=0.0, le=1.0)
    vendor_threat_reasons: List[str]

class InvoiceUploadResponse(BaseModel):
    id: int
    filename: str
    status: str
    message: str

class InvoiceStatusResponse(BaseModel):
    id: int
    filename: str
    status: str
    parsing_completed: bool
    injection_completed: bool
    risk_completed: bool
    parsed_data: Optional[ParsedInvoiceData] = None
    injection_result: Optional[InjectionDetectionResult] = None
    risk_result: Optional[RiskAnalysisResult] = None
    created_at: datetime
    processing_time_ms: Optional[int] = None

class InvoiceProcessRequest(BaseModel):
    invoice_id: int

class InvoiceProcessResponse(BaseModel):
    id: int
    status: str
    message: str
    parsed_data: Optional[ParsedInvoiceData] = None
    injection_result: Optional[InjectionDetectionResult] = None
    risk_result: Optional[RiskAnalysisResult] = None
