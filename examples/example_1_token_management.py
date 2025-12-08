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
        token_count = token_manager.get_token_count()
        print(f"✓ Loaded {token_count} GitHub tokens")
    except ValueError as e:
        print(f"✗ Error: {e}")
        print("\nTo use this example, create a .env.tokens file with:")
        print("GITHUB_TOKEN_1=ghp_your_token_here")
        return
    
    # Get the best available token
    token = token_manager.get_token()
    print(f"\n✓ Current token: {token[:10]}...")
    
    # Get all tokens
    all_tokens = token_manager.get_all_tokens()
    print(f"\n✓ Total available tokens: {len(all_tokens)}")
    for i, t in enumerate(all_tokens, 1):
        print(f"  Token {i}: {t[:10]}...")
    
    print("\n" + "=" * 50)
    print("Example completed successfully!")


if __name__ == "__main__":
    main()
