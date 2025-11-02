#!/bin/bash
# Quick script to run a converted Node.js project
# Usage: ./run_converted_project.sh /path/to/converted/project

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 /path/to/converted/project"
    echo ""
    echo "Example:"
    echo "  $0 /tmp/conversion-output-XXXXX"
    echo ""
    echo "To find recent conversions:"
    echo "  ls -lt /tmp/conversion-output-*"
    exit 1
fi

PROJECT_DIR="$1"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Directory not found: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

echo "=========================================="
echo "Setting up converted project"
echo "=========================================="
echo "Directory: $PROJECT_DIR"
echo ""

# Check if it's NestJS or Express
if [ -f "package.json" ]; then
    # Check if TypeScript/NestJS
    if grep -q "@nestjs/core" package.json 2>/dev/null || [ -d "src" ] && [ -f "tsconfig.json" ]; then
        echo "Detected: NestJS project"
        echo ""
        
        # Install dependencies
        echo "Installing dependencies..."
        npm install
        
        # Check for .env
        if [ ! -f ".env" ]; then
            echo ""
            echo "⚠️  Warning: .env file not found. Creating template..."
            cat > .env << EOF
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=sakila
DB_USER=root
DB_PASSWORD=your_password

# Server Configuration
PORT=3000
NODE_ENV=development

# JWT Configuration
JWT_SECRET=your-secret-key
JWT_EXPIRATION=24h
EOF
            echo "Created .env template. Please update with your database credentials."
            echo ""
        fi
        
        # Build if TypeScript
        if [ -f "tsconfig.json" ]; then
            echo "Building TypeScript..."
            npm run build 2>/dev/null || echo "Build skipped (may not be configured)"
        fi
        
        echo ""
        echo "=========================================="
        echo "Starting NestJS server..."
        echo "=========================================="
        echo ""
        npm run start:dev || npm run start || npm start
        
    else
        echo "Detected: Express project"
        echo ""
        
        # Install dependencies
        echo "Installing dependencies..."
        npm install
        
        # Check for .env
        if [ ! -f ".env" ]; then
            echo ""
            echo "⚠️  Warning: .env file not found. Creating template..."
            cat > .env << EOF
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=sakila
DB_USER=root
DB_PASSWORD=your_password

# Server Configuration
PORT=3000
NODE_ENV=development

# JWT Configuration
JWT_SECRET=your-secret-key
JWT_EXPIRATION=24h
EOF
            echo "Created .env template. Please update with your database credentials."
            echo ""
        fi
        
        echo ""
        echo "=========================================="
        echo "Starting Express server..."
        echo "=========================================="
        echo ""
        npm run dev || npm start
    fi
else
    echo "Error: package.json not found in $PROJECT_DIR"
    exit 1
fi



