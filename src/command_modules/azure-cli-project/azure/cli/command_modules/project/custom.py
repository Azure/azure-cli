# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import codecs
import glob
import json
import os
import platform
import socket
import sys
import threading
import webbrowser
from subprocess import (PIPE, CalledProcessError, Popen, check_call,
                        check_output)
from time import sleep
import requests
from sshtunnel import SSHTunnelForwarder

import azure.cli.command_modules.project.settings as settings
import azure.cli.command_modules.project.utils as utils
import azure.cli.core.azlogging as azlogging  # pylint: disable=invalid-name
from azure.cli.command_modules.acs.custom import (acs_create,
                                                  k8s_get_credentials,
                                                  k8s_install_cli)
from azure.cli.command_modules.acs._params import _get_default_install_location
from azure.cli.command_modules.project.jenkins import Jenkins
from azure.cli.command_modules.resource.custom import _deploy_arm_template_core
from azure.cli.command_modules.storage._factory import storage_client_factory
from azure.cli.core._environment import get_config_dir
from azure.cli.core._profile import Profile
from azure.cli.core._util import CLIError
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.containerregistry.models import (Registry,
                                                 StorageAccountProperties)
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.mgmt.resource.resources.models.resource_group import ResourceGroup
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import Kind, Sku, StorageAccountCreateParameters
from azure.mgmt.containerregistry.models import RegistryCreateParameters, StorageAccountParameters
from azure.mgmt.containerregistry.models import Sku as AcrSku
from azure.storage.file import FileService
from six.moves.urllib.error import URLError  # pylint: disable=import-error
from six.moves.urllib.request import urlopen  # pylint: disable=import-error

logger = azlogging.get_az_logger(__name__)  # pylint: disable=invalid-name
project_settings = settings.Project()  # pylint: disable=invalid-name
random_word = utils.get_random_word()

# TODO: Remove and switch to SSH once templates are updated
admin_password = 'Mindaro@Pass1!'  # pylint: disable=invalid-name
# pylint: disable=too-few-public-methods,too-many-arguments
# pylint: disable=no-self-use,too-many-locals,line-too-long,broad-except


def browse_pipeline():
    """
    Creates an SSH tunnel to Jenkins host and opens
    the pipeline in the browser
    """
    # TODO: Read the pipeline name from the project file and open
    # the URL to localhost:PORT/job/[pipelinename]
    jenkins_hostname = project_settings.jenkins_hostname
    admin_username = project_settings.admin_username

    if not jenkins_hostname:
        raise CLIError(
            'Jenkins host name does not exist in projectSettings.json')

    local_port = _get_available_local_port()
    local_address = 'http://127.0.0.1:{}'.format(local_port)
    utils.writeline('Jenkins Dashboard available at: {}'.format(local_address))
    utils.writeline('Press CTRL+C to close the tunnel')
    _wait_then_open_async(local_address)
    with SSHTunnelForwarder((jenkins_hostname, 22),
                            ssh_username=admin_username,
                            ssh_password=admin_password,
                            remote_bind_address=('127.0.0.1', 8080),
                            local_bind_address=('0.0.0.0', local_port)):
        try:
            while True:
                sleep(1)
        except KeyboardInterrupt:
            pass


def create_project(ssh_private_key, resource_group='mindaro-rg-' + random_word, name='mindaro-project-' + random_word, location='southcentralus'):
    """
    Creates a new project which consists of a new resource group,
    ACS Kubernetes cluster and Azure Container Registry
    """
    default_user_name = 'azureuser'

    # 0. Validate ssh private key path
    if not os.path.exists(ssh_private_key):
        raise CLIError(
            "ssh key does not exist: {}, please run 'ssh-keygen -b 1024' to generate it or pass the correct ssh key.".format(ssh_private_key))

    # 1. Create a resource group: resource_group, location
    utils.writeline('Creating resource group ...')
    res_client = _get_resource_client_factory()
    resource_group_parameters = ResourceGroup(
        location=location)
    res_client.resource_groups.create_or_update(
        resource_group, resource_group_parameters)
    utils.writeline('Resource group "{}" created.'.format(resource_group))

    # 2. Create a storage account (for ACR)
    utils.writeline('Creating storage account ...')
    storage_account_sku = Sku('Standard_LRS')
    storage_client = _get_storage_service_client()
    storage_account_parameters = StorageAccountCreateParameters(
        sku=storage_account_sku, kind=Kind.storage.value, location=location)
    storage_account_deployment = storage_client.storage_accounts.create(
        resource_group, utils.get_random_string(), parameters=storage_account_parameters)
    storage_account_deployment.wait()
    storage_account_result = storage_account_deployment.result()
    storage_account_name = storage_account_result.name
    storage_account_keys = storage_client.storage_accounts.list_keys(
        resource_group, storage_account_name).keys
    storage_account_key = storage_account_keys[0]
    utils.writeline(
        'Storage account "{}" created.'.format(storage_account_name))

    # 3. Create ACR (resource_group, location)
    utils.writeline('Creating Azure container registry ...')
    res_client.providers.register(
        resource_provider_namespace='Microsoft.ContainerRegistry')
    acr_client = _get_acr_service_client()
    acr_name = 'acr' + utils.get_random_registry_name()
    acr_client.registries.create(resource_group,
                                acr_name,
                                RegistryCreateParameters(
                                    location=location,
                                    sku=AcrSku('Basic'),
                                    storage_account=StorageAccountParameters(
                                        storage_account_name, storage_account_key))).wait()
    registry = acr_client.registries.get(resource_group, acr_name)
    utils.writeline(
        'Azure container registry "{}" created.'.format(acr_name))

    # 4. Create Kubernetes cluster
    utils.writeline('Creating Kubernetes cluster ...')
    kube_deployment_name = 'kube-' + utils.get_random_string()
    kube_cluster_name = 'kube-acs-' + utils.get_random_string()
    acs_deployment = acs_create(resource_group_name=resource_group,
                                deployment_name=kube_deployment_name,
                                name=kube_cluster_name,
                                ssh_key_value=utils.get_public_ssh_key_contents(
                                    ssh_private_key + '.pub'),
                                dns_name_prefix=kube_cluster_name,
                                admin_username=default_user_name,
                                location=location,
                                orchestrator_type='kubernetes')
    acs_deployment.wait()
    utils.writeline(
        'Kubernetes cluster "{}" created.'.format(kube_cluster_name))

    # 5. Install kubectl
    utils.writeline('Installing kubectl ...')
    k8s_install_cli(install_location=_get_default_install_location('kubectl'))

    # 6. Set Kubernetes config
    utils.writeline('Setting Kubernetes config ...')
    k8s_get_credentials(name=kube_cluster_name,
                        resource_group_name=resource_group,
                        ssh_key_file=ssh_private_key)
    utils.writeline(
        'Kubernetes config "{}" created.'.format(kube_cluster_name))

    # 7. Store the settings in projectSettings.json
    # TODO: We should create service principal and pass it to the
    # acs_create when creating the Kubernetes cluster
    client_id, client_secret = _get_service_principal()
    project_settings.client_id = client_id
    project_settings.client_secret = client_secret
    project_settings.resource_group = resource_group
    project_settings.cluster_name = kube_cluster_name
    project_settings.cluster_resource_group = resource_group
    project_settings.admin_username = default_user_name
    project_settings.container_registry_url = 'https://' + registry.login_server
    project_settings.location = location
    project_settings.project_name = name
    project_settings.ssh_private_key = ssh_private_key
    utils.writeline('Project "{}" created.'.format(name))

    # 8. Configure the Kubernetes cluster
    # Initializes a workspace definition that automates connection to a Kubernetes cluster
    # in an Azure container service for deploying services.
    _configure_cluster()


def create_deployment_pipeline(remote_access_token):  # pylint: disable=unused-argument
    """
    Provisions Jenkins and configures CI and CD pipelines, kicks off initial build-deploy
    and saves the CI/CD information to a local project file.
    """
    jenkins_resource, jenkins_deployment = _deploy_jenkins()

    # Wait for deployments to complete
    jenkins_deployment.wait()

    jenkins_hostname = '{}.{}.cloudapp.azure.com'.format(
        jenkins_resource.dns_prefix, jenkins_resource.location)
    project_settings.jenkins_hostname = jenkins_hostname
    utils.writeline('Jenkins hostname: {}'.format(jenkins_hostname))
    utils.writeline('Done.')


def _wait_then_open(url):
    """
    Waits for a bit then opens a URL. Useful for
    waiting for a proxy to come up, and then open the URL.
    """
    for _ in range(1, 10):
        try:
            urlopen(url)
        except URLError:
            sleep(1)
        break
    webbrowser.open_new_tab(url)


def _wait_then_open_async(url):
    """
    Tries to open the URL in the background thread.
    """
    thread = threading.Thread(target=_wait_then_open, args=({url}))
    thread.daemon = True
    thread.start()


def _get_available_local_port():
    """
    Gets a random, available local port
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


def _get_service_principal():
    """
    Gets the service principal and secret tuple
    from the acsServicePrincipal.json for currently logged in user
    """
    subscription_id = _get_subscription_id()
    config_file = os.path.join(get_config_dir(), 'acsServicePrincipal.json')
    file_descriptor = os.open(config_file, os.O_RDONLY)
    with os.fdopen(file_descriptor) as file_object:
        config_file_contents = json.loads(file_object.read())
    client_id = config_file_contents[subscription_id]['service_principal']
    client_secret = config_file_contents[subscription_id]['client_secret']
    return client_id, client_secret


def _get_subscription_id():
    _, sub_id, _ = Profile().get_login_credentials(subscription_id=None)
    return sub_id


def _deploy_jenkins():
    """
    Starts the Jenkins deployment and returns the resource and AzurePollerOperation
    """
    utils.writeline('Deploying Jenkins ...')
    git_repo = _get_git_remote_url()
    resource_group = project_settings.resource_group
    client_id = project_settings.client_id
    client_secret = project_settings.client_secret
    admin_username = project_settings.admin_username
    container_registry_url = project_settings.container_registry_url
    location = project_settings.location

    jenkins_dns_prefix = 'jenkins-' + utils.get_random_string()
    jenkins_resource = Jenkins(
        resource_group, admin_username,
        admin_password, client_id, client_secret,
        git_repo, jenkins_dns_prefix, location,
        container_registry_url)
    return (jenkins_resource, jenkins_resource.deploy())


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


def _get_acr_service_client():
    """
    Gets the ACR service client
    """
    return get_mgmt_service_client(ContainerRegistryManagementClient)


def _get_resource_client_factory():
    """
    Gets the service client for resource management
    """
    return get_mgmt_service_client(ResourceManagementClient)


def _get_storage_service_client():
    """
    Gets  the client for managing storage accounts.
    """
    return get_mgmt_service_client(StorageManagementClient)


def _get_git_remote_url():
    """
    Tries to find a remote for the repo in the current folder.
    If only one remote is present return that remote,
    if more than one remote is present it looks for origin.
    """
    try:
        remotes = check_output(['git', 'remote']).strip().splitlines()
        remote_url = ''
        if len(remotes) == 1:
            remote_url = check_output(
                ['git', 'remote', 'get-url', remotes[0].decode()]).strip()
        else:
            remote_url = check_output(
                ['git', 'remote', 'get-url', 'origin']).strip()
    except ValueError as value_error:
        logger.debug(value_error)
        raise CLIError(
            "A default remote was not found for the current folder. \
            Please run this command in a git repository folder with \
            an 'origin' remote or specify a remote using '--remote-url'")
    except CalledProcessError as called_process_err:
        raise CLIError(
            'Please ensure git version 2.7.0 or greater is installed.\n' + called_process_err)
    return remote_url.decode()


def _configure_cluster():  # pylint: disable=too-many-statements
    """
    Configures the cluster to deploy tenx services which can be used by the user
    deployed services and initializes a workspace on the local machine to connection.
    Asks for user input: ACR server name.
    """
    kubernetes_path = None
    try:
        # Setting the values
        dns_prefix = project_settings.cluster_name
        location = project_settings.location
        user_name = project_settings.admin_username
        acr_server = project_settings.container_registry_url.replace(
            "https://", "")
        ssh_private_key = project_settings.ssh_private_key

        # Validate kubectl context
        if not _validate_kubectl_context(dns_prefix):
            utils.writeline(
                "kubectl context not set to {}, please run 'az acs kubernetes get-credentials' to set it.".format(dns_prefix))
            sys.exit(1)

        if _cluster_configured(dns_prefix, user_name):
            utils.writeline('Cluster already configured.')
            return
        else:
            utils.writeline('Cluster not configured.')

        utils.writeline('Configuring Kubernetes cluster ...')

        # Removing existing cluster from ~/.ssh/known_hosts
        known_hostname_command = 'ssh-keygen -R {}.{}.cloudapp.azure.com'.format(
            dns_prefix, location)
        _execute_command(known_hostname_command, True)

        innerloop_client_path = _get_innerloop_home_path()
        kubernetes_path = os.path.join(
            innerloop_client_path, 'setup', 'Kubernetes')

        # Get resource group
        creds = _get_creds_from_master(
            dns_prefix, location, user_name, ssh_private_key)
        resource_group = creds['resourceGroup']
        client_id = creds['aadClientId']
        client_secret = creds['aadClientSecret']

        # Cluster Setup(deploying required artifacts in the kubectl nodes)
        utils.writeline('Preparing ARM configuration ...')
        k8_parameters = _prepare_arm_k8(dns_prefix)

        utils.writeline('Creating Resources ...')
        utils.writeline('This is going to take a while. Sit back and relax.')
        _deploy_arm_template_core(
            resource_group, template_file='{}/k8.deploy.json'.format(kubernetes_path), deployment_name=dns_prefix,
            parameters=k8_parameters)
        utils.writeline('Done with the resources!')

        utils.writeline('Creating tenx namespace ...')
        namespace_command = "kubectl create namespace tenx"
        _execute_command(namespace_command, True)

        utils.writeline('Deploying ACR credentials in Kubernetes ...')
        workspace_storage_key = _deploy_secrets_share_k8(
            acr_server, resource_group, dns_prefix, client_id, client_secret, location, user_name)

        utils.writeline('Enumerating Kubernetes agents ...')
        _enumerate_k8_agents(innerloop_client_path)

        utils.writeline('Preparing the cluster ...')
        remote_host = _get_remote_host(user_name, dns_prefix, location)
        _execute_command("ssh -i {0} -o StrictHostKeyChecking=no -p 22 {1} 'mkdir ~/.azure'".format(
            ssh_private_key, remote_host), True)
        _execute_command(
            "ssh -i {0} -p 22 {1} 'mkdir ~/.ssh'".format(ssh_private_key, remote_host), True)
        _execute_command("scp -i {0} -P 22 {1}/hosts.tmp {2}:~/hosts".format(
            ssh_private_key, kubernetes_path, remote_host))

        utils.writeline('Copying configuration files into the cluster ...')

        _execute_command(
            "scp -i {0} -P 22 {0} {1}:~/.ssh/id_rsa".format(ssh_private_key, remote_host))
        _execute_command("scp -i {0} -P 22 {1}/connectlocal.tmp.sh {2}:~/connectlocal.tmp.sh".format(
            ssh_private_key, kubernetes_path, remote_host))
        _execute_command("scp -i {0} -P 22 {1}/configagents.sh {2}:~/configagents.sh".format(
            ssh_private_key, kubernetes_path, remote_host))

        _execute_command(
            "eval $(ssh-agent) && ssh-add {}".format(ssh_private_key))
        _execute_command(
            "ssh -i {0} -o StrictHostKeyChecking=no -p 22 {1} 'chmod 600 ~/.ssh/id_rsa'".format(ssh_private_key, remote_host))
        _execute_command(
            "ssh -i {0} -o StrictHostKeyChecking=no -p 22 {1} 'chmod +x ./configagents.sh'".format(ssh_private_key, remote_host))

        utils.writeline('Configuring agents in the cluster ...')

        _execute_command(
            "ssh -A -i {0} -p 22 {1} 'source ./configagents.sh'".format(ssh_private_key, remote_host))

        utils.writeline('Deploying TenX services to K8 cluster ...')

        _execute_command(
            "kubectl create -f {}/tenx.tmp.yaml".format(kubernetes_path), True)
        _execute_command(
            "kubectl create -f {}/tenxPrivate.tmp.yaml".format(kubernetes_path), True)

        utils.writeline('Cleaning existing TenX services in cluster, if any')
        _execute_command(
            "kubectl delete -f {}/tenxServices.yaml -n tenx".format(kubernetes_path), True)
        _execute_command(
            "kubectl delete -f {}/tenxPrivateService.yaml -n tenx".format(kubernetes_path), True)
        _execute_command(
            "kubectl delete -f {}/tenxConfigService.yaml -n tenx".format(kubernetes_path), True)
        _execute_command(
            "kubectl delete -f {}/tenxBuildService.yaml -n tenx".format(kubernetes_path), True)
        _execute_command(
            "kubectl delete -f {}/tenxExecService.yaml -n tenx".format(kubernetes_path), True)
        _execute_command(
            "kubectl delete -f {}/tenxRsrcService.yaml -n tenx".format(kubernetes_path), True)
        _execute_command(
            "kubectl delete -f {}/tenxPublicEndpoint.yaml -n tenx".format(kubernetes_path), True)

        utils.writeline('Exposing TenX services from cluster')
        _execute_command(
            "kubectl create -f {}/tenxServices.yaml -n tenx".format(kubernetes_path))
        _execute_command(
            "kubectl create -f {}/tenxPrivateService.yaml -n tenx".format(kubernetes_path))
        _execute_command(
            "kubectl create -f {}/tenxConfigService.yaml -n tenx".format(kubernetes_path))
        _execute_command(
            "kubectl create -f {}/tenxBuildService.yaml -n tenx".format(kubernetes_path))
        _execute_command(
            "kubectl create -f {}/tenxExecService.yaml -n tenx".format(kubernetes_path))
        _execute_command(
            "kubectl create -f {}/tenxRsrcService.yaml -n tenx".format(kubernetes_path))
        _execute_command(
            "kubectl create -f {}/tenxPublicEndpoint.yaml -n tenx".format(kubernetes_path))

        # Initialize Workspace
        utils.writeline('Initializing Workspace: {} ...'.format(dns_prefix))
        utils.writeline('This might take some waiting.')
        workspace_storage = dns_prefix.replace('-', '') + 'wks'
        _initialize_workspace(
            dns_prefix, user_name, workspace_storage, workspace_storage_key, ssh_private_key, location=location)
    finally:
        # Removing temporary data files
        if kubernetes_path != None:
            file_path = os.path.join(kubernetes_path, '*.tmp.*')
            files = glob.glob(file_path)
            for single_file in files:
                os.remove(single_file)

        # Removing temporary creds azure.json
        azure_json_file = _get_creds_file()
        if os.path.exists(azure_json_file):
            os.remove(azure_json_file)


def _validate_kubectl_context(dns_prefix):
    context_command = 'kubectl config current-context'
    current_context = _get_command_output(context_command)
    return current_context.strip() == dns_prefix.strip()


def _cluster_configured(dns_prefix, user_name):  # pylint: disable=too-many-return-statements
    """
    Detects if the cluster exists and already configured i.e. all the required services are available and running.
    The check is done in 2 parts:
    1. Checks if the workspace is initialized (settings.json exists)
    2. Checks if all the services are running by pinging each URL.
    """

    utils.writeline('Detecting if the cluster is configured ...')
    settings_json_file_path = _get_workspace_settings_file()
    workspace_err_message = '  Workspace not defined.'
    if not os.path.exists(settings_json_file_path):
        logger.warning(workspace_err_message)
        return False
    cluster_settings = json.load(codecs.open(
        settings_json_file_path, 'r', 'utf-8-sig'))

    default_workspace_name = cluster_settings["DefaultWorkspace"]
    if not default_workspace_name:
        logger.warning(workspace_err_message)
        return False

    default_workspace = cluster_settings["Workspaces"][default_workspace_name]
    if not default_workspace:
        logger.warning(workspace_err_message)
        return False

    cluster = default_workspace["Cluster"]
    ssh_user = default_workspace["SSHUser"]

    if not(cluster == dns_prefix and ssh_user == user_name):
        return False

    try:
        url_sub_path = "api/ping"
        build_service_url = default_workspace["BuildServiceUrl"]
        logger.info('  Checking build service')
        if not _ping_url("{}/{}".format(build_service_url, url_sub_path)):
            return False

        exec_service_url = default_workspace["ExecServiceUrl"]
        logger.info('  Checking exec service')
        if not _ping_url("{}/{}".format(exec_service_url, url_sub_path)):
            return False

        rsrc_service_url = default_workspace["RsrcServiceUrl"]
        logger.info('  Checking rsrc service')
        if not _ping_url("{}/{}".format(rsrc_service_url, url_sub_path)):
            return False

        config_service_url = default_workspace["ConfigServiceUrl"]
        logger.info('  Checking config service')
        if not _ping_url("{}/{}".format(config_service_url, url_sub_path)):
            return False

        # All services running
        return True
    except Exception:
        return False


def _ping_url(url):
    """
    Pings passed URL and returns True if success.
    """
    req = requests.get(url)
    return req.status_code == 200


def _enumerate_k8_agents(innerloop_client_path):
    """
    Enumerate the Kubernetes nodes (agents) and write them in a file to be copied to the master host.
    """
    output = _get_command_output("kubectl get nodes")
    hosts_file_path = os.path.join(
        innerloop_client_path, 'setup', 'Kubernetes', 'hosts.tmp')

    try:
        with open(hosts_file_path, "w") as hosts_file:
            for line in output.splitlines():
                if not(line or line.strip()):
                    break
                if "Ready" in line:
                    line = line.replace('\t', '').strip()
                    parts = line.split(' ')
                    parts = list(filter(None, parts))
                    if len(parts) > 2 and parts[1] == "Ready" and "agent" in parts[0]:
                        hosts_file.write(parts[0] + '\n')
    except FileNotFoundError as error:
        raise CLIError(error)


def _deploy_secrets_share_k8(acr_server, resource_group, dns_prefix, client_id, client_secret, location, user_name):
    """
    Install cluster/registry secrets and creates share on the file storage.
    """
    _install_k8_secret(acr_server, dns_prefix, client_id,
                       client_secret, location, user_name)
    workspace_storage_key = _install_k8_shares(resource_group, dns_prefix)
    return workspace_storage_key


def _install_k8_secret(acr, dns_prefix, client_id, client_secret, location, cluster_user_name):
    """
    Creates a registry secret in the cluster, used by the tenx services.
    Prepares the file to create resource in the Kubernetes cluster.
    """
    kubectl_create_secret_command = "kubectl create secret docker-registry tenxregkey --docker-server={} --docker-username={} \
    --docker-password={} --docker-email={} -n tenx".format(acr, client_id, client_secret, _get_remote_host(cluster_user_name, dns_prefix, location))
    try:
        check_call(kubectl_create_secret_command, shell=True)
    except Exception:
        logger.debug("Command failed: %s\n", kubectl_create_secret_command)

    config_storage = dns_prefix.replace('-', '') + "cfgsa"
    private_storage = dns_prefix.replace('-', '') + "private"

    try:
        innerloop_client_path = _get_innerloop_home_path()
        tenx_yaml_path = os.path.join(
            innerloop_client_path, 'setup', 'Kubernetes', 'tenx.yaml')
        with open(tenx_yaml_path, "r") as tenx_yaml_file:
            tenx_yaml = tenx_yaml_file.read()
        tmp_tenx_yaml = tenx_yaml.replace("$TENX_PRIVATE_REGISTRY$", acr).replace(
            "$TENX_STORAGE_ACCOUNT$", config_storage)

        tmp_tenx_yaml_path = os.path.join(
            innerloop_client_path, 'setup', 'Kubernetes', 'tenx.tmp.yaml')
        with open(tmp_tenx_yaml_path, "w") as tmp_tenx_yaml_file:
            tmp_tenx_yaml_file.write(tmp_tenx_yaml)

        tenx_private_yaml_path = os.path.join(
            innerloop_client_path, 'setup', 'Kubernetes', 'tenxPrivate.yaml')
        with open(tenx_private_yaml_path, "r") as tenx_private_yaml_file:
            tenx_private_yaml = tenx_private_yaml_file.read()
        tmp_tenx_private_yaml = tenx_private_yaml.replace(
            "$TENX_STORAGE_ACCOUNT_PRIVATE$", private_storage)

        tmp_tenx_private_yaml_path = os.path.join(
            innerloop_client_path, 'setup', 'Kubernetes', 'tenxPrivate.tmp.yaml')
        with open(tmp_tenx_private_yaml_path, "w") as tmp_tenx_private_yaml_file:
            tmp_tenx_private_yaml_file.write(tmp_tenx_private_yaml)
    except FileNotFoundError as error:
        raise CLIError(error)


def _install_k8_shares(resource_group, dns_prefix):
    """
    Creates/ensures the shares in the file storage.
    Prepares the connection file that runs on each agent and mounts the directory to a share in the file storage.
    """
    # Populate connectlocal.tmp.sh with private storage account key
    config_storage = dns_prefix.replace('-', '') + "cfgsa"
    workspace_storage = dns_prefix.replace('-', '') + "wks"
    scf = storage_client_factory()
    config_storage_key = _get_storage_key(
        resource_group, scf, config_storage, 10)
    workspace_storage_key = _get_storage_key(
        resource_group, scf, workspace_storage, 10)

    innerloop_client_path = _get_innerloop_home_path()
    connect_template_path = os.path.join(
        innerloop_client_path, 'setup', 'Kubernetes', 'connectlocal.template.sh')
    with open(connect_template_path, "r") as connect_template_file:
        connect_template = connect_template_file.read()
    connect_template = connect_template.replace("$STORAGEACCOUNT_PRIVATE$", config_storage) \
        .replace("$STORAGE_ACCOUNT_PRIVATE_KEY$", config_storage_key) \
        .replace("$STORAGEACCOUNT$", workspace_storage) \
        .replace("$STORAGE_ACCOUNT_KEY$", workspace_storage_key) \
        .replace("$SHARE_NAME$", "mindaro")

    connect_output = os.path.join(
        innerloop_client_path, 'setup', 'Kubernetes', 'connectlocal.tmp.sh')
    with open(connect_output, "w") as connect_output_file:
        connect_output_file.write(connect_template)

    # Ensure 'cfgs' share exists in configStorage
    file_service = FileService(
        account_name=config_storage, account_key=config_storage_key)
    file_service.create_share(share_name='cfgs')

    # Ensure 'mindaro' share exists in configStorage
    file_service = FileService(
        account_name=workspace_storage, account_key=workspace_storage_key)
    file_service.create_share(share_name='mindaro')

    return workspace_storage_key


def _get_storage_key(resource_group, scf, storage, tries):
    # Re-tries in case the config storage account is not ready yet
    retry = 0
    storage_key = None
    while retry < tries:
        try:
            keys_list_json = scf.storage_accounts.list_keys(
                resource_group, storage).keys  # pylint: disable=no-member
            storage_key = list(keys_list_json)[0].value
            if storage_key != None:
                break
        except Exception as error:
            logger.debug(error)
        finally:
            logger.warning(
                "Couldn't get storage account key for {}, Retrying ...".format(storage))
            sleep(2)
            retry = retry + 1
    if storage_key is None:
        raise CLIError(
            "Can't get storage account key for {}".format(storage))
    return storage_key


def _execute_command(command, ignore_failure=False):
    """
    Executes a command.
    """
    with Popen(command, shell=True, stdout=PIPE, stderr=PIPE, bufsize=1, universal_newlines=True) as process:
        for line in process.stdout:
            logger.info(line)
        if ignore_failure:
            for err in process.stderr:
                logger.warning(err)

    if not ignore_failure:
        if process.returncode != 0:
            raise CLIError(CalledProcessError(process.returncode, command))


def _get_command_output(command):
    """
    Executes a command and provides the output.
    """
    output = check_output(command.split(' ')).strip().decode('utf-8')
    return output


def _get_creds_from_master(dns_prefix, location, user_name, ssh_private_key):
    """
    Copies azure.json file from the master host on the Kubernetes cluster to local system.
    Provides the json data from the file.
    """
    tenx_dir = _get_tenx_dir()
    if not os.path.exists(tenx_dir):
        os.mkdir(tenx_dir)

    azure_json_file = _get_creds_file()
    if os.path.exists(azure_json_file):
        os.remove(azure_json_file)

    _execute_command("scp -i {0} -P 22 {1}:/etc/kubernetes/azure.json {2}".format(
        ssh_private_key, _get_remote_host(user_name, dns_prefix, location), azure_json_file))

    with open(azure_json_file, "r") as credentials_file:
        creds = json.load(credentials_file)
    return creds


def _get_tenx_dir():
    """
    Provides the local path of .tenx dir.
    """
    tenx_dir = os.path.join(os.path.expanduser('~'), '.tenx')
    return tenx_dir


def _get_creds_file():
    """
    Provides the local path of azure.json file, copied from the master host on the Kubernetes cluster.
    """
    azure_json_file = os.path.join(_get_tenx_dir(), 'azure.json')
    return azure_json_file


def _get_workspace_settings_file():
    """
    Provides settings.json file path.
    """
    workspace_settings_file = os.path.join(_get_tenx_dir(), 'settings.json')
    return workspace_settings_file


def _get_remote_host(user_name, dns_prefix, location):
    """
    Provides a remote host according to the passed user_name, dns_prefix and location.
    """
    return "{}@{}.{}.cloudapp.azure.com".format(user_name, dns_prefix, location)


def _prepare_arm_k8(dns_prefix):
    """
    Prepares template file for configuring the Kubernetes cluster.
    """
    try:
        innerloop_client_path = _get_innerloop_home_path()
        k8_parameters_file_path = os.path.join(
            innerloop_client_path, 'setup', 'Kubernetes', 'k8.deploy.parameters.json')
        with open(k8_parameters_file_path, "r") as k8_parameters_file:
            k8_parameters = k8_parameters_file.read()
        new_k8_parameters = k8_parameters.replace(
            "CLUSTER_NAME", dns_prefix.replace('-', ''))

        new_k8_parameters_file_path = os.path.join(
            innerloop_client_path, 'setup', 'Kubernetes', 'k8.deploy.parameters.tmp.json')
        with open(new_k8_parameters_file_path, "w") as new_k8_parameters_file:
            new_k8_parameters_file.write(new_k8_parameters)

        return new_k8_parameters
    except FileNotFoundError as error:
        raise CLIError(error)


def _initialize_workspace(
        dns_prefix,
        user_name,
        storage_account_name,
        storage_account_key,
        ssh_private_key,
        location='westus',
        workspace_share_name='mindaro'):
    """
    Calls tenx initialize command on the current directory.
    Initialize creates settings.json file which contains all the credentials and links to connect to the cluster.
    """

    # TODO: to remove this below code to delete settings.json when we support
    # multiple sublevel workspaces
    settings_json_file = _get_workspace_settings_file()
    if os.path.exists(settings_json_file):
        os.remove(settings_json_file)

    run_innerloop_command('initialize', workspace_share_name, dns_prefix,
                          storage_account_name, storage_account_key, workspace_share_name, location, ssh_private_key, '--quiet', '--k8')

    # Checking if the services are ready
    while not _cluster_configured(dns_prefix, user_name):
        utils.writeline('Services are not ready yet. Waiting ...')
        sleep(5)
    utils.writeline('Cluster configured successfully.')


def service_run(project_path):
    """
    Automates building the project/service in a Docker image and pushing to an Azure container registry,
    and creates a release definition that automates deploying container images from a container registry
    to a Kubernetes cluster in an Azure container service. Then deploying the project as a service and running it.

    Run configures the cluster, if not already, then builds the service in the cluster and starts the service.

    :param project_path: Project/Service path to deploy on the Kubernetes cluster or current directory.
    :type project_path: String
    """

    curr_dir = None
    try:
        if not project_path == ".":
            curr_dir = os.getcwd()
            os.chdir(project_path)
            project_path = curr_dir
        elif not os.path.exists(project_path):
            raise CLIError("Invalid path: {}".format(project_path))

        # Validate if az project exists
        if not os.path.exists(project_settings.settings_file):
            utils.writeline(
                "projectResource.json not found, please run 'az project create' to create resources.")
            sys.exit(1)

        # Configuring Cluster
        _configure_cluster()

        # Building Service ...
        _service_build()

        # Starting Service ...
        _service_run()

    except Exception as error:
        raise CLIError(error)
    finally:
        if curr_dir and curr_dir.strip():
            os.chdir(curr_dir)


def _service_build():
    """
    Calls tenx build command on the current directory.
    Build implicitly syncs the files to the cluster and builds an image of the service.
    """
    run_innerloop_command('build')


def _service_run():
    """
    Calls tenx run command on the current directory.
    Run implicitly builds the service in the cluster and starts the service.
    """
    run_innerloop_command('run -t')


def run_innerloop_command(*args):
    """
    Calls InnerLoop client to set up a tenx project for a multi-container Docker application.
    """
    try:
        file_path = _get_innerloop_home_path()
        cmd = os.path.join(file_path, 'tenx.cmd') if(
            platform.system() == 'Windows') else os.path.join(file_path, 'tenx.sh')
        cmd = cmd + ' ' + ' '.join(args)

        # Prints subprocess output while process is running
        with Popen(cmd, shell=True, stdout=PIPE, bufsize=1, universal_newlines=True) as process:
            for line in process.stdout:
                sys.stdout.write(line)

        if process.returncode != 0:
            raise CLIError(CalledProcessError(process.returncode, cmd))
    except Exception as error:
        raise CLIError(error)


def _get_innerloop_home_path():
    """
    Gets the Mindaro-InnerLoop set HOME path.
    """
    try:
        env_var = "TENX_HOME"
        # TODO: to use az_config.get() when we update the env_var name to
        # AZURE_CONTAINER_INNERLOOP_HOME or anything else
        file_path = os.environ[env_var]
        return file_path
    except KeyError as error:
        raise CLIError(
            'Temporary: Please set the environment variable: {} to your inner loop source code directory.'.format(error))
    except Exception as error:
        raise CLIError(error)
