# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure_devtools.scenario_tests import mock_in_unit_test
from azure_devtools.scenario_tests.const import MOCKED_SUBSCRIPTION_ID, MOCKED_TENANT_ID

from .exceptions import CliExecutionError

MOCKED_USER_NAME = 'example@example.com'


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
                # TODO: Azure Identity may remove homeAccountId in the future, since it is internal to MSAL and
                #   may not be absolutely necessary
                "homeAccountId": "00000003-0000-0000-0000-000000000000.00000003-0000-0000-0000-000000000000",
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
    def _mock_get_token(*args, **kwargs):  # pylint: disable=unused-argument
        from azure.core.credentials import AccessToken
        import time
        fake_raw_token = 'top-secret-token-for-you'
        now = int(time.time())
        # Mock sdk/identity/azure-identity/azure/identity/_internal/msal_credentials.py:230
        return AccessToken(fake_raw_token, now + 3600)

    mock_in_unit_test(unit_test,
                      'azure.identity.InteractiveBrowserCredential.get_token',
                      _mock_get_token)


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

    mock_in_unit_test(unit_test,
                      'azure.cli.core.local_context._get_current_system_username',
                      _get_current_system_username)
