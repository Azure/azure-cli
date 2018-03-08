# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# Licensed under the MIT License.  See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------------------------

import importlib
import pytz
import datetime
import time

def list_mediaservices(client, resource_group_name=None):
    return client.list(resource_group_name) if resource_group_name else client.list_by_subscription()

def create_mediaservice(client, resource_group_name, account_name, storage_account, location=None, tags=None):

    storage_account_id = _build_storage_account_id(client.config.subscription_id, resource_group_name, storage_account)

    from azure.mgmt.media.models import StorageAccount
    storage_account_primary = StorageAccount('Primary', storage_account_id)

    return create_or_update_mediaservice(client, resource_group_name, account_name, [storage_account_primary], location, tags)


def add_mediaservice_secondary_storage(client, resource_group_name, account_name, storage_account):

    storage_account_id = _build_storage_account_id(client.config.subscription_id, resource_group_name, storage_account)

    ams = client.get(resource_group_name, account_name)

    storage_accounts_filtered = list(filter(lambda s: storage_account in s.id, ams.storage_accounts))

    from azure.mgmt.media.models import StorageAccount
    storage_account_secondary = StorageAccount('Secondary', storage_account_id)

    ams.storage_accounts.append(storage_account_secondary) if len(storage_accounts_filtered) == 0 else None

    return create_or_update_mediaservice(client, resource_group_name, account_name, ams.storage_accounts, ams.location, ams.tags)


def remove_mediaservice_secondary_storage(client, resource_group_name, account_name, storage_account):

    storage_account_id = _build_storage_account_id(client.config.subscription_id, resource_group_name, storage_account)

    ams = client.get(resource_group_name, account_name)

    storage_accounts_filtered = list(filter(lambda s: storage_account not in s.id and 'Secondary' in s.type.value, ams.storage_accounts))

    primary_storage_account = list(filter(lambda s: 'Primary' in s.type.value, ams.storage_accounts))[0]
    storage_accounts_filtered.append(primary_storage_account)

    return create_or_update_mediaservice(client, resource_group_name, account_name, storage_accounts_filtered, ams.location, ams.tags)


def create_or_update_mediaservice(client, resource_group_name, account_name, storage_accounts=None, location=None, tags=None):

    from azure.mgmt.media.models import MediaService
    media_service = MediaService(location=location, storage_accounts=storage_accounts, tags=tags)

    return client.create_or_update(resource_group_name, account_name, media_service)


def _build_storage_account_id(subscription_id, resource_group_name, storage_account):
    return "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Storage/storageAccounts/{2}".format(subscription_id, resource_group_name, storage_account)

def create_assign_sp_to_mediaservice(cmd, client, account_name, resource_group_name, sp_name=None, role='Contributor', sp_password=None, xml=False):

    ams = client.get(resource_group_name, account_name)

    from azure.cli.command_modules.role.custom import (create_service_principal_for_rbac, create_role_assignment, show_service_principal)
    from azure.cli.command_modules.role._client_factory import _graph_client_factory

    sp_name = '{}-access-sp'.format(account_name) if sp_name is None else sp_name

    query_exp = 'servicePrincipalNames/any(x:x eq \'{}\')'.format("http://" + sp_name)
    aad_sps = list(_graph_client_factory(cmd.cli_ctx).service_principals.list(filter=query_exp))

    if aad_sps:
        key_name = '{}-{}'.format(account_name, datetime.datetime.now(pytz.utc).strftime('%Y-%m-%d-%H-%M-%S'))
        #TODO: Generate password for the sp
    else:
        create_sp_result = create_service_principal_for_rbac(cmd, name=sp_name, password=sp_password, skip_assignment = True)

    # Workaround to allow 'create_service_principal_for_rbac' operation to
    # complete and continue with the 'create_role_assignment' operation
    # succesfully
    time.sleep(15)

    create_rol_assignment_result = create_role_assignment(cmd, role, assignee=create_sp_result['appId'], scope=ams.id)

    result = {
        'SubscriptionId': client.config.subscription_id,
        'Region': ams.location,
        'ResourceGroup': resource_group_name,
        'AccountName': account_name,
        'AadTenantId': create_sp_result['tenant'],
        'AadClientId': create_sp_result['appId'],
        'AadSecret': create_sp_result['password'],
        'ArmAadAudience': cmd.cli_ctx.cloud.endpoints.management,
        'AadEndpoint': cmd.cli_ctx.cloud.endpoints.active_directory,
        'ArmEndpoint': cmd.cli_ctx.cloud.endpoints.resource_manager
    }

    return getattr(importlib.import_module('azure.cli.command_modules.ams._format'), 'get_sp_create_output_{}'.format('xml'))(result) if xml else result