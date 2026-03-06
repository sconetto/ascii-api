# Contributing to ASCII API

Thank you for your interest in contributing to ASCII API!

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:

   ```bash
   git clone https://github.com/YOUR_USERNAME/ascii-api.git
   cd ascii-api
   ```

3. **Create a branch** for your changes:

   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
# Install dependencies
uv sync --extra dev

# Set up pre-commit hooks
pre-commit install
```

### Running the Server

```bash
uv run uvicorn app.main:app --reload
```

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) guidelines
- Use type hints (strict mode enabled)
- Run linter before committing:

  ```bash
  uv run ruff check --fix
  uv run ruff format
  ```

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=term-missing --cov-report=html
```

## Building

### Docker Build

```bash
docker build -t ascii-api .
```

### Local Build

```bash
uv build
```

## Making Changes

1. Make your changes in your feature branch
2. Test locally:

   ```bash
   uv run ruff check --fix && uv run ruff format && uv run pytest --cov=app
   ```

3. Pre-commit hooks will run automatically on commit

## Commit Messages

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification. Commit messages should follow this format:

```text
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (formatting)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding or correcting tests
- `chore`: Changes to the build process or auxiliary tools

### Examples

```bash
# Feature
git commit -m "feat(api): add gif support for ascii conversion"

# Bug fix
git commit -m "fix(validator): resolve memory leak in file processing"

# Documentation
git commit -m "docs(readme): update docker instructions"

# Breaking change
git commit -m "feat(api)!: change rate limit to 20 req/min"
```

1. Push to your fork:

   ```bash
   git push origin feature/your-feature-name
   ```

2. Open a Pull Request

## Pull Request Guidelines

- Fill out the PR template completely
- Include clear description of changes
- Ensure all CI checks pass
- Update documentation if needed
- Maintain or improve test coverage

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms.

## Questions?

Feel free to open an issue for questions about contributing.
