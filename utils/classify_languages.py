#!/usr/bin/env python3
"""
Script to add language classification to existing ranked data.
This is a temporary script for testing the new language-based ranking feature.
"""
import json
import os

def classify_by_name(repo_name):
    """Simple heuristic to classify repos by name until we fetch real language data"""
    name_lower = repo_name.lower()
    
    # Python projects
    python_keywords = ['python', 'django', 'flask', 'pytorch', 'tensorflow', 'pandas', 'numpy']
    if any(kw in name_lower for kw in python_keywords):
        return "Python"
    
    # C++ projects
    cpp_keywords = ['cpp', 'c++', 'tensorflow', 'opencv']
    if any(kw in name_lower for kw in cpp_keywords):
        return "C++"
    
    # Known projects
    known_languages = {
        "vscode": "TypeScript",
        "typescript": "TypeScript",
        "generative-ai": "Python",
        "ml-for-beginners": "Python",
        "system-design-primer": "Python",
        "ai-for-beginners": "Python",
        "web-dev-for-beginners": "JavaScript",
        "powertoys": "C#",
        "terminal": "C++",
        "calculator": "C++",
    }
    
    for key, lang in known_languages.items():
        if key in name_lower:
            return lang
    
    return "Other"

def main():
    input_file = "data/ranked_project_local_seattle.json"
    output_file = "data/ranked_by_language_seattle.json"
    
    # Load existing data
    with open(input_file, 'r') as f:
        repos = json.load(f)
    
    # Add language field
    for repo in repos:
        if 'language' not in repo:
            repo['language'] = classify_by_name(repo['name'])
    
    # Group by language
    language_groups = {"Python": [], "C++": [], "Other": []}
    for repo in repos:
        lang = repo['language']
        if lang == "Python":
            language_groups["Python"].append(repo)
        elif lang == "C++":
            language_groups["C++"].append(repo)
        else:
            language_groups["Other"].append(repo)
    
    # Create output structure
    output_data = {
        "Python": language_groups["Python"][:50],
        "C++": language_groups["C++"][:50],
        "Other": language_groups["Other"][:50],
        "metadata": {
            "total_repos": len(repos),
            "by_language": {
                "Python": len(language_groups["Python"]),
                "C++": len(language_groups["C++"]),
                "Other": len(language_groups["Other"])
            },
            "location": "Seattle",
            "note": "Language classification based on project names (heuristic)"
        }
    }
    
    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"✅ Created {output_file}")
    print(f"\n📊 Summary:")
    print(f"  Python: {output_data['metadata']['by_language']['Python']} projects")
    print(f"  C++: {output_data['metadata']['by_language']['C++']} projects")
    print(f"  Other: {output_data['metadata']['by_language']['Other']} projects")
    print(f"  Total: {output_data['metadata']['total_repos']} projects")

if __name__ == "__main__":
    main()
