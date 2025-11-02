"""LLM Configuration Manager for loading provider profiles from config file"""

import os
import json
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LLMConfigManager:
    """Manages LLM provider configurations from config file"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to config file (default: llm_config.json in project root)
        """
        if config_path is None:
            # Default to llm_config.json in project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "llm_config.json"
        
        self.config_path = Path(config_path)
        self.config = None
        self._load_config()
    
    def _load_config(self):
        """Load and parse configuration file"""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            logger.info("You can create llm_config.json with provider profiles")
            self.config = {"providers": {}, "default_profile": None}
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # Validate structure
            if "providers" not in self.config:
                self.config["providers"] = {}
            
            # Substitute environment variables in API keys
            self._substitute_env_vars()
            
            logger.info(f"Loaded config from {self.config_path}")
            logger.info(f"Found {len(self.config.get('providers', {}))} provider profiles")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            self.config = {"providers": {}, "default_profile": None}
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            self.config = {"providers": {}, "default_profile": None}
    
    def _substitute_env_vars(self):
        """Substitute environment variables in config values"""
        if not self.config or "providers" not in self.config:
            return
        
        for profile_name, profile_data in self.config["providers"].items():
            if isinstance(profile_data, dict):
                # Substitute in api_key
                if "api_key" in profile_data:
                    api_key = profile_data["api_key"]
                    if isinstance(api_key, str) and api_key.startswith("${") and api_key.endswith("}"):
                        env_var = api_key[2:-1]
                        profile_data["api_key"] = os.getenv(env_var, api_key)
                        if profile_data["api_key"] == api_key:
                            logger.warning(f"Environment variable {env_var} not set for profile {profile_name}")
                
                # Substitute in base_url if present
                if "base_url" in profile_data:
                    base_url = profile_data["base_url"]
                    if isinstance(base_url, str) and base_url.startswith("${") and base_url.endswith("}"):
                        env_var = base_url[2:-1]
                        profile_data["base_url"] = os.getenv(env_var, base_url)
    
    def get_profile(self, profile_name: Optional[str] = None) -> Optional[Dict]:
        """
        Get provider configuration profile
        
        Args:
            profile_name: Name of profile (default: use default_profile from config)
            
        Returns:
            Profile dictionary with provider, api_key, model, base_url (optional)
            Returns None if profile not found
        """
        if not self.config or "providers" not in self.config:
            return None
        
        # Use default profile if not specified
        if profile_name is None:
            profile_name = self.config.get("default_profile")
            if profile_name is None:
                logger.warning("No profile specified and no default_profile in config")
                return None
        
        profile = self.config["providers"].get(profile_name)
        
        if profile is None:
            logger.error(f"Profile '{profile_name}' not found in config")
            available = list(self.config["providers"].keys())
            if available:
                logger.info(f"Available profiles: {', '.join(available)}")
            return None
        
        # Validate profile
        if not self.validate_profile(profile):
            logger.error(f"Invalid profile '{profile_name}'")
            return None
        
        logger.info(f"Using profile: {profile_name}")
        return profile
    
    def validate_profile(self, profile: Dict) -> bool:
        """
        Validate profile structure
        
        Args:
            profile: Profile dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["provider", "api_key", "model"]
        
        for field in required_fields:
            if field not in profile:
                logger.error(f"Profile missing required field: {field}")
                return False
            
            if not profile[field]:
                logger.error(f"Profile field '{field}' is empty")
                return False
        
        # Validate provider
        valid_providers = ["gemini", "glm", "openrouter", "openai"]
        if profile["provider"] not in valid_providers:
            logger.error(f"Invalid provider: {profile['provider']}. Must be one of: {valid_providers}")
            return False
        
        return True
    
    def list_profiles(self) -> Dict[str, Dict]:
        """
        List all available profiles
        
        Returns:
            Dictionary of profile names to profile configs
        """
        if not self.config or "providers" not in self.config:
            return {}
        
        return self.config["providers"].copy()
    
    def get_default_profile_name(self) -> Optional[str]:
        """Get the default profile name from config"""
        return self.config.get("default_profile") if self.config else None


def load_profile(profile_name: Optional[str] = None, config_path: Optional[str] = None) -> Optional[Dict]:
    """
    Convenience function to load a profile
    
    Args:
        profile_name: Name of profile to load
        config_path: Path to config file
        
    Returns:
        Profile dictionary or None
    """
    manager = LLMConfigManager(config_path)
    return manager.get_profile(profile_name)

