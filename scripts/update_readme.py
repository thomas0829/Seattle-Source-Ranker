#!/usr/bin/env python3
"""
Update README.md with latest collection statistics
"""

import json
import re
from datetime import datetime
from pathlib import Path

def load_latest_data():
    """Load the latest collection data"""
    data_dir = Path(__file__).parent.parent / "data"
    
    # Find latest seattle_projects_*.json file
    project_files = list(data_dir.glob('seattle_projects_*.json'))
    if project_files:
        latest_file = max(project_files)
        print(f"📂 Loading data from {latest_file.name}")
        
        # Check if it's a Git LFS pointer
        with open(latest_file, 'r') as f:
            first_line = f.readline()
            if first_line.startswith('version https://git-lfs.github.com'):
                print(f"⚠️  Warning: {latest_file.name} is a Git LFS pointer, not actual data")
                return None
            f.seek(0)
            return json.load(f)
    
    return None

def update_readme(stats):
    """Update README.md with latest statistics"""
    readme_path = Path(__file__).parent.parent / "README.md"
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract statistics
    total_projects = stats.get('total_projects', 0)
    total_stars = stats.get('total_stars', 0)
    successful_users = stats.get('successful_users', 0)
    failed_users = stats.get('failed_users', 0)
    filtered_users = stats.get('filtered_users', 0)
    collected_at = stats.get('collected_at', '')
    
    # Format date
    if collected_at:
        try:
            dt = datetime.fromisoformat(collected_at.replace('Z', '+00:00'))
            date_str = dt.strftime('%b %d, %Y')
        except:
            date_str = datetime.now().strftime('%b %d, %Y')
    else:
        date_str = datetime.now().strftime('%b %d, %Y')
    
    # Calculate success rate
    total_checked = successful_users + failed_users + filtered_users
    if total_checked > 0:
        success_rate = (successful_users / (successful_users + failed_users)) * 100
    else:
        success_rate = 0
    
    # Update statistics section
    stats_pattern = r'\*\*Latest Collection Stats \([^)]+\):\*\*\n- Total Projects: \*\*[0-9,]+\*\*\n- Total Stars: \*\*[0-9,]+\*\*\n- Users Searched: \*\*[0-9,]+\*\*\n- Users with Valid Projects: \*\*[0-9,]+\*\* \([0-9.]+%\)\n- Success Rate: \*\*[0-9.]+%\*\*'
    
    stats_text = f"""**Latest Collection Stats ({date_str}):**
- Total Projects: **{total_projects:,}**
- Total Stars: **{total_stars:,}**
- Users Searched: **{total_checked:,}**
- Users with Valid Projects: **{successful_users:,}** ({(successful_users/total_checked*100):.1f}%)
- Success Rate: **{success_rate:.2f}%**"""
    
    # Replace statistics
    new_content = re.sub(stats_pattern, stats_text, content)
    
    # If pattern not found, try to find the section and update it
    if new_content == content:
        # Try simpler pattern
        stats_pattern2 = r'\*\*Latest Collection Stats.*?\n- Success Rate: \*\*[0-9.]+%\*\*'
        new_content = re.sub(stats_pattern2, stats_text, content, flags=re.DOTALL)
    
    # Write back
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ README.md updated successfully!")
    print(f"   Projects: {total_projects:,}")
    print(f"   Stars: {total_stars:,}")
    print(f"   Users: {successful_users:,}/{total_checked:,}")
    print(f"   Success Rate: {success_rate:.2f}%")

def main():
    print("📝 Updating README.md with latest statistics...")
    
    # Load data
    data = load_latest_data()
    
    if not data:
        print("❌ No data file found!")
        return
    
    # Update README
    update_readme(data)

if __name__ == "__main__":
    main()
