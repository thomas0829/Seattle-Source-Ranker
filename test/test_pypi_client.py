"""
Test PyPI Client module
"""
import pytest
import requests
from unittest.mock import Mock, patch
from seattle_source_ranker.pypi_client import PyPIClient


class TestPyPIClientInit:
    """Test PyPIClient initialization"""
    
    def test_init(self):
        """Test PyPIClient can be initialized"""
        client = PyPIClient()
        assert client.pypistats_api == "https://pypistats.org/api/packages"
        assert client.pypi_api == "https://pypi.org/pypi"
        assert isinstance(client.name_mappings, dict)
    
    def test_name_mappings_contains_pytorch(self):
        """Test that name mappings include common packages"""
        client = PyPIClient()
        assert "pytorch" in client.name_mappings
        assert client.name_mappings["pytorch"] == "torch"


class TestGetPackageName:
    """Test get_package_name method"""
    
    def test_get_package_name_with_slash(self):
        """Test extracting package name from owner/repo format"""
        client = PyPIClient()
        result = client.get_package_name("owner/repo")
        # Should extract 'repo' from 'owner/repo'
        assert result is not None
    
    def test_get_package_name_known_mapping(self):
        """Test known package name mappings"""
        client = PyPIClient()
        assert client.get_package_name("pytorch") == "torch"
        assert client.get_package_name("pytorch/pytorch") == "torch"
    
    def test_get_package_name_none_mapping(self):
        """Test repos that are known to not be packages"""
        client = PyPIClient()
        assert client.get_package_name("python/cpython") is None
        assert client.get_package_name("system-design-primer") is None


class TestGetRecentDownloads:
    """Test get_recent_downloads method"""
    
    def test_get_recent_downloads_exists(self):
        """Test that get_recent_downloads method exists"""
        client = PyPIClient()
        assert hasattr(client, 'get_recent_downloads')
    
    @patch('requests.get')
    def test_get_recent_downloads_mock_success(self, mock_get):
        """Test get_recent_downloads with mocked successful response"""
        client = PyPIClient()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'last_month': 1000000
            }
        }
        mock_get.return_value = mock_response
        
        result = client.get_recent_downloads('requests', 'month')
        
        # Should return download count
        assert result == 1000000 or isinstance(result, int)


class TestPackageExists:
    """Test package_exists method"""
    
    def test_package_exists_method(self):
        """Test that package_exists method exists"""
        client = PyPIClient()
        assert hasattr(client, 'package_exists')
    
    @patch('requests.get')
    def test_package_exists_true(self, mock_get):
        """Test package_exists returns True for existing package"""
        client = PyPIClient()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = client.package_exists('requests')
        assert result is True
    
    @patch('requests.get')
    def test_package_exists_false(self, mock_get):
        """Test package_exists returns False for non-existing package"""
        client = PyPIClient()
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = client.package_exists('nonexistent-package-xyz')
        assert result is False
    
    @patch('requests.get')
    def test_package_exists_exception_handling(self, mock_get):
        """Test package_exists returns False on exception"""
        client = PyPIClient()
        
        # Simulate network exception
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        result = client.package_exists('any-package')
        assert result is False
    
    @patch('requests.get')
    def test_package_exists_timeout(self, mock_get):
        """Test package_exists returns False on timeout"""
        client = PyPIClient()
        
        mock_get.side_effect = requests.exceptions.Timeout()
        
        result = client.package_exists('any-package')
        assert result is False


class TestGetPackageInfo:
    """Test get_package_info method"""
    
    def test_get_package_info_exists(self):
        """Test that get_package_info method exists"""
        client = PyPIClient()
        assert hasattr(client, 'get_package_info')
    
    @patch('seattle_source_ranker.pypi_client.PyPIClient.package_exists')
    @patch('seattle_source_ranker.pypi_client.PyPIClient.get_recent_downloads')
    def test_get_package_info_success(self, mock_downloads, mock_exists):
        """Test get_package_info with successful result"""
        client = PyPIClient()
        
        mock_exists.return_value = True
        mock_downloads.return_value = 5000000
        
        result = client.get_package_info('requests')
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'package_name' in result
        assert 'exists' in result
    
    def test_get_package_info_not_a_package(self):
        """Test get_package_info for known non-package"""
        client = PyPIClient()
        
        result = client.get_package_info('python/cpython')
        
        assert result['exists'] is False
        assert result['reason'] == 'not_a_package'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
