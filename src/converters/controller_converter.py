"""Convert Spring controllers to Express/NestJS routes"""

import re
import logging
from typing import Dict, Optional, Any, List
from ..clients.base_llm_client import BaseLLMClient
from ..clients.llm_client_factory import create_llm_client_from_config

logger = logging.getLogger(__name__)


class ControllerConverter:
    """Converts Spring controllers to Express routes or NestJS controllers"""
    
    def __init__(
        self,
        target_framework: str = "express",
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
        Initialize controller converter
        
        Args:
            target_framework: "express" or "nestjs" (default: express)
            llm_client: Pre-configured LLM client (optional, takes precedence)
            provider: LLM provider name ("gemini", "glm", "openrouter", "openai")
            api_token: API token for the provider
            model: Model name
            base_url: Optional base URL (for GLM/OpenAI custom endpoints)
            profile_name: Profile name from config file
            config_path: Path to config file
            gemini_api_token: Legacy parameter (deprecated)
        """
        # Store target framework (express or nestjs) for conversion strategy
        self.target_framework = target_framework
        
        # If client provided, use it directly (allows dependency injection and testing)
        # This takes precedence over other parameters
        if llm_client:
            self.client = llm_client
            return
        
        # Legacy support: convert gemini_api_token parameter to new format
        # Maintains backward compatibility with older code using gemini_api_token
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
    
    def convert_controller(self, controller_metadata: Dict, java_code: str = "") -> Dict[str, Any]:
        """
        Convert Spring controller to Express routes or NestJS controller
        
        Args:
            controller_metadata: Controller metadata with 'name', 'filePath', 'methods', etc.
            java_code: Full Java controller source code (optional)
            
        Returns:
            Dictionary with:
            {
                "name": "ControllerName",
                "file_path": "routes/ControllerName.js" or "controllers/ControllerName.ts",
                "code": "...",
                "routes": [...]
            }
        """
        try:
            # Read Java source code from file path if not provided as parameter
            # This handles cases where only metadata is available but we need the actual code
            if not java_code and controller_metadata.get("filePath"):
                try:
                    with open(controller_metadata["filePath"], 'r', encoding='utf-8') as f:
                        java_code = f.read()
                except Exception:
                    # File read failed - will proceed with metadata-based conversion
                    pass
            
            # Choose conversion strategy based on target framework and available resources
            # Express.js is the default and most common target
            if self.target_framework == "express":
                # Use LLM for intelligent conversion if available, otherwise use metadata
                if self.client and java_code:
                    # LLM conversion: Higher quality, preserves routing annotations better
                    return self._convert_to_express_with_llm(controller_metadata, java_code)
                else:
                    # Fallback: Pattern-based conversion from metadata only
                    return self._convert_to_express_from_metadata(controller_metadata)
            else:  # nestjs - TypeScript-based framework with decorators
                # NestJS conversion (similar to Express but uses decorators)
                if self.client and java_code:
                    return self._convert_to_nestjs_with_llm(controller_metadata, java_code)
                else:
                    return self._convert_to_nestjs_from_metadata(controller_metadata)
        except Exception as e:
            # Any unexpected error during conversion - log and return stub
            # Stub ensures conversion process continues without crashing
            logger.error(f"Failed to convert controller {controller_metadata.get('name', 'unknown')}: {e}")
            return self._create_stub_controller(controller_metadata)
    
    def _convert_to_express_with_llm(self, controller_metadata: Dict, java_code: str) -> Dict[str, Any]:
        """
        Convert Spring controller to Express routes using LLM for intelligent code translation.
        
        This method constructs a detailed prompt that guides the LLM through the conversion
        process, ensuring routing annotations are preserved while adapting to Express patterns.
        """
        
        # Check if code exceeds token limit and needs chunking
        estimated_tokens = self.client.estimate_tokens(java_code) if self.client else len(java_code) * 0.25
        max_tokens = 8000  # Token limit for chunking
        
        if estimated_tokens > max_tokens and self.client:
            # Use chunked conversion for large controllers
            return self._convert_to_express_with_llm_chunked(controller_metadata, java_code)
        
        # Standard conversion for smaller controllers
        limited_java_code = java_code
        
        # Construct comprehensive prompt with detailed documentation requirements
        # Documentation requirements are placed early to ensure they're not overlooked
        prompt = f"""Convert this Spring REST controller to Express.js routes.

Java Controller Code:
```java
{limited_java_code}
```

CRITICAL REQUIREMENTS - DOCUMENTATION:
1. **JSDoc Documentation (MANDATORY)**:
   - Add comprehensive JSDoc comments for the router file explaining:
     * What the controller handles (business purpose)
     * Original Java class name and Spring annotations converted
     * Base route path
   - Add JSDoc for EVERY route handler with:
     * @route {{METHOD}} {{path}} - HTTP method and route path
     * @description - Clear explanation of what the route does
     * @param {{Object}} req - Express request object with parameter descriptions
     * @param {{Object}} res - Express response object
     * @returns {{Promise}} - Response type description
     * @throws {{Error}} - Possible errors (HTTP status codes)
     * Example: 
     * /**
     *  * @route GET /api/customers/:id
     *  * @description Retrieves a customer by ID. Converts Spring @PathVariable to req.params.id
     *  * @param {{Object}} req.params.id - Customer ID from URL path
     *  * @returns {{Promise<Object>}} Customer object or 404 if not found
     *  */

2. **Inline Comments (MANDATORY)**:
   - Add inline comments explaining Spring annotation conversions:
     * "// @GetMapping converted to router.get()"
     * "// @PathVariable converted to req.params"
     * "// @RequestParam converted to req.query"
     * "// @RequestBody converted to req.body"
   - Comment on parameter extraction logic:
     * "// Extract ID from URL path (converts Spring @PathVariable)"
     * "// Get query parameters (converts Spring @RequestParam)"
   - Explain response handling:
     * "// Return JSON response with status code (replaces Spring ResponseEntity)"
     * "// Set appropriate HTTP status based on operation result"
   - Document error handling patterns:
     * "// Catch exceptions and return appropriate HTTP status (replaces Spring @ExceptionHandler)"
   - Comment on service method calls:
     * "// Call service method with await (replaces Spring service injection)"

3. **Route Extraction and Conversion**:
   - Extract all @RequestMapping, @GetMapping, @PostMapping, @PutMapping, @DeleteMapping, @PatchMapping
   - Convert to Express router:
     * @RestController or @Controller -> Express Router instance
     * @RequestMapping("/path") -> router base path or middleware
     * @GetMapping("/path") -> router.get("/path", handler)
     * @PostMapping("/path") -> router.post("/path", handler)
     * @PutMapping("/path") -> router.put("/path", handler)
     * @DeleteMapping("/path") -> router.delete("/path", handler)
     * @PatchMapping("/path") -> router.patch("/path", handler)
   - Add comments: "// Route converted from Spring @GetMapping"

4. **Method Parameter Conversion**:
   - @PathVariable -> req.params.paramName (add comment: "// @PathVariable -> req.params")
   - @RequestParam -> req.query.paramName (add comment: "// @RequestParam -> req.query")
   - @RequestBody -> req.body (add comment: "// @RequestBody -> req.body")
   - @RequestHeader -> req.headers.headerName (add comment: "// @RequestHeader -> req.headers")
   - Document parameter validation if present

5. **Response Handling Conversion**:
   - Return ResponseEntity -> res.status(code).json(data) (add comment explaining status code choice)
   - Return object directly -> res.json(object) or res.status(200).json(object)
   - Handle exceptions -> try-catch with res.status(error_code).json({error: message})
   - Add comments: "// Response format matches Spring ResponseEntity structure"

6. **Dependency Injection Conversion**:
   - @Autowired services -> require at top of file (add comment: "// @Autowired converted to require")
   - Call service methods with await (add comment: "// Async service call")
   - Document service dependencies in comments

7. **Error Handling**:
   - Try-catch blocks around route handlers (add comment: "// Error handling replaces Spring @ExceptionHandler")
   - HTTP status codes matching Spring responses (200, 201, 400, 404, 500, etc.)
   - Consistent error response format (add comment explaining format)
   - Log errors appropriately (add comment: "// Log error for debugging")

8. **Async/Await Patterns**:
   - All route handlers must be async functions
   - All service calls must use await
   - Add comments explaining async patterns where needed

Return only the complete Express router code with all documentation, no explanations."""

        try:
            # Generate converted code using LLM with token limit
            # 6000 tokens allows for complete router file plus documentation
            converted_code = self.client.generate(prompt, max_tokens=6000)
            
            # Extract controller name from metadata for file naming
            controller_name = controller_metadata.get("name", "Unknown")
            
            # Extract route information from Java code using regex patterns
            # This provides metadata about available routes for documentation
            routes = self._extract_routes(java_code)
            
            # Return converted controller with metadata
            return {
                "name": controller_name,
                "file_path": f"routes/{controller_name.lower()}.js",  # Standard path for routes
                "code": converted_code,
                "routes": routes,  # List of route metadata for documentation
                "type": "controller"  # Component type identifier
            }
        except Exception as e:
            # LLM generation failed - log warning and fallback to pattern-based conversion
            # This ensures conversion continues even if LLM is unavailable or times out
            logger.warning(f"LLM conversion failed, falling back to metadata: {e}")
            return self._convert_to_express_from_metadata(controller_metadata)
    
    def _convert_to_express_with_llm_chunked(self, controller_metadata: Dict, java_code: str) -> Dict[str, Any]:
        """Convert large controller using chunking strategy with route context preservation"""
        controller_name = controller_metadata.get("name", "Unknown")
        
        # Extract class-level annotations and base path for context preservation
        base_path = self._extract_base_path_from_code(java_code)
        class_annotations = self._extract_class_annotations(java_code)
        
        system_prompt = f"""Convert this Spring REST controller to Express.js routes.

This is a large controller being processed in chunks. For each chunk, convert the route methods to Express routes.
Preserve routing context: class-level annotations, base path, and service dependencies.

Controller: {controller_name}
Base Path: {base_path}
Class Annotations: {class_annotations}

CRITICAL REQUIREMENTS:
1. Add JSDoc comments for each route handler
2. Add inline comments explaining Spring annotation conversions
3. Preserve routing patterns and HTTP methods
4. Convert Spring annotations to Express router methods
5. Use async/await for all route handlers
6. Include proper error handling

For each chunk, provide converted Express routes for the methods in that chunk."""
        
        def process_chunk(client, chunk_prompt):
            """Process individual chunk"""
            return client.generate(chunk_prompt, max_tokens=6000, context=f"Controller Conversion (Chunk): {controller_name}")
        
        def combine_results(chunk_results):
            """Combine chunk results into single router file"""
            # Extract route information from original code
            routes = self._extract_routes(java_code)
            
            # If we have multiple chunks, combine them
            if len(chunk_results) == 1:
                combined_code = str(chunk_results[0])
            else:
                # Combine multiple chunk results
                combine_prompt = f"""Combine these partial Express router conversions into a single complete router file.

Controller Name: {controller_name}
Base Path: {base_path}

Partial conversions:
{chr(10).join([f'--- Chunk {i+1} ---{chr(10)}{str(result)}' for i, result in enumerate(chunk_results)])}

Requirements:
1. Merge all routes from all chunks into one router
2. Ensure only one router definition and export
3. Preserve all imports and requires
4. Maintain proper Express router structure
5. Remove duplicate router definitions
6. Ensure all routes are properly registered

Return only the complete, merged Express router code."""
                combined_code = self.client.generate(combine_prompt, max_tokens=8000, context=f"Controller Combination: {controller_name}")
            
            return {
                "name": controller_name,
                "file_path": f"routes/{controller_name.lower()}.js",
                "code": combined_code,
                "routes": routes,
                "type": "controller"
            }
        
        try:
            result = self.client.process_large_content(
                java_code,
                system_prompt,
                process_chunk_fn=process_chunk,
                combine_results_fn=combine_results,
                context=f"Controller Conversion: {controller_name}"
            )
            return result
        except Exception as e:
            logger.warning(f"Chunked conversion failed, falling back to metadata: {e}")
            return self._convert_to_express_from_metadata(controller_metadata)
    
    def _extract_base_path_from_code(self, java_code: str) -> str:
        """Extract base path from @RequestMapping annotation"""
        import re
        request_mapping_match = re.search(r'@RequestMapping\s*\(\s*["\']([^"\']+)["\']', java_code)
        return request_mapping_match.group(1) if request_mapping_match else "/api"
    
    def _extract_class_annotations(self, java_code: str) -> str:
        """Extract class-level annotations"""
        import re
        annotations = []
        class_match = re.search(r'@(\w+)\s*[\s\S]*?class\s+\w+', java_code)
        if class_match:
            annotation_match = re.findall(r'@(\w+)', java_code[:class_match.end()])
            annotations.extend(annotation_match)
        return ', '.join(set(annotations)) if annotations else ""
    
    def _convert_to_express_from_metadata(self, controller_metadata: Dict) -> Dict[str, Any]:
        """
        Convert controller using only metadata (fallback when Java code unavailable).
        
        This method generates route stubs based on extracted metadata,
        producing skeletons that need manual implementation or LLM refinement.
        """
        
        # Extract controller information from metadata
        controller_name = controller_metadata.get("name", "Unknown")
        methods = controller_metadata.get("methods", [])  # List of method metadata objects
        dependencies = controller_metadata.get("dependencies", [])  # Service dependencies
        
        # Generate Express routes using pattern-based conversion
        # This creates a skeleton with route handlers and basic structure
        routes_code = self._generate_express_routes(controller_name, methods, dependencies)
        
        return {
            "name": controller_name,
            "file_path": f"routes/{controller_name.lower()}.js",
            "code": routes_code,
            "routes": self._extract_routes_from_methods(methods),  # Extract routes from method names
            "type": "controller"
        }
    
    def _generate_express_routes(self, controller_name: str, methods: List[Dict], dependencies: List[str]) -> str:
        """
        Generate Express router code from metadata using pattern-based conversion.
        
        This method creates a router skeleton with:
        - Import statements for dependencies
        - Router instance
        - Route handlers based on method metadata
        
        Args:
            controller_name: Name of the controller class
            methods: List of method metadata dictionaries
            dependencies: List of dependency names (services, repositories, etc.)
        
        Returns:
            Complete JavaScript Express router code as string
        """
        
        # Start with Express router setup
        lines = [
            "const express = require('express');",
            "const router = express.Router();",
        ]
        
        # Filter dependencies to find services that need importing
        # Pattern: Look for 'Service' in dependency name (case-insensitive)
        service_deps = [dep for dep in dependencies if 'Service' in dep or 'service' in dep.lower()]
        
        # Generate require statements for service dependencies
        # Limit to 3 services to prevent overly complex imports
        for service in service_deps[:3]:
            # Convert service name to camelCase for variable naming
            # Example: "CustomerService" -> "customerService"
            service_var = service[0].lower() + service[1:]
            lines.append(f"const {service_var} = require('../services/{service}');")
        
        # Add blank line after imports for readability
        if service_deps:
            lines.append("")
        
        # Extract base path from controller name (not used in pattern-based conversion)
        # This is for reference - actual paths are determined per-route
        base_path = self._extract_base_path(controller_name)
        
        # Convert each method from metadata to Express route handler
        # Methods are converted individually to preserve signatures and descriptions
        for method in methods:
            route_code = self._convert_method_to_route(method, service_deps)
            if route_code:
                lines.append(route_code)
                lines.append("")
        
        # Add placeholder comment if no methods found
        # This helps identify incomplete conversions
        if not methods:
            lines.append("// Routes to be implemented")
            lines.append("")
        
        # Export router for use in main server file
        lines.append(f"module.exports = router;")
        
        # Join all lines with newlines to form complete code string
        return "\n".join(lines)
    
    def _convert_method_to_route(self, method: Dict, services: List[str]) -> str:
        """
        Convert a single controller method from metadata to Express route handler.
        
        This method generates a route skeleton with:
        - JSDoc comments from metadata
        - HTTP method and path inference from method name
        - Parameter extraction logic
        - Service call with error handling
        
        Args:
            method: Dictionary containing method metadata (name, signature, description)
            services: List of service dependency names
        
        Returns:
            Complete JavaScript route handler code as string
        """
        
        # Extract method information from metadata dictionary
        method_name = method.get("name", "unknown")
        signature = method.get("signature", "")  # Full Java method signature
        description = method.get("description", "")  # Method description from metadata extraction
        
        # Determine HTTP method and path from method name using naming conventions
        # Spring controllers typically use naming patterns: get*, create*, update*, delete*
        # Default to GET if pattern doesn't match
        http_method = "get"
        path = f"/{method_name.lower()}"
        
        # Infer HTTP method from method name prefix
        # This follows common REST API naming conventions
        if method_name.startswith("get") or method_name.startswith("find"):
            http_method = "get"
            # Remove "get" prefix and convert to lowercase for path
            # Example: "getCustomerById" -> "/customerbyid"
            path = f"/{method_name[3:].lower()}" if len(method_name) > 3 else "/"
        elif method_name.startswith("create") or method_name.startswith("add"):
            http_method = "post"
            # Remove "create" prefix (6 chars)
            path = f"/{method_name[6:].lower()}" if len(method_name) > 6 else "/"
        elif method_name.startswith("update") or method_name.startswith("put"):
            http_method = "put"
            # Remove "update" prefix (6 chars)
            path = f"/{method_name[6:].lower()}" if len(method_name) > 6 else "/"
        elif method_name.startswith("delete") or method_name.startswith("remove"):
            http_method = "delete"
            # Remove "delete" prefix (6 chars)
            path = f"/{method_name[6:].lower()}" if len(method_name) > 6 else "/"
        
        # Parse parameters from Java method signature using regex
        # Pattern matches: methodName(param1, param2, param3)
        # Captures everything inside parentheses
        params_match = re.search(r'\(([^)]*)\)', signature)
        params = params_match.group(1).split(',') if params_match else []
        
        # Extract parameter names from full signatures
        # Java format: "@PathVariable int id" or "String name" -> extract "id", "name"
        # Split by space and take last word (parameter name)
        param_vars = []
        for p in params:
            if p.strip():
                param_name = p.strip().split()[-1] if ' ' in p.strip() else p.strip()
                param_vars.append(param_name)
        
        # Determine if path should include parameter
        # For GET requests with parameters, use Express path parameter syntax
        # Simplified approach: assume first parameter is ID
        if param_vars and http_method == "get":
            path = f"/:id"  # Express path parameter syntax
        
        # Get first service for method calls (simplified - real code should inject all services)
        # Convert service name to camelCase for variable naming
        service_var = services[0][0].lower() + services[0][1:] if services else "service"
        
        # Build route handler code starting with JSDoc documentation
        route_lines = [
            f"/**",
            f" * {description}",
            f" * {method_name}",
            f" */",
            # Generate route definition: router.method(path, async handler)
            f"router.{http_method}('{path}', async (req, res) => {{",
            "    try {",
        ]
        
        # Add parameter extraction logic
        # This converts Spring annotations to Express request object access
        if param_vars:
            # Limit to 3 parameters to keep route handlers manageable
            for param in param_vars[:3]:
                # Determine parameter source based on naming convention
                # IDs typically come from URL path (@PathVariable)
                if param == "id" or "id" in param.lower():
                    # Extract from URL path params or query params (flexible)
                    route_lines.append(f"        const {param} = req.params.id || req.query.{param};")
                else:
                    # Other parameters come from request body or query (@RequestBody or @RequestParam)
                    route_lines.append(f"        const {param} = req.body.{param} || req.query.{param};")
            route_lines.append("")
        
        # Add service method call
        # Limit to 2 parameters in service call to keep it simple
        if services:
            param_list = ', '.join(param_vars[:2])
            route_lines.append(f"        const result = await {service_var}.{method_name}({param_list});")
        else:
            # No services available - add TODO comment
            route_lines.append(f"        // TODO: Call service method")
            route_lines.append(f"        const result = null;")
        
        # Add response handling and error handling
        route_lines.extend([
            "",
            # Success response with standard format
            "        res.status(200).json({",
            "            success: true,",
            "            data: result",
            "        });",
            "    } catch (error) {",
            # Log error with context for debugging
            "        console.error(`Error in {method_name}:`, error);",
            # Return error response with standard format
            "        res.status(500).json({",
            "            success: false,",
            "            error: error.message",
            "        });",
            "    }",
            "});"
        ])
        
        return "\n".join(route_lines)
    
    def _extract_base_path(self, controller_name: str) -> str:
        """
        Extract base path from controller name using naming convention.
        
        Converts controller names like "CustomerController" to "/api/customer"
        This follows REST API naming conventions.
        
        Args:
            controller_name: Name of the controller class (e.g., "CustomerController")
        
        Returns:
            Base path string (e.g., "/api/customer")
        """
        # Remove "Controller" suffix using regex
        # Pattern matches "Controller" at the end of the string
        base = re.sub(r'Controller$', '', controller_name).lower()
        return f"/api/{base}"
    
    def _extract_routes(self, java_code: str) -> List[Dict]:
        """
        Extract route information from Java controller code using regex patterns.
        
        This method parses Spring annotations to identify all HTTP routes:
        - @RequestMapping for base path
        - @GetMapping, @PostMapping, etc. for individual routes
        
        Args:
            java_code: Full Java controller source code
        
        Returns:
            List of route dictionaries with method and path keys
        """
        routes = []
        
        # Find @RequestMapping annotation to get base path
        # Pattern matches: @RequestMapping("/base/path")
        # Captures the path string inside quotes
        request_mapping_match = re.search(r'@RequestMapping\s*\(\s*["\']([^"\']+)["\']', java_code)
        # Extract base path or default to "/api" if not found
        base_path = request_mapping_match.group(1) if request_mapping_match else "/api"
        
        # Find all HTTP mapping annotations (@GetMapping, @PostMapping, etc.)
        # Pattern matches:
        # - @GetMapping, @PostMapping, @PutMapping, @DeleteMapping, @PatchMapping
        # - Optional value parameter: @GetMapping(value = "/path")
        # Group 1: HTTP method (Get, Post, Put, Delete, Patch)
        # Group 2: Optional path value
        mapping_pattern = r'@(Get|Post|Put|Delete|Patch)Mapping\s*(?:\([^)]*value\s*=\s*["\']([^"\']+)["\'])?'
        
        # Find all matching annotations in the code
        for match in re.finditer(mapping_pattern, java_code):
            # Extract HTTP method (convert to lowercase for consistency)
            http_method = match.group(1).lower()
            # Extract path value if present (otherwise empty string)
            path = match.group(2) if match.group(2) else ""
            # Combine base path with route-specific path
            # If path is empty, use just base_path
            full_path = f"{base_path}{path}" if path else base_path
            
            # Add route information to list
            routes.append({
                "method": http_method,  # HTTP method: "get", "post", etc.
                "path": full_path  # Full path: "/api/customers/:id"
            })
        
        return routes
    
    def _extract_routes_from_methods(self, methods: List[Dict]) -> List[Dict]:
        """
        Extract route information from method metadata (fallback when Java code unavailable).
        
        This method infers HTTP methods and paths from method names using naming conventions.
        Less accurate than parsing Java annotations but works with metadata only.
        
        Args:
            methods: List of method metadata dictionaries
        
        Returns:
            List of route dictionaries with method and path keys
        """
        routes = []
        
        # Infer routes from method names using common REST API naming patterns
        for method in methods:
            method_name = method.get("name", "")
            
            # Infer HTTP method from method name prefix
            # GET methods: typically start with "get"
            if method_name.startswith("get"):
                routes.append({"method": "get", "path": f"/{method_name.lower()}"})
            # POST methods: typically start with "create" or "add"
            elif method_name.startswith("create") or method_name.startswith("add"):
                routes.append({"method": "post", "path": f"/{method_name.lower()}"})
            # PUT methods: typically start with "update"
            elif method_name.startswith("update"):
                routes.append({"method": "put", "path": f"/{method_name.lower()}"})
            # DELETE methods: typically start with "delete"
            elif method_name.startswith("delete"):
                routes.append({"method": "delete", "path": f"/{method_name.lower()}"})
        
        return routes
    
    def _convert_to_nestjs_with_llm(self, controller_metadata: Dict, java_code: str) -> Dict[str, Any]:
        """
        Convert to NestJS controller using LLM (placeholder - not fully implemented).
        
        NestJS conversion would be similar to Express but uses TypeScript decorators.
        For now, this falls back to Express conversion.
        
        Args:
            controller_metadata: Controller metadata dictionary
            java_code: Full Java controller source code
        
        Returns:
            Dictionary with converted NestJS controller code (currently Express format)
        """
        # NestJS uses decorators similar to Spring (@Controller, @Get, @Post, etc.)
        # Implementation would be similar but convert to TypeScript with decorators
        logger.warning("NestJS conversion not fully implemented, using Express format")
        return self._convert_to_express_with_llm(controller_metadata, java_code)
    
    def _convert_to_nestjs_from_metadata(self, controller_metadata: Dict) -> Dict[str, Any]:
        """
        Convert to NestJS from metadata (placeholder - not fully implemented).
        
        For now, this falls back to Express conversion from metadata.
        
        Args:
            controller_metadata: Controller metadata dictionary
        
        Returns:
            Dictionary with converted NestJS controller code (currently Express format)
        """
        logger.warning("NestJS conversion not fully implemented, using Express format")
        return self._convert_to_express_from_metadata(controller_metadata)
    
    def _create_stub_controller(self, controller_metadata: Dict) -> Dict[str, Any]:
        """
        Create a minimal stub controller when conversion completely fails.
        
        This method is called as a last resort when:
        - LLM conversion fails
        - Metadata conversion fails
        - Java code is unreadable
        - Unexpected errors occur
        
        The stub ensures the conversion pipeline continues and provides
        a starting point for manual implementation.
        
        Args:
            controller_metadata: Controller metadata dictionary (may be incomplete)
        
        Returns:
            Dictionary with stub controller code
        """
        controller_name = controller_metadata.get("name", "Unknown")
        
        # Generate minimal controller stub with basic structure
        # Developers will need to implement actual routes based on original Java controller
        stub_code = f"""const express = require('express');
const router = express.Router();

/**
 * {controller_name} routes
 * TODO: Implement controller routes based on original Java controller
 * 
 * This is a stub generated when automatic conversion failed.
 * Please refer to the original Java controller class for route implementations.
 */

/**
 * @route GET /
 * @description Placeholder route indicating controller needs implementation
 * @returns {{Promise<Object>}} Basic response with controller name
 */
router.get('/', async (req, res) => {{
    res.status(200).json({{
        success: true,
        message: '{controller_name} controller',
        data: []
    }});
}});

module.exports = router;
"""
        
        return {
            "name": controller_name,
            "file_path": f"routes/{controller_name.lower()}.js",
            "code": stub_code,
            "routes": [],  # No routes extracted - manual implementation needed
            "type": "controller"
        }

