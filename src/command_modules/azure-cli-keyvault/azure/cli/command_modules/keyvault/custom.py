#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.mgmt.keyvault.models import (VaultCreateOrUpdateParameters,
                                        VaultProperties,
                                        AccessPolicyEntry,
                                        Permissions,
                                        Sku,
                                        SkuFamily,
                                        SkuName)
from azure.graphrbac import GraphRbacManagementClient

from azure.cli._util import CLIError
import azure.cli._logging as _logging

logger = _logging.get_az_logger(__name__)

def list_keyvault(client, resource_group_name=None):
    ''' List Vaults. '''
    vault_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list(vault_list)

def _get_current_user_object_id(graph_client):
    current_user = graph_client.objects.get_current_user()
    if current_user and current_user.object_id: #pylint:disable=no-member
        return current_user.object_id #pylint:disable=no-member

def _get_object_id_by_spn(graph_client, spn):
    accounts = list(graph_client.service_principals.list(
        filter="servicePrincipalNames/any(c:c eq '{}')".format(spn)))
    if not accounts:
        logger.warning("Unable to find user with spn '%s'", spn)
        return
    if len(accounts) > 1:
        logger.warning("Multiple service principals found with spn '%s'. "\
                    "You can avoid this by specifying object id.", spn)
        return
    return accounts[0].object_id

def _get_object_id_by_upn(graph_client, upn):
    accounts = list(graph_client.users.list(filter="userPrincipalName eq '{}'".format(upn)))
    if not accounts:
        logger.warning("Unable to find user with upn '%s'", upn)
        return
    if len(accounts) > 1:
        logger.warning("Multiple users principals found with upn '%s'. "\
                    "You can avoid this by specifying object id.", upn)
        return
    return accounts[0].object_id

def _get_object_id_from_subscription(graph_client, subscription):
    if subscription['user']:
        if subscription['user']['type'] == 'user':
            return _get_object_id_by_upn(graph_client, subscription['user']['name'])
        elif subscription['user']['type'] == 'servicePrincipal':
            return _get_object_id_by_spn(graph_client, subscription['user']['name'])
        else:
            logger.warning("Unknown user type '%s'", subscription['user']['type'])
    else:
        logger.warning('Current credentials are not from a user or service principal. '\
                    'Azure Key Vault does not work with certificate credentials.')

def _get_object_id(graph_client, subscription=None, spn=None, upn=None):
    if spn:
        return _get_object_id_by_spn(graph_client, spn)
    if upn:
        return _get_object_id_by_upn(graph_client, upn)
    return _get_object_id_from_subscription(graph_client, subscription)

def create_keyvault(client, resource_group_name, vault_name, location, #pylint:disable=too-many-arguments
                    sku_name=SkuName.standard.value,
                    sku_family=SkuFamily.a.value,
                    vault_uri=None,
                    enabled_for_deployment=None,
                    enabled_for_disk_encryption=None,
                    enabled_for_template_deployment=None,
                    no_self_perms=False,
                    tags=None):
    from azure.cli._profile import Profile
    profile = Profile()
    cred, _, tenant_id = profile.get_login_credentials(for_graph_client=True)
    graph_client = GraphRbacManagementClient(cred, tenant_id)
    subscription = profile.get_default_subscription()
    if no_self_perms:
        access_policies = []
    else:
        # TODO Use the enums instead of strings when new keyvault SDK is released
        # https://github.com/Azure/azure-sdk-for-python/blob/dev/azure-mgmt-keyvault/
        # azure/mgmt/keyvault/models/key_vault_management_client_enums.py
        permissions = Permissions(keys=['get',
                                        'create',
                                        'delete',
                                        'list',
                                        'update',
                                        'import',
                                        'backup',
                                        'restore'],
                                  secrets=['all'])
        object_id = _get_current_user_object_id(graph_client)
        if not object_id:
            object_id = _get_object_id(graph_client, subscription=subscription)
        if not object_id:
            raise CLIError('Cannot create vault.\n'
                           'Unable to query active directory for information '\
                           'about the current user.\n'
                           'You may try the --no-self-perms flag to create a vault'\
                           ' without permissions.')
        access_policies = [AccessPolicyEntry(tenant_id=tenant_id,
                                             object_id=object_id,
                                             permissions=permissions)]
    properties = VaultProperties(tenant_id=tenant_id,
                                 sku=Sku(name=sku_name, family=sku_family),
                                 access_policies=access_policies,
                                 vault_uri=vault_uri,
                                 enabled_for_deployment=enabled_for_deployment,
                                 enabled_for_disk_encryption=enabled_for_disk_encryption,
                                 enabled_for_template_deployment=enabled_for_template_deployment)
    parameters = VaultCreateOrUpdateParameters(location=location,
                                               tags=tags,
                                               properties=properties)
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=parameters)

def _object_id_args_helper(object_id, spn, upn):
    if not object_id:
        from azure.cli._profile import Profile
        profile = Profile()
        cred, _, tenant_id = profile.get_login_credentials(for_graph_client=True)
        graph_client = GraphRbacManagementClient(cred, tenant_id)
        object_id = _get_object_id(graph_client, spn=spn, upn=upn)
        if not object_id:
            raise CLIError('Unable to get object id from principal name.')
    return object_id

def set_policy(client, resource_group_name, vault_name, #pylint:disable=too-many-arguments
               object_id=None, spn=None, upn=None, perms_to_keys=None, perms_to_secrets=None):
    object_id = _object_id_args_helper(object_id, spn, upn)
    vault = client.get(resource_group_name=resource_group_name,
                       vault_name=vault_name)
    # Find the existing policy to set
    policy = next((p for p in vault.properties.access_policies \
             if object_id.lower() == p.object_id.lower() and \
             vault.properties.tenant_id.lower() == p.tenant_id.lower()), None)
    if not policy:
        # Add new policy as none found
        vault.properties.access_policies.append(AccessPolicyEntry(
            tenant_id=vault.properties.tenant_id,
            object_id=object_id,
            permissions=Permissions(keys=perms_to_keys,
                                    secrets=perms_to_secrets)))
    else:
        # Modify existing policy.
        # If perms_to_keys is not set, use prev. value (similarly with perms_to_secrets).
        keys = policy.permissions.keys if perms_to_keys is None else perms_to_keys
        secrets = policy.permissions.secrets if perms_to_secrets is None else perms_to_secrets
        policy.permissions = Permissions(keys=keys, secrets=secrets)
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=VaultCreateOrUpdateParameters(
                                       location=vault.location,
                                       tags=vault.tags,
                                       properties=vault.properties))

def delete_policy(client, resource_group_name, vault_name, object_id=None, spn=None, upn=None): #pylint:disable=too-many-arguments
    object_id = _object_id_args_helper(object_id, spn, upn)
    vault = client.get(resource_group_name=resource_group_name,
                       vault_name=vault_name)
    prev_policies_len = len(vault.properties.access_policies)
    vault.properties.access_policies = [p for p in vault.properties.access_policies if \
                                        vault.properties.tenant_id.lower() != p.tenant_id.lower() \
                                        or object_id.lower() != p.object_id.lower()]
    if len(vault.properties.access_policies) == prev_policies_len:
        raise CLIError('No matching policies found')
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=VaultCreateOrUpdateParameters(
                                       location=vault.location,
                                       tags=vault.tags,
                                       properties=vault.properties))
