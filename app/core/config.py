from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings."""
    
    # File handling
    max_file_size: int = 5242880  # 5MB
    allowed_doc_types: List[str] = ["text/plain", "text/html", "application/pdf"]
    humansign_extension: str = ".humansign"
    
    # API settings
    debug: bool = True
    api_title: str = "HumanSign Decoder API"
    api_version: str = "1.0"
    
    # ML settings
    model_confidence_threshold: float = 0.7
    require_signature_verification: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()  # type: ignore