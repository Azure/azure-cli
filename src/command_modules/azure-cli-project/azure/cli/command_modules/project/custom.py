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
from time import sleep
from subprocess import (PIPE,
                        CalledProcessError,
                        Popen,
                        check_output)
from scp import SCPClient
from sshtunnel import SSHTunnelForwarder
import requests
import paramiko
import azure.cli.command_modules.project.settings as settings
import azure.cli.command_modules.project.utils as utils
import azure.cli.core.azlogging as azlogging  # pylint: disable=invalid-name

from azure.cli.command_modules.acs._params import _get_default_install_location
from azure.cli.command_modules.acs.custom import (acs_create,
                                                  k8s_get_credentials,
                                                  k8s_install_cli)
from azure.cli.command_modules.project.jenkins import Jenkins
from azure.cli.command_modules.resource.custom import _deploy_arm_template_core
from azure.cli.command_modules.storage._factory import storage_client_factory
from azure.cli.core._config import az_config
from azure.cli.core._environment import get_config_dir
from azure.cli.core._profile import Profile
from azure.cli.core._util import CLIError
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.containerregistry.models import Sku as AcrSku
from azure.mgmt.containerregistry.models import (RegistryCreateParameters,
                                                 StorageAccountParameters)
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.mgmt.resource.resources.models.resource_group import ResourceGroup
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import Kind, Sku, StorageAccountCreateParameters
from azure.storage.file import FileService
from six.moves.urllib.error import URLError  # pylint: disable=import-error
from six.moves.urllib.request import urlopen  # pylint: disable=import-error

logger = azlogging.get_az_logger(__name__)  # pylint: disable=invalid-name
project_settings = settings.Project()  # pylint: disable=invalid-name
random_name = utils.get_random_name()  # pylint: disable=invalid-name

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
    local_address = 'http://127.0.0.1:{}/blue'.format(local_port)
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


def create_project(ssh_private_key, resource_group=random_name, name=random_name, location='southcentralus', force_create=False):
    """
    Creates a new project which consists of a new resource group,
    ACS Kubernetes cluster and Azure Container Registry
    """
    default_user_name = 'azureuser'
    longprocess = None
    current_process = None

    try:
        utils.write('Creating Project ')
        # Validate if mindaro project already exists
        if (not force_create) and project_settings.project_name:
            utils.write(
                '{} ...'.format(project_settings.project_name))
            sleep(5)
            logger.info('\nProject already exists.')
            utils.write('Complete.\n')
            return
        else:
            utils.write(
                '{} ...'.format(name))

        # 0. Validate ssh private key path
        if not os.path.exists(ssh_private_key):
            raise CLIError(
                "ssh key does not exist: {}, please run 'ssh-keygen -b 1024' to generate it or pass the correct ssh key.".format(ssh_private_key))

        longprocess = utils.Process()
        current_process = longprocess
        # 1. Create a resource group: resource_group, location
        utils.log(
            '\nCreating resource group ... ', logger)
        res_client = _get_resource_client_factory()
        resource_group_parameters = ResourceGroup(
            location=location)
        res_client.resource_groups.create_or_update(
            resource_group, resource_group_parameters)
        utils.log(
            'Resource group "{}" created.'.format(resource_group), logger)

        # 2. Create a storage account (for ACR)
        utils.log(
            'Creating storage account ... ', logger)
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
        utils.log(
            'Storage account "{}" created.'.format(storage_account_name), logger)

        # 3. Create ACR (resource_group, location)
        utils.log(
            'Creating Azure container registry ... ', logger)
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
        utils.log(
            'Azure container registry "{}" created.'.format(acr_name), logger)

        # 4. Create Kubernetes cluster
        utils.log(
            'Creating Kubernetes cluster ... ', logger)
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
        utils.log(
            'Kubernetes cluster "{}" created.'.format(kube_cluster_name), logger)

        # 5. Install kubectl
        utils.log(
            'Installing kubectl ... ', logger)
        k8s_install_cli(
            install_location=_get_default_install_location('kubectl'))
        utils.log(
            'Kubernetes installed.', logger)

        # 6. Set Kubernetes config
        utils.log(
            'Setting Kubernetes config ... ', logger)
        k8s_get_credentials(name=kube_cluster_name,
                            resource_group_name=resource_group,
                            ssh_key_file=ssh_private_key)
        utils.log(
            'Kubernetes config "{}" created.'.format(kube_cluster_name), logger)

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
        project_settings.container_registry_url = 'https://' + \
            registry.login_server  # pylint: disable=no-member
        project_settings.location = location
        project_settings.project_name = name
        project_settings.ssh_private_key = ssh_private_key
        utils.log(
            'Project "{}" created.'.format(name), logger)

        # 8. Configure the Kubernetes cluster
        # Initializes a workspace definition that automates connection to a Kubernetes cluster
        # in an Azure container service for deploying services.
        _configure_cluster()

        if longprocess:
            longprocess.process_stop()
        current_process = None
        utils.write(' Complete.\n')
    except KeyboardInterrupt:
        utils.writeline('Killing process ...')
    finally:
        if current_process:
            current_process.process_stop()


def create_deployment_pipeline(remote_access_token):  # pylint: disable=unused-argument
    """
    Provisions Jenkins and configures CI and CD pipelines, kicks off initial build-deploy
    and saves the CI/CD information to a local project file.
    """
    jenkins_resource, jenkins_deployment = _deploy_jenkins()

    # Wait for deployments to complete
    jenkins_deployment.wait()

    jenkins_hostname = _get_remote_host(
        jenkins_resource.dns_prefix, jenkins_resource.location)
    project_settings.jenkins_hostname = jenkins_hostname
    project_settings.set_ci_pipeline_name(
        jenkins_resource._get_ci_job_name(), _get_git_remote_url())
    project_settings.set_cd_pipeline_name(
        jenkins_resource._get_cd_job_name(), _get_git_remote_url())

    utils.writeline('Jenkins hostname: {}'.format(jenkins_hostname))
    utils.writeline('Complete.')


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
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_client.bind(('', 0))
    socket_client.listen(1)
    port = socket_client.getsockname()[1]
    socket_client.close()
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
    utils.log('Deploying Jenkins ... ', logger)
    git_repo = _get_git_remote_url()
    resource_group = project_settings.resource_group
    client_id = project_settings.client_id
    client_secret = project_settings.client_secret
    admin_username = project_settings.admin_username
    container_registry_url = project_settings.container_registry_url
    location = project_settings.location
    project_name = project_settings.project_name

    # TODO: Where do we get the service name from?
    service_name = os.path.basename(os.getcwd())

    jenkins_dns_prefix = 'jenkins-' + utils.get_random_string()
    jenkins_resource = Jenkins(
        resource_group, admin_username,
        admin_password, client_id, client_secret,
        git_repo, jenkins_dns_prefix, location,
        container_registry_url, service_name, project_name,
        _get_pipeline_name())
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


def _get_git_root_folder_name():
    """
    Gets the git root folder name. E.g. if current folder is
    /myfolder/subfolder/test and the git repo root is /myfolder
    this method returns myfolder
    """
    full_path = check_output(['git', 'rev-parse', '--show-toplevel'])
    return os.path.basename(full_path.decode().strip())


def _get_pipeline_name():
    """
    Gets the name used for Jenkins pipelines by
    getting the current folder, partitioning it at base_repo_name
    taking the string on the right (subfolder) replacing '/' with '-'
    and combine the both strings. For example:
    if command is run in the root folder of BikeSharing of the
    repository Contoso/BikeSharing, this method returns 'Contoso/BikeSharing'.
    If command is run in a subfolder (e.g. BikeSharing/reservations/api), method
    returns Contoso/BikeSharing-reservations-api
    """
    remote_url = _get_git_remote_url()
    # Get owner|organization/repo e.g. BikeSharing/reservations
    # and replace '/' with '-' as '/' can't be used in the pipeline name
    # which becomes a part of the URL
    owner_repo = remote_url.partition('github.com/')[2].replace('/', '-')

    base_repo_name = _get_git_root_folder_name()
    current_directory = os.getcwd()
    subfolders = current_directory.partition(
        base_repo_name)[2].strip('/').replace('/', '-')
    return '-'.join([owner_repo, subfolders]).strip('-')


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
            'Please ensure git version 3.5.0 or greater is installed.\n' + called_process_err)
    return remote_url.decode()


def _configure_cluster():  # pylint: disable=too-many-statements
    """
    Configures the cluster to deploy tenx services which can be used by the user
    deployed services and initializes a workspace on the local machine to connection.
    Asks for user input: ACR server name.
    """
    artifacts_path = None
    ssh_client = None
    scp_client = None
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
            raise CLIError(
                "kubectl context not set to {}, please run 'az acs kubernetes get-credentials' to set it.".format(dns_prefix))

        if _cluster_configured(dns_prefix, user_name):
            utils.log(
                'Cluster already configured.', logger)
            return
        else:
            logger.debug(
                'Cluster not configured.')

        utils.log(
            'Configuring Kubernetes cluster ... ', logger)

        innerloop_client_path = _get_innerloop_home_path()
        artifacts_path = os.path.join(
            innerloop_client_path, 'Artifacts')

        # Removing existing cluster from ~/.ssh/known_hosts
        known_hostname_command = 'ssh-keygen -R {}'.format(
            _get_remote_host(dns_prefix, location))
        _execute_command(known_hostname_command, True)

        # SSHClient connection
        port = 22
        ssh_client = _get_ssh_client(
            user_name, dns_prefix, location, port, ssh_private_key)
        # SCPCLient takes a paramiko transport as its only argument
        scp_client = SCPClient(
            ssh_client.get_transport())

        # Get resource group
        creds = _get_creds_from_master(scp_client)
        resource_group = creds['resourceGroup']
        client_id = creds['aadClientId']
        client_secret = creds['aadClientSecret']

        # Cluster Setup(deploying required artifacts in the kubectl nodes)
        utils.log('Preparing ARM configuration ... ', logger)
        k8_parameters = _prepare_arm_k8(dns_prefix, artifacts_path)
        utils.log(
            'ARM configuration prepared.', logger)

        utils.log('Creating Resources ... ', logger)
        _deploy_arm_template_core(
            resource_group, template_file='{}/k8.deploy.json'.format(artifacts_path), deployment_name=dns_prefix,
            parameters=k8_parameters)
        utils.log(
            'ARM template deployed.', logger)

        utils.log(
            'Creating tenx namespace ... ', logger)
        namespace_command = "kubectl create namespace tenx"
        _execute_command(namespace_command, True, 10)

        utils.log(
            'Deploying ACR credentials in Kubernetes ... ', logger)
        workspace_storage_key = _deploy_secrets_share_k8(
            acr_server, resource_group, dns_prefix, client_id, client_secret, location, user_name, artifacts_path)
        utils.log(
            'ACR credentials deployed.', logger)

        utils.log(
            'Enumerating Kubernetes agents ... ', logger)
        _enumerate_k8_agents(artifacts_path)

        utils.log(
            'Preparing the cluster ... ', logger)
        _run_remote_command(
            'mkdir ~/.azure', ssh_client)
        _run_remote_command(
            'mkdir ~/.ssh', ssh_client)
        _run_remote_command(
            'rm ~/hosts', ssh_client)
        scp_client.put(
            '{}/hosts.tmp'.format(artifacts_path), '~/hosts')
        utils.log(
            'Cluster prepared.', logger)

        utils.log(
            'Copying configuration files into the cluster ... ', logger)
        scp_client.put(
            ssh_private_key, '~/.ssh/id_rsa')
        scp_client.put(
            '{}/connectlocal.tmp.sh'.format(artifacts_path), '~/connectlocal.tmp.sh')
        scp_client.put(
            '{}/configagents.sh'.format(artifacts_path), '~/configagents.sh')

        _run_remote_command(
            'chmod 600 ~/.ssh/id_rsa', ssh_client)
        _run_remote_command(
            'chmod +x ./configagents.sh', ssh_client)
        utils.log(
            'Configuration files copied.', logger)

        utils.log(
            'Configuring agents in the cluster ... ', logger)
        _run_remote_command(
            'source ./configagents.sh', ssh_client, True)

        utils.log(
            'Cleaning existing TenX services in cluster ... ', logger)
        _execute_command(
            "kubectl delete -f {}/tenx.tmp.yaml".format(artifacts_path), True)
        _execute_command(
            "kubectl delete -f {}/tenxPrivate.tmp.yaml".format(artifacts_path), True)
        _execute_command(
            "kubectl delete -f {}/tenxServices.yaml -n tenx".format(artifacts_path), True)
        _execute_command(
            "kubectl delete -f {}/tenxPrivateService.yaml -n tenx".format(artifacts_path), True)
        _execute_command(
            "kubectl delete -f {}/tenxConfigService.yaml -n tenx".format(artifacts_path), True)
        _execute_command(
            "kubectl delete -f {}/tenxBuildService.yaml -n tenx".format(artifacts_path), True)
        _execute_command(
            "kubectl delete -f {}/tenxExecService.yaml -n tenx".format(artifacts_path), True)
        _execute_command(
            "kubectl delete -f {}/tenxRsrcService.yaml -n tenx".format(artifacts_path), True)
        _execute_command(
            "kubectl delete -f {}/tenxPublicEndpoint.yaml -n tenx".format(artifacts_path), True)

        utils.log(
            'Deploying TenX services to K8 cluster ... ', logger)
        _execute_command(
            "kubectl create -f {}/tenx.tmp.yaml".format(artifacts_path), True)
        _execute_command(
            "kubectl create -f {}/tenxPrivate.tmp.yaml".format(artifacts_path), True)

        utils.log(
            'Exposing TenX services from cluster ... ', logger)
        _execute_command(
            "kubectl create -f {}/tenxServices.yaml -n tenx".format(artifacts_path))
        _execute_command(
            "kubectl create -f {}/tenxPrivateService.yaml -n tenx".format(artifacts_path))
        _execute_command(
            "kubectl create -f {}/tenxConfigService.yaml -n tenx".format(artifacts_path))
        _execute_command(
            "kubectl create -f {}/tenxBuildService.yaml -n tenx".format(artifacts_path))
        _execute_command(
            "kubectl create -f {}/tenxExecService.yaml -n tenx".format(artifacts_path))
        _execute_command(
            "kubectl create -f {}/tenxRsrcService.yaml -n tenx".format(artifacts_path))
        _execute_command(
            "kubectl create -f {}/tenxPublicEndpoint.yaml -n tenx".format(artifacts_path))

        # Initialize Workspace
        utils.log(
            'Initializing Workspace: {} ... '.format(dns_prefix), logger)
        workspace_storage = dns_prefix.replace('-', '') + 'wks'
        _initialize_workspace(
            dns_prefix, user_name, workspace_storage, workspace_storage_key, ssh_private_key, location=location)
    finally:
        # Removing temporary data files
        if artifacts_path:
            file_path = os.path.join(artifacts_path, '*.tmp.*')
            files = glob.glob(file_path)
            for single_file in files:
                os.remove(single_file)

        # Removing temporary creds file: azure.json
        azure_json_file = _get_creds_file()
        if os.path.exists(azure_json_file):
            os.remove(azure_json_file)

        # Close SSHClient
        if scp_client:
            scp_client.close()
        if ssh_client:
            ssh_client.close()


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

    utils.log(
        'Detecting if the cluster is configured ... ', logger)
    settings_json_file_path = _get_workspace_settings_file()
    workspace_err_message = '  Workspace not defined.'
    if not os.path.exists(settings_json_file_path):
        logger.debug(workspace_err_message)
        return False
    cluster_settings = json.load(codecs.open(
        settings_json_file_path, 'r', 'utf-8-sig'))

    default_workspace_name = cluster_settings["DefaultWorkspace"]
    if not default_workspace_name:
        logger.debug(workspace_err_message)
        return False

    default_workspace = cluster_settings["Workspaces"][default_workspace_name]
    if not default_workspace:
        logger.debug(workspace_err_message)
        return False

    cluster = default_workspace["Cluster"]
    ssh_user = default_workspace["SSHUser"]

    if not(cluster == dns_prefix and ssh_user == user_name):
        return False

    try:
        url_sub_path = "api/ping"
        build_service_url = default_workspace["BuildServiceUrl"]
        utils.log('  Checking build service', logger)
        if not _ping_url("{}/{}".format(build_service_url, url_sub_path)):
            return False

        exec_service_url = default_workspace["ExecServiceUrl"]
        utils.log('  Checking exec service', logger)
        if not _ping_url("{}/{}".format(exec_service_url, url_sub_path)):
            return False

        rsrc_service_url = default_workspace["RsrcServiceUrl"]
        utils.log('  Checking rsrc service', logger)
        if not _ping_url("{}/{}".format(rsrc_service_url, url_sub_path)):
            return False

        config_service_url = default_workspace["ConfigServiceUrl"]
        utils.log('  Checking config service', logger)
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


def _enumerate_k8_agents(artifacts_path):
    """
    Enumerate the Kubernetes nodes (agents) and write them in a file to be copied to the master host.
    """
    output = _get_command_output("kubectl get nodes")
    hosts_file_path = os.path.join(
        artifacts_path, 'hosts.tmp')

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


def _deploy_secrets_share_k8(acr_server, resource_group, dns_prefix, client_id, client_secret, location, user_name, artifacts_path):
    """
    Install cluster/registry secrets and creates share on the file storage.
    """
    _install_k8_secret(acr_server, dns_prefix, client_id,
                       client_secret, location, user_name, artifacts_path)
    workspace_storage_key = _install_k8_shares(
        resource_group, dns_prefix, artifacts_path)
    return workspace_storage_key


def _install_k8_secret(acr, dns_prefix, client_id, client_secret, location, cluster_user_name, artifacts_path):
    """
    Creates a registry secret in the cluster, used by the tenx services.
    Prepares the file to create resource in the Kubernetes cluster.
    """
    kubectl_create_delete_command = "kubectl delete secret tenxregkey -n tenx"
    try:
        _execute_command(kubectl_create_delete_command, True)
    except Exception:
        logger.debug("Command failed: %s\n", kubectl_create_delete_command)

    kubectl_create_secret_command = "kubectl create secret docker-registry tenxregkey --docker-server={} --docker-username={} \
    --docker-password={} --docker-email={}@{} -n tenx".format(acr, client_id, client_secret, cluster_user_name, _get_remote_host(dns_prefix, location))
    try:
        _execute_command(kubectl_create_secret_command, True)
    except Exception:
        logger.debug("Command failed: %s\n", kubectl_create_secret_command)

    config_storage = dns_prefix.replace('-', '') + "cfgsa"
    private_storage = dns_prefix.replace('-', '') + "private"

    try:
        innerloop_client_path = _get_innerloop_home_path()
        tenx_yaml_path = os.path.join(
            artifacts_path, 'tenx.yaml')
        with open(tenx_yaml_path, "r") as tenx_yaml_file:
            tenx_yaml = tenx_yaml_file.read()
        tmp_tenx_yaml = tenx_yaml.replace("$TENX_PRIVATE_REGISTRY$", acr).replace(
            "$TENX_STORAGE_ACCOUNT$", config_storage)

        tmp_tenx_yaml_path = os.path.join(
            artifacts_path, 'tenx.tmp.yaml')
        with open(tmp_tenx_yaml_path, "w") as tmp_tenx_yaml_file:
            tmp_tenx_yaml_file.write(tmp_tenx_yaml)

        tenx_private_yaml_path = os.path.join(
            artifacts_path, 'tenxPrivate.yaml')
        with open(tenx_private_yaml_path, "r") as tenx_private_yaml_file:
            tenx_private_yaml = tenx_private_yaml_file.read()
        tmp_tenx_private_yaml = tenx_private_yaml.replace(
            "$TENX_STORAGE_ACCOUNT_PRIVATE$", private_storage)

        tmp_tenx_private_yaml_path = os.path.join(
            artifacts_path, 'tenxPrivate.tmp.yaml')
        with open(tmp_tenx_private_yaml_path, "w") as tmp_tenx_private_yaml_file:
            tmp_tenx_private_yaml_file.write(tmp_tenx_private_yaml)
    except FileNotFoundError as error:
        raise CLIError(error)


def _install_k8_shares(resource_group, dns_prefix, artifacts_path):
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
        artifacts_path, 'connectlocal.template.sh')
    with open(connect_template_path, "r") as connect_template_file:
        connect_template = connect_template_file.read()
    connect_template = connect_template.replace("$STORAGEACCOUNT_PRIVATE$", config_storage) \
        .replace("$STORAGE_ACCOUNT_PRIVATE_KEY$", config_storage_key) \
        .replace("$STORAGEACCOUNT$", workspace_storage) \
        .replace("$STORAGE_ACCOUNT_KEY$", workspace_storage_key) \
        .replace("$SHARE_NAME$", "mindaro")

    connect_output = os.path.join(
        artifacts_path, 'connectlocal.tmp.sh')
    with open(connect_output, "w") as connect_output_file:
        connect_output_file.write(connect_template)

    # Create 'cfgs' share in configStorage
    file_service = FileService(
        account_name=config_storage, account_key=config_storage_key)
    file_service.create_share(share_name='cfgs')

    # Create 'mindaro' share in configStorage
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
            logger.debug(
                "Couldn't get storage account key for {}, Retrying ... ".format(storage))
            sleep(2)
            retry = retry + 1
    if storage_key is None:
        raise CLIError(
            "Can't get storage account key for {}".format(storage))
    return storage_key


def _run_remote_command(command, ssh_client, async_call=False):
    """
    Runs a command on remote
    """
    if async_call:
        transport = ssh_client.get_transport()
        channel = transport.open_session()
        channel.exec_command(
            '{} > /dev/null 2>&1 &'.format(command))
    else:
        _, stdout, stderr = ssh_client.exec_command(command)
        for line in stdout:
            logger.info(line)
        for line in stderr:
            logger.debug(line)


def _get_ssh_client(user_name, dns_prefix, location, port, ssh_private_key):
    """
    Gets SSHClient
    """
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    # TODO: Remove the below command when we support protected SSH Keys
    pkey = paramiko.RSAKey.from_private_key_file(ssh_private_key)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(_get_remote_host(dns_prefix, location),
                port,
                username=user_name,
                pkey=pkey)
    return ssh


def _execute_command(command, ignore_failure=False, tries=1):
    """
    Executes a command.
    """
    retry = 0
    while retry < tries:
        utils.write()
        with Popen(command, shell=True, stdout=PIPE, stderr=PIPE, bufsize=1, universal_newlines=True) as process:
            for line in process.stdout:
                utils.log(line, logger)
            if ignore_failure:
                for err in process.stderr:
                    logger.debug(err)

        if process.returncode == 0:
            break
        else:
            if not ignore_failure:
                raise CLIError(CalledProcessError(process.returncode, command))
        sleep(2)
        retry = retry + 1


def _get_command_output(command):
    """
    Executes a command and provides the output.
    """
    output = check_output(command.split(' ')).strip().decode('utf-8')
    return output


def _get_creds_from_master(scp_client):
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

    scp_client.get(
        '/etc/kubernetes/azure.json', azure_json_file)
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


def _get_remote_host(dns_prefix, location):
    """
    Provides a remote host according to the passed dns_prefix and location.
    """
    return '{}.{}.cloudapp.azure.com'.format(dns_prefix, location)


def _prepare_arm_k8(dns_prefix, artifacts_path):
    """
    Prepares template file for configuring the Kubernetes cluster.
    """
    try:
        innerloop_client_path = _get_innerloop_home_path()
        k8_parameters_file_path = os.path.join(
            artifacts_path, 'k8.deploy.parameters.json')
        with open(k8_parameters_file_path, "r") as k8_parameters_file:
            k8_parameters = k8_parameters_file.read()
        new_k8_parameters = k8_parameters.replace(
            "CLUSTER_NAME", dns_prefix.replace('-', ''))

        new_k8_parameters_file_path = os.path.join(
            artifacts_path, 'k8.deploy.parameters.tmp.json')
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

    _run_innerloop_command('initialize', workspace_share_name, dns_prefix,
                           storage_account_name, storage_account_key, workspace_share_name, location, ssh_private_key, '--quiet', '--k8')

    # Checking if the services are ready
    while not _cluster_configured(dns_prefix, user_name):
        logger.debug(
            '\nServices are not ready yet. Waiting ... ')
        logger.info(
            '\nRetrying ... ')
        sleep(5)
    utils.log(
        'Cluster configured successfully.', logger)


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
            raise CLIError(
                'Invalid path: {}'.format(project_path))

        # Validate if mindaro project exists
        if not os.path.exists(project_settings.settings_file):
            raise CLIError(
                "projectResource.json not found, please run 'az project create' to create resources.")

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
    _run_innerloop_command('build')


def _service_run():
    """
    Calls tenx run command on the current directory.
    Run implicitly builds the service in the cluster and starts the service.
    """
    _run_innerloop_command('run -t -q')


def _run_innerloop_command(*args):
    """
    Calls InnerLoop client to set up a tenx project for a multi-container Docker application.
    """
    try:
        file_path = _get_innerloop_home_path()
        cmd = os.path.join(file_path, 'tenx.dll')
        cmd = cmd + ' ' + ' '.join(args)

        # Prints subprocess output while process is running
        with Popen('dotnet {}'.format(cmd), shell=True, stdout=PIPE, bufsize=1, universal_newlines=True) as process:
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
        home_path = az_config.get(
            'project', 'mindaro_home', None)  # AZURE_PROJECT_MINDARO_HOME
        if home_path is None:
            raise CLIError(
                'Please set the environment variable: AZURE_PROJECT_MINDARO_HOME to your inner loop source code directory.')
        else:
            return home_path
    except Exception as error:
        raise CLIError(error)
