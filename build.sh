#!/bin/bash
set -e  # Detiene el script si hay algún error

echo "=== Current directory ==="
pwd
ls -la

echo "=== Installing Python dependencies ==="
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "=== Installing Node dependencies ==="
npm install

echo "=== Building React app ==="
npm run build

echo "=== Verifying build structure ==="
echo "Contents of project root:"
ls -la

echo "--- Contents of dist/:"
ls -la dist/

echo "--- Detailed contents:"
find dist/ -type f | head -20

echo "=== Build completed successfully ==="