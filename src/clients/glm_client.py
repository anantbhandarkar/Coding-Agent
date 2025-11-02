"""GLM API client for LLM operations"""

import time
import json
import logging
import requests
from typing import List, Optional, Dict, Any
from .base_llm_client import BaseLLMClient
from ..utils.chunking import ChunkingStrategy

logger = logging.getLogger(__name__)


class GLMClient(BaseLLMClient):
    """Client for GLM API with custom URL support"""
    
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
        Initialize GLM client
        
        Args:
            api_token: GLM API token
            model: Model name (e.g., "glm-4-6")
            base_url: Base URL for GLM API endpoint (optional)
            max_retries: Maximum retry attempts
            retry_backoff: Backoff delays in seconds for retries
            max_output_tokens: Maximum tokens in response
        """
        if not model or not model.strip():
            raise ValueError("Model parameter is required for GLM client")
        
        self.api_token = api_token
        self.model_name = model.strip()
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff or [2, 5, 10]
        self.max_output_tokens = max_output_tokens
        self.chunking = ChunkingStrategy()
        
        # Set base URL - default GLM endpoint or custom
        if base_url:
            # Ensure URL doesn't end with chat/completions or /v1/chat/completions
            base_url = base_url.rstrip('/')
            if base_url.endswith('/v1/chat/completions'):
                base_url = base_url[:-20]
            elif base_url.endswith('/chat/completions'):
                base_url = base_url[:-16]
            
            # Handle z.ai API format: https://api.z.ai/api/coding/paas/v4
            # Try /chat/completions first (standard for this API)
            if 'api.z.ai' in base_url:
                self.base_url = base_url
                # z.ai API with /v4: use /chat/completions directly
                self.api_endpoint = f"{self.base_url}/chat/completions"
            else:
                self.base_url = base_url
                # Check if base_url already includes version path
                if '/v4' in self.base_url or '/v1' in self.base_url:
                    # If base_url has version, use /chat/completions directly
                    self.api_endpoint = f"{self.base_url}/chat/completions"
                else:
                    # Otherwise use /v1/chat/completions (standard OpenAI format)
                    self.api_endpoint = f"{self.base_url}/v1/chat/completions"
        else:
            # Default GLM endpoint (adjust based on actual GLM API)
            self.base_url = "https://open.bigmodel.cn/api/paas/v4"
            self.api_endpoint = f"{self.base_url}/chat/completions"
    
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.0,
        context: Optional[str] = None
    ) -> str:
        """
        Generate text using GLM API with retry logic
        
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
                
                # Parse GLM response format (OpenAI-compatible)
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    message = response_data["choices"][0].get("message", {})
                    content = message.get("content", "")
                    if content:
                        return content
                
                # Alternative format check
                if "text" in response_data:
                    return response_data["text"]
                
                raise ValueError(f"Unexpected response format: {response_data}")
                
            except requests.exceptions.HTTPError as e:
                # Try to get error details from response
                error_details = ""
                try:
                    if hasattr(response, 'text'):
                        error_details = f" Response: {response.text[:200]}"
                except:
                    pass
                
                if response.status_code == 401:
                    raise ValueError(f"Invalid API token: {e}{error_details}")
                elif response.status_code == 429:
                    wait_time = self.retry_backoff[min(attempt, len(self.retry_backoff) - 1)]
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Rate limited. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    raise ValueError(f"Rate limit exceeded: {e}{error_details}")
                elif response.status_code == 400:
                    # 400 Bad Request - don't retry, show error details
                    logger.error(f"Bad Request (400) from GLM API: {e}{error_details}")
                    logger.error(f"Endpoint: {self.api_endpoint}")
                    logger.error(f"Payload keys: {list(payload.keys())}")
                    raise ValueError(f"GLM API Bad Request (check endpoint URL, model name, or request format): {e}{error_details}")
                else:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_backoff[min(attempt, len(self.retry_backoff) - 1)]
                        logger.warning(f"HTTP error {response.status_code}: {e}{error_details}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    raise ValueError(f"GLM API error: {e}{error_details}")
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_backoff[min(attempt, len(self.retry_backoff) - 1)]
                    logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"GLM API call failed after {self.max_retries} attempts: {e}")
                    raise
            except (KeyError, ValueError) as e:
                logger.error(f"Failed to parse GLM response: {e}")
                raise ValueError(f"Invalid GLM response: {e}")
        
        raise ValueError("GLM API call failed after all retries")
    
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
            logger.error(f"Failed to parse JSON from GLM response: {e}")
            logger.error(f"Response text: {response_text[:500]}...")
            raise ValueError(f"Invalid JSON response from GLM: {e}")
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        return self.chunking.estimate_tokens(text)

