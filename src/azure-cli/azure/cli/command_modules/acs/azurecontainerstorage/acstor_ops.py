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
    CONST_ACSTOR_ALL,
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
    validate_storagepool_creation,
)
from knack.log import get_logger

logger = get_logger(__name__)


def perform_enable_azure_container_storage(  # pylint: disable=too-many-statements,too-many-locals,too-many-branches
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
    acstor_nodepool_skus,
    is_cluster_create,
    is_extension_installed=False,
    is_azureDisk_enabled=False,
    is_elasticSan_enabled=False,
    is_ephemeralDisk_localssd_enabled=False,
    is_ephemeralDisk_nvme_enabled=False,
    current_core_value=None,
):
    # Step 1: Validate if storagepool could be created.
    # Depends on the following:
    #   1a: Grant AKS cluster's node identity the following
    #       roles on the AKS managed resource group:
    #       Azure Container Storage Operator.
    #       Ensure grant was successful if creation of
    #       Elastic SAN storagepool is requested.
    validate_storagepool_creation(
        cmd,
        subscription_id,
        node_resource_group,
        kubelet_identity_object_id,
        storage_pool_type,
    )

    # Step 3: Configure the storagepool parameters
    config_settings = []
    if storage_pool_name is None:
        storage_pool_name = storage_pool_type.lower()
        if storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK:
            storage_pool_name = storage_pool_type.lower() + "-" + storage_pool_option.lower()
    if storage_pool_size is None:
        storage_pool_size = CONST_STORAGE_POOL_DEFAULT_SIZE_ESAN if \
            storage_pool_type == CONST_STORAGE_POOL_TYPE_ELASTIC_SAN else \
            CONST_STORAGE_POOL_DEFAULT_SIZE

    azure_disk_enabled = is_azureDisk_enabled if is_extension_installed else False
    elastic_san_enabled = is_elasticSan_enabled if is_extension_installed else False
    ephemeral_disk_nvme_enabled = is_ephemeralDisk_nvme_enabled if is_extension_installed else False
    ephemeral_disk_localssd_enabled = is_ephemeralDisk_localssd_enabled if is_extension_installed else False

    epheremaldisk_type = ""
    if storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK:
        if storage_pool_option == CONST_STORAGE_POOL_OPTION_NVME:
            ephemeral_disk_nvme_enabled = True
        elif storage_pool_option == CONST_STORAGE_POOL_OPTION_SSD:
            ephemeral_disk_localssd_enabled = True
        epheremaldisk_type = storage_pool_option.lower()
    else:
        if storage_pool_sku is None:
            storage_pool_sku = CONST_STORAGE_POOL_SKU_PREMIUM_LRS
        if storage_pool_type == CONST_STORAGE_POOL_TYPE_ELASTIC_SAN:
            config_settings.append({"global.cli.storagePool.elasticSan.sku": storage_pool_sku})
            elastic_san_enabled = True
        elif storage_pool_type == CONST_STORAGE_POOL_TYPE_AZURE_DISK:
            config_settings.append({"global.cli.storagePool.azureDisk.sku": storage_pool_sku})
            azure_disk_enabled = True

    config_settings.extend(
        [
            {"global.cli.activeControl": True},
            {"global.cli.storagePool.install.create": True},
            {"global.cli.storagePool.install.name": storage_pool_name},
            {"global.cli.storagePool.install.size": storage_pool_size},
            {"global.cli.storagePool.install.type": storage_pool_type},
            {"global.cli.storagePool.install.diskType": epheremaldisk_type},
            {"global.cli.storagePool.azureDisk.enabled": azure_disk_enabled},
            {"global.cli.storagePool.elasticSan.enabled": elastic_san_enabled},
            {"global.cli.storagePool.ephemeralDisk.nvme.enabled": ephemeral_disk_nvme_enabled},
            {"global.cli.storagePool.ephemeralDisk.temp.enabled": ephemeral_disk_localssd_enabled},
            # Always set cli.storagePool.disable.type to empty
            # and cli.storagePool.disable.validation to False
            # during enable operation so that any older disable
            # operation doesn't interfere with the current state.
            {"global.cli.storagePool.disable.validation": False},
            {"global.cli.storagePool.disable.type": ""},
            {"global.cli.storagePool.disable.active": False},
            # Resetting older cluster values from previous ARC version.
            {"cli.storagePool.type": ""},
            {"cli.storagePool.ephemeralDisk.diskType": ""},
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
            acstor_nodepool_skus,
            True,
        )

    else:
        resource_args = get_initial_resource_value_args(
            storage_pool_type,
            storage_pool_option,
            acstor_nodepool_skus,
        )

    config_settings.extend(resource_args)

    # Step 5: Install the k8s_extension 'microsoft.azurecontainerstorage'
    client_factory = get_k8s_extension_module(CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME)
    client = client_factory.cf_k8s_extension_operation(cmd.cli_ctx)

    k8s_extension_custom_mod = get_k8s_extension_module(CONST_K8S_EXTENSION_CUSTOM_MOD_NAME)
    update_settings = [
        {"global.cli.activeControl": True},
        {"global.cli.storagePool.install.create": False},
        {"global.cli.storagePool.install.name": ""},
        {"global.cli.storagePool.install.size": ""},
        {"global.cli.storagePool.install.type": ""},
        {"global.cli.storagePool.install.diskType": ""},
    ]
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
                    " Error: %s. Resetting cluster state.", storage_pool_type, ex
                )

                # If enabling of storagepool type in Azure Container Storage failed,
                # define the existing resource values for ioEngine and hugepages for
                # resetting the cluster state.
                resource_args = get_current_resource_value_args(
                    is_azureDisk_enabled,
                    is_elasticSan_enabled,
                    is_ephemeralDisk_localssd_enabled,
                    is_ephemeralDisk_nvme_enabled,
                    current_core_value,
                )

                update_settings.extend(resource_args)
                # Also, unset the type of storagepool which was supposed to enabled.
                if storage_pool_type == CONST_STORAGE_POOL_TYPE_AZURE_DISK:
                    update_settings.append({"global.cli.storagePool.azureDisk.enabled": False})
                elif storage_pool_type == CONST_STORAGE_POOL_TYPE_ELASTIC_SAN:
                    update_settings.append({"global.cli.storagePool.elasticSan.enabled": False})
                elif storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK:
                    if storage_pool_option == CONST_STORAGE_POOL_OPTION_NVME:
                        update_settings.append({"global.cli.storagePool.ephemeralDisk.nvme.enabled": False})
                    elif storage_pool_option == CONST_STORAGE_POOL_OPTION_SSD:
                        update_settings.append({"global.cli.storagePool.ephemeralDisk.temp.enabled": False})
            else:
                logger.error("AKS update to enable Azure Container Storage failed.\nError: %s", ex)

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


def perform_disable_azure_container_storage(  # pylint: disable=too-many-statements,too-many-locals,too-many-branches
    cmd,
    subscription_id,
    resource_group,
    cluster_name,
    node_resource_group,
    kubelet_identity_object_id,
    perform_validation,
    storage_pool_type,
    storage_pool_option,
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

    azure_disk_enabled = is_azureDisk_enabled
    elastic_san_enabled = is_elasticSan_enabled
    ephemeral_disk_nvme_enabled = is_ephemeralDisk_nvme_enabled
    ephemeral_disk_localssd_enabled = is_ephemeralDisk_localssd_enabled

    # Ensure that all the install storagepool fields are turned off.
    reset_install_settings = [
        {"global.cli.activeControl": True},
        {"global.cli.storagePool.install.create": False},
        {"global.cli.storagePool.install.name": ""},
        {"global.cli.storagePool.install.size": ""},
        {"global.cli.storagePool.install.type": ""},
        {"global.cli.storagePool.install.diskType": ""},
    ]

    pool_option = ""
    if storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK:
        if storage_pool_option is not None:
            pool_option = storage_pool_option.lower()
        else:
            if is_ephemeralDisk_nvme_enabled:
                pool_option = CONST_STORAGE_POOL_OPTION_NVME.lower()
            elif is_ephemeralDisk_localssd_enabled:
                pool_option = CONST_STORAGE_POOL_OPTION_SSD.lower()

    # Step 1: Perform validation if accepted by user
    if perform_validation:
        config_settings = [
            {"global.cli.storagePool.disable.validation": True},
            {"global.cli.storagePool.disable.type": storage_pool_type},
            # Set these values to ensure cluster state incase of
            # a cluster where cli operation has not yet run or older
            # version of charts were installed.
            {"global.cli.storagePool.azureDisk.enabled": azure_disk_enabled},
            {"global.cli.storagePool.elasticSan.enabled": elastic_san_enabled},
            {"global.cli.storagePool.ephemeralDisk.nvme.enabled": ephemeral_disk_nvme_enabled},
            {"global.cli.storagePool.ephemeralDisk.temp.enabled": ephemeral_disk_localssd_enabled},
        ]

        config_settings.extend(reset_install_settings)
        config_settings.append({"global.cli.storagePool.disable.diskType": pool_option.lower()})

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
            if storage_pool_type == CONST_ACSTOR_ALL:
                no_wait_delete_op = True
        except Exception as ex:  # pylint: disable=broad-except
            config_settings = [
                {"global.cli.storagePool.disable.validation": False},
                {"global.cli.storagePool.disable.type": ""},
                {"global.cli.storagePool.disable.diskType": ""},
                # Set these values to ensure cluster state incase of
                # a cluster where cli operation has not yet run or older
                # version of charts were installed.
                {"global.cli.storagePool.azureDisk.enabled": azure_disk_enabled},
                {"global.cli.storagePool.elasticSan.enabled": elastic_san_enabled},
                {"global.cli.storagePool.ephemeralDisk.nvme.enabled": ephemeral_disk_nvme_enabled},
                {"global.cli.storagePool.ephemeralDisk.temp.enabled": ephemeral_disk_localssd_enabled},
            ]

            config_settings.extend(reset_install_settings)

            err_msg = (
                "Validation failed. "
                "Please ensure that storagepools are not being used. "
                "Unable to perform disable Azure Container Storage operation. "
                "Resetting cluster state."
            )

            if storage_pool_type != CONST_ACSTOR_ALL:
                err_msg = (
                    "Validation failed. "
                    f"Please ensure that storagepools of type {storage_pool_type} are not being used. "
                    f"Unable to perform disable Azure Container Storage operation. "
                    "Resetting cluster state."
                )

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
                "Validation failed. Unable to perform Azure Container Storage operation. Resetting cluster state."
            ) from ex

    # Step 2: If the extension is installed and validation succeeded or skipped,
    # if we want to uninstall Azure Container Storage completely, then call
    # delete_k8s_extension. Else, if we want to disable a storagepool type,
    # we will perform another update_k8s_extension operation on the cluster.

    if storage_pool_type == CONST_ACSTOR_ALL:
        # Uninstallation operation
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

            if not no_wait_delete_op:
                LongRunningOperation(cmd.cli_ctx)(delete_op_result)
        except Exception as delete_ex:
            raise UnknownError(
                "Failure observed while disabling Azure Container Storage."
            ) from delete_ex

        logger.warning("Azure Container Storage has been disabled.")

        # Revoke role assignments irrespective of whether ElasticSAN
        # type was enabled on the cluster to handle older clusters where
        # the role assignments were done for all storagepool type during
        # installation of Azure Container Storage.
        perform_role_operations_on_managed_rg(
            cmd,
            subscription_id,
            node_resource_group,
            kubelet_identity_object_id,
            False
        )
    else:
        # Disabling a particular type of storagepool.
        if storage_pool_type == CONST_STORAGE_POOL_TYPE_AZURE_DISK:
            azure_disk_enabled = False
        elif storage_pool_type == CONST_STORAGE_POOL_TYPE_ELASTIC_SAN:
            elastic_san_enabled = False
        elif storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK:
            if storage_pool_option == CONST_STORAGE_POOL_OPTION_NVME:
                ephemeral_disk_nvme_enabled = False
            elif storage_pool_option == CONST_STORAGE_POOL_OPTION_SSD:
                ephemeral_disk_localssd_enabled = False
            elif storage_pool_option == CONST_ACSTOR_ALL:
                ephemeral_disk_nvme_enabled = False
                ephemeral_disk_localssd_enabled = False

        config_settings = [
            {"global.cli.storagePool.disable.validation": False},
            {"global.cli.storagePool.disable.type": storage_pool_type},
            {"global.cli.storagePool.disable.active": True},
            {"global.cli.storagePool.disable.diskType": pool_option.lower()},
            # Set these values to ensure cluster state incase of
            # a cluster where cli operation has not yet run or older
            # version of charts were installed.
            {"global.cli.storagePool.azureDisk.enabled": azure_disk_enabled},
            {"global.cli.storagePool.elasticSan.enabled": elastic_san_enabled},
            {"global.cli.storagePool.ephemeralDisk.nvme.enabled": ephemeral_disk_nvme_enabled},
            {"global.cli.storagePool.ephemeralDisk.temp.enabled": ephemeral_disk_localssd_enabled},
        ]

        config_settings.extend(reset_install_settings)

        # Define the new resource values for ioEngine and hugepages.
        resource_args = get_desired_resource_value_args(
            storage_pool_type,
            storage_pool_option,
            current_core_value,
            is_azureDisk_enabled,
            is_elasticSan_enabled,
            is_ephemeralDisk_localssd_enabled,
            is_ephemeralDisk_nvme_enabled,
            None,
            False,
        )
        config_settings.extend(resource_args)
        # Creating the set of config settings which
        # are required to demarcate that the disabling
        # process is completed. This config variable
        # will be used after the disabling operation is completed.
        update_settings = [
            {"global.cli.activeControl": True},
            {"global.cli.storagePool.disable.validation": False},
            {"global.cli.storagePool.disable.type": ""},
            {"global.cli.storagePool.disable.active": False},
            {"global.cli.storagePool.disable.diskType": ""},
        ]

        update_settings.extend(reset_install_settings)
        disable_op_failure = False
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

            # Revoke role assignments if we are disabling ElasticSAN storagepool type.
            if storage_pool_type == CONST_STORAGE_POOL_TYPE_ELASTIC_SAN and is_elasticSan_enabled:
                perform_role_operations_on_managed_rg(
                    cmd,
                    subscription_id,
                    node_resource_group,
                    kubelet_identity_object_id,
                    False
                )
        except Exception as disable_ex:  # pylint: disable=broad-except
            logger.error(
                "Failure observed while disabling Azure Container Storage storagepool type: %s.\nError: %s"
                "Resetting cluster state.", storage_pool_type, disable_ex
            )

            # If disabling type of storagepool in Azure Container Storage failed,
            # define the existing resource values for ioEngine and hugepages for
            # resetting the cluster state.
            resource_args = get_current_resource_value_args(
                is_azureDisk_enabled,
                is_elasticSan_enabled,
                is_ephemeralDisk_localssd_enabled,
                is_ephemeralDisk_nvme_enabled,
                current_core_value,
            )

            update_settings.extend(resource_args)
            # Revert back to storagepool type states which was supposed to disabled.
            azure_disk_enabled = is_azureDisk_enabled
            elastic_san_enabled = is_elasticSan_enabled
            ephemeral_disk_nvme_enabled = is_ephemeralDisk_nvme_enabled
            ephemeral_disk_localssd_enabled = is_ephemeralDisk_localssd_enabled
            disable_op_failure = True

        # Set the types of storagepool type states in the cluster
        # based on whether the previous operation succeeded or failed.
        update_settings.extend(
            [
                {"global.cli.storagePool.azureDisk.enabled": azure_disk_enabled},
                {"global.cli.storagePool.elasticSan.enabled": elastic_san_enabled},
                {"global.cli.storagePool.ephemeralDisk.nvme.enabled": ephemeral_disk_nvme_enabled},
                {"global.cli.storagePool.ephemeralDisk.temp.enabled": ephemeral_disk_localssd_enabled},
            ]
        )
        # Since we are just resetting the cluster state,
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
