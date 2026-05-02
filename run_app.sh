#!/bin/bash

# TrashWatch - Quick Start Script

echo "🗑️  TrashWatch - Starting Application..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if secrets are configured
if grep -q "YOUR_PROJECT_ID" .streamlit/secrets.toml; then
    echo "⚠️  WARNING: Supabase credentials not configured!"
    echo "📋 Please follow these steps:"
    echo "1. Go to supabase.com and create a project"
    echo "2. Copy your API credentials"
    echo "3. Edit .streamlit/secrets.toml with your credentials"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🚀 Starting Streamlit app..."
echo "📱 Open your browser to http://localhost:8501"
echo "⏹️  Press Ctrl+C to stop"
echo ""

streamlit run app.py
