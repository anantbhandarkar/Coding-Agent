# src/api/server.py

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional
import uuid
import logging
import os
import shutil
from pathlib import Path
from ..agents.orchestrator import create_conversion_workflow, ConversionState

app = FastAPI(title="Java to Node.js Conversion Agent")

# Serve static HTML file
BASE_DIR = Path(__file__).resolve().parent.parent.parent

@app.get("/")
async def root():
    """Serve the HTML interface"""
    html_path = BASE_DIR / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    return {"message": "Java to Node.js Conversion Agent API", "docs": "/docs"}

# Store conversion jobs (in-memory for Phase 1, DB in Phase 2)
conversion_jobs = {}

class ConversionRequest(BaseModel):
    # LLM Provider Configuration (new multi-provider support)
    llm_provider: Optional[str] = "gemini"  # "gemini", "glm", "openrouter", "openai"
    llm_api_token: Optional[str] = None  # API token (not required if using profile)
    llm_base_url: Optional[str] = None  # Custom base URL for GLM/OpenAI
    llm_profile_name: Optional[str] = None  # Profile name from config file
    llm_config_path: Optional[str] = None  # Path to config file
    # Legacy support (deprecated, but maintained for backward compatibility)
    gemini_api_token: Optional[str] = None
    
    github_url: HttpUrl
    target_framework: str = "express"  # or "nestjs"
    orm_choice: str = "sequelize"  # or "typeorm"
    model: str  # Model name (required, format depends on provider)

class ConversionResponse(BaseModel):
    job_id: str
    status: str  # "queued" | "processing" | "completed" | "failed"
    message: str

@app.post("/api/convert", response_model=ConversionResponse)
async def start_conversion(
    request: ConversionRequest,
    background_tasks: BackgroundTasks
):
    """Start a new conversion job"""
    
    # Validate inputs
    if request.target_framework not in ["express", "nestjs"]:
        raise HTTPException(400, "target_framework must be 'express' or 'nestjs'")
    
    if request.orm_choice not in ["sequelize", "typeorm"]:
        raise HTTPException(400, "orm_choice must be 'sequelize' or 'typeorm'")
    
    # Create job
    job_id = str(uuid.uuid4())
    
    conversion_jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "current_phase": None,
        "metadata": None,
        "output_path": None,
        "errors": []
    }
    
    # Validate LLM configuration
    if request.llm_profile_name:
        # Using profile - API token not required
        if request.llm_api_token:
            logger.warning(f"Job {job_id}: llm_api_token ignored when using profile")
    else:
        # Using direct provider - need API token
        if not request.llm_api_token and not request.gemini_api_token:
            raise HTTPException(400, "llm_api_token is required when not using llm_profile_name")
        
        # Legacy support: convert gemini_api_token
        if request.gemini_api_token and not request.llm_api_token:
            request.llm_provider = request.llm_provider or "gemini"
            request.llm_api_token = request.gemini_api_token
    
    # Default provider if not specified
    if not request.llm_provider:
        request.llm_provider = "gemini"
    
    # Start conversion in background
    background_tasks.add_task(
        run_conversion,
        job_id=job_id,
        github_url=str(request.github_url),
        target_framework=request.target_framework,
        orm_choice=request.orm_choice,
        model=request.model,
        llm_provider=request.llm_provider,
        llm_api_token=request.llm_api_token,
        llm_base_url=request.llm_base_url,
        llm_profile_name=request.llm_profile_name,
        llm_config_path=request.llm_config_path,
        # Legacy support
        gemini_api_token=request.gemini_api_token if request.llm_provider == "gemini" else None
    )
    
    return ConversionResponse(
        job_id=job_id,
        status="queued",
        message="Conversion job started"
    )

@app.get("/api/convert/{job_id}")
async def get_conversion_status(job_id: str):
    """Get status of conversion job"""
    
    if job_id not in conversion_jobs:
        raise HTTPException(404, "Job not found")
    
    job = conversion_jobs[job_id]
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "current_phase": job["current_phase"],
        "metadata": job["metadata"],
        "output_path": job["output_path"],
        "errors": job["errors"]
    }

@app.get("/api/convert/{job_id}/metadata")
async def get_project_metadata(job_id: str):
    """Get extracted project metadata"""
    
    if job_id not in conversion_jobs:
        raise HTTPException(404, "Job not found")
    
    job = conversion_jobs[job_id]
    
    if not job["metadata"]:
        raise HTTPException(400, "Metadata not yet extracted")
    
    return job["metadata"]

@app.get("/api/convert/{job_id}/download")
async def download_converted_project(job_id: str):
    """Download converted project as ZIP"""
    
    if job_id not in conversion_jobs:
        raise HTTPException(404, "Job not found")
    
    job = conversion_jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(400, "Conversion not completed")
    
    # Create ZIP file
    zip_path = _create_zip(job["output_path"])
    
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"converted-project-{job_id}.zip"
    )

def _create_zip(output_path: str) -> str:
    """Create ZIP file from output directory"""
    import tempfile
    zip_file = tempfile.mktemp(suffix='.zip')
    shutil.make_archive(zip_file.replace('.zip', ''), 'zip', output_path)
    return zip_file

@app.delete("/api/convert/{job_id}")
async def cancel_conversion(job_id: str):
    """Cancel a running conversion"""
    
    if job_id not in conversion_jobs:
        raise HTTPException(404, "Job not found")
    
    job = conversion_jobs[job_id]
    
    if job["status"] in ["completed", "failed"]:
        raise HTTPException(400, "Cannot cancel completed/failed job")
    
    # Set status to cancelled
    job["status"] = "cancelled"
    
    return {"message": "Conversion cancelled"}

# Background conversion task
async def run_conversion(
    job_id: str,
    github_url: str,
    target_framework: str,
    orm_choice: str,
    model: str,
    llm_provider: Optional[str] = None,
    llm_api_token: Optional[str] = None,
    llm_base_url: Optional[str] = None,
    llm_profile_name: Optional[str] = None,
    llm_config_path: Optional[str] = None,
    # Legacy support
    gemini_api_token: Optional[str] = None
):
    """Execute conversion workflow"""
    
    try:
        # Validate model is provided
        if not model or not model.strip():
            conversion_jobs[job_id]["status"] = "failed"
            conversion_jobs[job_id]["errors"].append(
                "Model parameter is required. Please specify model in the conversion request."
            )
            logging.error(f"Conversion {job_id} failed: Model parameter is required")
            return
        
        # Update status
        conversion_jobs[job_id]["status"] = "processing"
        conversion_jobs[job_id]["current_phase"] = "Cloning repository"
        conversion_jobs[job_id]["progress"] = 5
        
        # Create workflow
        workflow = create_conversion_workflow()
        
        # Initial state - support both new and legacy format
        state_data = {
            "github_url": github_url,
            "target_framework": target_framework,
            "orm_choice": orm_choice,
            "model": model.strip(),
            "repo_path": None,
            "codebase_text_file": None,
            "file_map": None,
            "metadata": None,
            "converted_components": {},
            "output_path": None,
            "validation_result": None,
            "errors": []
        }
        
        # LLM configuration
        if llm_profile_name:
            # Using config file profile
            state_data["llm_profile_name"] = llm_profile_name
            state_data["llm_config_path"] = llm_config_path
            state_data["llm_provider"] = None
            state_data["llm_api_token"] = None
            state_data["llm_base_url"] = None
            state_data["gemini_api_token"] = None
        else:
            # Using direct provider configuration
            state_data["llm_provider"] = llm_provider or "gemini"
            state_data["llm_api_token"] = llm_api_token
            state_data["llm_base_url"] = llm_base_url
            state_data["llm_profile_name"] = None
            state_data["llm_config_path"] = llm_config_path
            # Legacy support for backward compatibility
            if gemini_api_token and not llm_api_token:
                state_data["llm_provider"] = "gemini"
                state_data["llm_api_token"] = gemini_api_token
            state_data["gemini_api_token"] = gemini_api_token if state_data["llm_provider"] == "gemini" else None
        
        initial_state = ConversionState(**state_data)
        
        # Execute workflow with progress tracking
        result = None
        for event in workflow.stream(initial_state):
            node_name = list(event.keys())[0]
            node_output = event[node_name]
            
            # Update progress
            progress_map = {
                "clone_repo": 10,
                "analyze_structure": 20,
                "extract_metadata": 30,
                "map_dependencies": 40,
                "convert_models": 50,
                "convert_repositories": 60,
                "convert_services": 70,
                "convert_controllers": 80,
                "generate_config": 85,
                "generate_project": 90,
                "validate": 95
            }
            
            conversion_jobs[job_id]["progress"] = progress_map.get(node_name, 50)
            conversion_jobs[job_id]["current_phase"] = node_name.replace("_", " ").title()
            
            # Store metadata when available
            if "metadata" in node_output and node_output["metadata"]:
                conversion_jobs[job_id]["metadata"] = node_output["metadata"]
            
            result = node_output
        
        # Mark as completed
        conversion_jobs[job_id]["status"] = "completed"
        conversion_jobs[job_id]["progress"] = 100
        conversion_jobs[job_id]["output_path"] = result["output_path"]
        conversion_jobs[job_id]["validation_result"] = result["validation_result"]
        
        logging.info(f"Conversion {job_id} completed successfully")
        
    except Exception as e:
        # Mark as failed
        conversion_jobs[job_id]["status"] = "failed"
        conversion_jobs[job_id]["errors"].append(str(e))
        
        logging.error(f"Conversion {job_id} failed: {str(e)}")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

class ModelListRequest(BaseModel):
    api_token: str

@app.post("/api/models/list")
async def list_gemini_models(request: ModelListRequest):
    """List available Gemini models for a given API token"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=request.api_token)
        
        # Fetch available models
        models = []
        try:
            for model in genai.list_models():
                # Filter for Gemini models only
                if 'generateContent' in model.supported_generation_methods:
                    # Extract model name from full path (e.g., "models/gemini-2.5-flash" -> "gemini-2.5-flash")
                    model_name = model.name.split('/')[-1] if '/' in model.name else model.name
                    model_info = {
                        "name": model_name,
                        "display_name": model.display_name or model_name,
                        "full_name": model.name
                    }
                    models.append(model_info)
        except Exception as e:
            # Distinguish between authentication errors and other issues
            error_msg = str(e).lower()
            if 'api token' in error_msg or 'api key' in error_msg or 'authentication' in error_msg or 'permission' in error_msg:
                raise HTTPException(401, f"Invalid API token or insufficient permissions: {str(e)}")
            else:
                raise HTTPException(400, f"Failed to fetch models: {str(e)}. Check your API token.")
        
        if not models:
            # Return empty array instead of error - let frontend handle the message
            return {
                "models": [],
                "error": "No Gemini models available for this API token. This may indicate: 1) API token lacks permissions, 2) No models are currently available, 3) API token is invalid."
            }
        
        # Sort by preference: highest version Pro models first, then Flash, then others
        def extract_version(model_name):
            """Extract version number from model name (e.g., 'gemini-2.5-pro' -> 2.5)"""
            import re
            match = re.search(r'(\d+)\.(\d+)', model_name)
            if match:
                return float(f"{match.group(1)}.{match.group(2)}")
            match = re.search(r'(\d+)', model_name)
            if match:
                return float(match.group(1))
            return 0.0
        
        def sort_key(m):
            name = m["name"].lower()
            version = extract_version(name)
            
            # Priority: Pro models by version (highest first), then Flash by version, then others
            if "pro" in name and "flash" not in name:
                return (0, -version)  # Negative for descending order
            elif "flash" in name:
                return (1, -version)  # Negative for descending order
            else:
                return (2, name)
        
        models.sort(key=sort_key)  # 'key' here is Python's sort parameter, not API key
        
        return {"models": models}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error listing models: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)