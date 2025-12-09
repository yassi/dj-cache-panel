# Development Setup

This guide will help you set up Django Cache Panel for local development and contribution.

## Prerequisites

Before setting up the development environment, make sure you have:

- **Python 3.9+**: The minimum supported Python version
- **Git**: For version control
- **Make**: For using the included Makefile commands (optional)

## Getting the Source Code

### 1. Fork and Clone

1. **Fork the repository** on GitHub: [yassi/dj-cache-panel](https://github.com/yassi/dj-cache-panel)

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/dj-cache-panel.git
   cd dj-cache-panel
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/yassi/dj-cache-panel.git
   ```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Development Installation

The project includes a Makefile with several useful commands for development.

### Quick Setup

```bash
# Install all dependencies and package in editable mode
make install

# Or manually:
pip install -e .
pip install -r requirements.txt
```

## Project Structure

Understanding the project layout:

```
dj-cache-panel/
├── dj_cache_panel/          # Main package
│   ├── __init__.py
│   ├── admin.py             # Django admin integration
│   ├── apps.py              # Django app configuration
│   ├── models.py            # Placeholder model for admin
│   ├── urls.py              # URL patterns
│   ├── views.py             # Django views
│   └── templates/           # Django templates
│       └── admin/
│           └── dj_cache_panel/
│               ├── base.html
│               ├── index.html
│               └── styles.css
├── example_project/         # Example Django project
│   ├── manage.py
│   └── example_project/
│       ├── settings.py      # Django settings
│       └── urls.py          # URL configuration
├── tests/                   # Test suite
│   ├── base.py              # Test base classes
│   ├── conftest.py          # Pytest configuration
│   └── test_admin.py        # Admin integration tests
├── docs/                    # Documentation
├── pyproject.toml          # Project configuration
├── requirements.txt        # Development dependencies
├── Makefile               # Development commands
└── README.md              # Project documentation
```

## Example Project Setup

The repository includes an example Django project for development and testing.

### 1. Set Up the Example Project

```bash
cd example_project

# Run migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser
```

### 2. Run the Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/admin/` to access the Django admin with Cache Panel.

## Documentation Development

### Building Documentation

The documentation is built with MkDocs:

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

### Writing Documentation

Documentation is written in Markdown and located in the `docs/` directory:

- Follow the existing structure and style
- Include code examples for new features
- Update the navigation in `mkdocs.yml`

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=dj_cache_panel --cov-report=html

# Run specific test file
pytest tests/test_admin.py
```

See the [Testing Guide](testing.md) for more details.

## Getting Help

### Development Questions

- **GitHub Discussions**: [Project discussions](https://github.com/yassi/dj-cache-panel/discussions)
- **Issues**: [Report bugs or request features](https://github.com/yassi/dj-cache-panel/issues)

### Resources

- **Django Documentation**: [Django Project](https://docs.djangoproject.com/)
- **Python Packaging**: [PyPA Guides](https://packaging.python.org/)
- **Testing**: [Pytest Documentation](https://docs.pytest.org/)

Thank you for contributing to Django Cache Panel! 🎉
