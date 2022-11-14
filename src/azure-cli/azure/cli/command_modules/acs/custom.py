# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

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
from distutils.version import StrictVersion
from urllib.error import URLError
from urllib.request import urlopen

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
)
from azure.cli.command_modules.acs._helpers import get_snapshot_by_snapshot_id
from azure.cli.command_modules.acs._resourcegroup import get_rg_location
from azure.cli.command_modules.acs._validators import extract_comma_separated_string
from azure.cli.command_modules.acs.addonconfiguration import (
    add_ingress_appgw_addon_role_assignment,
    add_monitoring_role_assignment,
    add_virtual_node_role_assignment,
    ensure_container_insights_for_monitoring,
    ensure_default_log_analytics_workspace_for_monitoring,
)
from azure.cli.core._profile import Profile
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    AzureInternalError,
    FileOperationError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    ResourceNotFoundError,
    ValidationError,
)
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import in_cloud_console, sdk_no_wait
from knack.log import get_logger
from knack.prompting import NoTTYException, prompt_y_n
from knack.util import CLIError

logger = get_logger(__name__)

# pylint: disable=unused-argument


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
    dns_service_ip=None,
    docker_bridge_address=None,
    load_balancer_sku=None,
    load_balancer_managed_outbound_ip_count=None,
    load_balancer_outbound_ips=None,
    load_balancer_outbound_ip_prefixes=None,
    load_balancer_outbound_ports=None,
    load_balancer_idle_timeout=None,
    nat_gateway_managed_outbound_ip_count=None,
    nat_gateway_idle_timeout=None,
    outbound_type=None,
    network_plugin=None,
    network_policy=None,
    auto_upgrade_channel=None,
    cluster_autoscaler_profile=None,
    uptime_sla=False,
    fqdn_subdomain=None,
    api_server_authorized_ip_ranges=None,
    enable_private_cluster=False,
    private_dns_zone=None,
    disable_public_fqdn=False,
    service_principal=None,
    client_secret=None,
    enable_managed_identity=True,
    assign_identity=None,
    assign_kubelet_identity=None,
    enable_aad=False,
    enable_azure_rbac=False,
    aad_admin_group_object_ids=None,
    aad_client_app_id=None,
    aad_server_app_id=None,
    aad_server_app_secret=None,
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
    enable_defender=False,
    defender_config=None,
    disable_disk_driver=False,
    disable_file_driver=False,
    enable_blob_driver=None,
    disable_snapshot_controller=False,
    enable_azure_keyvault_kms=False,
    azure_keyvault_kms_key_id=None,
    azure_keyvault_kms_key_vault_network_access=None,
    azure_keyvault_kms_key_vault_resource_id=None,
    # addons
    enable_addons=None,
    workspace_resource_id=None,
    enable_msi_auth_for_monitoring=False,
    aci_subnet_name=None,
    appgw_name=None,
    appgw_subnet_cidr=None,
    appgw_id=None,
    appgw_subnet_id=None,
    appgw_watch_namespace=None,
    enable_sgxquotehelper=False,
    enable_secret_rotation=False,
    rotation_poll_interval=None,
    # nodepool paramerters
    nodepool_name="nodepool1",
    node_vm_size=None,
    os_sku=None,
    snapshot_id=None,
    vnet_subnet_id=None,
    pod_subnet_id=None,
    enable_node_public_ip=False,
    node_public_ip_prefix_id=None,
    enable_cluster_autoscaler=False,
    min_count=None,
    max_count=None,
    node_count=3,
    nodepool_tags=None,
    nodepool_labels=None,
    node_osdisk_type=None,
    node_osdisk_size=0,
    vm_set_type=None,
    zones=None,
    ppg=None,
    http_proxy_config=None,
    max_pods=0,
    enable_encryption_at_host=False,
    enable_ultra_ssd=False,
    enable_fips_image=False,
    kubelet_config=None,
    linux_os_config=None,
    no_wait=False,
    yes=False,
    aks_custom_headers=None,
    host_group_id=None,
    gpu_instance_profile=None,
    enable_syslog=False,
):
    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()

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
    load_balancer_managed_outbound_ip_count=None,
    load_balancer_outbound_ips=None,
    load_balancer_outbound_ip_prefixes=None,
    load_balancer_outbound_ports=None,
    load_balancer_idle_timeout=None,
    nat_gateway_managed_outbound_ip_count=None,
    nat_gateway_idle_timeout=None,
    auto_upgrade_channel=None,
    cluster_autoscaler_profile=None,
    uptime_sla=False,
    no_uptime_sla=False,
    api_server_authorized_ip_ranges=None,
    enable_public_fqdn=False,
    disable_public_fqdn=False,
    enable_managed_identity=False,
    assign_identity=None,
    assign_kubelet_identity=None,
    enable_aad=False,
    enable_azure_rbac=False,
    disable_azure_rbac=False,
    aad_tenant_id=None,
    aad_admin_group_object_ids=None,
    enable_oidc_issuer=False,
    windows_admin_password=None,
    enable_ahub=False,
    disable_ahub=False,
    enable_windows_gmsa=False,
    gmsa_dns_server=None,
    gmsa_root_domain_name=None,
    attach_acr=None,
    detach_acr=None,
    enable_defender=False,
    disable_defender=False,
    defender_config=None,
    enable_disk_driver=False,
    disable_disk_driver=False,
    enable_file_driver=False,
    disable_file_driver=False,
    enable_blob_driver=None,
    disable_blob_driver=None,
    enable_snapshot_controller=False,
    disable_snapshot_controller=False,
    enable_azure_keyvault_kms=False,
    disable_azure_keyvault_kms=False,
    azure_keyvault_kms_key_id=None,
    azure_keyvault_kms_key_vault_network_access=None,
    azure_keyvault_kms_key_vault_resource_id=None,
    # addons
    enable_secret_rotation=False,
    disable_secret_rotation=False,
    rotation_poll_interval=None,
    # nodepool paramerters
    enable_cluster_autoscaler=False,
    disable_cluster_autoscaler=False,
    update_cluster_autoscaler=False,
    min_count=None,
    max_count=None,
    nodepool_labels=None,
    http_proxy_config=None,
    no_wait=False,
    yes=False,
    aks_custom_headers=None,
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

    # null out the SP profile because otherwise validation complains
    instance.service_principal_profile = None

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
            # null out the SP profile because otherwise validation complains
            instance.service_principal_profile = None
            return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, name, instance)
    raise CLIError('The nodepool "{}" was not found.'.format(nodepool_name))


def aks_show(cmd, client, resource_group_name, name):
    mc = client.get(resource_group_name, name)
    return _remove_nulls([mc])[0]


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
                      no_wait=False,
                      enable_msi_auth_for_monitoring=False,
                      enable_syslog=False):
    instance = client.get(resource_group_name, name)
    msi_auth = False
    if instance.service_principal_profile.client_id == "msi":
        msi_auth = True
    subscription_id = get_subscription_id(cmd.cli_ctx)

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
                              no_wait=no_wait,
                              enable_syslog=enable_syslog)

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
                        enable_syslog=enable_syslog)
                else:
                    raise ArgumentUsageError(
                        "--enable-msi-auth-for-monitoring can not be used on clusters with service principal auth.")
            else:
                # monitoring addon will use legacy path
                if enable_syslog:
                    raise ArgumentUsageError(
                        "--enable-syslog can not be used without MSI auth.")
                ensure_container_insights_for_monitoring(
                    cmd, instance.addon_profiles[CONST_MONITORING_ADDON_NAME], subscription_id, resource_group_name, name, instance.location, aad_route=False)

        # adding a wait here since we rely on the result for role assignment
        result = LongRunningOperation(cmd.cli_ctx)(
            client.begin_create_or_update(resource_group_name, name, instance))

        # For monitoring addon, Metrics role assignement doesnt require in case of MSI auth
        if enable_monitoring and not enable_msi_auth_for_monitoring:
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


def _update_addons(cmd, instance, subscription_id, resource_group_name, name, addons, enable,
                   workspace_resource_id=None,
                   enable_msi_auth_for_monitoring=False,
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
                   no_wait=False,
                   enable_syslog=False):
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
                addon_profile.config[CONST_MONITORING_USING_AAD_MSI_AUTH] = enable_msi_auth_for_monitoring
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
        kubeconfig_path = os.environ["KUBECONFIG"].split(":")[0]
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
    except (IndexError, ValueError):
        raise CLIError("Fail to find kubeconfig file.")


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
    if platform.system() != "Windows" and not os.path.islink(existing_file):
        existing_file_perms = "{:o}".format(stat.S_IMODE(os.lstat(existing_file).st_mode))
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
        if node_name is not None:
            affinity = {
                "nodeAffinity": {
                    "requiredDuringSchedulingIgnoredDuringExecution": {
                        "nodeSelectorTerms": [
                            {
                                "matchExpressions": [
                                    {"key": "kubernetes.io/hostname", "operator": "In", "values": [node_name]}
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


# install kubectl & kubelogin
def k8s_install_cli(cmd, client_version='latest', install_location=None, base_src_url=None,
                    kubelogin_version='latest', kubelogin_install_location=None,
                    kubelogin_base_src_url=None):
    k8s_install_kubectl(cmd, client_version, install_location, base_src_url)
    k8s_install_kubelogin(cmd, kubelogin_version,
                          kubelogin_install_location, kubelogin_base_src_url)


# determine architecture for kubectl based on platform.processor()
# the results returned here may be inaccurate if the installed python is translated (e.g. by Rosetta)
def get_arch_for_cli_binary():
    arch = platform.processor().lower()
    formatted_arch = "amd64"
    if "arm" in arch:
        formatted_arch = "arm64"
    logger.warning(
        "The detected arch is %s, would be treated as %s, which may not match the actual situation due to translation "
        "and other reasons. If there is any problem, please download the appropriate binary by yourself.",
        arch,
        formatted_arch,
    )
    return formatted_arch


# install kubectl
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
    arch = get_arch_for_cli_binary()
    base_url = source_url + f"/{{}}/bin/{{}}/{arch}/{{}}"

    # ensure installation directory exists
    install_dir, cli = os.path.dirname(
        install_location), os.path.basename(install_location)
    if not os.path.exists(install_dir):
        os.makedirs(install_dir)

    if system == 'Windows':
        file_url = base_url.format(client_version, 'windows', 'kubectl.exe')
    elif system == 'Linux':
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
                           '    1. Run "set PATH=%PATH%;{0}" or "$env:path += \';{0}\'" for PowerShell. '
                           'This is good for the current command session.\n'
                           '    2. Update system PATH environment variable by following '
                           '"Control Panel->System->Advanced->Environment Variables", and re-open the command window. '
                           'You only need to do it once'.format(install_dir, cli))
    else:
        logger.warning('Please ensure that %s is in your search PATH, so the `%s` command can be found.',
                       install_dir, cli)


# install kubelogin
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
    arch = get_arch_for_cli_binary()
    if system == 'Windows':
        sub_dir, binary_name = 'windows_amd64', 'kubelogin.exe'
    elif system == 'Linux':
        sub_dir, binary_name = f'linux_{arch}', 'kubelogin'
    elif system == 'Darwin':
        sub_dir, binary_name = f'darwin_{arch}', 'kubelogin'
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


def aks_rotate_certs(cmd, client, resource_group_name, name, no_wait=True):
    return sdk_no_wait(no_wait, client.begin_rotate_cluster_certificates, resource_group_name, name)


def aks_get_versions(cmd, client, location):
    return client.list_orchestrators(location, resource_type='managedClusters')


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

    command_result_poller = sdk_no_wait(
        no_wait, client.begin_run_command, resource_group_name, name, request_payload, polling_interval=5, retry_total=0
    )
    if no_wait:
        # pylint: disable=protected-access
        command_result_polling_url = command_result_poller.polling_method()._initial_response.http_response.headers[
            "location"
        ]
        command_id_regex = re.compile(r"commandResults\/(\w*)\?")
        command_id = command_id_regex.findall(command_result_polling_url)[0]
        _aks_command_result_in_progess_helper(client, resource_group_name, name, command_id)
        return
    return _print_command_result(cmd.cli_ctx, command_result_poller.result(300))


def aks_command_result(cmd, client, resource_group_name, name, command_id=""):
    if not command_id:
        raise ValidationError('CommandID cannot be empty.')

    commandResult = client.get_command_result(resource_group_name, name, command_id)
    if commandResult is None:
        _aks_command_result_in_progess_helper(client, resource_group_name, name, command_id)
        return
    return _print_command_result(cmd.cli_ctx, commandResult)


def _aks_command_result_in_progess_helper(client, resource_group_name, name, command_id):
    # pylint: disable=unused-argument
    def command_result_direct_response_handler(pipeline_response, *args, **kwargs):
        deserialized_data = pipeline_response.context.get("deserialized_data", {})
        if deserialized_data:
            provisioning_state = deserialized_data.get("properties", {}).get("provisioningState", None)
            started_at = deserialized_data.get("properties", {}).get("startedAt", None)
            print(f"command id: {command_id}, started at: {started_at}, status: {provisioning_state}")
            print(
                f"Please use command \"az aks command result -g {resource_group_name} -n {name} -i {command_id}\" "
                "to get the future execution result"
            )
        else:
            print(f"failed to fetch command result for command id: {command_id}")
    client.get_command_result(resource_group_name, name, command_id, cls=command_result_direct_response_handler)


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
    print(f"{colorama.Fore.BLUE}command is in {commandResult.provisioning_state} state{colorama.Style.RESET_ALL}")
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
    os_type=None,
    os_sku=None,
    snapshot_id=None,
    vnet_subnet_id=None,
    pod_subnet_id=None,
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
    node_osdisk_type=None,
    node_osdisk_size=0,
    max_surge=None,
    mode=CONST_NODEPOOL_MODE_USER,
    scale_down_mode=CONST_SCALE_DOWN_MODE_DELETE,
    max_pods=0,
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
    gpu_instance_profile=None,
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
    mode=None,
    scale_down_mode=None,
    no_wait=False,
    aks_custom_headers=None,
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
                          no_wait=False,
                          aks_custom_headers=None,
                          snapshot_id=None):
    AgentPoolUpgradeSettings = cmd.get_models(
        "AgentPoolUpgradeSettings",
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        operation_group="managed_clusters",
    )
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


def aks_nodepool_snapshot_show(cmd, client, resource_group_name, snapshot_name):   # pylint: disable=unused-argument
    snapshot = client.get(resource_group_name, snapshot_name)
    return snapshot


def aks_nodepool_snapshot_delete(cmd,    # pylint: disable=unused-argument
                                 client,
                                 resource_group_name,
                                 snapshot_name,
                                 no_wait=False,
                                 yes=False):

    msg = 'This will delete the snapshot "{}" in resource group "{}", Are you sure?'.format(snapshot_name, resource_group_name)
    if not yes and not prompt_y_n(msg, default="n"):
        return None

    return client.delete(resource_group_name, snapshot_name)


def aks_nodepool_snapshot_list(cmd, client, resource_group_name=None):  # pylint: disable=unused-argument
    if resource_group_name is None or resource_group_name == '':
        return client.list()

    return client.list_by_resource_group(resource_group_name)


def aks_rotate_service_account_signing_keys(cmd, client, resource_group_name, name, no_wait=True):
    return sdk_no_wait(no_wait, client.begin_rotate_service_account_signing_keys, resource_group_name, name)
