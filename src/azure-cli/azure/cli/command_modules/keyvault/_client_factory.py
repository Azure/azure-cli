# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from knack.log import get_logger
from knack.util import CLIError

from azure.cli.core.azclierror import RequiredArgumentMissingError
from azure.cli.core.commands import CliCommandType
from azure.cli.core.commands.client_factory import prepare_client_kwargs_track2
from azure.cli.core.profiles import get_api_version, ResourceType
from azure.cli.core._profile import Profile

logger = get_logger(__name__)


class Clients(str, Enum):
    vaults = 'vaults'
    private_endpoint_connections = 'private_endpoint_connections'
    private_link_resources = 'private_link_resources'
    managed_hsms = 'managed_hsms'
    mhsm_private_endpoint_connections = 'mhsm_private_endpoint_connections'
    mhsm_private_link_resources = 'mhsm_private_link_resources'
    mhsm_regions = 'mhsm_regions'
    private_7_2 = 'private_7_2'


OPERATIONS_NAME = {
    Clients.vaults: 'VaultsOperations',
    Clients.private_endpoint_connections: 'PrivateEndpointConnectionsOperations',
    Clients.private_link_resources: 'PrivateLinkResourcesOperations',
    Clients.managed_hsms: 'ManagedHsmsOperations',
    Clients.mhsm_private_endpoint_connections: 'MHSMPrivateEndpointConnectionsOperations',
    Clients.mhsm_private_link_resources: 'MHSMPrivateLinkResourcesOperations',
    Clients.mhsm_regions: 'MHSMRegionsOperations'
}

KEYVAULT_TEMPLATE_STRINGS = {
    ResourceType.MGMT_KEYVAULT:
        'azure.mgmt.keyvault.{module_name}#{class_name}{obj_name}',
    ResourceType.DATA_KEYVAULT_ADMINISTRATION_BACKUP:
        'azure.keyvault.administration._backup_client#KeyVaultBackupClient{obj_name}',
    ResourceType.DATA_KEYVAULT_ADMINISTRATION_ACCESS_CONTROL:
        'azure.keyvault.administration._access_control_client#KeyVaultAccessControlClient{obj_name}',
    ResourceType.DATA_KEYVAULT_ADMINISTRATION_SETTING:
        'azure.keyvault.administration._settings_client#KeyVaultSettingsClient{obj_name}',
    ResourceType.DATA_KEYVAULT_CERTIFICATES:
        'azure.keyvault.certificates._client#CertificateClient{obj_name}',
    ResourceType.DATA_KEYVAULT_KEYS:
        'azure.keyvault.keys._client#KeyClient{obj_name}',
    ResourceType.DATA_KEYVAULT_SECRETS:
        'azure.keyvault.secrets._client#SecretClient{obj_name}',
    ResourceType.DATA_KEYVAULT_SECURITY_DOMAIN:
        'azure.keyvault.securitydomain._client#SecurityDomainClient{obj_name}',
}


def is_mgmt_plane(resource_type):
    return resource_type == ResourceType.MGMT_KEYVAULT


def get_operations_tmpl(resource_type, client_name):
    if resource_type in [ResourceType.DATA_KEYVAULT_ADMINISTRATION_BACKUP,
                         ResourceType.DATA_KEYVAULT_ADMINISTRATION_ACCESS_CONTROL,
                         ResourceType.DATA_KEYVAULT_CERTIFICATES,
                         ResourceType.DATA_KEYVAULT_KEYS,
                         ResourceType.DATA_KEYVAULT_SECRETS,
                         ResourceType.DATA_KEYVAULT_SECURITY_DOMAIN,
                         ResourceType.DATA_KEYVAULT_ADMINISTRATION_SETTING]:
        return KEYVAULT_TEMPLATE_STRINGS[resource_type].format(obj_name='.{}')

    class_name = OPERATIONS_NAME.get(client_name, '') if is_mgmt_plane(resource_type) else 'KeyVaultClient'
    return KEYVAULT_TEMPLATE_STRINGS[resource_type].format(
        module_name='operations',
        class_name=class_name,
        obj_name='.{}')


def get_docs_tmpl(resource_type, client_name, module_name='operations'):
    if resource_type in [ResourceType.DATA_KEYVAULT_ADMINISTRATION_BACKUP,
                         ResourceType.DATA_KEYVAULT_ADMINISTRATION_ACCESS_CONTROL,
                         ResourceType.DATA_KEYVAULT_CERTIFICATES,
                         ResourceType.DATA_KEYVAULT_KEYS,
                         ResourceType.DATA_KEYVAULT_SECRETS,
                         ResourceType.DATA_KEYVAULT_SECURITY_DOMAIN,
                         ResourceType.DATA_KEYVAULT_ADMINISTRATION_SETTING]:
        return KEYVAULT_TEMPLATE_STRINGS[resource_type].format(obj_name='.{}')

    if is_mgmt_plane(resource_type):
        class_name = OPERATIONS_NAME.get(client_name, '') + '.' if module_name == 'operations' else ''
    else:
        class_name = 'KeyVaultClient.'
    return KEYVAULT_TEMPLATE_STRINGS[resource_type].format(
        module_name=module_name,
        class_name=class_name,
        obj_name='{}')


# pylint: disable=too-many-return-statements
def get_client_factory(resource_type, client_name=''):
    if is_mgmt_plane(resource_type):
        return keyvault_mgmt_client_factory(resource_type, client_name)
    if resource_type == ResourceType.DATA_KEYVAULT_ADMINISTRATION_BACKUP:
        return data_plane_azure_keyvault_administration_backup_client
    if resource_type == ResourceType.DATA_KEYVAULT_ADMINISTRATION_ACCESS_CONTROL:
        return data_plane_azure_keyvault_administration_access_control_client
    if resource_type == ResourceType.DATA_KEYVAULT_ADMINISTRATION_SETTING:
        return data_plane_azure_keyvault_administration_setting_client
    if resource_type == ResourceType.DATA_KEYVAULT_CERTIFICATES:
        return data_plane_azure_keyvault_certificate_client
    if resource_type == ResourceType.DATA_KEYVAULT_KEYS:
        return data_plane_azure_keyvault_key_client
    if resource_type == ResourceType.DATA_KEYVAULT_SECRETS:
        return data_plane_azure_keyvault_secret_client
    if resource_type == ResourceType.DATA_KEYVAULT_SECURITY_DOMAIN:
        return data_plane_azure_keyvault_security_domain_client
    raise CLIError('Unsupported resource type: {}'.format(resource_type))


class ClientEntity:  # pylint: disable=too-few-public-methods
    def __init__(self, client_factory, command_type, operations_docs_tmpl, models_docs_tmpl):
        self.client_factory = client_factory
        self.command_type = command_type
        self.operations_docs_tmpl = operations_docs_tmpl
        self.models_docs_tmpl = models_docs_tmpl


def get_client(resource_type, client_name=''):
    client_factory = get_client_factory(resource_type, client_name)
    command_type = CliCommandType(
        operations_tmpl=get_operations_tmpl(resource_type, client_name),
        client_factory=client_factory,
        resource_type=resource_type
    )
    operations_docs_tmpl = get_docs_tmpl(resource_type, client_name, module_name='operations')
    models_docs_tmpl = get_docs_tmpl(resource_type, client_name, module_name='models')
    return ClientEntity(client_factory, command_type, operations_docs_tmpl, models_docs_tmpl)


def keyvault_mgmt_client_factory(resource_type, client_name):
    def _keyvault_mgmt_client_factory(cli_ctx, _):
        from azure.cli.core.commands.client_factory import get_mgmt_service_client
        return getattr(get_mgmt_service_client(cli_ctx, resource_type), client_name)

    return _keyvault_mgmt_client_factory


def data_plane_azure_keyvault_administration_backup_client(cli_ctx, command_args):
    from azure.keyvault.administration import KeyVaultBackupClient

    vault_url, credential, version = _prepare_data_plane_azure_keyvault_client(
        cli_ctx, command_args, ResourceType.DATA_KEYVAULT_ADMINISTRATION_BACKUP)
    client_kwargs = prepare_client_kwargs_track2(cli_ctx)
    client_kwargs.pop('http_logging_policy')
    return KeyVaultBackupClient(
        vault_url=vault_url, credential=credential, api_version=version,
        verify_challenge_resource=False, **client_kwargs)


def data_plane_azure_keyvault_administration_access_control_client(cli_ctx, command_args):
    from azure.keyvault.administration import KeyVaultAccessControlClient

    vault_url, credential, version = _prepare_data_plane_azure_keyvault_client(
        cli_ctx, command_args, ResourceType.DATA_KEYVAULT_ADMINISTRATION_ACCESS_CONTROL)
    client_kwargs = prepare_client_kwargs_track2(cli_ctx)
    client_kwargs.pop('http_logging_policy')
    return KeyVaultAccessControlClient(
        vault_url=vault_url, credential=credential, api_version=version,
        verify_challenge_resource=False, **client_kwargs)


def data_plane_azure_keyvault_administration_setting_client(cli_ctx, command_args):
    from azure.keyvault.administration import KeyVaultSettingsClient

    vault_url, credential, _ = _prepare_data_plane_azure_keyvault_client(
        cli_ctx, command_args, ResourceType.DATA_KEYVAULT_ADMINISTRATION_SETTING)
    command_args.pop('hsm_name', None)
    command_args.pop('vault_base_url', None)
    command_args.pop('identifier', None)
    client_kwargs = prepare_client_kwargs_track2(cli_ctx)
    client_kwargs.pop('http_logging_policy')
    return KeyVaultSettingsClient(
        vault_url=vault_url, credential=credential, api_version='7.4',
        verify_challenge_resource=False, **client_kwargs)


def data_plane_azure_keyvault_certificate_client(cli_ctx, command_args):
    from azure.keyvault.certificates import CertificateClient

    vault_url, credential, _ = _prepare_data_plane_azure_keyvault_client(
        cli_ctx, command_args, ResourceType.DATA_KEYVAULT_CERTIFICATES)
    command_args.pop('hsm_name', None)
    command_args.pop('vault_base_url', None)
    command_args.pop('identifier', None)
    client_kwargs = prepare_client_kwargs_track2(cli_ctx)
    client_kwargs.pop('http_logging_policy')
    return CertificateClient(
        vault_url=vault_url, credential=credential, api_version='7.4',
        verify_challenge_resource=False, **client_kwargs)


def data_plane_azure_keyvault_key_client(cli_ctx, command_args):
    from azure.keyvault.keys import KeyClient

    vault_url, credential, _ = _prepare_data_plane_azure_keyvault_client(
        cli_ctx, command_args, ResourceType.DATA_KEYVAULT_KEYS)
    command_args.pop('hsm_name', None)
    command_args.pop('vault_base_url', None)
    command_args.pop('identifier', None)
    client_kwargs = prepare_client_kwargs_track2(cli_ctx)
    client_kwargs.pop('http_logging_policy')
    return KeyClient(
        vault_url=vault_url, credential=credential, api_version='7.6-preview.2',
        verify_challenge_resource=False, **client_kwargs)


def data_plane_azure_keyvault_secret_client(cli_ctx, command_args):
    from azure.keyvault.secrets import SecretClient

    vault_url, credential, _ = _prepare_data_plane_azure_keyvault_client(
        cli_ctx, command_args, ResourceType.DATA_KEYVAULT_SECRETS)
    command_args.pop('hsm_name', None)
    command_args.pop('vault_base_url', None)
    command_args.pop('identifier', None)
    client_kwargs = prepare_client_kwargs_track2(cli_ctx)
    client_kwargs.pop('http_logging_policy')
    return SecretClient(
        vault_url=vault_url, credential=credential, api_version='7.4',
        verify_challenge_resource=False, **client_kwargs)


def data_plane_azure_keyvault_security_domain_client(cli_ctx, command_args):
    from azure.keyvault.securitydomain import SecurityDomainClient
    vault_url, credential, _ = _prepare_data_plane_azure_keyvault_client(
        cli_ctx, command_args, ResourceType.DATA_KEYVAULT_SECURITY_DOMAIN)
    command_args.pop('hsm_name', None)
    command_args.pop('vault_base_url', None)
    command_args.pop('identifier', None)
    client_kwargs = prepare_client_kwargs_track2(cli_ctx)
    client_kwargs.pop('http_logging_policy')
    return SecurityDomainClient(vault_url=vault_url, credential=credential,
                                verify_challenge_resource=False, **client_kwargs)


def _prepare_data_plane_azure_keyvault_client(cli_ctx, command_args, resource_type):
    version = str(get_api_version(cli_ctx, resource_type))
    profile = Profile(cli_ctx=cli_ctx)
    credential, _, _ = profile.get_login_credentials(subscription_id=cli_ctx.data.get('subscription_id'))
    vault_url = \
        command_args.get('hsm_name', None) or \
        command_args.get('vault_base_url', None) or \
        command_args.get('identifier', None)
    if not vault_url:
        raise RequiredArgumentMissingError('Please specify --hsm-name or --id')
    return vault_url, credential, version
