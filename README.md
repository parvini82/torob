# 🔍 Torob - AI-Powered Product Discovery

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Next.js](https://img.shields.io/badge/Next.js-latest-black)](https://nextjs.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An intelligent product discovery platform that uses AI to analyze product images and generate multilingual tags for improved search and categorization. The system processes images using advanced vision models and provides results in both English and Persian.

---

## ✨ Key Features

- 🖼️ AI-powered image analysis for product categorization
- 🌐 Multilingual tag generation (English & Persian)
- ⚡ FastAPI backend in Python
- 🎯 Modern Next.js frontend interface
- 📊 Evaluation pipeline for performance benchmarking
- 🔄 Flexible workflow using [LangGraph](https://langgraph.org/)
- 🛠️ Extensible modular software architecture
- 📦 Docker support for easy deployment

---

## 🏗️ System Architecture

### Overall Software Architecture

Below is an overview of the main components and how they interact:

> ![image](/docs/SoftwareArchitecture.png)

- **Frontend (Next.js)**: User interface for image upload, results visualization, tagging and search
- **Backend (FastAPI)**: API, image processing pipeline, orchestration
- **LangGraph Workflow**: Manages stepwise, modular, and robust pipelines for inference
- **Evaluation Suite**: For benchmarking performance on different datasets

---

### 📉 LangGraph Workflow Architecture

The system leverages [LangGraph](https://langgraph.org/) for orchestrating various steps in the AI-powered product analysis and tagging process.


> ![image](/docs/WorkflowArchitecture.jpg)

The workflow ensures modularity, fault tolerance, and easy extensions for custom pipelines.

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.10+
- Node.js (Latest LTS version)
- Docker (optional)

### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/parvini82/torob.git
   cd torob
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env for your configuration
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

---

## 💻 Usage

### Running the Backend

Start the FastAPI server:
```bash
python src/main.py
```
The API will be available at `http://localhost:8000`

### Running the Frontend

Inside the `frontend` directory:
```bash
npm run dev
# or
yarn dev
```
Visit `http://localhost:3000` in your browser.

### Using Docker

To build and run the container:
```bash
docker build -t torob .
docker run -p 8000:8000 torob
```

---

## 🔬 Evaluation & Challenging Tests

We have conducted a set of challenging tests using tricky, complex product images to benchmark the robustness of our AI models. The test images and detailed results can be found in the [`docs/ChallengingExamples`](docs/ChallengingExamples) folder.


---

## 🧪 Development

### Code Quality Tools

**Backend (Python)**
- **Black**: Code formatting (`black .`)
- **isort**: Import sorting (`isort .`)
- **mypy**: Type checking (`mypy .`)
- **flake8**: Linting (`flake8 .`)

**Frontend (Next.js + TypeScript)**
- **ESLint**  
- **Prettier**
- **TypeScript**

### Running Tests

```bash
# Backend tests
python -m pytest

# Generate test data
python scripts/generate_toy_sample.py

# Run evaluation
python scripts/run_evaluation.py
```

---

## 📖 Documentation

- **API Documentation**: Available at `http://localhost:8000/docs` when the backend server is running.
- **Frontend Documentation**: See [`frontend/README.md`](./frontend/README.md)
- **Evaluation & Results**: See [`evaluation/`](./evaluation/) for benchmarks, scripts, and detailed results.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch:
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. Run the pre-commit hooks:
   ```bash
   pre-commit install
   ```
4. Commit your changes and push
5. Open a Pull Request

Please ensure your code passes all tests and follows the project's coding standards.

---

## 📄 License

[MIT License](LICENSE) - See the LICENSE file for details

---

## 🆘 Support

- **Issues**: Use the [GitHub Issues](https://github.com/parvini82/torob/issues) page
- **Documentation**: Check the [`docs/`](./docs/) directory for detailed guides
- **Questions**: Start a [Discussion](https://github.com/parvini82/torob/discussions)

---

## 🛠️ Project Structure

```
torob/
├── frontend/                 # Next.js frontend application
│   ├── pages/               # Next.js pages
│   ├── src/                 # Source code
│   ├── public/              # Static assets
│   └── package.json         # Frontend dependencies
├── src/                     # Python backend
│   ├── controller/          # API controllers
│   ├── service/             # Business logic
│   ├── config/              # Configuration
│   └── utils/               # Utility functions
├── notebooks/               # Jupyter notebooks for analysis
├── tests/                   # Test files
├── scripts/                 # Utility scripts
├── evaluation/              # Evaluation configs, scripts, challenging test results
└── docs/                    # Documentation and architecture images
```

---
