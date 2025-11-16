from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/shieldnet"
    ASYNC_DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/shieldnet"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Locus/Web3 (for USDC payment execution)
    # These credentials are used ONLY for moving USDC when invoices are approved
    LOCUS_API_KEY: str = ""
    LOCUS_WALLET_ADDRESS: str = ""
    LOCUS_PRIVATE_KEY: str = ""
    USDC_CONTRACT_ADDRESS: str = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    
    # Threat Intelligence Storage Mode
    # Set USE_ONCHAIN_THREATS=true to enable blockchain integration (Base/L3)
    # When false (default), threats are stored locally in SQLite (no blockchain required)
    USE_ONCHAIN_THREATS: bool = False  # Feature flag for blockchain threat storage
    BASE_RPC_URL: str = ""  # e.g., https://base-mainnet.g.alchemy.com/v2/YOUR_KEY
    REPORTER_PRIVATE_KEY: str = ""  # Wallet that submits threat reports to Base
    SHIELDNET_CONTRACT_ADDRESS: str = ""  # Deployed ShieldNetThreatIntel contract address
    
    # Legacy Alchemy fields (kept for backward compatibility)
    ALCHEMY_API_KEY: str = ""
    ALCHEMY_BASE_RPC_URL: str = ""
    
    # ShieldNet Network
    SHIELDNET_API_URL: str = "https://api.shieldnet.network"
    SHIELDNET_API_KEY: str = ""
    
    # Google Gemini (for AI-powered invoice processing agents)
    GEMINI_API_KEY: str = ""
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "./uploads"
    
    # Fraud Detection Thresholds
    HIGH_CONFIDENCE_THRESHOLD: float = 0.85
    LOW_FRAUD_THRESHOLD: float = 0.15
    AUTO_PAY_MAX_AMOUNT: float = 2000.0
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
