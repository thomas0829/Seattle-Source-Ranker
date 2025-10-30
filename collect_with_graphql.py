#!/usr/bin/env python3
"""
Collect Seattle projects using GraphQL API
Direct repository search with cursor pagination - bypasses 1,000 result limit
"""
import os
import json
from datetime import datetime
from collectors.graphql_client import GitHubGraphQLClient


def collect_seattle_projects_graphql(target_count: int = 10000, output_file: str = "data/seattle_projects_10000.json"):
    """
    Collect Seattle projects using GraphQL API with cursor pagination.
    
    Args:
        target_count: Target number of projects to collect
        output_file: Output JSON file path
    """
    
    print("=" * 60)
    print("🚀 Seattle Project Collector (GraphQL)")
    print("=" * 60)
    
    # Initialize GraphQL client
    client = GitHubGraphQLClient()
    
    # Search query for Seattle repositories
    # Note: GraphQL search doesn't support location-based repo search directly
    # We need to search by topics, user location in bio, or other criteria
    
    # Strategy: Search repos with Seattle-related topics or owners
    search_queries = [
        "topic:seattle stars:>10",
        "topic:seattle-area stars:>5",
        "location:seattle in:readme stars:>10",
        "location:redmond in:readme stars:>5",
        "location:bellevue in:readme stars:>5",
    ]
    
    all_projects = []
    seen_repos = set()  # Deduplicate by name_with_owner
    
    for query in search_queries:
        print(f"\n📊 Searching: {query}")
        
        try:
            repos = client.fetch_all_repositories(
                query=query,
                max_results=target_count - len(all_projects),
                progress_bar=True
            )
            
            # Convert to our format and deduplicate
            for repo in repos:
                name_with_owner = repo.get('name_with_owner')
                
                if not name_with_owner or name_with_owner in seen_repos:
                    continue
                
                seen_repos.add(name_with_owner)
                
                # Extract owner info (already flattened by GraphQL client)
                owner = repo.get('owner', {})
                owner_data = {
                    'login': owner.get('login', ''),
                    'type': 'User',  # GraphQL client doesn't distinguish
                    'avatar_url': ''  # Not fetched in GraphQL query
                }
                
                # Build project dict (GraphQL client already flattened the structure)
                project = {
                    'name_with_owner': name_with_owner,
                    'name': repo.get('name', ''),
                    'description': repo.get('description', ''),
                    'url': repo.get('url', ''),
                    'stars': repo.get('stars', 0),
                    'forks': repo.get('forks', 0),
                    'watchers': repo.get('watchers', 0),
                    'open_issues': repo.get('open_issues', 0),
                    'created_at': repo.get('created_at', ''),
                    'updated_at': repo.get('updated_at', ''),
                    'pushed_at': repo.get('pushed_at', ''),
                    'language': repo.get('language'),
                    'license': repo.get('license'),
                    'owner': owner_data,
                    'is_fork': False,  # Can add this to GraphQL query if needed
                    'is_archived': False  # Can add this to GraphQL query if needed
                }
                
                all_projects.append(project)
                
                if len(all_projects) >= target_count:
                    break
            
            print(f"✅ Total collected: {len(all_projects)}/{target_count}")
            
            if len(all_projects) >= target_count:
                break
                
        except Exception as e:
            print(f"❌ Error with query '{query}': {e}")
            continue
    
    # Sort by stars (descending)
    all_projects.sort(key=lambda x: x['stars'], reverse=True)
    
    # Save to file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_projects, f, indent=2, ensure_ascii=False)
    
    # Save metadata
    metadata = {
        'total_projects': len(all_projects),
        'collection_date': datetime.now().isoformat(),
        'method': 'graphql',
        'queries_used': search_queries,
        'top_project': all_projects[0]['name_with_owner'] if all_projects else None,
        'total_stars': sum(p['stars'] for p in all_projects)
    }
    
    metadata_file = output_file.replace('.json', '_metadata.json')
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"✅ Collection Complete!")
    print(f"{'=' * 60}")
    print(f"📦 Total projects: {len(all_projects)}")
    print(f"⭐ Total stars: {metadata['total_stars']:,}")
    print(f"🏆 Top project: {metadata['top_project']}")
    print(f"💾 Saved to: {output_file}")
    print(f"📊 Metadata: {metadata_file}")
    
    return all_projects


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect Seattle projects using GraphQL')
    parser.add_argument('--target', type=int, default=10000, help='Target number of projects')
    parser.add_argument('--output', type=str, default='data/seattle_projects_10000.json', help='Output file path')
    
    args = parser.parse_args()
    
    collect_seattle_projects_graphql(
        target_count=args.target,
        output_file=args.output
    )
