"""Convert JPA entities to Sequelize/TypeORM models"""

import re
import logging
from typing import Dict, Optional, List, Any
from ..clients.base_llm_client import BaseLLMClient
from ..clients.llm_client_factory import create_llm_client_from_config

logger = logging.getLogger(__name__)


class ModelConverter:
    """Converts JPA entities to Sequelize models"""
    
    # Java to JavaScript type mappings
    TYPE_MAPPING = {
        "String": "DataTypes.STRING",
        "Integer": "DataTypes.INTEGER",
        "Long": "DataTypes.BIGINT",
        "Double": "DataTypes.DOUBLE",
        "Float": "DataTypes.FLOAT",
        "Boolean": "DataTypes.BOOLEAN",
        "Date": "DataTypes.DATE",
        "BigDecimal": "DataTypes.DECIMAL",
        "byte[]": "DataTypes.BLOB",
        "LocalDate": "DataTypes.DATEONLY",
        "LocalDateTime": "DataTypes.DATE",
        "Timestamp": "DataTypes.DATE",
    }
    
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
        Initialize model converter
        
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
        self.orm_choice = orm_choice
        
        # If client provided, use it directly
        if llm_client:
            self.client = llm_client
            return
        
        # Legacy support: convert gemini_api_token if present
        if gemini_api_token and not api_token:
            provider = provider or "gemini"
            api_token = gemini_api_token
        
        # Create client if API token provided
        if api_token and model:
            self.client = create_llm_client_from_config(
                provider=provider or "gemini",
                api_token=api_token,
                model=model,
                base_url=base_url,
                profile_name=profile_name,
                config_path=config_path
            )
        else:
            self.client = None
    
    def convert_entity(self, entity_metadata: Dict, java_code: str) -> Dict[str, Any]:
        """
        Convert JPA entity to Sequelize model
        
        Args:
            entity_metadata: Metadata dict from MetadataExtractor with 'name', 'filePath', etc.
            java_code: Full Java entity source code
            
        Returns:
            Dictionary with:
            {
                "name": "ModelName",
                "file_path": "models/ModelName.js",
                "code": "...",
                "table_name": "..."
            }
        """
        try:
            if self.client:
                # Use LLM for complex conversions
                return self._convert_with_llm(entity_metadata, java_code)
            else:
                # Use regex-based conversion
                return self._convert_with_regex(entity_metadata, java_code)
        except Exception as e:
            logger.error(f"Failed to convert entity {entity_metadata.get('name', 'unknown')}: {e}")
            return self._create_stub_model(entity_metadata)
    
    def _convert_with_llm(self, entity_metadata: Dict, java_code: str) -> Dict[str, Any]:
        """Convert using LLM for better accuracy with chunking support for large entities"""
        
        # Check if code exceeds token limit and needs chunking
        estimated_tokens = self.client.estimate_tokens(java_code) if self.client else len(java_code) * 0.25
        max_tokens = 8000  # Token limit for chunking
        
        if estimated_tokens > max_tokens and self.client:
            # Use chunked conversion for large entities
            return self._convert_with_llm_chunked(entity_metadata, java_code)
        
        # Standard conversion for smaller entities
        prompt = f"""Convert this JPA entity to a Sequelize model.

Java Entity Code:
```java
{java_code[:8000] if not self.client else java_code}
```

Requirements:
1. Map JPA annotations to Sequelize equivalents:
   - @Entity -> model definition
   - @Table(name="...") -> tableName in options
   - @Id -> primaryKey
   - @GeneratedValue -> autoIncrement
   - @Column(name="...", nullable=...) -> fieldName and allowNull
   - @ManyToOne, @OneToMany, @ManyToMany -> associations
   - @JoinColumn -> foreign key definition

2. Convert Java types to Sequelize DataTypes:
   - String -> DataTypes.STRING
   - Integer -> DataTypes.INTEGER
   - Long -> DataTypes.BIGINT
   - Double/Float -> DataTypes.DOUBLE/FLOAT
   - Boolean -> DataTypes.BOOLEAN
   - Date/LocalDateTime -> DataTypes.DATE
   - BigDecimal -> DataTypes.DECIMAL

3. Generate complete Sequelize model with:
   - Proper model definition
   - All fields with correct types
   - Primary key configuration
   - Table name mapping
   - Relationships (associations)
   - Timestamps if @Entity has @MappedSuperclass or uses @CreatedDate/@LastModifiedDate

4. Use Sequelize v6 syntax

Return only the complete model code, no explanations."""

        try:
            converted_code = self.client.generate(prompt, max_tokens=4000)
            
            # Extract table name
            table_name = self._extract_table_name(java_code)
            model_name = entity_metadata.get("name", "Unknown")
            
            # Determine file path
            file_path = f"models/{model_name}.js"
            
            return {
                "name": model_name,
                "file_path": file_path,
                "code": converted_code,
                "table_name": table_name,
                "type": "model"
            }
        except Exception as e:
            logger.warning(f"LLM conversion failed, falling back to regex: {e}")
            return self._convert_with_regex(entity_metadata, java_code)
    
    def _convert_with_llm_chunked(self, entity_metadata: Dict, java_code: str) -> Dict[str, Any]:
        """Convert large entity using chunking strategy"""
        model_name = entity_metadata.get("name", "Unknown")
        
        system_prompt = f"""Convert this JPA entity to a Sequelize model.

For each chunk of this large entity, provide the converted Sequelize code for the fields and relationships in that chunk.
Preserve all JPA annotations, field types, and relationships.

Requirements:
1. Map JPA annotations to Sequelize equivalents (@Entity, @Table, @Id, @Column, @ManyToOne, etc.)
2. Convert Java types to Sequelize DataTypes
3. Preserve relationships and associations
4. Use Sequelize v6 syntax

The final combined result should be a complete, working Sequelize model."""
        
        def process_chunk(client, chunk_prompt):
            """Process individual chunk"""
            return client.generate(chunk_prompt, max_tokens=4000, context=f"Model Conversion (Chunk): {model_name}")
        
        def combine_results(chunk_results):
            """Combine chunk results into single model"""
            # Extract table name from original code
            table_name = self._extract_table_name(java_code)
            
            # If we have multiple chunks, combine them
            if len(chunk_results) == 1:
                combined_code = str(chunk_results[0])
            else:
                # Combine multiple chunk results
                combine_prompt = f"""Combine these partial Sequelize model conversions into a single complete model.

Model Name: {model_name}
Table Name: {table_name}

Partial conversions:
{chr(10).join([f'--- Chunk {i+1} ---{chr(10)}{str(result)}' for i, result in enumerate(chunk_results)])}

Requirements:
1. Merge all fields from all chunks
2. Ensure only one model definition (not multiple define() calls)
3. Preserve all relationships and associations
4. Maintain proper Sequelize syntax
5. Include all imports and dependencies

Return only the complete, merged Sequelize model code."""
                combined_code = self.client.generate(combine_prompt, max_tokens=6000, context=f"Model Combination: {model_name}")
            
            return {
                "name": model_name,
                "file_path": f"models/{model_name}.js",
                "code": combined_code,
                "table_name": table_name,
                "type": "model"
            }
        
        try:
            result = self.client.process_large_content(
                java_code,
                system_prompt,
                process_chunk_fn=process_chunk,
                combine_results_fn=combine_results,
                context=f"Model Conversion: {model_name}"
            )
            return result
        except Exception as e:
            logger.warning(f"Chunked conversion failed, falling back to regex: {e}")
            return self._convert_with_regex(entity_metadata, java_code)
    
    def _convert_with_regex(self, entity_metadata: Dict, java_code: str) -> Dict[str, Any]:
        """Convert using regex patterns (fallback)"""
        
        model_name = entity_metadata.get("name", "Unknown")
        table_name = self._extract_table_name(java_code)
        
        # Extract fields
        fields = self._extract_fields(java_code)
        
        # Generate Sequelize model
        model_code = self._generate_sequelize_model(model_name, table_name, fields)
        
        return {
            "name": model_name,
            "file_path": f"models/{model_name}.js",
            "code": model_code,
            "table_name": table_name,
            "type": "model"
        }
    
    def _extract_table_name(self, java_code: str) -> str:
        """Extract table name from @Table annotation"""
        match = re.search(r'@Table\s*\(\s*name\s*=\s*"([^"]+)"', java_code)
        if match:
            return match.group(1)
        
        # Default: convert class name to snake_case
        class_match = re.search(r'class\s+(\w+)', java_code)
        if class_match:
            class_name = class_match.group(1)
            # Convert CamelCase to snake_case
            snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
            return snake_case
        
        return "unknown_table"
    
    def _extract_fields(self, java_code: str) -> List[Dict]:
        """Extract field definitions from Java code"""
        fields = []
        
        # Pattern to match field declarations with annotations
        field_pattern = r'(?:@\w+(?:\([^)]*\))?\s*)*\s*(?:private|protected|public)\s+(\w+(?:<[^>]+>)?)\s+(\w+)\s*[;=]'
        
        for match in re.finditer(field_pattern, java_code):
            java_type = match.group(1).strip()
            field_name = match.group(2).strip()
            
            # Check for @Id annotation before this field
            field_start = match.start()
            preceding = java_code[max(0, field_start - 200):field_start]
            
            is_id = '@Id' in preceding or field_name.lower() == 'id'
            is_nullable = '@Column' not in preceding or 'nullable = false' not in preceding
            
            # Map type
            js_type = self._map_type(java_type)
            
            fields.append({
                "name": field_name,
                "type": js_type,
                "primary_key": is_id,
                "nullable": is_nullable,
                "auto_increment": is_id and '@GeneratedValue' in preceding
            })
        
        return fields
    
    def _map_type(self, java_type: str) -> str:
        """Map Java type to Sequelize DataType"""
        # Remove generics
        base_type = re.sub(r'<.*>', '', java_type).strip()
        
        # Check mapping table
        if base_type in self.TYPE_MAPPING:
            return self.TYPE_MAPPING[base_type]
        
        # Default to STRING for unknown types
        return "DataTypes.STRING"
    
    def _generate_sequelize_model(self, model_name: str, table_name: str, fields: List[Dict]) -> str:
        """Generate Sequelize model code"""
        
        lines = [
            "const { DataTypes } = require('sequelize');",
            "const sequelize = require('../config/database');",
            "",
            f"const {model_name} = sequelize.define('{model_name}', {{"
        ]
        
        # Add fields
        for field in fields:
            field_def = []
            field_def.append(f"    {field['name']}: {{")
            field_def.append(f"        type: {field['type']},")
            
            if field.get('primary_key'):
                field_def.append("        primaryKey: true,")
            
            if field.get('auto_increment'):
                field_def.append("        autoIncrement: true,")
            
            if not field.get('nullable'):
                field_def.append("        allowNull: false,")
            
            field_def.append("    },")
            lines.extend(field_def)
        
        # Close model definition
        lines.append("}, {")
        lines.append(f'    tableName: "{table_name}",')
        lines.append("    timestamps: true,")
        lines.append("});")
        lines.append("")
        lines.append(f"module.exports = {model_name};")
        
        return "\n".join(lines)
    
    def _create_stub_model(self, entity_metadata: Dict) -> Dict[str, Any]:
        """Create a stub model when conversion fails"""
        model_name = entity_metadata.get("name", "Unknown")
        
        stub_code = f"""const {{ DataTypes }} = require('sequelize');
const sequelize = require('../config/database');

const {model_name} = sequelize.define('{model_name}', {{
    // TODO: Add fields based on Java entity
    id: {{
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true,
    }},
}}, {{
    tableName: '{model_name.lower()}',
    timestamps: true,
}});

module.exports = {model_name};
"""
        
        return {
            "name": model_name,
            "file_path": f"models/{model_name}.js",
            "code": stub_code,
            "table_name": model_name.lower(),
            "type": "model"
        }

