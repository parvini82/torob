# Development Tools Guide

This document provides detailed information about the development tools configured for the Torob project.

## 🔧 Tool Overview

### Frontend Tools

| Tool       | Purpose         | Configuration File | Command              |
| ---------- | --------------- | ------------------ | -------------------- |
| TypeScript | Type checking   | `tsconfig.json`    | `npm run type-check` |
| ESLint     | Code linting    | `.eslintrc.json`   | `npm run lint`       |
| Prettier   | Code formatting | `.prettierrc`      | `npm run format`     |
| Husky      | Git hooks       | `.husky/`          | Auto on commit       |

### Backend Tools

| Tool   | Purpose         | Configuration File | Command    |
| ------ | --------------- | ------------------ | ---------- |
| Black  | Code formatting | `pyproject.toml`   | `black .`  |
| isort  | Import sorting  | `pyproject.toml`   | `isort .`  |
| mypy   | Type checking   | `mypy.ini`         | `mypy .`   |
| flake8 | Code linting    | `.flake8`          | `flake8 .` |

## 📋 Configuration Details

### TypeScript Configuration (`tsconfig.json`)

- Target: ES5 with modern features
- Strict mode enabled
- Path mapping for `@/*` imports
- Excludes node_modules and build directories

### ESLint Configuration (`.eslintrc.json`)

- Extends Next.js recommended rules
- TypeScript support
- Prettier integration
- Custom rules for unused variables and React hooks

### Prettier Configuration (`.prettierrc`)

- Single quotes
- Semicolons
- 80 character line length
- 2-space indentation
- LF line endings

### Black Configuration (`pyproject.toml`)

- 88 character line length
- Python 3.9+ target
- Excludes notebooks directory

### mypy Configuration (`mypy.ini`)

- Strict type checking
- Excludes notebooks and tests
- Ignores missing imports for third-party libraries

## 🚀 Quick Commands

### Frontend

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Code quality checks
npm run lint          # ESLint
npm run lint:fix      # ESLint with auto-fix
npm run format        # Prettier
npm run format:check  # Check formatting
npm run type-check    # TypeScript
```

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Code quality checks
black .      # Format code
isort .      # Sort imports
mypy .       # Type checking
flake8 .     # Linting

# Run pre-commit hooks
pre-commit run --all-files
```

## 🔗 Pre-commit Hooks

The project uses pre-commit hooks to automatically run code quality checks before each commit.

### Hook Configuration (`.pre-commit-config.yaml`)

- **Python hooks**: Black, isort, mypy, flake8
- **JavaScript hooks**: ESLint, Prettier
- **General hooks**: File validation, whitespace cleanup

### Manual Hook Execution

```bash
# Run on staged files
pre-commit run

# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black
pre-commit run eslint
```

## 🛠️ IDE Setup

### VS Code

1. Install recommended extensions:

   - Python
   - ESLint
   - Prettier
   - TypeScript

2. Add to `.vscode/settings.json`:

```json
{
  "python.formatting.provider": "black",
  "python.sortImports.provider": "isort",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### PyCharm

1. Go to Settings → Tools → External Tools
2. Add Black, isort, and mypy as external tools
3. Configure ESLint and Prettier for frontend files

## 🐛 Troubleshooting

### Common Issues

1. **Pre-commit hooks failing**

   ```bash
   # Update pre-commit hooks
   pre-commit autoupdate

   # Reinstall hooks
   pre-commit uninstall
   pre-commit install
   ```

2. **TypeScript errors in frontend**

   ```bash
   # Clear Next.js cache
   rm -rf .next

   # Reinstall dependencies
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Python type checking issues**

   ```bash
   # Update mypy
   pip install --upgrade mypy

   # Clear mypy cache
   rm -rf .mypy_cache
   ```

### Performance Optimization

1. **Exclude large directories** from type checking
2. **Use incremental builds** for TypeScript
3. **Cache pre-commit hooks** for faster execution

## 📚 Additional Resources

- [Black Documentation](https://black.readthedocs.io/)
- [ESLint Documentation](https://eslints.org/)
- [Prettier Documentation](https://prettier.io/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [Pre-commit Documentation](https://pre-commit.com/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
