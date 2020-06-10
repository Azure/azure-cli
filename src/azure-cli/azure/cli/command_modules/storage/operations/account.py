# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Custom operations for storage account commands"""

import os
from azure.cli.command_modules.storage._client_factory import storage_client_factory, cf_sa_for_keys
from azure.cli.core.util import get_file_json, shell_safe_json_parse
from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


def str2bool(v):
    if v is not None:
        return v.lower() == "true"
    return v


# pylint: disable=too-many-locals, too-many-statements
def create_storage_account(cmd, resource_group_name, account_name, sku=None, location=None, kind=None,
                           tags=None, custom_domain=None, encryption_services=None, access_tier=None, https_only=None,
                           enable_files_aadds=None, bypass=None, default_action=None, assign_identity=False,
                           enable_large_file_share=None, enable_files_adds=None, domain_name=None,
                           net_bios_domain_name=None, forest_name=None, domain_guid=None, domain_sid=None,
                           azure_storage_sid=None, enable_hierarchical_namespace=None,
                           encryption_key_type_for_table=None, encryption_key_type_for_queue=None,
                           routing_choice=None, publish_microsoft_endpoints=None, publish_internet_endpoints=None):
    StorageAccountCreateParameters, Kind, Sku, CustomDomain, AccessTier, Identity, Encryption, NetworkRuleSet = \
        cmd.get_models('StorageAccountCreateParameters', 'Kind', 'Sku', 'CustomDomain', 'AccessTier', 'Identity',
                       'Encryption', 'NetworkRuleSet')
    scf = storage_client_factory(cmd.cli_ctx)
    if kind is None:
        logger.warning("The default kind for created storage account will change to 'StorageV2' from 'Storage' "
                       "in the future")
    params = StorageAccountCreateParameters(sku=Sku(name=sku), kind=Kind(kind), location=location, tags=tags)
    if custom_domain:
        params.custom_domain = CustomDomain(name=custom_domain, use_sub_domain=None)
    if encryption_services:
        params.encryption = Encryption(services=encryption_services)
    if access_tier:
        params.access_tier = AccessTier(access_tier)
    if assign_identity:
        params.identity = Identity()
    if https_only is not None:
        params.enable_https_traffic_only = https_only
    if enable_hierarchical_namespace is not None:
        params.is_hns_enabled = enable_hierarchical_namespace

    AzureFilesIdentityBasedAuthentication = cmd.get_models('AzureFilesIdentityBasedAuthentication')
    if enable_files_aadds is not None:
        params.azure_files_identity_based_authentication = AzureFilesIdentityBasedAuthentication(
            directory_service_options='AADDS' if enable_files_aadds else 'None')
    if enable_files_adds is not None:
        ActiveDirectoryProperties = cmd.get_models('ActiveDirectoryProperties')
        if enable_files_adds:  # enable AD
            if not (domain_name and net_bios_domain_name and forest_name and domain_guid and domain_sid and
                    azure_storage_sid):
                raise CLIError("To enable ActiveDirectoryDomainServicesForFile, user must specify all of: "
                               "--domain-name, --net-bios-domain-name, --forest-name, --domain-guid, --domain-sid and "
                               "--azure_storage_sid arguments in Azure Active Directory Properties Argument group.")

            active_directory_properties = ActiveDirectoryProperties(domain_name=domain_name,
                                                                    net_bios_domain_name=net_bios_domain_name,
                                                                    forest_name=forest_name, domain_guid=domain_guid,
                                                                    domain_sid=domain_sid,
                                                                    azure_storage_sid=azure_storage_sid)
            # TODO: Enabling AD will automatically disable AADDS. Maybe we should throw error message

            params.azure_files_identity_based_authentication = AzureFilesIdentityBasedAuthentication(
                directory_service_options='AD',
                active_directory_properties=active_directory_properties)

        else:  # disable AD
            if domain_name or net_bios_domain_name or forest_name or domain_guid or domain_sid or azure_storage_sid:  # pylint: disable=too-many-boolean-expressions
                raise CLIError("To disable ActiveDirectoryDomainServicesForFile, user can't specify any of: "
                               "--domain-name, --net-bios-domain-name, --forest-name, --domain-guid, --domain-sid and "
                               "--azure_storage_sid arguments in Azure Active Directory Properties Argument group.")

            params.azure_files_identity_based_authentication = AzureFilesIdentityBasedAuthentication(
                directory_service_options='None')

    if enable_large_file_share:
        LargeFileSharesState = cmd.get_models('LargeFileSharesState')
        params.large_file_shares_state = LargeFileSharesState("Enabled")

    if NetworkRuleSet and (bypass or default_action):
        if bypass and not default_action:
            raise CLIError('incorrect usage: --default-action ACTION [--bypass SERVICE ...]')
        params.network_rule_set = NetworkRuleSet(bypass=bypass, default_action=default_action, ip_rules=None,
                                                 virtual_network_rules=None)

    if encryption_key_type_for_table is not None or encryption_key_type_for_queue is not None:
        EncryptionServices = cmd.get_models('EncryptionServices')
        EncryptionService = cmd.get_models('EncryptionService')
        params.encryption = Encryption()
        params.encryption.services = EncryptionServices()
        if encryption_key_type_for_table is not None:
            table_encryption_service = EncryptionService(enabled=True, key_type=encryption_key_type_for_table)
            params.encryption.services.table = table_encryption_service
        if encryption_key_type_for_queue is not None:
            queue_encryption_service = EncryptionService(enabled=True, key_type=encryption_key_type_for_queue)
            params.encryption.services.queue = queue_encryption_service

    if any([routing_choice, publish_microsoft_endpoints, publish_internet_endpoints]):
        RoutingPreference = cmd.get_models('RoutingPreference')
        params.routing_preference = RoutingPreference(
            routing_choice=routing_choice,
            publish_microsoft_endpoints=str2bool(publish_microsoft_endpoints),
            publish_internet_endpoints=str2bool(publish_internet_endpoints)
        )

    return scf.storage_accounts.create(resource_group_name, account_name, params)


def list_storage_accounts(cmd, resource_group_name=None):
    scf = storage_client_factory(cmd.cli_ctx)
    if resource_group_name:
        accounts = scf.storage_accounts.list_by_resource_group(resource_group_name)
    else:
        accounts = scf.storage_accounts.list()
    return list(accounts)


def show_storage_account_connection_string(cmd, resource_group_name, account_name, protocol='https', blob_endpoint=None,
                                           file_endpoint=None, queue_endpoint=None, table_endpoint=None, sas_token=None,
                                           key_name='primary'):

    endpoint_suffix = cmd.cli_ctx.cloud.suffixes.storage_endpoint
    connection_string = 'DefaultEndpointsProtocol={};EndpointSuffix={}'.format(protocol, endpoint_suffix)
    if account_name is not None:
        scf = cf_sa_for_keys(cmd.cli_ctx, None)
        obj = scf.list_keys(resource_group_name, account_name)  # pylint: disable=no-member
        try:
            keys = [obj.keys[0].value, obj.keys[1].value]  # pylint: disable=no-member
        except AttributeError:
            # Older API versions have a slightly different structure
            keys = [obj.key1, obj.key2]  # pylint: disable=no-member

        connection_string = '{}{}{}'.format(
            connection_string,
            ';AccountName={}'.format(account_name),
            ';AccountKey={}'.format(keys[0] if key_name == 'primary' else keys[1]))  # pylint: disable=no-member

    connection_string = '{}{}'.format(connection_string,
                                      ';BlobEndpoint={}'.format(blob_endpoint) if blob_endpoint else '')
    connection_string = '{}{}'.format(connection_string,
                                      ';FileEndpoint={}'.format(file_endpoint) if file_endpoint else '')
    connection_string = '{}{}'.format(connection_string,
                                      ';QueueEndpoint={}'.format(queue_endpoint) if queue_endpoint else '')
    connection_string = '{}{}'.format(connection_string,
                                      ';TableEndpoint={}'.format(table_endpoint) if table_endpoint else '')
    connection_string = '{}{}'.format(connection_string,
                                      ';SharedAccessSignature={}'.format(sas_token) if sas_token else '')
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


def get_storage_account_properties(cli_ctx, account_id):
    scf = storage_client_factory(cli_ctx)
    from msrestazure.tools import parse_resource_id
    result = parse_resource_id(account_id)
    return scf.storage_accounts.get_properties(result['resource_group'], result['name'])


# pylint: disable=too-many-locals, too-many-statements, too-many-branches, too-many-boolean-expressions
def update_storage_account(cmd, instance, sku=None, tags=None, custom_domain=None, use_subdomain=None,
                           encryption_services=None, encryption_key_source=None, encryption_key_version=None,
                           encryption_key_name=None, encryption_key_vault=None,
                           access_tier=None, https_only=None, enable_files_aadds=None, assign_identity=False,
                           bypass=None, default_action=None, enable_large_file_share=None, enable_files_adds=None,
                           domain_name=None, net_bios_domain_name=None, forest_name=None, domain_guid=None,
                           domain_sid=None, azure_storage_sid=None, routing_choice=None,
                           publish_microsoft_endpoints=None, publish_internet_endpoints=None):
    StorageAccountUpdateParameters, Sku, CustomDomain, AccessTier, Identity, Encryption, NetworkRuleSet = \
        cmd.get_models('StorageAccountUpdateParameters', 'Sku', 'CustomDomain', 'AccessTier', 'Identity', 'Encryption',
                       'NetworkRuleSet')

    domain = instance.custom_domain
    if custom_domain is not None:
        domain = CustomDomain(name=custom_domain)
        if use_subdomain is not None:
            domain.use_sub_domain_name = use_subdomain == 'true'

    encryption = instance.encryption
    if not encryption and any((encryption_services, encryption_key_source, encryption_key_name,
                               encryption_key_vault, encryption_key_version is not None)):
        encryption = Encryption()
    if encryption_services:
        encryption.services = encryption_services

    if encryption_key_source:
        encryption.key_source = encryption_key_source

    KeySource = cmd.get_models('KeySource')
    if encryption.key_source == KeySource.microsoft_keyvault:
        if encryption.key_vault_properties is None:
            KeyVaultProperties = cmd.get_models('KeyVaultProperties')
            encryption.key_vault_properties = KeyVaultProperties()
    else:
        if any([encryption_key_name, encryption_key_vault, encryption_key_version]):
            raise ValueError(
                'Specify `--encryption-key-source=Microsoft.Keyvault` to configure key vault properties.')
        if encryption.key_vault_properties is not None:
            encryption.key_vault_properties = None

    if encryption_key_name:
        encryption.key_vault_properties.key_name = encryption_key_name
    if encryption_key_vault:
        encryption.key_vault_properties.key_vault_uri = encryption_key_vault
    if encryption_key_version is not None:
        encryption.key_vault_properties.key_version = encryption_key_version

    params = StorageAccountUpdateParameters(
        sku=Sku(name=sku) if sku is not None else instance.sku,
        tags=tags if tags is not None else instance.tags,
        custom_domain=domain,
        encryption=encryption,
        access_tier=AccessTier(access_tier) if access_tier is not None else instance.access_tier,
        enable_https_traffic_only=https_only if https_only is not None else instance.enable_https_traffic_only
    )
    AzureFilesIdentityBasedAuthentication = cmd.get_models('AzureFilesIdentityBasedAuthentication')
    if enable_files_aadds is not None:
        if enable_files_aadds:  # enable AADDS
            origin_storage_account = get_storage_account_properties(cmd.cli_ctx, instance.id)
            if origin_storage_account.azure_files_identity_based_authentication and \
                    origin_storage_account.azure_files_identity_based_authentication.directory_service_options == 'AD':
                raise CLIError("The Storage account already enabled ActiveDirectoryDomainServicesForFile, "
                               "please disable it by running this cmdlets with \"--enable-files-adds false\" "
                               "before enable AzureActiveDirectoryDomainServicesForFile.")
            params.azure_files_identity_based_authentication = AzureFilesIdentityBasedAuthentication(
                directory_service_options='AADDS' if enable_files_aadds else 'None')
        else:  # Only disable AADDS and keep others unchanged
            origin_storage_account = get_storage_account_properties(cmd.cli_ctx, instance.id)
            if not origin_storage_account.azure_files_identity_based_authentication or \
                    origin_storage_account.azure_files_identity_based_authentication.directory_service_options\
                    == 'AADDS':
                params.azure_files_identity_based_authentication = AzureFilesIdentityBasedAuthentication(
                    directory_service_options='None')
            else:
                params.azure_files_identity_based_authentication = \
                    origin_storage_account.azure_files_identity_based_authentication

    if enable_files_adds is not None:
        ActiveDirectoryProperties = cmd.get_models('ActiveDirectoryProperties')
        if enable_files_adds:  # enable AD
            if not(domain_name and net_bios_domain_name and forest_name and domain_guid and domain_sid and
                   azure_storage_sid):
                raise CLIError("To enable ActiveDirectoryDomainServicesForFile, user must specify all of: "
                               "--domain-name, --net-bios-domain-name, --forest-name, --domain-guid, --domain-sid and "
                               "--azure_storage_sid arguments in Azure Active Directory Properties Argument group.")
            origin_storage_account = get_storage_account_properties(cmd.cli_ctx, instance.id)
            if origin_storage_account.azure_files_identity_based_authentication and \
                    origin_storage_account.azure_files_identity_based_authentication.directory_service_options \
                    == 'AADDS':
                raise CLIError("The Storage account already enabled AzureActiveDirectoryDomainServicesForFile, "
                               "please disable it by running this cmdlets with \"--enable-files-aadds false\" "
                               "before enable ActiveDirectoryDomainServicesForFile.")
            active_directory_properties = ActiveDirectoryProperties(domain_name=domain_name,
                                                                    net_bios_domain_name=net_bios_domain_name,
                                                                    forest_name=forest_name, domain_guid=domain_guid,
                                                                    domain_sid=domain_sid,
                                                                    azure_storage_sid=azure_storage_sid)
            # TODO: Enabling AD will automatically disable AADDS. Maybe we should throw error message

            params.azure_files_identity_based_authentication = AzureFilesIdentityBasedAuthentication(
                directory_service_options='AD',
                active_directory_properties=active_directory_properties)

        else:  # disable AD
            if domain_name or net_bios_domain_name or forest_name or domain_guid or domain_sid or azure_storage_sid:
                raise CLIError("To disable ActiveDirectoryDomainServicesForFile, user can't specify any of: "
                               "--domain-name, --net-bios-domain-name, --forest-name, --domain-guid, --domain-sid and "
                               "--azure_storage_sid arguments in Azure Active Directory Properties Argument group.")
            # Only disable AD and keep others unchanged
            origin_storage_account = get_storage_account_properties(cmd.cli_ctx, instance.id)
            if not origin_storage_account.azure_files_identity_based_authentication or \
                    origin_storage_account.azure_files_identity_based_authentication.directory_service_options == 'AD':
                params.azure_files_identity_based_authentication = AzureFilesIdentityBasedAuthentication(
                    directory_service_options='None')
            else:
                params.azure_files_identity_based_authentication = \
                    origin_storage_account.azure_files_identity_based_authentication

    if assign_identity:
        params.identity = Identity()
    if enable_large_file_share:
        LargeFileSharesState = cmd.get_models('LargeFileSharesState')
        params.large_file_shares_state = LargeFileSharesState("Enabled")
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
            raise CLIError('incorrect usage: --default-action ACTION [--bypass SERVICE ...]')
        params.network_rule_set = acl

    if hasattr(params, 'routing_preference') and any([routing_choice, publish_microsoft_endpoints,
                                                      publish_internet_endpoints]):
        if params.routing_preference is None:
            RoutingPreference = cmd.get_models('RoutingPreference')
            params.routing_preference = RoutingPreference()
        if routing_choice is not None:
            params.routing_preference.routing_choice = routing_choice
        if publish_microsoft_endpoints is not None:
            params.routing_preference.publish_microsoft_endpoints = str2bool(publish_microsoft_endpoints)
        if publish_internet_endpoints is not None:
            params.routing_preference.publish_internet_endpoints = str2bool(publish_internet_endpoints)

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
            raise CLIError("Expected fully qualified resource ID: got '{}'".format(subnet))
        VirtualNetworkRule = cmd.get_models('VirtualNetworkRule')
        if not rules.virtual_network_rules:
            rules.virtual_network_rules = []
        rules.virtual_network_rules = [r for r in rules.virtual_network_rules
                                       if r.virtual_network_resource_id.lower() != subnet.lower()]
        rules.virtual_network_rules.append(VirtualNetworkRule(virtual_network_resource_id=subnet, action=action))
    if ip_address:
        IpRule = cmd.get_models('IPRule')
        if not rules.ip_rules:
            rules.ip_rules = []
        rules.ip_rules = [r for r in rules.ip_rules if r.ip_address_or_range != ip_address]
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


def _update_private_endpoint_connection_status(cmd, client, resource_group_name, account_name,
                                               private_endpoint_connection_name, is_approved=True, description=None):

    PrivateEndpointServiceConnectionStatus, ErrorResponseException = \
        cmd.get_models('PrivateEndpointServiceConnectionStatus', 'ErrorResponseException')

    private_endpoint_connection = client.get(resource_group_name=resource_group_name, account_name=account_name,
                                             private_endpoint_connection_name=private_endpoint_connection_name)

    old_status = private_endpoint_connection.private_link_service_connection_state.status
    new_status = PrivateEndpointServiceConnectionStatus.approved \
        if is_approved else PrivateEndpointServiceConnectionStatus.rejected
    private_endpoint_connection.private_link_service_connection_state.status = new_status
    private_endpoint_connection.private_link_service_connection_state.description = description
    try:
        return client.put(resource_group_name=resource_group_name,
                          account_name=account_name,
                          private_endpoint_connection_name=private_endpoint_connection_name,
                          properties=private_endpoint_connection)
    except ErrorResponseException as ex:
        if ex.response.status_code == 400:
            from msrestazure.azure_exceptions import CloudError
            if new_status == "Approved" and old_status == "Rejected":
                raise CloudError(ex.response, "You cannot approve the connection request after rejection. "
                                 "Please create a new connection for approval.")
        raise ex


def approve_private_endpoint_connection(cmd, client, resource_group_name, account_name,
                                        private_endpoint_connection_name, description=None):

    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name=resource_group_name, account_name=account_name, is_approved=True,
        private_endpoint_connection_name=private_endpoint_connection_name, description=description
    )


def reject_private_endpoint_connection(cmd, client, resource_group_name, account_name, private_endpoint_connection_name,
                                       description=None):
    return _update_private_endpoint_connection_status(
        cmd, client, resource_group_name=resource_group_name, account_name=account_name, is_approved=False,
        private_endpoint_connection_name=private_endpoint_connection_name, description=description
    )


def create_management_policies(client, resource_group_name, account_name, policy):
    if os.path.exists(policy):
        policy = get_file_json(policy)
    else:
        policy = shell_safe_json_parse(policy)
    return client.create_or_update(resource_group_name, account_name, policy=policy)


def update_management_policies(client, resource_group_name, account_name, parameters=None):
    if parameters:
        parameters = parameters.policy
    return client.create_or_update(resource_group_name, account_name, policy=parameters)


# TODO: support updating other properties besides 'enable_change_feed,delete_retention_policy'
def update_blob_service_properties(cmd, instance, enable_change_feed=None, enable_delete_retention=None,
                                   delete_retention_days=None, enable_restore_policy=None, restore_days=None,
                                   enable_versioning=None):
    if enable_change_feed is not None:
        instance.change_feed = cmd.get_models('ChangeFeed')(enabled=enable_change_feed)

    if enable_delete_retention is not None:
        if enable_delete_retention is False:
            delete_retention_days = None
        instance.delete_retention_policy = cmd.get_models('DeleteRetentionPolicy')(
            enabled=enable_delete_retention, days=delete_retention_days)

    if enable_restore_policy is not None:
        if enable_restore_policy is False:
            restore_days = None
        instance.restore_policy = cmd.get_models('RestorePolicyProperties')(
            enabled=enable_restore_policy, days=restore_days)

    if enable_versioning is not None:
        instance.is_versioning_enabled = enable_versioning

    return instance


def update_file_service_properties(cmd, client, resource_group_name, account_name, enable_delete_retention=None,
                                   delete_retention_days=None):

    if enable_delete_retention is not None:
        if enable_delete_retention is False:
            delete_retention_days = None
        delete_retention_policy = cmd.get_models('DeleteRetentionPolicy')(
            enabled=enable_delete_retention, days=delete_retention_days)

    # If already enabled, only update days
    if enable_delete_retention is None and delete_retention_days is not None:
        delete_retention_policy = client.get_service_properties(
            resource_group_name=resource_group_name,
            account_name=account_name).share_delete_retention_policy
        if delete_retention_policy is not None and delete_retention_policy.enabled:
            delete_retention_policy.days = delete_retention_days
        else:
            raise CLIError("Delete Retention Policy hasn't been enabled, and you cannot set delete retention days. "
                           "Please set --enabled-delete-retention as true to enable Delete Retention Policy.")

    return client.set_service_properties(resource_group_name=resource_group_name, account_name=account_name,
                                         share_delete_retention_policy=delete_retention_policy)


def create_encryption_scope(cmd, client, resource_group_name, account_name, encryption_scope_name,
                            key_source=None, key_uri=None):
    EncryptionScope = cmd.get_models('EncryptionScope')

    if key_source:
        encryption_scope = EncryptionScope(source=key_source)

    if key_uri:
        EncryptionScopeKeyVaultProperties = cmd.get_models('EncryptionScopeKeyVaultProperties')
        encryption_scope.key_vault_properties = EncryptionScopeKeyVaultProperties(key_uri=key_uri)

    return client.put(resource_group_name=resource_group_name, account_name=account_name,
                      encryption_scope_name=encryption_scope_name, encryption_scope=encryption_scope)


def update_encryption_scope(cmd, client, resource_group_name, account_name, encryption_scope_name,
                            key_source=None, key_uri=None, state=None):
    EncryptionScope, EncryptionScopeState = cmd.get_models('EncryptionScope', 'EncryptionScopeState')
    encryption_scope = EncryptionScope()

    if key_source:
        encryption_scope.source = key_source

    if key_uri:
        EncryptionScopeKeyVaultProperties = cmd.get_models('EncryptionScopeKeyVaultProperties')
        encryption_scope.key_vault_properties = EncryptionScopeKeyVaultProperties(key_uri=key_uri)

    if state is not None:
        encryption_scope.state = EncryptionScopeState(state)

    return client.patch(resource_group_name=resource_group_name, account_name=account_name,
                        encryption_scope_name=encryption_scope_name, encryption_scope=encryption_scope)
