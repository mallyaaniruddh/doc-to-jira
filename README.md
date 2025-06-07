# Jira Issue Creator

[![CI/CD Pipeline](https://github.com/yourusername/jira-issue-creator/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/jira-issue-creator/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/yourusername/jira-issue-creator/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/jira-issue-creator)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A robust Python application for creating Jira issues programmatically with comprehensive error handling, retry mechanisms, and automated testing.

## 🚀 Features

- **Robust Jira Integration**: Create issues with automatic retry mechanisms and exponential backoff
- **Custom Exception Handling**: Specific exceptions for different failure scenarios
- **Comprehensive Logging**: Structured logging throughout the application
- **JSON Batch Processing**: Create multiple issues from JSON user stories
- **Input Validation**: Thorough validation of all inputs before processing
- **Connection Testing**: Built-in connection validation and project info retrieval
- **Type Hints**: Full type hint support for better code maintainability

## 📋 Prerequisites

- Python 3.8 or higher
- Jira Cloud account with API access
- Valid Jira API token

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/jira-issue-creator.git
   cd jira-issue-creator
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install development dependencies** (optional):
   ```bash
   pip install -r requirements-dev.txt
   ```

## ⚙️ Configuration

1. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Configure your Jira credentials** in `.env`:
   ```env
   JIRA_BASE_URL=https://yourcompany.atlassian.net
   JIRA_EMAIL=your-email@company.com
   JIRA_API_TOKEN=your-api-token
   JIRA_PROJECT_KEY=YOUR-PROJECT-KEY
   ```

### Getting Your Jira API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a label and copy the generated token
4. Use this token as your `JIRA_API_TOKEN`

## 📖 Usage

### Basic Usage

```python
from doc_to_jira import DocToJira

# Initialize the client
jira = DocToJira()

# Create a single issue
issue_key = jira.create_jira_issue(
    summary="Fix login bug",
    description="Users cannot log in with special characters in password",
    issuetype="Bug"
)
print(f"Created issue: {issue_key}")
```

### Batch Processing from JSON

1. **Prepare your JSON file** (`user_stories.json`):
   ```json
   [
     {
       "user_story": "As a user, I want to reset my password",
       "deliverables": "Password reset functionality with email verification",
       "issue_type": "Story"
     },
     {
       "user_story": "Fix mobile responsiveness issue",
       "deliverables": "Ensure all pages work correctly on mobile devices",
       "issue_type": "Bug"
     }
   ]
   ```

2. **Run the batch processor**:
   ```bash
   python main_jira.py
   ```

### Command Line Usage

```bash
# Validate JSON structure first
python -c "from main_jira import validate_json_structure; validate_json_structure('user_stories.json')"

# Process issues
python main_jira.py
```

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run Tests with Coverage
```bash
pytest --cov=doc_to_jira --cov-report=html
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest -m unit

# Integration tests only  
pytest -m integration

# Exclude slow tests
pytest -m "not slow"
```

### Linting and Code Quality
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .
pylint doc_to_jira.py main_jira.py

# Type checking
mypy doc_to_jira.py main_jira.py
```

## 🔧 Development Setup

### Install Pre-commit Hooks
```bash
pre-commit install
```

This will automatically run code formatting, linting, and basic checks before each commit.

### Running Security Scans
```bash
# Check for security vulnerabilities
safety check

# Run security analysis
bandit -r . -x test_*.py
```

## 📊 CI/CD Pipeline

The project includes a comprehensive GitHub Actions pipeline that runs on every push and pull request:

### Test Matrix
- **Python versions**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Operating system**: Ubuntu (latest)

### Pipeline Stages
1. **Code Quality**: Linting, formatting checks, type checking
2. **Security Scanning**: Vulnerability detection, static analysis
3. **Unit Testing**: Comprehensive test suite with coverage reporting
4. **Integration Testing**: Mock-based integration tests
5. **JSON Validation**: Ensures user stories file structure is valid

### Coverage Reports
- Automatically uploaded to [Codecov](https://codecov.io)
- Minimum coverage threshold: 80%

## 🎯 API Reference

### DocToJira Class

#### Constructor
```python
DocToJira(max_retries: int = 3, retry_delay: float = 1.0)
```

#### Methods

**create_jira_issue(summary: str, description: str, issuetype: str) → str**
- Creates a Jira issue with retry mechanism
- Returns the issue key on success
- Raises custom exceptions on failure

**test_connection() → bool**
- Tests the connection to Jira
- Returns True if successful, False otherwise

**get_project_info() → Optional[dict]**
- Retrieves information about the configured project
- Returns project details or None if not found

### Custom Exceptions

- `JiraConfigurationError`: Missing or invalid configuration
- `JiraConnectionError`: Connection failures after retries
- `JiraIssueCreationError`: Issue creation failures after retries
- `JiraValidationError`: Input validation failures

## 📁 Project Structure

```
jira-issue-creator/
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI/CD pipeline
├── doc_to_jira.py                 # Main Jira integration class
├── main_jira.py                   # CLI interface and batch processing
├── test_doc_to_jira.py            # Comprehensive test suite
├── user_stories.json              # Example user stories data
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
├── pytest.ini                     # Pytest configuration
├── pyproject.toml                 # Project configuration
├── .flake8                        # Flake8 linting configuration
├── .pre-commit-config.yaml        # Pre-commit hooks configuration
├── .gitignore                     # Git ignore rules
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Run tests**: `pytest`
5. **Run pre-commit checks**: `pre-commit run --all-files`
6. **Commit your changes**: `git commit -m 'Add amazing feature'`
7. **Push to the branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Development Guidelines

- Write tests for new functionality
- Maintain test coverage above 80%
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Update documentation for API changes
- Use conventional commit messages

## 📝 Changelog

### v2.0.0 (Latest)
- ✨ Added custom exception classes
- 🚀 Implemented retry mechanisms with exponential backoff
- 📊 Added comprehensive logging throughout
- 🧪 Enhanced test suite with retry testing
- 🔧 Added utility methods for connection testing
- 📋 Improved input validation
- 🎯 Added type hints throughout codebase

### v1.0.0
- 🎉 Initial release
- Basic Jira issue creation
- JSON batch processing
- Simple error handling

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. **Check the documentation** above
2. **Search existing issues** in the GitHub repository
3. **Create a new issue** with detailed information about your problem
4. **Include logs and error messages** when reporting bugs

## 🙏 Acknowledgments

- [Atlassian JIRA Python Library](https://jira.readthedocs.io/) for the excellent Jira integration
- [GitHub Actions](https://github.com/features/actions) for CI/CD automation
- All contributors who help improve this project

---

**Made with ❤️ for efficient Jira workflow automation**