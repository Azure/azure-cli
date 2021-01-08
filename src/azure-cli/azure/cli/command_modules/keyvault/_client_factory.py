# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from knack.util import CLIError

from azure.cli.core.azclierror import RequiredArgumentMissingError
from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import get_api_version, ResourceType
from azure.cli.core._profile import Profile


class Clients(str, Enum):
    vaults = 'vaults'
    private_endpoint_connections = 'private_endpoint_connections'
    private_link_resources = 'private_link_resources'
    managed_hsms = 'managed_hsms'


OPERATIONS_NAME = {
    Clients.vaults: 'VaultsOperations',
    Clients.private_endpoint_connections: 'PrivateEndpointConnectionsOperations',
    Clients.private_link_resources: 'PrivateLinkResourcesOperations',
    Clients.managed_hsms: 'ManagedHsmsOperations'
}

KEYVAULT_TEMPLATE_STRINGS = {
    ResourceType.MGMT_KEYVAULT:
        'azure.mgmt.keyvault{api_version}.{module_name}#{class_name}{obj_name}',
    ResourceType.DATA_KEYVAULT:
        'azure.keyvault{api_version}.key_vault_client#{class_name}{obj_name}',
    ResourceType.DATA_PRIVATE_KEYVAULT:
        'azure.cli.command_modules.keyvault.vendored_sdks.azure_keyvault_t1{api_version}.'
        'key_vault_client#{class_name}{obj_name}',
    ResourceType.DATA_KEYVAULT_ADMINISTRATION_BACKUP:
        'azure.keyvault.administration._backup_client#KeyVaultBackupClient{obj_name}',
    ResourceType.DATA_KEYVAULT_ADMINISTRATION_ACCESS_CONTROL:
        'azure.keyvault.administration._access_control_client#KeyVaultAccessControlClient{obj_name}',
}


def is_mgmt_plane(resource_type):
    return resource_type == ResourceType.MGMT_KEYVAULT


def get_operations_tmpl(resource_type, client_name):
    if resource_type in [ResourceType.DATA_KEYVAULT_ADMINISTRATION_BACKUP,
                         ResourceType.DATA_KEYVAULT_ADMINISTRATION_ACCESS_CONTROL]:
        return KEYVAULT_TEMPLATE_STRINGS[resource_type].format(obj_name='.{}')

    class_name = OPERATIONS_NAME.get(client_name, '') if is_mgmt_plane(resource_type) else 'KeyVaultClient'
    return KEYVAULT_TEMPLATE_STRINGS[resource_type].format(
        api_version='',
        module_name='operations',
        class_name=class_name,
        obj_name='.{}')


def get_docs_tmpl(cli_ctx, resource_type, client_name, module_name='operations'):
    if resource_type in [ResourceType.DATA_KEYVAULT_ADMINISTRATION_BACKUP,
                         ResourceType.DATA_KEYVAULT_ADMINISTRATION_ACCESS_CONTROL]:
        return KEYVAULT_TEMPLATE_STRINGS[resource_type].format(obj_name='.{}')

    api_version = '.v' + str(get_api_version(cli_ctx, resource_type)).replace('.', '_').replace('-', '_')
    if is_mgmt_plane(resource_type):
        class_name = OPERATIONS_NAME.get(client_name, '') + '.' if module_name == 'operations' else ''
    else:
        class_name = 'KeyVaultClient.'
    return KEYVAULT_TEMPLATE_STRINGS[resource_type].format(
        api_version=api_version,
        module_name=module_name,
        class_name=class_name,
        obj_name='{}')


def get_client_factory(resource_type, client_name=''):
    if is_mgmt_plane(resource_type):
        return keyvault_mgmt_client_factory(resource_type, client_name)
    if resource_type == ResourceType.DATA_KEYVAULT:
        return keyvault_data_plane_factory
    if resource_type == ResourceType.DATA_PRIVATE_KEYVAULT:
        return keyvault_private_data_plane_factory_v7_2_preview
    if resource_type == ResourceType.DATA_KEYVAULT_ADMINISTRATION_BACKUP:
        return data_plane_azure_keyvault_administration_backup_client
    if resource_type == ResourceType.DATA_KEYVAULT_ADMINISTRATION_ACCESS_CONTROL:
        return data_plane_azure_keyvault_administration_access_control_client
    raise CLIError('Unsupported resource type: {}'.format(resource_type))


class ClientEntity:  # pylint: disable=too-few-public-methods
    def __init__(self, client_factory, command_type, operations_docs_tmpl, models_docs_tmpl):
        self.client_factory = client_factory
        self.command_type = command_type
        self.operations_docs_tmpl = operations_docs_tmpl
        self.models_docs_tmpl = models_docs_tmpl


def get_client(cli_ctx, resource_type, client_name=''):
    client_factory = get_client_factory(resource_type, client_name)
    command_type = CliCommandType(
        operations_tmpl=get_operations_tmpl(resource_type, client_name),
        client_factory=client_factory,
        resource_type=resource_type
    )
    operations_docs_tmpl = get_docs_tmpl(cli_ctx, resource_type, client_name, module_name='operations')
    models_docs_tmpl = get_docs_tmpl(cli_ctx, resource_type, client_name, module_name='models')
    return ClientEntity(client_factory, command_type, operations_docs_tmpl, models_docs_tmpl)


def is_azure_stack_profile(cmd):
    return cmd.cli_ctx.cloud.profile in [
        '2020-09-01-hybrid',
        '2019-03-01-hybrid',
        '2018-03-01-hybrid',
        '2017-03-09-profile'
    ]


def keyvault_mgmt_client_factory(resource_type, client_name):
    def _keyvault_mgmt_client_factory(cli_ctx, _):
        from azure.cli.core.commands.client_factory import get_mgmt_service_client
        return getattr(get_mgmt_service_client(cli_ctx, resource_type), client_name)
    return _keyvault_mgmt_client_factory


def keyvault_data_plane_factory(cli_ctx, _):
    from azure.keyvault import KeyVaultAuthentication, KeyVaultClient
    from azure.cli.core.util import should_disable_connection_verify

    version = str(get_api_version(cli_ctx, ResourceType.DATA_KEYVAULT))

    def get_token(server, resource, scope):  # pylint: disable=unused-argument
        import adal
        try:
            return Profile(cli_ctx=cli_ctx).get_raw_token(resource)[0]
        except adal.AdalError as err:
            # pylint: disable=no-member
            if (hasattr(err, 'error_response') and
                    ('error_description' in err.error_response) and
                    ('AADSTS70008:' in err.error_response['error_description'])):
                raise CLIError(
                    "Credentials have expired due to inactivity. Please run 'az login'")
            raise CLIError(err)

    client = KeyVaultClient(KeyVaultAuthentication(get_token), api_version=version)

    # HACK, work around the fact that KeyVault library does't take confiuration object on constructor
    # which could be used to turn off the verifiaction. Remove this once we migrate to new data plane library
    # pylint: disable=protected-access
    if hasattr(client, '_client') and hasattr(client._client, 'config'):
        verify = not should_disable_connection_verify()
        client._client.config.connection.verify = verify
    else:
        from knack.log import get_logger
        logger = get_logger(__name__)
        logger.info('Could not find the configuration object to turn off the verification if needed')

    return client


def keyvault_private_data_plane_factory_v7_2_preview(cli_ctx, _):
    from azure.cli.command_modules.keyvault.vendored_sdks.azure_keyvault_t1 import (
        KeyVaultAuthentication, KeyVaultClient)
    from azure.cli.core.util import should_disable_connection_verify

    version = str(get_api_version(cli_ctx, ResourceType.DATA_PRIVATE_KEYVAULT))

    def get_token(server, resource, scope):  # pylint: disable=unused-argument
        import adal
        try:
            return Profile(cli_ctx=cli_ctx).get_raw_token(resource)[0]
        except adal.AdalError as err:
            # pylint: disable=no-member
            if (hasattr(err, 'error_response') and
                    ('error_description' in err.error_response) and
                    ('AADSTS70008:' in err.error_response['error_description'])):
                raise CLIError(
                    "Credentials have expired due to inactivity. Please run 'az login'")
            raise CLIError(err)

    client = KeyVaultClient(KeyVaultAuthentication(get_token), api_version=version)

    # HACK, work around the fact that KeyVault library does't take confiuration object on constructor
    # which could be used to turn off the verifiaction. Remove this once we migrate to new data plane library
    # pylint: disable=protected-access
    if hasattr(client, '_client') and hasattr(client._client, 'config'):
        verify = not should_disable_connection_verify()
        client._client.config.connection.verify = verify
    else:
        from knack.log import get_logger
        logger = get_logger(__name__)
        logger.info('Could not find the configuration object to turn off the verification if needed')

    return client


def data_plane_azure_keyvault_administration_backup_client(cli_ctx, command_args):
    from azure.keyvault.administration import KeyVaultBackupClient

    version = str(get_api_version(cli_ctx, ResourceType.DATA_KEYVAULT_ADMINISTRATION_BACKUP))
    profile = Profile(cli_ctx=cli_ctx)
    credential, _, _ = profile.get_login_credentials(resource='https://managedhsm.azure.net')
    vault_url = \
        command_args.get('hsm_name', None) or \
        command_args.get('vault_base_url', None) or \
        command_args.get('identifier', None)
    if not vault_url:
        raise RequiredArgumentMissingError('Please specify --hsm-name or --id')
    return KeyVaultBackupClient(
        vault_url=vault_url, credential=credential, api_version=version)


def data_plane_azure_keyvault_administration_access_control_client(cli_ctx, command_args):
    from azure.keyvault.administration import KeyVaultAccessControlClient

    version = str(get_api_version(cli_ctx, ResourceType.DATA_KEYVAULT_ADMINISTRATION_ACCESS_CONTROL))
    profile = Profile(cli_ctx=cli_ctx)
    credential, _, _ = profile.get_login_credentials(resource='https://managedhsm.azure.net')
    vault_url = \
        command_args.get('hsm_name', None) or \
        command_args.get('vault_base_url', None) or \
        command_args.get('identifier', None)
    if not vault_url:
        raise RequiredArgumentMissingError('Please specify --hsm-name or --id')
    return KeyVaultAccessControlClient(
        vault_url=vault_url, credential=credential, api_version=version)
