# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument
from azure.mgmt.synapse.models import BlobAuditingPolicyState
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import ResourceType
from azure.cli.command_modules.monitor.operations.diagnostics_settings import create_diagnostics_settings
from azure.cli.command_modules.monitor._client_factory import cf_monitor
from knack.util import CLIError
from knack.log import get_logger


logger = get_logger(__name__)


def sqlpool_blob_auditing_policy_update(
        cmd,
        instance,
        workspace_name,
        resource_group_name,
        sql_pool_name,
        state=None,
        blob_storage_target_state=None,
        storage_account=None,
        storage_endpoint=None,
        storage_account_access_key=None,
        storage_account_subscription_id=None,
        is_storage_secondary_key_in_use=None,
        retention_days=None,
        audit_actions_and_groups=None,
        log_analytics_target_state=None,
        log_analytics_workspace_resource_id=None,
        event_hub_target_state=None,
        event_hub_authorization_rule_id=None,
        event_hub=None,
        is_azure_monitor_target_enabled=None):
    """
    Updates a sql pool blob auditing policy. Custom update function to apply parameters to instance.
    """
    _audit_policy_update(
        cmd=cmd,
        instance=instance,
        workspace_name=workspace_name,
        resource_group_name=resource_group_name,
        sql_pool_name=sql_pool_name,
        state=state,
        blob_storage_target_state=blob_storage_target_state,
        storage_account=storage_account,
        storage_endpoint=storage_endpoint,
        storage_account_access_key=storage_account_access_key,
        storage_account_subscription_id=storage_account_subscription_id,
        is_storage_secondary_key_in_use=is_storage_secondary_key_in_use,
        retention_days=retention_days,
        category_name='SQLSecurityAuditEvents',
        log_analytics_target_state=log_analytics_target_state,
        log_analytics_workspace_resource_id=log_analytics_workspace_resource_id,
        event_hub_target_state=event_hub_target_state,
        event_hub_authorization_rule_id=event_hub_authorization_rule_id,
        event_hub_name=event_hub,
        audit_actions_and_groups=audit_actions_and_groups,
        is_azure_monitor_target_enabled=is_azure_monitor_target_enabled)
    return instance


def sqlserver_blob_auditing_policy_update(
        cmd,
        instance,
        workspace_name,
        resource_group_name,
        blob_auditing_policy_name='default',
        state=None,
        blob_storage_target_state=None,
        storage_account=None,
        storage_endpoint=None,
        storage_account_access_key=None,
        retention_days=None,
        audit_actions_and_groups=None,
        log_analytics_target_state=None,
        log_analytics_workspace_resource_id=None,
        event_hub_target_state=None,
        event_hub_authorization_rule_id=None,
        event_hub=None,
        storage_account_subscription_id=None,
        is_storage_secondary_key_in_use=None,
        is_azure_monitor_target_enabled=None,
        queue_delay_milliseconds=None):
    _audit_policy_update(
        cmd=cmd,
        instance=instance,
        state=state,
        workspace_name=workspace_name,
        resource_group_name=resource_group_name,
        blob_storage_target_state=blob_storage_target_state,
        storage_account=storage_account,
        storage_endpoint=storage_endpoint,
        storage_account_access_key=storage_account_access_key,
        audit_actions_and_groups=audit_actions_and_groups,
        retention_days=retention_days,
        category_name='SQLSecurityAuditEvents',
        log_analytics_target_state=log_analytics_target_state,
        log_analytics_workspace_resource_id=log_analytics_workspace_resource_id,
        event_hub_target_state=event_hub_target_state,
        event_hub_authorization_rule_id=event_hub_authorization_rule_id,
        storage_account_subscription_id=storage_account_subscription_id,
        event_hub_name=event_hub,
        is_storage_secondary_key_in_use=is_storage_secondary_key_in_use,
        is_azure_monitor_target_enabled=is_azure_monitor_target_enabled)

    # this property is only for ServerBlobAuditingPolicy
    if queue_delay_milliseconds is not None:
        instance.queue_delay_ms = queue_delay_milliseconds

    return instance


def _audit_policy_update(
        cmd,
        instance,
        workspace_name,
        resource_group_name,
        sql_pool_name=None,
        state=None,
        blob_storage_target_state=None,
        storage_account=None,
        storage_endpoint=None,
        storage_account_access_key=None,
        storage_account_subscription_id=None,
        is_storage_secondary_key_in_use=None,
        retention_days=None,
        category_name=None,
        log_analytics_target_state=None,
        log_analytics_workspace_resource_id=None,
        event_hub_target_state=None,
        event_hub_authorization_rule_id=None,
        event_hub_name=None,
        audit_actions_and_groups=None,
        is_azure_monitor_target_enabled=None):

    # Arguments validation
    _audit_policy_validate_arguments(
        state=state,
        blob_storage_target_state=blob_storage_target_state,
        storage_account=storage_account,
        storage_endpoint=storage_endpoint,
        storage_account_access_key=storage_account_access_key,
        retention_days=retention_days,
        log_analytics_target_state=log_analytics_target_state,
        log_analytics_workspace_resource_id=log_analytics_workspace_resource_id,
        event_hub_target_state=event_hub_target_state,
        event_hub_authorization_rule_id=event_hub_authorization_rule_id,
        event_hub_name=event_hub_name)

    # Get diagnostic settings only if log_analytics_target_state or event_hub_target_state is provided
    if log_analytics_target_state is not None or event_hub_target_state is not None:
        diagnostic_settings = _get_diagnostic_settings(
            cmd=cmd,
            resource_group_name=resource_group_name,
            workspace_name=workspace_name,
            sql_pool_name=sql_pool_name)

        # Update diagnostic settings
        rollback_data = _audit_policy_update_diagnostic_settings(
            cmd=cmd,
            workspace_name=workspace_name,
            resource_group_name=resource_group_name,
            sql_pool_name=sql_pool_name,
            diagnostic_settings=diagnostic_settings,
            category_name=category_name,
            log_analytics_target_state=log_analytics_target_state,
            log_analytics_workspace_resource_id=log_analytics_workspace_resource_id,
            event_hub_target_state=event_hub_target_state,
            event_hub_authorization_rule_id=event_hub_authorization_rule_id,
            event_hub_name=event_hub_name)
    else:
        diagnostic_settings = None
        rollback_data = None

    try:
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
            _audit_policy_update_apply_blob_storage_details(
                cmd=cmd,
                instance=instance,
                blob_storage_target_state=blob_storage_target_state,
                storage_account=storage_account,
                storage_endpoint=storage_endpoint,
                storage_account_access_key=storage_account_access_key,
                retention_days=retention_days,
                storage_account_subscription_id=storage_account_subscription_id)

            if audit_actions_and_groups is not None:
                instance.audit_actions_and_groups = audit_actions_and_groups

            if not instance.audit_actions_and_groups or instance.audit_actions_and_groups == []:
                instance.audit_actions_and_groups = [
                    "SUCCESSFUL_DATABASE_AUTHENTICATION_GROUP",
                    "FAILED_DATABASE_AUTHENTICATION_GROUP",
                    "BATCH_COMPLETED_GROUP"]

            # Apply is_azure_monitor_target_enabled
            _audit_policy_update_apply_azure_monitor_target_enabled(
                instance=instance,
                diagnostic_settings=diagnostic_settings,
                category_name=category_name,
                log_analytics_target_state=log_analytics_target_state,
                event_hub_target_state=event_hub_target_state)
        return instance
    except Exception as err:
        logger.debug(err)

        if rollback_data is not None:
            _audit_policy_update_rollback(
                cmd=cmd,
                workspace_name=workspace_name,
                resource_group_name=resource_group_name,
                sql_pool_name=sql_pool_name,
                rollback_data=rollback_data)

        # Reraise the original exception
        raise err


def _audit_policy_update_apply_blob_storage_details(
        cmd,
        instance,
        blob_storage_target_state,
        retention_days,
        storage_account,
        storage_account_access_key,
        storage_endpoint,
        storage_account_subscription_id):
    '''
        Apply blob storage details on policy update
        '''
    if hasattr(instance, 'is_storage_secondary_key_in_use'):
        is_storage_secondary_key_in_use = instance.is_storage_secondary_key_in_use
    else:
        is_storage_secondary_key_in_use = False
    if blob_storage_target_state is None:
        # Original audit policy has no storage_endpoint
        if not instance.storage_endpoint:
            instance.storage_endpoint = None
            instance.storage_account_access_key = None
        else:
            # Resolve storage_account_access_key based on original storage_endpoint
            storage_account = _get_storage_account_name(instance.storage_endpoint)
            storage_resource_group = _find_storage_account_resource_group(cmd.cli_ctx, storage_account)

            instance.storage_account_access_key = _get_storage_key(
                cli_ctx=cmd.cli_ctx,
                storage_account=storage_account,
                resource_group_name=storage_resource_group,
                use_secondary_key=is_storage_secondary_key_in_use)
    elif _is_audit_policy_state_enabled(blob_storage_target_state):
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

    else:
        instance.storage_endpoint = None
        instance.storage_account_access_key = None


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
    from urllib.parse import urlparse

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


def _is_audit_policy_state_none_or_disabled(state):
    return state is None or _check_audit_policy_state(state, BlobAuditingPolicyState.disabled.value)


def _fetch_first_audit_diagnostic_setting(diagnostic_settings, category_name):
    return next((ds for ds in diagnostic_settings if hasattr(ds, 'logs') and
                 next((log for log in ds.logs if log.enabled and
                       log.category == category_name), None) is not None), None)


def _fetch_all_audit_diagnostic_settings(diagnostic_settings, category_name):
    return [ds for ds in diagnostic_settings if hasattr(ds, 'logs') and
            next((log for log in ds.logs if log.enabled and
                  log.category == category_name), None) is not None]


def _get_diagnostic_settings(
        cmd,
        resource_group_name,
        workspace_name,
        sql_pool_name=None):
    '''
    Common code to get workspace or sqlpool diagnostic settings
    '''

    diagnostic_settings_url = _get_diagnostic_settings_url(
        cmd=cmd, resource_group_name=resource_group_name,
        workspace_name=workspace_name, sql_pool_name=sql_pool_name)
    azure_monitor_client = cf_monitor(cmd.cli_ctx)
    return azure_monitor_client.diagnostic_settings.list(diagnostic_settings_url)


def _get_diagnostic_settings_url(
        cmd,
        resource_group_name,
        workspace_name,
        sql_pool_name=None):

    from azure.cli.core.commands.client_factory import get_subscription_id

    diagnostic_settings_url = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Synapse/workspaces/{}'.format(
        get_subscription_id(cmd.cli_ctx), resource_group_name, workspace_name)
    if sql_pool_name is not None:
        return diagnostic_settings_url + '/sqlpools/{}'.format(sql_pool_name)
    return diagnostic_settings_url


def _audit_policy_update_rollback(
        cmd,
        workspace_name,
        resource_group_name,
        sql_pool_name,
        rollback_data):
    '''
    Rollback diagnostic settings change
    '''

    diagnostic_settings_url = _get_diagnostic_settings_url(
        cmd=cmd,
        resource_group_name=resource_group_name,
        workspace_name=workspace_name,
        sql_pool_name=sql_pool_name)

    azure_monitor_client = cf_monitor(cmd.cli_ctx)

    for rd in rollback_data:
        rollback_diagnostic_setting = rd[1]

        if rd[0] == "create" or rd[0] == "update":
            create_diagnostics_settings(
                client=azure_monitor_client.diagnostic_settings,
                name=rollback_diagnostic_setting.name,
                resource_uri=diagnostic_settings_url,
                logs=rollback_diagnostic_setting.logs,
                metrics=rollback_diagnostic_setting.metrics,
                event_hub=rollback_diagnostic_setting.event_hub_name,
                event_hub_rule=rollback_diagnostic_setting.event_hub_authorization_rule_id,
                storage_account=rollback_diagnostic_setting.storage_account_id,
                workspace=rollback_diagnostic_setting.workspace_id)
        else:  # delete
            azure_monitor_client.diagnostic_settings.delete(diagnostic_settings_url, rollback_diagnostic_setting.name)


def _audit_policy_update_apply_azure_monitor_target_enabled(
        instance,
        diagnostic_settings,
        category_name,
        log_analytics_target_state,
        event_hub_target_state):
    '''
    Apply value of is_azure_monitor_target_enabled on policy update
    '''

    # If log_analytics_target_state and event_hub_target_state are None there is nothing to do
    if log_analytics_target_state is None and event_hub_target_state is None:
        return

    if _is_audit_policy_state_enabled(log_analytics_target_state) or\
            _is_audit_policy_state_enabled(event_hub_target_state):
        instance.is_azure_monitor_target_enabled = True
    else:
        # Sort received diagnostic settings by name and get first element to ensure consistency
        # between command executions
        diagnostic_settings.value.sort(key=lambda d: d.name)
        audit_diagnostic_setting = _fetch_first_audit_diagnostic_setting(diagnostic_settings.value, category_name)

        # Determine value of is_azure_monitor_target_enabled
        if audit_diagnostic_setting is None:
            updated_log_analytics_workspace_id = None
            updated_event_hub_authorization_rule_id = None
        else:
            updated_log_analytics_workspace_id = audit_diagnostic_setting.workspace_id
            updated_event_hub_authorization_rule_id = audit_diagnostic_setting.event_hub_authorization_rule_id

        if _is_audit_policy_state_disabled(log_analytics_target_state):
            updated_log_analytics_workspace_id = None

        if _is_audit_policy_state_disabled(event_hub_target_state):
            updated_event_hub_authorization_rule_id = None

        instance.is_azure_monitor_target_enabled = updated_log_analytics_workspace_id is not None or\
            updated_event_hub_authorization_rule_id is not None


def _is_audit_policy_state_disabled(state):
    return _check_audit_policy_state(state, BlobAuditingPolicyState.disabled.value)


def _audit_policy_update_diagnostic_settings(
        cmd,
        workspace_name,
        resource_group_name,
        sql_pool_name=None,
        diagnostic_settings=None,
        category_name=None,
        log_analytics_target_state=None,
        log_analytics_workspace_resource_id=None,
        event_hub_target_state=None,
        event_hub_authorization_rule_id=None,
        event_hub_name=None):
    '''
    Update audit policy's diagnostic settings
    '''

    # Fetch all audit diagnostic settings
    audit_diagnostic_settings = _fetch_all_audit_diagnostic_settings(diagnostic_settings.value, category_name)
    num_of_audit_diagnostic_settings = len(audit_diagnostic_settings)

    # If more than 1 audit diagnostic settings found then throw error
    if num_of_audit_diagnostic_settings > 1:
        raise CLIError('Multiple audit diagnostics settings are already enabled')

    diagnostic_settings_url = _get_diagnostic_settings_url(
        cmd=cmd,
        resource_group_name=resource_group_name,
        workspace_name=workspace_name,
        sql_pool_name=sql_pool_name)

    azure_monitor_client = cf_monitor(cmd.cli_ctx)

    # If no audit diagnostic settings found then create one if azure monitor is enabled
    if num_of_audit_diagnostic_settings == 0:
        if _is_audit_policy_state_enabled(log_analytics_target_state) or\
                _is_audit_policy_state_enabled(event_hub_target_state):
            created_diagnostic_setting = _audit_policy_create_diagnostic_setting(
                cmd=cmd,
                resource_group_name=resource_group_name,
                workspace_name=workspace_name,
                sql_pool_name=sql_pool_name,
                category_name=category_name,
                log_analytics_target_state=log_analytics_target_state,
                log_analytics_workspace_resource_id=log_analytics_workspace_resource_id,
                event_hub_target_state=event_hub_target_state,
                event_hub_authorization_rule_id=event_hub_authorization_rule_id,
                event_hub_name=event_hub_name)

            # Return rollback data tuple
            return [("delete", created_diagnostic_setting)]

        # azure monitor is disabled - there is nothing to do
        return None

    # This leaves us with case when num_of_audit_diagnostic_settings is 1
    audit_diagnostic_setting = audit_diagnostic_settings[0]

    # Initialize actually updated azure monitor fields
    if log_analytics_target_state is None:
        log_analytics_workspace_resource_id = audit_diagnostic_setting.workspace_id
    elif _is_audit_policy_state_disabled(log_analytics_target_state):
        log_analytics_workspace_resource_id = None

    if event_hub_target_state is None:
        event_hub_authorization_rule_id = audit_diagnostic_setting.event_hub_authorization_rule_id
        event_hub_name = audit_diagnostic_setting.event_hub_name
    elif _is_audit_policy_state_disabled(event_hub_target_state):
        event_hub_authorization_rule_id = None
        event_hub_name = None

    is_azure_monitor_target_enabled = log_analytics_workspace_resource_id is not None or\
        event_hub_authorization_rule_id is not None

    has_other_categories = next((log for log in audit_diagnostic_setting.logs
                                 if log.enabled and log.category != category_name), None) is not None

    # If there is no other categories except SQLSecurityAuditEvents\DevOpsOperationsAudit update or delete
    # the existing single diagnostic settings
    if not has_other_categories:
        # If azure monitor is enabled then update existing single audit diagnostic setting
        if is_azure_monitor_target_enabled:
            create_diagnostics_settings(
                client=azure_monitor_client.diagnostic_settings,
                name=audit_diagnostic_setting.name,
                resource_uri=diagnostic_settings_url,
                logs=audit_diagnostic_setting.logs,
                metrics=audit_diagnostic_setting.metrics,
                event_hub=event_hub_name,
                event_hub_rule=event_hub_authorization_rule_id,
                storage_account=audit_diagnostic_setting.storage_account_id,
                workspace=log_analytics_workspace_resource_id)

            # Return rollback data tuple
            return [("update", audit_diagnostic_setting)]

        # Azure monitor is disabled, delete existing single audit diagnostic setting
        azure_monitor_client.diagnostic_settings.delete(diagnostic_settings_url, audit_diagnostic_setting.name)

        # Return rollback data tuple
        return [("create", audit_diagnostic_setting)]

    # In case there are other categories in the existing single audit diagnostic setting a "split" must be performed:
    #   1. Disable SQLSecurityAuditEvents\DevOpsOperationsAudit category in found audit diagnostic setting
    #   2. Create new diagnostic setting with SQLSecurityAuditEvents\DevOpsOperationsAudit category,
    #      i.e. audit diagnostic setting

    # Build updated logs list with disabled SQLSecurityAuditEvents\DevOpsOperationsAudit category
    updated_logs = []

    LogSettings = cmd.get_models(
        'LogSettings',
        resource_type=ResourceType.MGMT_MONITOR,
        operation_group='diagnostic_settings')

    RetentionPolicy = cmd.get_models(
        'RetentionPolicy',
        resource_type=ResourceType.MGMT_MONITOR,
        operation_group='diagnostic_settings')

    for log in audit_diagnostic_setting.logs:
        if log.category == category_name:
            updated_logs.append(LogSettings(category=log.category, enabled=False,
                                            retention_policy=RetentionPolicy(enabled=False, days=0)))
        else:
            updated_logs.append(log)

    # Update existing diagnostic settings
    create_diagnostics_settings(
        client=azure_monitor_client.diagnostic_settings,
        name=audit_diagnostic_setting.name,
        resource_uri=diagnostic_settings_url,
        logs=updated_logs,
        metrics=audit_diagnostic_setting.metrics,
        event_hub=audit_diagnostic_setting.event_hub_name,
        event_hub_rule=audit_diagnostic_setting.event_hub_authorization_rule_id,
        storage_account=audit_diagnostic_setting.storage_account_id,
        workspace=audit_diagnostic_setting.workspace_id)

    # Add original 'audit_diagnostic_settings' to rollback_data list
    rollback_data = [("update", audit_diagnostic_setting)]

    # Create new diagnostic settings with enabled SQLSecurityAuditEvents\DevOpsOperationsAudit category
    # only if azure monitor is enabled
    if is_azure_monitor_target_enabled:
        created_diagnostic_setting = _audit_policy_create_diagnostic_setting(
            cmd=cmd,
            resource_group_name=resource_group_name,
            workspace_name=workspace_name,
            sql_pool_name=sql_pool_name,
            category_name=category_name,
            log_analytics_target_state=log_analytics_target_state,
            log_analytics_workspace_resource_id=log_analytics_workspace_resource_id,
            event_hub_target_state=event_hub_target_state,
            event_hub_authorization_rule_id=event_hub_authorization_rule_id,
            event_hub_name=event_hub_name)

        # Add 'created_diagnostic_settings' to rollback_data list in reverse order
        rollback_data.insert(0, ("delete", created_diagnostic_setting))

    return rollback_data


def _audit_policy_create_diagnostic_setting(
        cmd,
        resource_group_name,
        workspace_name,
        sql_pool_name=None,
        category_name=None,
        log_analytics_target_state=None,
        log_analytics_workspace_resource_id=None,
        event_hub_target_state=None,
        event_hub_authorization_rule_id=None,
        event_hub_name=None):
    '''
    Create audit diagnostic setting, i.e. containing single category - SQLSecurityAuditEvents or DevOpsOperationsAudit
    '''

    # Generate diagnostic settings name to be created
    name = category_name

    import inspect
    test_methods = ["test_sql_ws_audit_policy_logentry_eventhub", "test_sql_pool_audit_policy_logentry_eventhub"]
    test_mode = next((e for e in inspect.stack() if e.function in test_methods), None) is not None

    # For test environment the name should be constant, i.e. match the name written in recorded yaml file
    if test_mode:
        name += '_LogAnalytics' if log_analytics_target_state is not None else ''
        name += '_EventHub' if event_hub_target_state is not None else ''
    else:
        import uuid
        name += '_' + str(uuid.uuid4())

    diagnostic_settings_url = _get_diagnostic_settings_url(
        cmd=cmd,
        resource_group_name=resource_group_name,
        workspace_name=workspace_name,
        sql_pool_name=sql_pool_name)

    azure_monitor_client = cf_monitor(cmd.cli_ctx)

    LogSettings = cmd.get_models(
        'LogSettings',
        resource_type=ResourceType.MGMT_MONITOR,
        operation_group='diagnostic_settings')

    RetentionPolicy = cmd.get_models(
        'RetentionPolicy',
        resource_type=ResourceType.MGMT_MONITOR,
        operation_group='diagnostic_settings')

    return create_diagnostics_settings(
        client=azure_monitor_client.diagnostic_settings,
        name=name,
        resource_uri=diagnostic_settings_url,
        logs=[LogSettings(category=category_name, enabled=True,
                          retention_policy=RetentionPolicy(enabled=False, days=0))],
        metrics=None,
        event_hub=event_hub_name,
        event_hub_rule=event_hub_authorization_rule_id,
        storage_account=None,
        workspace=log_analytics_workspace_resource_id)


def _audit_policy_validate_arguments(
        state=None,
        blob_storage_target_state=None,
        storage_account=None,
        storage_endpoint=None,
        storage_account_access_key=None,
        retention_days=None,
        log_analytics_target_state=None,
        log_analytics_workspace_resource_id=None,
        event_hub_target_state=None,
        event_hub_authorization_rule_id=None,
        event_hub_name=None):
    '''
    Validate input agruments
    '''

    blob_storage_arguments_provided = blob_storage_target_state is not None or\
        storage_account is not None or storage_endpoint is not None or\
        storage_account_access_key is not None or\
        retention_days is not None

    log_analytics_arguments_provided = log_analytics_target_state is not None or\
        log_analytics_workspace_resource_id is not None

    event_hub_arguments_provided = event_hub_target_state is not None or\
        event_hub_authorization_rule_id is not None or\
        event_hub_name is not None

    if not state and not blob_storage_arguments_provided and\
            not log_analytics_arguments_provided and not event_hub_arguments_provided:
        raise CLIError('Either state or blob storage or log analytics or event hub arguments are missing')

    if _is_audit_policy_state_enabled(state) and\
            blob_storage_target_state is None and log_analytics_target_state is None and event_hub_target_state is None:
        raise CLIError('One of the following arguments must be enabled:'
                       ' blob-storage-target-state, log-analytics-target-state, event-hub-target-state')

    if _is_audit_policy_state_disabled(state) and\
            (blob_storage_arguments_provided or
             log_analytics_arguments_provided or
             event_hub_name):
        raise CLIError('No additional arguments should be provided once state is disabled')

    if (_is_audit_policy_state_none_or_disabled(blob_storage_target_state)) and\
            (storage_account is not None or storage_endpoint is not None or
             storage_account_access_key is not None):
        raise CLIError('Blob storage account arguments cannot be specified'
                       ' if blob-storage-target-state is not provided or disabled')

    if _is_audit_policy_state_enabled(blob_storage_target_state):
        if storage_account is not None and storage_endpoint is not None:
            raise CLIError('storage-account and storage-endpoint cannot be provided at the same time')

        if storage_account is None and storage_endpoint is None:
            raise CLIError('Either storage-account or storage-endpoint must be provided')

    # Server upper limit
    max_retention_days = 3285

    if retention_days is not None and\
            (int(retention_days) <= 0 or int(retention_days) >= max_retention_days):
        raise CLIError('retention-days must be a positive number greater than zero and lower than {}'
                       .format(max_retention_days))

    if _is_audit_policy_state_none_or_disabled(log_analytics_target_state) and\
            log_analytics_workspace_resource_id is not None:
        raise CLIError('Log analytics workspace resource id cannot be specified'
                       ' if log-analytics-target-state is not provided or disabled')

    if _is_audit_policy_state_enabled(log_analytics_target_state) and\
            log_analytics_workspace_resource_id is None:
        raise CLIError('Log analytics workspace resource id must be specified'
                       ' if log-analytics-target-state is enabled')

    if _is_audit_policy_state_none_or_disabled(event_hub_target_state) and\
            (event_hub_authorization_rule_id is not None or event_hub_name is not None):
        raise CLIError('Event hub arguments cannot be specified if event-hub-target-state is not provided or disabled')

    if _is_audit_policy_state_enabled(event_hub_target_state) and event_hub_authorization_rule_id is None:
        raise CLIError('event-hub-authorization-rule-id must be specified if event-hub-target-state is enabled')


def _get_diagnostic_settings_url(
        cmd,
        resource_group_name,
        workspace_name,
        sql_pool_name=None):

    from azure.cli.core.commands.client_factory import get_subscription_id

    diag_settings = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Synapse/workspaces/{}'.format(
        get_subscription_id(cmd.cli_ctx),
        resource_group_name, workspace_name)

    if sql_pool_name is not None:
        diag_settings = diag_settings + '/sqlpools/{}'.format(sql_pool_name)

    return diag_settings


def _get_diagnostic_settings(
        cmd,
        resource_group_name,
        workspace_name,
        sql_pool_name=None):
    '''
    Common code to get server or database diagnostic settings
    '''

    diagnostic_settings_url = _get_diagnostic_settings_url(
        cmd=cmd, resource_group_name=resource_group_name,
        workspace_name=workspace_name, sql_pool_name=sql_pool_name)
    azure_monitor_client = cf_monitor(cmd.cli_ctx)

    return azure_monitor_client.diagnostic_settings.list(diagnostic_settings_url)


def workspace_audit_policy_show(
        cmd,
        client,
        workspace_name,
        resource_group_name):
    '''
    Show workspace audit policy
    '''

    return _audit_policy_show(
        cmd=cmd,
        client=client,
        resource_group_name=resource_group_name,
        workspace_name=workspace_name,
        category_name='SQLSecurityAuditEvents')


def sqlpool_audit_policy_show(
        cmd,
        client,
        workspace_name,
        resource_group_name,
        sql_pool_name):
    '''
    Show sql pool audit policy
    '''

    return _audit_policy_show(
        cmd=cmd,
        client=client,
        resource_group_name=resource_group_name,
        workspace_name=workspace_name,
        sql_pool_name=sql_pool_name,
        category_name='SQLSecurityAuditEvents')


def _audit_policy_show(
        cmd,
        client,
        resource_group_name,
        workspace_name,
        sql_pool_name=None,
        category_name=None):
    '''
    Common code to get workspace or sqlpool audit policy including diagnostic settings
    '''

    # Request audit policy
    if sql_pool_name is None:
        audit_policy = client.get(
            resource_group_name=resource_group_name,
            workspace_name=workspace_name,
            blob_auditing_policy_name='default')
    else:
        audit_policy = client.get(
            resource_group_name=resource_group_name,
            workspace_name=workspace_name,
            sql_pool_name=sql_pool_name)

    audit_policy.blob_storage_target_state = BlobAuditingPolicyState.disabled
    audit_policy.event_hub_target_state = BlobAuditingPolicyState.disabled
    audit_policy.log_analytics_target_state = BlobAuditingPolicyState.disabled

    # If audit policy's state is disabled there is nothing to do
    if _is_audit_policy_state_disabled(audit_policy.state):
        return audit_policy

    if not audit_policy.storage_endpoint:
        audit_policy.blob_storage_target_state = BlobAuditingPolicyState.disabled
    else:
        audit_policy.blob_storage_target_state = BlobAuditingPolicyState.enabled

    # If 'is_azure_monitor_target_enabled' is false there is no reason to request diagnostic settings
    if not audit_policy.is_azure_monitor_target_enabled:
        return audit_policy

    # Request diagnostic settings
    diagnostic_settings = _get_diagnostic_settings(
        cmd=cmd, resource_group_name=resource_group_name,
        workspace_name=workspace_name, sql_pool_name=sql_pool_name)

    # Sort received diagnostic settings by name and get first element to ensure consistency between command executions
    diagnostic_settings.value.sort(key=lambda d: d.name)
    audit_diagnostic_setting = _fetch_first_audit_diagnostic_setting(diagnostic_settings.value, category_name)

    # Initialize azure monitor properties
    if audit_diagnostic_setting is not None:
        if audit_diagnostic_setting.workspace_id is not None:
            audit_policy.log_analytics_target_state = BlobAuditingPolicyState.enabled
            audit_policy.log_analytics_workspace_resource_id = audit_diagnostic_setting.workspace_id

        if audit_diagnostic_setting.event_hub_authorization_rule_id is not None:
            audit_policy.event_hub_target_state = BlobAuditingPolicyState.enabled
            audit_policy.event_hub_authorization_rule_id = audit_diagnostic_setting.event_hub_authorization_rule_id
            audit_policy.event_hub_name = audit_diagnostic_setting.event_hub_name

    return audit_policy
