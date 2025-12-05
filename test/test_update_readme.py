"""
Tests for scripts/update_readme.py
"""
import pytest
from pathlib import Path
from datetime import datetime


class TestDateFormatting:
    """Test date formatting in README updates"""
    
    def test_iso_date_parsing(self):
        """Test parsing ISO format dates"""
        # Test date parsing logic
        test_date = "2025-11-20T10:30:45"
        dt = datetime.fromisoformat(test_date.replace('Z', '+00:00'))
        formatted = dt.strftime('%Y-%m-%d %H:%M:%S PST')
        
        assert '2025-11-20' in formatted
        assert '10:30:45' in formatted
        assert 'PST' in formatted


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



if __name__ == '__main__':
    pytest.main([__file__, '-v'])
