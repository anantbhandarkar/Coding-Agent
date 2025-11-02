"""Map Java dependencies to Node.js equivalents"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# Static mapping of common Java libraries to Node.js equivalents
JAVA_TO_NODEJS_MAPPING = {
    # Spring Framework
    "org.springframework.boot:spring-boot-starter-web": {
        "package": "express",
        "version": "^4.18.0",
        "description": "Web framework for REST APIs"
    },
    "org.springframework.boot:spring-boot-starter-data-jpa": {
        "package": "sequelize",
        "version": "^6.32.0",
        "description": "ORM for database access"
    },
    "org.springframework.boot:spring-boot-starter-security": {
        "package": "passport",
        "version": "^0.6.0",
        "additional": ["passport-jwt", "jsonwebtoken"],
        "description": "Authentication and authorization"
    },
    "org.springframework.boot:spring-boot-starter-validation": {
        "package": "express-validator",
        "version": "^7.0.0",
        "description": "Request validation"
    },
    
    # Database Drivers
    "mysql:mysql-connector-java": {
        "package": "mysql2",
        "version": "^3.6.0",
        "description": "MySQL database driver"
    },
    "org.postgresql:postgresql": {
        "package": "pg",
        "version": "^8.11.0",
        "description": "PostgreSQL database driver"
    },
    "com.h2database:h2": {
        "package": "better-sqlite3",
        "version": "^9.0.0",
        "description": "In-memory database (using SQLite as alternative)"
    },
    
    # JSON Processing
    "com.fasterxml.jackson.core:jackson-databind": {
        "package": None,
        "description": "Built into Node.js (JSON.parse/stringify)"
    },
    
    # Logging
    "ch.qos.logback:logback-classic": {
        "package": "winston",
        "version": "^3.11.0",
        "description": "Logging framework"
    },
    "org.slf4j:slf4j-api": {
        "package": "winston",
        "version": "^3.11.0",
        "description": "Logging framework"
    },
    
    # Testing
    "org.springframework.boot:spring-boot-starter-test": {
        "package": "jest",
        "version": "^29.7.0",
        "description": "Testing framework"
    },
    "junit:junit": {
        "package": "jest",
        "version": "^29.7.0",
        "description": "Testing framework"
    },
    
    # Utilities
    "org.apache.commons:commons-lang3": {
        "package": "lodash",
        "version": "^4.17.21",
        "description": "Utility functions"
    },
    "com.google.guava:guava": {
        "package": "lodash",
        "version": "^4.17.21",
        "description": "Utility functions"
    },
    
    # HTTP Client
    "org.springframework.boot:spring-boot-starter-webflux": {
        "package": "axios",
        "version": "^1.6.0",
        "description": "HTTP client (for reactive web)"
    },
    "org.springframework:spring-webflux": {
        "package": "axios",
        "version": "^1.6.0",
        "description": "HTTP client"
    },
    
    # Configuration
    "org.springframework.boot:spring-boot-configuration-processor": {
        "package": "dotenv",
        "version": "^16.3.0",
        "description": "Configuration management"
    },
    
    # Caching
    "org.springframework.boot:spring-boot-starter-cache": {
        "package": "node-cache",
        "version": "^5.1.2",
        "description": "In-memory caching"
    },
    
    # Scheduled Tasks
    "org.springframework:spring-context": {
        "package": "node-cron",
        "version": "^3.0.3",
        "additional": ["node-schedule"],
        "description": "Scheduled tasks (if @Scheduled is used)"
    },
}

# Common mappings by artifact name only (fallback)
ARTIFACT_ONLY_MAPPING = {
    "spring-boot-starter-web": "express",
    "spring-boot-starter-data-jpa": "sequelize",
    "spring-boot-starter-security": "passport",
    "mysql-connector-java": "mysql2",
    "postgresql": "pg",
    "jackson-databind": None,  # Built-in
    "logback-classic": "winston",
    "slf4j-api": "winston",
    "commons-lang3": "lodash",
    "guava": "lodash",
    "webflux": "axios",
    "h2": "better-sqlite3",
}


class DependencyMapper:
    """Maps Java dependencies to Node.js package equivalents"""
    
    def __init__(self):
        """Initialize dependency mapper"""
        self.mapping = JAVA_TO_NODEJS_MAPPING.copy()
    
    def map_dependencies(self, java_dependencies: List[Dict[str, str]]) -> Dict[str, Dict]:
        """
        Map Java dependencies to Node.js packages
        
        Args:
            java_dependencies: List of Java dependencies with 'group', 'artifact', 'version'
            
        Returns:
            Dictionary mapping package names to their info:
            {
                "express": {"version": "^4.18.0", "description": "..."},
                "sequelize": {"version": "^6.32.0", "description": "..."},
                ...
            }
        """
        node_dependencies = {}
        mapped_packages = set()
        
        for java_dep in java_dependencies:
            group = java_dep.get("group", "")
            artifact = java_dep.get("artifact", "")
            version = java_dep.get("version", "")
            
            # Try full group:artifact match first
            full_key = f"{group}:{artifact}"
            mapping = self.mapping.get(full_key)
            
            if not mapping:
                # Try artifact-only match
                mapping = ARTIFACT_ONLY_MAPPING.get(artifact)
                if isinstance(mapping, str):
                    # Simple string mapping, convert to dict format
                    mapping = {"package": mapping}
                elif mapping is None:
                    # Check if artifact matches a key in mapping (partial match)
                    for key, value in self.mapping.items():
                        if artifact in key:
                            mapping = value
                            break
            
            if mapping:
                package_name = mapping.get("package")
                if package_name and package_name not in mapped_packages:
                    mapped_packages.add(package_name)
                    node_dependencies[package_name] = {
                        "version": mapping.get("version", "latest"),
                        "description": mapping.get("description", f"Mapped from {full_key}")
                    }
                    
                    # Add additional packages if specified
                    if "additional" in mapping:
                        for additional_pkg in mapping["additional"]:
                            if additional_pkg not in mapped_packages:
                                mapped_packages.add(additional_pkg)
                                node_dependencies[additional_pkg] = {
                                    "version": "latest",
                                    "description": f"Additional dependency for {package_name}"
                                }
            else:
                logger.warning(f"No Node.js equivalent found for {full_key}")
        
        # Always include essential packages
        essential_packages = {
            "express": {"version": "^4.18.0", "description": "Web framework"},
            "sequelize": {"version": "^6.32.0", "description": "ORM"},
            "dotenv": {"version": "^16.3.0", "description": "Environment configuration"},
            "cors": {"version": "^2.8.5", "description": "CORS middleware"},
            "helmet": {"version": "^7.1.0", "description": "Security headers"},
        }
        
        for pkg, info in essential_packages.items():
            if pkg not in node_dependencies:
                node_dependencies[pkg] = info
        
        logger.info(f"Mapped {len(node_dependencies)} Node.js packages from {len(java_dependencies)} Java dependencies")
        
        return node_dependencies
    
    def add_custom_mapping(self, java_dep: str, node_package: str, version: str = "latest", description: str = ""):
        """
        Add custom mapping for a Java dependency
        
        Args:
            java_dep: Java dependency key (group:artifact or just artifact)
            node_package: Node.js package name
            version: Package version
            description: Description of the mapping
        """
        self.mapping[java_dep] = {
            "package": node_package,
            "version": version,
            "description": description
        }
        logger.info(f"Added custom mapping: {java_dep} -> {node_package}")
    
    def get_package_json_dependencies(self, java_dependencies: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Generate package.json dependencies object
        
        Args:
            java_dependencies: List of Java dependencies
            
        Returns:
            Dictionary suitable for package.json "dependencies" field:
            {"express": "^4.18.0", "sequelize": "^6.32.0", ...}
        """
        mapped = self.map_dependencies(java_dependencies)
        
        return {
            pkg: info["version"]
            for pkg, info in mapped.items()
        }
    
    def get_dev_dependencies(self) -> Dict[str, str]:
        """
        Get standard dev dependencies for Node.js project
        
        Returns:
            Dictionary of dev dependencies
        """
        return {
            "jest": "^29.7.0",
            "@types/node": "^20.10.0",
            "@types/express": "^4.17.21",
            "@types/cors": "^2.8.17",
            "ts-node": "^10.9.1",
            "typescript": "^5.3.0",
            "nodemon": "^3.0.2"
        }



