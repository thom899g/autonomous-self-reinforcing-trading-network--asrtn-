"""
ASRTN Configuration Module
Centralized configuration management with environment variable support.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field, validator
from loguru import logger

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TradingConfig(BaseSettings):
    """Trading system configuration"""
    
    # Firebase Configuration (CRITICAL - per ecosystem requirements)
    firebase_project_id: str = Field(..., env="FIREBASE_PROJECT_ID")
    firebase_service_account_path: Path = Field(
        default=project_root / "config" / "firebase-service-account.json",
        env="FIREBASE_SERVICE_ACCOUNT_PATH"
    )
    
    # Trading Parameters
    initial_balance: float = Field(default=100000.0, ge=0.0)
    max_position_size: float = Field(default=0.1, ge=0.0, le=1.0)  # 10% of portfolio
    transaction_cost: float = Field(default=0.001, ge=0.0)  # 0.1% per trade
    risk_free_rate: float = Field(default=0.02, ge=0.0)
    
    # RL Training Parameters
    learning_rate: float = Field(default=0.0003, ge=0.0)
    gamma: float = Field(default=0.99, ge=0.0, le=1.0)
    batch_size: int = Field(default=64, ge=1)
    buffer_size: int = Field(default=10000, ge=1000)
    
    # Evolutionary Algorithm Parameters
    population_size: int = Field(default=50, ge=10)
    mutation_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    crossover_rate: float = Field(default=0.7, ge=0.0, le=1.0)
    elite_size: int = Field(default=5, ge=1)
    
    # Market Data Configuration
    data_sources: Dict[str, str] = Field(default={
        "crypto": "ccxt",
        "stocks": "yfinance",
        "forex": "oanda"
    })
    timeframe: str = Field(default="1h")
    lookback_window: int = Field(default=100, ge=10)
    
    # Distributed Computing
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    num_workers: int = Field(default=4, ge=1)
    
    # Risk Management
    max_drawdown_threshold: float = Field(default=0.2, ge=0.0, le=1.0)
    var_confidence: float = Field(default=0.95, ge=0.5, le=0.99)
    stop_loss_pct: float = Field(default=0.05, ge=0.0, le=0.5)
    
    class Config:
        env_file = project_root / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @validator("firebase_service_account_path")
    def validate_firebase_path(cls, v: Path) -> Path:
        """Validate Firebase service account file exists"""
        if not v.exists():
            logger.error(f"Firebase service account file not found: {v}")
            raise FileNotFoundError(f"Firebase service account file not found: {v}")
        return v
    
    @validator("max_position_size")
    def validate_position_size(cls, v: float, values: Dict[str, Any]) -> float:
        """Ensure position size is reasonable relative to balance"""
        initial_balance = values.get("initial_balance", 100000.0)
        max_position_value = v * initial_balance
        if max_position_value < 100:  # Minimum trade size
            logger.warning(f"Max position value ${max_position_value} is below minimum trade size")
        return v


def load_config(config_path: Optional[Path] = None) -> TradingConfig:
    """
    Load configuration with error handling
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        TradingConfig instance
        
    Raises: