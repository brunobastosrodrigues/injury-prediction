#!/usr/bin/env python3
"""
Code-level QA analysis for Injury Prediction System
Analyzes code for potential bugs without requiring dependencies to be installed.
"""

import os
import re
import json
from pathlib import Path


class CodeAnalysisQA:
    """Code-level QA testing without runtime dependencies"""
    
    def __init__(self, project_root):
        self.project_root = project_root
        self.bugs_found = []
        self.warnings = []
    
    def log_bug(self, severity, category, description, location, line_num=None):
        """Log a bug finding"""
        bug = {
            'severity': severity,
            'category': category,
            'description': description,
            'location': location,
            'line': line_num
        }
        self.bugs_found.append(bug)
        print(f"🐛 [{severity}] {category}: {description}")
        if location:
            loc_str = f"  📍 {location}"
            if line_num:
                loc_str += f":{line_num}"
            print(loc_str)
    
    def log_warning(self, category, description, location):
        """Log a warning"""
        self.warnings.append({
            'category': category,
            'description': description,
            'location': location
        })
        print(f"⚠️  {category}: {description} @ {location}")
    
    def analyze_file_for_common_issues(self, filepath):
        """Analyze a single file for common issues"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            relative_path = os.path.relpath(filepath, self.project_root)
            
            # Check for hardcoded credentials
            credential_patterns = [
                (r'password\s*=\s*["\']([^"\']+)["\']', 'Hardcoded password'),
                (r'api[_-]?key\s*=\s*["\']([^"\']+)["\']', 'Hardcoded API key'),
                (r'secret\s*=\s*["\']([^"\']+)["\']', 'Hardcoded secret'),
                (r'token\s*=\s*["\']([^"\']+)["\']', 'Hardcoded token'),
            ]
            
            for i, line in enumerate(lines, 1):
                for pattern, desc in credential_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Exclude environment variable patterns
                        if 'os.environ' not in line and 'getenv' not in line:
                            self.log_bug('HIGH', 'Security Issue', 
                                       f'{desc} found in code',
                                       relative_path, i)
            
            # Check for SQL injection vulnerabilities (string concatenation in queries)
            if filepath.endswith('.py'):
                for i, line in enumerate(lines, 1):
                    if 'execute' in line.lower() or 'query' in line.lower():
                        if ('+' in line or '%' in line) and ('f"' in line or "f'" in line):
                            self.log_bug('HIGH', 'Security Issue',
                                       'Potential SQL injection - string formatting in query',
                                       relative_path, i)
            
            # Check for eval/exec usage
            dangerous_functions = ['eval(', 'exec(', '__import__']
            for i, line in enumerate(lines, 1):
                for func in dangerous_functions:
                    if func in line and not line.strip().startswith('#'):
                        self.log_bug('HIGH', 'Security Issue',
                                   f'Dangerous function {func} used',
                                   relative_path, i)
            
            # Check for missing error handling
            if filepath.endswith('.py'):
                # Find try blocks and check if they have except
                try_blocks = []
                for i, line in enumerate(lines, 1):
                    if re.match(r'\s*try:', line):
                        try_blocks.append(i)
                
                for try_line in try_blocks:
                    # Check next 20 lines for except
                    found_except = False
                    for check_line in range(try_line, min(try_line + 20, len(lines))):
                        if 'except' in lines[check_line]:
                            found_except = True
                            # Check for bare except
                            if re.match(r'\s*except\s*:', lines[check_line]):
                                self.log_warning('Code Quality',
                                               'Bare except clause - should specify exception type',
                                               f"{relative_path}:{check_line + 1}")
                            break
                    
                    if not found_except:
                        self.log_bug('MEDIUM', 'Error Handling',
                                   'Try block without except clause',
                                   relative_path, try_line)
            
            # Check for TODO/FIXME comments
            for i, line in enumerate(lines, 1):
                if re.search(r'#\s*(TODO|FIXME|HACK|XXX)', line, re.IGNORECASE):
                    self.log_warning('Code Quality',
                                   f'Unresolved comment: {line.strip()}',
                                   f"{relative_path}:{i}")
            
            # Check for debugging code left in
            debug_patterns = ['print(', 'console.log(', 'debugger', 'pdb.set_trace']
            for i, line in enumerate(lines, 1):
                if line.strip().startswith('#'):
                    continue
                for pattern in debug_patterns:
                    if pattern in line:
                        # Exclude logger patterns
                        if 'logger' not in line.lower() and 'log_' not in line.lower():
                            if pattern == 'print(' and filepath.endswith('.py'):
                                # Check if it's in a main block or test
                                if "__main__" not in '\n'.join(lines[max(0, i-10):min(len(lines), i+10)]):
                                    self.log_warning('Code Quality',
                                                   f'Debug code may be left in: {pattern}',
                                                   f"{relative_path}:{i}")
            
        except Exception as e:
            print(f"❌ Error analyzing {filepath}: {e}")
    
    def check_api_routes_consistency(self):
        """Check API routes for common issues"""
        print("\n📋 Analyzing API Routes...")
        
        routes_dir = os.path.join(self.project_root, 'backend/app/api/routes')
        if not os.path.exists(routes_dir):
            return
        
        for route_file in os.listdir(routes_dir):
            if route_file.endswith('.py') and route_file != '__init__.py':
                filepath = os.path.join(routes_dir, route_file)
                
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Check if error responses are consistent
                if 'jsonify' in content:
                    # Check if all error responses have proper status codes
                    error_returns = re.findall(r"return\s+jsonify\(\{[^}]*'error'[^}]*\}\)", content)
                    for err in error_returns:
                        if '), 4' not in err and '), 5' not in err:
                            self.log_warning('API Design',
                                           f'Error response may be missing HTTP status code',
                                           f"backend/app/api/routes/{route_file}")
                
                # Check for missing input validation
                if '@bp.route' in content and 'request' in content:
                    if 'request.get_json()' in content:
                        # Should have validation
                        if 'ValidationError' not in content and 'Schema' not in content:
                            self.log_warning('Input Validation',
                                           'Route accepts JSON but may lack validation',
                                           f"backend/app/api/routes/{route_file}")
    
    def check_frontend_api_calls(self):
        """Check frontend API call consistency"""
        print("\n📋 Analyzing Frontend API Calls...")
        
        api_file = os.path.join(self.project_root, 'frontend/src/api/index.js')
        if not os.path.exists(api_file):
            self.log_bug('MEDIUM', 'Missing File',
                       'Frontend API client file not found',
                       'frontend/src/api/index.js')
            return
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        # Check for error handling in API calls
        if 'axios' in content:
            # Check if .catch() is used
            if '.catch' not in content and 'try' not in content:
                self.log_warning('Error Handling',
                               'API calls may lack error handling',
                               'frontend/src/api/index.js')
    
    def check_data_flow_issues(self):
        """Check for data flow and type consistency issues"""
        print("\n📋 Analyzing Data Flow...")
        
        # Check service files for consistent return types
        services_dir = os.path.join(self.project_root, 'backend/app/services')
        if os.path.exists(services_dir):
            for service_file in os.listdir(services_dir):
                if service_file.endswith('.py') and service_file != '__init__.py':
                    filepath = os.path.join(services_dir, service_file)
                    
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    # Check for None returns that might cause issues
                    if 'return None' in content:
                        # Check if callers handle None
                        self.log_warning('Data Flow',
                                       'Service returns None - ensure callers handle this',
                                       f"backend/app/services/{service_file}")
    
    def check_configuration_issues(self):
        """Check configuration files for issues"""
        print("\n📋 Analyzing Configuration...")
        
        # Check config.py
        config_file = os.path.join(self.project_root, 'backend/app/config.py')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                content = f.read()
            
            # Check if SECRET_KEY is set
            if 'SECRET_KEY' in content:
                if re.search(r"SECRET_KEY\s*=\s*['\"][\w]+['\"]", content):
                    self.log_bug('CRITICAL', 'Security Issue',
                               'Hardcoded SECRET_KEY found - should use environment variable',
                               'backend/app/config.py')
                elif 'os.environ' not in content and 'SECRET_KEY' in content:
                    self.log_warning('Configuration',
                                   'SECRET_KEY configuration may need environment variable',
                                   'backend/app/config.py')
            
            # Check for DEBUG mode
            if re.search(r"DEBUG\s*=\s*True", content):
                self.log_warning('Configuration',
                               'DEBUG=True found - ensure this is not used in production',
                               'backend/app/config.py')
        
        # Check docker-compose.yml for exposed secrets
        docker_file = os.path.join(self.project_root, 'docker-compose.yml')
        if os.path.exists(docker_file):
            with open(docker_file, 'r') as f:
                content = f.read()
            
            # Check for hardcoded credentials in environment variables
            if re.search(r'PASSWORD\s*:\s*\w+', content):
                self.log_bug('HIGH', 'Security Issue',
                           'Hardcoded password in docker-compose.yml',
                           'docker-compose.yml')
    
    def check_dependency_issues(self):
        """Check for dependency and import issues"""
        print("\n📋 Analyzing Dependencies...")
        
        req_file = os.path.join(self.project_root, 'backend/requirements.txt')
        if os.path.exists(req_file):
            with open(req_file, 'r') as f:
                requirements = f.read()
            
            # Check for version pinning
            unpinned = []
            for line in requirements.split('\n'):
                if line.strip() and not line.startswith('#'):
                    if '==' not in line and '>=' not in line and '<=' not in line:
                        unpinned.append(line.strip())
            
            if unpinned:
                self.log_warning('Dependency Management',
                               f'Unpinned dependencies found: {", ".join(unpinned[:5])}...',
                               'backend/requirements.txt')
            
            # Check for known vulnerable packages (example)
            vulnerable_patterns = [
                (r'flask==2\.0\.0', 'Flask 2.0.0 has known vulnerabilities'),
                (r'numpy==1\.19\.', 'Old numpy version may have vulnerabilities'),
            ]
            
            for pattern, msg in vulnerable_patterns:
                if re.search(pattern, requirements):
                    self.log_bug('MEDIUM', 'Security Issue',
                               msg,
                               'backend/requirements.txt')
    
    def check_file_path_security(self):
        """Check for path traversal vulnerabilities"""
        print("\n📋 Analyzing File Path Security...")
        
        # Check all Python files for file operations
        for root, dirs, files in os.walk(os.path.join(self.project_root, 'backend')):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    
                    with open(filepath, 'r', errors='ignore') as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines, 1):
                        # Check for file operations with user input
                        if any(op in line for op in ['open(', 'os.path.join(', 'Path(']):
                            # Check if input validation is nearby
                            context = '\n'.join(lines[max(0, i-5):min(len(lines), i+5)])
                            if 'request' in context or 'input' in context.lower():
                                if 'abspath' not in context and 'realpath' not in context:
                                    relative_path = os.path.relpath(filepath, self.project_root)
                                    self.log_warning('Security',
                                                   'File operation with potential user input - ensure path validation',
                                                   f"{relative_path}:{i}")
    
    def run_all_analyses(self):
        """Run all code analyses"""
        print("="*70)
        print("CODE ANALYSIS QA TEST SUITE")
        print("="*70)
        
        # Analyze all Python files
        print("\n📋 Analyzing Python Files...")
        for root, dirs, files in os.walk(self.project_root):
            # Skip venv, node_modules, .git
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', 'venv', '__pycache__', '.venv']]
            
            for file in files:
                if file.endswith(('.py', '.js', '.jsx')):
                    filepath = os.path.join(root, file)
                    self.analyze_file_for_common_issues(filepath)
        
        # Run specific analyses
        self.check_api_routes_consistency()
        self.check_frontend_api_calls()
        self.check_data_flow_issues()
        self.check_configuration_issues()
        self.check_dependency_issues()
        self.check_file_path_security()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate final report"""
        print("\n" + "="*70)
        print("CODE ANALYSIS SUMMARY")
        print("="*70)
        
        print(f"\n🐛 Bugs Found: {len(self.bugs_found)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.bugs_found:
            print("\n📋 BUGS BY SEVERITY:")
            
            bugs_by_severity = {}
            for bug in self.bugs_found:
                sev = bug['severity']
                if sev not in bugs_by_severity:
                    bugs_by_severity[sev] = []
                bugs_by_severity[sev].append(bug)
            
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                if severity in bugs_by_severity:
                    print(f"\n{severity} ({len(bugs_by_severity[severity])} bugs):")
                    for bug in bugs_by_severity[severity]:
                        print(f"  • [{bug['category']}] {bug['description']}")
                        loc = bug['location']
                        if bug['line']:
                            loc += f":{bug['line']}"
                        print(f"    Location: {loc}")
        
        # Save detailed report
        report_path = os.path.join(self.project_root, 'CODE_ANALYSIS_REPORT.md')
        self.save_report(report_path)
        print(f"\n📄 Detailed report saved to: {report_path}")
    
    def save_report(self, filepath):
        """Save detailed report to file"""
        with open(filepath, 'w') as f:
            f.write("# Code Analysis Report - Injury Prediction System\n\n")
            f.write(f"**Total Bugs Found:** {len(self.bugs_found)}\n")
            f.write(f"**Total Warnings:** {len(self.warnings)}\n\n")
            
            if self.bugs_found:
                f.write("## Bugs Found\n\n")
                
                bugs_by_severity = {}
                for bug in self.bugs_found:
                    sev = bug['severity']
                    if sev not in bugs_by_severity:
                        bugs_by_severity[sev] = []
                    bugs_by_severity[sev].append(bug)
                
                for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                    if severity in bugs_by_severity:
                        f.write(f"### {severity} Severity ({len(bugs_by_severity[severity])} bugs)\n\n")
                        for i, bug in enumerate(bugs_by_severity[severity], 1):
                            f.write(f"{i}. **[{bug['category']}]** {bug['description']}\n")
                            loc = bug['location']
                            if bug['line']:
                                loc += f":{bug['line']}"
                            f.write(f"   - Location: `{loc}`\n\n")
            
            if self.warnings:
                f.write("## Warnings\n\n")
                for i, warning in enumerate(self.warnings, 1):
                    f.write(f"{i}. **[{warning['category']}]** {warning['description']}\n")
                    f.write(f"   - Location: `{warning['location']}`\n\n")


if __name__ == '__main__':
    # Go up one level from scripts/
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    qa = CodeAnalysisQA(project_root)
    qa.run_all_analyses()
