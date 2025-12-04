"""
Token Manager for rotating multiple GitHub Personal Access Tokens
"""
import os
import threading
import requests
import time
from typing import List, Optional, Dict, Any


class TokenManager:
    """Manages multiple GitHub tokens with smart selection based on rate limits"""

    def __init__(self, tokens: Optional[List[str]] = None):
        """
        Initialize TokenManager with a list of tokens

        Args:
            tokens: List of GitHub Personal Access Tokens
                   If None, will read from environment variables
        """
        self._tokens = tokens or self._load_tokens_from_env()
        self._current_index = 0
        self._lock = threading.Lock()

        # Cache for rate limit info (avoid excessive API calls)
        self._rate_limit_cache = {}
        self._cache_duration = 60  # Cache for 60 seconds

        if not self._tokens:
            raise ValueError("No GitHub tokens provided. Please set GITHUB_TOKEN_1, GITHUB_TOKEN_2, etc.")

        # Only print in main process (not in worker processes)
        import multiprocessing
        if multiprocessing.current_process().name == 'MainProcess':
            print("✅ TokenManager initialized with {len(self._tokens)} tokens")

    def _load_tokens_from_env(self) -> List[str]:
        """Load tokens from environment variables"""
        tokens = []

        # Try to load from .env.tokens file first
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.tokens')
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key.startswith('GITHUB_TOKEN_') and value:
                            tokens.append(value)

        # Also check environment variables
        i = 1
        while True:
            token = os.getenv(f'GITHUB_TOKEN_{i}')
            if not token:
                break
            if token not in tokens:  # Avoid duplicates
                tokens.append(token)
            i += 1

        # Fallback to single GITHUB_TOKEN
        if not tokens:
            single_token = os.getenv('GITHUB_TOKEN')
            if single_token:
                tokens.append(single_token)

        return tokens

    def _check_token_rate_limit(self, token: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Check rate limit for a specific token with caching

        Args:
            token: GitHub token to check
            use_cache: Whether to use cached data

        Returns:
            Dict with 'remaining', 'limit', 'reset' keys
        """
        # Check cache first
        if use_cache and token in self._rate_limit_cache:
            cache_entry = self._rate_limit_cache[token]
            if time.time() - cache_entry['cached_at'] < self._cache_duration:
                return cache_entry['data']

        try:
            response = requests.get(
                'https://api.github.com/rate_limit',
                headers={'Authorization': f'token {token}'},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                result = {
                    'remaining': data['rate']['remaining'],
                    'limit': data['rate']['limit'],
                    'reset': data['rate']['reset']
                }

                # Update cache
                self._rate_limit_cache[token] = {
                    'data': result,
                    'cached_at': time.time()
                }

                return result
        except Exception:
            pass

        # Return default if check fails
        return {'remaining': 0, 'limit': 5000, 'reset': int(time.time()) + 3600}

    def get_token(self, force_check: bool = False) -> str:
        """
        Get best available token with highest remaining quota (thread-safe)
        Uses cached rate limit data by default for performance

        Args:
            force_check: Force fresh rate limit check (ignore cache)

        Returns:
            GitHub token with most remaining quota
        """
        with self._lock:
            # Try to find token with best rate limit
            best_token = None
            best_remaining = -1

            for token in self._tokens:
                rate_info = self._check_token_rate_limit(token, use_cache=not force_check)
                if rate_info['remaining'] > best_remaining:
                    best_remaining = rate_info['remaining']
                    best_token = token

            # If we found a good token, return it
            if best_token and best_remaining > 0:
                return best_token

            # Fallback to round-robin if all tokens exhausted
            token = self._tokens[self._current_index]
            self._current_index = (self._current_index + 1) % len(self._tokens)
            return token

    def get_token_count(self) -> int:
        """Get total number of tokens"""
        return len(self._tokens)

    def get_all_tokens(self) -> List[str]:
        """Get all tokens (useful for debugging)"""
        return self._tokens.copy()


# Global singleton instance
_token_manager_instance: Optional[TokenManager] = None


def get_token_manager() -> TokenManager:
    """
    Get or create global TokenManager instance

    Returns:
        Global TokenManager instance
    """
    global _token_manager_instance
    if _token_manager_instance is None:
        _token_manager_instance = TokenManager()
    return _token_manager_instance


def reset_token_manager():
    """Reset global TokenManager instance (useful for testing)"""
    global _token_manager_instance
    _token_manager_instance = None
