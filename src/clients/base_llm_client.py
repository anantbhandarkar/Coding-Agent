"""Base LLM client interface for all provider implementations"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Callable


class BaseLLMClient(ABC):
    """Abstract base class for all LLM provider clients"""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.0,
        context: Optional[str] = None
    ) -> str:
        """
        Generate text response from LLM
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum output tokens
            temperature: Sampling temperature
            context: Optional context string for logging
            
        Returns:
            Generated text response
            
        Raises:
            ValueError: If generation fails (safety blocks, etc.)
            Exception: If API call fails
        """
        pass
    
    @abstractmethod
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
            
        Raises:
            ValueError: If JSON parsing fails or generation fails
        """
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        pass
    
    def process_large_content(
        self,
        content: str,
        system_prompt: str,
        process_chunk_fn: Optional[Callable] = None,
        combine_results_fn: Optional[Callable] = None,
        context: Optional[str] = None
    ) -> Any:
        """
        Process large content by chunking and combining results
        
        Args:
            content: Large content to process
            system_prompt: System prompt for each chunk
            process_chunk_fn: Optional function to process each chunk
            combine_results_fn: Optional function to combine chunk results
            context: Optional context string for logging
            
        Returns:
            Combined result
        """
        # Default implementation - can be overridden by subclasses
        from ..utils.chunking import ChunkingStrategy
        
        chunking = ChunkingStrategy()
        chunks = chunking.chunk_file(content)
        
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
        import logging
        logger = logging.getLogger(__name__)
        
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
                           "\n\n---\n\n".join([str(r) for r in results])
            return self.generate(combine_prompt, context=context)
        
        return results[0] if results else None
    
    def chunk_text(self, text: str, max_tokens: int = 8000) -> List[str]:
        """
        Split text into chunks
        
        Args:
            text: Text to chunk
            max_tokens: Maximum tokens per chunk
            
        Returns:
            List of text chunks
        """
        from ..utils.chunking import ChunkingStrategy
        chunking = ChunkingStrategy()
        chunks = chunking.chunk_file(text, max_tokens=max_tokens)
        return [chunk.content for chunk in chunks]

