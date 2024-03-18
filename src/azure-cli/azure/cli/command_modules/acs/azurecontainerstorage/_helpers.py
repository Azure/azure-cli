# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from typing import Tuple

from azure.cli.command_modules.acs.azurecontainerstorage._consts import (
    CONST_ACSTOR_ALL,
    CONST_ACSTOR_IO_ENGINE_LABEL_KEY,
    CONST_ACSTOR_K8S_EXTENSION_NAME,
    CONST_EXT_INSTALLATION_NAME,
    CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME,
    CONST_K8S_EXTENSION_CUSTOM_MOD_NAME,
    CONST_K8S_EXTENSION_NAME,
    CONST_STORAGE_POOL_OPTION_NVME,
    CONST_STORAGE_POOL_OPTION_SSD,
    CONST_STORAGE_POOL_TYPE_AZURE_DISK,
    CONST_STORAGE_POOL_TYPE_ELASTIC_SAN,
    CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK,
)
from azure.cli.command_modules.acs._roleassignments import (
    add_role_assignment,
    build_role_scope,
    delete_role_assignments,
)
from azure.cli.core.azclierror import UnknownError
from knack.log import get_logger

logger = get_logger(__name__)


def validate_storagepool_creation(
    cmd,
    subscription_id,
    node_resource_group,
    kubelet_identity_object_id,
    storage_pool_type,
):
    if storage_pool_type == CONST_STORAGE_POOL_TYPE_ELASTIC_SAN:
        role_assignment_success = perform_role_operations_on_managed_rg(
            cmd,
            subscription_id,
            node_resource_group,
            kubelet_identity_object_id,
            True
        )

        if not role_assignment_success:
            raise UnknownError(
                f"Cannot set --enable-azure-container-storage to {CONST_STORAGE_POOL_TYPE_ELASTIC_SAN}. "
                "Unable to add Role Assignments needed for Elastic SAN storagepools to be functional. "
                "Please check with your admin for permissions."
            )


def perform_role_operations_on_managed_rg(
    cmd,
    subscription_id,
    node_resource_group,
    kubelet_identity_object_id,
    assign
):
    managed_rg_role_scope = build_role_scope(node_resource_group, None, subscription_id)
    roles = ["Azure Container Storage Operator"]
    result = True

    for role in roles:
        try:
            if assign:
                result = add_role_assignment(
                    cmd,
                    role,
                    kubelet_identity_object_id,
                    scope=managed_rg_role_scope,
                    delay=0,
                )
            else:
                # NOTE: delete_role_assignments accepts cli_ctx
                # instead of cmd unlike add_role_assignment.
                result = delete_role_assignments(
                    cmd.cli_ctx,
                    role,
                    kubelet_identity_object_id,
                    scope=managed_rg_role_scope,
                    delay=0,
                )

            if not result:
                break
        except Exception:  # pylint: disable=broad-except
            break
    else:
        return True

    if not assign:
        logger.error("\nUnable to revoke Role Assignments if any, added for Azure Container Storage.")

    return False


def get_k8s_extension_module(module_name):
    try:
        # adding the installed extension in the path
        from azure.cli.core.extension.operations import add_extension_to_path
        add_extension_to_path(CONST_K8S_EXTENSION_NAME)
        # import the extension module
        from importlib import import_module
        azext_custom = import_module(module_name)
        return azext_custom
    except ImportError:
        raise UnknownError(  # pylint: disable=raise-missing-from
            "Please add CLI extension `k8s-extension` for performing Azure Container Storage operations.\n"
            "Run command `az extension add --name k8s-extension`"
        )


def check_if_extension_is_installed(cmd, resource_group, cluster_name) -> bool:
    client_factory = get_k8s_extension_module(CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME)
    client = client_factory.cf_k8s_extension_operation(cmd.cli_ctx)
    k8s_extension_custom_mod = get_k8s_extension_module(CONST_K8S_EXTENSION_CUSTOM_MOD_NAME)
    return_val = True
    try:
        extension = k8s_extension_custom_mod.show_k8s_extension(
            client,
            resource_group,
            cluster_name,
            CONST_EXT_INSTALLATION_NAME,
            "managedClusters",
        )

        extension_type = extension.extension_type.lower()
        if extension_type != CONST_ACSTOR_K8S_EXTENSION_NAME:
            return_val = False
    except:  # pylint: disable=bare-except
        return_val = False

    return return_val


def get_extension_installed_and_cluster_configs(
    cmd,
    resource_group,
    cluster_name,
    agentpool_profiles
) -> Tuple[bool, bool, bool, bool, float]:
    client_factory = get_k8s_extension_module(CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME)
    client = client_factory.cf_k8s_extension_operation(cmd.cli_ctx)
    k8s_extension_custom_mod = get_k8s_extension_module(CONST_K8S_EXTENSION_CUSTOM_MOD_NAME)
    is_extension_installed = False
    is_elasticSan_enabled = False
    is_azureDisk_enabled = False
    is_ephemeralDisk_nvme_enabled = False
    is_ephemeralDisk_localssd_enabled = False
    resource_cpu_value = -1

    try:
        extension = k8s_extension_custom_mod.show_k8s_extension(
            client,
            resource_group,
            cluster_name,
            CONST_EXT_INSTALLATION_NAME,
            "managedClusters",
        )

        extension_type = extension.extension_type.lower()
        is_extension_installed = extension_type == CONST_ACSTOR_K8S_EXTENSION_NAME
        config_settings = extension.configuration_settings

        if is_extension_installed and config_settings is not None:
            is_cli_operation_active = config_settings.get("global.cli.activeControl", "False") == "True"
            if is_cli_operation_active:
                is_azureDisk_enabled = (
                    config_settings.get("global.cli.storagePool.azureDisk.enabled", "False") == "True"
                )
                is_elasticSan_enabled = (
                    config_settings.get("global.cli.storagePool.elasticSan.enabled", "False") == "True"
                )
                is_ephemeralDisk_nvme_enabled = (
                    config_settings.get("global.cli.storagePool.ephemeralDisk.nvme.enabled", "False") == "True"
                )
                is_ephemeralDisk_localssd_enabled = (
                    config_settings.get("global.cli.storagePool.ephemeralDisk.temp.enabled", "False") == "True"
                )
                cpu_value = config_settings.get("global.cli.resources.ioEngine.cpu", "1")
                resource_cpu_value = float(cpu_value)
            else:
                # For versions where "global.cli.activeControl" were not set it signifies
                # that selective control of storgepool type was not yet defined.
                # Hence, all the storagepool types are active and io engine core count is 1.
                is_azureDisk_enabled = is_elasticSan_enabled = is_ephemeralDisk_localssd_enabled = True
                resource_cpu_value = 1

                # Determine if epehemeral NVMe was active based on the labelled nodepools present in cluster.
                for agentpool in agentpool_profiles:
                    vm_size = agentpool.vm_size
                    node_labels = agentpool.node_labels
                    if (node_labels is not None and
                            node_labels.get(CONST_ACSTOR_IO_ENGINE_LABEL_KEY) is not None and
                            vm_size.lower().startswith('standard_l')):
                        is_ephemeralDisk_nvme_enabled = True
                        break

    except:  # pylint: disable=bare-except
        is_extension_installed = False

    return (
        is_extension_installed,
        is_azureDisk_enabled,
        is_elasticSan_enabled,
        is_ephemeralDisk_localssd_enabled,
        is_ephemeralDisk_nvme_enabled,
        resource_cpu_value
    )


def get_initial_resource_value_args(
    storage_pool_type,
    storage_pool_option,
    nodepool_skus,
):
    core_value = memory_value = hugepages_value = hugepages_number = 0
    if (storage_pool_type == CONST_STORAGE_POOL_TYPE_AZURE_DISK or
        (storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK and
         storage_pool_option == CONST_STORAGE_POOL_OPTION_SSD)):
        core_value = 1
        memory_value = 1
        hugepages_value = 1
        hugepages_number = 512
    elif (storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK and
          storage_pool_option == CONST_STORAGE_POOL_OPTION_NVME):
        core_value = _get_cpu_value_based_on_vm_size(nodepool_skus)
        memory_value = 2
        hugepages_value = 2
        hugepages_number = 1024

    return _generate_k8s_extension_resource_args(
        core_value,
        memory_value,
        hugepages_value,
        hugepages_number,
    )


def get_current_resource_value_args(
    is_azureDisk_enabled,
    is_elasticSan_enabled,
    is_ephemeralDisk_localssd_enabled,
    is_ephemeralDisk_nvme_enabled,
    current_core_value=None,
    nodepool_skus=None,
):
    (
        current_core_value,
        current_memory_value,
        current_hugepages_value,
        current_hugepages_number,
    ) = _get_current_resource_values(
        is_azureDisk_enabled,
        is_elasticSan_enabled,
        is_ephemeralDisk_localssd_enabled,
        is_ephemeralDisk_nvme_enabled,
        current_core_value,
        nodepool_skus,
    )

    return _generate_k8s_extension_resource_args(
        current_core_value,
        current_memory_value,
        current_hugepages_value,
        current_hugepages_number,
    )


def get_desired_resource_value_args(
    storage_pool_type,
    storage_pool_option,
    current_core_value,
    is_azureDisk_enabled,
    is_elasticSan_enabled,
    is_ephemeralDisk_localssd_enabled,
    is_ephemeralDisk_nvme_enabled,
    nodepool_skus,
    is_enabling_op,
):
    (
        current_core_value,
        current_memory_value,
        current_hugepages_value,
        current_hugepages_number,
    ) = _get_current_resource_values(
        is_azureDisk_enabled,
        is_elasticSan_enabled,
        is_ephemeralDisk_localssd_enabled,
        is_ephemeralDisk_nvme_enabled,
        current_core_value,
        nodepool_skus,
    )

    updated_core_value = updated_memory_value = \
        updated_hugepages_value = updated_hugepages_number = 0

    if is_enabling_op:
        if storage_pool_type == CONST_STORAGE_POOL_TYPE_AZURE_DISK or \
           (storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK and
                storage_pool_option == CONST_STORAGE_POOL_OPTION_SSD):
            updated_core_value = 1
            updated_memory_value = 1
            updated_hugepages_value = 1
            updated_hugepages_number = 512
        elif (storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK and
              storage_pool_option == CONST_STORAGE_POOL_OPTION_NVME):
            updated_core_value = _get_cpu_value_based_on_vm_size(nodepool_skus)
            updated_memory_value = 2
            updated_hugepages_value = 2
            updated_hugepages_number = 1024

        # We have decided the updated value based on the type we are enabling.
        # Now, we compare and check if the current values are already greater
        # than that and if so, we preserve the current values.
        updated_core_value = current_core_value \
            if current_core_value > updated_core_value else updated_core_value
        updated_memory_value = current_memory_value \
            if current_memory_value > updated_memory_value else updated_memory_value
        updated_hugepages_value = current_hugepages_value \
            if current_hugepages_value > updated_hugepages_value else updated_hugepages_value
        updated_hugepages_number = current_hugepages_number \
            if current_hugepages_number > updated_hugepages_number else updated_hugepages_number
    else:
        # If we are disabling AzureDisk storagepool but EphemeralDisk(any) is
        # still enabled, or if we are disabling Ephemeral LocalSSD but
        # AzureDisk or Ephemeral NVMe storagepool is still enabled, or
        # if we are disabling ElasticSan storagepool but AzureDisk or any
        # EphemeralDisk storagepool type is still enabled,
        # then we will preserve the current resource values.
        is_disabled_type_smaller_than_active_types = (
            (storage_pool_type == CONST_STORAGE_POOL_TYPE_ELASTIC_SAN and
                (is_azureDisk_enabled or is_ephemeralDisk_nvme_enabled or is_ephemeralDisk_localssd_enabled)) or
            (storage_pool_type == CONST_STORAGE_POOL_TYPE_AZURE_DISK and
                (is_ephemeralDisk_nvme_enabled or is_ephemeralDisk_localssd_enabled)) or
            (storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK and
                storage_pool_option == CONST_STORAGE_POOL_OPTION_SSD and
                (is_azureDisk_enabled or is_ephemeralDisk_nvme_enabled))
        )
        is_ephemeral_nvme_disabled_azureDisk_active = (
            storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK and
            (storage_pool_option == CONST_STORAGE_POOL_OPTION_NVME and
                (is_ephemeralDisk_localssd_enabled or is_azureDisk_enabled) or
                (storage_pool_option == CONST_ACSTOR_ALL and is_azureDisk_enabled))
        )
        if is_disabled_type_smaller_than_active_types:
            updated_core_value = current_core_value
            updated_memory_value = current_memory_value
            updated_hugepages_value = current_hugepages_value
            updated_hugepages_number = current_hugepages_number
        elif is_ephemeral_nvme_disabled_azureDisk_active:
            # If we are disabling Ephemeral NVMe storagepool but azureDisk is
            # still enabled, we will set the azureDisk storagepool type values.
            updated_core_value = 1
            updated_memory_value = 1
            updated_hugepages_value = 1
            updated_hugepages_number = 512

    return _generate_k8s_extension_resource_args(
        updated_core_value,
        updated_memory_value,
        updated_hugepages_value,
        updated_hugepages_number,
    )


# get_cores_from_sku returns the number of core in the vm_size passed.
# Returns -1 if there is a problem with parsing the vm_size.
def get_cores_from_sku(vm_size):
    cpu_value = -1
    pattern = r'standard_([a-z]+)(\d+)([a-z]*)_v(\d+)'
    match = re.search(pattern, vm_size.lower())
    if match:
        series_prefix = match.group(1)
        size_val = int(match.group(2))
        version = int(match.group(4))

        cpu_value = size_val
        # https://learn.microsoft.com/en-us/azure/virtual-machines/dv2-dsv2-series
        # https://learn.microsoft.com/en-us/azure/virtual-machines/dv2-dsv2-series-memory
        if version == 2 and (series_prefix in ('d', 'ds')):
            if size_val in (2, 11):
                cpu_value = 2
            elif size_val in (3, 12):
                cpu_value = 4
            elif size_val in (4, 13):
                cpu_value = 8
            elif size_val in (5, 14):
                cpu_value = 16
            elif size_val == 15:
                cpu_value = 20

    return cpu_value


def _get_cpu_value_based_on_vm_size(nodepool_skus):
    cpu_value = -1
    for vm_size in nodepool_skus:
        number_of_cores = get_cores_from_sku(vm_size)
        if number_of_cores != -1:
            if cpu_value == -1:
                cpu_value = number_of_cores * 0.25
            else:
                cpu_value = (number_of_cores * 0.25) if \
                    (cpu_value > number_of_cores * 0.25) else \
                    cpu_value
        else:
            raise UnknownError(
                f"Unable to determine the number of cores in nodepool of node size: {vm_size}"
            )

    if cpu_value == -1:
        cpu_value = 1
    return cpu_value


def _get_current_resource_values(
    is_azureDisk_enabled,
    is_elasticSan_enabled,
    is_ephemeralDisk_localssd_enabled,
    is_ephemeralDisk_nvme_enabled,
    current_core_value=None,
    nodepool_skus=None,
):
    # Setting these to default values set in the cluster when
    # all the storagepools used to be enabled by default.
    core_value = current_memory_value = current_hugepages_value = 1
    current_hugepages_number = 1024
    if is_elasticSan_enabled:
        core_value = 0
        current_memory_value = 0
        current_hugepages_value = 0
        current_hugepages_number = 0
    if is_azureDisk_enabled or is_ephemeralDisk_localssd_enabled:
        core_value = 1
        current_memory_value = 1
        current_hugepages_value = 1
        current_hugepages_number = 512
    if is_ephemeralDisk_nvme_enabled:
        if current_core_value is None and nodepool_skus is not None:
            core_value = _get_cpu_value_based_on_vm_size(nodepool_skus)
        current_memory_value = 2
        current_hugepages_value = 2
        current_hugepages_number = 1024

    current_core_value = current_core_value if current_core_value is not None else core_value

    return (
        current_core_value,
        current_memory_value,
        current_hugepages_value,
        current_hugepages_number
    )


def _generate_k8s_extension_resource_args(
    core_value,
    memory_value,
    hugepages_value,
    hugepages_number,
):
    memory_value_str = str(memory_value) + "Gi"
    hugepages_value_str = str(hugepages_value) + "Gi"

    resource_args = [
        {"global.cli.resources.num_hugepages": hugepages_number},
        {"global.cli.resources.ioEngine.cpu": str(core_value)},
        {"global.cli.resources.ioEngine.memory": memory_value_str},
        {"global.cli.resources.ioEngine.hugepages2Mi": hugepages_value_str},
    ]

    return resource_args
