#!/bin/bash

# Sentinel-1 Flood Detection Script - Setup for Linux/macOS
# This script automates the setup process for the Sentinel-1 analysis workflow

set -e  # Exit on error

echo "================================"
echo "Sentinel-1 Script Setup"
echo "================================"
echo ""

# Check if Python 3 is installed
echo "1. Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org/ or your package manager"
    exit 1
fi
python3 --version
echo "✓ Python found"
echo ""

# Create virtual environment
echo "2. Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "   Virtual environment already exists, skipping creation"
else
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "3. Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install requirements
echo "4. Installing Python dependencies..."
pip install --upgrade pip > /dev/null 2>&1 || true
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
echo "5. Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "   ⚠ .env file created from .env.example"
    echo "   Please edit .env and update SNAP_DIRECTORY with your SNAP installation path"
else
    echo "   .env file already exists"
fi
echo ""

# Detect SNAP installation
echo "6. Detecting SNAP installation..."
SNAP_DIR=""
for path in "/opt/snap" "/snap/snap" "$HOME/snap" "$HOME/esa-snap"; do
    if [ -f "$path/bin/gpt" ]; then
        echo "   ✓ Found SNAP at: $path"
        SNAP_DIR="$path"
        break
    fi
done

if [ -z "$SNAP_DIR" ]; then
    echo "   ⚠ SNAP not found in standard locations"
    echo "   Please ensure SNAP is installed and update SNAP_DIRECTORY in .env"
fi

echo ""

# Create data directories
echo "7. Creating data directories..."
for dir in "data" "data/products" "data/region_of_interest" "out"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "   Created: $dir"
    else
        echo "   Already exists: $dir"
    fi
done
echo ""

# Test imports
echo "8. Testing Python imports..."
python -c "
import sys
try:
    from dotenv import load_dotenv
    print('   ✓ python-dotenv imported')
except ImportError as e:
    print(f'   ✗ python-dotenv import failed: {e}')
    sys.exit(1)
" 2>&1 || true

echo ""

# Summary
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Edit .env and verify SNAP_DIRECTORY points to your SNAP installation"
echo "2. Add Sentinel-1 products to: data/products/"
echo "3. Add a region of interest shapefile to: data/region_of_interest/"
echo "4. Run: python main.py"
echo ""
echo "For more information, see SETUP.md"
echo ""
