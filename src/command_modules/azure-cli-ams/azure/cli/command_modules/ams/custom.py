# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# Licensed under the MIT License.  See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------------------------

import importlib
import pytz
import datetime
import time
from dateutil.relativedelta import relativedelta
import uuid

def list_mediaservices(client, resource_group_name=None):
    return client.list(resource_group_name) if resource_group_name else client.list_by_subscription()

def create_mediaservice(client, resource_group_name, account_name, storage_account, location=None, tags=None):

    storage_account_id = _build_storage_account_id(client.config.subscription_id, resource_group_name, storage_account)

    from azure.mediav3.models import StorageAccount
    storage_account_primary = StorageAccount('Primary', storage_account_id)

    return create_or_update_mediaservice(client, resource_group_name, account_name, [storage_account_primary], location, tags)


def add_mediaservice_secondary_storage(client, resource_group_name, account_name, storage_account):

    storage_account_id = _build_storage_account_id(client.config.subscription_id, resource_group_name, storage_account)

    ams = client.get(resource_group_name, account_name)

    storage_accounts_filtered = list(filter(lambda s: storage_account in s.id, ams.storage_accounts))

    from azure.mediav3.models import StorageAccount
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

    from azure.mediav3.models import MediaService
    media_service = MediaService(location=location, storage_accounts=storage_accounts, tags=tags)

    return client.create_or_update(resource_group_name, account_name, media_service)


def _build_storage_account_id(subscription_id, resource_group_name, storage_account):
    return "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Storage/storageAccounts/{2}".format(subscription_id, resource_group_name, storage_account)

def create_assign_sp_to_mediaservice(cmd, client, account_name, resource_group_name, sp_name=None, role='Contributor', sp_password=None, xml=False, years=None):

    ams = client.get(resource_group_name, account_name)

    from azure.cli.command_modules.role.custom import (create_service_principal_for_rbac, create_role_assignment, show_application, list_role_assignments)
    from azure.cli.command_modules.role._client_factory import _graph_client_factory
    graph_client = _graph_client_factory(cmd.cli_ctx)

    sp_name = '{}-access-sp'.format(account_name) if sp_name is None else sp_name
    sp_password = str(uuid.uuid4()) if sp_password is None else sp_password

    app_id = None
    tenant = None

    query_exp = 'servicePrincipalNames/any(x:x eq \'{}\')'.format("http://" + sp_name)
    aad_sps = list(graph_client.service_principals.list(filter=query_exp))

    if aad_sps:

        app_id = aad_sps[0].app_id

        tenant = aad_sps[0].additional_properties['appOwnerTenantId']

        app = show_application(graph_client.applications, aad_sps[0].app_id) # TODO: Refactor. Use passwordCredentials property

        app_creds = list(graph_client.applications.list_password_credentials(app.object_id))

        from azure.graphrbac.models import (PasswordCredential, ApplicationUpdateParameters)

        start_date = datetime.datetime.now(pytz.utc)
        end_date = start_date + relativedelta(years=years or 1)

        app_creds.append(PasswordCredential(start_date=start_date, end_date=end_date, key_id=str(uuid.uuid4()), value=sp_password))

        graph_client.applications.update_password_credentials(app.object_id, app_creds)

    else:
        create_sp_result = create_service_principal_for_rbac(cmd, name=sp_name, password=sp_password, skip_assignment = True)
        app_id = create_sp_result['appId']
        tenant = create_sp_result['tenant']

    # Workaround to allow 'create_service_principal_for_rbac' operation to
    # complete and continue with the 'create_role_assignment' operation
    # succesfully
    time.sleep(15)

    # TODO: Check role assignments and assign or not the new role

    assignments = list_role_assignments(cmd, assignee=app_id, show_all=True)

    if assignments:
        if len(list(filter(lambda x: x['properties']['roleDefinitionName'] == role, assignments))) == 0:
            create_rol_assignment_result = create_role_assignment(cmd, role, assignee=app_id, scope=ams.id)
    else:
        create_rol_assignment_result = create_role_assignment(cmd, role, assignee=app_id, scope=ams.id)
    
    result = {
        'SubscriptionId': client.config.subscription_id,
        'Region': ams.location,
        'ResourceGroup': resource_group_name,
        'AccountName': account_name,
        'AadTenantId': tenant,
        'AadClientId': app_id,
        'AadSecret': sp_password,
        'ArmAadAudience': cmd.cli_ctx.cloud.endpoints.management,
        'AadEndpoint': cmd.cli_ctx.cloud.endpoints.active_directory,
        'ArmEndpoint': cmd.cli_ctx.cloud.endpoints.resource_manager
    }

    return getattr(importlib.import_module('azure.cli.command_modules.ams._format'), 'get_sp_create_output_{}'.format('xml'))(result) if xml else result