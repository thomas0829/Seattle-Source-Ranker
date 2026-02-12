"""
Test Collection Worker module
"""
import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from seattle_source_ranker.collector.collection_worker import fetch_users_batch_task


class TestFetchUsersBatchTask:
    """Test fetch_users_batch_task function"""
    
    def test_task_exists(self):
        """Test that task is registered"""
        assert fetch_users_batch_task is not None
        assert hasattr(fetch_users_batch_task, 'name')
        # Task name should be the fully qualified module path
        assert fetch_users_batch_task.name == "seattle_source_ranker.collector.collection_worker.fetch_users_batch"
    
    def test_task_max_retries(self):
        """Test task max_retries configuration"""
        assert fetch_users_batch_task.max_retries == 3
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_fetch_users_batch_empty_list(self, mock_get, mock_get_tm):
        """Test fetching batch with empty user list"""
        # Mock TokenManager
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 5
        mock_get_tm.return_value = mock_tm
        
        # Call task with empty list (Celery handles self automatically)
        result = fetch_users_batch_task([])
        
        # Should return empty results
        assert isinstance(result, dict)
        assert result['batch_size'] == 0
        assert result['total_repos'] == 0
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    def test_fetch_users_batch_token_manager_available(self, mock_get_tm):
        """Test that task attempts to use TokenManager"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 3
        mock_tm.get_token.return_value = 'ghp_test_token'
        mock_get_tm.return_value = mock_tm
        
        # Call task - it will try to fetch but we're just testing initialization
        with patch('requests.get'):
            result = fetch_users_batch_task(['testuser'])
        
        # TokenManager should have been called
        mock_get_tm.assert_called_once()
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('os.getenv')
    def test_fetch_users_batch_fallback_token(self, mock_getenv, mock_get_tm):
        """Test fallback to GITHUB_TOKEN when TokenManager fails"""
        # Make TokenManager raise exception
        mock_get_tm.side_effect = Exception("TokenManager not available")
        mock_getenv.return_value = None  # No fallback token
        
        result = fetch_users_batch_task(['testuser'])
        
        # Should return with 0 successful users
        assert result['successful_users'] == 0
        assert result['failed_users'] == 1


class TestHelperFunctions:
    """Test helper functions in collection_worker"""
    
    def test_imports(self):
        """Test that module can be imported"""
        from seattle_source_ranker.collector import collection_worker
        assert collection_worker is not None
    
    def test_celery_app_import(self):
        """Test that celery_app is imported"""
        from seattle_source_ranker.collector.collection_worker import celery_app
        assert celery_app is not None


class TestRateLimitHandling:
    """Test rate limit handling logic"""
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_fetch_with_rate_limit_response(self, mock_get, mock_get_tm):
        """Test handling rate limit in responses"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 2
        mock_tm.get_token.return_value = 'ghp_token1'
        mock_get_tm.return_value = mock_tm
        
        # Mock response with low rate limit
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'X-RateLimit-Remaining': '5',
            'X-RateLimit-Reset': '1234567890'
        }
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        result = fetch_users_batch_task(['testuser'])
        
        # Should complete despite low rate limit
        assert isinstance(result, dict)
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_fetch_with_user_not_found(self, mock_get, mock_get_tm):
        """Test handling 404 user not found"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 1
        mock_tm.get_token.return_value = 'ghp_token'
        mock_get_tm.return_value = mock_tm
        
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {'X-RateLimit-Remaining': '5000'}
        mock_get.return_value = mock_response
        
        result = fetch_users_batch_task(['nonexistent_user'])
        
        assert result['failed_users'] == 1
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_fetch_with_successful_user(self, mock_get, mock_get_tm):
        """Test fetching successful user with repos"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 1
        mock_tm.get_token.return_value = 'ghp_token'
        mock_get_tm.return_value = mock_tm
        
        # Mock successful repo response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'X-RateLimit-Remaining': '5000'}
        mock_response.json.return_value = [
            {
                'name': 'test-repo',
                'stargazers_count': 100,
                'forks_count': 50,
                'watchers_count': 80,
                'language': 'Python'
            }
        ]
        mock_get.return_value = mock_response
        
        result = fetch_users_batch_task(['realuser'])
        
        assert result['total_repos'] >= 0
        assert isinstance(result['repos'], list)
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_fetch_with_multiple_users(self, mock_get, mock_get_tm):
        """Test fetching multiple users"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 1
        mock_tm.get_token.return_value = 'ghp_token'
        mock_get_tm.return_value = mock_tm
        
        # Mock responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'X-RateLimit-Remaining': '5000'}
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        result = fetch_users_batch_task(['user1', 'user2', 'user3'])
        
        assert result['batch_size'] == 3
        assert isinstance(result, dict)
        assert 'completed_at' in result


class TestRequestExceptionHandling:
    """Test exception handling"""
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_fetch_with_timeout(self, mock_get, mock_get_tm):
        """Test handling request timeout"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 1
        mock_tm.get_token.return_value = 'ghp_token'
        mock_get_tm.return_value = mock_tm
        
        # Mock timeout exception
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        
        result = fetch_users_batch_task(['testuser'])
        
        assert result['failed_users'] == 1
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_fetch_with_connection_error(self, mock_get, mock_get_tm):
        """Test handling connection error"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 1
        mock_tm.get_token.return_value = 'ghp_token'
        mock_get_tm.return_value = mock_tm
        
        # Mock connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = fetch_users_batch_task(['testuser'])
        
        assert result['failed_users'] == 1


class TestRepoProcessing:
    """Test repository processing and filtering logic"""
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_repo_filtering_archived(self, mock_get, mock_get_tm):
        """Test that archived repos are filtered out"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 3
        mock_tm.get_token.return_value = 'ghp_test_token'
        mock_get_tm.return_value = mock_tm
        
        # Mock response with archived repo
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'X-RateLimit-Remaining': '5000'}
        mock_response.json.return_value = [
            {
                "full_name": "testuser/archived-repo",
                "name": "archived-repo",
                "html_url": "https://github.com/testuser/archived-repo",
                "stargazers_count": 10,
                "forks_count": 5,
                "watchers_count": 3,
                "created_at": "2020-01-01T00:00:00Z",
                "updated_at": "2020-01-01T00:00:00Z",
                "fork": False,
                "archived": True,
                "size": 100,
                "owner": {"login": "testuser", "type": "User"}
            }
        ]
        mock_get.return_value = mock_response
        
        result = fetch_users_batch_task(['testuser'])
        
        # Should have no repos due to filtering
        assert result['total_repos'] == 0
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_repo_filtering_fork(self, mock_get, mock_get_tm):
        """Test that fork repos are filtered out"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 3
        mock_tm.get_token.return_value = 'ghp_test_token'
        mock_get_tm.return_value = mock_tm
        
        # Mock response with fork repo
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'X-RateLimit-Remaining': '5000'}
        mock_response.json.return_value = [
            {
                "full_name": "testuser/forked-repo",
                "name": "forked-repo",
                "html_url": "https://github.com/testuser/forked-repo",
                "stargazers_count": 10,
                "forks_count": 5,
                "watchers_count": 3,
                "created_at": "2020-01-01T00:00:00Z",
                "updated_at": "2020-01-01T00:00:00Z",
                "fork": True,
                "archived": False,
                "size": 100,
                "owner": {"login": "testuser", "type": "User"}
            }
        ]
        mock_get.return_value = mock_response
        
        result = fetch_users_batch_task(['testuser'])
        
        # Should have no repos due to filtering
        assert result['total_repos'] == 0
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_repo_filtering_empty_size(self, mock_get, mock_get_tm):
        """Test that empty repos (size=0) are filtered out"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 3
        mock_tm.get_token.return_value = 'ghp_test_token'
        mock_get_tm.return_value = mock_tm
        
        # Mock response with empty repo
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'X-RateLimit-Remaining': '5000'}
        mock_response.json.return_value = [
            {
                "full_name": "testuser/empty-repo",
                "name": "empty-repo",
                "html_url": "https://github.com/testuser/empty-repo",
                "stargazers_count": 0,
                "forks_count": 0,
                "watchers_count": 0,
                "created_at": "2020-01-01T00:00:00Z",
                "updated_at": "2020-01-01T00:00:00Z",
                "fork": False,
                "archived": False,
                "size": 0,
                "owner": {"login": "testuser", "type": "User"}
            }
        ]
        mock_get.return_value = mock_response
        
        result = fetch_users_batch_task(['testuser'])
        
        # Should have no repos due to filtering
        assert result['total_repos'] == 0
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_repo_filtering_disabled(self, mock_get, mock_get_tm):
        """Test that disabled repos are filtered out"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 3
        mock_tm.get_token.return_value = 'ghp_test_token'
        mock_get_tm.return_value = mock_tm
        
        # Mock response with disabled repo
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'X-RateLimit-Remaining': '5000'}
        mock_response.json.return_value = [
            {
                "full_name": "testuser/disabled-repo",
                "name": "disabled-repo",
                "html_url": "https://github.com/testuser/disabled-repo",
                "stargazers_count": 10,
                "forks_count": 5,
                "watchers_count": 3,
                "created_at": "2020-01-01T00:00:00Z",
                "updated_at": "2020-01-01T00:00:00Z",
                "fork": False,
                "archived": False,
                "disabled": True,
                "size": 100,
                "owner": {"login": "testuser", "type": "User"}
            }
        ]
        mock_get.return_value = mock_response
        
        result = fetch_users_batch_task(['testuser'])
        
        # Should have no repos due to filtering
        assert result['total_repos'] == 0
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_valid_repo_extraction(self, mock_get, mock_get_tm):
        """Test that valid repos are properly extracted"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 3
        mock_tm.get_token.return_value = 'ghp_test_token'
        mock_get_tm.return_value = mock_tm
        
        # Mock response with valid repo
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'X-RateLimit-Remaining': '5000'}
        mock_response.json.return_value = [
            {
                "full_name": "testuser/valid-repo",
                "name": "valid-repo",
                "description": "A valid repository",
                "html_url": "https://github.com/testuser/valid-repo",
                "stargazers_count": 10,
                "forks_count": 5,
                "watchers_count": 3,
                "subscribers_count": 2,
                "language": "Python",
                "topics": ["python", "test"],
                "created_at": "2020-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "pushed_at": "2023-06-01T00:00:00Z",
                "open_issues_count": 1,
                "has_issues": True,
                "fork": False,
                "archived": False,
                "size": 1000,
                "owner": {"login": "testuser", "type": "User"}
            }
        ]
        mock_get.return_value = mock_response
        
        result = fetch_users_batch_task(['testuser'])
        
        # Should have the repo with all fields
        assert result['total_repos'] == 1


class TestMultiTokenRateLimitHandling:
    """Test multi-token rate limit handling"""
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    @patch('time.sleep')
    def test_token_rotation_on_low_rate_limit(self, mock_sleep, mock_get, mock_get_tm):
        """Test token rotation when rate limit is low"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 3
        mock_tm.get_token.side_effect = ['token1', 'token2', 'token3', 'token2']
        mock_tm.get_all_token_status.return_value = [
            ('token2', 1000, 1234567890),
            ('token3', 500, 1234567891)
        ]
        mock_get_tm.return_value = mock_tm
        
        # First response: low rate limit
        mock_response_low = Mock()
        mock_response_low.status_code = 200
        mock_response_low.headers = {
            'X-RateLimit-Remaining': '50',
            'X-RateLimit-Reset': '1234567890'
        }
        mock_response_low.json.return_value = []
        
        mock_get.return_value = mock_response_low
        
        result = fetch_users_batch_task(['testuser'])
        
        # Should have processed the request
        assert isinstance(result, dict)
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    @patch('time.sleep')
    def test_multi_token_check_finds_available(self, mock_sleep, mock_get, mock_get_tm):
        """Test multi-token check finds available token"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 3
        mock_tm.get_token.side_effect = ['token1', 'token2']
        
        # Setup token status responses
        def get_side_effect(url, headers, timeout):
            if 'rate_limit' in url:
                # Rate limit check response
                mock_resp = Mock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    'resources': {
                        'core': {
                            'remaining': 1000,
                            'limit': 5000,
                            'reset': 1234567890
                        }
                    }
                }
                return mock_resp
            else:
                # Regular API response
                mock_resp = Mock()
                mock_resp.status_code = 200
                mock_resp.headers = {
                    'X-RateLimit-Remaining': '45',
                    'X-RateLimit-Reset': '1234567890'
                }
                mock_resp.json.return_value = []
                return mock_resp
        
        mock_get.side_effect = get_side_effect
        mock_get_tm.return_value = mock_tm
        
        result = fetch_users_batch_task(['testuser'])
        
        assert isinstance(result, dict)
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_api_error_status_code(self, mock_get, mock_get_tm):
        """Test handling of non-200/404/403 API error"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 3
        mock_tm.get_token.return_value = 'ghp_test_token'
        mock_get_tm.return_value = mock_tm
        
        # Mock 500 error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.headers = {'X-RateLimit-Remaining': '5000'}
        mock_get.return_value = mock_response
        
        result = fetch_users_batch_task(['testuser'])
        
        assert result['failed_users'] > 0


class TestFollowerValidation:
    """Test follower validation logic"""
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_user_with_few_repos_and_enough_followers(self, mock_get, mock_get_tm):
        """Test user with <10 repos but >=5 followers passes"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 3
        mock_tm.get_token.return_value = 'ghp_test_token'
        mock_get_tm.return_value = mock_tm
        
        # First call: repos endpoint
        mock_repos_response = Mock()
        mock_repos_response.status_code = 200
        mock_repos_response.headers = {'X-RateLimit-Remaining': '5000'}
        mock_repos_response.json.return_value = [
            {
                "full_name": "user/repo1",
                "name": "repo1",
                "html_url": "https://github.com/user/repo1",
                "stargazers_count": 5,
                "forks_count": 2,
                "watchers_count": 1,
                "subscribers_count": 1,
                "created_at": "2020-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "fork": False,
                "archived": False,
                "size": 100,
                "owner": {"login": "testuser", "type": "User"}
            }
        ] * 5  # 5 repos
        
        # Second call: user info endpoint
        mock_user_response = Mock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            "login": "testuser",
            "followers": 10  # Enough followers
        }
        
        mock_get.side_effect = [mock_repos_response, mock_user_response]
        
        result = fetch_users_batch_task(['testuser'])
        
        # User should be accepted
        assert result['total_repos'] == 5
        assert result['successful_users'] == 1
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_user_with_few_repos_and_not_enough_followers(self, mock_get, mock_get_tm):
        """Test user with <10 repos and <5 followers is filtered"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 3
        mock_tm.get_token.return_value = 'ghp_test_token'
        mock_get_tm.return_value = mock_tm
        
        # First call: repos endpoint (3 repos)
        mock_repos_response = Mock()
        mock_repos_response.status_code = 200
        mock_repos_response.headers = {'X-RateLimit-Remaining': '5000'}
        mock_repos_response.json.return_value = [
            {
                "full_name": "user/repo1",
                "name": "repo1",
                "html_url": "https://github.com/user/repo1",
                "stargazers_count": 1,
                "forks_count": 0,
                "watchers_count": 0,
                "subscribers_count": 0,
                "created_at": "2020-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "fork": False,
                "archived": False,
                "size": 100,
                "owner": {"login": "testuser", "type": "User"}
            }
        ] * 3
        
        # Second call: user info endpoint
        mock_user_response = Mock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            "login": "testuser",
            "followers": 2  # Not enough followers
        }
        
        mock_get.side_effect = [mock_repos_response, mock_user_response]
        
        result = fetch_users_batch_task(['testuser'])
        
        # User should be filtered
        assert result['filtered_users'] == 1
        assert result['failure_reasons']['filtered_criteria'] == 1
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_user_follower_check_fails_but_has_repos(self, mock_get, mock_get_tm):
        """Test user accepted when follower check fails but has repos"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 3
        mock_tm.get_token.return_value = 'ghp_test_token'
        mock_get_tm.return_value = mock_tm
        
        # First call: repos endpoint
        mock_repos_response = Mock()
        mock_repos_response.status_code = 200
        mock_repos_response.headers = {'X-RateLimit-Remaining': '5000'}
        mock_repos_response.json.return_value = [
            {
                "full_name": "user/repo1",
                "name": "repo1",
                "html_url": "https://github.com/user/repo1",
                "stargazers_count": 1,
                "forks_count": 0,
                "watchers_count": 0,
                "subscribers_count": 0,
                "created_at": "2020-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "fork": False,
                "archived": False,
                "size": 100,
                "owner": {"login": "testuser", "type": "User"}
            }
        ] * 5
        
        # Second call: user info endpoint (404)
        mock_user_response = Mock()
        mock_user_response.status_code = 404
        
        mock_get.side_effect = [mock_repos_response, mock_user_response]
        
        result = fetch_users_batch_task(['testuser'])
        
        # User should be accepted (has repos, follower check failed)
        assert result['total_repos'] == 5
        assert result['successful_users'] == 1
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_user_no_repos_and_follower_check_fails(self, mock_get, mock_get_tm):
        """Test user filtered when no repos and follower check fails"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 3
        mock_tm.get_token.return_value = 'ghp_test_token'
        mock_get_tm.return_value = mock_tm
        
        # First call: repos endpoint (all filtered out)
        mock_repos_response = Mock()
        mock_repos_response.status_code = 200
        mock_repos_response.headers = {'X-RateLimit-Remaining': '5000'}
        mock_repos_response.json.return_value = [
            {
                "full_name": "user/repo1",
                "name": "repo1",
                "html_url": "https://github.com/user/repo1",
                "stargazers_count": 1,
                "forks_count": 0,
                "watchers_count": 0,
                "created_at": "2020-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "fork": True,  # Fork - will be filtered
                "archived": False,
                "size": 100,
                "owner": {"login": "testuser", "type": "User"}
            }
        ]
        
        # Second call: user info endpoint (fails)
        mock_user_response = Mock()
        mock_user_response.status_code = 500
        
        mock_get.side_effect = [mock_repos_response, mock_user_response]
        
        result = fetch_users_batch_task(['testuser'])
        
        # User should be filtered (no valid repos and can't verify)
        assert result['filtered_users'] == 1


class TestPaginationLogic:
    """Test pagination handling"""
    
    @patch('seattle_source_ranker.tokens.get_token_manager')
    @patch('requests.get')
    def test_pagination_multiple_pages(self, mock_get, mock_get_tm):
        """Test handling multiple pages of repos"""
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 3
        mock_tm.get_token.return_value = 'ghp_test_token'
        mock_get_tm.return_value = mock_tm
        
        # First page: 100 repos
        mock_response_page1 = Mock()
        mock_response_page1.status_code = 200
        mock_response_page1.headers = {'X-RateLimit-Remaining': '5000'}
        mock_response_page1.json.return_value = [
            {
                "full_name": f"user/repo{i}",
                "name": f"repo{i}",
                "html_url": f"https://github.com/user/repo{i}",
                "stargazers_count": 1,
                "forks_count": 0,
                "watchers_count": 0,
                "subscribers_count": 0,
                "created_at": "2020-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "fork": False,
                "archived": False,
                "size": 100,
                "owner": {"login": "testuser", "type": "User"}
            }
            for i in range(100)
        ]
        
        # Second page: 50 repos (less than 100, stops pagination)
        mock_response_page2 = Mock()
        mock_response_page2.status_code = 200
        mock_response_page2.headers = {'X-RateLimit-Remaining': '4999'}
        mock_response_page2.json.return_value = [
            {
                "full_name": f"user/repo{i}",
                "name": f"repo{i}",
                "html_url": f"https://github.com/user/repo{i}",
                "stargazers_count": 1,
                "forks_count": 0,
                "watchers_count": 0,
                "subscribers_count": 0,
                "created_at": "2020-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "fork": False,
                "archived": False,
                "size": 100,
                "owner": {"login": "testuser", "type": "User"}
            }
            for i in range(100, 150)
        ]
        
        mock_get.side_effect = [mock_response_page1, mock_response_page2]
        
        result = fetch_users_batch_task(['testuser'])
        
        # Should have repos from both pages
        assert result['total_repos'] == 150
        assert result['successful_users'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
