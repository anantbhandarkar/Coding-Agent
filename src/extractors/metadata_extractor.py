"""Metadata extractor using LLM to extract project overview and module information"""

import json
import logging
from typing import Dict, List, Any, Optional
from ..clients.llm_client_factory import create_llm_client_from_config
from ..clients.base_llm_client import BaseLLMClient

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extracts comprehensive metadata from Java codebase using LLM"""
    
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
        Initialize metadata extractor
        
        Args:
            llm_client: Pre-configured LLM client (optional, takes precedence)
            provider: LLM provider name ("gemini", "glm", "openrouter", "openai")
            api_token: API token for the provider
            model: Model name
            base_url: Optional base URL (for GLM/OpenAI custom endpoints)
            profile_name: Profile name from config file
            config_path: Path to config file
            gemini_api_token: Legacy parameter (deprecated, use provider="gemini" with api_token)
        """
        # If client provided, use it directly
        if llm_client:
            self.client = llm_client
            return
        
        # Legacy support: convert gemini_api_token to new format
        if gemini_api_token and not api_token:
            provider = provider or "gemini"
            api_token = gemini_api_token
        
        # Create client using factory
        self.client = create_llm_client_from_config(
            provider=provider,
            api_token=api_token,
            model=model,
            base_url=base_url,
            profile_name=profile_name,
            config_path=config_path
        )
    
    def analyze_codebase(self, file_map: Dict[str, List[Dict]]) -> Dict:
        """
        Analyze entire codebase and extract metadata
        
        Args:
            file_map: Categorized file map from RepositoryAnalyzer
            
        Returns:
            Project overview JSON with structure:
            {
                "projectOverview": "...",
                "modules": [
                    {
                        "name": "...",
                        "description": "...",
                        "type": "Controller|Service|Repository|Entity|Other",
                        "methods": [
                            {
                                "name": "...",
                                "signature": "...",
                                "description": "...",
                                "complexity": "Low|Medium|High"
                            }
                        ],
                        "dependencies": ["..."]
                    }
                ]
            }
        """
        logger.info("Starting metadata extraction...")
        
        # Extract project overview first
        project_overview = self._extract_project_overview(file_map)
        
        # Extract module metadata
        modules = []
        
        # Quality tracking
        quality_stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "retried": 0,
            "fallback_used": 0,
            "average_score": 0.0,
            "scores": []
        }
        
        # Process all file categories
        for category in ['controllers', 'services', 'repositories', 'entities', 'configs', 'other']:
            files = file_map.get(category, [])
            logger.info(f"Processing {len(files)} {category} files...")
            
            for file_info in files:
                file_path = file_info.get('relative_path', file_info.get('path', 'unknown'))
                logger.info(f"Extracting metadata from: {file_path}")
                
                # Update execution status
                try:
                    from ..agents.orchestrator import _execution_status
                    _execution_status["current_file"] = file_path
                    _execution_status["files_processed"] = len(modules)
                except:
                    pass
                
                try:
                    module_metadata = self._extract_module_metadata(file_info, category)
                    if module_metadata:
                        # Validate quality and track stats
                        quality = self._validate_metadata_quality(module_metadata, file_info)
                        quality_stats["total"] += 1
                        quality_stats["scores"].append(quality['score'])
                        
                        if quality['validated']:
                            quality_stats["passed"] += 1
                        else:
                            quality_stats["failed"] += 1
                            if quality['score'] < 0.5:
                                quality_stats["fallback_used"] += 1
                        
                        # Remove quality metadata if present
                        if '_quality' in module_metadata:
                            del module_metadata['_quality']
                        
                        modules.append(module_metadata)
                        
                        quality_status = "✓" if quality['validated'] else "⚠"
                        logger.info(f"{quality_status} Extracted: {file_path} (quality: {quality['score']:.2f})")
                        
                        # Update execution status
                        try:
                            from ..agents.orchestrator import _execution_status
                            _execution_status["files_processed"] = len(modules)
                        except:
                            pass
                except ValueError as e:
                    error_msg = str(e)
                    # Check if it's a safety filter block
                    if "safety filters" in error_msg.lower():
                        logger.error(f"⚠️  Safety filter blocked: {file_path}")
                        logger.error(f"   Error: {error_msg[:200]}...")
                        # Store safety block info
                        from ..agents.orchestrator import _execution_status
                        _execution_status["safety_blocks"].append({
                            "file": file_path,
                            "category": category,
                            "error": error_msg
                        })
                    logger.warning(f"Failed to extract metadata for {file_path}: {error_msg}")
                    quality_stats["failed"] += 1
                except Exception as e:
                    logger.warning(f"Failed to extract metadata for {file_info.get('path', 'unknown')}: {e}")
                    # Create minimal metadata entry using enhanced fallback
                    fallback_metadata = self._extract_basic_metadata(file_info, category)
                    modules.append(fallback_metadata)
                    quality_stats["total"] += 1
                    quality_stats["failed"] += 1
                    quality_stats["fallback_used"] += 1
        
        # Calculate quality statistics
        if quality_stats["scores"]:
            quality_stats["average_score"] = sum(quality_stats["scores"]) / len(quality_stats["scores"])
        
        # Log quality statistics
        logger.info(f"Extracted metadata for {len(modules)} modules")
        logger.info(f"Quality Statistics:")
        logger.info(f"  - Total modules: {quality_stats['total']}")
        logger.info(f"  - Passed validation: {quality_stats['passed']} ({100*quality_stats['passed']/max(quality_stats['total'], 1):.1f}%)")
        logger.info(f"  - Failed validation: {quality_stats['failed']} ({100*quality_stats['failed']/max(quality_stats['total'], 1):.1f}%)")
        logger.info(f"  - Enhanced fallback used: {quality_stats['fallback_used']}")
        logger.info(f"  - Average quality score: {quality_stats['average_score']:.2f}")
        
        return {
            "projectOverview": project_overview,
            "modules": modules,
            "_quality_stats": quality_stats  # Include in output for reference (can be removed)
        }
    
    def analyze_codebase_from_file(self, codebase_text_file: str, file_map: Dict[str, List[Dict]]) -> Dict:
        """
        Analyze entire codebase from consolidated text file and extract metadata
        
        Args:
            codebase_text_file: Path to consolidated codebase text file from gitingest
            file_map: Categorized file map from RepositoryAnalyzer (without full content)
            
        Returns:
            Project overview JSON with structure:
            {
                "projectOverview": "...",
                "modules": [
                    {
                        "name": "...",
                        "description": "...",
                        "type": "Controller|Service|Repository|Entity|Other",
                        "methods": [...],
                        "dependencies": ["..."]
                    }
                ]
            }
        """
        logger.info(f"Starting metadata extraction from consolidated codebase file: {codebase_text_file}")
        
        try:
            # Read consolidated codebase file
            with open(codebase_text_file, 'r', encoding='utf-8') as f:
                codebase_content = f.read()
            
            logger.info(f"Read {len(codebase_content)} characters from consolidated codebase file")
            
            # Build structure summary for context
            structure_summary = self._build_structure_summary(file_map)
            
            # Extract project overview using consolidated file
            project_overview = self._extract_project_overview_from_file(codebase_content, structure_summary)
            
            # Extract all module metadata in one pass from consolidated file
            modules = self._extract_all_modules_from_file(codebase_content, file_map, structure_summary)
            
            logger.info(f"Extracted metadata for {len(modules)} modules from consolidated file")
            
            return {
                "projectOverview": project_overview,
                "modules": modules
            }
        except Exception as e:
            logger.error(f"Failed to analyze codebase from file: {e}")
            # Fallback to basic extraction
            return {
                "projectOverview": "Spring Boot application - analysis from consolidated file failed",
                "modules": []
            }
    
    def _build_structure_summary(self, file_map: Dict[str, List[Dict]]) -> str:
        """Build summary of file structure for context"""
        summary = "Project structure:\n"
        for category in ['controllers', 'services', 'repositories', 'entities', 'configs', 'other']:
            files = file_map.get(category, [])
            if files:
                summary += f"- {len(files)} {category}: "
                names = [f.get('class_name', 'unknown') for f in files[:5]]
                summary += ", ".join(names)
                if len(files) > 5:
                    summary += f" (and {len(files) - 5} more)"
                summary += "\n"
        return summary
    
    def _extract_project_overview_from_file(self, codebase_content: str, structure_summary: str) -> str:
        """Extract project overview from consolidated codebase file"""
        prompt = f"""Analyze this Java Spring Boot codebase and provide a high-level overview.

{structure_summary}

Full codebase content:
{codebase_content[:50000]}  # Use first 50KB for overview

Provide a concise 2-3 sentence overview describing:
1. The primary purpose/domain of this application
2. The main functionality it provides
3. Main features or capabilities

Return only the overview text, no additional formatting."""

        try:
            overview = self.client.generate(
                prompt,
                max_tokens=500,
                temperature=0.3,
                context="Project Overview Extraction (Consolidated File)"
            )
            return overview.strip()
        except Exception as e:
            logger.error(f"Failed to extract project overview from consolidated file: {e}")
            return "Spring Boot application - purpose and functionality to be determined from code analysis."
    
    def _extract_all_modules_from_file(self, codebase_content: str, file_map: Dict[str, List[Dict]], structure_summary: str) -> List[Dict]:
        """Extract metadata for all modules from consolidated codebase file"""
        modules = []
        
        # Quality tracking
        quality_stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "fallback_used": 0,
            "average_score": 0.0,
            "scores": []
        }
        
        # Build list of all files to process
        all_files = []
        for category in ['controllers', 'services', 'repositories', 'entities', 'configs', 'other']:
            for file_info in file_map.get(category, []):
                all_files.append((file_info, category))
        
        logger.info(f"Extracting metadata for {len(all_files)} modules from consolidated file...")
        
        # Update execution status
        try:
            from ..agents.orchestrator import _execution_status
            _execution_status["files_total"] = len(all_files)
            _execution_status["files_processed"] = 0
        except:
            pass
        
        # Process files, using consolidated codebase content
        for idx, (file_info, category) in enumerate(all_files):
            file_path = file_info.get('relative_path', file_info.get('path', 'unknown'))
            class_name = file_info.get('class_name', 'Unknown')
            
            # Update execution status
            try:
                from ..agents.orchestrator import _execution_status
                _execution_status["current_file"] = file_path
                _execution_status["files_processed"] = idx
            except:
                pass
            
            try:
                # Extract module metadata using consolidated file
                # Search for the class in the consolidated content
                module_metadata = self._extract_module_from_consolidated_file(
                    codebase_content, file_info, category, structure_summary
                )
                
                if module_metadata:
                    # Validate quality and track stats
                    quality = self._validate_metadata_quality(module_metadata, file_info)
                    quality_stats["total"] += 1
                    quality_stats["scores"].append(quality['score'])
                    
                    if quality['validated']:
                        quality_stats["passed"] += 1
                    else:
                        quality_stats["failed"] += 1
                        if quality['score'] < 0.5:
                            quality_stats["fallback_used"] += 1
                    
                    # Remove quality metadata if present
                    if '_quality' in module_metadata:
                        del module_metadata['_quality']
                    
                    modules.append(module_metadata)
                    
                    quality_status = "✓" if quality['validated'] else "⚠"
                    logger.info(f"{quality_status} Extracted: {file_path} (quality: {quality['score']:.2f})")
            except ValueError as e:
                error_msg = str(e)
                if "safety filters" in error_msg.lower():
                    logger.error(f"⚠️  Safety filter blocked: {file_path}")
                    from ..agents.orchestrator import _execution_status
                    _execution_status["safety_blocks"].append({
                        "file": file_path,
                        "category": category,
                        "error": error_msg
                    })
                logger.warning(f"Failed to extract metadata for {file_path}: {error_msg}")
                # Create minimal metadata entry using enhanced fallback
                fallback_metadata = self._extract_basic_metadata(file_info, category)
                modules.append(fallback_metadata)
                quality_stats["total"] += 1
                quality_stats["failed"] += 1
                quality_stats["fallback_used"] += 1
            except Exception as e:
                logger.warning(f"Failed to extract metadata for {file_path}: {e}")
                # Create minimal metadata entry using enhanced fallback
                fallback_metadata = self._extract_basic_metadata(file_info, category)
                modules.append(fallback_metadata)
                quality_stats["total"] += 1
                quality_stats["failed"] += 1
                quality_stats["fallback_used"] += 1
        
        # Calculate quality statistics
        if quality_stats["scores"]:
            quality_stats["average_score"] = sum(quality_stats["scores"]) / len(quality_stats["scores"])
        
        # Log quality statistics
        logger.info(f"Extracted metadata for {len(modules)} modules from consolidated file")
        logger.info(f"Quality Statistics (Consolidated File):")
        logger.info(f"  - Total modules: {quality_stats['total']}")
        logger.info(f"  - Passed validation: {quality_stats['passed']} ({100*quality_stats['passed']/max(quality_stats['total'], 1):.1f}%)")
        logger.info(f"  - Failed validation: {quality_stats['failed']} ({100*quality_stats['failed']/max(quality_stats['total'], 1):.1f}%)")
        logger.info(f"  - Enhanced fallback used: {quality_stats['fallback_used']}")
        logger.info(f"  - Average quality score: {quality_stats['average_score']:.2f}")
        
        return modules
    
    def _extract_module_from_consolidated_file(
        self, 
        codebase_content: str, 
        file_info: Dict, 
        category: str,
        structure_summary: str
    ) -> Optional[Dict]:
        """Extract metadata for a single module from consolidated codebase file"""
        class_name = file_info.get('class_name', 'Unknown')
        file_path = file_info.get('relative_path', '')
        
        # Try to locate the class in the consolidated content
        # Look for class declaration or file path marker
        class_marker = f"class {class_name}" if class_name != 'Unknown' else ""
        file_marker = file_path.replace('\\', '/') if file_path else ""
        
        # Build prompt with relevant section of codebase
        # If file path is in content, try to extract relevant section
        content_section = codebase_content
        if file_marker and file_marker in codebase_content:
            # Try to find file section (gitingest may include file paths)
            marker_index = codebase_content.find(file_marker)
            if marker_index > 0:
                # Extract section around this file (50KB before and after)
                start = max(0, marker_index - 25000)
                end = min(len(codebase_content), marker_index + 25000)
                content_section = codebase_content[start:end]
        elif class_marker and class_marker in codebase_content:
            # Try to find class by name
            marker_index = codebase_content.find(class_marker)
            if marker_index > 0:
                start = max(0, marker_index - 25000)
                end = min(len(codebase_content), marker_index + 25000)
                content_section = codebase_content[start:end]
        
        # Limit content section size for LLM
        if len(content_section) > 50000:
            content_section = content_section[:50000]
        
        prompt = self._build_extraction_prompt(content_section, class_name, category)
        
        context_str = f"Metadata Extraction (Consolidated File): {file_path} ({category})"
        
        try:
            schema = {
                "name": class_name,
                "description": "string - clear description of what this class does",
                "type": self._map_category_to_type(category),
                "methods": [
                    {
                        "name": "string",
                        "signature": "string - full method signature with parameters",
                        "description": "string - what this method does",
                        "complexity": "Low|Medium|High"
                    }
                ],
                "dependencies": ["string - list of other classes this depends on"]
            }
            
            response = self.client.generate_structured(prompt, schema, context=context_str)
            
            if not isinstance(response, dict):
                raise ValueError("Invalid response format")
            
            # Ensure required fields
            response['name'] = response.get('name', class_name)
            response['type'] = response.get('type', self._map_category_to_type(category))
            response['description'] = response.get('description', f"{class_name} class")
            response['methods'] = response.get('methods', [])
            response['dependencies'] = response.get('dependencies', [])
            response['filePath'] = file_path
            
            return response
            
        except Exception as e:
            logger.warning(f"Failed to extract metadata for {class_name} from consolidated file: {e}")
            # Fallback to enhanced basic metadata extraction
            # Try to get content from consolidated file if possible
            if content_section and len(content_section) > 100:
                # Use the extracted section for fallback
                file_info_with_content = file_info.copy()
                file_info_with_content['content'] = content_section
                return self._extract_basic_metadata(file_info_with_content, category)
            else:
                # Use fallback without content
                return self._extract_basic_metadata(file_info, category)
    
    def _extract_project_overview(self, file_map: Dict[str, List[Dict]]) -> str:
        """Extract high-level project overview"""
        
        # Build summary of project structure
        summary = f"Java project with:\n"
        summary += f"- {len(file_map.get('controllers', []))} controllers\n"
        summary += f"- {len(file_map.get('services', []))} services\n"
        summary += f"- {len(file_map.get('repositories', []))} repositories\n"
        summary += f"- {len(file_map.get('entities', []))} entities\n"
        
        # Get sample of controller names for context
        if file_map.get('controllers'):
            sample_controllers = [f.get('class_name', '') for f in file_map['controllers'][:3]]
            summary += f"\nSample controllers: {', '.join(sample_controllers)}\n"
        
        prompt = f"""Analyze this Java Spring Boot project structure and provide a high-level overview of what this application does.

Project structure summary:
{summary}

Provide a concise 2-3 sentence overview describing:
1. The primary purpose/domain of this application
2. The main functionality it provides
3. Main features or capabilities

Return only the overview text, no additional formatting."""

        try:
            overview = self.client.generate(
                prompt, 
                max_tokens=500, 
                temperature=0.3,
                context="Project Overview Extraction"
            )
            return overview.strip()
        except ValueError as e:
            # Handle safety filter blocks - provide fallback
            error_msg = str(e)
            if "safety filters" in error_msg.lower():
                logger.warning(f"Project overview extraction blocked by safety filters: {e}")
                logger.info("Attempting to generate overview with modified prompt...")
                # Try a more generic prompt
                try:
                    generic_prompt = f"""Provide a brief description (2-3 sentences) of what this Java application does based on these file counts:
                    - {len(file_map.get('controllers', []))} controllers
                    - {len(file_map.get('services', []))} services  
                    - {len(file_map.get('repositories', []))} repositories
                    - {len(file_map.get('entities', []))} entities
                    
                    Keep the description generic and professional."""
                    overview = self.client.generate(
                        generic_prompt, 
                        max_tokens=300, 
                        temperature=0.3,
                        context="Project Overview Extraction (Fallback)"
                    )
                    return overview.strip()
                except Exception as e2:
                    logger.warning(f"Fallback overview extraction also failed: {e2}")
            else:
                logger.error(f"Failed to extract project overview: {e}")
            return "Spring Boot application - purpose and functionality to be determined from code analysis."
        except Exception as e:
            logger.error(f"Failed to extract project overview: {e}")
            return "Spring Boot application - purpose and functionality to be determined from code analysis."
    
    def _extract_module_metadata(
        self,
        file_info: Dict,
        category: str
    ) -> Optional[Dict]:
        """Extract metadata for a single module/class with quality validation and retry logic"""
        
        content = file_info.get('content', '')
        class_name = file_info.get('class_name', 'Unknown')
        file_path = file_info.get('relative_path', '')
        
        # If content is too large, use chunking (without retry for now)
        estimated_tokens = self.client.estimate_tokens(content)
        
        if estimated_tokens > 8000:
            # Use chunking approach
            result = self._extract_module_metadata_chunked(file_info, category)
            # Validate chunked result but don't retry (would be expensive)
            if result:
                quality = self._validate_metadata_quality(result, file_info)
                if quality.get('issues'):
                    logger.warning(f"Quality issues in chunked extraction for {class_name}: {quality['issues']}")
                    # Use enhanced fallback if quality is too poor
                    if quality['score'] < 0.5:
                        logger.info(f"Using enhanced fallback for {class_name} due to poor quality")
                        return self._extract_basic_metadata(file_info, category)
            return result
        
        # Standard extraction with retry logic
        max_retries = 3
        retry_count = 0
        previous_quality_issues = []
        
        while retry_count <= max_retries:
            try:
                # Build prompt based on retry count
                if retry_count == 0:
                    prompt = self._build_extraction_prompt(content, class_name, category)
                else:
                    # Use retry prompt with quality issues from previous attempt
                    prompt = self._build_retry_prompt(content, class_name, category, 
                                                     previous_quality_issues, retry_count)
                
                # Create context string for logging
                context_str = f"Metadata Extraction: {file_path} ({category})"
                if retry_count > 0:
                    context_str += f" (Retry {retry_count})"
                
                # Generate structured response
                schema = {
                    "name": class_name,
                    "description": "string - clear description of what this class does (at least 30 characters)",
                    "type": self._map_category_to_type(category),
                    "methods": [
                        {
                            "name": "string",
                            "signature": "string - full method signature with parameters",
                            "description": "string - what this method does (at least 5 characters)",
                            "complexity": "Low|Medium|High"
                        }
                    ],
                    "dependencies": ["string - list of other classes this depends on"]
                }
                
                response = self.client.generate_structured(prompt, schema, context=context_str)
                
                # Validate and enhance response
                if not isinstance(response, dict):
                    raise ValueError("Invalid response format")
                
                # Ensure required fields
                response['name'] = response.get('name', class_name)
                response['type'] = response.get('type', self._map_category_to_type(category))
                response['description'] = response.get('description', f"{class_name} class")
                response['methods'] = response.get('methods', [])
                response['dependencies'] = response.get('dependencies', [])
                
                # Add file path for reference
                response['filePath'] = file_path
                
                # Validate quality
                quality = self._validate_metadata_quality(response, file_info)
                
                # If quality is good or we've exhausted retries, return result
                if quality['validated'] or retry_count == max_retries:
                    if not quality['validated'] and retry_count == max_retries:
                        logger.warning(f"Quality issues remain for {class_name} after {max_retries} retries: {quality['issues']}")
                        logger.info(f"Quality score: {quality['score']:.2f}")
                        # If quality is too poor, use enhanced fallback
                        if quality['score'] < 0.5:
                            logger.info(f"Using enhanced fallback for {class_name} due to poor quality")
                            return self._extract_basic_metadata(file_info, category)
                    else:
                        if retry_count > 0:
                            logger.info(f"Quality improved for {class_name} after retry {retry_count}")
                    
                    # Remove quality metadata before returning
                    return response
                
                # Quality issues found, prepare for retry
                previous_quality_issues = quality['issues']
                retry_count += 1
                logger.warning(f"Quality issues for {class_name}, retry {retry_count}/{max_retries}: {previous_quality_issues}")
                
            except ValueError as e:
                error_msg = str(e)
                if "safety filters" in error_msg.lower():
                    # Don't retry on safety filter blocks
                    logger.error(f"⚠️  Safety filter blocked: {file_path}")
                    return self._extract_basic_metadata(file_info, category)
                # For other ValueError, retry
                if retry_count < max_retries:
                    retry_count += 1
                    logger.warning(f"Failed extraction attempt {retry_count} for {class_name}: {e}")
                    continue
                else:
                    logger.error(f"Failed after {max_retries} retries for {class_name}: {e}")
                    return self._extract_basic_metadata(file_info, category)
            
            except Exception as e:
                # For other exceptions, retry once then fallback
                if retry_count < max_retries:
                    retry_count += 1
                    logger.warning(f"Exception during extraction for {class_name}, retry {retry_count}: {e}")
                    continue
                else:
                    logger.error(f"Failed after {max_retries} retries for {class_name}: {e}")
                    return self._extract_basic_metadata(file_info, category)
        
        # Should not reach here, but fallback just in case
        return self._extract_basic_metadata(file_info, category)
    
    def _extract_module_metadata_chunked(
        self,
        file_info: Dict,
        category: str
    ) -> Dict:
        """Extract metadata for large files using chunking"""
        
        content = file_info.get('content', '')
        class_name = file_info.get('class_name', 'Unknown')
        file_path = file_info.get('relative_path', 'unknown')
        context_str = f"Metadata Extraction (Chunked): {file_path} ({category})"
        
        # Process in chunks
        def process_chunk(client, chunk_prompt):
            schema = {
                "methods": [
                    {
                        "name": "string",
                        "signature": "string",
                        "description": "string",
                        "complexity": "Low|Medium|High"
                    }
                ],
                "dependencies": ["string"]
            }
            chunk_context = f"{context_str} (chunk processing)"
            return client.generate_structured(chunk_prompt, schema, context=chunk_context)
        
        def combine_results(chunk_results):
            all_methods = []
            all_dependencies = set()
            
            for result in chunk_results:
                if isinstance(result, dict):
                    all_methods.extend(result.get('methods', []))
                    all_dependencies.update(result.get('dependencies', []))
            
            return {
                "name": class_name,
                "description": f"{class_name} class with {len(all_methods)} methods",
                "type": self._map_category_to_type(category),
                "methods": all_methods,
                "dependencies": list(all_dependencies)
            }
        
        system_prompt = f"""Extract method information from this {category} class.
For each method, provide name, full signature, description, and complexity estimate (Low/Medium/High).
Also identify any dependencies (other classes this code references)."""
        
        result = self.client.process_large_content(
            content,
            system_prompt,
            process_chunk_fn=process_chunk,
            combine_results_fn=combine_results,
            context=context_str
        )
        
        if not result:
            return self._extract_basic_metadata(file_info, category)
        
        result['filePath'] = file_info.get('relative_path', '')
        return result
    
    def _extract_basic_metadata(self, file_info: Dict, category: str) -> Dict:
        """Enhanced fallback: extract basic metadata using regex patterns with intelligent heuristics"""
        import re
        
        content = file_info.get('content', '')
        class_name = file_info.get('class_name', 'Unknown')
        file_path = file_info.get('relative_path', '')
        
        # Generate better description
        description = self._generate_description_from_code(content, class_name, category)
        
        # Extract methods using regex with complexity analysis
        method_pattern = r'(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(?:abstract\s+)?[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*(?:\{|throws|;|\n)'
        methods = []
        method_matches = list(re.finditer(method_pattern, content))
        
        for match in method_matches:
            method_name = match.group(1)
            if method_name in ['class', 'interface', 'enum']:  # Skip false positives
                continue
            
            # Try to get full signature
            sig_start = content.rfind('\n', 0, match.start())
            sig_end = content.find('{', match.end())
            if sig_start > 0 and sig_end > sig_start:
                signature = content[sig_start:sig_end].strip()
            else:
                # Try to find method return type
                return_type_match = re.search(r'(\w+)\s+' + re.escape(method_name) + r'\s*\(', content[max(0, match.start()-100):match.start()])
                if return_type_match:
                    return_type = return_type_match.group(1)
                    signature = f"{return_type} {method_name}()"
                else:
                    signature = f"{method_name}()"
            
            # Extract method body for complexity estimation
            method_body = ""
            if sig_end > 0:
                # Find matching brace for method body
                brace_count = 0
                body_start = sig_end
                for i, char in enumerate(content[body_start:body_start+5000]):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            method_body = content[body_start:body_start+i+1]
                            break
            
            # Estimate complexity from method body
            complexity = self._estimate_complexity_from_code(method_body)
            
            # Generate better method description
            method_desc = self._generate_method_description(method_name, signature, method_body)
            
            methods.append({
                "name": method_name,
                "signature": signature,
                "description": method_desc,
                "complexity": complexity
            })
        
        # Use comprehensive dependency extraction
        dependencies = self._extract_dependencies_comprehensive(content)
        
        return {
            "name": class_name,
            "description": description,
            "type": self._map_category_to_type(category),
            "methods": methods[:20],  # Limit to first 20 methods
            "dependencies": dependencies[:15],  # Limit dependencies but use more
            "filePath": file_path
        }
    
    def _generate_description_from_code(self, content: str, class_name: str, category: str) -> str:
        """Generate description from code analysis"""
        import re
        
        # Try to extract JavaDoc comment
        javadoc_pattern = r'/\*\*\s*(.*?)\s*\*/'
        javadoc_match = re.search(javadoc_pattern, content, re.DOTALL)
        if javadoc_match:
            javadoc = javadoc_match.group(1).strip()
            # Clean up JavaDoc markers
            javadoc = re.sub(r'\s*\*\s*', ' ', javadoc)
            javadoc = re.sub(r'@\w+.*', '', javadoc)
            if len(javadoc) > 30:
                return javadoc[:200].strip()
        
        # Analyze annotations for context
        annotation_to_purpose = {
            '@Controller': 'Controller',
            '@RestController': 'REST controller',
            '@Service': 'Service',
            '@Repository': 'Repository',
            '@Component': 'Component',
            '@Entity': 'Entity',
            '@Configuration': 'Configuration'
        }
        
        purpose = None
        for annotation, purpose_text in annotation_to_purpose.items():
            if annotation in content:
                purpose = purpose_text
                break
        
        # Generate description based on category and annotations
        category_mapping = {
            'controllers': 'Controller',
            'services': 'Service',
            'repositories': 'Repository',
            'entities': 'Entity',
            'configs': 'Configuration'
        }
        
        type_text = purpose or category_mapping.get(category, 'Class')
        
        # Try to infer purpose from class name
        if class_name.endswith('Controller'):
            return f"REST controller for handling HTTP requests related to {class_name.replace('Controller', '').lower()} operations"
        elif class_name.endswith('Service'):
            return f"Service class providing business logic for {class_name.replace('Service', '').lower()} management"
        elif class_name.endswith('Repository') or class_name.endswith('DAO'):
            return f"Data access repository for {class_name.replace('Repository', '').replace('DAO', '').lower()} entities"
        elif class_name.endswith('Entity') or class_name.endswith('Model'):
            return f"JPA entity representing {class_name.replace('Entity', '').replace('Model', '').lower()} data"
        else:
            return f"{type_text} class for {class_name.lower()} operations"
    
    def _generate_method_description(self, method_name: str, signature: str, method_body: str) -> str:
        """Generate method description from name and signature"""
        # Common patterns
        if method_name.startswith('get'):
            field = method_name[3:] if len(method_name) > 3 else "property"
            return f"Retrieves the {field.lower()} value"
        elif method_name.startswith('set'):
            field = method_name[3:] if len(method_name) > 3 else "property"
            return f"Sets the {field.lower()} value"
        elif method_name.startswith('is'):
            field = method_name[2:] if len(method_name) > 2 else "property"
            return f"Checks if {field.lower()} is true"
        elif method_name.startswith('has'):
            field = method_name[3:] if len(method_name) > 3 else "property"
            return f"Checks if {field.lower()} exists"
        elif method_name.startswith('create'):
            return f"Creates a new {method_name[6:].lower() if len(method_name) > 6 else 'entity'}"
        elif method_name.startswith('update'):
            return f"Updates an existing {method_name[6:].lower() if len(method_name) > 6 else 'entity'}"
        elif method_name.startswith('delete') or method_name.startswith('remove'):
            return f"Deletes an existing {method_name[6:].lower() if len(method_name) > 6 else 'entity'}"
        elif method_name.startswith('find') or method_name.startswith('search'):
            return f"Finds {method_name[4:].lower() if len(method_name) > 4 else 'entities'} matching the criteria"
        elif 'save' in method_name.lower():
            return f"Saves the {method_name.replace('save', '').lower() if 'save' in method_name else 'entity'}"
        else:
            # Generic description based on return type
            if 'List' in signature or '[]' in signature:
                return f"Retrieves a list of {method_name.lower().replace('get', '').replace('find', '')}"
            elif 'boolean' in signature.lower() or 'Boolean' in signature:
                return f"Checks if {method_name.lower()}"
            else:
                return f"Performs {method_name.lower()} operation"
    
    def _estimate_complexity_from_code(self, method_code: str) -> str:
        """Estimate complexity from method code analysis"""
        import re
        
        if not method_code or len(method_code.strip()) < 10:
            return "Low"  # Empty or very short methods
        
        # Count complexity indicators
        loop_keywords = ['for', 'while', 'do']
        loop_count = sum(len(re.findall(rf'\b{kw}\s*\(', method_code)) for kw in loop_keywords)
        
        conditional_keywords = ['if', 'switch', 'catch']
        conditional_count = sum(len(re.findall(rf'\b{kw}\s*\(', method_code)) for kw in conditional_keywords)
        
        # Count method calls (excluding loops and conditionals)
        call_count = len(re.findall(r'\w+\s*\(', method_code))
        call_count = max(0, call_count - loop_count - conditional_count)
        
        # Count nested structures
        nested_loops = len(re.findall(r'\b(for|while)\s*\([^)]*\)\s*\{[^}]*\b(for|while)\s*\(', method_code))
        
        # Check for recursion
        has_recursion = bool(re.search(r'\breturn\s+\w+\s*\(', method_code))
        
        # Check for external service calls (patterns indicating external dependencies)
        external_call_patterns = [
            r'\.get\(', r'\.post\(', r'\.put\(', r'\.delete\(',  # HTTP calls
            r'\.save\(', r'\.find\(', r'\.delete\(', r'\.query\(',  # Database calls
            r'\.send\(', r'\.publish\(', r'\.call\(',  # Message/remote calls
        ]
        external_call_count = sum(len(re.findall(pattern, method_code)) for pattern in external_call_patterns)
        
        # Heuristic rules
        if nested_loops > 0 or has_recursion:
            return "High"
        elif loop_count == 0 and conditional_count <= 2 and call_count <= 3 and external_call_count <= 1:
            return "Low"
        elif loop_count <= 1 and conditional_count <= 4 and call_count <= 6 and external_call_count <= 2:
            return "Medium"
        elif external_call_count > 2 or call_count > 8:
            return "High"
        else:
            return "Medium"
    
    def _build_extraction_prompt(self, content: str, class_name: str, category: str) -> str:
        """Build enhanced prompt for metadata extraction with explicit examples"""
        
        prompt = f"""Analyze this Java {category} class and extract comprehensive metadata.

Class name: {class_name}
Category: {category}

Java code:
```java
{content[:10000]}  # Limit to first 10k chars
```

IMPORTANT: You must provide high-quality, specific descriptions. Do NOT use placeholder text like "Auto-extracted {{ClassName}}" or "{{methodName}} method". Provide actual meaningful descriptions.

Extract the following information:

1. CLASS DESCRIPTION:
   - Write a clear, specific description (at least 30 characters) of what this class does and its purpose
   - Explain its role in the application and main responsibilities
   - Example of GOOD description: "Service class that manages customer data, including CRUD operations, validation, and business rule enforcement"
   - Example of BAD description: "Auto-extracted CustomerService" or "CustomerService class"

2. PUBLIC METHODS:
   For each public method, provide:
   - Full method signature (including all parameters and return type)
   - Clear, specific description (at least 5 characters) explaining what the method does
   - Complexity estimate (Low/Medium/High) based on:
     * Low: Simple getters/setters, basic CRUD operations, single-line return statements
     * Medium: Business logic with multiple steps, data transformations, simple conditionals, single loops
     * High: Complex algorithms, nested loops, multiple external calls, heavy processing, recursion
   
   Example of GOOD method entry:
   {{
     "name": "getCustomerById",
     "signature": "public Customer getCustomerById(int id)",
     "description": "Retrieves a customer entity from the database by ID, returns null if not found",
     "complexity": "Low"
   }}
   
   Example of BAD method entry:
   {{
     "name": "getCustomerById",
     "signature": "getCustomerById()",
     "description": "getCustomerById method",
     "complexity": "Unknown"
   }}

3. INTERNAL DEPENDENCIES:
   - List all other classes this code references (excluding Java standard library)
   - Include classes from constructor injection, field declarations, method parameters, return types, and generics
   - Filter out java.* and javax.* packages
   - Example: ["CustomerRepository", "Customer", "Address", "OrderService"]

VALIDATION CHECKLIST (all must pass):
✓ Description is at least 30 characters and not a placeholder
   ✓ All methods have specific descriptions (not just "{{methodName}} method")
✓ All methods have complexity set to Low, Medium, or High (not "Unknown")
✓ Dependencies list includes all referenced classes

Return the information as a JSON object matching the provided schema."""
        
        return prompt
    
    def _build_retry_prompt(self, content: str, class_name: str, category: str, quality_issues: List[str], retry_count: int) -> str:
        """Build retry prompt with specific issues to fix"""
        
        issues_text = "\n".join([f"- {issue}" for issue in quality_issues])
        
        if retry_count == 1:
            # First retry: Add specific issues
            prompt = f"""Analyze this Java {category} class and extract comprehensive metadata.

Class name: {class_name}
Category: {category}

Java code:
```java
{content[:10000]}  # Limit to first 10k chars
```

CRITICAL: The previous extraction had quality issues that MUST be fixed:
{issues_text}

You MUST address all of these issues:
1. Provide a detailed, specific description (at least 30 characters) - NOT a placeholder like "Auto-extracted {{class_name}}"
2. For each method, provide a meaningful description explaining what it does - NOT just "{{methodName}} method"
3. Set complexity to Low, Medium, or High for ALL methods - NOT "Unknown"
4. Extract all dependencies from imports, fields, constructors, and method parameters

Focus on providing actual content, not placeholders. Analyze the code carefully and describe what it actually does."""
        elif retry_count == 2:
            # Second retry: Use stronger language with examples
            prompt = f"""Extract metadata from this Java class. The previous attempts failed quality checks.

Class: {class_name} ({category})

Code:
```java
{content[:10000]}
```

SPECIFIC ISSUES TO FIX:
{issues_text}

EXAMPLES OF WHAT YOU MUST DO:

Good description example:
"REST controller that handles HTTP requests for film operations including GET /films, POST /films, and PUT /films/:id endpoints with proper error handling"

Bad description (DO NOT USE):
"Auto-extracted FilmController"

Good method example:
{{
  "name": "findFilmsByTitle",
  "signature": "public List<Film> findFilmsByTitle(String title)",
  "description": "Searches for films matching the given title using case-insensitive partial matching",
  "complexity": "Medium"
}}

Bad method (DO NOT USE):
{{
  "name": "findFilmsByTitle",
  "description": "findFilmsByTitle method",
  "complexity": "Unknown"
}}

You MUST provide real, specific descriptions based on the actual code."""
        else:
            # Third retry: Simplified, very explicit
            prompt = f"""Extract metadata from {class_name}. Provide specific, detailed information.

Code:
```java
{content[:10000]}
```

Required:
1. Description: Write 2-3 sentences explaining what this class does. Minimum 30 characters.
2. Methods: For each method, write what it does. Minimum 5 characters per description.
3. Complexity: Set each method to Low, Medium, or High only. No "Unknown".
4. Dependencies: List all referenced classes.

Do not use placeholder text. Write actual descriptions based on the code."""
        
        return prompt
    
    def _map_category_to_type(self, category: str) -> str:
        """Map file category to module type"""
        mapping = {
            'controllers': 'Controller',
            'services': 'Service',
            'repositories': 'Repository',
            'entities': 'Entity',
            'configs': 'Config',
            'other': 'Other'
        }
        return mapping.get(category, 'Other')
    
    # ========== Quality Validation System ==========
    
    def _validate_metadata_quality(self, metadata: Dict, file_info: Dict) -> Dict:
        """Validate metadata quality and return issues"""
        issues = []
        validated = True
        
        # Check description
        if not self._check_description_quality(metadata.get('description', '')):
            issues.append("Description is too short or uses placeholder text")
            validated = False
        
        # Check methods
        method_issues = self._check_methods_quality(metadata.get('methods', []))
        if method_issues:
            issues.extend(method_issues)
            validated = False
        
        # Check dependencies (warn but don't fail if truly independent)
        deps = metadata.get('dependencies', [])
        if not deps and self._should_have_dependencies(file_info, metadata):
            issues.append("No dependencies found (may be incomplete)")
        
        # Calculate quality score
        score = self._calculate_quality_score(metadata)
        
        return {
            "validated": validated,
            "issues": issues,
            "score": score
        }
    
    def _check_description_quality(self, description: str) -> bool:
        """Validate description isn't placeholder"""
        if not description or len(description.strip()) < 30:
            return False
        
        # Check for placeholder patterns
        placeholder_patterns = [
            "auto-extracted",
            "auto extracted",
            f"{description.split()[0]} class" if description else "",
            "extracted",
            "unknown"
        ]
        
        description_lower = description.lower().strip()
        for pattern in placeholder_patterns:
            if pattern and pattern.lower() in description_lower:
                # Check if it's just the placeholder (not part of a longer description)
                if len(description_lower) < 50 and pattern.lower() in description_lower:
                    return False
        
        return True
    
    def _check_complexity_quality(self, complexity: str) -> bool:
        """Validate complexity isn't 'Unknown'"""
        if not complexity:
            return False
        complexity_upper = complexity.strip().upper()
        return complexity_upper in ["LOW", "MEDIUM", "HIGH"]
    
    def _check_methods_quality(self, methods: List[Dict]) -> List[str]:
        """Validate method descriptions and complexity"""
        issues = []
        
        if not methods:
            return issues  # Empty methods list is acceptable
        
        for idx, method in enumerate(methods):
            method_name = method.get('name', f'method_{idx}')
            
            # Check method description
            method_desc = method.get('description', '').strip()
            if not method_desc or len(method_desc) < 5:
                issues.append(f"Method '{method_name}' has empty or too short description")
            elif method_desc.lower() == f"{method_name} method" or method_desc.lower() == f"{method_name}":
                issues.append(f"Method '{method_name}' has placeholder description")
            
            # Check complexity
            complexity = method.get('complexity', '')
            if not self._check_complexity_quality(complexity):
                issues.append(f"Method '{method_name}' has invalid or missing complexity")
        
        return issues
    
    def _should_have_dependencies(self, file_info: Dict, metadata: Dict) -> bool:
        """Determine if this class should have dependencies"""
        # Entities and simple config classes might not have dependencies
        category = file_info.get('category', '')
        module_type = metadata.get('type', '')
        
        # Entities might not have many dependencies
        if module_type == 'Entity':
            return False
        
        # Controllers, Services, Repositories should have dependencies
        if module_type in ['Controller', 'Service', 'Repository']:
            return True
        
        # If class has methods, it likely has dependencies
        if metadata.get('methods'):
            return True
        
        return False
    
    def _calculate_quality_score(self, metadata: Dict) -> float:
        """Calculate quality score (0.0 to 1.0)"""
        score = 0.0
        max_score = 4.0
        
        # Description quality (1.0 points)
        if self._check_description_quality(metadata.get('description', '')):
            score += 1.0
        
        # Methods quality (1.0 points)
        methods = metadata.get('methods', [])
        if methods:
            method_issues = self._check_methods_quality(methods)
            methods_score = max(0.0, 1.0 - (len(method_issues) / max(len(methods), 1)))
            score += methods_score
        else:
            # Empty methods list gets 0.5 (might be valid for simple classes)
            score += 0.5
        
        # Dependencies (0.5 points)
        deps = metadata.get('dependencies', [])
        if deps:
            score += 0.5
        
        # Complexity coverage (1.5 points)
        methods = metadata.get('methods', [])
        if methods:
            valid_complexities = sum(1 for m in methods if self._check_complexity_quality(m.get('complexity', '')))
            if methods:
                score += 1.5 * (valid_complexities / len(methods))
        else:
            score += 0.75  # Partial credit if no methods
        
        return score / max_score
    
    # ========== Comprehensive Dependency Extraction ==========
    
    def _extract_dependencies_comprehensive(self, content: str) -> List[str]:
        """Extract dependencies from multiple sources in Java code"""
        import re
        dependencies = set()
        
        # 1. Parse import statements
        import_pattern = r'^import\s+(?:static\s+)?([\w.]+)\.(\w+);'
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            package = match.group(1)
            class_name = match.group(2)
            
            # Filter Java standard library
            if not package.startswith('java.') and not package.startswith('javax.'):
                dependencies.add(class_name)
        
        # 2. Parse constructor injection: @Autowired private Type field
        autowired_pattern = r'@Autowired\s+(?:private|protected|public)?\s+\w+\s+(\w+)\s+'
        for match in re.finditer(autowired_pattern, content):
            dep_class = match.group(1)
            if dep_class and not dep_class[0].islower():  # Class names start with uppercase
                dependencies.add(dep_class)
        
        # 3. Parse field declarations: private Type field;
        field_pattern = r'(?:private|protected|public)\s+(?:static\s+)?(?:final\s+)?(\w+)\s+\w+\s*[=;]'
        for match in re.finditer(field_pattern, content):
            type_name = match.group(1)
            # Filter primitives and common types
            if type_name not in ['int', 'long', 'float', 'double', 'boolean', 'char', 'byte', 'short',
                               'String', 'void', 'Object', 'List', 'Map', 'Set', 'Collection']:
                if not type_name[0].islower():  # Class names start with uppercase
                    dependencies.add(type_name)
        
        # 4. Parse method parameter types
        method_param_pattern = r'\(([^)]*)\)'
        for match in re.finditer(method_param_pattern, content):
            params = match.group(1)
            if params:
                # Extract types from parameters
                param_types = re.findall(r'(\w+)\s+\w+', params)
                for param_type in param_types:
                    if param_type not in ['int', 'long', 'float', 'double', 'boolean', 'char', 'byte', 'short',
                                         'String', 'void']:
                        if not param_type[0].islower():
                            dependencies.add(param_type)
        
        # 5. Extract generic type arguments: List<EntityType>, Optional<EntityType>, etc.
        generic_pattern = r'<(\w+)>'
        for match in re.finditer(generic_pattern, content):
            generic_type = match.group(1)
            if generic_type not in ['String', 'Integer', 'Long', 'Double', 'Boolean', 'Object']:
                if not generic_type[0].islower():
                    dependencies.add(generic_type)
        
        # 6. Extract from annotations: @OneToMany(mappedBy="entity"), @ManyToOne, etc.
        annotation_pattern = r'@(?:OneToMany|ManyToOne|OneToOne|ManyToMany|JoinColumn|Entity)\s*\([^)]*mappedBy\s*=\s*"?(\w+)"?'
        for match in re.finditer(annotation_pattern, content):
            entity_name = match.group(1)
            if entity_name and not entity_name[0].islower():
                dependencies.add(entity_name)
        
        # 7. Extract from return types in method signatures
        return_type_pattern = r'(?:public|private|protected)\s+(?:static\s+)?(\w+)\s+\w+\s*\('
        for match in re.finditer(return_type_pattern, content):
            return_type = match.group(1)
            if return_type not in ['void', 'int', 'long', 'float', 'double', 'boolean', 'char', 'byte', 'short',
                                 'String']:
                if not return_type[0].islower():
                    dependencies.add(return_type)
        
        # Filter out common Java types that aren't dependencies
        java_common = {
            'String', 'Object', 'Integer', 'Long', 'Double', 'Boolean', 'Character',
            'Byte', 'Short', 'Float', 'BigDecimal', 'BigInteger', 'Date', 'Calendar',
            'List', 'ArrayList', 'LinkedList', 'Set', 'HashSet', 'Map', 'HashMap',
            'Optional', 'Stream', 'Collection', 'Iterable', 'Iterator'
        }
        dependencies = {d for d in dependencies if d not in java_common}
        
        return sorted(list(dependencies))

