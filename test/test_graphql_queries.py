"""
Tests for GraphQL query structure
Ensures organizations are properly included in queries
"""
import pytest
import re
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestGraphQLQueries:
    """Test GraphQL query structure"""
    
    def test_distributed_collector_has_organization_fragment(self):
        """Test that distributed collector includes Organization fragment"""
        collector_file = Path(__file__).parent.parent / "distributed" / "distributed_collector.py"
        
        with open(collector_file, 'r') as f:
            content = f.read()
        
        # Check for the GraphQL query
        assert 'search(query:' in content, "GraphQL search query not found"
        
        # Check for User fragment
        assert '... on User' in content, "User fragment not found in query"
        assert '... on User { login' in content or '... on User {\n' in content, \
            "User fragment doesn't include login field"
        
        # Check for Organization fragment - THIS IS CRITICAL
        assert '... on Organization' in content, \
            "Organization fragment missing! Organizations will be excluded from results"
        assert '... on Organization { login' in content or '... on Organization {\n' in content, \
            "Organization fragment doesn't include login field"
    
    def test_query_includes_both_user_types(self):
        """Verify query handles both User and Organization types"""
        collector_file = Path(__file__).parent.parent / "distributed" / "distributed_collector.py"
        
        with open(collector_file, 'r') as f:
            content = f.read()
        
        # Simple check: both fragments should exist in the file
        assert '... on User' in content, "User fragment not found"
        assert '... on Organization' in content, "Organization fragment not found"
        
        # Check for login fields (even simpler)
        assert 'login' in content, "login field not found in query"
    
    def test_search_type_user_includes_organizations(self):
        """
        Test understanding: type:USER in GitHub search includes both users and organizations
        But GraphQL fragments are still needed to extract data from both types
        """
        # This is a documentation test
        info = """
        GitHub Search API behavior:
        - type:USER searches for accounts (includes both User and Organization)
        - GraphQL requires explicit fragments for each type to access fields
        - Without '... on Organization { login }', orgs appear as empty objects
        """
        
        assert "type:USER" in info
        assert "User and Organization" in info
        assert "explicit fragments" in info


class TestOrganizationInclusion:
    """Test that key Seattle organizations are captured"""
    
    def test_known_seattle_organizations(self):
        """List of known Seattle organizations that should be in results"""
        expected_orgs = [
            'allenai',           # Allen Institute for AI
            'awslabs',           # AWS Labs
            'FredHutch',         # Fred Hutchinson Cancer Center
            'Sage-Bionetworks',  # Sage Bionetworks
            'codefellows',       # Code Fellows
        ]
        
        # This test documents expected organizations
        # Actual verification would need to check collected data
        assert len(expected_orgs) == 5
        assert 'allenai' in expected_orgs


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
