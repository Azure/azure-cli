#!/usr/bin/env python3

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Test runner for Azure Migrate CLI module.

This script provides an easy way to run all tests for the Azure Migrate CLI module,
including unit tests, integration tests, and scenario tests.

Usage:
    python run_tests.py [options]

Options:
    --unit          Run only unit tests
    --integration   Run only integration tests  
    --scenario      Run only scenario tests
    --live          Run live scenario tests (requires Azure authentication)
    --coverage      Generate code coverage report
    --verbose       Run tests with verbose output
    --help          Show this help message
"""

import sys
import argparse
import unittest
from pathlib import Path

# Add the migrate module to the Python path
migrate_dir = Path(__file__).parent.parent
sys.path.insert(0, str(migrate_dir))

def run_unit_tests(verbose=False):
    """Run unit tests for the migrate module."""
    print("Running unit tests...")
    
    # Create test suite for unit tests
    suite = unittest.TestSuite()
    
    # Load unit test classes
    unit_test_classes = [
        # Custom function tests
        'azure.cli.command_modules.migrate.tests.latest.test_migrate_custom.TestMigratePowerShellUtils',
        'azure.cli.command_modules.migrate.tests.latest.test_migrate_custom.TestMigrateDiscoveryCommands',
        'azure.cli.command_modules.migrate.tests.latest.test_migrate_custom.TestMigrateReplicationCommands',
        'azure.cli.command_modules.migrate.tests.latest.test_migrate_custom.TestMigrateLocalCommands',
        'azure.cli.command_modules.migrate.tests.latest.test_migrate_custom.TestMigrateInfrastructureCommands',
        'azure.cli.command_modules.migrate.tests.latest.test_migrate_custom.TestMigrateAuthenticationCommands',
        'azure.cli.command_modules.migrate.tests.latest.test_migrate_custom.TestMigrateUtilityCommands',
        'azure.cli.command_modules.migrate.tests.latest.test_migrate_custom.TestMigrateErrorHandling',
        
        # PowerShell utility tests
        'azure.cli.command_modules.migrate.tests.latest.test_powershell_utils.TestPowerShellExecutor',
        'azure.cli.command_modules.migrate.tests.latest.test_powershell_utils.TestPowerShellExecutorFactory',
        'azure.cli.command_modules.migrate.tests.latest.test_powershell_utils.TestPowerShellExecutorEdgeCases',
        
        # Command loading tests
        'azure.cli.command_modules.migrate.tests.latest.test_migrate_commands.TestMigrateCommandLoading',
        'azure.cli.command_modules.migrate.tests.latest.test_migrate_commands.TestMigrateCommandParameters',
        'azure.cli.command_modules.migrate.tests.latest.test_migrate_commands.TestMigrateCommandValidation',
        'azure.cli.command_modules.migrate.tests.latest.test_migrate_commands.TestMigrateCommandIntegration',
    ]
    
    # Load tests from each class
    loader = unittest.TestLoader()
    for test_class_name in unit_test_classes:
        try:
            module_name, class_name = test_class_name.rsplit('.', 1)
            module = __import__(module_name, fromlist=[class_name])
            test_class = getattr(module, class_name)
            suite.addTest(loader.loadTestsFromTestCase(test_class))
        except (ImportError, AttributeError) as e:
            print(f"⚠️  Could not load test class {test_class_name}: {e}")
    
    # Run the tests
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_integration_tests(verbose=False):
    """Run integration tests for the migrate module."""
    print("Running integration tests...")
    
    # Integration tests are part of the scenario tests but with mocked dependencies
    return run_scenario_tests(verbose=verbose, live=False)

def run_scenario_tests(verbose=False, live=False):
    """Run scenario tests for the migrate module."""
    test_type = "live scenario" if live else "scenario"
    print(f"Running {test_type} tests...")
    
    try:
        from azure.cli.command_modules.migrate.tests.latest.test_migrate_scenario import (
            MigrateScenarioTest,
            MigrateParameterValidationTest
        )
        
        # Only run live tests if explicitly requested
        if live:
            from azure.cli.command_modules.migrate.tests.latest.test_migrate_scenario import (
                MigrateLiveScenarioTest
            )
            test_classes = [MigrateScenarioTest, MigrateParameterValidationTest, MigrateLiveScenarioTest]
        else:
            test_classes = [MigrateScenarioTest, MigrateParameterValidationTest]
        
        suite = unittest.TestSuite()
        loader = unittest.TestLoader()
        
        for test_class in test_classes:
            suite.addTest(loader.loadTestsFromTestCase(test_class))
        
        verbosity = 2 if verbose else 1
        runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"Could not import scenario tests: {e}")
        return False

def run_with_coverage(test_function, *args, **kwargs):
    """Run tests with code coverage analysis."""
    try:
        import coverage
    except ImportError:
        print("Coverage package not installed. Install with: pip install coverage")
        return False
    
    print("Running tests with coverage analysis...")
    
    # Start coverage
    cov = coverage.Coverage(source=['azure.cli.command_modules.migrate'])
    cov.start()
    
    try:
        # Run the tests
        success = test_function(*args, **kwargs)
        
        # Stop coverage and generate report
        cov.stop()
        cov.save()
        
        print("\nCoverage Report:")
        cov.report(show_missing=True)
        
        # Generate HTML report
        html_dir = migrate_dir / 'tests' / 'coverage_html'
        cov.html_report(directory=str(html_dir))
        print(f"HTML coverage report generated in: {html_dir}")
        
        return success
        
    except Exception as e:
        print(f"Error running tests with coverage: {e}")
        return False
    finally:
        cov.stop()

def run_all_tests(verbose=False, live=False):
    """Run all tests for the migrate module."""
    print("Running all Azure Migrate CLI tests...")
    
    results = []
    
    # Run unit tests
    print("\n" + "="*60)
    results.append(run_unit_tests(verbose=verbose))
    
    # Run integration tests
    print("\n" + "="*60)
    results.append(run_integration_tests(verbose=verbose))
    
    # Run scenario tests
    print("\n" + "="*60)
    results.append(run_scenario_tests(verbose=verbose, live=live))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary:")
    test_types = ["Unit Tests", "Integration Tests", "Scenario Tests"]
    for i, (test_type, success) in enumerate(zip(test_types, results)):
        status = "✅ PASSED" if success else "FAILED"
        print(f"  {test_type}: {status}")
    
    all_passed = all(results)
    overall_status = "✅ ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED"
    print(f"\n{overall_status}")
    
    return all_passed

def check_prerequisites():
    """Check if test prerequisites are met."""
    print("Checking test prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("Python 3.7+ required")
        return False
    
    # Check required packages
    required_packages = ['azure', 'knack', 'unittest']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        return False
    
    print("✅ Prerequisites check passed")
    return True

def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Run tests for Azure Migrate CLI module",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--unit', action='store_true', 
                      help='Run only unit tests')
    parser.add_argument('--integration', action='store_true',
                      help='Run only integration tests')
    parser.add_argument('--scenario', action='store_true',
                      help='Run only scenario tests')
    parser.add_argument('--live', action='store_true',
                      help='Run live scenario tests (requires Azure authentication)')
    parser.add_argument('--coverage', action='store_true',
                      help='Generate code coverage report')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Run tests with verbose output')
    parser.add_argument('--check-prereqs', action='store_true',
                      help='Only check prerequisites and exit')
    
    args = parser.parse_args()
    
    # Check prerequisites
    if not check_prerequisites():
        return 1
    
    if args.check_prereqs:
        return 0
    
    # Determine which tests to run
    success = True
    
    try:
        if args.unit:
            if args.coverage:
                success = run_with_coverage(run_unit_tests, verbose=args.verbose)
            else:
                success = run_unit_tests(verbose=args.verbose)
        
        elif args.integration:
            if args.coverage:
                success = run_with_coverage(run_integration_tests, verbose=args.verbose)
            else:
                success = run_integration_tests(verbose=args.verbose)
        
        elif args.scenario:
            if args.coverage:
                success = run_with_coverage(run_scenario_tests, verbose=args.verbose, live=args.live)
            else:
                success = run_scenario_tests(verbose=args.verbose, live=args.live)
        
        else:
            # Run all tests
            if args.coverage:
                success = run_with_coverage(run_all_tests, verbose=args.verbose, live=args.live)
            else:
                success = run_all_tests(verbose=args.verbose, live=args.live)
    
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
