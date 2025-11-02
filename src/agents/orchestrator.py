# src/agents/orchestrator.py

import os
import json
import uuid
import logging
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Any
from gitingest import ingest

from ..analyzers.repository_analyzer import RepositoryAnalyzer
from ..clients.llm_client_factory import create_llm_client_from_config
from ..extractors.metadata_extractor import MetadataExtractor
from ..mappers.dependency_mapper import DependencyMapper

logger = logging.getLogger(__name__)

from ..converters.model_converter import ModelConverter
from ..converters.repository_converter import RepositoryConverter
from ..converters.service_converter import ServiceConverter
from ..converters.controller_converter import ControllerConverter
from ..migrators.config_migrator import ConfigMigrator
from ..generators.project_generator import ProjectGenerator
from ..validators.conversion_validator import ConversionValidator

class ConversionState(TypedDict, total=False):
    github_url: str
    # LLM configuration - new multi-provider support
    llm_provider: Optional[str]  # "gemini", "glm", "openrouter", "openai"
    llm_api_token: Optional[str]  # Generic API token (replaces gemini_api_token)
    llm_base_url: Optional[str]  # Custom base URL for GLM/OpenAI
    llm_profile_name: Optional[str]  # Profile name from config file
    llm_config_path: Optional[str]  # Path to config file
    # Legacy support for backward compatibility
    gemini_api_token: Optional[str]  # Deprecated, use llm_api_token with llm_provider="gemini"
    target_framework: str
    orm_choice: str
    model: str  # Model name (format depends on provider)
    repo_path: Optional[str]
    codebase_text_file: Optional[str]  # Path to consolidated codebase text file from gitingest
    file_map: Optional[dict]
    metadata: Optional[dict]
    converted_components: dict
    output_path: Optional[str]
    validation_result: Optional[dict]
    errors: list
    java_dependencies: Optional[list]
    build_system: Optional[str]
    node_dependencies: Optional[dict]
    node_config: Optional[dict]
    _analyzer: Optional[Any]  # For storing RepositoryAnalyzer instance

# Global execution status tracker
_execution_status = {
    "current_phase": None,
    "current_file": None,
    "progress_percentage": 0,
    "files_processed": 0,
    "files_total": 0,
    "safety_blocks": [],
    "errors": []
}

def get_execution_status():
    """Get current execution status"""
    return _execution_status.copy()

def create_conversion_workflow():
    """Create LangGraph workflow"""
    
    workflow = StateGraph(ConversionState)
    
    # Define nodes
    workflow.add_node("clone_repo", clone_repository_node)
    workflow.add_node("ingest_codebase", ingest_codebase_node)
    workflow.add_node("analyze_structure", analyze_structure_node)
    workflow.add_node("extract_metadata", extract_metadata_node)
    workflow.add_node("map_dependencies", map_dependencies_node)
    workflow.add_node("convert_controllers", convert_controllers_node)
    workflow.add_node("convert_services", convert_services_node)
    workflow.add_node("convert_repositories", convert_repositories_node)
    workflow.add_node("convert_models", convert_models_node)
    workflow.add_node("generate_config", generate_config_node)
    workflow.add_node("generate_project", generate_project_node)
    workflow.add_node("validate", validate_node)
    
    # Define edges
    workflow.set_entry_point("clone_repo")
    workflow.add_edge("clone_repo", "ingest_codebase")
    workflow.add_edge("ingest_codebase", "analyze_structure")
    workflow.add_edge("analyze_structure", "extract_metadata")
    workflow.add_edge("extract_metadata", "map_dependencies")
    workflow.add_edge("map_dependencies", "convert_models")
    workflow.add_edge("convert_models", "convert_repositories")
    workflow.add_edge("convert_repositories", "convert_services")
    workflow.add_edge("convert_services", "convert_controllers")
    workflow.add_edge("convert_controllers", "generate_config")
    workflow.add_edge("generate_config", "generate_project")
    workflow.add_edge("generate_project", "validate")
    workflow.add_edge("validate", END)
    
    return workflow.compile()

## Helper functions

def _create_llm_client_from_state(state: ConversionState):
    """
    Create LLM client from conversion state
    
    Args:
        state: Conversion state with LLM configuration
        
    Returns:
        LLM client instance
    """
    model = state.get("model", "")
    provider = state.get("llm_provider")
    api_token = state.get("llm_api_token")
    base_url = state.get("llm_base_url")
    profile_name = state.get("llm_profile_name")
    config_path = state.get("llm_config_path")
    
    # If using profile, model can be None (will use profile's model)
    if profile_name:
        # Profile takes precedence - model override is optional
        return create_llm_client_from_config(
            provider=None,  # Will be determined from profile
            api_token=None,  # Will be determined from profile
            model=model if model and model.strip() else None,  # Optional override
            base_url=None,  # Will be determined from profile
            profile_name=profile_name,
            config_path=config_path
        )
    
    # Using direct provider configuration
    if not model or not model.strip():
        raise ValueError("Model parameter is required when not using profile")
    
    # Legacy support: convert gemini_api_token if present
    if not api_token and state.get("gemini_api_token"):
        provider = provider or "gemini"
        api_token = state["gemini_api_token"]
    
    # Default to gemini if no provider specified (backward compatibility)
    if not provider:
        provider = "gemini"
    
    return create_llm_client_from_config(
        provider=provider,
        api_token=api_token,
        model=model,
        base_url=base_url,
        profile_name=None,
        config_path=config_path
    )

def _extract_code_from_consolidated_file(codebase_text_file: str, file_path: str, class_name: str = None) -> str:
    """
    Extract Java code for a specific file from the consolidated codebase text file
    
    Args:
        codebase_text_file: Path to consolidated codebase text file
        file_path: Relative file path to locate in consolidated file
        class_name: Optional class name to help locate the code
        
    Returns:
        Extracted Java code string, or empty string if not found
    """
    if not codebase_text_file or not os.path.exists(codebase_text_file):
        return ""
    
    try:
        with open(codebase_text_file, 'r', encoding='utf-8') as f:
            codebase_content = f.read()
        
        # Look for file path marker (gitingest may include file paths)
        file_marker = file_path.replace('\\', '/')
        marker_index = -1
        
        if file_marker and file_marker in codebase_content:
            marker_index = codebase_content.find(file_marker)
        
        # If file path not found, try class name
        if marker_index < 0 and class_name:
            class_marker = f"class {class_name}"
            if class_marker in codebase_content:
                marker_index = codebase_content.find(class_marker)
        
        if marker_index >= 0:
            # Extract code section (try to find boundaries)
            # Look backwards for previous file marker or section separator
            start = marker_index
            for i in range(max(0, marker_index - 5000), marker_index):
                if codebase_content[i:i+10] == "=== CODEBASE" or codebase_content[i:i+20] == "=== FULL CODEBASE":
                    start = i
                    break
                # Check for file path markers
                if i > 0 and codebase_content[i-1] == '\n' and codebase_content[i:i+1].isupper():
                    # Might be a new file section
                    potential_start = codebase_content.rfind('\n\n', max(0, i-100), i)
                    if potential_start > 0:
                        start = potential_start + 2
                        break
            
            # Look forward for next file marker or reasonable end
            end = min(len(codebase_content), marker_index + 50000)
            next_file_marker = codebase_content.find('\n\n', marker_index + 100, end)
            if next_file_marker > marker_index:
                # Check if this looks like a new file (has path-like content)
                section = codebase_content[marker_index:next_file_marker+100]
                if any(x in section for x in ['.java', 'package ', 'import ', 'class ']):
                    end = next_file_marker + 100
            else:
                # Try to find class end (simple heuristic)
                closing_braces = codebase_content.count('}', marker_index, end) - codebase_content.count('{', marker_index, end)
                if closing_braces > 0:
                    last_brace = codebase_content.rfind('}', marker_index, end)
                    if last_brace > marker_index:
                        end = last_brace + 1
            
            extracted = codebase_content[start:end]
            # Try to clean up - find actual Java code start
            java_start = -1
            for marker in ['package ', 'import ', 'class ', 'public class ', 'interface ']:
                idx = extracted.find(marker)
                if idx >= 0 and (java_start < 0 or idx < java_start):
                    java_start = idx
            if java_start > 0 and java_start < 500:
                extracted = extracted[java_start:]
            
            return extracted
        
        # If not found by markers, return empty - will fallback to reading individual file
        return ""
    except Exception as e:
        logger.warning(f"Failed to extract code from consolidated file for {file_path}: {e}")
        return ""

## Node implementations

def clone_repository_node(state: ConversionState) -> ConversionState:
    """Clone GitHub repository"""
    try:
        analyzer = RepositoryAnalyzer(state["github_url"])
        repo_path = analyzer.clone_repository()
        
        # Store analyzer in state for later use
        return {
            **state,
            "repo_path": repo_path,
            "_analyzer": analyzer  # Store for cleanup
        }
    except Exception as e:
        logger.error(f"Failed to clone repository: {e}")
        return {
            **state,
            "errors": state.get("errors", []) + [f"Clone failed: {str(e)}"]
        }

def ingest_codebase_node(state: ConversionState) -> ConversionState:
    """Convert cloned repository into single consolidated text file using gitingest"""
    try:
        repo_path = state.get("repo_path")
        if not repo_path:
            raise ValueError("Repository not cloned. repo_path not found in state.")
        
        # Update execution status
        _execution_status["current_phase"] = "Ingesting codebase with gitingest"
        _execution_status["progress_percentage"] = 10
        
        logger.info(f"Ingesting codebase from {repo_path} using gitingest...")
        
        # Use gitingest to convert codebase into single text representation
        summary, tree, content = ingest(repo_path)
        
        # Create output directory if it doesn't exist
        output_dir = state.get("output_path")
        if not output_dir:
            output_dir = f"/tmp/conversion-output-{uuid.uuid4()}"
            os.makedirs(output_dir, exist_ok=True)
        
        # Save consolidated codebase to text file
        codebase_file_path = os.path.join(output_dir, "codebase.txt")
        with open(codebase_file_path, 'w', encoding='utf-8') as f:
            # Write summary, tree structure, and full content
            f.write("=== CODEBASE SUMMARY ===\n")
            f.write(f"{summary}\n\n")
            f.write("=== DIRECTORY TREE ===\n")
            f.write(f"{tree}\n\n")
            f.write("=== FULL CODEBASE CONTENT ===\n")
            f.write(content)
        
        logger.info(f"Codebase ingested and saved to {codebase_file_path}")
        logger.info(f"Consolidated file size: {len(content)} characters")
        
        return {
            **state,
            "codebase_text_file": codebase_file_path,
            "output_path": output_dir
        }
    except Exception as e:
        logger.error(f"Failed to ingest codebase: {e}")
        return {
            **state,
            "errors": state.get("errors", []) + [f"Codebase ingestion failed: {str(e)}"]
        }

def analyze_structure_node(state: ConversionState) -> ConversionState:
    """Discover and categorize files"""
    try:
        # Reuse analyzer from state if available
        analyzer = state.get("_analyzer")
        if not analyzer or analyzer.repo_path != state["repo_path"]:
            analyzer = RepositoryAnalyzer(state["github_url"])
            analyzer.repo_path = state["repo_path"]
            if not analyzer.repo_path:
                # If repo_path not set, clone again
                analyzer.clone_repository()
        
        file_map = analyzer.discover_files()
        build_system = analyzer.detect_build_system()
        dependencies = analyzer.parse_dependencies()
        
        return {
            **state,
            "file_map": file_map,
            "build_system": build_system,
            "java_dependencies": dependencies,
            "_analyzer": analyzer
        }
    except Exception as e:
        logger.error(f"Failed to analyze structure: {e}")
        return {
            **state,
            "errors": state.get("errors", []) + [f"Structure analysis failed: {str(e)}"]
        }

def extract_metadata_node(state: ConversionState) -> ConversionState:
    """Extract comprehensive project metadata"""
    try:
        if not state.get("file_map"):
            raise ValueError("file_map not found in state")
        
        # Update execution status
        _execution_status["current_phase"] = "Extracting Metadata"
        _execution_status["progress_percentage"] = 30
        
        # Count total files
        total_files = sum(len(files) for files in state["file_map"].values())
        _execution_status["files_total"] = total_files
        _execution_status["files_processed"] = 0
        
        model = state.get("model", "")
        if not model or not model.strip():
            raise ValueError(
                "Model parameter is required. Please specify --model when running conversion."
            )
        
        # Get LLM configuration from state (support both new and legacy format)
        provider = state.get("llm_provider")
        api_token = state.get("llm_api_token")
        base_url = state.get("llm_base_url")
        profile_name = state.get("llm_profile_name")
        config_path = state.get("llm_config_path")
        
        # Legacy support: convert gemini_api_token if present
        if not api_token and state.get("gemini_api_token"):
            provider = provider or "gemini"
            api_token = state["gemini_api_token"]
        
        # Default to gemini if no provider specified (backward compatibility)
        if not provider:
            provider = "gemini"
        
        extractor = MetadataExtractor(
            provider=provider,
            api_token=api_token,
            model=model,
            base_url=base_url,
            profile_name=profile_name,
            config_path=config_path,
            # Legacy support
            gemini_api_token=state.get("gemini_api_token") if not api_token else None
        )
        
        # Use consolidated codebase file if available, otherwise fallback to individual files
        codebase_text_file = state.get("codebase_text_file")
        if codebase_text_file and os.path.exists(codebase_text_file):
            logger.info(f"Using consolidated codebase file for metadata extraction: {codebase_text_file}")
            metadata = extractor.analyze_codebase_from_file(codebase_text_file, state["file_map"])
        else:
            logger.info("Consolidated codebase file not found, using individual file analysis (fallback)")
            metadata = extractor.analyze_codebase(state["file_map"])
        
        # Save metadata JSON
        output_dir = state.get("output_path")
        if not output_dir:
            output_dir = f"/tmp/conversion-output-{uuid.uuid4()}"
        
        # Always ensure output directory exists, even if it was already set in state
        os.makedirs(output_dir, exist_ok=True)
        
        metadata_path = os.path.join(output_dir, "project-metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata extracted and saved to {metadata_path}")
        
        return {
            **state,
            "metadata": metadata,
            "output_path": output_dir
        }
    except Exception as e:
        logger.error(f"Failed to extract metadata: {e}")
        # Return empty metadata dict to prevent cascading failures in downstream nodes
        empty_metadata = {"projectOverview": "", "modules": []}
        
        # Try to save empty metadata file if output directory is available
        output_dir = state.get("output_path")
        if output_dir:
            try:
                os.makedirs(output_dir, exist_ok=True)
                metadata_path = os.path.join(output_dir, "project-metadata.json")
                with open(metadata_path, "w") as f:
                    json.dump(empty_metadata, f, indent=2)
                logger.info(f"Saved empty metadata file to {metadata_path}")
            except Exception as save_error:
                logger.warning(f"Failed to save empty metadata file: {save_error}")
        
        return {
            **state,
            "metadata": empty_metadata,
            "errors": state.get("errors", []) + [f"Metadata extraction failed: {str(e)}"]
        }

def map_dependencies_node(state: ConversionState) -> ConversionState:
    """Map Java dependencies to Node.js"""
    try:
        mapper = DependencyMapper()
        java_deps = state.get("java_dependencies", [])
        node_deps = mapper.map_dependencies(java_deps)
        
        logger.info(f"Mapped {len(node_deps)} Node.js dependencies")
        
        return {
            **state,
            "node_dependencies": node_deps
        }
    except Exception as e:
        logger.error(f"Failed to map dependencies: {e}")
        return {
            **state,
            "errors": state.get("errors", []) + [f"Dependency mapping failed: {str(e)}"],
            "node_dependencies": {}
        }

def convert_models_node(state: ConversionState) -> ConversionState:
    """Convert JPA entities to ORM models"""
    try:
        # Check for metadata - skip gracefully if missing instead of failing
        metadata = state.get("metadata")
        if not metadata or not metadata.get("modules"):
            logger.warning("Metadata not found or has no modules, skipping model conversion")
            return {
                **state,
                "errors": state.get("errors", []) + [f"Model conversion skipped: Metadata not found"],
                "converted_components": {
                    **state.get("converted_components", {}),
                    "models": []
                }
            }
        
        model = state.get("model", "")
        if not model or not model.strip():
            raise ValueError(
                "Model parameter is required. Please specify --model when running conversion."
            )
        
        # Create LLM client from state
        llm_client = _create_llm_client_from_state(state)
        
        converter = ModelConverter(
            orm_choice="sequelize",
            llm_client=llm_client
        )
        
        converted_models = []
        entities = [m for m in state["metadata"]["modules"] if m.get("type") == "Entity"]
        
        logger.info(f"Converting {len(entities)} entities to models...")
        
        for entity in entities:
            try:
                # Get Java code from consolidated file or individual file
                java_code = ""
                file_path = entity.get("filePath")
                class_name = entity.get("name", "")
                
                # Try consolidated file first
                codebase_text_file = state.get("codebase_text_file")
                if codebase_text_file:
                    java_code = _extract_code_from_consolidated_file(codebase_text_file, file_path, class_name)
                
                # Fallback to reading individual file if not found in consolidated file
                if not java_code and file_path and state.get("repo_path"):
                    full_path = os.path.join(state["repo_path"], file_path)
                    if os.path.exists(full_path):
                        with open(full_path, 'r', encoding='utf-8') as f:
                            java_code = f.read()
                
                converted = converter.convert_entity(entity, java_code)
                converted_models.append(converted)
            except Exception as e:
                logger.warning(f"Failed to convert entity {entity.get('name', 'unknown')}: {e}")
                converted_models.append(converter._create_stub_model(entity))
        
        logger.info(f"Converted {len(converted_models)} models")
        
        return {
            **state,
            "converted_components": {
                **state.get("converted_components", {}),
                "models": converted_models
            }
        }
    except Exception as e:
        logger.error(f"Failed to convert models: {e}")
        return {
            **state,
            "errors": state.get("errors", []) + [f"Model conversion failed: {str(e)}"],
            "converted_components": {
                **state.get("converted_components", {}),
                "models": []
            }
        }

def convert_repositories_node(state: ConversionState) -> ConversionState:
    """Convert repositories/DAOs"""
    try:
        # Check for metadata - skip gracefully if missing instead of failing
        metadata = state.get("metadata")
        if not metadata or not metadata.get("modules"):
            logger.warning("Metadata not found or has no modules, skipping repository conversion")
            return {
                **state,
                "errors": state.get("errors", []) + [f"Repository conversion skipped: Metadata not found"],
                "converted_components": {
                    **state.get("converted_components", {}),
                    "repositories": []
                }
            }
        
        model = state.get("model", "")
        if not model or not model.strip():
            raise ValueError(
                "Model parameter is required. Please specify --model when running conversion."
            )
        
        # Create LLM client from state
        llm_client = _create_llm_client_from_state(state)
        
        converter = RepositoryConverter(
            orm_choice="sequelize",
            llm_client=llm_client
        )
        
        converted_repos = []
        repositories = [m for m in state["metadata"]["modules"] if m.get("type") == "Repository"]
        
        logger.info(f"Converting {len(repositories)} repositories...")
        
        for repo in repositories:
            try:
                # Find corresponding entity
                repo_name = repo.get("name", "")
                entity_name = repo_name.replace("Repository", "")
                entity = None
                
                for m in state["metadata"]["modules"]:
                    if m.get("name") == entity_name and m.get("type") == "Entity":
                        entity = m
                        break
                
                # Get Java code from consolidated file or individual file
                java_code = ""
                file_path = repo.get("filePath")
                class_name = repo.get("name", "")
                
                # Try consolidated file first
                codebase_text_file = state.get("codebase_text_file")
                if codebase_text_file:
                    java_code = _extract_code_from_consolidated_file(codebase_text_file, file_path, class_name)
                
                # Fallback to reading individual file if not found in consolidated file
                if not java_code and file_path and state.get("repo_path"):
                    full_path = os.path.join(state["repo_path"], file_path)
                    if os.path.exists(full_path):
                        with open(full_path, 'r', encoding='utf-8') as f:
                            java_code = f.read()
                
                converted = converter.convert_repository(repo, entity)
                converted_repos.append(converted)
            except Exception as e:
                logger.warning(f"Failed to convert repository {repo.get('name', 'unknown')}: {e}")
                converted_repos.append(converter._create_stub_repository(repo))
        
        logger.info(f"Converted {len(converted_repos)} repositories")
        
        return {
            **state,
            "converted_components": {
                **state.get("converted_components", {}),
                "repositories": converted_repos
            }
        }
    except Exception as e:
        logger.error(f"Failed to convert repositories: {e}")
        return {
            **state,
            "errors": state.get("errors", []) + [f"Repository conversion failed: {str(e)}"],
            "converted_components": {
                **state.get("converted_components", {}),
                "repositories": []
            }
        }

def convert_services_node(state: ConversionState) -> ConversionState:
    """Convert service layer"""
    try:
        # Check for metadata - skip gracefully if missing instead of failing
        metadata = state.get("metadata")
        if not metadata or not metadata.get("modules"):
            logger.warning("Metadata not found or has no modules, skipping service conversion")
            return {
                **state,
                "errors": state.get("errors", []) + [f"Service conversion skipped: Metadata not found"],
                "converted_components": {
                    **state.get("converted_components", {}),
                    "services": []
                }
            }
        
        model = state.get("model", "")
        if not model or not model.strip():
            raise ValueError(
                "Model parameter is required. Please specify --model when running conversion."
            )
        
        # Create LLM client from state
        llm_client = _create_llm_client_from_state(state)
        
        converter = ServiceConverter(
            llm_client=llm_client
        )
        
        converted_services = []
        services = [m for m in state["metadata"]["modules"] if m.get("type") == "Service"]
        
        logger.info(f"Converting {len(services)} services...")
        
        for service in services:
            try:
                # Get Java code from consolidated file or individual file
                java_code = ""
                file_path = service.get("filePath")
                class_name = service.get("name", "")
                
                # Try consolidated file first
                codebase_text_file = state.get("codebase_text_file")
                if codebase_text_file:
                    java_code = _extract_code_from_consolidated_file(codebase_text_file, file_path, class_name)
                
                # Fallback to reading individual file if not found in consolidated file
                if not java_code and file_path and state.get("repo_path"):
                    full_path = os.path.join(state["repo_path"], file_path)
                    if os.path.exists(full_path):
                        with open(full_path, 'r', encoding='utf-8') as f:
                            java_code = f.read()
                
                converted = converter.convert_service(service, java_code)
                converted_services.append(converted)
            except Exception as e:
                logger.warning(f"Failed to convert service {service.get('name', 'unknown')}: {e}")
                converted_services.append(converter._create_stub_service(service))
        
        logger.info(f"Converted {len(converted_services)} services")
        
        return {
            **state,
            "converted_components": {
                **state.get("converted_components", {}),
                "services": converted_services
            }
        }
    except Exception as e:
        logger.error(f"Failed to convert services: {e}")
        return {
            **state,
            "errors": state.get("errors", []) + [f"Service conversion failed: {str(e)}"],
            "converted_components": {
                **state.get("converted_components", {}),
                "services": []
            }
        }

def convert_controllers_node(state: ConversionState) -> ConversionState:
    """Convert controllers to routes"""
    try:
        # Check for metadata - skip gracefully if missing instead of failing
        metadata = state.get("metadata")
        if not metadata or not metadata.get("modules"):
            logger.warning("Metadata not found or has no modules, skipping controller conversion")
            return {
                **state,
                "errors": state.get("errors", []) + [f"Controller conversion skipped: Metadata not found"],
                "converted_components": {
                    **state.get("converted_components", {}),
                    "controllers": []
                }
            }
        
        model = state.get("model", "")
        if not model or not model.strip():
            raise ValueError(
                "Model parameter is required. Please specify --model when running conversion."
            )
        
        # Create LLM client from state
        llm_client = _create_llm_client_from_state(state)
        
        converter = ControllerConverter(
            target_framework=state.get("target_framework", "express"),
            llm_client=llm_client
        )
        
        converted_controllers = []
        controllers = [m for m in state["metadata"]["modules"] if m.get("type") == "Controller"]
        
        logger.info(f"Converting {len(controllers)} controllers...")
        
        for controller in controllers:
            try:
                # Get Java code from consolidated file or individual file
                java_code = ""
                file_path = controller.get("filePath")
                class_name = controller.get("name", "")
                
                # Try consolidated file first
                codebase_text_file = state.get("codebase_text_file")
                if codebase_text_file:
                    java_code = _extract_code_from_consolidated_file(codebase_text_file, file_path, class_name)
                
                # Fallback to reading individual file if not found in consolidated file
                if not java_code and file_path and state.get("repo_path"):
                    full_path = os.path.join(state["repo_path"], file_path)
                    if os.path.exists(full_path):
                        with open(full_path, 'r', encoding='utf-8') as f:
                            java_code = f.read()
                
                converted = converter.convert_controller(controller, java_code)
                converted_controllers.append(converted)
            except Exception as e:
                logger.warning(f"Failed to convert controller {controller.get('name', 'unknown')}: {e}")
                converted_controllers.append(converter._create_stub_controller(controller))
        
        logger.info(f"Converted {len(converted_controllers)} controllers")
        
        return {
            **state,
            "converted_components": {
                **state.get("converted_components", {}),
                "controllers": converted_controllers
            }
        }
    except Exception as e:
        logger.error(f"Failed to convert controllers: {e}")
        return {
            **state,
            "errors": state.get("errors", []) + [f"Controller conversion failed: {str(e)}"],
            "converted_components": {
                **state.get("converted_components", {}),
                "controllers": []
            }
        }

def generate_config_node(state: ConversionState) -> ConversionState:
    """Generate configuration files"""
    try:
        migrator = ConfigMigrator()
        repo_path = state.get("repo_path")
        
        if repo_path:
            config = migrator.migrate_config(repo_path)
        else:
            config = {
                "database": {"type": "mysql", "host": "localhost", "port": 3306},
                "server": {"port": 3000},
                "environment": {}
            }
        
        logger.info("Generated configuration")
        
        return {
            **state,
            "node_config": config
        }
    except Exception as e:
        logger.error(f"Failed to generate config: {e}")
        return {
            **state,
            "errors": state.get("errors", []) + [f"Config generation failed: {str(e)}"],
            "node_config": {}
        }

def generate_project_node(state: ConversionState) -> ConversionState:
    """Generate complete Node.js project"""
    try:
        generator = ProjectGenerator()
        
        converted_components = state.get("converted_components", {})
        node_dependencies = state.get("node_dependencies", {})
        node_config = state.get("node_config", {})
        metadata = state.get("metadata", {})
        
        output_path = state.get("output_path")
        if not output_path:
            output_path = f"/tmp/conversion-output-{uuid.uuid4()}"
            os.makedirs(output_path, exist_ok=True)
        
        final_path = generator.generate_project(
            converted_components=converted_components,
            dependencies=node_dependencies,
            config=node_config,
            metadata=metadata,
            output_path=output_path
        )
        
        logger.info(f"Generated project at {final_path}")
        
        return {
            **state,
            "output_path": final_path
        }
    except Exception as e:
        logger.error(f"Failed to generate project: {e}")
        return {
            **state,
            "errors": state.get("errors", []) + [f"Project generation failed: {str(e)}"],
            "output_path": state.get("output_path", "/tmp/conversion-output")
        }

def validate_node(state: ConversionState) -> ConversionState:
    """Validate generated project"""
    try:
        validator = ConversionValidator()
        output_path = state.get("output_path")
        
        if not output_path:
            raise ValueError("Output path not found")
        
        # Validate project structure
        validation_result = validator.validate_project(output_path)
        
        # Also validate metadata - ensure we have a dict, not None
        metadata = state.get("metadata") or {}
        metadata_validation = validator.validate_metadata(metadata)
        
        # Combine validation results
        combined_errors = validation_result.get("errors", []) + metadata_validation.get("errors", [])
        combined_warnings = validation_result.get("warnings", []) + metadata_validation.get("warnings", [])
        
        final_result = {
            "valid": validation_result.get("valid", False) and metadata_validation.get("valid", False),
            "errors": combined_errors,
            "warnings": combined_warnings,
            "stats": validation_result.get("stats", {})
        }
        
        logger.info(f"Validation completed: {'Valid' if final_result['valid'] else 'Invalid'}")
        
        return {
            **state,
            "validation_result": final_result
        }
    except Exception as e:
        logger.error(f"Failed to validate project: {e}")
        return {
            **state,
            "validation_result": {
                "valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "warnings": [],
                "stats": {}
            }
        }