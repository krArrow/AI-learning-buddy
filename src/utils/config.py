"""
Configuration management using Pydantic Settings.
Loads environment variables and provides type-safe configuration access.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # OpenAI/Openrouter Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    openrouter_api_key: str = Field(..., description="Openrouter API key")
    openai_model: str = Field(..., description="Default OpenAI model")
    openai_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Model temperature")
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///data/learning_buddy.db",
        description="Database connection URL"
    )
    database_echo: bool = Field(default=False, description="Echo SQL statements")
    
    # Vector Store Configuration
    chroma_persist_directory: str = Field(
        default="data/vector_store",
        description="ChromaDB persistence directory"
    )
    chroma_collection_name: str = Field(
        default="learning_resources",
        description="ChromaDB collection name"
    )
    
    # Application Configuration
    app_name: str = Field(default="AI Learning Buddy", description="Application name")
    app_version: str = Field(default="2.1.4", description="Application version")
    debug_mode: bool = Field(default=False, description="Debug mode flag")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # LangGraph Configuration
    max_iterations: int = Field(default=10, ge=1, le=100, description="Max graph iterations")
    recursion_limit: int = Field(default=50, ge=10, le=200, description="Recursion limit")
    
    # Agent Configuration
    goal_clarifier_model: str = Field(
        ...,
        description="Model for goal clarification agent"
    )
    content_curator_model: str = Field(
        ...,
        description="Model for content curation agent"
    )
    assessment_agent_model: str = Field(
        ...,
        description="Model for assessment agent"
    )
    
    # Memory Configuration
    conversation_memory_size: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Max conversation history size"
    )
    learning_memory_size: int = Field(
        default=500,
        ge=50,
        le=5000,
        description="Max learning memory size"
    )
    
    # Feature Flags
    enable_vector_search: bool = Field(default=True, description="Enable vector search")
    enable_analytics: bool = Field(default=True, description="Enable analytics")
    enable_assessments: bool = Field(default=True, description="Enable assessments")


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance (singleton pattern).
    
    Returns:
        Settings: The application settings
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment (useful for testing).
    
    Returns:
        Settings: Freshly loaded settings
    """
    global _settings
    _settings = Settings()
    return _settings
