# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import binascii
import datetime
import errno
import json
import os
import os.path
import platform
import random
import re
import ssl
import stat
import string
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import webbrowser
from six.moves.urllib.request import urlopen  # pylint: disable=import-error
from six.moves.urllib.error import URLError  # pylint: disable=import-error

import yaml
import dateutil.parser
from dateutil.relativedelta import relativedelta
from knack.log import get_logger
from knack.util import CLIError
from msrestazure.azure_exceptions import CloudError

from azure.cli.command_modules.acs import acs_client, proxy
from azure.cli.command_modules.acs._params import regions_in_preview, regions_in_prod
from azure.cli.core.api import get_config_dir
from azure.cli.core._profile import Profile
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.keys import is_valid_ssh_rsa_public_key
from azure.cli.core.util import in_cloud_console, shell_safe_json_parse, truncate_text, sdk_no_wait
from azure.graphrbac.models import (ApplicationCreateParameters,
                                    PasswordCredential,
                                    KeyCredential,
                                    ServicePrincipalCreateParameters,
                                    GetObjectsParameters)
from azure.mgmt.containerservice.models import ContainerServiceLinuxProfile
from azure.mgmt.containerservice.models import ContainerServiceNetworkProfile
from azure.mgmt.containerservice.models import ContainerServiceOrchestratorTypes
from azure.mgmt.containerservice.models import ContainerServiceServicePrincipalProfile
from azure.mgmt.containerservice.models import ContainerServiceSshConfiguration
from azure.mgmt.containerservice.models import ContainerServiceSshPublicKey
from azure.mgmt.containerservice.models import ContainerServiceStorageProfileTypes
from azure.mgmt.containerservice.models import ManagedCluster
from azure.mgmt.containerservice.models import ManagedClusterAADProfile
from azure.mgmt.containerservice.models import ManagedClusterAddonProfile
from azure.mgmt.containerservice.models import ManagedClusterAgentPoolProfile
from ._client_factory import cf_container_services
from ._client_factory import cf_resource_groups
from ._client_factory import get_auth_management_client
from ._client_factory import get_graph_rbac_management_client
from ._client_factory import cf_resources

logger = get_logger(__name__)


# pylint:disable=too-many-lines,unused-argument


def which(binary):
    path_var = os.getenv('PATH')
    if platform.system() == 'Windows':
        binary = binary + '.exe'
        parts = path_var.split(';')
    else:
        parts = path_var.split(':')

    for part in parts:
        bin_path = os.path.join(part, binary)
        if os.path.exists(bin_path) and os.path.isfile(bin_path) and os.access(bin_path, os.X_OK):
            return bin_path

    return None


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


def acs_browse(cmd, client, resource_group, name, disable_browser=False, ssh_key_file=None):
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
    acs_info = _get_acs_info(cmd.cli_ctx, name, resource_group)
    _acs_browse_internal(cmd, client, acs_info, resource_group, name, disable_browser, ssh_key_file)


def _acs_browse_internal(cmd, client, acs_info, resource_group, name, disable_browser, ssh_key_file):
    orchestrator_type = acs_info.orchestrator_profile.orchestrator_type  # pylint: disable=no-member

    if str(orchestrator_type).lower() == 'kubernetes' or \
       orchestrator_type == ContainerServiceOrchestratorTypes.kubernetes or \
       (acs_info.custom_profile and acs_info.custom_profile.orchestrator == 'kubernetes'):  # pylint: disable=no-member
        return k8s_browse(cmd, client, name, resource_group, disable_browser, ssh_key_file=ssh_key_file)
    elif str(orchestrator_type).lower() == 'dcos' or orchestrator_type == ContainerServiceOrchestratorTypes.dcos:
        return _dcos_browse_internal(acs_info, disable_browser, ssh_key_file)
    else:
        raise CLIError('Unsupported orchestrator type {} for browse'.format(orchestrator_type))


def k8s_browse(cmd, client, name, resource_group, disable_browser=False, ssh_key_file=None):
    """
    Launch a proxy and browse the Kubernetes web UI.
    :param disable_browser: If true, don't launch a web browser after estabilishing the proxy
    :type disable_browser: bool
    """
    acs_info = _get_acs_info(cmd.cli_ctx, name, resource_group)
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


def dcos_browse(cmd, client, name, resource_group, disable_browser=False, ssh_key_file=None):
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
    acs_info = _get_acs_info(cmd.cli_ctx, name, resource_group)
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


def acs_install_cli(cmd, client, resource_group, name, install_location=None, client_version=None):
    acs_info = _get_acs_info(cmd.cli_ctx, name, resource_group)
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
    if sys.version_info < (3, 4) or (in_cloud_console() and platform.system() == 'Windows'):
        try:
            return ssl.SSLContext(ssl.PROTOCOL_TLS)  # added in python 2.7.13 and 3.6
        except AttributeError:
            return ssl.SSLContext(ssl.PROTOCOL_TLSv1)

    return ssl.create_default_context()


def _urlretrieve(url, filename):
    req = urlopen(url, context=_ssl_context())
    with open(filename, "wb") as f:
        f.write(req.read())


def dcos_install_cli(cmd, install_location=None, client_version='1.8'):
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


def k8s_install_cli(cmd, client_version='latest', install_location=None):
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
    logger.warning('Please ensure that %s is in your search PATH, so the `%s` command can be found.',
                   os.path.dirname(install_location), os.path.basename(install_location))


def k8s_install_connector(cmd, client, name, resource_group_name, connector_name='aci-connector',
                          location=None, service_principal=None, client_secret=None,
                          chart_url=None, os_type='Linux', image_tag=None, aci_resource_group=None):
    _k8s_install_or_upgrade_connector("install", cmd, client, name, resource_group_name, connector_name,
                                      location, service_principal, client_secret, chart_url, os_type,
                                      image_tag, aci_resource_group)


def k8s_upgrade_connector(cmd, client, name, resource_group_name, connector_name='aci-connector',
                          location=None, service_principal=None, client_secret=None,
                          chart_url=None, os_type='Linux', image_tag=None, aci_resource_group=None):
    _k8s_install_or_upgrade_connector("upgrade", cmd, client, name, resource_group_name, connector_name,
                                      location, service_principal, client_secret, chart_url, os_type,
                                      image_tag, aci_resource_group)


def _k8s_install_or_upgrade_connector(helm_cmd, cmd, client, name, resource_group_name, connector_name,
                                      location, service_principal, client_secret, chart_url, os_type,
                                      image_tag, aci_resource_group):
    from subprocess import PIPE, Popen
    helm_not_installed = 'Helm not detected, please verify if it is installed.'
    url_chart = chart_url
    if image_tag is None:
        image_tag = 'latest'
    # Check if Helm is installed locally
    try:
        Popen(["helm"], stdout=PIPE, stderr=PIPE)
    except OSError:
        raise CLIError(helm_not_installed)
    # If SPN is specified, the secret should also be specified
    if service_principal is not None and client_secret is None:
        raise CLIError('--client-secret must be specified when --service-principal is specified')
    # Validate if the RG exists
    rg_location = _get_rg_location(cmd.cli_ctx, aci_resource_group or resource_group_name)
    # Auto assign the location
    if location is None:
        location = rg_location
    norm_location = location.replace(' ', '').lower()
    # Validate the location upon the ACI avaiable regions
    _validate_aci_location(norm_location)
    # Get the credentials from a AKS instance
    _, browse_path = tempfile.mkstemp()
    aks_get_credentials(cmd, client, resource_group_name, name, admin=False, path=browse_path)
    subscription_id = _get_subscription_id(cmd.cli_ctx)
    # Get the TenantID
    profile = Profile(cli_ctx=cmd.cli_ctx)
    _, _, tenant_id = profile.get_login_credentials()
    # Check if we want the linux connector
    if os_type.lower() in ['linux', 'both']:
        _helm_install_or_upgrade_aci_connector(helm_cmd, image_tag, url_chart, connector_name, service_principal,
                                               client_secret, subscription_id, tenant_id, aci_resource_group,
                                               norm_location, 'Linux')

    # Check if we want the windows connector
    if os_type.lower() in ['windows', 'both']:
        _helm_install_or_upgrade_aci_connector(helm_cmd, image_tag, url_chart, connector_name, service_principal,
                                               client_secret, subscription_id, tenant_id, aci_resource_group,
                                               norm_location, 'Windows')


def _helm_install_or_upgrade_aci_connector(helm_cmd, image_tag, url_chart, connector_name, service_principal,
                                           client_secret, subscription_id, tenant_id, aci_resource_group,
                                           norm_location, os_type):
    node_taint = 'azure.com/aci'
    helm_release_name = connector_name.lower() + '-' + os_type.lower() + '-' + norm_location
    node_name = 'virtual-kubelet-' + helm_release_name
    logger.warning("Deploying the ACI connector for '%s' using Helm", os_type)
    try:
        values = 'env.nodeName={},env.nodeTaint={},env.nodeOsType={},image.tag={}'.format(
            node_name, node_taint, os_type, image_tag)

        if service_principal:
            values += ",env.azureClientId=" + service_principal
        if client_secret:
            values += ",env.azureClientKey=" + client_secret
        if subscription_id:
            values += ",env.azureSubscriptionId=" + subscription_id
        if tenant_id:
            values += ",env.azureTenantId=" + tenant_id
        if aci_resource_group:
            values += ",env.aciResourceGroup=" + aci_resource_group
        if norm_location:
            values += ",env.aciRegion=" + norm_location

        if helm_cmd == "install":
            subprocess.call(["helm", "install", url_chart, "--name", helm_release_name, "--set", values])
        elif helm_cmd == "upgrade":
            subprocess.call(["helm", "upgrade", helm_release_name, url_chart, "--set", values])
    except subprocess.CalledProcessError as err:
        raise CLIError('Could not deploy the ACI connector Chart: {}'.format(err))


def k8s_uninstall_connector(cmd, client, name, resource_group_name, connector_name='aci-connector',
                            location=None, graceful=False, os_type='Linux'):
    from subprocess import PIPE, Popen
    helm_not_installed = "Error : Helm not detected, please verify if it is installed."
    # Check if Helm is installed locally
    try:
        Popen(["helm"], stdout=PIPE, stderr=PIPE)
    except OSError:
        raise CLIError(helm_not_installed)
    # Get the credentials from a AKS instance
    _, browse_path = tempfile.mkstemp()
    aks_get_credentials(cmd, client, resource_group_name, name, admin=False, path=browse_path)

    # Validate if the RG exists
    rg_location = _get_rg_location(cmd.cli_ctx, resource_group_name)
    # Auto assign the location
    if location is None:
        location = rg_location
    norm_location = location.replace(' ', '').lower()

    if os_type.lower() in ['linux', 'both']:
        helm_release_name = connector_name.lower() + '-linux-' + norm_location
        node_name = 'virtual-kubelet-' + helm_release_name
        _undeploy_connector(graceful, node_name, helm_release_name)

    if os_type.lower() in ['windows', 'both']:
        helm_release_name = connector_name.lower() + '-windows-' + norm_location
        node_name = 'virtual-kubelet-' + helm_release_name
        _undeploy_connector(graceful, node_name, helm_release_name)


def _undeploy_connector(graceful, node_name, helm_release_name):
    if graceful:
        logger.warning('Graceful option selected, will try to drain the node first')
        from subprocess import PIPE, Popen
        kubectl_not_installed = 'Kubectl not detected, please verify if it is installed.'
        try:
            Popen(["kubectl"], stdout=PIPE, stderr=PIPE)
        except OSError:
            raise CLIError(kubectl_not_installed)

        try:
            drain_node = subprocess.check_output(
                ['kubectl', 'drain', node_name, '--force', '--delete-local-data'],
                universal_newlines=True)

            if not drain_node:
                raise CLIError('Could not find the node, make sure you' +
                               ' are using the correct --os-type')
        except subprocess.CalledProcessError as err:
            raise CLIError('Could not find the node, make sure you are using the correct' +
                           ' --connector-name, --location and --os-type options: {}'.format(err))

    logger.warning("Undeploying the '%s' using Helm", helm_release_name)
    try:
        subprocess.call(['helm', 'del', helm_release_name, '--purge'])
    except subprocess.CalledProcessError as err:
        raise CLIError('Could not undeploy the ACI connector Chart: {}'.format(err))

    try:
        subprocess.check_output(
            ['kubectl', 'delete', 'node', node_name],
            universal_newlines=True)
    except subprocess.CalledProcessError as err:
        raise CLIError('Could not delete the node, make sure you are using the correct' +
                       ' --connector-name, --location and --os-type options: {}'.format(err))


def _build_service_principal(rbac_client, cli_ctx, name, url, client_secret):
    # use get_progress_controller
    hook = cli_ctx.get_progress_controller(True)
    hook.add(messsage='Creating service principal', value=0, total_val=1.0)
    logger.info('Creating service principal')
    # always create application with 5 years expiration
    start_date = datetime.datetime.utcnow()
    end_date = start_date + relativedelta(years=5)
    result = create_application(rbac_client.applications, name, url, [url], password=client_secret,
                                start_date=start_date, end_date=end_date)
    service_principal = result.app_id  # pylint: disable=no-member
    for x in range(0, 10):
        hook.add(message='Creating service principal', value=0.1 * x, total_val=1.0)
        try:
            create_service_principal(cli_ctx, service_principal, rbac_client=rbac_client)
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


def _add_role_assignment(cli_ctx, role, service_principal, delay=2):
    # AAD can have delays in propagating data, so sleep and retry
    hook = cli_ctx.get_progress_controller(True)
    hook.add(message='Waiting for AAD role to propagate', value=0, total_val=1.0)
    logger.info('Waiting for AAD role to propagate')
    for x in range(0, 10):
        hook.add(message='Waiting for AAD role to propagate', value=0.1 * x, total_val=1.0)
        try:
            # TODO: break this out into a shared utility library
            create_role_assignment(cli_ctx, role, service_principal)
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


def _get_subscription_id(cli_ctx):
    _, sub_id, _ = Profile(cli_ctx=cli_ctx).get_login_credentials(subscription_id=None)
    return sub_id


def _get_default_dns_prefix(name, resource_group_name, subscription_id):
    # Use subscription id to provide uniqueness and prevent DNS name clashes
    name_part = re.sub('[^A-Za-z0-9-]', '', name)[0:10]
    if not name_part[0].isalpha():
        name_part = (str('a') + name_part)[0:10]
    resource_group_part = re.sub('[^A-Za-z0-9-]', '', resource_group_name)[0:16]
    return '{}-{}-{}'.format(name_part, resource_group_part, subscription_id[0:6])


def list_acs_locations(cmd, client):
    return {
        "productionRegions": regions_in_prod,
        "previewRegions": regions_in_preview
    }


def _generate_windows_profile(windows, admin_username, admin_password):
    if windows:
        if not admin_password:
            raise CLIError('--admin-password is required.')
        if len(admin_password) < 6:
            raise CLIError('--admin-password must be at least 6 characters')
        windows_profile = {
            "adminUsername": admin_username,
            "adminPassword": admin_password,
        }
        return windows_profile
    return None


def _generate_master_pool_profile(api_version, master_profile, master_count, dns_name_prefix,
                                  master_vm_size, master_osdisk_size, master_vnet_subnet_id,
                                  master_first_consecutive_static_ip, master_storage_profile):
    master_pool_profile = {}
    default_master_pool_profile = {
        "count": int(master_count),
        "dnsPrefix": dns_name_prefix + 'mgmt',
    }
    if api_version == "2017-07-01":
        default_master_pool_profile = _update_dict(default_master_pool_profile, {
            "count": int(master_count),
            "dnsPrefix": dns_name_prefix + 'mgmt',
            "vmSize": master_vm_size,
            "osDiskSizeGB": int(master_osdisk_size),
            "vnetSubnetID": master_vnet_subnet_id,
            "firstConsecutiveStaticIP": master_first_consecutive_static_ip,
            "storageProfile": master_storage_profile,
        })
    if not master_profile:
        master_pool_profile = default_master_pool_profile
    else:
        master_pool_profile = _update_dict(default_master_pool_profile, master_profile)
    return master_pool_profile


def _generate_agent_pool_profiles(api_version, agent_profiles, agent_count, dns_name_prefix,
                                  agent_vm_size, os_type, agent_osdisk_size, agent_vnet_subnet_id,
                                  agent_ports, agent_storage_profile):
    agent_pool_profiles = []
    default_agent_pool_profile = {
        "count": int(agent_count),
        "vmSize": agent_vm_size,
        "osType": os_type,
        "dnsPrefix": dns_name_prefix + 'agent',
    }
    if api_version == "2017-07-01":
        default_agent_pool_profile = _update_dict(default_agent_pool_profile, {
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
        agent_pool_profiles.append(_update_dict(default_agent_pool_profile, {"name": "agentpool0"}))
    else:
        # override agentPoolProfiles by using the passed in agent_profiles
        for idx, ap in enumerate(agent_profiles):
            # if the user specified dnsPrefix, we honor that
            # otherwise, we use the idx to avoid duplicate dns name
            a = _update_dict({"dnsPrefix": dns_name_prefix + 'agent' + str(idx)}, ap)
            agent_pool_profiles.append(_update_dict(default_agent_pool_profile, a))
    return agent_pool_profiles


def _generate_outputs(name, orchestrator_type, admin_username):
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
    return outputs


def _generate_properties(api_version, orchestrator_type, orchestrator_version, master_pool_profile,
                         agent_pool_profiles, ssh_key_value, admin_username, windows_profile):
    properties = {
        "orchestratorProfile": {
            "orchestratorType": orchestrator_type,
        },
        "masterProfile": master_pool_profile,
        "agentPoolProfiles": agent_pool_profiles,
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
        properties["orchestratorProfile"]["orchestratorVersion"] = orchestrator_version

    if windows_profile is not None:
        properties["windowsProfile"] = windows_profile
    return properties


# pylint: disable=too-many-locals
def acs_create(cmd, client, resource_group_name, deployment_name, name, ssh_key_value, dns_name_prefix=None,
               location=None, admin_username="azureuser", api_version=None, master_profile=None,
               master_vm_size="Standard_D2_v2", master_osdisk_size=0, master_count=1, master_vnet_subnet_id="",
               master_first_consecutive_static_ip="10.240.255.5", master_storage_profile="",
               agent_profiles=None, agent_vm_size="Standard_D2_v2", agent_osdisk_size=0,
               agent_count=3, agent_vnet_subnet_id="", agent_ports=None, agent_storage_profile="",
               orchestrator_type="DCOS", orchestrator_version="", service_principal=None, client_secret=None, tags=None,
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

    subscription_id = _get_subscription_id(cmd.cli_ctx)
    if not dns_name_prefix:
        dns_name_prefix = _get_default_dns_prefix(name, resource_group_name, subscription_id)

    rg_location = _get_rg_location(cmd.cli_ctx, resource_group_name)
    if location is None:
        location = rg_location

    # if api-version is not specified, or specified in a version not supported
    # override based on location
    if api_version is None or api_version not in ["2017-01-31", "2017-07-01"]:
        if location in regions_in_preview:
            api_version = "2017-07-01"  # 2017-07-01 supported in the preview locations
        else:
            api_version = "2017-01-31"  # 2017-01-31 applied to other locations

    if orchestrator_type.lower() == 'kubernetes':
        principal_obj = _ensure_service_principal(cmd.cli_ctx, service_principal, client_secret, subscription_id,
                                                  dns_name_prefix, location, name)
        client_secret = principal_obj.get("client_secret")
        service_principal = principal_obj.get("service_principal")

    elif windows:
        raise CLIError('--windows is only supported for Kubernetes clusters')

    # set location if void
    if not location:
        location = '[resourceGroup().location]'

    # set os_type
    os_type = 'Linux'
    if windows:
        os_type = 'Windows'

    # set agent_ports if void
    if not agent_ports:
        agent_ports = []

    # get windows_profile
    windows_profile = _generate_windows_profile(windows, admin_username, admin_password)

    # The resources.properties fields should match with ContainerServices' api model
    master_pool_profile = _generate_master_pool_profile(api_version, master_profile, master_count, dns_name_prefix,
                                                        master_vm_size, master_osdisk_size, master_vnet_subnet_id,
                                                        master_first_consecutive_static_ip, master_storage_profile)

    agent_pool_profiles = _generate_agent_pool_profiles(api_version, agent_profiles, agent_count, dns_name_prefix,
                                                        agent_vm_size, os_type, agent_osdisk_size, agent_vnet_subnet_id,
                                                        agent_ports, agent_storage_profile)

    outputs = _generate_outputs(name, orchestrator_type, admin_username)

    properties = _generate_properties(api_version, orchestrator_type, orchestrator_version, master_pool_profile,
                                      agent_pool_profiles, ssh_key_value, admin_username, windows_profile)

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

    # Due to SPN replication latency, we do a few retries here
    max_retry = 30
    retry_exception = Exception(None)
    for _ in range(0, max_retry):
        try:
            return _invoke_deployment(cmd.cli_ctx, resource_group_name, deployment_name,
                                      template, params, validate, no_wait)
        except CloudError as ex:
            retry_exception = ex
            if 'is not valid according to the validation procedure' in ex.message or \
               'The credentials in ServicePrincipalProfile were invalid' in ex.message or \
               'not found in Active Directory tenant' in ex.message:
                time.sleep(3)
            else:
                raise ex
    raise retry_exception


def store_acs_service_principal(subscription_id, client_secret, service_principal,
                                file_name='acsServicePrincipal.json'):
    obj = {}
    if client_secret:
        obj['client_secret'] = client_secret
    if service_principal:
        obj['service_principal'] = service_principal

    config_path = os.path.join(get_config_dir(), file_name)
    full_config = load_service_principals(config_path=config_path)
    if not full_config:
        full_config = {}
    full_config[subscription_id] = obj

    with os.fdopen(os.open(config_path, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600),
                   'w+') as spFile:
        json.dump(full_config, spFile)


def load_acs_service_principal(subscription_id, file_name='acsServicePrincipal.json'):
    config_path = os.path.join(get_config_dir(), file_name)
    config = load_service_principals(config_path)
    if not config:
        return None
    return config.get(subscription_id)


def load_service_principals(config_path):
    if not os.path.exists(config_path):
        return None
    fd = os.open(config_path, os.O_RDONLY)
    try:
        with os.fdopen(fd) as f:
            return shell_safe_json_parse(f.read())
    except:  # pylint: disable=bare-except
        return None


def _invoke_deployment(cli_ctx, resource_group_name, deployment_name, template, parameters, validate, no_wait,
                       subscription_id=None):
    from azure.mgmt.resource.resources import ResourceManagementClient
    from azure.mgmt.resource.resources.models import DeploymentProperties

    properties = DeploymentProperties(template=template, parameters=parameters, mode='incremental')
    smc = get_mgmt_service_client(cli_ctx, ResourceManagementClient, subscription_id=subscription_id).deployments
    if validate:
        logger.info('==== BEGIN TEMPLATE ====')
        logger.info(json.dumps(template, indent=2))
        logger.info('==== END TEMPLATE ====')
        return smc.validate(resource_group_name, deployment_name, properties)
    return sdk_no_wait(no_wait, smc.create_or_update, resource_group_name, deployment_name, properties)


def k8s_get_credentials(cmd, client, name, resource_group_name,
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
    acs_info = _get_acs_info(cmd.cli_ctx, name, resource_group_name)
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


def load_kubernetes_configuration(filename):
    try:
        with open(filename) as stream:
            return yaml.safe_load(stream)
    except (IOError, OSError) as ex:
        if getattr(ex, 'errno', 0) == errno.ENOENT:
            raise CLIError('{} does not exist'.format(filename))
        else:
            raise
    except (yaml.parser.ParserError, UnicodeDecodeError) as ex:
        raise CLIError('Error parsing {} ({})'.format(filename, str(ex)))


def merge_kubernetes_configurations(existing_file, addition_file):
    existing = load_kubernetes_configuration(existing_file)
    addition = load_kubernetes_configuration(addition_file)

    # rename the admin context so it doesn't overwrite the user context
    for ctx in addition.get('contexts', []):
        try:
            if ctx['context']['user'].startswith('clusterAdmin'):
                admin_name = ctx['name'] + '-admin'
                addition['current-context'] = ctx['name'] = admin_name
                break
        except (KeyError, TypeError):
            continue

    if addition is None:
        raise CLIError('failed to load additional configuration from {}'.format(addition_file))

    if existing is None:
        existing = addition
    else:
        _handle_merge(existing, addition, 'clusters')
        _handle_merge(existing, addition, 'users')
        _handle_merge(existing, addition, 'contexts')
        existing['current-context'] = addition['current-context']

    # check that ~/.kube/config is only read- and writable by its owner
    if platform.system() != 'Windows':
        existing_file_perms = "{:o}".format(stat.S_IMODE(os.lstat(existing_file).st_mode))
        if not existing_file_perms.endswith('600'):
            logger.warning('%s has permissions "%s".\nIt should be readable and writable only by its owner.',
                           existing_file, existing_file_perms)

    with open(existing_file, 'w+') as stream:
        yaml.dump(existing, stream, default_flow_style=False)

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


def _get_acs_info(cli_ctx, name, resource_group_name):
    """
    Gets the ContainerService object from Azure REST API.

    :param name: ACS resource name
    :type name: String
    :param resource_group_name: Resource group name
    :type resource_group_name: String
    """
    container_services = cf_container_services(cli_ctx, None)
    return container_services.get(resource_group_name, name)


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


def update_acs(cmd, client, resource_group_name, container_service_name, new_agent_count):
    instance = client.get(resource_group_name, container_service_name)
    instance.agent_pool_profiles[0].count = new_agent_count  # pylint: disable=no-member

    # null out the service principal because otherwise validation complains
    if instance.orchestrator_profile.orchestrator_type == ContainerServiceOrchestratorTypes.kubernetes:
        instance.service_principal_profile = None

    # null out the windows profile so that validation doesn't complain about not having the admin password
    instance.windows_profile = None

    return client.create_or_update(resource_group_name, container_service_name, instance)


def list_container_services(cmd, client, resource_group_name=None):
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
    from azure.graphrbac.models import GraphErrorException
    password_creds, key_creds = _build_application_creds(password, key_value, key_type,
                                                         key_usage, start_date, end_date)

    app_create_param = ApplicationCreateParameters(available_to_other_tenants,
                                                   display_name,
                                                   identifier_uris,
                                                   homepage=homepage,
                                                   reply_urls=reply_urls,
                                                   key_credentials=key_creds,
                                                   password_credentials=password_creds)
    try:
        return client.create(app_create_param)
    except GraphErrorException as ex:
        if 'insufficient privileges' in str(ex).lower():
            link = 'https://docs.microsoft.com/en-us/azure/azure-resource-manager/resource-group-create-service-principal-portal'  # pylint: disable=line-too-long
            raise CLIError("Directory permission is needed for the current user to register the application. "
                           "For how to configure, please refer '{}'. Original error: {}".format(link, ex))
        raise


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
        password_creds = [PasswordCredential(start_date=start_date, end_date=end_date,
                                             key_id=str(uuid.uuid4()), value=password)]
    elif key_value:
        key_creds = [KeyCredential(start_date=start_date, end_date=end_date, value=key_value,
                                   key_id=str(uuid.uuid4()), usage=key_usage, type=key_type)]

    return (password_creds, key_creds)


def create_service_principal(cli_ctx, identifier, resolve_app=True, rbac_client=None):
    if rbac_client is None:
        rbac_client = get_graph_rbac_management_client(cli_ctx)

    if resolve_app:
        try:
            uuid.UUID(identifier)
            result = list(rbac_client.applications.list(filter="appId eq '{}'".format(identifier)))
        except ValueError:
            result = list(rbac_client.applications.list(
                filter="identifierUris/any(s:s eq '{}')".format(identifier)))

        if not result:  # assume we get an object id
            result = [rbac_client.applications.get(identifier)]
        app_id = result[0].app_id
    else:
        app_id = identifier

    return rbac_client.service_principals.create(ServicePrincipalCreateParameters(app_id, True))


def create_role_assignment(cli_ctx, role, assignee, resource_group_name=None, scope=None):
    return _create_role_assignment(cli_ctx, role, assignee, resource_group_name, scope)


def _create_role_assignment(cli_ctx, role, assignee, resource_group_name=None, scope=None, resolve_assignee=True):
    from azure.cli.core.profiles import ResourceType, get_sdk
    factory = get_auth_management_client(cli_ctx, scope)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions

    scope = _build_role_scope(resource_group_name, scope, assignments_client.config.subscription_id)

    role_id = _resolve_role_id(role, scope, definitions_client)
    object_id = _resolve_object_id(cli_ctx, assignee) if resolve_assignee else assignee
    RoleAssignmentCreateParameters = get_sdk(cli_ctx, ResourceType.MGMT_AUTHORIZATION,
                                             'RoleAssignmentCreateParameters', mod='models',
                                             operation_group='role_assignments')
    parameters = RoleAssignmentCreateParameters(role_definition_id=role_id, principal_id=object_id)
    assignment_name = uuid.uuid4()
    custom_headers = None
    return assignments_client.create(scope, assignment_name, parameters, custom_headers=custom_headers)


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


def _resolve_object_id(cli_ctx, assignee):
    client = get_graph_rbac_management_client(cli_ctx)
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


def aks_browse(cmd, client, resource_group_name, name, disable_browser=False, listen_port='8001'):
    if in_cloud_console():
        raise CLIError('This command requires a web browser, which is not supported in Azure Cloud Shell.')

    if not which('kubectl'):
        raise CLIError('Can not find kubectl executable in PATH')

    proxy_url = 'http://127.0.0.1:{0}/'.format(listen_port)
    _, browse_path = tempfile.mkstemp()
    # TODO: need to add an --admin option?
    aks_get_credentials(cmd, client, resource_group_name, name, admin=False, path=browse_path)
    # find the dashboard pod's name
    try:
        dashboard_pod = subprocess.check_output(
            ["kubectl", "get", "pods", "--kubeconfig", browse_path, "--namespace", "kube-system", "--output", "name",
             "--selector", "k8s-app=kubernetes-dashboard"],
            universal_newlines=True)
    except subprocess.CalledProcessError as err:
        raise CLIError('Could not find dashboard pod: {}'.format(err))
    if dashboard_pod:
        # remove any "pods/" or "pod/" prefix from the name
        dashboard_pod = str(dashboard_pod).split('/')[-1].strip()
    else:
        raise CLIError("Couldn't find the Kubernetes dashboard pod.")
    # launch kubectl port-forward locally to access the remote dashboard
    logger.warning('Proxy running on %s', proxy_url)
    logger.warning('Press CTRL+C to close the tunnel...')
    if not disable_browser:
        wait_then_open_async(proxy_url)
    try:
        subprocess.call(["kubectl", "--kubeconfig", browse_path, "--namespace", "kube-system",
                         "port-forward", dashboard_pod, "{0}:9090".format(listen_port)])
    except KeyboardInterrupt:
        # Let command processing finish gracefully after the user presses [Ctrl+C]
        return


def aks_create(cmd, client, resource_group_name, name, ssh_key_value,  # pylint: disable=too-many-locals
               dns_name_prefix=None,
               location=None,
               admin_username="azureuser",
               kubernetes_version='',
               node_vm_size="Standard_DS1_v2",
               node_osdisk_size=0,
               node_count=3,
               service_principal=None, client_secret=None,
               no_ssh_key=False,
               disable_rbac=None,
               enable_rbac=None,
               network_plugin=None,
               pod_cidr=None,
               service_cidr=None,
               dns_service_ip=None,
               docker_bridge_address=None,
               enable_addons=None,
               workspace_resource_id=None,
               vnet_subnet_id=None,
               max_pods=0,
               aad_client_app_id=None,
               aad_server_app_id=None,
               aad_server_app_secret=None,
               aad_tenant_id=None,
               tags=None,
               generate_ssh_keys=False,  # pylint: disable=unused-argument
               no_wait=False):
    if not no_ssh_key:
        try:
            if not ssh_key_value or not is_valid_ssh_rsa_public_key(ssh_key_value):
                raise ValueError()
        except (TypeError, ValueError):
            shortened_key = truncate_text(ssh_key_value)
            raise CLIError('Provided ssh key ({}) is invalid or non-existent'.format(shortened_key))

    subscription_id = _get_subscription_id(cmd.cli_ctx)
    if not dns_name_prefix:
        dns_name_prefix = _get_default_dns_prefix(name, resource_group_name, subscription_id)

    rg_location = _get_rg_location(cmd.cli_ctx, resource_group_name)
    if location is None:
        location = rg_location

    agent_pool_profile = ManagedClusterAgentPoolProfile(
        name='nodepool1',  # Must be 12 chars or less before ACS RP adds to it
        count=int(node_count),
        vm_size=node_vm_size,
        dns_prefix=dns_name_prefix,
        os_type="Linux",
        storage_profile=ContainerServiceStorageProfileTypes.managed_disks,
        vnet_subnet_id=vnet_subnet_id,
        max_pods=int(max_pods) if max_pods else None
    )
    if node_osdisk_size:
        agent_pool_profile.os_disk_size_gb = int(node_osdisk_size)

    linux_profile = None
    # LinuxProfile is just used for SSH access to VMs, so omit it if --no-ssh-key was specified.
    if not no_ssh_key:
        ssh_config = ContainerServiceSshConfiguration(
            public_keys=[ContainerServiceSshPublicKey(key_data=ssh_key_value)])
        linux_profile = ContainerServiceLinuxProfile(admin_username=admin_username, ssh=ssh_config)

    principal_obj = _ensure_aks_service_principal(cmd.cli_ctx,
                                                  service_principal=service_principal, client_secret=client_secret,
                                                  subscription_id=subscription_id, dns_name_prefix=dns_name_prefix,
                                                  location=location, name=name)
    service_principal_profile = ContainerServiceServicePrincipalProfile(
        client_id=principal_obj.get("service_principal"),
        secret=principal_obj.get("client_secret"),
        key_vault_secret_ref=None)

    network_profile = None
    if any([network_plugin, pod_cidr, service_cidr, dns_service_ip, docker_bridge_address]):
        network_profile = ContainerServiceNetworkProfile(
            network_plugin=network_plugin,
            pod_cidr=pod_cidr,
            service_cidr=service_cidr,
            dns_service_ip=dns_service_ip,
            docker_bridge_cidr=docker_bridge_address
        )

    addon_profiles = _handle_addons_args(
        cmd,
        enable_addons,
        subscription_id,
        resource_group_name,
        {},
        workspace_resource_id
    )
    if 'omsagent' in addon_profiles:
        _ensure_container_insights_for_monitoring(cmd, addon_profiles['omsagent'])

    aad_profile = None
    if any([aad_client_app_id, aad_server_app_id, aad_server_app_secret, aad_tenant_id]):
        aad_profile = ManagedClusterAADProfile(
            client_app_id=aad_client_app_id,
            server_app_id=aad_server_app_id,
            server_app_secret=aad_server_app_secret,
            tenant_id=aad_tenant_id
        )

    # Check that both --disable-rbac and --enable-rbac weren't provided
    if all([disable_rbac, enable_rbac]):
        raise CLIError('specify either "--disable-rbac" or "--enable-rbac", not both.')

    mc = ManagedCluster(
        location=location, tags=tags,
        dns_prefix=dns_name_prefix,
        kubernetes_version=kubernetes_version,
        enable_rbac=False if disable_rbac else True,
        agent_pool_profiles=[agent_pool_profile],
        linux_profile=linux_profile,
        service_principal_profile=service_principal_profile,
        network_profile=network_profile,
        addon_profiles=addon_profiles,
        aad_profile=aad_profile)

    # Due to SPN replication latency, we do a few retries here
    max_retry = 30
    retry_exception = Exception(None)
    for _ in range(0, max_retry):
        try:
            return sdk_no_wait(no_wait, client.create_or_update,
                               resource_group_name=resource_group_name, resource_name=name, parameters=mc)
        except CloudError as ex:
            retry_exception = ex
            if 'not found in Active Directory tenant' in ex.message:
                time.sleep(3)
            else:
                raise ex
    raise retry_exception


def aks_disable_addons(cmd, client, resource_group_name, name, addons, no_wait=False):
    instance = client.get(resource_group_name, name)
    subscription_id = _get_subscription_id(cmd.cli_ctx)

    instance = _update_addons(
        cmd,
        instance,
        subscription_id,
        resource_group_name,
        addons,
        enable=False,
        no_wait=no_wait
    )

    # send the managed cluster representation to update the addon profiles
    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, name, instance)


def aks_enable_addons(cmd, client, resource_group_name, name, addons, workspace_resource_id=None, no_wait=False):
    instance = client.get(resource_group_name, name)
    subscription_id = _get_subscription_id(cmd.cli_ctx)

    instance = _update_addons(cmd, instance, subscription_id, resource_group_name, addons, enable=True,
                              workspace_resource_id=workspace_resource_id, no_wait=no_wait)

    if 'omsagent' in instance.addon_profiles:
        _ensure_container_insights_for_monitoring(cmd, instance.addon_profiles['omsagent'])

    # send the managed cluster representation to update the addon profiles
    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, name, instance)


def aks_get_versions(cmd, client, location):
    return client.list_orchestrators(location, resource_type='managedClusters')


def aks_get_credentials(cmd, client, resource_group_name, name, admin=False,
                        path=os.path.join(os.path.expanduser('~'), '.kube', 'config')):
    access_profile = client.get_access_profile(
        resource_group_name, name, "clusterAdmin" if admin else "clusterUser")

    if not access_profile:
        raise CLIError("No Kubernetes access profile found.")
    else:
        kubeconfig = access_profile.kube_config.decode(encoding='UTF-8')
        _print_or_merge_credentials(path, kubeconfig)


ADDONS = {
    'http_application_routing': 'httpApplicationRouting',
    'monitoring': 'omsagent'
}


def aks_list(cmd, client, resource_group_name=None):
    if resource_group_name:
        managed_clusters = client.list_by_resource_group(resource_group_name)
    else:
        managed_clusters = client.list()
    return _remove_nulls(list(managed_clusters))


def aks_show(cmd, client, resource_group_name, name):
    mc = client.get(resource_group_name, name)
    return _remove_nulls([mc])[0]


def aks_scale(cmd, client, resource_group_name, name, node_count, no_wait=False):
    instance = client.get(resource_group_name, name)
    # TODO: change this approach when we support multiple agent pools.
    instance.agent_pool_profiles[0].count = int(node_count)  # pylint: disable=no-member

    # null out the SP and AAD profile because otherwise validation complains
    instance.service_principal_profile = None
    instance.aad_profile = None

    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, name, instance)


def aks_upgrade(cmd, client, resource_group_name, name, kubernetes_version, no_wait=False, **kwargs):  # pylint: disable=unused-argument
    instance = client.get(resource_group_name, name)
    instance.kubernetes_version = kubernetes_version

    # null out the SP and AAD profile because otherwise validation complains
    instance.service_principal_profile = None
    instance.aad_profile = None

    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, name, instance)


DEV_SPACES_EXTENSION_NAME = 'dev-spaces-preview'
DEV_SPACES_EXTENSION_MODULE = 'azext_dev_spaces_preview.custom'


def aks_use_dev_spaces(cmd, client, name, resource_group_name, update=False, space_name=None, prompt=False):
    """
    Use Azure Dev Spaces with a managed Kubernetes cluster.

    :param name: Name of the managed cluster.
    :type name: String
    :param resource_group_name: Name of resource group. You can configure the default group. \
    Using 'az configure --defaults group=<name>'.
    :type resource_group_name: String
    :param update: Update to the latest Azure Dev Spaces client components.
    :type update: bool
    :param space_name: Name of the new or existing dev space to select. Defaults to an interactive selection experience.
    :type space_name: String
    :param prompt: Do not prompt for confirmation. Requires --space.
    :type prompt: bool
    """

    if _get_or_add_extension(DEV_SPACES_EXTENSION_NAME, DEV_SPACES_EXTENSION_MODULE, update):
        azext_custom = _get_azext_module(DEV_SPACES_EXTENSION_NAME, DEV_SPACES_EXTENSION_MODULE)
        try:
            azext_custom.ads_use_dev_spaces(name, resource_group_name, update, space_name, prompt)
        except TypeError:
            raise CLIError("Use '--update' option to get the latest Azure Dev Spaces client components.")
        except AttributeError as ae:
            raise CLIError(ae)


def aks_remove_dev_spaces(cmd, client, name, resource_group_name, prompt=False):
    """
    Remove Azure Dev Spaces from a managed Kubernetes cluster.

    :param name: Name of the managed cluster.
    :type name: String
    :param resource_group_name: Name of resource group. You can configure the default group. \
    Using 'az configure --defaults group=<name>'.
    :type resource_group_name: String
    :param prompt: Do not prompt for confirmation.
    :type prompt: bool
    """

    if _get_or_add_extension(DEV_SPACES_EXTENSION_NAME, DEV_SPACES_EXTENSION_MODULE):
        azext_custom = _get_azext_module(DEV_SPACES_EXTENSION_NAME, DEV_SPACES_EXTENSION_MODULE)
        try:
            azext_custom.ads_remove_dev_spaces(name, resource_group_name, prompt)
        except AttributeError as ae:
            raise CLIError(ae)


def _update_addons(cmd, instance, subscription_id, resource_group_name, addons, enable, workspace_resource_id=None,
                   no_wait=False):
    # parse the comma-separated addons argument
    addon_args = addons.split(',')

    addon_profiles = instance.addon_profiles or {}

    # for each addons argument
    for addon_arg in addon_args:
        addon = ADDONS[addon_arg]
        if enable:
            # add new addons or update existing ones and enable them
            addon_profile = addon_profiles.get(addon, ManagedClusterAddonProfile(enabled=False))
            # special config handling for certain addons
            if addon == 'omsagent':
                if addon_profile.enabled:
                    raise CLIError('The monitoring addon is already enabled for this managed cluster.\n'
                                   'To change monitoring configuration, run "az aks disable-addons -a monitoring"'
                                   'before enabling it again.')
                if not workspace_resource_id:
                    workspace_resource_id = _ensure_default_log_analytics_workspace_for_monitoring(
                        cmd,
                        subscription_id,
                        resource_group_name)
                workspace_resource_id = workspace_resource_id.strip()
                if not workspace_resource_id.startswith('/'):
                    workspace_resource_id = '/' + workspace_resource_id
                if workspace_resource_id.endswith('/'):
                    workspace_resource_id = workspace_resource_id.rstrip('/')
                addon_profile.config = {'logAnalyticsWorkspaceResourceID': workspace_resource_id}
            addon_profiles[addon] = addon_profile
        else:
            if addon not in addon_profiles:
                raise CLIError("The addon {} is not installed.".format(addon))
            addon_profiles[addon].config = None
        addon_profiles[addon].enabled = enable

    instance.addon_profiles = addon_profiles

    # null out the SP and AAD profile because otherwise validation complains
    instance.service_principal_profile = None
    instance.aad_profile = None

    return instance


def _get_azext_module(extension_name, module_name):
    try:
        # Adding the installed extension in the path
        from azure.cli.core.extension import get_extension_path
        ext_dir = get_extension_path(extension_name)
        sys.path.append(ext_dir)
        # Import the extension module
        from importlib import import_module
        azext_custom = import_module(module_name)
        return azext_custom
    except ImportError as ie:
        raise CLIError(ie)


def _handle_addons_args(cmd, addons_str, subscription_id, resource_group_name, addon_profiles=None,
                        workspace_resource_id=None):
    if not addon_profiles:
        addon_profiles = {}
    addons = addons_str.split(',') if addons_str else []
    if 'http_application_routing' in addons:
        addon_profiles['httpApplicationRouting'] = ManagedClusterAddonProfile(enabled=True)
        addons.remove('http_application_routing')
    # TODO: can we help the user find a workspace resource ID?
    if 'monitoring' in addons:
        if not workspace_resource_id:
            # use default workspace if exists else create default workspace
            workspace_resource_id = _ensure_default_log_analytics_workspace_for_monitoring(
                cmd, subscription_id, resource_group_name)

        workspace_resource_id = workspace_resource_id.strip()
        if not workspace_resource_id.startswith('/'):
            workspace_resource_id = '/' + workspace_resource_id
        if workspace_resource_id.endswith('/'):
            workspace_resource_id = workspace_resource_id.rstrip('/')
        addon_profiles['omsagent'] = ManagedClusterAddonProfile(
            enabled=True, config={'logAnalyticsWorkspaceResourceID': workspace_resource_id})
        addons.remove('monitoring')
    # error out if '--enable-addons=monitoring' isn't set but workspace_resource_id is
    elif workspace_resource_id:
        raise CLIError('"--workspace-resource-id" requires "--enable-addons monitoring".')
    # error out if any (unrecognized) addons remain
    if addons:
        raise CLIError('"{}" {} not recognized by the --enable-addons argument.'.format(
            ",".join(addons), "are" if len(addons) > 1 else "is"))
    return addon_profiles


def _install_dev_spaces_extension(extension_name):
    try:
        from azure.cli.command_modules.extension import custom
        custom.add_extension(extension_name=extension_name)
    except Exception:  # nopa pylint: disable=broad-except
        return False
    return True


def _update_dev_spaces_extension(extension_name, extension_module):
    from azure.cli.core.extension import ExtensionNotInstalledException
    try:
        from azure.cli.command_modules.extension import custom
        custom.update_extension(extension_name=extension_name)

        # reloading the imported module to update
        try:
            from importlib import reload
        except ImportError:
            pass  # for python 2
        reload(sys.modules[extension_module])
    except CLIError as err:
        logger.info(err)
    except ExtensionNotInstalledException as err:
        logger.debug(err)
        return False
    except ModuleNotFoundError as err:
        logger.debug(err)
        logger.error("Error occurred attempting to load the extension module. Use --debug for more information.")
        return False
    return True


def _get_or_add_extension(extension_name, extension_module, update=False):
    from azure.cli.core.extension import (ExtensionNotInstalledException, get_extension)
    try:
        get_extension(extension_name)
        if update:
            return _update_dev_spaces_extension(extension_name, extension_module)
    except ExtensionNotInstalledException:
        return _install_dev_spaces_extension(extension_name)
    return True


def _ensure_default_log_analytics_workspace_for_monitoring(cmd, subscription_id, resource_group_name):
    # log analytics workspaces cannot be created in WCUS region due to capacity limits
    # so mapped to EUS per discussion with log analytics team
    AzureLocationToOmsRegionCodeMap = {
        "eastus": "EUS",
        "westeurope": "WEU",
        "southeastasia": "SEA",
        "australiasoutheast": "ASE",
        "usgovvirginia": "USGV",
        "westcentralus": "EUS",
        "japaneast": "EJP",
        "uksouth": "SUK",
        "canadacentral": "CCA",
        "centralindia": "CIN",
        "eastus2euap": "EAP"
    }
    AzureRegionToOmsRegionMap = {
        "australiaeast": "australiasoutheast",
        "australiasoutheast": "australiasoutheast",
        "brazilsouth": "eastus",
        "canadacentral": "canadacentral",
        "canadaeast": "canadacentral",
        "centralus": "eastus",
        "eastasia": "southeastasia",
        "eastus": "eastus",
        "eastus2": "eastus",
        "japaneast": "japaneast",
        "japanwest": "japaneast",
        "northcentralus": "eastus",
        "northeurope": "westeurope",
        "southcentralus": "eastus",
        "southeastasia": "southeastasia",
        "uksouth": "uksouth",
        "ukwest": "uksouth",
        "westcentralus": "eastus",
        "westeurope": "westeurope",
        "westus": "eastus",
        "westus2": "eastus",
        "centralindia": "centralindia",
        "southindia": "centralindia",
        "westindia": "centralindia",
        "koreacentral": "southeastasia",
        "koreasouth": "southeastasia",
        "francecentral": "westeurope",
        "francesouth": "westeurope"
    }

    rg_location = _get_rg_location(cmd.cli_ctx, resource_group_name)
    default_region_name = "eastus"
    default_region_code = "EUS"

    workspace_region = AzureRegionToOmsRegionMap[
        rg_location] if AzureRegionToOmsRegionMap[rg_location] else default_region_name
    workspace_region_code = AzureLocationToOmsRegionCodeMap[
        workspace_region] if AzureLocationToOmsRegionCodeMap[workspace_region] else default_region_code

    default_workspace_resource_group = 'DefaultResourceGroup-' + workspace_region_code
    default_workspace_name = 'DefaultWorkspace-{0}-{1}'.format(subscription_id, workspace_region_code)

    default_workspace_resource_id = '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.OperationalInsights' \
        '/workspaces/{2}'.format(subscription_id, default_workspace_resource_group, default_workspace_name)
    resource_groups = cf_resource_groups(cmd.cli_ctx, subscription_id)
    resources = cf_resources(cmd.cli_ctx, subscription_id)

    # check if default RG exists
    if resource_groups.check_existence(default_workspace_resource_group):
        try:
            resource = resources.get_by_id(default_workspace_resource_id, '2015-11-01-preview')
            return resource.id
        except CloudError as ex:
            if ex.status_code != 404:
                raise ex
    else:
        resource_groups.create_or_update(default_workspace_resource_group, {'location': workspace_region})

    default_workspace_params = {
        'location': workspace_region,
        'properties': {
            'sku': {
                'name': 'standalone'
            }
        }
    }
    async_poller = resources.create_or_update_by_id(default_workspace_resource_id, '2015-11-01-preview',
                                                    default_workspace_params)

    ws_resource_id = ''
    while True:
        result = async_poller.result(15)
        if async_poller.done():
            ws_resource_id = result.id
            break

    return ws_resource_id


def _ensure_container_insights_for_monitoring(cmd, addon):
    workspace_resource_id = addon.config['logAnalyticsWorkspaceResourceID']

    workspace_resource_id = workspace_resource_id.strip()

    if not workspace_resource_id.startswith('/'):
        workspace_resource_id = '/' + workspace_resource_id

    if workspace_resource_id.endswith('/'):
        workspace_resource_id = workspace_resource_id.rstrip('/')

    # extract subscription ID and resource group from workspace_resource_id URL
    try:
        subscription_id = workspace_resource_id.split('/')[2]
        resource_group = workspace_resource_id.split('/')[4]
    except IndexError:
        raise CLIError('Could not locate resource group in workspace-resource-id URL.')

    # region of workspace can be different from region of RG so find the location of the workspace_resource_id
    resources = cf_resources(cmd.cli_ctx, subscription_id)
    try:
        resource = resources.get_by_id(workspace_resource_id, '2015-11-01-preview')
        location = resource.location
    except CloudError as ex:
        raise ex

    unix_time_in_millis = int(
        (datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(0)).total_seconds() * 1000.0)

    solution_deployment_name = 'ContainerInsights-{}'.format(unix_time_in_millis)

    # pylint: disable=line-too-long
    template = {
        "$schema": "https://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {
            "workspaceResourceId": {
                "type": "string",
                "metadata": {
                    "description": "Azure Monitor Log Analytics Resource ID"
                }
            },
            "workspaceRegion": {
                "type": "string",
                "metadata": {
                    "description": "Azure Monitor Log Analytics workspace region"
                }
            },
            "solutionDeploymentName": {
                "type": "string",
                "metadata": {
                    "description": "Name of the solution deployment"
                }
            }
        },
        "resources": [
            {
                "type": "Microsoft.Resources/deployments",
                "name": "[parameters('solutionDeploymentName')]",
                "apiVersion": "2017-05-10",
                "subscriptionId": "[split(parameters('workspaceResourceId'),'/')[2]]",
                "resourceGroup": "[split(parameters('workspaceResourceId'),'/')[4]]",
                "properties": {
                    "mode": "Incremental",
                    "template": {
                        "$schema": "https://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#",
                        "contentVersion": "1.0.0.0",
                        "parameters": {},
                        "variables": {},
                        "resources": [
                            {
                                "apiVersion": "2015-11-01-preview",
                                "type": "Microsoft.OperationsManagement/solutions",
                                "location": "[parameters('workspaceRegion')]",
                                "name": "[Concat('ContainerInsights', '(', split(parameters('workspaceResourceId'),'/')[8], ')')]",
                                "properties": {
                                    "workspaceResourceId": "[parameters('workspaceResourceId')]"
                                },
                                "plan": {
                                    "name": "[Concat('ContainerInsights', '(', split(parameters('workspaceResourceId'),'/')[8], ')')]",
                                    "product": "[Concat('OMSGallery/', 'ContainerInsights')]",
                                    "promotionCode": "",
                                    "publisher": "Microsoft"
                                }
                            }
                        ]
                    },
                    "parameters": {}
                }
            }
        ]
    }

    params = {
        "workspaceResourceId": {
            "value": workspace_resource_id
        },
        "workspaceRegion": {
            "value": location
        },
        "solutionDeploymentName": {
            "value": solution_deployment_name
        }
    }

    deployment_name = 'aks-monitoring-{}'.format(unix_time_in_millis)
    # publish the Container Insights solution to the Log Analytics workspace
    return _invoke_deployment(cmd.cli_ctx, resource_group, deployment_name, template, params,
                              validate=False, no_wait=False, subscription_id=subscription_id)


def _ensure_aks_service_principal(cli_ctx,
                                  service_principal=None,
                                  client_secret=None,
                                  subscription_id=None,
                                  dns_name_prefix=None,
                                  location=None,
                                  name=None):
    file_name_aks = 'aksServicePrincipal.json'
    # TODO: This really needs to be unit tested.
    rbac_client = get_graph_rbac_management_client(cli_ctx)
    if not service_principal:
        # --service-principal not specified, try to load it from local disk
        principal_obj = load_acs_service_principal(subscription_id, file_name=file_name_aks)
        if principal_obj:
            service_principal = principal_obj.get('service_principal')
            client_secret = principal_obj.get('client_secret')
        else:
            # Nothing to load, make one.
            if not client_secret:
                client_secret = binascii.b2a_hex(os.urandom(10)).decode('utf-8')
            salt = binascii.b2a_hex(os.urandom(3)).decode('utf-8')
            url = 'http://{}.{}.{}.cloudapp.azure.com'.format(salt, dns_name_prefix, location)

            service_principal = _build_service_principal(rbac_client, cli_ctx, name, url, client_secret)
            if not service_principal:
                raise CLIError('Could not create a service principal with the right permissions. '
                               'Are you an Owner on this project?')
            logger.info('Created a service principal: %s', service_principal)
            # We don't need to add role assignment for this created SPN
    else:
        # --service-principal specfied, validate --client-secret was too
        if not client_secret:
            raise CLIError('--client-secret is required if --service-principal is specified')
    store_acs_service_principal(subscription_id, client_secret, service_principal, file_name=file_name_aks)
    return load_acs_service_principal(subscription_id, file_name=file_name_aks)


def _ensure_service_principal(cli_ctx,
                              service_principal=None,
                              client_secret=None,
                              subscription_id=None,
                              dns_name_prefix=None,
                              location=None,
                              name=None):
    # TODO: This really needs to be unit tested.
    rbac_client = get_graph_rbac_management_client(cli_ctx)
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

            service_principal = _build_service_principal(rbac_client, cli_ctx, name, url, client_secret)
            if not service_principal:
                raise CLIError('Could not create a service principal with the right permissions. '
                               'Are you an Owner on this project?')
            logger.info('Created a service principal: %s', service_principal)
            # add role first before save it
            if not _add_role_assignment(cli_ctx, 'Contributor', service_principal):
                logger.warning('Could not create a service principal with the right permissions. '
                               'Are you an Owner on this project?')
    else:
        # --service-principal specfied, validate --client-secret was too
        if not client_secret:
            raise CLIError('--client-secret is required if --service-principal is specified')
    store_acs_service_principal(subscription_id, client_secret, service_principal)
    return load_acs_service_principal(subscription_id)


def _get_rg_location(ctx, resource_group_name, subscription_id=None):
    groups = cf_resource_groups(ctx, subscription_id=subscription_id)
    # Just do the get, we don't need the result, it will error out if the group doesn't exist.
    rg = groups.get(resource_group_name)
    return rg.location


def _print_or_merge_credentials(path, kubeconfig):
    """Merge an unencrypted kubeconfig into the file at the specified path, or print it to
    stdout if the path is "-".
    """
    # Special case for printing to stdout
    if path == "-":
        print(kubeconfig)
        return

    # ensure that at least an empty ~/.kube/config exists
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except OSError as ex:
            if ex.errno != errno.EEXIST:
                raise
    if not os.path.exists(path):
        with os.fdopen(os.open(path, os.O_CREAT | os.O_WRONLY, 0o600), 'wt'):
            pass

    # merge the new kubeconfig into the existing one
    fd, temp_path = tempfile.mkstemp()
    additional_file = os.fdopen(fd, 'w+t')
    try:
        additional_file.write(kubeconfig)
        additional_file.flush()
        merge_kubernetes_configurations(path, temp_path)
    except yaml.YAMLError as ex:
        logger.warning('Failed to merge credentials to kube config file: %s', ex)
    finally:
        additional_file.close()
        os.remove(temp_path)


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
        for ap_profile in managed_cluster.agent_pool_profiles:
            for attr in ap_attrs:
                if getattr(ap_profile, attr, None) is None:
                    delattr(ap_profile, attr)
        for attr in sp_attrs:
            if getattr(managed_cluster.service_principal_profile, attr, None) is None:
                delattr(managed_cluster.service_principal_profile, attr)
    return managed_clusters


def _validate_aci_location(norm_location):
    """
    Validate the Azure Container Instance location
    """
    aci_locations = [
        "westus",
        "eastus",
        "westeurope",
        "southeastasia",
        "westus2",
        "northeurope"
    ]
    if norm_location not in aci_locations:
        raise CLIError('Azure Container Instance is not available at location "{}".'.format(norm_location) +
                       ' The available locations are "{}"'.format(','.join(aci_locations)))
