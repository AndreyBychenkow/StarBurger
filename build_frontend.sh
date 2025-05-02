#!/bin/bash

# Strict mode
set -euo pipefail

# Variables
FRONTEND_DIR=$(dirname "$0")
ENTRY_POINTS=("bundles-src/index.js")

echo ">>> Building frontend assets"

# Go to the project directory
cd "$FRONTEND_DIR"

# Install dependencies if package.json exists
if [ -f "package.json" ]; then
    echo ">>> Installing Node.js dependencies"
    npm ci
fi

# Build each entry point
if [ ${#ENTRY_POINTS[@]} -gt 0 ]; then
    echo ">>> Found ${#ENTRY_POINTS[@]} entry points, building sequentially"
    
    for entry_point in "${ENTRY_POINTS[@]}"; do
        entry_name=$(basename "$entry_point" .js)
        echo ">>> Building $entry_name"
        
        npx parcel build "$entry_point" -d bundles --public-url /static/ || {
            echo ">>> Failed to build $entry_name"
            exit 1
        }
    done
    
    echo ">>> Frontend assets built successfully"
else
    echo ">>> No entry points found, skipping build"
fi 