# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from __future__ import print_function
from collections import OrderedDict
from azure.cli.core.commands import cli_command
from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE
from azure.cli.core.util import empty_on_404
from ._client_factory import _container_instance_client_factory

if not supported_api_version(PROFILE_TYPE, max_api='2017-03-09-profile'):
    custom_path = 'azure.cli.command_modules.container.custom#{}'

    def transform_log_output(result):
        '''Print log. '''
        print(result)

    def transform_container_group(result):
        """Transform a container group to table output. """
        return OrderedDict([('Name', result['name']),
                            ('ResourceGroup', result['resourceGroup']),
                            ('ProvisioningState', result.get('provisioningState')),
                            ('Image', get_images(result)),
                            ('IP:ports', format_ip_address(result)),
                            ('CPU/Memory', format_cpu_memory(result)),
                            ('OsType', result.get('osType')),
                            ('Location', result['location'])])

    def get_images(container_group):
        """Get all images of a container group. """
        containers = container_group.get('containers')
        if containers is not None and containers:
            images = set([])
            for container in containers:
                images.add(container['image'])
            return ','.join(images)
        return None

    def format_cpu_memory(container_group):
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

    def format_ip_address(container_group):
        """Format IP address. """
        ip_address = container_group.get('ipAddress')
        if ip_address is not None:
            ports = ','.join(str(p['port']) for p in ip_address['ports'])
            return '{0}:{1}'.format(ip_address.get('ip'), ports)
        return None

    def transform_container_group_list(result):
        """Transform a container group list to table output. """
        return [transform_container_group(container_group) for container_group in result]

    cli_command(__name__, 'container list', custom_path.format('list_containers'), _container_instance_client_factory, table_transformer=transform_container_group_list)
    cli_command(__name__, 'container create', custom_path.format('create_container'), _container_instance_client_factory, table_transformer=transform_container_group_list)
    cli_command(__name__, 'container show', custom_path.format('get_container'), _container_instance_client_factory, exception_handler=empty_on_404, table_transformer=transform_container_group)
    cli_command(__name__, 'container delete', custom_path.format('delete_container'), _container_instance_client_factory, confirmation=True)
    cli_command(__name__, 'container logs', custom_path.format('container_logs'), _container_instance_client_factory, transform=transform_log_output)
