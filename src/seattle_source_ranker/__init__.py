"""
Seattle Source Ranker

A comprehensive tool for discovering, analyzing, and ranking open source projects
from Seattle's tech community.

This package provides functionality for:
- Collecting GitHub user and repository data
- Analyzing project metrics and quality indicators
- Scoring and ranking projects using the SSR algorithm
- Managing GitHub API tokens and rate limits
- Checking PyPI package publication status

Main modules:
    - collector: Data collection from GitHub API
    - scoring: SSR algorithm and project ranking
    - pypi: PyPI package detection and verification
    - tokens: GitHub token management and rotation

Example:
    >>> from seattle_source_ranker.tokens import TokenManager
    >>> tm = TokenManager()
    >>> token = tm.get_token()
"""

__version__ = "1.0.0"
__author__ = "thomas0829"

# Import main components for easy access
from .tokens import TokenManager
from .pypi import PyPIChecker

__all__ = [
    "TokenManager",
    "PyPIChecker",
]
