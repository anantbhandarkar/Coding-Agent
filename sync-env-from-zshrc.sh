#!/bin/bash
# Helper script to sync environment variables from .zshrc to .env file
# Usage: ./sync-env-from-zshrc.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# API key variables to look for
API_VARS=("GEMINI_API_KEY" "OPENROUTER_API_KEY" "OPENAI_API_KEY" "GLM_API_KEY" "GLM_BASE_URL")

# Find .zshrc or .bashrc
SHELL_PROFILE=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
    print_info "Found .zshrc at $SHELL_PROFILE"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_PROFILE="$HOME/.bashrc"
    print_info "Found .bashrc at $SHELL_PROFILE"
else
    print_warning "No .zshrc or .bashrc found. Cannot sync environment variables."
    exit 1
fi

# Extract export statements from shell profile
ENV_FILE=".env"
print_info "Syncing API keys from $SHELL_PROFILE to $ENV_FILE..."

# Backup existing .env if it exists
if [ -f "$ENV_FILE" ]; then
    BACKUP_FILE="${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$ENV_FILE" "$BACKUP_FILE"
    print_info "Backed up existing .env to $BACKUP_FILE"
fi

# Extract API key exports from shell profile
{
    echo "# Environment variables synced from $SHELL_PROFILE"
    echo "# Generated on: $(date)"
    echo "#"
    
    for var in "${API_VARS[@]}"; do
        # Extract export line for this variable
        export_line=$(grep -E "^export[[:space:]]+${var}=" "$SHELL_PROFILE" 2>/dev/null | head -1 || true)
        
        if [ -n "$export_line" ]; then
            # Extract just the variable=value part (remove 'export ')
            value_line=$(echo "$export_line" | sed 's/^export[[:space:]]*//')
            echo "$value_line"
            print_success "Found $var"
        else
            echo "# $var=not_found_in_${SHELL_PROFILE##*/}"
            print_warning "$var not found in $SHELL_PROFILE"
        fi
    done
    
    # Add other common Docker variables
    echo ""
    echo "# Optional Docker settings"
    echo "# API_PORT=8000"
    
} > "$ENV_FILE"

print_success "Created/updated $ENV_FILE"
print_info "You can now use './docker-run.sh start' and it will automatically load these variables"

