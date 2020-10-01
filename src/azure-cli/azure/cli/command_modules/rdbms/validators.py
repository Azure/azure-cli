# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import re

from knack.prompting import prompt_pass, NoTTYException
from knack.util import CLIError
from knack.log import get_logger
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.validators import (
    get_default_location_from_resource_group, validate_tags)
from azure.cli.core.util import parse_proxy_resource_id

logger = get_logger(__name__)


def _get_resource_group_from_server_name(cli_ctx, server_name):
    """
    Fetch resource group from server name
    :param str server_name: name of the server
    :return: resource group name or None
    :rtype: str
    """
    from azure.cli.core.profiles import ResourceType
    from msrestazure.tools import parse_resource_id

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
    if ns.backup_retention:
        val = ns.backup_retention
        if not 7 <= int(val) <= 35:
            raise CLIError('incorrect usage: --backup_retention. Range is 7 to 35 days.')


# Validates if a subnet id or name have been given by the user. If subnet id is given, vnet-name should not be provided.
def validate_subnet(cmd, namespace):
    from msrestazure.tools import resource_id, is_valid_resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id

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


def pg_storage_validator(ns):
    if ns.storage_mb:
        if str(ns.storage_mb) in ['32', '64', '128', '256', '512', '1024', '2048', '4096', '8192', '16384']:
            ns.storage_mb = int(ns.storage_mb) * 1024
        else:
            raise CLIError('Incorrect value for --storage-size : Allowed values(in GB) : \
                            {32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384}')


def mysql_storage_validator(ns):
    if ns.storage_mb:
        if 10 <= int(ns.storage_mb) <= 16384:
            ns.storage_mb = int(ns.storage_mb) * 1024
        else:
            raise CLIError('Incorrect value for --storage-size  : Allowed values(in GB) : Integers ranging 10-16384')


def tier_validator(ns):
    if ns.tier:
        if str(ns.tier) not in ['Burstable', 'GeneralPurpose', 'MemoryOptimized']:
            raise CLIError('Incorrect value for --tier. Allowed values : Burstable, GeneralPurpose, MemoryOptimized')

        if re.match(r"^Standard_B\d", ns.sku_name) and ns.tier != 'Burstable':
            raise CLIError('SKU and tier are not matching. SKU "{}" is in "Burstable" tier. '
                           'Specify "--tier Burstable" argument to deploy with the SKU'.format(ns.sku_name))
        if re.match(r"^Standard_D\d+s_v3$", ns.sku_name) and ns.tier != 'GeneralPurpose':
            raise CLIError('SKU and tier are not matching. SKU "{}" is in "General Purpose" tier. '
                           'Specify "--tier GeneralPurpose" argument to deploy with the SKU'.format(ns.sku_name))
        if re.match(r"^Standard_E\d+s_v3$", ns.sku_name) and ns.tier != 'MemoryOptimized':
            raise CLIError('SKU and tier are not matching. SKU "{}" is in "Memory Optimized" tier. '
                           'Specify "--tier MemoryOptimized" argument to deploy with the SKU'.format(ns.sku_name))


def pg_sku_name_validator(ns):
    if ns.sku_name:
        if len(ns.sku_name.split('_')) != 3:
            raise CLIError('Incorrect value for --sku-name. Follow the convention Standard_{VM name}. '
                           'Examples: Standard_D4s_v3')
        server_type, cpu, server_v3 = ns.sku_name.split('_')
        if server_type != 'Standard' or server_v3 != 'v3':
            raise CLIError('Incorrect value for --sku-name. Follow the convention Standard_{VM name}. '
                           'Examples: Standard_D4s_v3')
        if not re.match(r"^(D|E)\d+s$", cpu) or \
           (re.match(r"^(D|E)\d+s$", cpu) and int(cpu[1:-1]) not in [2, 4, 8, 16, 32, 48, 64]):
            raise CLIError('Incorrect value for --sku-name.  Follow the convention Standard_{VM name}. '
                           'Examples: Standard_D4s_v3. \nAllowed number of vCores: 2, 4, 8, 16, 32, 48, 64')


def mysql_sku_name_validator(ns):
    if ns.sku_name:
        if len(ns.sku_name.split('_')) == 2:
            server_type, cpu = ns.sku_name.split('_')
            if server_type != 'Standard' or cpu not in ['B1ms', 'B2s', 'B1s']:
                raise CLIError('Incorrect value for --sku-name. Follow the convention Standard_{VM name}. '
                               'Examples: Standard_D4s_v3 Standard_E8s_v3 Standard_B1ms')
        elif len(ns.sku_name.split('_')) == 3:
            server_type, cpu, server_v3 = ns.sku_name.split('_')
            if server_type != 'Standard' or server_v3 != 'v4':
                raise CLIError('Incorrect value for --sku-name. Follow the convention Standard_{VM name}. '
                               'Examples: Standard_D4s_v3 Standard_B1ms')
            if not re.match(r"^(D|E)\d+ds$", cpu) or \
               (re.match(r"^(D|E)\d+ds$", cpu) and int(cpu[1:-1]) not in [2, 4, 8, 16, 32, 48, 64]):
                raise CLIError('Incorrect value for --sku-name.  Follow the convention Standard_{VM name}. '
                               'Examples: Standard_D4s_v3 Standard_E8s_v3 Standard_B1ms. '
                               '\nAllowed number of vCores: 2, 4, 8, 16, 32, 48, 64')


def pg_version_validator(ns):
    if ns.version:
        if ns.version not in ['11', '12']:
            raise CLIError('Incorrect value for --version. Allowed values : {11, 12}')


def mysql_version_validator(ns):
    if ns.version:
        if ns.version not in ['5.6', '5.7', '8.0']:
            raise CLIError('Incorrect value for --version. Allowed values : {5.6, 5.7, 8.0}')


def maintenance_window_validator(ns):
    options = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Disabled"]
    if ns.maintenance_window:
        parsed_input = ns.maintenance_window.split(':')
        if not parsed_input or len(parsed_input) > 3:
            raise CLIError('Incorrect value for --maintenance-window. '
                           'Enter <Day>:<Hour>:<Minute>. Example: "Mon:8:30" to schedule on Monday, 8:30 UTC')
        if len(parsed_input) >= 1 and parsed_input[0] not in options:
            raise CLIError('Incorrect value for --maintenance-window. '
                           'The first value means the scheduled day in a week or '
                           'can be "Disabled" to reset maintenance window.'
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


def public_access_validator(ns):
    if ns.public_access:
        val = ns.public_access.lower()
        if not (val == 'all' or val == 'none' or (len(val.split('-')) == 1 and _validate_ip(val)) or
                (len(val.split('-')) == 2 and _validate_ip(val))):
            raise CLIError('incorrect usage: --public-access. '
                           'Acceptable values are \'all\', \'none\',\'<startIP>\' and '
                           '\'<startIP>-<destinationIP>\' where startIP and destinationIP ranges from '
                           '0.0.0.0 to 255.255.255.255')


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
    if len(parsed_ip) == 4 and _valid_range(int(parsed_ip[0])) and _valid_range(int(parsed_ip[1])) \
       and _valid_range(int(parsed_ip[2])) and _valid_range(int(parsed_ip[3])):
        return True
    return False


def _valid_range(addr_range):
    if 0 <= addr_range <= 255:
        return True
    return False
