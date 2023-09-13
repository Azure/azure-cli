# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods
from knack.log import get_logger
from ._util import import_aaz_by_profile


logger = get_logger(__name__)


_PublicIP = import_aaz_by_profile("network.public_ip")


def create_public_ip(cmd, resource_group_name, public_ip_address_name, location=None, tags=None,
                     allocation_method=None, dns_name=None,
                     idle_timeout=4, reverse_fqdn=None, ip_address=None):
    public_ip_args = {
        'name': public_ip_address_name,
        "resource_group": resource_group_name,
        'location': location,
        'tags': tags,
        'allocation_method': allocation_method,
        'idle_timeout': idle_timeout,
        'ip_address': ip_address,
    }

    if not allocation_method:
        public_ip_args['allocation_method'] = 'Dynamic'

    if dns_name or reverse_fqdn:
        public_ip_args['dns_name'] = dns_name
        public_ip_args['reverse_fqdn'] = reverse_fqdn

    PublicIpCreate = import_aaz_by_profile("network.public_ip").Create
    return PublicIpCreate(cli_ctx=cmd.cli_ctx)(command_args=public_ip_args)
