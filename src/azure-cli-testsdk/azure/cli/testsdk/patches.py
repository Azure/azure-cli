# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure_devtools.scenario_tests.const import MOCKED_SUBSCRIPTION_ID, MOCKED_TENANT_ID
from azure_devtools.scenario_tests.exceptions import AzureTestError

from .exceptions import CliExecutionError

MOCKED_USER_NAME = 'example@example.com'


def patch_time_sleep_api(unit_test):
    def _time_sleep_skip(*_):
        return

    mock_in_unit_test(unit_test, 'time.sleep', _time_sleep_skip)


def patch_progress_controller(unit_test):
    def _mock_pass(*args, **kwargs):  # pylint: disable=unused-argument
        pass

    mock_in_unit_test(
        unit_test, 'azure.cli.core.commands.progress.ProgressHook.update', _mock_pass)
    mock_in_unit_test(
        unit_test, 'azure.cli.core.commands.progress.ProgressHook.add', _mock_pass)
    mock_in_unit_test(
        unit_test, 'azure.cli.core.commands.progress.ProgressHook.end', _mock_pass)


def patch_main_exception_handler(unit_test):
    from vcr.errors import CannotOverwriteExistingCassetteException

    def _handle_main_exception(ex, *args, **kwargs):  # pylint: disable=unused-argument
        if isinstance(ex, CannotOverwriteExistingCassetteException):
            # This exception usually caused by a no match HTTP request. This is a product error
            # that is caused by change of SDK invocation.
            raise ex

        raise CliExecutionError(ex)

    mock_in_unit_test(unit_test, 'azure.cli.core.util.handle_exception', _handle_main_exception)


def patch_load_cached_subscriptions(unit_test):
    def _handle_load_cached_subscription(*args, **kwargs):  # pylint: disable=unused-argument

        return [{
            "id": MOCKED_SUBSCRIPTION_ID,
            "user": {
                "name": MOCKED_USER_NAME,
                "type": "user"
            },
            "state": "Enabled",
            "name": "Example",
            "tenantId": MOCKED_TENANT_ID,
            "isDefault": True}]

    mock_in_unit_test(unit_test,
                      'azure.cli.core._profile.Profile.load_cached_subscriptions',
                      _handle_load_cached_subscription)


def patch_retrieve_token_for_user(unit_test):
    def _retrieve_token_for_user(*args, **kwargs):  # pylint: disable=unused-argument
        import datetime
        fake_token = 'top-secret-token-for-you'
        return 'Bearer', fake_token, {
            "tokenType": "Bearer",
            "expiresIn": 3600,
            "expiresOn": (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S.%f"),
            "resource": args[3],
            "accessToken": fake_token,
            "refreshToken": fake_token
        }

    mock_in_unit_test(unit_test,
                      'azure.cli.core._profile.CredsCache.retrieve_token_for_user',
                      _retrieve_token_for_user)


def patch_long_run_operation_delay(unit_test):
    def _shortcut_long_run_operation(*args, **kwargs):  # pylint: disable=unused-argument
        return

    mock_in_unit_test(unit_test,
                      'msrestazure.azure_operation.AzureOperationPoller._delay',
                      _shortcut_long_run_operation)
    mock_in_unit_test(unit_test,
                      'msrestazure.polling.arm_polling.ARMPolling._delay',
                      _shortcut_long_run_operation)
    mock_in_unit_test(unit_test,
                      'azure.cli.core.commands.LongRunningOperation._delay',
                      _shortcut_long_run_operation)


def patch_get_current_system_username(unit_test):
    def _get_current_system_username(*args, **kwargs):  # pylint: disable=unused-argument
        from .utilities import create_random_name
        return create_random_name(prefix='example_')

    mock_in_unit_test(unit_test, 'azure.cli.core.local_context._get_current_system_username', _get_current_system_username)


def mock_in_unit_test(unit_test, target, replacement):
    try:
        import unittest.mock as mock
    except ImportError:
        import mock
    import unittest

    if not isinstance(unit_test, unittest.TestCase):
        raise AzureTestError('Patches can be only called from a unit test')

    mp = mock.patch(target, replacement)
    mp.__enter__()
    unit_test.addCleanup(mp.__exit__, None, None, None)
