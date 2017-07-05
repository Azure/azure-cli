# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure_devtools.scenario_tests import mock_in_unit_test
from azure_devtools.scenario_tests.const import MOCKED_SUBSCRIPTION_ID, MOCKED_TENANT_ID

from .exceptions import CliExecutionError


def patch_progress_controller(unit_test):
    def _mock_pass(*args, **kwargs):  # pylint: disable=unused-argument
        pass

    mock_in_unit_test(
        unit_test, 'azure.cli.core.commands.progress.ProgressHook.update', _mock_pass)
    mock_in_unit_test(
        unit_test, 'azure.cli.core.commands.progress.ProgressHook.add', _mock_pass)
    mock_in_unit_test(
        unit_test, 'azure.cli.core.commands.progress.ProgressHook.end', _mock_pass)
    mock_in_unit_test(
        unit_test, 'azure.cli.command_modules.storage.custom._update_progress', _mock_pass)


def patch_main_exception_handler(unit_test):
    from vcr.errors import CannotOverwriteExistingCassetteException

    def _handle_main_exception(ex):
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
                "name": "example@example.com",
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
        return 'Bearer', 'top-secret-token-for-you', None

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
                      'azure.cli.core.commands.LongRunningOperation._delay',
                      _shortcut_long_run_operation)
