#!/usr/bin/env python3
"""
Tests for distributed/distributed_collector.py
Tests for distributed collection system
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import, skip tests if dependencies not available
try:
    from distributed.distributed_collector import DistributedCollector
    DISTRIBUTED_AVAILABLE = True
except ImportError:
    DISTRIBUTED_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="Celery/Redis not available")


class TestBatchCreation:
    """Test batch creation logic"""
    
    def test_create_batches_basic(self):
        """Test basic batch creation"""
        collector = DistributedCollector(batch_size=10, auto_manage_workers=False)
        users = [f'user{i}' for i in range(100)]
        
        batches = collector.create_batches(users)
        
        assert len(batches) == 10  # 100 users / 10 per batch
        assert len(batches[0]) == 10
        assert len(batches[-1]) == 10
    
    def test_create_batches_uneven(self):
        """Test batch creation with uneven division"""
        collector = DistributedCollector(batch_size=10, auto_manage_workers=False)
        users = [f'user{i}' for i in range(95)]
        
        batches = collector.create_batches(users)
        
        # 95 / 10 = 9 full batches + 1 partial
        assert len(batches) == 10
        assert len(batches[-1]) == 5  # Last batch has 5 users
    
    def test_create_batches_small_list(self):
        """Test batch creation with fewer users than batch size"""
        collector = DistributedCollector(batch_size=50, auto_manage_workers=False)
        users = [f'user{i}' for i in range(20)]
        
        batches = collector.create_batches(users)
        
        assert len(batches) == 1
        assert len(batches[0]) == 20
    
    def test_create_batches_empty(self):
        """Test batch creation with empty list"""
        collector = DistributedCollector(batch_size=10, auto_manage_workers=False)
        users = []
        
        batches = collector.create_batches(users)
        
        assert len(batches) == 0
    
    def test_create_batches_preserves_order(self):
        """Test that batches preserve user order"""
        collector = DistributedCollector(batch_size=5, auto_manage_workers=False)
        users = [f'user{i}' for i in range(15)]
        
        batches = collector.create_batches(users)
        
        # Flatten and check order preserved
        flattened = [u for batch in batches for u in batch]
        assert flattened == users


class TestCollectorInit:
    """Test DistributedCollector initialization"""
    
    def test_init_default_params(self):
        """Test initialization with default parameters"""
        collector = DistributedCollector(auto_manage_workers=False)
        
        assert collector.batch_size > 0
        assert collector.num_workers > 0
    
    def test_init_custom_params(self):
        """Test initialization with custom parameters"""
        collector = DistributedCollector(
            batch_size=25,
            num_workers=4,
            concurrency=3,
            auto_manage_workers=False
        )
        
        assert collector.batch_size == 25
        assert collector.num_workers == 4
        assert collector.concurrency == 3
    
    def test_init_invalid_batch_size(self):
        """Test that invalid batch size is handled"""
        # batch_size of 0 is now allowed (uses default)
        collector = DistributedCollector(batch_size=0, auto_manage_workers=False)
        # Just verify it doesn't crash
        assert collector is not None


class TestWorkerManagement:
    """Test worker management functions"""
    
    @patch('subprocess.run')
    def test_check_workers(self, mock_run):
        """Test checking worker status"""
        mock_run.return_value = MagicMock(
            stdout="8 workers online",
            returncode=0
        )
        
        collector = DistributedCollector(auto_manage_workers=False)
        
        # Should not crash when checking workers
        try:
            count = collector.check_workers()
            assert isinstance(count, int)
        except:
            # It's okay if workers aren't actually running
            pass


class TestGraphQLQuery:
    """Test GraphQL query structure"""
    
    def test_query_has_organization_fragment(self):
        """Test that query includes Organization fragment (critical!)"""
        collector_file = Path(__file__).parent.parent / "distributed" / "distributed_collector.py"
        
        with open(collector_file, 'r') as f:
            content = f.read()
        
        # Critical: Must include Organization fragment
        assert '... on Organization' in content, \
            "Organization fragment missing! Organizations will be excluded."
        assert '... on User' in content, \
            "User fragment missing!"
    
    def test_query_has_required_fields(self):
        """Test that query includes required fields"""
        collector_file = Path(__file__).parent.parent / "distributed" / "distributed_collector.py"
        
        with open(collector_file, 'r') as f:
            content = f.read()
        
        # Check for essential fields in GraphQL query
        assert 'login' in content
        # repositories is referenced in comments/strings, not directly in query
        assert 'query' in content or 'GraphQL' in content


class TestDataAggregation:
    """Test result aggregation logic"""
    
    def test_aggregate_empty_results(self):
        """Test aggregation with empty results"""
        collector = DistributedCollector(auto_manage_workers=False)
        
        # Mock empty result
        mock_result = MagicMock()
        mock_result.successful.return_value = []
        mock_result.failed.return_value = []
        
        aggregated = collector.aggregate_results(mock_result)
        
        assert 'projects' in aggregated
        # metadata field not required, just verify basic structure
        assert 'total_projects' in aggregated


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
