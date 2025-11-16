from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    HELD = "held"
    BLOCKED = "blocked"
    PAID = "paid"

class DecisionType(str, enum.Enum):
    APPROVE = "approve"
    HOLD = "hold"
    BLOCK = "block"

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    wallet_address = Column(String, index=True)
    email = Column(String)
    phone = Column(String)
    is_trusted = Column(Boolean, default=False)
    risk_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    invoices = relationship("Invoice", back_populates="vendor")
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")
    contracts = relationship("Contract", back_populates="vendor")

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USDC")
    due_date = Column(DateTime(timezone=True))
    issue_date = Column(DateTime(timezone=True))
    po_number = Column(String, index=True)
    
    # Parsed data
    line_items = Column(JSON)  # Array of line items
    raw_data = Column(JSON)  # Original parsed data
    file_path = Column(String)
    template_hash = Column(String, index=True)  # For fraud detection
    
    # Status and scores
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.PENDING)
    confidence_score = Column(Float)  # Legit score
    fraud_score = Column(Float)  # Scammy score
    decision = Column(SQLEnum(DecisionType))
    decision_reason = Column(Text)
    
    # Verification flags
    po_matched = Column(Boolean, default=False)
    contract_matched = Column(Boolean, default=False)
    vendor_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Relationships
    vendor = relationship("Vendor", back_populates="invoices")
    transaction = relationship("Transaction", back_populates="invoice", uselist=False)
    threat_reports = relationship("ThreatReport", back_populates="invoice")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String, unique=True, nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USDC")
    description = Column(Text)
    line_items = Column(JSON)
    issue_date = Column(DateTime(timezone=True))
    expiry_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    vendor = relationship("Vendor", back_populates="purchase_orders")

class Contract(Base):
    __tablename__ = "contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_number = Column(String, unique=True, nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    value = Column(Float)
    currency = Column(String, default="USDC")
    description = Column(Text)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    terms = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    vendor = relationship("Vendor", back_populates="contracts")

class WorkLog(Base):
    __tablename__ = "work_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    po_number = Column(String)
    description = Column(Text)
    quantity = Column(Float)
    unit = Column(String)
    log_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ThreatReport(Base):
    __tablename__ = "threat_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    threat_type = Column(String)  # e.g., "duplicate_invoice", "fake_vendor", etc.
    severity = Column(String)  # high, medium, low
    
    # Fingerprint data
    vendor_fingerprint = Column(String, index=True)
    wallet_fingerprint = Column(String, index=True)
    template_fingerprint = Column(String, index=True)
    
    # Details
    description = Column(Text)
    indicators = Column(JSON)  # Array of red flags
    amount_saved = Column(Float)
    
    # Network sharing
    is_shared = Column(Boolean, default=False)
    anonymized_data = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="threat_reports")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), unique=True, nullable=False)
    tx_hash = Column(String, unique=True, index=True)  # Blockchain transaction hash
    from_wallet = Column(String)  # Locus wallet
    to_wallet = Column(String)  # Vendor wallet
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USDC")
    status = Column(String)  # pending, confirmed, failed
    gas_fee = Column(Float)
    block_number = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True))
    
    # Relationships
    invoice = relationship("Invoice", back_populates="transaction")

class Mandate(Base):
    __tablename__ = "mandates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    rule_type = Column(String)  # auto_pay, block, hold, alert
    
    # Conditions
    max_amount = Column(Float)
    min_confidence_score = Column(Float)
    max_fraud_score = Column(Float)
    require_po_match = Column(Boolean, default=False)
    require_contract_match = Column(Boolean, default=False)
    require_trusted_vendor = Column(Boolean, default=False)
    allowed_vendors = Column(JSON)  # Array of vendor IDs
    blocked_vendors = Column(JSON)  # Array of vendor IDs
    
    # Priority and status
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class TreasuryWallet(Base):
    __tablename__ = "treasury_wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    wallet_address = Column(String, unique=True, nullable=False, index=True)
    balance = Column(Float, default=0.0)
    currency = Column(String, default="USDC")
    is_active = Column(Boolean, default=True)
    total_paid = Column(Float, default=0.0)
    total_held = Column(Float, default=0.0)
    total_blocked = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False)
    entity_type = Column(String)  # invoice, transaction, mandate, etc.
    entity_id = Column(Integer)
    user_id = Column(Integer)
    details = Column(JSON)
    ip_address = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProcessingStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    CHECKING_INJECTION = "checking_injection"
    ANALYZING_RISK = "analyzing_risk"
    COMPLETED = "completed"
    FAILED = "failed"

class InvoiceProcessing(Base):
    """Multi-agent invoice processing pipeline"""
    __tablename__ = "invoice_processing"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.UPLOADED)
    
    # Parsing results
    parsing_completed = Column(Integer, default=0)
    parsed_data = Column(JSON, nullable=True)
    parsing_confidence = Column(Float, default=0.0)
    
    # Injection detection results
    injection_completed = Column(Integer, default=0)
    injection_threats = Column(JSON, nullable=True)
    injection_risk_level = Column(String, nullable=True)
    
    # Risk analysis results
    risk_completed = Column(Integer, default=0)
    fraud_score = Column(Float, default=0.0)
    fraud_factors = Column(JSON, nullable=True)
    decision = Column(SQLEnum(DecisionType), nullable=True)
    decision_reason = Column(Text, nullable=True)
    
    # Network intel
    vendor_threat_score = Column(Float, default=0.0)
    vendor_threat_reasons = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processing_time_ms = Column(Integer, nullable=True)
