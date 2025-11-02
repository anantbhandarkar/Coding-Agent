"""Token chunking and batching utilities for LLM operations"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Chunk:
    """Represents a chunk of code"""
    content: str
    start_line: int
    end_line: int
    estimated_tokens: int


@dataclass
class Batch:
    """Represents a batch of files for processing"""
    files: List[Dict]
    total_estimated_tokens: int


class ChunkingStrategy:
    """Handles chunking and batching of code for LLM processing"""
    
    # Approximate tokens per character (varies by language)
    # Java/JavaScript: ~4 characters per token on average
    TOKENS_PER_CHAR = 0.25
    
    def __init__(self, max_chunk_tokens: int = 8000, max_batch_tokens: int = 80000):
        """
        Initialize chunking strategy
        
        Args:
            max_chunk_tokens: Maximum tokens per chunk (default: 8k, safe for Gemini)
            max_batch_tokens: Maximum tokens per batch (default: 80k for batch processing)
        """
        self.max_chunk_tokens = max_chunk_tokens
        self.max_batch_tokens = max_batch_tokens
    
    def estimate_tokens(self, content: str) -> int:
        """
        Estimate token count for content
        
        Args:
            content: Text content to estimate
            
        Returns:
            Estimated token count
        """
        # Rough estimation: 4 chars per token for code
        # More accurate would use tiktoken, but this works for estimation
        return int(len(content) * self.TOKENS_PER_CHAR)
    
    def chunk_file(self, file_content: str, max_tokens: int = None) -> List[Chunk]:
        """
        Split a Java file into chunks by methods/classes
        
        Args:
            file_content: Full file content
            max_tokens: Override max chunk tokens
            
        Returns:
            List of Chunk objects
        """
        max_tokens = max_tokens or self.max_chunk_tokens
        
        # If file is small enough, return as single chunk
        if self.estimate_tokens(file_content) <= max_tokens:
            return [Chunk(
                content=file_content,
                start_line=1,
                end_line=file_content.count('\n') + 1,
                estimated_tokens=self.estimate_tokens(file_content)
            )]
        
        # Split by class boundaries first
        chunks = []
        lines = file_content.split('\n')
        
        # Find class boundaries
        class_pattern = r'^(public\s+)?(final\s+)?(abstract\s+)?class\s+\w+'
        interface_pattern = r'^(public\s+)?interface\s+\w+'
        enum_pattern = r'^(public\s+)?(enum\s+\w+|@\w+.*\s+enum)'
        
        current_chunk_lines = []
        current_start_line = 1
        brace_count = 0
        in_class = False
        
        for i, line in enumerate(lines, start=1):
            current_chunk_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            
            # Check if we're starting a new class/interface/enum
            if re.match(class_pattern, line.strip()) or \
               re.match(interface_pattern, line.strip()) or \
               re.match(enum_pattern, line.strip()):
                # If we have accumulated content and starting new class, chunk it
                if current_chunk_lines and in_class and brace_count == 0:
                    chunk_content = '\n'.join(current_chunk_lines[:-1])  # Exclude the new class line
                    if chunk_content.strip():
                        tokens = self.estimate_tokens(chunk_content)
                        if tokens > 0:
                            chunks.append(Chunk(
                                content=chunk_content,
                                start_line=current_start_line,
                                end_line=i - 1,
                                estimated_tokens=tokens
                            ))
                    current_chunk_lines = [line]
                    current_start_line = i
                    in_class = True
                    brace_count = 1
                else:
                    in_class = True
                    if brace_count == 0:
                        brace_count = 1
            
            # If chunk is getting too large and we're at a method boundary, split
            current_content = '\n'.join(current_chunk_lines)
            if self.estimate_tokens(current_content) > max_tokens and brace_count > 0:
                # Try to split at method boundary
                method_boundary = self._find_method_boundary(current_chunk_lines)
                if method_boundary > 0:
                    chunk_content = '\n'.join(current_chunk_lines[:method_boundary])
                    if chunk_content.strip():
                        tokens = self.estimate_tokens(chunk_content)
                        chunks.append(Chunk(
                            content=chunk_content,
                            start_line=current_start_line,
                            end_line=current_start_line + method_boundary - 1,
                            estimated_tokens=tokens
                        ))
                    current_chunk_lines = current_chunk_lines[method_boundary:]
                    current_start_line = current_start_line + method_boundary
        
        # Add remaining content as final chunk
        if current_chunk_lines:
            chunk_content = '\n'.join(current_chunk_lines)
            if chunk_content.strip():
                tokens = self.estimate_tokens(chunk_content)
                chunks.append(Chunk(
                    content=chunk_content,
                    start_line=current_start_line,
                    end_line=len(lines),
                    estimated_tokens=tokens
                ))
        
        # If still too large, split by methods more aggressively
        final_chunks = []
        for chunk in chunks:
            if chunk.estimated_tokens <= max_tokens:
                final_chunks.append(chunk)
            else:
                # Split by methods
                method_chunks = self._split_by_methods(chunk.content, max_tokens)
                for mc in method_chunks:
                    final_chunks.append(Chunk(
                        content=mc,
                        start_line=chunk.start_line,
                        end_line=chunk.end_line,
                        estimated_tokens=self.estimate_tokens(mc)
                    ))
        
        return final_chunks
    
    def _find_method_boundary(self, lines: List[str]) -> int:
        """Find a good split point (after a method)"""
        brace_count = 0
        for i, line in enumerate(lines):
            brace_count += line.count('{') - line.count('}')
            # If we complete a method (brace_count back to previous level)
            if i > 0 and brace_count <= 0:
                return i + 1
        return 0
    
    def _split_by_methods(self, content: str, max_tokens: int) -> List[str]:
        """Split content by method boundaries"""
        methods = []
        method_pattern = r'(public|private|protected)\s+.*?\s+\w+\s*\([^)]*\)\s*\{'
        
        # Find all method starts
        method_starts = []
        for match in re.finditer(method_pattern, content, re.MULTILINE):
            method_starts.append(match.start())
        
        if not method_starts:
            # No methods found, split by size
            return self._split_by_size(content, max_tokens)
        
        # Extract methods
        for i, start in enumerate(method_starts):
            end = method_starts[i + 1] if i + 1 < len(method_starts) else len(content)
            method = content[start:end]
            if self.estimate_tokens(method) <= max_tokens:
                methods.append(method)
            else:
                # Method itself is too large, split it
                methods.extend(self._split_by_size(method, max_tokens))
        
        return methods
    
    def _split_by_size(self, content: str, max_tokens: int) -> List[str]:
        """Split content by size when no good boundaries exist"""
        chunks = []
        estimated_total = self.estimate_tokens(content)
        num_chunks = (estimated_total // max_tokens) + 1
        
        chunk_size = len(content) // num_chunks
        for i in range(0, len(content), chunk_size):
            chunks.append(content[i:i + chunk_size])
        
        return chunks
    
    def chunk_interface(self, interface_content: str, max_tokens: int = None) -> List[Chunk]:
        """
        Split a Java interface into chunks by method signatures.
        
        This method is specifically designed for Spring Data repository interfaces
        which are interfaces (not classes) with only method signatures.
        
        Args:
            interface_content: Full interface content
            max_tokens: Override max chunk tokens
            
        Returns:
            List of Chunk objects, each preserving interface context
        """
        max_tokens = max_tokens or self.max_chunk_tokens
        
        # If interface is small enough, return as single chunk
        if self.estimate_tokens(interface_content) <= max_tokens:
            return [Chunk(
                content=interface_content,
                start_line=1,
                end_line=interface_content.count('\n') + 1,
                estimated_tokens=self.estimate_tokens(interface_content)
            )]
        
        # Extract interface declaration (signature with generics and extends)
        lines = interface_content.split('\n')
        interface_declaration = ""
        interface_start = 0
        interface_end = 0
        in_interface = False
        brace_count = 0
        
        # Find interface declaration
        interface_pattern = r'^(public\s+)?interface\s+\w+'
        for i, line in enumerate(lines, start=1):
            if re.match(interface_pattern, line.strip()) and not in_interface:
                interface_start = i
                in_interface = True
                brace_count = line.count('{') - line.count('}')
                interface_declaration = line
                # Continue collecting declaration lines until opening brace
                if '{' not in line:
                    for j in range(i, min(i + 10, len(lines))):
                        interface_declaration += '\n' + lines[j]
                        brace_count += lines[j].count('{') - lines[j].count('}')
                        if '{' in lines[j]:
                            interface_end = j + 1
                            break
                else:
                    interface_end = i + 1
                break
        
        if not interface_declaration:
            # Fallback: treat as regular file chunking
            return self.chunk_file(interface_content, max_tokens)
        
        # Extract methods from interface
        method_signatures = []
        current_method = []
        in_method = False
        method_brace_count = 0
        
        # Process lines after interface declaration
        for i in range(interface_end, len(lines)):
            line = lines[i]
            
            # Check for method signature (typically: modifier returnType methodName(params);)
            method_pattern = r'(?:public\s+)?(?:abstract\s+)?[\w<>\[\]]+\s+\w+\s*\([^)]*\)\s*(?:throws\s+[\w.]+)?\s*;'
            if re.search(method_pattern, line.strip()) or (in_method and line.strip().endswith(';')):
                if not in_method:
                    current_method = [line]
                    in_method = True
                else:
                    current_method.append(line)
                
                # Method ends with semicolon
                if line.strip().endswith(';'):
                    method_signatures.append({
                        'signature': '\n'.join(current_method),
                        'start_line': interface_end + len(method_signatures),
                        'end_line': i + 1
                    })
                    current_method = []
                    in_method = False
            elif in_method:
                current_method.append(line)
        
        # Group methods into chunks (3-5 methods per chunk, preserving interface context)
        chunks = []
        methods_per_chunk = 4  # Target number of methods per chunk
        
        for i in range(0, len(method_signatures), methods_per_chunk):
            method_group = method_signatures[i:i + methods_per_chunk]
            
            # Build chunk content: interface declaration + method group
            chunk_content = interface_declaration + '\n'
            
            for method in method_group:
                chunk_content += method['signature'] + '\n'
            
            # Estimate tokens
            estimated_tokens = self.estimate_tokens(chunk_content)
            
            # If chunk is too large, split method group further
            if estimated_tokens > max_tokens:
                # Split this group in half
                mid = len(method_group) // 2
                first_half = method_group[:mid]
                second_half = method_group[mid:]
                
                # First half chunk
                chunk_content_1 = interface_declaration + '\n'
                for method in first_half:
                    chunk_content_1 += method['signature'] + '\n'
                chunks.append(Chunk(
                    content=chunk_content_1,
                    start_line=interface_start,
                    end_line=first_half[-1]['end_line'] if first_half else interface_end,
                    estimated_tokens=self.estimate_tokens(chunk_content_1)
                ))
                
                # Second half chunk
                chunk_content_2 = interface_declaration + '\n'
                for method in second_half:
                    chunk_content_2 += method['signature'] + '\n'
                chunks.append(Chunk(
                    content=chunk_content_2,
                    start_line=interface_start,
                    end_line=second_half[-1]['end_line'] if second_half else interface_end,
                    estimated_tokens=self.estimate_tokens(chunk_content_2)
                ))
            else:
                chunks.append(Chunk(
                    content=chunk_content,
                    start_line=interface_start,
                    end_line=method_group[-1]['end_line'] if method_group else interface_end,
                    estimated_tokens=estimated_tokens
                ))
        
        return chunks if chunks else [Chunk(
            content=interface_content,
            start_line=1,
            end_line=len(lines),
            estimated_tokens=self.estimate_tokens(interface_content)
        )]
    
    def batch_files(self, files: List[Dict], max_batch_tokens: int = None) -> List[Batch]:
        """
        Group small files into batches for efficient processing
        
        Args:
            files: List of file metadata dicts with 'content' and 'path' keys
            max_batch_tokens: Override max batch tokens
            
        Returns:
            List of Batch objects
        """
        max_batch_tokens = max_batch_tokens or self.max_batch_tokens
        
        batches = []
        current_batch = []
        current_tokens = 0
        
        for file_info in files:
            content = file_info.get('content', '')
            file_tokens = self.estimate_tokens(content)
            
            # If single file exceeds batch limit, create single-file batch
            if file_tokens > max_batch_tokens:
                # Create batch with just this file
                if current_batch:
                    batches.append(Batch(
                        files=current_batch,
                        total_estimated_tokens=current_tokens
                    ))
                    current_batch = []
                    current_tokens = 0
                
                batches.append(Batch(
                    files=[file_info],
                    total_estimated_tokens=file_tokens
                ))
            else:
                # Add to current batch if space available
                if current_tokens + file_tokens <= max_batch_tokens:
                    current_batch.append(file_info)
                    current_tokens += file_tokens
                else:
                    # Start new batch
                    if current_batch:
                        batches.append(Batch(
                            files=current_batch,
                            total_estimated_tokens=current_tokens
                        ))
                    current_batch = [file_info]
                    current_tokens = file_tokens
        
        # Add remaining batch
        if current_batch:
            batches.append(Batch(
                files=current_batch,
                total_estimated_tokens=current_tokens
            ))
        
        return batches

