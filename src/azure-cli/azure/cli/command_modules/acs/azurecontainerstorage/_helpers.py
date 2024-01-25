# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
from datetime import datetime

from azure.cli.command_modules.acs._client_factory import get_providers_client_factory
from azure.cli.command_modules.acs.azurecontainerstorage._consts import (
    CONST_ACSTOR_K8S_EXTENSION_NAME,
    CONST_EXT_INSTALLATION_NAME,
    CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME,
    CONST_K8S_EXTENSION_CUSTOM_MOD_NAME,
    CONST_K8S_EXTENSION_NAME,
    CONST_STORAGE_POOL_OPTION_NVME,
    CONST_STORAGE_POOL_TYPE_ELASTIC_SAN,
    CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK,
    RP_REGISTRATION_POLLING_INTERVAL_IN_SEC,
)
from azure.cli.command_modules.acs._roleassignments import (
    add_role_assignment,
    build_role_scope,
    delete_role_assignments,
)
from azure.cli.core.azclierror import UnknownError
from knack.log import get_logger

logger = get_logger(__name__)


def register_dependent_rps(cmd, subscription_id) -> bool:
    required_rp = 'Microsoft.KubernetesConfiguration'
    from azure.mgmt.resource.resources.models import (
        ProviderConsentDefinition, ProviderRegistrationRequest)

    properties = ProviderRegistrationRequest(
        third_party_provider_consent=ProviderConsentDefinition(
            consent_to_authorization=False
        )
    )
    client = get_providers_client_factory(cmd.cli_ctx)
    is_registered = False
    try:
        is_registered = _is_rp_registered(cmd, required_rp, subscription_id)
        if is_registered:
            return True
        client.register(required_rp, properties=properties)
        # wait for registration to finish
        timeout_secs = 120
        start = datetime.utcnow()
        is_registered = _is_rp_registered(cmd, required_rp, subscription_id)
        while not is_registered:
            is_registered = _is_rp_registered(cmd, required_rp, subscription_id)
            time.sleep(RP_REGISTRATION_POLLING_INTERVAL_IN_SEC)
            if (datetime.utcnow() - start).seconds >= timeout_secs:
                logger.error(
                    "Timed out while waiting for the %s resource provider to be registered.", required_rp
                )
                break

    except Exception as e:  # pylint: disable=broad-except
        logger.error(
            "Installation of Azure Container Storage requires registering to the following resource provider: %s. "
            "We were unable to perform the registration on your behalf due to the following error: %s\n"
            "Please check with your admin on permissions, or try running registration manually with: "
            "`az provider register --namespace %s` command.", required_rp, e, required_rp
        )

    return is_registered


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
                "Unable to add Role Assignments needed for Elastic SAN storagepools to be functional. " \
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
    roles = ["Reader", "Network Contributor", "Elastic SAN Owner", "Elastic SAN Volume Group Owner"]
    # roles = ["Azure Container Storage Operator"]
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


def get_extension_installed_and_cluster_configs(cmd, resource_group, cluster_name)  -> Tuple[bool, bool, bool, bool, Union[str, None]]:
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
        if extension_type != CONST_ACSTOR_K8S_EXTENSION_NAME:
            is_extension_installed = False

        if is_extension_installed:
            config_settings = extension.configuration_settings
            if config_settings is not None:
                is_azureDisk_enabled = bool(config_settings.get("cli.storagePool.azureDisk.enabled", "False"))
                is_elasticSan_enabled = bool(config_settings.get("cli.storagePool.elasticSan.enabled", "False"))
                is_ephemeralDisk_enabled = bool(config_settings.get("cli.storagePool.ephemeralDisk.enabled", "False"))
                storagepool_type_val = config_settings.get("cli.storagePool.type", None)
                cpu_value = config_settings.get("cli.resources.ioEngine.cpu", None)
                if storagepool_type_val is not None:
                    if storagepool_type_val == CONST_STORAGE_POOL_TYPE_AZURE_DISK:
                        is_azureDisk_enabled = True
                    elif storage_pool_type == CONST_STORAGE_POOL_TYPE_ELASTIC_SAN:
                        is_elasticSan_enabled = True
                    elif storagepool_type_val == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK:
                        ephemeral_disk_type = config_settings.get("cli.storagePool.ephemeralDisk.diskType", CONST_STORAGE_POOL_OPTION_NVME)
                        if ephemeral_disk_type == CONST_STORAGE_POOL_OPTION_NVME:
                            is_ephemeralDisk_nvme_enabled = True
                        elif ephemeral_disk_type == CONST_STORAGE_POOL_OPTION_SSD:
                            is_ephemeral_localssd_enabled = True
                if cpu_value is not None:
                    resource_cpu_value = int(cpu_value)

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
    agentpool_details,
):
    core_value = memory_value = hugepages_value = hugepages_number = 0
    if storage_pool_type == CONST_STORAGE_POOL_TYPE_AZURE_DISK or \
      (storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK and \
      storage_pool_option == CONST_STORAGE_POOL_OPTION_SSD):
        core_value = 1
        memory_value = 1
        hugepages_value = 1
        hugepages_number = 512
    elif storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK and \
      storage_pool_option == CONST_STORAGE_POOL_OPTION_NVME:
        core_value = _get_cpu_value_based_on_vm_size(agentpool_details)
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
    agentpool_details=None,
):
    (
        current_core_value,
        current_memory_value,
        current_hugepages_value,
        current_hugepages_number,
    ) = _get_current_resource_values(
        is_azureDisk_enabled,
        is_elasticSan_enabled,
        is_ephemeral_localssd_enabled,
        is_ephemeralDisk_nvme_enabled,
        current_core_value,
        agentpool_details,
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
    agentpool_details,
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
        is_ephemeral_localssd_enabled,
        is_ephemeralDisk_nvme_enabled,
        current_core_value,
        agentpool_details,
    )

    return _generate_k8s_extension_resource_args(
        current_core_value,
        current_memory_value,
        current_hugepages_value,
        current_hugepages_number,
    )

    updated_core_value = updated_memory_value = \
      updated_hugepages_value = updated_hugepages_number = 0

    if is_enabling_op:
        if storage_pool_type == CONST_STORAGE_POOL_TYPE_AZURE_DISK or \
           (storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK and \
           storage_pool_option == CONST_STORAGE_POOL_OPTION_SSD):
            updated_core_value = 1
            updated_memory_value = 1
            updated_hugepages_value = 1
            updated_hugepages_number = 512
        elif storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK and \
           storage_pool_option == CONST_STORAGE_POOL_OPTION_NVME:
            updated_core_value = _get_cpu_value_based_on_vm_size(agentpool_details)
            updated_memory_value = 2
            updated_hugepages_value = 2
            updated_hugepages_number = 1024

        # We have decided the updated value based on the type we are enabling.
        # Now, we compare and check if the current values are already greater
        # than that and if so, we preserve the current values.
        updated_core_value = current_core_value if current_core_value > updated_core_value else updated_core_value
        updated_memory_value = current_memory_value if current_memory_value > updated_memory_value else updated_memory_value
        updated_hugepages_value = current_hugepages_value if current_hugepages_value > updated_hugepages_value else updated_hugepages_value
        updated_hugepages_number = current_hugepages_number if current_hugepages_number > proposed_hugepages_number else proposed_hugepages_number
    else:
        # If we are disabling Ephemeral NVMe storagepool but azureDisk is
        # still enabled, we will set the azureDisk storagepool type values.
        if storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK and \
          is_ephemeralDisk_nvme_enabled and is_azureDisk_enabled:
            updated_core_value = 1
            updated_memory_value = 1
            updated_hugepages_value = 1
            updated_hugepages_number = 512
        # If we are disabling AzureDisk storagepool but EphemeralDisk is
        # still enabled, then we will preserve the current resource values.
        elif storage_pool_type == CONST_STORAGE_POOL_TYPE_AZURE_DISK and \
          (is_ephemeralDisk_nvme_enabled or is_ephemeral_localssd_enabled):
            updated_core_value = current_core_value
            updated_memory_value = current_memory_value
            updated_hugepages_value = current_hugepages_value
            updated_hugepages_number = current_hugepages_number

    return _generate_k8s_extension_resource_args(
        updated_core_value,
        updated_memory_value,
        updated_hugepages_value,
        updated_hugepages_number,
    )


def _is_rp_registered(cmd, required_rp, subscription_id):
    registered = False
    try:
        providers_client = get_providers_client_factory(cmd.cli_ctx, subscription_id)
        registration_state = getattr(providers_client.get(required_rp), 'registration_state', "NotRegistered")

        registered = (registration_state and registration_state.lower() == 'registered')
    except Exception:  # pylint: disable=broad-except
        pass
    return registered


def _get_cpu_value_based_on_vm_size(agentpool_details):
    cpu_value = -1
    for vm_size in agentpool_details:
        pattern = r'standard_l(\d+)s_v\d+'
        match = re.search(pattern, vm_size.lower())
        if match:
            number_of_cores = match.group(1)
            if cpu_value == -1:
                cpu_value = number_of_cores * 0.25
            else:
                cpu_value = (number_of_cores * 0.25) if \
                            (cpu_value > number_of_cores * 0.25) else \
                            cpu_value

        else:
            logger.warning(
                f"Unable to get the number of cores in nodepool of vm size: {vm_size}"
            )
    return cpu_value


def _get_current_resource_values(
    is_azureDisk_enabled,
    is_elasticSan_enabled,
    is_ephemeralDisk_localssd_enabled,
    is_ephemeralDisk_nvme_enabled,    
    current_core_value=None,
    agentpool_details=None,
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
        if current_core_value is None and agentpool_details is not None:
            core_value = _get_cpu_value_based_on_vm_size(agentpool_details)
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
        {"cli.resources.num_hugepages": hugepages_number},
        {"cli.resources.ioEngine.cpu": str(core_value)},
        {"cli.resources.ioEngine.memory": memory_value_str},
        {"cli.resources.ioEngine.hugepages2Mi": hugepages_value_str},
    ]

    return resource_args
