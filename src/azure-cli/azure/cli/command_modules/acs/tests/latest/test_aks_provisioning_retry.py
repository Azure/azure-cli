# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import unittest
from unittest.mock import MagicMock, patch

from azure.cli.testsdk.checkers import JMESPathCheck
from knack.util import CLIError


class MockExecutionResult:
    def __init__(self, output_json):
        self._json = output_json
        self.output = json.dumps(output_json)
        self.json_value = None
        self.skip_assert = False

    def get_output_in_json(self):
        return self._json

    def assert_with_checks(self, *args):
        checks = []
        for each in args:
            if isinstance(each, list):
                checks.extend(each)
            elif callable(each):
                checks.append(each)
        if not self.skip_assert:
            for c in checks:
                c(self)
        return self


class TestShouldRetryForProvisioningState(unittest.TestCase):

    def _make_instance(self):
        from azure.cli.command_modules.acs.tests.latest.test_aks_commands import (
            AzureKubernetesServiceScenarioTest,
        )
        return object.__new__(AzureKubernetesServiceScenarioTest)

    def test_non_terminal_state_returns_true(self):
        inst = self._make_instance()
        result = MockExecutionResult({
            'id': '/subscriptions/xxx/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/mc',
            'provisioningState': 'Updating',
        })
        should_retry, resource_id = inst._should_retry_for_provisioning_state(result)
        self.assertTrue(should_retry)
        self.assertIn('managedClusters/mc', resource_id)

    def test_succeeded_returns_false(self):
        inst = self._make_instance()
        result = MockExecutionResult({'id': '/subscriptions/xxx/rg/mc', 'provisioningState': 'Succeeded'})
        should_retry, _ = inst._should_retry_for_provisioning_state(result)
        self.assertFalse(should_retry)

    def test_failed_raises_assertion(self):
        inst = self._make_instance()
        result = MockExecutionResult({'id': '/subscriptions/xxx/rg/mc', 'provisioningState': 'Failed'})
        with self.assertRaises(AssertionError):
            inst._should_retry_for_provisioning_state(result)

    def test_canceled_raises_assertion(self):
        inst = self._make_instance()
        result = MockExecutionResult({'id': '/subscriptions/xxx/rg/mc', 'provisioningState': 'Canceled'})
        with self.assertRaises(AssertionError):
            inst._should_retry_for_provisioning_state(result)

    def test_no_id_returns_false(self):
        inst = self._make_instance()
        result = MockExecutionResult({'provisioningState': 'Updating'})
        should_retry, _ = inst._should_retry_for_provisioning_state(result)
        self.assertFalse(should_retry)

    def test_list_response_returns_false(self):
        inst = self._make_instance()
        result = MockExecutionResult([{'id': '/some/id', 'provisioningState': 'Updating'}])
        should_retry, _ = inst._should_retry_for_provisioning_state(result)
        self.assertFalse(should_retry)


class TestCmdRetryDispatch(unittest.TestCase):

    @patch.dict(os.environ, {'AZURE_CLI_TEST_RETRY_PROVISIONING_CHECK': 'true'})
    def test_live_command_without_checks_uses_retry_path(self):
        from azure.cli.command_modules.acs.tests.latest.test_aks_commands import (
            AzureKubernetesServiceScenarioTest,
        )
        instance = object.__new__(AzureKubernetesServiceScenarioTest)
        instance.is_live = True
        instance._cmd_with_retry = MagicMock()

        instance.cmd('aks delete', checks=None, expect_failure=False)

        instance._cmd_with_retry.assert_called_once_with('aks delete', [], False)


class TestCmdWithRetry(unittest.TestCase):

    def _make_instance(self):
        from azure.cli.command_modules.acs.tests.latest.test_aks_commands import (
            AzureKubernetesServiceScenarioTest,
        )
        instance = object.__new__(AzureKubernetesServiceScenarioTest)
        instance.kwargs = {}
        instance._apply_kwargs = lambda cmd: cmd
        instance.cli_ctx = MagicMock()
        return instance

    def _result(self, data):
        return MockExecutionResult(data)

    @patch.dict(os.environ, {'AZURE_CLI_TEST_PROVISIONING_MAX_RETRIES': '3', 'AZURE_CLI_TEST_PROVISIONING_BASE_DELAY': '0.01'})
    @patch('time.sleep', return_value=None)
    @patch('random.uniform', return_value=0)
    @patch('azure.cli.testsdk.base.execute')
    def test_no_retry_when_already_succeeded(self, mock_execute, _mock_random, _mock_sleep):
        mock_execute.return_value = self._result({'id': '/rg/mc', 'provisioningState': 'Succeeded'})
        self._make_instance()._cmd_with_retry('aks show', [JMESPathCheck('provisioningState', 'Succeeded')], False)
        mock_execute.assert_called_once()

    @patch.dict(os.environ, {'AZURE_CLI_TEST_PROVISIONING_MAX_RETRIES': '3', 'AZURE_CLI_TEST_PROVISIONING_BASE_DELAY': '0.01'})
    @patch('time.sleep', return_value=None)
    @patch('random.uniform', return_value=0)
    @patch('azure.cli.testsdk.base.execute')
    def test_retries_until_succeeded(self, mock_execute, _mock_random, _mock_sleep):
        resource_id = '/subscriptions/xxx/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/mc'
        mock_execute.side_effect = [
            self._result({'id': resource_id, 'provisioningState': 'Updating'}),
            self._result({'provisioningState': 'Updating'}),
            self._result({'provisioningState': 'Succeeded'}),
            self._result({'provisioningState': 'Succeeded'}),
        ]
        self._make_instance()._cmd_with_retry('aks show', [JMESPathCheck('provisioningState', 'Succeeded')], False)
        self.assertEqual(mock_execute.call_count, 4)

    @patch.dict(os.environ, {'AZURE_CLI_TEST_PROVISIONING_MAX_RETRIES': '2', 'AZURE_CLI_TEST_PROVISIONING_BASE_DELAY': '0.01'})
    @patch('time.sleep', return_value=None)
    @patch('random.uniform', return_value=0)
    @patch('azure.cli.testsdk.base.execute')
    def test_raises_on_failed_state(self, mock_execute, _mock_random, _mock_sleep):
        mock_execute.side_effect = [
            self._result({'id': '/rg/mc', 'provisioningState': 'Updating'}),
            self._result({'provisioningState': 'Failed'}),
        ]
        with self.assertRaises(AssertionError):
            self._make_instance()._cmd_with_retry('aks show', [JMESPathCheck('provisioningState', 'Succeeded')], False)

    @patch.dict(os.environ, {'AZURE_CLI_TEST_PROVISIONING_MAX_RETRIES': '2', 'AZURE_CLI_TEST_PROVISIONING_BASE_DELAY': '0.01'})
    @patch('time.sleep', return_value=None)
    @patch('random.uniform', return_value=0)
    @patch('azure.cli.testsdk.base.execute')
    def test_raises_immediately_on_initial_failed_state(self, mock_execute, _mock_random, _mock_sleep):
        mock_execute.return_value = self._result({'id': '/rg/mc', 'provisioningState': 'Failed'})
        with self.assertRaises(AssertionError):
            self._make_instance()._cmd_with_retry('aks show', [JMESPathCheck('provisioningState', 'Succeeded')], False)
        mock_execute.assert_called_once()

    @patch.dict(os.environ, {'AZURE_CLI_TEST_PROVISIONING_MAX_RETRIES': '2', 'AZURE_CLI_TEST_PROVISIONING_BASE_DELAY': '0.01'})
    @patch('time.sleep', return_value=None)
    @patch('random.uniform', return_value=0)
    @patch('azure.cli.testsdk.base.execute')
    def test_raises_timeout_after_max_retries(self, mock_execute, _mock_random, _mock_sleep):
        poll = self._result({'provisioningState': 'Updating'})
        mock_execute.side_effect = [self._result({'id': '/rg/mc', 'provisioningState': 'Updating'}), poll, poll]
        with self.assertRaises(TimeoutError):
            self._make_instance()._cmd_with_retry('aks show', [JMESPathCheck('provisioningState', 'Succeeded')], False)

    @patch.dict(os.environ, {'AZURE_CLI_TEST_PROVISIONING_MAX_RETRIES': '3', 'AZURE_CLI_TEST_PROVISIONING_BASE_DELAY': '0.01'})
    @patch('time.sleep', return_value=None)
    @patch('random.uniform', return_value=0)
    @patch('azure.cli.testsdk.base.execute')
    def test_non_provisioning_checks_still_run(self, mock_execute, _mock_random, _mock_sleep):
        mock_execute.return_value = self._result({'id': '/rg/mc', 'name': 'mc', 'provisioningState': 'Succeeded'})
        name_check = MagicMock()
        self._make_instance()._cmd_with_retry('aks show', [JMESPathCheck('provisioningState', 'Succeeded'), name_check], False)
        name_check.assert_called_once()

    @patch.dict(os.environ, {'AZURE_CLI_TEST_PROVISIONING_MAX_RETRIES': '2', 'AZURE_CLI_TEST_PROVISIONING_BASE_DELAY': '0.01'})
    @patch('time.sleep', return_value=None)
    @patch('random.uniform', return_value=0)
    @patch('azure.cli.testsdk.base.execute')
    def test_checks_and_return_value_use_settled_response(self, mock_execute, _mock_random, _mock_sleep):
        resource_id = '/subscriptions/xxx/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/mc'
        initial_result = self._result({
            'id': resource_id,
            'provisioningState': 'Updating',
            'feature': {'enabled': False},
        })
        settled_result = self._result({
            'id': resource_id,
            'provisioningState': 'Succeeded',
            'feature': {'enabled': True},
        })
        mock_execute.side_effect = [initial_result, settled_result]
        instance = self._make_instance()
        instance._refetch_settled_aks_result = MagicMock(return_value=settled_result)

        result = instance._cmd_with_retry(
            'aks show',
            [
                JMESPathCheck('provisioningState', 'Succeeded'),
                JMESPathCheck('feature.enabled', True),
            ],
            False,
        )

        self.assertIs(result, settled_result)
        instance._refetch_settled_aks_result.assert_called_once_with(resource_id, initial_result)

    @patch.dict(os.environ, {'AZURE_CLI_TEST_PROVISIONING_MAX_RETRIES': '3', 'AZURE_CLI_TEST_PROVISIONING_BASE_DELAY': '0.01'})
    @patch('time.sleep', return_value=None)
    @patch('random.uniform', return_value=0)
    @patch('azure.cli.testsdk.base.execute')
    def test_missing_provisioning_state_fails_loudly(self, mock_execute, _mock_random, _mock_sleep):
        # Regression: when the response body has no 'provisioningState',
        # _should_retry_for_provisioning_state returns (False, None) and the
        # adapter MUST still run the provisioning check against the result
        # so the assertion fails loudly rather than being silently dropped.
        from azure.cli.testsdk.exceptions import JMESPathCheckAssertionError
        mock_execute.return_value = self._result({'id': '/rg/mc', 'name': 'mc'})
        with self.assertRaises(JMESPathCheckAssertionError):
            self._make_instance()._cmd_with_retry(
                'aks show',
                [JMESPathCheck('provisioningState', 'Succeeded')],
                False,
            )

    @patch.dict(os.environ, {'AZURE_CLI_TEST_PROVISIONING_MAX_RETRIES': '3', 'AZURE_CLI_TEST_PROVISIONING_BASE_DELAY': '0.01'})
    @patch('time.sleep', return_value=None)
    @patch('random.uniform', return_value=0)
    @patch('azure.cli.testsdk.base.execute')
    def test_missing_id_fails_loudly(self, mock_execute, _mock_random, _mock_sleep):
        # Regression: when the response body has no 'id', polling cannot
        # proceed; the provisioning check MUST still run against the result
        # rather than be silently dropped.
        from azure.cli.testsdk.exceptions import JMESPathCheckAssertionError
        mock_execute.return_value = self._result({'provisioningState': 'Updating'})
        with self.assertRaises(JMESPathCheckAssertionError):
            self._make_instance()._cmd_with_retry(
                'aks show',
                [JMESPathCheck('provisioningState', 'Succeeded')],
                False,
            )

    @patch.dict(os.environ, {
        'AZURE_CLI_TEST_PROVISIONING_MAX_RETRIES': '5',
        'AZURE_CLI_TEST_PROVISIONING_BASE_DELAY': '2.0',
        'AZURE_CLI_TEST_PROVISIONING_MAX_DELAY': '10.0',
    })
    @patch('time.sleep', return_value=None)
    @patch('random.uniform', return_value=0)
    @patch('azure.cli.testsdk.base.execute')
    def test_delay_is_clamped_to_max_delay(self, mock_execute, _mock_random, mock_sleep):
        # Regression: exponential backoff must be capped by
        # AZURE_CLI_TEST_PROVISIONING_MAX_DELAY so a single sleep can't grow
        # unbounded (e.g. base 2.0 * 2^9 = 1024s on attempt 9).
        resource_id = '/subscriptions/xxx/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/mc'
        mock_execute.side_effect = [
            self._result({'id': resource_id, 'provisioningState': 'Updating'}),
            self._result({'provisioningState': 'Updating'}),
            self._result({'provisioningState': 'Updating'}),
            self._result({'provisioningState': 'Updating'}),
            self._result({'provisioningState': 'Updating'}),
            self._result({'provisioningState': 'Succeeded'}),
            self._result({'provisioningState': 'Succeeded'}),
        ]
        self._make_instance()._cmd_with_retry('aks show', [JMESPathCheck('provisioningState', 'Succeeded')], False)
        # Without the cap, attempts 3 and 4 would sleep 16s and 32s.
        # With max_delay=10.0 and jitter pinned to 0, every sleep must be <= 10.0.
        for call in mock_sleep.call_args_list:
            self.assertLessEqual(call.args[0], 10.0)


class TestExecuteWithTransientConflictRetry(unittest.TestCase):

    def _make_instance(self):
        from azure.cli.command_modules.acs.tests.latest.test_aks_commands import (
            AzureKubernetesServiceScenarioTest,
        )
        instance = object.__new__(AzureKubernetesServiceScenarioTest)
        instance.cli_ctx = MagicMock()
        return instance

    @patch.dict(os.environ, {
        'AZURE_CLI_TEST_OPERATION_MAX_RETRIES': '3',
        'AZURE_CLI_TEST_OPERATION_BASE_DELAY': '0.01',
    })
    @patch('time.sleep', return_value=None)
    @patch('random.uniform', return_value=0)
    @patch('azure.cli.testsdk.base.execute')
    def test_retries_transient_operation_conflict(self, mock_execute, _mock_random, mock_sleep):
        expected = MockExecutionResult({'provisioningState': 'Succeeded'})
        mock_execute.side_effect = [
            CLIError('Operation is not allowed: Another operation is in progress.'),
            expected,
        ]

        result = self._make_instance()._execute_with_transient_conflict_retry('aks update', False)

        self.assertIs(result, expected)
        self.assertEqual(mock_execute.call_count, 2)
        mock_sleep.assert_called_once()

    @patch.dict(os.environ, {'AZURE_CLI_TEST_OPERATION_MAX_RETRIES': '3'})
    @patch('time.sleep', return_value=None)
    @patch('azure.cli.testsdk.base.execute')
    def test_does_not_retry_other_errors(self, mock_execute, mock_sleep):
        mock_execute.side_effect = CLIError('Invalid parameter')

        with self.assertRaisesRegex(CLIError, 'Invalid parameter'):
            self._make_instance()._execute_with_transient_conflict_retry('aks update', False)

        mock_execute.assert_called_once()
        mock_sleep.assert_not_called()

    @patch.dict(os.environ, {'AZURE_CLI_TEST_OPERATION_MAX_RETRIES': '3'})
    @patch('time.sleep', return_value=None)
    @patch('azure.cli.testsdk.base.execute')
    def test_does_not_retry_expected_failure(self, mock_execute, mock_sleep):
        mock_execute.side_effect = CLIError(
            'Operation is not allowed: in-progress PutExtensionAddonHandler.PUT operation'
        )

        with self.assertRaises(CLIError):
            self._make_instance()._execute_with_transient_conflict_retry('aks update', True)

        mock_execute.assert_called_once()
        mock_sleep.assert_not_called()


class TestRefetchSettledAksResult(unittest.TestCase):

    def _make_instance(self):
        from azure.cli.command_modules.acs.tests.latest.test_aks_commands import (
            AzureKubernetesServiceScenarioTest,
        )
        instance = object.__new__(AzureKubernetesServiceScenarioTest)
        instance.cli_ctx = MagicMock()
        return instance

    @patch('azure.cli.testsdk.base.execute')
    def test_refetches_managed_cluster_with_native_show(self, mock_execute):
        expected = MockExecutionResult({'provisioningState': 'Succeeded'})
        mock_execute.return_value = expected
        resource_id = (
            '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ContainerService/'
            'managedClusters/cluster'
        )
        instance = self._make_instance()

        result = instance._refetch_settled_aks_result(resource_id, MagicMock())

        self.assertIs(result, expected)
        mock_execute.assert_called_once_with(
            instance.cli_ctx,
            'aks show --resource-group rg --name cluster',
            expect_failure=False,
        )

    @patch('azure.cli.testsdk.base.execute')
    def test_refetches_agent_pool_with_native_show(self, mock_execute):
        expected = MockExecutionResult({'provisioningState': 'Succeeded'})
        mock_execute.return_value = expected
        resource_id = (
            '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ContainerService/'
            'managedClusters/cluster/agentPools/pool'
        )
        instance = self._make_instance()

        result = instance._refetch_settled_aks_result(resource_id, MagicMock())

        self.assertIs(result, expected)
        mock_execute.assert_called_once_with(
            instance.cli_ctx,
            'aks nodepool show --resource-group rg --cluster-name cluster --name pool',
            expect_failure=False,
        )

    @patch('azure.cli.testsdk.base.execute')
    def test_keeps_original_result_for_non_aks_resource(self, mock_execute):
        original = MagicMock()

        result = self._make_instance()._refetch_settled_aks_result(
            '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet',
            original,
        )

        self.assertIs(result, original)
        mock_execute.assert_not_called()

    @patch('azure.cli.testsdk.base.execute')
    def test_keeps_original_result_for_other_aks_child_resource(self, mock_execute):
        original = MagicMock()
        resource_id = (
            '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ContainerService/'
            'managedClusters/cluster/trustedAccessRoleBindings/binding'
        )

        result = self._make_instance()._refetch_settled_aks_result(resource_id, original)

        self.assertIs(result, original)
        mock_execute.assert_not_called()


if __name__ == '__main__':
    unittest.main()
