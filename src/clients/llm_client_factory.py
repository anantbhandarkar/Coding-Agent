"""Factory for creating LLM client instances"""

import logging
from typing import Optional
from .base_llm_client import BaseLLMClient
from .gemini_client import GeminiClient
from .glm_client import GLMClient
from .openrouter_client import OpenRouterClient
from .openai_client import OpenAIClient
from ..config.llm_config_manager import LLMConfigManager

logger = logging.getLogger(__name__)


def create_llm_client(
    provider: str,
    api_token: str,
    model: str,
    base_url: Optional[str] = None,
    config_path: Optional[str] = None
) -> BaseLLMClient:
    """
    Factory function to create LLM client instance
    
    Args:
        provider: Provider name ("gemini", "glm", "openrouter", "openai")
        api_token: API token for the provider
        model: Model name
        base_url: Optional base URL (for GLM/OpenAI custom endpoints)
        config_path: Optional path to config file (if loading from profile)
        
    Returns:
        LLM client instance
        
    Raises:
        ValueError: If provider is invalid or required parameters are missing
    """
    provider = provider.lower().strip()
    
    if provider == "gemini":
        return GeminiClient(api_token=api_token, model=model)
    
    elif provider == "glm":
        return GLMClient(api_token=api_token, model=model, base_url=base_url)
    
    elif provider == "openrouter":
        return OpenRouterClient(api_token=api_token, model=model)
    
    elif provider == "openai":
        return OpenAIClient(api_token=api_token, model=model, base_url=base_url)
    
    else:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Supported providers: gemini, glm, openrouter, openai"
        )


def create_llm_client_from_profile(
    profile_name: Optional[str] = None,
    config_path: Optional[str] = None,
    model_override: Optional[str] = None
) -> BaseLLMClient:
    """
    Create LLM client from configuration profile
    
    Args:
        profile_name: Name of profile in config file (default: use default_profile)
        config_path: Path to config file (default: llm_config.json in project root)
        model_override: Optional model name to override profile's model
        
    Returns:
        LLM client instance
        
    Raises:
        ValueError: If profile not found or invalid
    """
    manager = LLMConfigManager(config_path)
    profile = manager.get_profile(profile_name)
    
    if profile is None:
        available = list(manager.list_profiles().keys())
        if available:
            raise ValueError(
                f"Profile '{profile_name}' not found. Available profiles: {', '.join(available)}"
            )
        else:
            raise ValueError(
                f"No profiles found in config file. Please create llm_config.json with provider profiles."
            )
    
    provider = profile["provider"]
    api_token = profile["api_key"]
    model = model_override or profile["model"]  # Use override if provided, else profile model
    base_url = profile.get("base_url")
    
    logger.info(f"Creating {provider} client with model: {model}")
    return create_llm_client(
        provider=provider,
        api_token=api_token,
        model=model,
        base_url=base_url,
        config_path=config_path
    )


def create_llm_client_from_config(
    provider: Optional[str] = None,
    api_token: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    profile_name: Optional[str] = None,
    config_path: Optional[str] = None
) -> BaseLLMClient:
    """
    Create LLM client with flexible configuration options
    
    Priority:
    1. Direct parameters (provider, api_token, model) - if all provided
    2. Profile name with model override - if profile_name and model provided
    3. Profile name - if provided (uses profile's model)
    4. Default profile from config - if exists
    
    Args:
        provider: Provider name (optional if using profile)
        api_token: API token (optional if using profile)
        model: Model name (required, can override profile's model)
        base_url: Base URL (optional, for GLM/OpenAI)
        profile_name: Profile name from config (optional)
        config_path: Path to config file (optional)
        
    Returns:
        LLM client instance
        
    Raises:
        ValueError: If configuration is invalid
    """
    # If all direct parameters provided, use them
    if provider and api_token and model:
        return create_llm_client(
            provider=provider,
            api_token=api_token,
            model=model,
            base_url=base_url,
            config_path=config_path
        )
    
    # If profile name provided, use profile (with model override if provided)
    if profile_name:
        return create_llm_client_from_profile(
            profile_name=profile_name,
            config_path=config_path,
            model_override=model  # Model can override profile's model
        )
    
    # Try default profile (with model override if provided)
    try:
        return create_llm_client_from_profile(
            config_path=config_path,
            model_override=model  # Model can override profile's model
        )
    except ValueError:
        # If no profile available, require direct parameters
        if not provider or not api_token or not model:
            raise ValueError(
                "Either provide (provider, api_token, model) directly or configure profiles in llm_config.json"
            )
        return create_llm_client(
            provider=provider,
            api_token=api_token,
            model=model,
            base_url=base_url
        )

