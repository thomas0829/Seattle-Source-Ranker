#!/usr/bin/env python3
"""
Example 2: PyPI Package Detection

This example demonstrates how to check if GitHub projects are
published on PyPI using the PyPIChecker.
"""

from seattle_source_ranker.pypi import PyPIChecker

def main():
    """Demonstrate PyPI package detection"""
    
    print("Seattle Source Ranker - PyPI Detection Example")
    print("=" * 50)
    
    # Initialize PyPI checker
    checker = PyPIChecker()
    print(f"✓ Loaded {len(checker.pypi_packages)} PyPI packages")
    
    # Example projects to check
    test_projects = [
        {
            'name': 'requests',
            'owner': 'psf',
            'language': 'Python',
            'topics': ['http', 'python', 'requests'],
            'description': 'Python HTTP library'
        },
        {
            'name': 'flask',
            'owner': 'pallets',
            'language': 'Python',
            'topics': ['web-framework', 'python'],
            'description': 'A micro web framework'
        },
        {
            'name': 'not-a-real-package-xyz',
            'owner': 'nobody',
            'language': 'Python',
            'topics': [],
            'description': 'This does not exist on PyPI'
        },
        {
            'name': 'awesome-python',
            'owner': 'vinta',
            'language': 'Python',
            'topics': ['awesome', 'list'],
            'description': 'A curated list of Python frameworks'
        },
    ]
    
    print("\nChecking projects:")
    print("-" * 50)
    
    for project in test_projects:
        is_on_pypi, confidence, reason = checker.check_project(project)
        status = "✓ ON PyPI" if is_on_pypi else "✗ NOT on PyPI"
        print(f"{project['name']:30s} {status}")
        if is_on_pypi:
            print(f"{'':30s}   Confidence: {confidence:.2f} ({reason})")
    
    # Batch checking
    print("\n" + "=" * 50)
    print("Batch checking multiple projects...")
    
    results = checker.batch_check(test_projects)
    pypi_count = sum(1 for r in results if r.get('on_pypi'))
    print(f"✓ Results stored in project dictionaries with 'on_pypi' field")
    
    print("\n" + "=" * 50)
    print("Example completed successfully!")


if __name__ == "__main__":
    main()
