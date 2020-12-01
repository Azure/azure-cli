# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument
from azure.mgmt.synapse.models import SecurityAlertPolicyState
from knack.util import CLIError
from .sqlpoolblobauditingpolicy import _find_storage_account_resource_group, _get_storage_endpoint, \
    _get_storage_account_name, _get_storage_key


def sqlpool_security_alert_policy_update(
        cmd,
        instance,
        state=None,
        storage_account=None,
        storage_endpoint=None,
        storage_account_access_key=None,
        retention_days=None,
        email_addresses=None,
        disabled_alerts=None,
        email_account_admins=None):
    '''
    Updates a SQL pool's security alert policy. Custom update function to apply parameters to instance.
    '''

    # Apply state
    if state:
        instance.state = SecurityAlertPolicyState[state.lower()]
    enabled = instance.state.value.lower() == SecurityAlertPolicyState.enabled.value.lower()  # pylint: disable=no-member

    # Set storage-related properties
    _sqlpool_security_policy_update(
        cmd.cli_ctx,
        instance,
        enabled,
        storage_account,
        storage_endpoint,
        storage_account_access_key,
        False)

    # Set other properties
    if retention_days:
        instance.retention_days = retention_days

    if email_addresses:
        instance.email_addresses = ";".join(email_addresses)

    if disabled_alerts:
        instance.disabled_alerts = ";".join(disabled_alerts)

    if email_account_admins:
        instance.email_account_admins = email_account_admins

    return instance


def _sqlpool_security_policy_update(
        cli_ctx,
        instance,
        enabled,
        storage_account,
        storage_endpoint,
        storage_account_access_key,
        use_secondary_key):
    """
    Common code for updating audit and threat detection policy.
    """

    # Validate storage endpoint arguments
    if storage_endpoint and storage_account:
        raise CLIError('--storage-endpoint and --storage-account cannot both be specified.')

    # Set storage endpoint
    if storage_endpoint:
        instance.storage_endpoint = storage_endpoint
    if storage_account:
        storage_resource_group = _find_storage_account_resource_group(cli_ctx, storage_account)
        instance.storage_endpoint = _get_storage_endpoint(cli_ctx, storage_account, storage_resource_group)

    # Set storage access key
    if storage_account_access_key:
        # Access key is specified
        instance.storage_account_access_key = storage_account_access_key
    elif enabled:
        # Access key is not specified, but state is Enabled.
        # If state is Enabled, then access key property is required in PUT. However access key is
        # readonly (GET returns empty string for access key), so we need to determine the value
        # and then PUT it back. (We don't want the user to be force to specify this, because that
        # would be very annoying when updating non-storage-related properties).
        # This doesn't work if the user used generic update args, i.e. `--set state=Enabled`
        # instead of `--state Enabled`, since the generic update args are applied after this custom
        # function, but at least we tried.
        if not storage_account:
            storage_account = _get_storage_account_name(instance.storage_endpoint)
            storage_resource_group = _find_storage_account_resource_group(cli_ctx, storage_account)

        instance.storage_account_access_key = _get_storage_key(
            cli_ctx,
            storage_account,
            storage_resource_group,
            use_secondary_key)
