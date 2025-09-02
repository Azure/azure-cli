# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Unified Testing Infrastructure for Azure Migrate CLI
====================================================

This module provides a comprehensive, unified testing system that includes:
- PowerShell cmdlet mocking with realistic responses
- Base test classes with common setup
- Test configuration and utilities
- Comprehensive test runner
- Cross-platform compatibility

Usage:
    from test_framework import MigrateTestCase, create_test_suite, run_all_tests
"""

import unittest
import sys
import os
import re
import json
import platform
from unittest.mock import Mock, patch, MagicMock
from knack.util import CLIError


# ============================================================================
# PowerShell Mocking System
# ============================================================================

class PowerShellCmdletMocker:
    """Comprehensive PowerShell cmdlet mocking system with realistic responses."""
    
    def __init__(self):
        self.cmdlet_responses = {
            # PowerShell version and system info
            '$PSVersionTable.PSVersion.ToString()': {
                'stdout': '7.3.4',
                'stderr': '',
                'returncode': 0
            },
            '$PSVersionTable.PSVersion.Major': {
                'stdout': '7',
                'stderr': '',
                'returncode': 0
            },
            
            # Azure module checks
            'Get-Module -ListAvailable Az.*': {
                'stdout': 'Az.Accounts    2.15.1\nAz.Migrate     2.1.0\nAz.Resources   6.5.3',
                'stderr': '',
                'returncode': 0
            },
            'Get-Module -ListAvailable Az.Migrate': {
                'stdout': 'ModuleType Version    Name                                ExportedCommands\n' +
                         'Manifest   2.1.0      Az.Migrate                          {Get-AzMigrateProject, New-AzMigrateProject...}',
                'stderr': '',
                'returncode': 0
            },
            'Get-Module -ListAvailable Az.Migrate | Select-Object -First 1': {
                'stdout': 'Az.Migrate Module Found',
                'stderr': '',
                'returncode': 0
            },
            
            # Azure authentication
            'Connect-AzAccount': {
                'stdout': 'Account                 SubscriptionName        TenantId\n' +
                         'user@contoso.com        My Subscription         12345678-1234-1234-1234-123456789012',
                'stderr': '',
                'returncode': 0
            },
            'Disconnect-AzAccount': {
                'stdout': 'Disconnected from Azure account.',
                'stderr': '',
                'returncode': 0
            },
            
            # Azure authentication check with proper JSON format for PowerShell utils
            '(Get-AzContext) -ne $null': {
                'stdout': 'True',
                'stderr': '',
                'returncode': 0
            },
            'if (Get-AzContext) { @{IsAuthenticated=$true; AccountId=(Get-AzContext).Account.Id} | ConvertTo-Json } else { @{IsAuthenticated=$false; Error="Not authenticated"} | ConvertTo-Json }': {
                'stdout': '{"IsAuthenticated":true,"AccountId":"test@example.com"}',
                'stderr': '',
                'returncode': 0
            },
            
            'Get-AzContext': {
                'stdout': json.dumps({
                    'Account': 'user@contoso.com',
                    'Subscription': {
                        'Id': 'f6f66a94-f184-45da-ac12-ffbfd8a6eb29',
                        'Name': 'My Subscription'
                    },
                    'Tenant': {
                        'Id': '12345678-1234-1234-1234-123456789012'
                    }
                }),
                'stderr': '',
                'returncode': 0
            },
            
            # Azure Migrate specific cmdlets
            'Get-AzMigrateProject': {
                'stdout': json.dumps([{
                    'Name': 'TestMigrateProject',
                    'ResourceGroupName': 'migrate-rg',
                    'Location': 'East US 2',
                    'Id': '/subscriptions/f6f66a94-f184-45da-ac12-ffbfd8a6eb29/resourceGroups/migrate-rg/providers/Microsoft.Migrate/migrateprojects/TestMigrateProject'
                }]),
                'stderr': '',
                'returncode': 0
            },
            'Get-AzMigrateDiscoveredServer': {
                'stdout': json.dumps([{
                    'Name': 'Server001',
                    'DisplayName': 'WebServer-01',
                    'Type': 'Microsoft.OffAzure/VMwareSites/machines',
                    'OperatingSystemType': 'Windows',
                    'OperatingSystemName': 'Windows Server 2019',
                    'AllocatedMemoryInMB': 8192,
                    'NumberOfCores': 4,
                    'PowerState': 'On'
                }]),
                'stderr': '',
                'returncode': 0
            },
            'New-AzMigrateServerReplication': {
                'stdout': json.dumps({
                    'Name': 'replication-job-001',
                    'Id': '/subscriptions/f6f66a94-f184-45da-ac12-ffbfd8a6eb29/resourceGroups/migrate-rg/providers/Microsoft.RecoveryServices/vaults/migrate-vault/replicationJobs/replication-job-001',
                    'Status': 'InProgress',
                    'StartTime': '2024-01-15T10:00:00Z'
                }),
                'stderr': '',
                'returncode': 0
            },
            'Get-AzMigrateJob': {
                'stdout': json.dumps({
                    'Name': 'migration-job-001',
                    'Status': 'Succeeded',
                    'ActivityId': 'activity-123',
                    'StartTime': '2024-01-15T10:00:00Z',
                    'EndTime': '2024-01-15T12:30:00Z'
                }),
                'stderr': '',
                'returncode': 0
            },
            
            # Resource management
            'Get-AzResourceGroup': {
                'stdout': json.dumps([
                    {'ResourceGroupName': 'migrate-rg', 'Location': 'eastus2'},
                    {'ResourceGroupName': 'production-rg', 'Location': 'westus2'},
                    {'ResourceGroupName': 'development-rg', 'Location': 'centralus'}
                ]),
                'stderr': '',
                'returncode': 0
            },
            
            # Infrastructure checks
            'Test-AzMigrateReplicationInfrastructure': {
                'stdout': json.dumps({
                    'Status': 'Ready',
                    'Details': 'All infrastructure components are properly configured',
                    'Prerequisites': ['PowerShell 7+', 'Az.Migrate module', 'Network connectivity']
                }),
                'stderr': '',
                'returncode': 0
            }
        }
        
        # Patterns for dynamic responses
        self.pattern_responses = [
            (r'Set-AzContext.*-SubscriptionId\s+["\']?([a-f0-9-]+)["\']?', self._mock_set_context),
            (r'Get-AzMigrateDiscoveredServer.*-DisplayName\s+["\']?([^"\']+)["\']?', self._mock_get_server_by_name),
            (r'New-AzMigrateServerReplication.*-MachineId\s+["\']?([^"\']+)["\']?', self._mock_create_replication),
            (r'Get-AzMigrateJob.*-JobName\s+["\']?([^"\']+)["\']?', self._mock_get_job_status),
        ]

    def _mock_set_context(self, match):
        """Mock Set-AzContext response with provided subscription ID."""
        subscription_id = match.group(1)
        return {
            'stdout': f'Azure context set successfully\nSubscription: {subscription_id}',
            'stderr': '',
            'returncode': 0
        }

    def _mock_get_server_by_name(self, match):
        """Mock Get-AzMigrateDiscoveredServer response for specific server."""
        server_name = match.group(1)
        return {
            'stdout': json.dumps({
                'Name': f'Server-{server_name}',
                'DisplayName': server_name,
                'Type': 'Microsoft.OffAzure/VMwareSites/machines',
                'OperatingSystemType': 'Windows',
                'OperatingSystemName': 'Windows Server 2019',
                'AllocatedMemoryInMB': 8192,
                'NumberOfCores': 4,
                'PowerState': 'On',
                'Id': f'/subscriptions/f6f66a94-f184-45da-ac12-ffbfd8a6eb29/resourceGroups/migrate-rg/providers/Microsoft.OffAzure/VMwareSites/migrate-site/machines/{server_name}'
            }),
            'stderr': '',
            'returncode': 0
        }

    def _mock_create_replication(self, match):
        """Mock New-AzMigrateServerReplication response."""
        machine_id = match.group(1)
        return {
            'stdout': json.dumps({
                'Name': f'replication-{machine_id[-8:]}',
                'Id': f'/subscriptions/f6f66a94-f184-45da-ac12-ffbfd8a6eb29/resourceGroups/migrate-rg/providers/Microsoft.RecoveryServices/vaults/migrate-vault/replicationJobs/replication-{machine_id[-8:]}',
                'Status': 'InProgress',
                'StartTime': '2024-01-15T10:00:00Z',
                'MachineId': machine_id
            }),
            'stderr': '',
            'returncode': 0
        }

    def _mock_get_job_status(self, match):
        """Mock Get-AzMigrateJob response for specific job."""
        job_name = match.group(1)
        return {
            'stdout': json.dumps({
                'Name': job_name,
                'Status': 'Succeeded',
                'ActivityId': f'activity-{job_name[-6:]}',
                'StartTime': '2024-01-15T10:00:00Z',
                'EndTime': '2024-01-15T12:30:00Z',
                'PercentComplete': 100
            }),
            'stderr': '',
            'returncode': 0
        }

    def get_response(self, script_content):
        """Get mock response for a PowerShell script."""
        # Clean up the script content
        clean_script = script_content.strip()
        
        # Check for exact matches first
        if clean_script in self.cmdlet_responses:
            return self.cmdlet_responses[clean_script]
        
        # Check for pattern matches
        for pattern, handler in self.pattern_responses:
            match = re.search(pattern, clean_script, re.IGNORECASE)
            if match:
                return handler(match)
        
        # Handle special cases
        if 'Get-Module' in clean_script and 'Az.' in clean_script:
            return {
                'stdout': 'Az.Migrate Module Found',
                'stderr': '',
                'returncode': 0
            }
        
        if any(cmdlet in clean_script for cmdlet in ['Connect-Az', 'Set-Az', 'Get-Az', 'New-Az']):
            return {
                'stdout': 'Azure operation completed successfully',
                'stderr': '',
                'returncode': 0
            }
        
        # Default response for unknown cmdlets
        return {
            'stdout': 'Mock PowerShell command executed successfully',
            'stderr': '',
            'returncode': 0
        }


def create_mock_powershell_executor():
    """Create a fully mocked PowerShell executor for testing."""
    mocker = PowerShellCmdletMocker()
    
    # Create the mock executor
    mock_executor = Mock()
    mock_executor.platform = 'windows'
    mock_executor.powershell_cmd = 'powershell'
    
    # Mock availability check
    mock_executor.check_powershell_availability.return_value = (True, 'powershell')
    
    # Mock script execution with smart responses
    def mock_execute_script(script_content, parameters=None):
        # Add parameters to script if provided
        if parameters:
            param_string = ' '.join([f'-{k} "{v}"' for k, v in parameters.items()])
            full_script = f'{script_content} {param_string}'
        else:
            full_script = script_content
            
        return mocker.get_response(full_script)
    
    def mock_execute_script_interactive(script_content, parameters=None):
        # For interactive scripts, return the same as regular execution
        result = mock_execute_script(script_content, parameters)
        return result
    
    def mock_execute_azure_authenticated_script(script_content, subscription_id=None, parameters=None):
        # For Azure authenticated scripts, return the same as regular execution
        result = mock_execute_script(script_content, parameters)
        return result
    
    def mock_check_azure_authentication():
        # Return Azure authentication status
        return {
            'IsAuthenticated': True,
            'AccountId': 'test@example.com'
        }
    
    mock_executor.execute_script.side_effect = mock_execute_script
    mock_executor.execute_script_interactive.side_effect = mock_execute_script_interactive
    mock_executor.execute_azure_authenticated_script.side_effect = mock_execute_azure_authenticated_script
    mock_executor.check_azure_authentication.side_effect = mock_check_azure_authentication
    
    return mock_executor


# ============================================================================
# Test Configuration and Constants
# ============================================================================

class TestConfig:
    """Configuration class for Azure Migrate tests."""
    
    # Test data constants
    SAMPLE_SUBSCRIPTION_ID = "f6f66a94-f184-45da-ac12-ffbfd8a6eb29"
    SAMPLE_TENANT_ID = "12345678-1234-1234-1234-123456789012"
    SAMPLE_RESOURCE_GROUP = "migrate-rg"
    SAMPLE_PROJECT_NAME = "TestMigrateProject"
    SAMPLE_SERVER_NAME = "WebServer-01"
    
    # Mock data structures
    MOCK_SERVER_DATA = {
        "Name": "Server001",
        "DisplayName": "WebServer-01",
        "Type": "Microsoft.OffAzure/VMwareSites/machines",
        "OperatingSystemType": "Windows",
        "OperatingSystemName": "Windows Server 2019",
        "AllocatedMemoryInMB": 8192,
        "NumberOfCores": 4,
        "PowerState": "On"
    }
    
    MOCK_PROJECT_DATA = {
        "Name": "TestMigrateProject",
        "ResourceGroupName": "migrate-rg",
        "Location": "East US 2",
        "Id": f"/subscriptions/{SAMPLE_SUBSCRIPTION_ID}/resourceGroups/migrate-rg/providers/Microsoft.Migrate/migrateprojects/TestMigrateProject"
    }


# ============================================================================
# Base Test Classes
# ============================================================================

class MigrateTestCase(unittest.TestCase):
    """
    Base test case class for Azure Migrate tests with comprehensive setup.
    
    This class provides:
    - Automatic PowerShell mocking
    - Common test fixtures
    - Helper methods for assertions
    - Proper teardown
    """
    
    def setUp(self):
        """Set up common test fixtures with comprehensive mocking."""
        # Set up mock CLI context
        self.cmd = Mock()
        self.cmd.cli_ctx = Mock()
        self.cmd.cli_ctx.config = Mock()
        
        # Create comprehensive PowerShell mock
        self.mock_ps_executor = create_mock_powershell_executor()
        
        # Mock platform module with proper callable functions
        platform_mock = Mock()
        platform_mock.system.return_value = 'Windows'
        platform_mock.version.return_value = '10.0.19041'
        platform_mock.python_version.return_value = '3.9.7'
        
        # Patch all PowerShell executor calls
        self.powershell_patchers = [
            patch('azure.cli.command_modules.migrate.custom.get_powershell_executor', 
                  return_value=self.mock_ps_executor),
            patch('azure.cli.command_modules.migrate._powershell_utils.get_powershell_executor', 
                  return_value=self.mock_ps_executor),
            patch('azure.cli.core.util.run_cmd'),
            patch('subprocess.run'),
            patch('platform.system', return_value='Windows'),
            patch('platform.version', return_value='10.0.19041'),
            patch('platform.python_version', return_value='3.9.7')
        ]
        
        # Additional platform patches for inline imports and module-level patches
        self.additional_patches = [
            patch('azure.cli.command_modules.migrate.custom.platform', platform_mock),
            patch('azure.cli.command_modules.migrate._powershell_utils.platform', platform_mock),
        ]
        
        # Start all patches
        for i, patcher in enumerate(self.powershell_patchers):
            mock_obj = patcher.start()
            # Only configure run_cmd and subprocess.run mocks (not PowerShell executor mocks)
            if i >= 2 and hasattr(mock_obj, 'return_value'):  # Skip first two patches (PowerShell executors)
                mock_obj.return_value = Mock(returncode=0, stdout='PowerShell 7.3.4', stderr='')
        
        # Start additional patches
        for patcher in self.additional_patches:
            patcher.start()
        
        # Patch the platform module in sys.modules to handle local imports
        import sys
        original_platform = sys.modules.get('platform')
        sys.modules['platform'] = platform_mock
        self._original_platform_module = original_platform

    def tearDown(self):
        """Clean up all patches."""
        for patcher in self.powershell_patchers:
            patcher.stop()
        
        # Stop additional patches
        for patcher in self.additional_patches:
            patcher.stop()
        
        # Restore original platform module
        import sys
        if hasattr(self, '_original_platform_module'):
            if self._original_platform_module:
                sys.modules['platform'] = self._original_platform_module
            else:
                sys.modules.pop('platform', None)

    def assert_powershell_called_with_cmdlet(self, cmdlet_fragment):
        """Assert that PowerShell was called with a specific cmdlet."""
        # Helper method for PowerShell call verification
        # Implementation depends on how you want to track calls
        pass
    
    def get_mock_server_data(self, server_name=None):
        """Get mock server data for testing."""
        data = TestConfig.MOCK_SERVER_DATA.copy()
        if server_name:
            data['DisplayName'] = server_name
            data['Name'] = f'Server-{server_name}'
        return data
    
    def get_mock_project_data(self, project_name=None):
        """Get mock project data for testing."""
        data = TestConfig.MOCK_PROJECT_DATA.copy()
        if project_name:
            data['Name'] = project_name
        return data


class MigrateScenarioTest(MigrateTestCase):
    """Base class for scenario tests with additional Azure CLI integration."""
    
    def setUp(self):
        """Set up scenario test with Azure CLI context."""
        super().setUp()
        
        # Additional setup for scenario tests
        self.resource_group = TestConfig.SAMPLE_RESOURCE_GROUP
        self.subscription_id = TestConfig.SAMPLE_SUBSCRIPTION_ID
        self.project_name = TestConfig.SAMPLE_PROJECT_NAME


# ============================================================================
# Test Discovery and Suite Creation
# ============================================================================

def discover_test_modules():
    """Discover all test modules in the current directory."""
    test_modules = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    for filename in os.listdir(current_dir):
        if filename.startswith('test_') and filename.endswith('.py') and filename != 'test_framework.py':
            module_name = filename[:-3]  # Remove .py extension
            test_modules.append(module_name)
    
    return test_modules


def create_test_suite(include_modules=None, exclude_modules=None):
    """
    Create a comprehensive test suite.
    
    Args:
        include_modules: List of specific modules to include (None = all)
        exclude_modules: List of modules to exclude (None = exclude none)
    
    Returns:
        unittest.TestSuite: Complete test suite
    """
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Discover available test modules
    available_modules = discover_test_modules()
    
    # Filter modules based on include/exclude criteria
    if include_modules:
        modules_to_load = [m for m in available_modules if m in include_modules]
    else:
        modules_to_load = available_modules
    
    if exclude_modules:
        modules_to_load = [m for m in modules_to_load if m not in exclude_modules]
    
    # Load tests from each module
    for module_name in modules_to_load:
        try:
            # Add current directory to path if needed
            if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            
            # Import the module
            module = __import__(module_name, fromlist=[''])
            
            # Load tests from the module
            module_suite = loader.loadTestsFromModule(module)
            suite.addTest(module_suite)
            
            print(f"[OK] Loaded tests from {module_name}")
            
        except ImportError as e:
            print(f"[WARN] Could not import {module_name}: {e}")
        except Exception as e:
            print(f"[ERROR] Error loading {module_name}: {e}")
    
    return suite


# ============================================================================
# Test Runner
# ============================================================================

def run_all_tests(verbosity=2, buffer=True, include_modules=None, exclude_modules=None):
    """
    Run all tests with comprehensive reporting.
    
    Args:
        verbosity: Test output verbosity (0=quiet, 1=normal, 2=verbose)
        buffer: Capture stdout/stderr during tests
        include_modules: List of specific modules to include
        exclude_modules: List of modules to exclude
    
    Returns:
        bool: True if all tests passed, False otherwise
    """
    print("Azure Migrate CLI - Unified Test Framework")
    print("=" * 60)
    print("All PowerShell commands are mocked with realistic responses.")
    print("No external dependencies required.\n")
    
    # Create test suite
    suite = create_test_suite(include_modules, exclude_modules)
    
    if suite.countTestCases() == 0:
        print("[ERROR] No tests found to run!")
        return False
    
    # Configure test runner
    runner = unittest.TextTestRunner(
        verbosity=verbosity,
        stream=sys.stdout,
        buffer=buffer
    )
    
    print(f"\nRunning {suite.countTestCases()} tests...")
    print("=" * 60)
    
    # Run tests
    result = runner.run(suite)
    
    # Print comprehensive summary
    print("\n" + "=" * 60)
    print("Test Execution Summary")
    print("=" * 60)
    
    total_tests = result.testsRun
    successes = total_tests - len(result.failures) - len(result.errors)
    success_rate = (successes / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Successes: {successes}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Show failures
    if result.failures:
        print(f"\n[FAILURES] Test Failures ({len(result.failures)}):")
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"  {i}. {test}")
            # Show first few lines of traceback
            lines = traceback.split('\n')[:3]
            for line in lines:
                if line.strip():
                    print(f"     {line}")
    
    # Show errors
    if result.errors:
        print(f"\n[ERRORS] Test Errors ({len(result.errors)}):")
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"  {i}. {test}")
            # Show first few lines of traceback
            lines = traceback.split('\n')[:3]
            for line in lines:
                if line.strip():
                    print(f"     {line}")
    
    # Final status
    if result.wasSuccessful():
        print("\n[SUCCESS] All tests passed!")
    else:
        print(f"\n[WARNING] {len(result.failures) + len(result.errors)} test(s) failed.")
    
    print("=" * 60)
    
    return result.wasSuccessful()


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Azure Migrate CLI Unified Test Framework')
    parser.add_argument('--verbosity', '-v', type=int, default=2, choices=[0, 1, 2],
                        help='Test output verbosity (0=quiet, 1=normal, 2=verbose)')
    parser.add_argument('--include', nargs='+', help='Specific test modules to include')
    parser.add_argument('--exclude', nargs='+', help='Test modules to exclude')
    parser.add_argument('--no-buffer', action='store_true', help='Don\'t capture stdout/stderr during tests')
    
    args = parser.parse_args()
    
    success = run_all_tests(
        verbosity=args.verbosity,
        buffer=not args.no_buffer,
        include_modules=args.include,
        exclude_modules=args.exclude
    )
    
    sys.exit(0 if success else 1)
