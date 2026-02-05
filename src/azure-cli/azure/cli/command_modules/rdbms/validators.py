# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from dateutil import parser
import re
from knack.prompting import prompt_pass, NoTTYException
from knack.util import CLIError
from knack.log import get_logger
from azure.mgmt.core.tools import parse_resource_id, resource_id, is_valid_resource_id, is_valid_resource_name
from azure.cli.core.azclierror import ValidationError, ArgumentUsageError
from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_subscription_id
from azure.cli.core.commands.validators import (
    get_default_location_from_resource_group, validate_tags)
from azure.cli.core.util import parse_proxy_resource_id
from azure.cli.core.profiles import ResourceType
from azure.core.exceptions import HttpResponseError
from ._client_factory import (cf_mysql_flexible_servers)
from ._flexible_server_util import (get_mysql_versions, get_mysql_skus, get_mysql_storage_size,
                                    get_mysql_backup_retention, get_mysql_tiers, get_mysql_list_skus_info,
                                    _is_resource_name)

logger = get_logger(__name__)


# pylint: disable=import-outside-toplevel, raise-missing-from, unbalanced-tuple-unpacking
def _get_resource_group_from_server_name(cli_ctx, server_name):
    """
    Fetch resource group from server name
    :param str server_name: name of the server
    :return: resource group name or None
    :rtype: str
    """

    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RDBMS).servers
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


def mysql_restore_tier_validator(target_tier, source_tier, sku_info):
    _mysql_tier_validator(target_tier, sku_info)
    sku_list = list(sku_info.keys())
    if sku_list.index(target_tier) < sku_list.index(source_tier):
        raise CLIError("Incorrect value: --tier. Restored server must not go to below the source server compute tier.")


# pylint: disable=too-many-locals
def mysql_arguments_validator(db_context, location, tier, sku_name, storage_gb, backup_retention=None,
                              server_name=None, zone=None, standby_availability_zone=None, high_availability=None,
                              subnet=None, public_access=None, version=None, auto_grow=None, replication_role=None,
                              geo_redundant_backup=None, byok_identity=None, backup_byok_identity=None, byok_key=None,
                              backup_byok_key=None, disable_data_encryption=None, iops=None, auto_io_scaling=None,
                              instance=None):
    validate_server_name(db_context, server_name, 'Microsoft.DBforMySQL/flexibleServers')

    list_skus_info = get_mysql_list_skus_info(db_context.cmd, location, server_name=instance.name if instance else None)
    sku_info = list_skus_info['sku_info']
    single_az = list_skus_info['single_az']
    geo_paired_regions = list_skus_info['geo_paired_regions']

    _network_arg_validator(subnet, public_access)
    _mysql_tier_validator(tier, sku_info)  # need to be validated first
    if geo_redundant_backup is None and instance is not None:
        geo_redundant_backup = instance.backup.geo_redundant_backup
    mysql_georedundant_backup_validator(geo_redundant_backup, geo_paired_regions)
    if tier is None and instance is not None:
        tier = instance.sku.tier
    mysql_retention_validator(backup_retention, sku_info, tier)
    mysql_storage_validator(storage_gb, sku_info, tier, instance)
    mysql_sku_name_validator(sku_name, sku_info, tier, instance)
    _mysql_high_availability_validator(high_availability, standby_availability_zone, zone, tier,
                                       single_az, auto_grow, instance)
    _mysql_version_validator(version, sku_info, tier, instance)
    mysql_auto_grow_validator(auto_grow, replication_role, high_availability, instance)
    _mysql_byok_validator(byok_identity, backup_byok_identity, byok_key, backup_byok_key,
                          disable_data_encryption, geo_redundant_backup, instance)
    _mysql_iops_validator(iops, auto_io_scaling, instance)


def mysql_retention_validator(backup_retention, sku_info, tier):
    if backup_retention is not None:
        backup_retention_range = get_mysql_backup_retention(sku_info, tier)
        if not 1 <= int(backup_retention) <= backup_retention_range[1]:
            raise CLIError('incorrect usage: --backup-retention. Range is {} to {} days.'
                           .format(1, backup_retention_range[1]))


def mysql_storage_validator(storage_gb, sku_info, tier, instance):
    if storage_gb is not None:
        if instance:
            original_size = instance.storage.storage_size_gb
            if original_size > storage_gb:
                raise CLIError('Updating storage cannot be smaller than the '
                               'original storage size {} GiB.'.format(original_size))
        storage_sizes = get_mysql_storage_size(sku_info, tier)
        min_mysql_storage = 20
        if not max(min_mysql_storage, storage_sizes[0]) <= storage_gb <= storage_sizes[1]:
            raise CLIError('Incorrect value for --storage-size. Allowed values(in GiB) : Integers ranging {}-{}'
                           .format(max(min_mysql_storage, storage_sizes[0]), storage_sizes[1]))


def mysql_georedundant_backup_validator(geo_redundant_backup, geo_paired_regions):
    if geo_redundant_backup and geo_redundant_backup.lower() == 'enabled' and len(geo_paired_regions) == 0:
        raise ArgumentUsageError("The region of the server does not support geo-restore feature.")


def _mysql_tier_validator(tier, sku_info):
    if tier:
        tiers = get_mysql_tiers(sku_info)
        if tier not in tiers:
            raise CLIError('Incorrect value for --tier. Allowed values : {}'.format(tiers))


def mysql_sku_name_validator(sku_name, sku_info, tier, instance):
    if instance is not None:
        tier = instance.sku.tier if tier is None else tier
    if sku_name:
        skus = get_mysql_skus(sku_info, tier)
        if sku_name not in skus:
            raise CLIError('Incorrect value for --sku-name. The SKU name does not match tier selection. '
                           'Default value for --tier is Burstable. '
                           'For Business Critical and General Purpose you need to specify --tier value explicitly. '
                           'Allowed values for given tier: {}'.format(skus))


def _mysql_version_validator(version, sku_info, tier, instance):
    if instance is not None:
        tier = instance.sku.tier if tier is None else tier
    if version:
        versions = get_mysql_versions(sku_info, tier)
        if version not in versions:
            raise CLIError('Incorrect value for --version. Allowed values : {}'.format(versions))


def mysql_auto_grow_validator(auto_grow, replication_role, high_availability, instance):
    if auto_grow is None:
        return
    if instance is not None:
        replication_role = instance.replication_role if replication_role is None else replication_role
        high_availability = instance.high_availability.mode if high_availability is None else high_availability
    # if replica, cannot be disabled
    if replication_role not in ('None', None) and auto_grow.lower() == 'disabled':
        raise ValidationError("Auto grow feature for replica server cannot be disabled.")
    # if ha, cannot be disabled
    if high_availability == 'ZoneRedundant' and auto_grow.lower() == 'disabled':
        raise ValidationError("Auto grow feature for high availability server cannot be disabled.")


def _mysql_high_availability_validator(high_availability, standby_availability_zone, zone, tier, single_az,
                                       auto_grow, instance):
    if instance:
        tier = instance.sku.tier if tier is None else tier
        auto_grow = instance.storage.auto_grow if auto_grow is None else auto_grow
        zone = instance.availability_zone if zone is None else zone
    if high_availability is not None and high_availability.lower() != 'disabled':
        if tier == 'Burstable':
            raise ArgumentUsageError("High availability is not supported for Burstable tier")
        if single_az and high_availability.lower() == 'zoneredundant':
            raise ArgumentUsageError("This region is single availability zone. "
                                     "Zone redundant high availability is not supported "
                                     "in a single availability zone region.")
        if auto_grow.lower == 'Disabled':
            raise ArgumentUsageError("Enabling High availability requires auto-grow to be turned ON.")
    if standby_availability_zone:
        if not high_availability or high_availability.lower() != 'zoneredundant':
            raise ArgumentUsageError("You need to enable zone redundant high availability "
                                     "to set standby availability zone.")
        if zone == standby_availability_zone:
            raise ArgumentUsageError("Your server is in availability zone {}. "
                                     "The zone of the server cannot be same as the standby zone.".format(zone))


def _mysql_byok_validator(byok_identity, backup_byok_identity, byok_key, backup_byok_key,
                          disable_data_encryption, geo_redundant_backup, instance):
    # identity and key should be provided as a pair
    if bool(byok_identity is None) ^ bool(byok_key is None) or\
       bool(backup_byok_identity is None) ^ bool(backup_byok_key is None):
        raise ArgumentUsageError("User assigned identity and keyvault key need to be provided together. "
                                 "Please provide --identity, --key (and --backup-identity, --backup-key "
                                 "if applicable) together.")

    if byok_identity is None and backup_byok_identity is not None:
        raise ArgumentUsageError("Backup identity and key must be provided with principal identity and key.")

    if disable_data_encryption and (byok_key or backup_byok_key):
        raise ArgumentUsageError("Data encryption cannot be disabled if key or backup key is provided.")

    if not disable_data_encryption and (geo_redundant_backup and geo_redundant_backup.lower() == 'enabled') and \
       (byok_identity is not None and backup_byok_identity is None):
        raise ArgumentUsageError("Backup identity and key need to be provided for geo-redundant server.")

    if (instance and instance.replication_role == "Replica") and (disable_data_encryption or byok_key):
        raise CLIError("Data encryption cannot be modified on a server with replication role. "
                       "Use the primary server instead.")


def _mysql_iops_validator(iops, auto_io_scaling, instance):
    if iops is None:
        return
    if instance is not None:
        auto_io_scaling = instance.storage.auto_io_scaling if auto_io_scaling is None else auto_io_scaling
    if auto_io_scaling.lower() == 'enabled':
        logger.warning("The server has enabled the auto scale iops. So the iops will be ignored.")


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


def validate_private_dns_zone(db_context, server_name, private_dns_zone, private_dns_zone_suffix):
    cmd = db_context.cmd
    server_endpoint = cmd.cli_ctx.cloud.suffixes.mysql_server_endpoint
    if private_dns_zone == server_name + server_endpoint:
        raise ValidationError("private dns zone name cannot be same as the server's fully qualified domain name")

    if private_dns_zone[-len(private_dns_zone_suffix):] != private_dns_zone_suffix:
        raise ValidationError('The suffix of the private DNS zone should be "{}"'.format(private_dns_zone_suffix))

    if _is_resource_name(private_dns_zone) and not is_valid_resource_name(private_dns_zone) \
            or not _is_resource_name(private_dns_zone) and not is_valid_resource_id(private_dns_zone):
        raise ValidationError("Check if the private dns zone name or Id is in correct format.")


def validate_mysql_ha_enabled(server):
    if server.storage_profile.storage_autogrow == "Disabled":
        raise ValidationError("You need to enable auto grow first to enable high availability.")


def validate_vnet_location(vnet, location):
    if vnet["location"] != location:
        raise ValidationError("The location of Vnet should be same as the location of the server")


def validate_mysql_replica(server):
    # Tier validation
    if server.sku.tier == 'Burstable':
        raise ValidationError("Read replica is not supported for the Burstable pricing tier. "
                              "Scale up the source server to General Purpose or Memory Optimized. ")


def validate_mysql_tier_update(instance, tier):
    if instance.sku.tier in ['GeneralPurpose', 'MemoryOptimized'] and tier == 'Burstable':
        if instance.replication_role == 'Source':
            raise ValidationError("Read replica is not supported for Burstable Tier")
        if instance.high_availability.mode != 'Disabled':
            raise ValidationError("High availability is not supported for Burstable Tier")


def validate_georestore_location(db_context, location):
    list_skus_info = get_mysql_list_skus_info(db_context.cmd, db_context.location)
    geo_paired_regions = list_skus_info['geo_paired_regions']

    if location not in geo_paired_regions:
        raise ValidationError("The region is not paired with the region of the source server. ")


def validate_replica_location(cmd, source_server_location, replica_location):
    if source_server_location != replica_location:
        list_skus_info = get_mysql_list_skus_info(cmd, source_server_location)
        geo_paired_regions = list_skus_info['geo_paired_regions']

        if replica_location not in geo_paired_regions:
            raise ValidationError("The region is not paired with the region of the source server. ")


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


def validate_public_access_server(cmd, resource_group_name, server_name):
    server_operations_client = cf_mysql_flexible_servers(cmd.cli_ctx, '_')

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
