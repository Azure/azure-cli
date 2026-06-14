# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import unittest
from unittest.mock import MagicMock, patch

from azure.cli.testsdk.checkers import JMESPathCheck


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
        ]
        self._make_instance()._cmd_with_retry('aks show', [JMESPathCheck('provisioningState', 'Succeeded')], False)
        self.assertEqual(mock_execute.call_count, 3)

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


if __name__ == '__main__':
    unittest.main()
