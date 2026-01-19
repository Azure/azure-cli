# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

"""Custom operations for storage account commands"""

import os
from ipaddress import ip_network
from azure.cli.command_modules.storage._client_factory import storage_client_factory, cf_sa_for_keys
from azure.cli.core.util import get_file_json, shell_safe_json_parse, find_child_item, user_confirmation
from azure.cli.core.profiles import ResourceType, get_sdk
from ..aaz.latest.storage.account.migration._start import Start as _AccountMigrationStart
from ..aaz.latest.storage.account import FileServiceUsage as _FileServiceUsage
from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


def check_name_availability(cmd, client, name):
    StorageAccountCheckNameAvailabilityParameters = cmd.get_models('StorageAccountCheckNameAvailabilityParameters')
    account_name = StorageAccountCheckNameAvailabilityParameters(name=name, type="Microsoft.Storage/storageAccounts")
    return client.check_name_availability(account_name)


def regenerate_key(cmd, client, account_name, key_name, resource_group_name=None):
    StorageAccountRegenerateKeyParameters = cmd.get_models('StorageAccountRegenerateKeyParameters')
    regenerate_key_parameters = StorageAccountRegenerateKeyParameters(key_name=key_name)
    return client.regenerate_key(resource_group_name, account_name, regenerate_key_parameters)


def generate_sas(cmd, client, services, resource_types, permission, expiry, start=None,
                 ip=None, protocol=None, **kwargs):
    from azure.cli.core.azclierror import RequiredArgumentMissingError
    if not client.account_name or not client.credential or not client.credential.account_key:
        error_msg = """
        Missing/Invalid credentials to access storage service. The following variations are accepted:
            (1) account name and key (--account-name and --account-key options or
                set AZURE_STORAGE_ACCOUNT and AZURE_STORAGE_KEY environment variables)
            (2) account name (--account-name option or AZURE_STORAGE_ACCOUNT environment variable;
                this will make calls to query for a storage account key using login credentials)
            (3) connection string (--connection-string option or
                set AZURE_STORAGE_CONNECTION_STRING environment variable); some shells will require
                quoting to preserve literal character interpretation.
        """
        raise RequiredArgumentMissingError(error_msg)

    t_account_sas = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_BLOB,
                            '_shared.shared_access_signature#SharedAccessSignature')

    return t_account_sas(account_name=client.account_name, account_key=client.credential.account_key).\
        generate_account(services=services, resource_types=resource_types, permission=permission, expiry=expiry,
                         start=start, ip=ip, protocol=protocol, **kwargs)


# pylint: disable=too-many-locals, too-many-statements, too-many-branches, unused-argument, line-too-long
def create_storage_account(cmd, resource_group_name, account_name, sku=None, location=None, kind=None,
                           tags=None, custom_domain=None, encryption_services=None, encryption_key_source=None,
                           encryption_key_name=None, encryption_key_vault=None, encryption_key_version=None,
                           access_tier=None, https_only=None, enable_sftp=None, enable_local_user=None,
                           enable_files_aadkerb=None,
                           enable_files_aadds=None, bypass=None, default_action=None, assign_identity=False,
                           enable_large_file_share=None, enable_files_adds=None, domain_name=None,
                           net_bios_domain_name=None, forest_name=None, domain_guid=None, domain_sid=None,
                           sam_account_name=None, account_type=None,
                           azure_storage_sid=None, enable_hierarchical_namespace=None,
                           encryption_key_type_for_table=None, encryption_key_type_for_queue=None,
                           routing_choice=None, publish_microsoft_endpoints=None, publish_internet_endpoints=None,
                           require_infrastructure_encryption=None, allow_blob_public_access=None,
                           min_tls_version=None, allow_shared_key_access=None, edge_zone=None,
                           identity_type=None, user_identity_id=None,
                           key_vault_user_identity_id=None, federated_identity_client_id=None,
                           sas_expiration_action=None, sas_expiration_period=None, key_expiration_period_in_days=None,
                           allow_cross_tenant_replication=None, default_share_permission=None,
                           enable_nfs_v3=None, subnet=None, vnet_name=None, action='Allow', enable_alw=None,
                           immutability_period_since_creation_in_days=None, immutability_policy_state=None,
                           allow_protected_append_writes=None, public_network_access=None, dns_endpoint_type=None,
                           enable_smb_oauth=None, zones=None, zone_placement_policy=None,
                           enable_blob_geo_priority_replication=None, publish_ipv6_endpoint=None):
    StorageAccountCreateParameters, Kind, Sku, CustomDomain, AccessTier, Identity, Encryption, NetworkRuleSet = \
        cmd.get_models('StorageAccountCreateParameters', 'Kind', 'Sku', 'CustomDomain', 'AccessTier', 'Identity',
                       'Encryption', 'NetworkRuleSet')
    scf = storage_client_factory(cmd.cli_ctx)

    # check name availability and throw a warning if an account with the same name is found
    # TODO throw error instead of just a warning during the next breaking change window
    StorageAccountCheckNameAvailabilityParameters = cmd.get_models('StorageAccountCheckNameAvailabilityParameters')
    account_name_param = StorageAccountCheckNameAvailabilityParameters(name=account_name,
                                                                       type="Microsoft.Storage/storageAccounts")
    name_is_available = scf.storage_accounts.check_name_availability(account_name_param)
    if name_is_available and not name_is_available.name_available and name_is_available.reason == "AlreadyExists":
        logger.warning("A storage account with the provided name %s is found. "
                       "Will continue to update the existing account.", account_name)

    if kind is None:
        logger.warning("The default kind for created storage account will change to 'StorageV2' from 'Storage' "
                       "in the future")
    params = StorageAccountCreateParameters(sku=Sku(name=sku), kind=Kind(kind), location=location, tags=tags,
                                            encryption=Encryption(key_source="Microsoft.Storage"))
    # TODO: remove this part when server side remove the constraint
    if encryption_services is None:
        params.encryption.services = {'blob': {}}

    if custom_domain:
        params.custom_domain = CustomDomain(name=custom_domain, use_sub_domain=None)

    # Encryption
    if encryption_services:
        params.encryption = Encryption(services=encryption_services)

    if encryption_key_source is not None:
        params.encryption.key_source = encryption_key_source

    if params.encryption.key_source and params.encryption.key_source == "Microsoft.Keyvault":
        if params.encryption.key_vault_properties is None:
            KeyVaultProperties = cmd.get_models('KeyVaultProperties')
            params.encryption.key_vault_properties = KeyVaultProperties(key_name=encryption_key_name,
                                                                        key_vault_uri=encryption_key_vault,
                                                                        key_version=encryption_key_version)

    if identity_type and 'UserAssigned' in identity_type and user_identity_id:
        params.identity = Identity(type=identity_type, user_assigned_identities={user_identity_id: {}})
    elif identity_type:
        params.identity = Identity(type=identity_type)
    if key_vault_user_identity_id is not None or federated_identity_client_id is not None:
        EncryptionIdentity = cmd.get_models('EncryptionIdentity')
        params.encryption.encryption_identity = EncryptionIdentity(
            encryption_user_assigned_identity=key_vault_user_identity_id,
            encryption_federated_identity_client_id=federated_identity_client_id
        )

    if access_tier:
        params.access_tier = AccessTier(access_tier)
    if assign_identity:
        params.identity = Identity(type='SystemAssigned')
    if https_only is not None:
        params.enable_https_traffic_only = https_only
    if enable_hierarchical_namespace is not None:
        params.is_hns_enabled = enable_hierarchical_namespace
    if enable_sftp is not None:
        params.is_sftp_enabled = enable_sftp
    if enable_local_user is not None:
        params.is_local_user_enabled = enable_local_user

    AzureFilesIdentityBasedAuthentication = cmd.get_models('AzureFilesIdentityBasedAuthentication')
    if enable_files_aadds is not None:
        params.azure_files_identity_based_authentication = AzureFilesIdentityBasedAuthentication(
            directory_service_options='AADDS' if enable_files_aadds else 'None')
    if enable_files_aadkerb is not None:
        if enable_files_aadkerb:
            active_directory_properties = None
            if domain_name or domain_guid:
                ActiveDirectoryProperties = cmd.get_models('ActiveDirectoryProperties')
                active_directory_properties = ActiveDirectoryProperties(domain_name=domain_name,
                                                                        domain_guid=domain_guid)
            params.azure_files_identity_based_authentication = AzureFilesIdentityBasedAuthentication(
                directory_service_options='AADKERB',
                active_directory_properties=active_directory_properties)
        else:
            params.azure_files_identity_based_authentication = AzureFilesIdentityBasedAuthentication(
                directory_service_options='None')

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
                                                                    azure_storage_sid=azure_storage_sid,
                                                                    sam_account_name=sam_account_name,
                                                                    account_type=account_type)
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

    if default_share_permission is not None:
        if params.azure_files_identity_based_authentication is None:
            params.azure_files_identity_based_authentication = AzureFilesIdentityBasedAuthentication(
                directory_service_options='None')
        params.azure_files_identity_based_authentication.default_share_permission = default_share_permission

    if enable_smb_oauth is not None:
        if params.azure_files_identity_based_authentication is None:
            params.azure_files_identity_based_authentication = AzureFilesIdentityBasedAuthentication(
                directory_service_options='None')
        params.azure_files_identity_based_authentication.smb_o_auth_settings = {
            "is_smb_o_auth_enabled": enable_smb_oauth
        }

    if enable_large_file_share:
        LargeFileSharesState = cmd.get_models('LargeFileSharesState')
        params.large_file_shares_state = LargeFileSharesState("Enabled")

    if NetworkRuleSet and (bypass or default_action or subnet):
        virtual_network_rules = None
        if bypass and not default_action:
            raise CLIError('incorrect usage: --default-action ACTION [--bypass SERVICE ...]')
        if subnet:
            from azure.mgmt.core.tools import is_valid_resource_id
            if not is_valid_resource_id(subnet):
                raise CLIError("Expected fully qualified resource ID: got '{}'".format(subnet))
            VirtualNetworkRule = cmd.get_models('VirtualNetworkRule')
            virtual_network_rules = [VirtualNetworkRule(virtual_network_resource_id=subnet,
                                                        action=action)]
        params.network_rule_set = NetworkRuleSet(
            bypass=bypass, default_action=default_action, ip_rules=None,
            virtual_network_rules=virtual_network_rules)

    if encryption_key_type_for_table is not None or encryption_key_type_for_queue is not None:
        EncryptionServices = cmd.get_models('EncryptionServices')
        EncryptionService = cmd.get_models('EncryptionService')
        if params.encryption is None:
            params.encryption = Encryption()
        if params.encryption.services is None:
            params.encryption.services = EncryptionServices()
        if encryption_key_type_for_table is not None:
            table_encryption_service = EncryptionService(enabled=True, key_type=encryption_key_type_for_table)
            if isinstance(params.encryption.services, dict):
                params.encryption.services["table"] = table_encryption_service
            else:
                params.encryption.services.table = table_encryption_service
        if encryption_key_type_for_queue is not None:
            queue_encryption_service = EncryptionService(enabled=True, key_type=encryption_key_type_for_queue)
            if isinstance(params.encryption.services, dict):
                params.encryption.services["queue"] = queue_encryption_service
            else:
                params.encryption.services.queue = queue_encryption_service

    if any([routing_choice, publish_microsoft_endpoints, publish_internet_endpoints]):
        RoutingPreference = cmd.get_models('RoutingPreference')
        params.routing_preference = RoutingPreference(
            routing_choice=routing_choice,
            publish_microsoft_endpoints=publish_microsoft_endpoints,
            publish_internet_endpoints=publish_internet_endpoints
        )
    if allow_blob_public_access is not None:
        params.allow_blob_public_access = allow_blob_public_access

    if require_infrastructure_encryption:
        params.encryption.require_infrastructure_encryption = require_infrastructure_encryption

    if min_tls_version:
        if min_tls_version in ['TLS1_0', 'TLS1_1']:
            logger.warning('TLS 1.0 and TLS 1.1 have been retired on 2026/02/03, will use TLS 1.2 instead.')
            min_tls_version = 'TLS1_2'
        params.minimum_tls_version = min_tls_version

    if allow_shared_key_access is not None:
        params.allow_shared_key_access = allow_shared_key_access

    if edge_zone is not None:
        ExtendedLocation, ExtendedLocationTypes = cmd.get_models('ExtendedLocation', 'ExtendedLocationTypes')
        params.extended_location = ExtendedLocation(name=edge_zone,
                                                    type=ExtendedLocationTypes.EDGE_ZONE)

    if key_expiration_period_in_days is not None:
        KeyPolicy = cmd.get_models('KeyPolicy')
        params.key_policy = KeyPolicy(key_expiration_period_in_days=key_expiration_period_in_days)

    if sas_expiration_period is not None or sas_expiration_action is not None:
        SasPolicy = cmd.get_models('SasPolicy')
        if sas_expiration_period is None and sas_expiration_action is not None:
            from azure.cli.core.azclierror import InvalidArgumentValueError
            raise InvalidArgumentValueError('--sas-expiration-action can only be specified together with'
                                            ' --sas-expiration-period')
        if sas_expiration_action is None:
            sas_expiration_action = 'Log'
        params.sas_policy = SasPolicy(sas_expiration_period=sas_expiration_period,
                                      expiration_action=sas_expiration_action)

    if allow_cross_tenant_replication is not None:
        params.allow_cross_tenant_replication = allow_cross_tenant_replication

    if enable_nfs_v3 is not None:
        params.enable_nfs_v3 = enable_nfs_v3

    if enable_alw is not None:
        ImmutableStorageAccount = cmd.get_models('ImmutableStorageAccount')
        AccountImmutabilityPolicyProperties = cmd.get_models('AccountImmutabilityPolicyProperties')
        immutability_policy = None

        if any([immutability_period_since_creation_in_days, immutability_policy_state,
                allow_protected_append_writes is not None]):
            immutability_policy = AccountImmutabilityPolicyProperties(
                immutability_period_since_creation_in_days=immutability_period_since_creation_in_days,
                state=immutability_policy_state,
                allow_protected_append_writes=allow_protected_append_writes
            )

        params.immutable_storage_with_versioning = ImmutableStorageAccount(enabled=enable_alw,
                                                                           immutability_policy=immutability_policy)

    if public_network_access is not None:
        params.public_network_access = public_network_access

    if dns_endpoint_type is not None:
        params.dns_endpoint_type = dns_endpoint_type

    if zones is not None:
        params.zones = zones

    if zone_placement_policy is not None:
        Placement = cmd.get_models('Placement')
        params.placement = Placement(zone_placement_policy=zone_placement_policy)

    if enable_blob_geo_priority_replication is not None:
        GeoPriorityReplicationStatus = cmd.get_models('GeoPriorityReplicationStatus')
        params.geo_priority_replication_status = GeoPriorityReplicationStatus(is_blob_enabled=enable_blob_geo_priority_replication)

    if publish_ipv6_endpoint is not None:
        DualStackEndpointPreference = cmd.get_models('DualStackEndpointPreference')
        params.dual_stack_endpoint_preference = DualStackEndpointPreference(
            publish_ipv6_endpoint=publish_ipv6_endpoint
        )

    return scf.storage_accounts.begin_create(resource_group_name, account_name, params)


def list_storage_accounts(cmd, resource_group_name=None):
    scf = storage_client_factory(cmd.cli_ctx)
    if resource_group_name:
        accounts = scf.storage_accounts.list_by_resource_group(resource_group_name)
    else:
        accounts = scf.storage_accounts.list()
    return list(accounts)


def show_storage_account_connection_string(cmd, resource_group_name, account_name, protocol='https', blob_endpoint=None,
                                           file_endpoint=None, queue_endpoint=None, table_endpoint=None, sas_token=None,
                                           key_name='key1'):

    endpoint_suffix = cmd.cli_ctx.cloud.suffixes.storage_endpoint
    connection_string = 'DefaultEndpointsProtocol={};EndpointSuffix={}'.format(protocol, endpoint_suffix)
    if account_name is not None:
        scf = cf_sa_for_keys(cmd.cli_ctx, None)
        obj = scf.list_keys(resource_group_name, account_name, logging_enable=False)  # pylint: disable=no-member
        try:
            keys = [obj.keys[0].value, obj.keys[1].value]  # pylint: disable=no-member
        except AttributeError:
            # Older API versions have a slightly different structure
            keys = [obj.key1, obj.key2]  # pylint: disable=no-member

        sa = scf.get_properties(resource_group_name, account_name)
        if getattr(sa, 'primary_endpoints') is not None:
            if not blob_endpoint:
                blob_endpoint = getattr(sa.primary_endpoints, 'blob', None)
            if not file_endpoint:
                file_endpoint = getattr(sa.primary_endpoints, 'file', None)
            if not queue_endpoint:
                queue_endpoint = getattr(sa.primary_endpoints, 'queue', None)
            if not table_endpoint:
                table_endpoint = getattr(sa.primary_endpoints, 'table', None)

        connection_string = '{}{}{}'.format(
            connection_string,
            ';AccountName={}'.format(account_name),
            ';AccountKey={}'.format(keys[0] if key_name == 'key1' else keys[1]))  # pylint: disable=no-member

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
    from azure.mgmt.core.tools import parse_resource_id
    result = parse_resource_id(account_id)
    return scf.storage_accounts.get_properties(result['resource_group'], result['name'])


# pylint: disable=too-many-locals, too-many-statements, too-many-branches, too-many-boolean-expressions, line-too-long
def update_storage_account(cmd, instance, sku=None, tags=None, custom_domain=None, use_subdomain=None,
                           encryption_services=None, encryption_key_source=None, encryption_key_version=None,
                           encryption_key_name=None, encryption_key_vault=None, enable_files_aadkerb=None,
                           access_tier=None, https_only=None, enable_sftp=None, enable_local_user=None,
                           enable_files_aadds=None, assign_identity=False,
                           bypass=None, default_action=None, enable_large_file_share=None, enable_files_adds=None,
                           domain_name=None, net_bios_domain_name=None, forest_name=None, domain_guid=None,
                           domain_sid=None, azure_storage_sid=None, sam_account_name=None, account_type=None,
                           routing_choice=None, publish_microsoft_endpoints=None, publish_internet_endpoints=None,
                           allow_blob_public_access=None, min_tls_version=None, allow_shared_key_access=None,
                           identity_type=None, user_identity_id=None,
                           key_vault_user_identity_id=None, federated_identity_client_id=None,
                           sas_expiration_action=None, sas_expiration_period=None, key_expiration_period_in_days=None,
                           allow_cross_tenant_replication=None, default_share_permission=None,
                           immutability_period_since_creation_in_days=None, immutability_policy_state=None,
                           allow_protected_append_writes=None, public_network_access=None, upgrade_to_storagev2=None,
                           yes=None, enable_smb_oauth=None, zones=None, zone_placement_policy=None,
                           enable_blob_geo_priority_replication=None, publish_ipv6_endpoint=None):
    StorageAccountUpdateParameters, Sku, CustomDomain, AccessTier, Identity, Encryption, NetworkRuleSet, Kind = \
        cmd.get_models('StorageAccountUpdateParameters', 'Sku', 'CustomDomain', 'AccessTier', 'Identity', 'Encryption',
                       'NetworkRuleSet', 'Kind')

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

    if encryption.key_source and encryption.key_source == "Microsoft.Keyvault":
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

    warning_message = None
    if upgrade_to_storagev2:
        if instance.kind == Kind.STORAGE:
            warning_message = "Upgrading a General Purpose v1 storage account to a general-purpose v2 account is " \
                              "free. You may specify the desired account tier during the upgrade process. " \
                              "If an account tier is not specified on upgrade, the default account tier of the " \
                              "upgraded account will be Hot. \nHowever, changing the storage access tier after the " \
                              "upgrade may result in changes to your bill so it is recommended to specify the new " \
                              "account tier during upgrade. \n" \
                              "See (http://go.microsoft.com/fwlink/?LinkId=786482) to learn more."
        elif instance.kind == Kind.BLOB_STORAGE:
            warning_message = "Upgrading a BlobStorage account to a general-purpose v2 account is free as long as " \
                              "the upgraded account's tier remains unchanged. If an account tier is not specified " \
                              "on upgrade, the default account tier of the upgraded account will be Hot. \nIf there " \
                              "are account access tier changes as part of the upgrade, there will be charges " \
                              "associated with moving blobs as part of the account access tier change. \n" \
                              "See (http://go.microsoft.com/fwlink/?LinkId=786482) to learn more."
            if access_tier is None:
                access_tier = AccessTier.HOT
        elif access_tier is not None:
            warning_message = "Changing the access tier may result in additional charges. \n" \
                              "See (http://go.microsoft.com/fwlink/?LinkId=786482) to learn more."
    else:
        if access_tier is not None:
            warning_message = "Changing the access tier may result in additional charges. \n" \
                              "See (http://go.microsoft.com/fwlink/?LinkId=786482) to learn more."

    if warning_message:
        user_confirmation(warning_message, yes)

    params = StorageAccountUpdateParameters(
        sku=Sku(name=sku) if sku is not None else instance.sku,
        tags=tags if tags is not None else instance.tags,
        custom_domain=domain,
        encryption=encryption,
        access_tier=AccessTier(access_tier) if access_tier is not None else instance.access_tier,
        enable_https_traffic_only=https_only if https_only is not None else instance.enable_https_traffic_only
    )

    if upgrade_to_storagev2:
        params.kind = Kind.STORAGE_V2

    if identity_type and 'UserAssigned' in identity_type and user_identity_id:
        user_assigned_identities = {user_identity_id: {}}
        if instance.identity and instance.identity.user_assigned_identities:
            for item in instance.identity.user_assigned_identities:
                if item != user_identity_id:
                    user_assigned_identities[item] = None
        params.identity = Identity(type=identity_type, user_assigned_identities=user_assigned_identities)
    elif identity_type:
        params.identity = Identity(type=identity_type)

    if key_vault_user_identity_id is not None or federated_identity_client_id is not None:
        original_encryption_identity = params.encryption.encryption_identity if params.encryption else None
        EncryptionIdentity = cmd.get_models('EncryptionIdentity')
        if not original_encryption_identity:
            original_encryption_identity = EncryptionIdentity()
        params.encryption.encryption_identity = EncryptionIdentity(
            encryption_user_assigned_identity=key_vault_user_identity_id if key_vault_user_identity_id else original_encryption_identity.encryption_user_assigned_identity,
            encryption_federated_identity_client_id=federated_identity_client_id if federated_identity_client_id else original_encryption_identity.encryption_federated_identity_client_id
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
            if origin_storage_account.azure_files_identity_based_authentication and \
                    origin_storage_account.azure_files_identity_based_authentication.directory_service_options == 'AADKERB':
                raise CLIError("The Storage account already enabled AzureActiveDirectoryKerberosForFile, "
                               "please disable it by running this cmdlets with \"--enable-files-aadkerb false\" "
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

    if enable_files_aadkerb is not None:
        if enable_files_aadkerb:  # enable AADKERB
            if instance.azure_files_identity_based_authentication and \
                    instance.azure_files_identity_based_authentication.directory_service_options \
                    == 'AADDS':
                raise CLIError("The Storage account already enabled AzureActiveDirectoryDomainServicesForFile, "
                               "please disable it by running this cmdlets with \"--enable-files-aadds false\" "
                               "before enable AzureActiveDirectoryKerberosForFile.")
            if instance.azure_files_identity_based_authentication and \
                    instance.azure_files_identity_based_authentication.directory_service_options == 'AD':
                raise CLIError("The Storage account already enabled ActiveDirectoryDomainServicesForFile, "
                               "please disable it by running this cmdlets with \"--enable-files-adds false\" "
                               "before enable AzureActiveDirectoryKerberosForFile.")
            active_directory_properties = None
            if domain_name or domain_guid:
                ActiveDirectoryProperties = cmd.get_models('ActiveDirectoryProperties')
                active_directory_properties = ActiveDirectoryProperties(domain_name=domain_name,
                                                                        domain_guid=domain_guid)
            params.azure_files_identity_based_authentication = AzureFilesIdentityBasedAuthentication(
                directory_service_options='AADKERB',
                active_directory_properties=active_directory_properties)

        else:  # disable AADKERB
            # Only disable AADKERB and keep others unchanged
            if not instance.azure_files_identity_based_authentication or \
                    instance.azure_files_identity_based_authentication.directory_service_options == 'AADKERB':
                params.azure_files_identity_based_authentication = AzureFilesIdentityBasedAuthentication(
                    directory_service_options='None')
            else:
                params.azure_files_identity_based_authentication = \
                    instance.azure_files_identity_based_authentication

    if enable_files_adds is not None:
        ActiveDirectoryProperties = cmd.get_models('ActiveDirectoryProperties')
        if enable_files_adds:  # enable AD
            if not (domain_name and net_bios_domain_name and forest_name and domain_guid and domain_sid and
                    azure_storage_sid):
                raise CLIError("To enable ActiveDirectoryDomainServicesForFile, user must specify all of: "
                               "--domain-name, --net-bios-domain-name, --forest-name, --domain-guid, --domain-sid and "
                               "--azure_storage_sid arguments in Azure Active Directory Properties Argument group.")
            if instance.azure_files_identity_based_authentication and \
                    instance.azure_files_identity_based_authentication.directory_service_options \
                    == 'AADDS':
                raise CLIError("The Storage account already enabled AzureActiveDirectoryDomainServicesForFile, "
                               "please disable it by running this cmdlets with \"--enable-files-aadds false\" "
                               "before enable ActiveDirectoryDomainServicesForFile.")
            if instance.azure_files_identity_based_authentication and \
                    instance.azure_files_identity_based_authentication.directory_service_options == 'AADKERB':
                raise CLIError("The Storage account already enabled AzureActiveDirectoryKerberosForFile, "
                               "please disable it by running this cmdlets with \"--enable-files-aadkerb false\" "
                               "before enable ActiveDirectoryDomainServicesForFile.")
            active_directory_properties = ActiveDirectoryProperties(domain_name=domain_name,
                                                                    net_bios_domain_name=net_bios_domain_name,
                                                                    forest_name=forest_name, domain_guid=domain_guid,
                                                                    domain_sid=domain_sid,
                                                                    azure_storage_sid=azure_storage_sid,
                                                                    sam_account_name=sam_account_name,
                                                                    account_type=account_type)
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
            if not instance.azure_files_identity_based_authentication or \
                    instance.azure_files_identity_based_authentication.directory_service_options == 'AD':
                params.azure_files_identity_based_authentication = AzureFilesIdentityBasedAuthentication(
                    directory_service_options='None')
            else:
                params.azure_files_identity_based_authentication = \
                    instance.azure_files_identity_based_authentication
    if default_share_permission is not None:
        if params.azure_files_identity_based_authentication is None:
            params.azure_files_identity_based_authentication = AzureFilesIdentityBasedAuthentication(
                directory_service_options='None') if instance.azure_files_identity_based_authentication is None \
                else instance.azure_files_identity_based_authentication
        params.azure_files_identity_based_authentication.default_share_permission = default_share_permission

    if enable_smb_oauth is not None:
        if params.azure_files_identity_based_authentication is None:
            params.azure_files_identity_based_authentication = AzureFilesIdentityBasedAuthentication(
                directory_service_options='None') if instance.azure_files_identity_based_authentication is None \
                else instance.azure_files_identity_based_authentication
        params.azure_files_identity_based_authentication.smb_o_auth_settings = {
            "is_smb_o_auth_enabled": enable_smb_oauth
        }

    if assign_identity:
        params.identity = Identity(type='SystemAssigned')
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
            params.routing_preference.publish_microsoft_endpoints = publish_microsoft_endpoints
        if publish_internet_endpoints is not None:
            params.routing_preference.publish_internet_endpoints = publish_internet_endpoints

    if allow_blob_public_access is not None:
        params.allow_blob_public_access = allow_blob_public_access

    if min_tls_version:
        if min_tls_version in ['TLS1_0', 'TLS1_1']:
            logger.warning('TLS 1.0 and TLS 1.1 have been retired on 2026/02/03, will use TLS 1.2 instead.')
            min_tls_version = 'TLS1_2'
        params.minimum_tls_version = min_tls_version

    if allow_shared_key_access is not None:
        params.allow_shared_key_access = allow_shared_key_access

    if key_expiration_period_in_days is not None:
        KeyPolicy = cmd.get_models('KeyPolicy')
        params.key_policy = KeyPolicy(key_expiration_period_in_days=key_expiration_period_in_days)

    if sas_expiration_period is not None or sas_expiration_action is not None:
        SasPolicy = cmd.get_models('SasPolicy')
        if sas_expiration_period is None and sas_expiration_action is not None:
            from azure.cli.core.azclierror import InvalidArgumentValueError
            raise InvalidArgumentValueError('--sas-expiration-action can only be specified together '
                                            'with --sas-expiration-period')
        if sas_expiration_action is None:
            sas_expiration_action = 'Log'
            if instance.sas_policy is not None and instance.sas_policy.expiration_action is not None:
                sas_expiration_action = instance.sas_policy.expiration_action

        params.sas_policy = SasPolicy(sas_expiration_period=sas_expiration_period,
                                      expiration_action=sas_expiration_action)

    if allow_cross_tenant_replication is not None:
        params.allow_cross_tenant_replication = allow_cross_tenant_replication

    if any([immutability_period_since_creation_in_days, immutability_policy_state, allow_protected_append_writes is not None]):
        ImmutableStorageAccount = cmd.get_models('ImmutableStorageAccount')
        AccountImmutabilityPolicyProperties = cmd.get_models('AccountImmutabilityPolicyProperties')
        immutability_policy = None

        immutability_policy = AccountImmutabilityPolicyProperties(
            immutability_period_since_creation_in_days=immutability_period_since_creation_in_days,
            state=immutability_policy_state,
            allow_protected_append_writes=allow_protected_append_writes
        )

        params.immutable_storage_with_versioning = ImmutableStorageAccount(enabled=None,
                                                                           immutability_policy=immutability_policy)

    if public_network_access is not None:
        params.public_network_access = public_network_access

    if enable_sftp is not None:
        params.is_sftp_enabled = enable_sftp
    if enable_local_user is not None:
        params.is_local_user_enabled = enable_local_user

    if zones is not None:
        params.zones = zones

    if zone_placement_policy is not None:
        Placement = cmd.get_models('Placement')
        params.placement = Placement(zone_placement_policy=zone_placement_policy)

    if enable_blob_geo_priority_replication is not None:
        GeoPriorityReplicationStatus = cmd.get_models('GeoPriorityReplicationStatus')
        params.geo_priority_replication_status = GeoPriorityReplicationStatus(is_blob_enabled=enable_blob_geo_priority_replication)

    if publish_ipv6_endpoint is not None:
        DualStackEndpointPreference = cmd.get_models('DualStackEndpointPreference')
        params.dual_stack_endpoint_preference = DualStackEndpointPreference(
            publish_ipv6_endpoint=publish_ipv6_endpoint
        )

    return params


def list_network_rules(client, resource_group_name, account_name):
    sa = client.get_properties(resource_group_name, account_name)
    rules = sa.network_rule_set
    delattr(rules, 'bypass')
    delattr(rules, 'default_action')
    return rules


def add_network_rule(cmd, client, resource_group_name, account_name, action='Allow', subnet=None,
                     vnet_name=None, ip_address=None, ipv6_address=None, tenant_id=None, resource_id=None):  # pylint: disable=unused-argument
    sa = client.get_properties(resource_group_name, account_name)
    rules = sa.network_rule_set
    if not subnet and not ip_address and not ipv6_address:
        logger.warning('No subnet or ip address supplied.')

    if subnet:
        from azure.mgmt.core.tools import is_valid_resource_id
        if not is_valid_resource_id(subnet):
            raise CLIError("Expected fully qualified resource ID: got '{}'".format(subnet))
        VirtualNetworkRule = cmd.get_models('VirtualNetworkRule')
        if not rules.virtual_network_rules:
            rules.virtual_network_rules = []
        rules.virtual_network_rules = [r for r in rules.virtual_network_rules
                                       if r.virtual_network_resource_id.lower() != subnet.lower()]
        rules.virtual_network_rules.append(VirtualNetworkRule(virtual_network_resource_id=subnet, action=action))

    if ip_address:
        rules.ip_rules = _process_add_ip(cmd, ip_address, rules.ip_rules, action=action, ipv6=False)

    if ipv6_address:
        rules.ipv6_rules = _process_add_ip(cmd, ipv6_address, rules.ipv6_rules, action=action, ipv6=True)

    if resource_id:
        ResourceAccessRule = cmd.get_models('ResourceAccessRule')
        if not rules.resource_access_rules:
            rules.resource_access_rules = []
        rules.resource_access_rules = [r for r in rules.resource_access_rules if r.resource_id !=
                                       resource_id or r.tenant_id != tenant_id]
        rules.resource_access_rules.append(ResourceAccessRule(tenant_id=tenant_id, resource_id=resource_id))

    StorageAccountUpdateParameters = cmd.get_models('StorageAccountUpdateParameters')
    params = StorageAccountUpdateParameters(network_rule_set=rules)
    return client.update(resource_group_name, account_name, params)


def _process_add_ip(cmd, ip_address, ip_rules, action, ipv6=False):
    IpRule = cmd.get_models('IPRule')
    if not ip_rules:
        ip_rules = []
    for ip in ip_address:
        to_modify = True
        for x in ip_rules:
            existing_ip_network = ip_network(x.ip_address_or_range)
            new_ip_network = ip_network(ip)
            if new_ip_network.overlaps(existing_ip_network):
                logger.warning("IP%s/CIDR %s overlaps with %s, which exists already. Not adding duplicates.",
                               "v6" if ipv6 else "v4", ip, x.ip_address_or_range)
                to_modify = False
                break
        if to_modify:
            ip_rules.append(IpRule(ip_address_or_range=ip, action=action))
    return ip_rules


def remove_network_rule(cmd, client, resource_group_name, account_name, ip_address=None, ipv6_address=None, subnet=None,
                        vnet_name=None, tenant_id=None, resource_id=None):  # pylint: disable=unused-argument
    sa = client.get_properties(resource_group_name, account_name)
    rules = sa.network_rule_set
    if subnet:
        rules.virtual_network_rules = [x for x in rules.virtual_network_rules
                                       if not x.virtual_network_resource_id.endswith(subnet)]
    if ip_address:
        to_remove = [ip_network(x) for x in ip_address]
        rules.ip_rules = list(filter(lambda x: all(ip_network(x.ip_address_or_range) != i for i in to_remove),
                                     rules.ip_rules))

    if ipv6_address:
        to_remove = [ip_network(x) for x in ipv6_address]
        rules.ipv6_rules = list(filter(lambda x: all(ip_network(x.ip_address_or_range) != i for i in to_remove),
                                       rules.ipv6_rules))

    if resource_id:
        rules.resource_access_rules = [x for x in rules.resource_access_rules if
                                       not (x.tenant_id == tenant_id and x.resource_id == resource_id)]

    StorageAccountUpdateParameters = cmd.get_models('StorageAccountUpdateParameters')
    params = StorageAccountUpdateParameters(network_rule_set=rules)
    return client.update(resource_group_name, account_name, params)


def _update_private_endpoint_connection_status(cmd, client, resource_group_name, account_name,
                                               private_endpoint_connection_name, is_approved=True, description=None):
    from azure.core.exceptions import HttpResponseError
    PrivateEndpointServiceConnectionStatus = cmd.get_models('PrivateEndpointServiceConnectionStatus')

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
    except HttpResponseError as ex:
        if ex.response.status_code == 400:
            if new_status == "Approved" and old_status == "Rejected":
                raise CLIError(ex.response, "You cannot approve the connection request after rejection. Please create "
                                            "a new connection for approval.")
            if new_status == "Approved" and old_status == "Approved":
                raise CLIError(ex.response, "Your connection is already approved. No need to approve again.")
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


def create_management_policies(cmd, client, resource_group_name, account_name, policy):
    if os.path.exists(policy):
        policy = get_file_json(policy)
    else:
        policy = shell_safe_json_parse(policy)
    ManagementPolicyName = cmd.get_models('ManagementPolicyName')
    management_policy = cmd.get_models('ManagementPolicy')(policy=policy)
    return client.create_or_update(resource_group_name, account_name,
                                   ManagementPolicyName.DEFAULT, properties=management_policy)


def get_management_policy(cmd, client, resource_group_name, account_name):
    ManagementPolicyName = cmd.get_models('ManagementPolicyName')
    return client.get(resource_group_name, account_name, ManagementPolicyName.DEFAULT)


def delete_management_policy(cmd, client, resource_group_name, account_name):
    ManagementPolicyName = cmd.get_models('ManagementPolicyName')
    return client.delete(resource_group_name, account_name, ManagementPolicyName.DEFAULT)


def update_management_policies(cmd, client, resource_group_name, account_name, parameters=None):
    ManagementPolicyName = cmd.get_models('ManagementPolicyName')
    return client.create_or_update(resource_group_name, account_name,
                                   ManagementPolicyName.DEFAULT, properties=parameters)


# TODO: support updating other properties besides 'enable_change_feed,delete_retention_policy'
def update_blob_service_properties(cmd, instance, enable_change_feed=None, change_feed_retention_days=None,
                                   enable_delete_retention=None, delete_retention_days=None,
                                   enable_restore_policy=None, restore_days=None,
                                   enable_versioning=None, enable_container_delete_retention=None,
                                   container_delete_retention_days=None, default_service_version=None,
                                   enable_last_access_tracking=None):
    if enable_change_feed is not None:
        if enable_change_feed is False:
            change_feed_retention_days = None
        instance.change_feed = cmd.get_models('ChangeFeed')(
            enabled=enable_change_feed, retention_in_days=change_feed_retention_days)

    if enable_container_delete_retention is not None:
        if enable_container_delete_retention is False:
            container_delete_retention_days = None
        instance.container_delete_retention_policy = cmd.get_models('DeleteRetentionPolicy')(
            enabled=enable_container_delete_retention, days=container_delete_retention_days)

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

    if default_service_version is not None:
        instance.default_service_version = default_service_version

    # Update last access time tracking policy
    if enable_last_access_tracking is not None:
        LastAccessTimeTrackingPolicy = cmd.get_models('LastAccessTimeTrackingPolicy')
        instance.last_access_time_tracking_policy = LastAccessTimeTrackingPolicy(enable=enable_last_access_tracking)

    return instance


def update_file_service_properties(cmd, instance, enable_delete_retention=None,
                                   delete_retention_days=None, enable_smb_multichannel=None,
                                   versions=None, authentication_methods=None, kerberos_ticket_encryption=None,
                                   channel_encryption=None, require_smb_encryption_in_transit=None,
                                   require_nfs_encryption_in_transit=None):
    from azure.cli.core.azclierror import ValidationError
    params = {}
    # set delete retention policy according input
    if enable_delete_retention is not None:
        if enable_delete_retention is False:
            delete_retention_days = None
        instance.share_delete_retention_policy = cmd.get_models('DeleteRetentionPolicy')(
            enabled=enable_delete_retention, days=delete_retention_days)

    # If already enabled, only update days
    if enable_delete_retention is None and delete_retention_days is not None:
        if instance.share_delete_retention_policy is not None and instance.share_delete_retention_policy.enabled:
            instance.share_delete_retention_policy.days = delete_retention_days
        else:
            raise ValidationError(
                "Delete Retention Policy hasn't been enabled, and you cannot set delete retention days. "
                "Please set --enable-delete-retention as true to enable Delete Retention Policy.")

    # Fix the issue in server when delete_retention_policy.enabled=False, the returned days is 0
    # TODO: remove it when server side return null not 0 for days
    if instance.share_delete_retention_policy is not None and instance.share_delete_retention_policy.enabled is False:
        instance.share_delete_retention_policy.days = None
    if instance.share_delete_retention_policy:
        params['share_delete_retention_policy'] = instance.share_delete_retention_policy

    # set protocol settings
    smbSetting = cmd.get_models('SmbSetting')
    nfsSetting = cmd.get_models('NfsSetting')
    if not instance.protocol_settings:
        instance.protocol_settings = cmd.get_models('ProtocolSettings')(smb=smbSetting(), nfs=nfsSetting())
    else:
        if not instance.protocol_settings.smb:
            instance.protocol_settings.smb = smbSetting()
        if not instance.protocol_settings.nfs:
            instance.protocol_settings.nfs = nfsSetting()

    if enable_smb_multichannel is not None:
        instance.protocol_settings.smb.multichannel = cmd.get_models('Multichannel')(enabled=enable_smb_multichannel)
    if versions is not None:
        instance.protocol_settings.smb.versions = versions
    if authentication_methods is not None:
        instance.protocol_settings.smb.authentication_methods = authentication_methods
    if kerberos_ticket_encryption is not None:
        instance.protocol_settings.smb.kerberos_ticket_encryption = kerberos_ticket_encryption
    if channel_encryption is not None:
        instance.protocol_settings.smb.channel_encryption = channel_encryption
    if require_smb_encryption_in_transit is not None:
        instance.protocol_settings.smb.encryption_in_transit = (
            cmd.get_models('EncryptionInTransit')(required=require_smb_encryption_in_transit))
    if require_nfs_encryption_in_transit is not None:
        instance.protocol_settings.nfs.encryption_in_transit = (
            cmd.get_models('EncryptionInTransit')(required=require_nfs_encryption_in_transit))

    if any(instance.protocol_settings.smb.__dict__.values()) or any(instance.protocol_settings.nfs.__dict__.values()):
        params['protocol_settings'] = instance.protocol_settings

    return params


def create_encryption_scope(cmd, client, resource_group_name, account_name, encryption_scope_name,
                            key_source=None, key_uri=None, require_infrastructure_encryption=None):
    EncryptionScope = cmd.get_models('EncryptionScope')

    if key_source:
        encryption_scope = EncryptionScope(source=key_source)

    if key_uri:
        EncryptionScopeKeyVaultProperties = cmd.get_models('EncryptionScopeKeyVaultProperties')
        encryption_scope.key_vault_properties = EncryptionScopeKeyVaultProperties(key_uri=key_uri)

    if require_infrastructure_encryption is not None:
        encryption_scope.require_infrastructure_encryption = require_infrastructure_encryption

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


def list_encryption_scope(client, resource_group_name, account_name,
                          maxpagesize=None, marker=None, filter=None, include=None):  # pylint: disable=redefined-builtin
    generator = client.list(resource_group_name, account_name, maxpagesize=maxpagesize, filter=filter, include=include)
    pages = generator.by_page(continuation_token=marker)

    result = list(next(pages))
    if pages.continuation_token:
        next_marker = {"nextMarker": pages.continuation_token}
        result.append(next_marker)

    return result


# pylint: disable=no-member
def create_or_policy(cmd, client, account_name, resource_group_name=None, properties=None, source_account=None,
                     destination_account=None, policy_id="default", rule_id=None, source_container=None,
                     destination_container=None, min_creation_time=None, prefix_match=None, enable_metrics=None,
                     priority_replication=None):
    from azure.core.exceptions import HttpResponseError
    ObjectReplicationPolicy = cmd.get_models('ObjectReplicationPolicy')

    if properties is None:
        rules = []
        (ObjectReplicationPolicyRule, ObjectReplicationPolicyFilter, ObjectReplicationPolicyPropertiesMetrics,
         ObjectReplicationPolicyPropertiesPriorityReplication) = \
            cmd.get_models('ObjectReplicationPolicyRule', 'ObjectReplicationPolicyFilter',
                           'ObjectReplicationPolicyPropertiesMetrics',
                           'ObjectReplicationPolicyPropertiesPriorityReplication')
        if source_container and destination_container:
            rule = ObjectReplicationPolicyRule(
                rule_id=rule_id,
                source_container=source_container,
                destination_container=destination_container,
                filters=ObjectReplicationPolicyFilter(prefix_match=prefix_match, min_creation_time=min_creation_time)
            )
            rules.append(rule)
        or_policy = ObjectReplicationPolicy(source_account=source_account,
                                            destination_account=destination_account,
                                            rules=rules,
                                            metrics=ObjectReplicationPolicyPropertiesMetrics(enabled=enable_metrics),
                                            priority_replication=ObjectReplicationPolicyPropertiesPriorityReplication(
                                                enabled=priority_replication))
    else:
        or_policy = properties
    try:
        return client.create_or_update(resource_group_name=resource_group_name, account_name=account_name,
                                       object_replication_policy_id=policy_id, properties=or_policy)
    except HttpResponseError as ex:
        if ex.error.code == 'InvalidRequestPropertyValue' and policy_id == 'default':
            from azure.mgmt.core.tools import parse_resource_id
            if account_name == parse_resource_id(or_policy.source_account)['name']:
                raise CLIError('ValueError: Please specify --policy-id with auto-generated policy id value on '
                               'destination account.')
        raise ex


# pylint: disable=line-too-long
def update_or_policy(cmd, client, parameters, resource_group_name, account_name, object_replication_policy_id=None,
                     properties=None, source_account=None, destination_account=None, enable_metrics=None,
                     priority_replication=None):

    if source_account is not None:
        parameters.source_account = source_account
    if destination_account is not None:
        parameters.destination_account = destination_account

    if properties is not None:
        parameters = properties
        if "policyId" in properties.keys() and properties["policyId"]:
            object_replication_policy_id = properties["policyId"]

    if enable_metrics is not None:
        ObjectReplicationPolicyPropertiesMetrics = cmd.get_models('ObjectReplicationPolicyPropertiesMetrics')
        parameters.metrics = ObjectReplicationPolicyPropertiesMetrics(enabled=enable_metrics)

    if priority_replication is not None:
        ObjectReplicationPolicyPropertiesPriorityReplication = (
            cmd.get_models('ObjectReplicationPolicyPropertiesPriorityReplication'))
        parameters.priority_replication = ObjectReplicationPolicyPropertiesPriorityReplication(enabled=priority_replication)

    return client.create_or_update(resource_group_name=resource_group_name, account_name=account_name,
                                   object_replication_policy_id=object_replication_policy_id, properties=parameters)


def get_or_policy(client, resource_group_name, account_name, policy_id='default'):
    return client.get(resource_group_name=resource_group_name, account_name=account_name,
                      object_replication_policy_id=policy_id)


def add_or_rule(cmd, client, resource_group_name, account_name, policy_id,
                source_container, destination_container, min_creation_time=None, prefix_match=None):

    """
    Initialize rule for or policy
    """
    policy_properties = client.get(resource_group_name, account_name, policy_id)

    ObjectReplicationPolicyRule, ObjectReplicationPolicyFilter = \
        cmd.get_models('ObjectReplicationPolicyRule', 'ObjectReplicationPolicyFilter')
    new_or_rule = ObjectReplicationPolicyRule(
        source_container=source_container,
        destination_container=destination_container,
        filters=ObjectReplicationPolicyFilter(prefix_match=prefix_match, min_creation_time=min_creation_time)
    )
    policy_properties.rules.append(new_or_rule)
    return client.create_or_update(resource_group_name, account_name, policy_id, policy_properties)


def remove_or_rule(client, resource_group_name, account_name, policy_id, rule_id):

    or_policy = client.get(resource_group_name=resource_group_name,
                           account_name=account_name,
                           object_replication_policy_id=policy_id)

    rule = find_child_item(or_policy, rule_id, path='rules', key_path='rule_id')
    or_policy.rules.remove(rule)

    return client.create_or_update(resource_group_name, account_name, policy_id, or_policy)


def get_or_rule(client, resource_group_name, account_name, policy_id, rule_id):
    policy_properties = client.get(resource_group_name, account_name, policy_id)
    for rule in policy_properties.rules:
        if rule.rule_id == rule_id:
            return rule
    raise CLIError("{} does not exist.".format(rule_id))


def list_or_rules(client, resource_group_name, account_name, policy_id):
    policy_properties = client.get(resource_group_name, account_name, policy_id)
    return policy_properties.rules


def update_or_rule(client, resource_group_name, account_name, policy_id, rule_id, source_container=None,
                   destination_container=None, min_creation_time=None, prefix_match=None):

    policy_properties = client.get(resource_group_name, account_name, policy_id)

    for i, rule in enumerate(policy_properties.rules):
        if rule.rule_id == rule_id:
            if destination_container is not None:
                policy_properties.rules[i].destination_container = destination_container
            if source_container is not None:
                policy_properties.rules[i].source_container = source_container
            if min_creation_time is not None:
                policy_properties.rules[i].filters.min_creation_time = min_creation_time
            if prefix_match is not None:
                policy_properties.rules[i].filters.prefix_match = prefix_match

    client.create_or_update(resource_group_name=resource_group_name, account_name=account_name,
                            object_replication_policy_id=policy_id, properties=policy_properties)

    return get_or_rule(client, resource_group_name=resource_group_name, account_name=account_name,
                       policy_id=policy_id, rule_id=rule_id)


def create_blob_inventory_policy(cmd, client, resource_group_name, account_name, policy):
    if os.path.exists(policy):
        policy = get_file_json(policy)
    else:
        policy = shell_safe_json_parse(policy)

    BlobInventoryPolicy, InventoryRuleType, BlobInventoryPolicyName = \
        cmd.get_models('BlobInventoryPolicy', 'InventoryRuleType', 'BlobInventoryPolicyName')
    properties = BlobInventoryPolicy()
    if 'type' not in policy:
        policy['type'] = InventoryRuleType.INVENTORY
    properties.policy = policy

    return client.create_or_update(resource_group_name=resource_group_name, account_name=account_name,
                                   blob_inventory_policy_name=BlobInventoryPolicyName.DEFAULT, properties=properties)


def delete_blob_inventory_policy(cmd, client, resource_group_name, account_name):
    BlobInventoryPolicyName = cmd.get_models('BlobInventoryPolicyName')
    return client.delete(resource_group_name=resource_group_name, account_name=account_name,
                         blob_inventory_policy_name=BlobInventoryPolicyName.DEFAULT)


def get_blob_inventory_policy(cmd, client, resource_group_name, account_name):
    BlobInventoryPolicyName = cmd.get_models('BlobInventoryPolicyName')
    return client.get(resource_group_name=resource_group_name, account_name=account_name,
                      blob_inventory_policy_name=BlobInventoryPolicyName.DEFAULT)


def update_blob_inventory_policy(cmd, client, resource_group_name, account_name, parameters=None):
    BlobInventoryPolicyName = cmd.get_models('BlobInventoryPolicyName')
    return client.create_or_update(resource_group_name=resource_group_name, account_name=account_name,
                                   blob_inventory_policy_name=BlobInventoryPolicyName.DEFAULT, properties=parameters)


def _generate_local_user(local_user, permission_scope=None, ssh_authorized_key=None,
                         home_directory=None, has_shared_key=None, has_ssh_key=None, has_ssh_password=None):
    if permission_scope is not None:
        local_user.permission_scopes = permission_scope
    if ssh_authorized_key is not None:
        local_user.ssh_authorized_keys = ssh_authorized_key
    if home_directory is not None:
        local_user.home_directory = home_directory
    if has_shared_key is not None:
        local_user.has_shared_key = has_shared_key
    if has_ssh_key is not None:
        local_user.has_ssh_key = has_ssh_key
    if has_ssh_password is not None:
        local_user.has_ssh_password = has_ssh_password


def create_local_user(cmd, client, resource_group_name, account_name, username, permission_scope=None, home_directory=None,
                      has_shared_key=None, has_ssh_key=None, has_ssh_password=None, ssh_authorized_key=None, **kwargs):
    LocalUser = cmd.get_models('LocalUser')
    local_user = LocalUser()

    _generate_local_user(local_user, permission_scope, ssh_authorized_key,
                         home_directory, has_shared_key, has_ssh_key, has_ssh_password)
    return client.create_or_update(resource_group_name=resource_group_name, account_name=account_name,
                                   username=username, properties=local_user)


def update_local_user(cmd, client, resource_group_name, account_name, username, permission_scope=None,
                      home_directory=None, has_shared_key=None, has_ssh_key=None, has_ssh_password=None,
                      ssh_authorized_key=None, **kwargs):
    local_user = client.get(resource_group_name, account_name, username)

    _generate_local_user(local_user, permission_scope, ssh_authorized_key,
                         home_directory, has_shared_key, has_ssh_key, has_ssh_password)
    return client.create_or_update(resource_group_name=resource_group_name, account_name=account_name,
                                   username=username, properties=local_user)


def begin_failover(client, resource_group_name, account_name, failover_type=None, yes=None, **kwargs):
    if not failover_type or failover_type.lower() != "planned":
        message = """
        The secondary cluster will become the primary cluster after failover. Please understand the following impact to your storage account before you initiate the failover:
            1. Please check the Last Sync Time using `az storage account show` with `--expand geoReplicationStats` and check the "geoReplicationStats" property. This is the data you may lose if you initiate the failover.
            2. After the failover, your storage account type will be converted to locally redundant storage (LRS). You can convert your account to use geo-redundant storage (GRS).
            3. Once you re-enable GRS/GZRS for your storage account, Microsoft will replicate data to your new secondary region. Replication time is dependent on the amount of data to replicate. Please note that there are bandwidth charges for the bootstrap. Please refer to doc: https://azure.microsoft.com/pricing/details/bandwidth/
        """
        user_confirmation(message, yes)
    return client.begin_failover(resource_group_name=resource_group_name, account_name=account_name,
                                 failover_type=failover_type, **kwargs)


def list_blob_cors_rules(client, resource_group_name, account_name):
    blob_service_properties = client.get_service_properties(resource_group_name=resource_group_name,
                                                            account_name=account_name)
    if not blob_service_properties.cors or not blob_service_properties.cors.cors_rules:
        return []
    return blob_service_properties.cors.cors_rules


# pylint: disable=dangerous-default-value
def add_blob_cors_rule(cmd, client, resource_group_name, account_name, max_age_in_seconds,
                       allowed_origins, allowed_methods, allowed_headers=[], exposed_headers=[]):
    CorsRules, CorsRule = cmd.get_models('CorsRules', 'CorsRule')
    blob_service_properties = client.get_service_properties(resource_group_name=resource_group_name,
                                                            account_name=account_name)
    if not blob_service_properties.cors or not blob_service_properties.cors.cors_rules:
        blob_service_properties.cors = CorsRules(cors_rules=[])

    new_rule = CorsRule(allowed_origins=allowed_origins, allowed_methods=allowed_methods,
                        allowed_headers=allowed_headers, exposed_headers=exposed_headers,
                        max_age_in_seconds=max_age_in_seconds)
    blob_service_properties.cors.cors_rules.append(new_rule)
    return client.set_service_properties(resource_group_name=resource_group_name,
                                         account_name=account_name,
                                         parameters=blob_service_properties).cors.cors_rules


def clear_blob_cors_rules(cmd, client, resource_group_name, account_name):
    blob_service_properties = client.get_service_properties(resource_group_name=resource_group_name,
                                                            account_name=account_name)
    CorsRules = cmd.get_models('CorsRules')
    blob_service_properties.cors = CorsRules(cors_rules=[])
    client.set_service_properties(resource_group_name=resource_group_name,
                                  account_name=account_name,
                                  parameters=blob_service_properties)
    return []


class AccountMigrationStart(_AccountMigrationStart):
    def pre_operations(self):
        logger.warning('After your request to convert the account’s redundancy configuration is validated, the '
                       'conversion will typically complete in a few days, but can take a few weeks depending on '
                       'current resource demands in the region, account size, and other factors. The conversion can’t '
                       'be stopped after being initiated, and for accounts with geo redundancy a failover can’t be '
                       'initiated while conversion is in progress. The data within the storage account will continue '
                       'to be accessible with no loss of durability or availability.')


def _format_storage_account_id(args_schema):
    from azure.cli.core.aaz import AAZResourceIdArgFormat
    args_schema.account_name._fmt = AAZResourceIdArgFormat(
        template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Storage/"
                 "storageAccounts/{}"
    )
    args_schema.resource_group._required = False


class FileServiceUsage(_FileServiceUsage):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        _format_storage_account_id(args_schema)
        args_schema.file_services_name._registered = False
        args_schema.file_services_name._required = False
        args_schema.file_service_usages_name._registered = False
        args_schema.file_service_usages_name._required = False
        return args_schema

    def pre_operations(self):
        from .._validators import parse_account_name_aaz
        args = self.ctx.args
        parse_account_name_aaz(self, args)
        args.file_services_name = 'default'
        args.file_service_usages_name = 'default'
