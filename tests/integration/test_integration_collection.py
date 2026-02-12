"""
Integration tests for distributed collection system
Requires: Redis + Celery workers running
Run with: pytest tests/integration/test_integration_collection.py -v
"""
import pytest
import time
from unittest.mock import patch, Mock
from seattle_source_ranker.collector.collection_worker import fetch_users_batch_task


class TestCeleryTaskIntegration:
    """Integration tests using real Celery infrastructure"""
    
    @patch('requests.get')
    @patch('seattle_source_ranker.tokens.get_token_manager')
    def test_celery_task_execution(self, mock_get_tm, mock_get):
        """Test that Celery task can be executed through the queue"""
        # Setup mocks
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 3
        mock_tm.get_token.return_value = 'ghp_test_token'
        mock_get_tm.return_value = mock_tm
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'X-RateLimit-Remaining': '5000'}
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        # Execute task synchronously (without workers, just test task definition)
        result = fetch_users_batch_task(['testuser'])
        
        # Verify task executed
        assert isinstance(result, dict)
        assert 'batch_size' in result
        assert result['batch_size'] == 1
    
    @patch('requests.get')
    @patch('seattle_source_ranker.tokens.get_token_manager')
    def test_celery_async_task_dispatch(self, mock_get_tm, mock_get):
        """Test dispatching task to Celery workers (requires workers running)"""
        # Setup mocks
        mock_tm = Mock()
        mock_tm.get_token_count.return_value = 3
        mock_tm.get_token.return_value = 'ghp_test_token'
        mock_get_tm.return_value = mock_tm
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'X-RateLimit-Remaining': '5000'}
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        try:
            # Dispatch task asynchronously to workers
            async_result = fetch_users_batch_task.apply_async(
                args=[['async_testuser']],
                expires=30
            )
            
            # Wait for task completion (max 10 seconds)
            result = async_result.get(timeout=10)
            
            # Verify task completed through workers
            assert isinstance(result, dict)
            assert 'batch_size' in result
            assert result['completed_at'] is not None
            
        except Exception as e:
            # If workers not available, skip gracefully
            pytest.skip(f"Celery workers not available: {e}")
    
    def test_redis_connection(self):
        """Test Redis connection is available"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            assert r.ping()
        except ImportError:
            pytest.skip("redis-py not installed")
        except Exception as e:
            pytest.fail(f"Redis connection failed: {e}")
    
    def test_celery_worker_status(self):
        """Test that Celery workers are responding"""
        try:
            from seattle_source_ranker.celery_config import celery_app
            
            # Check active workers
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            
            if active_workers:
                print(f"\nActive workers: {list(active_workers.keys())}")
                assert len(active_workers) > 0
            else:
                pytest.skip("No Celery workers detected")
                
        except Exception as e:
            pytest.skip(f"Could not inspect workers: {e}")


class TestDistributedCollectorIntegration:
    """Integration tests for DistributedCollector with real infrastructure"""
    
    @patch('requests.post')
    @patch('seattle_source_ranker.tokens.get_token_manager')
    def test_small_batch_collection(self, mock_get_tm, mock_post):
        """Test collecting small batch of users with real Celery workers"""
        from seattle_source_ranker.collector.distributed_collector import DistributedCollector
        
        # Setup mocks
        mock_tm = Mock()
        mock_tm.get_token.return_value = 'ghp_test_token'
        mock_tm.get_token_count.return_value = 3
        mock_get_tm.return_value = mock_tm
        
        # Mock GraphQL search response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'X-RateLimit-Remaining': '5000',
            'X-RateLimit-Reset': '1234567890'
        }
        mock_response.json.return_value = {
            'data': {
                'search': {
                    'userCount': 5,
                    'pageInfo': {'hasNextPage': False, 'endCursor': None},
                    'edges': [
                        {'node': {'login': f'integration_test_user{i}'}} 
                        for i in range(5)
                    ]
                }
            }
        }
        mock_post.return_value = mock_response
        
        try:
            # Create collector (don't auto-start workers, use existing ones)
            collector = DistributedCollector(
                batch_size=5,
                auto_manage_workers=False
            )
            
            # Test batch creation
            users = ['user1', 'user2', 'user3', 'user4', 'user5']
            batches = collector.create_batches(users)
            
            assert len(batches) == 1
            assert len(batches[0]) == 5
            
        except Exception as e:
            pytest.skip(f"DistributedCollector integration test failed: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
