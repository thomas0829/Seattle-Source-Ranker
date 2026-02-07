# Contributing to Seattle Source Ranker

Thank you for your interest in contributing to Seattle Source Ranker! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Seattle-Source-Ranker.git
   cd Seattle-Source-Ranker
   ```
3. **Install dependencies**:
   ```bash
   pip install -e .
   ```
4. **Set up your environment**:
   - Create `.env.tokens` with your GitHub tokens (see [MULTI_TOKEN_GUIDE.md](docs/MULTI_TOKEN_GUIDE.md))
   - Start Redis: `redis-server --daemonize yes`

## Development Workflow

1. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write clean, readable code
   - Follow existing code style and conventions
   - Add tests for new functionality

3. **Test your changes**:
   ```bash
   cd test && bash run_tests.sh
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add: brief description of your changes"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request** on GitHub

## Code Guidelines

- **Python**: Follow PEP 8 style guide
- **JavaScript/React**: Use consistent formatting (Prettier-compatible)
- **Documentation**: Update relevant docs when adding features
- **Testing**: Maintain or improve test coverage

## Testing

Run the test suite before submitting PRs:

```bash
cd test
bash run_tests.sh
```

All tests should pass before your PR can be merged.

## Reporting Issues

- Use GitHub Issues to report bugs or suggest features
- Include clear descriptions and steps to reproduce
- Provide system information (OS, Python version, etc.)

## Questions?

- Check [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues
- Review existing issues and discussions
- Open a new issue if you need help

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

[Return to README](README.md)
