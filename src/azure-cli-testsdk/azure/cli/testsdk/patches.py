# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .exceptions import CliExecutionError, CliTestError
from .const import MOCKED_SUBSCRIPTION_ID, MOCKED_TENANT_ID


def patch_progress_controller(unit_test):
    def _handle_progress_update(*args):  # pylint: disable=unused-argument
        pass

    def _handle_progress_add(*args, **kwargs):  # pylint: disable=unused-argument
        pass

    def _mock_update_progress(*args, **kwargs):  # pylint: disable=unused-argument
        pass

    _mock_in_unit_test(
        unit_test, 'azure.cli.core.commands.progress.ProgressHook.update', _handle_progress_update)
    _mock_in_unit_test(
        unit_test, 'azure.cli.core.commands.progress.ProgressHook.add', _handle_progress_add)
    _mock_in_unit_test(
        unit_test, 'azure.cli.command_modules.storage.custom._update_progress', _mock_update_progress)


def patch_main_exception_handler(unit_test):
    from vcr.errors import CannotOverwriteExistingCassetteException

    def _handle_main_exception(ex):
        if isinstance(ex, CannotOverwriteExistingCassetteException):
            # This exception usually caused by a no match HTTP request. This is a product error
            # that is caused by change of SDK invocation.
            raise ex

        raise CliExecutionError(ex)

    _mock_in_unit_test(unit_test, 'azure.cli.main.handle_exception', _handle_main_exception)


def patch_load_cached_subscriptions(unit_test):
    def _handle_load_cached_subscription(*args, **kwargs):  # pylint: disable=unused-argument

        return [{
            "id": MOCKED_SUBSCRIPTION_ID,
            "user": {
                "name": "example@example.com",
                "type": "user"
            },
            "state": "Enabled",
            "name": "Example",
            "tenantId": MOCKED_TENANT_ID,
            "isDefault": True}]

    _mock_in_unit_test(unit_test,
                       'azure.cli.core._profile.Profile.load_cached_subscriptions',
                       _handle_load_cached_subscription)


def patch_retrieve_token_for_user(unit_test):
    def _retrieve_token_for_user(*args, **kwargs):  # pylint: disable=unused-argument
        return 'Bearer', 'top-secret-token-for-you', None

    _mock_in_unit_test(unit_test,
                       'azure.cli.core._profile.CredsCache.retrieve_token_for_user',
                       _retrieve_token_for_user)


def patch_long_run_operation_delay(unit_test):
    def _shortcut_long_run_operation(*args, **kwargs):  # pylint: disable=unused-argument
        return

    _mock_in_unit_test(unit_test,
                       'msrestazure.azure_operation.AzureOperationPoller._delay',
                       _shortcut_long_run_operation)
    _mock_in_unit_test(unit_test,
                       'azure.cli.core.commands.LongRunningOperation._delay',
                       _shortcut_long_run_operation)


def patch_time_sleep_api(unit_test):
    def _time_sleep_skip(*_):
        return

    _mock_in_unit_test(unit_test, 'time.sleep', _time_sleep_skip)


def _mock_in_unit_test(unit_test, target, replacement):
    import mock
    import unittest

    if not isinstance(unit_test, unittest.TestCase):
        raise CliTestError('The patch_main_exception_handler can be only used in unit test')

    mp = mock.patch(target, replacement)
    mp.__enter__()
    unit_test.addCleanup(mp.__exit__)
