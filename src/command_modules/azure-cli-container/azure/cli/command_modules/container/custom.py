# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods,too-many-arguments,no-self-use,too-many-locals,line-too-long,unused-argument

import shlex
import threading
import time
import sys
from knack.prompting import prompt_pass, NoTTYException
from knack.util import CLIError
from azure.mgmt.containerinstance.models import (AzureFileVolume, Container, ContainerGroup, ContainerGroupNetworkProtocol,
                                                 ContainerPort, ImageRegistryCredential, IpAddress, Port, ResourceRequests,
                                                 ResourceRequirements, Volume, VolumeMount)
from ._client_factory import cf_container_groups, cf_container_logs


ACR_SERVER_SUFFIX = '.azurecr.io/'
AZURE_FILE_VOLUME_NAME = 'azurefile'


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
    return client.delete(resource_group_name, name)


def create_container(client,
                     resource_group_name,
                     name,
                     image,
                     location=None,
                     cpu=1,
                     memory=1.5,
                     restart_policy='Always',
                     ports=None,
                     os_type='Linux',
                     ip_address=None,
                     dns_name_label=None,
                     command_line=None,
                     environment_variables=None,
                     registry_login_server=None,
                     registry_username=None,
                     registry_password=None,
                     azure_file_volume_share_name=None,
                     azure_file_volume_account_name=None,
                     azure_file_volume_account_key=None,
                     azure_file_volume_mount_path=None):
    """Create a container group. """

    ports = ports or [80]

    container_resource_requirements = _create_resource_requirements(cpu=cpu, memory=memory)

    image_registry_credentials = _create_image_registry_credentials(registry_login_server=registry_login_server,
                                                                    registry_username=registry_username,
                                                                    registry_password=registry_password,
                                                                    image=image)

    command = shlex.split(command_line) if command_line else None

    azure_file_volume = _create_azure_file_volume(azure_file_volume_share_name=azure_file_volume_share_name,
                                                  azure_file_volume_account_name=azure_file_volume_account_name,
                                                  azure_file_volume_account_key=azure_file_volume_account_key)

    azure_file_volume_mount = _create_azure_file_volume_mount(azure_file_volume=azure_file_volume,
                                                              azure_file_volume_mount_path=azure_file_volume_mount_path)

    cgroup_ip_address = _create_ip_address(ip_address, ports, dns_name_label)

    container = Container(name=name,
                          image=image,
                          resources=container_resource_requirements,
                          command=command,
                          ports=[ContainerPort(port=p) for p in ports] if cgroup_ip_address else None,
                          environment_variables=environment_variables,
                          volume_mounts=azure_file_volume_mount)

    cgroup = ContainerGroup(location=location,
                            containers=[container],
                            os_type=os_type,
                            restart_policy=restart_policy,
                            ip_address=cgroup_ip_address,
                            image_registry_credentials=image_registry_credentials,
                            volumes=azure_file_volume)

    return client.create_or_update(resource_group_name, name, cgroup)


# pylint: disable=inconsistent-return-statements
def _create_resource_requirements(cpu, memory):
    """Create resource requirements. """
    if cpu or memory:
        container_resource_requests = ResourceRequests(memory_in_gb=memory, cpu=cpu)
        return ResourceRequirements(requests=container_resource_requests)


def _create_image_registry_credentials(registry_login_server, registry_username, registry_password, image):
    """Create image registry credentials. """
    image_registry_credentials = None
    if registry_login_server:
        if not registry_username:
            raise CLIError('Please specify --registry-username in order to use custom image registry.')
        if not registry_password:
            try:
                registry_password = prompt_pass(msg='Image registry password: ')
            except NoTTYException:
                raise CLIError('Please specify --registry-password in order to use custom image registry.')
        image_registry_credentials = [ImageRegistryCredential(server=registry_login_server,
                                                              username=registry_username,
                                                              password=registry_password)]
    elif ACR_SERVER_SUFFIX in image:
        if not registry_password:
            try:
                registry_password = prompt_pass(msg='Image registry password: ')
            except NoTTYException:
                raise CLIError('Please specify --registry-password in order to use Azure Container Registry.')

        acr_server = image.split("/")[0] if image.split("/") else None
        acr_username = image.split(ACR_SERVER_SUFFIX)[0] if image.split(ACR_SERVER_SUFFIX) else None
        if acr_server and acr_username:
            image_registry_credentials = [ImageRegistryCredential(server=acr_server,
                                                                  username=acr_username,
                                                                  password=registry_password)]
        else:
            raise CLIError('Failed to parse ACR server or username from image name; please explicitly specify --registry-server and --registry-username.')

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

    return [Volume(name=AZURE_FILE_VOLUME_NAME, azure_file=azure_file_volume)] if azure_file_volume else None


# pylint: disable=inconsistent-return-statements
def _create_azure_file_volume_mount(azure_file_volume, azure_file_volume_mount_path):
    """Create Azure File volume mount. """
    if azure_file_volume_mount_path:
        if not azure_file_volume:
            raise CLIError('Please specify --azure-file-volume-share-name --azure-file-volume-account-name --azure-file-volume-account-key '
                           'to enable Azure File volume mount.')
        return [VolumeMount(name=AZURE_FILE_VOLUME_NAME, mount_path=azure_file_volume_mount_path)]


# pylint: disable=inconsistent-return-statements
def _create_ip_address(ip_address, ports, dns_name_label):
    """Create IP address. """
    if (ip_address and ip_address.lower() == 'public') or dns_name_label:
        return IpAddress(ports=[Port(protocol=ContainerGroupNetworkProtocol.tcp, port=p) for p in ports], dns_name_label=dns_name_label)


# pylint: disable=inconsistent-return-statements
def container_logs(cmd, resource_group_name, name, container_name=None, follow=False):
    """Tail a container instance log. """
    logs_client = cf_container_logs(cmd.cli_ctx)
    container_group_client = cf_container_groups(cmd.cli_ctx)
    container_group = container_group_client.get(resource_group_name, name)

    # If container name is not present, use the first container.
    if container_name is None:
        container_name = container_group.containers[0].name

    if not follow:
        log = logs_client.list(resource_group_name, name, container_name)
        print(log.content)
    else:
        _start_streaming(
            terminate_condition=_is_container_terminated,
            terminate_condition_args=(container_group_client, resource_group_name, name, container_name),
            shupdown_grace_period=5,
            stream_target=_stream_logs,
            stream_args=(logs_client, resource_group_name, name, container_name, container_group.restart_policy))


def attach_to_container(cmd, resource_group_name, name, container_name=None):
    """Attach to a container. """
    logs_client = cf_container_logs(cmd.cli_ctx)
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
        stream_args=(container_group_client, logs_client, resource_group_name, name, container_name))


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
        log = client.list(resource_group_name, name, container_name)
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


def _stream_container_events_and_logs(container_group_client, logs_client, resource_group_name, name, container_name):
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

    _stream_logs(logs_client, resource_group_name, name, container_name, container_group.restart_policy)


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
