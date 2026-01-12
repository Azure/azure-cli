# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=ungrouped-imports

from azure.cli.core.aaz import AAZStrArg, AAZResourceGroupNameArg, has_value
from .aaz.latest.aks.safeguards._wait import Wait
from .aaz.latest.aks.safeguards._list import List
from .aaz.latest.aks.safeguards._delete import Delete
from .aaz.latest.aks.safeguards._show import Show
from .aaz.latest.aks.safeguards._update import Update
from .aaz.latest.aks.safeguards._create import Create
import base64
import errno
import io
import json
import os
import os.path
import platform
import re
import shutil
import ssl
import stat
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import webbrowser
import zipfile
from packaging.version import Version
from urllib.error import URLError
from urllib.request import urlopen
from azure.cli.command_modules.acs.maintenanceconfiguration import aks_maintenanceconfiguration_update_internal
import datetime
from dateutil.parser import parse

import colorama
import requests
import yaml
from azure.cli.command_modules.acs._client_factory import (
    cf_agent_pools,
)
from azure.cli.command_modules.acs._consts import (
    ADDONS,
    CONST_ACC_SGX_QUOTE_HELPER_ENABLED,
    CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME,
    CONST_CANIPULL_IMAGE,
    CONST_CONFCOM_ADDON_NAME,
    CONST_INGRESS_APPGW_ADDON_NAME,
    CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID,
    CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME,
    CONST_INGRESS_APPGW_SUBNET_CIDR,
    CONST_INGRESS_APPGW_SUBNET_ID,
    CONST_INGRESS_APPGW_WATCH_NAMESPACE,
    CONST_KUBE_DASHBOARD_ADDON_NAME,
    CONST_MONITORING_ADDON_NAME,
    CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID,
    CONST_MONITORING_USING_AAD_MSI_AUTH,
    CONST_NODEPOOL_MODE_USER,
    CONST_OPEN_SERVICE_MESH_ADDON_NAME,
    CONST_ROTATION_POLL_INTERVAL,
    CONST_SCALE_DOWN_MODE_DELETE,
    CONST_SCALE_SET_PRIORITY_REGULAR,
    CONST_SECRET_ROTATION_ENABLED,
    CONST_SPOT_EVICTION_POLICY_DELETE,
    CONST_VIRTUAL_NODE_ADDON_NAME,
    CONST_VIRTUAL_NODE_SUBNET_NAME,
    DecoratorEarlyExitException,
    CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_START,
    CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_COMPLETE,
    CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_ROLLBACK,
    CONST_AZURE_SERVICE_MESH_MODE_ISTIO,
    CONST_MANAGED_CLUSTER_SKU_TIER_PREMIUM,
    CONST_ARTIFACT_SOURCE_DIRECT,
    CONST_VIRTUAL_MACHINES,
)
from azure.cli.command_modules.acs._polling import RunCommandLocationPolling
from azure.cli.command_modules.acs._helpers import get_snapshot_by_snapshot_id, check_is_private_link_cluster
from azure.cli.command_modules.acs._resourcegroup import get_rg_location
from azure.cli.command_modules.acs.managednamespace import aks_managed_namespace_add, aks_managed_namespace_update
from azure.cli.command_modules.acs._validators import extract_comma_separated_string
from azure.cli.command_modules.acs.addonconfiguration import (
    add_ingress_appgw_addon_role_assignment,
    add_virtual_node_role_assignment,
    ensure_container_insights_for_monitoring,
    ensure_default_log_analytics_workspace_for_monitoring,
)
from azure.cli.core._profile import Profile
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    AzureInternalError,
    ClientRequestError,
    CLIInternalError,
    FileOperationError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    ResourceNotFoundError,
    UnknownError,
    ValidationError,
    RequiredArgumentMissingError,
)
from azure.cli.core.cloud import get_active_cloud
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.client_factory import get_subscription_id, get_mgmt_service_client
from azure.cli.core.profiles import ResourceType
from azure.mgmt.core.polling.arm_polling import ARMPolling
from azure.cli.core.util import in_cloud_console, sdk_no_wait
from azure.core.exceptions import ResourceNotFoundError as ResourceNotFoundErrorAzCore
from azure.mgmt.containerservice.models import KubernetesSupportPlan
from humanfriendly.terminal.spinners import Spinner
from knack.log import get_logger
from knack.prompting import NoTTYException, prompt_y_n
from knack.util import CLIError

logger = get_logger(__name__)

# pylint: disable=unused-argument


logger = get_logger(__name__)


def _validate_and_set_managed_cluster_argument(ctx):
    from azure.mgmt.core.tools import is_valid_resource_id

    args = ctx.args
    has_managed_cluster = has_value(args.managed_cluster)
    has_rg_and_cluster = has_value(
        args.resource_group) and has_value(args.cluster_name)

    # Ensure exactly one of the two conditions is true
    if has_managed_cluster == has_rg_and_cluster:
        raise ArgumentUsageError(
            "You must provide either 'managed_cluster' or both 'resource_group' and 'cluster_name', but not both.")

    if not has_managed_cluster:
        # pylint: disable=line-too-long
        args.managed_cluster = f"/subscriptions/{ctx.subscription_id}/resourceGroups/{args.resource_group}/providers/Microsoft.ContainerService/managedClusters/{args.cluster_name}"
    else:
        # If managed_cluster is provided but is not a full resource ID, treat it as a cluster name
        # and require resource_group to be provided
        managed_cluster_value = args.managed_cluster.to_serialized_data()

        # Normalize resource ID: add leading slash if missing for backward compatibility
        if managed_cluster_value and not managed_cluster_value.startswith('/'):
            managed_cluster_value = f"/{managed_cluster_value}"

        if not is_valid_resource_id(managed_cluster_value):
            # It's just a cluster name, need resource group
            if not has_value(args.resource_group):
                raise ArgumentUsageError(
                    "When providing cluster name via -c/--cluster, you must also provide -g/--resource-group.")
            # Build the full resource ID
            managed_cluster_value = f"/subscriptions/{ctx.subscription_id}/resourceGroups/{args.resource_group}/providers/Microsoft.ContainerService/managedClusters/{managed_cluster_value.lstrip('/')}"

        args.managed_cluster = managed_cluster_value


def _add_resource_group_cluster_name_subscription_id_args(_args_schema):
    _args_schema.resource_group = AAZResourceGroupNameArg(
        options=["-g", "--resource-group"],
        # pylint: disable=line-too-long
        help="The name of the resource group. You can configure the default group using az configure --defaults group=`<name>`. You may provide either 'managed_cluster' or both 'resource_group' and 'name', but not both",
        required=False,
    )
    _args_schema.cluster_name = AAZStrArg(
        options=["--name", "-n"],
        # pylint: disable=line-too-long
        help="The name of the Managed Cluster.You may provide either 'managed_cluster' or both 'resource_group' and name', but not both.",
        required=False,
    )
    _args_schema.managed_cluster._required = False  # pylint: disable=protected-access
    return _args_schema


class AKSSafeguardsShowCustom(Show):
    def pre_operations(self):
        _validate_and_set_managed_cluster_argument(self.ctx)

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        _args_schema = super()._build_arguments_schema(*args, **kwargs)
        after_schema = _add_resource_group_cluster_name_subscription_id_args(
            _args_schema)
        return after_schema


class AKSSafeguardsDeleteCustom(Delete):
    def pre_operations(self):
        _validate_and_set_managed_cluster_argument(self.ctx)

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        _args_schema = super()._build_arguments_schema(*args, **kwargs)
        return _add_resource_group_cluster_name_subscription_id_args(_args_schema)


class AKSSafeguardsUpdateCustom(Update):
    def pre_operations(self):
        _validate_and_set_managed_cluster_argument(self.ctx)

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        _args_schema = super()._build_arguments_schema(*args, **kwargs)
        return _add_resource_group_cluster_name_subscription_id_args(_args_schema)


class AKSSafeguardsCreateCustom(Create):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        _args_schema = super()._build_arguments_schema(*args, **kwargs)
        return _add_resource_group_cluster_name_subscription_id_args(_args_schema)

    def pre_operations(self):
        from azure.cli.core.util import send_raw_request
        from azure.cli.core.azclierror import HTTPError

        # Validate and set managed cluster argument
        _validate_and_set_managed_cluster_argument(self.ctx)

        # Check if Deployment Safeguards already exists before attempting create
        resource_uri = self.ctx.args.managed_cluster.to_serialized_data()

        # Validate resource_uri format to prevent URL injection
        if not resource_uri.startswith('/subscriptions/'):
            raise CLIError(f"Invalid managed cluster resource ID format: {resource_uri}")

        # Construct the GET URL to check if resource already exists
        api_version = self._aaz_info['version']
        safeguards_url = f"https://management.azure.com{resource_uri}/providers/Microsoft.ContainerService/deploymentSafeguards/default?api-version={api_version}"

        # Check if resource already exists
        resource_exists = False
        try:
            response = send_raw_request(self.ctx.cli_ctx, "GET", safeguards_url)
            if response.status_code == 200:
                resource_exists = True
        except HTTPError as ex:
            # 404 means resource doesn't exist, which is expected for create
            if ex.response.status_code != 404:
                # Re-raise if it's not a 404 - could be auth issue, network problem, etc.
                raise

        # If resource exists, block the create
        if resource_exists:
            raise CLIError(
                "Deployment Safeguards instance already exists for this cluster. "
                "Please use 'az aks safeguards update' to modify the configuration, "
                "or 'az aks safeguards delete' to remove it before creating a new one."
            )


class AKSSafeguardsListCustom(List):
    def pre_operations(self):
        _validate_and_set_managed_cluster_argument(self.ctx)

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        _args_schema = super()._build_arguments_schema(*args, **kwargs)
        return _add_resource_group_cluster_name_subscription_id_args(_args_schema)


class AKSSafeguardsWaitCustom(Wait):
    def pre_operations(self):
        _validate_and_set_managed_cluster_argument(self.ctx)

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        _args_schema = super()._build_arguments_schema(*args, **kwargs)
        return _add_resource_group_cluster_name_subscription_id_args(_args_schema)


def get_cmd_test_hook_data(filename):
    hook_data = None
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    test_hook_file_path = os.path.join(curr_dir, 'tests/latest/data', filename)
    if os.path.exists(test_hook_file_path):
        with open(test_hook_file_path, "r") as f:
            hook_data = json.load(f)
    return hook_data


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


# pylint: disable=too-many-statements,too-many-branches,too-many-locals
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
    if Version(instance.kubernetes_version) >= Version('1.19.0') or (not addon_profile.enabled):
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
            raise ResourceNotFoundError(
                'Could not find dashboard pod: {} Command output: {}'.format(err, err.output))
        if dashboard_pod:
            # remove any "pods/" or "pod/" prefix from the name
            dashboard_pod = str(dashboard_pod).rsplit(
                '/', maxsplit=1)[-1].strip()
        else:
            raise ResourceNotFoundError(
                "Couldn't find the Kubernetes dashboard pod.")

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
            dashboard_port = int(dashboard_port.replace("'", ""))
        except subprocess.CalledProcessError as err:
            raise ResourceNotFoundError(
                'Could not find dashboard port: {} Command output: {}'.format(err, err.output))

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
                        logger.warning(
                            "Currently in a test environment, the proxy is closed due to a preset timeout!")
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
                logger.warning(
                    "Currently in a test environment, the proxy is closed due to a preset timeout!")
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


def aks_machine_list(cmd, client, resource_group_name, cluster_name, nodepool_name):
    return client.list(resource_group_name, cluster_name, nodepool_name)


def aks_machine_show(cmd, client, resource_group_name, cluster_name, nodepool_name, machine_name):
    return client.get(resource_group_name, cluster_name, nodepool_name, machine_name)


# pylint: disable=unused-argument
def aks_namespace_add(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    name,
    cpu_request,
    cpu_limit,
    memory_request,
    memory_limit,
    tags=None,
    labels=None,
    annotations=None,
    aks_custom_headers=None,
    ingress_policy=None,
    egress_policy=None,
    adoption_policy=None,
    delete_policy=None,
    no_wait=False,
):
    existedNamespace = None
    try:
        existedNamespace = client.get(resource_group_name, cluster_name, name)
    except ResourceNotFoundErrorAzCore:
        pass

    if existedNamespace:
        raise ClientRequestError(
            f"Namespace '{name}' already exists. Please use 'az aks namespace update' to update it."
        )

    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()
    headers = extract_comma_separated_string(
        aks_custom_headers,
        enable_strip=True,
        extract_kv=True,
        default_value={},
        allow_appending_values_to_same_key=True,
    )
    return aks_managed_namespace_add(cmd, client, raw_parameters, headers, no_wait)


# pylint: disable=unused-argument
def aks_namespace_update(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    name,
    cpu_request=None,
    cpu_limit=None,
    memory_request=None,
    memory_limit=None,
    tags=None,
    labels=None,
    annotations=None,
    aks_custom_headers=None,
    ingress_policy=None,
    egress_policy=None,
    adoption_policy=None,
    delete_policy=None,
    no_wait=False,
):
    try:
        existedNamespace = client.get(resource_group_name, cluster_name, name)
    except ResourceNotFoundErrorAzCore:
        raise ClientRequestError(
            f"Namespace '{name}' doesn't exist. "
            "Please use 'aks namespace list' to get current list of managed namespaces"
        )

    if existedNamespace:
        # DO NOT MOVE: get all the original parameters and save them as a dictionary
        raw_parameters = locals()
        headers = extract_comma_separated_string(
            aks_custom_headers,
            enable_strip=True,
            extract_kv=True,
            default_value={},
            allow_appending_values_to_same_key=True,
        )
        return aks_managed_namespace_update(cmd, client, raw_parameters, headers, existedNamespace, no_wait)


def aks_namespace_show(
    cmd,  # pylint: disable=unused-argument
    client,
    resource_group_name,
    cluster_name,
    name
):
    logger.warning('resource_group_name: %s, cluster_name: %s, managed_namespace_name: %s ',
                   resource_group_name, cluster_name, name)
    return client.get(resource_group_name, cluster_name, name)


def aks_namespace_list(
    cmd,  # pylint: disable=unused-argument
    client,
    resource_group_name=None,
    cluster_name=None,
):
    if resource_group_name and cluster_name:
        return client.list_by_managed_cluster(resource_group_name, cluster_name)
    rcf = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    full_resource_type = "Microsoft.ContainerService/managedClusters/managedNamespaces"
    filters = [f"resourceType eq '{full_resource_type}'"]
    if resource_group_name:
        filters.append(f"resourceGroup eq '{resource_group_name}'")
    odata_filter = " and ".join(filters)
    expand = "createdTime,changedTime,provisioningState"
    resources = rcf.resources.list(filter=odata_filter, expand=expand)
    return list(resources)


def aks_namespace_delete(
    cmd,  # pylint: disable=unused-argument
    client,
    resource_group_name,
    cluster_name,
    name,
    no_wait=False,
):
    namespace_exists = False
    namespace_instances = client.list_by_managed_cluster(resource_group_name, cluster_name)
    for instance in namespace_instances:
        if instance.name.lower() == name.lower():
            namespace_exists = True
            break

    if not namespace_exists:
        raise ClientRequestError(
            f"Managed namespace {name} doesn't exist, "
            "use 'aks namespace list' to get current managed namespace list"
        )

    return sdk_no_wait(
        no_wait,
        client.begin_delete,
        resource_group_name,
        cluster_name,
        name,
    )


def aks_namespace_get_credentials(
    cmd,  # pylint: disable=unused-argument
    client,
    resource_group_name,
    cluster_name,
    name,
    path=os.path.join(os.path.expanduser("~"), ".kube", "config"),
    overwrite_existing=False,
    context_name=None,
):
    credentialResults = None
    credentialResults = client.list_credential(resource_group_name, cluster_name, name)

    # Check if KUBECONFIG environmental variable is set
    # If path is different than default then that means -f/--file is passed
    # in which case we ignore the KUBECONFIG variable
    # KUBECONFIG can be colon separated. If we find that condition, use the first entry
    if "KUBECONFIG" in os.environ and path == os.path.join(os.path.expanduser('~'), '.kube', 'config'):
        kubeconfig_path = os.environ["KUBECONFIG"].split(os.pathsep)[0]
        if kubeconfig_path:
            logger.info("The default path '%s' is replaced by '%s' defined in KUBECONFIG.", path, kubeconfig_path)
            path = kubeconfig_path
        else:
            logger.warning("Invalid path '%s' defined in KUBECONFIG.", kubeconfig_path)

    if not credentialResults:
        raise CLIError("No Kubernetes credentials found.")
    try:
        kubeconfig = credentialResults.kubeconfigs[0].value.decode(
            encoding='UTF-8')
        _print_or_merge_credentials(
            path, kubeconfig, overwrite_existing, context_name)
    except (IndexError, ValueError) as exc:
        raise CLIError("Fail to find kubeconfig file.") from exc


def aks_maintenanceconfiguration_list(
    cmd,
    client,
    resource_group_name,
    cluster_name
):
    return client.list_by_managed_cluster(resource_group_name, cluster_name)


def aks_maintenanceconfiguration_show(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    config_name
):
    logger.warning('resource_group_name: %s, cluster_name: %s, config_name: %s ',
                   resource_group_name, cluster_name, config_name)
    return client.get(resource_group_name, cluster_name, config_name)


def aks_maintenanceconfiguration_delete(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    config_name
):
    logger.warning('resource_group_name: %s, cluster_name: %s, config_name: %s ',
                   resource_group_name, cluster_name, config_name)
    return client.delete(resource_group_name, cluster_name, config_name)


def aks_maintenanceconfiguration_add(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    config_name,
    config_file=None,
    weekday=None,
    start_hour=None,
    schedule_type=None,
    interval_days=None,
    interval_weeks=None,
    interval_months=None,
    day_of_week=None,
    day_of_month=None,
    week_index=None,
    duration_hours=None,
    utc_offset=None,
    start_date=None,
    start_time=None
):
    configs = client.list_by_managed_cluster(resource_group_name, cluster_name)
    for config in configs:
        if config.name == config_name:
            raise CLIError("Maintenance configuration '{}' already exists, please try a different name, "
                           "use 'aks maintenanceconfiguration list' to get current list of maitenance configurations".format(config_name))
    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()
    return aks_maintenanceconfiguration_update_internal(cmd, client, raw_parameters)


def aks_maintenanceconfiguration_update(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    config_name,
    config_file=None,
    weekday=None,
    start_hour=None,
    schedule_type=None,
    interval_days=None,
    interval_weeks=None,
    interval_months=None,
    day_of_week=None,
    day_of_month=None,
    week_index=None,
    duration_hours=None,
    utc_offset=None,
    start_date=None,
    start_time=None
):
    configs = client.list_by_managed_cluster(resource_group_name, cluster_name)
    found = False
    for config in configs:
        if config.name == config_name:
            found = True
            break
    if not found:
        raise ResourceNotFoundError("Maintenance configuration '{}' doesn't exist."
                                    "use 'aks maintenanceconfiguration list' to get current list of maitenance configurations".format(config_name))
    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()
    return aks_maintenanceconfiguration_update_internal(cmd, client, raw_parameters)


def wait_then_open(url):
    """
    Waits for a bit then opens a URL.  Useful for waiting for a proxy to come up, and then open the URL.
    """
    for _ in range(1, 10):
        try:
            _urlopen_read(url)
        except URLError:
            time.sleep(1)
        break
    webbrowser.open_new_tab(url)


def wait_then_open_async(url):
    """
    Spawns a thread that waits for a bit then opens a URL.
    """
    t = threading.Thread(target=wait_then_open, args=(url,))
    t.daemon = True
    t.start()


# pylint: disable=too-many-locals
def aks_create(
    cmd,
    client,
    resource_group_name,
    name,
    ssh_key_value,
    location=None,
    kubernetes_version="",
    tags=None,
    dns_name_prefix=None,
    node_osdisk_diskencryptionset_id=None,
    disable_local_accounts=False,
    disable_rbac=None,
    edge_zone=None,
    admin_username="azureuser",
    generate_ssh_keys=False,
    no_ssh_key=False,
    pod_cidr=None,
    service_cidr=None,
    ip_families=None,
    pod_cidrs=None,
    service_cidrs=None,
    dns_service_ip=None,
    docker_bridge_address=None,
    load_balancer_sku=None,
    load_balancer_managed_outbound_ip_count=None,
    load_balancer_managed_outbound_ipv6_count=None,
    load_balancer_outbound_ips=None,
    load_balancer_outbound_ip_prefixes=None,
    load_balancer_outbound_ports=None,
    load_balancer_idle_timeout=None,
    load_balancer_backend_pool_type=None,
    nat_gateway_managed_outbound_ip_count=None,
    nat_gateway_idle_timeout=None,
    outbound_type=None,
    network_plugin=None,
    network_plugin_mode=None,
    network_policy=None,
    network_dataplane=None,
    auto_upgrade_channel=None,
    node_os_upgrade_channel=None,
    cluster_autoscaler_profile=None,
    sku=None,
    tier=None,
    fqdn_subdomain=None,
    api_server_authorized_ip_ranges=None,
    enable_private_cluster=False,
    private_dns_zone=None,
    disable_public_fqdn=False,
    service_principal=None,
    client_secret=None,
    enable_managed_identity=None,
    assign_identity=None,
    assign_kubelet_identity=None,
    enable_aad=False,
    enable_azure_rbac=False,
    aad_admin_group_object_ids=None,
    aad_tenant_id=None,
    enable_oidc_issuer=False,
    windows_admin_username=None,
    windows_admin_password=None,
    enable_ahub=False,
    enable_windows_gmsa=False,
    gmsa_dns_server=None,
    gmsa_root_domain_name=None,
    attach_acr=None,
    skip_subnet_role_assignment=False,
    node_resource_group=None,
    nrg_lockdown_restriction_level=None,
    k8s_support_plan=None,
    enable_defender=False,
    defender_config=None,
    disable_disk_driver=False,
    disable_file_driver=False,
    enable_blob_driver=None,
    enable_workload_identity=False,
    disable_snapshot_controller=False,
    enable_azure_keyvault_kms=False,
    azure_keyvault_kms_key_id=None,
    azure_keyvault_kms_key_vault_network_access=None,
    azure_keyvault_kms_key_vault_resource_id=None,
    enable_image_cleaner=False,
    image_cleaner_interval_hours=None,
    enable_keda=False,
    enable_vpa=False,
    custom_ca_trust_certificates=None,
    disable_run_command=False,
    # advanced networking
    enable_acns=None,
    disable_acns_observability=None,
    disable_acns_security=None,
    acns_advanced_networkpolicies=None,
    # network isoalted cluster
    bootstrap_artifact_source=CONST_ARTIFACT_SOURCE_DIRECT,
    bootstrap_container_registry_resource_id=None,
    # addons
    enable_addons=None,
    workspace_resource_id=None,
    enable_msi_auth_for_monitoring=True,
    enable_syslog=False,
    data_collection_settings=None,
    ampls_resource_id=None,
    enable_high_log_scale_mode=False,
    aci_subnet_name=None,
    appgw_name=None,
    appgw_subnet_cidr=None,
    appgw_id=None,
    appgw_subnet_id=None,
    appgw_watch_namespace=None,
    enable_sgxquotehelper=False,
    enable_secret_rotation=False,
    rotation_poll_interval=None,
    enable_app_routing=False,
    enable_ai_toolchain_operator=False,
    app_routing_default_nginx_controller=None,
    enable_static_egress_gateway=False,
    # nodepool paramerters
    nodepool_name="nodepool1",
    node_vm_size=None,
    vm_sizes=None,
    os_sku=None,
    snapshot_id=None,
    vnet_subnet_id=None,
    pod_subnet_id=None,
    pod_ip_allocation_mode=None,
    enable_node_public_ip=False,
    node_public_ip_prefix_id=None,
    enable_cluster_autoscaler=False,
    min_count=None,
    max_count=None,
    node_count=3,
    nodepool_tags=None,
    nodepool_labels=None,
    nodepool_taints=None,
    nodepool_allowed_host_ports=None,
    nodepool_asg_ids=None,
    node_osdisk_type=None,
    node_osdisk_size=None,
    vm_set_type=None,
    zones=None,
    ppg=None,
    http_proxy_config=None,
    max_pods=None,
    enable_encryption_at_host=False,
    enable_ultra_ssd=False,
    enable_fips_image=False,
    kubelet_config=None,
    linux_os_config=None,
    host_group_id=None,
    crg_id=None,
    gpu_instance_profile=None,
    message_of_the_day=None,
    workload_runtime=None,
    # azure service mesh
    enable_azure_service_mesh=None,
    revision=None,
    # azure monitor profile
    enable_azure_monitor_metrics=False,
    azure_monitor_workspace_resource_id=None,
    ksm_metric_labels_allow_list=None,
    ksm_metric_annotations_allow_list=None,
    grafana_resource_id=None,
    enable_windows_recording_rules=False,
    # azure container storage
    enable_azure_container_storage=None,
    container_storage_version=None,
    storage_pool_name=None,
    storage_pool_size=None,
    storage_pool_sku=None,
    storage_pool_option=None,
    ephemeral_disk_volume_type=None,
    ephemeral_disk_nvme_perf_tier=None,
    # misc
    yes=False,
    no_wait=False,
    aks_custom_headers=None,
    node_public_ip_tags=None,
    if_match=None,
    if_none_match=None,
    # metrics profile
    enable_cost_analysis=False,
    # trusted launch
    enable_vtpm=False,
    enable_secure_boot=False,
    # apiserver vnet integration
    enable_apiserver_vnet_integration=False,
    apiserver_subnet_id=None,
    # node provisioning
    node_provisioning_mode=None,
    node_provisioning_default_pools=None,
):
    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()

    # validation for existing cluster
    existing_mc = None
    try:
        existing_mc = client.get(resource_group_name, name)
    # pylint: disable=broad-except
    except Exception as ex:
        logger.debug("failed to get cluster, error: %s", ex)
    if existing_mc:
        raise ClientRequestError(
            f"The cluster '{name}' under resource group '{resource_group_name}' already exists. "
            "Please use command 'az aks update' to update the existing cluster, "
            "or select a different cluster name to create a new cluster."
        )

    # decorator pattern
    from azure.cli.command_modules.acs.managed_cluster_decorator import AKSManagedClusterCreateDecorator
    aks_create_decorator = AKSManagedClusterCreateDecorator(
        cmd=cmd,
        client=client,
        raw_parameters=raw_parameters,
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
    )
    try:
        # construct mc profile
        mc = aks_create_decorator.construct_mc_profile_default()
    except DecoratorEarlyExitException:
        # exit gracefully
        return None
    # send request to create a real managed cluster
    return aks_create_decorator.create_mc(mc)


def aks_update(
    cmd,
    client,
    resource_group_name,
    name,
    tags=None,
    disable_local_accounts=False,
    enable_local_accounts=False,
    ip_families=None,
    network_plugin=None,
    network_plugin_mode=None,
    network_dataplane=None,
    network_policy=None,
    pod_cidr=None,
    load_balancer_managed_outbound_ip_count=None,
    load_balancer_managed_outbound_ipv6_count=None,
    load_balancer_outbound_ips=None,
    load_balancer_outbound_ip_prefixes=None,
    load_balancer_outbound_ports=None,
    load_balancer_idle_timeout=None,
    load_balancer_backend_pool_type=None,
    load_balancer_sku=None,
    nat_gateway_managed_outbound_ip_count=None,
    nat_gateway_idle_timeout=None,
    outbound_type=None,
    auto_upgrade_channel=None,
    node_os_upgrade_channel=None,
    cluster_autoscaler_profile=None,
    sku=None,
    tier=None,
    api_server_authorized_ip_ranges=None,
    enable_public_fqdn=False,
    disable_public_fqdn=False,
    private_dns_zone=None,
    enable_managed_identity=False,
    assign_identity=None,
    assign_kubelet_identity=None,
    enable_aad=False,
    enable_azure_rbac=False,
    disable_azure_rbac=False,
    aad_tenant_id=None,
    aad_admin_group_object_ids=None,
    enable_oidc_issuer=False,
    k8s_support_plan=None,
    windows_admin_password=None,
    enable_ahub=False,
    disable_ahub=False,
    enable_windows_gmsa=False,
    gmsa_dns_server=None,
    gmsa_root_domain_name=None,
    disable_windows_gmsa=False,
    attach_acr=None,
    detach_acr=None,
    assignee_principal_type=None,
    nrg_lockdown_restriction_level=None,
    enable_defender=False,
    disable_defender=False,
    defender_config=None,
    enable_disk_driver=False,
    disable_disk_driver=False,
    enable_file_driver=False,
    disable_file_driver=False,
    enable_blob_driver=None,
    disable_blob_driver=None,
    enable_workload_identity=False,
    disable_workload_identity=False,
    enable_snapshot_controller=False,
    disable_snapshot_controller=False,
    enable_azure_keyvault_kms=False,
    disable_azure_keyvault_kms=False,
    azure_keyvault_kms_key_id=None,
    azure_keyvault_kms_key_vault_network_access=None,
    azure_keyvault_kms_key_vault_resource_id=None,
    enable_image_cleaner=False,
    disable_image_cleaner=False,
    image_cleaner_interval_hours=None,
    http_proxy_config=None,
    enable_keda=False,
    disable_keda=False,
    enable_vpa=False,
    disable_vpa=False,
    enable_force_upgrade=False,
    disable_force_upgrade=False,
    upgrade_override_until=None,
    custom_ca_trust_certificates=None,
    enable_run_command=False,
    disable_run_command=False,
    # advanced networking
    disable_acns=None,
    enable_acns=None,
    disable_acns_observability=None,
    disable_acns_security=None,
    acns_advanced_networkpolicies=None,
    # network isoalted cluster
    bootstrap_artifact_source=None,
    bootstrap_container_registry_resource_id=None,
    # addons
    enable_secret_rotation=False,
    disable_secret_rotation=False,
    enable_ai_toolchain_operator=False,
    disable_ai_toolchain_operator=False,
    rotation_poll_interval=None,
    enable_static_egress_gateway=False,
    disable_static_egress_gateway=False,
    # nodepool paramerters
    enable_cluster_autoscaler=False,
    disable_cluster_autoscaler=False,
    update_cluster_autoscaler=False,
    min_count=None,
    max_count=None,
    nodepool_labels=None,
    nodepool_taints=None,
    migrate_vmas_to_vms=False,
    # azure monitor profile
    enable_azure_monitor_metrics=False,
    azure_monitor_workspace_resource_id=None,
    ksm_metric_labels_allow_list=None,
    ksm_metric_annotations_allow_list=None,
    grafana_resource_id=None,
    enable_windows_recording_rules=False,
    disable_azure_monitor_metrics=False,
    # azure container storage
    enable_azure_container_storage=None,
    disable_azure_container_storage=None,
    container_storage_version=None,
    storage_pool_name=None,
    storage_pool_size=None,
    storage_pool_sku=None,
    storage_pool_option=None,
    azure_container_storage_nodepools=None,
    ephemeral_disk_volume_type=None,
    ephemeral_disk_nvme_perf_tier=None,
    # misc
    yes=False,
    no_wait=False,
    aks_custom_headers=None,
    if_match=None,
    if_none_match=None,
    # metrics profile
    enable_cost_analysis=False,
    disable_cost_analysis=False,
    # apiserver vnet integration
    enable_apiserver_vnet_integration=False,
    apiserver_subnet_id=None,
    enable_private_cluster=False,
    disable_private_cluster=False,
    # node provisioning
    node_provisioning_mode=None,
    node_provisioning_default_pools=None,
):
    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()

    # decorator pattern
    from azure.cli.command_modules.acs.managed_cluster_decorator import AKSManagedClusterUpdateDecorator
    aks_update_decorator = AKSManagedClusterUpdateDecorator(
        cmd=cmd,
        client=client,
        raw_parameters=raw_parameters,
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
    )
    try:
        # update mc profile
        mc = aks_update_decorator.update_mc_profile_default()
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
                enable_force_upgrade=False,
                disable_force_upgrade=False,
                upgrade_override_until=None,
                tier=None,
                k8s_support_plan=None,
                yes=False,
                if_match=None,
                if_none_match=None):
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
                raise CLIError('This cluster is using AvailabilitySet. Node image upgrade only operation '
                               'can only be applied on VirtualMachineScaleSets or VirtualMachines cluster.')
            agent_pool_client = cf_agent_pools(cmd.cli_ctx)
            _upgrade_single_nodepool_image_version(True, agent_pool_client,
                                                   resource_group_name, name, agent_pool_profile.name)
        mc = client.get(resource_group_name, name)
        return _remove_nulls([mc])[0]

    if tier is not None:
        instance.sku.tier = tier

    if k8s_support_plan is not None:
        instance.support_plan = k8s_support_plan

    if (instance.support_plan == KubernetesSupportPlan.AKS_LONG_TERM_SUPPORT and instance.sku.tier is not None and instance.sku.tier.lower() != CONST_MANAGED_CLUSTER_SKU_TIER_PREMIUM.lower()):
        raise CLIError(
            "AKS Long Term Support is only available for Premium tier clusters.")

    instance = _update_upgrade_settings(
        cmd,
        instance,
        enable_force_upgrade=enable_force_upgrade,
        disable_force_upgrade=disable_force_upgrade,
        upgrade_override_until=upgrade_override_until)

    if instance.kubernetes_version == kubernetes_version or kubernetes_version == '':
        # don't prompt here because there is another prompt below?
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
            msg = ("Since --control-plane-only parameter is not specified, this will upgrade the control plane "
                   "AND all nodepools to version {}. Continue?").format(instance.kubernetes_version)
            if not yes and not prompt_y_n(msg, default="n"):
                return None
            upgrade_all = True
        else:
            msg = ("Since --control-plane-only parameter is specified, this will upgrade only the kubernetes version of the control plane to {}. "
                   "Kubernetes versions of the node pools will remain unchanged, "
                   "but node image version may be upgraded if there has been cluster config change that requires VM reimage. "
                   "Continue?").format(instance.kubernetes_version)
            if not yes and not prompt_y_n(msg, default="n"):
                return None

    if upgrade_all:
        for agent_profile in instance.agent_pool_profiles:
            agent_profile.orchestrator_version = kubernetes_version
            agent_profile.creation_data = None

    # null out the SP profile because otherwise validation complains
    instance.service_principal_profile = None

    active_cloud = get_active_cloud(cmd.cli_ctx)
    if active_cloud.profile != "latest":
        return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, name, instance)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, name, instance, if_match=if_match, if_none_match=if_none_match)


def _update_upgrade_settings(cmd, instance,
                             enable_force_upgrade=False,
                             disable_force_upgrade=False,
                             upgrade_override_until=None):
    existing_until = None
    if instance.upgrade_settings is not None and instance.upgrade_settings.override_settings is not None and instance.upgrade_settings.override_settings.until is not None:
        existing_until = instance.upgrade_settings.override_settings.until

    force_upgrade = None
    if enable_force_upgrade is False and disable_force_upgrade is False:
        force_upgrade = None
    elif enable_force_upgrade is not None:
        force_upgrade = enable_force_upgrade
    elif disable_force_upgrade is not None:
        force_upgrade = not disable_force_upgrade

    ClusterUpgradeSettings = cmd.get_models(
        "ClusterUpgradeSettings",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="managed_clusters",
    )

    UpgradeOverrideSettings = cmd.get_models(
        "UpgradeOverrideSettings",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="managed_clusters",
    )

    if force_upgrade is not None or upgrade_override_until is not None:
        if instance.upgrade_settings is None:
            instance.upgrade_settings = ClusterUpgradeSettings()
        if instance.upgrade_settings.override_settings is None:
            instance.upgrade_settings.override_settings = UpgradeOverrideSettings()
        # sets force_upgrade
        if force_upgrade is not None:
            instance.upgrade_settings.override_settings.force_upgrade = force_upgrade
        # sets until
        if upgrade_override_until is not None:
            try:
                instance.upgrade_settings.override_settings.until = parse(
                    upgrade_override_until)
            except Exception:  # pylint: disable=broad-except
                raise InvalidArgumentValueError(
                    f"{upgrade_override_until} is not a valid datatime format."
                )
        elif force_upgrade:
            default_extended_until = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=3)
            if existing_until is None or existing_until.timestamp() < default_extended_until.timestamp():
                instance.upgrade_settings.override_settings.until = default_extended_until
    return instance


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

            if agent_profile.type == CONST_VIRTUAL_MACHINES:
                if len(agent_profile.virtual_machines_profile.scale.manual) == 1:
                    agent_profile.virtual_machines_profile.scale.manual[0].count = int(node_count)
                else:
                    raise ClientRequestError("Cannot scale virtual machines node pool with more than one size.")
            else:
                agent_profile.count = int(node_count)  # pylint: disable=no-member
            # null out the SP profile because otherwise validation complains
            instance.service_principal_profile = None
            return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, name, instance)
    raise CLIError('The nodepool "{}" was not found.'.format(nodepool_name))


def aks_show(cmd, client, resource_group_name, name):
    mc = client.get(resource_group_name, name)
    return _remove_nulls([mc])[0]


def aks_stop(cmd, client, resource_group_name, name, no_wait=False):
    instance = client.get(resource_group_name, name)
    # print warning when stopping a private link cluster
    if check_is_private_link_cluster(instance):
        logger.warning('Your private cluster apiserver IP might get changed when it\'s stopped and started.\n'
                       'Any user provisioned private endpoints linked to this private cluster will need to be deleted and created again. '
                       'Any user managed DNS record also needs to be updated with the new IP.')
    return sdk_no_wait(no_wait, client.begin_stop, resource_group_name, name)


def aks_list(cmd, client, resource_group_name=None):
    if resource_group_name:
        managed_clusters = client.list_by_resource_group(resource_group_name)
    else:
        managed_clusters = client.list()
    return _remove_nulls(list(managed_clusters))


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


# pylint: disable=line-too-long
def aks_disable_addons(cmd, client, resource_group_name, name, addons, no_wait=False):
    instance = client.get(resource_group_name, name)
    subscription_id = get_subscription_id(cmd.cli_ctx)
    try:
        if addons == "monitoring" and CONST_MONITORING_ADDON_NAME in instance.addon_profiles and \
                instance.addon_profiles[CONST_MONITORING_ADDON_NAME].enabled and \
                CONST_MONITORING_USING_AAD_MSI_AUTH in instance.addon_profiles[CONST_MONITORING_ADDON_NAME].config and \
                str(instance.addon_profiles[CONST_MONITORING_ADDON_NAME].config[CONST_MONITORING_USING_AAD_MSI_AUTH]).lower() == 'true':
            # remove the DCR association because otherwise the DCR can't be deleted
            ensure_container_insights_for_monitoring(
                cmd,
                instance.addon_profiles[CONST_MONITORING_ADDON_NAME],
                subscription_id,
                resource_group_name,
                name,
                instance.location,
                remove_monitoring=True,
                aad_route=True,
                create_dcr=False,
                create_dcra=True,
                enable_syslog=False,
                data_collection_settings=None,
                is_private_cluster=False,
                ampls_resource_id=None,
                enable_high_log_scale_mode=False,
            )
    except TypeError:
        pass

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


# pylint: disable=line-too-long
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
                      enable_msi_auth_for_monitoring=True,
                      enable_syslog=False,
                      data_collection_settings=None,
                      ampls_resource_id=None,
                      enable_high_log_scale_mode=False,
                      no_wait=False,):
    instance = client.get(resource_group_name, name)
    msi_auth = False
    if instance.service_principal_profile.client_id == "msi":
        msi_auth = True
    else:
        enable_msi_auth_for_monitoring = False
    subscription_id = get_subscription_id(cmd.cli_ctx)

    is_private_cluster = False
    if instance.api_server_access_profile and instance.api_server_access_profile.enable_private_cluster:
        is_private_cluster = True

    instance = _update_addons(cmd, instance, subscription_id, resource_group_name, name, addons, enable=True,
                              workspace_resource_id=workspace_resource_id,
                              enable_msi_auth_for_monitoring=enable_msi_auth_for_monitoring,
                              subnet_name=subnet_name,
                              appgw_name=appgw_name,
                              appgw_subnet_cidr=appgw_subnet_cidr,
                              appgw_id=appgw_id,
                              appgw_subnet_id=appgw_subnet_id,
                              appgw_watch_namespace=appgw_watch_namespace,
                              enable_sgxquotehelper=enable_sgxquotehelper,
                              enable_secret_rotation=enable_secret_rotation,
                              rotation_poll_interval=rotation_poll_interval,
                              no_wait=no_wait,)

    enable_monitoring = is_monitoring_addon_enabled(addons, instance)
    ingress_appgw_addon_enabled = CONST_INGRESS_APPGW_ADDON_NAME in instance.addon_profiles \
        and instance.addon_profiles[CONST_INGRESS_APPGW_ADDON_NAME].enabled

    os_type = 'Linux'
    virtual_node_addon_name = CONST_VIRTUAL_NODE_ADDON_NAME + os_type
    enable_virtual_node = (virtual_node_addon_name in instance.addon_profiles and
                           instance.addon_profiles[virtual_node_addon_name].enabled)

    need_pull_for_result = enable_monitoring or ingress_appgw_addon_enabled or enable_virtual_node

    if need_pull_for_result:
        if enable_monitoring:
            if CONST_MONITORING_USING_AAD_MSI_AUTH in instance.addon_profiles[CONST_MONITORING_ADDON_NAME].config and \
               str(instance.addon_profiles[CONST_MONITORING_ADDON_NAME].config[CONST_MONITORING_USING_AAD_MSI_AUTH]).lower() == 'true':
                if msi_auth:
                    # create a Data Collection Rule (DCR) and associate it with the cluster
                    ensure_container_insights_for_monitoring(
                        cmd, instance.addon_profiles[CONST_MONITORING_ADDON_NAME],
                        subscription_id,
                        resource_group_name,
                        name,
                        instance.location,
                        aad_route=True,
                        create_dcr=True,
                        create_dcra=True,
                        enable_syslog=enable_syslog,
                        data_collection_settings=data_collection_settings,
                        is_private_cluster=is_private_cluster,
                        ampls_resource_id=ampls_resource_id,
                        enable_high_log_scale_mode=enable_high_log_scale_mode)
                else:
                    raise ArgumentUsageError(
                        "--enable-msi-auth-for-monitoring can not be used on clusters with service principal auth.")
            else:
                # monitoring addon will use legacy path
                if enable_syslog:
                    raise ArgumentUsageError(
                        "--enable-syslog can not be used without MSI auth.")
                if enable_high_log_scale_mode:
                    raise ArgumentUsageError(
                        "--enable-high-log-scale-mode can not be used without MSI auth.")
                if data_collection_settings is not None:
                    raise ArgumentUsageError(
                        "--data-collection-settings can not be used without MSI auth.")
                if ampls_resource_id is not None:
                    raise ArgumentUsageError(
                        "--ampls-resource-id supported only in MSI auth mode.")
                ensure_container_insights_for_monitoring(
                    cmd, instance.addon_profiles[CONST_MONITORING_ADDON_NAME], subscription_id, resource_group_name, name, instance.location, aad_route=False)

        # adding a wait here since we rely on the result for role assignment
        result = LongRunningOperation(cmd.cli_ctx)(
            client.begin_create_or_update(resource_group_name, name, instance))

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


def _update_addons(cmd, instance, subscription_id, resource_group_name, name, addons, enable,
                   workspace_resource_id=None,
                   enable_msi_auth_for_monitoring=True,
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
                   no_wait=False,):
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

                cloud_name = cmd.cli_ctx.cloud.name
                if enable_msi_auth_for_monitoring and (cloud_name.lower() == 'ussec' or cloud_name.lower() == 'usnat'):
                    if instance.identity is not None and instance.identity.type is not None and instance.identity.type == "userassigned":
                        logger.warning(
                            "--enable_msi_auth_for_monitoring is not supported in %s cloud and continuing monitoring enablement without this flag.", cloud_name)
                        enable_msi_auth_for_monitoring = False

                addon_profile.config = {
                    CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID: workspace_resource_id}
                addon_profile.config[CONST_MONITORING_USING_AAD_MSI_AUTH] = "true" if enable_msi_auth_for_monitoring else "false"
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
                addon_profile = ManagedClusterAddonProfile(
                    enabled=True, config={})
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

    # null out the SP profile because otherwise validation complains
    instance.service_principal_profile = None

    return instance


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
            raise InvalidArgumentValueError(
                "--format can only be specified when requesting clusterUser credential.")
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
        kubeconfig_path = os.environ["KUBECONFIG"].split(os.pathsep)[0]
        if kubeconfig_path:
            logger.info(
                "The default path '%s' is replaced by '%s' defined in KUBECONFIG.", path, kubeconfig_path)
            path = kubeconfig_path
        else:
            logger.warning(
                "Invalid path '%s' defined in KUBECONFIG.", kubeconfig_path)

    if not credentialResults:
        raise CLIError("No Kubernetes credentials found.")
    try:
        kubeconfig = credentialResults.kubeconfigs[0].value.decode(
            encoding='UTF-8')
        _print_or_merge_credentials(
            path, kubeconfig, overwrite_existing, context_name)

        # Check if kubeconfig requires kubelogin with devicecode and convert it
        if uses_kubelogin_devicecode(kubeconfig):
            if which("kubelogin"):
                try:
                    # Run kubelogin convert-kubeconfig -l azurecli
                    subprocess.run(
                        ["kubelogin", "convert-kubeconfig", "-l", "azurecli"],
                        cwd=os.path.dirname(path),
                        check=True,
                    )
                    logger.warning("Converted kubeconfig to use Azure CLI authentication.")
                except subprocess.CalledProcessError as e:
                    logger.warning("Failed to convert kubeconfig with kubelogin: %s", str(e))
                except Exception as e:  # pylint: disable=broad-except
                    logger.warning("Error running kubelogin: %s", str(e))
            else:
                logger.warning(
                    "The kubeconfig uses devicecode authentication which requires kubelogin. "
                    "Please install kubelogin from https://github.com/Azure/kubelogin or run "
                    "'az aks install-cli' to install both kubectl and kubelogin. "
                    "If devicecode login fails, try running "
                    "'kubelogin convert-kubeconfig -l azurecli' to unblock yourself."
                )

    except (IndexError, ValueError):
        raise CLIError("Fail to find kubeconfig file.")


def uses_kubelogin_devicecode(kubeconfig: str) -> bool:
    try:
        config = yaml.safe_load(kubeconfig)

        # Check if users section exists and has at least one user
        if not config or not config.get('users') or len(config['users']) == 0:
            return False

        first_user = config['users'][0]
        user_info = first_user.get('user', {})
        exec_info = user_info.get('exec', {})

        # Check if command is kubelogin
        command = exec_info.get('command', '')
        if 'kubelogin' not in command:
            return False

        # Check if args contains --login and devicecode
        args = exec_info.get('args', [])
        # Join args into a string for easier pattern matching
        args_str = ' '.join(args)
        # Check for '--login devicecode' or '-l devicecode'
        if '--login devicecode' in args_str or '-l devicecode' in args_str:
            return True
        return False
    except (yaml.YAMLError, KeyError, TypeError, AttributeError) as e:
        # If there's any error parsing the kubeconfig, assume it doesn't require kubelogin
        logger.debug("Error parsing kubeconfig: %s", str(e))
        return False


def _handle_merge(existing, addition, key, replace):
    if not addition.get(key, False):
        return
    if key not in existing:
        raise FileOperationError(
            "No such key '{}' in existing config, please confirm whether it is a valid config file. "
            "May back up this config file, delete it and retry the command.".format(
                key
            )
        )
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
    except OSError as ex:
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
    if platform.system() != "Windows" and not os.path.islink(existing_file):
        existing_file_perms = "{:o}".format(
            stat.S_IMODE(os.lstat(existing_file).st_mode))
        if not existing_file_perms.endswith("600"):
            logger.warning(
                '%s has permissions "%s".\nIt should be readable and writable only by its owner.',
                existing_file,
                existing_file_perms,
            )

    with open(existing_file, 'w+') as stream:
        yaml.safe_dump(existing, stream, default_flow_style=False)

    current_context = addition.get('current-context', 'UNKNOWN')
    msg = 'Merged "{}" as current context in {}'.format(
        current_context, existing_file)
    logger.warning(msg)


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


def aks_check_acr(cmd, client, resource_group_name, name, acr, node_name=None):
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
            kubectl_minor_version = int(
                re.sub(r"\D", "", kubectl_version["clientVersion"]["minor"]))
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
                        "volumeMounts": [
                            {"name": "azurejson", "mountPath": "/etc/kubernetes"},
                            {"name": "sslcerts", "mountPath": "/etc/ssl/certs"},
                            {"name": "sfcerts", "mountPath": "/etc/pki"},
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
                    {"name": "sfcerts", "hostPath": {
                        "path": "/etc/pki", "type": "DirectoryOrCreate"}},
                ],
                "nodeSelector": {"kubernetes.io/os": "linux"},
            }
        }
        if node_name is not None:
            affinity = {
                "nodeAffinity": {
                    "requiredDuringSchedulingIgnoredDuringExecution": {
                        "nodeSelectorTerms": [
                            {
                                "matchExpressions": [
                                    {"key": "kubernetes.io/hostname",
                                        "operator": "In", "values": [node_name]}
                                ]
                            }
                        ]
                    }
                }
            }
            overrides["spec"]["affinity"] = affinity

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
            raise AzureInternalError(
                "Failed to check the ACR: {} Command output: {}".format(err, err.output))
        if output:
            print(output)
            # only return the output in test case "test_aks_create_attach_acr"
            test_hook_data = get_cmd_test_hook_data(
                "test_aks_create_attach_acr.hook")
            if test_hook_data:
                test_configs = test_hook_data.get("configs", None)
                if test_configs and test_configs.get("returnOutput", False):
                    return_msg = output
        else:
            raise AzureInternalError("Failed to check the ACR.")
    finally:
        os.close(fd)
    return return_msg


# install kubectl & kubelogin
def k8s_install_cli(cmd, client_version='latest', install_location=None, base_src_url=None,
                    kubelogin_version='latest', kubelogin_install_location=None,
                    kubelogin_base_src_url=None, gh_token=None):
    arch = get_arch_for_cli_binary()
    k8s_install_kubectl(cmd, client_version,
                        install_location, base_src_url, arch=arch)
    k8s_install_kubelogin(cmd, kubelogin_version,
                          kubelogin_install_location, kubelogin_base_src_url, arch=arch, gh_token=gh_token)


# determine the architecture for the binary based on platform.machine()
# currently only used to distinguish between amd64 and arm64 (386, arm, ppc64le, s390x not supported)
# Note: the results returned here may be inaccurate if the installed python is translated (e.g. by Rosetta)
def get_arch_for_cli_binary():
    arch = platform.machine().lower()
    if "amd64" in arch or "x86_64" in arch:
        formatted_arch = "amd64"
    elif "armv8" in arch or "aarch64" in arch or "arm64" in arch:
        formatted_arch = "arm64"
    else:
        raise CLIInternalError(
            "Unsupported architecture: '{}'. Currently only supports downloading the binary "
            "of arm64/amd64 architecture for linux/darwin/windows platform, please download "
            "the corresponding binary for other platforms or architectures by yourself".format(
                arch
            )
        )
    logger.warning(
        'The detected architecture of current device is "%s", and the binary for "%s" '
        'will be downloaded. If the detection is wrong, please download and install '
        'the binary corresponding to the appropriate architecture.',
        arch,
        formatted_arch,
    )
    return formatted_arch


# get the user path environment variable
def get_windows_user_path():
    reg_query_exp = "reg query HKCU\\Environment /v path"
    reg_regex_exp = r"REG\w+"
    try:
        reg_result = subprocess.run(reg_query_exp.split(
            " "), shell=True, check=True, capture_output=True, text=True)
    except Exception as e:
        raise CLIInternalError(
            "failed to perfrom reg query, error: {}".format(e))
    raw_user_path = reg_result.stdout.strip()
    # find the identifier where the user's path really starts
    m = re.search(reg_regex_exp, raw_user_path)
    identifier = m.group(0) if m else ""
    if not identifier:
        raise CLIInternalError("failed to parse reg query result")
    start_idx = raw_user_path.find(identifier)
    user_path = raw_user_path[start_idx + len(identifier):].strip()
    return user_path


# append the installation directory to the user path environment variable
def append_install_dir_to_windows_user_path(install_dir, binary_name):
    user_path = ""
    try:
        user_path = get_windows_user_path()
    # pylint: disable=broad-except
    except Exception as e:
        logger.debug("failed to get user path, error: %s", e)
        log_windows_post_installation_manual_steps_warning(
            install_dir, binary_name)
        # unable to get user path, skip appending user path
        return
    if install_dir in user_path:
        logger.debug(
            "installation directory '%s' already exists in user path", install_dir)
        return
    # keep user path style (with or without semicolon at the end)
    flag = user_path.endswith(";")
    setxexp = ["setx", "path", "{}{}{}{}".format(
        user_path, "" if flag else ";", install_dir, ";" if flag else "")]
    try:
        subprocess.run(setxexp, shell=True, check=True, capture_output=True)
        log_windows_successful_installation_warning(install_dir)
    # pylint: disable=broad-except
    except Exception as e:
        logger.debug("failed to set user path, error: %s", e)
        log_windows_post_installation_manual_steps_warning(
            install_dir, binary_name)


# handle system path issues after binary installation
def handle_windows_post_install(install_dir, binary_name):
    if not check_windows_install_dir(install_dir):
        append_install_dir_to_windows_user_path(install_dir, binary_name)


# check if the installation directory is in the system path
def check_windows_install_dir(install_dir):
    env_paths = os.environ['PATH'].split(';')
    return next((x for x in env_paths if x.lower().rstrip('\\') == install_dir.lower()), None)


def log_windows_successful_installation_warning(install_dir):
    logger.warning(
        'The installation directory "%s" has been successfully appended to the user path, '
        "the configuration will only take effect in the new command sessions. "
        "Please re-open the command window.", install_dir
    )


# pylint: disable=logging-format-interpolation
def log_windows_post_installation_manual_steps_warning(install_dir, binary_name):
    logger.warning(
        'Please add "{0}" to your search PATH so the `{1}` can be found. 2 options: \n'
        '    1. Run "set PATH=%PATH%;{0}" or "$env:path += \';{0}\'" for PowerShell. '
        "This is good for the current command session.\n"
        "    2. Update system PATH environment variable by following "
        '"Control Panel->System->Advanced->Environment Variables", and re-open the command window. '
        "You only need to do it once".format(install_dir, binary_name)
    )


def validate_install_location(install_location: str, exe_name: str) -> None:
    # check if the installation path is a directory
    if os.path.isdir(install_location):
        from azure.cli.command_modules.acs._params import _get_default_install_location
        raise InvalidArgumentValueError(
            'The installation location "{}" is a directory. Please specify a path '
            'including the binary filename e.g. "{}".'.format(
                install_location, _get_default_install_location(exe_name)
            )
        )
    # check if the binary filename in installation path is correct
    binary_name = os.path.basename(install_location)
    if binary_name != exe_name:
        logger.error(
            'The binary filename "%s" in install location does not match '
            'the expected binary name "%s".',
            binary_name,
            exe_name,
        )


# install kubectl
def k8s_install_kubectl(cmd, client_version='latest', install_location=None, source_url=None, arch=None):
    """
    Install kubectl, a command-line interface for Kubernetes clusters.
    """

    if not source_url:
        source_url = "https://dl.k8s.io/release"
        cloud_name = cmd.cli_ctx.cloud.name
        if cloud_name.lower() == 'azurechinacloud':
            source_url = 'https://mirror.azure.cn/kubernetes/kubectl'

    if client_version == 'latest':
        latest_version_url = source_url + '/stable.txt'
        logger.warning(
            'No version specified, will get the latest version of kubectl from "%s"', latest_version_url)
        version = _urlopen_read(source_url + '/stable.txt')
        client_version = version.decode('UTF-8').strip()
    else:
        client_version = "v%s" % client_version

    file_url = ''
    system = platform.system()
    if arch is None:
        arch = get_arch_for_cli_binary()
    base_url = source_url + f"/{{}}/bin/{{}}/{arch}/{{}}"

    # ensure installation directory exists
    install_dir, cli = os.path.dirname(
        install_location), os.path.basename(install_location)
    if not os.path.exists(install_dir):
        os.makedirs(install_dir)

    if system == 'Windows':
        binary_name = 'kubectl.exe'
        file_url = base_url.format(client_version, 'windows', binary_name)
    elif system == 'Linux':
        binary_name = 'kubectl'
        file_url = base_url.format(client_version, 'linux', binary_name)
    elif system == 'Darwin':
        binary_name = 'kubectl'
        file_url = base_url.format(client_version, 'darwin', binary_name)
    else:
        raise UnknownError("Unsupported system '{}'.".format(system))

    # validate install location
    validate_install_location(install_location, binary_name)

    logger.warning('Downloading client to "%s" from "%s"',
                   install_location, file_url)
    try:
        _urlretrieve(file_url, install_location)
        os.chmod(install_location,
                 os.stat(install_location).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError as ex:
        raise CLIError(
            'Connection error while attempting to download client ({})'.format(ex))

    if system == 'Windows':
        handle_windows_post_install(install_dir, cli)
    else:
        logger.warning('Please ensure that %s is in your search PATH, so the `%s` command can be found.',
                       install_dir, cli)


# install kubelogin
def k8s_install_kubelogin(cmd, client_version='latest', install_location=None, source_url=None, arch=None, gh_token=None):
    """
    Install kubelogin, a client-go credential (exec) plugin implementing azure authentication.
    """

    cloud_name = cmd.cli_ctx.cloud.name

    if not source_url:
        source_url = 'https://github.com/Azure/kubelogin/releases/download'
        if cloud_name.lower() == 'azurechinacloud':
            source_url = 'https://mirror.azure.cn/kubernetes/kubelogin'

    if client_version == 'latest':
        latest_release_url = 'https://api.github.com/repos/Azure/kubelogin/releases/latest'
        if cloud_name.lower() == 'azurechinacloud':
            latest_release_url = 'https://mirror.azure.cn/kubernetes/kubelogin/latest'
        logger.warning(
            'No version specified, will get the latest version of kubelogin from "%s"', latest_release_url)
        latest_release = _urlopen_read(latest_release_url, gh_token=gh_token)
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
    if arch is None:
        arch = get_arch_for_cli_binary()
    if system == 'Windows':
        sub_dir, binary_name = 'windows_amd64', 'kubelogin.exe'
    elif system == 'Linux':
        sub_dir, binary_name = f'linux_{arch}', 'kubelogin'
    elif system == 'Darwin':
        sub_dir, binary_name = f'darwin_{arch}', 'kubelogin'
    else:
        raise UnknownError("Unsupported system '{}'.".format(system))

    # validate install location
    validate_install_location(install_location, binary_name)

    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            download_path = os.path.join(tmp_dir, 'kubelogin.zip')
            logger.warning('Downloading client to "%s" from "%s"',
                           download_path, file_url)
            _urlretrieve(file_url, download_path)
        except OSError as ex:
            raise CLIError(
                'Connection error while attempting to download client ({})'.format(ex))
        _unzip(download_path, tmp_dir)
        download_path = os.path.join(tmp_dir, 'bin', sub_dir, binary_name)
        logger.warning('Moving binary to "%s" from "%s"',
                       install_location, download_path)
        shutil.move(download_path, install_location)
    os.chmod(install_location, os.stat(install_location).st_mode |
             stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    if system == 'Windows':
        handle_windows_post_install(install_dir, cli)
    else:
        logger.warning('Please ensure that %s is in your search PATH, so the `%s` command can be found.',
                       install_dir, cli)


def _ssl_context():
    return ssl.create_default_context()


def _urlopen_read(url, context=None, gh_token=None):
    if context is None:
        context = _ssl_context()
    try:
        from urllib.request import Request
        request = Request(url)
        if gh_token:
            request.add_header('Authorization', f'Bearer {gh_token}')
        return urlopen(request, context=context).read()
    except URLError as ex:
        error_msg = str(ex)
        if "[SSL: CERTIFICATE_VERIFY_FAILED]" in error_msg and "unable to get local issuer certificate" in error_msg:
            raise ClientRequestError(
                "SSL certificate verification failed. Please ensure that the python interpreter used by azure-cli uses "
                "the appropriate cert store when making requests. For more details, please refer to "
                "https://github.com/Azure/azure-cli/issues/19305"
            )
        raise ex


def _urlretrieve(url, filename, gh_token=None):
    with open(filename, "wb") as f:
        f.write(_urlopen_read(url, gh_token=gh_token))


def _unzip(src, dest):
    logger.debug('Extracting %s to %s.', src, dest)
    system = platform.system()
    if system in ('Linux', 'Darwin', 'Windows'):
        with zipfile.ZipFile(src, 'r') as zipObj:
            zipObj.extractall(dest)
    else:
        raise CLIError('The current system is not supported.')


def aks_rotate_certs(cmd, client, resource_group_name, name, no_wait=True):
    return sdk_no_wait(no_wait, client.begin_rotate_cluster_certificates, resource_group_name, name)


def aks_get_versions(cmd, client, location):
    return client.list_kubernetes_versions(location)


def aks_runcommand(cmd, client, resource_group_name, name, command_string="", command_files=None, no_wait=False):
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

    polling_interval = 5
    retry_total = 0

    command_result_poller = sdk_no_wait(
        no_wait, client.begin_run_command, resource_group_name, name, request_payload,
        # NOTE: Note sure if retry_total is used in ARMPolling
        polling=ARMPolling(polling_interval, lro_options={
                           "final-state-via": "location"}, lro_algorithms=[RunCommandLocationPolling()], retry_total=retry_total),
        polling_interval=polling_interval,
        retry_total=retry_total
    )
    if no_wait:
        # pylint: disable=protected-access
        command_result_polling_url = command_result_poller.polling_method()._initial_response.http_response.headers[
            "location"
        ]
        command_id_regex = re.compile(r"commandResults\/(\w*)\?")
        command_id = command_id_regex.findall(command_result_polling_url)[0]
        _aks_command_result_in_progess_helper(
            client, resource_group_name, name, command_id)
        return

    spinner = Spinner(label='Running', stream=sys.stderr, hide_cursor=False)
    progress_controller = cmd.cli_ctx.get_progress_controller(
        det=False, spinner=spinner)

    now = datetime.datetime.now()
    progress_controller.begin()
    while not command_result_poller.done():
        if datetime.datetime.now() - now >= datetime.timedelta(seconds=300):
            break

        progress_controller.add(message=command_result_poller.status())
        progress_controller.update()
        time.sleep(0.5)

    progress_controller.end()
    return _print_command_result(cmd.cli_ctx, command_result_poller.result(timeout=0))


def aks_command_result(cmd, client, resource_group_name, name, command_id=""):
    if not command_id:
        raise ValidationError('CommandID cannot be empty.')

    commandResult = client.get_command_result(
        resource_group_name, name, command_id)
    if commandResult is None:
        _aks_command_result_in_progess_helper(
            client, resource_group_name, name, command_id)
        return
    return _print_command_result(cmd.cli_ctx, commandResult)


def _aks_command_result_in_progess_helper(client, resource_group_name, name, command_id):
    # pylint: disable=unused-argument
    def command_result_direct_response_handler(pipeline_response, *args, **kwargs):
        deserialized_data = pipeline_response.context.get(
            "deserialized_data", {})
        if deserialized_data:
            provisioning_state = deserialized_data.get(
                "properties", {}).get("provisioningState", None)
            started_at = deserialized_data.get(
                "properties", {}).get("startedAt", None)
            print(
                f"command id: {command_id}, started at: {started_at}, status: {provisioning_state}")
            print(
                f"Please use command \"az aks command result -g {resource_group_name} -n {name} -i {command_id}\" "
                "to get the future execution result"
            )
        else:
            print(
                f"failed to fetch command result for command id: {command_id}")
    client.get_command_result(
        resource_group_name, name, command_id, cls=command_result_direct_response_handler)


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
    print(f"{colorama.Fore.BLUE}command (id: {commandResult.id}) is in {commandResult.provisioning_state} state{colorama.Style.RESET_ALL}")
    return


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


# legacy: dev space command
DEV_SPACES_EXTENSION_NAME = 'dev-spaces'
DEV_SPACES_EXTENSION_MODULE = 'azext_dev_spaces.custom'


# legacy: dev space command
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


# legacy: dev space command
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


# legacy: dev space command
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


# legacy: dev space command
def _install_dev_spaces_extension(cmd, extension_name):
    try:
        from azure.cli.core.extension import operations
        operations.add_extension(cmd=cmd, extension_name=extension_name)
    except Exception:  # nopa pylint: disable=broad-except
        return False
    return True


# legacy: dev space command
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


# legacy: dev space command
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


def aks_agentpool_add(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    nodepool_name,
    kubernetes_version=None,
    node_vm_size=None,
    vm_sizes=None,
    vm_set_type=None,
    os_type=None,
    os_sku=None,
    snapshot_id=None,
    vnet_subnet_id=None,
    pod_subnet_id=None,
    pod_ip_allocation_mode=None,
    enable_node_public_ip=False,
    node_public_ip_prefix_id=None,
    enable_cluster_autoscaler=False,
    min_count=None,
    max_count=None,
    node_count=3,
    priority=CONST_SCALE_SET_PRIORITY_REGULAR,
    eviction_policy=CONST_SPOT_EVICTION_POLICY_DELETE,
    spot_max_price=float("nan"),
    labels=None,
    tags=None,
    node_taints=None,
    message_of_the_day=None,
    node_osdisk_type=None,
    node_osdisk_size=None,
    max_surge=None,
    max_unavailable=None,
    drain_timeout=None,
    node_soak_duration=None,
    undrainable_node_behavior=None,
    mode=CONST_NODEPOOL_MODE_USER,
    scale_down_mode=CONST_SCALE_DOWN_MODE_DELETE,
    max_pods=None,
    zones=None,
    ppg=None,
    enable_encryption_at_host=False,
    enable_ultra_ssd=False,
    enable_fips_image=False,
    kubelet_config=None,
    linux_os_config=None,
    no_wait=False,
    aks_custom_headers=None,
    host_group_id=None,
    crg_id=None,
    gpu_instance_profile=None,
    allowed_host_ports=None,
    asg_ids=None,
    node_public_ip_tags=None,
    disable_windows_outbound_nat=False,
    workload_runtime=None,
    # trusted launch
    enable_vtpm=False,
    enable_secure_boot=False,
    # etag headers
    if_match=None,
    if_none_match=None,
    # gpu driver
    gpu_driver=None,
    # static egress gateway - gateway-mode pool
    gateway_prefix_size=None,
    # local DNS
    localdns_config=None,
):
    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()

    # decorator pattern
    from azure.cli.command_modules.acs.agentpool_decorator import AKSAgentPoolAddDecorator
    from azure.cli.command_modules.acs._consts import AgentPoolDecoratorMode
    aks_agentpool_add_decorator = AKSAgentPoolAddDecorator(
        cmd=cmd,
        client=client,
        raw_parameters=raw_parameters,
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        agentpool_decorator_mode=AgentPoolDecoratorMode.STANDALONE,
    )
    try:
        # construct agentpool profile
        agentpool = aks_agentpool_add_decorator.construct_agentpool_profile_default()
    except DecoratorEarlyExitException:
        # exit gracefully
        return None
    # send request to add a real agentpool
    return aks_agentpool_add_decorator.add_agentpool(agentpool)


def aks_agentpool_update(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    nodepool_name,
    enable_cluster_autoscaler=False,
    disable_cluster_autoscaler=False,
    update_cluster_autoscaler=False,
    min_count=None,
    max_count=None,
    labels=None,
    tags=None,
    node_taints=None,
    max_surge=None,
    max_unavailable=None,
    drain_timeout=None,
    node_soak_duration=None,
    undrainable_node_behavior=None,
    mode=None,
    scale_down_mode=None,
    no_wait=False,
    aks_custom_headers=None,
    allowed_host_ports=None,
    asg_ids=None,
    os_sku=None,
    enable_fips_image=False,
    disable_fips_image=False,
    # trusted launch
    enable_vtpm=False,
    disable_vtpm=False,
    enable_secure_boot=False,
    disable_secure_boot=False,
    # etag headers
    if_match=None,
    if_none_match=None,
    # local DNS
    localdns_config=None,
    gpu_driver=None,
):
    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()

    # decorator pattern
    from azure.cli.command_modules.acs.agentpool_decorator import AKSAgentPoolUpdateDecorator
    from azure.cli.command_modules.acs._consts import AgentPoolDecoratorMode
    aks_agentpool_update_decorator = AKSAgentPoolUpdateDecorator(
        cmd=cmd,
        client=client,
        raw_parameters=raw_parameters,
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        agentpool_decorator_mode=AgentPoolDecoratorMode.STANDALONE,
    )
    try:
        # update agentpool profile
        agentpool = aks_agentpool_update_decorator.update_agentpool_profile_default()
    except DecoratorEarlyExitException:
        # exit gracefully
        return None
    # send request to update the real agentpool
    return aks_agentpool_update_decorator.update_agentpool(agentpool)


def aks_agentpool_get_upgrade_profile(cmd, client, resource_group_name, cluster_name, nodepool_name):
    return client.get_upgrade_profile(resource_group_name, cluster_name, nodepool_name)


def aks_agentpool_upgrade(cmd, client, resource_group_name, cluster_name,
                          nodepool_name,
                          kubernetes_version='',
                          node_image_only=False,
                          max_surge=None,
                          max_unavailable=None,
                          drain_timeout=None,
                          node_soak_duration=None,
                          undrainable_node_behavior=None,
                          snapshot_id=None,
                          no_wait=False,
                          aks_custom_headers=None,
                          yes=False,
                          if_match=None,
                          if_none_match=None):
    AgentPoolUpgradeSettings = cmd.get_models(
        "AgentPoolUpgradeSettings",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="managed_clusters",
    )
    if kubernetes_version != '' and node_image_only:
        raise MutuallyExclusiveArgumentError(
            'Conflicting flags. Upgrading the Kubernetes version will also '
            'upgrade node image version. If you only want to upgrade the '
            'node version please use the "--node-image-only" option only.'
        )

    # Note: we exclude this option because node image upgrade can't accept nodepool put fields like max surge
    hasUpgradeSetting = max_surge or drain_timeout or node_soak_duration or undrainable_node_behavior or max_unavailable
    if hasUpgradeSetting and node_image_only:
        raise MutuallyExclusiveArgumentError(
            'Conflicting flags. Unable to specify max-surge/drain-timeout/node-soak-duration/max-unavailable with node-image-only.'
            'If you want to use max-surge/drain-timeout/node-soak-duration with a node image upgrade, please first '
            'update max-surge/drain-timeout/node-soak-duration/max-unavailable using "az aks nodepool update --max-surge/--drain-timeout/--node-soak-duration/--max-unavailable".'
        )

    if node_image_only:
        return _upgrade_single_nodepool_image_version(no_wait,
                                                      client,
                                                      resource_group_name,
                                                      cluster_name,
                                                      nodepool_name,
                                                      snapshot_id)

    # load model CreationData, for nodepool snapshot
    CreationData = cmd.get_models(
        "CreationData",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="managed_clusters",
    )

    creationData = None
    if snapshot_id:
        snapshot = get_snapshot_by_snapshot_id(cmd.cli_ctx, snapshot_id)
        if not kubernetes_version and not node_image_only:
            kubernetes_version = snapshot.kubernetes_version

        creationData = CreationData(
            source_resource_id=snapshot_id
        )

    instance = client.get(resource_group_name, cluster_name, nodepool_name)

    if kubernetes_version == '' or instance.orchestrator_version == kubernetes_version:
        msg = "The new kubernetes version is the same as the current kubernetes version."
        if instance.provisioning_state == "Succeeded":
            msg = "The cluster is already on version {} and is not in a failed state. No operations will occur when upgrading to the same version if the cluster is not in a failed state.".format(
                instance.orchestrator_version)
        elif instance.provisioning_state == "Failed":
            msg = "Cluster currently in failed state. Proceeding with upgrade to existing version {} to attempt resolution of failed cluster state.".format(
                instance.orchestrator_version)
        if not yes and not prompt_y_n(msg):
            return None

    instance.orchestrator_version = kubernetes_version
    instance.creation_data = creationData

    if not instance.upgrade_settings:
        instance.upgrade_settings = AgentPoolUpgradeSettings()

    if max_surge:
        instance.upgrade_settings.max_surge = max_surge
    if drain_timeout:
        instance.upgrade_settings.drain_timeout_in_minutes = drain_timeout
    if isinstance(node_soak_duration, int) and node_soak_duration >= 0:
        instance.upgrade_settings.node_soak_duration_in_minutes = node_soak_duration
    if undrainable_node_behavior:
        instance.upgrade_settings.undrainable_node_behavior = undrainable_node_behavior

    # custom headers
    aks_custom_headers = extract_comma_separated_string(
        aks_custom_headers,
        enable_strip=True,
        extract_kv=True,
        default_value={},
        allow_appending_values_to_same_key=True,
    )

    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        nodepool_name,
        instance,
        headers=aks_custom_headers,
        if_match=if_match,
        if_none_match=if_none_match,
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
    if instance.type_properties_type == CONST_VIRTUAL_MACHINES:
        if len(instance.virtual_machines_profile.scale.manual) == 1:
            instance.virtual_machines_profile.scale.manual[0].count = new_node_count
        else:
            raise ClientRequestError("Cannot scale virtual machines node pool with more than one size.")
    else:
        instance.count = new_node_count  # pylint: disable=no-member
    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        nodepool_name,
        instance,
    )


def aks_agentpool_start(cmd,   # pylint: disable=unused-argument
                        client,
                        resource_group_name,
                        cluster_name,
                        nodepool_name,
                        aks_custom_headers=None,
                        no_wait=False):
    agentpool_exists = False
    instances = client.list(resource_group_name, cluster_name)
    for agentpool_profile in instances:
        if agentpool_profile.name.lower() == nodepool_name.lower():
            agentpool_exists = True
            break
    if not agentpool_exists:
        raise InvalidArgumentValueError(
            "Node pool {} doesnt exist, use 'aks nodepool list' to get current node pool list".format(nodepool_name))
    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    PowerState = cmd.get_models('PowerState', operation_group='agent_pools')
    power_state = PowerState(code="Running")
    instance.power_state = power_state
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, cluster_name, nodepool_name, instance, headers=None)


def aks_agentpool_stop(cmd,   # pylint: disable=unused-argument
                       client,
                       resource_group_name,
                       cluster_name,
                       nodepool_name,
                       aks_custom_headers=None,
                       no_wait=False):
    agentpool_exists = False
    instances = client.list(resource_group_name, cluster_name)
    for agentpool_profile in instances:
        if agentpool_profile.name.lower() == nodepool_name.lower():
            agentpool_exists = True
            break
    if not agentpool_exists:
        raise InvalidArgumentValueError(
            "Node pool {} doesnt exist, use 'aks nodepool list' to get current node pool list".format(nodepool_name))
    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    PowerState = cmd.get_models('PowerState', operation_group='agent_pools')
    power_state = PowerState(code="Stopped")
    instance.power_state = power_state
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, cluster_name, nodepool_name, instance, headers=None)


def aks_agentpool_delete(cmd, client, resource_group_name, cluster_name,
                         nodepool_name,
                         no_wait=False,
                         if_match=None,
                         ignore_pdb=None):
    agentpool_exists = False
    instances = client.list(resource_group_name, cluster_name)
    for agentpool_profile in instances:
        if agentpool_profile.name.lower() == nodepool_name.lower():
            agentpool_exists = True
            break

    if not agentpool_exists:
        raise CLIError("Node pool {} doesnt exist, "
                       "use 'aks nodepool list' to get current node pool list".format(nodepool_name))

    if cmd.cli_ctx.cloud.profile != "latest":
        return sdk_no_wait(no_wait, client.begin_delete, resource_group_name, cluster_name, nodepool_name)

    return sdk_no_wait(no_wait, client.begin_delete, resource_group_name, cluster_name, nodepool_name, if_match=if_match, ignore_pod_disruption_budget=ignore_pdb)


def aks_agentpool_operation_abort(cmd,
                                  client,
                                  resource_group_name,
                                  cluster_name,
                                  nodepool_name,
                                  no_wait=False):
    PowerState = cmd.get_models(
        "PowerState",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="agent_pools",
    )

    agentpool_exists = False
    instances = client.list(resource_group_name, cluster_name)
    for agentpool_profile in instances:
        if agentpool_profile.name.lower() == nodepool_name.lower():
            agentpool_exists = True
            break
    if not agentpool_exists:
        raise InvalidArgumentValueError(
            "Node pool {} doesnt exist, use 'aks nodepool list' to get current node pool list".format(nodepool_name))
    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    power_state = PowerState(code="Running")
    instance.power_state = power_state
    return sdk_no_wait(no_wait, client.begin_abort_latest_operation, resource_group_name, cluster_name, nodepool_name)


def aks_operation_abort(cmd,   # pylint: disable=unused-argument
                        client,
                        resource_group_name,
                        name,
                        no_wait=False):
    PowerState = cmd.get_models(
        "PowerState",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="managed_clusters",
    )

    instance = client.get(resource_group_name, name)
    power_state = PowerState(code="Running")
    if instance is None:
        raise InvalidArgumentValueError(
            "Cluster {} doesnt exist, use 'aks list' to get current cluster list".format(name))
    instance.power_state = power_state
    return sdk_no_wait(no_wait, client.begin_abort_latest_operation, resource_group_name, name)


def aks_agentpool_delete_machines(cmd,   # pylint: disable=unused-argument
                                  client,
                                  resource_group_name,
                                  cluster_name,
                                  nodepool_name,
                                  machine_names,
                                  no_wait=False):
    agentpool_exists = False
    instances = client.list(resource_group_name, cluster_name)
    for agentpool_profile in instances:
        if agentpool_profile.name.lower() == nodepool_name.lower():
            agentpool_exists = True
            break

    if not agentpool_exists:
        raise ResourceNotFoundError(
            f"Node pool {nodepool_name} doesn't exist, "
            "use 'az aks nodepool list' to get current node pool list"
        )

    if len(machine_names) == 0:
        raise RequiredArgumentMissingError(
            "--machine-names doesn't provide, "
            "use 'az aks machine list' to get current machine list"
        )

    AgentPoolDeleteMachinesParameter = cmd.get_models(
        "AgentPoolDeleteMachinesParameter",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="agent_pools",
    )

    machines = AgentPoolDeleteMachinesParameter(machine_names=machine_names)
    return sdk_no_wait(
        no_wait,
        client.begin_delete_machines,
        resource_group_name,
        cluster_name,
        nodepool_name,
        machines,
    )


def aks_agentpool_manual_scale_add(cmd,
                                   client,
                                   resource_group_name,
                                   cluster_name,
                                   nodepool_name,
                                   vm_sizes,
                                   node_count,
                                   no_wait=False):
    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    if instance.type_properties_type != CONST_VIRTUAL_MACHINES:
        raise ClientRequestError("Cannot add manual to a non-virtualmachines node pool.")

    ManualScaleProfile = cmd.get_models(
        "ManualScaleProfile",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="managed_clusters",
    )
    sizes = [x.strip() for x in vm_sizes.split(",")]
    if len(sizes) != 1:
        raise ClientRequestError("We only accept single sku size for manual profile.")
    new_manual_scale_profile = ManualScaleProfile(size=sizes[0], count=int(node_count))
    instance.virtual_machines_profile.scale.manual.append(new_manual_scale_profile)

    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        nodepool_name,
        instance
    )


def aks_agentpool_manual_scale_update(cmd,    # pylint: disable=unused-argument
                                      client,
                                      resource_group_name,
                                      cluster_name,
                                      nodepool_name,
                                      current_vm_sizes,
                                      vm_sizes=None,
                                      node_count=None,
                                      no_wait=False):
    if vm_sizes is None and node_count is None:
        raise RequiredArgumentMissingError("specify --vm-sizes or --node-count or both.")

    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    if instance.type_properties_type != CONST_VIRTUAL_MACHINES:
        raise ClientRequestError("Cannot update manual in a non-virtualmachines node pool.")

    _current_vm_sizes = [x.strip().lower() for x in current_vm_sizes.split(",")]
    if len(_current_vm_sizes) != 1:
        raise InvalidArgumentValueError(f"We only accept single sku size for manual profile. {current_vm_sizes} is invalid.")

    _vm_sizes = [x.strip().lower() for x in vm_sizes.split(",")] if vm_sizes else []
    if len(_vm_sizes) != 1:
        raise InvalidArgumentValueError(f"We only accept single sku size for manual profile. {vm_sizes} is invalid.")

    manual_exists = False
    for m in instance.virtual_machines_profile.scale.manual:
        if m.size.lower() == _current_vm_sizes[0]:
            manual_exists = True
            if vm_sizes:
                m.size = _vm_sizes[0]
            if node_count:
                m.count = int(node_count)
            break
    if not manual_exists:
        raise InvalidArgumentValueError(f"Manual with size {_current_vm_sizes[0]} doesn't exist in node pool {nodepool_name}.")

    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        nodepool_name,
        instance
    )


def aks_agentpool_manual_scale_delete(cmd,    # pylint: disable=unused-argument
                                      client,
                                      resource_group_name,
                                      cluster_name,
                                      nodepool_name,
                                      current_vm_sizes,
                                      no_wait=False):
    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    if instance.type_properties_type != CONST_VIRTUAL_MACHINES:
        raise CLIError("Cannot delete manual in a non-virtualmachines node pool.")

    _current_vm_sizes = [x.strip().lower() for x in current_vm_sizes.split(",")]
    if len(_current_vm_sizes) != 1:
        raise InvalidArgumentValueError(f"We only accept single sku size for manual profile. {current_vm_sizes} is invalid.")

    manual_exists = False
    for m in instance.virtual_machines_profile.scale.manual:
        if m.size.lower() == _current_vm_sizes[0]:
            manual_exists = True
            instance.virtual_machines_profile.scale.manual.remove(m)
            break
    if not manual_exists:
        raise InvalidArgumentValueError(f"Manual with size {_current_vm_sizes[0]} doesn't exist in node pool {nodepool_name}.")
    if len(instance.virtual_machines_profile.scale.manual) == 0:
        raise InvalidArgumentValueError(f"Cannot delete the last manual profile in node pool {nodepool_name}. ")

    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        nodepool_name,
        instance
    )


def aks_agentpool_show(cmd, client, resource_group_name, cluster_name, nodepool_name):
    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    return instance


def aks_agentpool_list(cmd, client, resource_group_name, cluster_name):
    return client.list(resource_group_name, cluster_name)


def aks_nodepool_snapshot_create(cmd,    # pylint: disable=too-many-locals,too-many-statements,too-many-branches
                                 client,
                                 resource_group_name,
                                 snapshot_name,
                                 nodepool_id,
                                 location=None,
                                 tags=None,
                                 aks_custom_headers=None,
                                 no_wait=False):

    rg_location = get_rg_location(cmd.cli_ctx, resource_group_name)
    if location is None:
        location = rg_location

    # load model CreationData, Snapshot
    CreationData = cmd.get_models(
        "CreationData",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="managed_clusters",
    )
    Snapshot = cmd.get_models(
        "Snapshot",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="managed_clusters",
    )

    creationData = CreationData(
        source_resource_id=nodepool_id
    )

    snapshot = Snapshot(
        name=snapshot_name,
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
        allow_appending_values_to_same_key=True,
    )
    return client.create_or_update(resource_group_name, snapshot_name, snapshot, headers=aks_custom_headers)


def aks_nodepool_snapshot_update(cmd, client, resource_group_name, snapshot_name, tags):   # pylint: disable=unused-argument
    TagsObject = cmd.get_models(
        "TagsObject",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="snapshots",
    )
    tagsObject = TagsObject(
        tags=tags
    )

    snapshot = client.update_tags(
        resource_group_name, snapshot_name, tagsObject)
    return snapshot


def aks_nodepool_snapshot_show(cmd, client, resource_group_name, snapshot_name):   # pylint: disable=unused-argument
    snapshot = client.get(resource_group_name, snapshot_name)
    return snapshot


def aks_nodepool_snapshot_delete(cmd,    # pylint: disable=unused-argument
                                 client,
                                 resource_group_name,
                                 snapshot_name,
                                 no_wait=False,
                                 yes=False):

    msg = 'This will delete the snapshot "{}" in resource group "{}", Are you sure?'.format(
        snapshot_name, resource_group_name)
    if not yes and not prompt_y_n(msg, default="n"):
        return None

    return client.delete(resource_group_name, snapshot_name)


def aks_nodepool_snapshot_list(cmd, client, resource_group_name=None):  # pylint: disable=unused-argument
    if resource_group_name is None or resource_group_name == '':
        return client.list()

    return client.list_by_resource_group(resource_group_name)


def aks_rotate_service_account_signing_keys(cmd, client, resource_group_name, name, no_wait=True):
    return sdk_no_wait(no_wait, client.begin_rotate_service_account_signing_keys, resource_group_name, name)


def aks_trustedaccess_role_list(cmd, client, location):  # pylint: disable=unused-argument
    return client.list(location)


def aks_trustedaccess_role_binding_list(cmd, client, resource_group_name, cluster_name):   # pylint: disable=unused-argument
    return client.list(resource_group_name, cluster_name)


def aks_trustedaccess_role_binding_get(cmd, client, resource_group_name, cluster_name, role_binding_name):
    return client.get(resource_group_name, cluster_name, role_binding_name)


def aks_trustedaccess_role_binding_create(cmd, client, resource_group_name, cluster_name, role_binding_name,
                                          source_resource_id, roles):
    TrustedAccessRoleBinding = cmd.get_models(
        "TrustedAccessRoleBinding",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="trusted_access_role_bindings",
    )
    existedBinding = None
    try:
        existedBinding = client.get(
            resource_group_name, cluster_name, role_binding_name)
    except ResourceNotFoundErrorAzCore:
        pass

    if existedBinding:
        raise InvalidArgumentValueError("TrustedAccess RoleBinding " + role_binding_name +
                                        " already existed, please use 'az aks trustedaccess rolebinding update' command to update!")

    roleList = roles.split(',')
    roleBinding = TrustedAccessRoleBinding(
        source_resource_id=source_resource_id, roles=roleList)
    return client.begin_create_or_update(resource_group_name, cluster_name, role_binding_name, roleBinding)


def aks_trustedaccess_role_binding_update(cmd, client, resource_group_name, cluster_name, role_binding_name, roles):
    TrustedAccessRoleBinding = cmd.get_models(
        "TrustedAccessRoleBinding",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="trusted_access_role_bindings",
    )
    existedBinding = client.get(
        resource_group_name, cluster_name, role_binding_name)

    roleList = roles.split(',')
    roleBinding = TrustedAccessRoleBinding(
        source_resource_id=existedBinding.source_resource_id, roles=roleList)
    return client.begin_create_or_update(resource_group_name, cluster_name, role_binding_name, roleBinding)


def aks_trustedaccess_role_binding_delete(cmd, client, resource_group_name, cluster_name, role_binding_name):
    return client.begin_delete(resource_group_name, cluster_name, role_binding_name)


def aks_mesh_enable(
        cmd,
        client,
        resource_group_name,
        name,
        revision=None,
        key_vault_id=None,
        ca_cert_object_name=None,
        ca_key_object_name=None,
        root_cert_object_name=None,
        cert_chain_object_name=None
):
    instance = client.get(resource_group_name, name)
    addon_profiles = instance.addon_profiles
    if key_vault_id is not None and ca_cert_object_name is not None and ca_key_object_name is not None and root_cert_object_name is not None and cert_chain_object_name is not None:
        if not addon_profiles or not addon_profiles[CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME] or not addon_profiles[CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME].enabled:
            raise CLIError(
                'AzureKeyvaultSecretsProvider addon is required for Azure Service Mesh plugin certificate authority feature.')

    return _aks_mesh_update(cmd,
                            client,
                            resource_group_name,
                            name,
                            key_vault_id,
                            ca_cert_object_name,
                            ca_key_object_name,
                            root_cert_object_name,
                            cert_chain_object_name,
                            revision=revision,
                            enable_azure_service_mesh=True)


def aks_mesh_disable(
        cmd,
        client,
        resource_group_name,
        name,
):
    return _aks_mesh_update(cmd, client, resource_group_name, name, disable_azure_service_mesh=True)


def aks_mesh_enable_ingress_gateway(
        cmd,
        client,
        resource_group_name,
        name,
        ingress_gateway_type,
):
    return _aks_mesh_update(
        cmd,
        client,
        resource_group_name,
        name,
        enable_ingress_gateway=True,
        ingress_gateway_type=ingress_gateway_type)


def aks_mesh_disable_ingress_gateway(
        cmd,
        client,
        resource_group_name,
        name,
        ingress_gateway_type,
):
    return _aks_mesh_update(
        cmd,
        client,
        resource_group_name,
        name,
        disable_ingress_gateway=True,
        ingress_gateway_type=ingress_gateway_type)


def aks_mesh_enable_egress_gateway(
        cmd,
        client,
        resource_group_name,
        name,
        istio_egressgateway_name,
        istio_egressgateway_namespace,
        gateway_configuration_name,
):
    return _aks_mesh_update(
        cmd,
        client,
        resource_group_name,
        name,
        enable_egress_gateway=True,
        istio_egressgateway_name=istio_egressgateway_name,
        istio_egressgateway_namespace=istio_egressgateway_namespace,
        gateway_configuration_name=gateway_configuration_name)


def aks_mesh_disable_egress_gateway(
        cmd,
        client,
        resource_group_name,
        name,
        istio_egressgateway_name,
        istio_egressgateway_namespace,
):
    return _aks_mesh_update(
        cmd,
        client,
        resource_group_name,
        name,
        istio_egressgateway_name=istio_egressgateway_name,
        istio_egressgateway_namespace=istio_egressgateway_namespace,
        disable_egress_gateway=True)


def aks_mesh_get_revisions(
        cmd,
        client,
        location
):
    revisonProfiles = client.list_mesh_revision_profiles(location)
    # 'revisonProfiles' is an ItemPaged object
    revisions = []
    # Iterate over items within pages
    for page in revisonProfiles.by_page():
        for item in page:
            revisions.append(item)

    if revisions:
        return revisions[0].properties

    return None


def check_iterator(iterator):
    import itertools
    try:
        first = next(iterator)
    except StopIteration:   # iterator is empty
        return True, iterator
    except TypeError:       # iterator is not iterable, e.g. None
        return True, iterator
    return False, itertools.chain([first], iterator)


def aks_mesh_get_upgrades(
        cmd,
        client,
        resource_group_name,
        name
):
    upgradeProfiles = client.list_mesh_upgrade_profiles(
        resource_group_name, name)
    is_empty, upgradeProfiles = check_iterator(upgradeProfiles)
    if is_empty:
        logger.warning("No mesh upgrade profiles found for the cluster '%s' " +
                       "in the resource group '%s'.", name, resource_group_name)
        return None
    upgrade = next(upgradeProfiles, None)
    if upgrade:
        return upgrade.properties
    return None


def aks_mesh_upgrade_start(
        cmd,
        client,
        resource_group_name,
        name,
        revision
):
    return _aks_mesh_update(
        cmd,
        client,
        resource_group_name,
        name,
        revision=revision,
        mesh_upgrade_command=CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_START)


def aks_mesh_upgrade_complete(
        cmd,
        client,
        resource_group_name,
        name,
        yes=False
):
    return _aks_mesh_update(
        cmd,
        client,
        resource_group_name,
        name,
        yes=yes,
        mesh_upgrade_command=CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_COMPLETE)


def aks_mesh_upgrade_rollback(
        cmd,
        client,
        resource_group_name,
        name,
        yes=False
):
    return _aks_mesh_update(
        cmd,
        client,
        resource_group_name,
        name,
        yes=yes,
        mesh_upgrade_command=CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_ROLLBACK)


def _aks_mesh_get_supported_revisions(
        cmd,
        client,
        location):

    revisions = aks_mesh_get_revisions(cmd, client, location)
    supported_revisions = [r.revision for r in revisions.mesh_revisions]
    return supported_revisions


def _aks_mesh_update(
        cmd,
        client,
        resource_group_name,
        name,
        key_vault_id=None,
        ca_cert_object_name=None,
        ca_key_object_name=None,
        root_cert_object_name=None,
        cert_chain_object_name=None,
        enable_azure_service_mesh=None,
        disable_azure_service_mesh=None,
        enable_ingress_gateway=None,
        disable_ingress_gateway=None,
        ingress_gateway_type=None,
        enable_egress_gateway=None,
        disable_egress_gateway=None,
        istio_egressgateway_name=None,
        istio_egressgateway_namespace=None,
        gateway_configuration_name=None,
        revision=None,
        yes=False,
        mesh_upgrade_command=None,
):
    raw_parameters = locals()

    from azure.cli.command_modules.acs.managed_cluster_decorator import AKSManagedClusterUpdateDecorator

    aks_update_decorator = AKSManagedClusterUpdateDecorator(
        cmd=cmd,
        client=client,
        raw_parameters=raw_parameters,
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
    )

    try:
        mc = aks_update_decorator.fetch_mc()
        mc = aks_update_decorator.update_azure_service_mesh_profile(mc)

        # check for unsupported asm revision once the smp in mc object has been updated
        # skip the warning incase upgrade is in progress
        service_mesh_profile = mc.service_mesh_profile
        if (
            service_mesh_profile and
            service_mesh_profile.mode == CONST_AZURE_SERVICE_MESH_MODE_ISTIO and
            service_mesh_profile.istio and
            service_mesh_profile.istio.revisions and
            len(service_mesh_profile.istio.revisions) == 1
        ):
            revision = service_mesh_profile.istio.revisions[0]
            supported_revisions = _aks_mesh_get_supported_revisions(
                cmd, client, mc.location)
            if revision not in supported_revisions:
                msg = (
                    f"Istio mesh revision {revision} currently in use in your cluster is no longer supported.\n"
                    "Please upgrade for continued support. Use `az aks mesh get-upgrades` to check for available "
                    "upgrades.\nMore information about mesh upgrades and version support can be found here:"
                    " https://aka.ms/asm-aks-upgrade-docs"
                )
                logger.warning(msg)

    except DecoratorEarlyExitException:
        return None

    return aks_update_decorator.update_mc(mc)


def aks_approuting_enable(
        cmd,
        client,
        resource_group_name,
        name,
        enable_kv=False,
        keyvault_id=None,
        nginx=None
):
    return _aks_approuting_update(
        cmd,
        client,
        resource_group_name,
        name,
        enable_app_routing=True,
        keyvault_id=keyvault_id,
        enable_kv=enable_kv,
        nginx=nginx)


def aks_approuting_disable(
        cmd,
        client,
        resource_group_name,
        name
):
    return _aks_approuting_update(
        cmd,
        client,
        resource_group_name,
        name,
        enable_app_routing=False)


def aks_approuting_update(
        cmd,
        client,
        resource_group_name,
        name,
        keyvault_id=None,
        enable_kv=False,
        nginx=None
):
    return _aks_approuting_update(
        cmd,
        client,
        resource_group_name,
        name,
        keyvault_id=keyvault_id,
        enable_kv=enable_kv,
        nginx=nginx)


def aks_approuting_zone_add(
        cmd,
        client,
        resource_group_name,
        name,
        dns_zone_resource_ids,
        attach_zones=False
):
    return _aks_approuting_update(
        cmd,
        client,
        resource_group_name,
        name,
        dns_zone_resource_ids=dns_zone_resource_ids,
        add_dns_zone=True,
        attach_zones=attach_zones)


def aks_approuting_zone_delete(
        cmd,
        client,
        resource_group_name,
        name,
        dns_zone_resource_ids
):
    return _aks_approuting_update(
        cmd,
        client,
        resource_group_name,
        name,
        dns_zone_resource_ids=dns_zone_resource_ids,
        delete_dns_zone=True)


def aks_approuting_zone_update(
        cmd,
        client,
        resource_group_name,
        name,
        dns_zone_resource_ids,
        attach_zones=False
):
    return _aks_approuting_update(
        cmd,
        client,
        resource_group_name,
        name,
        dns_zone_resource_ids=dns_zone_resource_ids,
        update_dns_zone=True,
        attach_zones=attach_zones)


def aks_approuting_zone_list(
        cmd,
        client,
        resource_group_name,
        name
):
    from azure.mgmt.core.tools import parse_resource_id
    mc = client.get(resource_group_name, name)

    if mc.ingress_profile and mc.ingress_profile.web_app_routing and mc.ingress_profile.web_app_routing.enabled:
        if mc.ingress_profile.web_app_routing.dns_zone_resource_ids:
            dns_zone_resource_ids = mc.ingress_profile.web_app_routing.dns_zone_resource_ids
            dns_zone_list = []
            for dns_zone in dns_zone_resource_ids:
                dns_zone_dict = {}
                parsed_dns_zone = parse_resource_id(dns_zone)
                dns_zone_dict['id'] = dns_zone
                dns_zone_dict['subscription'] = parsed_dns_zone['subscription']
                dns_zone_dict['resource_group'] = parsed_dns_zone['resource_group']
                dns_zone_dict['name'] = parsed_dns_zone['name']
                dns_zone_dict['type'] = parsed_dns_zone['type']
                dns_zone_list.append(dns_zone_dict)
            return dns_zone_list
        raise CLIError('No dns zone attached to the cluster')
    raise CLIError('App routing addon is not enabled')


# pylint: disable=unused-argument
def _aks_approuting_update(
        cmd,
        client,
        resource_group_name,
        name,
        enable_app_routing=None,
        enable_kv=None,
        keyvault_id=None,
        add_dns_zone=None,
        delete_dns_zone=None,
        update_dns_zone=None,
        dns_zone_resource_ids=None,
        attach_zones=None,
        nginx=None
):
    from azure.cli.command_modules.acs.managed_cluster_decorator import AKSManagedClusterUpdateDecorator

    raw_parameters = locals()

    aks_update_decorator = AKSManagedClusterUpdateDecorator(
        cmd=cmd,
        client=client,
        raw_parameters=raw_parameters,
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
    )

    try:
        mc = aks_update_decorator.fetch_mc()
        mc = aks_update_decorator.update_app_routing_profile(mc)
    except DecoratorEarlyExitException:
        return None

    return aks_update_decorator.update_mc(mc)


def is_monitoring_addon_enabled(addons, instance):
    monitoring_addon_enabled = False
    is_monitoring_addon = False
    try:
        addon_args = addons.split(',')
        for addon_arg in addon_args:
            if addon_arg in ADDONS:
                addon = ADDONS[addon_arg]
                if addon == CONST_MONITORING_ADDON_NAME:
                    is_monitoring_addon = True
                    break

        addon_profiles = instance.addon_profiles or {}
        monitoring_addon_enabled = is_monitoring_addon and CONST_MONITORING_ADDON_NAME in addon_profiles and addon_profiles[
            CONST_MONITORING_ADDON_NAME].enabled
    except Exception as ex:  # pylint: disable=broad-except
        logger.debug("failed to check monitoring addon enabled: %s", ex)
    return monitoring_addon_enabled
