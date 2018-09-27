# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Custom operations for storage account commands"""

from azure.cli.command_modules.storage._client_factory import storage_client_factory


def create_storage_account(cmd, resource_group_name, account_name, sku=None, location=None, kind=None,
                           tags=None, custom_domain=None, encryption_services=None, access_tier=None, https_only=None,
                           bypass=None, default_action=None, assign_identity=False):
    StorageAccountCreateParameters, Kind, Sku, CustomDomain, AccessTier, Identity, Encryption, NetworkRuleSet = \
        cmd.get_models('StorageAccountCreateParameters', 'Kind', 'Sku', 'CustomDomain', 'AccessTier', 'Identity',
                       'Encryption', 'NetworkRuleSet')
    scf = storage_client_factory(cmd.cli_ctx)
    params = StorageAccountCreateParameters(sku=Sku(name=sku), kind=Kind(kind), location=location, tags=tags)
    if custom_domain:
        params.custom_domain = CustomDomain(name=custom_domain, use_sub_domain=None)
    if encryption_services:
        params.encryption = Encryption(services=encryption_services)
    if access_tier:
        params.access_tier = AccessTier(access_tier)
    if assign_identity:
        params.identity = Identity()
    if https_only:
        params.enable_https_traffic_only = https_only
    # temporary fix to allow idempotent create when value is None. (sdk defaults with False)
    params.is_hns_enabled = None

    if NetworkRuleSet and (bypass or default_action):
        if bypass and not default_action:
            from knack.util import CLIError
            raise CLIError('incorrect usage: --default-action ACTION [--bypass SERVICE ...]')
        params.network_rule_set = NetworkRuleSet(bypass=bypass, default_action=default_action, ip_rules=None,
                                                 virtual_network_rules=None)

    return scf.storage_accounts.create(resource_group_name, account_name, params)


def list_storage_accounts(cmd, resource_group_name=None):
    scf = storage_client_factory(cmd.cli_ctx)
    if resource_group_name:
        accounts = scf.storage_accounts.list_by_resource_group(resource_group_name)
    else:
        accounts = scf.storage_accounts.list()
    return list(accounts)


def show_storage_account_connection_string(cmd, resource_group_name, account_name, protocol='https', blob_endpoint=None,
                                           file_endpoint=None, queue_endpoint=None, table_endpoint=None,
                                           key_name='primary'):
    scf = storage_client_factory(cmd.cli_ctx)
    obj = scf.storage_accounts.list_keys(resource_group_name, account_name)  # pylint: disable=no-member
    try:
        keys = [obj.keys[0].value, obj.keys[1].value]  # pylint: disable=no-member
    except AttributeError:
        # Older API versions have a slightly different structure
        keys = [obj.key1, obj.key2]  # pylint: disable=no-member

    endpoint_suffix = cmd.cli_ctx.cloud.suffixes.storage_endpoint
    connection_string = 'DefaultEndpointsProtocol={};EndpointSuffix={};AccountName={};AccountKey={}'.format(
        protocol,
        endpoint_suffix,
        account_name,
        keys[0] if key_name == 'primary' else keys[1])  # pylint: disable=no-member
    connection_string = '{}{}'.format(connection_string,
                                      ';BlobEndpoint={}'.format(blob_endpoint) if blob_endpoint else '')
    connection_string = '{}{}'.format(connection_string,
                                      ';FileEndpoint={}'.format(file_endpoint) if file_endpoint else '')
    connection_string = '{}{}'.format(connection_string,
                                      ';QueueEndpoint={}'.format(queue_endpoint) if queue_endpoint else '')
    connection_string = '{}{}'.format(connection_string,
                                      ';TableEndpoint={}'.format(table_endpoint) if table_endpoint else '')
    return {'connectionString': connection_string}


def show_storage_account_usage(cmd, location):
    scf = storage_client_factory(cmd.cli_ctx)
    try:
        client = scf.usages
    except NotImplementedError:
        client = scf.usage
    return next((x for x in client.list_by_location(location) if x.name.value == 'StorageAccounts'), None)  # pylint: disable=no-member


def show_storage_account_usage_no_location(cmd):
    scf = storage_client_factory(cmd.cli_ctx)
    return next((x for x in scf.usage.list() if x.name.value == 'StorageAccounts'), None)  # pylint: disable=no-member


# pylint: disable=too-many-locals
def update_storage_account(cmd, instance, sku=None, tags=None, custom_domain=None, use_subdomain=None,
                           encryption_services=None, encryption_key_source=None, encryption_key_vault_properties=None,
                           access_tier=None, https_only=None, assign_identity=False, bypass=None, default_action=None):
    StorageAccountUpdateParameters, Sku, CustomDomain, AccessTier, Identity, Encryption, NetworkRuleSet = \
        cmd.get_models('StorageAccountUpdateParameters', 'Sku', 'CustomDomain', 'AccessTier', 'Identity',
                       'Encryption', 'NetworkRuleSet')
    domain = instance.custom_domain
    if custom_domain is not None:
        domain = CustomDomain(name=custom_domain)
        if use_subdomain is not None:
            domain.name = use_subdomain == 'true'

    encryption = instance.encryption
    if encryption_services:
        if not encryption:
            encryption = Encryption(services=encryption_services)
        else:
            encryption.services = encryption_services

    if encryption_key_source or encryption_key_vault_properties:
        if encryption:
            encryption.key_source = encryption_key_source
            encryption.key_vault_properties = encryption_key_vault_properties
        else:
            raise ValueError('--encryption-services is required when configure encryption key source')

    params = StorageAccountUpdateParameters(
        sku=Sku(name=sku) if sku is not None else instance.sku,
        tags=tags if tags is not None else instance.tags,
        custom_domain=domain,
        encryption=encryption,
        access_tier=AccessTier(access_tier) if access_tier is not None else instance.access_tier,
        enable_https_traffic_only=https_only if https_only is not None else instance.enable_https_traffic_only
    )
    if assign_identity:
        params.identity = Identity()

    if NetworkRuleSet:
        acl = instance.network_rule_set
        if acl:
            if bypass:
                acl.bypass = bypass
            if default_action:
                acl.default_action = default_action
        elif default_action:
            acl = NetworkRuleSet(bypass=bypass, virtual_network_rules=None, ip_rules=None,
                                 default_action=default_action)
        elif bypass:
            from knack.util import CLIError
            raise CLIError('incorrect usage: --default-action ACTION [--bypass SERVICE ...]')
        params.network_rule_set = acl

    return params


def list_network_rules(client, resource_group_name, account_name):
    sa = client.get_properties(resource_group_name, account_name)
    rules = sa.network_rule_set
    delattr(rules, 'bypass')
    delattr(rules, 'default_action')
    return rules


def add_network_rule(cmd, client, resource_group_name, account_name, action='Allow', subnet=None,
                     vnet_name=None, ip_address=None):  # pylint: disable=unused-argument
    sa = client.get_properties(resource_group_name, account_name)
    rules = sa.network_rule_set
    if subnet:
        from msrestazure.tools import is_valid_resource_id
        if not is_valid_resource_id(subnet):
            from knack.util import CLIError
            raise CLIError("Expected fully qualified resource ID: got '{}'".format(subnet))
        VirtualNetworkRule = cmd.get_models('VirtualNetworkRule')
        if not rules.virtual_network_rules:
            rules.virtual_network_rules = []
        rules.virtual_network_rules.append(VirtualNetworkRule(virtual_network_resource_id=subnet, action=action))
    if ip_address:
        IpRule = cmd.get_models('IPRule')
        if not rules.ip_rules:
            rules.ip_rules = []
        rules.ip_rules.append(IpRule(ip_address_or_range=ip_address, action=action))

    StorageAccountUpdateParameters = cmd.get_models('StorageAccountUpdateParameters')
    params = StorageAccountUpdateParameters(network_rule_set=rules)
    return client.update(resource_group_name, account_name, params)


def remove_network_rule(cmd, client, resource_group_name, account_name, ip_address=None, subnet=None,
                        vnet_name=None):  # pylint: disable=unused-argument
    sa = client.get_properties(resource_group_name, account_name)
    rules = sa.network_rule_set
    if subnet:
        rules.virtual_network_rules = [x for x in rules.virtual_network_rules
                                       if not x.virtual_network_resource_id.endswith(subnet)]
    if ip_address:
        rules.ip_rules = [x for x in rules.ip_rules if x.ip_address_or_range != ip_address]

    StorageAccountUpdateParameters = cmd.get_models('StorageAccountUpdateParameters')
    params = StorageAccountUpdateParameters(network_rule_set=rules)
    return client.update(resource_group_name, account_name, params)
