#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from __future__ import print_function
import binascii
import json
import os
import os.path
import platform
import random
import string
import sys
from six.moves.urllib.request import urlretrieve #pylint: disable=import-error
import time

from msrestazure.azure_exceptions import CloudError

import azure.cli.core._logging as _logging
from azure.cli.command_modules.acs import acs_client, proxy
from azure.cli.command_modules.vm.mgmt_acs.lib import \
    AcsCreationClient as ACSClient
# pylint: disable=too-few-public-methods,too-many-arguments,no-self-use,line-too-long
from azure.cli.core._util import CLIError
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource.resources import ResourceManagementClient

logger = _logging.get_az_logger(__name__)

def dcos_browse(name, resource_group_name):
    """
    Creates an SSH tunnel to the Azure container service, and opens the Mesosphere DC/OS dashboard in the browser.

    :param name: name: Name of the target Azure container service instance.
    :type name: String
    :param resource_group_name:  Name of Azure container service's resource group.
    :type resource_group_name: String
    """
    acs_info = _get_acs_info(name, resource_group_name)
    acs = acs_client.ACSClient()
    if not acs.connect(_get_host_name(acs_info), _get_username(acs_info)):
        raise CLIError('Error connecting to ACS: {}'.format(_get_host_name(acs_info)))

    octarine_bin = '/opt/mesosphere/bin/octarine'
    if not acs.file_exists(octarine_bin):
        raise CLIError('Proxy server ({}) does not exist on the cluster.'.format(octarine_bin))

    proxy_id = _rand_str(16)
    proxy_cmd = '{} {}'.format(octarine_bin, proxy_id)
    acs.run(proxy_cmd, background=True)

    # Parse the output to get the remote PORT
    proxy_client_cmd = '{} --client --port {}'.format(octarine_bin, proxy_id)
    stdout, _ = acs.run(proxy_client_cmd)
    remote_port = int(stdout.read().decode().strip())
    local_port = acs.get_available_local_port()

    # Set the proxy
    proxy.set_http_proxy('127.0.0.1', local_port)
    logger.info('Proxy running on 127.0.0.1:%s', local_port)
    logger.info('Press CTRL+C to close the tunnel...')
    try:
        acs.create_tunnel(
            remote_host='127.0.0.1',
            remote_port=remote_port,
            local_port=local_port,
            open_url='http://localhost')
    finally:
        proxy.disable_http_proxy()

    return

def dcos_install_cli(install_location=None, client_version='1.8'):
    """
    Downloads the dcos command line from Mesosphere
    """
    system = platform.system()

    if not install_location:
        raise CLIError("No install location specified and it could not be determined from the current platform '{}'".format(system))
    base_url = 'https://downloads.dcos.io/binaries/cli/{}/x86-64/dcos-{}/{}'
    if system == 'Windows':
        file_url = base_url.format('windows', client_version, 'dcos.exe')
    elif system == 'Linux':
        # TODO Support ARM CPU here
        file_url = base_url.format('linux', client_version, 'dcos')
    elif system == 'Darwin':
        file_url = base_url.format('darwin', client_version, 'dcos')
    else:
        raise CLIError('Proxy server ({}) does not exist on the cluster.'.format(system))

    logger.info('Downloading client to %s', install_location)
    try:
        urlretrieve(file_url, install_location)
    except IOError as err:
        raise CLIError('Connection error while attempting to download client ({})'.format(err))

def k8s_install_cli(client_version="1.4.5", install_location=None):
    """
    Downloads the kubectl command line from Kubernetes
    """
    file_url = ''
    system = platform.system()
    base_url = 'https://storage.googleapis.com/kubernetes-release/release/v{}/bin/{}/amd64/{}'
    if system == 'Windows':
        file_url = base_url.format(client_version, 'windows', 'kubectl.exe')
    elif system == 'Linux':
        # TODO: Support ARM CPU here
        file_url = base_url.format(client_version, 'linux', 'kubectl')
    elif system == 'Darwin':
        file_url = base_url.format(client_version, 'darwin', 'kubectl')
    else:
        raise CLIError('Proxy server ({}) does not exist on the cluster.'.format(system))

    logger.info('Downloading client to %s', install_location)
    try:
        urlretrieve(file_url, install_location)
    except IOError as err:
        raise CLIError('Connection error while attempting to download client ({})'.format(err))

def _build_service_principal(name, url, client_secret):
    from azure.cli.command_modules.role.custom import (
        _graph_client_factory,
        create_application,
        create_service_principal,
    )

    sys.stdout.write('creating service principal')
    result = create_application(_graph_client_factory().applications, name, url, [url], password=client_secret)
    service_principal = result.app_id #pylint: disable=no-member
    for x in range(0, 10):
        try:
            create_service_principal(service_principal)
        # TODO figure out what exception AAD throws here sometimes.
        except: #pylint: disable=bare-except
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(2 + 2 * x)
    print('done')
    return service_principal

def _add_role_assignment(role, service_principal):
    # AAD can have delays in propogating data, so sleep and retry
    sys.stdout.write('waiting for AAD role to propogate.')
    for x in range(0, 10):
        from azure.cli.command_modules.role.custom import create_role_assignment
        try:
            # TODO: break this out into a shared utility library
            create_role_assignment(role, service_principal)
            break
        except CloudError as ex:
            if ex.message == 'The role assignment already exists.':
                break
            sys.stdout.write('.')
            logger.info('%s', ex.message)
            time.sleep(2 + 2 * x)
        except: #pylint: disable=bare-except
            sys.stdout.write('.')
            time.sleep(2 + 2 * x)
    print('done')

def acs_create(resource_group_name, deployment_name, dns_name_prefix, name, ssh_key_value, content_version=None, admin_username="azureuser", agent_count="3", agent_vm_size="Standard_D2_v2", location=None, master_count="3", orchestrator_type="dcos", service_principal=None, client_secret=None, tags=None, custom_headers=None, raw=False, **operation_config):
    """Create a new Acs.
    :param resource_group_name: The name of the resource group. The name
     is case insensitive.
    :type resource_group_name: str
    :param deployment_name: The name of the deployment.
    :type deployment_name: str
    :param dns_name_prefix: Sets the Domain name prefix for the cluster.
     The concatenation of the domain name and the regionalized DNS zone
     make up the fully qualified domain name associated with the public
     IP address.
    :type dns_name_prefix: str
    :param name: Resource name for the container service.
    :type name: str
    :param ssh_key_value: Configure all linux machines with the SSH RSA
     public key string.  Your key should include three parts, for example
    'ssh-rsa AAAAB...snip...UcyupgH azureuser@linuxvm
    :type ssh_key_value: str
    :param content_version: If included it must match the ContentVersion
     in the template.
    :type content_version: str
    :param admin_username: User name for the Linux Virtual Machines.
    :type admin_username: str
    :param agent_count: The number of agents for the cluster.  Note, for
     DC/OS clusters you will also get 1 or 2 public agents in addition to
     these seleted masters.
    :type agent_count: str
    :param agent_vm_size: The size of the Virtual Machine.
    :type agent_vm_size: str
    :param location: Location for VM resources.
    :type location: str
    :param master_count: The number of DC/OS masters for the cluster.
    :type master_count: str
    :param orchestrator_type: The type of orchestrator used to manage the
     applications on the cluster. Possible values include: 'dcos', 'swarm'
    :type orchestrator_type: str or :class:`orchestratorType
     <Default.models.orchestratorType>`
    :param tags: Tags object.
    :type tags: object
    :param dict custom_headers: headers that will be added to the request
    :param bool raw: returns the direct response alongside the
     deserialized response
    :rtype:
    :class:`AzureOperationPoller<msrestazure.azure_operation.AzureOperationPoller>`
     instance that returns :class:`DeploymentExtended
     <Default.models.DeploymentExtended>`
    :rtype: :class:`ClientRawResponse<msrest.pipeline.ClientRawResponse>`
     if raw=true
    :raises: :class:`CloudError<msrestazure.azure_exceptions.CloudError>`
    """
    if orchestrator_type == 'Kubernetes' or orchestrator_type == 'kubernetes':
        principalObj = load_acs_service_principal()
        if principalObj:
            service_principal = principalObj.get('service_principal')
            client_secret = principalObj.get('client_secret')

        if not service_principal:
            if not client_secret:
                client_secret = binascii.b2a_hex(os.urandom(10)).decode('utf-8')
            store_acs_service_principal(client_secret, None)
            salt = binascii.b2a_hex(os.urandom(3)).decode('utf-8')
            url = 'http://{}.{}-k8s-masters.{}.cloudapp.azure.com'.format(salt, dns_name_prefix, location)

            service_principal = _build_service_principal(name, url, client_secret)
            logger.info('Created a service principal: %s', service_principal)
        store_acs_service_principal(client_secret, service_principal)
        _add_role_assignment('Owner', service_principal)
        return _create_kubernetes(resource_group_name, deployment_name, dns_name_prefix, name, ssh_key_value, admin_username=admin_username, agent_count=agent_count, agent_vm_size=agent_vm_size, location=location, service_principal=service_principal, client_secret=client_secret)

    ops = get_mgmt_service_client(ACSClient).acs
    return ops.create_or_update(resource_group_name, deployment_name, dns_name_prefix, name, ssh_key_value, content_version=content_version, admin_username=admin_username, agent_count=agent_count, agent_vm_size=agent_vm_size, location=location, master_count=master_count, orchestrator_type=orchestrator_type, tags=tags, custom_headers=custom_headers, raw=raw, operation_config=operation_config)

def store_acs_service_principal(client_secret, service_principal):
    obj = {}
    if client_secret:
        obj['client_secret'] = client_secret
    if service_principal:
        obj['service_principal'] = service_principal
    configPath = os.path.join(os.path.expanduser('~'), '.azure', 'acsServicePrincipal.json')
    with os.fdopen(os.open(configPath, os.O_RDWR|os.O_CREAT|os.O_TRUNC, 0o600),
                   'w+') as spFile:
        json.dump(obj, spFile)

def load_acs_service_principal():
    configPath = os.path.join(os.path.expanduser('~'), '.azure', 'acsServicePrincipal.json')
    if not os.path.exists(configPath):
        return None
    fd = os.open(configPath, os.O_RDONLY)
    try:
        return json.loads(os.fdopen(fd).read())
    except: #pylint: disable=bare-except
        return None

def _create_kubernetes(resource_group_name, deployment_name, dns_name_prefix, name, ssh_key_value, admin_username="azureuser", agent_count="3", agent_vm_size="Standard_D2_v2", location=None, service_principal=None, client_secret=None):
    from azure.mgmt.resource.resources.models import DeploymentProperties
    if not location:
        location = '[resourceGroup().location]'
    template = {
        "$schema": "https://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#",
        "contentVersion": "1.0.0.0",
        "resources": [
            {
                "apiVersion": "2016-09-30",
                "location": location,
                "type": "Microsoft.ContainerService/containerServices",
                "name": name,
                "properties": {
                    "orchestratorProfile": {
                        "orchestratorType": "Custom"
                    },
                    "masterProfile": {
                        "count": 1,
                        "dnsPrefix": dns_name_prefix + '-k8s-masters'
                    },
                    "agentPoolProfiles": [
                        {
                            "name": "agentpools",
                            "count": agent_count,
                            "vmSize": agent_vm_size,
                            "dnsPrefix": dns_name_prefix + '-k8s-agents',
                        }
                    ],
                    "linuxProfile": {
                        "ssh": {
                            "publicKeys": [
                                {
                                    "keyData": ssh_key_value
                                }
                            ]
                        },
                        "adminUsername": admin_username
                    },
                    "servicePrincipalProfile": {
                        "ClientId": service_principal,
                        "Secret": client_secret
                    },
                    "customProfile": {
                        "orchestrator": "kubernetes"
                    }
                }
            }
        ]
    }

    properties = DeploymentProperties(template=template, template_link=None,
                                      parameters=None, mode='incremental')
    smc = get_mgmt_service_client(ResourceManagementClient)
    return smc.deployments.create_or_update(resource_group_name, deployment_name, properties)

def acs_get_credentials(dns_prefix, location):
    # TODO: once we get the right swagger in here, update this to actually pull location and dns_prefix
    #acs_info = _get_acs_info(name, resource_group_name)
    home = os.path.expanduser('~')

    path = os.path.join(home, '.kube', 'config')
    # TODO: this only works for public cloud, need other casing for national clouds
    acs_client.SecureCopy('azureuser', '{}-k8s-masters.{}.cloudapp.azure.com'.format(dns_prefix, location),
                          '.kube/config', path)

def _get_host_name(acs_info):
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

def _get_username(acs_info):
    """
    Gets the admin user name from the Linux profile of the ContainerService object.

    :param acs_info: ContainerService object from Azure REST API
    :type acs_info: ContainerService
    """
    if acs_info.linux_profile is not None:
        return acs_info.linux_profile.admin_username
    return None

def _get_acs_info(name, resource_group_name):
    """
    Gets the ContainerService object from Azure REST API.

    :param name: ACS resource name
    :type name: String
    :param resource_group_name: Resource group name
    :type resource_group_name: String
    """
    mgmt_client = get_mgmt_service_client(ComputeManagementClient)
    return mgmt_client.container_services.get(resource_group_name, name)

def _rand_str(n):
    """
    Gets a random string
    """
    choices = string.ascii_lowercase + string.digits
    return ''.join(random.SystemRandom().choice(choices) for _ in range(n))
