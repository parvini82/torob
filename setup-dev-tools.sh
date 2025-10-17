#!/bin/bash

# Setup script for development tools
echo "Setting up development tools for Torob project..."

# Install Python development dependencies
echo "Installing Python development dependencies..."
pip install -r requirements.txt

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Setup frontend
echo "Setting up frontend development tools..."
cd frontend

# Install frontend dependencies
npm install

# Setup Husky (skip for now due to monorepo structure)
echo "Husky setup skipped - using pre-commit hooks for git hooks instead"

cd ..

echo "Development tools setup complete!"
echo ""
echo "Available commands:"
echo "Frontend:"
echo "  npm run lint          - Run ESLint"
echo "  npm run lint:fix      - Run ESLint with auto-fix"
echo "  npm run format        - Run Prettier"
echo "  npm run format:check  - Check Prettier formatting"
echo "  npm run type-check    - Run TypeScript type checking"
echo ""
echo "Backend:"
echo "  black .               - Format Python code with Black"
echo "  isort .               - Sort Python imports"
echo "  mypy .                - Run type checking"
echo "  flake8 .              - Run linting"
echo ""
echo "Pre-commit hooks are now active for both frontend and backend!"
