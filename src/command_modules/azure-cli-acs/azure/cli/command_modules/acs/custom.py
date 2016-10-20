#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import os
import random

import azure.cli.core._logging as _logging
from azure.cli.command_modules.acs import acs_client, proxy
# pylint: disable=too-few-public-methods,too-many-arguments,no-self-use
from azure.cli.core._util import CLIError
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.mgmt.compute import ComputeManagementClient

logger = _logging.get_az_logger(__name__)

def dcos_browse(name, resource_group_name):
    """
    Creates an SSH tunnel to the ACS cluster

    :param name: ACS resource name
    :type name: String
    :param resource_group_name: Resource group name
    :type resource_group_name: String
    """

    acs_info = get_acs_info(name, resource_group_name)
    acs = acs_client.ACSClient()
    if not acs.connect(get_host_name(acs_info), get_username(acs_info)):
        raise Exception('Error connecting to ACS: {}'.format(get_host_name(acs_info)))

    octarine_bin = '/opt/mesosphere/bin/octarine'
    if not acs.file_exists(octarine_bin):
        raise Exception('Proxy server ({}) does not exist on the cluster.'.format(octarine_bin))

    proxy_id = rand_str(16)
    proxy_cmd = '{} {}'.format(octarine_bin, proxy_id)
    acs.run(proxy_cmd, background = True)

    # Parse the output to get the remote PORT
    proxy_client_cmd = '{} --client --port {}'.format(octarine_bin, proxy_id)
    stdout, _ = acs.run(proxy_client_cmd)
    remote_port = int(stdout.read().decode().strip())
    local_port = acs.get_available_local_port()
    
    # Set the proxy
    proxy.set_http_proxy('127.0.0.1', local_port)
    logger.info('Proxy running on 127.0.0.1:{}'.format(local_port))
    logger.info('Press CTRL+C to close the tunnel...')
    acs.create_tunnel(remote_host='127.0.0.1', remote_port=remote_port, local_port=local_port, open_url = 'http://localhost')

    # Turn the proxy off
    proxy.unset_http_proxy()
    return

def get_host_name(acs_info):
    """
    Gets the FQDN from the acs_info object.

    :param acs_info: ContainerService object from Azure REST API
    :type acs_info: ContainerService
    """
    if acs_info is None:
        raise CLIError('Missing acs_info')
    if acs_info.master_profile is None:
        raise CLIError('Missing master_profile')
    if acs_info.master_profile.fqdn is None:
        raise CLIError('Missing fqdn')
    return acs_info.master_profile.fqdn 

def get_public_host_name(acs_info):
    """
    Gets the FQDN of the public agents from the acs_info object.

    :param acs_info: ContainerService object from Azure REST API
    :type acs_info: ContainerService
    """
    if acs_info is None:
        raise CLIError('Missing acs_info')
    if acs_info.agent_pool_profiles is None:
        raise CLIError('Missing agent_pool_profiles')
    if len(acs_info.agent_pool_profiles) < 1:
        raise CLIError('Missing agent profile')
    if acs_info.agent_pool_profiles[0] is None:
        raise CLIError('Agent profile is None')
    if acs_info.agent_pool_profiles[0].fqdn is None:
        raise CLIError('Missing public fqdn')
    return acs_info.agent_pool_profiles[0].fqdn

def get_username(acs_info):
    """
    Gets the admin user name from the Linux profile of the ContainerService object

    :param acs_info: ContainerService object from Azure REST API
    :type acs_info: ContainerService
    """
    if acs_info.linux_profile is not None:
        return acs_info.linux_profile.admin_username
    return None

def get_acs_info(name, resource_group_name):
    """
    Gets the ContainerService object from Azure REST API

    :param name: ACS resource name
    :type name: String
    :param resource_group_name: Resource group name
    :type resource_group_name: String
    """
    #Remove the hack after https://github.com/Azure/azure-rest-api-specs/issues/352 fixed
    from azure.mgmt.compute.models import ContainerService#pylint: disable=wrong-import-position
    for a in ['id', 'name', 'type', 'location']:
        ContainerService._attribute_map[a]['type'] = 'str'#pylint: disable=protected-access
    ContainerService._attribute_map['tags']['type'] = '{str}'#pylint: disable=protected-access
    ######

    mgmt_client = get_mgmt_service_client(ComputeManagementClient)
    return mgmt_client.container_service.get(resource_group_name, name)

def rand_str(n):
    """
    Gets a random string
    """
    choices = string.ascii_lowercase + string.digits
    return ''.join(random.SystemRandom().choice(choices) for _ in range(n))