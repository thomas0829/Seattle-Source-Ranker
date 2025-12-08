#!/usr/bin/env python3
"""
Example 1: Basic Token Management

This example demonstrates how to use the TokenManager to handle
GitHub API authentication with automatic token rotation.
"""

from seattle_source_ranker.tokens import TokenManager

def main():
    """Demonstrate basic token management"""
    
    print("Seattle Source Ranker - Token Management Example")
    print("=" * 50)
    
    # Initialize TokenManager
    # It will automatically load tokens from .env.tokens or environment variables
    try:
        token_manager = TokenManager()
        print(f"✓ Loaded {len(token_manager.tokens)} GitHub tokens")
    except ValueError as e:
        print(f"✗ Error: {e}")
        print("\nTo use this example, create a .env.tokens file with:")
        print("GITHUB_TOKEN_1=ghp_your_token_here")
        return
    
    # Get the best available token
    token = token_manager.get_token()
    print(f"\n✓ Current token: {token[:10]}...")
    
    # Check rate limit for current token
    try:
        limit_info = token_manager.check_rate_limit()
        print(f"\n✓ Rate limit info:")
        print(f"  - Remaining: {limit_info['remaining']}/{limit_info['limit']}")
        print(f"  - Reset time: {limit_info['reset']}")
    except Exception as e:
        print(f"✗ Could not check rate limit: {e}")
    
    # Rotate to next token
    next_token = token_manager.rotate_token()
    print(f"\n✓ Rotated to next token: {next_token[:10]}...")
    
    print("\n" + "=" * 50)
    print("Example completed successfully!")


if __name__ == "__main__":
    main()
