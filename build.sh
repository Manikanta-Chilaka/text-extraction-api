#!/usr/bin/env bash
set -e

echo "Installing system dependencies..."
apt-get update
apt-get install -y --no-install-recommends \
    python3-dev \
    build-essential \
    antiword \
    unrtf \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

echo "Installing Python packages..."
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

echo "Build complete!"