#!/usr/bin/env python3
"""
Test PyPI checker with 50 real Seattle Python projects
"""
import json
import sys
import glob
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.pypi_checker import PyPIChecker


def load_real_projects(limit=50):
    """Load real Python projects from collected data"""
    # Find latest project file
    project_files = glob.glob('data/seattle_projects_*.json')
    
    if not project_files:
        print("❌ No project data found. Using sample projects instead.")
        return get_sample_projects()
    
    latest_file = max(project_files)
    print(f"📂 Loading projects from {latest_file}")
    
    with open(latest_file) as f:
        data = json.load(f)
    
    # Get projects data
    if isinstance(data, dict) and 'projects' in data:
        all_projects = data['projects']
    elif isinstance(data, list):
        all_projects = data
    else:
        print("❌ Unexpected data format")
        return get_sample_projects()
    
    # Filter Python projects
    python_projects = [p for p in all_projects if p.get('language') == 'Python']
    
    print(f"Found {len(python_projects):,} Python projects")
    
    # Sample 50 projects with diverse characteristics
    import random
    random.seed(42)  # Reproducible
    
    # Get a mix of high-star and low-star projects
    python_projects.sort(key=lambda x: x.get('stars', 0), reverse=True)
    
    sample = []
    # 20 high-star projects (more likely to be packages)
    sample.extend(python_projects[:20])
    # 30 random projects
    sample.extend(random.sample(python_projects[20:], min(30, len(python_projects)-20)))
    
    return sample[:limit]


def get_sample_projects():
    """Fallback: Sample of known projects for testing"""
    return [
        # Known packages (should be True)
        {'name': 'requests', 'description': 'HTTP library', 'language': 'Python', 'stars': 50000},
        {'name': 'flask', 'description': 'Web framework', 'language': 'Python', 'stars': 60000},
        {'name': 'django', 'description': 'Web framework', 'language': 'Python', 'stars': 70000},
        {'name': 'numpy', 'description': 'Scientific computing', 'language': 'Python', 'stars': 25000},
        {'name': 'pandas', 'description': 'Data analysis', 'language': 'Python', 'stars': 40000},
        {'name': 'scikit-learn', 'description': 'Machine learning', 'language': 'Python', 'stars': 55000},
        {'name': 'matplotlib', 'description': 'Plotting library', 'language': 'Python', 'stars': 18000},
        {'name': 'pytest', 'description': 'Testing framework', 'language': 'Python', 'stars': 10000},
        {'name': 'black', 'description': 'Code formatter', 'language': 'Python', 'stars': 35000},
        {'name': 'mypy', 'description': 'Type checker', 'language': 'Python', 'stars': 16000},
        
        # AllenAI projects (some on PyPI)
        {'name': 'allennlp', 'description': 'NLP library', 'language': 'Python', 'stars': 11000, 'owner': 'allenai'},
        {'name': 'allennlp-models', 'description': 'NLP models', 'language': 'Python', 'stars': 1000, 'owner': 'allenai'},
        {'name': 'cached-path', 'description': 'File caching', 'language': 'Python', 'stars': 100, 'owner': 'allenai'},
        
        # Microsoft projects
        {'name': 'playwright-python', 'description': 'Browser automation', 'language': 'Python', 'stars': 9000, 'owner': 'microsoft'},
        {'name': 'semantic-kernel', 'description': 'AI orchestration', 'language': 'Python', 'stars': 15000, 'owner': 'microsoft'},
        
        # Projects likely NOT on PyPI
        {'name': 'awesome-python', 'description': 'Awesome list', 'language': 'Python', 'stars': 180000},
        {'name': 'system-design-primer', 'description': 'Learning resource', 'language': 'Python', 'stars': 250000},
        {'name': 'public-apis', 'description': 'API list', 'language': 'Python', 'stars': 280000},
        {'name': 'python-tutorial', 'description': 'Tutorial', 'language': 'Python', 'stars': 5000},
        {'name': 'my-dotfiles', 'description': 'Config files', 'language': 'Python', 'stars': 50},
        {'name': 'homework-project', 'description': 'School project', 'language': 'Python', 'stars': 0},
        {'name': 'test-repo-123', 'description': 'Test', 'language': 'Python', 'stars': 1},
        {'name': 'learning-python', 'description': 'Learning', 'language': 'Python', 'stars': 100},
        {'name': 'python-examples', 'description': 'Examples', 'language': 'Python', 'stars': 200},
        {'name': 'django-demo', 'description': 'Demo project', 'language': 'Python', 'stars': 10},
    ]


def test_50_projects():
    """Test PyPI checker with 50 projects"""
    print("=" * 80)
    print("🧪 Testing PyPI Checker with 50 Real Projects")
    print("=" * 80)
    print()
    
    # Load projects
    projects = load_real_projects(50)
    print(f"\n📊 Testing {len(projects)} projects\n")
    
    # Initialize checker
    checker = PyPIChecker()
    print()
    
    # Check each project
    results = {
        'true_positive': [],   # On PyPI and detected
        'true_negative': [],   # Not on PyPI and not detected
        'false_positive': [],  # Not on PyPI but detected (need manual verification)
        'false_negative': [],  # On PyPI but not detected (need manual verification)
        'uncertain': []        # Need manual review
    }
    
    print("🔍 Checking projects...\n")
    print(f"{'#':<4} {'Project':<35} {'Stars':<8} {'Match':<8} {'Conf':<6} {'Method':<25}")
    print("-" * 95)
    
    for i, project in enumerate(projects, 1):
        is_on_pypi, confidence, method = checker.check_project(project)
        
        # Display result
        status = "✅" if is_on_pypi else "❌"
        name = project.get('name', 'unknown')[:30]
        stars = project.get('stars', 0)
        
        print(f"{i:<4} {name:<35} {stars:<8} {status:<8} {confidence:<6.2f} {method:<25}")
        
        # Categorize (we'll need manual verification for accuracy)
        project['check_result'] = {
            'on_pypi': is_on_pypi,
            'confidence': confidence,
            'method': method
        }
        
        # High confidence results
        if confidence > 0.8:
            if is_on_pypi:
                results['true_positive'].append(project)
            else:
                results['true_negative'].append(project)
        # Low confidence - uncertain
        elif confidence > 0.4:
            results['uncertain'].append(project)
        else:
            if is_on_pypi:
                results['uncertain'].append(project)
            else:
                results['true_negative'].append(project)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 RESULTS SUMMARY")
    print("=" * 80)
    
    total_detected = sum(1 for p in projects if p['check_result']['on_pypi'])
    total_not_detected = len(projects) - total_detected
    
    print(f"\n✅ Detected on PyPI: {total_detected} ({total_detected/len(projects)*100:.1f}%)")
    print(f"❌ Not on PyPI: {total_not_detected} ({total_not_detected/len(projects)*100:.1f}%)")
    
    print(f"\n🎯 Confidence Distribution:")
    high_conf = sum(1 for p in projects if p['check_result']['confidence'] > 0.8)
    med_conf = sum(1 for p in projects if 0.4 < p['check_result']['confidence'] <= 0.8)
    low_conf = sum(1 for p in projects if p['check_result']['confidence'] <= 0.4)
    
    print(f"   High (>0.8): {high_conf} projects")
    print(f"   Medium (0.4-0.8): {med_conf} projects")
    print(f"   Low (<0.4): {low_conf} projects")
    
    print(f"\n📈 Match Methods:")
    methods = {}
    for p in projects:
        method = p['check_result']['method']
        methods[method] = methods.get(method, 0) + 1
    
    for method, count in sorted(methods.items(), key=lambda x: -x[1]):
        print(f"   {method}: {count}")
    
    print("\n" + "=" * 80)
    print("💡 MANUAL VERIFICATION NEEDED")
    print("=" * 80)
    print("\nPlease verify these results by checking PyPI manually:")
    print("Visit: https://pypi.org/project/<package-name>/\n")
    
    # Show a few high-confidence positives for manual check
    print("🔍 High-confidence matches (should be on PyPI):")
    high_conf_positive = [p for p in projects if p['check_result']['on_pypi'] and p['check_result']['confidence'] > 0.85][:10]
    for p in high_conf_positive:
        name = p.get('name', 'unknown')
        print(f"   • {name} - https://pypi.org/project/{name}/")
    
    print("\n🔍 Projects marked as NOT on PyPI (verify they shouldn't be):")
    high_conf_negative = [p for p in projects if not p['check_result']['on_pypi']][:10]
    for p in high_conf_negative:
        name = p.get('name', 'unknown')
        print(f"   • {name}")
    
    return projects


if __name__ == '__main__':
    test_50_projects()
