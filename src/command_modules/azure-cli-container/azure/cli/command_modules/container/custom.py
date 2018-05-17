# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods,too-many-arguments,no-self-use,too-many-locals,line-too-long,unused-argument

import errno
try:
    import msvcrt
except ImportError:
    # Not supported for Linux machines.
    pass
import platform
import select
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
                                                 ResourceRequirements, Volume, VolumeMount, ContainerExecRequestTerminalSize,
                                                 GitRepoVolume)
from azure.cli.command_modules.resource._client_factory import _resource_client_factory
from ._client_factory import cf_container_groups, cf_container_logs, cf_start_container

logger = get_logger(__name__)
WINDOWS_NAME = 'Windows'
SERVER_DELIMITER = '.'
AZURE_FILE_VOLUME_NAME = 'azurefile'
SECRETS_VOLUME_NAME = 'secrets'
GITREPO_VOLUME_NAME = 'gitrepo'


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


def create_container(cmd,
                     resource_group_name,
                     name=None,
                     image=None,
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
                     azure_file_volume_mount_path=None,
                     gitrepo_url=None,
                     gitrepo_dir='.',
                     gitrepo_revision=None,
                     gitrepo_mount_path=None,
                     secrets=None,
                     secrets_mount_path=None,
                     file=None):
    """Create a container group. """

    if file:
        return _create_update_from_file(cmd.cli_ctx, resource_group_name, name, location, file)

    if not name:
        raise CLIError("error: the --name/-n argument is required unless specified with a passed in file.")

    if not image:
        raise CLIError("error: the --image argument is required unless specified with a passed in file.")

    ports = ports or [80]

    container_resource_requirements = _create_resource_requirements(cpu=cpu, memory=memory)

    image_registry_credentials = _create_image_registry_credentials(registry_login_server=registry_login_server,
                                                                    registry_username=registry_username,
                                                                    registry_password=registry_password,
                                                                    image=image)

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

    gitrepo_volume = _create_gitrepo_volume(gitrepo_url=gitrepo_url, gitrepo_dir=gitrepo_dir, gitrepo_revision=gitrepo_revision)
    gitrepo_volume_mount = _create_gitrepo_volume_mount(gitrepo_volume=gitrepo_volume, gitrepo_mount_path=gitrepo_mount_path)

    if gitrepo_volume:
        volumes.append(gitrepo_volume)
        mounts.append(gitrepo_volume_mount)

    cgroup_ip_address = _create_ip_address(ip_address, ports, dns_name_label)

    container = Container(name=name,
                          image=image,
                          resources=container_resource_requirements,
                          command=command,
                          ports=[ContainerPort(port=p) for p in ports] if cgroup_ip_address else None,
                          environment_variables=environment_variables,
                          volume_mounts=mounts or None)

    cgroup = ContainerGroup(location=location,
                            containers=[container],
                            os_type=os_type,
                            restart_policy=restart_policy,
                            ip_address=cgroup_ip_address,
                            image_registry_credentials=image_registry_credentials,
                            volumes=volumes or None)

    container_group_client = cf_container_groups(cmd.cli_ctx)
    raw_response = container_group_client.create_or_update(resource_group_name, name, cgroup, raw=True)
    return raw_response.output


def _create_update_from_file(cli_ctx, resource_group_name, name, location, file):
    resource_client = _resource_client_factory(cli_ctx)
    container_group_client = cf_container_groups(cli_ctx)

    cg_defintion = None

    try:
        with open(file, 'r') as f:
            cg_defintion = yaml.load(f)
    except FileNotFoundError:
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

    location = location or cg_defintion.get('location', None)
    if not location:
        location = resource_client.resource_groups.get(resource_group_name).location
    cg_defintion['location'] = location

    api_version = cg_defintion.get('apiVersion', None) or container_group_client.api_version

    resource = resource_client.resources.create_or_update(resource_group_name,
                                                          "Microsoft.ContainerInstance",
                                                          '',
                                                          "containerGroups",
                                                          name,
                                                          api_version,
                                                          cg_defintion,
                                                          raw=True)
    return resource.output


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
    elif SERVER_DELIMITER in image.split("/")[0]:
        if not registry_username:
            try:
                registry_username = prompt(msg='Image registry username: ')
            except NoTTYException:
                raise CLIError('Please specify --registry-username in order to use Azure Container Registry.')

        if not registry_password:
            try:
                registry_password = prompt_pass(msg='Image registry password: ')
            except NoTTYException:
                raise CLIError('Please specify --registry-password in order to use Azure Container Registry.')

        acr_server = image.split("/")[0] if image.split("/") else None
        if acr_server:
            image_registry_credentials = [ImageRegistryCredential(server=acr_server,
                                                                  username=registry_username,
                                                                  password=registry_password)]
        else:
            raise CLIError('Failed to parse ACR server from image name; please explicitly specify --registry-server.')

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


def container_export(cmd, resource_group_name, name, file):
    resource_client = _resource_client_factory(cmd.cli_ctx)
    container_group_client = cf_container_groups(cmd.cli_ctx)

    resource = resource_client.resources.get(resource_group_name,
                                             "Microsoft.ContainerInstance",
                                             '',
                                             "containerGroups",
                                             name,
                                             container_group_client.api_version,
                                             False).__dict__

    # Remove unwanted properites
    resource['properties'].pop('instanceView', None)
    resource.pop('sku', None)
    resource.pop('id', None)
    resource.pop('plan', None)
    resource.pop('identity', None)
    resource.pop('kind', None)
    resource.pop('managed_by', None)
    resource['properties'].pop('provisioningState', None)

    for i in range(len(resource['properties']['containers'])):
        resource['properties']['containers'][i]['properties'].pop('instanceView', None)

    # Add the api version
    resource['apiVersion'] = container_group_client.api_version

    with open(file, 'w+') as f:
        yaml.dump(resource, f, default_flow_style=False)


def container_exec(cmd, resource_group_name, name, exec_command, container_name=None, terminal_row_size=20, terminal_col_size=80):
    """Start exec for a container. """

    start_container_client = cf_start_container(cmd.cli_ctx)
    container_group_client = cf_container_groups(cmd.cli_ctx)
    container_group = container_group_client.get(resource_group_name, name)

    if container_name or container_name is None and len(container_group.containers) == 1:
        # If only one container in container group, use that container.
        if container_name is None:
            container_name = container_group.containers[0].name

        terminal_size = ContainerExecRequestTerminalSize(rows=terminal_row_size, cols=terminal_col_size)

        execContainerResponse = start_container_client.launch_exec(resource_group_name, name, container_name, exec_command, terminal_size)

        if platform.system() is WINDOWS_NAME:
            _start_exec_pipe_win(execContainerResponse.web_socket_uri, execContainerResponse.password)
        else:
            _start_exec_pipe(execContainerResponse.web_socket_uri, execContainerResponse.password)

    else:
        raise CLIError('--container-name required when container group has more than one container.')


def _start_exec_pipe_win(web_socket_uri, password):

    def _on_ws_open(ws):
        ws.send(password)
        t = threading.Thread(target=_capture_stdin, args=[ws])
        t.daemon = True
        t.start()

    ws = websocket.WebSocketApp(web_socket_uri, on_open=_on_ws_open, on_message=_on_ws_msg)

    ws.run_forever()


def _on_ws_msg(ws, msg):
    sys.stdout.write(msg)
    sys.stdout.flush()


def _capture_stdin(ws):
    while True:
        if msvcrt.kbhit:
            x = msvcrt.getch()
            ws.send(x)


def _start_exec_pipe(web_socket_uri, password):
    ws = websocket.create_connection(web_socket_uri)

    oldtty = termios.tcgetattr(sys.stdin)
    old_handler = signal.getsignal(signal.SIGWINCH)

    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        ws.send(password)
        while True:
            try:
                if not _cycle_exec_pipe(ws):
                    break
            except (select.error, IOError) as e:
                if e.args and e.args[0] == errno.EINTR:
                    pass
                else:
                    raise
    except websocket.WebSocketException:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
        signal.signal(signal.SIGWINCH, old_handler)


def _cycle_exec_pipe(ws):
    r, _, _ = select.select([ws.sock, sys.stdin], [], [])
    if ws.sock in r:
        data = ws.recv()
        if not data:
            return False
        sys.stdout.write(data)
        sys.stdout.flush()
    if sys.stdin in r:
        x = sys.stdin.read(1)
        if not x:
            return True
        ws.send(x)
    return True


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
