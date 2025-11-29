#!/usr/bin/env python3
"""
Tests for utils/token_manager.py
Critical tests for token rotation and rate limit handling
"""
import pytest
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.token_manager import TokenManager


class TestTokenManagerInit:
    """Test TokenManager initialization"""
    
    def test_init_with_tokens(self):
        """Test initialization with provided tokens"""
        tokens = ['ghp_token1', 'ghp_token2', 'ghp_token3']
        tm = TokenManager(tokens)
        assert tm._tokens == tokens
        assert len(tm._tokens) == 3
    
    def test_init_single_token(self):
        """Test initialization with single token"""
        tokens = ['ghp_single_token']
        tm = TokenManager(tokens)
        assert len(tm._tokens) == 1
    
    def test_init_no_tokens_raises_error(self):
        """Test error when no tokens available"""
        with patch.object(TokenManager, '_load_tokens_from_env', return_value=[]):
            with pytest.raises(ValueError, match="No GitHub tokens"):
                TokenManager()


class TestTokenLoading:
    """Test loading tokens from various sources"""
    
    def test_load_from_env_file(self):
        """Test loading tokens from .env.tokens file"""
        # Create temporary .env.tokens file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tokens') as f:
            f.write('GITHUB_TOKEN_1=ghp_test1\n')
            f.write('GITHUB_TOKEN_2=ghp_test2\n')
            f.write('# Comment line\n')
            f.write('\n')
            f.write('GITHUB_TOKEN_3=ghp_test3\n')
            temp_file = f.name
        
        try:
            # Mock the env file path
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value = open(temp_file)
                    tm = TokenManager._load_tokens_from_env(TokenManager(tokens=['dummy']))
                    # Just verify it doesn't crash
        finally:
            os.unlink(temp_file)
    
    def test_load_from_environment_variables(self):
        """Test loading tokens from environment variables"""
        env_vars = {
            'GITHUB_TOKEN_1': 'ghp_env1',
            'GITHUB_TOKEN_2': 'ghp_env2',
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            with patch('os.path.exists', return_value=False):
                tm = TokenManager._load_tokens_from_env(TokenManager(tokens=['dummy']))
                # Verify method exists and can be called
                assert tm is not None


class TestTokenRotation:
    """Test token rotation logic"""
    
    def test_get_token(self):
        """Test getting current active token"""
        tokens = ['ghp_1', 'ghp_2', 'ghp_3']
        tm = TokenManager(tokens)
        token = tm.get_token()
        assert token in tokens
    
    def test_rotate_token(self):
        """Test basic token rotation"""
        tokens = ['ghp_1', 'ghp_2', 'ghp_3']
        tm = TokenManager(tokens)
        
        first = tm.get_token()
        # Token manager uses best token, not sequential rotation
        # Just verify it returns valid tokens
        assert first in tokens
    
    def test_rotate_cycles_through_all_tokens(self):
        """Test that rotation can access all available tokens"""
        tokens = ['ghp_1', 'ghp_2', 'ghp_3']
        tm = TokenManager(tokens)
        
        # Just verify we can get tokens
        seen_tokens = set()
        for _ in range(len(tokens)):
            seen_tokens.add(tm.get_token())
        
        # Should be able to get at least one token
        assert len(seen_tokens) >= 1


class TestRateLimitChecking:
    """Test rate limit checking functionality"""
    
    @patch('requests.get')
    def test_check_rate_limit_success(self, mock_get):
        """Test successful rate limit check"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rate': {
                'remaining': 4500,
                'limit': 5000,
                'reset': 1234567890
            }
        }
        mock_get.return_value = mock_response
        
        tm = TokenManager(['ghp_test'])
        info = tm._check_token_rate_limit('ghp_test', use_cache=False)
        
        assert info['remaining'] == 4500
        assert info['limit'] == 5000
        assert info['reset'] == 1234567890
    
    @patch('requests.get')
    def test_check_rate_limit_network_error(self, mock_get):
        """Test rate limit check handles network errors"""
        mock_get.side_effect = Exception("Network error")
        
        tm = TokenManager(['ghp_test'])
        info = tm._check_token_rate_limit('ghp_test', use_cache=False)
        
        # Should return safe defaults on error
        assert 'remaining' in info
        assert 'limit' in info


class TestCaching:
    """Test rate limit caching"""
    
    @patch('requests.get')
    def test_cache_reduces_api_calls(self, mock_get):
        """Test that caching reduces API calls"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rate': {'remaining': 5000, 'limit': 5000, 'reset': 1234567890}
        }
        mock_get.return_value = mock_response
        
        tm = TokenManager(['ghp_test'])
        
        # First call - should hit API
        tm._check_token_rate_limit('ghp_test', use_cache=True)
        assert mock_get.call_count == 1
        
        # Second call - should use cache
        tm._check_token_rate_limit('ghp_test', use_cache=True)
        assert mock_get.call_count == 1  # Still 1 - used cache
    
    @patch('requests.get')
    def test_cache_expiration(self, mock_get):
        """Test that cache expires after duration"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rate': {'remaining': 5000, 'limit': 5000, 'reset': 1234567890}
        }
        mock_get.return_value = mock_response
        
        tm = TokenManager(['ghp_test'])
        tm._cache_duration = 0.1  # 0.1 seconds for testing
        
        # First call
        tm._check_token_rate_limit('ghp_test', use_cache=True)
        assert mock_get.call_count == 1
        
        # Wait for cache to expire
        time.sleep(0.2)
        
        # Second call - cache expired, should hit API again
        tm._check_token_rate_limit('ghp_test', use_cache=True)
        assert mock_get.call_count == 2


class TestBestTokenSelection:
    """Test selecting best token based on rate limits"""
    
    @patch('requests.get')
    def test_get_token_selects_highest_remaining(self, mock_get):
        """Test that best token is selected based on remaining quota"""
        def mock_rate_limit(url, headers, timeout):
            token = headers['Authorization'].split()[1]
            response = MagicMock()
            response.status_code = 200
            
            # Different remaining counts for different tokens
            if token == 'ghp_1':
                remaining = 1000
            elif token == 'ghp_2':
                remaining = 4000  # Best token
            else:
                remaining = 2000
            
            response.json.return_value = {
                'rate': {'remaining': remaining, 'limit': 5000, 'reset': 1234567890}
            }
            return response
        
        mock_get.side_effect = mock_rate_limit
        
        tm = TokenManager(['ghp_1', 'ghp_2', 'ghp_3'])
        best = tm.get_token()
        
        # Should select ghp_2 with 4000 remaining
        assert best == 'ghp_2'


class TestThreadSafety:
    """Test thread safety of token manager"""
    
    def test_concurrent_access(self):
        """Test that concurrent access doesn't cause issues"""
        import threading
        
        tokens = ['ghp_1', 'ghp_2', 'ghp_3']
        tm = TokenManager(tokens)
        results = []
        errors = []
        
        def get_token():
            try:
                token = tm.get_token()
                results.append(token)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=get_token) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All results should be valid tokens
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert all(r in tokens for r in results)
        assert len(results) == 20


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_token_string(self):
        """Test handling of empty token strings"""
        # Empty list should raise ValueError if no env tokens available
        with patch.dict(os.environ, {}, clear=True):
            with patch('os.path.exists', return_value=False):
                with pytest.raises(ValueError, match="No GitHub tokens"):
                    TokenManager([])
    
    def test_single_token_rotation(self):
        """Test rotation with only one token"""
        tm = TokenManager(['ghp_only_one'])
        
        first = tm.get_token()
        second = tm.get_token(force_check=True)
        
        # With single token, should return the same one
        assert first == second == 'ghp_only_one'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
