#!/usr/bin/env python3
"""
Example 3: Project Scoring

This example demonstrates how to calculate SSR scores for GitHub projects
using the scoring algorithm.
"""

from seattle_source_ranker.scoring import (
    calculate_github_score,
    age_factor,
    activity_factor,
    health_factor
)
from datetime import datetime, timedelta, timezone

def main():
    """Demonstrate project scoring"""
    
    print("Seattle Source Ranker - Project Scoring Example")
    print("=" * 50)
    
    # Create sample projects
    now = datetime.now(timezone.utc)
    
    projects = [
        {
            'name': 'High Quality Project',
            'stars': 5000,
            'forks': 800,
            'watchers': 300,
            'open_issues': 50,
            'created_at': (now - timedelta(days=1095)).strftime("%Y-%m-%dT%H:%M:%SZ"),  # 3 years
            'pushed_at': (now - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),  # 5 days ago
        },
        {
            'name': 'Popular but Stale',
            'stars': 10000,
            'forks': 1500,
            'watchers': 500,
            'open_issues': 200,
            'created_at': (now - timedelta(days=2920)).strftime("%Y-%m-%dT%H:%M:%SZ"),  # 8 years
            'pushed_at': (now - timedelta(days=730)).strftime("%Y-%m-%dT%H:%M:%SZ"),  # 2 years ago
        },
        {
            'name': 'New Rising Star',
            'stars': 500,
            'forks': 50,
            'watchers': 100,
            'open_issues': 10,
            'created_at': (now - timedelta(days=180)).strftime("%Y-%m-%dT%H:%M:%SZ"),  # 6 months
            'pushed_at': (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),  # Yesterday
        },
    ]
    
    print("\nScoring projects:")
    print("-" * 50)
    
    for project in projects:
        score = calculate_github_score(project)
        
        # Calculate individual factors
        age = age_factor(project['created_at'])
        activity = activity_factor(project['pushed_at'], project['created_at'])
        health = health_factor(project['stars'], project['open_issues'])
        
        print(f"\n{project['name']}:")
        print(f"  SSR Score: {score:,.2f}")
        print(f"  Stars: {project['stars']:,}")
        print(f"  Age Factor: {age:.2f}")
        print(f"  Activity Factor: {activity:.2f}")
        print(f"  Health Factor: {health:.2f}")
    
    # Sort by score
    projects_with_scores = [(p, calculate_github_score(p)) for p in projects]
    projects_with_scores.sort(key=lambda x: x[1], reverse=True)
    
    print("\n" + "=" * 50)
    print("Ranking:")
    for i, (project, score) in enumerate(projects_with_scores, 1):
        print(f"{i}. {project['name']:30s} Score: {score:,.2f}")
    
    print("\n" + "=" * 50)
    print("Example completed successfully!")


if __name__ == "__main__":
    main()
