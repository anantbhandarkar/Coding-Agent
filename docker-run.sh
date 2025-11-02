#!/bin/bash
# Quick Docker execution helper script for Java to Node.js Conversion Agent

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to load environment variables from shell profile
load_env_vars() {
    # List of API key variables to look for
    local api_vars=("GEMINI_API_KEY" "OPENROUTER_API_KEY" "OPENAI_API_KEY" "GLM_API_KEY" "GLM_BASE_URL")
    local loaded_count=0
    
    # Check if .env file exists first (takes precedence)
    if [ -f ".env" ]; then
        set -a  # Automatically export all variables
        source .env 2>/dev/null || true
        set +a
        print_info "Loaded environment variables from .env file"
        return
    fi
    
    # Check if variables are already exported in current shell
    for var in "${api_vars[@]}"; do
        if [ -n "${!var}" ]; then
            ((loaded_count++))
        fi
    done
    
    if [ "$loaded_count" -gt 0 ]; then
        print_info "Found $loaded_count environment variable(s) already exported in current shell"
        return
    fi
    
    # Try to load from .zshrc (macOS default)
    if [ -f "$HOME/.zshrc" ]; then
        while IFS= read -r line; do
            # Skip comments and empty lines
            [[ "$line" =~ ^[[:space:]]*# ]] && continue
            [[ -z "$line" ]] && continue
            
            # Extract export statements for our API keys
            if [[ "$line" =~ ^export[[:space:]]+([A-Z_]+)= ]]; then
                var_name="${BASH_REMATCH[1]}"
                # Check if this is one of our API key variables
                for api_var in "${api_vars[@]}"; do
                    if [ "$var_name" = "$api_var" ]; then
                        # Export the variable safely
                        eval "$line" 2>/dev/null && ((loaded_count++)) || true
                        break
                    fi
                done
            fi
        done < <(grep -E "^export[[:space:]]+(GEMINI_API_KEY|OPENROUTER_API_KEY|OPENAI_API_KEY|GLM_API_KEY|GLM_BASE_URL)=" "$HOME/.zshrc" 2>/dev/null || true)
    fi
    
    # Also try .bashrc if .zshrc didn't work or no variables found
    if [ "$loaded_count" -eq 0 ] && [ -f "$HOME/.bashrc" ]; then
        while IFS= read -r line; do
            [[ "$line" =~ ^[[:space:]]*# ]] && continue
            [[ -z "$line" ]] && continue
            
            if [[ "$line" =~ ^export[[:space:]]+([A-Z_]+)= ]]; then
                var_name="${BASH_REMATCH[1]}"
                for api_var in "${api_vars[@]}"; do
                    if [ "$var_name" = "$api_var" ]; then
                        eval "$line" 2>/dev/null && ((loaded_count++)) || true
                        break
                    fi
                done
            fi
        done < <(grep -E "^export[[:space:]]+(GEMINI_API_KEY|OPENROUTER_API_KEY|OPENAI_API_KEY|GLM_API_KEY|GLM_BASE_URL)=" "$HOME/.bashrc" 2>/dev/null || true)
    fi
    
    if [ "$loaded_count" -gt 0 ]; then
        print_info "Loaded $loaded_count environment variable(s) from shell profile"
    else
        print_warning "No API keys found in shell profile or current shell."
        print_info "Run './sync-env-from-zshrc.sh' to create .env file, or export variables manually"
    fi
}

# Load environment variables at startup
load_env_vars

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Function to check if container is running
is_running() {
    docker ps --format '{{.Names}}' | grep -q "^java-to-nodejs-converter$"
}

# Function to build image
build_image() {
    print_info "Building Docker image..."
    docker build -t java-to-nodejs-converter .
    print_success "Image built successfully!"
}

# Function to start API server
start_api() {
    if is_running; then
        print_warning "Container is already running. Stop it first with: ./docker-run.sh stop"
        return
    fi
    
    print_info "Starting API server..."
    
    # Create necessary directories
    mkdir -p outputs tmp
    
    # Use docker-compose if available, otherwise docker compose
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        docker compose up -d
    fi
    
    print_success "API server started!"
    print_info "Web UI: http://localhost:8000"
    print_info "API Docs: http://localhost:8000/docs"
    print_info "View logs: ./docker-run.sh logs"
}

# Function to stop container
stop_container() {
    print_info "Stopping container..."
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    else
        docker compose down
    fi
    print_success "Container stopped!"
}

# Function to view logs
view_logs() {
    if command -v docker-compose &> /dev/null; then
        docker-compose logs -f
    else
        docker compose logs -f
    fi
}

# Function to run CLI conversion
run_conversion() {
    if [ -z "$1" ]; then
        echo "Usage: ./docker-run.sh convert --github-url <url> [options]"
        echo ""
        echo "Example:"
        echo "  ./docker-run.sh convert \\"
        echo "    --github-url \"https://github.com/owner/repo\" \\"
        echo "    --profile glm-4-6-zai \\"
        echo "    --output \"/path/to/output\""
        exit 1
    fi
    
    # Create necessary directories
    mkdir -p outputs tmp
    
    # Parse arguments to find --output and mount it
    OUTPUT_DIR=""
    DOCKER_ARGS=()
    SKIP_NEXT=false
    
    for arg in "$@"; do
        if [ "$SKIP_NEXT" = true ]; then
            OUTPUT_DIR="$arg"
            # Create the output directory if it doesn't exist
            mkdir -p "$OUTPUT_DIR"
            # Mount it as a volume at /app/custom-output
            DOCKER_ARGS+=("-v" "$OUTPUT_DIR:/app/custom-output")
            SKIP_NEXT=false
            # Transform --output argument to use container path
            DOCKER_ARGS+=("--output" "/app/custom-output")
        elif [ "$arg" = "--output" ]; then
            SKIP_NEXT=true
        else
            # Pass through all other arguments
            DOCKER_ARGS+=("$arg")
        fi
    done
    
    print_info "Running conversion..."
    
    docker run --rm \
        -v "$(pwd)/outputs:/app/outputs" \
        -v "$(pwd)/tmp:/app/tmp" \
        ${OUTPUT_DIR:+-v "$OUTPUT_DIR:/app/custom-output"} \
        -v "$(pwd)/llm_config.json:/app/llm_config.json:ro" \
        -e GEMINI_API_KEY="${GEMINI_API_KEY:-}" \
        -e OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}" \
        -e OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
        -e GLM_API_KEY="${GLM_API_KEY:-}" \
        -e GLM_BASE_URL="${GLM_BASE_URL:-}" \
        java-to-nodejs-converter \
        python run_conversion.py "${DOCKER_ARGS[@]}"
}

# Function to show status
show_status() {
    if is_running; then
        print_success "Container is running"
        docker ps --filter "name=java-to-nodejs-converter"
        echo ""
        print_info "Health check:"
        curl -s http://localhost:8000/docs > /dev/null && print_success "API is healthy" || print_warning "API health check failed"
    else
        print_warning "Container is not running"
    fi
}

# Function to open shell in container
shell() {
    docker exec -it java-to-nodejs-converter /bin/bash || \
    docker run --rm -it \
        -v "$(pwd)/outputs:/app/outputs" \
        -v "$(pwd)/tmp:/app/tmp" \
        java-to-nodejs-converter /bin/bash
}

# Function to clean up
clean() {
    print_info "Cleaning up containers and images..."
    docker-compose down --rmi local -v 2>/dev/null || docker compose down --rmi local -v 2>/dev/null || true
    print_success "Cleanup complete!"
}

# Function to show help
show_help() {
    echo "Java to Node.js Conversion Agent - Docker Helper"
    echo ""
    echo "Usage: ./docker-run.sh <command> [options]"
    echo ""
    echo "Commands:"
    echo "  build              Build Docker image"
    echo "  start              Start API server (default)"
    echo "  stop               Stop running container"
    echo "  restart            Restart container"
    echo "  logs               View container logs"
    echo "  status             Show container status"
    echo "  convert [args]     Run CLI conversion (pass conversion args)"
    echo "  shell              Open bash shell in container"
    echo "  clean              Stop and remove containers/images"
    echo "  help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./docker-run.sh start                    # Start API server"
    echo "  ./docker-run.sh convert --github-url ... # Run conversion"
    echo "  ./docker-run.sh logs                     # View logs"
    echo ""
    echo "Environment variables (set in .env or export):"
    echo "  GEMINI_API_KEY, OPENROUTER_API_KEY, etc."
}

# Main command handling
case "${1:-help}" in
    build)
        build_image
        ;;
    start|up)
        start_api
        ;;
    stop|down)
        stop_container
        ;;
    restart)
        stop_container
        sleep 2
        start_api
        ;;
    logs)
        view_logs
        ;;
    status)
        show_status
        ;;
    convert)
        shift
        run_conversion "$@"
        ;;
    shell|bash)
        shell
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run './docker-run.sh help' for usage information"
        exit 1
        ;;
esac

