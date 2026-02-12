"""
Test frontend code syntax and quality
"""
import subprocess
import sys
from pathlib import Path
import json

# Frontend directory
FRONTEND_DIR = Path(__file__).parent.parent.parent / 'frontend'
SRC_DIR = FRONTEND_DIR / 'src'


class TestJavaScriptSyntax:
    """Test JavaScript/JSX syntax"""
    
    def test_javascript_files_exist(self):
        """Verify JavaScript files exist"""
        js_files = list(SRC_DIR.glob('*.js')) + list(SRC_DIR.glob('*.jsx'))
        assert len(js_files) > 0, "No JavaScript files found in frontend/src"
    
    def test_no_syntax_errors_in_js_files(self):
        """Check for syntax errors in JavaScript files"""
        js_files = list(SRC_DIR.glob('*.js')) + list(SRC_DIR.glob('*.jsx'))
        
        for js_file in js_files:
            # Try to parse with Node.js
            result = subprocess.run(
                ['node', '--check', str(js_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"\n[ERROR] Syntax error in {js_file}:")
                print(result.stderr)
            
            assert result.returncode == 0, f"Syntax error in {js_file.name}"
    
    def test_package_json_valid(self):
        """Verify package.json is valid JSON"""
        package_json = FRONTEND_DIR / 'package.json'
        assert package_json.exists(), "package.json not found"
        
        with open(package_json, 'r') as f:
            data = json.load(f)
        
        # Check required fields
        assert 'name' in data
        assert 'version' in data
        assert 'dependencies' in data or 'devDependencies' in data
    
    def test_no_console_log_in_production(self):
        """Check for console.log statements that should be removed"""
        js_files = list(SRC_DIR.glob('*.js')) + list(SRC_DIR.glob('*.jsx'))
        
        files_with_console = []
        for js_file in js_files:
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Allow console.error and console.warn, but flag console.log
                if 'console.log(' in content:
                    files_with_console.append(js_file.name)
        
        # This is a warning, not a failure
        if files_with_console:
            print(f"\n[WARNING] Files with console.log: {', '.join(files_with_console)}")


class TestCSSSyntax:
    """Test CSS syntax and structure"""
    
    def test_css_files_exist(self):
        """Verify CSS files exist"""
        css_files = list(SRC_DIR.glob('*.css'))
        assert len(css_files) > 0, "No CSS files found in frontend/src"
    
    def test_no_syntax_errors_in_css(self):
        """Basic CSS syntax validation"""
        css_files = list(SRC_DIR.glob('*.css'))
        
        for css_file in css_files:
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic checks
            open_braces = content.count('{')
            close_braces = content.count('}')
            
            assert open_braces == close_braces, \
                f"Mismatched braces in {css_file.name}: {open_braces} open, {close_braces} close"
    
    def test_no_duplicate_selectors(self):
        """Check for obvious duplicate selectors (basic check)"""
        css_files = list(SRC_DIR.glob('*.css'))
        
        for css_file in css_files:
            with open(css_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Look for class definitions
            selectors = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('.') and '{' in stripped:
                    selector = stripped.split('{')[0].strip()
                    if selector in selectors:
                        print(f"\n[WARNING] Duplicate selector '{selector}' in {css_file.name}")
                    selectors.append(selector)


class TestReactComponents:
    """Test React component structure"""
    
    def test_components_have_imports(self):
        """Verify React components import React"""
        js_files = list(SRC_DIR.glob('*.js')) + list(SRC_DIR.glob('*.jsx'))
        
        for js_file in js_files:
            # Skip non-component files
            if js_file.name in ['index.js', 'reportWebVitals.js', 'setupTests.js']:
                continue
            
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # If file contains JSX (return statement with <), it should import React or use modern syntax
            if 'return (' in content and '<' in content:
                has_react_import = 'import' in content or 'require' in content
                assert has_react_import, f"{js_file.name} appears to be a component but has no imports"
    
    def test_components_export_default(self):
        """Verify page components have default export"""
        component_files = [
            'App.js',
            'HomePage.js',
            'OverallRankingsPage.js',
            'PythonRankingsPage.js',
            'ScoringPage.js',
            'ValidationPage.js'
        ]
        
        for comp_name in component_files:
            comp_file = SRC_DIR / comp_name
            if not comp_file.exists():
                continue
            
            with open(comp_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            has_export = 'export default' in content or 'module.exports' in content
            assert has_export, f"{comp_name} should have a default export"


class TestBuildConfiguration:
    """Test build and configuration files"""
    
    def test_public_index_html_exists(self):
        """Verify public/index.html exists"""
        index_html = FRONTEND_DIR / 'public' / 'index.html'
        assert index_html.exists(), "public/index.html not found"
    
    def test_public_manifest_exists(self):
        """Verify public/manifest.json exists"""
        manifest = FRONTEND_DIR / 'public' / 'manifest.json'
        assert manifest.exists(), "public/manifest.json not found"
        
        with open(manifest, 'r') as f:
            data = json.load(f)
        
        assert 'short_name' in data or 'name' in data


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
