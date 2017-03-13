# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64
import codecs
import glob
import json
import os
import platform
import sys
from subprocess import PIPE, CalledProcessError, Popen, check_output
import requests

import azure.cli.command_modules.project.settings as settings
import azure.cli.command_modules.project.utils as utils
import azure.cli.core.azlogging as azlogging  # pylint: disable=invalid-name
from azure.cli.command_modules.project.jenkins import Jenkins
from azure.cli.command_modules.project.spinnaker import Spinnaker
from azure.cli.core._util import CLIError
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.mgmt.compute import ComputeManagementClient

logger = azlogging.get_az_logger(__name__) # pylint: disable=invalid-name
project_settings = settings.Project() # pylint: disable=invalid-name

# TODO: Remove and switch to SSH once templates are updated
admin_password = 'Mindaro@Pass1!' # pylint: disable=invalid-name
# pylint: disable=too-few-public-methods,too-many-arguments,no-self-use,too-many-locals,line-too-long,broad-except

def create_continuous_deployment(remote_access_token): # pylint: disable=unused-argument
    """
    Provisions Jenkins and Spinnaker, configures CI and CD pipelines, kicks off initial build-deploy
    and saves the CI/CD information to a local project file.
    """
    jenkins_resource, jenkins_deployment = _deploy_jenkins()
    spinnaker_resource, spinnaker_deployment = _deploy_spinnaker()

    # Wait for deployments to complete
    spinnaker_deployment.wait()
    jenkins_deployment.wait()
    _ = jenkins_deployment.result()
    jenkins_resource.configure()

    spinnaker_deployment_result = spinnaker_deployment.result()
    spinnaker_hostname = spinnaker_deployment_result.properties.outputs[
        'hostname']['value']

    _configure_spinnaker(spinnaker_resource, spinnaker_hostname)

    # TODO: Spinnker won't trigger pipeline if ACR is entire empty
    # TODO: how do we provide a correct service port when configuring Spinnaker
    utils.writeline('Done.')

def _configure_spinnaker(spinnaker_resource, spinnaker_hostname):
    """
    Configures the Spinnaker resource
    """
    utils.writeline('Configuring Spinnaker...')
    client_id = project_settings.client_id
    client_secret = project_settings.client_secret
    cluster_name = project_settings.cluster_name
    cluster_resource_group = project_settings.cluster_resource_group
    container_registry_url = project_settings.container_registry_url

    acs_info = _get_acs_info(cluster_name, cluster_resource_group)
    spinnaker_resource.configure(
        spinnaker_hostname, acs_info, container_registry_url, 'myrepo/peterj', client_id, client_secret)

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

    jenkins_dns_prefix = 'jenkins-' + utils.get_random_string()
    jenkins_resource = Jenkins(
        resource_group, admin_username,
        admin_password, client_id, client_secret,
        git_repo, jenkins_dns_prefix,
        container_registry_url)
    return (jenkins_resource, jenkins_resource.deploy())


def _deploy_spinnaker():
    """
    Starts the Spinnaker deployment and returns the resource and AzurePollerOperation
    """
    utils.writeline('Deploying Spinnaker...')
    resource_group = project_settings.resource_group
    admin_username = project_settings.admin_username
    public_ssh_key_filename = os.path.join(
        os.path.expanduser("~"), '.ssh', 'id_rsa.pub')

    spinnaker_dns_prefix = 'spinnaker-' + utils.get_random_string()
    spinnaker_resource = Spinnaker(
        resource_group, admin_username, public_ssh_key_filename, spinnaker_dns_prefix)
    return (spinnaker_resource, spinnaker_resource.deploy())


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

def setup(dns_prefix, location, user_name):
    """
    Initializes a workspace definition that automates connection to a Kubernetes cluster in an Azure container
    service for deploying services.

    :param dns_prefix: Prefix used to create a unique fully qualified domain name (FQDN) for the master.
    :type dns_prefix: String
    :param location: Azure region for the Azure Container Service deployment.
    :type location: String
    :param user_name: User name for an account on each of the Linux virtual machines in the cluster.
    :type user_name: String
    """
    _configure_cluster(dns_prefix, location, user_name)

def _configure_cluster(dns_prefix, location, user_name): # pylint: disable=too-many-statements
    """
    Configures the cluster to deploy tenx services which can be used by the user deployed services and initializes
    a workspace on the local machine to connection.
    Asks for user input: ACR server name.
    """
    try:
        innerloop_client_path = _get_innerloop_home_path()
        kubernetes_path = os.path.join(innerloop_client_path, 'setup', 'Kubernetes')

        if _cluster_configured(dns_prefix, user_name):
            sys.stdout.write(' Cluster already configured.\n')
            return
        else:
            sys.stdout.write(' Cluster not configured.\n')

        sys.stdout.write(' Configuring Kubernetes cluster\n')

        # Get resource group
        creds = _get_creds_from_master(dns_prefix, location, user_name)
        resource_group = creds['resourceGroup']
        client_id = creds['aadClientId']
        client_secret = creds['aadClientSecret']

        # Cluster Setup(deploying required artifacts in the kubectl nodes)
        sys.stdout.write('\nPlease ensure these requirements are met:')
        sys.stdout.write('\n1. You have created a Kubernetes cluster in ACS, installed kubectl on this computer and are able to connect to your Kubernetes cluster.')
        sys.stdout.write('\n2. You have created an Azure Container Registry in the same Azure Subscription.')

        # TODO: Remove the below input when azp create will be implemented and we can take the acr_server_name from the resource file generated by azp create
        acr_server = input("\nPlease enter the Azure Container Registry server name, such as test-microsoft.azurecr.io, to continue.\nOtherwise, please press Ctrl-C: ")

        sys.stdout.write('\n Preparing ARM configuration\n')
        _prepare_arm_k8(dns_prefix)

        sys.stdout.write('\n Creating Resources\n')
        sys.stdout.write(' This is going to take a while. Sit back and relax.\n')
        deployment_command = "az group deployment create --template-file {0}/k8.deploy.json --parameters \
        '@{0}/k8.deploy.parameters.tmp.json' -g {1} -n {2}".format(kubernetes_path, resource_group, dns_prefix)
        _execute_command(deployment_command)
        sys.stdout.write('\n Done with the resources!\n')

        sys.stdout.write('\n Creating tenx namespace\n')
        namespace_command = "kubectl create namespace tenx"
        _execute_command(namespace_command, True)

        sys.stdout.write('\n Deploying ACR credentials in Kubernetes\n')
        workspace_storage_key = _deploy_secrets_share_k8(acr_server, resource_group, dns_prefix, client_id, client_secret, location, user_name)

        sys.stdout.write('\n Enumerating Kubernetes agents\n')
        _enumerate_k8_agents(innerloop_client_path)

        sys.stdout.write('\n Preparing the cluster\n')
        remote_host = _get_remote_host(user_name, dns_prefix, location)
        ssh_private_key = _get_ssh_private_key()
        _execute_command("ssh -i {0} -o StrictHostKeyChecking=no -p 22 {1} 'mkdir ~/.azure'".format(ssh_private_key, remote_host), True)
        _execute_command("ssh -i {0} -p 22 {1} 'mkdir ~/.ssh'".format(ssh_private_key, remote_host), True)
        _execute_command("scp -i {0} -P 22 {1}/hosts.tmp {2}:~/hosts".format(ssh_private_key, kubernetes_path, remote_host))

        sys.stdout.write('\n Copying configuration files into the cluster\n')

        _execute_command("scp -i {1} -P 22 {1} {0}:~/.ssh/id_rsa".format(remote_host, ssh_private_key))
        _execute_command("scp -i {2} -P 22 {1}/connectlocal.tmp.sh {0}:~/connectlocal.tmp.sh".format(remote_host, kubernetes_path, ssh_private_key))
        _execute_command("scp -i {2} -P 22 {1}/configagents.sh {0}:~/configagents.sh".format(remote_host, kubernetes_path, ssh_private_key))

        _execute_command("ssh -i {0} -o StrictHostKeyChecking=no -p 22 {1} 'chmod 600 ~/.ssh/id_rsa'".format(ssh_private_key, remote_host))
        _execute_command("ssh -i {0} -o StrictHostKeyChecking=no -p 22 {1} 'chmod +x ./configagents.sh'".format(ssh_private_key, remote_host))

        sys.stdout.write('\n Configuring agents in the cluster\n')

        _execute_command("ssh -i {0} -p 22 {1} 'source ./configagents.sh'".format(ssh_private_key, remote_host))

        sys.stdout.write('\n Deploying TenX services to K8 cluster\n')

        _execute_command("kubectl create -f {0}/tenx.tmp.yaml".format(kubernetes_path), True)
        _execute_command("kubectl create -f {0}/tenxPrivate.tmp.yaml".format(kubernetes_path), True)

        sys.stdout.write('\n Cleaning existing TenX services in cluster, if any\n')
        _execute_command("kubectl delete -f {0}/tenxServices.yaml -n tenx".format(kubernetes_path), True)
        _execute_command("kubectl delete -f {0}/tenxPrivateService.yaml -n tenx".format(kubernetes_path), True)
        _execute_command("kubectl delete -f {0}/tenxConfigService.yaml -n tenx".format(kubernetes_path), True)
        _execute_command("kubectl delete -f {0}/tenxBuildService.yaml -n tenx".format(kubernetes_path), True)
        _execute_command("kubectl delete -f {0}/tenxExecService.yaml -n tenx".format(kubernetes_path), True)
        _execute_command("kubectl delete -f {0}/tenxRsrcService.yaml -n tenx".format(kubernetes_path), True)
        _execute_command("kubectl delete -f {0}/tenxPublicEndpoint.yaml -n tenx".format(kubernetes_path), True)

        sys.stdout.write('\n Exposing TenX services from cluster\n')
        _execute_command("kubectl create -f {0}/tenxServices.yaml -n tenx".format(kubernetes_path))
        _execute_command("kubectl create -f {0}/tenxPrivateService.yaml -n tenx".format(kubernetes_path))
        _execute_command("kubectl create -f {0}/tenxConfigService.yaml -n tenx".format(kubernetes_path))
        _execute_command("kubectl create -f {0}/tenxBuildService.yaml -n tenx".format(kubernetes_path))
        _execute_command("kubectl create -f {0}/tenxExecService.yaml -n tenx".format(kubernetes_path))
        _execute_command("kubectl create -f {0}/tenxRsrcService.yaml -n tenx".format(kubernetes_path))
        _execute_command("kubectl create -f {0}/tenxPublicEndpoint.yaml -n tenx".format(kubernetes_path))

        # Initialize Workspace
        sys.stdout.write("\n Initializing Workspace: {0}".format(dns_prefix))
        sys.stdout.write(' This might take some waiting.\n')
        workspace_storage = dns_prefix.replace('-', '') + "wks"
        _initialize_workspace(dns_prefix, workspace_storage, workspace_storage_key)
    finally:
        # Removing temporary data files
        file_path = os.path.join(kubernetes_path, '*.tmp.*')
        files = glob.glob(file_path)
        for file in files:
            os.remove(file)

def _cluster_configured(dns_prefix, user_name): # pylint: disable=too-many-return-statements
    """
    Detects if the cluster exists and already configured i.e. all the required services are available and running.
    The check is done in 2 parts:
    1. Checks if the workspace is initialized (settings.json exists)
    2. Checks if all the services are running by pinging each URL.
    """

    sys.stdout.write('\n Detecting if the cluster exists\n')
    settings_json_file_path = _get_workspace_settings_file()
    workspace_err_message = '  Workspace not defined.'
    if not os.path.exists(settings_json_file_path):
        logger.warning(workspace_err_message)
        return False
    cluster_settings = json.load(codecs.open(settings_json_file_path, 'r', 'utf-8-sig'))

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
        if not _ping_url("{0}/{1}".format(build_service_url, url_sub_path)):
            return False

        exec_service_url = default_workspace["ExecServiceUrl"]
        logger.info('  Checking exec service')
        if not _ping_url("{0}/{1}".format(exec_service_url, url_sub_path)):
            return False

        rsrc_service_url = default_workspace["RsrcServiceUrl"]
        logger.info('  Checking rsrc service')
        if not _ping_url("{0}/{1}".format(rsrc_service_url, url_sub_path)):
            return False

        config_service_url = default_workspace["ConfigServiceUrl"]
        logger.info('  Checking config service')
        if not _ping_url("{0}/{1}".format(config_service_url, url_sub_path)):
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
    hosts_file_path = os.path.join(innerloop_client_path, 'setup', 'Kubernetes', 'hosts.tmp')

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
    Install cluster/registry secrets and creates sahre on the file storage.
    """
    _install_k8_secret(acr_server, dns_prefix, client_id, client_secret, location, user_name)
    workspace_storage_key = _install_k8_shares(resource_group, dns_prefix)
    return workspace_storage_key

def _install_k8_secret(acr, dns_prefix, user_name, password, location, cluster_user_name):
    """
    Creates a registry secret in the cluster, used by the tenx services.
    Prepares the file to create resource in the Kubernetes cluster.
    """
    kubectl_create_secret_command = "kubectl create secret docker-registry tenxregkey --docker-server={0} --docker-username={1} \
    --docker-password={2} --docker-email={3} -n tenx".format(acr, user_name, password, _get_creds_from_master(dns_prefix, location, cluster_user_name))
    try:
        _execute_command(kubectl_create_secret_command)
    except Exception:
        logger.debug("Command failed: %s\n", kubectl_create_secret_command)

    config_storage = dns_prefix.replace('-', '') + "cfgsa"
    private_storage = dns_prefix.replace('-', '') + "private"

    try:
        innerloop_client_path = _get_innerloop_home_path()
        tenx_yaml_path = os.path.join(innerloop_client_path, 'setup', 'Kubernetes', 'tenx.yaml')
        with open(tenx_yaml_path, "r") as tenx_yaml_file:
            tenx_yaml = tenx_yaml_file.read()
        tmp_tenx_yaml = tenx_yaml.replace("$TENX_PRIVATE_REGISTRY$", acr).replace("$TENX_STORAGE_ACCOUNT$", config_storage)

        tmp_tenx_yaml_path = os.path.join(innerloop_client_path, 'setup', 'Kubernetes', 'tenx.tmp.yaml')
        with open(tmp_tenx_yaml_path, "w") as tmp_tenx_yaml_file:
            tmp_tenx_yaml_file.write(tmp_tenx_yaml)

        tenx_private_yaml_path = os.path.join(innerloop_client_path, 'setup', 'Kubernetes', 'tenxPrivate.yaml')
        with open(tenx_private_yaml_path, "r") as tenx_private_yaml_file:
            tenx_private_yaml = tenx_private_yaml_file.read()
        tmp_tenx_private_yaml = tenx_private_yaml.replace("$TENX_STORAGE_ACCOUNT_PRIVATE$", private_storage)

        tmp_tenx_private_yaml_path = os.path.join(innerloop_client_path, 'setup', 'Kubernetes', 'tenxPrivate.tmp.yaml')
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

    try:
        storage_command = "az storage account keys list -n {0} -g {1}".format(config_storage, resource_group)
        keys_list = _get_command_output(storage_command)
        keys_list_json = json.loads(keys_list)
        config_storage_key = keys_list_json[0]['value']
    except Exception as error:
        logger.debug(error)
        raise CLIError("Can't get storage account key for {0}".format(config_storage))

    try:
        wks_storage_command = "az storage account keys list -n {0} -g {1}".format(workspace_storage, resource_group)
        keys_list = _get_command_output(wks_storage_command)
        keys_list_json = json.loads(keys_list)
        workspace_storage_key = keys_list_json[0]['value']
    except Exception as error:
        logger.debug(error)
        raise CLIError("Can't get storage account key for {0}".format(workspace_storage))

    innerloop_client_path = _get_innerloop_home_path()
    connect_template_path = os.path.join(innerloop_client_path, 'setup', 'Kubernetes', 'connectlocal.template.sh')
    with open(connect_template_path, "r") as connect_template_file:
        connect_template = connect_template_file.read()
    connect_template = connect_template.replace("$STORAGEACCOUNT_PRIVATE$", config_storage) \
        .replace("$STORAGE_ACCOUNT_PRIVATE_KEY$", config_storage_key) \
        .replace("$STORAGEACCOUNT$", workspace_storage) \
        .replace("$STORAGE_ACCOUNT_KEY$", workspace_storage_key) \
        .replace("$SHARE_NAME$", "mindaro")

    connect_output = os.path.join(innerloop_client_path, 'setup', 'Kubernetes', 'connectlocal.tmp.sh')
    with open(connect_output, "w") as connect_output_file:
        connect_output_file.write(connect_template)

    # Ensure 'cfgs' share exists in configStorage
    _execute_command("az storage share create -n 'cfgs' --account-name {0} --account-key {1}".format(config_storage, config_storage_key))

    # Ensure 'mindaro' share exists in configStorage
    _execute_command("az storage share create -n 'mindaro' --account-name {0} --account-key {1}".format(workspace_storage, workspace_storage_key))

    return workspace_storage_key

def to_base64(string_value):
    """
    Converts string to base64 string.
    """
    encoding = "utf-8"
    return base64.b64encode(bytes(string_value, encoding)).decode(encoding)

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
    encoding = "utf-8"
    output = ''
    with Popen(command, shell=True, stdout=PIPE, stderr=PIPE) as process:
        for line in process.stdout:
            output = output +(line.rstrip().decode(encoding)) + '\n'
    if process.returncode != 0:
        raise CLIError(CalledProcessError(process.returncode, command))

    return output

def _get_creds_from_master(dns_prefix, location, user_name):
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

    _execute_command("scp -i {0} -P 22 {1}:/etc/kubernetes/azure.json {2}".format(_get_ssh_private_key(), _get_remote_host(user_name, dns_prefix, location), azure_json_file))

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

def _get_ssh_private_key():
    """
    Provides ssh private key file path.
    """
    ssh_private_key_file = os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa')
    return ssh_private_key_file

def _get_remote_host(user_name, dns_prefix, location):
    """
    Provides a remote host according to the passed user_name, dns_prefix and location.
    """
    return "{0}@{1}.{2}.cloudapp.azure.com".format(user_name, dns_prefix, location)

def _prepare_arm_k8(dns_prefix):
    """
    Prepares template file for configuring the Kubernetes cluster.
    """
    try:
        innerloop_client_path = _get_innerloop_home_path()
        k8_parameters_file_path = os.path.join(innerloop_client_path, 'setup', 'Kubernetes', 'k8.deploy.parameters.json')
        with open(k8_parameters_file_path, "r") as k8_parameters_file:
            k8_parameters = k8_parameters_file.read()
        new_k8_parameters = k8_parameters.replace("CLUSTER_NAME", dns_prefix.replace('-', ''))

        new_k8_parameters_file_path = os.path.join(innerloop_client_path, 'setup', 'Kubernetes', 'k8.deploy.parameters.tmp.json')
        with open(new_k8_parameters_file_path, "w") as new_k8_parameters_file:
            new_k8_parameters_file.write(new_k8_parameters)

    except FileNotFoundError as error:
        raise CLIError(error)

def _initialize_workspace(
        dns_prefix,
        storage_account_name,
        storage_account_key,
        workspace_share_name='mindaro'):
    """
    Calls tenx initialize command on the current directory.
    Initialize creates settings.json file which contains all the credentials and links to connect to the cluster.
    """

    # TODO: to remove this below code to delete settings.json when we support multiple sublevel workspaces
    settings_json_file = _get_workspace_settings_file()
    if os.path.exists(settings_json_file):
        os.remove(settings_json_file)

    run_innerloop_command('initialize', workspace_share_name, dns_prefix, storage_account_name, storage_account_key, workspace_share_name, '--k8')

def service_run(dns_prefix, location, project_path, user_name):
    """
    Automates building the project/service in a Docker image and pushing to an Azure container registry,
    and creates a release definition that automates deploying container images from a container registry
    to a Kubernetes cluster in an Azure container service. Then deploying the project as a service and running it.

    Run configures the cluster, if not already, then builds the service in the cluster and starts the service.

    :param dns_prefix: Prefix used to create a unique fully qualified domain name (FQDN) for the master.
    :type dns_prefix: String
    :param location: Azure region for the Azure Container Service deployment.
    :type location: String
    :param project_path: Project/Service path to deploy on the Kubernetes cluster or current directory.
    :type project_path: String
    :param user_name: User name for an account on each of the Linux virtual machines in the cluster.
    :type user_name: String
    """

    curr_dir = None
    try:
        if not project_path == ".":
            curr_dir = os.getcwd()
            os.chdir(project_path)
            project_path = curr_dir
        elif not os.path.exists(project_path):
            raise CLIError("Invalid path: {0}".format(project_path))

        # Configuring Cluster
        _configure_cluster(dns_prefix, location, user_name)

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
    run_innerloop_command('run')

def run_innerloop_command(*args):
    """
    Calls InnerLoop client to set up a tenx project for a multi-container Docker application.
    """
    try:
        file_path = _get_innerloop_home_path()
        cmd = os.path.join(file_path, 'tenx.cmd') if(platform.system() == 'Windows') else os.path.join(file_path, 'tenx.sh')
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
        # TODO: to use az_config.get() when we update the env_var name to AZURE_CONTAINER_INNERLOOP_HOME or anything else
        file_path = os.environ[env_var]
        return file_path
    except KeyError as error:
        raise CLIError('Temporary: Please set the environment variable: {0} to your inner loop source code directory.'.format(error))
    except Exception as error:
        raise CLIError(error)
