# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument
from azure.mgmt.synapse.models import BlobAuditingPolicyState
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import ResourceType
from knack.util import CLIError


def sqlpool_blob_auditing_policy_update(
        cmd,
        instance,
        state=None,
        storage_account=None,
        storage_endpoint=None,
        storage_account_access_key=None,
        storage_account_subscription_id=None,
        is_storage_secondary_key_in_use=None,
        retention_days=None,
        audit_actions_and_groups=None,
        is_azure_monitor_target_enabled=None):
    """
    Updates a sql pool blob auditing policy. Custom update function to apply parameters to instance.
    """

    _audit_policy_update(cmd, instance, state, storage_account, storage_endpoint, storage_account_access_key,
                         storage_account_subscription_id, is_storage_secondary_key_in_use, retention_days,
                         audit_actions_and_groups, is_azure_monitor_target_enabled)
    return instance


def sqlserver_blob_auditing_policy_update(
        cmd,
        instance,
        state=None,
        storage_account=None,
        storage_endpoint=None,
        storage_account_access_key=None,
        retention_days=None,
        audit_actions_and_groups=None,
        storage_account_subscription_id=None,
        is_storage_secondary_key_in_use=None,
        is_azure_monitor_target_enabled=None,
        queue_delay_milliseconds=None):
    _audit_policy_update(cmd, instance, state, storage_account, storage_endpoint, storage_account_access_key,
                         storage_account_subscription_id, is_storage_secondary_key_in_use, retention_days,
                         audit_actions_and_groups, is_azure_monitor_target_enabled)

    # this property is only for ServerBlobAuditingPolicy
    if queue_delay_milliseconds is not None:
        instance.queue_delay_ms = queue_delay_milliseconds

    return instance


def _audit_policy_update(
        cmd,
        instance,
        state=None,
        storage_account=None,
        storage_endpoint=None,
        storage_account_access_key=None,
        storage_account_subscription_id=None,
        is_storage_secondary_key_in_use=None,
        retention_days=None,
        audit_actions_and_groups=None,
        is_azure_monitor_target_enabled=None):

    # Apply State
    if state is not None:
        instance.state = BlobAuditingPolicyState[state.lower()]

    # Apply additional command line arguments only if policy's state is enabled
    if _is_audit_policy_state_enabled(instance.state):
        if is_storage_secondary_key_in_use is not None:
            instance.is_storage_secondary_key_in_use = is_storage_secondary_key_in_use
        if is_azure_monitor_target_enabled is not None:
            instance.is_azure_monitor_target_enabled = is_azure_monitor_target_enabled

        # handle storage related parameters
        _audit_policy_update_apply_blob_storage_details(cmd, instance, retention_days, storage_account,
                                                        storage_account_access_key, storage_endpoint,
                                                        storage_account_subscription_id)

        if audit_actions_and_groups is not None:
            instance.audit_actions_and_groups = audit_actions_and_groups

        if not instance.audit_actions_and_groups or instance.audit_actions_and_groups == []:
            instance.audit_actions_and_groups = [
                "SUCCESSFUL_DATABASE_AUTHENTICATION_GROUP",
                "FAILED_DATABASE_AUTHENTICATION_GROUP",
                "BATCH_COMPLETED_GROUP"]


def _audit_policy_update_apply_blob_storage_details(cmd, instance, retention_days, storage_account,
                                                    storage_account_access_key, storage_endpoint,
                                                    storage_account_subscription_id):
    if storage_account is not None:
        storage_resource_group = _find_storage_account_resource_group(cmd.cli_ctx, storage_account)
        storage_endpoint = _get_storage_endpoint(cmd.cli_ctx, storage_account, storage_resource_group)
        storage_account_subscription_id = _find_storage_account_subscription_id(cmd.cli_ctx, storage_account)

    if storage_endpoint is not None:
        instance.storage_endpoint = storage_endpoint

    if storage_account_subscription_id is not None:
        instance.storage_account_subscription_id = storage_account_subscription_id

    if storage_account_access_key is not None:
        instance.storage_account_access_key = storage_account_access_key
    elif storage_endpoint is not None:
        # Resolve storage_account if not provided
        if storage_account is None:
            storage_account = _get_storage_account_name(storage_endpoint)
            storage_resource_group = _find_storage_account_resource_group(cmd.cli_ctx, storage_account)

        # Resolve storage_account_access_key based on storage_account
        instance.storage_account_access_key = _get_storage_key(
            cli_ctx=cmd.cli_ctx,
            storage_account=storage_account,
            resource_group_name=storage_resource_group,
            use_secondary_key=instance.is_storage_secondary_key_in_use)

    if retention_days is not None:
        instance.retention_days = retention_days


def _find_storage_account_resource_id(cli_ctx, name):
    '''
    Finds a storage account's resource group by querying ARM resource cache.

    Why do we have to do this: so we know the resource group in order to later query the storage API
    to determine the account's keys and endpoint. Why isn't this just a command line parameter:
    because if it was a command line parameter then the customer would need to specify storage
    resource group just to update some unrelated property, which is annoying and makes no sense to
    the customer.
    '''

    storage_type = 'Microsoft.Storage/storageAccounts'
    classic_storage_type = 'Microsoft.ClassicStorage/storageAccounts'

    query = "name eq '{}' and (resourceType eq '{}' or resourceType eq '{}')".format(
        name, storage_type, classic_storage_type)

    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    resources = list(client.resources.list(filter=query))

    if not resources:
        raise CLIError("No storage account with name '{}' was found.".format(name))

    if len(resources) > 1:
        raise CLIError("Multiple storage accounts with name '{}' were found.".format(name))

    if resources[0].type == classic_storage_type:
        raise CLIError("The storage account with name '{}' is a classic storage account which is"
                       " not supported by this command. Use a non-classic storage account or"
                       " specify storage endpoint and key instead.".format(name))

    return resources[0].id


def _find_storage_account_resource_group(cli_ctx, name):
    """
    Finds a storage account's resource group by querying ARM resource cache.

    Why do we have to do this: so we know the resource group in order to later query the storage API
    to determine the account's keys and endpoint. Why isn't this just a command line parameter:
    because if it was a command line parameter then the customer would need to specify storage
    resource group just to update some unrelated property, which is annoying and makes no sense to
    the customer.
    """
    resource_id = _find_storage_account_resource_id(cli_ctx, name)
    # Split the uri and return just the resource group
    return resource_id.split('/')[4]


def _find_storage_account_subscription_id(cli_ctx, name):
    """
    Finds a storage account's resource group by querying ARM resource cache.

    Why do we have to do this: so we know the resource group in order to later query the storage API
    to determine the account's keys and endpoint. Why isn't this just a command line parameter:
    because if it was a command line parameter then the customer would need to specify storage
    resource group just to update some unrelated property, which is annoying and makes no sense to
    the customer.
    """
    resource_id = _find_storage_account_resource_id(cli_ctx, name)
    # Split the uri and return just the resource group
    return resource_id.split('/')[2]


def _get_storage_account_name(storage_endpoint):
    """
    Determines storage account name from endpoint url string.
    e.g. 'https://mystorage.blob.core.windows.net' -> 'mystorage'
    """
    # url parse package has different names in Python 2 and 3. 'six' package works cross-version.
    from six.moves.urllib.parse import urlparse  # pylint: disable=import-error

    return urlparse(storage_endpoint).netloc.split('.')[0]


def _get_storage_endpoint(
        cli_ctx,
        storage_account,
        resource_group_name):
    """
    Gets storage account endpoint by querying storage ARM API.
    """
    from azure.mgmt.storage import StorageManagementClient

    # Get storage account
    client = get_mgmt_service_client(cli_ctx, StorageManagementClient)
    account = client.storage_accounts.get_properties(
        resource_group_name=resource_group_name,
        account_name=storage_account)

    # Get endpoint
    # pylint: disable=no-member
    endpoints = account.primary_endpoints
    try:
        return endpoints.blob
    except AttributeError:
        raise CLIError("The storage account with name '{}' (id '{}') has no blob endpoint. Use a"
                       " different storage account.".format(account.name, account.id))


def _get_storage_key(
        cli_ctx,
        storage_account,
        resource_group_name,
        use_secondary_key):
    """
    Gets storage account key by querying storage ARM API.
    """
    from azure.mgmt.storage import StorageManagementClient

    # Get storage keys
    client = get_mgmt_service_client(cli_ctx, StorageManagementClient)
    keys = client.storage_accounts.list_keys(
        resource_group_name=resource_group_name,
        account_name=storage_account)

    # Choose storage key
    index = 1 if use_secondary_key else 0
    return keys.keys[index].value  # pylint: disable=no-member


def _check_audit_policy_state(
        state,
        value):
    return state is not None and state.lower() == value.lower()


def _is_audit_policy_state_enabled(state):
    return _check_audit_policy_state(state, BlobAuditingPolicyState.enabled.value)
