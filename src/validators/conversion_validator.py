"""Validate converted Node.js project"""

import os
import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ConversionValidator:
    """Validates converted Node.js project"""
    
    def __init__(self):
        """Initialize validator"""
        pass
    
    def validate_project(self, project_path: str) -> Dict[str, Any]:
        """
        Validate generated project
        
        Args:
            project_path: Path to generated project
            
        Returns:
            Validation result dictionary:
            {
                "valid": bool,
                "errors": [...],
                "warnings": [...],
                "stats": {...}
            }
        """
        errors = []
        warnings = []
        stats = {
            "models": 0,
            "repositories": 0,
            "services": 0,
            "controllers": 0,
            "total_files": 0
        }
        
        # Check if directory exists
        if not os.path.exists(project_path):
            errors.append(f"Project path does not exist: {project_path}")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings,
                "stats": stats
            }
        
        # Validate package.json
        package_json_path = os.path.join(project_path, "package.json")
        if not os.path.exists(package_json_path):
            errors.append("package.json not found")
        else:
            try:
                with open(package_json_path, 'r') as f:
                    package_json = json.load(f)
                    if not package_json.get("dependencies"):
                        warnings.append("No dependencies in package.json")
            except Exception as e:
                errors.append(f"Invalid package.json: {e}")
        
        # Validate server.js
        server_path = os.path.join(project_path, "server.js")
        if not os.path.exists(server_path):
            errors.append("server.js not found")
        
        # Validate directory structure
        required_dirs = ["models", "repositories", "services", "routes"]
        for dir_name in required_dirs:
            dir_path = os.path.join(project_path, dir_name)
            if os.path.exists(dir_path):
                files = [f for f in os.listdir(dir_path) if f.endswith('.js')]
                stats[dir_name] = len(files)
                if not files:
                    warnings.append(f"{dir_name}/ directory is empty")
            else:
                warnings.append(f"{dir_name}/ directory not found")
        
        # Count total files
        for root, dirs, files in os.walk(project_path):
            # Exclude node_modules and .git
            if 'node_modules' in root or '.git' in root:
                continue
            stats["total_files"] += len([f for f in files if f.endswith('.js')])
        
        # Validate .env file
        env_path = os.path.join(project_path, ".env")
        if not os.path.exists(env_path):
            warnings.append(".env file not found (create from .env.example if needed)")
        
        # Validate config directory
        config_path = os.path.join(project_path, "config")
        if not os.path.exists(config_path):
            warnings.append("config/ directory not found")
        else:
            db_config = os.path.join(config_path, "database.js")
            if not os.path.exists(db_config):
                warnings.append("config/database.js not found")
        
        # Check for syntax errors in generated files (basic check)
        self._check_syntax_errors(project_path, errors, warnings)
        
        valid = len(errors) == 0
        
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "stats": stats
        }
    
    def _check_syntax_errors(self, project_path: str, errors: List[str], warnings: List[str]):
        """Basic syntax checking for JS files"""
        import subprocess
        
        js_files = []
        for root, dirs, files in os.walk(project_path):
            if 'node_modules' in root:
                continue
            for file in files:
                if file.endswith('.js'):
                    js_files.append(os.path.join(root, file))
        
        # Use node --check for basic syntax validation
        syntax_errors = []
        for js_file in js_files[:10]:  # Limit to first 10 files
            try:
                result = subprocess.run(
                    ['node', '--check', js_file],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 0:
                    syntax_errors.append(f"{js_file}: {result.stderr.decode('utf-8')[:200]}")
            except Exception:
                # Skip if node is not available or file cannot be checked
                pass
        
        if syntax_errors:
            errors.extend(syntax_errors[:5])  # Limit errors
    
    def validate_metadata(self, metadata: Dict) -> Dict[str, Any]:
        """
        Validate extracted metadata
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        # Handle None metadata defensively
        if metadata is None:
            errors.append("Metadata is None")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings
            }
        
        if not metadata.get("projectOverview"):
            warnings.append("Project overview is missing")
        
        modules = metadata.get("modules", [])
        if not modules:
            errors.append("No modules found in metadata")
        else:
            # Check module completeness
            incomplete = 0
            for module in modules:
                if not module.get("description") or module.get("description") == "":
                    incomplete += 1
                if not module.get("methods"):
                    warnings.append(f"Module {module.get('name', 'Unknown')} has no methods")
            
            if incomplete > len(modules) * 0.5:
                warnings.append(f"{incomplete} modules have incomplete metadata")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

