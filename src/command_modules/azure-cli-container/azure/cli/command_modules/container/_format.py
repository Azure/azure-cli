# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
from collections import OrderedDict


def _get_images(container_group):
    """Get all images of a container group. """
    containers = container_group.get('containers')
    if containers is not None and containers:
        images = set([])
        for container in containers:
            images.add(container['image'])
        return ','.join(images)
    return None


def _format_cpu_memory(container_group):
    """Format CPU and memory. """
    containers = container_group.get('containers')
    if containers is not None and containers:
        total_cpu = 0
        total_memory = 0
        for container in containers:
            resources = container.get('resources')
            if resources is not None:
                resources_requests = resources.get('requests')
                if resources_requests is not None:
                    total_cpu += resources_requests.get('cpu', 0)
                    total_memory += resources_requests.get('memoryInGb', 0)
            return '{0} core/{1} gb'.format(total_cpu, total_memory)
    return None


def _format_ip_address(container_group):
    """Format IP address. """
    ip_address = container_group.get('ipAddress')
    if ip_address:
        ports = ip_address['ports'] or []

        if ip_address['type'] == 'Private':
            for container in container_group.get('containers'):
                ports += container.get('ports')

        ports = ','.join(str(p['port']) for p in ports)
        return '{0}:{1}'.format(ip_address.get('ip'), ports)
    return None


def _format_status(container_group):
    return container_group['instanceView']['state'] or container_group['provisioningState']


def _format_network(container_group):
    ip_address = container_group.get('ipAddress')
    if ip_address:
        return ip_address['type']
    return None


def transform_container_group(result):
    """Transform a container group to table output. """
    return OrderedDict([('Name', result['name']),
                        ('ResourceGroup', result['resourceGroup']),
                        ('Status', _format_status(result)),
                        ('Image', _get_images(result)),
                        ('IP:ports', _format_ip_address(result)),
                        ('Network', _format_network(result)),
                        ('CPU/Memory', _format_cpu_memory(result)),
                        ('OsType', result.get('osType')),
                        ('Location', result['location'])])


def transform_container_group_list(result):
    """Transform a container group list to table output. """
    return [transform_container_group(container_group) for container_group in result]
