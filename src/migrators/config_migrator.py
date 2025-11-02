"""Migrate Java configuration to Node.js"""

import os
import re
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class ConfigMigrator:
    """Migrates Java Spring Boot configuration to Node.js"""
    
    def __init__(self):
        """Initialize config migrator"""
        pass
    
    def migrate_config(self, repo_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Migrate configuration from Java project
        
        Args:
            repo_path: Path to cloned repository (optional)
            
        Returns:
            Dictionary with Node.js configuration:
            {
                "database": {...},
                "server": {...},
                "environment": {...}
            }
        """
        config = {
            "database": {},
            "server": {},
            "environment": {}
        }
        
        if not repo_path:
            # Return default config
            return {
                "database": {"type": "mysql", "host": "localhost", "port": 3306},
                "server": {"port": 3000},
                "environment": {}
            }
        
        # Look for application.properties or application.yml
        properties_path = os.path.join(repo_path, "src", "main", "resources", "application.properties")
        yml_path = os.path.join(repo_path, "src", "main", "resources", "application.yml")
        
        if os.path.exists(properties_path):
            config.update(self._parse_properties(properties_path))
        elif os.path.exists(yml_path):
            config.update(self._parse_yml(yml_path))
        
        # Create .env format
        env_config = self._generate_env_config(config)
        config["env"] = env_config
        
        return config
    
    def _parse_properties(self, file_path: str) -> Dict[str, Any]:
        """Parse application.properties file"""
        config = {
            "database": {},
            "server": {},
            "environment": {}
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse database config
            db_host = self._extract_property(content, r'spring\.datasource\.url.*?://[^/]+/(\w+)', 'localhost')
            db_name = self._extract_property(content, r'spring\.datasource\.url.*?/(\w+)(?:\?|$)', 'mydb')
            db_user = self._extract_property(content, r'spring\.datasource\.username=(.+)', 'root')
            db_password = self._extract_property(content, r'spring\.datasource\.password=(.+)', '')
            db_driver = self._extract_property(content, r'spring\.datasource\.driver-class-name=(.+)', '')
            
            # Determine database type from URL
            db_url = self._extract_property(content, r'spring\.datasource\.url=(.+)', '')
            if 'mysql' in db_url.lower():
                db_type = 'mysql'
            elif 'postgresql' in db_url.lower():
                db_type = 'postgresql'
            elif 'h2' in db_url.lower():
                db_type = 'sqlite'
            else:
                db_type = 'mysql'  # Default
            
            config["database"] = {
                "type": db_type,
                "host": self._extract_host_from_url(db_url) or 'localhost',
                "port": self._extract_port_from_url(db_url, db_type) or 3306,
                "database": db_name,
                "username": db_user,
                "password": db_password,
                "driver": db_driver
            }
            
            # Parse server config
            server_port = self._extract_property(content, r'server\.port=(\d+)', '3000')
            config["server"] = {
                "port": int(server_port),
                "host": "0.0.0.0"
            }
            
            # Parse JPA/Hibernate config
            jpa_dialect = self._extract_property(content, r'spring\.jpa\.database-platform=(.+)', '')
            jpa_ddl = self._extract_property(content, r'spring\.jpa\.hibernate\.ddl-auto=(.+)', 'none')
            
            if jpa_dialect:
                config["database"]["dialect"] = jpa_dialect
            config["database"]["sync"] = jpa_ddl == "update" or jpa_ddl == "create"
            
        except Exception as e:
            logger.warning(f"Failed to parse properties file: {e}")
        
        return config
    
    def _parse_yml(self, file_path: str) -> Dict[str, Any]:
        """Parse application.yml file (basic parsing)"""
        # Basic YAML parsing - could be enhanced
        config = {
            "database": {},
            "server": {},
            "environment": {}
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract database URL
            db_url_match = re.search(r'datasource:\s*\n\s*url:\s*["\']?([^"\'\n]+)', content)
            if db_url_match:
                db_url = db_url_match.group(1)
                config["database"] = {
                    "type": "mysql" if "mysql" in db_url else "postgresql",
                    "host": self._extract_host_from_url(db_url) or "localhost",
                    "port": self._extract_port_from_url(db_url) or 3306,
                    "database": self._extract_property(content, r'url:.*?/(\w+)', 'mydb')
                }
            
            # Extract server port
            port_match = re.search(r'server:\s*\n\s*port:\s*(\d+)', content)
            if port_match:
                config["server"]["port"] = int(port_match.group(1))
            else:
                config["server"]["port"] = 3000
                
        except Exception as e:
            logger.warning(f"Failed to parse YAML file: {e}")
        
        return config
    
    def _extract_property(self, content: str, pattern: str, default: str = "") -> str:
        """Extract property value using regex"""
        match = re.search(pattern, content, re.IGNORECASE)
        return match.group(1).strip() if match else default
    
    def _extract_host_from_url(self, url: str) -> Optional[str]:
        """Extract host from JDBC URL"""
        if not url:
            return None
        match = re.search(r'://([^:/]+)', url)
        return match.group(1) if match else None
    
    def _extract_port_from_url(self, url: str, db_type: str = "mysql") -> Optional[int]:
        """Extract port from JDBC URL"""
        if not url:
            # Default ports
            defaults = {"mysql": 3306, "postgresql": 5432, "h2": 8082}
            return defaults.get(db_type, 3306)
        
        match = re.search(r':(\d+)/', url)
        if match:
            return int(match.group(1))
        
        # Default ports by type
        defaults = {"mysql": 3306, "postgresql": 5432, "h2": 8082}
        return defaults.get(db_type, 3306)
    
    def _generate_env_config(self, config: Dict) -> str:
        """Generate .env file content"""
        lines = []
        
        # Database config
        db = config.get("database", {})
        lines.append(f"DB_TYPE={db.get('type', 'mysql')}")
        lines.append(f"DB_HOST={db.get('host', 'localhost')}")
        lines.append(f"DB_PORT={db.get('port', 3306)}")
        lines.append(f"DB_NAME={db.get('database', 'mydb')}")
        lines.append(f"DB_USER={db.get('username', 'root')}")
        lines.append(f"DB_PASSWORD={db.get('password', '')}")
        
        # Server config
        server = config.get("server", {})
        lines.append(f"PORT={server.get('port', 3000)}")
        lines.append(f"NODE_ENV=development")
        
        return "\n".join(lines)
    
    def generate_config_files(self, config: Dict, output_path: str):
        """
        Generate Node.js configuration files
        
        Args:
            config: Configuration dictionary
            output_path: Output directory
        """
        # Create config directory
        config_dir = os.path.join(output_path, "config")
        os.makedirs(config_dir, exist_ok=True)
        
        # Generate .env file
        env_path = os.path.join(output_path, ".env")
        with open(env_path, 'w') as f:
            f.write(config.get("env", ""))
        
        # Generate database config
        db_config_path = os.path.join(config_dir, "database.js")
        db_config_code = self._generate_database_config(config.get("database", {}))
        with open(db_config_path, 'w') as f:
            f.write(db_config_code)
        
        logger.info(f"Generated configuration files in {output_path}")
    
    def _generate_database_config(self, db_config: Dict) -> str:
        """Generate database configuration file"""
        db_type = db_config.get("type", "mysql")
        
        if db_type == "mysql":
            return f"""const {{ Sequelize }} = require('sequelize');
require('dotenv').config();

const sequelize = new Sequelize(
    process.env.DB_NAME || '{db_config.get('database', 'mydb')}',
    process.env.DB_USER || '{db_config.get('username', 'root')}',
    process.env.DB_PASSWORD || '{db_config.get('password', '')}',
    {{
        host: process.env.DB_HOST || '{db_config.get('host', 'localhost')}',
        port: process.env.DB_PORT || {db_config.get('port', 3306)},
        dialect: 'mysql',
        logging: process.env.NODE_ENV === 'development' ? console.log : false,
    }}
);

module.exports = sequelize;
"""
        else:
            return f"""const {{ Sequelize }} = require('sequelize');
require('dotenv').config();

const sequelize = new Sequelize(
    process.env.DB_NAME || '{db_config.get('database', 'mydb')}',
    process.env.DB_USER || '{db_config.get('username', 'root')}',
    process.env.DB_PASSWORD || '{db_config.get('password', '')}',
    {{
        host: process.env.DB_HOST || '{db_config.get('host', 'localhost')}',
        port: process.env.DB_PORT || {db_config.get('port', 5432)},
        dialect: '{db_type}',
        logging: process.env.NODE_ENV === 'development' ? console.log : false,
    }}
);

module.exports = sequelize;
"""

