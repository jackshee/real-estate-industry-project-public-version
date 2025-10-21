#!/bin/bash

# MAST30034 Project 2 - Virtual Environment Setup Script for macOS/Linux
# This script sets up a Python virtual environment for the project

set -e  # Exit on any error

echo "🏠 MAST30034 Project 2 - Virtual Environment Setup"
echo "=================================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3 from https://python.org or using Homebrew:"
    echo "  brew install python"
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "✅ Found Python $PYTHON_VERSION"

# Check if we're in the project directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

echo "✅ Found requirements.txt"

# Remove existing virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔄 Removing existing virtual environment..."
    rm -rf venv
fi

# Create new virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing project dependencies..."
pip install -r requirements.txt

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Start Jupyter Lab:"
echo "   jupyter lab"
echo ""
echo "3. Or run notebooks directly:"
echo "   jupyter notebook"
echo ""
echo "4. When you're done, deactivate the environment:"
echo "   deactivate"
echo ""
echo "💡 Tip: You can also run 'source venv/bin/activate' in any terminal"
echo "   session to activate the environment for that session."

