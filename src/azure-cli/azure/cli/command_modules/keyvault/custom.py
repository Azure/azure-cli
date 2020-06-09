# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
import codecs
import json
import math
import os
import time
import struct


from knack.log import get_logger
from knack.util import CLIError

from OpenSSL import crypto
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives.serialization import load_pem_private_key, Encoding, PublicFormat
from cryptography.exceptions import UnsupportedAlgorithm


from azure.cli.core import telemetry
from azure.cli.core.profiles import ResourceType

from ._validators import _construct_vnet, secret_text_encoding_values

logger = get_logger(__name__)


def _default_certificate_profile(cmd):

    Action = cmd.get_models('Action', resource_type=ResourceType.DATA_KEYVAULT)
    ActionType = cmd.get_models('ActionType', resource_type=ResourceType.DATA_KEYVAULT)
    KeyUsageType = cmd.get_models('KeyUsageType', resource_type=ResourceType.DATA_KEYVAULT)
    CertificateAttributes = cmd.get_models('CertificateAttributes', resource_type=ResourceType.DATA_KEYVAULT)
    CertificatePolicy = cmd.get_models('CertificatePolicy', resource_type=ResourceType.DATA_KEYVAULT)
    IssuerParameters = cmd.get_models('IssuerParameters', resource_type=ResourceType.DATA_KEYVAULT)
    KeyProperties = cmd.get_models('KeyProperties', resource_type=ResourceType.DATA_KEYVAULT)
    LifetimeAction = cmd.get_models('LifetimeAction', resource_type=ResourceType.DATA_KEYVAULT)
    SecretProperties = cmd.get_models('SecretProperties', resource_type=ResourceType.DATA_KEYVAULT)
    X509CertificateProperties = cmd.get_models('X509CertificateProperties', resource_type=ResourceType.DATA_KEYVAULT)
    Trigger = cmd.get_models('Trigger', resource_type=ResourceType.DATA_KEYVAULT)

    template = CertificatePolicy(
        key_properties=KeyProperties(
            exportable=True,
            key_type=u'RSA',
            key_size=2048,
            reuse_key=True
        ),
        secret_properties=SecretProperties(
            content_type=u'application/x-pkcs12'
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
            subject=u'CN=CLIGetDefaultPolicy',
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
            name=u'Self',
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
    Action = cmd.get_models('Action', resource_type=ResourceType.DATA_KEYVAULT)
    ActionType = cmd.get_models('ActionType', resource_type=ResourceType.DATA_KEYVAULT)
    KeyUsageType = cmd.get_models('KeyUsageType', resource_type=ResourceType.DATA_KEYVAULT)
    CertificateAttributes = cmd.get_models('CertificateAttributes', resource_type=ResourceType.DATA_KEYVAULT)
    CertificatePolicy = cmd.get_models('CertificatePolicy', resource_type=ResourceType.DATA_KEYVAULT)
    IssuerParameters = cmd.get_models('IssuerParameters', resource_type=ResourceType.DATA_KEYVAULT)
    KeyProperties = cmd.get_models('KeyProperties', resource_type=ResourceType.DATA_KEYVAULT)
    LifetimeAction = cmd.get_models('LifetimeAction', resource_type=ResourceType.DATA_KEYVAULT)
    SecretProperties = cmd.get_models('SecretProperties', resource_type=ResourceType.DATA_KEYVAULT)
    X509CertificateProperties = cmd.get_models('X509CertificateProperties', resource_type=ResourceType.DATA_KEYVAULT)
    SubjectAlternativeNames = cmd.get_models('SubjectAlternativeNames', resource_type=ResourceType.DATA_KEYVAULT)
    Trigger = cmd.get_models('Trigger', resource_type=ResourceType.DATA_KEYVAULT)

    template = CertificatePolicy(
        key_properties=KeyProperties(
            exportable=True,
            key_type=u'(optional) RSA or RSA-HSM (default RSA)',
            key_size=2048,
            reuse_key=True
        ),
        secret_properties=SecretProperties(
            content_type=u'application/x-pkcs12 or application/x-pem-file'
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
                emails=[u'hello@contoso.com'],
                dns_names=[u'hr.contoso.com', u'm.contoso.com'],
                upns=[]
            ),
            subject=u'C=US, ST=WA, L=Redmond, O=Contoso, OU=Contoso HR, CN=www.contoso.com',
            ekus=[u'1.3.6.1.5.5.7.3.1'],
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
            name=u'Unknown, Self, or {IssuerName}',
            certificate_type=u'(optional) DigiCert, GlobalSign or WoSign'
        ),
        attributes=CertificateAttributes(
            enabled=True
        )
    )
    del template.id
    del template.attributes
    return template


def list_keyvault(client, resource_group_name=None):
    vault_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list(vault_list)


# pylint: disable=inconsistent-return-statements
def _get_current_user_object_id(graph_client):
    from msrestazure.azure_exceptions import CloudError
    try:
        current_user = graph_client.signed_in_user.get()
        if current_user and current_user.object_id:  # pylint:disable=no-member
            return current_user.object_id  # pylint:disable=no-member
    except CloudError:
        pass


def _get_object_id_by_spn(graph_client, spn):
    accounts = list(graph_client.service_principals.list(
        filter="servicePrincipalNames/any(c:c eq '{}')".format(spn)))
    if not accounts:
        logger.warning("Unable to find user with spn '%s'", spn)
        return None
    if len(accounts) > 1:
        logger.warning("Multiple service principals found with spn '%s'. "
                       "You can avoid this by specifying object id.", spn)
        return None
    return accounts[0].object_id


def _get_object_id_by_upn(graph_client, upn):
    accounts = list(graph_client.users.list(filter="userPrincipalName eq '{}'".format(upn)))
    if not accounts:
        logger.warning("Unable to find user with upn '%s'", upn)
        return None
    if len(accounts) > 1:
        logger.warning("Multiple users principals found with upn '%s'. "
                       "You can avoid this by specifying object id.", upn)
        return None
    return accounts[0].object_id


def _get_object_id_from_subscription(graph_client, subscription):
    if not subscription:
        return None

    if subscription['user']:
        if subscription['user']['type'] == 'user':
            return _get_object_id_by_upn(graph_client, subscription['user']['name'])
        if subscription['user']['type'] == 'servicePrincipal':
            return _get_object_id_by_spn(graph_client, subscription['user']['name'])
        logger.warning("Unknown user type '%s'", subscription['user']['type'])
    else:
        logger.warning('Current credentials are not from a user or service principal. '
                       'Azure Key Vault does not work with certificate credentials.')
    return None


def _get_object_id(graph_client, subscription=None, spn=None, upn=None):
    if spn:
        return _get_object_id_by_spn(graph_client, spn)
    if upn:
        return _get_object_id_by_upn(graph_client, upn)
    return _get_object_id_from_subscription(graph_client, subscription)


def _create_network_rule_set(cmd, bypass=None, default_action=None):
    NetworkRuleSet = cmd.get_models('NetworkRuleSet', resource_type=ResourceType.MGMT_KEYVAULT)
    NetworkRuleBypassOptions = cmd.get_models('NetworkRuleBypassOptions', resource_type=ResourceType.MGMT_KEYVAULT)
    NetworkRuleAction = cmd.get_models('NetworkRuleAction', resource_type=ResourceType.MGMT_KEYVAULT)

    return NetworkRuleSet(bypass=bypass or NetworkRuleBypassOptions.azure_services.value,
                          default_action=default_action or NetworkRuleAction.allow.value)


# region KeyVault Vault
def get_default_policy(cmd, client, scaffold=False):  # pylint: disable=unused-argument
    """
    Get a default certificate policy to be used with `az keyvault certificate create`
    :param client:
    :param bool scaffold: create a fully formed policy structure with default values
    :return: policy dict
    :rtype: dict
    """
    return _scaffold_certificate_profile(cmd) if scaffold else _default_certificate_profile(cmd)


def recover_keyvault(cmd, client, vault_name, resource_group_name, location):
    from azure.cli.core._profile import Profile

    VaultCreateOrUpdateParameters = cmd.get_models('VaultCreateOrUpdateParameters',
                                                   resource_type=ResourceType.MGMT_KEYVAULT)
    CreateMode = cmd.get_models('CreateMode', resource_type=ResourceType.MGMT_KEYVAULT)

    # tenantId and sku shouldn't be required
    Sku = cmd.get_models('Sku', resource_type=ResourceType.MGMT_KEYVAULT)
    SkuName = cmd.get_models('SkuName', resource_type=ResourceType.MGMT_KEYVAULT)
    profile = Profile(cli_ctx=cmd.cli_ctx)
    _, _, tenant_id = profile.get_login_credentials(
        resource=cmd.cli_ctx.cloud.endpoints.active_directory_graph_resource_id)

    params = VaultCreateOrUpdateParameters(location=location,
                                           properties={'tenant_id': tenant_id,
                                                       'sku': Sku(name=SkuName.standard.value),
                                                       'create_mode': CreateMode.recover.value})

    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=params)


def _parse_network_acls(cmd, resource_group_name, network_acls_json, network_acls_ips, network_acls_vnets):
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

    network_acls = _create_network_rule_set(cmd)

    from msrestazure.tools import is_valid_resource_id

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


def create_keyvault(cmd, client,  # pylint: disable=too-many-locals
                    resource_group_name, vault_name, location=None, sku=None,
                    enabled_for_deployment=None,
                    enabled_for_disk_encryption=None,
                    enabled_for_template_deployment=None,
                    enable_rbac_authorization=None,
                    enable_soft_delete=None,
                    enable_purge_protection=None,
                    retention_days=None,
                    network_acls=None,
                    network_acls_ips=None,
                    network_acls_vnets=None,
                    bypass=None,
                    default_action=None,
                    no_self_perms=None,
                    tags=None):

    from azure.cli.core._profile import Profile
    from azure.graphrbac.models import GraphErrorException
    from azure.graphrbac import GraphRbacManagementClient

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

    profile = Profile(cli_ctx=cmd.cli_ctx)
    cred, _, tenant_id = profile.get_login_credentials(
        resource=cmd.cli_ctx.cloud.endpoints.active_directory_graph_resource_id)

    graph_client = GraphRbacManagementClient(
        cred,
        tenant_id,
        base_url=cmd.cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
    subscription = profile.get_subscription()

    # if bypass or default_action was specified create a NetworkRuleSet
    # if neither were specified we will parse it from parameter `--network-acls`
    if cmd.supported_api_version(resource_type=ResourceType.MGMT_KEYVAULT, min_api='2018-02-14'):
        network_acls = _create_network_rule_set(cmd, bypass, default_action) \
            if bypass or default_action else \
            _parse_network_acls(cmd, resource_group_name, network_acls, network_acls_ips, network_acls_vnets)

    if no_self_perms or enable_rbac_authorization:
        access_policies = []
    else:
        permissions = Permissions(keys=[KeyPermissions.get,
                                        KeyPermissions.create,
                                        KeyPermissions.delete,
                                        KeyPermissions.list,
                                        KeyPermissions.update,
                                        KeyPermissions.import_enum,
                                        KeyPermissions.backup,
                                        KeyPermissions.restore,
                                        KeyPermissions.recover],
                                  secrets=[
                                      SecretPermissions.get,
                                      SecretPermissions.list,
                                      SecretPermissions.set,
                                      SecretPermissions.delete,
                                      SecretPermissions.backup,
                                      SecretPermissions.restore,
                                      SecretPermissions.recover],
                                  certificates=[
                                      CertificatePermissions.get,
                                      CertificatePermissions.list,
                                      CertificatePermissions.delete,
                                      CertificatePermissions.create,
                                      CertificatePermissions.import_enum,
                                      CertificatePermissions.update,
                                      CertificatePermissions.managecontacts,
                                      CertificatePermissions.getissuers,
                                      CertificatePermissions.listissuers,
                                      CertificatePermissions.setissuers,
                                      CertificatePermissions.deleteissuers,
                                      CertificatePermissions.manageissuers,
                                      CertificatePermissions.recover],
                                  storage=[
                                      StoragePermissions.get,
                                      StoragePermissions.list,
                                      StoragePermissions.delete,
                                      StoragePermissions.set,
                                      StoragePermissions.update,
                                      StoragePermissions.regeneratekey,
                                      StoragePermissions.setsas,
                                      StoragePermissions.listsas,
                                      StoragePermissions.getsas,
                                      StoragePermissions.deletesas])
        try:
            object_id = _get_current_user_object_id(graph_client)
        except GraphErrorException:
            object_id = _get_object_id(graph_client, subscription=subscription)
        if not object_id:
            raise CLIError('Cannot create vault.\nUnable to query active directory for information '
                           'about the current user.\nYou may try the --no-self-perms flag to '
                           'create a vault without permissions.')
        access_policies = [AccessPolicyEntry(tenant_id=tenant_id,
                                             object_id=object_id,
                                             permissions=permissions)]

    properties = VaultProperties(tenant_id=tenant_id,
                                 sku=Sku(name=sku),
                                 access_policies=access_policies,
                                 vault_uri=None,
                                 enabled_for_deployment=enabled_for_deployment,
                                 enabled_for_disk_encryption=enabled_for_disk_encryption,
                                 enabled_for_template_deployment=enabled_for_template_deployment,
                                 enable_rbac_authorization=enable_rbac_authorization,
                                 enable_soft_delete=enable_soft_delete,
                                 enable_purge_protection=enable_purge_protection,
                                 soft_delete_retention_in_days=int(retention_days))
    if hasattr(properties, 'network_acls'):
        properties.network_acls = network_acls
    parameters = VaultCreateOrUpdateParameters(location=location,
                                               tags=tags,
                                               properties=properties)
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=parameters)


def update_keyvault_setter(cmd, client, parameters, resource_group_name, vault_name):
    VaultCreateOrUpdateParameters = cmd.get_models('VaultCreateOrUpdateParameters',
                                                   resource_type=ResourceType.MGMT_KEYVAULT)
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=VaultCreateOrUpdateParameters(
                                       location=parameters.location,
                                       properties=parameters.properties))


def update_keyvault(cmd, instance, enabled_for_deployment=None,
                    enabled_for_disk_encryption=None,
                    enabled_for_template_deployment=None,
                    enable_rbac_authorization=None,
                    enable_soft_delete=None,
                    enable_purge_protection=None,
                    retention_days=None,
                    bypass=None,
                    default_action=None,):
    if enabled_for_deployment is not None:
        instance.properties.enabled_for_deployment = enabled_for_deployment

    if enabled_for_disk_encryption is not None:
        instance.properties.enabled_for_disk_encryption = enabled_for_disk_encryption

    if enabled_for_template_deployment is not None:
        instance.properties.enabled_for_template_deployment = enabled_for_template_deployment

    if enable_rbac_authorization is not None:
        instance.properties.enable_rbac_authorization = enable_rbac_authorization

    if enable_soft_delete is not None:
        instance.properties.enable_soft_delete = enable_soft_delete

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
    return instance


def _object_id_args_helper(cli_ctx, object_id, spn, upn):
    if not object_id:
        from azure.cli.core._profile import Profile
        from azure.graphrbac import GraphRbacManagementClient

        profile = Profile(cli_ctx=cli_ctx)
        cred, _, tenant_id = profile.get_login_credentials(
            resource=cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
        graph_client = GraphRbacManagementClient(cred,
                                                 tenant_id,
                                                 base_url=cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
        object_id = _get_object_id(graph_client, spn=spn, upn=upn)
        if not object_id:
            raise CLIError('Unable to get object id from principal name.')
    return object_id


def _permissions_distinct(permissions):
    if permissions:
        return [_ for _ in {p for p in permissions}]
    return permissions


def set_policy(cmd, client, resource_group_name, vault_name,
               object_id=None, spn=None, upn=None, key_permissions=None, secret_permissions=None,
               certificate_permissions=None, storage_permissions=None):
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
                   vault.properties.tenant_id.lower() == p.tenant_id.lower()), None)
    if not policy:
        # Add new policy as none found
        vault.properties.access_policies.append(AccessPolicyEntry(
            tenant_id=vault.properties.tenant_id,
            object_id=object_id,
            permissions=Permissions(keys=key_permissions,
                                    secrets=secret_permissions,
                                    certificates=certificate_permissions,
                                    storage=storage_permissions)))
    else:
        # Modify existing policy.
        # If key_permissions is not set, use prev. value (similarly with secret_permissions).
        keys = policy.permissions.keys if key_permissions is None else key_permissions
        secrets = policy.permissions.secrets if secret_permissions is None else secret_permissions
        certs = policy.permissions.certificates \
            if certificate_permissions is None else certificate_permissions
        storage = policy.permissions.storage if storage_permissions is None else storage_permissions
        policy.permissions = Permissions(keys=keys, secrets=secrets, certificates=certs, storage=storage)
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=VaultCreateOrUpdateParameters(
                                       location=vault.location,
                                       tags=vault.tags,
                                       properties=vault.properties))


def add_network_rule(cmd, client, resource_group_name, vault_name, ip_address=None, subnet=None, vnet_name=None):  # pylint: disable=unused-argument
    """ Add a network rule to the network ACLs for a Key Vault. """

    VirtualNetworkRule = cmd.get_models('VirtualNetworkRule', resource_type=ResourceType.MGMT_KEYVAULT)
    IPRule = cmd.get_models('IPRule', resource_type=ResourceType.MGMT_KEYVAULT)
    VaultCreateOrUpdateParameters = cmd.get_models('VaultCreateOrUpdateParameters',
                                                   resource_type=ResourceType.MGMT_KEYVAULT)
    vault = client.get(resource_group_name=resource_group_name, vault_name=vault_name)
    vault.properties.network_acls = vault.properties.network_acls or _create_network_rule_set(cmd)
    rules = vault.properties.network_acls

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

    if ip_address:
        rules.ip_rules = rules.ip_rules or []
        # if the rule already exists, don't add again
        to_modify = True
        for x in rules.ip_rules:
            if x.value == ip_address:
                to_modify = False
                break
        if to_modify:
            rules.ip_rules.append(IPRule(value=ip_address))

    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=VaultCreateOrUpdateParameters(
                                       location=vault.location,
                                       tags=vault.tags,
                                       properties=vault.properties))


def remove_network_rule(cmd, client, resource_group_name, vault_name, ip_address=None, subnet=None, vnet_name=None):  # pylint: disable=unused-argument
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
        new_rules = [x for x in rules.ip_rules if x.value != ip_address]
        to_modify |= len(new_rules) != len(rules.ip_rules)
        if to_modify:
            rules.ip_rules = new_rules

    # if we didn't modify the network rules just return the vault as is
    if not to_modify:
        return vault

    # otherwise update
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=VaultCreateOrUpdateParameters(
                                       location=vault.location,
                                       tags=vault.tags,
                                       properties=vault.properties))


def list_network_rules(cmd, client, resource_group_name, vault_name):  # pylint: disable=unused-argument
    """ List the network rules from the network ACLs for a Key Vault. """
    vault = client.get(resource_group_name=resource_group_name, vault_name=vault_name)
    return vault.properties.network_acls


def delete_policy(cmd, client, resource_group_name, vault_name, object_id=None, spn=None, upn=None):
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
                                        object_id.lower() != p.object_id.lower()]
    if len(vault.properties.access_policies) == prev_policies_len:
        raise CLIError('No matching policies found')
    return client.create_or_update(resource_group_name=resource_group_name,
                                   vault_name=vault_name,
                                   parameters=VaultCreateOrUpdateParameters(
                                       location=vault.location,
                                       tags=vault.tags,
                                       properties=vault.properties))
# endregion


# region KeyVault Key
def create_key(cmd, client, vault_base_url, key_name, protection=None,  # pylint: disable=unused-argument
               key_size=None, key_ops=None, disabled=False, expires=None,
               not_before=None, tags=None, kty=None, curve=None):
    KeyAttributes = cmd.get_models('KeyAttributes', resource_type=ResourceType.DATA_KEYVAULT)
    key_attrs = KeyAttributes(enabled=not disabled, not_before=not_before, expires=expires)
    return client.create_key(vault_base_url=vault_base_url,
                             key_name=key_name,
                             kty=kty,
                             key_size=key_size,
                             key_ops=key_ops,
                             key_attributes=key_attrs,
                             tags=tags,
                             curve=curve)


def backup_key(client, file_path, vault_base_url=None,
               key_name=None, identifier=None):  # pylint: disable=unused-argument
    backup = client.backup_key(vault_base_url, key_name).value
    with open(file_path, 'wb') as output:
        output.write(backup)


def restore_key(client, vault_base_url, file_path):
    with open(file_path, 'rb') as file_in:
        data = file_in.read()
    return client.restore_key(vault_base_url, data)


def _int_to_bytes(i):
    h = hex(i)
    if len(h) > 1 and h[0:2] == '0x':
        h = h[2:]
    # need to strip L in python 2.x
    h = h.strip('L')
    if len(h) % 2:
        h = '0' + h
    return codecs.decode(h, 'hex')


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


def import_key(cmd, client, vault_base_url, key_name, protection=None, key_ops=None, disabled=False, expires=None,
               not_before=None, tags=None, pem_file=None, pem_password=None, byok_file=None):
    """ Import a private key. Supports importing base64 encoded private keys from PEM files.
        Supports importing BYOK keys into HSM for premium key vaults. """
    KeyAttributes = cmd.get_models('KeyAttributes', resource_type=ResourceType.DATA_KEYVAULT)
    JsonWebKey = cmd.get_models('JsonWebKey', resource_type=ResourceType.DATA_KEYVAULT)

    key_attrs = KeyAttributes(enabled=not disabled, not_before=not_before, expires=expires)
    key_obj = JsonWebKey(key_ops=key_ops)
    if pem_file:
        logger.info('Reading %s', pem_file)
        with open(pem_file, 'rb') as f:
            pem_data = f.read()
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
    elif byok_file:
        with open(byok_file, 'rb') as f:
            byok_data = f.read()
        key_obj.kty = 'RSA-HSM'
        key_obj.t = byok_data

    return client.import_key(vault_base_url, key_name, key_obj, protection == 'hsm', key_attrs, tags)


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


def download_key(client, file_path, vault_base_url=None, key_name=None, key_version='',
                 encoding=None, identifier=None):  # pylint: disable=unused-argument
    """ Download a key from a KeyVault. """
    if os.path.isfile(file_path) or os.path.isdir(file_path):
        raise CLIError("File or directory named '{}' already exists.".format(file_path))

    key = client.get_key(vault_base_url, key_name, key_version)
    json_web_key = _jwk_to_dict(key.key)
    key_type = json_web_key['kty']
    pub_key = ''

    if key_type in ['RSA', 'RSA-HSM']:
        pub_key = _extract_rsa_public_key_from_jwk(json_web_key)
    elif key_type in ['EC', 'EC-HSM']:
        pub_key = _extract_ec_public_key_from_jwk(json_web_key)
    else:
        raise CLIError('Unsupported key type: {}. (Supported key types: RSA, RSA-HSM, EC, EC-HSM)'.format(key_type))

    def _to_der(k):
        return k.public_bytes(
            encoding=Encoding.DER,
            format=PublicFormat.SubjectPublicKeyInfo
        )

    def _to_pem(k):
        # https://github.com/mpdavis/python-jose/blob/eed086d7650ccbd4ea8b555157aff3b1b99f14b9/jose/backends/cryptography_backend.py#L329-L332
        return k.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo
        )

    methods = {
        'DER': _to_der,
        'PEM': _to_pem
    }

    if encoding not in methods.keys():
        raise CLIError('Unsupported encoding: {}. (Supported encodings: DER, PEM)'.format(encoding))

    try:
        with open(file_path, 'wb') as f:
            f.write(methods[encoding](pub_key))
    except Exception as ex:  # pylint: disable=broad-except
        if os.path.isfile(file_path):
            os.remove(file_path)
        raise ex
# endregion


# region KeyVault Secret
def download_secret(client, file_path, vault_base_url=None, secret_name=None, encoding=None,
                    secret_version='', identifier=None):  # pylint: disable=unused-argument
    """ Download a secret from a KeyVault. """
    if os.path.isfile(file_path) or os.path.isdir(file_path):
        raise CLIError("File or directory named '{}' already exists.".format(file_path))

    secret = client.get_secret(vault_base_url, secret_name, secret_version)

    if not encoding:
        encoding = secret.tags.get('file-encoding', 'utf-8') if secret.tags else 'utf-8'

    secret_value = secret.value

    try:
        if encoding in secret_text_encoding_values:
            with open(file_path, 'w') as f:
                f.write(secret_value)
        else:
            if encoding == 'base64':
                import base64
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


def backup_secret(client, file_path, vault_base_url=None,
                  secret_name=None, identifier=None):  # pylint: disable=unused-argument
    backup = client.backup_secret(vault_base_url, secret_name).value
    with open(file_path, 'wb') as output:
        output.write(backup)


def restore_secret(client, vault_base_url, file_path):
    with open(file_path, 'rb') as file_in:
        data = file_in.read()
    return client.restore_secret(vault_base_url, data)
# endregion


# region KeyVault Certificate
# pylint: disable=inconsistent-return-statements
def create_certificate(cmd, client, vault_base_url, certificate_name, certificate_policy,
                       disabled=False, tags=None, validity=None):
    CertificateAttributes = cmd.get_models('CertificateAttributes', resource_type=ResourceType.DATA_KEYVAULT)
    cert_attrs = CertificateAttributes(enabled=not disabled)
    logger.info("Starting long-running operation 'keyvault certificate create'")

    if validity is not None:
        certificate_policy['x509_certificate_properties']['validity_in_months'] = validity

    client.create_certificate(
        vault_base_url, certificate_name, certificate_policy, cert_attrs, tags)

    if certificate_policy['issuer_parameters']['name'].lower() == 'unknown':
        # return immediately for a pending certificate
        return client.get_certificate_operation(vault_base_url, certificate_name)

    # otherwise loop until the certificate creation is complete
    while True:
        check = client.get_certificate_operation(vault_base_url, certificate_name)
        if check.status != 'inProgress':
            logger.info(
                "Long-running operation 'keyvault certificate create' finished with result %s.",
                check)
            return check
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Long-running operation wait cancelled.")
            raise
        except Exception as client_exception:
            telemetry.set_exception(exception=client_exception, fault_type='cert-create-error',
                                    summary='Unexpected client exception during cert creation')
            message = getattr(client_exception, 'message', client_exception)

            try:
                ex_message = json.loads(client_exception.response.text)  # pylint: disable=no-member
                message = str(message) + ' ' + ex_message['error']['details'][0]['message']
            except:  # pylint: disable=bare-except
                pass

            raise CLIError('{}'.format(message))


def _asn1_to_iso8601(asn1_date):
    import dateutil.parser
    if isinstance(asn1_date, bytes):
        asn1_date = asn1_date.decode('utf-8')
    return dateutil.parser.parse(asn1_date)


def import_certificate(cmd, client, vault_base_url, certificate_name, certificate_data,
                       disabled=False, password=None, certificate_policy=None, tags=None):
    import binascii
    CertificateAttributes = cmd.get_models('CertificateAttributes', resource_type=ResourceType.DATA_KEYVAULT)
    SecretProperties = cmd.get_models('SecretProperties', resource_type=ResourceType.DATA_KEYVAULT)
    CertificatePolicy = cmd.get_models('CertificatePolicy', resource_type=ResourceType.DATA_KEYVAULT)
    x509 = None
    content_type = None
    try:
        x509 = crypto.load_certificate(crypto.FILETYPE_PEM, certificate_data)
        # if we get here, we know it was a PEM file
        content_type = 'application/x-pem-file'
        try:
            # for PEM files (including automatic endline conversion for Windows)
            certificate_data = certificate_data.decode('utf-8').replace('\r\n', '\n')
        except UnicodeDecodeError:
            certificate_data = binascii.b2a_base64(certificate_data).decode('utf-8')
    except (ValueError, crypto.Error):
        pass

    if not x509:
        try:
            if password:
                x509 = crypto.load_pkcs12(certificate_data, password).get_certificate()
            else:
                x509 = crypto.load_pkcs12(certificate_data).get_certificate()
            content_type = 'application/x-pkcs12'
            certificate_data = binascii.b2a_base64(certificate_data).decode('utf-8')
        except crypto.Error:
            raise CLIError(
                'We could not parse the provided certificate as .pem or .pfx. Please verify the certificate with OpenSSL.')  # pylint: disable=line-too-long

    not_before, not_after = None, None

    if x509.get_notBefore():
        not_before = _asn1_to_iso8601(x509.get_notBefore())

    if x509.get_notAfter():
        not_after = _asn1_to_iso8601(x509.get_notAfter())

    cert_attrs = CertificateAttributes(
        enabled=not disabled,
        not_before=not_before,
        expires=not_after)

    if certificate_policy:
        secret_props = certificate_policy.get('secret_properties')
        if secret_props:
            secret_props['content_type'] = content_type
        elif certificate_policy and not secret_props:
            certificate_policy['secret_properties'] = SecretProperties(content_type=content_type)

        attributes = certificate_policy.get('attributes')
        if attributes:
            attributes['created'] = None
            attributes['updated'] = None
    else:
        certificate_policy = CertificatePolicy(
            secret_properties=SecretProperties(content_type=content_type))

    logger.info("Starting 'keyvault certificate import'")
    result = client.import_certificate(vault_base_url=vault_base_url,
                                       certificate_name=certificate_name,
                                       base64_encoded_certificate=certificate_data,
                                       certificate_attributes=cert_attrs,
                                       certificate_policy=certificate_policy,
                                       tags=tags,
                                       password=password)
    logger.info("Finished 'keyvault certificate import'")
    return result


def download_certificate(client, file_path, vault_base_url=None, certificate_name=None,
                         identifier=None, encoding='PEM', certificate_version=''):   # pylint: disable=unused-argument
    """ Download a certificate from a KeyVault. """
    if os.path.isfile(file_path) or os.path.isdir(file_path):
        raise CLIError("File or directory named '{}' already exists.".format(file_path))

    cert = client.get_certificate(
        vault_base_url, certificate_name, certificate_version).cer

    try:
        with open(file_path, 'wb') as f:
            if encoding == 'DER':
                f.write(cert)
            else:
                import base64
                encoded = base64.encodestring(cert)  # pylint:disable=deprecated-method
                if isinstance(encoded, bytes):
                    encoded = encoded.decode("utf-8")
                encoded = '-----BEGIN CERTIFICATE-----\n' + encoded + '-----END CERTIFICATE-----\n'
                f.write(encoded.encode("utf-8"))
    except Exception as ex:  # pylint: disable=broad-except
        if os.path.isfile(file_path):
            os.remove(file_path)
        raise ex


def backup_certificate(client, file_path, vault_base_url=None,
                       certificate_name=None, identifier=None):  # pylint: disable=unused-argument
    cert = client.backup_certificate(vault_base_url, certificate_name).value
    with open(file_path, 'wb') as output:
        output.write(cert)


def restore_certificate(client, vault_base_url, file_path):
    with open(file_path, 'rb') as file_in:
        data = file_in.read()
    return client.restore_certificate(vault_base_url, data)


def add_certificate_contact(cmd, client, vault_base_url, contact_email, contact_name=None,
                            contact_phone=None):
    """ Add a contact to the specified vault to receive notifications of certificate operations. """
    Contact = cmd.get_models('Contact', resource_type=ResourceType.DATA_KEYVAULT)
    Contacts = cmd.get_models('Contacts', resource_type=ResourceType.DATA_KEYVAULT)
    KeyVaultErrorException = cmd.get_models('KeyVaultErrorException', resource_type=ResourceType.DATA_KEYVAULT)
    try:
        contacts = client.get_certificate_contacts(vault_base_url)
    except KeyVaultErrorException:
        contacts = Contacts(contact_list=[])
    contact = Contact(email_address=contact_email, name=contact_name, phone=contact_phone)
    if any((x for x in contacts.contact_list if x.email_address == contact_email)):
        raise CLIError("contact '{}' already exists".format(contact_email))
    contacts.contact_list.append(contact)
    return client.set_certificate_contacts(vault_base_url, contacts.contact_list)


def delete_certificate_contact(cmd, client, vault_base_url, contact_email):
    """ Remove a certificate contact from the specified vault. """
    Contacts = cmd.get_models('Contacts', resource_type=ResourceType.DATA_KEYVAULT)
    orig_contacts = client.get_certificate_contacts(vault_base_url).contact_list
    remaining_contacts = [x for x in client.get_certificate_contacts(vault_base_url).contact_list
                          if x.email_address != contact_email]
    remaining = Contacts(contact_list=remaining_contacts)
    if len(remaining_contacts) == len(orig_contacts):
        raise CLIError("contact '{}' not found in vault '{}'".format(contact_email, vault_base_url))
    if remaining.contact_list:
        return client.set_certificate_contacts(vault_base_url, remaining.contact_list)
    return client.delete_certificate_contacts(vault_base_url)


def create_certificate_issuer(cmd, client, vault_base_url, issuer_name, provider_name, account_id=None,
                              password=None, disabled=None, organization_id=None):
    """ Create a certificate issuer record.
    :param issuer_name: Unique identifier for the issuer settings.
    :param provider_name: The certificate provider name. Must be registered with your
        tenant ID and in your region.
    :param account_id: The issuer account id/username/etc.
    :param password: The issuer account password/secret/etc.
    :param organization_id: The organization id.
    """
    IssuerCredentials = cmd.get_models('IssuerCredentials', resource_type=ResourceType.DATA_KEYVAULT)
    OrganizationDetails = cmd.get_models('OrganizationDetails', resource_type=ResourceType.DATA_KEYVAULT)
    IssuerAttributes = cmd.get_models('IssuerAttributes', resource_type=ResourceType.DATA_KEYVAULT)
    credentials = IssuerCredentials(account_id=account_id, password=password)
    issuer_attrs = IssuerAttributes(enabled=not disabled)
    org_details = OrganizationDetails(id=organization_id, admin_details=[])
    return client.set_certificate_issuer(
        vault_base_url, issuer_name, provider_name, credentials, org_details, issuer_attrs)


def update_certificate_issuer(client, vault_base_url, issuer_name, provider_name=None,
                              account_id=None, password=None, enabled=None, organization_id=None):
    """ Update a certificate issuer record.
    :param issuer_name: Unique identifier for the issuer settings.
    :param provider_name: The certificate provider name. Must be registered with your
        tenant ID and in your region.
    :param account_id: The issuer account id/username/etc.
    :param password: The issuer account password/secret/etc.
    :param organization_id: The organization id.
    """
    def update(obj, prop, value, nullable=False):
        set_value = value if value is not None else getattr(obj, prop, None)
        if set_value is None and not nullable:
            raise CLIError("property '{}' cannot be cleared".format(prop))
        if not set_value and nullable:
            set_value = None
        setattr(obj, prop, set_value)

    issuer = client.get_certificate_issuer(vault_base_url, issuer_name)
    update(issuer.credentials, 'account_id', account_id, True)
    update(issuer.credentials, 'password', password, True)
    update(issuer.attributes, 'enabled', enabled)
    update(issuer.organization_details, 'id', organization_id, True)
    update(issuer, 'provider', provider_name)
    return client.set_certificate_issuer(
        vault_base_url, issuer_name, issuer.provider, issuer.credentials,
        issuer.organization_details, issuer.attributes)


def list_certificate_issuer_admins(client, vault_base_url, issuer_name):
    """ List admins for a specified certificate issuer. """
    return client.get_certificate_issuer(
        vault_base_url, issuer_name).organization_details.admin_details


def add_certificate_issuer_admin(cmd, client, vault_base_url, issuer_name, email, first_name=None,
                                 last_name=None, phone=None):
    """ Add admin details for a specified certificate issuer. """
    AdministratorDetails = cmd.get_models('AdministratorDetails', resource_type=ResourceType.DATA_KEYVAULT)
    issuer = client.get_certificate_issuer(vault_base_url, issuer_name)
    org_details = issuer.organization_details
    admins = org_details.admin_details
    if any((x for x in admins if x.email_address == email)):
        raise CLIError("admin '{}' already exists".format(email))
    new_admin = AdministratorDetails(first_name=first_name, last_name=last_name, email_address=email, phone=phone)
    admins.append(new_admin)
    org_details.admin_details = admins
    result = client.set_certificate_issuer(
        vault_base_url, issuer_name, issuer.provider, issuer.credentials, org_details,
        issuer.attributes)
    created_admin = next(x for x in result.organization_details.admin_details
                         if x.email_address == email)
    return created_admin


def delete_certificate_issuer_admin(client, vault_base_url, issuer_name, email):
    """ Remove admin details for the specified certificate issuer. """
    issuer = client.get_certificate_issuer(vault_base_url, issuer_name)
    org_details = issuer.organization_details
    admins = org_details.admin_details
    remaining = [x for x in admins if x.email_address != email]
    if len(remaining) == len(admins):
        raise CLIError("admin '{}' not found for issuer '{}'".format(email, issuer_name))
    org_details.admin_details = remaining
    client.set_certificate_issuer(
        vault_base_url, issuer_name, issuer.provider, issuer.credentials, org_details,
        issuer.attributes)
# endregion


# region storage_account
def backup_storage_account(client, file_path, vault_base_url=None,
                           storage_account_name=None, identifier=None):  # pylint: disable=unused-argument
    backup = client.backup_storage_account(vault_base_url, storage_account_name).value
    with open(file_path, 'wb') as output:
        output.write(backup)


def restore_storage_account(client, vault_base_url, file_path):
    with open(file_path, 'rb') as file_in:
        data = file_in.read()
        return client.restore_storage_account(vault_base_url, data)
# endregion


# region private_endpoint
def _update_private_endpoint_connection_status(cmd, client, resource_group_name, vault_name,
                                               private_endpoint_connection_name, is_approved=True, description=None,
                                               no_wait=False):
    PrivateEndpointServiceConnectionStatus = cmd.get_models('PrivateEndpointServiceConnectionStatus',
                                                            resource_type=ResourceType.MGMT_KEYVAULT)

    private_endpoint_connection = client.get(resource_group_name=resource_group_name, vault_name=vault_name,
                                             private_endpoint_connection_name=private_endpoint_connection_name)

    new_status = PrivateEndpointServiceConnectionStatus.approved \
        if is_approved else PrivateEndpointServiceConnectionStatus.rejected
    private_endpoint_connection.private_link_service_connection_state.status = new_status
    private_endpoint_connection.private_link_service_connection_state.description = description

    retval = client.put(resource_group_name=resource_group_name,
                        vault_name=vault_name,
                        private_endpoint_connection_name=private_endpoint_connection_name,
                        properties=private_endpoint_connection)

    if no_wait:
        return retval

    new_retval = \
        _wait_private_link_operation(client, resource_group_name, vault_name, private_endpoint_connection_name)

    if new_retval:
        return new_retval
    return retval


def _wait_private_link_operation(client, resource_group_name, vault_name, private_endpoint_connection_name):
    retries = 0
    max_retries = 10
    wait_second = 1
    while retries < max_retries:
        pl = client.get(resource_group_name=resource_group_name,
                        vault_name=vault_name,
                        private_endpoint_connection_name=private_endpoint_connection_name)

        if pl.provisioning_state == 'Succeeded':
            return pl
        time.sleep(wait_second)
        retries += 1

    return None


def approve_private_endpoint_connection(cmd, client, resource_group_name, vault_name, private_endpoint_connection_name,
                                        description=None, no_wait=False):
    """Approve a private endpoint connection request for a Key Vault."""

    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name, vault_name, private_endpoint_connection_name, is_approved=True,
        description=description, no_wait=no_wait
    )


def reject_private_endpoint_connection(cmd, client, resource_group_name, vault_name, private_endpoint_connection_name,
                                       description=None, no_wait=False):
    """Reject a private endpoint connection request for a Key Vault."""

    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name, vault_name, private_endpoint_connection_name, is_approved=False,
        description=description, no_wait=no_wait
    )
# endregion
