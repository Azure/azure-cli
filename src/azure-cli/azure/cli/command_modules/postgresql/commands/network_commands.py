# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long, import-outside-toplevel
from azure.cli.core.azclierror import RequiredArgumentMissingError, ValidationError
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.util import CLIError, sdk_no_wait
from azure.mgmt import postgresqlflexibleservers as postgresql_flexibleservers
from knack.log import get_logger
from requests import get
from ..aaz.latest.network.vnet.subnet import (
    Create as SubnetCreate,
    Update as SubnetUpdate,
)
from ..utils._flexible_server_util import (
    get_user_confirmation,
    parse_public_access_input,
)
from ..utils.validators import (
    validate_private_dns_zone,
    validate_resource_group,
    validate_subnet,
)

logger = get_logger(__name__)
DELEGATION_SERVICE_NAME = "Microsoft.DBforPostgreSQL/flexibleServers"
IP_ADDRESS_CHECKER = 'https://api.ipify.org'


def flexible_server_migrate_network(client, resource_group_name, server_name, no_wait=False):
    validate_resource_group(resource_group_name)

    return sdk_no_wait(no_wait, client.begin_migrate_network_mode, resource_group_name, server_name)


def compute_firewall_rule_ip_ranges(public_access, yes):
    if public_access is None:
        try:
            # In USSec and USNat, the IP address checker is not available as the public Internet is not accessible.
            # When the user does not provide a public IP address or does not disble public access,
            # the `az cli postgres flexible-server create` command will fail with the error
            # HTTPSConnectionPool(host='api.ipify.org', port443): Max retries excceeded with url
            ip_address = get(IP_ADDRESS_CHECKER).text
        except Exception as ex:
            raise CLIError("Unable to detect your current IP address. Provide a valid IP address or CIDR range for --public-access parameter or set --public-access Disabled. Error: {}".format(ex))

        logger.warning("Detected current client IP : %s", ip_address)
        if yes:
            return ip_address, ip_address

        if get_user_confirmation("Do you want to enable access to client {0}".format(ip_address), yes=yes):
            return ip_address, ip_address

        if get_user_confirmation("Do you want to enable access for all IPs", yes=yes):
            return '0.0.0.0', '255.255.255.255'
        return -1, -1

    if str(public_access).lower() == 'all':
        start_ip, end_ip = '0.0.0.0', '255.255.255.255'
    elif str(public_access).lower() in ['none', 'disabled', 'enabled']:
        start_ip, end_ip = -1, -1
    else:
        start_ip, end_ip = parse_public_access_input(public_access)

    return start_ip, end_ip


def flexible_server_validate_network(cmd, resource_group_name, server_name,
                                               location, db_context, private_dns_zone_arguments=None, public_access=None,
                                               vnet=None, subnet=None, yes=False):
    validate_resource_group(resource_group_name)

    start_ip = -1
    end_ip = -1
    network = postgresql_flexibleservers.models.Network()

    if subnet is not None:
        subnet_id = validate_subnet(cmd,
                                            resource_group_name,
                                            vnet=vnet,
                                            subnet=subnet)
        private_dns_zone_id = validate_private_dns_zone(db_context,
                                                        server_name=server_name,
                                                        private_dns_zone=private_dns_zone_arguments,
                                                        subnet_id=subnet_id,
                                                        location=location)
        network.delegated_subnet_resource_id = subnet_id
        network.private_dns_zone_arm_resource_id = private_dns_zone_id
    elif subnet is None and private_dns_zone_arguments is not None:
        raise RequiredArgumentMissingError("Private DNS zone can only be used with private access setting. Use --subnet parameter.")
    else:
        start_ip, end_ip = compute_firewall_rule_ip_ranges(public_access, yes=yes)
        if public_access is not None and str(public_access).lower() in ['disabled', 'none']:
            network.public_network_access = 'Disabled'
        else:
            network.public_network_access = 'Enabled'

    return network, start_ip, end_ip
