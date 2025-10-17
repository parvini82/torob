# Torob - AI-Powered Product Discovery

A full-stack application for AI-powered product discovery and recommendation using image analysis and natural language processing.

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd torob
   ```

2. **Run the automated setup script**

   ```bash
   ./setup-dev-tools.sh
   ```

   This script will:

   - Install Python dependencies
   - Set up pre-commit hooks
   - Install frontend dependencies
   - Configure Husky for frontend pre-commit hooks

### Manual Setup

If you prefer manual setup or the automated script fails:

#### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Setup Husky
npm run prepare
```

## 🛠️ Development Tools

This project includes comprehensive code quality tools to ensure consistent, high-quality code across the team.

### Frontend Tools (Next.js + TypeScript)

#### Type Checking

- **TypeScript**: Static type checking for JavaScript/React code
- **Command**: `npm run type-check`

#### Code Formatting

- **Prettier**: Automatic code formatting
- **Commands**:
  - `npm run format` - Format all files
  - `npm run format:check` - Check formatting without fixing

#### Linting

- **ESLint**: Code quality and style enforcement
- **Commands**:
  - `npm run lint` - Run linting
  - `npm run lint:fix` - Run linting with auto-fix

#### Configuration Files

- `tsconfig.json` - TypeScript configuration
- `.eslintrc.json` - ESLint rules and plugins
- `.prettierrc` - Prettier formatting rules
- `.prettierignore` - Files to ignore for formatting

### Backend Tools (Python)

#### Code Formatting

- **Black**: Automatic Python code formatting
- **Command**: `black .`

#### Import Sorting

- **isort**: Automatic import sorting and organization
- **Command**: `isort .`

#### Type Checking

- **mypy**: Static type checking for Python
- **Command**: `mypy .`

#### Linting

- **flake8**: Code style and error checking
- **Command**: `flake8 .`

#### Configuration Files

- `pyproject.toml` - Black, isort, and mypy configuration
- `.flake8` - flake8 configuration
- `mypy.ini` - mypy type checking configuration

## 🔗 Pre-commit Hooks

Pre-commit hooks automatically run code quality checks before each commit, ensuring consistent code quality across the team.

### Features

- **Automatic formatting** with Black and Prettier
- **Import sorting** with isort
- **Type checking** with mypy and TypeScript
- **Linting** with flake8 and ESLint
- **File validation** (YAML, large files, merge conflicts)

### Setup

Pre-commit hooks are automatically installed when you run `./setup-dev-tools.sh` or manually with:

```bash
pre-commit install
```

### Manual Execution

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

## 📁 Project Structure

```
torob/
├── frontend/                 # Next.js frontend application
│   ├── pages/               # Next.js pages
│   ├── src/                 # Source code
│   ├── public/              # Static assets
│   ├── .eslintrc.json       # ESLint configuration
│   ├── .prettierrc          # Prettier configuration
│   ├── tsconfig.json        # TypeScript configuration
│   └── package.json         # Frontend dependencies
├── src/                     # Python backend
│   ├── controller/          # API controllers
│   ├── service/             # Business logic
│   ├── config/              # Configuration
│   └── utils/               # Utility functions
├── notebooks/               # Jupyter notebooks for analysis
├── tests/                   # Test files
├── .pre-commit-config.yaml  # Pre-commit hooks configuration
├── pyproject.toml          # Python tool configurations
├── requirements.txt        # Python dependencies
└── setup-dev-tools.sh     # Development setup script
```

## 🚦 Development Workflow

1. **Before starting work**: Ensure all tools are set up with `./setup-dev-tools.sh`
2. **During development**:
   - Use your IDE's integration with these tools for real-time feedback
   - Run `npm run type-check` and `mypy .` periodically for type checking
3. **Before committing**: Pre-commit hooks will automatically run all checks
4. **If hooks fail**: Fix the issues and commit again

## 🔧 IDE Integration

### VS Code

Install these extensions for optimal experience:

- **Python**: Official Python extension with Black, isort, and mypy integration
- **ESLint**: ESLint extension for JavaScript/TypeScript
- **Prettier**: Prettier extension for code formatting
- **TypeScript**: Built-in TypeScript support

### PyCharm

- Enable Black, isort, and mypy in Settings → Tools → External Tools
- Configure ESLint and Prettier for frontend files

## 🤝 Contributing

1. Follow the code style enforced by our tools
2. Ensure all pre-commit hooks pass
3. Write type hints for new Python functions
4. Use TypeScript for new frontend code
5. Run tests before submitting PRs

## 📚 Additional Resources

- [Black Documentation](https://black.readthedocs.io/)
- [ESLint Documentation](https://eslint.org/)
- [Prettier Documentation](https://prettier.io/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [Pre-commit Documentation](https://pre-commit.com/)
