#!/usr/bin/env python3
"""
Update README.md with latest collection statistics
"""

import json
import re
from datetime import datetime
from pathlib import Path

def load_latest_data():
    """Load the latest collection data from user and project files"""
    data_dir = Path(__file__).parent.parent / "data"
    
    # Find latest seattle_users_*.json file (this is what we commit to Git)
    user_files = list(data_dir.glob('seattle_users_*.json'))
    if not user_files:
        return None
        
    latest_user_file = max(user_files)
    print(f"📂 Loading user data from {latest_user_file.name}")
    
    with open(latest_user_file, 'r') as f:
        user_data = json.load(f)
    
    # Try to find latest project file (will exist during workflow run)
    project_files = list(data_dir.glob('seattle_projects_*.json'))
    project_data = None
    
    if project_files:
        latest_project_file = max(project_files)
        print(f"📂 Loading project data from {latest_project_file.name}")
        
        try:
            with open(latest_project_file, 'r') as f:
                project_data = json.load(f)
            print(f"✅ Successfully loaded project data")
        except Exception as e:
            print(f"⚠️  Warning: Could not load project data: {e}")
    else:
        print(f"⚠️  No project data found (will use user data only)")
    
    # Try to find PyPI data
    pypi_file = data_dir / 'seattle_pypi_projects.json'
    pypi_data = None
    
    if pypi_file.exists():
        print(f"📂 Loading PyPI data from {pypi_file.name}")
        try:
            with open(pypi_file, 'r') as f:
                pypi_data = json.load(f)
            print(f"✅ Successfully loaded PyPI data")
        except Exception as e:
            print(f"⚠️  Warning: Could not load PyPI data: {e}")
    else:
        print(f"⚠️  No PyPI data found (will skip PyPI statistics)")
    
    return {
        'user_data': user_data,
        'project_data': project_data,
        'pypi_data': pypi_data
    }

def update_readme(stats):
    """Update README.md with latest statistics"""
    readme_path = Path(__file__).parent.parent / "README.md"
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract statistics
    total_users = stats.get('total_users', 0)
    total_projects = stats.get('total_projects')
    total_stars = stats.get('total_stars')
    pypi_projects = stats.get('pypi_projects')
    pypi_total_python = stats.get('pypi_total_python')
    pypi_rate = stats.get('pypi_detection_rate')
    collected_at = stats.get('collected_at', '')
    
    # Format date
    if collected_at:
        try:
            dt = datetime.fromisoformat(collected_at.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d %H:%M:%S PST')
        except:
            date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S PST')
    else:
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S PST')
    
    new_content = content
    
    # Update project count if available
    if total_projects is not None:
        project_pattern = r'- \*\*[0-9,]+ projects\*\* tracked across Seattle.s developer community'
        project_text = f"- **{total_projects:,} projects** tracked across Seattle's developer community"
        new_content = re.sub(project_pattern, project_text, new_content)
    
    # Update stars count if available
    if total_stars is not None:
        stars_pattern = r'- \*\*[0-9,]+ total stars\*\* accumulated by Seattle projects'
        stars_text = f"- **{total_stars:,} total stars** accumulated by Seattle projects"
        new_content = re.sub(stars_pattern, stars_text, new_content)
    
    # Update user count (always available)
    user_pattern = r'- \*\*[0-9,]+ users\*\* collected in latest run'
    user_text = f"- **{total_users:,} users** collected in latest run"
    new_content = re.sub(user_pattern, user_text, new_content)
    
    # Update PyPI statistics if available
    if pypi_projects is not None and pypi_total_python is not None:
        pypi_pattern = r'- \*\*[0-9,]+ Python projects\*\* published on PyPI \([0-9.]+% of Python projects\)'
        if pypi_rate:
            pypi_text = f"- **{pypi_projects:,} Python projects** published on PyPI ({pypi_rate} of Python projects)"
        else:
            pypi_text = f"- **{pypi_projects:,} Python projects** published on PyPI"
        
        # If pattern exists, replace it
        if re.search(pypi_pattern, new_content):
            new_content = re.sub(pypi_pattern, pypi_text, new_content)
        else:
            # If pattern doesn't exist, add it after the users line
            new_content = re.sub(
                r'(- \*\*[0-9,]+ users\*\* collected in latest run)',
                r'\1\n' + pypi_text,
                new_content
            )
    
    # Update the date line
    # Pattern: - Last updated: 2025-11-15 21:06:33 PST
    date_pattern = r'- Last updated: [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} PST'
    date_text = f"- Last updated: {date_str}"
    
    new_content = re.sub(date_pattern, date_text, new_content)
    
    # Write back
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ README.md updated successfully!")
    if total_projects is not None:
        print(f"   Total Projects: {total_projects:,}")
    if total_stars is not None:
        print(f"   Total Stars: {total_stars:,}")
    print(f"   Total Users: {total_users:,}")
    print(f"   Last Updated: {date_str}")

def main():
    print("📝 Updating README.md with latest statistics...")
    
    # Load data
    data = load_latest_data()
    
    if not data:
        print("❌ No data file found!")
        return
    
    user_data = data['user_data']
    project_data = data['project_data']
    pypi_data = data['pypi_data']
    
    # Build statistics from user data
    # Check if it's the new format (with total_users field) or old format (dict of users)
    if isinstance(user_data, dict) and 'total_users' in user_data:
        # New format: has metadata
        total_users = user_data.get('total_users', 0)
        collected_at = user_data.get('collected_at', datetime.now().isoformat())
    else:
        # Old format: dict of users
        total_users = len(user_data)
        collected_at = datetime.now().isoformat()
    
    stats = {
        'total_users': total_users,
        'collected_at': collected_at
    }
    
    # Add project statistics if available
    if project_data:
        stats['total_projects'] = project_data.get('total_projects')
        stats['total_stars'] = project_data.get('total_stars')
        print(f"✅ Found project data with {stats['total_projects']:,} projects and {stats['total_stars']:,} stars")
    
    # Add PyPI statistics if available
    if pypi_data:
        stats['pypi_projects'] = pypi_data.get('projects_on_pypi', 0)
        stats['pypi_total_python'] = pypi_data.get('total_python_projects', 0)
        stats['pypi_detection_rate'] = pypi_data.get('detection_rate', '0%')
        print(f"✅ Found PyPI data with {stats['pypi_projects']:,} projects on PyPI")
    
    print(f"✅ Found {stats['total_users']:,} users in latest data")
    
    # Update README
    update_readme(stats)

if __name__ == "__main__":
    main()
