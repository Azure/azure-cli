# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import base64
import binascii
import errno
import json
import os
import os.path
import uuid
import datetime
import platform
import random
import string
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
import stat
import ssl
import re
import yaml
import dateutil.parser
from dateutil.relativedelta import relativedelta
from six.moves.urllib.request import urlopen  # pylint: disable=import-error
from six.moves.urllib.error import URLError  # pylint: disable=import-error

from msrestazure.azure_exceptions import CloudError

import azure.cli.core.azlogging as azlogging
from azure.cli.core.application import APPLICATION
from azure.cli.command_modules.acs import acs_client, proxy
from azure.cli.command_modules.acs._params import regionsInPreview, regionsInProd
from azure.cli.core.util import CLIError, shell_safe_json_parse
from azure.cli.core._profile import Profile
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core._environment import get_config_dir
from azure.cli.core.keys import is_valid_ssh_rsa_public_key
from azure.cli.core.profiles import ResourceType
from azure.mgmt.containerservice import ContainerServiceClient
from azure.mgmt.containerservice.models import ContainerServiceAgentPoolProfile
from azure.mgmt.containerservice.models import ContainerServiceLinuxProfile
from azure.mgmt.containerservice.models import ContainerServiceOrchestratorTypes
from azure.mgmt.containerservice.models import ContainerServiceServicePrincipalProfile
from azure.mgmt.containerservice.models import ContainerServiceSshConfiguration
from azure.mgmt.containerservice.models import ContainerServiceSshPublicKey
from azure.mgmt.containerservice.models import ContainerServiceStorageProfileTypes
from azure.mgmt.containerservice.models import ManagedCluster
from azure.mgmt.containerservice.models import ManagedClusterProperties
from azure.graphrbac.models import (ApplicationCreateParameters,
                                    PasswordCredential,
                                    KeyCredential,
                                    ServicePrincipalCreateParameters,
                                    GetObjectsParameters)
from azure.mgmt.authorization.models import RoleAssignmentProperties

from ._client_factory import (_auth_client_factory, _graph_client_factory)

logger = azlogging.get_az_logger(__name__)

# pylint:disable=too-many-lines


def which(binary):
    pathVar = os.getenv('PATH')
    if platform.system() == 'Windows':
        binary = binary + '.exe'
        parts = pathVar.split(';')
    else:
        parts = pathVar.split(':')

    for part in parts:
        bin_path = os.path.join(part, binary)
        if os.path.exists(bin_path) and os.path.isfile(bin_path) and os.access(bin_path, os.X_OK):
            return bin_path

    return None


def _resource_client_factory():
    return get_mgmt_service_client(ResourceType.MGMT_RESOURCE_RESOURCES)


def wait_then_open(url):
    """
    Waits for a bit then opens a URL.  Useful for waiting for a proxy to come up, and then open the URL.
    """
    for _ in range(1, 10):
        try:
            urlopen(url, context=_ssl_context())
        except URLError:
            time.sleep(1)
        break
    webbrowser.open_new_tab(url)


def wait_then_open_async(url):
    """
    Spawns a thread that waits for a bit then opens a URL.
    """
    t = threading.Thread(target=wait_then_open, args=({url}))
    t.daemon = True
    t.start()


def acs_browse(resource_group, name, disable_browser=False, ssh_key_file=None):
    """
    Opens a browser to the web interface for the cluster orchestrator

    :param name: Name of the target Azure container service instance.
    :type name: String
    :param resource_group_name:  Name of Azure container service's resource group.
    :type resource_group_name: String
    :param disable_browser: If true, don't launch a web browser after estabilishing the proxy
    :type disable_browser: bool
    :param ssh_key_file: If set a path to an SSH key to use, only applies to DCOS
    :type ssh_key_file: string
    """
    _acs_browse_internal(_get_acs_info(name, resource_group), resource_group, name, disable_browser,
                         ssh_key_file)


def _acs_browse_internal(acs_info, resource_group, name, disable_browser, ssh_key_file):
    orchestrator_type = acs_info.orchestrator_profile.orchestrator_type  # pylint: disable=no-member

    if orchestrator_type == 'kubernetes' or \
       orchestrator_type == ContainerServiceOrchestratorTypes.kubernetes or \
       (acs_info.custom_profile and acs_info.custom_profile.orchestrator == 'kubernetes'):  # pylint: disable=no-member
        return k8s_browse(name, resource_group, disable_browser, ssh_key_file=ssh_key_file)
    elif orchestrator_type == 'dcos' or orchestrator_type == ContainerServiceOrchestratorTypes.dcos:
        return _dcos_browse_internal(acs_info, disable_browser, ssh_key_file)
    else:
        raise CLIError('Unsupported orchestrator type {} for browse'.format(orchestrator_type))


def k8s_browse(name, resource_group, disable_browser=False, ssh_key_file=None):
    """
    Launch a proxy and browse the Kubernetes web UI.
    :param disable_browser: If true, don't launch a web browser after estabilishing the proxy
    :type disable_browser: bool
    """
    acs_info = _get_acs_info(name, resource_group)
    _k8s_browse_internal(name, acs_info, disable_browser, ssh_key_file)


def _k8s_browse_internal(name, acs_info, disable_browser, ssh_key_file):
    if not which('kubectl'):
        raise CLIError('Can not find kubectl executable in PATH')
    browse_path = os.path.join(get_config_dir(), 'acsBrowseConfig.yaml')
    if os.path.exists(browse_path):
        os.remove(browse_path)

    _k8s_get_credentials_internal(name, acs_info, browse_path, ssh_key_file)

    logger.warning('Proxy running on 127.0.0.1:8001/ui')
    logger.warning('Press CTRL+C to close the tunnel...')
    if not disable_browser:
        wait_then_open_async('http://127.0.0.1:8001/ui')
    subprocess.call(["kubectl", "--kubeconfig", browse_path, "proxy"])


def dcos_browse(name, resource_group, disable_browser=False, ssh_key_file=None):
    """
    Creates an SSH tunnel to the Azure container service, and opens the Mesosphere DC/OS dashboard in the browser.

    :param name: name: Name of the target Azure container service instance.
    :type name: String
    :param resource_group_name:  Name of Azure container service's resource group.
    :type resource_group_name: String
    :param disable_browser: If true, don't launch a web browser after estabilishing the proxy
    :type disable_browser: bool
    :param ssh_key_file: Path to the SSH key to use
    :type ssh_key_file: string
    """
    acs_info = _get_acs_info(name, resource_group)
    _dcos_browse_internal(acs_info, disable_browser, ssh_key_file)


def _dcos_browse_internal(acs_info, disable_browser, ssh_key_file):
    if not os.path.isfile(ssh_key_file):
        raise CLIError('Private key file {} does not exist'.format(ssh_key_file))

    acs = acs_client.ACSClient()
    if not acs.connect(_get_host_name(acs_info), _get_username(acs_info),
                       key_filename=ssh_key_file):
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
    logger.warning('Proxy running on 127.0.0.1:%s', local_port)
    logger.warning('Press CTRL+C to close the tunnel...')
    if not disable_browser:
        wait_then_open_async('http://127.0.0.1')
    try:
        acs.create_tunnel(
            remote_host='127.0.0.1',
            remote_port=remote_port,
            local_port=local_port)
    finally:
        proxy.disable_http_proxy()

    return


def acs_install_cli(resource_group, name, install_location=None, client_version=None):
    acs_info = _get_acs_info(name, resource_group)
    orchestrator_type = acs_info.orchestrator_profile.orchestrator_type  # pylint: disable=no-member
    kwargs = {'install_location': install_location}
    if client_version:
        kwargs['client_version'] = client_version
    if orchestrator_type == 'kubernetes':
        return k8s_install_cli(**kwargs)
    elif orchestrator_type == 'dcos':
        return dcos_install_cli(**kwargs)
    else:
        raise CLIError('Unsupported orchestrator type {} for install-cli'.format(orchestrator_type))


def _ssl_context():
    if sys.version_info < (3, 4):
        return ssl.SSLContext(ssl.PROTOCOL_TLSv1)

    return ssl.create_default_context()


def _urlretrieve(url, filename):
    req = urlopen(url, context=_ssl_context())
    with open(filename, "wb") as f:
        f.write(req.read())


def dcos_install_cli(install_location=None, client_version='1.8'):
    """
    Downloads the dcos command line from Mesosphere
    """
    system = platform.system()

    if not install_location:
        raise CLIError(
            "No install location specified and it could not be determined from the current platform '{}'".format(
                system))
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

    logger.warning('Downloading client to %s', install_location)
    try:
        _urlretrieve(file_url, install_location)
        os.chmod(install_location,
                 os.stat(install_location).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except IOError as err:
        raise CLIError('Connection error while attempting to download client ({})'.format(err))


def k8s_install_cli(client_version='latest', install_location=None):
    """Install kubectl, a command-line interface for Kubernetes clusters."""

    if client_version == 'latest':
        context = _ssl_context()
        version = urlopen('https://storage.googleapis.com/kubernetes-release/release/stable.txt',
                          context=context).read()
        client_version = version.decode('UTF-8').strip()
    else:
        client_version = "v%s" % client_version

    file_url = ''
    system = platform.system()
    base_url = 'https://storage.googleapis.com/kubernetes-release/release/{}/bin/{}/amd64/{}'
    if system == 'Windows':
        file_url = base_url.format(client_version, 'windows', 'kubectl.exe')
    elif system == 'Linux':
        # TODO: Support ARM CPU here
        file_url = base_url.format(client_version, 'linux', 'kubectl')
    elif system == 'Darwin':
        file_url = base_url.format(client_version, 'darwin', 'kubectl')
    else:
        raise CLIError('Proxy server ({}) does not exist on the cluster.'.format(system))

    logger.warning('Downloading client to %s from %s', install_location, file_url)
    try:
        _urlretrieve(file_url, install_location)
        os.chmod(install_location,
                 os.stat(install_location).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except IOError as ex:
        raise CLIError('Connection error while attempting to download client ({})'.format(ex))


def _build_service_principal(client, name, url, client_secret):
    # use get_progress_controller
    hook = APPLICATION.get_progress_controller(True)
    hook.add(messsage='Creating service principal', value=0, total_val=1.0)
    logger.info('Creating service principal')
    result = create_application(client.applications, name, url, [url], password=client_secret)
    service_principal = result.app_id  # pylint: disable=no-member
    for x in range(0, 10):
        hook.add(message='Creating service principal', value=0.1 * x, total_val=1.0)
        try:
            create_service_principal(service_principal, client=client)
            break
        # TODO figure out what exception AAD throws here sometimes.
        except Exception as ex:  # pylint: disable=broad-except
            logger.info(ex)
            time.sleep(2 + 2 * x)
    else:
        return False
    hook.add(message='Finished service principal creation', value=1.0, total_val=1.0)
    logger.info('Finished service principal creation')
    return service_principal


def _add_role_assignment(role, service_principal, delay=2):
    # AAD can have delays in propagating data, so sleep and retry
    hook = APPLICATION.get_progress_controller(True)
    hook.add(message='Waiting for AAD role to propagate', value=0, total_val=1.0)
    logger.info('Waiting for AAD role to propagate')
    for x in range(0, 10):
        hook.add(message='Waiting for AAD role to propagate', value=0.1 * x, total_val=1.0)
        try:
            # TODO: break this out into a shared utility library
            create_role_assignment(role, service_principal)
            # Sleep for a while to get role assignment propagated
            time.sleep(20)
            break
        except CloudError as ex:
            if ex.message == 'The role assignment already exists.':
                break
            logger.info(ex.message)
        except:  # pylint: disable=bare-except
            pass
        time.sleep(delay + delay * x)
    else:
        return False
    hook.add(message='AAD role propagation done', value=1.0, total_val=1.0)
    logger.info('AAD role propagation done')
    return True


def _get_subscription_id():
    _, sub_id, _ = Profile().get_login_credentials(subscription_id=None)
    return sub_id


def _get_default_dns_prefix(name, resource_group_name, subscription_id):
    # Use subscription id to provide uniqueness and prevent DNS name clashes
    name_part = re.sub('[^A-Za-z0-9-]', '', name)[0:10]
    if not name_part[0].isalpha():
        name_part = (str('a') + name_part)[0:10]
    resource_group_part = re.sub('[^A-Za-z0-9-]', '', resource_group_name)[0:16]
    return '{}-{}-{}'.format(name_part, resource_group_part, subscription_id[0:6])


def list_acs_locations():
    return {
        "productionRegions": regionsInProd,
        "previewRegions": regionsInPreview
    }


# pylint: disable=too-many-locals
# pylint: disable-msg=too-many-arguments
def acs_create(resource_group_name, deployment_name, name, ssh_key_value, dns_name_prefix=None,
               location=None,
               admin_username="azureuser",
               api_version=None,
               master_profile=None,
               master_vm_size="Standard_D2_v2",
               master_osdisk_size=0,
               master_count=1,
               master_vnet_subnet_id="",
               master_first_consecutive_static_ip="10.240.255.5",
               master_storage_profile="",
               agent_profiles=None,
               agent_vm_size="Standard_D2_v2",
               agent_osdisk_size=0,
               agent_count=3,
               agent_vnet_subnet_id="",
               agent_ports=None,
               agent_storage_profile="",
               orchestrator_type="DCOS",
               orchestrator_release="", service_principal=None, client_secret=None, tags=None,
               windows=False, admin_password="", generate_ssh_keys=False,  # pylint: disable=unused-argument
               validate=False, no_wait=False):
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
    :param api_version: ACS API version to use
    :type api_version: str
    :param master_profile: MasterProfile used to describe master pool
    :type master_profile: dict
    :param master_vm_size: The size of master pool Virtual Machine
    :type master_vm_size: str
    :param master_osdisk_size: The osDisk size in GB of master pool Virtual Machine
    :type master_osdisk_size: int
    :param master_count: The number of masters for the cluster.
    :type master_count: int
    :param master_vnet_subnet_id: The vnet subnet id for master pool
    :type master_vnet_subnet_id: str
    :param master_storage_profile: The storage profile used for master pool.
     Possible value could be StorageAccount, ManagedDisk.
    :type master_storage_profile: str
    :param agent_profiles: AgentPoolProfiles used to describe agent pools
    :type agent_profiles: dict
    :param agent_count: the default number of agents for the agent pools.
    :type agent_count: int
    :param agent_vm_size: The size of the Virtual Machine.
    :type agent_vm_size: str
    :param agent_osdisk_size: The osDisk size in GB of agent pool Virtual Machine
    :type agent_osdisk_size: int
    :param agent_vnet_subnet_id: The vnet subnet id for master pool
    :type agent_vnet_subnet_id: str
    :param agent_ports: the ports exposed on the agent pool
    :type agent_ports: list
    :param agent_storage_profile: The storage profile used for agent pool.
     Possible value could be StorageAccount, ManagedDisk.
    :type agent_storage_profile: str
    :param location: Location for VM resources.
    :type location: str
    :param orchestrator_type: The type of orchestrator used to manage the
     applications on the cluster.
    :type orchestrator_type: str or :class:`orchestratorType
     <Default.models.orchestratorType>`
    :param service_principal: The service principal used for cluster authentication
     to Azure APIs. If not specified, it is created for you and stored in the
     ${HOME}/.azure directory.
    :type service_principal: str
    :param client_secret: The secret associated with the service principal. If
     --service-principal is specified, then secret should also be specified. If
     --service-principal is not specified, the secret is auto-generated for you
     and stored in ${HOME}/.azure/ directory.
    :param tags: Tags object.
    :type tags: object
    :param windows: If true, the cluster will be built for running Windows container.
    :type windows: bool
    :param admin_password: The adminstration password for Windows nodes. Only available if --windows=true
    :type admin_password: str
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
    if ssh_key_value is not None and not is_valid_ssh_rsa_public_key(ssh_key_value):
        raise CLIError('Provided ssh key ({}) is invalid or non-existent'.format(ssh_key_value))

    subscription_id = _get_subscription_id()
    if not dns_name_prefix:
        dns_name_prefix = _get_default_dns_prefix(name, resource_group_name, subscription_id)

    groups = _resource_client_factory().resource_groups
    # Just do the get, we don't need the result, it will error out if the group doesn't exist.
    rg = groups.get(resource_group_name)
    if location is None:
        location = rg.location  # pylint:disable=no-member

    # if api-version is not specified, or specified in a version not supported
    # override based on location
    if api_version is None or api_version not in ["2017-01-31", "2017-07-01"]:
        # 2017-07-01 supported in the preview locations
        if location in regionsInPreview:
            api_version = "2017-07-01"
        # 2017-01-31 applied to other locations
        else:
            api_version = "2017-01-31"

    if orchestrator_type.lower() == 'kubernetes':
        principal_obj = _ensure_service_principal(service_principal, client_secret, subscription_id,
                                                  dns_name_prefix, location, name)
        client_secret = principal_obj.get("client_secret")
        service_principal = principal_obj.get("service_principal")

    elif windows:
        raise CLIError('--windows is only supported for Kubernetes clusters')

    return _create(resource_group_name, deployment_name, dns_name_prefix, name,
                   ssh_key_value, admin_username=admin_username,
                   api_version=api_version,
                   orchestrator_type=orchestrator_type,
                   orchestrator_release=orchestrator_release,
                   master_profile=master_profile,
                   master_vm_size=master_vm_size,
                   master_osdisk_size=master_osdisk_size,
                   master_vnet_subnet_id=master_vnet_subnet_id,
                   master_first_consecutive_static_ip=master_first_consecutive_static_ip,
                   master_storage_profile=master_storage_profile,
                   agent_profiles=agent_profiles,
                   agent_count=agent_count, agent_vm_size=agent_vm_size,
                   agent_osdisk_size=agent_osdisk_size,
                   agent_vnet_subnet_id=agent_vnet_subnet_id,
                   agent_ports=agent_ports,
                   agent_storage_profile=agent_storage_profile,
                   location=location, service_principal=service_principal,
                   client_secret=client_secret, master_count=master_count,
                   windows=windows, admin_password=admin_password,
                   validate=validate, no_wait=no_wait, tags=tags)


def store_acs_service_principal(subscription_id, client_secret, service_principal,
                                config_path=os.path.join(get_config_dir(),
                                                         'acsServicePrincipal.json')):
    obj = {}
    if client_secret:
        obj['client_secret'] = client_secret
    if service_principal:
        obj['service_principal'] = service_principal

    fullConfig = load_acs_service_principals(config_path=config_path)
    if not fullConfig:
        fullConfig = {}
    fullConfig[subscription_id] = obj

    with os.fdopen(os.open(config_path, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600),
                   'w+') as spFile:
        json.dump(fullConfig, spFile)


def load_acs_service_principal(subscription_id, config_path=os.path.join(get_config_dir(),
                                                                         'acsServicePrincipal.json')):
    config = load_acs_service_principals(config_path)
    if not config:
        return None
    return config.get(subscription_id)


def load_acs_service_principals(config_path):
    if not os.path.exists(config_path):
        return None
    fd = os.open(config_path, os.O_RDONLY)
    try:
        with os.fdopen(fd) as f:
            return shell_safe_json_parse(f.read())
    except:  # pylint: disable=bare-except
        return None


# pylint: disable-msg=too-many-arguments
def _create(resource_group_name, deployment_name, dns_name_prefix, name, ssh_key_value,
            admin_username="azureuser", api_version=None, orchestrator_type="DCOS", orchestrator_release="",
            master_profile=None, master_vm_size="Standard_D2_v2", master_osdisk_size=0, master_count=1,
            master_vnet_subnet_id="", master_first_consecutive_static_ip="", master_storage_profile="",
            agent_profiles=None, agent_count=3, agent_vm_size="Standard_D2_v2", agent_osdisk_size=0,
            agent_vnet_subnet_id="", agent_ports=None, agent_storage_profile="",
            location=None, service_principal=None, client_secret=None,
            windows=False, admin_password='', validate=False, no_wait=False, tags=None):
    if not location:
        location = '[resourceGroup().location]'
    windows_profile = None
    os_type = 'Linux'
    if windows:
        if not admin_password:
            raise CLIError('--admin-password is required.')
        if len(admin_password) < 6:
            raise CLIError('--admin-password must be at least 6 characters')
        windows_profile = {
            "adminUsername": admin_username,
            "adminPassword": admin_password,
        }
        os_type = 'Windows'

    if not agent_ports:
        agent_ports = []

    # The resources.properties fields should match with ContainerServices' api model
    # So assumption:
    # The API model created for new version should be compatible to use it in an older version
    # There maybe additional field specified, but could be ignored by the older version
    masterPoolProfile = {}
    defaultMasterPoolProfile = {
        "count": int(master_count),
        "dnsPrefix": dns_name_prefix + 'mgmt',
    }
    if api_version == "2017-07-01":
        defaultMasterPoolProfile = _update_dict(defaultMasterPoolProfile, {
            "count": int(master_count),
            "dnsPrefix": dns_name_prefix + 'mgmt',
            "vmSize": master_vm_size,
            "osDiskSizeGB": int(master_osdisk_size),
            "vnetSubnetID": master_vnet_subnet_id,
            "firstConsecutiveStaticIP": master_first_consecutive_static_ip,
            "storageProfile": master_storage_profile,
        })
    if not master_profile:
        masterPoolProfile = defaultMasterPoolProfile
    else:
        masterPoolProfile = _update_dict(defaultMasterPoolProfile, master_profile)

    agentPoolProfiles = []
    defaultAgentPoolProfile = {
        "count": int(agent_count),
        "vmSize": agent_vm_size,
        "osType": os_type,
        "dnsPrefix": dns_name_prefix + 'agent',
    }
    if api_version == "2017-07-01":
        defaultAgentPoolProfile = _update_dict(defaultAgentPoolProfile, {
            "count": int(agent_count),
            "vmSize": agent_vm_size,
            "osDiskSizeGB": int(agent_osdisk_size),
            "osType": os_type,
            "dnsPrefix": dns_name_prefix + 'agent',
            "vnetSubnetID": agent_vnet_subnet_id,
            "ports": agent_ports,
            "storageProfile": agent_storage_profile,
        })
    if agent_profiles is None:
        agentPoolProfiles.append(_update_dict(defaultAgentPoolProfile, {"name": "agentpool0"}))
    else:
        # override agentPoolProfiles by using the passed in agent_profiles
        for idx, ap in enumerate(agent_profiles):
            # if the user specified dnsPrefix, we honor that
            # otherwise, we use the idx to avoid duplicate dns name
            a = _update_dict({"dnsPrefix": dns_name_prefix + 'agent' + str(idx)}, ap)
            agentPoolProfiles.append(_update_dict(defaultAgentPoolProfile, a))

    # define outputs
    outputs = {
        "masterFQDN": {
            "type": "string",
            "value": "[reference(concat('Microsoft.ContainerService/containerServices/', '{}')).masterProfile.fqdn]".format(name)  # pylint: disable=line-too-long
        },
        "sshMaster0": {
            "type": "string",
            "value": "[concat('ssh ', '{0}', '@', reference(concat('Microsoft.ContainerService/containerServices/', '{1}')).masterProfile.fqdn, ' -A -p 22')]".format(admin_username, name)  # pylint: disable=line-too-long
        },
    }
    if orchestrator_type.lower() != "kubernetes":
        outputs["agentFQDN"] = {
            "type": "string",
            "value": "[reference(concat('Microsoft.ContainerService/containerServices/', '{}')).agentPoolProfiles[0].fqdn]".format(name)  # pylint: disable=line-too-long
        }
        # override sshMaster0 for non-kubernetes scenarios
        outputs["sshMaster0"] = {
            "type": "string",
            "value": "[concat('ssh ', '{0}', '@', reference(concat('Microsoft.ContainerService/containerServices/', '{1}')).masterProfile.fqdn, ' -A -p 2200')]".format(admin_username, name)  # pylint: disable=line-too-long
        }
    properties = {
        "orchestratorProfile": {
            "orchestratorType": orchestrator_type,
        },
        "masterProfile": masterPoolProfile,
        "agentPoolProfiles": agentPoolProfiles,
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
    }
    if api_version == "2017-07-01":
        properties["orchestratorProfile"]["orchestratorRelease"] = orchestrator_release

    if windows_profile is not None:
        properties["windowsProfile"] = windows_profile

    resource = {
        "apiVersion": api_version,
        "location": location,
        "type": "Microsoft.ContainerService/containerServices",
        "name": name,
        "tags": tags,
        "properties": properties,
    }
    template = {
        "$schema": "https://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#",
        "contentVersion": "1.0.0.0",
        "resources": [
            resource,
        ],
        "outputs": outputs,
    }
    params = {}
    if service_principal is not None and client_secret is not None:
        properties["servicePrincipalProfile"] = {
            "clientId": service_principal,
            "secret": "[parameters('clientSecret')]",
        }
        template["parameters"] = {
            "clientSecret": {
                "type": "secureString",
                "metadata": {
                    "description": "The client secret for the service principal"
                }
            }
        }
        params = {
            "clientSecret": {
                "value": client_secret
            }
        }
    return _invoke_deployment(resource_group_name, deployment_name, template, params, validate, no_wait)


def _invoke_deployment(resource_group_name, deployment_name, template, parameters, validate, no_wait):
    from azure.mgmt.resource.resources import ResourceManagementClient
    from azure.mgmt.resource.resources.models import DeploymentProperties

    properties = DeploymentProperties(template=template, parameters=parameters, mode='incremental')
    smc = get_mgmt_service_client(ResourceManagementClient).deployments
    if validate:
        logger.info('==== BEGIN TEMPLATE ====')
        logger.info(json.dumps(template, indent=2))
        logger.info('==== END TEMPLATE ====')
        return smc.validate(resource_group_name, deployment_name, properties)
    return smc.create_or_update(resource_group_name, deployment_name, properties, raw=no_wait)


def k8s_get_credentials(name, resource_group_name,
                        path=os.path.join(os.path.expanduser('~'), '.kube', 'config'),
                        ssh_key_file=None):
    """Download and install kubectl credentials from the cluster master
    :param name: The name of the cluster.
    :type name: str
    :param resource_group_name: The name of the resource group.
    :type resource_group_name: str
    :param path: Where to install the kubectl config file
    :type path: str
    :param ssh_key_file: Path to an SSH key file to use
    :type ssh_key_file: str
    """
    acs_info = _get_acs_info(name, resource_group_name)
    _k8s_get_credentials_internal(name, acs_info, path, ssh_key_file)


def _k8s_get_credentials_internal(name, acs_info, path, ssh_key_file):
    if ssh_key_file is not None and not os.path.isfile(ssh_key_file):
        raise CLIError('Private key file {} does not exist'.format(ssh_key_file))

    dns_prefix = acs_info.master_profile.dns_prefix  # pylint: disable=no-member
    location = acs_info.location  # pylint: disable=no-member
    user = acs_info.linux_profile.admin_username  # pylint: disable=no-member
    _mkdir_p(os.path.dirname(path))

    path_candidate = path
    ix = 0
    while os.path.exists(path_candidate):
        ix += 1
        path_candidate = '{}-{}-{}'.format(path, name, ix)

    # TODO: this only works for public cloud, need other casing for national clouds

    acs_client.secure_copy(user, '{}.{}.cloudapp.azure.com'.format(dns_prefix, location),
                           '.kube/config', path_candidate, key_filename=ssh_key_file)

    # merge things
    if path_candidate != path:
        try:
            merge_kubernetes_configurations(path, path_candidate)
        except yaml.YAMLError as exc:
            logger.warning('Failed to merge credentials to kube config file: %s', exc)
            logger.warning('The credentials have been saved to %s', path_candidate)


def _handle_merge(existing, addition, key):
    if addition[key]:
        if existing[key] is None:
            existing[key] = addition[key]
            return

        for i in addition[key]:
            if i not in existing[key]:
                existing[key].append(i)


def merge_kubernetes_configurations(existing_file, addition_file):
    try:
        with open(existing_file) as stream:
            existing = yaml.safe_load(stream)
    except (IOError, OSError) as ex:
        if getattr(ex, 'errno', 0) == errno.ENOENT:
            raise CLIError('{} does not exist'.format(existing_file))
        else:
            raise
    except yaml.parser.ParserError as ex:
        raise CLIError('Error parsing {} ({})'.format(existing_file, str(ex)))

    try:
        with open(addition_file) as stream:
            addition = yaml.safe_load(stream)
    except (IOError, OSError) as ex:
        if getattr(ex, 'errno', 0) == errno.ENOENT:
            raise CLIError('{} does not exist'.format(existing_file))
        else:
            raise
    except yaml.parser.ParserError as ex:
        raise CLIError('Error parsing {} ({})'.format(addition_file, str(ex)))

    if addition is None:
        raise CLIError('failed to load additional configuration from {}'.format(addition_file))

    if existing is None:
        existing = addition
    else:
        _handle_merge(existing, addition, 'clusters')
        _handle_merge(existing, addition, 'users')
        _handle_merge(existing, addition, 'contexts')
        existing['current-context'] = addition['current-context']

    with open(existing_file, 'w+') as stream:
        yaml.dump(existing, stream, default_flow_style=True)

    current_context = addition.get('current-context', 'UNKNOWN')
    msg = 'Merged "{}" as current context in {}'.format(current_context, existing_file)
    print(msg)


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
    mgmt_client = get_mgmt_service_client(ContainerServiceClient)
    return mgmt_client.container_services.get(resource_group_name, name)


def _rand_str(n):
    """
    Gets a random string
    """
    choices = string.ascii_lowercase + string.digits
    return ''.join(random.SystemRandom().choice(choices) for _ in range(n))


def _mkdir_p(path):
    # http://stackoverflow.com/a/600612
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def update_acs(client, resource_group_name, container_service_name, new_agent_count):
    instance = client.get(resource_group_name, container_service_name)
    instance.agent_pool_profiles[0].count = new_agent_count  # pylint: disable=no-member

    # null out the service principal because otherwise validation complains
    if instance.orchestrator_profile.orchestrator_type == ContainerServiceOrchestratorTypes.kubernetes:
        instance.service_principal_profile = None

    # null out the windows profile so that validation doesn't complain about not having the admin password
    instance.windows_profile = None

    return client.create_or_update(resource_group_name, container_service_name, instance)


def list_container_services(client, resource_group_name=None):
    ''' List Container Services. '''
    svc_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list(svc_list)


def show_service_principal(client, identifier):
    object_id = _resolve_service_principal(client, identifier)
    return client.get(object_id)


def _resolve_service_principal(client, identifier):
    # todo: confirm with graph team that a service principal name must be unique
    result = list(client.list(filter="servicePrincipalNames/any(c:c eq '{}')".format(identifier)))
    if result:
        return result[0].object_id
    try:
        uuid.UUID(identifier)
        return identifier  # assume an object id
    except ValueError:
        raise CLIError("service principal '{}' doesn't exist".format(identifier))


def create_application(client, display_name, homepage, identifier_uris,
                       available_to_other_tenants=False, password=None, reply_urls=None,
                       key_value=None, key_type=None, key_usage=None, start_date=None,
                       end_date=None):
    password_creds, key_creds = _build_application_creds(password, key_value, key_type,
                                                         key_usage, start_date, end_date)

    app_create_param = ApplicationCreateParameters(available_to_other_tenants,
                                                   display_name,
                                                   identifier_uris,
                                                   homepage=homepage,
                                                   reply_urls=reply_urls,
                                                   key_credentials=key_creds,
                                                   password_credentials=password_creds)
    return client.create(app_create_param)


def _build_application_creds(password=None, key_value=None, key_type=None,
                             key_usage=None, start_date=None, end_date=None):
    if password and key_value:
        raise CLIError('specify either --password or --key-value, but not both.')

    if not start_date:
        start_date = datetime.datetime.utcnow()
    elif isinstance(start_date, str):
        start_date = dateutil.parser.parse(start_date)

    if not end_date:
        end_date = start_date + relativedelta(years=1)
    elif isinstance(end_date, str):
        end_date = dateutil.parser.parse(end_date)

    key_type = key_type or 'AsymmetricX509Cert'
    key_usage = key_usage or 'Verify'

    password_creds = None
    key_creds = None
    if password:
        password_creds = [PasswordCredential(start_date, end_date, str(uuid.uuid4()), password)]
    elif key_value:
        key_creds = [KeyCredential(start_date, end_date, key_value, str(uuid.uuid4()), key_usage, key_type)]

    return (password_creds, key_creds)


def create_service_principal(identifier, resolve_app=True, client=None):
    if client is None:
        client = _graph_client_factory()

    if resolve_app:
        try:
            uuid.UUID(identifier)
            result = list(client.applications.list(filter="appId eq '{}'".format(identifier)))
        except ValueError:
            result = list(client.applications.list(
                filter="identifierUris/any(s:s eq '{}')".format(identifier)))

        if not result:  # assume we get an object id
            result = [client.applications.get(identifier)]
        app_id = result[0].app_id
    else:
        app_id = identifier

    return client.service_principals.create(ServicePrincipalCreateParameters(app_id, True))


def create_role_assignment(role, assignee, resource_group_name=None, scope=None):
    return _create_role_assignment(role, assignee, resource_group_name, scope)


def _create_role_assignment(role, assignee, resource_group_name=None, scope=None,
                            resolve_assignee=True):
    factory = _auth_client_factory(scope)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions

    scope = _build_role_scope(resource_group_name, scope,
                              assignments_client.config.subscription_id)

    role_id = _resolve_role_id(role, scope, definitions_client)
    object_id = _resolve_object_id(assignee) if resolve_assignee else assignee
    properties = RoleAssignmentProperties(role_id, object_id)
    assignment_name = uuid.uuid4()
    custom_headers = None
    return assignments_client.create(scope, assignment_name, properties,
                                     custom_headers=custom_headers)


def _build_role_scope(resource_group_name, scope, subscription_id):
    subscription_scope = '/subscriptions/' + subscription_id
    if scope:
        if resource_group_name:
            err = 'Resource group "{}" is redundant because scope is supplied'
            raise CLIError(err.format(resource_group_name))
    elif resource_group_name:
        scope = subscription_scope + '/resourceGroups/' + resource_group_name
    else:
        scope = subscription_scope
    return scope


def _resolve_role_id(role, scope, definitions_client):
    role_id = None
    try:
        uuid.UUID(role)
        role_id = role
    except ValueError:
        pass
    if not role_id:  # retrieve role id
        role_defs = list(definitions_client.list(scope, "roleName eq '{}'".format(role)))
        if not role_defs:
            raise CLIError("Role '{}' doesn't exist.".format(role))
        elif len(role_defs) > 1:
            ids = [r.id for r in role_defs]
            err = "More than one role matches the given name '{}'. Please pick a value from '{}'"
            raise CLIError(err.format(role, ids))
        role_id = role_defs[0].id
    return role_id


def _resolve_object_id(assignee):
    client = _graph_client_factory()
    result = None
    if assignee.find('@') >= 0:  # looks like a user principal name
        result = list(client.users.list(filter="userPrincipalName eq '{}'".format(assignee)))
    if not result:
        result = list(client.service_principals.list(
            filter="servicePrincipalNames/any(c:c eq '{}')".format(assignee)))
    if not result:  # assume an object id, let us verify it
        result = _get_object_stubs(client, [assignee])

    # 2+ matches should never happen, so we only check 'no match' here
    if not result:
        raise CLIError("No matches in graph database for '{}'".format(assignee))

    return result[0].object_id


def _get_object_stubs(graph_client, assignees):
    params = GetObjectsParameters(include_directory_object_references=True,
                                  object_ids=assignees)
    return list(graph_client.objects.get_objects_by_object_ids(params))


def _update_dict(dict1, dict2):
    cp = dict1.copy()
    cp.update(dict2)
    return cp


def aks_browse(client, resource_group_name, name, disable_browser=False):
    """
    Open a web browser to the dashboard for a managed Kubernetes cluster.

    :param disable_browser: If true, don't launch a web browser after establishing the
     kubectl port-forward
    :type disable_browser: bool
    """
    if not which('kubectl'):
        raise CLIError('Can not find kubectl executable in PATH')

    proxy_url = 'http://127.0.0.1:8001/'
    with tempfile.NamedTemporaryFile(mode='w+t') as kube_config:
        browse_path = kube_config.name
        # TODO: need to add an --admin option?
        aks_get_credentials(client, resource_group_name, name, admin=False, path=browse_path)
        # find the dashboard pod's name
        dashboard_pod = subprocess.check_output(
            ["kubectl", "get", "pods", "--namespace", "kube-system", "--output", "name",
             "--selector", "k8s-app=kubernetes-dashboard"],
            universal_newlines=True)
        if dashboard_pod:
            # remove the "pods/" prefix from the name
            dashboard_pod = str(dashboard_pod)[5:].strip()
        else:
            raise CLIError("Couldn't find the Kubernetes dashboard pod.")
        # launch kubectl port-forward locally to access the remote dashboard
        logger.warning('Proxy running on {}'.format(proxy_url))
        logger.warning('Press CTRL+C to close the tunnel...')
        if not disable_browser:
            wait_then_open_async(proxy_url)
        subprocess.call(["kubectl", "--kubeconfig", browse_path, "--namespace", "kube-system",
                         "port-forward", dashboard_pod, "8001:9090"])


def aks_create(client, resource_group_name, name, ssh_key_value,  # pylint: disable=too-many-locals
               dns_name_prefix=None,
               location=None,
               admin_username="azureuser",
               kubernetes_version="1.7.7",
               agent_vm_size="Standard_D2_v2",
               agent_osdisk_size=0,
               agent_count=3,
               service_principal=None, client_secret=None,
               tags=None,
               generate_ssh_keys=False,  # pylint: disable=unused-argument
               no_wait=False):
    """Create a managed Kubernetes cluster.
    :type dns_name_prefix: str
    :param location: Location for VM resources.
    :type location: str
    :param ssh_key_value: Configure all linux machines with the SSH RSA
     public key string.  Your key should include three parts, for example
    'ssh-rsa AAAAB...snip...UcyupgH azureuser@linuxvm
    :type ssh_key_value: str
    :param admin_username: User name for the Linux Virtual Machines.
    :type admin_username: str
    :param kubernetes_version: The version of Kubernetes to use for creating
     the cluster, such as '1.7.7' or '1.8.1'.
    :type kubernetes_version: str
    :param agent_count: the default number of agents for the agent pools.
    :type agent_count: int
    :param agent_vm_size: The size of the Virtual Machine.
    :type agent_vm_size: str
    :param agent_osdisk_size: The osDisk size in GB of agent pool Virtual Machine
    :type agent_osdisk_size: int
    :param service_principal: The service principal used for cluster authentication
     to Azure APIs. If not specified, it is created for you and stored in the
     ${HOME}/.azure directory.
    :type service_principal: str
    :param client_secret: The secret associated with the service principal. If
     --service-principal is specified, then secret should also be specified. If
     --service-principal is not specified, the secret is auto-generated for you
     and stored in ${HOME}/.azure/ directory.
    :param tags: Tags object.
    :type tags: object
    :param no_wait: Start creating but return immediately instead of waiting
     until the managed cluster is created.
    :type no_wait: bool
    """
    try:
        if not ssh_key_value or not is_valid_ssh_rsa_public_key(ssh_key_value):
            raise ValueError()
    except:
        shortened_key = '{} ... {}'.format(ssh_key_value[:30], ssh_key_value[-30:]).strip()
        raise CLIError('Provided ssh key ({}) is invalid or non-existent'.format(shortened_key))

    subscription_id = _get_subscription_id()
    if not dns_name_prefix:
        dns_name_prefix = _get_default_dns_prefix(name, resource_group_name, subscription_id)

    groups = _resource_client_factory().resource_groups
    # Just do the get, we don't need the result, it will error out if the group doesn't exist.
    rg = groups.get(resource_group_name)
    if location is None:
        location = rg.location  # pylint:disable=no-member

    ssh_config = ContainerServiceSshConfiguration(
        [ContainerServiceSshPublicKey(key_data=ssh_key_value)])
    agent_pool_profile = ContainerServiceAgentPoolProfile(
        'agentpool1',  # Must be 12 chars or less before ACS RP adds to it
        count=int(agent_count),
        vm_size=agent_vm_size,
        dns_prefix=dns_name_prefix,
        os_type="Linux",
        storage_profile=ContainerServiceStorageProfileTypes.managed_disks
    )
    if agent_osdisk_size:
        agent_pool_profile.os_disk_size_gb = int(agent_osdisk_size)

    linux_profile = ContainerServiceLinuxProfile(admin_username, ssh=ssh_config)
    principal_obj = _ensure_service_principal(service_principal=service_principal, client_secret=client_secret,
                                              subscription_id=subscription_id, dns_name_prefix=dns_name_prefix,
                                              location=location, name=name)
    service_principal_profile = ContainerServiceServicePrincipalProfile(
        client_id=principal_obj.get("service_principal"),
        secret=principal_obj.get("client_secret"),
        key_vault_secret_ref=None)

    props = ManagedClusterProperties(
        dns_prefix=dns_name_prefix,
        kubernetes_version=kubernetes_version,
        agent_pool_profiles=[agent_pool_profile],
        linux_profile=linux_profile,
        service_principal_profile=service_principal_profile)
    mc = ManagedCluster(location=location, tags=tags, properties=props)

    return client.create_or_update(
        resource_group_name=resource_group_name, resource_name=name, parameters=mc, raw=no_wait)


def aks_delete(client, resource_group_name, name, no_wait=False, **kwargs):  # pylint: disable=unused-argument
    """Delete a managed Kubernetes cluster.
    :param no_wait: Start deleting but return immediately instead of waiting
     until the managed cluster is deleted.
    :type no_wait: bool
    """
    return client.delete(resource_group_name, name, raw=no_wait)


def aks_get_credentials(client, resource_group_name, name, admin=False,
                        path=os.path.join(os.path.expanduser('~'), '.kube', 'config')):
    """Get credentials to access a managed Kubernetes cluster.
    :param path: A kubectl config file to create or update. Use "-" to print YAML
     to stdout instead
    :type path: str
    :param admin: Get the "clusterAdmin" kubectl config instead of the default "clusterUser"
    :type admin: bool
    """
    mc = aks_show(client, resource_group_name, name)
    access_profiles = mc.properties.access_profiles
    if not access_profiles:
        msg = "No Kubernetes access profiles found. Cluster provisioning state is \"{}\"."
        raise CLIError(msg.format(mc.properties.provisioning_state))
    else:
        access_profiles = access_profiles.as_dict()
        access_profile = access_profiles.get('cluster_admin' if admin else 'cluster_user')
        encoded_kubeconfig = access_profile.get('kube_config')
        kubeconfig = base64.b64decode(encoded_kubeconfig).decode(encoding='UTF-8')

        # Special case for printing to stdout
        if path == "-":
            print(kubeconfig)
            return

        # ensure that at least an empty ~/.kube/config exists
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError as ex:
                if ex.errno != errno.EEXIST:
                    raise
        if not os.path.exists(path):
            with open(path, 'w+t'):
                pass

        # merge the new kubeconfig into the existing one
        with tempfile.NamedTemporaryFile(mode='w+t') as additional_file:
            additional_file.write(kubeconfig)
            additional_file.flush()
            try:
                merge_kubernetes_configurations(path, additional_file.name)
            except yaml.YAMLError as ex:
                logger.warning('Failed to merge credentials to kube config file: %s', ex)


def aks_get_versions(client, resource_group_name, name):
    """Get versions available to upgrade a managed Kubernetes cluster.
    """
    return client.get_upgrade_profile(resource_group_name, name)


def aks_list(client, resource_group_name=None):
    """List managed Kubernetes clusters."""
    if resource_group_name:
        managed_clusters = client.list_by_resource_group(resource_group_name)
    else:
        managed_clusters = client.list()
    return _remove_nulls(list(managed_clusters))


def aks_show(client, resource_group_name, name):
    """Show a managed Kubernetes cluster."""
    mc = client.get(resource_group_name, name)
    return _remove_nulls([mc])[0]


def aks_scale(client, resource_group_name, name, agent_count, no_wait=False):
    """Scale the agent pool in a managed Kubernetes cluster.
    :param agent_count: The desired number of agent nodes.
    :type agent_count: int
    :param no_wait: Start upgrading but return immediately instead of waiting
     until the managed cluster is upgraded.
    :type no_wait: bool
    """
    instance = client.get(resource_group_name, name)
    # TODO: change this approach when we support multiple agent pools.
    instance.properties.agent_pool_profiles[0].count = int(agent_count)  # pylint: disable=no-member

    # null out the service principal because otherwise validation complains
    instance.properties.service_principal_profile = None

    return client.create_or_update(resource_group_name, name, instance, raw=no_wait)


def aks_upgrade(client, resource_group_name, name, kubernetes_version, no_wait=False, **kwargs):  # pylint: disable=unused-argument
    """Upgrade a managed Kubernetes cluster to a newer version.
    :param kubernetes_version: The version of Kubernetes to upgrade the cluster to,
    such as '1.7.7' or '1.8.1'.
    :type kubernetes_version: str
    :param no_wait: Start upgrading but return immediately instead of waiting
     until the managed cluster is upgraded.
    :type no_wait: bool
    """
    instance = client.get(resource_group_name, name)
    instance.properties.kubernetes_release = None
    instance.properties.kubernetes_version = kubernetes_version

    # null out the service principal because otherwise validation complains
    instance.properties.service_principal_profile = None

    return client.create_or_update(resource_group_name, name, instance, raw=no_wait)


def _ensure_service_principal(service_principal=None,
                              client_secret=None,
                              subscription_id=None,
                              dns_name_prefix=None,
                              location=None,
                              name=None):
    # TODO: This really needs to be unit tested.
    client = _graph_client_factory()
    if not service_principal:
        # --service-principal not specified, try to load it from local disk
        principal_obj = load_acs_service_principal(subscription_id)
        if principal_obj:
            service_principal = principal_obj.get('service_principal')
            client_secret = principal_obj.get('client_secret')
        else:
            # Nothing to load, make one.
            if not client_secret:
                client_secret = binascii.b2a_hex(os.urandom(10)).decode('utf-8')
            salt = binascii.b2a_hex(os.urandom(3)).decode('utf-8')
            url = 'http://{}.{}.{}.cloudapp.azure.com'.format(salt, dns_name_prefix, location)

            service_principal = _build_service_principal(client, name, url, client_secret)
            if not service_principal:
                raise CLIError('Could not create a service principal with the right permissions. '
                               'Are you an Owner on this project?')
            logger.info('Created a service principal: %s', service_principal)
            # add role first before save it
            if not _add_role_assignment('Contributor', service_principal):
                logger.warning('Could not create a service principal with the right permissions. '
                               'Are you an Owner on this project?')
    else:
        # --service-principal specfied, validate --client-secret was too
        if not client_secret:
            raise CLIError('--client-secret is required if --service-principal is specified')
    store_acs_service_principal(subscription_id, client_secret, service_principal)
    return load_acs_service_principal(subscription_id)


def _remove_nulls(managed_clusters):
    """
    Remove some often-empty fields from a list of ManagedClusters, so the JSON representation
    doesn't contain distracting null fields.

    This works around a quirk of the SDK for python behavior. These fields are not sent
    by the server, but get recreated by the CLI's own "to_dict" serialization.
    """
    attrs = ['tags']
    ap_attrs = ['dns_prefix', 'fqdn', 'os_disk_size_gb', 'ports', 'vnet_subnet_id']
    sp_attrs = ['key_vault_secret_ref', 'secret']
    for managed_cluster in managed_clusters:
        for attr in attrs:
            if getattr(managed_cluster, attr, None) is None:
                delattr(managed_cluster, attr)
        props = managed_cluster.properties
        for ap_profile in props.agent_pool_profiles:
            for attr in ap_attrs:
                if getattr(ap_profile, attr, None) is None:
                    delattr(ap_profile, attr)
        for attr in sp_attrs:
            if getattr(props.service_principal_profile, attr, None) is None:
                delattr(props.service_principal_profile, attr)
    return managed_clusters
