"""
Test shell scripts syntax and structure
"""
import subprocess
from pathlib import Path


# Scripts directory
SCRIPTS_DIR = Path(__file__).parent.parent / 'scripts'


class TestShellScripts:
    """Test shell script syntax"""
    
    def test_shell_scripts_exist(self):
        """Verify shell scripts exist"""
        sh_files = list(SCRIPTS_DIR.glob('*.sh'))
        assert len(sh_files) > 0, "No shell scripts found in scripts/"
    
    def test_bash_syntax_valid(self):
        """Check bash syntax for all shell scripts"""
        sh_files = list(SCRIPTS_DIR.glob('*.sh'))
        
        for sh_file in sh_files:
            # Use bash -n to check syntax without executing
            result = subprocess.run(
                ['bash', '-n', str(sh_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"\n[ERROR] Syntax error in {sh_file.name}:")
                print(result.stderr)
            
            assert result.returncode == 0, f"Syntax error in {sh_file.name}"
    
    def test_scripts_have_shebang(self):
        """Verify scripts start with shebang"""
        sh_files = list(SCRIPTS_DIR.glob('*.sh'))
        
        for sh_file in sh_files:
            with open(sh_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
            
            assert first_line.startswith('#!'), \
                f"{sh_file.name} should start with shebang (#!/bin/bash or #!/usr/bin/env bash)"
    
    def test_scripts_are_executable(self):
        """Check if scripts have executable permission"""
        sh_files = list(SCRIPTS_DIR.glob('*.sh'))
        
        for sh_file in sh_files:
            is_executable = sh_file.stat().st_mode & 0o111
            if not is_executable:
                print(f"\n[WARNING] {sh_file.name} is not executable (chmod +x needed)")


class TestGitHubActions:
    """Test GitHub Actions workflow files"""
    
    def test_workflow_files_exist(self):
        """Verify workflow files exist"""
        workflow_dir = Path(__file__).parent.parent / '.github' / 'workflows'
        yml_files = list(workflow_dir.glob('*.yml')) + list(workflow_dir.glob('*.yaml'))
        assert len(yml_files) > 0, "No workflow files found in .github/workflows"
    
    def test_workflow_syntax_valid(self):
        """Check YAML syntax for workflow files"""
        import yaml
        
        workflow_dir = Path(__file__).parent.parent / '.github' / 'workflows'
        yml_files = list(workflow_dir.glob('*.yml')) + list(workflow_dir.glob('*.yaml'))
        
        for yml_file in yml_files:
            with open(yml_file, 'r', encoding='utf-8') as f:
                try:
                    yaml.safe_load(f)
                except yaml.YAMLError as e:
                    assert False, f"YAML syntax error in {yml_file.name}: {e}"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
