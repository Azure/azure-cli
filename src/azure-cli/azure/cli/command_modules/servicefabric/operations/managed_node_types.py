# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long,too-many-lines

from azure.cli.core.commands import LongRunningOperation
from azure.core.exceptions import HttpResponseError
from azure.mgmt.servicefabricmanagedclusters.models import (
    NodeType,
    EndpointRangeDescription,
    VMSSExtension,
    VaultSecretGroup,
    VaultCertificate,
    SubResource,
    NodeTypeActionParameters
)

from knack.log import get_logger

logger = get_logger(__name__)


# pylint:disable=too-many-locals,
def create_node_type(cmd,
                     client,
                     resource_group_name,
                     cluster_name,
                     node_type_name,
                     instance_count,
                     primary=False,
                     disk_size=None,
                     disk_type=None,
                     application_start_port=None,
                     application_end_port=None,
                     ephemeral_start_port=None,
                     ephemeral_end_port=None,
                     vm_size=None,
                     vm_image_publisher=None,
                     vm_image_offer=None,
                     vm_image_sku=None,
                     vm_image_version=None,
                     capacity=None,
                     placement_property=None,
                     is_stateless=False,
                     multiple_placement_groups=False,
                     tags=None):

    #  set defult parameters
    if disk_size is None:
        disk_size = 100

    if vm_size is None:
        vm_size = "Standard_D2"

    if vm_image_publisher is None:
        vm_image_publisher = "MicrosoftWindowsServer"

    if vm_image_offer is None:
        vm_image_offer = "WindowsServer"

    if vm_image_sku is None:
        vm_image_sku = "2019-Datacenter"

    if vm_image_version is None:
        vm_image_version = "latest"

    try:
        new_node_type = NodeType(is_primary=primary,
                                 vm_instance_count=int(instance_count),
                                 data_disk_size_gb=disk_size,
                                 data_disk_type=disk_type,
                                 vm_size=vm_size,
                                 vm_image_publisher=vm_image_publisher,
                                 vm_image_offer=vm_image_offer,
                                 vm_image_sku=vm_image_sku,
                                 vm_image_version=vm_image_version,
                                 capacities=capacity,
                                 placement_properties=placement_property,
                                 is_stateless=is_stateless,
                                 multiple_placement_groups=multiple_placement_groups,
                                 tags=tags)

        if application_start_port and application_end_port:
            new_node_type.application_ports = EndpointRangeDescription(start_port=application_start_port,
                                                                       end_port=application_end_port)

        if ephemeral_start_port and ephemeral_end_port:
            new_node_type.ephemeral_ports = EndpointRangeDescription(start_port=ephemeral_start_port,
                                                                     end_port=ephemeral_end_port)

        logger.info("Creating node type '%s'", node_type_name)
        poller = client.node_types.begin_create_or_update(resource_group_name, cluster_name, node_type_name, new_node_type)
        node_type = LongRunningOperation(cmd.cli_ctx)(poller)
        return node_type
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def update_node_type(cmd,
                     client,
                     resource_group_name,
                     cluster_name,
                     node_type_name,
                     instance_count=None,
                     vm_size=None,
                     application_start_port=None,
                     application_end_port=None,
                     ephemeral_start_port=None,
                     ephemeral_end_port=None,
                     capacity=None,
                     placement_property=None,
                     tags=None):
    try:
        node_type = client.node_types.get(resource_group_name, cluster_name, node_type_name)

        if instance_count is not None:
            node_type.vm_instance_count = instance_count

        if application_start_port and application_end_port:
            node_type.application_ports = EndpointRangeDescription(start_port=application_start_port,
                                                                   end_port=application_end_port)

        if ephemeral_start_port and ephemeral_end_port:
            node_type.ephemeral_ports = EndpointRangeDescription(start_port=ephemeral_start_port,
                                                                 end_port=ephemeral_end_port)

        if capacity is not None:
            node_type.capacities = capacity

        if placement_property is not None:
            node_type.placement_properties = placement_property

        if vm_size is not None:
            node_type.vm_size = vm_size

        if tags is not None:
            node_type.tags = tags

        poller = client.node_types.begin_create_or_update(resource_group_name, cluster_name, node_type_name, node_type)
        return LongRunningOperation(cmd.cli_ctx)(poller)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def reimage_node(cmd,
                 client,
                 resource_group_name,
                 cluster_name,
                 node_type_name,
                 node_name,
                 force=False):
    try:
        nodes = [node_name] if isinstance(node_name, str) else node_name
        action_parameters = NodeTypeActionParameters(nodes=nodes, force=force)
        poller = client.node_types.begin_reimage(resource_group_name, cluster_name, node_type_name, parameters=action_parameters)
        LongRunningOperation(cmd.cli_ctx, start_msg='Reimaging nodes', finish_msg='Nodes reimaged')(poller)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def restart_node(cmd,
                 client,
                 resource_group_name,
                 cluster_name,
                 node_type_name,
                 node_name,
                 force=False):
    try:
        nodes = [node_name] if isinstance(node_name, str) else node_name
        action_parameters = NodeTypeActionParameters(nodes=nodes, force=force)
        poller = client.node_types.begin_restart(resource_group_name, cluster_name, node_type_name, parameters=action_parameters)
        LongRunningOperation(cmd.cli_ctx, start_msg='Restarting nodes', finish_msg='Nodes restarted')(poller)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def delete_node(cmd,
                client,
                resource_group_name,
                cluster_name,
                node_type_name,
                node_name,
                force=False):
    try:
        nodes = [node_name] if isinstance(node_name, str) else node_name
        action_parameters = NodeTypeActionParameters(nodes=nodes, force=force)
        poller = client.node_types.begin_delete_node(resource_group_name, cluster_name, node_type_name, parameters=action_parameters)
        LongRunningOperation(cmd.cli_ctx, start_msg='Deleting nodes', finish_msg='Nodes deleted')(poller)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def add_vm_extension(cmd,
                     client,
                     resource_group_name,
                     cluster_name,
                     node_type_name,
                     extension_name,
                     publisher,
                     extension_type,
                     type_handler_version,
                     force_update_tag=None,
                     auto_upgrade_minor_version=True,
                     setting=None,
                     protected_setting=None,
                     provision_after_extension=None):
    try:
        node_type: NodeType = client.node_types.get(resource_group_name, cluster_name, node_type_name)

        if node_type.vm_extensions is None:
            node_type.vm_extensions = []

        newExtension = VMSSExtension(name=extension_name,
                                     publisher=publisher,
                                     type=extension_type,
                                     type_handler_version=type_handler_version,
                                     force_update_tag=force_update_tag,
                                     auto_upgrade_minor_version=auto_upgrade_minor_version,
                                     settings=setting,
                                     protected_settings=protected_setting,
                                     provision_after_extensions=provision_after_extension)

        node_type.vm_extensions.append(newExtension)

        poller = client.node_types.begin_create_or_update(resource_group_name, cluster_name, node_type_name, node_type)
        return LongRunningOperation(cmd.cli_ctx)(poller)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def delete_vm_extension(cmd,
                        client,
                        resource_group_name,
                        cluster_name,
                        node_type_name,
                        extension_name):
    try:
        node_type: NodeType = client.node_types.get(resource_group_name, cluster_name, node_type_name)

        if node_type.vm_extensions is not None:
            original_len = len(node_type.vm_extensions)
            node_type.vm_extensions = list(filter(lambda x: x.name.lower() != extension_name.lower(), node_type.vm_extensions))
            if original_len == len(node_type.vm_extensions):
                raise 'Extension with name {} not found'.format(extension_name)

        poller = client.node_types.begin_create_or_update(resource_group_name, cluster_name, node_type_name, node_type)
        return LongRunningOperation(cmd.cli_ctx)(poller)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise


def add_vm_secret(cmd,
                  client,
                  resource_group_name,
                  cluster_name,
                  node_type_name,
                  source_vault_id,
                  certificate_url,
                  certificate_store):
    try:
        node_type: NodeType = client.node_types.get(resource_group_name, cluster_name, node_type_name)

        if node_type.vm_secrets is None:
            node_type.vm_secrets = []

        vault = next((x for x in node_type.vm_secrets if x.source_vault.id.lower() == source_vault_id.lower()), None)

        vault_certificate = VaultCertificate(certificate_store=certificate_store, certificate_url=certificate_url)
        new_vault_secret_group = False
        if vault is None:
            new_vault_secret_group = True
            source_vault = SubResource(id=source_vault_id)
            vault = VaultSecretGroup(source_vault=source_vault, vault_certificates=[])

        if vault.vault_certificates is None:
            vault.vault_certificates = []

        vault.vault_certificates.append(vault_certificate)

        if new_vault_secret_group:
            node_type.vm_secrets.append(vault)

        poller = client.node_types.begin_create_or_update(resource_group_name, cluster_name, node_type_name, node_type)
        return LongRunningOperation(cmd.cli_ctx)(poller)
    except HttpResponseError as ex:
        logger.error("HttpResponseError: %s", ex)
        raise
