"""Repository analyzer for GitHub repositories"""

import os
import re
import tempfile
import logging
from typing import Dict, List, Optional
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class RepositoryAnalyzer:
    """Analyzes GitHub repositories: cloning, file discovery, categorization"""
    
    # File categorization patterns
    CONTROLLER_PATTERNS = [
        r'@RestController',
        r'@Controller',
        r'class\s+\w+Controller',
        r'extends.*Controller'
    ]
    
    SERVICE_PATTERNS = [
        r'@Service',
        r'class\s+\w+Service',
        r'implements\s+\w+Service'
    ]
    
    REPOSITORY_PATTERNS = [
        r'@Repository',
        r'interface\s+\w+Repository',
        r'extends\s+\w*Repository',
        r'extends\s+JpaRepository',
        r'extends\s+CrudRepository'
    ]
    
    ENTITY_PATTERNS = [
        r'@Entity',
        r'@Table',
        r'class\s+\w+\s+implements\s+Serializable',
        r'@Jpa.*Entity'
    ]
    
    CONFIG_PATTERNS = [
        r'@Configuration',
        r'@SpringBootApplication',
        r'class\s+\w+Config'
    ]
    
    def __init__(self, github_url: str):
        """
        Initialize repository analyzer
        
        Args:
            github_url: GitHub repository URL (e.g., https://github.com/owner/repo)
        """
        self.github_url = github_url
        self.repo_path = None
        self.temp_dir = None
        
        # Extract owner and repo name
        match = re.match(r'https?://github\.com/([^/]+)/([^/]+)', github_url)
        if not match:
            raise ValueError(f"Invalid GitHub URL: {github_url}")
        
        self.owner = match.group(1)
        self.repo_name = match.group(2).replace('.git', '')
    
    def clone_repository(self, branch: str = None) -> str:
        """
        Clone GitHub repository to temporary directory
        
        Args:
            branch: Optional branch name (default: main/master)
            
        Returns:
            Path to cloned repository
        """
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix=f"conversion-{self.repo_name}-")
        
        try:
            # Determine branch
            if not branch:
                # Try to detect default branch
                try:
                    result = subprocess.run(
                        ['git', 'ls-remote', '--heads', self.github_url],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0 and result.stdout:
                        # Check for main or master
                        if 'refs/heads/main' in result.stdout:
                            branch = 'main'
                        elif 'refs/heads/master' in result.stdout:
                            branch = 'master'
                        else:
                            # Use first branch found
                            first_branch = result.stdout.split('\n')[0].split('/')[-1]
                            branch = first_branch
                except Exception as e:
                    logger.warning(f"Could not detect branch: {e}, using 'main'")
                    branch = 'main'
            
            # Clone repository
            logger.info(f"Cloning {self.github_url} (branch: {branch}) to {self.temp_dir}")
            
            clone_cmd = ['git', 'clone', '--depth', '1']
            if branch:
                clone_cmd.extend(['--branch', branch])
            clone_cmd.extend([self.github_url, self.temp_dir])
            
            result = subprocess.run(
                clone_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Git clone failed: {result.stderr}")
            
            # Find the actual repo directory (might have subdirectory)
            repo_dir = os.path.join(self.temp_dir, self.repo_name)
            if os.path.exists(repo_dir):
                self.repo_path = repo_dir
            else:
                self.repo_path = self.temp_dir
            
            logger.info(f"Successfully cloned repository to {self.repo_path}")
            return self.repo_path
            
        except Exception as e:
            # Cleanup on error
            self.cleanup()
            raise RuntimeError(f"Failed to clone repository: {e}")
    
    def discover_files(self) -> Dict[str, List[Dict]]:
        """
        Recursively discover and categorize Java files
        
        Returns:
            Dictionary with categorized files:
            {
                'controllers': [{'path': str, 'package': str, 'class': str}],
                'services': [...],
                'repositories': [...],
                'entities': [...],
                'configs': [...],
                'other': [...]
            }
        """
        if not self.repo_path:
            raise ValueError("Repository not cloned. Call clone_repository() first.")
        
        file_map = {
            'controllers': [],
            'services': [],
            'repositories': [],
            'entities': [],
            'configs': [],
            'other': []
        }
        
        # Find all Java files
        java_files = list(Path(self.repo_path).rglob('*.java'))
        
        logger.info(f"Found {len(java_files)} Java files")
        
        for java_file in java_files:
            # Skip test files for now (can add option later)
            if 'test' in str(java_file).lower():
                continue
            
            try:
                with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                    # Read only first 10KB for categorization and metadata extraction
                    # Full content is now in consolidated codebase file
                    content_sample = f.read(10000)
                
                # Categorize file and extract metadata
                file_info = {
                    'path': str(java_file),
                    'relative_path': str(java_file.relative_to(self.repo_path)),
                    'package': self._extract_package(content_sample),
                    'class_name': self._extract_class_name(content_sample)
                    # Note: 'content' field removed - use consolidated codebase file instead
                }
                
                category = self._categorize_file(content_sample)
                file_map[category].append(file_info)
                
            except Exception as e:
                logger.warning(f"Error reading {java_file}: {e}")
                continue
        
        logger.info(f"Categorized files: {sum(len(v) for v in file_map.values())} total")
        for category, files in file_map.items():
            logger.info(f"  {category}: {len(files)}")
        
        return file_map
    
    def detect_build_system(self) -> str:
        """
        Detect build system (Maven, Gradle, or Ant)
        
        Returns:
            'maven', 'gradle', 'ant', or 'unknown'
        """
        if not self.repo_path:
            raise ValueError("Repository not cloned. Call clone_repository() first.")
        
        # Check for Maven
        pom_path = os.path.join(self.repo_path, 'pom.xml')
        if os.path.exists(pom_path):
            return 'maven'
        
        # Check for Gradle
        gradle_paths = [
            os.path.join(self.repo_path, 'build.gradle'),
            os.path.join(self.repo_path, 'build.gradle.kts'),
            os.path.join(self.repo_path, 'settings.gradle')
        ]
        if any(os.path.exists(p) for p in gradle_paths):
            return 'gradle'
        
        # Check for Ant
        build_xml = os.path.join(self.repo_path, 'build.xml')
        if os.path.exists(build_xml):
            return 'ant'
        
        return 'unknown'
    
    def parse_dependencies(self) -> List[Dict[str, str]]:
        """
        Parse dependencies from build file
        
        Returns:
            List of dependencies: [{'group': str, 'artifact': str, 'version': str}]
        """
        if not self.repo_path:
            raise ValueError("Repository not cloned. Call clone_repository() first.")
        
        build_system = self.detect_build_system()
        
        if build_system == 'maven':
            return self._parse_maven_dependencies()
        elif build_system == 'gradle':
            return self._parse_gradle_dependencies()
        else:
            logger.warning(f"Unknown build system: {build_system}, cannot parse dependencies")
            return []
    
    def _parse_maven_dependencies(self) -> List[Dict[str, str]]:
        """Parse Maven pom.xml dependencies"""
        pom_path = os.path.join(self.repo_path, 'pom.xml')
        
        if not os.path.exists(pom_path):
            return []
        
        try:
            tree = ET.parse(pom_path)
            root = tree.getroot()
            
            # Handle namespace
            ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            
            dependencies = []
            for dep in root.findall('.//maven:dependency', ns):
                group = dep.find('maven:groupId', ns)
                artifact = dep.find('maven:artifactId', ns)
                version = dep.find('maven:version', ns)
                
                if group is not None and artifact is not None:
                    dependencies.append({
                        'group': group.text,
                        'artifact': artifact.text,
                        'version': version.text if version is not None else 'unknown'
                    })
            
            logger.info(f"Parsed {len(dependencies)} Maven dependencies")
            return dependencies
            
        except Exception as e:
            logger.error(f"Error parsing pom.xml: {e}")
            return []
    
    def _parse_gradle_dependencies(self) -> List[Dict[str, str]]:
        """Parse Gradle build.gradle dependencies (basic regex-based)"""
        gradle_path = os.path.join(self.repo_path, 'build.gradle')
        
        if not os.path.exists(gradle_path):
            return []
        
        try:
            with open(gradle_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            dependencies = []
            # Pattern: implementation 'group:artifact:version'
            pattern = r"(?:implementation|compile|api)\s+['\"]([^:]+):([^:]+):([^'\"]+)['\"]"
            
            for match in re.finditer(pattern, content):
                dependencies.append({
                    'group': match.group(1),
                    'artifact': match.group(2),
                    'version': match.group(3)
                })
            
            logger.info(f"Parsed {len(dependencies)} Gradle dependencies")
            return dependencies
            
        except Exception as e:
            logger.error(f"Error parsing build.gradle: {e}")
            return []
    
    def _categorize_file(self, content: str) -> str:
        """Categorize Java file based on patterns"""
        # Check in order of specificity
        for pattern in self.REPOSITORY_PATTERNS:
            if re.search(pattern, content):
                return 'repositories'
        
        for pattern in self.ENTITY_PATTERNS:
            if re.search(pattern, content):
                return 'entities'
        
        for pattern in self.CONTROLLER_PATTERNS:
            if re.search(pattern, content):
                return 'controllers'
        
        for pattern in self.SERVICE_PATTERNS:
            if re.search(pattern, content):
                return 'services'
        
        for pattern in self.CONFIG_PATTERNS:
            if re.search(pattern, content):
                return 'configs'
        
        return 'other'
    
    def _extract_package(self, content: str) -> str:
        """Extract package declaration"""
        match = re.search(r'^package\s+([\w.]+);', content, re.MULTILINE)
        return match.group(1) if match else 'unknown'
    
    def _extract_class_name(self, content: str) -> str:
        """Extract class name"""
        match = re.search(r'(?:public\s+)?(?:final\s+)?(?:abstract\s+)?class\s+(\w+)', content)
        if not match:
            match = re.search(r'(?:public\s+)?interface\s+(\w+)', content)
        return match.group(1) if match else 'unknown'
    
    def analyze_project_structure(self) -> Dict:
        """Analyze overall project structure"""
        if not self.repo_path:
            raise ValueError("Repository not cloned. Call clone_repository() first.")
        
        file_map = self.discover_files()
        build_system = self.detect_build_system()
        dependencies = self.parse_dependencies()
        
        return {
            'build_system': build_system,
            'dependencies': dependencies,
            'file_counts': {
                'controllers': len(file_map['controllers']),
                'services': len(file_map['services']),
                'repositories': len(file_map['repositories']),
                'entities': len(file_map['entities']),
                'configs': len(file_map['configs']),
                'other': len(file_map['other'])
            },
            'total_java_files': sum(len(v) for v in file_map.values())
        }
    
    def cleanup(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory: {e}")
            self.temp_dir = None
            self.repo_path = None

