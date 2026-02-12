"""
Shared test configuration for Seattle Source Ranker.

Adds project root to sys.path so all tests can import
seattle_source_ranker without manual path manipulation.
"""
import sys
from pathlib import Path

# Project root (parent of tests/)
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
