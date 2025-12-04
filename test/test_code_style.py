#!/usr/bin/env python3
"""
Test code style and quality using pylint.

This test ensures that the codebase maintains a minimum quality score
and follows Python best practices.
"""
import subprocess
import sys
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestCodeStyle:
    """Test code style and quality standards"""

    # Files to check for code quality
    FILES_TO_CHECK = [
        'scripts/generate_frontend_data.py',
        'scripts/secondary_update.py',
        'scripts/generate_pypi_projects.py',
        'scripts/update_readme.py',
        'distributed/distributed_collector.py',
        'distributed/workers/collection_worker.py',
        'utils/token_manager.py',
        'utils/pypi_checker.py',
        'utils/pypi_client.py',
        'utils/celery_config.py',
    ]

    # Minimum acceptable pylint score
    # Note: Set to 8.75 due to unavoidable complexity warnings
    # (too-many-locals, too-many-branches) in large functions
    MIN_PYLINT_SCORE = 8.75

    def test_pylint_score_meets_minimum(self):
        """Test that pylint score is at least 8.75/10"""
        try:
            # Run pylint on all specified files
            result = subprocess.run(
                ['pylint'] + self.FILES_TO_CHECK,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=60,
                check=False
            )

            # Extract score from output
            # Format: "Your code has been rated at X.XX/10"
            output = result.stdout
            score_line = [line for line in output.split('\n') if 'rated at' in line]

            if not score_line:
                pytest.fail("Could not find pylint score in output")

            # Parse score (e.g., "8.54/10" -> 8.54)
            score_text = score_line[0].split('rated at')[1].split('/10')[0].strip()
            score = float(score_text)

            # Assert minimum score
            assert score >= self.MIN_PYLINT_SCORE, (
                f"Pylint score {score:.2f}/10 is below minimum {self.MIN_PYLINT_SCORE}/10\n"
                f"Run 'pylint {' '.join(self.FILES_TO_CHECK)}' to see details"
            )

            print(f"\n✅ Code quality score: {score:.2f}/10 (minimum: {self.MIN_PYLINT_SCORE}/10)")

        except FileNotFoundError:
            pytest.skip("pylint not installed - run: pip install pylint")
        except subprocess.TimeoutExpired:
            pytest.fail("Pylint check timed out after 60 seconds")

    def test_no_syntax_errors(self):
        """Test that all Python files compile without syntax errors"""
        for file_path in self.FILES_TO_CHECK:
            full_path = PROJECT_ROOT / file_path

            if not full_path.exists():
                pytest.skip(f"File not found: {file_path}")

            try:
                result = subprocess.run(
                    ['python3', '-m', 'py_compile', str(full_path)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False
                )

                assert result.returncode == 0, (
                    f"Syntax error in {file_path}:\n{result.stderr}"
                )
            except subprocess.TimeoutExpired:
                pytest.fail(f"Syntax check timed out for {file_path}")

    def test_critical_pylint_errors_absent(self):
        """Test that there are no critical pylint errors (E-level)"""
        try:
            result = subprocess.run(
                ['pylint', '--errors-only'] + self.FILES_TO_CHECK,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=60,
                check=False
            )

            # If there are errors, pylint returns non-zero
            # But we want to check the actual output for E-level errors
            output = result.stdout

            # Look for error lines (format: filename:line:col: E####: message)
            error_lines = [
                line for line in output.split('\n')
                if ': E' in line and not 'E0401' in line  # Ignore import errors
            ]

            if error_lines:
                pytest.fail(
                    f"Found {len(error_lines)} critical pylint errors:\n" +
                    '\n'.join(error_lines[:5])  # Show first 5
                )

            print(f"✅ No critical errors found")

        except FileNotFoundError:
            pytest.skip("pylint not installed")
        except subprocess.TimeoutExpired:
            pytest.fail("Pylint error check timed out")

    def test_specific_file_quality(self):
        """Test individual file quality scores for core modules"""
        core_files = [
            'scripts/generate_frontend_data.py',
            'utils/token_manager.py',
            'utils/pypi_checker.py',
        ]

        min_score = 8.5  # Slightly lower threshold for individual files

        for file_path in core_files:
            full_path = PROJECT_ROOT / file_path

            if not full_path.exists():
                continue

            try:
                result = subprocess.run(
                    ['pylint', str(full_path)],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False
                )

                output = result.stdout
                score_line = [line for line in output.split('\n') if 'rated at' in line]

                if score_line:
                    score_text = score_line[0].split('rated at')[1].split('/10')[0].strip()
                    score = float(score_text)

                    assert score >= min_score, (
                        f"{file_path}: score {score:.2f}/10 is below {min_score}/10"
                    )

                    print(f"  {file_path}: {score:.2f}/10")

            except FileNotFoundError:
                pytest.skip("pylint not installed")
            except subprocess.TimeoutExpired:
                pytest.fail(f"Pylint check timed out for {file_path}")


class TestImportStructure:
    """Test that imports are properly structured"""

    def test_no_circular_imports(self):
        """Test that there are no circular import dependencies"""
        # This is a basic test - just try importing main modules
        modules_to_test = [
            'utils.token_manager',
            'utils.pypi_checker',
            'utils.celery_config',
        ]

        for module_name in modules_to_test:
            try:
                # Try to import - circular imports will cause ImportError
                __import__(module_name)
            except ImportError as e:
                if 'circular' in str(e).lower():
                    pytest.fail(f"Circular import detected in {module_name}: {e}")
                # Other import errors might be due to missing dependencies


class TestDocumentation:
    """Test that code is properly documented"""

    def test_main_functions_have_docstrings(self):
        """Test that main functions have docstrings (sample check)"""
        # This is a basic check - could be expanded
        from utils.token_manager import TokenManager

        assert TokenManager.__doc__ is not None, "TokenManager class missing docstring"
        assert TokenManager.get_token.__doc__ is not None, "get_token method missing docstring"

    def test_modules_have_docstrings(self):
        """Test that modules have docstrings"""
        import utils.token_manager
        import utils.pypi_checker

        assert utils.token_manager.__doc__ is not None, "token_manager module missing docstring"
        assert utils.pypi_checker.__doc__ is not None, "pypi_checker module missing docstring"


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v'])
