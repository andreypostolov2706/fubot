"""
Core Configuration
"""
import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SERVICES_DIR = BASE_DIR / "services"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
SERVICES_DIR.mkdir(exist_ok=True)


class Config:
    """Application configuration"""
    
    # === Telegram ===
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # === Database ===
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite+aiosqlite:///{DATA_DIR}/core.db"
    )
    
    # === Admin ===
    ADMIN_IDS: List[int] = [
        int(x.strip()) 
        for x in os.getenv("ADMIN_IDS", "").split(",") 
        if x.strip()
    ]
    
    # === Payments ===
    YOOKASSA_SHOP_ID: Optional[str] = os.getenv("YOOKASSA_SHOP_ID")
    YOOKASSA_SECRET_KEY: Optional[str] = os.getenv("YOOKASSA_SECRET_KEY")
    
    # === CryptoBot ===
    CRYPTOBOT_API_TOKEN: Optional[str] = os.getenv("CRYPTOBOT_API_TOKEN")
    CRYPTOBOT_TESTNET: bool = os.getenv("CRYPTOBOT_TESTNET", "false").lower() == "true"
    
    # === Platega (SBP) ===
    PLATEGA_MERCHANT_ID: Optional[str] = os.getenv("PLATEGA_MERCHANT_ID")
    PLATEGA_API_KEY: Optional[str] = os.getenv("PLATEGA_API_KEY")
    
    # === Debug ===
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # === Paths ===
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    SERVICES_DIR: Path = SERVICES_DIR
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        errors = []
        
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        
        if not cls.ADMIN_IDS:
            errors.append("ADMIN_IDS is required (at least one admin)")
        
        if errors:
            for error in errors:
                print(f"❌ Config Error: {error}")
            return False
        
        return True
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in cls.ADMIN_IDS


config = Config()
