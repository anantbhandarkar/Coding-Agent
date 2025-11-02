"""Convert Spring Data JPA repositories to Sequelize DAOs"""

import re
import logging
from typing import Dict, Optional, Any, List
from ..clients.base_llm_client import BaseLLMClient
from ..clients.llm_client_factory import create_llm_client_from_config

logger = logging.getLogger(__name__)


class RepositoryConverter:
    """Converts Spring Data JPA repositories to Sequelize-based DAOs"""
    
    def __init__(
        self,
        orm_choice: str = "sequelize",
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
        Initialize repository converter
        
        Args:
            orm_choice: "sequelize" or "typeorm" (default: sequelize)
            llm_client: Pre-configured LLM client (optional, takes precedence)
            provider: LLM provider name ("gemini", "glm", "openrouter", "openai")
            api_token: API token for the provider
            model: Model name
            base_url: Optional base URL (for GLM/OpenAI custom endpoints)
            profile_name: Profile name from config file
            config_path: Path to config file
            gemini_api_token: Legacy parameter (deprecated)
        """
        # Store ORM choice (sequelize or typeorm) for conversion strategy
        # Currently only Sequelize is fully implemented
        self.orm_choice = orm_choice
        
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
    
    def convert_repository(self, repo_metadata: Dict, entity_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Convert JPA repository to Sequelize DAO
        
        Args:
            repo_metadata: Repository metadata with 'name', 'filePath', 'methods', etc.
            entity_metadata: Optional entity metadata for type information
            
        Returns:
            Dictionary with:
            {
                "name": "RepositoryName",
                "file_path": "repositories/RepositoryName.js",
                "code": "...",
                "model_name": "..."
            }
        """
        try:
            # Read Java repository code from file path if not provided as parameter
            # This handles cases where only metadata is available but we need the actual code
            java_code = ""
            if repo_metadata.get("filePath"):
                try:
                    with open(repo_metadata["filePath"], 'r', encoding='utf-8') as f:
                        java_code = f.read()
                except Exception:
                    # File read failed - will proceed with metadata-based conversion
                    pass
            
            # Choose conversion strategy based on available resources:
            # - LLM conversion: Higher quality, preserves Spring Data query methods better
            # - Metadata conversion: Fallback when LLM unavailable or code unreadable
            if self.client and java_code:
                # Use LLM for intelligent conversion with context understanding
                # Entity metadata helps LLM understand relationships and types
                return self._convert_with_llm(repo_metadata, java_code, entity_metadata)
            else:
                # Fall back to pattern-based conversion from metadata only
                return self._convert_from_metadata(repo_metadata, entity_metadata)
        except Exception as e:
            # Any unexpected error during conversion - log and return stub
            # Stub ensures conversion process continues without crashing
            logger.error(f"Failed to convert repository {repo_metadata.get('name', 'unknown')}: {e}")
            return self._create_stub_repository(repo_metadata)
    
    def _convert_with_llm(self, repo_metadata: Dict, java_code: str, entity_metadata: Optional[Dict]) -> Dict[str, Any]:
        """
        Convert Spring Data JPA repository to Sequelize DAO using LLM for intelligent code translation.
        
        This method constructs a detailed prompt that guides the LLM through the conversion
        process, ensuring Spring Data query methods are correctly mapped to Sequelize queries.
        """
        
        # Check if code exceeds token limit and needs chunking
        estimated_tokens = self.client.estimate_tokens(java_code) if self.client else len(java_code) * 0.25
        max_tokens = 8000  # Token limit for chunking
        
        if estimated_tokens > max_tokens and self.client:
            # Use interface-based chunked conversion for large repositories
            return self._convert_with_llm_chunked(repo_metadata, java_code, entity_metadata)
        
        # Standard conversion for smaller repositories
        limited_java_code = java_code
        
        # Add entity context if available to help LLM understand relationships
        # This improves conversion quality for methods involving entity relationships
        entity_context = ""
        if entity_metadata:
            entity_context = f"\n\nRelated Entity: {entity_metadata.get('name', 'Unknown')}"
        
        # Construct comprehensive prompt with detailed documentation requirements
        # Documentation requirements are placed early to ensure they're not overlooked
        prompt = f"""Convert this Spring Data JPA repository interface to a Sequelize DAO class.

Java Repository Code:
```java
{limited_java_code}
```
{entity_context}

CRITICAL REQUIREMENTS - DOCUMENTATION:
1. **JSDoc Documentation (MANDATORY)**:
   - Add comprehensive JSDoc comments for the DAO class explaining:
     * What the repository does (data access for which entity)
     * Original Java interface name and Spring Data methods converted
     * Associated Sequelize model name
   - Add JSDoc for EVERY method with:
     * @description - Clear explanation of what the method does
     * @param {{type}} paramName - Description of each parameter
     * @returns {{Promise<type>}} - Return type description
     * @throws {{Error}} - Possible errors that can be thrown
     * Example:
     * /**
     *  * @description Finds an entity by ID. Converts Spring Data's findByPk to Sequelize findByPk.
     *  * @param {{number}} id - Entity ID
     *  * @returns {{Promise<Object|null>}} Entity object or null if not found
     *  * Conversion note: Spring Data JPA's findById returns Optional<T>, Sequelize returns object or null
     *  */

2. **Inline Comments (MANDATORY)**:
   - Add inline comments explaining Spring Data query method conversions:
     * "// Spring Data findBy* -> Sequelize findOne with where clause"
     * "// Spring Data findAllBy* -> Sequelize findAll with where clause"
     * "// Spring Data save -> Sequelize create/update based on entity.id"
     * "// Spring Data deleteById -> Sequelize destroy with where clause"
   - Comment on query construction:
     * "// Build where clause from Spring Data method name pattern"
     * "// Convert Spring Data query method naming to Sequelize where conditions"
   - Explain Sequelize operators:
     * "// Sequelize Op.like for Spring Data 'Like' queries"
     * "// Sequelize Op.in for Spring Data 'In' queries"
     * "// Sequelize Op.and for Spring Data 'And' queries"
   - Document return type conversions:
     * "// Java Optional<T> -> JavaScript null or object (not Promise<Optional>)"
     * "// Java List<T> -> JavaScript array (Promise<Array>)"
     * "// Java void -> Promise<void>"
   - Add comments for complex query logic:
     * "// Handle update vs create based on entity ID presence"

3. **Interface to Class Conversion**:
   - Convert Spring Data JPA interface to a class with instance methods
   - Use async/await for all database operations
   - Add comment: "// Converted from Spring Data JPA interface to Sequelize DAO class"

4. **JPA Repository Method Mapping**:
   - findBy*(...) -> Model.findOne({{where: {{...}}}}) (add comment: "// Spring Data findBy* -> Sequelize findOne")
   - findAllBy*(...) -> Model.findAll({{where: {{...}}}}) (add comment: "// Spring Data findAllBy* -> Sequelize findAll")
   - save(entity) -> Model.create(...) or Model.update(...) (add comment explaining logic)
   - deleteById(id) -> Model.destroy({{where: {{id}}}}) (add comment: "// Spring Data deleteById -> Sequelize destroy")
   - count() -> Model.count() (add comment: "// Spring Data count -> Sequelize count")
   - existsById(id) -> Model.count({{where: {{id}}}}) > 0 (add comment explaining boolean conversion)

5. **Method Signature Conversions**:
   - Java Optional<T> -> Promise that resolves to object or null (add comment explaining Optional conversion)
   - Java List<T> -> Promise that resolves to array (add comment: "// Returns Promise<Array>")
   - Java void -> Promise that resolves to void (add comment: "// Returns Promise<void>")

6. **Spring Data Query Method Conversions**:
   - findByFieldName -> where: {{fieldName: value}} (add comment explaining field extraction)
   - findByFieldNameAndOtherField -> where: {{fieldName: value, otherField: value}} (add comment: "// Spring Data 'And' -> Sequelize object with multiple fields")
   - findByFieldNameLike -> where: {{fieldName: {{[Op.like]: value}}}} (add comment: "// Spring Data 'Like' -> Sequelize Op.like")
   - findByFieldNameIn -> where: {{fieldName: {{[Op.in]: value}}}} (add comment: "// Spring Data 'In' -> Sequelize Op.in")
   - Document all query method conversions in comments

7. **Sequelize Syntax**:
   - Use Sequelize v6 syntax with async/await (add comment: "// Sequelize v6 async/await pattern")
   - Import required Sequelize operators: const {{ Op }} = require('sequelize')
   - Use proper Sequelize query patterns (add comments explaining Sequelize-specific syntax)

8. **Error Handling**:
   - Include proper error handling with try-catch blocks (add comment: "// Error handling for database operations")
   - Document error types that may occur (add comment explaining possible Sequelize errors)
   - Log errors appropriately (add comment: "// Log database errors for debugging")

Return only the complete DAO class code with all documentation, no explanations."""

        try:
            # Generate converted code using LLM with token limit
            # 4000 tokens allows for complete DAO class plus documentation
            converted_code = self.client.generate(prompt, max_tokens=4000)
            
            # Extract repository name and derive model name
            repo_name = repo_metadata.get("name", "Unknown")
            # Model name is typically repository name without "Repository" suffix
            model_name = self._extract_model_name(repo_name)
            
            # Return converted repository with metadata
            return {
                "name": repo_name,
                "file_path": f"repositories/{repo_name}.js",  # Standard path for repositories
                "code": converted_code,
                "model_name": model_name,  # Associated Sequelize model name
                "type": "repository"  # Component type identifier
            }
        except Exception as e:
            # LLM generation failed - log warning and fallback to pattern-based conversion
            # This ensures conversion continues even if LLM is unavailable or times out
            logger.warning(f"LLM conversion failed, falling back to metadata: {e}")
            return self._convert_from_metadata(repo_metadata, entity_metadata)
    
    def _convert_with_llm_chunked(self, repo_metadata: Dict, java_code: str, entity_metadata: Optional[Dict]) -> Dict[str, Any]:
        """Convert large repository interface using interface-based chunking strategy"""
        repo_name = repo_metadata.get("name", "Unknown")
        model_name = self._extract_model_name(repo_name)
        
        # Extract entity context for preserving relationships
        entity_context = ""
        if entity_metadata:
            entity_name = entity_metadata.get('name', 'Unknown')
            entity_fields = entity_metadata.get('methods', [])[:5]  # Sample of entity fields
            entity_context = f"""
Related Entity: {entity_name}
Entity Type: {entity_metadata.get('type', 'Entity')}
This repository provides data access for the {entity_name} entity.
"""
        
        # Extract interface signature for context preservation
        import re
        interface_match = re.search(r'(public\s+)?interface\s+(\w+)\s*(?:extends\s+([^{]+))?\{', java_code)
        interface_name = interface_match.group(2) if interface_match else repo_name
        extends_clause = interface_match.group(3).strip() if interface_match and interface_match.group(3) else ""
        
        system_prompt = f"""Convert this Spring Data JPA repository interface to a Sequelize DAO class.

This is a large repository interface being processed in chunks. For each chunk, convert the method signatures to Sequelize DAO methods.
Preserve interface context: interface signature, generics, and entity relationships.

Repository: {repo_name}
Model: {model_name}
Interface Signature: public interface {interface_name} {f'extends {extends_clause}' if extends_clause else ''}
{entity_context}

CRITICAL REQUIREMENTS:
1. Add JSDoc comments for the DAO class and each method
2. Add inline comments explaining Spring Data query method conversions
3. Convert interface methods to async class methods
4. Preserve Spring Data query method naming patterns (findBy*, findAllBy*, etc.)
5. Use Sequelize operators (Op.like, Op.in, Op.and, etc.) appropriately
6. Include proper error handling

For each chunk, provide converted Sequelize DAO methods for the method signatures in that chunk.
Remember: You're converting an INTERFACE to a CLASS, so provide complete method implementations."""
        
        def process_chunk(client, chunk_prompt):
            """Process individual chunk with interface context"""
            return client.generate(chunk_prompt, max_tokens=4000, context=f"Repository Conversion (Chunk): {repo_name}")
        
        def combine_results(chunk_results):
            """Combine chunk results into single DAO class"""
            # If we have multiple chunks, combine them
            if len(chunk_results) == 1:
                combined_code = str(chunk_results[0])
            else:
                # Combine multiple chunk results
                combine_prompt = f"""Combine these partial Sequelize DAO conversions into a single complete DAO class.

Repository Name: {repo_name}
Model Name: {model_name}
Original Interface: public interface {repo_name} {f'extends {extends_clause}' if extends_clause else ''}

Partial conversions:
{chr(10).join([f'--- Chunk {i+1} ---{chr(10)}{str(result)}' for i, result in enumerate(chunk_results)])}

Requirements:
1. Merge all methods from all chunks into one DAO class
2. Ensure only one class definition (not multiple class declarations)
3. Preserve all imports and requires (Sequelize model, Op operators)
4. Maintain proper class structure (constructor optional, methods)
5. Remove duplicate class definitions
6. Convert interface signature to class definition:
   - Interface: public interface {repo_name} extends JpaRepository<Entity, ID>
   - Class: class {repo_name} {{ ... }}
7. Ensure all methods are async functions
8. Maintain proper Sequelize query patterns

Return only the complete, merged Sequelize DAO class code."""
                combined_code = self.client.generate(combine_prompt, max_tokens=6000, context=f"Repository Combination: {repo_name}")
            
            return {
                "name": repo_name,
                "file_path": f"repositories/{repo_name}.js",
                "code": combined_code,
                "model_name": model_name,
                "type": "repository"
            }
        
        try:
            # Use interface-based chunking strategy
            from ..utils.chunking import ChunkingStrategy
            chunking = ChunkingStrategy()
            chunks = chunking.chunk_interface(java_code, max_tokens=8000)
            
            if not chunks:
                logger.warning("No chunks generated, falling back to direct conversion")
                return self._convert_with_llm(repo_metadata, java_code, entity_metadata)
            
            # Process chunks
            results = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing repository chunk {i + 1}/{len(chunks)} ({chunk.estimated_tokens} tokens)")
                chunk_prompt = f"{system_prompt}\n\nJava Repository Interface (chunk {i + 1} of {len(chunks)}):\n```java\n{chunk.content}\n```"
                result = self.client.generate(chunk_prompt, max_tokens=4000, context=f"Repository Conversion (Chunk {i + 1}/{len(chunks)}): {repo_name}")
                results.append(result)
            
            # Combine results
            return combine_results(results)
            
        except Exception as e:
            logger.warning(f"Chunked conversion failed, falling back to metadata: {e}")
            return self._convert_from_metadata(repo_metadata, entity_metadata)
    
    def _convert_from_metadata(self, repo_metadata: Dict, entity_metadata: Optional[Dict]) -> Dict[str, Any]:
        """
        Convert repository using only metadata (fallback when Java code unavailable).
        
        This method generates a DAO skeleton based on extracted metadata,
        producing stubs that need manual implementation or LLM refinement.
        """
        
        # Extract repository information from metadata
        repo_name = repo_metadata.get("name", "Unknown")
        # Model name is derived from repository name (remove "Repository" suffix)
        model_name = self._extract_model_name(repo_name)
        
        # Extract method metadata for DAO generation
        methods = repo_metadata.get("methods", [])  # List of method metadata objects
        
        # Generate DAO code using pattern-based conversion
        # This creates a skeleton with method signatures and basic structure
        dao_code = self._generate_dao_code(repo_name, model_name, methods)
        
        return {
            "name": repo_name,
            "file_path": f"repositories/{repo_name}.js",
            "code": dao_code,
            "model_name": model_name,
            "type": "repository"
        }
    
    def _extract_model_name(self, repo_name: str) -> str:
        """
        Extract model name from repository name using naming convention.
        
        Spring Data repositories typically follow naming pattern: EntityNameRepository
        This method removes the "Repository" suffix to get the entity/model name.
        
        Args:
            repo_name: Name of the repository class (e.g., "CustomerRepository")
        
        Returns:
            Model name string (e.g., "Customer")
        """
        # Remove "Repository" suffix using regex
        # Pattern matches "Repository" at the end of the string
        model_name = re.sub(r'Repository$', '', repo_name)
        return model_name
    
    def _generate_dao_code(self, repo_name: str, model_name: str, methods: List[Dict]) -> str:
        """
        Generate Sequelize DAO code from metadata using pattern-based conversion.
        
        This method creates a DAO skeleton with:
        - Import statements for model and Sequelize operators
        - Class definition
        - Method stubs based on metadata
        
        Args:
            repo_name: Name of the repository class
            model_name: Name of the associated Sequelize model
            methods: List of method metadata dictionaries
        
        Returns:
            Complete JavaScript DAO class code as string
        """
        
        # Start with imports and class definition
        lines = [
            # Import Sequelize model for data access
            f"const {model_name} = require('../models/{model_name}');",
            # Import Sequelize operators (Op.like, Op.in, etc.) for query construction
            "const { Op } = require('sequelize');",
            "",
            # Start class definition
            f"class {repo_name} {{"
        ]
        
        # Convert each method from metadata to Sequelize DAO method
        # Methods are converted individually to preserve signatures and descriptions
        for method in methods:
            method_code = self._convert_method(method, model_name)
            lines.append(method_code)
            lines.append("")
        
        # If no methods found, add basic CRUD operations
        # This ensures every repository has at least fundamental operations
        if not methods:
            lines.extend(self._generate_basic_crud(model_name))
        
        # Close class definition
        lines.append("}")
        lines.append("")
        
        # Export singleton instance (common Node.js pattern)
        # Alternative would be: module.exports = RepositoryName; (class export)
        lines.append(f"module.exports = new {repo_name}();")
        
        # Join all lines with newlines to form complete code string
        return "\n".join(lines)
    
    def _convert_method(self, method: Dict, model_name: str) -> str:
        """
        Convert a single method from metadata to Sequelize DAO method.
        
        This method generates method code based on Spring Data naming conventions:
        - findBy* -> findOne
        - findAllBy* -> findAll
        - save -> create/update
        - delete* -> destroy
        
        Args:
            method: Dictionary containing method metadata (name, signature, description)
            model_name: Name of the Sequelize model to use
        
        Returns:
            Complete JavaScript method code as string
        """
        
        # Extract method information from metadata dictionary
        method_name = method.get("name", "unknownMethod")
        signature = method.get("signature", "")  # Full Java method signature
        description = method.get("description", "")  # Method description from metadata extraction
        
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
        
        # Generate method code based on Spring Data naming patterns
        # Spring Data uses method name patterns to infer query logic
        if method_name.startswith("findBy"):
            # Spring Data findBy* pattern -> Sequelize findOne
            # Extract field name from method name (remove "findBy" prefix)
            field = method_name[6:]  # Remove "findBy" (6 characters)
            # Convert field name to camelCase (first letter lowercase)
            field = field[0].lower() + field[1:] if field else "id"
            # Use first parameter as value for where clause
            param_value = params[0] if params else 'id'
            return f"""    /**
     * {description}
     * @description Finds an entity by field value. Converts Spring Data findBy* to Sequelize findOne.
     * @param {{any}} {param_value} - Field value to search for
     * @returns {{Promise<Object|null>}} Entity object or null if not found
     */
    async {method_name}({', '.join(params)}) {{
        // Spring Data findBy* -> Sequelize findOne with where clause
        return await {model_name}.findOne({{
            where: {{{field}: {param_value}}}
        }});
    }}"""
        elif method_name.startswith("findAllBy"):
            # Spring Data findAllBy* pattern -> Sequelize findAll
            # Extract field name from method name (remove "findAllBy" prefix)
            field = method_name[9:]  # Remove "findAllBy" (9 characters)
            # Convert field name to camelCase
            field = field[0].lower() + field[1:] if field else "id"
            param_value = params[0] if params else 'id'
            return f"""    /**
     * {description}
     * @description Finds all entities by field value. Converts Spring Data findAllBy* to Sequelize findAll.
     * @param {{any}} {param_value} - Field value to search for
     * @returns {{Promise<Array>}} Array of entity objects
     */
    async {method_name}({', '.join(params)}) {{
        // Spring Data findAllBy* -> Sequelize findAll with where clause
        return await {model_name}.findAll({{
            where: {{{field}: {param_value}}}
        }});
    }}"""
        elif method_name == "save" or method_name.startswith("save"):
            # Spring Data save pattern -> Sequelize create/update
            # Logic: if entity has ID, update; otherwise, create
            param_entity = params[0] if params else 'entity'
            return f"""    /**
     * {description}
     * @description Saves an entity (create or update). Converts Spring Data save to Sequelize create/update.
     * @param {{Object}} {param_entity} - Entity object to save
     * @returns {{Promise<Object>}} Saved entity object
     */
    async save({', '.join(params)}) {{
        // Spring Data save -> Sequelize create (if new) or update (if exists)
        // Check if entity has ID to determine create vs update
        if ({param_entity}.id) {{
            // Entity exists - perform update
            return await {model_name}.update({param_entity}, {{
                where: {{id: {param_entity}.id}}
            }});
        }} else {{
            // New entity - perform create
            return await {model_name}.create({param_entity});
        }}
    }}"""
        elif method_name.startswith("delete") or method_name.startswith("remove"):
            # Spring Data delete* pattern -> Sequelize destroy
            param_id = params[0] if params else 'id'
            return f"""    /**
     * {description}
     * @description Deletes an entity by ID. Converts Spring Data deleteById to Sequelize destroy.
     * @param {{any}} {param_id} - Entity ID to delete
     * @returns {{Promise<number>}} Number of deleted rows
     */
    async {method_name}({', '.join(params)}) {{
        // Spring Data deleteById -> Sequelize destroy with where clause
        return await {model_name}.destroy({{
            where: {{{param_id}}}
        }});
    }}"""
        else:
            # Generic method - doesn't match Spring Data patterns
            # Generate stub that needs manual implementation
            return f"""    /**
     * {description}
     * TODO: Implement method logic based on original Java repository method
     * @description Generic method - needs manual implementation
     */
    async {method_name}({', '.join(params)}) {{
        // TODO: Convert Spring Data query method to Sequelize query
        // Refer to original Java repository interface for implementation details
        throw new Error('Method not yet implemented');
    }}"""
    
    def _generate_basic_crud(self, model_name: str) -> List[str]:
        """
        Generate basic CRUD methods when no method metadata is available.
        
        This provides fundamental database operations:
        - findById: Retrieve single entity
        - findAll: Retrieve all entities
        - save: Create or update entity
        - deleteById: Delete entity by ID
        
        Args:
            model_name: Name of the Sequelize model
        
        Returns:
            List of method code lines as strings
        """
        return [
            "    /**",
            "     * Find entity by ID",
            "     * @description Retrieves an entity by its primary key",
            "     * @param {number} id - Entity ID",
            "     * @returns {Promise<Object|null>} Entity object or null if not found",
            "     */",
            f"    async findById(id) {{",
            # Sequelize findByPk is equivalent to Spring Data findById
            f"        return await {model_name}.findByPk(id);",
            "    }",
            "",
            "    /**",
            "     * Find all entities",
            "     * @description Retrieves all entities from the database",
            "     * @returns {Promise<Array>} Array of entity objects",
            "     */",
            f"    async findAll() {{",
            # Sequelize findAll is equivalent to Spring Data findAll
            f"        return await {model_name}.findAll();",
            "    }",
            "",
            "    /**",
            "     * Save entity (create or update)",
            "     * @description Creates a new entity or updates existing one based on ID presence",
            "     * @param {Object} entity - Entity object to save",
            "     * @returns {Promise<Object>} Saved entity object",
            "     */",
            f"    async save(entity) {{",
            # Spring Data save logic: create if new, update if exists
            f"        if (entity.id) {{",
            # Entity exists - perform update
            f"            return await {model_name}.update(entity, {{",
            "                where: {id: entity.id}",
            "            });",
            f"        }} else {{",
            # New entity - perform create
            f"            return await {model_name}.create(entity);",
            "        }",
            "    }",
            "",
            "    /**",
            "     * Delete entity by ID",
            "     * @description Deletes an entity by its primary key",
            "     * @param {number} id - Entity ID to delete",
            "     * @returns {Promise<number>} Number of deleted rows",
            "     */",
            f"    async deleteById(id) {{",
            # Sequelize destroy is equivalent to Spring Data deleteById
            f"        return await {model_name}.destroy({{",
            "            where: {id}",
            "        });",
            "    }",
        ]
    
    def _create_stub_repository(self, repo_metadata: Dict) -> Dict[str, Any]:
        """
        Create a minimal stub repository when conversion completely fails.
        
        This method is called as a last resort when:
        - LLM conversion fails
        - Metadata conversion fails
        - Java code is unreadable
        - Unexpected errors occur
        
        The stub ensures the conversion pipeline continues and provides
        a starting point for manual implementation.
        
        Args:
            repo_metadata: Repository metadata dictionary (may be incomplete)
        
        Returns:
            Dictionary with stub repository code
        """
        repo_name = repo_metadata.get("name", "Unknown")
        # Extract model name from repository name
        model_name = self._extract_model_name(repo_name)
        
        # Generate minimal repository stub with basic CRUD operations
        # Developers will need to implement additional methods based on original Java repository
        stub_code = f"""const {model_name} = require('../models/{model_name}');

/**
 * {repo_name} - Data Access Object
 * TODO: Implement repository methods based on original Java repository interface
 * 
 * This is a stub generated when automatic conversion failed.
 * Please refer to the original Java repository interface for method implementations.
 */
class {repo_name} {{
    /**
     * Find entity by ID
     * @description Basic CRUD operation - retrieves entity by primary key
     * @param {{number}} id - Entity ID
     * @returns {{Promise<Object|null>}} Entity object or null
     */
    async findById(id) {{
        return await {model_name}.findByPk(id);
    }}
    
    /**
     * Find all entities
     * @description Basic CRUD operation - retrieves all entities
     * @returns {{Promise<Array>}} Array of entity objects
     */
    async findAll() {{
        return await {model_name}.findAll();
    }}
    
    /**
     * Save entity (create or update)
     * @description Basic CRUD operation - creates new or updates existing entity
     * @param {{Object}} entity - Entity object to save
     * @returns {{Promise<Object>}} Saved entity object
     */
    async save(entity) {{
        // Handle create vs update based on entity.id
        if (entity.id) {{
            return await {model_name}.update(entity, {{where: {{id: entity.id}}}});
        }} else {{
            return await {model_name}.create(entity);
        }}
    }}
    
    /**
     * Delete entity by ID
     * @description Basic CRUD operation - deletes entity by primary key
     * @param {{number}} id - Entity ID to delete
     * @returns {{Promise<number>}} Number of deleted rows
     */
    async deleteById(id) {{
        return await {model_name}.destroy({{where: {{id}}}});
    }}
}}

module.exports = new {repo_name}();
"""
        
        return {
            "name": repo_name,
            "file_path": f"repositories/{repo_name}.js",
            "code": stub_code,
            "model_name": model_name,
            "type": "repository"
        }

