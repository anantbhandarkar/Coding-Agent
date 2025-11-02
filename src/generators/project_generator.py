"""Generate complete Node.js project structure"""

import os
import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ProjectGenerator:
    """Generates complete Node.js project from converted components"""
    
    def __init__(self):
        """Initialize project generator"""
        pass
    
    def generate_project(
        self,
        converted_components: Dict[str, List[Dict]],
        dependencies: Dict[str, Dict],
        config: Dict[str, Any],
        metadata: Dict,
        output_path: str
    ) -> str:
        """
        Generate complete Node.js project
        
        Args:
            converted_components: Dictionary with 'models', 'repositories', 'services', 'controllers'
            dependencies: Node.js dependencies mapping
            config: Configuration dictionary
            metadata: Project metadata
            output_path: Output directory path
            
        Returns:
            Path to generated project
        """
        # Create output directory structure
        os.makedirs(output_path, exist_ok=True)
        
        dirs = ["models", "repositories", "services", "routes", "config", "middleware"]
        for dir_name in dirs:
            os.makedirs(os.path.join(output_path, dir_name), exist_ok=True)
        
        # Generate package.json
        self._generate_package_json(output_path, dependencies)
        
        # Generate main server file
        self._generate_server_file(output_path, converted_components.get("controllers", []))
        
        # Generate configuration files
        if config:
            from ..migrators.config_migrator import ConfigMigrator
            migrator = ConfigMigrator()
            migrator.generate_config_files(config, output_path)
        
        # Write converted components
        self._write_components(output_path, converted_components)
        
        # Generate README
        self._generate_readme(output_path, metadata)
        
        # Generate .gitignore
        self._generate_gitignore(output_path)
        
        logger.info(f"Generated project at {output_path}")
        return output_path
    
    def _generate_package_json(self, output_path: str, dependencies: Dict[str, Dict]):
        """Generate package.json file"""
        
        # Get dependency versions
        deps = {
            pkg: info.get("version", "latest")
            for pkg, info in dependencies.items()
        }
        
        # Add essential dev dependencies
        dev_deps = {
            "jest": "^29.7.0",
            "@types/node": "^20.10.0",
            "nodemon": "^3.0.2"
        }
        
        package_json = {
            "name": "converted-nodejs-project",
            "version": "1.0.0",
            "description": "Converted from Java Spring Boot application",
            "main": "server.js",
            "scripts": {
                "start": "node server.js",
                "dev": "nodemon server.js",
                "test": "jest"
            },
            "dependencies": deps,
            "devDependencies": dev_deps,
            "engines": {
                "node": ">=18.0.0"
            }
        }
        
        package_path = os.path.join(output_path, "package.json")
        with open(package_path, 'w') as f:
            json.dump(package_json, f, indent=2)
        
        logger.info("Generated package.json")
    
    def _generate_server_file(self, output_path: str, controllers: List[Dict]):
        """Generate main server.js file"""
        
        lines = [
            "const express = require('express');",
            "const cors = require('cors');",
            "const helmet = require('helmet');",
            "require('dotenv').config();",
            "",
            "const app = express();",
            "",
            "// Middleware",
            "app.use(helmet());",
            "app.use(cors());",
            "app.use(express.json());",
            "app.use(express.urlencoded({ extended: true }));",
            "",
            "// Routes"
        ]
        
        # Import and register controllers
        for controller in controllers:
            controller_name = controller.get("name", "").lower()
            file_path = controller.get("file_path", "").replace("routes/", "").replace(".js", "")
            if file_path:
                route_path = f"routes/{file_path}"
                route_var = controller_name.replace("controller", "Router")
                lines.append(f"const {route_var} = require('./{route_path}');")
                # Extract base path from controller
                base_path = self._extract_base_path(controller.get("name", ""))
                lines.append(f"app.use('{base_path}', {route_var});")
        
        # If no controllers, add placeholder
        if not controllers:
            lines.append("// TODO: Register routes")
            lines.append("// app.use('/api', require('./routes/index'));")
        
        lines.extend([
            "",
            "// Error handling middleware",
            "app.use((err, req, res, next) => {",
            "    console.error(err.stack);",
            "    res.status(500).json({",
            "        success: false,",
            "        error: err.message",
            "    });",
            "});",
            "",
            "// 404 handler",
            "app.use((req, res) => {",
            "    res.status(404).json({",
            "        success: false,",
            "        error: 'Route not found'",
            "    });",
            "});",
            "",
            "const PORT = process.env.PORT || 3000;",
            "",
            "app.listen(PORT, () => {",
            "    console.log(`Server running on port ${{PORT}}`);",
            "});",
            "",
            "module.exports = app;"
        ])
        
        server_path = os.path.join(output_path, "server.js")
        with open(server_path, 'w') as f:
            f.write("\n".join(lines))
        
        logger.info("Generated server.js")
    
    def _extract_base_path(self, controller_name: str) -> str:
        """Extract base path from controller name"""
        base = controller_name.replace("Controller", "").lower()
        return f"/api/{base}"
    
    def _write_components(self, output_path: str, components: Dict[str, List[Dict]]):
        """Write all converted components to files"""
        
        component_types = ["models", "repositories", "services", "controllers"]
        
        for comp_type in component_types:
            comp_list = components.get(comp_type, [])
            for component in comp_list:
                file_path = component.get("file_path", "")
                code = component.get("code", "")
                
                if file_path and code:
                    full_path = os.path.join(output_path, file_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    
                    with open(full_path, 'w') as f:
                        f.write(code)
                    
                    logger.debug(f"Wrote {file_path}")
    
    def _generate_readme(self, output_path: str, metadata: Dict):
        """Generate comprehensive README.md with all required sections"""
        
        overview = metadata.get("projectOverview", "Node.js application converted from Java Spring Boot")
        modules = metadata.get("modules", [])
        
        # Count modules by type
        module_counts = {}
        for module in modules:
            module_type = module.get("type", "Unknown")
            module_counts[module_type] = module_counts.get(module_type, 0) + 1
        
        lines = [
            "# Converted Node.js Project",
            "",
            "---",
            "",
            "## Solution Overview",
            "",
            "This project was automatically generated by converting a Java Spring Boot application to Node.js using ",
            "an AI-powered conversion agent. The conversion process preserves the original application's structure, ",
            "business logic, and functionality while adapting it to Node.js and Express.js patterns.",
            "",
            "### Key Features",
            "",
            "- ✅ **Complete Architecture Conversion**: Controller → Service → Repository pattern preserved",
            "- ✅ **Database Integration**: JPA entities converted to Sequelize models with relationship mapping",
            "- ✅ **API Compatibility**: Spring REST controllers converted to Express.js routes",
            "- ✅ **Business Logic Preservation**: Service layer logic translated to async/await patterns",
            "- ✅ **Structured Metadata**: Full project analysis with method signatures, complexity, and dependencies",
            "- ✅ **Production Ready**: Includes error handling, middleware, and configuration files",
            "",
            "### High-Level Conversion Process",
            "",
            "The conversion follows these steps:",
            "",
            "1. **Repository Analysis**: Clone and analyze Java codebase structure",
            "2. **Code Ingestion**: Consolidate all Java files into analyzable format",
            "3. **Metadata Extraction**: Extract structured information using LLM (class descriptions, methods, dependencies)",
            "4. **Dependency Mapping**: Map Java dependencies to Node.js equivalents",
            "5. **Code Conversion**: Convert each component type (Models → Repositories → Services → Controllers)",
            "6. **Project Generation**: Assemble complete Node.js project with package.json, server.js, and configuration",
            "7. **Validation**: Verify project structure and code quality",
            "",
            "---",
            "",
            "## Architecture",
            "",
            "### System Architecture",
            "",
            "The conversion system uses a pipeline-based architecture built on LangGraph workflow:",
            "",
            "```mermaid",
            "graph TD",
            "    A[Clone Repository] --> B[Ingest Codebase]",
            "    B --> C[Analyze Structure]",
            "    C --> D[Extract Metadata]",
            "    D --> E[Map Dependencies]",
            "    E --> F[Convert Models]",
            "    F --> G[Convert Repositories]",
            "    G --> H[Convert Services]",
            "    H --> I[Convert Controllers]",
            "    I --> J[Generate Config]",
            "    J --> K[Generate Project]",
            "    K --> L[Validate]",
            "    L --> M[Output]",
            "    ",
            "    style A fill:#e1f5ff",
            "    style D fill:#fff4e1",
            "    style F fill:#e8f5e9",
            "    style G fill:#e8f5e9",
            "    style H fill:#e8f5e9",
            "    style I fill:#e8f5e9",
            "    style K fill:#f3e5f5",
            "```",
            "",
            "### Component Architecture",
            "",
            "```mermaid",
            "graph LR",
            "    A[Repository Analyzer] --> B[File Discovery]",
            "    A --> C[File Categorization]",
            "    ",
            "    D[Metadata Extractor] --> E[LLM Client]",
            "    D --> F[Chunking Strategy]",
            "    D --> G[Token Manager]",
            "    ",
            "    H[Model Converter] --> E",
            "    I[Repository Converter] --> E",
            "    J[Service Converter] --> E",
            "    K[Controller Converter] --> E",
            "    ",
            "    L[Project Generator] --> M[Package.json]",
            "    L --> N[Server.js]",
            "    L --> O[Directory Structure]",
            "    ",
            "    style E fill:#fff4e1",
            "    style F fill:#e1f5ff",
            "```",
            "",
            "### Component Interactions",
            "",
            "- **Repository Analyzer**: Recursively discovers Java files and categorizes them using regex patterns",
            "- **Metadata Extractor**: Uses LLM to extract structured metadata (descriptions, methods, complexity, dependencies)",
            "- **Chunking Strategy**: Splits large files into manageable chunks respecting token limits",
            "- **LLM Clients**: Multi-provider support (Gemini, GLM, OpenRouter, OpenAI) with unified interface",
            "- **Converters**: Specialized converters for each component type using LLM-assisted translation",
            "- **Project Generator**: Assembles final project structure with all necessary files",
            "",
            "---",
            "",
            "## Instructions to Run the Tool",
            "",
            "### Prerequisites",
            "",
            "- Node.js 18+ installed",
            "- npm or yarn package manager",
            "- Database credentials (MySQL/PostgreSQL) if applicable",
            "- Environment variables configured (see `.env.example`)",
            "",
            "### Installation",
            "",
            "1. **Install dependencies**:",
            "   ```bash",
            "   npm install",
            "   ```",
            "",
            "2. **Configure environment**:",
            "   ```bash",
            "   cp .env.example .env",
            "   # Edit .env with your database credentials",
            "   ```",
            "",
            "3. **Run database migrations** (if applicable):",
            "   ```bash",
            "   npm run migrate",
            "   ```",
            "",
            "### Running the Application",
            "",
            "**Start the server**:",
            "```bash",
            "npm start",
            "```",
            "",
            "**Development mode with hot reload**:",
            "```bash",
            "npm run dev",
            "```",
            "",
            "The server will start on `http://localhost:3000` by default (or the port specified in `.env`).",
            "",
            "### API Endpoints",
            "",
            "The converted application exposes RESTful endpoints based on the original Spring controllers:",
            "",
            "- Routes are accessible at `/api/{resource}` paths",
            "- HTTP methods: GET, POST, PUT, DELETE, PATCH",
            "- Request/Response format: JSON",
            "",
            "Check the `routes/` directory for specific endpoint definitions.",
            "",
            "### Configuration Options",
            "",
            "Key configuration options in `.env`:",
            "",
            "```env",
            "PORT=3000                    # Server port",
            "NODE_ENV=development         # Environment (development/production)",
            "DB_HOST=localhost            # Database host",
            "DB_PORT=3306                # Database port",
            "DB_NAME=your_database       # Database name",
            "DB_USER=your_user           # Database user",
            "DB_PASS=your_password       # Database password",
            "```",
            "",
            "---",
            "",
            "## Assumptions and Limitations",
            "",
            "### Assumptions Made During Conversion",
            "",
            "1. **Spring Framework Patterns**:",
            "   - Assumes standard Spring Boot architecture (Controller-Service-Repository)",
            "   - Spring annotations are properly structured",
            "   - Dependency injection uses constructor-based or field-based `@Autowired`",
            "",
            "2. **Database Layer**:",
            "   - JPA entities follow standard JPA conventions",
            "   - Relationships are explicitly defined with annotations",
            "   - Repository interfaces extend Spring Data JPA interfaces",
            "",
            "3. **API Design**:",
            "   - RESTful API patterns are followed",
            "   - Request/Response objects are properly structured",
            "   - HTTP status codes follow REST conventions",
            "",
            "4. **Code Structure**:",
            "   - Java code follows standard conventions",
            "   - Package structure is clear and organized",
            "   - Method naming follows Java conventions",
            "",
            "### Known Limitations",
            "",
            "1. **Complex Spring Features**:",
            "   - Some advanced Spring features (AOP, Transactions, Caching) require manual review",
            "   - Custom Spring Boot auto-configuration may not be converted",
            "   - Spring Security configurations need manual setup",
            "",
            "2. **Framework-Specific Code**:",
            "   - Thymeleaf templates are not converted (converted to JSON responses)",
            "   - JSP pages require manual conversion",
            "   - WebSocket implementations need manual setup",
            "",
            "3. **Third-Party Integrations**:",
            "   - External service integrations may need API client updates",
            "   - Custom serialization/deserialization needs review",
            "   - Message queue integrations require setup",
            "",
            "4. **Language-Specific Features**:",
            "   - Java generics complexity may not perfectly translate",
            "   - Reflection-based code needs manual adaptation",
            "   - Java 8+ stream operations converted to async/await patterns",
            "",
            "5. **Testing**:",
            "   - Unit tests are not converted automatically",
            "   - Integration tests require manual creation",
            "   - Test fixtures need to be recreated",
            "",
            "### Manual Review Requirements",
            "",
            "Before deploying to production, please review:",
            "",
            "- ✅ **Error Handling**: Verify error responses match requirements",
            "- ✅ **Authentication/Authorization**: Implement security middleware",
            "- ✅ **Input Validation**: Add validation using libraries like Joi or express-validator",
            "- ✅ **Database Queries**: Verify Sequelize queries match original JPA behavior",
            "- ✅ **Environment Configuration**: Review all configuration values",
            "- ✅ **Performance**: Test under load and optimize as needed",
            "- ✅ **Logging**: Set up proper logging infrastructure",
            "",
            "### Edge Cases",
            "",
            "The following scenarios may require additional attention:",
            "",
            "- Very large codebases (>1000 files) may hit token limits",
            "- Complex inheritance hierarchies may need simplification",
            "- Custom annotations require manual mapping",
            "- Reflection-based dependency injection needs review",
            "- Circular dependencies may need restructuring",
            "",
            "---",
            "",
            "## Token Limits Management in LLM Integration",
            "",
            "### Overview",
            "",
            "The conversion system intelligently manages token limits across different LLM providers to ensure ",
            "reliable processing of large codebases. Token management is critical for:",
            "",
            "- Preventing API rate limit errors",
            "- Ensuring complete code analysis",
            "- Optimizing API costs",
            "- Maintaining conversion quality",
            "",
            "### Chunking Strategy",
            "",
            "**File-Level Chunking**:",
            "",
            "Large files are split into manageable chunks using a smart chunking strategy:",
            "",
            "1. **Method-Based Chunking**:",
            "   - Files are split at method boundaries when possible",
            "   - Preserves method context for better LLM understanding",
            "   - Maintains class structure awareness",
            "",
            "2. **Size-Based Chunking**:",
            "   - Default chunk size: **8,000 tokens** (safe for most providers)",
            "   - Fallback to character-based splitting if method boundaries not found",
            "   - Each chunk includes relevant class context",
            "",
            "3. **Token Estimation**:",
            "   - Uses approximation: **~4 characters per token** for Java/JavaScript",
            "   - Accounts for code complexity and structure",
            "   - Provides accurate estimates for chunk sizing",
            "",
            "**Code**:",
            "```python",
            "# From ChunkingStrategy class",
            "TOKENS_PER_CHAR = 0.25  # 4 chars per token",
            "max_chunk_tokens = 8000  # Default chunk size",
            "```",
            "",
            "### Batching Strategy",
            "",
            "**File Batching**:",
            "",
            "Small files are grouped into batches for efficient processing:",
            "",
            "1. **Batch Size Limit**:",
            "   - Maximum batch size: **80,000 tokens**",
            "   - Multiple small files processed together",
            "   - Reduces API calls for small codebases",
            "",
            "2. **Batch Processing**:",
            "   - Files sorted by size",
            "   - Batches filled until token limit reached",
            "   - Large files excluded from batches (processed individually)",
            "",
            "3. **Parallel Processing**:",
            "   - Multiple batches can be processed concurrently (provider-dependent)",
            "   - Respects rate limits per provider",
            "",
            "### LLM Provider Considerations",
            "",
            "**Gemini (Google)**:",
            "- Context window: Up to 1M tokens (depending on model)",
            "- Default chunk size: 8,000 tokens (safe)",
            "- Batch support: Yes",
            "- Rate limits: Vary by API tier",
            "",
            "**OpenRouter**:",
            "- Context window: Model-dependent (typically 4k-128k tokens)",
            "- Chunk size: Adapts to model limits",
            "- Batch support: Varies by model",
            "- Rate limits: Vary by subscription",
            "",
            "**OpenAI**:",
            "- Context window: Model-dependent (GPT-4: 8k-128k tokens)",
            "- Chunk size: 8,000 tokens (conservative)",
            "- Batch support: Yes (via batch API)",
            "- Rate limits: Tier-based",
            "",
            "**GLM (Zhipu AI)**:",
            "- Context window: Model-dependent",
            "- Chunk size: 8,000 tokens (default)",
            "- Batch support: Model-dependent",
            "- Rate limits: Subscription-based",
            "",
            "### Processing Large Content",
            "",
            "**Chunk Processing Flow**:",
            "",
            "```mermaid",
            "graph TD",
            "    A[Large File/Content] --> B{Token Count}",
            "    B -->|>8k tokens| C[Split into Chunks]",
            "    B -->|<=8k tokens| D[Process Directly]",
            "    C --> E[Process Chunk 1]",
            "    C --> F[Process Chunk 2]",
            "    C --> G[Process Chunk N]",
            "    E --> H[Combine Results]",
            "    F --> H",
            "    G --> H",
            "    D --> I[Return Result]",
            "    H --> I",
            "    ",
            "    style C fill:#fff4e1",
            "    style H fill:#e8f5e9",
            "```",
            "",
            "**Result Combination**:",
            "",
            "- Individual chunk results are combined using LLM",
            "- Context from all chunks is preserved",
            "- Final result is comprehensive and coherent",
            "",
            "### Token Estimation Details",
            "",
            "**Estimation Formula**:",
            "```python",
            "estimated_tokens = len(content) * 0.25  # 4 chars per token",
            "```",
            "",
            "**Why This Works**:",
            "- Java/JavaScript code averages ~4 characters per token",
            "- Provides conservative estimates (safe buffer)",
            "- Accounts for whitespace, comments, and structure",
            "",
            "### Best Practices",
            "",
            "1. **Monitor Token Usage**:",
            "   - Log chunk sizes and token counts",
            "   - Track API call frequency",
            "   - Monitor rate limit errors",
            "",
            "2. **Optimize Chunk Sizes**:",
            "   - Adjust `max_chunk_tokens` based on provider/model",
            "   - Balance between context and cost",
            "   - Consider model-specific limits",
            "",
            "3. **Handle Rate Limits**:",
            "   - Implement exponential backoff",
            "   - Batch requests when possible",
            "   - Use async processing for large codebases",
            "",
            "---",
            "",
            "## Project Structure",
            "",
            "```",
            "converted-project/",
            "├── models/              # Sequelize models (JPA entities)",
            "├── repositories/         # Data access objects (Spring repositories)",
            "├── services/             # Business logic (Spring services)",
            "├── routes/              # Express routes (Spring controllers)",
            "├── config/              # Configuration files",
            "├── middleware/          # Express middleware",
            "├── server.js            # Main application entry point",
            "├── package.json         # Node.js dependencies",
            "├── .env                 # Environment variables",
            "├── .env.example         # Environment template",
            "├── .gitignore          # Git ignore rules",
            "└── README.md           # This file",
            "```",
            "",
            "### Directory Descriptions",
            "",
            "- **`models/`**: Sequelize model definitions converted from JPA `@Entity` classes",
            "- **`repositories/`**: Data access layer converted from Spring Data JPA repositories",
            "- **`services/`**: Business logic layer converted from Spring `@Service` classes",
            "- **`routes/`**: Express.js route handlers converted from Spring `@Controller` classes",
            "- **`config/`**: Application configuration (database, environment, etc.)",
            "- **`middleware/`**: Express middleware (error handling, authentication, etc.)",
            "",
            "---",
            "",
            "## Converted Modules",
            "",
            f"**Total modules converted: {len(modules)}**",
            "",
            "### Module Breakdown",
            ""
        ]
        
        # Add module counts by type
        if module_counts:
            lines.append("| Type | Count |")
            lines.append("|------|-------|")
            for module_type, count in sorted(module_counts.items()):
                lines.append(f"| {module_type} | {count} |")
            lines.append("")
        
        lines.append("### Module List")
        lines.append("")
        
        # Add module list
        for module in modules[:30]:  # Increased to 30
            module_name = module.get('name', 'Unknown')
            module_type = module.get('type', 'Unknown')
            description = module.get('description', '')
            methods_count = len(module.get('methods', []))
            
            lines.append(f"#### {module_name} ({module_type})")
            if description:
                lines.append(f"")
                lines.append(f"{description}")
            
            if methods_count > 0:
                lines.append(f"")
                lines.append(f"**Methods**: {methods_count}")
                
                # Show first few methods
                methods = module.get('methods', [])[:5]
                for method in methods:
                    method_name = method.get('name', 'Unknown')
                    signature = method.get('signature', '')
                    complexity = method.get('complexity', 'Unknown')
                    lines.append(f"- `{signature}` ({complexity} complexity)")
                
                if len(module.get('methods', [])) > 5:
                    remaining = len(module.get('methods', [])) - 5
                    lines.append(f"- ... and {remaining} more methods")
            
            dependencies = module.get('dependencies', [])
            if dependencies:
                lines.append(f"")
                lines.append(f"**Dependencies**: {', '.join(dependencies[:5])}")
                if len(dependencies) > 5:
                    lines.append(f"  ... and {len(dependencies) - 5} more")
            
            lines.append("")
        
        if len(modules) > 30:
            lines.append(f"*... and {len(modules) - 30} more modules*")
            lines.append("")
        
        lines.extend([
            "---",
            "",
            "## Output Format",
            "",
            "### Generated Files",
            "",
            "The conversion produces:",
            "",
            "1. **JavaScript/TypeScript Files**:",
            "   - All converted code in `models/`, `repositories/`, `services/`, `routes/`",
            "   - Proper ES6+ syntax with async/await",
            "   - JSDoc comments for documentation",
            "",
            "2. **Configuration Files**:",
            "   - `package.json`: Node.js dependencies and scripts",
            "   - `server.js`: Express.js application setup",
            "   - `.env.example`: Environment variable template",
            "   - Database configuration files",
            "",
            "3. **Metadata Files**:",
            "   - `project-metadata.json`: Structured project analysis",
            "   - Contains: project overview, module descriptions, method signatures, complexity, dependencies",
            "",
            "4. **Documentation**:",
            "   - `README.md`: This comprehensive documentation",
            "   - `.gitignore`: Git ignore rules",
            "",
            "### JSON Structured Output",
            "",
            "The `project-metadata.json` file contains structured information about the converted project:",
            "",
            "```json",
            "{",
            '  "projectOverview": "High-level description of the application",',
            '  "modules": [',
            "    {",
            '      "name": "CustomerService",',
            '      "description": "Service for customer management",',
            '      "type": "Service",',
            '      "methods": [',
            "        {",
            '          "name": "getCustomerById",',
            '          "signature": "public Customer getCustomerById(int id)",',
            '          "description": "Retrieves customer data by ID",',
            '          "complexity": "Low"',
            "        }",
            "      ],",
            '      "dependencies": ["CustomerRepository", "Customer"]',
            "    }",
            "  ]",
            "}",
            "```",
            "",
            "---",
            "",
            "## Conversion Details",
            "",
            "### Java → Node.js Mapping",
            "",
            "| Java (Spring Boot) | Node.js (Express) |",
            "|-------------------|-------------------|",
            "| `@RestController` | `express.Router()` |",
            "| `@GetMapping` | `router.get()` |",
            "| `@PostMapping` | `router.post()` |",
            "| `@Service` | ES6 Class |",
            "| `@Repository` | Sequelize DAO |",
            "| `@Entity` | Sequelize Model |",
            "| `JpaRepository<T, ID>` | Sequelize Model methods |",
            "| `@Autowired` | Constructor injection / require |",
            "| `ResponseEntity<T>` | `res.status().json()` |",
            "| `List<T>` | JavaScript Array |",
            "| `Optional<T>` | Null check or object |",
            "",
            "### Conversion Patterns",
            "",
            "1. **Synchronous → Asynchronous**:",
            "   - Java synchronous calls → JavaScript async/await",
            "   - Database operations use promises",
            "   - Service methods are async functions",
            "",
            "2. **Dependency Injection**:",
            "   - Spring `@Autowired` → Constructor injection",
            "   - Repository dependencies → require() statements",
            "   - Service dependencies → Constructor parameters",
            "",
            "3. **Error Handling**:",
            "   - Java exceptions → JavaScript try/catch",
            "   - Spring exception handlers → Express error middleware",
            "   - HTTP status codes preserved",
            "",
            "---",
            "",
            "## Troubleshooting",
            "",
            "### Common Issues",
            "",
            "1. **Module Not Found Errors**:",
            "   ```bash",
            "   npm install  # Reinstall dependencies",
            "   ```",
            "",
            "2. **Database Connection Errors**:",
            "   - Verify `.env` configuration",
            "   - Check database server is running",
            "   - Verify credentials and network access",
            "",
            "3. **Port Already in Use**:",
            "   ```bash",
            "   # Change PORT in .env or kill existing process",
            "   lsof -ti:3000 | xargs kill -9",
            "   ```",
            "",
            "4. **Missing Dependencies**:",
            "   - Check `package.json` for required packages",
            "   - Run `npm install` to install missing dependencies",
            "",
            "### Getting Help",
            "",
            "If you encounter issues:",
            "",
            "1. Check the error logs for detailed messages",
            "2. Verify all environment variables are set correctly",
            "3. Review the converted code for manual fixes needed",
            "4. Consult the original Java codebase for reference",
            "",
            "---",
            "",
            "## Additional Notes",
            "",
            "- This project was automatically converted from Java Spring Boot",
            "- Some manual adjustments may be required for production use",
            "- Review and test all endpoints before deploying to production",
            "- Consider adding comprehensive test coverage",
            "- Implement proper logging and monitoring",
            "- Set up CI/CD pipelines for automated deployments",
            "",
            "---",
            "",
            f"**Generated on**: {metadata.get('_generated_at', 'Unknown')}",
            f"**Conversion Tool**: Java-to-Node.js Conversion Agent",
            f"**Original Project**: {overview[:100]}...",
            ""
        ])
        
        readme_path = os.path.join(output_path, "README.md")
        with open(readme_path, 'w') as f:
            f.write("\n".join(lines))
        
        logger.info("Generated comprehensive README.md")
    
    def _generate_gitignore(self, output_path: str):
        """Generate .gitignore file"""
        
        gitignore_content = """node_modules/
.env
.DS_Store
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
dist/
build/
.coverage/
"""
        
        gitignore_path = os.path.join(output_path, ".gitignore")
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
        
        logger.info("Generated .gitignore")

