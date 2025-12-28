#!/usr/bin/env python3
"""
Comprehensive QA Test Suite for Injury Prediction System
Tests API endpoints, data validation, error handling, and edge cases.
"""

import sys
import os
import json
import time
from typing import Dict, List, Tuple

# Add project paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))
sys.path.insert(0, os.path.join(project_root, 'synthetic_data_generation'))


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class QATestSuite:
    """QA test suite for comprehensive system testing"""
    
    def __init__(self):
        self.bugs_found = []
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_bug(self, severity: str, category: str, description: str, location: str = ""):
        """Log a bug finding"""
        bug = {
            'severity': severity,  # CRITICAL, HIGH, MEDIUM, LOW
            'category': category,
            'description': description,
            'location': location
        }
        self.bugs_found.append(bug)
        print(f"{Colors.RED}[BUG FOUND - {severity}]{Colors.RESET} {category}: {description}")
        if location:
            print(f"  Location: {location}")
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log a test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            print(f"{Colors.GREEN}✓{Colors.RESET} {test_name}")
        else:
            self.failed_tests += 1
            print(f"{Colors.RED}✗{Colors.RESET} {test_name}: {message}")
        
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })
    
    def test_schema_validations(self):
        """Test API schema validations"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}=== Testing API Schema Validations ==={Colors.RESET}\n")
        
        try:
            from backend.app.api.schemas import (
                DataGenerationSchema, 
                PreprocessingSchema, 
                TrainingSchema,
                IngestionSchema
            )
            from pydantic import ValidationError
            
            # Test DataGenerationSchema
            # Test 1: Valid input
            try:
                schema = DataGenerationSchema(n_athletes=100, simulation_year=2024)
                self.log_test("DataGenerationSchema - Valid input", True)
            except Exception as e:
                self.log_test("DataGenerationSchema - Valid input", False, str(e))
                self.log_bug("HIGH", "Schema Validation", 
                           f"Valid DataGenerationSchema input failed: {e}",
                           "backend/app/api/schemas.py:DataGenerationSchema")
            
            # Test 2: Out of range n_athletes (too large)
            try:
                schema = DataGenerationSchema(n_athletes=10000)
                self.log_test("DataGenerationSchema - Out of range athletes (>5000)", False, 
                            "Should reject n_athletes > 5000")
                self.log_bug("MEDIUM", "Schema Validation",
                           "Schema accepts n_athletes > 5000 which may cause performance issues",
                           "backend/app/api/schemas.py:DataGenerationSchema")
            except ValidationError:
                self.log_test("DataGenerationSchema - Out of range athletes (>5000)", True)
            
            # Test 3: Out of range n_athletes (zero or negative)
            try:
                schema = DataGenerationSchema(n_athletes=0)
                self.log_test("DataGenerationSchema - Zero athletes", False,
                            "Should reject n_athletes = 0")
                self.log_bug("MEDIUM", "Schema Validation",
                           "Schema accepts n_athletes = 0",
                           "backend/app/api/schemas.py:DataGenerationSchema")
            except ValidationError:
                self.log_test("DataGenerationSchema - Zero athletes", True)
            
            # Test 4: Invalid simulation year
            try:
                schema = DataGenerationSchema(simulation_year=1999)
                self.log_test("DataGenerationSchema - Invalid year (1999)", False,
                            "Should reject year < 2000")
                self.log_bug("LOW", "Schema Validation",
                           "Schema accepts simulation_year < 2000",
                           "backend/app/api/schemas.py:DataGenerationSchema")
            except ValidationError:
                self.log_test("DataGenerationSchema - Invalid year (1999)", True)
            
            # Test PreprocessingSchema
            # Test 5: Invalid split strategy
            try:
                schema = PreprocessingSchema(dataset_id="test", split_strategy="invalid_strategy")
                self.log_test("PreprocessingSchema - Invalid split strategy", False,
                            "Should reject invalid split_strategy")
                self.log_bug("HIGH", "Schema Validation",
                           "Schema accepts invalid split_strategy",
                           "backend/app/api/schemas.py:PreprocessingSchema")
            except ValidationError:
                self.log_test("PreprocessingSchema - Invalid split strategy", True)
            
            # Test 6: Invalid split ratio
            try:
                schema = PreprocessingSchema(dataset_id="test", split_ratio=0.9)
                self.log_test("PreprocessingSchema - Split ratio too high (0.9)", False,
                            "Should reject split_ratio > 0.5")
                self.log_bug("MEDIUM", "Schema Validation",
                           "Schema accepts split_ratio > 0.5 which may leave insufficient training data",
                           "backend/app/api/schemas.py:PreprocessingSchema")
            except ValidationError:
                self.log_test("PreprocessingSchema - Split ratio too high (0.9)", True)
            
            # Test 7: Missing required fields
            try:
                schema = PreprocessingSchema()
                self.log_test("PreprocessingSchema - Missing dataset_id", False,
                            "Should require dataset_id")
                self.log_bug("HIGH", "Schema Validation",
                           "PreprocessingSchema doesn't require dataset_id",
                           "backend/app/api/schemas.py:PreprocessingSchema")
            except ValidationError:
                self.log_test("PreprocessingSchema - Missing dataset_id", True)
            
            # Test TrainingSchema
            # Test 8: Invalid model type
            try:
                schema = TrainingSchema(split_id="test", models=["invalid_model"])
                self.log_test("TrainingSchema - Invalid model type", False,
                            "Should reject invalid model types")
                self.log_bug("HIGH", "Schema Validation",
                           "Schema accepts invalid model types",
                           "backend/app/api/schemas.py:TrainingSchema")
            except ValidationError:
                self.log_test("TrainingSchema - Invalid model type", True)
            
            # Test 9: Empty model list
            try:
                schema = TrainingSchema(split_id="test", models=[])
                # Empty list might be valid if there's a default
                self.log_test("TrainingSchema - Empty model list", True)
            except ValidationError as e:
                self.log_test("TrainingSchema - Empty model list", True)
            
        except ImportError as e:
            self.log_test("Schema Import", False, str(e))
            self.log_bug("CRITICAL", "Import Error",
                       f"Cannot import schemas: {e}",
                       "backend/app/api/schemas.py")
    
    def test_file_structure(self):
        """Test file structure and required files"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}=== Testing File Structure ==={Colors.RESET}\n")
        
        required_files = [
            'backend/app/__init__.py',
            'backend/app/config.py',
            'backend/run.py',
            'frontend/package.json',
            'docker-compose.yml',
            'README.md'
        ]
        
        for file_path in required_files:
            full_path = os.path.join(project_root, file_path)
            exists = os.path.exists(full_path)
            self.log_test(f"File exists: {file_path}", exists)
            if not exists:
                self.log_bug("HIGH", "Missing File",
                           f"Required file not found: {file_path}",
                           file_path)
        
        # Check data directories
        data_dirs = ['data/raw', 'data/processed', 'data/models']
        for dir_path in data_dirs:
            full_path = os.path.join(project_root, dir_path)
            if not os.path.exists(full_path):
                print(f"{Colors.YELLOW}[INFO]{Colors.RESET} Creating missing directory: {dir_path}")
                try:
                    os.makedirs(full_path, exist_ok=True)
                    self.log_test(f"Data directory: {dir_path}", True)
                except Exception as e:
                    self.log_test(f"Data directory: {dir_path}", False, str(e))
                    self.log_bug("MEDIUM", "Directory Creation",
                               f"Cannot create data directory: {dir_path}",
                               dir_path)
    
    def test_config_files(self):
        """Test configuration files"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}=== Testing Configuration Files ==={Colors.RESET}\n")
        
        try:
            from backend.app import config
            
            # Test if config exists
            self.log_test("Config module imports", True)
            
            # Test configuration classes
            config_classes = ['DevelopmentConfig', 'ProductionConfig', 'TestingConfig']
            for config_class in config_classes:
                if hasattr(config, config_class):
                    self.log_test(f"Config class exists: {config_class}", True)
                else:
                    self.log_test(f"Config class exists: {config_class}", False)
                    self.log_bug("MEDIUM", "Missing Configuration",
                               f"Configuration class not found: {config_class}",
                               "backend/app/config.py")
            
        except ImportError as e:
            self.log_test("Config module imports", False, str(e))
            self.log_bug("CRITICAL", "Import Error",
                       f"Cannot import config: {e}",
                       "backend/app/config.py")
        
        # Test hyperparameters file
        hyperparams_path = os.path.join(project_root, 'backend/app/config/hyperparameters.yaml')
        if os.path.exists(hyperparams_path):
            self.log_test("Hyperparameters file exists", True)
            try:
                import yaml
                with open(hyperparams_path, 'r') as f:
                    params = yaml.safe_load(f)
                
                # Check for required model configs
                required_models = ['lasso', 'random_forest', 'xgboost']
                for model in required_models:
                    if model in params:
                        self.log_test(f"Hyperparameters for {model}", True)
                    else:
                        self.log_test(f"Hyperparameters for {model}", False)
                        self.log_bug("MEDIUM", "Missing Configuration",
                                   f"Hyperparameters not defined for {model}",
                                   "backend/app/config/hyperparameters.yaml")
            except Exception as e:
                self.log_test("Parse hyperparameters YAML", False, str(e))
                self.log_bug("HIGH", "Configuration Error",
                           f"Cannot parse hyperparameters.yaml: {e}",
                           "backend/app/config/hyperparameters.yaml")
        else:
            self.log_test("Hyperparameters file exists", False)
            self.log_bug("HIGH", "Missing File",
                       "Hyperparameters configuration file not found",
                       "backend/app/config/hyperparameters.yaml")
    
    def test_service_imports(self):
        """Test that all service modules can be imported"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}=== Testing Service Imports ==={Colors.RESET}\n")
        
        services = [
            'data_generation_service',
            'preprocessing_service',
            'training_service',
            'analytics_service',
            'ingestion_service',
            'explainability',
            'validation_service'
        ]
        
        for service in services:
            try:
                module = __import__(f'backend.app.services.{service}', fromlist=[service])
                self.log_test(f"Import service: {service}", True)
            except ImportError as e:
                self.log_test(f"Import service: {service}", False, str(e))
                self.log_bug("HIGH", "Import Error",
                           f"Cannot import service {service}: {e}",
                           f"backend/app/services/{service}.py")
            except Exception as e:
                self.log_test(f"Import service: {service}", False, str(e))
                self.log_bug("HIGH", "Runtime Error",
                           f"Error importing service {service}: {e}",
                           f"backend/app/services/{service}.py")
    
    def test_route_imports(self):
        """Test that all route modules can be imported"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}=== Testing Route Imports ==={Colors.RESET}\n")
        
        routes = [
            'data_generation',
            'preprocessing',
            'training',
            'analytics',
            'data_ingestion',
            'explainability',
            'validation'
        ]
        
        for route in routes:
            try:
                module = __import__(f'backend.app.api.routes.{route}', fromlist=[route])
                self.log_test(f"Import route: {route}", True)
                
                # Check if blueprint is defined
                if hasattr(module, 'bp') or hasattr(module, f'{route}_bp'):
                    self.log_test(f"Blueprint defined: {route}", True)
                else:
                    self.log_test(f"Blueprint defined: {route}", False)
                    self.log_bug("MEDIUM", "Missing Blueprint",
                               f"Blueprint not found in route module {route}",
                               f"backend/app/api/routes/{route}.py")
                    
            except ImportError as e:
                self.log_test(f"Import route: {route}", False, str(e))
                self.log_bug("HIGH", "Import Error",
                           f"Cannot import route {route}: {e}",
                           f"backend/app/api/routes/{route}.py")
            except Exception as e:
                self.log_test(f"Import route: {route}", False, str(e))
                self.log_bug("HIGH", "Runtime Error",
                           f"Error importing route {route}: {e}",
                           f"backend/app/api/routes/{route}.py")
    
    def test_synthetic_data_generation(self):
        """Test synthetic data generation modules"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}=== Testing Synthetic Data Generation ==={Colors.RESET}\n")
        
        modules = [
            'synthetic_data_generation.logistics.athlete_profiles',
            'synthetic_data_generation.logistics.training_plan',
            'synthetic_data_generation.sensor_data.daily_metrics_simulation',
            'synthetic_data_generation.training_response.injury_simulation',
            'synthetic_data_generation.simulate_year'
        ]
        
        for module_name in modules:
            try:
                module = __import__(module_name, fromlist=[module_name.split('.')[-1]])
                self.log_test(f"Import: {module_name}", True)
            except ImportError as e:
                self.log_test(f"Import: {module_name}", False, str(e))
                self.log_bug("HIGH", "Import Error",
                           f"Cannot import {module_name}: {e}",
                           module_name.replace('.', '/') + '.py')
            except Exception as e:
                self.log_test(f"Import: {module_name}", False, str(e))
                self.log_bug("MEDIUM", "Runtime Error",
                           f"Error importing {module_name}: {e}",
                           module_name.replace('.', '/') + '.py')
    
    def test_frontend_structure(self):
        """Test frontend file structure"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}=== Testing Frontend Structure ==={Colors.RESET}\n")
        
        frontend_files = [
            'frontend/src/main.jsx',
            'frontend/src/App.jsx',
            'frontend/vite.config.js',
            'frontend/package.json'
        ]
        
        for file_path in frontend_files:
            full_path = os.path.join(project_root, file_path)
            exists = os.path.exists(full_path)
            self.log_test(f"Frontend file: {file_path}", exists)
            if not exists:
                self.log_bug("HIGH", "Missing File",
                           f"Required frontend file not found: {file_path}",
                           file_path)
        
        # Check for key directories
        frontend_dirs = [
            'frontend/src/components',
            'frontend/src/pages',
            'frontend/src/context',
            'frontend/src/api'
        ]
        
        for dir_path in frontend_dirs:
            full_path = os.path.join(project_root, dir_path)
            exists = os.path.exists(full_path)
            self.log_test(f"Frontend directory: {dir_path}", exists)
            if not exists:
                self.log_bug("MEDIUM", "Missing Directory",
                           f"Frontend directory not found: {dir_path}",
                           dir_path)
    
    def test_docker_configuration(self):
        """Test Docker configuration"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}=== Testing Docker Configuration ==={Colors.RESET}\n")
        
        docker_compose_path = os.path.join(project_root, 'docker-compose.yml')
        
        if os.path.exists(docker_compose_path):
            self.log_test("docker-compose.yml exists", True)
            
            try:
                import yaml
                with open(docker_compose_path, 'r') as f:
                    compose_config = yaml.safe_load(f)
                
                # Check for required services
                required_services = ['backend', 'frontend', 'redis', 'celery_worker']
                for service in required_services:
                    if 'services' in compose_config and service in compose_config['services']:
                        self.log_test(f"Docker service defined: {service}", True)
                    else:
                        self.log_test(f"Docker service defined: {service}", False)
                        self.log_bug("HIGH", "Missing Service",
                                   f"Docker service not defined: {service}",
                                   "docker-compose.yml")
                
                # Check port mappings
                if 'services' in compose_config:
                    backend = compose_config['services'].get('backend', {})
                    if 'ports' in backend:
                        self.log_test("Backend port mapping", True)
                    else:
                        self.log_test("Backend port mapping", False)
                        self.log_bug("MEDIUM", "Configuration Issue",
                                   "Backend service missing port mapping",
                                   "docker-compose.yml")
                    
            except Exception as e:
                self.log_test("Parse docker-compose.yml", False, str(e))
                self.log_bug("HIGH", "Configuration Error",
                           f"Cannot parse docker-compose.yml: {e}",
                           "docker-compose.yml")
        else:
            self.log_test("docker-compose.yml exists", False)
            self.log_bug("HIGH", "Missing File",
                       "Docker Compose configuration file not found",
                       "docker-compose.yml")
    
    def generate_bug_report(self):
        """Generate comprehensive bug report"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}QA TEST SUMMARY{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
        
        print(f"Total Tests Run: {self.total_tests}")
        print(f"{Colors.GREEN}Passed: {self.passed_tests}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {self.failed_tests}{Colors.RESET}")
        print(f"Pass Rate: {(self.passed_tests/self.total_tests*100):.1f}%\n")
        
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}BUG REPORT{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
        
        if not self.bugs_found:
            print(f"{Colors.GREEN}✓ No bugs found! System appears to be functioning correctly.{Colors.RESET}\n")
            return
        
        print(f"Total Bugs Found: {len(self.bugs_found)}\n")
        
        # Group bugs by severity
        bugs_by_severity = {
            'CRITICAL': [],
            'HIGH': [],
            'MEDIUM': [],
            'LOW': []
        }
        
        for bug in self.bugs_found:
            bugs_by_severity[bug['severity']].append(bug)
        
        # Print bugs by severity
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            bugs = bugs_by_severity[severity]
            if bugs:
                color = Colors.RED if severity in ['CRITICAL', 'HIGH'] else Colors.YELLOW
                print(f"{color}{Colors.BOLD}{severity} SEVERITY ({len(bugs)} bugs):{Colors.RESET}\n")
                
                for i, bug in enumerate(bugs, 1):
                    print(f"{i}. {Colors.BOLD}[{bug['category']}]{Colors.RESET} {bug['description']}")
                    if bug['location']:
                        print(f"   Location: {bug['location']}")
                    print()
        
        # Save report to file
        report_path = os.path.join(project_root, 'QA_BUG_REPORT.md')
        self.save_bug_report_to_file(report_path)
        print(f"{Colors.GREEN}Bug report saved to: {report_path}{Colors.RESET}\n")
    
    def save_bug_report_to_file(self, filepath: str):
        """Save detailed bug report to markdown file"""
        with open(filepath, 'w') as f:
            f.write("# QA Test Report - Injury Prediction System\n\n")
            f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Test Summary
            f.write("## Test Summary\n\n")
            f.write(f"- **Total Tests:** {self.total_tests}\n")
            f.write(f"- **Passed:** {self.passed_tests}\n")
            f.write(f"- **Failed:** {self.failed_tests}\n")
            f.write(f"- **Pass Rate:** {(self.passed_tests/self.total_tests*100):.1f}%\n\n")
            
            # Bugs Found
            f.write(f"## Bugs Found: {len(self.bugs_found)}\n\n")
            
            if not self.bugs_found:
                f.write("✅ **No bugs found!** System appears to be functioning correctly.\n\n")
                return
            
            # Group bugs by severity
            bugs_by_severity = {
                'CRITICAL': [],
                'HIGH': [],
                'MEDIUM': [],
                'LOW': []
            }
            
            for bug in self.bugs_found:
                bugs_by_severity[bug['severity']].append(bug)
            
            # Write bugs by severity
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                bugs = bugs_by_severity[severity]
                if bugs:
                    f.write(f"### {severity} Severity ({len(bugs)} bugs)\n\n")
                    
                    for i, bug in enumerate(bugs, 1):
                        f.write(f"{i}. **[{bug['category']}]** {bug['description']}\n")
                        if bug['location']:
                            f.write(f"   - **Location:** `{bug['location']}`\n")
                        f.write("\n")
            
            # Detailed Test Results
            f.write("## Detailed Test Results\n\n")
            
            current_category = None
            for result in self.test_results:
                # Group by test category (extract from test name)
                test_parts = result['test'].split(' - ')
                category = test_parts[0] if len(test_parts) > 1 else "General"
                
                if category != current_category:
                    f.write(f"### {category}\n\n")
                    current_category = category
                
                status = "✅ PASS" if result['passed'] else "❌ FAIL"
                f.write(f"- {status}: {result['test']}")
                if result['message']:
                    f.write(f" - {result['message']}")
                f.write("\n")
            
            f.write("\n## Recommendations\n\n")
            f.write("1. Address CRITICAL and HIGH severity bugs immediately\n")
            f.write("2. Review MEDIUM severity bugs and prioritize based on impact\n")
            f.write("3. Consider LOW severity bugs for future improvements\n")
            f.write("4. Add automated tests to prevent regression\n")
            f.write("5. Implement continuous integration testing\n")
    
    def run_all_tests(self):
        """Run all QA tests"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}INJURY PREDICTION SYSTEM - QA TEST SUITE{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
        
        # Run all test categories
        self.test_file_structure()
        self.test_config_files()
        self.test_schema_validations()
        self.test_service_imports()
        self.test_route_imports()
        self.test_synthetic_data_generation()
        self.test_frontend_structure()
        self.test_docker_configuration()
        
        # Generate final report
        self.generate_bug_report()


if __name__ == '__main__':
    qa_suite = QATestSuite()
    qa_suite.run_all_tests()
