# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import colorama
import base64
import binascii
import datetime
import errno
import io
import json
import os
import os.path
import platform
import random
import re
import shutil
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
import zipfile
from distutils.version import StrictVersion
from math import isnan
from urllib.request import urlopen
from urllib.error import URLError

# pylint: disable=import-error
import yaml
import dateutil.parser
from dateutil.relativedelta import relativedelta
from knack.log import get_logger
from knack.util import CLIError
from knack.prompting import NoTTYException, prompt_y_n
from msrestazure.azure_exceptions import CloudError
import requests

# pylint: disable=no-name-in-module,import-error
from azure.cli.command_modules.acs import acs_client, proxy
from azure.cli.command_modules.acs._params import regions_in_preview, regions_in_prod
from azure.cli.core.api import get_config_dir
from azure.cli.core.azclierror import (ResourceNotFoundError,
                                       ClientRequestError,
                                       ArgumentUsageError,
                                       InvalidArgumentValueError,
                                       MutuallyExclusiveArgumentError,
                                       ValidationError,
                                       UnauthorizedError,
                                       AzureInternalError,
                                       FileOperationError)
from azure.cli.core._profile import Profile
from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands.client_factory import get_mgmt_service_client, get_subscription_id
from azure.cli.core.keys import is_valid_ssh_rsa_public_key
from azure.cli.core.util import in_cloud_console, shell_safe_json_parse, truncate_text, sdk_no_wait
from azure.cli.core.commands import LongRunningOperation
from azure.graphrbac.models import (ApplicationCreateParameters,
                                    ApplicationUpdateParameters,
                                    PasswordCredential,
                                    KeyCredential,
                                    ServicePrincipalCreateParameters,
                                    GetObjectsParameters,
                                    ResourceAccess, RequiredResourceAccess)

from azure.mgmt.containerservice.models import ContainerServiceOrchestratorTypes

from ._client_factory import cf_container_services
from ._client_factory import cf_resource_groups
from ._client_factory import get_auth_management_client
from ._client_factory import get_graph_rbac_management_client
from ._client_factory import cf_resources
from ._client_factory import get_resource_by_name
from ._client_factory import cf_container_registry_service
from ._client_factory import cf_agent_pools
from ._client_factory import cf_snapshots_client
from ._client_factory import get_msi_client

from ._consts import CONST_SCALE_SET_PRIORITY_REGULAR, CONST_SCALE_SET_PRIORITY_SPOT, CONST_SPOT_EVICTION_POLICY_DELETE
from ._consts import CONST_SCALE_DOWN_MODE_DELETE
from ._consts import CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME
from ._consts import CONST_MONITORING_ADDON_NAME
from ._consts import CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID
from ._consts import CONST_VIRTUAL_NODE_ADDON_NAME
from ._consts import CONST_VIRTUAL_NODE_SUBNET_NAME
from ._consts import CONST_KUBE_DASHBOARD_ADDON_NAME
from ._consts import CONST_AZURE_POLICY_ADDON_NAME
from ._consts import CONST_INGRESS_APPGW_ADDON_NAME
from ._consts import CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID, CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME
from ._consts import CONST_INGRESS_APPGW_SUBNET_CIDR, CONST_INGRESS_APPGW_SUBNET_ID
from ._consts import CONST_INGRESS_APPGW_WATCH_NAMESPACE
from ._consts import CONST_CONFCOM_ADDON_NAME, CONST_ACC_SGX_QUOTE_HELPER_ENABLED
from ._consts import CONST_OPEN_SERVICE_MESH_ADDON_NAME
from ._consts import (CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME,
                      CONST_SECRET_ROTATION_ENABLED,
                      CONST_ROTATION_POLL_INTERVAL)
from ._consts import ADDONS
from ._consts import CONST_CANIPULL_IMAGE
from ._consts import CONST_MANAGED_IDENTITY_OPERATOR_ROLE, CONST_MANAGED_IDENTITY_OPERATOR_ROLE_ID
from ._consts import DecoratorEarlyExitException
from .addonconfiguration import (
    add_monitoring_role_assignment,
    add_ingress_appgw_addon_role_assignment,
    add_virtual_node_role_assignment,
    ensure_default_log_analytics_workspace_for_monitoring,
    ensure_container_insights_for_monitoring,
)
from ._resourcegroup import get_rg_location
from ._validators import extract_comma_separated_string

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


def get_cmd_test_hook_data(filename):
    hook_data = None
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    test_hook_file_path = os.path.join(curr_dir, 'tests/latest/data', filename)
    if os.path.exists(test_hook_file_path):
        with open(test_hook_file_path, "r") as f:
            hook_data = json.load(f)
    return hook_data


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


def acs_browse(cmd, client, resource_group_name, name, disable_browser=False, ssh_key_file=None):
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
    acs_info = _get_acs_info(cmd.cli_ctx, name, resource_group_name)
    _acs_browse_internal(
        cmd, client, acs_info, resource_group_name, name, disable_browser, ssh_key_file)


def _acs_browse_internal(cmd, client, acs_info, resource_group_name, name, disable_browser, ssh_key_file):
    orchestrator_type = acs_info.orchestrator_profile.orchestrator_type  # pylint: disable=no-member

    if str(orchestrator_type).lower() == 'kubernetes' or \
       orchestrator_type == ContainerServiceOrchestratorTypes.kubernetes or \
       (acs_info.custom_profile and acs_info.custom_profile.orchestrator == 'kubernetes'):  # pylint: disable=no-member
        return k8s_browse(cmd, client, name, resource_group_name, disable_browser, ssh_key_file=ssh_key_file)
    if str(orchestrator_type).lower() == 'dcos' or orchestrator_type == ContainerServiceOrchestratorTypes.dcos:
        return _dcos_browse_internal(acs_info, disable_browser, ssh_key_file)
    raise CLIError(
        'Unsupported orchestrator type {} for browse'.format(orchestrator_type))


def k8s_browse(cmd, client, name, resource_group_name, disable_browser=False, ssh_key_file=None):
    """
    Launch a proxy and browse the Kubernetes web UI.
    :param disable_browser: If true, don't launch a web browser after estabilishing the proxy
    :type disable_browser: bool
    """
    acs_info = _get_acs_info(cmd.cli_ctx, name, resource_group_name)
    _k8s_browse_internal(name, acs_info, disable_browser, ssh_key_file)


def _k8s_browse_internal(name, acs_info, disable_browser, ssh_key_file):
    if not which('kubectl'):
        raise CLIError('Can not find kubectl executable in PATH')
    browse_path = os.path.join(get_config_dir(), 'acsBrowseConfig.yaml')
    if os.path.exists(browse_path):
        os.remove(browse_path)

    _k8s_get_credentials_internal(
        name, acs_info, browse_path, ssh_key_file, False)

    logger.warning('Proxy running on 127.0.0.1:8001/ui')
    logger.warning('Press CTRL+C to close the tunnel...')
    if not disable_browser:
        wait_then_open_async('http://127.0.0.1:8001/ui')
    subprocess.call(["kubectl", "--kubeconfig", browse_path, "proxy"])


def dcos_browse(cmd, client, name, resource_group_name, disable_browser=False, ssh_key_file=None):
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
    acs_info = _get_acs_info(cmd.cli_ctx, name, resource_group_name)
    _dcos_browse_internal(acs_info, disable_browser, ssh_key_file)


def _dcos_browse_internal(acs_info, disable_browser, ssh_key_file):
    if not os.path.isfile(ssh_key_file):
        raise CLIError(
            'Private key file {} does not exist'.format(ssh_key_file))

    acs = acs_client.ACSClient()
    if not acs.connect(_get_host_name(acs_info), _get_username(acs_info),
                       key_filename=ssh_key_file):
        raise CLIError('Error connecting to ACS: {}'.format(
            _get_host_name(acs_info)))

    octarine_bin = '/opt/mesosphere/bin/octarine'
    if not acs.file_exists(octarine_bin):
        raise CLIError(
            'Proxy server ({}) does not exist on the cluster.'.format(octarine_bin))

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


def acs_install_cli(cmd, client, resource_group_name, name, install_location=None, client_version=None):
    acs_info = _get_acs_info(cmd.cli_ctx, name, resource_group_name)
    orchestrator_type = acs_info.orchestrator_profile.orchestrator_type  # pylint: disable=no-member
    kwargs = {'install_location': install_location}
    if client_version:
        kwargs['client_version'] = client_version
    if orchestrator_type == 'kubernetes':
        return k8s_install_cli(**kwargs)
    if orchestrator_type == 'dcos':
        return dcos_install_cli(**kwargs)
    raise CLIError(
        'Unsupported orchestrator type {} for install-cli'.format(orchestrator_type))


def _ssl_context():
    if sys.version_info < (3, 4) or (in_cloud_console() and platform.system() == 'Windows'):
        try:
            # added in python 2.7.13 and 3.6
            return ssl.SSLContext(ssl.PROTOCOL_TLS)
        except AttributeError:
            return ssl.SSLContext(ssl.PROTOCOL_TLSv1)

    return ssl.create_default_context()


def _urlretrieve(url, filename):
    req = urlopen(url, context=_ssl_context())
    with open(filename, "wb") as f:
        f.write(req.read())


def _unzip(src, dest):
    logger.debug('Extracting %s to %s.', src, dest)
    system = platform.system()
    if system in ('Linux', 'Darwin', 'Windows'):
        with zipfile.ZipFile(src, 'r') as zipObj:
            zipObj.extractall(dest)
    else:
        raise CLIError('The current system is not supported.')


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
        raise CLIError(
            'Proxy server ({}) does not exist on the cluster.'.format(system))

    logger.warning('Downloading client to %s', install_location)
    try:
        _urlretrieve(file_url, install_location)
        os.chmod(install_location,
                 os.stat(install_location).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except IOError as err:
        raise CLIError(
            'Connection error while attempting to download client ({})'.format(err))


def k8s_install_cli(cmd, client_version='latest', install_location=None, base_src_url=None,
                    kubelogin_version='latest', kubelogin_install_location=None,
                    kubelogin_base_src_url=None):
    k8s_install_kubectl(cmd, client_version, install_location, base_src_url)
    k8s_install_kubelogin(cmd, kubelogin_version,
                          kubelogin_install_location, kubelogin_base_src_url)


def k8s_install_kubectl(cmd, client_version='latest', install_location=None, source_url=None):
    """
    Install kubectl, a command-line interface for Kubernetes clusters.
    """

    if not source_url:
        source_url = "https://storage.googleapis.com/kubernetes-release/release"
        cloud_name = cmd.cli_ctx.cloud.name
        if cloud_name.lower() == 'azurechinacloud':
            source_url = 'https://mirror.azure.cn/kubernetes/kubectl'

    if client_version == 'latest':
        context = _ssl_context()
        version = urlopen(source_url + '/stable.txt', context=context).read()
        client_version = version.decode('UTF-8').strip()
    else:
        client_version = "v%s" % client_version

    file_url = ''
    system = platform.system()
    base_url = source_url + '/{}/bin/{}/amd64/{}'

    # ensure installation directory exists
    install_dir, cli = os.path.dirname(
        install_location), os.path.basename(install_location)
    if not os.path.exists(install_dir):
        os.makedirs(install_dir)

    if system == 'Windows':
        file_url = base_url.format(client_version, 'windows', 'kubectl.exe')
    elif system == 'Linux':
        # TODO: Support ARM CPU here
        file_url = base_url.format(client_version, 'linux', 'kubectl')
    elif system == 'Darwin':
        file_url = base_url.format(client_version, 'darwin', 'kubectl')
    else:
        raise CLIError(
            'Proxy server ({}) does not exist on the cluster.'.format(system))

    logger.warning('Downloading client to "%s" from "%s"',
                   install_location, file_url)
    try:
        _urlretrieve(file_url, install_location)
        os.chmod(install_location,
                 os.stat(install_location).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except IOError as ex:
        raise CLIError(
            'Connection error while attempting to download client ({})'.format(ex))

    if system == 'Windows':  # be verbose, as the install_location likely not in Windows's search PATHs
        env_paths = os.environ['PATH'].split(';')
        found = next((x for x in env_paths if x.lower().rstrip(
            '\\') == install_dir.lower()), None)
        if not found:
            # pylint: disable=logging-format-interpolation
            logger.warning('Please add "{0}" to your search PATH so the `{1}` can be found. 2 options: \n'
                           '    1. Run "set PATH=%PATH%;{0}" or "$env:path += \'{0}\'" for PowerShell. '
                           'This is good for the current command session.\n'
                           '    2. Update system PATH environment variable by following '
                           '"Control Panel->System->Advanced->Environment Variables", and re-open the command window. '
                           'You only need to do it once'.format(install_dir, cli))
    else:
        logger.warning('Please ensure that %s is in your search PATH, so the `%s` command can be found.',
                       install_dir, cli)


def k8s_install_kubelogin(cmd, client_version='latest', install_location=None, source_url=None):
    """
    Install kubelogin, a client-go credential (exec) plugin implementing azure authentication.
    """

    cloud_name = cmd.cli_ctx.cloud.name

    if not source_url:
        source_url = 'https://github.com/Azure/kubelogin/releases/download'
        if cloud_name.lower() == 'azurechinacloud':
            source_url = 'https://mirror.azure.cn/kubernetes/kubelogin'

    if client_version == 'latest':
        context = _ssl_context()
        latest_release_url = 'https://api.github.com/repos/Azure/kubelogin/releases/latest'
        if cloud_name.lower() == 'azurechinacloud':
            latest_release_url = 'https://mirror.azure.cn/kubernetes/kubelogin/latest'
        latest_release = urlopen(latest_release_url, context=context).read()
        client_version = json.loads(latest_release)['tag_name'].strip()
    else:
        client_version = "v%s" % client_version

    base_url = source_url + '/{}/kubelogin.zip'
    file_url = base_url.format(client_version)

    # ensure installation directory exists
    install_dir, cli = os.path.dirname(
        install_location), os.path.basename(install_location)
    if not os.path.exists(install_dir):
        os.makedirs(install_dir)

    system = platform.system()
    if system == 'Windows':
        sub_dir, binary_name = 'windows_amd64', 'kubelogin.exe'
    elif system == 'Linux':
        # TODO: Support ARM CPU here
        sub_dir, binary_name = 'linux_amd64', 'kubelogin'
    elif system == 'Darwin':
        if platform.machine() == 'arm64':
            sub_dir, binary_name = 'darwin_arm64', 'kubelogin'
        else:
            sub_dir, binary_name = 'darwin_amd64', 'kubelogin'
    else:
        raise CLIError(
            'Proxy server ({}) does not exist on the cluster.'.format(system))

    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            download_path = os.path.join(tmp_dir, 'kubelogin.zip')
            logger.warning('Downloading client to "%s" from "%s"',
                           download_path, file_url)
            _urlretrieve(file_url, download_path)
        except IOError as ex:
            raise CLIError(
                'Connection error while attempting to download client ({})'.format(ex))
        _unzip(download_path, tmp_dir)
        download_path = os.path.join(tmp_dir, 'bin', sub_dir, binary_name)
        shutil.move(download_path, install_location)
    os.chmod(install_location, os.stat(install_location).st_mode |
             stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    if system == 'Windows':  # be verbose, as the install_location likely not in Windows's search PATHs
        env_paths = os.environ['PATH'].split(';')
        found = next((x for x in env_paths if x.lower().rstrip(
            '\\') == install_dir.lower()), None)
        if not found:
            # pylint: disable=logging-format-interpolation
            logger.warning('Please add "{0}" to your search PATH so the `{1}` can be found. 2 options: \n'
                           '    1. Run "set PATH=%PATH%;{0}" or "$env:path += \'{0}\'" for PowerShell. '
                           'This is good for the current command session.\n'
                           '    2. Update system PATH environment variable by following '
                           '"Control Panel->System->Advanced->Environment Variables", and re-open the command window. '
                           'You only need to do it once'.format(install_dir, cli))
    else:
        logger.warning('Please ensure that %s is in your search PATH, so the `%s` command can be found.',
                       install_dir, cli)


def _build_service_principal(rbac_client, cli_ctx, name, url, client_secret):
    # use get_progress_controller
    hook = cli_ctx.get_progress_controller(True)
    hook.add(messsage='Creating service principal', value=0, total_val=1.0)
    logger.info('Creating service principal')
    # always create application with 5 years expiration
    start_date = datetime.datetime.utcnow()
    end_date = start_date + relativedelta(years=5)
    result, aad_session_key = create_application(rbac_client.applications, name, url, [url], password=client_secret,
                                                 start_date=start_date, end_date=end_date)
    service_principal = result.app_id  # pylint: disable=no-member
    for x in range(0, 10):
        hook.add(message='Creating service principal',
                 value=0.1 * x, total_val=1.0)
        try:
            create_service_principal(
                cli_ctx, service_principal, rbac_client=rbac_client)
            break
        # TODO figure out what exception AAD throws here sometimes.
        except Exception as ex:  # pylint: disable=broad-except
            logger.info(ex)
            time.sleep(2 + 2 * x)
    else:
        return False, aad_session_key
    hook.add(message='Finished service principal creation',
             value=1.0, total_val=1.0)
    logger.info('Finished service principal creation')
    return service_principal, aad_session_key


def _add_role_assignment(cmd, role, service_principal_msi_id, is_service_principal=True, delay=2, scope=None):
    # AAD can have delays in propagating data, so sleep and retry
    hook = cmd.cli_ctx.get_progress_controller(True)
    hook.add(message='Waiting for AAD role to propagate',
             value=0, total_val=1.0)
    logger.info('Waiting for AAD role to propagate')
    for x in range(0, 10):
        hook.add(message='Waiting for AAD role to propagate',
                 value=0.1 * x, total_val=1.0)
        try:
            # TODO: break this out into a shared utility library
            create_role_assignment(
                cmd, role, service_principal_msi_id, is_service_principal, scope=scope)
            break
        except CloudError as ex:
            if ex.message == 'The role assignment already exists.':
                break
            logger.info(ex.message)
        except CLIError as ex:
            logger.warning(str(ex))
        except Exception as ex:  # pylint: disable=broad-except
            logger.error(str(ex))
        time.sleep(delay + delay * x)
    else:
        return False
    hook.add(message='AAD role propagation done', value=1.0, total_val=1.0)
    logger.info('AAD role propagation done')
    return True


def delete_role_assignments(cli_ctx, ids=None, assignee=None, role=None, resource_group_name=None,
                            scope=None, include_inherited=False, yes=None, is_service_principal=True):
    factory = get_auth_management_client(cli_ctx, scope)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions
    ids = ids or []
    if ids:
        if assignee or role or resource_group_name or scope or include_inherited:
            raise CLIError(
                'When assignment ids are used, other parameter values are not required')
        for i in ids:
            assignments_client.delete_by_id(i)
        return
    if not any([ids, assignee, role, resource_group_name, scope, assignee, yes]):
        msg = 'This will delete all role assignments under the subscription. Are you sure?'
        if not prompt_y_n(msg, default="n"):
            return

    scope = _build_role_scope(resource_group_name, scope,
                              assignments_client.config.subscription_id)
    assignments = _search_role_assignments(cli_ctx, assignments_client, definitions_client,
                                           scope, assignee, role, include_inherited,
                                           include_groups=False, is_service_principal=is_service_principal)

    if assignments:
        for a in assignments:
            assignments_client.delete_by_id(a.id)


def _delete_role_assignments(cli_ctx, role, service_principal, delay=2, scope=None, is_service_principal=True):
    # AAD can have delays in propagating data, so sleep and retry
    hook = cli_ctx.get_progress_controller(True)
    hook.add(message='Waiting for AAD role to delete', value=0, total_val=1.0)
    logger.info('Waiting for AAD role to delete')
    for x in range(0, 10):
        hook.add(message='Waiting for AAD role to delete',
                 value=0.1 * x, total_val=1.0)
        try:
            delete_role_assignments(cli_ctx,
                                    role=role,
                                    assignee=service_principal,
                                    scope=scope,
                                    is_service_principal=is_service_principal)
            break
        except CLIError as ex:
            raise ex
        except CloudError as ex:
            logger.info(ex)
        time.sleep(delay + delay * x)
    else:
        return False
    hook.add(message='AAD role deletion done', value=1.0, total_val=1.0)
    logger.info('AAD role deletion done')
    return True


def _search_role_assignments(cli_ctx, assignments_client, definitions_client,
                             scope, assignee, role, include_inherited, include_groups,
                             is_service_principal=True):
    assignee_object_id = None
    if assignee:
        if is_service_principal:
            assignee_object_id = _resolve_object_id(cli_ctx, assignee)
        else:
            assignee_object_id = assignee

    # always use "scope" if provided, so we can get assignments beyond subscription e.g. management groups
    if scope:
        assignments = list(assignments_client.list_for_scope(
            scope=scope, filter='atScope()'))
    elif assignee_object_id:
        if include_groups:
            f = "assignedTo('{}')".format(assignee_object_id)
        else:
            f = "principalId eq '{}'".format(assignee_object_id)
        assignments = list(assignments_client.list(filter=f))
    else:
        assignments = list(assignments_client.list())

    if assignments:
        assignments = [a for a in assignments if (
            not scope or
            include_inherited and re.match(_get_role_property(a, 'scope'), scope, re.I) or
            _get_role_property(a, 'scope').lower() == scope.lower()
        )]

        if role:
            role_id = _resolve_role_id(role, scope, definitions_client)
            assignments = [i for i in assignments if _get_role_property(
                i, 'role_definition_id') == role_id]

        if assignee_object_id:
            assignments = [i for i in assignments if _get_role_property(
                i, 'principal_id') == assignee_object_id]

    return assignments


def _get_role_property(obj, property_name):
    if isinstance(obj, dict):
        return obj[property_name]
    return getattr(obj, property_name)


def _get_default_dns_prefix(name, resource_group_name, subscription_id):
    # Use subscription id to provide uniqueness and prevent DNS name clashes
    name_part = re.sub('[^A-Za-z0-9-]', '', name)[0:10]
    if not name_part[0].isalpha():
        name_part = (str('a') + name_part)[0:10]
    resource_group_part = re.sub(
        '[^A-Za-z0-9-]', '', resource_group_name)[0:16]
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
        master_pool_profile = _update_dict(
            default_master_pool_profile, master_profile)
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
        agent_pool_profiles.append(_update_dict(
            default_agent_pool_profile, {"name": "agentpool0"}))
    else:
        # override agentPoolProfiles by using the passed in agent_profiles
        for idx, ap in enumerate(agent_profiles):
            # if the user specified dnsPrefix, we honor that
            # otherwise, we use the idx to avoid duplicate dns name
            a = _update_dict(
                {"dnsPrefix": dns_name_prefix + 'agent' + str(idx)}, ap)
            agent_pool_profiles.append(
                _update_dict(default_agent_pool_profile, a))
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


def _get_user_assigned_identity_resource_id_regular_expression():
    return re.compile(
        r'/subscriptions/(.*?)/resourcegroups/(.*?)/providers/microsoft.managedidentity/userassignedidentities/(.*)',
        flags=re.IGNORECASE)


def _get_user_assigned_identity(cli_ctx, resource_id):
    resource_id = resource_id.lower()
    _re_user_assigned_identity_resource_id = _get_user_assigned_identity_resource_id_regular_expression()
    match = _re_user_assigned_identity_resource_id.search(resource_id)
    if match:
        subscription_id = match.group(1)
        resource_group_name = match.group(2)
        identity_name = match.group(3)
        msi_client = get_msi_client(cli_ctx, subscription_id)
        try:
            identity = msi_client.user_assigned_identities.get(resource_group_name=resource_group_name,
                                                               resource_name=identity_name)
        except CloudError as ex:
            if 'was not found' in ex.message:
                raise ResourceNotFoundError("Identity {} not found.".format(resource_id))
            raise ClientRequestError(ex.message)
        return identity
    raise InvalidArgumentValueError(
        "Cannot parse identity name from provided resource id {}.".format(resource_id))


def _get_user_assigned_identity_client_id(cli_ctx, resource_id):
    return _get_user_assigned_identity(cli_ctx, resource_id).client_id


def _get_user_assigned_identity_object_id(cli_ctx, resource_id):
    return _get_user_assigned_identity(cli_ctx, resource_id).principal_id


_re_snapshot_resource_id = re.compile(
    r'/subscriptions/(.*?)/resourcegroups/(.*?)/providers/microsoft.containerservice/snapshots/(.*)',
    flags=re.IGNORECASE)


def _get_snapshot(cli_ctx, snapshot_id):
    snapshot_id = snapshot_id.lower()
    match = _re_snapshot_resource_id.search(snapshot_id)
    if match:
        subscription_id = match.group(1)
        resource_group_name = match.group(2)
        snapshot_name = match.group(3)
        snapshot_client = cf_snapshots_client(cli_ctx, subscription_id=subscription_id)
        try:
            snapshot = snapshot_client.get(resource_group_name, snapshot_name)
        except CloudError as ex:
            if 'was not found' in ex.message:
                raise ResourceNotFoundError("Snapshot {} not found.".format(snapshot_id))
            raise CLIError(ex.message)
        return snapshot
    raise InvalidArgumentValueError(
        "Cannot parse snapshot name from provided resource id {}.".format(snapshot_id))


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
        raise CLIError(
            'Provided ssh key ({}) is invalid or non-existent'.format(ssh_key_value))

    subscription_id = get_subscription_id(cmd.cli_ctx)
    if not dns_name_prefix:
        dns_name_prefix = _get_default_dns_prefix(
            name, resource_group_name, subscription_id)

    rg_location = get_rg_location(cmd.cli_ctx, resource_group_name)
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
    windows_profile = _generate_windows_profile(
        windows, admin_username, admin_password)

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
            return _invoke_deployment(cmd, resource_group_name, deployment_name,
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


def _invoke_deployment(cmd, resource_group_name, deployment_name, template, parameters, validate, no_wait,
                       subscription_id=None):
    DeploymentProperties = cmd.get_models(
        'DeploymentProperties', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    properties = DeploymentProperties(
        template=template, parameters=parameters, mode='incremental')
    smc = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES,
                                  subscription_id=subscription_id).deployments

    Deployment = cmd.get_models(
        'Deployment', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
    deployment = Deployment(properties=properties)

    if validate:
        logger.info('==== BEGIN TEMPLATE ====')
        logger.info(json.dumps(template, indent=2))
        logger.info('==== END TEMPLATE ====')
        if cmd.supported_api_version(min_api='2019-10-01', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES):
            validation_poller = smc.begin_validate(
                resource_group_name, deployment_name, deployment)
            return LongRunningOperation(cmd.cli_ctx)(validation_poller)

        return smc.validate(resource_group_name, deployment_name, deployment)

    return sdk_no_wait(no_wait, smc.begin_create_or_update, resource_group_name, deployment_name, deployment)


def k8s_get_credentials(cmd, client, name, resource_group_name,
                        path=os.path.join(os.path.expanduser(
                            '~'), '.kube', 'config'),
                        ssh_key_file=None,
                        overwrite_existing=False):
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
    _k8s_get_credentials_internal(
        name, acs_info, path, ssh_key_file, overwrite_existing)


def _k8s_get_credentials_internal(name, acs_info, path, ssh_key_file, overwrite_existing):
    if ssh_key_file is not None and not os.path.isfile(ssh_key_file):
        raise CLIError(
            'Private key file {} does not exist'.format(ssh_key_file))

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
            merge_kubernetes_configurations(
                path, path_candidate, overwrite_existing)
        except yaml.YAMLError as exc:
            logger.warning(
                'Failed to merge credentials to kube config file: %s', exc)
            logger.warning(
                'The credentials have been saved to %s', path_candidate)


def _handle_merge(existing, addition, key, replace):
    if not addition.get(key, False):
        return
    if not existing.get(key):
        existing[key] = addition[key]
        return

    for i in addition[key]:
        for j in existing[key]:
            if not i.get('name', False) or not j.get('name', False):
                continue
            if i['name'] == j['name']:
                if replace or i == j:
                    existing[key].remove(j)
                else:
                    msg = 'A different object named {} already exists in your kubeconfig file.\nOverwrite?'
                    overwrite = False
                    try:
                        overwrite = prompt_y_n(msg.format(i['name']))
                    except NoTTYException:
                        pass
                    if overwrite:
                        existing[key].remove(j)
                    else:
                        msg = 'A different object named {} already exists in {} in your kubeconfig file.'
                        raise CLIError(msg.format(i['name'], key))
        existing[key].append(i)


def load_kubernetes_configuration(filename):
    try:
        with open(filename) as stream:
            return yaml.safe_load(stream)
    except (IOError, OSError) as ex:
        if getattr(ex, 'errno', 0) == errno.ENOENT:
            raise CLIError('{} does not exist'.format(filename))
        raise
    except (yaml.parser.ParserError, UnicodeDecodeError) as ex:
        raise CLIError('Error parsing {} ({})'.format(filename, str(ex)))


def merge_kubernetes_configurations(existing_file, addition_file, replace, context_name=None):
    existing = load_kubernetes_configuration(existing_file)
    addition = load_kubernetes_configuration(addition_file)

    if context_name is not None:
        addition['contexts'][0]['name'] = context_name
        addition['contexts'][0]['context']['cluster'] = context_name
        addition['clusters'][0]['name'] = context_name
        addition['current-context'] = context_name

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
        raise CLIError(
            'failed to load additional configuration from {}'.format(addition_file))

    if existing is None:
        existing = addition
    else:
        _handle_merge(existing, addition, 'clusters', replace)
        _handle_merge(existing, addition, 'users', replace)
        _handle_merge(existing, addition, 'contexts', replace)
        existing['current-context'] = addition['current-context']

    # check that ~/.kube/config is only read- and writable by its owner
    if platform.system() != 'Windows':
        existing_file_perms = "{:o}".format(
            stat.S_IMODE(os.lstat(existing_file).st_mode))
        if not existing_file_perms.endswith('600'):
            logger.warning('%s has permissions "%s".\nIt should be readable and writable only by its owner.',
                           existing_file, existing_file_perms)

    with open(existing_file, 'w+') as stream:
        yaml.safe_dump(existing, stream, default_flow_style=False)

    current_context = addition.get('current-context', 'UNKNOWN')
    msg = 'Merged "{}" as current context in {}'.format(
        current_context, existing_file)
    logger.warning(msg)


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

    return client.begin_create_or_update(resource_group_name, container_service_name, instance)


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
    result = list(client.list(
        filter="servicePrincipalNames/any(c:c eq '{}')".format(identifier)))
    if result:
        return result[0].object_id
    try:
        uuid.UUID(identifier)
        return identifier  # assume an object id
    except ValueError:
        raise CLIError(
            "service principal '{}' doesn't exist".format(identifier))


def create_application(client, display_name, homepage, identifier_uris,
                       available_to_other_tenants=False, password=None, reply_urls=None,
                       key_value=None, key_type=None, key_usage=None, start_date=None,
                       end_date=None, required_resource_accesses=None):
    from azure.graphrbac.models import GraphErrorException
    password_creds, key_creds = _build_application_creds(password, key_value, key_type,
                                                         key_usage, start_date, end_date)

    app_create_param = ApplicationCreateParameters(available_to_other_tenants=available_to_other_tenants,
                                                   display_name=display_name,
                                                   identifier_uris=identifier_uris,
                                                   homepage=homepage,
                                                   reply_urls=reply_urls,
                                                   key_credentials=key_creds,
                                                   password_credentials=password_creds,
                                                   required_resource_access=required_resource_accesses)
    try:
        result = client.create(app_create_param, raw=True)
        return result.output, result.response.headers["ocp-aad-session-key"]
    except GraphErrorException as ex:
        if 'insufficient privileges' in str(ex).lower():
            link = 'https://docs.microsoft.com/azure/azure-resource-manager/resource-group-create-service-principal-portal'  # pylint: disable=line-too-long
            raise CLIError("Directory permission is needed for the current user to register the application. "
                           "For how to configure, please refer '{}'. Original error: {}".format(link, ex))
        raise


def update_application(client, object_id, display_name, homepage, identifier_uris,
                       available_to_other_tenants=False, password=None, reply_urls=None,
                       key_value=None, key_type=None, key_usage=None, start_date=None,
                       end_date=None, required_resource_accesses=None):
    from azure.graphrbac.models import GraphErrorException
    password_creds, key_creds = _build_application_creds(password, key_value, key_type,
                                                         key_usage, start_date, end_date)
    try:
        if key_creds:
            client.update_key_credentials(object_id, key_creds)
        if password_creds:
            client.update_password_credentials(object_id, password_creds)
        if reply_urls:
            client.patch(object_id, ApplicationUpdateParameters(
                reply_urls=reply_urls))
        return
    except GraphErrorException as ex:
        if 'insufficient privileges' in str(ex).lower():
            link = 'https://docs.microsoft.com/azure/azure-resource-manager/resource-group-create-service-principal-portal'  # pylint: disable=line-too-long
            raise CLIError("Directory permission is needed for the current user to register the application. "
                           "For how to configure, please refer '{}'. Original error: {}".format(link, ex))
        raise


def _build_application_creds(password=None, key_value=None, key_type=None,
                             key_usage=None, start_date=None, end_date=None):
    if password and key_value:
        raise CLIError(
            'specify either --password or --key-value, but not both.')

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
            result = list(rbac_client.applications.list(
                filter="appId eq '{}'".format(identifier)))
        except ValueError:
            result = list(rbac_client.applications.list(
                filter="identifierUris/any(s:s eq '{}')".format(identifier)))

        if not result:  # assume we get an object id
            result = [rbac_client.applications.get(identifier)]
        app_id = result[0].app_id
    else:
        app_id = identifier

    return rbac_client.service_principals.create(ServicePrincipalCreateParameters(app_id=app_id, account_enabled=True))


def create_role_assignment(cmd, role, assignee, is_service_principal, resource_group_name=None, scope=None):
    return _create_role_assignment(cmd,
                                   role, assignee, resource_group_name,
                                   scope, resolve_assignee=is_service_principal)


def _create_role_assignment(cmd, role, assignee,
                            resource_group_name=None, scope=None, resolve_assignee=True):
    from azure.cli.core.profiles import get_sdk
    factory = get_auth_management_client(cmd.cli_ctx, scope)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions

    scope = _build_role_scope(
        resource_group_name, scope, assignments_client.config.subscription_id)

    role_id = _resolve_role_id(role, scope, definitions_client)

    # If the cluster has service principal resolve the service principal client id to get the object id,
    # if not use MSI object id.
    object_id = assignee
    if resolve_assignee:
        from azure.graphrbac.models import GraphErrorException
        error_msg = "Failed to resolve service principal object ID: "
        try:
            object_id = _resolve_object_id(cmd.cli_ctx, assignee)
        except GraphErrorException as ex:
            if ex.response is not None:
                error_code = getattr(ex.response, "status_code", None)
                error_reason = getattr(ex.response, "reason", None)
                internal_error = ""
                if error_code:
                    internal_error += str(error_code)
                if error_reason:
                    if internal_error:
                        internal_error += " - "
                    internal_error += str(error_reason)
                if internal_error:
                    error_msg += "({}) ".format(internal_error)
            error_msg += ex.message
            # this should be UserFault or ServiceError, but it is meaningless to distinguish them here
            raise CLIError(error_msg)
        except Exception as ex:  # pylint: disable=bare-except
            raise CLIError(error_msg + str(ex))

    assignment_name = uuid.uuid4()
    custom_headers = None

    RoleAssignmentCreateParameters = get_sdk(cmd.cli_ctx, ResourceType.MGMT_AUTHORIZATION,
                                             'RoleAssignmentCreateParameters', mod='models',
                                             operation_group='role_assignments')
    if cmd.supported_api_version(min_api='2018-01-01-preview', resource_type=ResourceType.MGMT_AUTHORIZATION):
        parameters = RoleAssignmentCreateParameters(
            role_definition_id=role_id, principal_id=object_id)
        return assignments_client.create(scope, assignment_name, parameters, custom_headers=custom_headers)

    RoleAssignmentProperties = get_sdk(cmd.cli_ctx, ResourceType.MGMT_AUTHORIZATION,
                                       'RoleAssignmentProperties', mod='models',
                                       operation_group='role_assignments')
    properties = RoleAssignmentProperties(role_definition_id=role_id, principal_id=object_id)
    return assignments_client.create(scope, assignment_name, properties, custom_headers=custom_headers)


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
        role_defs = list(definitions_client.list(
            scope, "roleName eq '{}'".format(role)))
        if not role_defs:
            raise CLIError("Role '{}' doesn't exist.".format(role))
        if len(role_defs) > 1:
            ids = [r.id for r in role_defs]
            err = "More than one role matches the given name '{}'. Please pick a value from '{}'"
            raise CLIError(err.format(role, ids))
        role_id = role_defs[0].id
    return role_id


def _resolve_object_id(cli_ctx, assignee):
    client = get_graph_rbac_management_client(cli_ctx)
    result = None
    if assignee.find('@') >= 0:  # looks like a user principal name
        result = list(client.users.list(
            filter="userPrincipalName eq '{}'".format(assignee)))
    if not result:
        result = list(client.service_principals.list(
            filter="servicePrincipalNames/any(c:c eq '{}')".format(assignee)))
    if not result:  # assume an object id, let us verify it
        result = _get_object_stubs(client, [assignee])

    # 2+ matches should never happen, so we only check 'no match' here
    if not result:
        raise CLIError(
            "No matches in graph database for '{}'".format(assignee))

    return result[0].object_id


def _get_object_stubs(graph_client, assignees):
    params = GetObjectsParameters(include_directory_object_references=True,
                                  object_ids=assignees)
    return list(graph_client.objects.get_objects_by_object_ids(params))


def _update_dict(dict1, dict2):
    cp = dict1.copy()
    cp.update(dict2)
    return cp


def subnet_role_assignment_exists(cmd, scope):
    network_contributor_role_id = "4d97b98b-1d4f-4787-a291-c67834d212e7"

    factory = get_auth_management_client(cmd.cli_ctx, scope)
    assignments_client = factory.role_assignments

    if cmd.supported_api_version(min_api='2018-01-01-preview', resource_type=ResourceType.MGMT_AUTHORIZATION):
        for i in assignments_client.list_for_scope(scope=scope, filter='atScope()'):
            if i.scope == scope and i.role_definition_id.endswith(network_contributor_role_id):
                return True
    return False


def aks_check_acr(cmd, client, resource_group_name, name, acr):
    if not which("kubectl"):
        raise ValidationError("Can not find kubectl executable in PATH")

    return_msg = None
    fd, browse_path = tempfile.mkstemp()
    try:
        aks_get_credentials(
            cmd, client, resource_group_name, name, admin=False, path=browse_path
        )

        # Get kubectl minor version
        kubectl_minor_version = -1
        try:
            cmd = f"kubectl version -o json --kubeconfig {browse_path}"
            output = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            jsonS, _ = output.communicate()
            kubectl_version = json.loads(jsonS)
            # Remove any non-numeric characters like + from minor version
            kubectl_minor_version = int(re.sub(r"\D", "", kubectl_version["clientVersion"]["minor"]))
            kubectl_server_minor_version = int(
                kubectl_version["serverVersion"]["minor"])
            kubectl_server_patch = int(
                kubectl_version["serverVersion"]["gitVersion"].split(".")[-1])
            if kubectl_server_minor_version < 17 or (kubectl_server_minor_version == 17 and kubectl_server_patch < 14):
                logger.warning(
                    "There is a known issue for Kubernetes versions < 1.17.14 when connecting to "
                    "ACR using MSI. See https://github.com/kubernetes/kubernetes/pull/96355 for"
                    "more information."
                )
        except subprocess.CalledProcessError as err:
            raise ValidationError(
                "Could not find kubectl minor version: {}".format(err))
        if kubectl_minor_version == -1:
            raise ValidationError("Failed to get kubectl version")

        podName = "canipull-" + str(uuid.uuid4())
        overrides = {
            "spec": {
                "restartPolicy": "Never",
                "hostNetwork": True,
                "containers": [
                    {
                        "securityContext": {"runAsUser": 0},
                        "name": podName,
                        "image": CONST_CANIPULL_IMAGE,
                        "args": ["-v6", acr],
                        "stdin": True,
                        "stdinOnce": True,
                        "tty": True,
                        "volumeMounts": [
                            {"name": "azurejson", "mountPath": "/etc/kubernetes"},
                            {"name": "sslcerts", "mountPath": "/etc/ssl/certs"},
                        ],
                    }
                ],
                "tolerations": [
                    {"key": "CriticalAddonsOnly", "operator": "Exists"},
                    {"effect": "NoExecute", "operator": "Exists"},
                ],
                "volumes": [
                    {"name": "azurejson", "hostPath": {"path": "/etc/kubernetes"}},
                    {"name": "sslcerts", "hostPath": {"path": "/etc/ssl/certs"}},
                ],
                "nodeSelector": {"kubernetes.io/os": "linux"},
            }
        }

        try:
            cmd = [
                "kubectl",
                "run",
                "--kubeconfig",
                browse_path,
                "--rm",
                "--quiet",
                "--image",
                CONST_CANIPULL_IMAGE,
                "--overrides",
                json.dumps(overrides),
                "-it",
                podName,
                "--namespace=default",
            ]

            # Support kubectl versons < 1.18
            if kubectl_minor_version < 18:
                cmd += ["--generator=run-pod/v1"]

            output = subprocess.check_output(
                cmd,
                universal_newlines=True,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as err:
            raise AzureInternalError("Failed to check the ACR: {} Command output: {}".format(err, err.output))
        if output:
            print(output)
            # only return the output in test case "test_aks_create_attach_acr"
            test_hook_data = get_cmd_test_hook_data("test_aks_create_attach_acr.hook")
            if test_hook_data:
                test_configs = test_hook_data.get("configs", None)
                if test_configs and test_configs.get("returnOutput", False):
                    return_msg = output
        else:
            raise AzureInternalError("Failed to check the ACR.")
    finally:
        os.close(fd)
    return return_msg


# pylint: disable=too-many-statements,too-many-branches
def _aks_browse(
    cmd,
    client,
    resource_group_name,
    name,
    disable_browser=False,
    listen_address="127.0.0.1",
    listen_port="8001",
    resource_type=ResourceType.MGMT_CONTAINERSERVICE,
):
    ManagedClusterAddonProfile = cmd.get_models('ManagedClusterAddonProfile',
                                                resource_type=resource_type,
                                                operation_group='managed_clusters')
    # verify the kube-dashboard addon was not disabled
    instance = client.get(resource_group_name, name)
    addon_profiles = instance.addon_profiles or {}
    # addon name is case insensitive
    addon_profile = next((addon_profiles[k] for k in addon_profiles
                          if k.lower() == CONST_KUBE_DASHBOARD_ADDON_NAME.lower()),
                         ManagedClusterAddonProfile(enabled=False))

    return_msg = None
    # open portal view if addon is not enabled or k8s version >= 1.19.0
    if StrictVersion(instance.kubernetes_version) >= StrictVersion('1.19.0') or (not addon_profile.enabled):
        subscription_id = get_subscription_id(cmd.cli_ctx)
        dashboardURL = (
            # Azure Portal URL (https://portal.azure.com for public cloud)
            cmd.cli_ctx.cloud.endpoints.portal +
            ('/#resource/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.ContainerService'
             '/managedClusters/{2}/workloads').format(subscription_id, resource_group_name, name)
        )

        if in_cloud_console():
            logger.warning(
                'To view the Kubernetes resources view, please open %s in a new tab', dashboardURL)
        else:
            logger.warning('Kubernetes resources view on %s', dashboardURL)
            return_msg = "Kubernetes resources view on {}".format(dashboardURL)

        if not disable_browser:
            webbrowser.open_new_tab(dashboardURL)
        return return_msg

    # otherwise open the kube-dashboard addon
    if not which('kubectl'):
        raise FileOperationError('Can not find kubectl executable in PATH')

    fd, browse_path = tempfile.mkstemp()
    try:
        aks_get_credentials(cmd, client, resource_group_name,
                            name, admin=False, path=browse_path)

        # find the dashboard pod's name
        try:
            dashboard_pod = subprocess.check_output(
                [
                    "kubectl",
                    "get",
                    "pods",
                    "--kubeconfig",
                    browse_path,
                    "--namespace",
                    "kube-system",
                    "--output",
                    "name",
                    "--selector",
                    "k8s-app=kubernetes-dashboard",
                ],
                universal_newlines=True,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as err:
            raise ResourceNotFoundError('Could not find dashboard pod: {} Command output: {}'.format(err, err.output))
        if dashboard_pod:
            # remove any "pods/" or "pod/" prefix from the name
            dashboard_pod = str(dashboard_pod).split('/')[-1].strip()
        else:
            raise ResourceNotFoundError("Couldn't find the Kubernetes dashboard pod.")

        # find the port
        try:
            dashboard_port = subprocess.check_output(
                [
                    "kubectl",
                    "get",
                    "pods",
                    "--kubeconfig",
                    browse_path,
                    "--namespace",
                    "kube-system",
                    "--selector",
                    "k8s-app=kubernetes-dashboard",
                    "--output",
                    "jsonpath='{.items[0].spec.containers[0].ports[0].containerPort}'",
                ],
                universal_newlines=True,
                stderr=subprocess.STDOUT,
            )
            # output format: "'{port}'"
            dashboard_port = int((dashboard_port.replace("'", "")))
        except subprocess.CalledProcessError as err:
            raise ResourceNotFoundError('Could not find dashboard port: {} Command output: {}'.format(err, err.output))

        # use https if dashboard container is using https
        if dashboard_port == 8443:
            protocol = 'https'
        else:
            protocol = 'http'

        proxy_url = 'http://{0}:{1}/'.format(listen_address, listen_port)
        dashboardURL = '{0}/api/v1/namespaces/kube-system/services/{1}:kubernetes-dashboard:/proxy/'.format(proxy_url,
                                                                                                            protocol)
        # launch kubectl port-forward locally to access the remote dashboard
        if in_cloud_console():
            # TODO: better error handling here.
            response = requests.post(
                'http://localhost:8888/openport/{0}'.format(listen_port))
            result = json.loads(response.text)
            dashboardURL = '{0}api/v1/namespaces/kube-system/services/{1}:kubernetes-dashboard:/proxy/'.format(
                result['url'], protocol)
            term_id = os.environ.get('ACC_TERM_ID')
            if term_id:
                response = requests.post(
                    "http://localhost:8888/openLink/{0}".format(term_id),
                    json={"url": dashboardURL},
                )
            logger.warning(
                'To view the console, please open %s in a new tab', dashboardURL)
        else:
            logger.warning('Proxy running on %s', proxy_url)

        timeout = None
        test_hook_data = get_cmd_test_hook_data("test_aks_browse_legacy.hook")
        if test_hook_data:
            test_configs = test_hook_data.get("configs", None)
            if test_configs and test_configs.get("enableTimeout", False):
                timeout = test_configs.get("timeoutInterval", None)
        logger.warning('Press CTRL+C to close the tunnel...')
        if not disable_browser:
            wait_then_open_async(dashboardURL)
        try:
            try:
                subprocess.check_output(
                    [
                        "kubectl",
                        "--kubeconfig",
                        browse_path,
                        "proxy",
                        "--address",
                        listen_address,
                        "--port",
                        listen_port,
                    ],
                    universal_newlines=True,
                    stderr=subprocess.STDOUT,
                    timeout=timeout,
                )
            except subprocess.CalledProcessError as err:
                if err.output.find('unknown flag: --address'):
                    return_msg = "Test Invalid Address! "
                    if listen_address != '127.0.0.1':
                        logger.warning(
                            '"--address" is only supported in kubectl v1.13 and later.')
                        logger.warning(
                            'The "--listen-address" argument will be ignored.')
                    try:
                        subprocess.call(["kubectl", "--kubeconfig",
                                        browse_path, "proxy", "--port", listen_port], timeout=timeout)
                    except subprocess.TimeoutExpired:
                        logger.warning("Currently in a test environment, the proxy is closed due to a preset timeout!")
                        return_msg = return_msg if return_msg else ""
                        return_msg += "Test Passed!"
                    except subprocess.CalledProcessError as new_err:
                        raise AzureInternalError(
                            "Could not open proxy: {} Command output: {}".format(
                                new_err, new_err.output
                            )
                        )
                else:
                    raise AzureInternalError(
                        "Could not open proxy: {} Command output: {}".format(
                            err, err.output
                        )
                    )
            except subprocess.TimeoutExpired:
                logger.warning("Currently in a test environment, the proxy is closed due to a preset timeout!")
                return_msg = return_msg if return_msg else ""
                return_msg += "Test Passed!"
        except KeyboardInterrupt:
            # Let command processing finish gracefully after the user presses [Ctrl+C]
            pass
        finally:
            if in_cloud_console():
                requests.post('http://localhost:8888/closeport/8001')
    finally:
        os.close(fd)
    return return_msg


# pylint: disable=too-many-statements,too-many-branches
def aks_browse(
    cmd,
    client,
    resource_group_name,
    name,
    disable_browser=False,
    listen_address="127.0.0.1",
    listen_port="8001",
):

    return _aks_browse(
        cmd,
        client,
        resource_group_name,
        name,
        disable_browser=disable_browser,
        listen_address=listen_address,
        listen_port=listen_port,
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
    )


def _trim_nodepoolname(nodepool_name):
    if not nodepool_name:
        return "nodepool1"
    return nodepool_name[:12]


def _validate_ssh_key(no_ssh_key, ssh_key_value):
    if not no_ssh_key:
        try:
            if not ssh_key_value or not is_valid_ssh_rsa_public_key(ssh_key_value):
                raise ValueError()
        except (TypeError, ValueError):
            shortened_key = truncate_text(ssh_key_value)
            raise CLIError(
                'Provided ssh key ({}) is invalid or non-existent'.format(shortened_key))


# pylint: disable=too-many-statements,too-many-branches
def aks_create(cmd, client, resource_group_name, name, ssh_key_value,  # pylint: disable=too-many-locals
               dns_name_prefix=None,
               location=None,
               admin_username="azureuser",
               windows_admin_username=None,
               windows_admin_password=None,
               enable_ahub=False,
               kubernetes_version='',
               node_vm_size=None,
               node_osdisk_type=None,
               node_osdisk_size=0,
               node_osdisk_diskencryptionset_id=None,
               node_count=3,
               nodepool_name="nodepool1",
               nodepool_tags=None,
               nodepool_labels=None,
               service_principal=None, client_secret=None,
               no_ssh_key=False,
               disable_rbac=None,
               enable_rbac=None,
               vm_set_type=None,
               skip_subnet_role_assignment=False,
               os_sku=None,
               enable_cluster_autoscaler=False,
               cluster_autoscaler_profile=None,
               network_plugin=None,
               network_policy=None,
               uptime_sla=False,
               pod_cidr=None,
               service_cidr=None,
               dns_service_ip=None,
               docker_bridge_address=None,
               load_balancer_sku=None,
               load_balancer_managed_outbound_ip_count=None,
               load_balancer_outbound_ips=None,
               load_balancer_outbound_ip_prefixes=None,
               load_balancer_outbound_ports=None,
               load_balancer_idle_timeout=None,
               outbound_type=None,
               auto_upgrade_channel=None,
               enable_addons=None,
               workspace_resource_id=None,
               vnet_subnet_id=None,
               ppg=None,
               max_pods=0,
               min_count=None,
               max_count=None,
               aad_client_app_id=None,
               aad_server_app_id=None,
               aad_server_app_secret=None,
               aad_tenant_id=None,
               tags=None,
               zones=None,
               enable_node_public_ip=False,
               node_public_ip_prefix_id=None,
               generate_ssh_keys=False,  # pylint: disable=unused-argument
               api_server_authorized_ip_ranges=None,
               enable_private_cluster=False,
               private_dns_zone=None,
               fqdn_subdomain=None,
               disable_public_fqdn=False,
               enable_managed_identity=True,
               assign_identity=None,
               attach_acr=None,
               enable_aad=False,
               aad_admin_group_object_ids=None,
               aci_subnet_name=None,
               appgw_name=None,
               appgw_subnet_cidr=None,
               appgw_id=None,
               appgw_subnet_id=None,
               appgw_watch_namespace=None,
               enable_sgxquotehelper=False,
               enable_encryption_at_host=False,
               enable_secret_rotation=False,
               rotation_poll_interval=None,
               assign_kubelet_identity=None,
               enable_ultra_ssd=False,
               edge_zone=None,
               disable_local_accounts=False,
               enable_fips_image=False,
               no_wait=False,
               yes=False,
               enable_azure_rbac=False,
               aks_custom_headers=None,
               snapshot_id=None,
               ):
    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()

    # decorator pattern
    from .decorator import AKSCreateDecorator
    aks_create_decorator = AKSCreateDecorator(
        cmd=cmd,
        client=client,
        raw_parameters=raw_parameters,
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
    )
    try:
        # construct mc profile
        mc = aks_create_decorator.construct_default_mc_profile()
    except DecoratorEarlyExitException:
        # exit gracefully
        return None
    # send request to create a real managed cluster
    return aks_create_decorator.create_mc(mc)


def aks_disable_addons(cmd, client, resource_group_name, name, addons, no_wait=False):
    instance = client.get(resource_group_name, name)
    subscription_id = get_subscription_id(cmd.cli_ctx)

    instance = _update_addons(
        cmd,
        instance,
        subscription_id,
        resource_group_name,
        name,
        addons,
        enable=False,
        no_wait=no_wait
    )

    # send the managed cluster representation to update the addon profiles
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, name, instance)


def aks_enable_addons(cmd, client, resource_group_name, name, addons,
                      workspace_resource_id=None,
                      subnet_name=None,
                      appgw_name=None,
                      appgw_subnet_cidr=None,
                      appgw_id=None,
                      appgw_subnet_id=None,
                      appgw_watch_namespace=None,
                      enable_sgxquotehelper=False,
                      enable_secret_rotation=False,
                      rotation_poll_interval=None,
                      no_wait=False):
    instance = client.get(resource_group_name, name)
    subscription_id = get_subscription_id(cmd.cli_ctx)

    instance = _update_addons(cmd, instance, subscription_id, resource_group_name, name, addons, enable=True,
                              workspace_resource_id=workspace_resource_id,
                              subnet_name=subnet_name,
                              appgw_name=appgw_name,
                              appgw_subnet_cidr=appgw_subnet_cidr,
                              appgw_id=appgw_id,
                              appgw_subnet_id=appgw_subnet_id,
                              appgw_watch_namespace=appgw_watch_namespace,
                              enable_sgxquotehelper=enable_sgxquotehelper,
                              enable_secret_rotation=enable_secret_rotation,
                              rotation_poll_interval=rotation_poll_interval,
                              no_wait=no_wait)

    enable_monitoring = CONST_MONITORING_ADDON_NAME in instance.addon_profiles \
        and instance.addon_profiles[CONST_MONITORING_ADDON_NAME].enabled
    ingress_appgw_addon_enabled = CONST_INGRESS_APPGW_ADDON_NAME in instance.addon_profiles \
        and instance.addon_profiles[CONST_INGRESS_APPGW_ADDON_NAME].enabled

    os_type = 'Linux'
    virtual_node_addon_name = CONST_VIRTUAL_NODE_ADDON_NAME + os_type
    enable_virtual_node = (virtual_node_addon_name in instance.addon_profiles and
                           instance.addon_profiles[virtual_node_addon_name].enabled)

    need_pull_for_result = enable_monitoring or ingress_appgw_addon_enabled or enable_virtual_node

    if need_pull_for_result:
        if enable_monitoring:
            ensure_container_insights_for_monitoring(
                cmd,
                instance.addon_profiles[CONST_MONITORING_ADDON_NAME],
                subscription_id,
                resource_group_name,
                name,
                instance.location,
                aad_route=False,
            )

        # adding a wait here since we rely on the result for role assignment
        result = LongRunningOperation(cmd.cli_ctx)(
            client.begin_create_or_update(resource_group_name, name, instance))

        if enable_monitoring:
            cloud_name = cmd.cli_ctx.cloud.name
            # mdm metrics supported only in Azure Public cloud so add the role assignment only in this cloud
            if cloud_name.lower() == 'azurecloud':
                from msrestazure.tools import resource_id
                cluster_resource_id = resource_id(
                    subscription=subscription_id,
                    resource_group=resource_group_name,
                    namespace='Microsoft.ContainerService', type='managedClusters',
                    name=name
                )
                add_monitoring_role_assignment(
                    result, cluster_resource_id, cmd)

        if ingress_appgw_addon_enabled:
            add_ingress_appgw_addon_role_assignment(result, cmd)

        if enable_virtual_node:
            # All agent pool will reside in the same vnet, we will grant vnet level Contributor role
            # in later function, so using a random agent pool here is OK
            random_agent_pool = result.agent_pool_profiles[0]
            if random_agent_pool.vnet_subnet_id != "":
                add_virtual_node_role_assignment(
                    cmd, result, random_agent_pool.vnet_subnet_id)
            # Else, the cluster is not using custom VNet, the permission is already granted in AKS RP,
            # we don't need to handle it in client side in this case.
    else:
        result = sdk_no_wait(no_wait, client.begin_create_or_update,
                             resource_group_name, name, instance)
    return result


def aks_get_versions(cmd, client, location):
    return client.list_orchestrators(location, resource_type='managedClusters')


def aks_get_credentials(cmd, client, resource_group_name, name, admin=False,
                        path=os.path.join(os.path.expanduser(
                            '~'), '.kube', 'config'),
                        overwrite_existing=False, context_name=None, public_fqdn=False,
                        credential_format=None):
    credentialResults = None
    serverType = None
    if public_fqdn:
        serverType = 'public'
    if credential_format:
        credential_format = credential_format.lower()
        if admin:
            raise InvalidArgumentValueError("--format can only be specified when requesting clusterUser credential.")
    if admin:
        if cmd.cli_ctx.cloud.profile == "latest":
            credentialResults = client.list_cluster_admin_credentials(
                resource_group_name, name, serverType)
        else:
            credentialResults = client.list_cluster_admin_credentials(
                resource_group_name, name)
    else:
        if cmd.cli_ctx.cloud.profile == "latest":
            credentialResults = client.list_cluster_user_credentials(
                resource_group_name, name, serverType, credential_format)
        else:
            credentialResults = client.list_cluster_user_credentials(
                resource_group_name, name)

    # Check if KUBECONFIG environmental variable is set
    # If path is different than default then that means -f/--file is passed
    # in which case we ignore the KUBECONFIG variable
    # KUBECONFIG can be colon separated. If we find that condition, use the first entry
    if "KUBECONFIG" in os.environ and path == os.path.join(os.path.expanduser('~'), '.kube', 'config'):
        path = os.environ["KUBECONFIG"].split(":")[0]

    if not credentialResults:
        raise CLIError("No Kubernetes credentials found.")
    try:
        kubeconfig = credentialResults.kubeconfigs[0].value.decode(
            encoding='UTF-8')
        _print_or_merge_credentials(
            path, kubeconfig, overwrite_existing, context_name)
    except (IndexError, ValueError):
        raise CLIError("Fail to find kubeconfig file.")


def aks_list(cmd, client, resource_group_name=None):
    if resource_group_name:
        managed_clusters = client.list_by_resource_group(resource_group_name)
    else:
        managed_clusters = client.list()
    return _remove_nulls(list(managed_clusters))


def aks_show(cmd, client, resource_group_name, name):
    mc = client.get(resource_group_name, name)
    return _remove_nulls([mc])[0]


def aks_update_credentials(cmd, client, resource_group_name, name,
                           reset_service_principal=False,
                           reset_aad=False,
                           service_principal=None,
                           client_secret=None,
                           aad_server_app_id=None,
                           aad_server_app_secret=None,
                           aad_client_app_id=None,
                           aad_tenant_id=None,
                           no_wait=False):
    ManagedClusterServicePrincipalProfile = cmd.get_models('ManagedClusterServicePrincipalProfile',
                                                           resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                                           operation_group='managed_clusters')
    if bool(reset_service_principal) == bool(reset_aad):
        raise CLIError(
            'usage error: --reset-service-principal | --reset-aad-profile')
    if reset_service_principal:
        if service_principal is None or client_secret is None:
            raise CLIError(
                'usage error: --reset-service-principal --service-principal ID --client-secret SECRET')
        service_principal_profile = ManagedClusterServicePrincipalProfile(
            client_id=service_principal, secret=client_secret
        )
        return sdk_no_wait(no_wait,
                           client.begin_reset_service_principal_profile,
                           resource_group_name,
                           name, service_principal_profile)
    if not all([aad_client_app_id, aad_server_app_id, aad_server_app_secret]):
        raise CLIError('usage error: --reset-aad --aad-client-app-id ID --aad-server-app-id ID '
                       '--aad-server-app-secret SECRET [--aad-tenant-id ID]')
    parameters = {
        'clientAppID': aad_client_app_id,
        'serverAppID': aad_server_app_id,
        'serverAppSecret': aad_server_app_secret,
        'tenantID': aad_tenant_id
    }
    return sdk_no_wait(no_wait,
                       client.begin_reset_aad_profile,
                       resource_group_name,
                       name, parameters)


def aks_scale(cmd, client, resource_group_name, name, node_count, nodepool_name="", no_wait=False):
    instance = client.get(resource_group_name, name)

    if len(instance.agent_pool_profiles) > 1 and nodepool_name == "":
        raise CLIError('There are more than one node pool in the cluster. '
                       'Please specify nodepool name or use az aks nodepool command to scale node pool')

    for agent_profile in instance.agent_pool_profiles:
        if agent_profile.name == nodepool_name or (nodepool_name == "" and len(instance.agent_pool_profiles) == 1):
            if agent_profile.enable_auto_scaling:
                raise CLIError(
                    "Cannot scale cluster autoscaler enabled node pool.")

            agent_profile.count = int(node_count)  # pylint: disable=no-member
            # null out the SP and AAD profile because otherwise validation complains
            instance.service_principal_profile = None
            instance.aad_profile = None
            return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, name, instance)
    raise CLIError('The nodepool "{}" was not found.'.format(nodepool_name))


# pylint: disable=inconsistent-return-statements
def aks_update(cmd, client, resource_group_name, name,
               enable_cluster_autoscaler=False,
               disable_cluster_autoscaler=False,
               update_cluster_autoscaler=False,
               cluster_autoscaler_profile=None,
               min_count=None, max_count=None,
               uptime_sla=False,
               no_uptime_sla=False,
               load_balancer_managed_outbound_ip_count=None,
               load_balancer_outbound_ips=None,
               load_balancer_outbound_ip_prefixes=None,
               load_balancer_outbound_ports=None,
               load_balancer_idle_timeout=None,
               attach_acr=None,
               detach_acr=None,
               api_server_authorized_ip_ranges=None,
               enable_aad=False,
               aad_tenant_id=None,
               aad_admin_group_object_ids=None,
               enable_ahub=False,
               disable_ahub=False,
               windows_admin_password=None,
               auto_upgrade_channel=None,
               enable_managed_identity=False,
               assign_identity=None,
               disable_local_accounts=False,
               enable_local_accounts=False,
               yes=False,
               no_wait=False,
               enable_public_fqdn=False,
               disable_public_fqdn=False,
               enable_azure_rbac=False,
               disable_azure_rbac=False,
               enable_secret_rotation=False,
               disable_secret_rotation=False,
               rotation_poll_interval=None,
               tags=None,
               nodepool_labels=None,
               aks_custom_headers=None):
    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()

    # decorator pattern
    from .decorator import AKSUpdateDecorator
    aks_update_decorator = AKSUpdateDecorator(
        cmd=cmd,
        client=client,
        raw_parameters=raw_parameters,
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
    )
    try:
        # update mc profile
        mc = aks_update_decorator.update_default_mc_profile()
    except DecoratorEarlyExitException:
        # exit gracefully
        return None
    # send request to update the real managed cluster
    return aks_update_decorator.update_mc(mc)


# pylint: disable=unused-argument,inconsistent-return-statements,too-many-return-statements
def aks_upgrade(cmd,
                client,
                resource_group_name, name,
                kubernetes_version='',
                control_plane_only=False,
                node_image_only=False,
                no_wait=False,
                yes=False):
    msg = 'Kubernetes may be unavailable during cluster upgrades.\n Are you sure you want to perform this operation?'
    if not yes and not prompt_y_n(msg, default="n"):
        return None

    instance = client.get(resource_group_name, name)

    vmas_cluster = False
    for agent_profile in instance.agent_pool_profiles:
        if agent_profile.type.lower() == "availabilityset":
            vmas_cluster = True
            break

    if kubernetes_version != '' and node_image_only:
        raise CLIError('Conflicting flags. Upgrading the Kubernetes version will also upgrade node image version. '
                       'If you only want to upgrade the node version please use the "--node-image-only" option only.')

    if node_image_only:
        msg = "This node image upgrade operation will run across every node pool in the cluster" \
              "and might take a while, do you wish to continue?"
        if not yes and not prompt_y_n(msg, default="n"):
            return None

        # This only provide convenience for customer at client side so they can run az aks upgrade to upgrade all
        # nodepools of a cluster. The SDK only support upgrade single nodepool at a time.
        for agent_pool_profile in instance.agent_pool_profiles:
            if vmas_cluster:
                raise CLIError('This cluster is not using VirtualMachineScaleSets. Node image upgrade only operation '
                               'can only be applied on VirtualMachineScaleSets cluster.')
            agent_pool_client = cf_agent_pools(cmd.cli_ctx)
            _upgrade_single_nodepool_image_version(True, agent_pool_client,
                                                   resource_group_name, name, agent_pool_profile.name)
        mc = client.get(resource_group_name, name)
        return _remove_nulls([mc])[0]

    if instance.kubernetes_version == kubernetes_version:
        if instance.provisioning_state == "Succeeded":
            logger.warning("The cluster is already on version %s and is not in a failed state. No operations "
                           "will occur when upgrading to the same version if the cluster is not in a failed state.",
                           instance.kubernetes_version)
        elif instance.provisioning_state == "Failed":
            logger.warning("Cluster currently in failed state. Proceeding with upgrade to existing version %s to "
                           "attempt resolution of failed cluster state.", instance.kubernetes_version)

    upgrade_all = False
    instance.kubernetes_version = kubernetes_version

    # for legacy clusters, we always upgrade node pools with CCP.
    if instance.max_agent_pools < 8 or vmas_cluster:
        if control_plane_only:
            msg = ("Legacy clusters do not support control plane only upgrade. All node pools will be "
                   "upgraded to {} as well. Continue?").format(instance.kubernetes_version)
            if not yes and not prompt_y_n(msg, default="n"):
                return None
        upgrade_all = True
    else:
        if not control_plane_only:
            msg = ("Since control-plane-only argument is not specified, this will upgrade the control plane "
                   "AND all nodepools to version {}. Continue?").format(instance.kubernetes_version)
            if not yes and not prompt_y_n(msg, default="n"):
                return None
            upgrade_all = True
        else:
            msg = ("Since control-plane-only argument is specified, this will upgrade only the control plane to {}. "
                   "Node pool will not change. Continue?").format(instance.kubernetes_version)
            if not yes and not prompt_y_n(msg, default="n"):
                return None

    if upgrade_all:
        for agent_profile in instance.agent_pool_profiles:
            agent_profile.orchestrator_version = kubernetes_version
            agent_profile.creation_data = None

    # null out the SP and AAD profile because otherwise validation complains
    instance.service_principal_profile = None
    instance.aad_profile = None

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, name, instance)


def _upgrade_single_nodepool_image_version(no_wait, client, resource_group_name, cluster_name, nodepool_name,
                                           snapshot_id=None):
    headers = {}
    if snapshot_id:
        headers["AKSSnapshotId"] = snapshot_id

    return sdk_no_wait(
        no_wait,
        client.begin_upgrade_node_image_version,
        resource_group_name,
        cluster_name,
        nodepool_name,
        headers=headers)


def aks_runcommand(cmd, client, resource_group_name, name, command_string="", command_files=None):
    colorama.init()

    mc = client.get(resource_group_name, name)

    if not command_string:
        raise ValidationError('Command cannot be empty.')
    RunCommandRequest = cmd.get_models('RunCommandRequest', resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                       operation_group='managed_clusters')
    request_payload = RunCommandRequest(command=command_string)
    request_payload.context = _get_command_context(command_files)

    # if this cluster have Azure AD enabled, we should pass user token.
    # so the command execution also using current user identity.
    # here we aquire token for AKS managed server AppID (same id for all cloud)
    if mc.aad_profile is not None and mc.aad_profile.managed:
        request_payload.cluster_token = _get_dataplane_aad_token(
            cmd.cli_ctx, "6dae42f8-4368-4678-94ff-3960e28e3630")

    commandResultFuture = client.begin_run_command(
        resource_group_name, name, request_payload, polling_interval=5, retry_total=0)

    return _print_command_result(cmd.cli_ctx, commandResultFuture.result(300))


def aks_command_result(cmd, client, resource_group_name, name, command_id=""):
    if not command_id:
        raise ValidationError('CommandID cannot be empty.')

    commandResult = client.get_command_result(
        resource_group_name, name, command_id)
    return _print_command_result(cmd.cli_ctx, commandResult)


def _print_command_result(cli_ctx, commandResult):
    # cli_ctx.data['safe_params'] contains list of parameter name user typed in, without value.
    # cli core also use this calculate ParameterSetName header for all http request from cli.
    if (cli_ctx.data['safe_params'] is None or
        "-o" in cli_ctx.data['safe_params'] or
            "--output" in cli_ctx.data['safe_params']):
        # user specified output format, honor their choice, return object to render pipeline
        return commandResult

    # user didn't specified any format, we can customize the print for best experience
    if commandResult.provisioning_state == "Succeeded":
        # succeed, print exitcode, and logs
        print(
            f"{colorama.Fore.GREEN}command started at {commandResult.started_at}, "
            f"finished at {commandResult.finished_at} "
            f"with exitcode={commandResult.exit_code}{colorama.Style.RESET_ALL}")
        print(commandResult.logs)
        return

    if commandResult.provisioning_state == "Failed":
        # failed, print reason in error
        print(
            f"{colorama.Fore.RED}command failed with reason: {commandResult.reason}{colorama.Style.RESET_ALL}")
        return

    # *-ing state
    print(f"{colorama.Fore.BLUE}command is in : {commandResult.provisioning_state} state{colorama.Style.RESET_ALL}")
    return None


def _get_command_context(command_files):
    if not command_files:
        return ""

    filesToAttach = {}
    # . means to attach current folder, cannot combine more files. (at least for now)
    if len(command_files) == 1 and command_files[0] == ".":
        # current folder
        cwd = os.getcwd()
        for filefolder, _, files in os.walk(cwd):
            for file in files:
                # retain folder structure
                rel = os.path.relpath(filefolder, cwd)
                filesToAttach[os.path.join(
                    filefolder, file)] = os.path.join(rel, file)
    else:
        for file in command_files:
            if file == ".":
                raise ValidationError(
                    ". is used to attach current folder, not expecting other attachements.")
            if os.path.isfile(file):
                # for individual attached file, flatten them to same folder
                filesToAttach[file] = os.path.basename(file)
            else:
                raise ValidationError(
                    f"{file} is not valid file, or not accessable.")

    if len(filesToAttach) < 1:
        logger.debug("no files to attach!")
        return ""

    zipStream = io.BytesIO()
    zipFile = zipfile.ZipFile(zipStream, "w")
    for _, (osfile, zipEntry) in enumerate(filesToAttach.items()):
        zipFile.write(osfile, zipEntry)
    # zipFile.printdir() // use this to debug
    zipFile.close()

    return str(base64.encodebytes(zipStream.getbuffer()), "utf-8")


def _get_dataplane_aad_token(cli_ctx, serverAppId):
    # this function is mostly copied from keyvault cli
    return Profile(cli_ctx=cli_ctx).get_raw_token(resource=serverAppId)[0][2].get('accessToken')


DEV_SPACES_EXTENSION_NAME = 'dev-spaces'
DEV_SPACES_EXTENSION_MODULE = 'azext_dev_spaces.custom'


def aks_use_dev_spaces(cmd, client, name, resource_group_name, update=False, space_name=None,
                       endpoint_type='Public', prompt=False):
    """
    Use Azure Dev Spaces with a managed Kubernetes cluster.

    :param name: Name of the managed cluster.
    :type name: String
    :param resource_group_name: Name of resource group. You can configure the default group. \
    Using 'az configure --defaults group=<name>'.
    :type resource_group_name: String
    :param update: Update to the latest Azure Dev Spaces client components.
    :type update: bool
    :param space_name: Name of the new or existing dev space to select. Defaults to an \
    interactive selection experience.
    :type space_name: String
    :param endpoint_type: The endpoint type to be used for a Azure Dev Spaces controller. \
    See https://aka.ms/azds-networking for more information.
    :type endpoint_type: String
    :param prompt: Do not prompt for confirmation. Requires --space.
    :type prompt: bool
    """

    if _get_or_add_extension(cmd, DEV_SPACES_EXTENSION_NAME, DEV_SPACES_EXTENSION_MODULE, update):
        azext_custom = _get_azext_module(
            DEV_SPACES_EXTENSION_NAME, DEV_SPACES_EXTENSION_MODULE)
        try:
            azext_custom.ads_use_dev_spaces(
                name, resource_group_name, update, space_name, endpoint_type, prompt)
        except TypeError:
            raise CLIError(
                "Use '--update' option to get the latest Azure Dev Spaces client components.")
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

    if _get_or_add_extension(cmd, DEV_SPACES_EXTENSION_NAME, DEV_SPACES_EXTENSION_MODULE):
        azext_custom = _get_azext_module(
            DEV_SPACES_EXTENSION_NAME, DEV_SPACES_EXTENSION_MODULE)
        try:
            azext_custom.ads_remove_dev_spaces(
                name, resource_group_name, prompt)
        except AttributeError as ae:
            raise CLIError(ae)


def aks_rotate_certs(cmd, client, resource_group_name, name, no_wait=True):
    return sdk_no_wait(no_wait, client.begin_rotate_cluster_certificates, resource_group_name, name)


def _update_addons(cmd, instance, subscription_id, resource_group_name, name, addons, enable,
                   workspace_resource_id=None,
                   subnet_name=None,
                   appgw_name=None,
                   appgw_subnet_cidr=None,
                   appgw_id=None,
                   appgw_subnet_id=None,
                   appgw_watch_namespace=None,
                   enable_sgxquotehelper=False,
                   enable_secret_rotation=False,
                   disable_secret_rotation=False,
                   rotation_poll_interval=None,
                   no_wait=False):
    ManagedClusterAddonProfile = cmd.get_models('ManagedClusterAddonProfile',
                                                resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                                operation_group='managed_clusters')
    # parse the comma-separated addons argument
    addon_args = addons.split(',')

    addon_profiles = instance.addon_profiles or {}

    os_type = 'Linux'

    # for each addons argument
    for addon_arg in addon_args:
        if addon_arg not in ADDONS:
            raise CLIError("Invalid addon name: {}.".format(addon_arg))
        addon = ADDONS[addon_arg]
        if addon == CONST_VIRTUAL_NODE_ADDON_NAME:
            # only linux is supported for now, in the future this will be a user flag
            addon += os_type

        # honor addon names defined in Azure CLI
        for key in list(addon_profiles):
            if key.lower() == addon.lower() and key != addon:
                addon_profiles[addon] = addon_profiles.pop(key)

        if enable:
            # add new addons or update existing ones and enable them
            addon_profile = addon_profiles.get(
                addon, ManagedClusterAddonProfile(enabled=False))
            # special config handling for certain addons
            if addon == CONST_MONITORING_ADDON_NAME:
                if addon_profile.enabled:
                    raise CLIError('The monitoring addon is already enabled for this managed cluster.\n'
                                   'To change monitoring configuration, run "az aks disable-addons -a monitoring"'
                                   'before enabling it again.')
                if not workspace_resource_id:
                    workspace_resource_id = ensure_default_log_analytics_workspace_for_monitoring(
                        cmd,
                        subscription_id,
                        resource_group_name)
                workspace_resource_id = workspace_resource_id.strip()
                if not workspace_resource_id.startswith('/'):
                    workspace_resource_id = '/' + workspace_resource_id
                if workspace_resource_id.endswith('/'):
                    workspace_resource_id = workspace_resource_id.rstrip('/')
                addon_profile.config = {
                    CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID: workspace_resource_id}
            elif addon == (CONST_VIRTUAL_NODE_ADDON_NAME + os_type):
                if addon_profile.enabled:
                    raise CLIError('The virtual-node addon is already enabled for this managed cluster.\n'
                                   'To change virtual-node configuration, run '
                                   '"az aks disable-addons -a virtual-node -g {resource_group_name}" '
                                   'before enabling it again.')
                if not subnet_name:
                    raise CLIError(
                        'The aci-connector addon requires setting a subnet name.')
                addon_profile.config = {
                    CONST_VIRTUAL_NODE_SUBNET_NAME: subnet_name}
            elif addon == CONST_INGRESS_APPGW_ADDON_NAME:
                if addon_profile.enabled:
                    raise CLIError('The ingress-appgw addon is already enabled for this managed cluster.\n'
                                   'To change ingress-appgw configuration, run '
                                   f'"az aks disable-addons -a ingress-appgw -n {name} -g {resource_group_name}" '
                                   'before enabling it again.')
                addon_profile = ManagedClusterAddonProfile(
                    enabled=True, config={})
                if appgw_name is not None:
                    addon_profile.config[CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME] = appgw_name
                if appgw_subnet_cidr is not None:
                    addon_profile.config[CONST_INGRESS_APPGW_SUBNET_CIDR] = appgw_subnet_cidr
                if appgw_id is not None:
                    addon_profile.config[CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID] = appgw_id
                if appgw_subnet_id is not None:
                    addon_profile.config[CONST_INGRESS_APPGW_SUBNET_ID] = appgw_subnet_id
                if appgw_watch_namespace is not None:
                    addon_profile.config[CONST_INGRESS_APPGW_WATCH_NAMESPACE] = appgw_watch_namespace
            elif addon == CONST_CONFCOM_ADDON_NAME:
                if addon_profile.enabled:
                    raise ValidationError('The confcom addon is already enabled for this managed cluster.',
                                          recommendation='To change confcom configuration, run '
                                          f'"az aks disable-addons -a confcom -n {name} -g {resource_group_name}" '
                                          'before enabling it again.')
                addon_profile = ManagedClusterAddonProfile(
                    enabled=True, config={CONST_ACC_SGX_QUOTE_HELPER_ENABLED: "false"})
                if enable_sgxquotehelper:
                    addon_profile.config[CONST_ACC_SGX_QUOTE_HELPER_ENABLED] = "true"
            elif addon == CONST_OPEN_SERVICE_MESH_ADDON_NAME:
                if addon_profile.enabled:
                    raise AzureInternalError(
                        'The open-service-mesh addon is already enabled for this managed '
                        'cluster.\n To change open-service-mesh configuration, run '
                        '"az aks disable-addons -a open-service-mesh -n {} -g {}" '
                        'before enabling it again.'
                        .format(name, resource_group_name))
                addon_profile = ManagedClusterAddonProfile(enabled=True, config={})
            elif addon == CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME:
                if addon_profile.enabled:
                    raise ArgumentUsageError(
                        'The azure-keyvault-secrets-provider addon is already enabled for this managed cluster.\n'
                        'To change azure-keyvault-secrets-provider configuration, run '
                        f'"az aks disable-addons -a azure-keyvault-secrets-provider -n {name} -g {resource_group_name}" '  # pylint: disable=line-too-long
                        'before enabling it again.')
                addon_profile = ManagedClusterAddonProfile(
                    enabled=True, config={CONST_SECRET_ROTATION_ENABLED: "false", CONST_ROTATION_POLL_INTERVAL: "2m"})
                if enable_secret_rotation:
                    addon_profile.config[CONST_SECRET_ROTATION_ENABLED] = "true"
                if disable_secret_rotation:
                    addon_profile.config[CONST_SECRET_ROTATION_ENABLED] = "false"
                if rotation_poll_interval is not None:
                    addon_profile.config[CONST_ROTATION_POLL_INTERVAL] = rotation_poll_interval
                addon_profiles[CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME] = addon_profile
            addon_profiles[addon] = addon_profile
        else:
            if addon not in addon_profiles:
                if addon == CONST_KUBE_DASHBOARD_ADDON_NAME:
                    addon_profiles[addon] = ManagedClusterAddonProfile(
                        enabled=False)
                else:
                    raise CLIError(
                        "The addon {} is not installed.".format(addon))
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
        from azure.cli.core.extension.operations import add_extension_to_path
        add_extension_to_path(extension_name)
        # Import the extension module
        from importlib import import_module
        azext_custom = import_module(module_name)
        return azext_custom
    except ImportError as ie:
        raise CLIError(ie)


def _handle_addons_args(cmd, addons_str, subscription_id, resource_group_name, addon_profiles=None,
                        workspace_resource_id=None,
                        aci_subnet_name=None,
                        vnet_subnet_id=None,
                        appgw_name=None,
                        appgw_subnet_cidr=None,
                        appgw_id=None,
                        appgw_subnet_id=None,
                        appgw_watch_namespace=None,
                        enable_sgxquotehelper=False,
                        enable_secret_rotation=False,
                        rotation_poll_interval=None,):
    ManagedClusterAddonProfile = cmd.get_models('ManagedClusterAddonProfile',
                                                resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                                operation_group='managed_clusters')
    if not addon_profiles:
        addon_profiles = {}
    addons = addons_str.split(',') if addons_str else []
    if 'http_application_routing' in addons:
        addon_profiles[CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME] = ManagedClusterAddonProfile(
            enabled=True)
        addons.remove('http_application_routing')
    if 'kube-dashboard' in addons:
        addon_profiles[CONST_KUBE_DASHBOARD_ADDON_NAME] = ManagedClusterAddonProfile(
            enabled=True)
        addons.remove('kube-dashboard')
    # TODO: can we help the user find a workspace resource ID?
    if 'monitoring' in addons:
        if not workspace_resource_id:
            # use default workspace if exists else create default workspace
            workspace_resource_id = ensure_default_log_analytics_workspace_for_monitoring(
                cmd, subscription_id, resource_group_name)

        workspace_resource_id = workspace_resource_id.strip()
        if not workspace_resource_id.startswith('/'):
            workspace_resource_id = '/' + workspace_resource_id
        if workspace_resource_id.endswith('/'):
            workspace_resource_id = workspace_resource_id.rstrip('/')
        addon_profiles[CONST_MONITORING_ADDON_NAME] = ManagedClusterAddonProfile(
            enabled=True, config={CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID: workspace_resource_id})
        addons.remove('monitoring')
    # error out if '--enable-addons=monitoring' isn't set but workspace_resource_id is
    elif workspace_resource_id:
        raise CLIError(
            '"--workspace-resource-id" requires "--enable-addons monitoring".')
    if 'azure-policy' in addons:
        addon_profiles[CONST_AZURE_POLICY_ADDON_NAME] = ManagedClusterAddonProfile(
            enabled=True)
        addons.remove('azure-policy')
    if 'virtual-node' in addons:
        if not aci_subnet_name or not vnet_subnet_id:
            raise CLIError(
                '"--enable-addons virtual-node" requires "--aci-subnet-name" and "--vnet-subnet-id".')
        # TODO: how about aciConnectorwindows, what is its addon name?
        os_type = 'Linux'
        addon_profiles[CONST_VIRTUAL_NODE_ADDON_NAME + os_type] = ManagedClusterAddonProfile(
            enabled=True,
            config={CONST_VIRTUAL_NODE_SUBNET_NAME: aci_subnet_name}
        )
        addons.remove('virtual-node')
    if 'ingress-appgw' in addons:
        addon_profile = ManagedClusterAddonProfile(enabled=True, config={})
        if appgw_name is not None:
            addon_profile.config[CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME] = appgw_name
        if appgw_subnet_cidr is not None:
            addon_profile.config[CONST_INGRESS_APPGW_SUBNET_CIDR] = appgw_subnet_cidr
        if appgw_id is not None:
            addon_profile.config[CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID] = appgw_id
        if appgw_subnet_id is not None:
            addon_profile.config[CONST_INGRESS_APPGW_SUBNET_ID] = appgw_subnet_id
        if appgw_watch_namespace is not None:
            addon_profile.config[CONST_INGRESS_APPGW_WATCH_NAMESPACE] = appgw_watch_namespace
        addon_profiles[CONST_INGRESS_APPGW_ADDON_NAME] = addon_profile
        addons.remove('ingress-appgw')
    if 'confcom' in addons:
        addon_profile = ManagedClusterAddonProfile(
            enabled=True, config={CONST_ACC_SGX_QUOTE_HELPER_ENABLED: "false"})
        if enable_sgxquotehelper:
            addon_profile.config[CONST_ACC_SGX_QUOTE_HELPER_ENABLED] = "true"
        addon_profiles[CONST_CONFCOM_ADDON_NAME] = addon_profile
        addons.remove('confcom')
    if 'open-service-mesh' in addons:
        addon_profile = ManagedClusterAddonProfile(enabled=True, config={})
        addon_profiles[CONST_OPEN_SERVICE_MESH_ADDON_NAME] = addon_profile
        addons.remove('open-service-mesh')
    if 'azure-keyvault-secrets-provider' in addons:
        addon_profile = ManagedClusterAddonProfile(
            enabled=True, config={CONST_SECRET_ROTATION_ENABLED: "false", CONST_ROTATION_POLL_INTERVAL: "2m"}
        )
        if enable_secret_rotation:
            addon_profile.config[CONST_SECRET_ROTATION_ENABLED] = "true"
        if rotation_poll_interval is not None:
            addon_profile.config[CONST_ROTATION_POLL_INTERVAL] = rotation_poll_interval
        addon_profiles[CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME] = addon_profile
        addons.remove('azure-keyvault-secrets-provider')
    # error out if any (unrecognized) addons remain
    if addons:
        raise CLIError('"{}" {} not recognized by the --enable-addons argument.'.format(
            ",".join(addons), "are" if len(addons) > 1 else "is"))
    return addon_profiles


def _install_dev_spaces_extension(cmd, extension_name):
    try:
        from azure.cli.core.extension import operations
        operations.add_extension(cmd=cmd, extension_name=extension_name)
    except Exception:  # nopa pylint: disable=broad-except
        return False
    return True


def _update_dev_spaces_extension(cmd, extension_name, extension_module):
    from azure.cli.core.extension import ExtensionNotInstalledException
    try:
        from azure.cli.core.extension import operations
        operations.update_extension(cmd=cmd, extension_name=extension_name)
        operations.reload_extension(extension_name=extension_name)
    except CLIError as err:
        logger.info(err)
    except ExtensionNotInstalledException as err:
        logger.debug(err)
        return False
    except ModuleNotFoundError as err:
        logger.debug(err)
        logger.error(
            "Error occurred attempting to load the extension module. Use --debug for more information.")
        return False
    return True


def _get_or_add_extension(cmd, extension_name, extension_module, update=False):
    from azure.cli.core.extension import (
        ExtensionNotInstalledException, get_extension)
    try:
        get_extension(extension_name)
        if update:
            return _update_dev_spaces_extension(cmd, extension_name, extension_module)
    except ExtensionNotInstalledException:
        return _install_dev_spaces_extension(cmd, extension_name)
    return True


def _ensure_container_insights_for_monitoring(cmd, addon):
    # Workaround for this addon key which has been seen lowercased in the wild.
    for key in list(addon.config):
        if (key.lower() == CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID.lower() and
                key != CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID):
            addon.config[CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID] = addon.config.pop(
                key)

    workspace_resource_id = addon.config[CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID]

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
        raise CLIError(
            'Could not locate resource group in workspace-resource-id URL.')

    # region of workspace can be different from region of RG so find the location of the workspace_resource_id
    resources = cf_resources(cmd.cli_ctx, subscription_id)
    try:
        resource = resources.get_by_id(
            workspace_resource_id, '2015-11-01-preview')
        location = resource.location
    except CloudError as ex:
        raise ex

    unix_time_in_millis = int(
        (datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(0)).total_seconds() * 1000.0)

    solution_deployment_name = 'ContainerInsights-{}'.format(
        unix_time_in_millis)

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
    return _invoke_deployment(cmd, resource_group, deployment_name, template, params,
                              validate=False, no_wait=False, subscription_id=subscription_id)


def _ensure_aks_acr(cmd,
                    assignee,
                    acr_name_or_id,
                    subscription_id,
                    detach=False,
                    is_service_principal=True):
    from msrestazure.tools import is_valid_resource_id, parse_resource_id
    # Check if the ACR exists by resource ID.
    if is_valid_resource_id(acr_name_or_id):
        try:
            parsed_registry = parse_resource_id(acr_name_or_id)
            acr_client = cf_container_registry_service(
                cmd.cli_ctx, subscription_id=parsed_registry['subscription'])
            registry = acr_client.registries.get(
                parsed_registry['resource_group'], parsed_registry['name'])
        except CloudError as ex:
            raise CLIError(ex.message)
        _ensure_aks_acr_role_assignment(
            cmd, assignee, registry.id, detach, is_service_principal)
        return

    # Check if the ACR exists by name accross all resource groups.
    registry_name = acr_name_or_id
    registry_resource = 'Microsoft.ContainerRegistry/registries'
    try:
        registry = get_resource_by_name(
            cmd.cli_ctx, registry_name, registry_resource)
    except CloudError as ex:
        if 'was not found' in ex.message:
            raise CLIError(
                "ACR {} not found. Have you provided the right ACR name?".format(registry_name))
        raise CLIError(ex.message)
    _ensure_aks_acr_role_assignment(cmd, assignee, registry.id, detach, is_service_principal)
    return


def aks_agentpool_show(cmd, client, resource_group_name, cluster_name, nodepool_name):
    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    return instance


def aks_agentpool_list(cmd, client, resource_group_name, cluster_name):
    return client.list(resource_group_name, cluster_name)


def aks_agentpool_add(cmd, client, resource_group_name, cluster_name, nodepool_name,
                      kubernetes_version=None,
                      zones=None,
                      enable_node_public_ip=False,
                      node_public_ip_prefix_id=None,
                      node_vm_size=None,
                      node_osdisk_type=None,
                      node_osdisk_size=0,
                      node_count=3,
                      vnet_subnet_id=None,
                      ppg=None,
                      max_pods=0,
                      os_type=None,
                      os_sku=None,
                      min_count=None,
                      max_count=None,
                      enable_cluster_autoscaler=False,
                      scale_down_mode=CONST_SCALE_DOWN_MODE_DELETE,
                      node_taints=None,
                      priority=CONST_SCALE_SET_PRIORITY_REGULAR,
                      eviction_policy=CONST_SPOT_EVICTION_POLICY_DELETE,
                      spot_max_price=float('nan'),
                      tags=None,
                      labels=None,
                      max_surge=None,
                      mode="User",
                      enable_encryption_at_host=False,
                      enable_ultra_ssd=False,
                      enable_fips_image=False,
                      snapshot_id=None,
                      no_wait=False,
                      aks_custom_headers=None):
    AgentPool = cmd.get_models('AgentPool',
                               resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                               operation_group='agent_pools')
    AgentPoolUpgradeSettings = cmd.get_models('AgentPoolUpgradeSettings',
                                              resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                              operation_group='agent_pools')
    instances = client.list(resource_group_name, cluster_name)
    for agentpool_profile in instances:
        if agentpool_profile.name == nodepool_name:
            raise CLIError("Node pool {} already exists, please try a different name, "
                           "use 'aks nodepool list' to get current list of node pool".format(nodepool_name))

    upgradeSettings = AgentPoolUpgradeSettings()
    taints_array = []
    creationData = None
    # load model CreationData
    from azure.cli.command_modules.acs.decorator import AKSModels
    CreationData = AKSModels(cmd, ResourceType.MGMT_CONTAINERSERVICE).CreationData
    if snapshot_id:
        snapshot = _get_snapshot(cmd.cli_ctx, snapshot_id)
        if not kubernetes_version:
            kubernetes_version = snapshot.kubernetes_version
        if not os_type:
            os_type = snapshot.os_type
        if not os_sku:
            os_sku = snapshot.os_sku
        if not node_vm_size:
            node_vm_size = snapshot.vm_size

        creationData = CreationData(
            source_resource_id=snapshot_id
        )

    if not os_type:
        os_type = "Linux"

    if node_taints is not None:
        for taint in node_taints.split(','):
            try:
                taint = taint.strip()
                taints_array.append(taint)
            except ValueError:
                raise CLIError(
                    'Taint does not match allowed values. Expect value such as "special=true:NoSchedule".')

    if node_vm_size is None:
        if os_type.lower() == "windows":
            node_vm_size = "Standard_D2s_v3"
        else:
            node_vm_size = "Standard_DS2_v2"

    if max_surge:
        upgradeSettings.max_surge = max_surge

    agent_pool = AgentPool(
        name=nodepool_name,
        tags=tags,
        node_labels=labels,
        count=int(node_count),
        vm_size=node_vm_size,
        os_type=os_type,
        os_sku=os_sku,
        vnet_subnet_id=vnet_subnet_id,
        proximity_placement_group_id=ppg,
        agent_pool_type="VirtualMachineScaleSets",
        max_pods=int(max_pods) if max_pods else None,
        orchestrator_version=kubernetes_version,
        availability_zones=zones,
        scale_set_priority=priority,
        scale_down_mode=scale_down_mode,
        enable_node_public_ip=enable_node_public_ip,
        node_public_ip_prefix_id=node_public_ip_prefix_id,
        node_taints=taints_array,
        upgrade_settings=upgradeSettings,
        enable_encryption_at_host=enable_encryption_at_host,
        enable_ultra_ssd=enable_ultra_ssd,
        mode=mode,
        enable_fips=enable_fips_image,
        creation_data=creationData
    )

    if priority == CONST_SCALE_SET_PRIORITY_SPOT:
        agent_pool.scale_set_eviction_policy = eviction_policy
        if isnan(spot_max_price):
            spot_max_price = -1
        agent_pool.spot_max_price = spot_max_price

    _check_cluster_autoscaler_flag(
        enable_cluster_autoscaler, min_count, max_count, node_count, agent_pool)

    if node_osdisk_size:
        agent_pool.os_disk_size_gb = int(node_osdisk_size)

    if node_osdisk_type:
        agent_pool.os_disk_type = node_osdisk_type

    # custom headers
    aks_custom_headers = extract_comma_separated_string(
        aks_custom_headers,
        enable_strip=True,
        extract_kv=True,
        default_value={},
    )

    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        nodepool_name,
        agent_pool,
        headers=aks_custom_headers,
    )


def aks_agentpool_scale(cmd, client, resource_group_name, cluster_name,
                        nodepool_name,
                        node_count=3,
                        no_wait=False):
    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    new_node_count = int(node_count)
    if instance.enable_auto_scaling:
        raise CLIError("Cannot scale cluster autoscaler enabled node pool.")
    if new_node_count == instance.count:
        raise CLIError(
            "The new node count is the same as the current node count.")
    instance.count = new_node_count  # pylint: disable=no-member
    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        nodepool_name,
        instance,
    )


def aks_agentpool_upgrade(cmd, client, resource_group_name, cluster_name,
                          nodepool_name,
                          kubernetes_version='',
                          node_image_only=False,
                          max_surge=None,
                          no_wait=False,
                          aks_custom_headers=None,
                          snapshot_id=None):
    AgentPoolUpgradeSettings = cmd.get_models('AgentPoolUpgradeSettings', operation_group='agent_pools')
    if kubernetes_version != '' and node_image_only:
        raise CLIError(
            'Conflicting flags. Upgrading the Kubernetes version will also '
            'upgrade node image version. If you only want to upgrade the '
            'node version please use the "--node-image-only" option only.'
        )

    # Note: we exclude this option because node image upgrade can't accept nodepool put fields like max surge
    if max_surge and node_image_only:
        raise MutuallyExclusiveArgumentError(
            'Conflicting flags. Unable to specify max-surge with node-image-only.'
            'If you want to use max-surge with a node image upgrade, please first '
            'update max-surge using "az aks nodepool update --max-surge".'
        )

    if node_image_only:
        return _upgrade_single_nodepool_image_version(no_wait,
                                                      client,
                                                      resource_group_name,
                                                      cluster_name,
                                                      nodepool_name,
                                                      snapshot_id)

    # load model CreationData
    from azure.cli.command_modules.acs.decorator import AKSModels
    CreationData = AKSModels(cmd, ResourceType.MGMT_CONTAINERSERVICE).CreationData

    creationData = None
    if snapshot_id:
        snapshot = _get_snapshot(cmd.cli_ctx, snapshot_id)
        if not kubernetes_version and not node_image_only:
            kubernetes_version = snapshot.kubernetes_version

        creationData = CreationData(
            source_resource_id=snapshot_id
        )

    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    instance.orchestrator_version = kubernetes_version
    instance.creation_data = creationData

    if not instance.upgrade_settings:
        instance.upgrade_settings = AgentPoolUpgradeSettings()

    if max_surge:
        instance.upgrade_settings.max_surge = max_surge

    # custom headers
    aks_custom_headers = extract_comma_separated_string(
        aks_custom_headers,
        enable_strip=True,
        extract_kv=True,
        default_value={},
    )

    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        nodepool_name,
        instance,
        headers=aks_custom_headers,
    )


# pylint: disable=too-many-boolean-expressions
def aks_agentpool_update(cmd, client, resource_group_name, cluster_name, nodepool_name,
                         enable_cluster_autoscaler=False,
                         disable_cluster_autoscaler=False,
                         update_cluster_autoscaler=False,
                         scale_down_mode=None,
                         min_count=None, max_count=None,
                         tags=None,
                         max_surge=None,
                         mode=None,
                         labels=None,
                         node_taints=None,
                         no_wait=False,
                         aks_custom_headers=None):
    AgentPoolUpgradeSettings = cmd.get_models('AgentPoolUpgradeSettings',
                                              resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                              operation_group='agent_pools')
    update_autoscaler = enable_cluster_autoscaler + \
        disable_cluster_autoscaler + update_cluster_autoscaler

    if update_autoscaler > 1:
        raise CLIError('Please specify one of "--enable-cluster-autoscaler" or '
                       '"--disable-cluster-autoscaler" or '
                       '"--update-cluster-autoscaler"')

    if (update_autoscaler == 0 and not tags and not scale_down_mode and not mode and not max_surge and
            labels is None and node_taints is None):
        raise CLIError('Please specify one or more of "--enable-cluster-autoscaler" or '
                       '"--disable-cluster-autoscaler" or '
                       '"--update-cluster-autoscaler" or '
                       '"--tags" or "--mode" or "--max-surge" or "--scale-down-mode or '
                       '"--labels"or "--node-taints"')

    instance = client.get(resource_group_name, cluster_name, nodepool_name)

    _validate_autoscaler_update_counts(min_count, max_count, enable_cluster_autoscaler or
                                       update_cluster_autoscaler)

    if enable_cluster_autoscaler:
        if instance.enable_auto_scaling:
            logger.warning('Autoscaler is already enabled for this node pool.\n'
                           'Please run "az aks nodepool update --update-cluster-autoscaler" '
                           'if you want to update min-count or max-count.')
            return None
        instance.min_count = int(min_count)
        instance.max_count = int(max_count)
        instance.enable_auto_scaling = True

    if update_cluster_autoscaler:
        if not instance.enable_auto_scaling:
            raise CLIError('Autoscaler is not enabled for this node pool.\n'
                           'Run "az aks nodepool update --enable-cluster-autoscaler" '
                           'to enable cluster with min-count and max-count.')
        instance.min_count = int(min_count)
        instance.max_count = int(max_count)

    if not instance.upgrade_settings:
        instance.upgrade_settings = AgentPoolUpgradeSettings()

    if max_surge:
        instance.upgrade_settings.max_surge = max_surge

    if disable_cluster_autoscaler:
        if not instance.enable_auto_scaling:
            logger.warning(
                'Autoscaler is already disabled for this node pool.')
            return None
        instance.enable_auto_scaling = False
        instance.min_count = None
        instance.max_count = None

    instance.tags = tags

    if scale_down_mode is not None:
        instance.scale_down_mode = scale_down_mode

    if mode is not None:
        instance.mode = mode

    if labels is not None:
        instance.node_labels = labels

    if node_taints is not None:
        taints_array = []
        if node_taints != '':
            for taint in node_taints.split(','):
                try:
                    taint = taint.strip()
                    taints_array.append(taint)
                except ValueError:
                    raise InvalidArgumentValueError(
                        'Taint does not match allowed values. Expect value such as "special=true:NoSchedule".')
        instance.node_taints = taints_array

    # custom headers
    aks_custom_headers = extract_comma_separated_string(
        aks_custom_headers,
        enable_strip=True,
        extract_kv=True,
        default_value={},
    )

    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        nodepool_name,
        instance,
        headers=aks_custom_headers,
    )


def aks_agentpool_delete(cmd, client, resource_group_name, cluster_name,
                         nodepool_name,
                         no_wait=False):
    agentpool_exists = False
    instances = client.list(resource_group_name, cluster_name)
    for agentpool_profile in instances:
        if agentpool_profile.name.lower() == nodepool_name.lower():
            agentpool_exists = True
            break

    if not agentpool_exists:
        raise CLIError("Node pool {} doesnt exist, "
                       "use 'aks nodepool list' to get current node pool list".format(nodepool_name))

    return sdk_no_wait(no_wait, client.begin_delete, resource_group_name, cluster_name, nodepool_name)


def aks_agentpool_get_upgrade_profile(cmd, client, resource_group_name, cluster_name, nodepool_name):
    return client.get_upgrade_profile(resource_group_name, cluster_name, nodepool_name)


def _ensure_aks_acr_role_assignment(cmd,
                                    assignee,
                                    registry_id,
                                    detach=False,
                                    is_service_principal=True):
    if detach:
        if not _delete_role_assignments(cmd.cli_ctx,
                                        'acrpull',
                                        assignee,
                                        scope=registry_id,
                                        is_service_principal=is_service_principal):
            raise CLIError('Could not delete role assignments for ACR. '
                           'Are you an Owner on this subscription?')
        return

    if not _add_role_assignment(cmd,
                                'acrpull',
                                assignee,
                                scope=registry_id,
                                is_service_principal=is_service_principal):
        raise CLIError('Could not create a role assignment for ACR. '
                       'Are you an Owner on this subscription?')
    return


def _ensure_aks_service_principal(cli_ctx,
                                  service_principal=None,
                                  client_secret=None,
                                  subscription_id=None,
                                  dns_name_prefix=None,
                                  fqdn_subdomain=None,
                                  location=None,
                                  name=None):
    aad_session_key = None
    # TODO: This really needs to be unit tested.
    rbac_client = get_graph_rbac_management_client(cli_ctx)
    if not service_principal:
        # --service-principal not specified, make one.
        if not client_secret:
            client_secret = _create_client_secret()
        salt = binascii.b2a_hex(os.urandom(3)).decode('utf-8')
        if dns_name_prefix:
            url = 'https://{}.{}.{}.cloudapp.azure.com'.format(
                salt, dns_name_prefix, location)
        else:
            url = 'https://{}.{}.{}.cloudapp.azure.com'.format(
                salt, fqdn_subdomain, location)

        service_principal, aad_session_key = _build_service_principal(
            rbac_client, cli_ctx, name, url, client_secret)
        if not service_principal:
            raise CLIError('Could not create a service principal with the right permissions. '
                           'Are you an Owner on this project?')
        logger.info('Created a service principal: %s', service_principal)
        # We don't need to add role assignment for this created SPN
    else:
        # --service-principal specfied, validate --client-secret was too
        if not client_secret:
            raise CLIError(
                '--client-secret is required if --service-principal is specified')
    return {
        'client_secret': client_secret,
        'service_principal': service_principal,
        'aad_session_key': aad_session_key,
    }


def _ensure_osa_aad(cmd,
                    cli_ctx,
                    aad_client_app_id=None,
                    aad_client_app_secret=None,
                    aad_tenant_id=None,
                    identifier=None,
                    name=None, create=False,
                    customer_admin_group_id=None):
    OpenShiftManagedClusterAADIdentityProvider = cmd.get_models('OpenShiftManagedClusterAADIdentityProvider',
                                                                resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                                                operation_group='open_shift_managed_clusters')
    rbac_client = get_graph_rbac_management_client(cli_ctx)
    if create:
        # This reply_url is temporary set since Azure need one to create the AAD.
        app_id_name = 'https://{}'.format(name)
        if not aad_client_app_secret:
            aad_client_app_secret = _create_client_secret()

        # Delegate Sign In and Read User Profile permissions on Windows Azure Active Directory API
        resource_access = ResourceAccess(id="311a71cc-e848-46a1-bdf8-97ff7156d8e6",
                                         additional_properties=None, type="Scope")
        # Read directory permissions on Windows Azure Active Directory API
        directory_access = ResourceAccess(id="5778995a-e1bf-45b8-affa-663a9f3f4d04",
                                          additional_properties=None, type="Role")

        required_osa_aad_access = RequiredResourceAccess(resource_access=[resource_access, directory_access],
                                                         additional_properties=None,
                                                         resource_app_id="00000002-0000-0000-c000-000000000000")

        list_aad_filtered = list(rbac_client.applications.list(filter="identifierUris/any(s:s eq '{}')"
                                                               .format(app_id_name)))
        if list_aad_filtered:
            aad_client_app_id = list_aad_filtered[0].app_id
            # Updating reply_url with the correct FQDN information returned by the RP
            reply_url = 'https://{}/oauth2callback/Azure%20AD'.format(
                identifier)
            update_application(client=rbac_client.applications,
                               object_id=list_aad_filtered[0].object_id,
                               display_name=name,
                               identifier_uris=[app_id_name],
                               reply_urls=[reply_url],
                               homepage=app_id_name,
                               password=aad_client_app_secret,
                               required_resource_accesses=[required_osa_aad_access])
            logger.info('Updated AAD: %s', aad_client_app_id)
        else:
            result, _aad_session_key = create_application(client=rbac_client.applications,
                                                          display_name=name,
                                                          identifier_uris=[
                                                              app_id_name],
                                                          homepage=app_id_name,
                                                          password=aad_client_app_secret,
                                                          required_resource_accesses=[required_osa_aad_access])
            aad_client_app_id = result.app_id
            logger.info('Created an AAD: %s', aad_client_app_id)
        # Get the TenantID
        if aad_tenant_id is None:
            profile = Profile(cli_ctx=cli_ctx)
            _, _, aad_tenant_id = profile.get_login_credentials()
    return OpenShiftManagedClusterAADIdentityProvider(
        client_id=aad_client_app_id,
        secret=aad_client_app_secret,
        tenant_id=aad_tenant_id,
        kind='AADIdentityProvider',
        customer_admin_group_id=customer_admin_group_id)


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
        # --service-principal not specified, make one.
        if not client_secret:
            client_secret = _create_client_secret()
        salt = binascii.b2a_hex(os.urandom(3)).decode('utf-8')
        url = 'https://{}.{}.{}.cloudapp.azure.com'.format(
            salt, dns_name_prefix, location)

        service_principal, _aad_session_key = _build_service_principal(
            rbac_client, cli_ctx, name, url, client_secret)
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
            raise CLIError(
                '--client-secret is required if --service-principal is specified')

    return {
        'client_secret': client_secret,
        'service_principal': service_principal,
    }


def _create_client_secret():
    # Add a special character to satisfy AAD SP secret requirements
    special_char = '$'
    client_secret = binascii.b2a_hex(
        os.urandom(10)).decode('utf-8') + special_char
    return client_secret


def _get_rg_location(ctx, resource_group_name, subscription_id=None):
    groups = cf_resource_groups(ctx, subscription_id=subscription_id)
    # Just do the get, we don't need the result, it will error out if the group doesn't exist.
    rg = groups.get(resource_group_name)
    return rg.location


def _check_cluster_autoscaler_flag(enable_cluster_autoscaler,
                                   min_count,
                                   max_count,
                                   node_count,
                                   agent_pool_profile):
    if enable_cluster_autoscaler:
        if min_count is None or max_count is None:
            raise CLIError(
                'Please specify both min-count and max-count when --enable-cluster-autoscaler enabled')
        if int(min_count) > int(max_count):
            raise CLIError(
                'Value of min-count should be less than or equal to value of max-count')
        if int(node_count) < int(min_count) or int(node_count) > int(max_count):
            raise CLIError(
                'node-count is not in the range of min-count and max-count')
        agent_pool_profile.min_count = int(min_count)
        agent_pool_profile.max_count = int(max_count)
        agent_pool_profile.enable_auto_scaling = True
    else:
        if min_count is not None or max_count is not None:
            raise CLIError(
                'min-count and max-count are required for --enable-cluster-autoscaler, please use the flag')


def _validate_autoscaler_update_counts(min_count, max_count, is_enable_or_update):
    """
    Validates the min, max, and node count when performing an update
    """
    if min_count is None or max_count is None:
        if is_enable_or_update:
            raise CLIError('Please specify both min-count and max-count when --enable-cluster-autoscaler or '
                           '--update-cluster-autoscaler is set.')
    if min_count is not None and max_count is not None:
        if int(min_count) > int(max_count):
            raise CLIError(
                'Value of min-count should be less than or equal to value of max-count.')


def _print_or_merge_credentials(path, kubeconfig, overwrite_existing, context_name):
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
        merge_kubernetes_configurations(
            path, temp_path, overwrite_existing, context_name)
    except yaml.YAMLError as ex:
        logger.warning(
            'Failed to merge credentials to kube config file: %s', ex)
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
    ap_attrs = ['os_disk_size_gb', 'vnet_subnet_id']
    sp_attrs = ['secret']
    for managed_cluster in managed_clusters:
        for attr in attrs:
            if getattr(managed_cluster, attr, None) is None:
                delattr(managed_cluster, attr)
        if managed_cluster.agent_pool_profiles is not None:
            for ap_profile in managed_cluster.agent_pool_profiles:
                for attr in ap_attrs:
                    if getattr(ap_profile, attr, None) is None:
                        delattr(ap_profile, attr)
        for attr in sp_attrs:
            if getattr(managed_cluster.service_principal_profile, attr, None) is None:
                delattr(managed_cluster.service_principal_profile, attr)
    return managed_clusters


def _remove_osa_nulls(managed_clusters):
    """
    Remove some often-empty fields from a list of OpenShift ManagedClusters, so the JSON representation
    doesn't contain distracting null fields.

    This works around a quirk of the SDK for python behavior. These fields are not sent
    by the server, but get recreated by the CLI's own "to_dict" serialization.
    """
    attrs = ['tags', 'plan', 'type', 'id']
    ap_master_attrs = ['name', 'os_type']
    net_attrs = ['peer_vnet_id']
    for managed_cluster in managed_clusters:
        for attr in attrs:
            if hasattr(managed_cluster, attr) and getattr(managed_cluster, attr) is None:
                delattr(managed_cluster, attr)
        for attr in ap_master_attrs:
            if getattr(managed_cluster.master_pool_profile, attr, None) is None:
                delattr(managed_cluster.master_pool_profile, attr)
        for attr in net_attrs:
            if getattr(managed_cluster.network_profile, attr, None) is None:
                delattr(managed_cluster.network_profile, attr)
    return managed_clusters


def _validate_aci_location(norm_location):
    """
    Validate the Azure Container Instance location
    """
    aci_locations = [
        "australiaeast",
        "canadacentral",
        "centralindia",
        "centralus",
        "eastasia",
        "eastus",
        "eastus2",
        "eastus2euap",
        "japaneast",
        "northcentralus",
        "northeurope",
        "southcentralus",
        "southeastasia",
        "southindia",
        "uksouth",
        "westcentralus",
        "westus",
        "westus2",
        "westeurope"
    ]

    if norm_location not in aci_locations:
        raise CLIError('Azure Container Instance is not available at location "{}".'.format(norm_location) +
                       ' The available locations are "{}"'.format(','.join(aci_locations)))


def osa_list(cmd, client, resource_group_name=None):
    if resource_group_name:
        managed_clusters = client.list_by_resource_group(resource_group_name)
    else:
        managed_clusters = client.list()
    return _remove_osa_nulls(list(managed_clusters))


def _format_workspace_id(workspace_id):
    workspace_id = workspace_id.strip()
    if not workspace_id.startswith('/'):
        workspace_id = '/' + workspace_id
    if workspace_id.endswith('/'):
        workspace_id = workspace_id.rstrip('/')
    return workspace_id


def openshift_create(cmd, client, resource_group_name, name,  # pylint: disable=too-many-locals
                     location=None,
                     compute_vm_size="Standard_D4s_v3",
                     compute_count=3,
                     aad_client_app_id=None,
                     aad_client_app_secret=None,
                     aad_tenant_id=None,
                     vnet_prefix="10.0.0.0/8",
                     subnet_prefix="10.0.0.0/24",
                     vnet_peer=None,
                     tags=None,
                     no_wait=False,
                     workspace_id=None,
                     customer_admin_group_id=None):
    OpenShiftManagedClusterAgentPoolProfile = cmd.get_models('OpenShiftManagedClusterAgentPoolProfile',
                                                             resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                                             operation_group='open_shift_managed_clusters')
    OpenShiftAgentPoolProfileRole = cmd.get_models('OpenShiftAgentPoolProfileRole',
                                                   resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                                   operation_group='open_shift_managed_clusters')
    OpenShiftManagedClusterIdentityProvider = cmd.get_models('OpenShiftManagedClusterIdentityProvider',
                                                             resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                                             operation_group='open_shift_managed_clusters')
    OpenShiftManagedCluster = cmd.get_models('OpenShiftManagedCluster',
                                             resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                             operation_group='open_shift_managed_clusters')
    OpenShiftRouterProfile = cmd.get_models('OpenShiftRouterProfile',
                                            resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                            operation_group='open_shift_managed_clusters')
    NetworkProfile = cmd.get_models('NetworkProfile',
                                    resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                    operation_group='open_shift_managed_clusters')
    OpenShiftManagedClusterAuthProfile = cmd.get_models('OpenShiftManagedClusterAuthProfile',
                                                        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                                        operation_group='open_shift_managed_clusters')
    OpenShiftManagedClusterMonitorProfile = cmd.get_models('OpenShiftManagedClusterMonitorProfile',
                                                           resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                                           operation_group='open_shift_managed_clusters')
    logger.warning('Support for the creation of ARO 3.11 clusters ends 30 Nov 2020. Please see aka.ms/aro/4 for information on switching to ARO 4.')  # pylint: disable=line-too-long

    if location is None:
        location = get_rg_location(cmd.cli_ctx, resource_group_name)
    agent_pool_profiles = []
    agent_node_pool_profile = OpenShiftManagedClusterAgentPoolProfile(
        name='compute',  # Must be 12 chars or less before ACS RP adds to it
        count=int(compute_count),
        vm_size=compute_vm_size,
        os_type="Linux",
        role=OpenShiftAgentPoolProfileRole.compute,
        subnet_cidr=subnet_prefix
    )

    agent_infra_pool_profile = OpenShiftManagedClusterAgentPoolProfile(
        name='infra',  # Must be 12 chars or less before ACS RP adds to it
        count=int(3),
        vm_size="Standard_D4s_v3",
        os_type="Linux",
        role=OpenShiftAgentPoolProfileRole.infra,
        subnet_cidr=subnet_prefix
    )

    agent_pool_profiles.append(agent_node_pool_profile)
    agent_pool_profiles.append(agent_infra_pool_profile)

    agent_master_pool_profile = OpenShiftManagedClusterAgentPoolProfile(
        name='master',  # Must be 12 chars or less before ACS RP adds to it
        count=int(3),
        vm_size="Standard_D4s_v3",
        os_type="Linux",
        subnet_cidr=subnet_prefix
    )
    identity_providers = []

    create_aad = False

    # Validating if the cluster is not existing since we are not supporting the AAD rotation on OSA for now
    try:
        client.get(resource_group_name, name)
    except CloudError:
        # Validating if aad_client_app_id aad_client_app_secret aad_tenant_id are set
        if aad_client_app_id is None and aad_client_app_secret is None and aad_tenant_id is None:
            create_aad = True

    osa_aad_identity = _ensure_osa_aad(cmd,
                                       cmd.cli_ctx,
                                       aad_client_app_id=aad_client_app_id,
                                       aad_client_app_secret=aad_client_app_secret,
                                       aad_tenant_id=aad_tenant_id, identifier=None,
                                       name=name, create=create_aad,
                                       customer_admin_group_id=customer_admin_group_id)
    identity_providers.append(
        OpenShiftManagedClusterIdentityProvider(
            name='Azure AD',
            provider=osa_aad_identity
        )
    )
    auth_profile = OpenShiftManagedClusterAuthProfile(
        identity_providers=identity_providers)

    default_router_profile = OpenShiftRouterProfile(name='default')

    if vnet_peer is not None:
        from msrestazure.tools import is_valid_resource_id, resource_id
        if not is_valid_resource_id(vnet_peer):
            vnet_peer = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace='Microsoft.Network', type='virtualNetwork',
                name=vnet_peer
            )
    if workspace_id is not None:
        workspace_id = _format_workspace_id(workspace_id)
        monitor_profile = OpenShiftManagedClusterMonitorProfile(
            enabled=True, workspace_resource_id=workspace_id)  # pylint: disable=line-too-long
    else:
        monitor_profile = None

    network_profile = NetworkProfile(
        vnet_cidr=vnet_prefix, peer_vnet_id=vnet_peer)
    osamc = OpenShiftManagedCluster(
        location=location, tags=tags,
        open_shift_version="v3.11",
        network_profile=network_profile,
        auth_profile=auth_profile,
        agent_pool_profiles=agent_pool_profiles,
        master_pool_profile=agent_master_pool_profile,
        router_profiles=[default_router_profile],
        monitor_profile=monitor_profile)

    try:
        # long_running_operation_timeout=300
        result = sdk_no_wait(no_wait, client.begin_create_or_update,
                             resource_group_name=resource_group_name, resource_name=name, parameters=osamc)
        result = LongRunningOperation(cmd.cli_ctx)(result)
        instance = client.get(resource_group_name, name)
        _ensure_osa_aad(cmd,
                        cmd.cli_ctx,
                        aad_client_app_id=osa_aad_identity.client_id,
                        aad_client_app_secret=osa_aad_identity.secret,
                        aad_tenant_id=osa_aad_identity.tenant_id, identifier=instance.public_hostname,
                        name=name, create=create_aad)
    except CloudError as ex:
        if "The resource type could not be found in the namespace 'Microsoft.ContainerService" in ex.message:
            raise CLIError(
                'Please make sure your subscription is whitelisted to use this service. https://aka.ms/openshift/managed')  # pylint: disable=line-too-long
        if "No registered resource provider found for location" in ex.message:
            raise CLIError(
                'Please make sure your subscription is whitelisted to use this service. https://aka.ms/openshift/managed')  # pylint: disable=line-too-long
        raise ex


def openshift_show(cmd, client, resource_group_name, name):
    logger.warning('The az openshift command is deprecated and has been replaced by az aro for ARO 4 clusters.  See http://aka.ms/aro/4 for information on switching to ARO 4.')  # pylint: disable=line-too-long

    mc = client.get(resource_group_name, name)
    return _remove_osa_nulls([mc])[0]


def openshift_scale(cmd, client, resource_group_name, name, compute_count, no_wait=False):
    logger.warning('The az openshift command is deprecated and has been replaced by az aro for ARO 4 clusters.  See http://aka.ms/aro/4 for information on switching to ARO 4.')  # pylint: disable=line-too-long

    instance = client.get(resource_group_name, name)
    # TODO: change this approach when we support multiple agent pools.
    idx = 0
    for i in range(len(instance.agent_pool_profiles)):
        if instance.agent_pool_profiles[i].name.lower() == "compute":
            idx = i
            break

    instance.agent_pool_profiles[idx].count = int(
        compute_count)  # pylint: disable=no-member

    # null out the AAD profile and add manually the masterAP name because otherwise validation complains
    instance.master_pool_profile.name = "master"
    instance.auth_profile = None

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, name, instance)


def openshift_monitor_enable(cmd, client, resource_group_name, name, workspace_id, no_wait=False):
    OpenShiftManagedClusterMonitorProfile = cmd.get_models('OpenShiftManagedClusterMonitorProfile',
                                                           resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                                           operation_group='open_shift_managed_clusters')
    logger.warning('The az openshift command is deprecated and has been replaced by az aro for ARO 4 clusters.  See http://aka.ms/aro/4 for information on switching to ARO 4.')  # pylint: disable=line-too-long

    instance = client.get(resource_group_name, name)
    workspace_id = _format_workspace_id(workspace_id)
    monitor_profile = OpenShiftManagedClusterMonitorProfile(
        enabled=True, workspace_resource_id=workspace_id)  # pylint: disable=line-too-long
    instance.monitor_profile = monitor_profile

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, name, instance)


def openshift_monitor_disable(cmd, client, resource_group_name, name, no_wait=False):
    OpenShiftManagedClusterMonitorProfile = cmd.get_models('OpenShiftManagedClusterMonitorProfile',
                                                           resource_type=ResourceType.MGMT_CONTAINERSERVICE,
                                                           operation_group='open_shift_managed_clusters')
    logger.warning('The az openshift command is deprecated and has been replaced by az aro for ARO 4 clusters.  See http://aka.ms/aro/4 for information on switching to ARO 4.')  # pylint: disable=line-too-long

    instance = client.get(resource_group_name, name)
    monitor_profile = OpenShiftManagedClusterMonitorProfile(
        enabled=False, workspace_resource_id=None)  # pylint: disable=line-too-long
    instance.monitor_profile = monitor_profile
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, name, instance)


def _is_msi_cluster(managed_cluster):
    return (managed_cluster and managed_cluster.identity and
            (managed_cluster.identity.type.casefold() == "systemassigned" or
             managed_cluster.identity.type.casefold() == "userassigned"))


def _put_managed_cluster_ensuring_permission(
        cmd,     # pylint: disable=too-many-locals,too-many-statements,too-many-branches
        client,
        subscription_id,
        resource_group_name,
        name,
        managed_cluster,
        monitoring_addon_enabled,
        ingress_appgw_addon_enabled,
        virtual_node_addon_enabled,
        need_grant_vnet_permission_to_cluster_identity,
        vnet_subnet_id,
        enable_managed_identity,
        attach_acr,
        headers,
        no_wait
):
    # some addons require post cluster creation role assigment
    need_post_creation_role_assignment = (monitoring_addon_enabled or
                                          ingress_appgw_addon_enabled or
                                          (enable_managed_identity and attach_acr) or
                                          virtual_node_addon_enabled or
                                          need_grant_vnet_permission_to_cluster_identity)
    if need_post_creation_role_assignment:
        poller = client.begin_create_or_update(
            resource_group_name=resource_group_name,
            resource_name=name,
            parameters=managed_cluster,
            headers=headers)
        # Grant vnet permission to system assigned identity RIGHT AFTER
        # the cluster is put, this operation can reduce latency for the
        # role assignment take effect
        if need_grant_vnet_permission_to_cluster_identity:
            instant_cluster = client.get(resource_group_name, name)
            if not _add_role_assignment(cmd, 'Network Contributor',
                                        instant_cluster.identity.principal_id, scope=vnet_subnet_id,
                                        is_service_principal=False):
                logger.warning('Could not create a role assignment for subnet. '
                               'Are you an Owner on this subscription?')

        # adding a wait here since we rely on the result for role assignment
        cluster = LongRunningOperation(cmd.cli_ctx)(poller)
        cloud_name = cmd.cli_ctx.cloud.name
        # add cluster spn/msi Monitoring Metrics Publisher role assignment to publish metrics to MDM
        # mdm metrics is supported only in azure public cloud, so add the role assignment only in this cloud
        if monitoring_addon_enabled and cloud_name.lower() == 'azurecloud':
            from msrestazure.tools import resource_id
            cluster_resource_id = resource_id(
                subscription=subscription_id,
                resource_group=resource_group_name,
                namespace='Microsoft.ContainerService', type='managedClusters',
                name=name
            )
            add_monitoring_role_assignment(cluster, cluster_resource_id, cmd)
        if ingress_appgw_addon_enabled:
            add_ingress_appgw_addon_role_assignment(cluster, cmd)
        if virtual_node_addon_enabled:
            add_virtual_node_role_assignment(cmd, cluster, vnet_subnet_id)

        if enable_managed_identity and attach_acr:
            # Attach ACR to cluster enabled managed identity
            if cluster.identity_profile is None or \
               cluster.identity_profile["kubeletidentity"] is None:
                logger.warning('Your cluster is successfully created, but we failed to attach '
                               'acr to it, you can manually grant permission to the identity '
                               'named <ClUSTER_NAME>-agentpool in MC_ resource group to give '
                               'it permission to pull from ACR.')
            else:
                kubelet_identity_object_id = cluster.identity_profile["kubeletidentity"].object_id
                _ensure_aks_acr(cmd,
                                assignee=kubelet_identity_object_id,
                                acr_name_or_id=attach_acr,
                                subscription_id=subscription_id,
                                is_service_principal=False)
    else:
        cluster = sdk_no_wait(no_wait, client.begin_create_or_update,
                              resource_group_name=resource_group_name,
                              resource_name=name,
                              parameters=managed_cluster,
                              headers=headers)

    return cluster


def _ensure_cluster_identity_permission_on_kubelet_identity(cmd, cluster_identity_object_id, scope):
    factory = get_auth_management_client(cmd.cli_ctx, scope)
    assignments_client = factory.role_assignments

    for i in assignments_client.list_for_scope(scope=scope, filter='atScope()'):
        if i.scope.lower() != scope.lower():
            continue
        if not i.role_definition_id.lower().endswith(CONST_MANAGED_IDENTITY_OPERATOR_ROLE_ID):
            continue
        if i.principal_id.lower() != cluster_identity_object_id.lower():
            continue
        # already assigned
        return

    if not _add_role_assignment(cmd, CONST_MANAGED_IDENTITY_OPERATOR_ROLE, cluster_identity_object_id,
                                is_service_principal=False, scope=scope):
        raise UnauthorizedError('Could not grant Managed Identity Operator '
                                'permission to cluster identity at scope {}'.format(scope))


def aks_snapshot_create(cmd,    # pylint: disable=too-many-locals,too-many-statements,too-many-branches
                        client,
                        resource_group_name,
                        name,
                        nodepool_id,
                        location=None,
                        tags=None,
                        aks_custom_headers=None,
                        no_wait=False):

    rg_location = get_rg_location(cmd.cli_ctx, resource_group_name)
    if location is None:
        location = rg_location

    # load model CreationData, Snapshot
    from azure.cli.command_modules.acs.decorator import AKSModels
    CreationData = AKSModels(cmd, ResourceType.MGMT_CONTAINERSERVICE).CreationData
    Snapshot = AKSModels(cmd, ResourceType.MGMT_CONTAINERSERVICE).Snapshot

    creationData = CreationData(
        source_resource_id=nodepool_id
    )

    snapshot = Snapshot(
        name=name,
        tags=tags,
        location=location,
        creation_data=creationData
    )

    # custom headers
    aks_custom_headers = extract_comma_separated_string(
        aks_custom_headers,
        enable_strip=True,
        extract_kv=True,
        default_value={},
    )
    return client.create_or_update(resource_group_name, name, snapshot, headers=aks_custom_headers)


def aks_snapshot_show(cmd, client, resource_group_name, name):   # pylint: disable=unused-argument
    snapshot = client.get(resource_group_name, name)
    return snapshot


def aks_snapshot_delete(cmd,    # pylint: disable=unused-argument
                        client,
                        resource_group_name,
                        name,
                        no_wait=False,
                        yes=False):

    msg = 'This will delete the snapshot "{}" in resource group "{}", Are you sure?'.format(name, resource_group_name)
    if not yes and not prompt_y_n(msg, default="n"):
        return None

    return client.delete(resource_group_name, name)


def aks_snapshot_list(cmd, client, resource_group_name=None):  # pylint: disable=unused-argument
    if resource_group_name is None or resource_group_name == '':
        return client.list()

    return client.list_by_resource_group(resource_group_name)
