# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import unittest
from unittest.mock import Mock, patch

from azure.cli.core.commands import LongRunningOperation
from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.patches import patch_long_run_operation_delay
from azure.cli.testsdk.scenario_tests.patches import patch_time_sleep_api
from azure.mgmt.core.polling.arm_polling import ARMPolling


class TestPlaybackPollingDelay(unittest.TestCase):
    def test_foreground_yields_and_service_delay_is_skipped_in_either_patch_order(self):
        original_foreground_delay = LongRunningOperation._delay
        original_service_delay = ARMPolling._delay
        original_sleep = time.sleep
        for hooks in (
                (patch_time_sleep_api, patch_long_run_operation_delay),
                (patch_long_run_operation_delay, patch_time_sleep_api)):
            with self.subTest(hooks=hooks):
                scenario = unittest.TestCase()
                try:
                    with patch('azure.cli.testsdk.patches.threading.Event') as event_factory:
                        for hook in hooks:
                            hook(scenario)
                    event_factory.assert_called_once_with()
                    event = event_factory.return_value
                    self.assertIsNone(ARMPolling._delay(None))
                    event.wait.assert_not_called()
                    self.assertIsNone(LongRunningOperation._delay(None))
                    event.wait.assert_called_once_with(0.001)
                    event.set.assert_not_called()
                    self.assertIsNone(time.sleep(60))
                finally:
                    scenario.doCleanups()
                self.assertIs(LongRunningOperation._delay, original_foreground_delay)
                self.assertIs(ARMPolling._delay, original_service_delay)
                self.assertIs(time.sleep, original_sleep)

    def test_delay_patch_is_registered_only_for_playback(self):
        scenario = ScenarioTest('runTest')
        self.addCleanup(scenario.doCleanups)
        self.assertIn(patch_long_run_operation_delay, scenario.replay_patches)
        self.assertNotIn(patch_long_run_operation_delay, scenario.recording_patches)

    def test_foreground_preserves_completion_and_errors(self):
        patch_time_sleep_api(self)
        patch_long_run_operation_delay(self)
        cli_ctx = Mock()
        cli_ctx.config.getboolean.return_value = True
        result = object()
        failure = RuntimeError('polling failed')
        for outcome in (result, failure):
            with self.subTest(outcome=outcome):
                poller = Mock()
                poller.done.side_effect = [False, True]
                if outcome is failure:
                    poller.result.side_effect = failure
                    with self.assertRaises(RuntimeError) as raised:
                        LongRunningOperation(cli_ctx)(poller)
                    self.assertIs(raised.exception, failure)
                else:
                    poller.result.return_value = result
                    self.assertIs(LongRunningOperation(cli_ctx)(poller), result)
                self.assertEqual(poller.done.call_count, 2)
                poller.result.assert_called_once_with()
