# Coding-Agent

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)
![Python](https://img.shields.io/badge/python-%3E%3D3.14-brightgreen.svg)
![Docker](https://img.shields.io/badge/docker-%3E%3D24.0-blue.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)

**An intelligent Python-based agentic application that automatically converts Java Spring Boot applications to Node.js/Express using advanced LLM-powered analysis and generation.**

[Features](#-features) •
[Quick Start](#-quick-start) •
[Documentation](#-documentation) •
[Architecture](#-architecture) •
[Contributing](#-contributing) •
[Support](#-support)

</div>

---

## 📑 Table of Contents

- [Features](#-features)
  - [Core Capabilities](#core-capabilities)
  - [Advanced Features](#-advanced-features)
  - [Workflow Architecture](#workflow-architecture)
- [Quick Start](#-quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Using the CLI](#using-the-cli)
  - [Using Docker](#using-docker)
- [Documentation](#-documentation)
  - [User Guides](#user-guides)
  - [Technical Documentation](#technical-documentation)
  - [Configuration Guides](#configuration-guides)
- [Architecture](#-architecture)
  - [Conversion Workflow](#conversion-workflow)
  - [Generated Output Structure](#generated-output-structure)
  - [System Components](#system-components)
- [Configuration](#-configuration)
  - [LLM Provider Configuration](#llm-provider-configuration)
  - [Environment Variables](#environment-variables)
  - [Multi-LLM Provider Strategy](#multi-llm-provider-strategy)
- [Monitoring & Status Tracking](#-monitoring--status-tracking)
- [Docker Services](#-docker-services)
- [Security Features](#-security-features)
- [Performance Optimization](#-performance-optimization)
- [API Reference](#-api-reference)
- [Use Cases](#-use-cases)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

---

## 🌟 Features

### Core Capabilities
- **Automatic Code Conversion**: Converts Spring Boot Java code to Node.js/Express
- **Multi-LLM Support**: Gemini, GLM, OpenAI, OpenRouter with multiple models
- **Intelligent Analysis**: Deep code analysis with architecture pattern detection
- **Database Migration**: Converts JPA entities to Sequelize models
- **API Mapping**: Translates REST controllers to Express routes
- **Quality Validation**: Automated syntax and code quality validation
- **Deployment Ready**: Generates Docker files and deployment guides
- **Codebase Ingestion**: Uses `gitingest` for intelligent codebase text consolidation

### 🎯 Advanced Features

- **📦 Docker-Compatible Output**: Generated code includes production-ready Dockerfile, docker-compose.yml, and .dockerignore
- **📝 Comprehensive Documentation**: All generated code includes detailed comments and explanations
- **📊 Metadata Generation**: 
  - Complete analysis of original Java codebase
  - Detailed metadata of converted Node.js code
- **🔄 Intelligent Chunking**: Advanced code segmentation with context preservation for large codebases
- **🎨 Multiple Framework Support**: 
  - Express.js with Sequelize ORM
  - NestJS with TypeORM
- **🔍 Real-time Status Monitoring**: Track conversion progress with detailed phase and file-level status
- **⚡ Safety Blocks**: Automatic detection and isolation of problematic code sections

### Workflow Architecture
- **Repository Cloning**: Automatic GitHub repository cloning
- **Codebase Ingestion**: Intelligent codebase text consolidation
- **Structure Analysis**: Classifies files (Controller, Service, Entity, etc.)
- **Metadata Extraction**: Extracts API endpoints, database entities, dependencies
- **Dependency Mapping**: Maps Java dependencies to npm packages
- **Code Conversion**: Converts models, repositories, services, controllers
- **Configuration Migration**: Generates Node.js configuration files
- **Project Generation**: Creates complete Node.js project structure
- **Validation**: Validates converted code for syntax and quality

Each component operates in an isolated context and returns aggregated results to the orchestrator.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.14+ (recommended)
- Git 2.39+
- Docker 24.0+ and Docker Compose 2.0+ (optional, for containerized execution)
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space
- At least one LLM API key (Gemini, OpenAI, GLM, OpenRouter)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/anantbhandarkar/Coding-Agent.git
cd Coding-Agent

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure LLM provider (see Configuration section below)
# Copy llm_config.json.example to llm_config.json and update with your API keys
cp llm_config.json.example llm_config.json
# Edit llm_config.json with your API keys

# 5. Verify installation
python run_conversion.py --help
```

**📘 [Complete setup guide →](./QUICK_START.md)**  
**🔧 [Environment setup guide →](./ENV_VARIABLES_SETUP.md)**  
**📝 [LLM configuration guide →](./LLM_CONFIG_GUIDE.md)**

### Using the CLI

```bash
# Activate virtual environment
source venv/bin/activate

# Convert using Gemini (with config profile)
python run_conversion.py \
  --github-url "https://github.com/owner/repo" \
  --profile glm-4-6-zai \
  --model "GLM-4.6" \
  --framework express \
  --orm sequelize

# Convert using OpenRouter with DeepSeek (free tier available)
python run_conversion.py \
  --github-url "https://github.com/owner/repo" \
  --provider openrouter \
  --api-token "YOUR_OPENROUTER_KEY" \
  --model "deepseek/deepseek-chat-v3.1:free" \
  --framework express \
  --orm sequelize

# Convert to NestJS with TypeORM
python run_conversion.py \
  --github-url "https://github.com/owner/repo" \
  --profile openrouter-deepseek \
  --model "deepseek/deepseek-chat-v3.1:free" \
  --framework nestjs \
  --orm typeorm

# Specify custom output directory
python run_conversion.py \
  --github-url "https://github.com/owner/repo" \
  --profile glm-4-6-zai \
  --model "GLM-4.6" \
  --output "/path/to/output"
```

**⚡ [Quick reference commands →](./USAGE.md)**

### Using Docker

```bash
# Using docker-run.sh script
./docker-run.sh convert \
  --github-url "https://github.com/owner/repo" \
  --profile glm-4-6-zai \
  --output "/path/to/output"

# Using build-and-run script
./build-and-run.sh

# Using docker-compose directly
docker-compose up
```

**🐳 [Docker setup guide →](./DOCKER_QUICKSTART.md)**

### Using the API Server

```bash
# Start the API server
python -m src.api.server

# Server starts on http://localhost:8000
# Access web UI at http://localhost:8000
```

Then make a POST request to `/api/convert`:

```bash
curl -X POST "http://localhost:8000/api/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "github_url": "https://github.com/owner/repo",
    "provider": "gemini",
    "api_token": "YOUR_API_TOKEN",
    "model": "gemini-2.5-flash",
    "target_framework": "express",
    "orm_choice": "sequelize"
  }'
```

**📘 [Complete API usage guide →](./USAGE.md)**

---

## 📚 Documentation

### User Guides

| Guide | Description | Link |
|-------|-------------|------|
| **Quick Start** | Complete setup and first conversion | [QUICK_START.md](./QUICK_START.md) |
| **Usage Guide** | Detailed usage instructions and examples | [USAGE.md](./USAGE.md) |
| **Environment Setup** | API key configuration and environment management | [ENV_VARIABLES_SETUP.md](./ENV_VARIABLES_SETUP.md) |
| **LLM Configuration** | Multi-LLM provider configuration guide | [LLM_CONFIG_GUIDE.md](./LLM_CONFIG_GUIDE.md) |

### Technical Documentation

| Document | Description | Link |
|----------|-------------|------|
| **Docker Setup** | Docker containerization and deployment | [DOCKER.md](./DOCKER.md) |
| **Docker Quickstart** | Quick Docker setup guide | [DOCKER_QUICKSTART.md](./DOCKER_QUICKSTART.md) |
| **Docker Setup Complete** | Complete Docker deployment guide | [DOCKER_SETUP_COMPLETE.md](./DOCKER_SETUP_COMPLETE.md) |
| **GitHub MCP Setup** | GitHub Model Context Protocol setup | [GITHUB_MCP_SETUP.md](./GITHUB_MCP_SETUP.md) |

---

## 🏗️ Architecture

### Conversion Workflow

```
┌─────────────────────────────────────────────┐
│     ORCHESTRATOR (Main Coordinator)         │
│  - Manages workflow execution               │
│  - Spawns nodes with isolated context      │
│  - Aggregates results from all nodes        │
│  - Handles multi-LLM provider switching     │
│  - Tracks execution status                  │
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┼──────────┬──────────┬─────────┐
    ▼          ▼          ▼          ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Clone  │ │ Ingest │ │Analyze │ │Convert │ │Validate│
│ Repo   │ │Codebase│ │Structure│ │ Code   │ │ Result │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

### Conversion Workflow Steps

1. **Repository Cloning** (`clone_repo`)
   - Clones Spring Boot repository from GitHub
   - Extracts repository path and branch information

2. **Codebase Ingestion** (`ingest_codebase`)
   - Uses `gitingest` for intelligent codebase text consolidation
   - Creates a single comprehensive text file of the entire codebase
   - Maintains file mappings for reference

3. **Structure Analysis** (`analyze_structure`)
   - Classifies files (Controller, Service, Entity, Repository, etc.)
   - Extracts API endpoints
   - Maps database entities
   - Analyzes dependencies
   - Identifies build system (Maven, Gradle)

4. **Metadata Extraction** (`extract_metadata`)
   - Extracts comprehensive metadata from analyzed structure
   - Creates structured metadata JSON
   - Maps relationships between components

5. **Dependency Mapping** (`map_dependencies`)
   - Maps Java dependencies to npm packages
   - Creates package.json structure
   - Identifies equivalent Node.js libraries

6. **Model Conversion** (`convert_models`)
   - Converts JPA entities to Sequelize/TypeORM models
   - Preserves relationships and annotations
   - Generates database schemas

7. **Repository Conversion** (`convert_repositories`)
   - Converts Spring Data repositories to Sequelize/TypeORM repositories
   - Maps query methods to Node.js equivalents
   - Preserves custom queries

8. **Service Conversion** (`convert_services`)
   - Converts Spring service classes to Node.js service modules
   - Preserves business logic
   - Maps dependency injection patterns

9. **Controller Conversion** (`convert_controllers`)
   - Translates Spring REST controllers to Express routes
   - Maps annotations and request/response handling
   - Generates route handlers

10. **Configuration Migration** (`generate_config`)
    - Generates database configuration files
    - Creates application configuration
    - Sets up environment variables

11. **Project Generation** (`generate_project`)
    - Creates complete Node.js project structure
    - Generates package.json, Dockerfile, docker-compose.yml
    - Creates README and deployment guides

12. **Validation** (`validate`)
    - Validates JavaScript/TypeScript syntax
    - Checks code quality
    - Verifies dependencies
    - Generates validation report

### Generated Output Structure

```
output/{conversion-id}/
├── codebase.txt                 # Consolidated codebase text
├── config/
│   └── database.js             # Database configuration
├── models/                      # Sequelize/TypeORM models
│   ├── Actor.js
│   ├── Category.js
│   └── ...
├── repositories/                # Repository layer
│   ├── ActorRepository.js
│   └── ...
├── services/                    # Business logic layer
│   ├── ActorService.js
│   └── ...
├── routes/                       # Express routes/controllers
│   ├── actorcontroller.js
│   └── ...
├── server.js                    # Main application entry
├── package.json                 # Dependencies
├── project-metadata.json        # Conversion metadata
└── README.md                    # Setup instructions
```

### System Components

**Core Modules:**
- `src/agents/orchestrator.py` - Main workflow orchestrator using LangGraph
- `src/analyzers/repository_analyzer.py` - Code structure analysis
- `src/extractors/metadata_extractor.py` - Metadata extraction
- `src/mappers/dependency_mapper.py` - Dependency mapping
- `src/converters/` - Code conversion modules
  - `model_converter.py` - Entity to model conversion
  - `repository_converter.py` - Repository conversion
  - `service_converter.py` - Service conversion
  - `controller_converter.py` - Controller to route conversion
- `src/migrators/config_migrator.py` - Configuration migration
- `src/generators/project_generator.py` - Project structure generation
- `src/validators/conversion_validator.py` - Code validation

**LLM Client Modules:**
- `src/clients/base_llm_client.py` - Base LLM client interface
- `src/clients/gemini_client.py` - Google Gemini client
- `src/clients/glm_client.py` - GLM/Z.AI client
- `src/clients/openai_client.py` - OpenAI client
- `src/clients/openrouter_client.py` - OpenRouter client
- `src/clients/llm_client_factory.py` - Client factory

**Supporting Modules:**
- `src/config/llm_config_manager.py` - LLM configuration management
- `src/utils/chunking.py` - Intelligent code chunking
- `src/api/server.py` - FastAPI web server

---

## 🔧 Configuration

### LLM Provider Configuration

The system supports multiple LLM providers through configuration profiles in `llm_config.json`:

```json
{
  "providers": {
    "glm-4-6-zai": {
      "provider": "glm",
      "api_key": "${GLM_API_KEY}",
      "model": "GLM-4.6",
      "base_url": "https://api.z.ai/api/coding/paas/v4"
    },
    "openrouter-deepseek": {
      "provider": "openrouter",
      "api_key": "${OPENROUTER_API_KEY}",
      "base_url": "https://openrouter.ai/api/v1",
      "model": "deepseek/deepseek-chat-v3.1:free"
    },
    "openai-custom": {
      "provider": "openai",
      "api_key": "${OPENAI_API_KEY}",
      "base_url": "https://api.openai.com/v1/responses",
      "model": "gpt-4o"
    }
  },
  "default_profile": "openrouter-deepseek"
}
```

**📘 [Complete LLM configuration guide →](./LLM_CONFIG_GUIDE.md)**

### Environment Variables

Set environment variables for API keys (used in `llm_config.json`):

```bash
# GLM API Key
export GLM_API_KEY="your_glm_api_key"

# OpenRouter API Key
export OPENROUTER_API_KEY="your_openrouter_api_key"

# OpenAI API Key
export OPENAI_API_KEY="your_openai_api_key"

# Gemini API Key (if using directly)
export GEMINI_API_TOKEN="your_gemini_api_token"
```

**📘 [Complete environment setup guide →](./ENV_VARIABLES_SETUP.md)**

### Multi-LLM Provider Strategy

The system supports runtime LLM provider switching:
- **Profile-based**: Use `--profile` flag with profiles from `llm_config.json`
- **Direct Provider**: Use `--provider` flag with direct API token
- **Fallback Support**: Automatic fallback to alternative providers on errors

**Supported Providers:**
- **Gemini**: Google's Gemini models (gemini-2.5-flash, gemini-1.5-flash)
- **GLM**: Z.AI GLM models (GLM-4.6)
- **OpenAI**: OpenAI models (gpt-4o, gpt-4-turbo)
- **OpenRouter**: Access to multiple models including DeepSeek, Claude, etc.

---

## 📊 Monitoring & Status Tracking

### Real-time Status Monitoring

The orchestrator provides real-time status tracking:

```python
from src.agents.orchestrator import get_execution_status

status = get_execution_status()
# Returns:
# {
#   "current_phase": "convert_controllers",
#   "current_file": "UserController.java",
#   "progress_percentage": 75,
#   "files_processed": 15,
#   "files_total": 20,
#   "safety_blocks": [...],
#   "errors": [...]
# }
```

### Status Output

When running conversions, you'll see real-time status updates:

```
[75%] convert_controllers - UserController.java [⚠️  2 safety blocks]
```

**Safety Blocks**: Code sections that couldn't be converted automatically, requiring manual review.

---

## 🐳 Docker Services

The application can run in Docker containers for isolated execution:

```bash
# Build and run
docker-compose build
docker-compose up

# Or use the convenience script
./docker-run.sh convert --github-url "https://github.com/owner/repo" --profile glm-4-6-zai
```

**🐳 [Complete Docker setup guide →](./DOCKER.md)**

---

## 🔒 Security Features

- **Secure API Key Management**: Uses environment variables and configuration files
- **Code Sanitization**: Sanitizes code before LLM processing
- **Secure File Handling**: Secure temporary file management
- **Input Validation**: Validates all inputs and GitHub URLs
- **Docker Isolation**: Containerized execution for security

**Security Best Practices:**
- Never commit API keys to version control
- Use environment variables for sensitive data
- Review generated code before deployment
- Validate all converted outputs

---

## 📈 Performance Optimization

### Intelligent Code Chunking

- **Smart Segmentation**: Advanced code segmentation with context preservation
- **Token-Aware Processing**: Automatic limit calculation per LLM provider
- **Semantic Splitting**: Respects code boundaries (classes, methods)
- **Batch Optimization**: Intelligent grouping with parallel processing

### Resource Efficiency

- **Parallel Processing**: Multiple files analyzed concurrently
- **Memory Management**: Optimized for large codebases without overflow
- **Progress Tracking**: Real-time conversion progress with detailed logging
- **Error Recovery**: Graceful handling of failures with safety blocks

---

## 📝 API Reference

### Start Conversion

```http
POST /api/convert
Content-Type: application/json

{
  "github_url": "https://github.com/user/repo",
  "provider": "gemini",
  "api_token": "YOUR_API_TOKEN",
  "model": "gemini-2.5-flash",
  "target_framework": "express",
  "orm_choice": "sequelize"
}
```

### Get Status

```http
GET /api/convert/{job_id}
```

### Get Metadata

```http
GET /api/convert/{job_id}/metadata
```

### Download Result

```http
GET /api/convert/{job_id}/download
```

---

## 🎯 Use Cases

1. **Microservices Migration**: Convert Spring Boot microservices to Node.js
2. **Technology Stack Modernization**: Move from Java to JavaScript ecosystem
3. **Rapid Prototyping**: Quick Node.js version of existing Spring Boot app
4. **Learning Tool**: Understand code conversion patterns and best practices
5. **Multi-Framework Exploration**: Easily compare Express vs NestJS implementations

---

## 🛠️ Troubleshooting

### Common Issues

**Issue: LLM API errors**
```bash
# Check API keys
echo $GLM_API_KEY
echo $OPENROUTER_API_KEY

# Test connection
python -c "from src.clients.llm_client_factory import create_llm_client_from_config; client = create_llm_client_from_config({...}); print('OK')"
```

**Issue: Memory issues**
```bash
# Reduce concurrent processing in code
# Or increase system memory allocation
```

**Issue: Conversion failures**
```bash
# Check safety blocks in output
# Review validation errors
# Ensure GitHub repository is accessible
```

**Issue: Docker problems**
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up
```

**📘 [Complete troubleshooting guide →](./QUICK_START.md#troubleshooting)**

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository** and create a feature branch
2. **Make your changes** following our coding standards:
   - Python 3.14+ with type hints
   - Async/await for async operations
   - Comprehensive docstrings
   - Use `logging` (not `print`)
3. **Add tests** and ensure all tests pass
4. **Submit a pull request** with a clear description

### Coding Standards
- Follow PEP 8 style guide
- Use type hints for all functions
- Add docstrings to all modules and functions
- Write tests for new features
- Update documentation for changes

**💡 First time contributing?** Check out open issues labeled `good first issue`

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details (if applicable).

---

## 🙏 Acknowledgments

- Built with [LangGraph](https://langchain-ai.github.io/langgraph/) for workflow orchestration
- Powered by multiple LLM providers (Gemini, GLM, OpenAI, OpenRouter)
- Uses [gitingest](https://github.com/anantbhandarkar/gitingest) for intelligent codebase ingestion
- FastAPI for web API server
- Inspired by modern agentic frameworks and code conversion tools

---



### Get Help

- **📖 Documentation**: Start with [QUICK_START.md](./QUICK_START.md)
- **🐛 Bug Reports**: Open an issue on GitHub
- **💡 Feature Requests**: Open a feature request issue
- **❓ Questions**: Open a discussion on GitHub

### Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/anantbhandarkar/Coding-Agent/issues)
- **GitHub Discussions**: [Ask questions and share ideas](https://github.com/anantbhandarkar/Coding-Agent/discussions)
- **Pull Requests**: [Contribute code and improvements](https://github.com/anantbhandarkar/Coding-Agent/pulls)

### Project Information

- **Version**: 1.0.0
- **Status**: Production Ready ✅
- **Last Updated**: 2025-11-02
- **Maintained**: Actively maintained

---

<div align="center">

**Made with ❤️ by the Anant Bhandarkar**

[⬆ Back to top](#coding-agent)

</div>

