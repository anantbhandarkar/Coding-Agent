"""OpenAI API client for LLM operations"""

import time
import json
import logging
import requests
from typing import List, Optional, Dict, Any
from .base_llm_client import BaseLLMClient
from ..utils.chunking import ChunkingStrategy

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI API with custom URL support"""
    
    def __init__(
        self,
        api_token: str,
        model: str,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        retry_backoff: List[float] = None,
        max_output_tokens: int = 8192
    ):
        """
        Initialize OpenAI client
        
        Args:
            api_token: OpenAI API token
            model: Model name (e.g., "gpt-4o", "gpt-5-codex")
            base_url: Base URL for OpenAI API endpoint (optional, defaults to official API)
            max_retries: Maximum retry attempts
            retry_backoff: Backoff delays in seconds for retries
            max_output_tokens: Maximum tokens in response
        """
        if not model or not model.strip():
            raise ValueError("Model parameter is required for OpenAI client")
        
        self.api_token = api_token
        self.model_name = model.strip()
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff or [2, 5, 10]
        self.max_output_tokens = max_output_tokens
        self.chunking = ChunkingStrategy()
        
        # Set base URL - default OpenAI endpoint or custom
        if base_url:
            # Ensure URL doesn't end with /v1/chat/completions
            base_url = base_url.rstrip('/')
            if base_url.endswith('/v1/chat/completions'):
                base_url = base_url[:-20]
            self.base_url = base_url
        else:
            # Default OpenAI endpoint
            self.base_url = "https://api.openai.com"
        
        self.api_endpoint = f"{self.base_url}/v1/chat/completions"
    
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.0,
        context: Optional[str] = None
    ) -> str:
        """
        Generate text using OpenAI API with retry logic
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum output tokens (uses default if None)
            temperature: Sampling temperature
            context: Optional context string for logging
            
        Returns:
            Generated text
        """
        max_tokens = max_tokens or self.max_output_tokens
        
        if context:
            logger.info(f"Processing: {context}")
        
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=120
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                # Parse OpenAI response format
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    message = response_data["choices"][0].get("message", {})
                    content = message.get("content", "")
                    if content:
                        return content
                
                raise ValueError(f"Unexpected response format: {response_data}")
                
            except requests.exceptions.HTTPError as e:
                if response.status_code == 401:
                    raise ValueError(f"Invalid API token: {e}")
                elif response.status_code == 429:
                    wait_time = self.retry_backoff[min(attempt, len(self.retry_backoff) - 1)]
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Rate limited. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    raise ValueError(f"Rate limit exceeded: {e}")
                else:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_backoff[min(attempt, len(self.retry_backoff) - 1)]
                        logger.warning(f"HTTP error {response.status_code}: {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    raise ValueError(f"OpenAI API error: {e}")
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_backoff[min(attempt, len(self.retry_backoff) - 1)]
                    logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"OpenAI API call failed after {self.max_retries} attempts: {e}")
                    raise
            except (KeyError, ValueError) as e:
                logger.error(f"Failed to parse OpenAI response: {e}")
                raise ValueError(f"Invalid OpenAI response: {e}")
        
        raise ValueError("OpenAI API call failed after all retries")
    
    def generate_structured(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ) -> Dict:
        """
        Generate structured JSON response
        
        Args:
            prompt: Input prompt with JSON schema instruction
            schema: Optional JSON schema to include in prompt
            context: Optional context string for logging
            
        Returns:
            Parsed JSON dictionary
        """
        # Add schema instruction if provided
        if schema:
            schema_prompt = f"{prompt}\n\nReturn response as valid JSON matching this schema: {json.dumps(schema)}"
        else:
            schema_prompt = f"{prompt}\n\nReturn response as valid JSON."
        
        response_text = self.generate(schema_prompt, context=context)
        
        # Try to extract JSON from response
        try:
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OpenAI response: {e}")
            logger.error(f"Response text: {response_text[:500]}...")
            raise ValueError(f"Invalid JSON response from OpenAI: {e}")
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        return self.chunking.estimate_tokens(text)

