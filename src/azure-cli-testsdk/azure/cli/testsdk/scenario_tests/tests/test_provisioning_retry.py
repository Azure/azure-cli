# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import json
import unittest
from unittest import mock

from azure.cli.testsdk.checkers import JMESPathCheck
from azure.cli.testsdk.exceptions import JMESPathCheckAssertionError


class MockExecutionResult:
    """Minimal mock of ExecutionResult for testing retry logic."""

    def __init__(self, json_data, exit_code=0):
        self.output = json.dumps(json_data)
        self.exit_code = exit_code
        self.json_value = None
        self.skip_assert = False
        self.applog = ''

    def get_output_in_json(self):
        if not self.json_value:
            self.json_value = json.loads(self.output)
        return self.json_value

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


class MockCheckerMixin:
    """Instantiable wrapper around CheckerMixin for testing."""

    def __init__(self):
        from azure.cli.testsdk.base import CheckerMixin
        # Borrow methods from CheckerMixin
        self._should_retry = CheckerMixin._should_retry_for_provisioning_state.__get__(self)
        self._retry = CheckerMixin._cmd_with_retry.__get__(self)
        self._is_provisioning_state_check = CheckerMixin._is_provisioning_state_check
        self.kwargs = {}


# ---------------------------------------------------------------------------
# Tests for _should_retry_for_provisioning_state
# ---------------------------------------------------------------------------

class TestShouldRetryForProvisioningState(unittest.TestCase):

    def _make_mixin(self):
        return MockCheckerMixin()

    def test_returns_false_when_env_var_not_set(self):
        """Default is 'false' — retry should not trigger."""
        mixin = self._make_mixin()
        checks = [JMESPathCheck('provisioningState', 'Succeeded')]
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(mixin._should_retry(checks))

    def test_returns_true_when_enabled_and_check_matches(self):
        mixin = self._make_mixin()
        checks = [JMESPathCheck('provisioningState', 'Succeeded')]
        with mock.patch.dict(os.environ, {'AZURE_CLI_TEST_RETRY_PROVISIONING_CHECK': 'true'}):
            self.assertTrue(mixin._should_retry(checks))

    def test_returns_false_when_checks_is_none(self):
        mixin = self._make_mixin()
        with mock.patch.dict(os.environ, {'AZURE_CLI_TEST_RETRY_PROVISIONING_CHECK': 'true'}):
            self.assertFalse(mixin._should_retry(None))

    def test_returns_false_when_checks_is_empty(self):
        mixin = self._make_mixin()
        with mock.patch.dict(os.environ, {'AZURE_CLI_TEST_RETRY_PROVISIONING_CHECK': 'true'}):
            self.assertFalse(mixin._should_retry([]))

    def test_returns_false_when_no_provisioning_state_check(self):
        mixin = self._make_mixin()
        checks = [JMESPathCheck('name', 'myCluster')]
        with mock.patch.dict(os.environ, {'AZURE_CLI_TEST_RETRY_PROVISIONING_CHECK': 'true'}):
            self.assertFalse(mixin._should_retry(checks))

    def test_returns_false_when_expected_value_is_not_succeeded(self):
        mixin = self._make_mixin()
        checks = [JMESPathCheck('provisioningState', 'Failed')]
        with mock.patch.dict(os.environ, {'AZURE_CLI_TEST_RETRY_PROVISIONING_CHECK': 'true'}):
            self.assertFalse(mixin._should_retry(checks))

    def test_case_insensitive_query(self):
        mixin = self._make_mixin()
        checks = [JMESPathCheck('ProvisioningState', 'Succeeded')]
        with mock.patch.dict(os.environ, {'AZURE_CLI_TEST_RETRY_PROVISIONING_CHECK': 'true'}):
            self.assertTrue(mixin._should_retry(checks))

    def test_single_check_not_in_list(self):
        """Checks can be passed as a single callable, not wrapped in a list."""
        mixin = self._make_mixin()
        check = JMESPathCheck('provisioningState', 'Succeeded')
        with mock.patch.dict(os.environ, {'AZURE_CLI_TEST_RETRY_PROVISIONING_CHECK': 'true'}):
            self.assertTrue(mixin._should_retry(check))

    def test_mixed_checks_with_one_matching(self):
        mixin = self._make_mixin()
        checks = [
            JMESPathCheck('name', 'myCluster'),
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('location', 'eastus'),
        ]
        with mock.patch.dict(os.environ, {'AZURE_CLI_TEST_RETRY_PROVISIONING_CHECK': 'true'}):
            self.assertTrue(mixin._should_retry(checks))



# ---------------------------------------------------------------------------
# Tests for _cmd_with_retry
# ---------------------------------------------------------------------------

class TestCmdWithRetry(unittest.TestCase):

    def _make_mixin(self):
        return MockCheckerMixin()

    def _env(self, **overrides):
        """Return env dict with retry enabled and fast delays for testing."""
        env = {
            'AZURE_CLI_TEST_RETRY_PROVISIONING_CHECK': 'true',
            'AZURE_CLI_TEST_MAX_RETRIES': '3',
            'AZURE_CLI_TEST_BASE_DELAY': '0',
            'AZURE_CLI_TEST_MAX_DELAY': '0',
        }
        env.update(overrides)
        return env

    @mock.patch('azure.cli.testsdk.base.execute')
    def test_happy_path_no_retry(self, mock_execute):
        """If the original command passes all checks, return immediately."""
        mixin = self._make_mixin()
        result = MockExecutionResult({
            'id': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/mc',
            'provisioningState': 'Succeeded',
            'etag': 'aaa',
        })
        mock_execute.return_value = result

        checks = [JMESPathCheck('provisioningState', 'Succeeded')]

        with mock.patch.dict(os.environ, self._env()):
            ret = mixin._retry('az aks show -g rg -n mc', checks, mock.MagicMock())

        self.assertEqual(ret, result)
        mock_execute.assert_called_once()  # No polling calls

    @mock.patch('azure.cli.testsdk.base.execute')
    def test_retry_then_succeed(self, mock_execute):
        """Original fails, poll returns Updating then Succeeded."""
        mixin = self._make_mixin()

        original = MockExecutionResult({
            'id': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/mc',
            'provisioningState': 'Updating',
            'etag': 'aaa',
        })
        poll_updating = MockExecutionResult({
            'properties': {'provisioningState': 'Updating'},
            'etag': 'bbb',
        })
        poll_succeeded = MockExecutionResult({
            'properties': {'provisioningState': 'Succeeded'},
            'etag': 'bbb',
        })

        mock_execute.side_effect = [original, poll_updating, poll_succeeded]
        checks = [JMESPathCheck('provisioningState', 'Succeeded')]

        with mock.patch.dict(os.environ, self._env()):
            ret = mixin._retry('az aks show -g rg -n mc', checks, mock.MagicMock())

        # Returns original result (not the poll result)
        self.assertEqual(ret, original)
        self.assertEqual(mock_execute.call_count, 3)  # 1 original + 2 polls

    @mock.patch('azure.cli.testsdk.base.execute')
    def test_etag_change_logged(self, mock_execute):
        """When etag changes, a warning is logged."""
        mixin = self._make_mixin()

        original = MockExecutionResult({
            'id': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/mc',
            'provisioningState': 'Updating',
            'etag': 'original-etag-value',
        })
        poll_succeeded = MockExecutionResult({
            'properties': {'provisioningState': 'Succeeded'},
            'etag': 'different-etag-value',
        })

        mock_execute.side_effect = [original, poll_succeeded]
        checks = [JMESPathCheck('provisioningState', 'Succeeded')]

        with mock.patch.dict(os.environ, self._env()):
            with mock.patch('azure.cli.testsdk.base.logger') as mock_logger:
                mixin._retry('az aks show -g rg -n mc', checks, mock.MagicMock())

        # Verify warning was logged about etag change
        etag_warnings = [c for c in mock_logger.warning.call_args_list
                         if 'ETag changed' in c[0][0]]
        self.assertEqual(len(etag_warnings), 1)
        self.assertIn('ETag changed', etag_warnings[0][0][0])

    @mock.patch('azure.cli.testsdk.base.execute')
    def test_terminal_failure_raises_immediately(self, mock_execute):
        """If poll returns Failed, raise immediately without further retries."""
        mixin = self._make_mixin()

        original = MockExecutionResult({
            'id': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/mc',
            'provisioningState': 'Updating',
            'etag': 'aaa',
        })
        poll_failed = MockExecutionResult({
            'properties': {'provisioningState': 'Failed'},
            'etag': 'bbb',
        })

        mock_execute.side_effect = [original, poll_failed]
        checks = [JMESPathCheck('provisioningState', 'Succeeded')]

        with mock.patch.dict(os.environ, self._env()):
            with self.assertRaises(AssertionError) as ctx:
                mixin._retry('az aks show -g rg -n mc', checks, mock.MagicMock())

        self.assertIn('Failed', str(ctx.exception))
        self.assertEqual(mock_execute.call_count, 2)  # 1 original + 1 poll, no more

    @mock.patch('azure.cli.testsdk.base.execute')
    def test_no_resource_id_raises_original_error(self, mock_execute):
        """If response has no 'id' field, raise the original assertion error."""
        mixin = self._make_mixin()

        original = MockExecutionResult({
            'provisioningState': 'Updating',
            'name': 'something',
        })
        mock_execute.return_value = original
        checks = [JMESPathCheck('provisioningState', 'Succeeded')]

        with mock.patch.dict(os.environ, self._env()):
            with self.assertRaises(JMESPathCheckAssertionError):
                mixin._retry('az aks show -g rg -n mc', checks, mock.MagicMock())

        mock_execute.assert_called_once()  # No polling — can't poll without resource id

    @mock.patch('azure.cli.testsdk.base.execute')
    def test_timeout_raises_after_max_retries(self, mock_execute):
        """If all polls return Updating, raise TimeoutError after max retries."""
        mixin = self._make_mixin()

        original = MockExecutionResult({
            'id': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/mc',
            'provisioningState': 'Updating',
            'etag': 'aaa',
        })
        poll_updating = MockExecutionResult({
            'properties': {'provisioningState': 'Updating'},
            'etag': 'bbb',
        })

        # 1 original + 3 polls (max_retries=3)
        mock_execute.side_effect = [original, poll_updating, poll_updating, poll_updating]
        checks = [JMESPathCheck('provisioningState', 'Succeeded')]

        with mock.patch.dict(os.environ, self._env()):
            with self.assertRaises(TimeoutError) as ctx:
                mixin._retry('az aks show -g rg -n mc', checks, mock.MagicMock())

        self.assertIn('did not reach', str(ctx.exception))
        self.assertEqual(mock_execute.call_count, 4)  # 1 original + 3 polls

    @mock.patch('azure.cli.testsdk.base.execute')
    def test_poll_command_uses_resource_id(self, mock_execute):
        """Verify the poll uses 'resource show --ids <id>', not the original command."""
        mixin = self._make_mixin()

        resource_id = '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/mc'
        original = MockExecutionResult({
            'id': resource_id,
            'provisioningState': 'Updating',
            'etag': 'aaa',
        })
        poll_succeeded = MockExecutionResult({
            'properties': {'provisioningState': 'Succeeded'},
            'etag': 'aaa',
        })

        mock_execute.side_effect = [original, poll_succeeded]
        checks = [JMESPathCheck('provisioningState', 'Succeeded')]

        with mock.patch.dict(os.environ, self._env()):
            mixin._retry('az aks update -g rg -n mc --enable-something', checks, mock.MagicMock())

        # Second call should be the poll command, not the original update
        poll_call = mock_execute.call_args_list[1]
        self.assertIn('resource show --ids', str(poll_call))

    # -----------------------------------------------------------------------
    # Two-phase check validation tests
    # -----------------------------------------------------------------------

    @mock.patch('azure.cli.testsdk.base.execute')
    def test_two_phase_race_with_other_checks_passing(self, mock_execute):
        """Scenario A: provisioningState=Updating (race), other checks pass after poll."""
        mixin = self._make_mixin()

        original = MockExecutionResult({
            'id': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/mc',
            'provisioningState': 'Updating',
            'etag': 'aaa',
            'networkProfile': {'outboundType': 'managedNATGateway'},
            'tags': {'key1': 'value1'},
        })
        poll_succeeded = MockExecutionResult({
            'properties': {'provisioningState': 'Succeeded'},
            'etag': 'bbb',
        })

        mock_execute.side_effect = [original, poll_succeeded]
        checks = [
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('networkProfile.outboundType', 'managedNATGateway'),
            JMESPathCheck('tags.key1', 'value1'),
        ]

        with mock.patch.dict(os.environ, self._env()):
            ret = mixin._retry('az aks create -g rg -n mc', checks, mock.MagicMock())

        self.assertEqual(ret, original)
        self.assertEqual(mock_execute.call_count, 2)  # 1 original + 1 poll

    @mock.patch('azure.cli.testsdk.base.execute')
    def test_two_phase_no_race_other_check_fails(self, mock_execute):
        """Scenario B: provisioningState=Succeeded, but another check fails — error propagates."""
        mixin = self._make_mixin()

        original = MockExecutionResult({
            'id': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/mc',
            'provisioningState': 'Succeeded',
            'etag': 'aaa',
            'networkProfile': {'outboundType': 'loadBalancer'},  # Wrong value!
        })
        mock_execute.return_value = original
        checks = [
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('networkProfile.outboundType', 'managedNATGateway'),  # Will fail
        ]

        with mock.patch.dict(os.environ, self._env()):
            with self.assertRaises(JMESPathCheckAssertionError) as ctx:
                mixin._retry('az aks create -g rg -n mc', checks, mock.MagicMock())

        # Error should be about outboundType, not provisioningState
        self.assertIn('outboundType', str(ctx.exception))
        mock_execute.assert_called_once()  # No polling — Phase 1 passed

    @mock.patch('azure.cli.testsdk.base.execute')
    def test_two_phase_race_and_other_check_fails(self, mock_execute):
        """Scenario C: provisioningState=Updating (race) AND another check is wrong — fails correctly."""
        mixin = self._make_mixin()

        original = MockExecutionResult({
            'id': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/mc',
            'provisioningState': 'Updating',
            'etag': 'aaa',
            'networkProfile': {'outboundType': 'loadBalancer'},  # Wrong value!
        })
        poll_succeeded = MockExecutionResult({
            'properties': {'provisioningState': 'Succeeded'},
            'etag': 'bbb',
        })

        mock_execute.side_effect = [original, poll_succeeded]
        checks = [
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('networkProfile.outboundType', 'managedNATGateway'),  # Will fail in Phase 2
        ]

        with mock.patch.dict(os.environ, self._env()):
            with self.assertRaises(JMESPathCheckAssertionError) as ctx:
                mixin._retry('az aks create -g rg -n mc', checks, mock.MagicMock())

        # Error should be about outboundType (Phase 2 failure after Phase 1 retry succeeded)
        self.assertIn('outboundType', str(ctx.exception))
        self.assertEqual(mock_execute.call_count, 2)  # 1 original + 1 poll


if __name__ == '__main__':
    unittest.main()
