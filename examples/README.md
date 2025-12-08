# Examples

This directory contains simple examples demonstrating how to use the Seattle Source Ranker package.

## Prerequisites

Make sure you have installed the package:

```bash
pip install -e .
```

For token management example, you'll need GitHub tokens configured in `.env.tokens`:

```
GITHUB_TOKEN_1=ghp_your_token_here
GITHUB_TOKEN_2=ghp_your_token_here
```

## Examples

### 1. Token Management (`example_1_token_management.py`)

Demonstrates how to:
- Load GitHub API tokens
- Check rate limits
- Rotate between tokens

```bash
python examples/example_1_token_management.py
```

### 2. PyPI Package Detection (`example_2_pypi_checker.py`)

Demonstrates how to:
- Check if a project is on PyPI
- Batch check multiple projects
- Understand detection accuracy

```bash
python examples/example_2_pypi_checker.py
```

### 3. Project Scoring (`example_3_scoring.py`)

Demonstrates how to:
- Calculate SSR scores for projects
- Understand scoring factors (age, activity, health)
- Rank projects by score

```bash
python examples/example_3_scoring.py
```

## Expected Output

Each example will print clear, formatted output showing:
- ✓ Success indicators
- ✗ Error messages (if any)
- Detailed metrics and results

## Notes

- Examples are designed to run independently
- No external services required (except Token Management for API calls)
- All examples use sample data for demonstration
