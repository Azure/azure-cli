# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Test configuration and utilities for Azure Migrate CLI module tests.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch


class MigrateTestConfig:
    """Configuration class for Azure Migrate tests."""
    
    # Test data constants
    TEST_RESOURCE_GROUP = 'test-migrate-rg'
    TEST_PROJECT_NAME = 'test-migrate-project'
    TEST_SUBSCRIPTION_ID = '00000000-0000-0000-0000-000000000000'
    TEST_TENANT_ID = '11111111-1111-1111-1111-111111111111'
    TEST_VM_NAME = 'test-vm'
    TEST_TARGET_VM_NAME = 'migrated-test-vm'
    TEST_DISK_ID = 'disk-001'
    TEST_NIC_ID = 'nic-001'
    
    # Mock responses
    MOCK_DISCOVERED_SERVERS_RESPONSE = {
        'DiscoveredServers': [
            {
                'Id': '/subscriptions/test/machines/vm1',
                'Name': 'vm1',
                'DisplayName': 'Test VM 1',
                'Type': 'Microsoft.OffAzure/VMwareSites/machines',
                'Disk': [
                    {
                        'Uuid': 'disk-001',
                        'IsOSDisk': True,
                        'SizeInGB': 64
                    }
                ],
                'NetworkAdapter': [
                    {
                        'NicId': 'nic-001',
                        'IpAddress': '192.168.1.100'
                    }
                ]
            }
        ],
        'Count': 1,
        'ProjectName': TEST_PROJECT_NAME,
        'ResourceGroupName': TEST_RESOURCE_GROUP
    }
    
    MOCK_AUTHENTICATION_SUCCESS = {
        'IsAuthenticated': True,
        'AccountId': 'test@example.com',
        'TenantId': TEST_TENANT_ID,
        'SubscriptionId': TEST_SUBSCRIPTION_ID
    }
    
    MOCK_AUTHENTICATION_FAILURE = {
        'IsAuthenticated': False,
        'Error': 'No authentication context found'
    }
    
    MOCK_PREREQUISITES_SUCCESS = {
        'platform': 'Windows',
        'platform_version': '10.0.19041',
        'python_version': '3.9.7',
        'powershell_available': True,
        'powershell_version': '7.3.0',
        'azure_powershell_available': True,
        'recommendations': []
    }
    
    MOCK_PREREQUISITES_POWERSHELL_MISSING = {
        'platform': 'Linux',
        'platform_version': '5.4.0',
        'python_version': '3.9.7',
        'powershell_available': False,
        'powershell_version': None,
        'azure_powershell_available': False,
        'recommendations': ['Install PowerShell Core']
    }


class MockPowerShellExecutor:
    """Mock PowerShell executor for testing."""
    
    def __init__(self, 
                 powershell_available=True,
                 azure_authenticated=True,
                 script_responses=None):
        self.powershell_available = powershell_available
        self.azure_authenticated = azure_authenticated
        self.script_responses = script_responses or {}
        self.call_history = []
    
    def check_powershell_availability(self):
        """Mock PowerShell availability check."""
        self.call_history.append('check_powershell_availability')
        if self.powershell_available:
            return True, 'powershell'
        return False, None
    
    def check_azure_authentication(self):
        """Mock Azure authentication check."""
        self.call_history.append('check_azure_authentication')
        if self.azure_authenticated:
            return MigrateTestConfig.MOCK_AUTHENTICATION_SUCCESS
        return MigrateTestConfig.MOCK_AUTHENTICATION_FAILURE
    
    def execute_script(self, script, parameters=None):
        """Mock script execution."""
        self.call_history.append(f'execute_script: {script[:50]}...')
        
        # Return predefined responses based on script content
        if 'PSVersionTable' in script:
            return {'stdout': '7.3.0', 'stderr': '', 'returncode': 0}
        elif 'Get-Module' in script:
            return {'stdout': 'Az.Migrate Module Found', 'stderr': '', 'returncode': 0}
        elif script in self.script_responses:
            return self.script_responses[script]
        
        return {'stdout': 'Mock response', 'stderr': '', 'returncode': 0}
    
    def execute_script_interactive(self, script):
        """Mock interactive script execution."""
        self.call_history.append(f'execute_script_interactive: {script[:50]}...')
        return {'returncode': 0}
    
    def execute_azure_authenticated_script(self, script, subscription_id=None):
        """Mock Azure authenticated script execution."""
        self.call_history.append(f'execute_azure_authenticated_script: {script[:50]}...')
        
        # Return discovered servers response for discovery scripts
        if 'Get-AzMigrateDiscoveredServer' in script:
            import json
            return {
                'stdout': json.dumps(MigrateTestConfig.MOCK_DISCOVERED_SERVERS_RESPONSE),
                'stderr': ''
            }
        
        return {'stdout': 'Azure script executed', 'stderr': ''}


class MigrateTestCase(unittest.TestCase):
    """Base test case class for Azure Migrate tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Start PowerShell executor mock
        self.ps_executor_patcher = patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
        self.mock_ps_executor_getter = self.ps_executor_patcher.start()
        
        # Create mock executor with default successful responses
        self.mock_ps_executor = MockPowerShellExecutor()
        self.mock_ps_executor_getter.return_value = self.mock_ps_executor
        
        # Mock platform detection
        self.platform_patcher = patch('platform.system')
        self.mock_platform = self.platform_patcher.start()
        self.mock_platform.return_value = 'Windows'
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.ps_executor_patcher.stop()
        self.platform_patcher.stop()
        super().tearDown()
    
    def configure_mock_executor(self, 
                              powershell_available=True,
                              azure_authenticated=True,
                              script_responses=None):
        """Configure the mock PowerShell executor."""
        self.mock_ps_executor = MockPowerShellExecutor(
            powershell_available=powershell_available,
            azure_authenticated=azure_authenticated,
            script_responses=script_responses
        )
        self.mock_ps_executor_getter.return_value = self.mock_ps_executor
    
    def assert_powershell_called(self, method_name):
        """Assert that a specific PowerShell method was called."""
        self.assertIn(method_name, self.mock_ps_executor.call_history)
    
    def assert_script_contains(self, expected_content):
        """Assert that a script containing specific content was executed."""
        for call in self.mock_ps_executor.call_history:
            if 'execute_script' in call and expected_content in call:
                return
        self.fail(f"No script call found containing: {expected_content}")


def create_test_suite():
    """Create a comprehensive test suite for the migrate module."""
    from azure.cli.command_modules.migrate.tests.latest.test_migrate_custom import (
        TestMigratePowerShellUtils,
        TestMigrateDiscoveryCommands,
        TestMigrateReplicationCommands,
        TestMigrateLocalCommands,
        TestMigrateInfrastructureCommands,
        TestMigrateAuthenticationCommands,
        TestMigrateUtilityCommands,
        TestMigrateErrorHandling
    )
    
    from azure.cli.command_modules.migrate.tests.latest.test_powershell_utils import (
        TestPowerShellExecutor,
        TestPowerShellExecutorFactory,
        TestPowerShellExecutorEdgeCases
    )
    
    from azure.cli.command_modules.migrate.tests.latest.test_migrate_commands import (
        TestMigrateCommandLoading,
        TestMigrateCommandParameters,
        TestMigrateCommandValidation,
        TestMigrateCommandIntegration
    )
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add custom function tests
    suite.addTest(unittest.makeSuite(TestMigratePowerShellUtils))
    suite.addTest(unittest.makeSuite(TestMigrateDiscoveryCommands))
    suite.addTest(unittest.makeSuite(TestMigrateReplicationCommands))
    suite.addTest(unittest.makeSuite(TestMigrateLocalCommands))
    suite.addTest(unittest.makeSuite(TestMigrateInfrastructureCommands))
    suite.addTest(unittest.makeSuite(TestMigrateAuthenticationCommands))
    suite.addTest(unittest.makeSuite(TestMigrateUtilityCommands))
    suite.addTest(unittest.makeSuite(TestMigrateErrorHandling))
    
    # Add PowerShell utility tests
    suite.addTest(unittest.makeSuite(TestPowerShellExecutor))
    suite.addTest(unittest.makeSuite(TestPowerShellExecutorFactory))
    suite.addTest(unittest.makeSuite(TestPowerShellExecutorEdgeCases))
    
    # Add command loading and integration tests
    suite.addTest(unittest.makeSuite(TestMigrateCommandLoading))
    suite.addTest(unittest.makeSuite(TestMigrateCommandParameters))
    suite.addTest(unittest.makeSuite(TestMigrateCommandValidation))
    suite.addTest(unittest.makeSuite(TestMigrateCommandIntegration))
    
    return suite


def run_tests(verbosity=2):
    """Run all tests with specified verbosity."""
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
