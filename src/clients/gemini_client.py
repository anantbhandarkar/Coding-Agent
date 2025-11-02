"""Gemini API client for LLM operations"""

import time
import logging
from typing import List, Optional, Dict, Any
import google.generativeai as genai
from ..utils.chunking import ChunkingStrategy, Chunk, Batch
from .base_llm_client import BaseLLMClient

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """Client for Google Gemini API with token management and retry logic"""
    
    def __init__(
        self,
        api_token: str,
        model: str,
        max_retries: int = 3,
        retry_backoff: List[float] = None,
        max_output_tokens: int = 8192
    ):
        """
        Initialize Gemini client
        
        Args:
            api_token: Google Gemini API token
            model: Model name (required, e.g., "gemini-2.5-flash")
            max_retries: Maximum retry attempts
            retry_backoff: Backoff delays in seconds for retries
            max_output_tokens: Maximum tokens in response
            
        Raises:
            ValueError: If model is empty or None
        """
        if not model or not model.strip():
            raise ValueError(
                "Model parameter is required. Please specify --model when running conversion. "
                "Example: --model gemini-2.5-flash"
            )
        
        self.api_token = api_token
        self.model_name = model.strip()
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff or [2, 5, 10]
        self.max_output_tokens = max_output_tokens
        self.chunking = ChunkingStrategy()
        
        # Configure Gemini
        genai.configure(api_key=api_token)
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate(self, prompt: str, max_tokens: int = None, temperature: float = 0.0, context: str = None) -> str:
        """
        Generate text using Gemini API with retry logic
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum output tokens (uses default if None)
            temperature: Sampling temperature
            context: Optional context string for logging (e.g., file path, operation name)
            
        Returns:
            Generated text
            
        Raises:
            Exception: If all retries fail
        """
        max_tokens = max_tokens or self.max_output_tokens
        
        # Log context if provided
        if context:
            logger.info(f"Processing: {context}")
        
        for attempt in range(self.max_retries):
            try:
                generation_config = genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature
                )
                
                # Configure safety settings to be very permissive for code conversion
                # Code analysis can trigger false positives, so we block only the most severe content
                safety_settings = [
                    {
                        "category": genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        "threshold": genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    },
                    {
                        "category": genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        "threshold": genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    },
                    {
                        "category": genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        "threshold": genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    },
                    {
                        "category": genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        "threshold": genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    },
                ]
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                
                # Check for finish reasons that indicate blocked content
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    finish_reason = candidate.finish_reason
                    
                    # Handle finish_reason as enum or integer
                    # Finish reason codes: 1=STOP (normal), 2=SAFETY, 3=RECITATION, 4=OTHER
                    finish_reason_value = finish_reason.value if hasattr(finish_reason, 'value') else finish_reason
                    
                    if finish_reason_value == 2:  # SAFETY
                        # Log which content triggered the safety filter
                        prompt_preview = prompt[:200] + "..." if len(prompt) > 200 else prompt
                        logger.error(f"Safety filter triggered. Context: {context or 'Unknown'}")
                        logger.error(f"Prompt preview: {prompt_preview}")
                        
                        # Try to identify potentially triggering words in prompt
                        triggering_words = []
                        try:
                            triggering_words = self._identify_potential_triggers(prompt)
                            if triggering_words:
                                logger.warning(f"Potentially triggering words found: {', '.join(triggering_words[:10])}")
                        except Exception as e:
                            logger.debug(f"Could not identify triggers: {e}")
                        
                        safety_ratings = getattr(candidate, 'safety_ratings', [])
                        safety_details = []
                        
                        # Extract safety rating details
                        if safety_ratings:
                            for rating in safety_ratings:
                                try:
                                    # Try different ways to access category and probability
                                    if hasattr(rating, 'category'):
                                        category = rating.category
                                        category_name = category.name if hasattr(category, 'name') else str(category)
                                    elif hasattr(rating, 'category_name'):
                                        category_name = rating.category_name
                                    else:
                                        category_name = "Unknown"
                                    
                                    if hasattr(rating, 'probability'):
                                        prob = rating.probability
                                        prob_name = prob.name if hasattr(prob, 'name') else str(prob)
                                        prob_value = prob.value if hasattr(prob, 'value') else None
                                        
                                        # Include ratings with any non-zero probability
                                        if prob_value is not None and prob_value > 0:
                                            safety_details.append(f"{category_name}: {prob_name}")
                                        elif prob_name and "NONE" not in prob_name.upper():
                                            safety_details.append(f"{category_name}: {prob_name}")
                                    elif hasattr(rating, 'probability_name'):
                                        prob_name = rating.probability_name
                                        if "NONE" not in prob_name.upper():
                                            safety_details.append(f"{category_name}: {prob_name}")
                                except Exception as e:
                                    logger.debug(f"Error extracting safety rating: {e}")
                                    continue
                        
                        # Also check response.prompt_feedback for safety issues
                        prompt_feedback = getattr(response, 'prompt_feedback', None)
                        if prompt_feedback:
                            fb_safety = getattr(prompt_feedback, 'safety_ratings', [])
                            for rating in fb_safety:
                                try:
                                    if hasattr(rating, 'category'):
                                        category = rating.category
                                        category_name = category.name if hasattr(category, 'name') else str(category)
                                        prob = getattr(rating, 'probability', None)
                                        if prob:
                                            prob_name = prob.name if hasattr(prob, 'name') else str(prob)
                                            if prob_name and "NONE" not in prob_name.upper():
                                                safety_details.append(f"Prompt {category_name}: {prob_name}")
                                except:
                                    pass
                        
                        details_str = ', '.join(safety_details) if safety_details else 'No details available'
                        
                        # Build error message with context
                        error_msg = f"Response blocked by safety filters (finish_reason=SAFETY)."
                        if context:
                            error_msg += f"\nContext: {context}"
                        error_msg += f"\nSafety ratings: {details_str}"
                        
                        if triggering_words:
                            error_msg += f"\nPotentially triggering words detected: {', '.join(triggering_words[:10])}"
                        
                        error_msg += (
                            "\n\nThis may happen if the code contains words/phrases that trigger safety filters."
                            "\nSuggested fixes:"
                            "\n  1. Try a different model (e.g., gemini-1.5-flash)"
                            "\n  2. Review the code for sensitive variable names, comments, or string literals"
                            "\n  3. The conversion may continue for other files that don't trigger safety filters"
                        )
                        
                        # Log full details for debugging
                        logger.error(f"Safety block details:\n{error_msg}")
                        
                        raise ValueError(error_msg)
                    elif finish_reason_value == 3:  # RECITATION
                        raise ValueError(
                            "Response blocked due to recitation policy. "
                            "The model detected potential verbatim content from training data."
                        )
                    elif finish_reason_value == 4:  # OTHER
                        raise ValueError(
                            f"Response blocked for unknown reason (finish_reason={finish_reason_value}). "
                            "Please try again or use a different model."
                        )
                    elif finish_reason_value == 1:  # STOP (normal completion)
                        # Normal completion - check if text is available
                        if hasattr(response, 'text') and response.text:
                            return response.text
                        else:
                            # Try to get text from candidate content
                            if candidate.content and candidate.content.parts:
                                text_parts = [part.text for part in candidate.content.parts if hasattr(part, 'text') and part.text]
                                if text_parts:
                                    return ''.join(text_parts)
                    
                    # If we get here, response is empty
                    raise ValueError(
                        f"Empty response from Gemini (finish_reason={finish_reason_value}). "
                        "The model did not generate any content."
                    )
                else:
                    # No candidates in response
                    raise ValueError(
                        "No candidates returned from Gemini API. "
                        "The response may have been filtered or the prompt may be invalid."
                    )
                    
            except ValueError as e:
                # Don't retry on ValueError (safety blocks, etc.) - these are final
                error_msg = str(e)
                if context:
                    logger.error(f"Gemini API request failed for '{context}': {error_msg}")
                else:
                    logger.error(f"Gemini API request failed: {error_msg}")
                raise
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_backoff[min(attempt, len(self.retry_backoff) - 1)]
                    logger.warning(
                        f"Gemini API call failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Gemini API call failed after {self.max_retries} attempts: {str(e)}")
                    raise
    
    def generate_batch(self, prompts: List[str]) -> List[str]:
        """
        Generate responses for multiple prompts (sequential for now)
        
        Args:
            prompts: List of prompts
            
        Returns:
            List of generated texts
        """
        results = []
        for i, prompt in enumerate(prompts):
            logger.info(f"Processing batch prompt {i + 1}/{len(prompts)}")
            result = self.generate(prompt)
            results.append(result)
        return results
    
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
        import json
        
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
            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            logger.error(f"Response text: {response_text[:500]}...")
            raise ValueError(f"Invalid JSON response from Gemini: {e}")
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        return self.chunking.estimate_tokens(text)
    
    def _identify_potential_triggers(self, prompt: str) -> List[str]:
        """
        Identify potentially triggering words/phrases in the prompt.
        This is a heuristic to help identify what might have triggered safety filters.
        
        Args:
            prompt: The prompt text to analyze
            
        Returns:
            List of potentially triggering words found
        """
        # Common words/phrases that might trigger safety filters in code context
        # This is a heuristic - actual triggers depend on Gemini's internal filters
        potential_triggers = []
        
        # Convert to lowercase for matching
        prompt_lower = prompt.lower()
        
        # Patterns that might trigger safety filters (context-dependent)
        trigger_patterns = [
            r'\b(hack|attack|exploit|vulnerability|inject|bypass)\w*\b',
            r'\b(kill|destroy|delete|remove|drop|truncate)\w*\b',
            r'\b(secret|password|token|credential|auth)\w*\b',
            r'\b(user|admin|root|privilege|access|permission)\w*\b',
            r'\b(data|info|personal|private|sensitive)\w*\b',
            r'\b(error|exception|fail|crash|bug|issue)\w*\b',
            r'\b(test|check|validate|verify|assert)\w*\b',
        ]
        
        import re
        for pattern in trigger_patterns:
            matches = re.findall(pattern, prompt_lower, re.IGNORECASE)
            for match in matches:
                if match not in potential_triggers:
                    potential_triggers.append(match)
        
        # Return unique triggers, limited to most relevant
        return list(set(potential_triggers))[:20]
    
    def chunk_text(self, text: str, max_tokens: int = 8000) -> List[str]:
        """
        Split text into chunks
        
        Args:
            text: Text to chunk
            max_tokens: Maximum tokens per chunk
            
        Returns:
            List of text chunks
        """
        chunks = self.chunking.chunk_file(text, max_tokens=max_tokens)
        return [chunk.content for chunk in chunks]
    
    def process_large_content(
        self,
        content: str,
        system_prompt: str,
        process_chunk_fn: callable = None,
        combine_results_fn: callable = None,
        context: str = None
    ) -> Any:
        """
        Process large content by chunking and combining results
        
        Args:
            content: Large content to process
            system_prompt: System prompt for each chunk
            process_chunk_fn: Optional function to process each chunk
            combine_results_fn: Optional function to combine chunk results
            
        Returns:
            Combined result
        """
        chunks = self.chunking.chunk_file(content)
        
        if not chunks:
            return None
        
        # If single chunk, process directly
        if len(chunks) == 1:
            prompt = f"{system_prompt}\n\nCode:\n{chunks[0].content}"
            chunk_context = f"{context} (single chunk)" if context else None
            if process_chunk_fn:
                return process_chunk_fn(self, prompt)
            return self.generate(prompt, context=chunk_context)
        
        # Process each chunk
        results = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i + 1}/{len(chunks)} ({chunk.estimated_tokens} tokens)")
            chunk_prompt = f"{system_prompt}\n\nCode (part {i + 1} of {len(chunks)}):\n{chunk.content}"
            chunk_context = f"{context} (chunk {i + 1}/{len(chunks)})" if context else None
            
            if process_chunk_fn:
                result = process_chunk_fn(self, chunk_prompt)
            else:
                result = self.generate(chunk_prompt, context=chunk_context)
            
            results.append(result)
        
        # Combine results
        if combine_results_fn:
            return combine_results_fn(results)
        
        # Default: combine as summary
        if len(results) > 1:
            combine_prompt = f"Combine these partial analyses into a single comprehensive result:\n\n" + \
                           "\n\n---\n\n".join(results)
            return self.generate(combine_prompt)
        
        return results[0] if results else None

