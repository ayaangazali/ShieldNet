from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import time
import logging

from app.config import settings
from app.database import engine, Base
from app.routers import invoices, treasury, threats, analytics, mandates, vendors, blockchain
# DISABLED FOR NOW - FOCUSING ON BLOCKCHAIN ONLY
# from app.routers import invoice_processing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ShieldNet API",
    description="""
    ShieldNet - AI-Powered Invoice Fraud Detection & Payment Automation
    
    ## Core Features
    
    * **Invoice Intake Agent** - Upload/parse invoices (PDF/JSON) with auto-extraction
    * **Local Verification** - Cross-check against POs, contracts, and vendor data
    * **Network Fraud Check** - Compare against ShieldNet threat intelligence
    * **Risk Scoring** - Confidence (legit) and fraud (scammy) scores
    * **3-way Decision Engine** - Approve/Hold/Block classification
    * **Treasury Agent** - Secure USDC payments via Locus wallet
    * **Policy-Based Auto-Pay** - Rules-driven payment automation
    * **Threat Intelligence** - Shared fraud detection network
    * **Analytics Dashboard** - Comprehensive threat and treasury analytics
    * **Mandates** - Company-level governance rules
    
    ## Architecture
    
    - LLM agents analyze and recommend
    - Treasury Agent + Locus policies control funds
    - Strict separation of roles for security
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"Status: {response.status_code} Time: {process_time:.3f}s"
        )
        
        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url.path} Error: {str(e)}")
        raise

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred"
        }
    )

# Include routers
app.include_router(invoices.router)
# DISABLED: app.include_router(invoice_processing.router)  # Focusing on blockchain only
app.include_router(blockchain.router)  # 🔥 BLOCKCHAIN THREAT INTELLIGENCE - PRIMARY FOCUS
app.include_router(treasury.router)
app.include_router(threats.router)
app.include_router(analytics.router)
app.include_router(mandates.router)
app.include_router(vendors.router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "ShieldNet API",
        "version": "1.0.0",
        "status": "operational",
        "description": "AI-Powered Invoice Fraud Detection & Payment Automation",
        "docs": "/docs",
        "features": [
            "Invoice Intake & Parsing",
            "Local Verification",
            "Network Fraud Check",
            "Risk & Confidence Scoring",
            "3-way Decision Engine",
            "Treasury & Payments",
            "Threat Intelligence",
            "Analytics & Reporting",
            "Policy-Based Mandates"
        ]
    }

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting ShieldNet API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info("API documentation available at /docs")
    
    # Create database tables (in production, use Alembic migrations)
    # Uncomment the following to auto-create tables on startup
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down ShieldNet API...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
