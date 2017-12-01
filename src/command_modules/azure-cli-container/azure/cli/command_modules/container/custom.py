# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods,too-many-arguments,no-self-use,too-many-locals,line-too-long,unused-argument

import shlex
from azure.cli.core.prompting import prompt_pass, NoTTYException
from azure.cli.core.util import CLIError
from azure.mgmt.containerinstance.models import (ContainerGroup, Container, ContainerPort, Port, IpAddress,
                                                 ImageRegistryCredential, ResourceRequirements, ResourceRequests,
                                                 ContainerGroupNetworkProtocol, Volume, AzureFileVolume, VolumeMount)


ACR_SERVER_SUFFIX = '.azurecr.io/'
AZURE_FILE_VOLUME_NAME = 'azurefile'


def list_containers(client, resource_group_name=None):
    """List all container groups in a resource group. """
    if resource_group_name is None:
        return client.container_groups.list()
    return client.container_groups.list_by_resource_group(resource_group_name)


def get_container(client, resource_group_name, name):
    """Show details of a container group. """
    return client.container_groups.get(resource_group_name, name)


def delete_container(client, resource_group_name, name, **kwargs):
    """Delete a container group. """
    return client.container_groups.delete(resource_group_name, name)


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

    ports = ports or []

    container_resource_requirements = create_resource_requirements(cpu=cpu, memory=memory)

    image_registry_credentials = create_image_registry_credentials(registry_login_server=registry_login_server,
                                                                   registry_username=registry_username,
                                                                   registry_password=registry_password,
                                                                   image=image)

    command = shlex.split(command_line) if command_line else None

    azure_file_volume = create_azure_file_volume(azure_file_volume_share_name=azure_file_volume_share_name,
                                                 azure_file_volume_account_name=azure_file_volume_account_name,
                                                 azure_file_volume_account_key=azure_file_volume_account_key)

    azure_file_volume_mount = create_azure_file_volume_mount(azure_file_volume=azure_file_volume,
                                                             azure_file_volume_mount_path=azure_file_volume_mount_path)

    container = Container(name=name,
                          image=image,
                          resources=container_resource_requirements,
                          command=command,
                          ports=[ContainerPort(port=p) for p in ports],
                          environment_variables=environment_variables,
                          volume_mounts=azure_file_volume_mount)

    cgroup_ip_address = create_ip_address(ip_address, ports)

    cgroup = ContainerGroup(location=location,
                            containers=[container],
                            os_type=os_type,
                            restart_policy=restart_policy,
                            ip_address=cgroup_ip_address,
                            image_registry_credentials=image_registry_credentials,
                            volumes=azure_file_volume)

    return client.container_groups.create_or_update(resource_group_name, name, cgroup)


def create_resource_requirements(cpu, memory):
    """Create resource requirements. """
    if cpu or memory:
        container_resource_requests = ResourceRequests(memory_in_gb=memory, cpu=cpu)
        return ResourceRequirements(requests=container_resource_requests)


def create_image_registry_credentials(registry_login_server, registry_username, registry_password, image):
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


def create_azure_file_volume(azure_file_volume_share_name, azure_file_volume_account_name, azure_file_volume_account_key):
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


def create_azure_file_volume_mount(azure_file_volume, azure_file_volume_mount_path):
    """Create Azure File volume mount. """
    if azure_file_volume_mount_path:
        if not azure_file_volume:
            raise CLIError('Please specify --azure-file-volume-share-name --azure-file-volume-account-name --azure-file-volume-account-key '
                           'to enable Azure File volume mount.')
        return [VolumeMount(name=AZURE_FILE_VOLUME_NAME, mount_path=azure_file_volume_mount_path)]


def create_ip_address(ip_address, ports):
    """Create IP address. """
    if ip_address and ip_address.lower() == 'public':
        return IpAddress(ports=[Port(protocol=ContainerGroupNetworkProtocol.tcp, port=p) for p in ports])


def container_logs(client, resource_group_name, name, container_name=None):
    """Tail a container instance log. """
    if container_name is None:
        container_name = name
    log = client.container_logs.list(resource_group_name, container_name, name)
    return log.content
