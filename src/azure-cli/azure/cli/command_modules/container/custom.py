# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods,no-self-use,too-many-locals,line-too-long,unused-argument

import errno
try:
    import msvcrt
    from ._vt_helper import enable_vt_mode
except ImportError:
    # Not supported for Linux machines.
    pass
import os
import platform
import shlex
import signal
import sys
import threading
import time
try:
    import termios
    import tty
except ImportError:
    # Not supported for Windows machines.
    pass
import websocket
import yaml
from knack.log import get_logger
from knack.prompting import prompt_pass, prompt, NoTTYException
from knack.util import CLIError
from azure.mgmt.containerinstance.models import (AzureFileVolume, Container, ContainerGroup, ContainerGroupNetworkProtocol,
                                                 ContainerPort, ImageRegistryCredential, IpAddress, Port, ResourceRequests,
                                                 ResourceRequirements, Volume, VolumeMount, ContainerExecRequest, ContainerExecRequestTerminalSize,
                                                 GitRepoVolume, LogAnalytics, ContainerGroupDiagnostics, ContainerGroupSubnetId,
                                                 ContainerGroupIpAddressType, ResourceIdentityType, ContainerGroupIdentity)
from azure.cli.core.util import sdk_no_wait
from azure.cli.core.azclierror import RequiredArgumentMissingError
from ._client_factory import (cf_container_groups, cf_container, cf_log_analytics_workspace,
                              cf_log_analytics_workspace_shared_keys, cf_resource, cf_network, cf_msi)

logger = get_logger(__name__)
WINDOWS_NAME = 'Windows'
SERVER_DELIMITER = '.'
ACR_SERVER_DELIMITER = '.azurecr.io'
AZURE_FILE_VOLUME_NAME = 'azurefile'
SECRETS_VOLUME_NAME = 'secrets'
GITREPO_VOLUME_NAME = 'gitrepo'
MSI_LOCAL_ID = '[system]'


def list_containers(client, resource_group_name=None):
    """List all container groups in a resource group. """
    if resource_group_name is None:
        return client.list()
    return client.list_by_resource_group(resource_group_name)


def get_container(client, resource_group_name, name):
    """Show details of a container group. """
    return client.get(resource_group_name, name)


def delete_container(client, resource_group_name, name, **kwargs):
    """Delete a container group. """
    return client.begin_delete(resource_group_name, name)


# pylint: disable=too-many-statements
def create_container(cmd,
                     resource_group_name,
                     name=None,
                     image=None,
                     location=None,
                     cpu=1,
                     memory=1.5,
                     restart_policy='Always',
                     ports=None,
                     protocol=None,
                     os_type='Linux',
                     ip_address=None,
                     dns_name_label=None,
                     command_line=None,
                     environment_variables=None,
                     secure_environment_variables=None,
                     registry_login_server=None,
                     registry_username=None,
                     registry_password=None,
                     azure_file_volume_share_name=None,
                     azure_file_volume_account_name=None,
                     azure_file_volume_account_key=None,
                     azure_file_volume_mount_path=None,
                     log_analytics_workspace=None,
                     log_analytics_workspace_key=None,
                     vnet=None,
                     vnet_name=None,
                     vnet_address_prefix='10.0.0.0/16',
                     subnet=None,
                     subnet_address_prefix='10.0.0.0/24',
                     gitrepo_url=None,
                     gitrepo_dir='.',
                     gitrepo_revision=None,
                     gitrepo_mount_path=None,
                     secrets=None,
                     secrets_mount_path=None,
                     file=None,
                     assign_identity=None,
                     identity_scope=None,
                     identity_role='Contributor',
                     no_wait=False,
                     acr_identity=None,
                     zone=None):
    """Create a container group. """
    if file:
        return _create_update_from_file(cmd.cli_ctx, resource_group_name, name, location, file, no_wait)

    if not name:
        raise CLIError("error: the --name/-n argument is required unless specified with a passed in file.")

    if not image:
        raise CLIError("error: the --image argument is required unless specified with a passed in file.")

    ports = ports or [80]
    protocol = protocol or ContainerGroupNetworkProtocol.tcp

    container_resource_requirements = _create_resource_requirements(cpu=cpu, memory=memory)

    image_registry_credentials = _create_image_registry_credentials(cmd=cmd,
                                                                    resource_group_name=resource_group_name,
                                                                    registry_login_server=registry_login_server,
                                                                    registry_username=registry_username,
                                                                    registry_password=registry_password,
                                                                    image=image,
                                                                    identity=acr_identity)

    command = shlex.split(command_line) if command_line else None

    volumes = []
    mounts = []

    azure_file_volume = _create_azure_file_volume(azure_file_volume_share_name=azure_file_volume_share_name,
                                                  azure_file_volume_account_name=azure_file_volume_account_name,
                                                  azure_file_volume_account_key=azure_file_volume_account_key)
    azure_file_volume_mount = _create_azure_file_volume_mount(azure_file_volume=azure_file_volume,
                                                              azure_file_volume_mount_path=azure_file_volume_mount_path)

    if azure_file_volume:
        volumes.append(azure_file_volume)
        mounts.append(azure_file_volume_mount)

    secrets_volume = _create_secrets_volume(secrets)
    secrets_volume_mount = _create_secrets_volume_mount(secrets_volume=secrets_volume,
                                                        secrets_mount_path=secrets_mount_path)

    if secrets_volume:
        volumes.append(secrets_volume)
        mounts.append(secrets_volume_mount)

    diagnostics = None
    tags = {}
    if log_analytics_workspace and log_analytics_workspace_key:
        log_analytics = LogAnalytics(
            workspace_id=log_analytics_workspace, workspace_key=log_analytics_workspace_key)

        diagnostics = ContainerGroupDiagnostics(
            log_analytics=log_analytics
        )
    elif log_analytics_workspace and not log_analytics_workspace_key:
        diagnostics, tags = _get_diagnostics_from_workspace(
            cmd.cli_ctx, log_analytics_workspace)
        if not diagnostics:
            raise CLIError('Log Analytics workspace "' + log_analytics_workspace + '" not found.')
    elif not log_analytics_workspace and log_analytics_workspace_key:
        raise CLIError('"--log-analytics-workspace-key" requires "--log-analytics-workspace".')

    gitrepo_volume = _create_gitrepo_volume(gitrepo_url=gitrepo_url, gitrepo_dir=gitrepo_dir, gitrepo_revision=gitrepo_revision)
    gitrepo_volume_mount = _create_gitrepo_volume_mount(gitrepo_volume=gitrepo_volume, gitrepo_mount_path=gitrepo_mount_path)

    if gitrepo_volume:
        volumes.append(gitrepo_volume)
        mounts.append(gitrepo_volume_mount)

    # Concatenate secure and standard environment variables
    if environment_variables and secure_environment_variables:
        environment_variables = environment_variables + secure_environment_variables
    else:
        environment_variables = environment_variables or secure_environment_variables

    identity = None
    if assign_identity is not None:
        identity = _build_identities_info(assign_identity)

    # Set up VNET and subnet if needed
    subnet_id = None
    cgroup_subnet = None
    if subnet:
        subnet_id = _get_subnet_id(cmd, location, resource_group_name, vnet, vnet_address_prefix, subnet, subnet_address_prefix)
        cgroup_subnet = [ContainerGroupSubnetId(id=subnet_id)]

    cgroup_ip_address = _create_ip_address(ip_address, ports, protocol, dns_name_label, subnet_id)

    # Setup zones, validation done in control plane so check is not needed here
    zones = None
    if zone:
        zones = [zone]

    container = Container(name=name,
                          image=image,
                          resources=container_resource_requirements,
                          command=command,
                          ports=[ContainerPort(
                              port=p, protocol=protocol) for p in ports] if cgroup_ip_address else None,
                          environment_variables=environment_variables,
                          volume_mounts=mounts or None)

    cgroup = ContainerGroup(location=location,
                            identity=identity,
                            containers=[container],
                            os_type=os_type,
                            restart_policy=restart_policy,
                            ip_address=cgroup_ip_address,
                            image_registry_credentials=image_registry_credentials,
                            volumes=volumes or None,
                            subnet_ids=cgroup_subnet,
                            diagnostics=diagnostics,
                            tags=tags,
                            zones=zones)

    container_group_client = cf_container_groups(cmd.cli_ctx)

    lro = sdk_no_wait(no_wait, container_group_client.begin_create_or_update, resource_group_name,
                      name, cgroup)

    if assign_identity is not None and identity_scope:
        from azure.cli.core.commands.arm import assign_identity
        cg = container_group_client.get(resource_group_name, name)
        assign_identity(cmd.cli_ctx, lambda: cg, lambda cg: cg, identity_role, identity_scope)

    return lro


def _build_identities_info(identities):
    identities = identities or []
    identity_type = ResourceIdentityType.none
    if not identities or MSI_LOCAL_ID in identities:
        identity_type = ResourceIdentityType.system_assigned
    external_identities = [x for x in identities if x != MSI_LOCAL_ID]
    if external_identities and identity_type == ResourceIdentityType.system_assigned:
        identity_type = ResourceIdentityType.system_assigned_user_assigned
    elif external_identities:
        identity_type = ResourceIdentityType.user_assigned
    identity = ContainerGroupIdentity(type=identity_type)
    if external_identities:
        identity.user_assigned_identities = {e: {} for e in external_identities}
    return identity


def _get_resource(client, resource_group_name, *subresources):
    from azure.core.exceptions import HttpResponseError
    try:
        resource = client.get(resource_group_name, *subresources)
        return resource
    except HttpResponseError as ex:
        if ex.error.code == "NotFound" or ex.error.code == "ResourceNotFound":
            return None
        raise


def _get_subnet_id(cmd, location, resource_group_name, vnet, vnet_address_prefix, subnet, subnet_address_prefix):
    from azure.cli.core.profiles import ResourceType
    from msrestazure.tools import parse_resource_id, is_valid_resource_id

    aci_delegation_service_name = "Microsoft.ContainerInstance/containerGroups"
    Delegation = cmd.get_models('Delegation', resource_type=ResourceType.MGMT_NETWORK)
    aci_delegation = Delegation(
        name=aci_delegation_service_name,
        service_name=aci_delegation_service_name
    )

    ncf = cf_network(cmd.cli_ctx)

    vnet_name = vnet
    subnet_name = subnet
    if is_valid_resource_id(subnet):
        parsed_subnet_id = parse_resource_id(subnet)
        subnet_name = parsed_subnet_id['resource_name']
        vnet_name = parsed_subnet_id['name']
        resource_group_name = parsed_subnet_id['resource_group']
    elif is_valid_resource_id(vnet):
        parsed_vnet_id = parse_resource_id(vnet)
        vnet_name = parsed_vnet_id['resource_name']
        resource_group_name = parsed_vnet_id['resource_group']

    subnet = _get_resource(ncf.subnets, resource_group_name, vnet_name, subnet_name)
    # For an existing subnet, validate and add delegation if needed
    if subnet:
        logger.info('Using existing subnet "%s" in resource group "%s"', subnet.name, resource_group_name)
        for sal in (subnet.service_association_links or []):
            if sal.linked_resource_type != aci_delegation_service_name:
                raise CLIError("Can not use subnet with existing service association links other than {}.".format(aci_delegation_service_name))

        if not subnet.delegations:
            logger.info('Adding ACI delegation to the existing subnet.')
            subnet.delegations = [aci_delegation]
            subnet = ncf.subnets.begin_create_or_update(resource_group_name, vnet_name, subnet_name, subnet).result()
        else:
            for delegation in subnet.delegations:
                if delegation.service_name != aci_delegation_service_name:
                    raise CLIError("Can not use subnet with existing delegations other than {}".format(aci_delegation_service_name))

    # Create new subnet and Vnet if not exists
    else:
        Subnet, VirtualNetwork, AddressSpace = cmd.get_models('Subnet', 'VirtualNetwork',
                                                              'AddressSpace', resource_type=ResourceType.MGMT_NETWORK)

        vnet = _get_resource(ncf.virtual_networks, resource_group_name, vnet_name)
        if not vnet:
            logger.info('Creating new vnet "%s" in resource group "%s"', vnet_name, resource_group_name)
            ncf.virtual_networks.begin_create_or_update(resource_group_name,
                                                        vnet_name,
                                                        VirtualNetwork(name=vnet_name,
                                                                       location=location,
                                                                       polling=False,
                                                                       address_space=AddressSpace(address_prefixes=[vnet_address_prefix])))
        subnet = Subnet(
            name=subnet_name,
            location=location,
            address_prefix=subnet_address_prefix,
            delegations=[aci_delegation])

        logger.info('Creating new subnet "%s" in resource group "%s"', subnet_name, resource_group_name)
        subnet = ncf.subnets.begin_create_or_update(resource_group_name, vnet_name, subnet_name, subnet).result()

    return subnet.id


def _get_diagnostics_from_workspace(cli_ctx, log_analytics_workspace):
    from msrestazure.tools import parse_resource_id
    log_analytics_workspace_client = cf_log_analytics_workspace(cli_ctx)
    log_analytics_workspace_shared_keys_client = cf_log_analytics_workspace_shared_keys(cli_ctx)

    for workspace in log_analytics_workspace_client.list():
        if log_analytics_workspace in (workspace.name, workspace.customer_id):
            keys = log_analytics_workspace_shared_keys_client.get_shared_keys(
                parse_resource_id(workspace.id)['resource_group'], workspace.name)

            log_analytics = LogAnalytics(
                workspace_id=workspace.customer_id, workspace_key=keys.primary_shared_key)

            diagnostics = ContainerGroupDiagnostics(
                log_analytics=log_analytics)

            return (diagnostics, {'oms-resource-link': workspace.id})

    return None, {}


# pylint: disable=unsupported-assignment-operation,protected-access
def _create_update_from_file(cli_ctx, resource_group_name, name, location, file, no_wait):
    resource_client = cf_resource(cli_ctx)
    container_group_client = cf_container_groups(cli_ctx)
    cg_defintion = None

    try:
        with open(file, 'r') as f:
            cg_defintion = yaml.safe_load(f)
    except OSError:  # FileNotFoundError introduced in Python 3
        raise CLIError("No such file or directory: " + file)
    except yaml.YAMLError as e:
        raise CLIError("Error while parsing yaml file:\n\n" + str(e))

    # Validate names match if both are provided
    if name and cg_defintion.get('name', None):
        if name != cg_defintion.get('name', None):
            raise CLIError("The name parameter and name from yaml definition must match.")
    else:
        # Validate at least one name is provided
        name = name or cg_defintion.get('name', None)
        if cg_defintion.get('name', None) is None and not name:
            raise CLIError("The name of the container group is required")

    cg_defintion['name'] = name

    if cg_defintion.get('location'):
        location = cg_defintion.get('location')
    cg_defintion['location'] = location

    api_version = cg_defintion.get('apiVersion', None) or container_group_client._config.api_version

    return sdk_no_wait(no_wait,
                       resource_client.resources.begin_create_or_update,
                       resource_group_name,
                       "Microsoft.ContainerInstance",
                       '',
                       "containerGroups",
                       name,
                       api_version,
                       cg_defintion)


# pylint: disable=inconsistent-return-statements
def _create_resource_requirements(cpu, memory):
    """Create resource requirements. """
    if cpu or memory:
        container_resource_requests = ResourceRequests(memory_in_gb=memory, cpu=cpu)
        return ResourceRequirements(requests=container_resource_requests)


def _create_image_registry_credentials(cmd, resource_group_name, registry_login_server, registry_username, registry_password, image, identity):
    from msrestazure.tools import is_valid_resource_id
    image_registry_credentials = None

    if identity:
        # Get full resource ID if only identity name is provided
        if not is_valid_resource_id(identity):
            msi_client = cf_msi(cmd.cli_ctx)
            identity = msi_client.user_assigned_identities.get(resource_group_name=resource_group_name,
                                                               resource_name=identity).id
        if registry_login_server:
            image_registry_credentials = [ImageRegistryCredential(server=registry_login_server,
                                                                  username=registry_username,
                                                                  password=registry_password,
                                                                  identity=identity)]
        elif ACR_SERVER_DELIMITER in image.split("/")[0]:
            acr_server = image.split("/")[0] if image.split("/") else None
            if acr_server:
                image_registry_credentials = [ImageRegistryCredential(server=acr_server,
                                                                      username=registry_username,
                                                                      password=registry_password,
                                                                      identity=identity)]
        else:
            raise RequiredArgumentMissingError('Failed to parse login server from image name; please explicitly specify --registry-server.')
        return image_registry_credentials

    if registry_login_server:
        if not registry_username:
            raise RequiredArgumentMissingError('Please specify --registry-username in order to use custom image registry.')
        if not registry_password:
            try:
                registry_password = prompt_pass(msg='Image registry password: ')
            except NoTTYException:
                raise RequiredArgumentMissingError('Please specify --registry-password in order to use custom image registry.')
        image_registry_credentials = [ImageRegistryCredential(server=registry_login_server,
                                                              username=registry_username,
                                                              password=registry_password)]
    elif ACR_SERVER_DELIMITER in image.split("/")[0]:
        if not registry_username:
            try:
                registry_username = prompt(msg='Image registry username: ')
            except NoTTYException:
                raise RequiredArgumentMissingError('Please specify --registry-username in order to use Azure Container Registry.')

        if not registry_password:
            try:
                registry_password = prompt_pass(msg='Image registry password: ')
            except NoTTYException:
                raise RequiredArgumentMissingError('Please specify --registry-password in order to use Azure Container Registry.')

        acr_server = image.split("/")[0] if image.split("/") else None
        if acr_server:
            image_registry_credentials = [ImageRegistryCredential(server=acr_server,
                                                                  username=registry_username,
                                                                  password=registry_password)]
    elif registry_username and registry_password and SERVER_DELIMITER in image.split("/")[0]:
        login_server = image.split("/")[0] if image.split("/") else None
        if login_server:
            image_registry_credentials = [ImageRegistryCredential(server=login_server,
                                                                  username=registry_username,
                                                                  password=registry_password)]
        else:
            raise RequiredArgumentMissingError('Failed to parse login server from image name; please explicitly specify --registry-server.')

    return image_registry_credentials


def _create_azure_file_volume(azure_file_volume_share_name, azure_file_volume_account_name, azure_file_volume_account_key):
    """Create Azure File volume. """
    azure_file_volume = None
    if azure_file_volume_share_name:
        if not azure_file_volume_account_name:
            raise CLIError('Please specify --azure-file-volume-account-name in order to use Azure File volume.')
        if not azure_file_volume_account_key:
            try:
                azure_file_volume_account_key = prompt_pass(msg='Azure File storage account key: ')
            except NoTTYException:
                raise CLIError('Please specify --azure-file-volume-account-key in order to use Azure File volume.')

        azure_file_volume = AzureFileVolume(share_name=azure_file_volume_share_name,
                                            storage_account_name=azure_file_volume_account_name,
                                            storage_account_key=azure_file_volume_account_key)

    return Volume(name=AZURE_FILE_VOLUME_NAME, azure_file=azure_file_volume) if azure_file_volume else None


def _create_secrets_volume(secrets):
    """Create secrets volume. """
    return Volume(name=SECRETS_VOLUME_NAME, secret=secrets) if secrets else None


def _create_gitrepo_volume(gitrepo_url, gitrepo_dir, gitrepo_revision):
    """Create Git Repo volume. """
    gitrepo_volume = GitRepoVolume(repository=gitrepo_url, directory=gitrepo_dir, revision=gitrepo_revision)

    return Volume(name=GITREPO_VOLUME_NAME, git_repo=gitrepo_volume) if gitrepo_url else None


# pylint: disable=inconsistent-return-statements
def _create_azure_file_volume_mount(azure_file_volume, azure_file_volume_mount_path):
    """Create Azure File volume mount. """
    if azure_file_volume_mount_path:
        if not azure_file_volume:
            raise CLIError('Please specify --azure-file-volume-share-name --azure-file-volume-account-name --azure-file-volume-account-key '
                           'to enable Azure File volume mount.')
        return VolumeMount(name=AZURE_FILE_VOLUME_NAME, mount_path=azure_file_volume_mount_path)


def _create_secrets_volume_mount(secrets_volume, secrets_mount_path):
    """Create secrets volume mount. """
    if secrets_volume:
        if not secrets_mount_path:
            raise CLIError('Please specify --secrets --secrets-mount-path '
                           'to enable secrets volume mount.')
        return VolumeMount(name=SECRETS_VOLUME_NAME, mount_path=secrets_mount_path)


def _create_gitrepo_volume_mount(gitrepo_volume, gitrepo_mount_path):
    """Create Git Repo volume mount. """
    if gitrepo_mount_path:
        if not gitrepo_volume:
            raise CLIError('Please specify --gitrepo-url (--gitrepo-dir --gitrepo-revision) '
                           'to enable Git Repo volume mount.')
        return VolumeMount(name=GITREPO_VOLUME_NAME, mount_path=gitrepo_mount_path)


# pylint: disable=inconsistent-return-statements
def _create_ip_address(ip_address, ports, protocol, dns_name_label, subnet_id):
    """Create IP address. """
    if (ip_address and ip_address.lower() == 'public') or dns_name_label:
        return IpAddress(ports=[Port(protocol=protocol, port=p) for p in ports],
                         dns_name_label=dns_name_label, type=ContainerGroupIpAddressType.public)
    if subnet_id:
        return IpAddress(ports=[Port(protocol=protocol, port=p) for p in ports],
                         type=ContainerGroupIpAddressType.private)


# pylint: disable=inconsistent-return-statements
def container_logs(cmd, resource_group_name, name, container_name=None, follow=False):
    """Tail a container instance log. """
    container_client = cf_container(cmd.cli_ctx)
    container_group_client = cf_container_groups(cmd.cli_ctx)
    container_group = container_group_client.get(resource_group_name, name)

    # If container name is not present, use the first container.
    if container_name is None:
        container_name = container_group.containers[0].name

    if not follow:
        log = container_client.list_logs(resource_group_name, name, container_name)
        print(log.content)
    else:
        _start_streaming(
            terminate_condition=_is_container_terminated,
            terminate_condition_args=(container_group_client, resource_group_name, name, container_name),
            shupdown_grace_period=5,
            stream_target=_stream_logs,
            stream_args=(container_client, resource_group_name, name, container_name, container_group.restart_policy))


# pylint: disable=protected-access
def container_export(cmd, resource_group_name, name, file):
    resource_client = cf_resource(cmd.cli_ctx)
    container_group_client = cf_container_groups(cmd.cli_ctx)
    resource = resource_client.resources.get(resource_group_name,
                                             "Microsoft.ContainerInstance",
                                             '',
                                             "containerGroups",
                                             name,
                                             container_group_client._config.api_version).__dict__

    # Remove unwanted properites
    resource['properties'].pop('instanceView', None)
    resource.pop('sku', None)
    resource.pop('id', None)
    resource.pop('plan', None)
    resource.pop('kind', None)
    resource.pop('managed_by', None)
    resource['properties'].pop('provisioningState', None)

    # Correctly export the identity
    try:
        identity = resource['identity'].type
        if identity != ResourceIdentityType.none:
            resource['identity'] = resource['identity'].__dict__
            identity_entry = {'type': resource['identity']['type'].value}
            if resource['identity']['user_assigned_identities']:
                identity_entry['user_assigned_identities'] = {k: {} for k in resource['identity']['user_assigned_identities']}
            resource['identity'] = identity_entry
    except (KeyError, AttributeError):
        resource.pop('indentity', None)

    # Remove container instance views
    for i in range(len(resource['properties']['containers'])):
        resource['properties']['containers'][i]['properties'].pop('instanceView', None)

    # Add the api version
    resource['apiVersion'] = container_group_client._config.api_version

    with open(file, 'w+') as f:
        yaml.safe_dump(resource, f, default_flow_style=False)


def container_exec(cmd, resource_group_name, name, exec_command, container_name=None):
    """Start exec for a container. """

    container_client = cf_container(cmd.cli_ctx)
    container_group_client = cf_container_groups(cmd.cli_ctx)
    container_group = container_group_client.get(resource_group_name, name)

    if container_name or container_name is None and len(container_group.containers) == 1:
        # If only one container in container group, use that container.
        if container_name is None:
            container_name = container_group.containers[0].name

        try:
            terminalsize = os.get_terminal_size()
        except OSError:
            terminalsize = os.terminal_size((80, 24))
        terminal_size = ContainerExecRequestTerminalSize(rows=terminalsize.lines, cols=terminalsize.columns)
        exec_request = ContainerExecRequest(command=exec_command, terminal_size=terminal_size)

        execContainerResponse = container_client.execute_command(resource_group_name, name, container_name, exec_request)

        if platform.system() is WINDOWS_NAME:
            _start_exec_pipe_windows(execContainerResponse.web_socket_uri, execContainerResponse.password)
        else:
            _start_exec_pipe_linux(execContainerResponse.web_socket_uri, execContainerResponse.password)

    else:
        raise CLIError('--container-name required when container group has more than one container.')


def _start_exec_pipe_windows(web_socket_uri, password):
    import colorama
    colorama.deinit()
    enable_vt_mode()
    buff = bytearray()
    lock = threading.Lock()

    def _on_ws_open_windows(ws):
        ws.send(password)
        readKeyboard = threading.Thread(target=_capture_stdin, args=[_getch_windows, buff, lock], daemon=True)
        readKeyboard.start()
        flushKeyboard = threading.Thread(target=_flush_stdin, args=[ws, buff, lock], daemon=True)
        flushKeyboard.start()
    ws = websocket.WebSocketApp(web_socket_uri, on_open=_on_ws_open_windows, on_message=_on_ws_msg)
    # in windows, msvcrt.getch doesn't give us ctrl+C so we have to manually catch it with kb interrupt and send it over the socket
    websocketRun = threading.Thread(target=ws.run_forever)
    websocketRun.start()
    while websocketRun.is_alive():
        try:
            time.sleep(0.01)
        except KeyboardInterrupt:
            try:
                ws.send(b'\x03')  # CTRL-C character (ETX character)
            finally:
                pass
    colorama.reinit()


def _start_exec_pipe_linux(web_socket_uri, password):
    stdin_fd = sys.stdin.fileno()
    old_tty = termios.tcgetattr(stdin_fd)
    old_winch_handler = signal.getsignal(signal.SIGWINCH)
    tty.setraw(stdin_fd)
    tty.setcbreak(stdin_fd)
    buff = bytearray()
    lock = threading.Lock()

    def _on_ws_open_linux(ws):
        ws.send(password)
        readKeyboard = threading.Thread(target=_capture_stdin, args=[_getch_linux, buff, lock], daemon=True)
        readKeyboard.start()
        flushKeyboard = threading.Thread(target=_flush_stdin, args=[ws, buff, lock], daemon=True)
        flushKeyboard.start()
    ws = websocket.WebSocketApp(web_socket_uri, on_open=_on_ws_open_linux, on_message=_on_ws_msg)
    ws.run_forever()
    termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_tty)
    signal.signal(signal.SIGWINCH, old_winch_handler)


def _on_ws_msg(ws, msg):
    if isinstance(msg, str):
        msg = msg.encode()
    sys.stdout.buffer.write(msg)
    sys.stdout.flush()


def _capture_stdin(getch_func, buff, lock):
    # this method will fill up the buffer from one thread (using the lock)
    while True:
        try:
            x = getch_func()
            lock.acquire()
            buff.extend(x)
            lock.release()
        finally:
            if lock.locked():
                lock.release()


def _flush_stdin(ws, buff, lock):
    # this method will flush the buffer out to the websocket (using the lock)
    while True:
        time.sleep(0.01)
        try:
            if not buff:
                continue
            lock.acquire()
            x = bytes(buff)
            buff.clear()
            lock.release()
            ws.send(x, opcode=0x2)  # OPCODE_BINARY = 0x2
        except (OSError, IOError, websocket.WebSocketConnectionClosedException) as e:
            if isinstance(e, websocket.WebSocketConnectionClosedException):
                pass
            elif e.errno == 9:  # [Errno 9] Bad file descriptor
                pass
            elif e.args and e.args[0] == errno.EINTR:
                pass
            else:
                raise
        finally:
            if lock.locked():
                lock.release()


def _getch_windows():
    while not msvcrt.kbhit():
        time.sleep(0.01)
    return msvcrt.getch()


def _getch_linux():
    ch = sys.stdin.read(1)
    return ch.encode()


def attach_to_container(cmd, resource_group_name, name, container_name=None):
    """Attach to a container. """
    container_client = cf_container(cmd.cli_ctx)
    container_group_client = cf_container_groups(cmd.cli_ctx)
    container_group = container_group_client.get(resource_group_name, name)

    # If container name is not present, use the first container.
    if container_name is None:
        container_name = container_group.containers[0].name

    _start_streaming(
        terminate_condition=_is_container_terminated,
        terminate_condition_args=(container_group_client, resource_group_name, name, container_name),
        shupdown_grace_period=5,
        stream_target=_stream_container_events_and_logs,
        stream_args=(container_group_client, container_client, resource_group_name, name, container_name))


def _start_streaming(terminate_condition, terminate_condition_args, shupdown_grace_period, stream_target, stream_args):
    """Start streaming for the stream target. """
    import colorama
    colorama.init()

    try:
        t = threading.Thread(target=stream_target, args=stream_args)
        t.daemon = True
        t.start()

        while not terminate_condition(*terminate_condition_args) and t.is_alive():
            time.sleep(10)

        time.sleep(shupdown_grace_period)

    finally:
        colorama.deinit()


def _stream_logs(client, resource_group_name, name, container_name, restart_policy):
    """Stream logs for a container. """
    lastOutputLines = 0
    while True:
        log = client.list_logs(resource_group_name, name, container_name)
        lines = log.content.split('\n')
        currentOutputLines = len(lines)

        # Should only happen when the container restarts.
        if currentOutputLines < lastOutputLines and restart_policy != 'Never':
            print("Warning: you're having '--restart-policy={}'; the container '{}' was just restarted; the tail of the current log might be missing. Exiting...".format(restart_policy, container_name))
            break

        _move_console_cursor_up(lastOutputLines)
        print(log.content)

        lastOutputLines = currentOutputLines
        time.sleep(2)


def _stream_container_events_and_logs(container_group_client, container_client, resource_group_name, name, container_name):
    """Stream container events and logs. """
    lastOutputLines = 0
    lastContainerState = None

    while True:
        container_group, container = _find_container(container_group_client, resource_group_name, name, container_name)

        container_state = 'Unknown'
        if container.instance_view and container.instance_view.current_state and container.instance_view.current_state.state:
            container_state = container.instance_view.current_state.state

        _move_console_cursor_up(lastOutputLines)
        if container_state != lastContainerState:
            print("Container '{}' is in state '{}'...".format(container_name, container_state))

        currentOutputLines = 0
        if container.instance_view and container.instance_view.events:
            for event in sorted(container.instance_view.events, key=lambda e: e.last_timestamp):
                print('(count: {}) (last timestamp: {}) {}'.format(event.count, event.last_timestamp, event.message))
                currentOutputLines += 1

        lastOutputLines = currentOutputLines
        lastContainerState = container_state

        if container_state == 'Running':
            print('\nStart streaming logs:')
            break

        time.sleep(2)

    _stream_logs(container_client, resource_group_name, name, container_name, container_group.restart_policy)


def _is_container_terminated(client, resource_group_name, name, container_name):
    """Check if a container should be considered terminated. """
    container_group, container = _find_container(client, resource_group_name, name, container_name)

    # If a container group is terminated, assume the container is also terminated.
    if container_group.instance_view and container_group.instance_view.state:
        if container_group.instance_view.state == 'Succeeded' or container_group.instance_view.state == 'Failed':
            return True

    # If the restart policy is Always, assume the container will be restarted.
    if container_group.restart_policy:
        if container_group.restart_policy == 'Always':
            return False

    # Only assume the container is terminated if its state is Terminated.
    if container.instance_view and container.instance_view.current_state and container.instance_view.current_state.state == 'Terminated':
        return True

    return False


def _find_container(client, resource_group_name, name, container_name):
    """Find a container in a container group. """
    container_group = client.get(resource_group_name, name)
    containers = [c for c in container_group.containers if c.name == container_name]

    if len(containers) != 1:
        raise CLIError("Found 0 or more than 1 container with name '{}'".format(container_name))

    return container_group, containers[0]


def _move_console_cursor_up(lines):
    """Move console cursor up. """
    if lines > 0:
        # Use stdout.write to support Python 2
        sys.stdout.write('\033[{}A\033[K\033[J'.format(lines))


def _gen_guid():
    import uuid
    return uuid.uuid4()
