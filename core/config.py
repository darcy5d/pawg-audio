"""
Configuration Management System

This module provides a centralized configuration management system with environment-based settings,
secure API key management, and processing parameters.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import json
import logging
from dataclasses import dataclass, field
from enum import Enum

class Environment(Enum):
    """Enumeration of supported environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    url: str
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False
    connect_args: Dict[str, Any] = field(default_factory=dict)

@dataclass
class APIConfig:
    """API configuration settings."""
    base_url: str
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1

@dataclass
class ProcessingConfig:
    """Processing pipeline configuration settings."""
    batch_size: int = 100
    max_workers: int = 4
    timeout: int = 300
    retry_attempts: int = 3
    retry_delay: int = 5

@dataclass
class AnalysisConfig:
    """Analysis module configuration settings."""
    min_confidence: float = 0.7
    min_sentiment_magnitude: float = 0.5
    trend_window_days: int = 30
    prediction_window_days: int = 90
    entity_min_mentions: int = 5

@dataclass
class Config:
    """Main configuration class."""
    environment: Environment
    debug: bool
    database: DatabaseConfig
    api: APIConfig
    processing: ProcessingConfig
    analysis: AnalysisConfig
    api_keys: Dict[str, str] = field(default_factory=dict)
    plugins: Dict[str, Dict[str, Any]] = field(default_factory=dict)

class ConfigManager:
    """Manages configuration loading and access."""
    
    def __init__(self, env: Optional[Environment] = None):
        self.logger = logging.getLogger(__name__)
        self._config: Optional[Config] = None
        self._env = env or self._determine_environment()
        self._load_config()
    
    def _determine_environment(self) -> Environment:
        """Determine the current environment."""
        env = os.getenv("ENVIRONMENT", "development").lower()
        try:
            return Environment(env)
        except ValueError:
            self.logger.warning(f"Invalid environment '{env}', defaulting to development")
            return Environment.DEVELOPMENT
    
    def _load_config(self) -> None:
        """Load configuration from environment and config files."""
        # Load environment variables
        load_dotenv()
        
        # Load base config file
        config_path = Path("config") / f"{self._env.value}.json"
        if not config_path.exists():
            self.logger.warning(f"Config file not found: {config_path}")
            config_data = {}
        else:
            with open(config_path) as f:
                config_data = json.load(f)
        
        # Load API keys securely
        api_keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "cohere": os.getenv("COHERE_API_KEY")
        }
        
        # Create configuration objects
        self._config = Config(
            environment=self._env,
            debug=os.getenv("DEBUG", "false").lower() == "true",
            database=DatabaseConfig(**config_data.get("database", {})),
            api=APIConfig(**config_data.get("api", {})),
            processing=ProcessingConfig(**config_data.get("processing", {})),
            analysis=AnalysisConfig(**config_data.get("analysis", {})),
            api_keys=api_keys,
            plugins=config_data.get("plugins", {})
        )
    
    def get_config(self) -> Config:
        """Get the current configuration."""
        if not self._config:
            self._load_config()
        return self._config
    
    def reload_config(self) -> None:
        """Reload the configuration from files."""
        self._load_config()
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get an API key for a specific provider."""
        return self._config.api_keys.get(provider) if self._config else None
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get configuration for a specific plugin."""
        return self._config.plugins.get(plugin_name, {}) if self._config else {}
    
    def update_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """Update configuration for a specific plugin."""
        if self._config:
            self._config.plugins[plugin_name] = config
    
    def validate_config(self) -> bool:
        """Validate the current configuration."""
        if not self._config:
            return False
        
        # Validate required API keys
        required_keys = ["openai", "anthropic"]
        missing_keys = [key for key in required_keys if not self._config.api_keys.get(key)]
        if missing_keys:
            self.logger.error(f"Missing required API keys: {', '.join(missing_keys)}")
            return False
        
        # Validate database configuration
        if not self._config.database.url:
            self.logger.error("Missing database URL")
            return False
        
        return True 