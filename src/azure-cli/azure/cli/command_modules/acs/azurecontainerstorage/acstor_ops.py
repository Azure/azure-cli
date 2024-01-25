# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import UnknownError
from azure.cli.core.commands import LongRunningOperation
from azure.cli.command_modules.acs.azurecontainerstorage._consts import (
    CONST_ACSTOR_K8S_EXTENSION_NAME,
    CONST_EXT_INSTALLATION_NAME,
    CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME,
    CONST_K8S_EXTENSION_CUSTOM_MOD_NAME,
    CONST_STORAGE_POOL_DEFAULT_SIZE,
    CONST_STORAGE_POOL_DEFAULT_SIZE_ESAN,
    CONST_STORAGE_POOL_OPTION_NVME,
    CONST_STORAGE_POOL_OPTION_SSD,
    CONST_STORAGE_POOL_SKU_PREMIUM_LRS,
    CONST_STORAGE_POOL_TYPE_AZURE_DISK,
    CONST_STORAGE_POOL_TYPE_ELASTIC_SAN,
    CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK,
)
from azure.cli.command_modules.acs.azurecontainerstorage._helpers import (
    get_k8s_extension_module,
    get_current_resource_value_args,
    get_desired_resource_value_args,
    get_initial_resource_value_args,
    perform_role_operations_on_managed_rg,
    register_dependent_rps,
    validate_storagepool_creation,
)
from knack.log import get_logger

logger = get_logger(__name__)


def perform_enable_azure_container_storage(
    cmd,
    subscription_id,
    resource_group,
    cluster_name,
    node_resource_group,
    kubelet_identity_object_id,
    storage_pool_name,
    storage_pool_type,
    storage_pool_size,
    storage_pool_sku,
    storage_pool_option,
    agentpool_details,
    is_cluster_create,
    is_extension_installed=False,
    is_azureDisk_enabled=False,
    is_elasticSan_enabled=False,
    is_ephemeralDisk_localssd_enabled=False,
    is_ephemeralDisk_nvme_enabled=False,
    current_core_value=None,
):
    # Step 1: Check and register the dependent provider for ManagedClusters i.e.
    # Microsoft.KubernetesConfiguration
    # if not register_dependent_rps(cmd, subscription_id):
    #     return

    if storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK and \
       storage_pool_option == CONST_STORAGE_POOL_OPTION_SSD:
        storage_pool_option = "temp"

    # Step 2: Validate if storagepool could be created.
    # Depends on the following:
    #   2a: Grant AKS cluster's node identity the following
    #       roles on the AKS managed resource group:
    #       1. Reader
    #       2. Network Contributor
    #       3. Elastic SAN Owner
    #       4. Elastic SAN Volume Group Owner
    #       Azure Container Storage Operator (replace)
    #       Ensure grant was successful if creation of
    #       Elastic SAN storagepool is requested.
    validate_storagepool_creation(
        cmd,
        subscription_id,
        node_resource_group,
        kubelet_identity_object_id,
        storage_pool_type,
        storage_pool_option,
    )

    # Step 3: Configure the storagepool parameters
    config_settings = []
    if storage_pool_name is None:
        storage_pool_name = storage_pool_type.lower()
    if storage_pool_size is None:
        storage_pool_size = CONST_STORAGE_POOL_DEFAULT_SIZE_ESAN if \
            storage_pool_type == CONST_STORAGE_POOL_TYPE_ELASTIC_SAN else \
            CONST_STORAGE_POOL_DEFAULT_SIZE

    azure_disk_enabled = is_azureDisk_enabled if is_extension_installed else False
    elastic_san_enabled = is_elasticSan_enabled if is_extension_installed else False
    ephemeral_disk_enabled = (is_ephemeralDisk_nvme_enabled or is_ephemeralDisk_localssd_enabled) if is_extension_installed or \
                             False

    if storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK:
        config_settings.append({"cli.storagePool.ephemeralDisk.diskType": storage_pool_option.lower()})
        ephemeral_disk_enabled = True
    else:
        if storage_pool_sku is None:
            storage_pool_sku = CONST_STORAGE_POOL_SKU_PREMIUM_LRS
        if storage_pool_type == CONST_STORAGE_POOL_TYPE_ELASTIC_SAN:
            config_settings.append({"cli.storagePool.elasticSan.sku": storage_pool_sku})
            elastic_san_enabled = True
        elif storage_pool_type == CONST_STORAGE_POOL_TYPE_AZURE_DISK:
            config_settings.append({"cli.storagePool.azureDisk.sku": storage_pool_sku})
            azure_disk_enabled = True

    config_settings.extend(
        [
            {"cli.storagePool.create": True},
            {"cli.storagePool.name": storage_pool_name},
            {"cli.storagePool.size": storage_pool_size},
            {"cli.storagePool.type": storage_pool_type},
            {"cli.storagePool.azureDisk.enabled": azure_disk_enabled},
            {"cli.storagePool.elasticSan.enabled": elastic_san_enabled},
            {"cli.storagePool.ephemeralDisk.enabled": ephemeral_disk_enabled},
            # Always set cli.storagePool.disable.type to empty
            # and cli.storagePool.disable.validation to False
            # during enable operation so that any older disable
            # operation doesn't interfere with the current state.
            {"cli.storagePool.disable.validation": False},
            {"cli.storagePool.disable.type": ""},
            {"cli.storagePool.disable.active": False},
        ]
    )

    if is_extension_installed:
        resource_args = get_desired_resource_value_args(
            storage_pool_type,
            storage_pool_option,
            current_core_value,
            is_azureDisk_enabled,
            is_elasticSan_enabled,
            is_ephemeralDisk_localssd_enabled,
            is_ephemeralDisk_nvme_enabled,
            agentpool_details,
            True,
        )

    else:
        resource_args = get_initial_resource_value_args(
            storage_pool_type,
            storage_pool_option,
            agentpool_details,
        )

    config_settings.extend(resource_args)

    # Step 5: Install the k8s_extension 'microsoft.azurecontainerstorage'
    client_factory = get_k8s_extension_module(CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME)
    client = client_factory.cf_k8s_extension_operation(cmd.cli_ctx)

    k8s_extension_custom_mod = get_k8s_extension_module(CONST_K8S_EXTENSION_CUSTOM_MOD_NAME)
    try:
        if is_extension_installed:
            result = k8s_extension_custom_mod.update_k8s_extension(
                cmd,
                client,
                resource_group,
                cluster_name,
                CONST_EXT_INSTALLATION_NAME,
                "managedClusters",
                configuration_settings=config_settings,
                yes=True,
                no_wait=False,
            )
            op_text = "Azure Container Storage successfully updated"
        else:
            result = k8s_extension_custom_mod.create_k8s_extension(
                cmd,
                client,
                resource_group,
                cluster_name,
                CONST_EXT_INSTALLATION_NAME,
                "managedClusters",
                CONST_ACSTOR_K8S_EXTENSION_NAME,
                auto_upgrade_minor_version=True,
                release_train="stable",
                scope="cluster",
                release_namespace="acstor",
                configuration_settings=config_settings,
            )
            op_text = "Azure Container Storage successfully installed"

            long_op_result = LongRunningOperation(cmd.cli_ctx)(result)
            if long_op_result.provisioning_state == "Succeeded":
                logger.warning(op_text)
    except Exception as ex:  # pylint: disable=broad-except
        if is_cluster_create:
            logger.error("Azure Container Storage failed to install.\nError: %s", ex)
            logger.warning(
                "AKS cluster is created. "
                "Please run `az aks update` along with `--enable-azure-container-storage` "
                "to enable Azure Container Storage."
            )
        else:
            if is_extension_installed:
                logger.error(
                    "AKS update to enable Azure Container Storage pool type %s failed. \n"
                    " Error: %s", storage_pool_type, ex
                )
            else:
                logger.error("AKS update to enable Azure Container Storage failed.\nError: %s", ex)


def perform_disable_azure_container_storage(
    cmd,
    subscription_id,
    resource_group,
    cluster_name,
    node_resource_group,
    kubelet_identity_object_id,
    perform_validation,
    storage_pool_type,
    is_elasticSan_enabled,
    is_azureDisk_enabled,
    is_ephemeralDisk_localssd_enabled,
    is_ephemeralDisk_nvme_enabled,
    current_core_value,
):
    client_factory = get_k8s_extension_module(CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME)
    client = client_factory.cf_k8s_extension_operation(cmd.cli_ctx)
    k8s_extension_custom_mod = get_k8s_extension_module(CONST_K8S_EXTENSION_CUSTOM_MOD_NAME)
    no_wait_delete_op = False
    # Step 1: Perform validation if accepted by user
    if perform_validation:
        config_settings = [
            {"cli.storagePool.disable.validation": True},
            {"cli.storagePool.disable.type": storage_pool_type},
        ]

        try:
            update_result = k8s_extension_custom_mod.update_k8s_extension(
                cmd,
                client,
                resource_group,
                cluster_name,
                CONST_EXT_INSTALLATION_NAME,
                "managedClusters",
                configuration_settings=config_settings,
                yes=True,
                no_wait=False,
            )

            update_long_op_result = LongRunningOperation(cmd.cli_ctx)(update_result)
            if update_long_op_result.provisioning_state == "Succeeded":
                logger.warning("Validation succeeded. Continuing Azure Container Storage disable operation...")

            # Since, pre uninstall validation will ensure deletion of storagepools,
            # we don't need to long wait while performing the delete operation.
            # Setting no_wait_delete_op = True.
            # Only relevant when we are uninstalling Azure Container Storage completely.
            if storage_pool_type == CONST_STORAGE_POOL_TYPE_ALL:
                no_wait_delete_op = True
        except Exception as ex:  # pylint: disable=broad-except
            config_settings = [
                {"cli.storagePool.disable.validation": False},
                {"cli.storagePool.disable.type": ""},
            ]

            err_msg = "Validation failed. " \
                    "Please ensure that storagepools are not being used. " \
                    "Unable to perform disable Azure Container Storage operation. " \
                    "Reseting cluster state."

            if storage_pool_type != CONST_STORAGE_POOL_TYPE_ALL:
                err_msg = "Validation failed. " \
                        f"Please ensure that storagepools of type {storage_pool_type} are not being used. " \
                        f"Unable to perform disable Azure Container Storage operation. " \
                        "Reseting cluster state."

            k8s_extension_custom_mod.update_k8s_extension(
                cmd,
                client,
                resource_group,
                cluster_name,
                CONST_EXT_INSTALLATION_NAME,
                "managedClusters",
                configuration_settings=config_settings,
                yes=True,
                no_wait=True,
            )

            if "pre-upgrade hooks failed" in str(ex):
                raise UnknownError(err_msg) from ex
            raise UnknownError(
                "Validation failed. Unable to perform Azure Container Storage operation. Reseting cluster state."
            ) from ex

    # Step 2: If the extension is installed and validation succeeded or skipped, call delete_k8s_extension
    # This step is only relevant when uninstallation of Azure Container Storage is active.
    if storage_pool_type == CONST_STORAGE_POOL_TYPE_ALL:
        try:
            delete_op_result = k8s_extension_custom_mod.delete_k8s_extension(
                cmd,
                client,
                resource_group,
                cluster_name,
                CONST_EXT_INSTALLATION_NAME,
                "managedClusters",
                yes=True,
                no_wait=no_wait_delete_op,
            )
            else:
            if not no_wait_delete_op:
                LongRunningOperation(cmd.cli_ctx)(delete_op_result)
        except Exception as delete_ex:
            raise UnknownError(
                "Failure observed while disabling Azure Container Storage."
            ) from delete_ex

        logger.warning("Azure Container Storage has been disabled.")

        # Step 3: Revoke AKS cluster's node identity the following
        # roles on the AKS managed resource group:
        # 1. Reader
        # 2. Network Contributor
        # 3. Elastic SAN Owner
        # 4. Elastic SAN Volume Group Owner
        perform_role_operations_on_managed_rg(cmd, subscription_id, node_resource_group, kubelet_identity_object_id, False)
    else:
        # Here we start disabling a particular type of storagepool.
        config_settings = [
            {"cli.storagePool.disable.validation": False},
            {"cli.storagePool.disable.type": storage_pool_type},
            {"cli.storagePool.disable.active": True},
        ]
        if storage_pool_type == CONST_STORAGE_POOL_TYPE_AZURE_DISK:
            config_settings.append({"cli.storagePool.azureDisk.enabled": False})
        elif storage_pool_type == CONST_STORAGE_POOL_TYPE_ELASTIC_SAN:
            config_settings.append({"cli.storagePool.elasticSan.enabled": False})
        elif storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK:
            config_settings.append({"cli.storagePool.ephemeralDisk.enabled": False})
        # Define the new resource values for ioEngine and hugepages.
        resource_args = get_desired_resource_value_args(
            storage_pool_type,
            storage_pool_option,
            current_core_value,
            is_azureDisk_enabled,
            is_elasticSan_enabled,
            is_ephemeralDisk_localssd_enabled,
            is_ephemeralDisk_nvme_enabled,
            agentpool_details,
            False,
        )
        config_settings.extend(resource_args)
        # Creating the set of config settings which
        # are required to demarcate that the disabling
        # process is completed. This config variable
        # will be used after the disabling operation is completed.
        update_settings = [
            {"cli.storagePool.disable.validation": False},
            {"cli.storagePool.disable.type": ""},
            {"cli.storagePool.disable.active": False},
        ]
        try:
            disable_op_result = k8s_extension_custom_mod.update_k8s_extension(
                cmd,
                client,
                resource_group,
                cluster_name,
                CONST_EXT_INSTALLATION_NAME,
                "managedClusters",
                configuration_settings=config_settings,
                yes=True,
                no_wait=False,
            )
            LongRunningOperation(cmd.cli_ctx)(disable_op_result)
        except Exception as disable_ex:
            logger.error(
                "Failure observed while disabling Azure Container Storage storagepool type: %s.\nError: %s"
                "Reseting cluster state.", storage_pool_type, disable_ex
            ) from disable_ex

            # If disabling type of storagepool in Azure Container Storage failed,
            # define the existing resource values for ioEngine and hugepages for
            # reseting the cluster state.
            resource_args = get_current_resource_value_args(
                is_azureDisk_enabled,
                is_elasticSan_enabled,
                is_ephemeralDisk_localssd_enabled,
                is_ephemeralDisk_nvme_enabled,
                current_core_value,
            )

            update_settings.extend(resource_args)
            # Also, unset the type of storagepool which was supposed to disabled.
            if storage_pool_type == CONST_STORAGE_POOL_TYPE_AZURE_DISK:
                update_settings.append({"cli.storagePool.azureDisk.enabled": True})
            elif storage_pool_type == CONST_STORAGE_POOL_TYPE_ELASTIC_SAN:
                update_settings.append({"cli.storagePool.elasticSan.enabled": True})
            elif storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK:
                update_settings.append({"cli.storagePool.ephemeralDisk.enabled": True})
            disable_op_failure = True

        # Since we are just reseting the cluster state,
        # we are going to perform a non waiting operation.
        k8s_extension_custom_mod.update_k8s_extension(
            cmd,
            client,
            resource_group,
            cluster_name,
            CONST_EXT_INSTALLATION_NAME,
            "managedClusters",
            configuration_settings=update_settings,
            yes=True,
            no_wait=True,
        )

        if not disable_op_failure:
            logger.warning("Azure Container Storage storagepool type %s has been disabled.", storage_pool_type)