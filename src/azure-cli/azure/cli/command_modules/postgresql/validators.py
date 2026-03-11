# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from dateutil import parser
from functools import cmp_to_key
import re
from knack.prompting import prompt_pass, NoTTYException
from knack.util import CLIError
from knack.log import get_logger
import math
from azure.mgmt.core.tools import parse_resource_id, resource_id, is_valid_resource_id, is_valid_resource_name
from azure.cli.core.azclierror import ValidationError, ArgumentUsageError
from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_subscription_id
from azure.cli.core.commands.validators import (
    get_default_location_from_resource_group, validate_tags)
from azure.cli.core.util import parse_proxy_resource_id
from azure.cli.core.profiles import ResourceType
from azure.core.exceptions import HttpResponseError
from ._client_factory import (cf_postgres_flexible_servers,
                              cf_postgres_check_resource_availability)
from ._flexible_server_util import (get_postgres_skus, get_postgres_storage_sizes, get_postgres_tiers,
                                    _is_resource_name)
from ._flexible_server_location_capabilities_util import (get_postgres_location_capability_info,
                                                          get_postgres_server_capability_info,
                                                          get_performance_tiers,
                                                          get_performance_tiers_for_storage)

logger = get_logger(__name__)


# pylint: disable=import-outside-toplevel, raise-missing-from, unbalanced-tuple-unpacking
def _get_resource_group_from_server_name(cli_ctx, server_name):
    """
    Fetch resource group from server name
    :param str server_name: name of the server
    :return: resource group name or None
    :rtype: str
    """

    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_POSTGRESQL).servers
    for server in client.list():
        id_comps = parse_resource_id(server.id)
        if id_comps['name'] == server_name:
            return id_comps['resource_group']
    return None


def get_combined_validator(validators):
    def _final_validator_impl(cmd, namespace):
        # do additional creation validation
        verbs = cmd.name.rsplit(' ', 2)
        if verbs[1] == 'server' and verbs[2] == 'create':
            password_validator(namespace)
            get_default_location_from_resource_group(cmd, namespace)

        validate_tags(namespace)

        for validator in validators:
            validator(namespace)

    return _final_validator_impl


def configuration_value_validator(ns):
    val = ns.value
    if val is None or not val.strip():
        ns.value = None
        ns.source = 'system-default'


def tls_validator(ns):
    if ns.minimal_tls_version:
        if ns.ssl_enforcement is not None and ns.ssl_enforcement != 'Enabled':
            raise CLIError('Cannot specify TLS version when ssl_enforcement is explicitly Disabled')


def password_validator(ns):
    if not ns.administrator_login_password:
        try:
            ns.administrator_login_password = prompt_pass(msg='Admin Password: ')
        except NoTTYException:
            raise CLIError('Please specify password in non-interactive mode.')


def retention_validator(ns):
    if ns.backup_retention is not None:
        val = ns.backup_retention
        if not 7 <= int(val) <= 35:
            raise CLIError('incorrect usage: --backup-retention. Range is 7 to 35 days.')


def node_count_validator(ns):
    if ns.cluster_size is not None:
        val = ns.cluster_size
        if not 1 <= int(val) <= 10:
            raise CLIError('incorrect usage: --node-count. Range is 1 to 10 for an elastic cluster.')


def db_renaming_cluster_validator(ns):
    if ns.database_name is not None and ns.create_cluster != 'ElasticCluster':
        raise ArgumentUsageError('incorrect usage: --database-name can only be '
                                 'used when --cluster-option is set to ElasticCluster.')


# Validates if a subnet id or name have been given by the user. If subnet id is given, vnet-name should not be provided.
def validate_subnet(cmd, namespace):

    subnet = namespace.virtual_network_subnet_id
    subnet_is_id = is_valid_resource_id(subnet)
    vnet = namespace.vnet_name

    if (subnet_is_id and not vnet) or (not subnet and not vnet):
        pass
    elif subnet and not subnet_is_id and vnet:
        namespace.virtual_network_subnet_id = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet,
            child_type_1='subnets',
            child_name_1=subnet)
    else:
        raise CLIError('incorrect usage: [--subnet ID | --subnet NAME --vnet-name NAME]')
    delattr(namespace, 'vnet_name')


def validate_private_endpoint_connection_id(cmd, namespace):
    if namespace.connection_id:
        result = parse_proxy_resource_id(namespace.connection_id)
        namespace.private_endpoint_connection_name = result['child_name_1']
        namespace.server_name = result['name']
        namespace.resource_group_name = result['resource_group']
    if namespace.server_name and not namespace.resource_group_name:
        namespace.resource_group_name = _get_resource_group_from_server_name(cmd.cli_ctx, namespace.server_name)

    if not all([namespace.server_name, namespace.resource_group_name, namespace.private_endpoint_connection_name]):
        raise CLIError('incorrect usage: [--id ID | --name NAME --server-name NAME]')

    del namespace.connection_id


# pylint: disable=too-many-locals
def pg_arguments_validator(db_context, location, tier, sku_name, storage_gb, server_name=None, database_name=None,
                           zone=None, standby_availability_zone=None, high_availability=None,
                           zonal_resiliency=None, allow_same_zone=False, subnet=None,
                           public_access=None, version=None, instance=None, geo_redundant_backup=None,
                           byok_identity=None, byok_key=None, backup_byok_identity=None, backup_byok_key=None,
                           auto_grow=None, performance_tier=None,
                           storage_type=None, iops=None, throughput=None, create_cluster=None, cluster_size=None,
                           password_auth=None, microsoft_entra_auth=None,
                           admin_name=None, admin_id=None, admin_type=None):
    validate_server_name(db_context, server_name, 'Microsoft.DBforPostgreSQL/flexibleServers')
    validate_database_name(database_name)
    is_create = not instance
    if is_create:
        list_location_capability_info = get_postgres_location_capability_info(
            db_context.cmd,
            location)
    else:
        list_location_capability_info = get_postgres_server_capability_info(
            db_context.cmd,
            resource_group=parse_resource_id(instance.id)["resource_group"],
            server_name=instance.name)
    sku_info = list_location_capability_info['sku_info']
    sku_info = {k.lower(): v for k, v in sku_info.items()}
    single_az = list_location_capability_info['single_az']
    geo_backup_supported = list_location_capability_info['geo_backup_supported']
    _cluster_validator(create_cluster, cluster_size, auto_grow, version, tier, instance)
    _network_arg_validator(subnet, public_access)
    _pg_tier_validator(tier, sku_info)  # need to be validated first
    if tier is None and instance is not None:
        tier = instance.sku.tier.lower()
    if "supported_storageV2_size" in sku_info[tier.lower()]:
        supported_storageV2_size = sku_info[tier.lower()]["supported_storageV2_size"]
    else:
        supported_storageV2_size = None
    _pg_storage_type_validator(storage_type, auto_grow, performance_tier,
                               tier, supported_storageV2_size, iops, throughput, instance)
    _pg_storage_performance_tier_validator(performance_tier,
                                           sku_info,
                                           tier,
                                           instance.storage.storage_size_gb if storage_gb is None else storage_gb)
    if geo_redundant_backup is None and instance is not None:
        geo_redundant_backup = instance.backup.geo_redundant_backup
    _pg_georedundant_backup_validator(geo_redundant_backup, geo_backup_supported)
    _pg_storage_validator(storage_gb, sku_info, tier, storage_type, iops, throughput, instance)
    _pg_sku_name_validator(sku_name, sku_info, tier, instance)
    _pg_high_availability_validator(high_availability, zonal_resiliency, allow_same_zone,
                                    standby_availability_zone, zone, tier, single_az, instance)
    _pg_version_validator(version, list_location_capability_info['server_versions'])
    pg_byok_validator(byok_identity, byok_key, backup_byok_identity, backup_byok_key, geo_redundant_backup, instance)
    is_microsoft_entra_auth = bool(microsoft_entra_auth is not None and microsoft_entra_auth.lower() == 'enabled')
    _pg_authentication_validator(password_auth, is_microsoft_entra_auth,
                                 admin_name, admin_id, admin_type, instance)


def _cluster_validator(create_cluster, cluster_size, auto_grow, version, tier, instance):
    if create_cluster == 'ElasticCluster' or (instance and instance.cluster and instance.cluster.cluster_size > 0):
        if instance is None and version != '17':
            raise ValidationError("Elastic cluster is only supported for PostgreSQL version 17.")

        if cluster_size and instance and instance.cluster.cluster_size > cluster_size:
            raise ValidationError('Updating node count cannot be less than the current size of {} nodes.'
                                  .format(instance.cluster.cluster_size))
        if auto_grow and auto_grow.lower() != 'disabled':
            raise ValidationError("Storage Auto-grow is currently not supported for elastic cluster.")
        if tier == 'Burstable':
            raise ValidationError("Burstable tier is currently not supported for elastic cluster.")

    if cluster_size and instance and not instance.cluster:
        raise ValidationError("Node count can only be specified for an elastic cluster.")


def _pg_storage_validator(storage_gb, sku_info, tier, storage_type, iops, throughput, instance):
    is_ssdv2 = storage_type == "PremiumV2_LRS" or instance is not None and instance.storage.type == "PremiumV2_LRS"
    # storage_gb range validation
    if storage_gb is not None:
        if instance is not None:
            original_size = instance.storage.storage_size_gb
            if original_size > storage_gb:
                raise CLIError('Decrease of current storage size isn\'t supported. Current storage size is {} GiB \
                                and you\'re trying to set it to {} GiB.'
                               .format(original_size, storage_gb))
        if not is_ssdv2:
            storage_sizes = get_postgres_storage_sizes(sku_info, tier)
            if storage_gb not in storage_sizes:
                storage_sizes = sorted([int(size) for size in storage_sizes])
                raise CLIError('Incorrect value for --storage-size : Allowed values (in GiB) : {}'
                               .format(storage_sizes))

    # ssdv2 range validation
    if is_ssdv2 and (storage_gb is not None or throughput is not None or iops is not None):
        _valid_ssdv2_range(storage_gb, sku_info, tier, iops, throughput, instance)


def _valid_ssdv2_range(storage_gb, sku_info, tier, iops, throughput, instance):
    storage_gib = storage_gb if storage_gb is not None else instance.storage.storage_size_gb
    storage_iops = iops if iops is not None else instance.storage.iops
    storage_throughput = throughput if throughput is not None else instance.storage.throughput

    # find min and max values for storage
    sku_tier = tier.lower()
    supported_storageV2_size = sku_info[sku_tier]["supported_storageV2_size"]
    min_storage = instance.storage.storage_size_gb if instance is not None else supported_storageV2_size
    max_storage = sku_info[sku_tier]["supported_storageV2_size_max"]
    if not min_storage <= storage_gib <= max_storage:
        raise CLIError('The requested value for storage size does not fall between {} and {} GiB.'
                       .format(min_storage, max_storage))

    storage = storage_gib * 1.07374182
    # find min and max values for IOPS
    min_iops = sku_info[sku_tier]["supported_storageV2_iops"]
    supported_max_iops = sku_info[sku_tier]["supported_storageV2_iops_max"]
    calculated_max_iops = math.floor(max(0, storage - 6) * 500 + min_iops)
    max_iops = min(supported_max_iops, calculated_max_iops)

    if not min_iops <= storage_iops <= max_iops:
        raise CLIError('The requested value for IOPS does not fall between {} and {} operations/sec.'
                       .format(min_iops, max_iops))

    # find min and max values for throughput
    min_throughput = sku_info[sku_tier]["supported_storageV2_throughput"]
    supported_max_throughput = sku_info[sku_tier]["supported_storageV2_throughput_max"]
    if storage > 6:
        max_storage_throughput = math.floor(max(0.25 * storage_iops, min_throughput))
    else:
        max_storage_throughput = min_throughput
    max_throughput = min(supported_max_throughput, max_storage_throughput)

    if not min_throughput <= storage_throughput <= max_throughput:
        raise CLIError('The requested value for throughput does not fall between {} and {} MB/sec.'
                       .format(min_throughput, max_throughput))


def _pg_tier_validator(tier, sku_info):
    if tier:
        tiers = [item.lower() for item in get_postgres_tiers(sku_info)]
        if tier.lower() not in tiers:
            raise CLIError('Incorrect value for --tier. Allowed values : {}'.format(tiers))


def compare_sku_names(sku_1, sku_2):
    regex_pattern = r"\D+(?P<core_number>\d+)\D+(?P<version>\d*)"

    sku_1_match = re.search(regex_pattern, sku_1)
    sku_2_match = re.search(regex_pattern, sku_2)

    # the case where version number is different, sort by the version number first
    if sku_1_match.group('version') and int(sku_2_match.group('version')) > int(sku_1_match.group('version')):
        return 1
    if sku_1_match.group('version') and int(sku_2_match.group('version')) < int(sku_1_match.group('version')):
        return -1

    # the case where version number is the same, we want to sort by the core number
    if int(sku_2_match.group('core_number')) < int(sku_1_match.group('core_number')):
        return 1
    if int(sku_2_match.group('core_number')) > int(sku_1_match.group('core_number')):
        return -1

    return 0


def _pg_sku_name_validator(sku_name, sku_info, tier, instance):
    additional_error = ''
    if instance is not None:
        tier = instance.sku.tier if tier is None else tier
    else:
        additional_error = 'When --tier is not specified, it defaults to GeneralPurpose. '
    if sku_name:
        skus = [item.lower() for item in get_postgres_skus(sku_info, tier.lower())]
        if sku_name.lower() not in skus:
            raise CLIError('Incorrect value for --sku-name. The SKU name does not exist in {} tier. {}'
                           'Provide a valid SKU name for this tier, or specify --tier with the right tier for the '
                           'SKU name chosen. Allowed values : {}'
                           .format(tier, additional_error, sorted(skus, key=cmp_to_key(compare_sku_names))))


def _pg_storage_performance_tier_validator(performance_tier, sku_info, tier=None, storage_size=None):
    if performance_tier:
        tiers = get_postgres_tiers(sku_info)
        if tier.lower() in [item.lower() for item in tiers]:
            if storage_size is None:
                performance_tiers = [item.lower() for item in
                                     get_performance_tiers(sku_info[tier.lower()]["storage_edition"])]
            else:
                performance_tiers = [item.lower() for item in
                                     get_performance_tiers_for_storage(sku_info[tier.lower()]["storage_edition"],
                                     storage_size=storage_size)]

            if performance_tier.lower() not in performance_tiers:
                raise CLIError('Incorrect value for --performance-tier for storage-size: {}.'
                               ' Allowed values : {}'.format(storage_size, performance_tiers))


def _pg_version_validator(version, versions):
    if version:
        if version not in versions:
            raise CLIError('Incorrect value for --version. Allowed values : {}'.format(sorted(versions)))
        if version in ('11', '12'):
            logger.warning("Support for PostgreSQL %s has officially ended. "
                           "We recommend selecting PostgreSQL 14 or a later version for "
                           "all future operations.", str(version))
        if version == '13':
            logger.warning("PostgreSQL version 13 will reach end-of-life (EOL) soon. "
                           "Upgrade to PostgreSQL 14 or later as soon as possible to "
                           "maintain security, performance, and supportability.")


def _pg_high_availability_validator(high_availability, zonal_resiliency, allow_same_zone,
                                    standby_availability_zone, zone, tier, single_az, instance):
    high_availability_enabled = (high_availability is not None and high_availability.lower() != 'disabled')
    zonal_resiliency_enabled = (zonal_resiliency is not None and zonal_resiliency.lower() != 'disabled')
    high_availability_zone_redundant = (high_availability_enabled and high_availability.lower() == 'zoneredundant')

    if high_availability_enabled and zonal_resiliency_enabled:
        raise ArgumentUsageError("Setting both --high-availability and --zonal-resiliency is not allowed. "
                                 "Please set only --zonal-resiliency to move forward.")

    if instance:
        tier = instance.sku.tier if tier is None else tier
        zone = instance.availability_zone if zone is None else zone

    if high_availability_enabled:
        if tier == 'Burstable':
            raise ArgumentUsageError("High availability is not supported for Burstable tier")
        if single_az and high_availability_zone_redundant:
            raise ArgumentUsageError("This region is single availability zone. "
                                     "Zone redundant high availability is not supported "
                                     "in a single availability zone region.")

    if zonal_resiliency_enabled:
        if tier == 'Burstable':
            raise ArgumentUsageError("High availability is not supported for Burstable tier")
        if single_az and allow_same_zone is False:
            raise ArgumentUsageError("This region is single availability zone. "
                                     "To proceed, please set --allow-same-zone.")

    if standby_availability_zone:
        if not high_availability_zone_redundant and not zonal_resiliency_enabled:
            raise ArgumentUsageError("You need to enable high availability by setting --zonal-resiliency to Enabled "
                                     "to set standby availability zone.")
        if zone == standby_availability_zone:
            raise ArgumentUsageError("Your server is in availability zone {}. "
                                     "The zone of the server cannot be same as the standby zone.".format(zone))

    if allow_same_zone and not zonal_resiliency_enabled:
        raise ArgumentUsageError("You can only set --allow-same-zone when --zonal-resiliency is Enabled.")


def _pg_georedundant_backup_validator(geo_redundant_backup, geo_backup_supported):
    if (geo_redundant_backup and geo_redundant_backup.lower() == 'enabled') and not geo_backup_supported:
        raise ArgumentUsageError("The region of the server does not support geo-restore feature.")


def pg_byok_validator(byok_identity, byok_key, backup_byok_identity=None, backup_byok_key=None,
                      geo_redundant_backup=None, instance=None):
    if bool(byok_identity is None) ^ bool(byok_key is None):
        raise ArgumentUsageError("User assigned identity and keyvault key need to be provided together. "
                                 "Please provide --identity and --key together.")

    if bool(backup_byok_identity is None) ^ bool(backup_byok_key is None):
        raise ArgumentUsageError("User assigned identity and keyvault key need to be provided together. "
                                 "Please provide --backup-identity and --backup-key together.")

    if bool(byok_identity is not None) and bool(backup_byok_identity is not None) and \
       byok_identity.lower() == backup_byok_identity.lower():
        raise ArgumentUsageError("Primary user assigned identity and backup identity cannot be same. "
                                 "Please provide different identities for --identity and --backup-identity.")

    if (instance is not None) and \
       not (instance.data_encryption and instance.data_encryption.type == 'AzureKeyVault') and \
       (byok_key or backup_byok_key):
        raise ArgumentUsageError("You cannot enable data encryption on a server "
                                 "that was not created with data encryption.")

    if geo_redundant_backup is None or geo_redundant_backup.lower() == 'disabled':
        if backup_byok_identity or backup_byok_key:
            raise ArgumentUsageError("Geo-redundant backup is not enabled. "
                                     "You cannot provide Geo-location user assigned identity and keyvault key.")
    else:
        if instance is None and (bool(byok_key is not None) ^ bool(backup_byok_key is not None)):
            raise ArgumentUsageError("Please provide both primary as well as geo-back user assigned identity "
                                     "and keyvault key to enable Data encryption for geo-redundant backup.")
        if instance is not None and (bool(byok_identity is None) ^ bool(backup_byok_identity is None)):
            primary_user_assigned_identity_id = byok_identity if byok_identity else \
                instance.data_encryption.primary_user_assigned_identity_id
            geo_backup_user_assigned_identity_id = backup_byok_identity if backup_byok_identity else \
                instance.data_encryption.geo_backup_user_assigned_identity_id
            if primary_user_assigned_identity_id.lower() == geo_backup_user_assigned_identity_id.lower():
                raise ArgumentUsageError("Primary user assigned identity and backup identity cannot be same. "
                                         "Please provide different identities for --identity and --backup-identity.")


def _network_arg_validator(subnet, public_access):
    if subnet is not None and public_access is not None:
        raise CLIError("Incorrect usage : A combination of the parameters --subnet "
                       "and --public-access is invalid. Use either one of them.")


def maintenance_window_validator(ns):
    options = ["sun", "mon", "tue", "wed", "thu", "fri", "sat", "disabled"]
    if ns.maintenance_window:
        parsed_input = ns.maintenance_window.split(':')
        if not parsed_input or len(parsed_input) > 3:
            raise CLIError('Incorrect value for --maintenance-window. '
                           'Enter <Day>:<Hour>:<Minute>. Example: "Mon:8:30" to schedule on Monday, 8:30 UTC')
        if len(parsed_input) >= 1 and parsed_input[0].lower() not in options:
            raise CLIError('Incorrect value for --maintenance-window. '
                           'The first value means the scheduled day in a week or '
                           'can be "Disabled" to reset maintenance window. '
                           'Allowed values: {"Sun","Mon","Tue","Wed","Thu","Fri","Sat"}')
        if len(parsed_input) >= 2 and \
           (not parsed_input[1].isdigit() or int(parsed_input[1]) < 0 or int(parsed_input[1]) > 23):
            raise CLIError('Incorrect value for --maintenance-window. '
                           'The second number means the scheduled hour in the scheduled day. '
                           'Allowed values: {0, 1, ... 23}')
        if len(parsed_input) >= 3 and \
           (not parsed_input[2].isdigit() or int(parsed_input[2]) < 0 or int(parsed_input[2]) > 59):
            raise CLIError('Incorrect value for --maintenance-window. '
                           'The third number means the scheduled minute in the scheduled hour. '
                           'Allowed values: {0, 1, ... 59}')


def ip_address_validator(ns):
    if (ns.end_ip_address and not _validate_ip(ns.end_ip_address)) or \
       (ns.start_ip_address and not _validate_ip(ns.start_ip_address)):
        raise CLIError('Incorrect value for ip address. '
                       'Ip address should be IPv4 format. Example: 12.12.12.12. ')
    if ns.start_ip_address and ns.end_ip_address:
        _validate_start_and_end_ip_address_order(ns.start_ip_address, ns.end_ip_address)


def public_access_validator(ns):
    if ns.public_access:
        val = ns.public_access.lower()
        if not (val in ['disabled', 'enabled', 'all', 'none'] or
                (len(val.split('-')) == 1 and _validate_ip(val)) or
                (len(val.split('-')) == 2 and _validate_ip(val))):
            raise CLIError('incorrect usage: --public-access. '
                           'Acceptable values are \'Disabled\', \'Enabled\', \'All\', \'None\',\'<startIP>\' and '
                           '\'<startIP>-<destinationIP>\' where startIP and destinationIP ranges from '
                           '0.0.0.0 to 255.255.255.255')
        if len(val.split('-')) == 2:
            vals = val.split('-')
            _validate_start_and_end_ip_address_order(vals[0], vals[1])


def _validate_start_and_end_ip_address_order(start_ip, end_ip):
    start_ip_elements = [int(octet) for octet in start_ip.split('.')]
    end_ip_elements = [int(octet) for octet in end_ip.split('.')]

    for idx in range(4):
        if start_ip_elements[idx] < end_ip_elements[idx]:
            break
        if start_ip_elements[idx] > end_ip_elements[idx]:
            raise ArgumentUsageError("The end IP address is smaller than the start IP address.")


def _validate_ip(ips):
    """
    # Regex not working for re.(regex, '255.255.255.255'). Hence commenting it out for now
    regex = r'^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?).(
                25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?).(
                25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?).(
                25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)$'
    """
    parsed_input = ips.split('-')
    if len(parsed_input) == 1:
        return _validate_ranges_in_ip(parsed_input[0])
    if len(parsed_input) == 2:
        return _validate_ranges_in_ip(parsed_input[0]) and _validate_ranges_in_ip(parsed_input[1])
    return False


def _validate_ranges_in_ip(ip):
    parsed_ip = ip.split('.')
    if len(parsed_ip) == 4 and _valid_range(parsed_ip[0]) and _valid_range(parsed_ip[1]) \
       and _valid_range(parsed_ip[2]) and _valid_range(parsed_ip[3]):
        return True
    return False


def _valid_range(addr_range):
    if addr_range.isdigit() and 0 <= int(addr_range) <= 255:
        return True
    return False


def virtual_endpoint_name_validator(ns):
    if not re.search(r'^(?=[a-z0-9].*)(?=.*[a-z-])(?!.*[^a-z0-9-])(?=.*[a-z0-9]$)', ns.virtual_endpoint_name):
        raise ValidationError("The virtual endpoint name can only contain 0-9, a-z, and \'-\'. "
                              "The virtual endpoint name must not start or end in a hyphen. "
                              "Additionally, the name of the virtual endpoint must be at least 3 characters "
                              "and no more than 63 characters in length. ")


def firewall_rule_name_validator(ns):
    if not ns.firewall_rule_name:
        return
    if not re.search(r'^[a-zA-Z0-9][-_a-zA-Z0-9]{1,126}[_a-zA-Z0-9]$', ns.firewall_rule_name):
        raise ValidationError("The firewall rule name can only contain 0-9, a-z, A-Z, \'-\' and \'_\'. "
                              "Additionally, the name of the firewall rule must be at least 3 characters "
                              "and no more than 128 characters in length. ")


def postgres_firewall_rule_name_validator(ns):
    if not ns.firewall_rule_name:
        return
    if not re.search(r'^[a-zA-Z0-9][-_a-zA-Z0-9]{0,79}(?<!-)$', ns.firewall_rule_name):
        raise ValidationError("The firewall rule name can only contain 0-9, a-z, A-Z, \'-\' and \'_\'. "
                              "Additionally, the name of the firewall rule must be at least 1, "
                              "and no more than 80 characters in length. Firewall rule must not end with '-'.")


def validate_server_name(db_context, server_name, type_):
    client = db_context.cf_availability(db_context.cmd.cli_ctx, '_')

    if not server_name:
        return

    if len(server_name) < 3 or len(server_name) > 63:
        raise ValidationError("Server name must be at least 3 characters and at most 63 characters.")
    try:
        result = client.check_with_location(db_context.location,
                                            parameters={
                                                'name': server_name,
                                                'type': type_})
    except HttpResponseError as e:
        if e.status_code == 403 and e.error and e.error.code == 'AuthorizationFailed':
            client_without_location = db_context.cf_availability(db_context.cmd.cli_ctx, '_')
            result = client_without_location.check_globally(parameters={'name': server_name, 'type': type_})
        else:
            raise e

    if not result.name_available:
        raise ValidationError(result.message)


def validate_virtual_endpoint_name_availability(cmd, virtual_endpoint_name):
    client = cf_postgres_check_resource_availability(cmd.cli_ctx, '_')
    resource_type = 'Microsoft.DBforPostgreSQL/flexibleServers/virtualendpoints'
    result = client.check_globally(parameters={'name': virtual_endpoint_name, 'type': resource_type})
    if result and result.name_available is False:
        raise ValidationError("Virtual endpoint's base name is not available.")


def validate_migration_runtime_server(cmd, migrationInstanceResourceId, target_resource_group_name, target_server_name):
    id_comps = parse_resource_id(migrationInstanceResourceId)
    runtime_server_resource_resource_type = id_comps['resource_type'].lower()
    if "flexibleservers" != runtime_server_resource_resource_type:
        raise ValidationError("Migration Runtime Resource ID provided should be Flexible server.")

    server_operations_client = cf_postgres_flexible_servers(cmd.cli_ctx, '_')
    target_server = server_operations_client.get(target_resource_group_name, target_server_name)
    if target_server.id.lower() == migrationInstanceResourceId.lower():
        raise ValidationError("Migration Runtime server is same as Target Flexible server. "
                              "Please change the values accordingly.")


def validate_private_dns_zone(db_context, server_name, private_dns_zone, private_dns_zone_suffix):
    cmd = db_context.cmd
    server_endpoint = cmd.cli_ctx.cloud.suffixes.postgresql_server_endpoint
    if private_dns_zone == server_name + server_endpoint:
        raise ValidationError("private dns zone name cannot be same as the server's fully qualified domain name")

    if private_dns_zone[-len(private_dns_zone_suffix):] != private_dns_zone_suffix:
        raise ValidationError('The suffix of the private DNS zone should be "{}"'.format(private_dns_zone_suffix))

    if _is_resource_name(private_dns_zone) and not is_valid_resource_name(private_dns_zone) \
            or not _is_resource_name(private_dns_zone) and not is_valid_resource_id(private_dns_zone):
        raise ValidationError("Check if the private dns zone name or Id is in correct format.")


def validate_vnet_location(vnet, location):
    if vnet["location"] != location:
        raise ValidationError("The location of Vnet should be same as the location of the server")


def validate_postgres_replica(cmd, tier, location, instance, sku_name,
                              storage_gb, performance_tier=None, list_location_capability_info=None):
    # Tier validation
    if tier == 'Burstable':
        raise ValidationError("Read replica is not supported for the Burstable pricing tier. "
                              "Scale up the source server to General Purpose or Memory Optimized. ")

    if not list_location_capability_info:
        list_location_capability_info = get_postgres_location_capability_info(cmd, location)

    sku_info = list_location_capability_info['sku_info']
    _pg_tier_validator(tier, sku_info)  # need to be validated first
    _pg_sku_name_validator(sku_name, sku_info, tier, instance)
    _pg_storage_performance_tier_validator(performance_tier,
                                           sku_info,
                                           tier,
                                           storage_gb)


def validate_georestore_network(source_server_object, public_access, vnet, subnet, db_engine):
    if source_server_object.network.public_network_access == 'Disabled' and not any((public_access, vnet, subnet)):
        raise ValidationError("Please specify network parameters if you are geo-restoring a private access server. "
                              F"Run 'az {db_engine} flexible-server geo-restore --help' command to see examples")


def validate_and_format_restore_point_in_time(restore_time):
    try:
        return parser.parse(restore_time)
    except:
        raise ValidationError("The restore point in time value has incorrect date format. "
                              "Please use ISO format e.g., 2024-10-22T00:08:23+00:00.")


def is_citus_cluster(cmd, resource_group_name, server_name):
    server_operations_client = cf_postgres_flexible_servers(cmd.cli_ctx, '_')
    server = server_operations_client.get(resource_group_name, server_name)

    return server.cluster and server.cluster.cluster_size > 0


def validate_citus_cluster(cmd, resource_group_name, server_name):
    if is_citus_cluster(cmd, resource_group_name, server_name):
        raise ValidationError("Elastic cluster does not currently support this operation.")


def validate_public_access_server(cmd, resource_group_name, server_name):
    server_operations_client = cf_postgres_flexible_servers(cmd.cli_ctx, '_')

    server = server_operations_client.get(resource_group_name, server_name)
    if server.network.public_network_access == 'Disabled':
        raise ValidationError("Firewall rule operations cannot be requested for "
                              "a server that doesn't have public access enabled.")


def _validate_identity(cmd, namespace, identity):
    if is_valid_resource_id(identity):
        return identity

    if _is_resource_name(identity):
        return resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.ManagedIdentity',
            type='userAssignedIdentities',
            name=identity)

    raise ValidationError('Invalid identity name or ID.')


def validate_identity(cmd, namespace):
    if namespace.identity:
        namespace.identity = _validate_identity(cmd, namespace, namespace.identity)


def validate_byok_identity(cmd, namespace):
    if namespace.byok_identity:
        namespace.byok_identity = _validate_identity(cmd, namespace, namespace.byok_identity)

    if hasattr(namespace, 'backup_byok_identity') and namespace.backup_byok_identity:
        namespace.backup_byok_identity = _validate_identity(cmd, namespace, namespace.backup_byok_identity)


def validate_identities(cmd, namespace):
    if namespace.identities:
        namespace.identities = [_validate_identity(cmd, namespace, identity) for identity in namespace.identities]


def _pg_storage_type_validator(storage_type, auto_grow, performance_tier, tier,
                               supported_storageV2_size, iops, throughput, instance):
    is_create_ssdv2 = storage_type == "PremiumV2_LRS"
    is_update_ssdv2 = instance is not None and instance.storage.type == "PremiumV2_LRS"

    if is_create_ssdv2:
        if supported_storageV2_size is None:
            raise CLIError('Storage type set to PremiumV2_LRS is not supported for this region.')
        if iops is None or throughput is None:
            raise CLIError('To set --storage-type, required to provide --iops and --throughput.')
    elif instance is None and (throughput is not None or iops is not None):
        raise CLIError('To provide values for both --iops and --throughput, '
                       'please set "--storage-type" to "PremiumV2_LRS".')

    if is_create_ssdv2 or is_update_ssdv2:
        if auto_grow and auto_grow.lower() != 'disabled':
            raise ValidationError("Storage Auto-grow is not supported for servers with Premium SSD V2.")
        if performance_tier:
            raise ValidationError("Performance tier is not supported for servers with Premium SSD V2.")
        if tier and tier.lower() == 'burstable':
            raise ValidationError("Burstable tier is not supported for servers with Premium SSD V2.")
    else:
        if throughput is not None:
            raise CLIError('Updating throughput is only capable for server created with Premium SSD v2.')
        if iops is not None:
            raise CLIError('Updating storage iops is only capable for server created with Premium SSD v2.')


def pg_restore_validator(compute_tier, **args):
    is_ssdv2_enabled = args.get('storage_type', None) == "PremiumV2_LRS"

    if is_ssdv2_enabled and compute_tier.lower() == 'burstable':
        raise ValidationError("Burstable tier is not supported for servers with Premium SSD V2.")


def _pg_authentication_validator(password_auth, is_microsoft_entra_auth_enabled,
                                 admin_name, admin_id, admin_type, instance):
    if instance is None:
        if (password_auth is not None and password_auth.lower() == 'disabled') and not is_microsoft_entra_auth_enabled:
            raise CLIError('Need to have an authentication method enabled, please set --microsoft-entra-auth '
                           'to "Enabled" or --password-auth to "Enabled".')

        if not is_microsoft_entra_auth_enabled and (admin_name or admin_id or admin_type):
            raise CLIError('To provide values for --admin-object-id, --admin-display-name, and --admin-type '
                           'please set --microsoft-entra-auth to "Enabled".')
        if (admin_name is not None or admin_id is not None or admin_type is not None) and \
           not (admin_name is not None and admin_id is not None and admin_type is not None):
            raise CLIError('To add Microsoft Entra admin, please provide values for --admin-object-id, '
                           '--admin-display-name, and --admin-type.')


def check_resource_group(resource_group_name):
    # check if rg is already null originally
    if not resource_group_name:
        return False

    # replace single and double quotes with empty string
    resource_group_name = resource_group_name.replace("'", '')
    resource_group_name = resource_group_name.replace('"', '')

    # check if rg is empty after removing quotes
    if not resource_group_name:
        return False
    return True


def validate_resource_group(resource_group_name):
    if not check_resource_group(resource_group_name):
        raise CLIError('Resource group name cannot be empty.')


def validate_backup_name(backup_name):
    # check if backup_name is already null originally
    if not backup_name:
        raise CLIError('Backup name cannot be empty.')

    # replace single and double quotes with empty string
    backup_name = backup_name.replace("'", '')
    backup_name = backup_name.replace('"', '')

    # check if backup_name is empty or contains only whitespace after removing the quote
    if not backup_name or backup_name.isspace():
        raise CLIError('Backup name cannot be empty or contain only whitespaces.')

    # check if backup_name exceeds 128 characters
    if len(backup_name) > 128:
        raise CLIError('Backup name cannot exceed 128 characters.')


def validate_database_name(database_name):
    if database_name is not None and not re.match(r'^[a-zA-Z_][\w\-]{0,62}$', database_name):
        raise ValidationError("Database name must begin with a letter (a-z) or underscore (_). "
                              "Subsequent characters in a name can be letters, digits (0-9), hyphens (-), "
                              "or underscores. Database name length must be less than 64 characters.")
