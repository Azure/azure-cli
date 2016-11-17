# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Commands for DNS Zone Management
"""

#pylint: disable=too-many-arguments
def create_dns_zone(client, resource_group_name, zone_name, location='global', tags=None,
                    if_none_match=False):
    from azure.mgmt.dns.models import Zone

    kwargs = {
        'resource_group_name':resource_group_name,
        'zone_name': zone_name,
        'parameters': Zone(location, tags=tags)
    }

    if if_none_match:
        kwargs['if_none_match'] = '*'

    return client.create_or_update(**kwargs)
