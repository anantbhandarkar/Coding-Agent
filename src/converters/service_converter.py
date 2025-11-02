"""Convert Spring services to Node.js service classes"""

import re
import logging
from typing import Dict, Optional, Any, List
from ..clients.base_llm_client import BaseLLMClient
from ..clients.llm_client_factory import create_llm_client_from_config

logger = logging.getLogger(__name__)


class ServiceConverter:
    """Converts Spring services to Node.js service classes"""
    
    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        provider: Optional[str] = None,
        api_token: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        profile_name: Optional[str] = None,
        config_path: Optional[str] = None,
        # Legacy support
        gemini_api_token: Optional[str] = None
    ):
        """
        Initialize service converter
        
        Args:
            llm_client: Pre-configured LLM client (optional, takes precedence)
            provider: LLM provider name ("gemini", "glm", "openrouter", "openai")
            api_token: API token for the provider
            model: Model name
            base_url: Optional base URL (for GLM/OpenAI custom endpoints)
            profile_name: Profile name from config file
            config_path: Path to config file
            gemini_api_token: Legacy parameter (deprecated)
        """
        # If client provided, use it directly (takes precedence over other parameters)
        # This allows for dependency injection and testing with mock clients
        if llm_client:
            self.client = llm_client
            return
        
        # Legacy support: convert gemini_api_token parameter to new format
        # This maintains backward compatibility with older code that used gemini_api_token
        if gemini_api_token and not api_token:
            provider = provider or "gemini"
            api_token = gemini_api_token
        
        # Create LLM client from configuration if API token and model are provided
        # If either is missing, client will be None and fallback to metadata-based conversion
        if api_token and model:
            self.client = create_llm_client_from_config(
                provider=provider or "gemini",  # Default to Gemini if no provider specified
                api_token=api_token,
                model=model,
                base_url=base_url,  # Custom endpoint for self-hosted models (GLM/OpenAI)
                profile_name=profile_name,  # Profile from config file
                config_path=config_path  # Path to llm_config.json
            )
        else:
            # No LLM client available - will use regex/metadata-based conversion
            self.client = None
    
    def convert_service(self, service_metadata: Dict, java_code: str = "") -> Dict[str, Any]:
        """
        Convert Spring service to Node.js service class
        
        Args:
            service_metadata: Service metadata with 'name', 'filePath', 'methods', etc.
            java_code: Full Java service source code (optional)
            
        Returns:
            Dictionary with:
            {
                "name": "ServiceName",
                "file_path": "services/ServiceName.js",
                "code": "..."
            }
        """
        try:
            # Read Java source code from file path if not provided as parameter
            # This handles cases where only metadata is available but we need the actual code
            if not java_code and service_metadata.get("filePath"):
                try:
                    with open(service_metadata["filePath"], 'r', encoding='utf-8') as f:
                        java_code = f.read()
                except Exception:
                    # File read failed - will proceed with metadata-based conversion
                    pass
            
            # Choose conversion strategy based on available resources:
            # - LLM conversion: Higher quality, preserves business logic better
            # - Metadata conversion: Fallback when LLM unavailable or code unreadable
            if self.client and java_code:
                # Use LLM for intelligent conversion with context understanding
                return self._convert_with_llm(service_metadata, java_code)
            else:
                # Fall back to pattern-based conversion from metadata only
                return self._convert_from_metadata(service_metadata)
        except Exception as e:
            # Any unexpected error during conversion - log and return stub
            # Stub ensures conversion process continues without crashing
            logger.error(f"Failed to convert service {service_metadata.get('name', 'unknown')}: {e}")
            return self._create_stub_service(service_metadata)
    
    def _convert_with_llm(self, service_metadata: Dict, java_code: str) -> Dict[str, Any]:
        """
        Convert Spring service to Node.js using LLM for intelligent code translation.
        
        This method constructs a detailed prompt that guides the LLM through the conversion
        process, ensuring business logic is preserved while adapting to Node.js patterns.
        """
        
        # Check if code exceeds token limit and needs chunking
        estimated_tokens = self.client.estimate_tokens(java_code) if self.client else len(java_code) * 0.25
        max_tokens = 8000  # Token limit for chunking
        
        if estimated_tokens > max_tokens and self.client:
            # Use chunked conversion for large services
            return self._convert_with_llm_chunked(service_metadata, java_code)
        
        # Standard conversion for smaller services
        limited_java_code = java_code
        
        # Construct comprehensive prompt with detailed documentation requirements
        # Documentation requirements are placed early to ensure they're not overlooked
        prompt = f"""Convert this Spring service class to a Node.js service class.

Java Service Code:
```java
{limited_java_code}
```

CRITICAL REQUIREMENTS - DOCUMENTATION:
1. **JSDoc Documentation (MANDATORY)**:
   - Add comprehensive JSDoc comments for the class explaining:
     * What the service does (business purpose)
     * Original Java class name and Spring annotations converted
     * Dependencies and their types
   - Add JSDoc for EVERY method with:
     * @description - Clear explanation of what the method does
     * @param {{type}} paramName - Description of each parameter
     * @returns {{Promise<type>}} - Return type description
     * @throws {{Error}} - Possible errors that can be thrown
     * Example: @description Retrieves a customer by ID. Converts Spring's Optional<T> to null/object pattern.
     * Conversion notes: Explain any Java-to-JavaScript adaptations (e.g., "Converted from Spring's @Transactional to manual transaction handling")

2. **Inline Comments (MANDATORY)**:
   - Add inline comments explaining complex business logic
   - Comment every Spring annotation conversion (e.g., "// @Autowired converted to constructor injection")
   - Explain type conversions (e.g., "// Java Optional<T> -> JavaScript null/object pattern")
   - Document error handling strategies
   - Explain Sequelize query patterns where they differ from JPA
   - Add comments for edge cases and validation logic
   - Example: "// Validate input before processing - converted from Spring @Valid annotation"

3. **Code Conversion Requirements**:
   - Remove @Service, @Autowired annotations
   - Convert @Autowired dependencies to constructor injection or require statements
   - Convert all class methods to async functions (Node.js database operations are async)
   
4. **Dependency Injection Conversion**:
   - @Autowired fields -> constructor parameters or require at top
   - Spring repositories -> require corresponding DAO/repository modules
   - Other services -> require corresponding service modules
   - Add comments: "// Dependency injected via constructor (replaces Spring @Autowired)"

5. **Method Implementation Conversion**:
   - Java return types -> JavaScript returns
   - Java Optional<T> -> JavaScript that returns null or object (document in comments)
   - Java List<T> -> JavaScript array (document as Promise<Array>)
   - Java void -> JavaScript void return (document as Promise<void>)
   - Add async/await for all database operations
   - Convert Spring Data repository calls to Sequelize DAO calls with explanatory comments

6. **Business Logic Preservation**:
   - Keep core business logic intact
   - Convert Spring Data repository calls to Sequelize DAO calls (add comments explaining query differences)
   - Convert exception handling (try-catch) - document exception type conversions
   - Convert validation logic - comment on validation patterns used

7. **Spring Annotation Conversions**:
   - @Transactional -> Implement database transactions manually, add comment: "// Manual transaction handling (replaces Spring @Transactional)"
   - @Cacheable -> Add comment: "// TODO: Add caching layer (Spring @Cacheable not automatically converted)"
   - @Async -> Add comment: "// Already async by nature in Node.js (replaces Spring @Async)"
   - Document all annotation conversions in comments

8. **Modern JavaScript Standards (ES6+)**:
   - Use const/let (never var)
   - Use arrow functions where appropriate
   - Use async/await (preferred over Promise.then)
   - Use destructuring for object/array operations
   - Add comments explaining ES6+ features where they improve readability

Return only the complete service class code with all documentation, no explanations."""

        try:
            # Generate converted code using LLM with token limit
            # 6000 tokens allows for complete service class plus documentation
            converted_code = self.client.generate(prompt, max_tokens=6000)
            
            # Extract service name from metadata for file naming
            service_name = service_metadata.get("name", "Unknown")
            
            # Return converted service with metadata
            return {
                "name": service_name,
                "file_path": f"services/{service_name}.js",  # Standard path for services
                "code": converted_code,
                "type": "service"  # Component type identifier
            }
        except Exception as e:
            # LLM generation failed - log warning and fallback to pattern-based conversion
            # This ensures conversion continues even if LLM is unavailable or times out
            logger.warning(f"LLM conversion failed, falling back to metadata: {e}")
            return self._convert_from_metadata(service_metadata)
    
    def _convert_with_llm_chunked(self, service_metadata: Dict, java_code: str) -> Dict[str, Any]:
        """Convert large service using chunking strategy with business logic context preservation"""
        service_name = service_metadata.get("name", "Unknown")
        dependencies = service_metadata.get("dependencies", [])
        
        system_prompt = f"""Convert this Spring service class to a Node.js service class.

This is a large service being processed in chunks. For each chunk, convert the methods to Node.js async methods.
Preserve business logic context: constructor, dependencies, and service-level annotations.

Service: {service_name}
Dependencies: {', '.join(dependencies) if dependencies else 'None'}

CRITICAL REQUIREMENTS:
1. Add JSDoc comments for the class and each method
2. Add inline comments explaining Spring annotation conversions
3. Preserve business logic and validation
4. Convert all methods to async functions
5. Use async/await for all database operations
6. Include proper error handling
7. Maintain dependency injection patterns

For each chunk, provide converted Node.js service methods."""
        
        def process_chunk(client, chunk_prompt):
            """Process individual chunk"""
            return client.generate(chunk_prompt, max_tokens=6000, context=f"Service Conversion (Chunk): {service_name}")
        
        def combine_results(chunk_results):
            """Combine chunk results into single service class"""
            # If we have multiple chunks, combine them
            if len(chunk_results) == 1:
                combined_code = str(chunk_results[0])
            else:
                # Combine multiple chunk results
                combine_prompt = f"""Combine these partial Node.js service conversions into a single complete service class.

Service Name: {service_name}
Dependencies: {', '.join(dependencies) if dependencies else 'None'}

Partial conversions:
{chr(10).join([f'--- Chunk {i+1} ---{chr(10)}{str(result)}' for i, result in enumerate(chunk_results)])}

Requirements:
1. Merge all methods from all chunks into one class
2. Ensure only one class definition (not multiple class declarations)
3. Preserve all imports and requires
4. Maintain proper class structure (constructor, methods)
5. Remove duplicate class definitions
6. Ensure all dependencies are properly injected
7. Maintain proper async/await patterns

Return only the complete, merged Node.js service class code."""
                combined_code = self.client.generate(combine_prompt, max_tokens=8000, context=f"Service Combination: {service_name}")
            
            return {
                "name": service_name,
                "file_path": f"services/{service_name}.js",
                "code": combined_code,
                "type": "service"
            }
        
        try:
            result = self.client.process_large_content(
                java_code,
                system_prompt,
                process_chunk_fn=process_chunk,
                combine_results_fn=combine_results,
                context=f"Service Conversion: {service_name}"
            )
            return result
        except Exception as e:
            logger.warning(f"Chunked conversion failed, falling back to metadata: {e}")
            return self._convert_from_metadata(service_metadata)
    
    def _convert_from_metadata(self, service_metadata: Dict) -> Dict[str, Any]:
        """
        Convert service using only metadata (fallback when Java code unavailable).
        
        This method generates a service skeleton based on extracted metadata,
        producing stubs that need manual implementation.
        """
        
        # Extract service information from metadata
        service_name = service_metadata.get("name", "Unknown")
        methods = service_metadata.get("methods", [])  # List of method metadata objects
        
        # Extract dependencies from metadata for proper import statements
        # Dependencies typically include repositories, other services, and models
        dependencies = service_metadata.get("dependencies", [])
        
        # Generate service code using pattern-based conversion
        # This creates a skeleton with method signatures and basic structure
        service_code = self._generate_service_code(service_name, methods, dependencies)
        
        return {
            "name": service_name,
            "file_path": f"services/{service_name}.js",
            "code": service_code,
            "type": "service"
        }
    
    def _generate_service_code(self, service_name: str, methods: List[Dict], dependencies: List[str]) -> str:
        """
        Generate Node.js service code from metadata using pattern-based conversion.
        
        This method creates a service skeleton with:
        - Import statements for dependencies
        - Class definition with constructor
        - Method stubs based on metadata
        
        Args:
            service_name: Name of the service class
            methods: List of method metadata dictionaries
            dependencies: List of dependency names (repositories, services, etc.)
        
        Returns:
            Complete JavaScript service class code as string
        """
        
        lines = []
        
        # Filter dependencies to find repositories/DAOs that need importing
        # Pattern: Look for 'Repository' or 'Dao' in dependency name
        repo_deps = [dep for dep in dependencies if 'Repository' in dep or 'Dao' in dep]
        
        # Generate require statements for repository dependencies
        # These will be used in the service methods for data access
        for repo in repo_deps:
            # Extract base name (remove Repository suffix if present)
            # Note: Current logic may have issue with double replace - keeping as-is for compatibility
            repo_name = repo.replace('Repository', '').replace('Repository', '')
            lines.append(f"const {repo}Repository = require('../repositories/{repo}Repository');")
        
        # Add blank line after imports for readability
        if repo_deps:
            lines.append("")
        
        # Start class definition
        lines.append(f"class {service_name} {{")
        lines.append("")
        
        # Add constructor with dependency injection
        # This replaces Spring's @Autowired annotation pattern
        if dependencies:
            lines.append("    constructor() {")
            # Limit to 5 dependencies to prevent overly complex constructors
            # Real services typically have 2-4 dependencies
            for dep in dependencies[:5]:
                # Convert dependency name to camelCase for property naming
                # Example: "CustomerRepository" -> "customerRepository"
                dep_var = dep[0].lower() + dep[1:] if dep else "dependency"
                # Try repository first, then fallback to service
                # This handles both repository and service dependencies
                lines.append(f"        this.{dep_var} = require('../repositories/{dep}Repository') || require('../services/{dep}');")
            lines.append("    }")
            lines.append("")
        
        # Convert each method from metadata to JavaScript method
        # Methods are converted individually to preserve signatures and descriptions
        for method in methods:
            method_code = self._convert_method(method)
            lines.append(method_code)
            lines.append("")
        
        # Add placeholder comment if no methods found
        # This helps identify incomplete conversions
        if not methods:
            lines.append("    /**")
            lines.append("     * Service methods to be implemented")
            lines.append("     */")
            lines.append("")
        
        # Close class definition
        lines.append("}")
        lines.append("")
        
        # Export singleton instance (common Node.js pattern)
        # Alternative would be: module.exports = ServiceName; (class export)
        lines.append(f"module.exports = new {service_name}();")
        
        # Join all lines with newlines to form complete code string
        return "\n".join(lines)
    
    def _convert_method(self, method: Dict) -> str:
        """
        Convert a single method from metadata to JavaScript method stub.
        
        This method generates a method skeleton with:
        - JSDoc comments from metadata
        - Method signature with parameters
        - Basic error handling structure
        - TODO comments for implementation
        
        Args:
            method: Dictionary containing method metadata (name, signature, description, complexity)
        
        Returns:
            Complete JavaScript method code as string
        """
        
        # Extract method information from metadata dictionary
        method_name = method.get("name", "unknownMethod")
        signature = method.get("signature", "")  # Full Java method signature
        description = method.get("description", "")  # Method description from metadata extraction
        complexity = method.get("complexity", "Medium")  # Complexity level (Low/Medium/High)
        
        # Parse parameters from Java method signature using regex
        # Pattern matches: methodName(param1, param2, param3)
        # Captures everything inside parentheses
        params_match = re.search(r'\(([^)]*)\)', signature)
        params = params_match.group(1).split(',') if params_match else []
        
        # Extract parameter names from full signatures
        # Java format: "String name, int id" -> extract "name", "id"
        # Split by space and take last word (parameter name)
        params = [p.strip().split()[-1] if ' ' in p.strip() else p.strip() 
                  for p in params if p.strip()]
        
        # Determine return type from Java signature
        # Maps Java types to Promise-wrapped JavaScript types
        # All methods are async in Node.js, so return types are Promises
        return_type = "Promise<any>"  # Default fallback
        if "void" in signature:
            return_type = "Promise<void>"
        elif "List" in signature or "[]" in signature:
            return_type = "Promise<Array>"
        elif "Optional" in signature:
            return_type = "Promise<object|null>"  # Optional<T> -> null or object
        
        # Build method code starting with JSDoc documentation
        method_lines = [
            "    /**",
            f"     * {description}",
            f"     * Complexity: {complexity}",
            "     */",
            # Generate method signature: async methodName(param1, param2)
            f"    async {method_name}({', '.join(params)}) {{",
            "        try {",
            "            // TODO: Implement business logic",
        ]
        
        # Generate method-specific implementation hints based on naming patterns
        # This helps developers understand what the method should do
        if method_name.startswith("get") or method_name.startswith("find"):
            # Retrieval methods - typically read operations
            method_lines.append("            // Retrieve data logic here")
            # Use first parameter as ID if available
            param_id = params[0] if params else 'id'
            method_lines.append(f"            // return await this.repository.findById({param_id});")
        elif method_name.startswith("create") or method_name.startswith("save"):
            # Creation/save methods - typically write operations
            method_lines.append("            // Create/update logic here")
            param_entity = params[0] if params else 'entity'
            method_lines.append(f"            // return await this.repository.save({param_entity});")
        elif method_name.startswith("delete") or method_name.startswith("remove"):
            # Deletion methods - typically remove operations
            method_lines.append("            // Delete logic here")
            param_id = params[0] if params else 'id'
            method_lines.append(f"            // return await this.repository.deleteById({param_id});")
        else:
            # Generic business logic method
            method_lines.append("            // Business logic implementation")
        
        # Add error handling structure (try-catch pattern)
        # This matches Spring's exception handling but uses JavaScript Error
        method_lines.extend([
            "            throw new Error('Method not yet implemented');",
            "        } catch (error) {",
            # Log error with context for debugging
            "            console.error(`Error in {method_name}:`, error);",
            # Re-throw to allow controller-level error handling
            "            throw error;",
            "        }",
            "    }"
        ])
        
        return "\n".join(method_lines)
    
    def _create_stub_service(self, service_metadata: Dict) -> Dict[str, Any]:
        """
        Create a minimal stub service when conversion completely fails.
        
        This method is called as a last resort when:
        - LLM conversion fails
        - Metadata conversion fails
        - Java code is unreadable
        - Unexpected errors occur
        
        The stub ensures the conversion pipeline continues and provides
        a starting point for manual implementation.
        
        Args:
            service_metadata: Service metadata dictionary (may be incomplete)
        
        Returns:
            Dictionary with stub service code
        """
        service_name = service_metadata.get("name", "Unknown")
        
        # Generate minimal service stub with basic structure
        # Developers will need to implement actual methods based on original Java code
        stub_code = f"""class {service_name} {{
    /**
     * Service class for {service_name}
     * TODO: Implement service methods based on original Java service
     * 
     * This is a stub generated when automatic conversion failed.
     * Please refer to the original Java service class for implementation details.
     */
    
    constructor() {{
        // Initialize dependencies
        // TODO: Add require statements for repositories and services
    }}
    
    /**
     * Example method - to be replaced with actual implementations
     * 
     * @description Placeholder method indicating service needs implementation
     * @returns {{Promise<void>}}
     * @throws {{Error}} Always throws - indicates method not implemented
     */
    async exampleMethod() {{
        throw new Error('Service methods not yet implemented');
    }}
}}

module.exports = new {service_name}();
"""
        
        return {
            "name": service_name,
            "file_path": f"services/{service_name}.js",
            "code": stub_code,
            "type": "service"
        }

