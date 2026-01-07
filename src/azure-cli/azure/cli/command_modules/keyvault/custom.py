# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
import base64
import codecs
import hashlib
import json
import math
import os
import re
import struct
import time
import uuid
from ipaddress import ip_network

from azure.cli.command_modules.keyvault._client_factory import get_client_factory, Clients
from azure.cli.command_modules.keyvault._validators import _construct_vnet, secret_text_encoding_values
from azure.cli.command_modules.keyvault.security_domain.jwe import JWE
from azure.cli.command_modules.keyvault.security_domain.security_domain import Datum, SecurityDomainRestoreData
from azure.cli.command_modules.keyvault.security_domain.shared_secret import SharedSecret
from azure.cli.command_modules.keyvault.security_domain.sp800_108 import KDF
from azure.cli.command_modules.keyvault.security_domain.utils import Utils
from azure.cli.core.azclierror import InvalidArgumentValueError, RequiredArgumentMissingError, \
    MutuallyExclusiveArgumentError
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import sdk_no_wait

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives.serialization import load_pem_private_key, Encoding, PublicFormat
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.x509 import load_pem_x509_certificate

from knack.log import get_logger
from knack.util import CLIError, todict


logger = get_logger(__name__)


def _default_certificate_profile(cmd):
    def get_model(x):
        return cmd.loader.get_sdk(x, resource_type=ResourceType.DATA_KEYVAULT_CERTIFICATES, mod='_generated_models')

    Action = get_model('Action')
    ActionType = get_model('ActionType')
    KeyUsageType = get_model('KeyUsageType')
    CertificateAttributes = get_model('CertificateAttributes')
    CertificatePolicy = get_model('CertificatePolicy')
    IssuerParameters = get_model('IssuerParameters')
    KeyProperties = get_model('KeyProperties')
    LifetimeAction = get_model('LifetimeAction')
    SecretProperties = get_model('SecretProperties')
    X509CertificateProperties = get_model('X509CertificateProperties')
    Trigger = get_model('Trigger')

    template = CertificatePolicy(
        key_properties=KeyProperties(
            exportable=True,
            key_type='RSA',
            key_size=2048,
            reuse_key=True
        ),
        secret_properties=SecretProperties(
            content_type='application/x-pkcs12'
        ),
        x509_certificate_properties=X509CertificateProperties(
            key_usage=[
                KeyUsageType.c_rl_sign,
                KeyUsageType.data_encipherment,
                KeyUsageType.digital_signature,
                KeyUsageType.key_encipherment,
                KeyUsageType.key_agreement,
                KeyUsageType.key_cert_sign
            ],
            subject='CN=CLIGetDefaultPolicy',
            validity_in_months=12
        ),
        lifetime_actions=[LifetimeAction(
            trigger=Trigger(
                days_before_expiry=90
            ),
            action=Action(
                action_type=ActionType.auto_renew
            )
        )],
        issuer_parameters=IssuerParameters(
            name='Self',
        ),
        attributes=CertificateAttributes(
            enabled=True
        )
    )
    del template.id
    del template.attributes
    del template.issuer_parameters.certificate_type
    del template.lifetime_actions[0].trigger.lifetime_percentage
    del template.x509_certificate_properties.subject_alternative_names
    del template.x509_certificate_properties.ekus
    return template


def _scaffold_certificate_profile(cmd):
    def get_model(x):
        return cmd.loader.get_sdk(x, resource_type=ResourceType.DATA_KEYVAULT_CERTIFICATES, mod='_generated_models')

    Action = get_model('Action')
    ActionType = get_model('ActionType')
    KeyUsageType = get_model('KeyUsageType')
    CertificateAttributes = get_model('CertificateAttributes')
    CertificatePolicy = get_model('CertificatePolicy')
    IssuerParameters = get_model('IssuerParameters')
    KeyProperties = get_model('KeyProperties')
    LifetimeAction = get_model('LifetimeAction')
    SecretProperties = get_model('SecretProperties')
    X509CertificateProperties = get_model('X509CertificateProperties')
    SubjectAlternativeNames = get_model('SubjectAlternativeNames')
    Trigger = get_model('Trigger')

    template = CertificatePolicy(
        key_properties=KeyProperties(
            exportable=True,
            key_type='(optional) RSA or RSA-HSM (default RSA)',
            key_size=2048,
            reuse_key=True
        ),
        secret_properties=SecretProperties(
            content_type='application/x-pkcs12 or application/x-pem-file'
        ),
        x509_certificate_properties=X509CertificateProperties(
            key_usage=[
                KeyUsageType.c_rl_sign,
                KeyUsageType.data_encipherment,
                KeyUsageType.digital_signature,
                KeyUsageType.key_encipherment,
                KeyUsageType.key_agreement,
                KeyUsageType.key_cert_sign
            ],
            subject_alternative_names=SubjectAlternativeNames(
                emails=['hello@contoso.com'],
                dns_names=['hr.contoso.com', 'm.contoso.com'],
                upns=[]
            ),
            subject='C=US, ST=WA, L=Redmond, O=Contoso, OU=Contoso HR, CN=www.contoso.com',
            ekus=['1.3.6.1.5.5.7.3.1'],
            validity_in_months=24
        ),
        lifetime_actions=[LifetimeAction(
            trigger=Trigger(
                days_before_expiry=90
            ),
            action=Action(
                action_type=ActionType.auto_renew
            )
        )],
        issuer_parameters=IssuerParameters(
            name='Unknown, Self, or {IssuerName}',
            certificate_type='(optional) DigiCert, GlobalSign or WoSign'
        ),
        attributes=CertificateAttributes(
            enabled=True
        )
    )
    del template.id
    del template.attributes
    return template


def delete_vault_or_hsm(cmd, client, resource_group_name=None, vault_name=None, hsm_name=None, no_wait=False):
    if vault_name:
        return client.delete(resource_group_name=resource_group_name, vault_name=vault_name)

    assert hsm_name
    hsm_client = get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)(cmd.cli_ctx, None)
    logger.warning('This command will soft delete the resource, and you will still be billed until it is purged. '
                   'For more information, go to https://aka.ms/doc/KeyVaultMHSMSoftDelete')
    return sdk_no_wait(
        no_wait, hsm_client.begin_delete,
        resource_group_name=resource_group_name,
        name=hsm_name
    )


def get_deleted_vault_or_hsm(cmd, client, location=None, vault_name=None, hsm_name=None):
    if vault_name:
        return client.get_deleted(vault_name=vault_name, location=location)

    hsm_client = get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)(cmd.cli_ctx, None)
    return hsm_client.get_deleted(name=hsm_name, location=location)


def purge_vault_or_hsm(cmd, client, location=None, vault_name=None, hsm_name=None,  # pylint: disable=unused-argument
                       no_wait=False):
    if vault_name:
        return sdk_no_wait(
            no_wait,
            client.begin_purge_deleted,
            location=location,
            vault_name=vault_name
        )

    hsm_client = get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)(cmd.cli_ctx, None)
    return sdk_no_wait(
        no_wait,
        hsm_client.begin_purge_deleted,
        location=location,
        name=hsm_name
    )


def list_deleted_vault_or_hsm(cmd, client, resource_type=None):
    if resource_type is None:
        hsm_client = get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)(cmd.cli_ctx, None)
        resources = []
        resources.extend(client.list_deleted())
        resources.extend(hsm_client.list_deleted())
        return resources

    if resource_type == 'hsm':
        hsm_client = get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)(cmd.cli_ctx, None)
        return hsm_client.list_deleted()

    if resource_type == 'vault':
        return client.list_deleted()

    raise CLIError('Unsupported resource type: {}'.format(resource_type))


def list_vault_or_hsm(cmd, client, resource_group_name=None, resource_type=None):
    if resource_type is None:
        hsm_client = get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)(cmd.cli_ctx, None)
        resources = []
        try:
            resources.extend(list_vault(client, resource_group_name))
            resources.extend(list_hsm(hsm_client, resource_group_name))
        except:  # pylint: disable=bare-except
            pass

        return resources

    if resource_type == 'hsm':
        hsm_client = get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)(cmd.cli_ctx, None)
        return list_hsm(hsm_client, resource_group_name)

    if resource_type == 'vault':
        return list_vault(client, resource_group_name)

    raise CLIError('Unsupported resource type: {}'.format(resource_type))


def list_hsm(client, resource_group_name=None):
    hsm_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list_by_subscription()
    return list(hsm_list)


def list_vault(client, resource_group_name=None):
    vault_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list(vault_list)


def _create_network_rule_set(cmd, bypass=None, default_action=None):
    NetworkRuleSet = cmd.get_models('NetworkRuleSet', resource_type=ResourceType.MGMT_KEYVAULT)
    NetworkRuleBypassOptions = cmd.get_models('NetworkRuleBypassOptions', resource_type=ResourceType.MGMT_KEYVAULT)
    NetworkRuleAction = cmd.get_models('NetworkRuleAction', resource_type=ResourceType.MGMT_KEYVAULT)

    # We actually should not set any default value from client side
    # Keep this 'if' section to avoid breaking change
    if not bypass and not default_action:
        return NetworkRuleSet(bypass=NetworkRuleBypassOptions.azure_services.value,
                              default_action=NetworkRuleAction.allow.value)
    return NetworkRuleSet(bypass=bypass, default_action=default_action)


# region KeyVault Vault
def get_default_policy(cmd, scaffold=False):  # pylint: disable=unused-argument
    """
    Get a default certificate policy to be used with `az keyvault certificate create`
    :param bool scaffold: create a fully formed policy structure with default values
    :return: policy dict
    :rtype: dict
    """
    return _scaffold_certificate_profile(cmd) if scaffold else _default_certificate_profile(cmd)


def recover_vault_or_hsm(cmd, client, resource_group_name=None, location=None, vault_name=None, hsm_name=None,
                         no_wait=False):
    if vault_name:
        return recover_vault(cmd=cmd,
                             client=client,
                             resource_group_name=resource_group_name,
                             location=location,
                             vault_name=vault_name,
                             no_wait=no_wait)

    if hsm_name:
        hsm_client = get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)(cmd.cli_ctx, None)
        return recover_hsm(cmd=cmd,
                           client=hsm_client,
                           resource_group_name=resource_group_name,
                           location=location,
                           hsm_name=hsm_name,
                           no_wait=no_wait)


def recover_hsm(cmd, client, hsm_name, resource_group_name, location, no_wait=False):
    from azure.cli.core._profile import Profile, _TENANT_ID

    ManagedHsm = cmd.get_models('ManagedHsm', resource_type=ResourceType.MGMT_KEYVAULT,
                                operation_group='managed_hsms')
    ManagedHsmSku = cmd.get_models('ManagedHsmSku', resource_type=ResourceType.MGMT_KEYVAULT,
                                   operation_group='managed_hsms')

    # tenantId and sku shouldn't be required
    profile = Profile(cli_ctx=cmd.cli_ctx)
    tenant_id = profile.get_subscription(subscription=cmd.cli_ctx.data.get('subscription_id', None))[_TENANT_ID]

    # Use 'Recover' as 'create_mode' temporarily since it's a bug from service side making 'create_mode' case-sensitive
    # Will change it back to CreateMode.recover.value('recover') from SDK definition after service fix
    parameters = ManagedHsm(location=location,
                            sku=ManagedHsmSku(name='Standard_B1', family='B'),
                            properties={'tenant_id': tenant_id, 'create_mode': 'Recover'})

    return sdk_no_wait(
        no_wait, client.begin_create_or_update,
        resource_group_name=resource_group_name,
        name=hsm_name,
        parameters=parameters
    )


def recover_vault(cmd, client, vault_name, resource_group_name, location, no_wait=False):
    from azure.cli.core._profile import Profile, _TENANT_ID

    VaultCreateOrUpdateParameters = cmd.get_models('VaultCreateOrUpdateParameters',
                                                   resource_type=ResourceType.MGMT_KEYVAULT)
    CreateMode = cmd.get_models('CreateMode', resource_type=ResourceType.MGMT_KEYVAULT)

    # tenantId and sku shouldn't be required
    Sku = cmd.get_models('Sku', resource_type=ResourceType.MGMT_KEYVAULT)
    SkuName = cmd.get_models('SkuName', resource_type=ResourceType.MGMT_KEYVAULT)
    profile = Profile(cli_ctx=cmd.cli_ctx)
    tenant_id = profile.get_subscription(subscription=cmd.cli_ctx.data.get('subscription_id', None))[_TENANT_ID]

    params = VaultCreateOrUpdateParameters(location=location,
                                           properties={'tenantId': tenant_id,
                                                       'sku': Sku(name=SkuName.standard.value, family='A'),
                                                       'createMode': CreateMode.recover.value})

    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name=resource_group_name,
                       vault_name=vault_name,
                       parameters=params)


def _parse_network_acls(cmd, resource_group_name, network_acls_json, network_acls_ips, network_acls_vnets,
                        bypass, default_action):
    if network_acls_json is None:
        network_acls_json = {}

    rule_names = ['ip', 'vnet']
    for rn in rule_names:
        if rn not in network_acls_json:
            network_acls_json[rn] = []

    if network_acls_ips:
        for ip_rule in network_acls_ips:
            if ip_rule not in network_acls_json['ip']:
                network_acls_json['ip'].append(ip_rule)

    if network_acls_vnets:
        for vnet_rule in network_acls_vnets:
            if vnet_rule not in network_acls_json['vnet']:
                network_acls_json['vnet'].append(vnet_rule)

    VirtualNetworkRule = cmd.get_models('VirtualNetworkRule', resource_type=ResourceType.MGMT_KEYVAULT)
    IPRule = cmd.get_models('IPRule', resource_type=ResourceType.MGMT_KEYVAULT)

    network_acls = _create_network_rule_set(cmd, bypass, default_action)

    from azure.mgmt.core.tools import is_valid_resource_id

    network_acls.virtual_network_rules = []
    for vnet_rule in network_acls_json.get('vnet', []):
        items = vnet_rule.split('/')
        if len(items) == 2:
            vnet_name = items[0].lower()
            subnet_name = items[1].lower()
            vnet = _construct_vnet(cmd, resource_group_name, vnet_name, subnet_name)
            network_acls.virtual_network_rules.append(VirtualNetworkRule(id=vnet))
        else:
            subnet_id = vnet_rule.lower()
            if is_valid_resource_id(subnet_id):
                network_acls.virtual_network_rules.append(VirtualNetworkRule(id=subnet_id))
            else:
                raise CLIError('Invalid VNet rule: {}. Format: {{vnet_name}}/{{subnet_name}} or {{subnet_id}}'.
                               format(vnet_rule))

    network_acls.ip_rules = []
    for ip_rule in network_acls_json.get('ip', []):
        network_acls.ip_rules.append(IPRule(value=ip_rule))

    return network_acls


def get_vault_or_hsm(cmd, client, resource_group_name, vault_name=None, hsm_name=None):
    if vault_name:
        return client.get(resource_group_name=resource_group_name, vault_name=vault_name)

    hsm_client = get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)(cmd.cli_ctx, None)
    return hsm_client.get(resource_group_name=resource_group_name, name=hsm_name)


# pylint: disable=too-many-locals
def create_vault_or_hsm(cmd, client,
                        resource_group_name, vault_name=None, hsm_name=None,
                        administrators=None,
                        location=None, sku=None,
                        enabled_for_deployment=None,
                        enabled_for_disk_encryption=None,
                        enabled_for_template_deployment=None,
                        enable_rbac_authorization=True,
                        enable_purge_protection=None,
                        retention_days=None,
                        network_acls=None,
                        network_acls_ips=None,
                        network_acls_vnets=None,
                        bypass=None,
                        default_action=None,
                        no_self_perms=None,
                        tags=None,
                        no_wait=False,
                        public_network_access=None,
                        user_identities=None,
                        ):
    if vault_name:
        return create_vault(cmd=cmd,
                            client=client,
                            resource_group_name=resource_group_name,
                            vault_name=vault_name,
                            location=location,
                            sku=sku,
                            enabled_for_deployment=enabled_for_deployment,
                            enabled_for_disk_encryption=enabled_for_disk_encryption,
                            enabled_for_template_deployment=enabled_for_template_deployment,
                            enable_rbac_authorization=enable_rbac_authorization,
                            enable_purge_protection=enable_purge_protection,
                            retention_days=retention_days,
                            network_acls=network_acls,
                            network_acls_ips=network_acls_ips,
                            network_acls_vnets=network_acls_vnets,
                            bypass=bypass,
                            default_action=default_action,
                            no_self_perms=no_self_perms,
                            tags=tags,
                            no_wait=no_wait,
                            public_network_access=public_network_access)

    if hsm_name:
        hsm_client = get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)(cmd.cli_ctx, None)

        from msrest.exceptions import ValidationError
        try:
            return create_hsm(cmd=cmd,
                              client=hsm_client,
                              resource_group_name=resource_group_name,
                              hsm_name=hsm_name,
                              administrators=administrators,
                              location=location,
                              sku=sku,
                              enable_purge_protection=enable_purge_protection,
                              retention_days=retention_days,
                              network_acls_ips=network_acls_ips,
                              public_network_access=public_network_access,
                              bypass=bypass,
                              default_action=default_action,
                              tags=tags,
                              user_identities=user_identities,
                              no_wait=no_wait)
        except ValidationError as ex:
            error_msg = str(ex)
            if 'Parameter \'name\' must conform to the following pattern' in error_msg:
                error_msg = 'Managed HSM name must be between 3-24 alphanumeric characters. ' \
                            'The name must begin with a letter, end with a letter or digit, ' \
                            'and not contain hyphens.'
            raise CLIError(error_msg)


# pylint: disable=too-many-locals
def create_hsm(cmd, client,
               resource_group_name, hsm_name, administrators, location=None, sku=None,
               enable_purge_protection=None,
               retention_days=None,
               network_acls_ips=None,
               public_network_access=None,
               bypass=None,
               default_action=None,
               tags=None,
               user_identities=None,
               no_wait=False):

    if not administrators:
        raise CLIError('Please specify --administrators')

    administrators = [admin.strip().replace('\r', '').replace('\n', '') for admin in administrators]

    from azure.cli.core._profile import Profile, _TENANT_ID

    if not sku:
        sku = 'Standard_B1'
    sku_family = sku.split('_')[1][0]

    ManagedHsm = cmd.get_models('ManagedHsm', resource_type=ResourceType.MGMT_KEYVAULT,
                                operation_group='managed_hsms')
    ManagedHsmProperties = cmd.get_models('ManagedHsmProperties', resource_type=ResourceType.MGMT_KEYVAULT,
                                          operation_group='managed_hsms')
    ManagedHsmSku = cmd.get_models('ManagedHsmSku', resource_type=ResourceType.MGMT_KEYVAULT,
                                   operation_group='managed_hsms')
    MHSMIPRule = cmd.get_models('MHSMIPRule', resource_type=ResourceType.MGMT_KEYVAULT,
                                operation_group='managed_hsms')

    network_acls = _create_network_rule_set(cmd, bypass, default_action)
    network_acls.ip_rules = []
    if network_acls_ips:
        for ip in network_acls_ips:
            network_acls.ip_rules.append(MHSMIPRule(value=ip))

    profile = Profile(cli_ctx=cmd.cli_ctx)
    tenant_id = profile.get_subscription(subscription=cmd.cli_ctx.data.get('subscription_id', None))[_TENANT_ID]

    properties = ManagedHsmProperties(tenant_id=tenant_id,
                                      enable_purge_protection=enable_purge_protection,
                                      soft_delete_retention_in_days=retention_days,
                                      initial_admin_object_ids=administrators,
                                      network_acls=network_acls,
                                      public_network_access=public_network_access)
    parameters = ManagedHsm(location=location,
                            tags=tags,
                            sku=ManagedHsmSku(name=sku, family=sku_family),
                            properties=properties)

    if user_identities:
        ManagedServiceIdentity = cmd.get_models('ManagedServiceIdentity', resource_type=ResourceType.MGMT_KEYVAULT,
                                                operation_group='managed_hsms')
        if len(user_identities) == 1 and user_identities[0].lower() == 'none':
            parameters.identity = ManagedServiceIdentity(type='None')
        else:
            identities = {i: {} for i in user_identities}
            parameters.identity = ManagedServiceIdentity(type='UserAssigned', user_assigned_identities=identities)

    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name=resource_group_name,
                       name=hsm_name,
                       parameters=parameters)


def wait_hsm(client, hsm_name, resource_group_name):
    return client.get(resource_group_name=resource_group_name, name=hsm_name)


def wait_vault_or_hsm(cmd, client, resource_group_name, vault_name=None, hsm_name=None):
    if vault_name:
        return client.get(resource_group_name=resource_group_name, vault_name=vault_name)
    hsm_client = get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)(cmd.cli_ctx, None)
    return hsm_client.get(resource_group_name=resource_group_name, name=hsm_name)


def create_vault(cmd, client,  # pylint: disable=too-many-locals, too-many-statements
                 resource_group_name, vault_name, location=None, sku=None,
                 enabled_for_deployment=None,
                 enabled_for_disk_encryption=None,
                 enabled_for_template_deployment=None,
                 enable_rbac_authorization=None,
                 enable_purge_protection=None,
                 retention_days=None,
                 network_acls=None,
                 network_acls_ips=None,
                 network_acls_vnets=None,
                 bypass=None,
                 default_action=None,
                 no_self_perms=None,
                 tags=None,
                 no_wait=False,
                 public_network_access=None):
    from azure.core.exceptions import HttpResponseError
    try:
        vault = client.get(resource_group_name=resource_group_name, vault_name=vault_name)
        if vault:
            raise InvalidArgumentValueError('The specified vault: {} already exists'.format(vault_name))
    except HttpResponseError:
        # if client.get raise exception, we can take it as no existing vault found
        # just continue the normal creation process
        pass

    VaultCreateOrUpdateParameters = cmd.get_models('VaultCreateOrUpdateParameters',
                                                   resource_type=ResourceType.MGMT_KEYVAULT)
    Permissions = cmd.get_models('Permissions', resource_type=ResourceType.MGMT_KEYVAULT)
    KeyPermissions = cmd.get_models('KeyPermissions', resource_type=ResourceType.MGMT_KEYVAULT)
    SecretPermissions = cmd.get_models('SecretPermissions', resource_type=ResourceType.MGMT_KEYVAULT)
    CertificatePermissions = cmd.get_models('CertificatePermissions', resource_type=ResourceType.MGMT_KEYVAULT)
    StoragePermissions = cmd.get_models('StoragePermissions', resource_type=ResourceType.MGMT_KEYVAULT)
    AccessPolicyEntry = cmd.get_models('AccessPolicyEntry', resource_type=ResourceType.MGMT_KEYVAULT)
    Sku = cmd.get_models('Sku', resource_type=ResourceType.MGMT_KEYVAULT)
    VaultProperties = cmd.get_models('VaultProperties', resource_type=ResourceType.MGMT_KEYVAULT)

    from azure.cli.core._profile import Profile, _TENANT_ID
    profile = Profile(cli_ctx=cmd.cli_ctx)
    subscription = profile.get_subscription(subscription=cmd.cli_ctx.data.get('subscription_id', None))
    tenant_id = subscription[_TENANT_ID]

    # if bypass or default_action was specified create a NetworkRuleSet
    # if neither were specified we will parse it from parameter `--network-acls`
    if network_acls or network_acls_ips or network_acls_vnets:
        network_acls = _parse_network_acls(
            cmd, resource_group_name, network_acls, network_acls_ips, network_acls_vnets, bypass, default_action)
    else:
        network_acls = _create_network_rule_set(cmd, bypass, default_action)

    if no_self_perms or enable_rbac_authorization:
        access_policies = []
    else:
        permissions = Permissions(keys_property=[KeyPermissions.all],
                                  secrets=[SecretPermissions.all],
                                  certificates=[CertificatePermissions.all],
                                  storage=[StoragePermissions.all])

        from azure.cli.command_modules.role.util import get_current_identity_object_id
        object_id = get_current_identity_object_id(cmd.cli_ctx)
        if not object_id:
            raise CLIError('Cannot create vault.\nUnable to query active directory for information '
                           'about the current user.\nYou may try the --no-self-perms flag to '
                           'create a vault without permissions.')
        access_policies = [AccessPolicyEntry(tenant_id=tenant_id,
                                             object_id=object_id,
                                             permissions=permissions)]

    if not sku:
        sku = 'standard'

    properties = VaultProperties(tenant_id=tenant_id,
                                 sku=Sku(name=sku, family='A'),
                                 access_policies=access_policies,
                                 vault_uri=None,
                                 enabled_for_deployment=enabled_for_deployment,
                                 enabled_for_disk_encryption=enabled_for_disk_encryption,
                                 enabled_for_template_deployment=enabled_for_template_deployment,
                                 enable_rbac_authorization=enable_rbac_authorization,
                                 enable_purge_protection=enable_purge_protection,
                                 soft_delete_retention_in_days=int(retention_days),
                                 public_network_access=public_network_access)
    if hasattr(properties, 'network_acls'):
        properties.network_acls = network_acls
    parameters = VaultCreateOrUpdateParameters(location=location,
                                               tags=tags,
                                               properties=properties)

    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name=resource_group_name,
                       vault_name=vault_name,
                       parameters=parameters)


def update_vault_setter(cmd, client, parameters, resource_group_name, vault_name, no_wait=False):
    VaultCreateOrUpdateParameters = cmd.get_models('VaultCreateOrUpdateParameters',
                                                   resource_type=ResourceType.MGMT_KEYVAULT)
    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name=resource_group_name,
                       vault_name=vault_name,
                       parameters=VaultCreateOrUpdateParameters(
                           location=parameters.location,
                           tags=parameters.tags,
                           properties=parameters.properties))


def update_hsm_setter(cmd, client, parameters, resource_group_name, name, no_wait=False):
    ManagedHsm = cmd.get_models('ManagedHsm', resource_type=ResourceType.MGMT_KEYVAULT, operation_group='managed_hsms')
    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name=resource_group_name,
                       name=name,
                       parameters=ManagedHsm(
                           sku=parameters.sku,
                           tags=parameters.tags,
                           location=parameters.location,
                           identity=parameters.identity,
                           properties=parameters.properties))


def update_vault(cmd, instance,
                 enabled_for_deployment=None,
                 enabled_for_disk_encryption=None,
                 enabled_for_template_deployment=None,
                 enable_rbac_authorization=None,
                 enable_purge_protection=None,
                 retention_days=None,
                 bypass=None,
                 default_action=None,
                 public_network_access=None):
    if enabled_for_deployment is not None:
        instance.properties.enabled_for_deployment = enabled_for_deployment

    if enabled_for_disk_encryption is not None:
        instance.properties.enabled_for_disk_encryption = enabled_for_disk_encryption

    if enabled_for_template_deployment is not None:
        instance.properties.enabled_for_template_deployment = enabled_for_template_deployment

    if enable_rbac_authorization is not None:
        instance.properties.enable_rbac_authorization = enable_rbac_authorization

    if enable_purge_protection is not None:
        instance.properties.enable_purge_protection = enable_purge_protection

    if retention_days is not None:
        instance.properties.soft_delete_retention_in_days = int(retention_days)

    if bypass or default_action and (hasattr(instance.properties, 'network_acls')):
        if instance.properties.network_acls is None:
            instance.properties.network_acls = _create_network_rule_set(cmd, bypass, default_action)
        else:
            if bypass:
                instance.properties.network_acls.bypass = bypass
            if default_action:
                instance.properties.network_acls.default_action = default_action

    if public_network_access is not None:
        instance.properties.public_network_access = public_network_access

    return instance


def update_hsm(cmd, instance,
               enable_purge_protection=None,
               bypass=None,
               default_action=None,
               secondary_locations=None,
               public_network_access=None,
               user_identities=None):
    if enable_purge_protection is not None:
        instance.properties.enable_purge_protection = enable_purge_protection

    if secondary_locations is not None:
        # service not ready
        raise InvalidArgumentValueError('--secondary-locations has not been supported yet for hsm')

    if public_network_access is not None:
        instance.properties.public_network_access = public_network_access

    if bypass or default_action and (hasattr(instance.properties, 'network_acls')):
        if instance.properties.network_acls is None:
            instance.properties.network_acls = _create_network_rule_set(cmd, bypass, default_action)
        else:
            if bypass:
                instance.properties.network_acls.bypass = bypass
            if default_action:
                instance.properties.network_acls.default_action = default_action
    if user_identities:
        ManagedServiceIdentity = cmd.get_models('ManagedServiceIdentity', resource_type=ResourceType.MGMT_KEYVAULT,
                                                operation_group='managed_hsms')
        if len(user_identities) == 1 and user_identities[0].lower() == 'none':
            instance.identity = ManagedServiceIdentity(type='None')
        else:
            identities = {i: {} for i in user_identities}
            instance.identity = ManagedServiceIdentity(type='UserAssigned', user_assigned_identities=identities)
    return instance


def _object_id_args_helper(cli_ctx, object_id, spn, upn):
    if not object_id:
        from azure.cli.command_modules.role.util import get_object_id
        object_id = get_object_id(cli_ctx, spn=spn, upn=upn)
        if not object_id:
            raise CLIError('Unable to get object id from principal name.')
    return object_id


def _permissions_distinct(permissions):
    if permissions:
        return list(set(permissions))
    return permissions


def set_policy(cmd, client, resource_group_name, vault_name,
               object_id=None, application_id=None, spn=None, upn=None, key_permissions=None, secret_permissions=None,
               certificate_permissions=None, storage_permissions=None, no_wait=False):
    """ Update security policy settings for a Key Vault. """

    VaultCreateOrUpdateParameters = cmd.get_models('VaultCreateOrUpdateParameters',
                                                   resource_type=ResourceType.MGMT_KEYVAULT)
    AccessPolicyEntry = cmd.get_models('AccessPolicyEntry', resource_type=ResourceType.MGMT_KEYVAULT)
    Permissions = cmd.get_models('Permissions', resource_type=ResourceType.MGMT_KEYVAULT)
    object_id = _object_id_args_helper(cmd.cli_ctx, object_id, spn, upn)
    vault = client.get(resource_group_name=resource_group_name,
                       vault_name=vault_name)

    key_permissions = _permissions_distinct(key_permissions)
    secret_permissions = _permissions_distinct(secret_permissions)
    certificate_permissions = _permissions_distinct(certificate_permissions)
    storage_permissions = _permissions_distinct(storage_permissions)

    try:
        enable_rbac_authorization = getattr(vault.properties, 'enable_rbac_authorization')
    except:  # pylint: disable=bare-except
        pass
    else:
        if enable_rbac_authorization:
            raise CLIError('Cannot set policies to a vault with \'--enable-rbac-authorization\' specified')

    # Find the existing policy to set
    policy = next((p for p in vault.properties.access_policies
                   if object_id.lower() == p.object_id.lower() and
                   (application_id or '').lower() == (p.application_id or '').lower() and
                   vault.properties.tenant_id.lower() == p.tenant_id.lower()), None)
    if not policy:
        # Add new policy as none found
        vault.properties.access_policies.append(AccessPolicyEntry(
            tenant_id=vault.properties.tenant_id,
            object_id=object_id,
            application_id=application_id,
            permissions=Permissions(keys_property=key_permissions,
                                    secrets=secret_permissions,
                                    certificates=certificate_permissions,
                                    storage=storage_permissions)))
    else:
        # Modify existing policy.
        # If key_permissions is not set, use prev. value (similarly with secret_permissions).
        keys = policy.permissions.keys_property if key_permissions is None else key_permissions
        secrets = policy.permissions.secrets if secret_permissions is None else secret_permissions
        certs = policy.permissions.certificates \
            if certificate_permissions is None else certificate_permissions
        storage = policy.permissions.storage if storage_permissions is None else storage_permissions
        policy.permissions = Permissions(keys_property=keys, secrets=secrets, certificates=certs, storage=storage)

    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name=resource_group_name,
                       vault_name=vault_name,
                       parameters=VaultCreateOrUpdateParameters(
                           location=vault.location,
                           tags=vault.tags,
                           properties=vault.properties))


def add_network_rule_for_vault_or_hsm(cmd, client, resource_group_name, vault_name=None, hsm_name=None,
                                      ip_address=None, subnet=None, vnet_name=None, no_wait=False):
    if vault_name:
        return add_vault_network_rule(cmd, client, resource_group_name, vault_name,
                                      ip_address=ip_address, subnet=subnet, vnet_name=vnet_name, no_wait=no_wait)
    if hsm_name:
        hsm_client = get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)(cmd.cli_ctx, None)
        return add_hsm_network_rule(cmd, hsm_client, resource_group_name, hsm_name,
                                    ip_address=ip_address, subnet=subnet, vnet_name=vnet_name, no_wait=no_wait)


def add_vault_network_rule(cmd, client, resource_group_name, vault_name, ip_address=None, subnet=None,
                           vnet_name=None, no_wait=False):  # pylint: disable=unused-argument
    """ Add a network rule to the network ACLs for a Key Vault. """
    VirtualNetworkRule = cmd.get_models('VirtualNetworkRule', resource_type=ResourceType.MGMT_KEYVAULT)
    IPRule = cmd.get_models('IPRule', resource_type=ResourceType.MGMT_KEYVAULT)
    VaultCreateOrUpdateParameters = cmd.get_models('VaultCreateOrUpdateParameters',
                                                   resource_type=ResourceType.MGMT_KEYVAULT)
    vault = client.get(resource_group_name=resource_group_name, vault_name=vault_name)
    vault.properties.network_acls = vault.properties.network_acls or _create_network_rule_set(cmd)
    rules = vault.properties.network_acls

    if not subnet and not ip_address:
        logger.warning('No subnet or ip address supplied.')

    to_update = False
    if subnet:
        rules.virtual_network_rules = rules.virtual_network_rules or []

        # if the rule already exists, don't add again
        to_modify = True
        for x in rules.virtual_network_rules:
            if x.id.lower() == subnet.lower():
                to_modify = False
                break
        if to_modify:
            rules.virtual_network_rules.append(VirtualNetworkRule(id=subnet))
            to_update = True

    if ip_address:
        rules.ip_rules = rules.ip_rules or []
        # if the rule already exists, don't add again
        for ip in ip_address:
            to_modify = True
            for x in rules.ip_rules:
                existing_ip_network = ip_network(x.value)
                new_ip_network = ip_network(ip)
                if new_ip_network.overlaps(existing_ip_network):
                    logger.warning("IP/CIDR %s overlaps with %s, which exists already. Not adding duplicates.",
                                   ip, x.value)
                    to_modify = False
                    break
            if to_modify:
                rules.ip_rules.append(IPRule(value=ip))
                to_update = True

    # if we didn't modify the network rules just return the vault as is
    if not to_update:
        return vault

    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name=resource_group_name,
                       vault_name=vault_name,
                       parameters=VaultCreateOrUpdateParameters(
                           location=vault.location,
                           tags=vault.tags,
                           properties=vault.properties))


def add_hsm_network_rule(cmd, client, resource_group_name, hsm_name,
                         ip_address=None, subnet=None, vnet_name=None, no_wait=False):
    if subnet or vnet_name:
        raise InvalidArgumentValueError("--subnet and --vnet-name are not supported for MHSM yet")

    hsm = client.get(resource_group_name=resource_group_name, name=hsm_name)
    hsm.properties.network_acls = hsm.properties.network_acls or _create_network_rule_set(cmd)
    rules = hsm.properties.network_acls
    IPRule = cmd.get_models('MHSMIPRule', resource_type=ResourceType.MGMT_KEYVAULT)

    to_update = False
    if ip_address:
        rules.ip_rules = rules.ip_rules or []
        # if the rule already exists, don't add again
        for ip in ip_address:
            to_modify = True
            for x in rules.ip_rules:
                existing_ip_network = ip_network(x.value)
                new_ip_network = ip_network(ip)
                if new_ip_network.overlaps(existing_ip_network):
                    logger.warning("IP/CIDR %s overlaps with %s, which exists already. Not adding duplicates.",
                                   ip, x.value)
                    to_modify = False
                    break
            if to_modify:
                rules.ip_rules.append(IPRule(value=ip))
                to_update = True

    if not to_update:
        return hsm

    client.begin_create_or_update(resource_group_name=resource_group_name,
                                  name=hsm_name,
                                  parameters=hsm,
                                  polling=not no_wait).result()
    if not no_wait:
        return client.get(resource_group_name=resource_group_name, name=hsm_name)


def remove_network_rule_for_vault_or_hsm(cmd, client, resource_group_name, vault_name=None, hsm_name=None,
                                         ip_address=None, subnet=None, vnet_name=None, no_wait=False):
    if vault_name:
        return remove_vault_network_rule(cmd, client, resource_group_name, vault_name,
                                         ip_address=ip_address, subnet=subnet, vnet_name=vnet_name, no_wait=no_wait)
    hsm_client = get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)(cmd.cli_ctx, None)
    return remove_hsm_network_rule(hsm_client, resource_group_name, hsm_name,
                                   ip_address=ip_address, subnet=subnet, vnet_name=vnet_name, no_wait=no_wait)


def remove_vault_network_rule(cmd, client, resource_group_name, vault_name, ip_address=None,
                              subnet=None, vnet_name=None, no_wait=False):  # pylint: disable=unused-argument
    """ Remove a network rule from the network ACLs for a Key Vault. """

    VaultCreateOrUpdateParameters = cmd.get_models('VaultCreateOrUpdateParameters',
                                                   resource_type=ResourceType.MGMT_KEYVAULT)
    vault = client.get(resource_group_name=resource_group_name, vault_name=vault_name)

    if not vault.properties.network_acls:
        return vault

    rules = vault.properties.network_acls

    to_modify = False

    if subnet and rules.virtual_network_rules:
        # key vault service will convert subnet ID to lowercase, so do case-insensitive compare
        new_rules = [x for x in rules.virtual_network_rules if x.id.lower() != subnet.lower()]
        to_modify |= len(new_rules) != len(rules.virtual_network_rules)
        if to_modify:
            rules.virtual_network_rules = new_rules

    if ip_address and rules.ip_rules:
        to_remove = [ip_network(x) for x in ip_address]
        new_rules = list(filter(lambda x: all(ip_network(x.value) != i for i in to_remove), rules.ip_rules))
        to_modify |= len(new_rules) != len(rules.ip_rules)
        if to_modify:
            rules.ip_rules = new_rules

    # if we didn't modify the network rules just return the vault as is
    if not to_modify:
        return vault

    # otherwise update
    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name=resource_group_name,
                       vault_name=vault_name,
                       parameters=VaultCreateOrUpdateParameters(
                           location=vault.location,
                           tags=vault.tags,
                           properties=vault.properties))


def remove_hsm_network_rule(client, resource_group_name, hsm_name,
                            ip_address=None, subnet=None, vnet_name=None, no_wait=False):
    if subnet or vnet_name:
        raise InvalidArgumentValueError("--subnet and --vnet-name are not supported for MHSM yet")

    hsm = client.get(resource_group_name=resource_group_name, name=hsm_name)

    if not hsm.properties.network_acls:
        return hsm

    rules = hsm.properties.network_acls

    to_modify = False

    if ip_address and rules.ip_rules:
        to_remove = [ip_network(x) for x in ip_address]
        new_rules = list(filter(lambda x: all(ip_network(x.value) != i for i in to_remove), rules.ip_rules))
        to_modify |= len(new_rules) != len(rules.ip_rules)
        if to_modify:
            rules.ip_rules = new_rules

    # if we didn't modify the network rules just return the vault as is
    if not to_modify:
        return hsm

    # otherwise update
    client.begin_create_or_update(resource_group_name=resource_group_name,
                                  name=hsm_name,
                                  parameters=hsm,
                                  polling=not no_wait).result()
    if not no_wait:
        return client.get(resource_group_name=resource_group_name, name=hsm_name)


def list_network_rules(cmd, client, resource_group_name, vault_name=None, hsm_name=None):  # pylint: disable=unused-argument
    """ List the network rules from the network ACLs for a Key Vault or a Managed HSM. """
    if vault_name:
        vault = client.get(resource_group_name=resource_group_name, vault_name=vault_name)
        return vault.properties.network_acls
    hsm_client = get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.managed_hsms)(cmd.cli_ctx, None)
    hsm = hsm_client.get(resource_group_name, name=hsm_name)
    return hsm.properties.network_acls


def delete_policy(cmd, client, resource_group_name, vault_name,
                  object_id=None, application_id=None, spn=None, upn=None, no_wait=False):
    """ Delete security policy settings for a Key Vault. """
    VaultCreateOrUpdateParameters = cmd.get_models('VaultCreateOrUpdateParameters',
                                                   resource_type=ResourceType.MGMT_KEYVAULT)
    object_id = _object_id_args_helper(cmd.cli_ctx, object_id, spn, upn)
    vault = client.get(resource_group_name=resource_group_name,
                       vault_name=vault_name)

    try:
        enable_rbac_authorization = getattr(vault.properties, 'enable_rbac_authorization')
    except:  # pylint: disable=bare-except
        pass
    else:
        if enable_rbac_authorization:
            raise CLIError('Cannot delete policies to a vault with \'--enable-rbac-authorization\' specified')

    prev_policies_len = len(vault.properties.access_policies)
    vault.properties.access_policies = [p for p in vault.properties.access_policies if
                                        vault.properties.tenant_id.lower() != p.tenant_id.lower() or
                                        object_id.lower() != p.object_id.lower() or
                                        (application_id or '').lower() != (p.application_id or '').lower()]
    if len(vault.properties.access_policies) == prev_policies_len:
        raise CLIError('No matching policies found')

    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name=resource_group_name,
                       vault_name=vault_name,
                       parameters=VaultCreateOrUpdateParameters(
                           location=vault.location,
                           tags=vault.tags,
                           properties=vault.properties))
# endregion


# region KeyVault Key
def create_key(client, name=None, protection=None,  # pylint: disable=unused-argument
               key_size=None, key_ops=None, disabled=False, expires=None,
               not_before=None, tags=None, kty=None, curve=None, exportable=None, release_policy=None):

    return client.create_key(name=name,
                             key_type=kty,
                             size=key_size,
                             key_operations=key_ops,
                             enabled=not disabled,
                             not_before=not_before,
                             expires_on=expires,
                             tags=tags,
                             curve=curve,
                             exportable=exportable,
                             release_policy=release_policy)


def list_keys(client, maxresults=None, include_managed=False):
    result = client.list_properties_of_keys(max_page_size=maxresults)
    if not include_managed:
        return [_ for _ in result if not getattr(_, 'managed')] if result else result
    return result


def get_key_attestation(client, name, version=None, file_path=None):
    key = client.get_key_attestation(name=name, version=version)
    key_attestation = key.properties.attestation
    if not file_path:
        return key_attestation

    if os.path.isfile(file_path) or os.path.isdir(file_path):
        raise CLIError("File or directory named '{}' already exists.".format(file_path))

    try:
        from ._command_type import _encode_hex
        with open(file_path, 'w') as outfile:
            json.dump(todict(_encode_hex(key_attestation)), outfile)
    except Exception as ex:  # pylint: disable=broad-except
        if os.path.isfile(file_path):
            os.remove(file_path)
        raise ex


def delete_key(client, name):
    return client.begin_delete_key(name).result()


def recover_key(client, name):
    return client.begin_recover_deleted_key(name).result()


def encrypt_key(cmd, client, algorithm, value, iv=None, aad=None, name=None, version=None):
    EncryptionAlgorithm = cmd.loader.get_sdk('EncryptionAlgorithm', mod='crypto._enums',
                                             resource_type=ResourceType.DATA_KEYVAULT_KEYS)
    import binascii
    crypto_client = client.get_cryptography_client(name, key_version=version)
    return crypto_client.encrypt(EncryptionAlgorithm(algorithm), value,
                                 iv=binascii.unhexlify(iv) if iv else None,
                                 additional_authenticated_data=binascii.unhexlify(aad) if aad else None)


def decrypt_key(cmd, client, algorithm, value, iv=None, tag=None, aad=None,
                name=None, version=None, data_type='base64'):  # pylint: disable=unused-argument
    EncryptionAlgorithm = cmd.loader.get_sdk('EncryptionAlgorithm', mod='crypto._enums',
                                             resource_type=ResourceType.DATA_KEYVAULT_KEYS)
    import binascii
    crypto_client = client.get_cryptography_client(name, key_version=version)
    return crypto_client.decrypt(EncryptionAlgorithm(algorithm), value,
                                 iv=binascii.unhexlify(iv) if iv else None,
                                 authentication_tag=binascii.unhexlify(tag) if tag else None,
                                 additional_authenticated_data=binascii.unhexlify(aad) if aad else None)


def sign_key(cmd, client, algorithm, digest, name=None, version=None):
    SignatureAlgorithm = cmd.loader.get_sdk('SignatureAlgorithm', mod='crypto._enums',
                                            resource_type=ResourceType.DATA_KEYVAULT_KEYS)
    crypto_client = client.get_cryptography_client(name, key_version=version)
    return crypto_client.sign(SignatureAlgorithm(algorithm), base64.b64decode(digest.encode('utf-8')))


def verify_key(cmd, client, algorithm, digest, signature, name=None, version=None):
    SignatureAlgorithm = cmd.loader.get_sdk('SignatureAlgorithm', mod='crypto._enums',
                                            resource_type=ResourceType.DATA_KEYVAULT_KEYS)
    crypto_client = client.get_cryptography_client(name, key_version=version)
    return crypto_client.verify(SignatureAlgorithm(algorithm),
                                base64.b64decode(digest.encode('utf-8')),
                                base64.b64decode(signature.encode('utf-8')))


def backup_key(client, file_path, name):
    backup = client.backup_key(name)
    with open(file_path, 'wb') as output:
        output.write(backup)


def restore_key(cmd, client, name=None, file_path=None, storage_resource_uri=None,  # pylint: disable=unused-argument
                storage_account_name=None, blob_container_name=None,
                token=None, backup_folder=None, no_wait=False):
    if file_path:
        if any([storage_account_name, blob_container_name, token, backup_folder]):
            raise MutuallyExclusiveArgumentError('Do not use --file/-f with any of --storage-account-name/'
                                                 '--blob-container-name/--storage-container-SAS-token/--backup-folder')
        if name:
            raise MutuallyExclusiveArgumentError('Please do not specify --name/-n when using --file/-f')

        if no_wait:
            raise MutuallyExclusiveArgumentError('Please do not specify --no-wait when using --file/-f')

    if not file_path and not any([storage_account_name, blob_container_name, token, backup_folder]):
        raise RequiredArgumentMissingError('Please specify --file/-f or --storage-account-name & '
                                           '--blob-container-name & --storage-container-SAS-token & --backup-folder')

    if file_path:
        with open(file_path, 'rb') as file_in:
            data = file_in.read()
        return client.restore_key_backup(data)

    if not token:
        raise RequiredArgumentMissingError('Please specify --storage-container-SAS-token/-t')
    if not backup_folder:
        raise RequiredArgumentMissingError('Please specify --backup-folder')

    storage_account_parameters_check(storage_resource_uri, storage_account_name, blob_container_name)
    if not storage_resource_uri:
        storage_resource_uri = construct_storage_uri(
            cmd.cli_ctx.cloud.suffixes.storage_endpoint, storage_account_name, blob_container_name)

    backup_client = get_client_factory(
        ResourceType.DATA_KEYVAULT_ADMINISTRATION_BACKUP)(cmd.cli_ctx, {'vault_base_url': client.vault_url})
    return sdk_no_wait(
        no_wait, backup_client.begin_selective_restore,
        folder_url='{}/{}'.format(storage_resource_uri, backup_folder),
        sas_token=token,
        key_name=name
    )


def _int_to_bytes(i):
    h = hex(i)
    if len(h) > 1 and h[0:2] == '0x':
        h = h[2:]
    # need to strip L in python 2.x
    h = h.strip('L')
    if len(h) % 2:
        h = '0' + h
    return codecs.decode(h, 'hex')


def _public_rsa_key_to_jwk(rsa_key, jwk, encoding=None):
    pubv = rsa_key.public_numbers()
    jwk['n'] = _int_to_bytes(pubv.n)
    if encoding:
        jwk['n'] = encoding(jwk['n'])
    jwk['e'] = _int_to_bytes(pubv.e)
    if encoding:
        jwk['e'] = encoding(jwk['e'])


def _private_rsa_key_to_jwk(rsa_key, jwk):
    priv = rsa_key.private_numbers()
    jwk.n = _int_to_bytes(priv.public_numbers.n)
    jwk.e = _int_to_bytes(priv.public_numbers.e)
    jwk.q = _int_to_bytes(priv.q)
    jwk.p = _int_to_bytes(priv.p)
    jwk.d = _int_to_bytes(priv.d)
    jwk.dq = _int_to_bytes(priv.dmq1)
    jwk.dp = _int_to_bytes(priv.dmp1)
    jwk.qi = _int_to_bytes(priv.iqmp)


def _private_ec_key_to_jwk(ec_key, jwk):
    supported_curves = {
        'secp256r1': 'P-256',
        'secp384r1': 'P-384',
        'secp521r1': 'P-521',
        'secp256k1': 'SECP256K1'
    }
    curve = ec_key.private_numbers().public_numbers.curve.name

    jwk.crv = supported_curves.get(curve, None)
    if not jwk.crv:
        raise CLIError("Import failed: Unsupported curve, {}.".format(curve))

    jwk.x = _int_to_bytes(ec_key.private_numbers().public_numbers.x)
    jwk.y = _int_to_bytes(ec_key.private_numbers().public_numbers.y)
    jwk.d = _int_to_bytes(ec_key.private_numbers().private_value)


def import_key(cmd, client, name=None,  # pylint: disable=too-many-locals
               protection=None, key_ops=None, disabled=False, expires=None,
               not_before=None, tags=None, pem_file=None, pem_string=None, pem_password=None, byok_file=None,
               byok_string=None, kty='RSA', curve=None, exportable=None, release_policy=None):
    """ Import a private key. Supports importing base64 encoded private keys from PEM files or strings.
        Supports importing BYOK keys into HSM for premium key vaults. """
    JsonWebKey = cmd.loader.get_sdk('JsonWebKey', resource_type=ResourceType.DATA_KEYVAULT_KEYS, mod='_models')

    key_obj = JsonWebKey(key_ops=key_ops)
    if pem_file or pem_string:
        if pem_file:
            logger.info('Reading %s', pem_file)
            with open(pem_file, 'rb') as f:
                pem_data = f.read()
        elif pem_string:
            pem_data = pem_string.encode('UTF-8')
        pem_password = str(pem_password).encode() if pem_password else None

        try:
            pkey = load_pem_private_key(pem_data, pem_password, default_backend())
        except (ValueError, TypeError, UnsupportedAlgorithm) as e:
            if str(e) == 'Could not deserialize key data.':
                raise CLIError('Import failed: {} The private key in the PEM file must be encrypted.'.format(e))
            raise CLIError('Import failed: {}'.format(e))

        # populate key into jwk
        if isinstance(pkey, rsa.RSAPrivateKey):
            key_obj.kty = 'RSA'
            _private_rsa_key_to_jwk(pkey, key_obj)
        elif isinstance(pkey, ec.EllipticCurvePrivateKey):
            key_obj.kty = 'EC'
            _private_ec_key_to_jwk(pkey, key_obj)
        else:
            raise CLIError('Import failed: Unsupported key type, {}.'.format(type(pkey)))

    elif byok_file or byok_string:
        if byok_file:
            logger.info('Reading %s', byok_file)
            with open(byok_file, 'rb') as f:
                byok_data = f.read()
        elif byok_string:
            byok_data = byok_string.encode('UTF-8')

        key_obj.kty = kty + '-HSM'
        key_obj.t = byok_data
        key_obj.crv = curve

    return client.import_key(name=name, key=key_obj,
                             hardware_protected=(protection == 'hsm'),
                             enabled=not disabled, tags=tags,
                             not_before=not_before, expires_on=expires,
                             exportable=exportable, release_policy=release_policy)


def _bytes_to_int(b):
    """Convert bytes to hex integer"""
    len_diff = 4 - len(b) % 4 if len(b) % 4 > 0 else 0
    b = len_diff * b'\x00' + b  # We have to patch leading zeros for using struct.unpack
    bytes_num = int(math.floor(len(b) / 4))
    ans = 0
    items = struct.unpack('>' + 'I' * bytes_num, b)
    for sub_int in items:  # Accumulate all items into a big integer
        ans *= 2 ** 32
        ans += sub_int
    return ans


def _jwk_to_dict(jwk):
    """Convert a `JsonWebKey` struct to a python dict"""
    d = {}
    if jwk.crv:
        d['crv'] = jwk.crv
    if jwk.kid:
        d['kid'] = jwk.kid
    if jwk.kty:
        d['kty'] = jwk.kty
    if jwk.d:
        d['d'] = _bytes_to_int(jwk.d)
    if jwk.dp:
        d['dp'] = _bytes_to_int(jwk.dp)
    if jwk.dq:
        d['dq'] = _bytes_to_int(jwk.dq)
    if jwk.e:
        d['e'] = _bytes_to_int(jwk.e)
    if jwk.k:
        d['k'] = _bytes_to_int(jwk.k)
    if jwk.n:
        d['n'] = _bytes_to_int(jwk.n)
    if jwk.p:
        d['p'] = _bytes_to_int(jwk.p)
    if jwk.q:
        d['q'] = _bytes_to_int(jwk.q)
    if jwk.qi:
        d['qi'] = _bytes_to_int(jwk.qi)
    if jwk.t:
        d['t'] = _bytes_to_int(jwk.t)
    if jwk.x:
        d['x'] = _bytes_to_int(jwk.x)
    if jwk.y:
        d['y'] = _bytes_to_int(jwk.y)

    return d


def _extract_rsa_public_key_from_jwk(jwk_dict):
    # https://github.com/mpdavis/python-jose/blob/eed086d7650ccbd4ea8b555157aff3b1b99f14b9/jose/backends/cryptography_backend.py#L249-L254
    e = jwk_dict.get('e', 256)
    n = jwk_dict.get('n')
    public = rsa.RSAPublicNumbers(e, n)
    return public.public_key(default_backend())


def _extract_ec_public_key_from_jwk(jwk_dict):
    # https://github.com/mpdavis/python-jose/blob/eed086d7650ccbd4ea8b555157aff3b1b99f14b9/jose/backends/cryptography_backend.py#L81-L100
    if not all(k in jwk_dict for k in ['x', 'y', 'crv']):
        raise CLIError('Invalid EC key: missing properties(x, y, crv)')

    x = jwk_dict.get('x')
    y = jwk_dict.get('y')
    curves = {
        'P-256': ec.SECP256R1,
        'P-384': ec.SECP384R1,
        'P-521': ec.SECP521R1,
        'P-256K': ec.SECP256K1,
        'SECP256K1': ec.SECP256K1
    }
    curve = curves[jwk_dict['crv']]
    public = ec.EllipticCurvePublicNumbers(x, y, curve())
    return public.public_key(default_backend())


def _export_public_key(k, encoding=Encoding.PEM):
    # https://github.com/mpdavis/python-jose/blob/eed086d7650ccbd4ea8b555157aff3b1b99f14b9/jose/backends/cryptography_backend.py#L329-L332
    return k.public_bytes(
        encoding=encoding,
        format=PublicFormat.SubjectPublicKeyInfo
    )


def _export_public_key_to_der(k):
    return _export_public_key(k, encoding=Encoding.DER)


def _export_public_key_to_pem(k):
    return _export_public_key(k, encoding=Encoding.PEM)


def download_key(client, file_path, name, version='', encoding=None):
    """ Download a key from a KeyVault. """
    if os.path.isfile(file_path) or os.path.isdir(file_path):
        raise CLIError("File or directory named '{}' already exists.".format(file_path))

    key = client.get_key(name=name, version=version)
    json_web_key = _jwk_to_dict(key.key)
    key_type = json_web_key['kty']
    pub_key = ''

    if key_type in ['RSA', 'RSA-HSM']:
        pub_key = _extract_rsa_public_key_from_jwk(json_web_key)
    elif key_type in ['EC', 'EC-HSM']:
        pub_key = _extract_ec_public_key_from_jwk(json_web_key)
    else:
        raise CLIError('Unsupported key type: {}. (Supported key types: RSA, RSA-HSM, EC, EC-HSM)'.format(key_type))

    methods = {
        'DER': _export_public_key_to_der,
        'PEM': _export_public_key_to_pem
    }

    if encoding not in methods:
        raise CLIError('Unsupported encoding: {}. (Supported encodings: DER, PEM)'.format(encoding))

    try:
        with open(file_path, 'wb') as f:
            f.write(methods[encoding](pub_key))
    except Exception as ex:  # pylint: disable=broad-except
        if os.path.isfile(file_path):
            os.remove(file_path)
        raise ex


def get_policy_template():
    policy = {
        'version': '1.0.0',
        'anyOf': [{
            'authority': '<issuer>',
            'allOf': [{
                'claim': '<claim name>',
                'equals': '<value to match>'
            }]
        }]
    }
    return policy


def update_key_rotation_policy(cmd, client, value, key_name=None):
    from azure.cli.core.util import read_file_content, get_json_object
    if os.path.exists(value):
        value = read_file_content(value)

    policy = get_json_object(value)
    if not policy:
        raise InvalidArgumentValueError("Please specify a valid policy")

    KeyRotationLifetimeAction = cmd.loader.get_sdk('KeyRotationLifetimeAction', mod='_models',
                                                   resource_type=ResourceType.DATA_KEYVAULT_KEYS)
    KeyRotationPolicy = cmd.loader.get_sdk('KeyRotationPolicy', mod='_models',
                                           resource_type=ResourceType.DATA_KEYVAULT_KEYS)
    lifetime_actions = []
    if policy.get('lifetime_actions', None):
        for action in policy['lifetime_actions']:
            try:
                action_type = action['action'].get('type', None) if action.get('action', None) else None
            except AttributeError:
                action_type = action.get('action', None)
            time_after_create = action['trigger'].get('time_after_create', None) \
                if action.get('trigger', None) else action.get('time_after_create', None)
            time_before_expiry = action['trigger'].get('time_before_expiry', None) \
                if action.get('trigger', None) else action.get('time_before_expiry', None)
            lifetime_action = KeyRotationLifetimeAction(action_type,
                                                        time_after_create=time_after_create,
                                                        time_before_expiry=time_before_expiry)
            lifetime_actions.append(lifetime_action)
    expires_in = policy.get('expires_in', None) or policy.get('expiry_time', None)
    if policy.get('attributes', None):
        expires_in = policy['attributes'].get('expires_in', None) or policy['attributes'].get('expiry_time', None)
    return client.update_key_rotation_policy(key_name=key_name,
                                             policy=KeyRotationPolicy(lifetime_actions=lifetime_actions,
                                                                      expires_in=expires_in))
# endregion


# region KeyVault Secret
def download_secret(client, file_path, name=None, encoding=None, version='', overwrite=False):  # pylint: disable=unused-argument
    """ Download a secret from a KeyVault. """
    if os.path.isdir(file_path):
        raise CLIError("Cannot write to '{}': it is a directory.".format(file_path))

    if not overwrite and os.path.isfile(file_path):
        raise CLIError("File '{}' already exists. Use --overwrite to overwrite the existing file.".format(file_path))

    secret = client.get_secret(name, version)

    if not encoding:
        encoding = secret.properties.tags.get('file-encoding', 'utf-8') if secret.properties.tags else 'utf-8'

    secret_value = secret.value

    try:
        if encoding in secret_text_encoding_values:
            with open(file_path, 'w') as f:
                f.write(secret_value)
        else:
            if encoding == 'base64':
                decoded = base64.b64decode(secret_value)
            elif encoding == 'hex':
                import binascii
                decoded = binascii.unhexlify(secret_value)

            with open(file_path, 'wb') as f:
                f.write(decoded)
    except Exception as ex:  # pylint: disable=broad-except
        if os.path.isfile(file_path):
            os.remove(file_path)
        raise ex


def backup_secret(client, file_path, name=None):  # pylint: disable=unused-argument
    backup = client.backup_secret(name)
    with open(file_path, 'wb') as output:
        output.write(backup)


def restore_secret(client, file_path):
    with open(file_path, 'rb') as file_in:
        data = file_in.read()
    return client.restore_secret_backup(data)
# endregion


# region KeyVault Certificate
# pylint: disable=inconsistent-return-statements
def create_certificate(client, certificate_name, policy,
                       disabled=False, tags=None):
    logger.info("Starting long-running operation 'keyvault certificate create'")

    poller = client.begin_create_certificate(certificate_name=certificate_name,
                                             policy=policy,
                                             enabled=not disabled,
                                             tags=tags)
    if policy.issuer_name.lower() == 'unknown':
        # return immediately for a pending certificate
        return client.get_certificate_operation(certificate_name)

    # otherwise polling until the certificate creation is complete
    poller.result()
    return client.get_certificate_operation(certificate_name)


def _asn1_to_iso8601(asn1_date):
    import dateutil.parser
    if isinstance(asn1_date, bytes):
        asn1_date = asn1_date.decode('utf-8')
    return dateutil.parser.parse(asn1_date)


def download_certificate(client, file_path, certificate_name=None, encoding='PEM', version=''):
    """ Download a certificate from a KeyVault. """
    if os.path.isfile(file_path) or os.path.isdir(file_path):
        raise CLIError("File or directory named '{}' already exists.".format(file_path))

    cert = client.get_certificate_version(certificate_name, version).cer

    try:
        with open(file_path, 'wb') as f:
            if encoding == 'DER':
                f.write(cert)
            else:
                encoded = base64.encodebytes(cert)
                if isinstance(encoded, bytes):
                    encoded = encoded.decode("utf-8")
                encoded = '-----BEGIN CERTIFICATE-----\n' + encoded + '-----END CERTIFICATE-----\n'
                f.write(encoded.encode("utf-8"))
    except Exception as ex:  # pylint: disable=broad-except
        if os.path.isfile(file_path):
            os.remove(file_path)
        raise ex


def backup_certificate(client, file_path, certificate_name=None):  # pylint: disable=unused-argument
    cert = client.backup_certificate(certificate_name)
    with open(file_path, 'wb') as output:
        output.write(cert)


def restore_certificate(client, file_path):
    with open(file_path, 'rb') as file_in:
        data = file_in.read()
    return client.restore_certificate_backup(backup=data)


def add_certificate_contact(cmd, client, email, name=None, phone=None):
    """ Add a contact to the specified vault to receive notifications of certificate operations. """
    CertificateContact = cmd.loader.get_sdk('CertificateContact', resource_type=ResourceType.DATA_KEYVAULT_CERTIFICATES,
                                            mod='_models')
    from azure.core.exceptions import ResourceNotFoundError
    try:
        contacts = client.get_contacts()
    except ResourceNotFoundError:
        contacts = []
    contact = CertificateContact(email=email, name=name, phone=phone)
    if any(x for x in contacts if x.email == email):
        raise CLIError("contact '{}' already exists".format(email))
    contacts.append(contact)
    return client.set_contacts(contacts)


def delete_certificate_contact(client, email):
    """ Remove a certificate contact from the specified vault. """
    orig_contacts = client.get_contacts()
    remaining_contacts = [x for x in orig_contacts if x.email != email]
    if len(remaining_contacts) == len(orig_contacts):
        raise CLIError("contact '{}' not found in vault".format(email))
    if remaining_contacts is not None and len(remaining_contacts) > 0:
        return client.set_contacts(remaining_contacts)
    client.delete_contacts()
    return []


def create_certificate_issuer(client, issuer_name, provider_name, account_id=None,
                              password=None, disabled=None, organization_id=None):
    """ Create a certificate issuer record.
    :param issuer_name: The name of the issuer.
    :param provider_name: The certificate provider name. Must be registered with your
        tenant ID and in your region.
    :param account_id: The issuer account id/username/etc.
    :param password: The issuer account password/secret/etc.
    :param organization_id: The organization id.
    """
    return client.create_issuer(issuer_name, provider_name, enabled=not disabled, account_id=account_id,
                                password=password, organization_id=organization_id)


def update_certificate_issuer(client, issuer_name, provider_name=None,
                              account_id=None, password=None, enabled=None, organization_id=None):
    """ Update a certificate issuer record.
    :param issuer_name: Unique identifier for the issuer settings.
    :param provider_name: The certificate provider name. Must be registered with your
        tenant ID and in your region.
    :param account_id: The issuer account id/username/etc.
    :param password: The issuer account password/secret/etc.
    :param organization_id: The organization id.
    """
    return client.update_issuer(issuer_name, provider=provider_name, enabled=enabled, account_id=account_id,
                                password=password, organization_id=organization_id)


def add_certificate_issuer_admin(cmd, client, issuer_name, email, first_name=None,
                                 last_name=None, phone=None):
    """ Add admin details for a specified certificate issuer. """
    AdministratorContact = cmd.loader.get_sdk('AdministratorContact',
                                              resource_type=ResourceType.DATA_KEYVAULT_CERTIFICATES,
                                              mod='_models')
    issuer = client.get_issuer(issuer_name)
    admins = issuer.admin_contacts
    if any(x for x in admins if x.email == email):
        raise CLIError("admin '{}' already exists".format(email))
    new_admin = AdministratorContact(first_name=first_name, last_name=last_name, email=email, phone=phone)
    admins.append(new_admin)
    client.update_issuer(issuer_name, admin_contacts=admins)
    return {
        "emailAddress": email,
        "firstName": first_name,
        "lastName": last_name,
        "phone": phone
    }


def delete_certificate_issuer_admin(client, issuer_name, email):
    """ Remove admin details for the specified certificate issuer. """
    issuer = client.get_issuer(issuer_name)
    admins = issuer.admin_contacts
    remaining = [x for x in admins if x.email != email]
    if len(remaining) == len(admins):
        raise CLIError("admin '{}' not found for issuer '{}'".format(email, issuer_name))
    if remaining:
        client.update_issuer(issuer_name, admin_contacts=remaining)
    else:
        organization_id = issuer.organization_id
        client.update_issuer(issuer_name, organization_id=organization_id)
# endregion


# region private_link
def _verify_vault_or_hsm_name(vault_name, hsm_name):
    if not vault_name and not hsm_name:
        raise RequiredArgumentMissingError('Please specify --vault-name or --hsm-name.')


def list_private_link_resource(cmd, client, resource_group_name, vault_name=None, hsm_name=None):
    _verify_vault_or_hsm_name(vault_name, hsm_name)

    if vault_name:
        return client.list_by_vault(resource_group_name=resource_group_name, vault_name=vault_name)

    hsm_plr_client = get_client_factory(ResourceType.MGMT_KEYVAULT,
                                        Clients.mhsm_private_link_resources)(cmd.cli_ctx, None)
    return hsm_plr_client.list_by_mhsm_resource(resource_group_name=resource_group_name, name=hsm_name)
# endregion


# region private_endpoint
def _update_private_endpoint_connection_status(cmd, client, resource_group_name, name,
                                               private_endpoint_connection_name, is_approved=True, description=None,
                                               no_wait=False):
    PrivateEndpointServiceConnectionStatus = cmd.get_models('PrivateEndpointServiceConnectionStatus',
                                                            resource_type=ResourceType.MGMT_KEYVAULT)

    connection = client.get(resource_group_name, name, private_endpoint_connection_name)

    new_status = PrivateEndpointServiceConnectionStatus.approved \
        if is_approved else PrivateEndpointServiceConnectionStatus.rejected
    connection.private_link_service_connection_state.status = new_status
    connection.private_link_service_connection_state.description = description

    retval = client.put(resource_group_name, name, private_endpoint_connection_name, connection)

    if no_wait:
        return retval

    new_retval = \
        _wait_private_link_operation(client, resource_group_name, name, private_endpoint_connection_name)

    if new_retval:
        return new_retval
    return retval


def _wait_private_link_operation(client, resource_group_name, name, private_endpoint_connection_name):
    retries = 0
    max_retries = 10
    wait_second = 1
    while retries < max_retries:
        pl = client.get(resource_group_name, name, private_endpoint_connection_name)

        if pl.provisioning_state == 'Succeeded':
            return pl
        time.sleep(wait_second)
        retries += 1

    return None


def _get_vault_or_hsm_pec_client(cmd, client, vault_name, hsm_name):
    _verify_vault_or_hsm_name(vault_name, hsm_name)
    if vault_name:
        return client
    return get_client_factory(ResourceType.MGMT_KEYVAULT, Clients.mhsm_private_endpoint_connections)(cmd.cli_ctx, None)


def approve_private_endpoint_connection(cmd, client, resource_group_name, private_endpoint_connection_name,
                                        vault_name=None, hsm_name=None, description=None, no_wait=False):
    """Approve a private endpoint connection request for a Key Vault."""
    pec_client = _get_vault_or_hsm_pec_client(cmd, client, vault_name, hsm_name)
    return _update_private_endpoint_connection_status(cmd, pec_client, resource_group_name,
                                                      vault_name or hsm_name, private_endpoint_connection_name,
                                                      is_approved=True, description=description, no_wait=no_wait)


def reject_private_endpoint_connection(cmd, client, resource_group_name, private_endpoint_connection_name,
                                       vault_name=None, hsm_name=None, description=None, no_wait=False):
    """Reject a private endpoint connection request for a Key Vault."""
    pec_client = _get_vault_or_hsm_pec_client(cmd, client, vault_name, hsm_name)
    return _update_private_endpoint_connection_status(cmd, pec_client, resource_group_name,
                                                      vault_name or hsm_name, private_endpoint_connection_name,
                                                      is_approved=False, description=description, no_wait=no_wait)


def delete_private_endpoint_connection(cmd, client, resource_group_name, private_endpoint_connection_name,
                                       vault_name=None, hsm_name=None):
    pec_client = _get_vault_or_hsm_pec_client(cmd, client, vault_name, hsm_name)
    return pec_client.begin_delete(resource_group_name,
                                   vault_name or hsm_name,
                                   private_endpoint_connection_name)


def list_private_endpoint_connection(cmd, client, resource_group_name, hsm_name):
    pec_client = _get_vault_or_hsm_pec_client(cmd, client, None, hsm_name)
    return pec_client.list_by_resource(resource_group_name, hsm_name)


def show_private_endpoint_connection(cmd, client, resource_group_name, private_endpoint_connection_name,
                                     vault_name=None, hsm_name=None):
    pec_client = _get_vault_or_hsm_pec_client(cmd, client, vault_name, hsm_name)
    return pec_client.get(resource_group_name,
                          vault_name or hsm_name,
                          private_endpoint_connection_name)
# endregion


# region role
def _is_guid(guid):
    try:
        uuid.UUID(guid)
        return True
    except ValueError:
        return False


def _resolve_role_id(client, role, scope):
    role_id = None
    if re.match(r'Microsoft.KeyVault/providers/Microsoft.Authorization/roleDefinitions/.+', role, re.I):
        last_part = role.split('/')[-1]
        if _is_guid(last_part):
            role_id = role
    elif _is_guid(role):
        role_id = 'Microsoft.KeyVault/providers/Microsoft.Authorization/roleDefinitions/{}'.format(role)
    else:
        all_roles = list_role_definitions(client, scope=scope)
        for _role in all_roles:
            if _role.role_name == role:
                role_id = _role.id
                break
    return role_id


def _get_role_dics(role_defs):
    return {i.id: i.role_name for i in role_defs}


def _get_principal_dics(cli_ctx, role_assignments):
    principal_ids = {getattr(i.properties, 'principal_id', None) for i in role_assignments
                     if getattr(i, 'properties', None)}
    if principal_ids:
        from azure.cli.command_modules.role import graph_client_factory, GraphError
        try:
            from azure.cli.command_modules.role.custom import (_get_displayable_name, _get_object_stubs,
                                                               _odata_type_to_arm_principal_type)

            graph_client = graph_client_factory(cli_ctx)
            principals = _get_object_stubs(graph_client, principal_ids)

            results = {}
            for i in principals:
                object_id = i['id']
                display_name = _get_displayable_name(i)
                principal_type = _odata_type_to_arm_principal_type(i['@odata.type'])
                results[object_id] = (display_name, principal_type)
            return results
        except GraphError as ex:
            # failure on resolving principal due to graph permission should not fail the whole thing
            logger.info("Failed to resolve graph object information per error '%s'", ex)

    return {}


def _reconstruct_role_assignment(role_dics, principal_dics, role_assignment):
    ret = {
        'id': role_assignment.role_assignment_id,
        'name': role_assignment.name,
        'scope': role_assignment.properties.scope,
        'type': role_assignment.type
    }
    role_definition_id = getattr(role_assignment.properties, 'role_definition_id', None)\
        if getattr(role_assignment, 'properties', None) else None
    ret['roleDefinitionId'] = role_definition_id
    if role_definition_id:
        ret['roleName'] = role_dics.get(role_definition_id)
    else:
        ret['roleName'] = None  # the role definition might have been deleted

    # fill in principal names
    principal_id = getattr(role_assignment.properties, 'principal_id', None)\
        if getattr(role_assignment, 'properties', None) else None
    ret['principalId'] = principal_id
    if principal_id:
        principal_info = principal_dics.get(principal_id)
        if principal_info:
            ret['principalName'], ret['principalType'] = principal_info
        else:
            ret['principalName'] = ret['principalType'] = 'Unknown'

    return ret


# for injecting test seems to produce predictable role assignment id for playback
def _gen_guid():
    return uuid.uuid4()


# pylint: disable=unused-argument
def create_role_assignment(cmd, client, role, scope, assignee_object_id=None,
                           role_assignment_name=None, assignee=None,
                           assignee_principal_type=None, hsm_name=None, identifier=None):
    """ Create a new role assignment for a user, group, or service principal. """
    from azure.cli.command_modules.role.custom import _resolve_object_id

    if not assignee_object_id and not assignee:
        raise CLIError('Please specify --assignee or --assignee-object-id.')

    if assignee_object_id is None:
        if _is_guid(assignee):
            assignee_object_id = assignee
        else:
            assignee_object_id = _resolve_object_id(cmd.cli_ctx, assignee)

    role_definition_id = _resolve_role_id(client, role=role, scope=scope)
    if not role_definition_id:
        raise CLIError('Unknown role "{}". Please use "az keyvault role definition list" '
                       'to check whether the role is existing.'.format(role))

    if role_assignment_name is None:
        role_assignment_name = str(_gen_guid())

    if scope is None:
        scope = ''

    role_assignment = client.create_role_assignment(
        scope=scope,
        definition_id=role_definition_id,
        principal_id=assignee_object_id,
        name=role_assignment_name,
    )

    role_defs = list_role_definitions(client)
    role_dics = _get_role_dics(role_defs)
    principal_dics = _get_principal_dics(cmd.cli_ctx, [role_assignment])

    return _reconstruct_role_assignment(
        role_dics=role_dics,
        principal_dics=principal_dics,
        role_assignment=role_assignment
    )


# pylint: disable=unused-argument
def delete_role_assignment(cmd, client, role_assignment_name=None, scope=None, assignee=None, role=None,
                           assignee_object_id=None, ids=None, hsm_name=None, identifier=None):
    """ Delete a role assignment. """
    query_scope = scope
    if query_scope is None:
        query_scope = ''

    if ids is not None:
        for cnt_id in ids:
            cnt_name = cnt_id.split('/')[-1]
            client.delete_role_assignment(scope=query_scope, name=cnt_name)
    else:
        if role_assignment_name is not None:
            client.delete_role_assignment(scope=query_scope, name=role_assignment_name)
        else:
            matched_role_assignments = list_role_assignments(
                cmd, client, scope=scope, role=role, assignee_object_id=assignee_object_id, assignee=assignee
            )
            for role_assignment in matched_role_assignments:
                client.delete_role_assignment(scope=query_scope, name=role_assignment.get('name'))


def list_role_assignments(cmd, client, scope=None, assignee=None, role=None, assignee_object_id=None,
                          hsm_name=None, identifier=None):  # pylint: disable=unused-argument
    """ List role assignments. """
    from azure.cli.command_modules.role.custom import _resolve_object_id

    if assignee_object_id is None and assignee is not None:
        assignee_object_id = _resolve_object_id(cmd.cli_ctx, assignee)

    query_scope = scope
    if query_scope is None:
        query_scope = ''

    role_definition_id = None
    if role is not None:
        role_definition_id = _resolve_role_id(client, role=role, scope=query_scope)

    all_role_assignments = client.list_role_assignments(scope=query_scope)
    matched_role_assignments = []
    for role_assignment in all_role_assignments:
        if role_definition_id is not None:
            if role_assignment.properties.role_definition_id != role_definition_id:
                continue
        if scope is not None:
            cnt_scope = role_assignment.properties.scope
            if cnt_scope not in [scope, '/' + scope]:
                continue
        if assignee_object_id is not None:
            if role_assignment.properties.principal_id != assignee_object_id:
                continue
        matched_role_assignments.append(role_assignment)

    role_defs = list_role_definitions(client)
    role_dics = _get_role_dics(role_defs)
    principal_dics = _get_principal_dics(cmd.cli_ctx, matched_role_assignments)

    ret = []
    for i in matched_role_assignments:
        ret.append(_reconstruct_role_assignment(
            role_dics=role_dics,
            principal_dics=principal_dics,
            role_assignment=i
        ))

    return ret


def list_role_definitions(client, scope=None, hsm_name=None, custom_role_only=False):  # pylint: disable=unused-argument
    """ List role definitions. """
    query_scope = scope
    if query_scope is None:
        query_scope = ''
    role_definitions = client.list_role_definitions(scope=query_scope)
    if custom_role_only:
        role_definitions = [role for role in role_definitions if role.role_type == 'CustomRole']
    return role_definitions


def create_role_definition(client, hsm_name, role_definition):  # pylint: disable=unused-argument
    return _create_update_role_definition(client, role_definition, for_update=False)


def update_role_definition(client, hsm_name, role_definition):  # pylint: disable=unused-argument
    return _create_update_role_definition(client, role_definition, for_update=True)


def _create_update_role_definition(client, role_definition, for_update):
    from azure.cli.core.util import get_file_json, shell_safe_json_parse
    from azure.keyvault.administration import KeyVaultPermission

    if os.path.exists(role_definition):
        role_definition = get_file_json(role_definition)
    else:
        role_definition = shell_safe_json_parse(role_definition)

    if not isinstance(role_definition, dict):
        raise InvalidArgumentValueError('Invalid role definition. A valid dictionary JSON representation is expected.')
    # to workaround service defects, ensure property names are camel case
    # e.g. NotActions -> notActions
    names = [p for p in role_definition if p[:1].isupper()]
    for n in names:
        new_name = n[:1].lower() + n[1:]
        role_definition[new_name] = role_definition.pop(n)

    role_scope = '/'  # Managed HSM only supports '/'
    role_definition_name = None
    role_name = role_definition.get('roleName', None)
    description = role_definition.get('description', None)
    permissions = [KeyVaultPermission(
        actions=role_definition.get('actions', None),
        not_actions=role_definition.get('notActions', None),
        data_actions=role_definition.get('dataActions', None),
        not_data_actions=role_definition.get('notDataActions', None)
    )]

    if for_update:
        role_definition_name = role_definition.get('name', None)
        role_id = role_definition.get('id', None)

        if role_definition_name is None and role_id is None:
            raise InvalidArgumentValueError('Please provide "name" or "id" property in'
                                            ' your role definition JSON content.')

        role_definition_name = _get_role_definition_name(role_definition_name, role_id)

    result_role_definition = client.set_role_definition(
        scope=role_scope,
        permissions=permissions,
        name=role_definition_name,
        role_name=role_name,
        description=description
    )

    return result_role_definition


def _get_role_definition_name(role_definition_name, role_id):
    if role_definition_name is None and role_id is None:
        raise InvalidArgumentValueError('Please specify either --role-definition-name or --role-id.')

    if role_definition_name is None:
        if '/' not in role_id:
            raise InvalidArgumentValueError('The role resource id is invalid: {}'.format(role_id))
        role_definition_name = role_id.split('/')[-1]

    return role_definition_name


# pylint: disable=unused-argument
def delete_role_definition(client, hsm_name, role_definition_name=None, role_id=None):
    # Get role definition name
    role_definition_name = _get_role_definition_name(role_definition_name, role_id)

    role_scope = '/'  # Managed HSM only supports '/'
    client.delete_role_definition(role_scope, role_definition_name)


def show_role_definition(client, hsm_name, role_definition_name=None, role_id=None):  # pylint: disable=unused-argument
    # Get role definition name
    role_definition_name = _get_role_definition_name(role_definition_name, role_id)

    role_scope = '/'  # Managed HSM only supports '/'
    result_role_definition = client.get_role_definition(role_scope, role_definition_name)

    return result_role_definition
# endregion


# region full backup/restore
def construct_storage_uri(endpoint, storage_account_name, blob_container_name):
    return 'https://{}.blob.{}/{}'.format(storage_account_name, endpoint, blob_container_name)


def storage_account_parameters_check(storage_resource_uri, storage_account_name, blob_container_name):
    if storage_resource_uri and any([storage_account_name, blob_container_name]):
        raise MutuallyExclusiveArgumentError('Please do not specify --storage-account-name or --blob-container-name '
                                             'if --storage-resource-uri is specified.')
    if not storage_resource_uri:
        if not storage_account_name:
            raise RequiredArgumentMissingError('Please specify --storage-account-name')
        if not blob_container_name:
            raise RequiredArgumentMissingError('Please specify --blob-container-name')

    if not storage_resource_uri and not any([storage_account_name, blob_container_name]):
        raise RequiredArgumentMissingError('Please specify --storage-resource-uri or '
                                           '--storage-account-name & --blob-container-name')


def full_backup(cmd, client, storage_resource_uri=None, storage_account_name=None, blob_container_name=None,
                token=None, use_managed_identity=None, hsm_name=None):  # pylint: disable=unused-argument
    storage_account_parameters_check(storage_resource_uri, storage_account_name, blob_container_name)
    if not storage_resource_uri:
        storage_resource_uri = construct_storage_uri(
            cmd.cli_ctx.cloud.suffixes.storage_endpoint, storage_account_name, blob_container_name)
    poller = client.begin_backup(storage_resource_uri, sas_token=token, use_managed_identity=use_managed_identity)
    result = todict(poller.result())
    result['status'] = poller.status()
    return result


def full_restore(cmd, client, folder_to_restore,
                 storage_resource_uri=None, storage_account_name=None, blob_container_name=None,
                 token=None, use_managed_identity=None, key_name=None, hsm_name=None):  # pylint: disable=unused-argument
    storage_account_parameters_check(storage_resource_uri, storage_account_name, blob_container_name)
    if not storage_resource_uri:
        storage_resource_uri = construct_storage_uri(
            cmd.cli_ctx.cloud.suffixes.storage_endpoint, storage_account_name, blob_container_name)
    folder_url = '{}/{}'.format(storage_resource_uri, folder_to_restore)
    return client.begin_restore(folder_url, sas_token=token, key_name=key_name,
                                use_managed_identity=use_managed_identity)
# endregion


# region security domain
def security_domain_init_recovery(client, sd_exchange_key):
    if os.path.exists(sd_exchange_key):
        raise CLIError("File named '{}' already exists.".format(sd_exchange_key))

    ret = client.get_transfer_key()
    exchange_key = json.loads(ret['transfer_key'])

    def get_x5c_as_pem():
        x5c = exchange_key.get('x5c', [])
        if not x5c:
            raise CLIError('Insufficient x5c.')
        b64cert = x5c[0]
        header = '-----BEGIN CERTIFICATE-----'
        footer = '-----END CERTIFICATE-----'
        pem = [header]
        for i in range(0, len(b64cert), 65):
            line_len = min(65, len(b64cert) - i)
            line = b64cert[i: i + line_len]
            pem.append(line)
        pem.append(footer)
        return '\n'.join(pem)

    try:
        with open(sd_exchange_key, 'w') as f:
            f.write(get_x5c_as_pem())
    except Exception as ex:  # pylint: disable=broad-except
        if os.path.isfile(sd_exchange_key):
            os.remove(sd_exchange_key)
        raise ex


def _wait_security_domain_operation(client, target_operation='upload'):
    retries = 0
    max_retries = 30
    wait_second = 5
    while retries < max_retries:
        try:
            ret = None
            if target_operation == 'upload':
                ret = client.get_upload_status()
            elif target_operation == 'download':
                ret = client.get_download_status()

            # v7.2-preview and v7.2 will change the upload operation from Sync to Async
            # due to service defects, it returns 'Succeeded' before the change and 'Success' after the change
            if ret and getattr(ret, 'status', None) in ['Succeeded', 'Success', 'Failed']:
                return ret
        except:  # pylint: disable=bare-except
            pass
        time.sleep(wait_second)
        retries += 1

    return None


def _security_domain_make_restore_blob(sd_wrapping_keys, passwords, sd_exchange_key, enc_data, shared_keys, required):
    share_arrays = _security_domain_gen_share_arrays(sd_wrapping_keys, passwords, shared_keys, required)
    return _security_domain_gen_blob(sd_exchange_key, share_arrays, enc_data, required)


def _security_domain_gen_share_arrays(sd_wrapping_keys, passwords, shared_keys, required):
    matched = 0
    share_arrays = []
    ok = False

    for private_key_index, private_key_path in enumerate(sd_wrapping_keys):
        if ok:
            break
        if not os.path.exists(private_key_path):
            raise CLIError('SD wrapping key {} does not exist.'.format(private_key_path))
        if os.path.isdir(private_key_path):
            raise CLIError('{} is a directory. A file is required.'.format(private_key_path))

        prefix = '.'.join(private_key_path.split('.')[:-1])
        cert_path = prefix + '.cer'
        if not os.path.exists(cert_path):
            raise CLIError('Certificate {} does not exist. You should put it into the same folder with your wrapping '
                           'keys'.format(cert_path))

        with open(private_key_path, 'rb') as f:
            pem_data = f.read()
            password = passwords[private_key_index] if private_key_index < len(passwords) else None
            if password and not isinstance(password, bytes):
                password = password.encode(encoding="utf-8")
            private_key = load_pem_private_key(pem_data, password=password, backend=default_backend())

        with open(cert_path, 'rb') as f:
            pem_data = f.read()
            cert = load_pem_x509_certificate(pem_data, backend=default_backend())
            public_bytes = cert.public_bytes(Encoding.DER)
            x5tS256 = Utils.security_domain_b64_url_encode(hashlib.sha256(public_bytes).digest())
            for item in shared_keys['enc_shares']:
                if x5tS256 == item['x5t_256']:
                    jwe = JWE(compact_jwe=item['enc_key'])
                    share = jwe.decrypt_using_private_key(private_key)
                    if not share:
                        continue

                    share_arrays.append(Utils.convert_to_uint16(share))
                    matched += 1
                    if matched >= required:
                        ok = True
                        break

    if matched < required:
        raise CLIError('Insufficient shares available.')

    return share_arrays


def _security_domain_gen_blob(sd_exchange_key, share_arrays, enc_data, required):
    master_key = SharedSecret.get_plaintext(share_arrays, required=required)

    plaintext_list = []
    for item in enc_data['data']:
        compact_jwe = item['compact_jwe']
        tag = item['tag']
        enc_key = KDF.sp800_108(master_key, label=tag, context='', bit_length=512)
        jwe_data = JWE(compact_jwe)
        plaintext = jwe_data.decrypt_using_bytes(enc_key)
        plaintext_list.append((plaintext, tag))

    # encrypt
    security_domain_restore_data = SecurityDomainRestoreData()
    security_domain_restore_data.enc_data.kdf = 'sp108_kdf'
    master_key = Utils.get_random(32)

    for plaintext, tag in plaintext_list:
        enc_key = KDF.sp800_108(master_key, label=tag, context='', bit_length=512)
        jwe = JWE()
        jwe.encrypt_using_bytes(enc_key, plaintext, alg_id='A256CBC-HS512', kid=tag)
        datum = Datum(compact_jwe=jwe.encode_compact(), tag=tag)
        security_domain_restore_data.enc_data.data.append(datum)

    with open(sd_exchange_key, 'rb') as f:
        pem_data = f.read()
        exchange_cert = load_pem_x509_certificate(pem_data, backend=default_backend())

    # make the wrapped key
    jwe_wrapped = JWE()
    jwe_wrapped.encrypt_using_cert(exchange_cert, master_key)
    security_domain_restore_data.wrapped_key.enc_key = jwe_wrapped.encode_compact()
    thumbprint = Utils.get_SHA256_thumbprint(exchange_cert)
    security_domain_restore_data.wrapped_key.x5t_256 = Utils.security_domain_b64_url_encode(thumbprint)
    return json.dumps(security_domain_restore_data.to_json())


def _security_domain_restore_blob(sd_file, sd_exchange_key, sd_wrapping_keys, passwords=None):

    if not sd_exchange_key:
        raise RequiredArgumentMissingError('Please specify --sd-exchange-key')
    if not sd_wrapping_keys:
        raise RequiredArgumentMissingError('Please specify --sd-wrapping-keys')

    resource_paths = [sd_file, sd_exchange_key]
    for p in resource_paths:
        if not os.path.exists(p):
            raise CLIError('File {} does not exist.'.format(p))
        if os.path.isdir(p):
            raise CLIError('{} is a directory. A file is required.'.format(p))

    with open(sd_file) as f:
        sd_data = json.load(f)
        if not sd_data or 'EncData' not in sd_data or 'SharedKeys' not in sd_data:
            raise CLIError('Invalid SD file.')
        enc_data = sd_data['EncData']
        shared_keys = sd_data['SharedKeys']

    required = shared_keys['required']
    if required < 2 or required > 10:
        raise CLIError('Invalid SD file: the value of "required" should be in range [2, 10].')
    if len(sd_wrapping_keys) < required:
        raise CLIError('Length of --sd-wrapping-keys list should not less than {} for decrypting this SD file.'
                       .format(required))

    key_algorithm = shared_keys['key_algorithm']
    if key_algorithm != 'shamir_share':
        raise CLIError('Unsupported SharedKeys algorithm: {}. Supported: {}'.format(key_algorithm, 'shamir_share'))

    if passwords is None:
        passwords = []

    restore_blob_value = _security_domain_make_restore_blob(
        sd_wrapping_keys=sd_wrapping_keys,
        passwords=passwords,
        sd_exchange_key=sd_exchange_key,
        enc_data=enc_data,
        shared_keys=shared_keys,
        required=required
    )
    return restore_blob_value


def _security_domain_upload_blob(client, restore_blob_value, no_wait=False):
    security_domain = {'value': restore_blob_value}
    poller = client.begin_upload(security_domain=security_domain, skip_activation_polling=no_wait)
    poller.result()
    return client.get_upload_status()


def security_domain_upload(client, sd_file, restore_blob=False, sd_exchange_key=None,
                           sd_wrapping_keys=None, passwords=None, no_wait=False):
    if not restore_blob:
        restore_blob_value = _security_domain_restore_blob(sd_file, sd_exchange_key, sd_wrapping_keys, passwords)
    else:
        with open(sd_file, 'r') as f:
            restore_blob_value = f.read()
            if not restore_blob_value:
                raise CLIError('Empty restore_blob_value.')
    retval = _security_domain_upload_blob(client, restore_blob_value, no_wait)
    return retval


def security_domain_restore_blob(sd_file, sd_exchange_key, sd_wrapping_keys, sd_file_restore_blob,
                                 passwords=None):  # pylint: disable=unused-argument
    restore_blob_value = _security_domain_restore_blob(sd_file, sd_exchange_key, sd_wrapping_keys,
                                                       passwords)
    try:
        with open(sd_file_restore_blob, 'w') as f:
            f.write(restore_blob_value)
    except Exception as ex:  # pylint: disable=broad-except
        if os.path.isfile(sd_file_restore_blob):
            os.remove(sd_file_restore_blob)
        raise ex


def security_domain_download(client, sd_wrapping_keys, security_domain_file, sd_quorum, no_wait=False):
    if os.path.exists(security_domain_file):
        raise CLIError("File named '{}' already exists.".format(security_domain_file))

    for path in sd_wrapping_keys:
        if os.path.isdir(path):
            raise CLIError('{} is a directory. A file is required.'.format(path))

    N = len(sd_wrapping_keys)
    M = sd_quorum
    if N < 3 or N > 10:
        raise CLIError('The number of wrapping keys (N) should be in range [3, 10].')
    if M < 2 or M > 10:
        raise CLIError('The quorum of security domain (M) should be in range [2, 10].')

    certificates = []
    for path in sd_wrapping_keys:
        sd_jwk = {}
        with open(path, 'rb') as f:
            pem_data = f.read()

        cert = load_pem_x509_certificate(pem_data, backend=default_backend())
        public_key = cert.public_key()
        public_bytes = cert.public_bytes(Encoding.DER)
        sd_jwk['x5c'] = [Utils.security_domain_b64_url_encode_for_x5c(public_bytes)]  # only one cert, not a chain
        sd_jwk['x5t'] = Utils.security_domain_b64_url_encode(hashlib.sha1(public_bytes).digest())
        sd_jwk['x5t#S256'] = Utils.security_domain_b64_url_encode(hashlib.sha256(public_bytes).digest())
        sd_jwk['key_ops'] = ['verify', 'encrypt', 'wrapKey']

        # populate key into jwk
        if isinstance(public_key, rsa.RSAPublicKey) and public_key.key_size >= 2048:
            sd_jwk['kty'] = 'RSA'
            sd_jwk['alg'] = 'RSA-OAEP-256'
            _public_rsa_key_to_jwk(public_key, sd_jwk, encoding=Utils.security_domain_b64_url_encode)
        else:
            raise CLIError('Only RSA >= 2048 is supported.')

        certificates.append(sd_jwk)

    # save security-domain backup value to local file
    def _save_to_local_file(file_path, security_domain):
        try:
            with open(file_path, 'w') as f:
                f.write(security_domain.value)
        except Exception as ex:  # pylint: disable=bare-except
            if os.path.isfile(file_path):
                os.remove(file_path)
            from azure.cli.core.azclierror import FileOperationError
            raise FileOperationError(str(ex))

    certificate_info = {'certificates': certificates, 'required': sd_quorum}
    poller = client.begin_download(certificate_info=certificate_info, skip_activation_polling=no_wait)
    security_domain = poller.result()
    if poller.status() != 'Failed':
        _save_to_local_file(security_domain_file, security_domain)
    if not no_wait:
        return client.get_download_status()


def check_name_availability(cmd, client, name, resource_type='hsm'):
    CheckNameAvailabilityParameters = cmd.get_models('CheckMhsmNameAvailabilityParameters')
    check_name = CheckNameAvailabilityParameters(name=name)
    return client.check_mhsm_name_availability(check_name)
# endregion


# region mhsm regions
def add_hsm_region(cmd, client, resource_group_name, name, region_name, no_wait=False):
    MHSMGeoReplicatedRegion = cmd.get_models('MHSMGeoReplicatedRegion', resource_type=ResourceType.MGMT_KEYVAULT)

    hsm = client.get(resource_group_name=resource_group_name, name=name)
    existing_regions = hsm.properties.regions or []
    for existing_region in existing_regions:
        if region_name == existing_region.name:
            logger.warning("%s has already existed", region_name)
            return hsm
    existing_regions.append(MHSMGeoReplicatedRegion(name=region_name))
    hsm.properties.regions = existing_regions
    return sdk_no_wait(no_wait, client.begin_update,
                       resource_group_name=resource_group_name,
                       name=name,
                       parameters=hsm)


def remove_hsm_region(client, resource_group_name, name, region_name, no_wait=False):
    hsm = client.get(resource_group_name=resource_group_name, name=name)
    existing_regions = hsm.properties.regions or []
    for existing_region in existing_regions:
        if region_name == existing_region.name:
            existing_regions.remove(existing_region)
            hsm.properties.regions = existing_regions
            return sdk_no_wait(no_wait, client.begin_update,
                               resource_group_name=resource_group_name,
                               name=name, parameters=hsm)
    logger.warning("%s doesn't exist", region_name)
    return hsm
# endregion


# region mhsm settings
def update_hsm_setting(client, name, value, setting_type=None):
    # TODO: remove this additional call to `get_setting` after SDK fix the auth issue for `update_setting`
    # TODO: For now, we need to call `get_setting` first to make sure client has set credential correctly
    client.get_setting(name=name)
    from azure.keyvault.administration import KeyVaultSetting
    setting = KeyVaultSetting(name=name, value=value, setting_type=setting_type)
    return client.update_setting(setting)
# endregion


# region secret
def list_secret(client, **kwargs):
    include_managed = kwargs.pop('include_managed', None)
    result = client.list_properties_of_secrets(**kwargs)
    kwargs.update({
        "include_managed": include_managed
    })
    return result

# endregion


def set_attributes_certificate(client, certificate_name, version=None, policy=None, **kwargs):
    if policy:
        client.update_certificate_policy(certificate_name=certificate_name, policy=policy)
    if kwargs.get('enabled') is not None or kwargs.get('tags') is not None:
        return client.update_certificate_properties(certificate_name=certificate_name, version=version, **kwargs)
    return client.get_certificate(certificate_name=certificate_name)
