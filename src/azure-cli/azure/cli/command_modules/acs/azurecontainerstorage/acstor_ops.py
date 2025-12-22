# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import UnknownError
from azure.cli.core.commands import LongRunningOperation
from azure.cli.command_modules.acs.azurecontainerstorage._consts import (
    CONST_ACSTOR_ALL,
    CONST_ACSTOR_V1_K8S_EXTENSION_NAME,
    CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY,
    CONST_DISK_TYPE_PV_WITH_ANNOTATION,
    CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD,
    CONST_ACSTOR_V1_EXT_INSTALLATION_NAME,
    CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME,
    CONST_K8S_EXTENSION_CUSTOM_MOD_NAME,
    CONST_ACSTOR_EXT_INSTALLATION_NAME,
    CONST_ACSTOR_EXT_INSTALLATION_NAMESPACE,
    CONST_ACSTOR_K8S_EXTENSION_NAME,
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
    check_if_new_storagepool_creation_required,
    get_k8s_extension_module,
    get_current_resource_value_args,
    get_desired_resource_value_args,
    get_initial_resource_value_args,
    perform_role_operations_on_managed_rg,
    validate_storagepool_creation,
    should_delete_extension,
)
from knack.log import get_logger

logger = get_logger(__name__)


def perform_enable_azure_container_storage_v1(  # pylint: disable=too-many-statements,too-many-locals,too-many-branches
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
    ephemeral_disk_volume_type,
    ephemeral_disk_nvme_perf_tier,
    is_cluster_create,
    existing_ephemeral_disk_volume_type=CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY,
    existing_ephemeral_nvme_perf_tier=CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD,
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

    is_storagepool_create_op_required = check_if_new_storagepool_creation_required(
        storage_pool_type,
        ephemeral_disk_volume_type,
        ephemeral_disk_nvme_perf_tier,
        existing_ephemeral_disk_volume_type,
        existing_ephemeral_nvme_perf_tier,
        is_extension_installed,
        is_ephemeralDisk_nvme_enabled,
        is_ephemeralDisk_localssd_enabled,
    )

    config_settings = []
    azure_disk_enabled = is_azureDisk_enabled if is_extension_installed else False
    elastic_san_enabled = is_elasticSan_enabled if is_extension_installed else False
    ephemeral_disk_nvme_enabled = is_ephemeralDisk_nvme_enabled if is_extension_installed else False
    ephemeral_disk_localssd_enabled = is_ephemeralDisk_localssd_enabled if is_extension_installed else False
    # Step 3: Configure the storagepool parameters
    if is_storagepool_create_op_required:
        if storage_pool_name is None:
            storage_pool_name = storage_pool_type.lower()
            if storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK:
                storage_pool_name = storage_pool_type.lower() + "-" + storage_pool_option.lower()
        if storage_pool_size is None:
            storage_pool_size = CONST_STORAGE_POOL_DEFAULT_SIZE_ESAN if \
                storage_pool_type == CONST_STORAGE_POOL_TYPE_ELASTIC_SAN else \
                CONST_STORAGE_POOL_DEFAULT_SIZE

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
                {"global.cli.storagePool.install.name": storage_pool_name},
                {"global.cli.storagePool.install.size": storage_pool_size},
                {"global.cli.storagePool.install.type": storage_pool_type},
                {"global.cli.storagePool.install.diskType": epheremaldisk_type},
            ]
        )

    enable_ephemeral_bypass_annotation = (
        (ephemeral_disk_volume_type is None and
            existing_ephemeral_nvme_perf_tier.lower() == CONST_DISK_TYPE_PV_WITH_ANNOTATION.lower()) or
        (ephemeral_disk_volume_type is not None and
            ephemeral_disk_volume_type.lower() == CONST_DISK_TYPE_PV_WITH_ANNOTATION.lower())
    )

    if existing_ephemeral_nvme_perf_tier is None:
        existing_ephemeral_nvme_perf_tier = CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD
    if ephemeral_disk_nvme_perf_tier is None:
        ephemeral_disk_nvme_perf_tier = existing_ephemeral_nvme_perf_tier

    perf_tier_updated = False
    if existing_ephemeral_nvme_perf_tier.lower() != ephemeral_disk_nvme_perf_tier.lower():
        perf_tier_updated = True

    config_settings.extend(
        [
            {"global.cli.activeControl": True},
            {"global.cli.storagePool.install.create": is_storagepool_create_op_required},
            {"global.cli.storagePool.azureDisk.enabled": azure_disk_enabled},
            {"global.cli.storagePool.elasticSan.enabled": elastic_san_enabled},
            {"global.cli.storagePool.ephemeralDisk.nvme.enabled": ephemeral_disk_nvme_enabled},
            {"global.cli.storagePool.ephemeralDisk.temp.enabled": ephemeral_disk_localssd_enabled},
            {
                "global.cli.storagePool.ephemeralDisk.enableEphemeralBypassAnnotation":
                enable_ephemeral_bypass_annotation
            },
            {"global.cli.storagePool.ephemeralDisk.nvme.perfTier": ephemeral_disk_nvme_perf_tier},
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
            ephemeral_disk_nvme_perf_tier,
            current_core_value,
            is_azureDisk_enabled,
            is_elasticSan_enabled,
            is_ephemeralDisk_localssd_enabled,
            is_ephemeralDisk_nvme_enabled,
            perf_tier_updated,
            acstor_nodepool_skus,
            True,
        )

    else:
        resource_args = get_initial_resource_value_args(
            storage_pool_type,
            storage_pool_option,
            acstor_nodepool_skus,
            ephemeral_disk_nvme_perf_tier,
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

    update_after_exception = False
    delete_extension = False
    try:
        if is_extension_installed:
            result = k8s_extension_custom_mod.update_k8s_extension(
                cmd,
                client,
                resource_group,
                cluster_name,
                CONST_ACSTOR_V1_EXT_INSTALLATION_NAME,
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
                CONST_ACSTOR_V1_EXT_INSTALLATION_NAME,
                "managedClusters",
                CONST_ACSTOR_V1_K8S_EXTENSION_NAME,
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

            delete_extension = True
        else:
            if is_extension_installed:
                update_after_exception = True
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
                    existing_ephemeral_nvme_perf_tier,
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
                        update_settings.extend(
                            [
                                {"global.cli.storagePool.ephemeralDisk.nvme.enabled": False},
                                {
                                    "global.cli.storagePool.ephemeralDisk.nvme.perfTier":
                                    existing_ephemeral_nvme_perf_tier
                                },
                            ]
                        )
                    elif storage_pool_option == CONST_STORAGE_POOL_OPTION_SSD:
                        update_settings.append({"global.cli.storagePool.ephemeralDisk.temp.enabled": False})
                    enable_ephemeral_bypass_annotation = (
                        existing_ephemeral_disk_volume_type.lower() == CONST_DISK_TYPE_PV_WITH_ANNOTATION.lower()
                    )
                    update_settings.append(
                        {
                            "global.cli.storagePool.ephemeralDisk.enableEphemeralBypassAnnotation":
                            enable_ephemeral_bypass_annotation
                        }
                    )
            else:
                logger.error("AKS update to enable Azure Container Storage failed.\nError: %s", ex)
                delete_extension = True

    if delete_extension:
        k8s_extension_custom_mod.delete_k8s_extension(
            cmd,
            client,
            resource_group,
            cluster_name,
            CONST_ACSTOR_V1_EXT_INSTALLATION_NAME,
            "managedClusters",
            yes=True,
            no_wait=True,
        )
    elif is_storagepool_create_op_required or update_after_exception:
        k8s_extension_custom_mod.update_k8s_extension(
            cmd,
            client,
            resource_group,
            cluster_name,
            CONST_ACSTOR_V1_EXT_INSTALLATION_NAME,
            "managedClusters",
            configuration_settings=update_settings,
            yes=True,
            no_wait=True,
        )


def perform_disable_azure_container_storage_v1(  # pylint: disable=too-many-statements,too-many-locals,too-many-branches
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
    existing_ephemeral_disk_volume_type=CONST_DISK_TYPE_EPHEMERAL_VOLUME_ONLY,
    existing_ephemeral_nvme_perf_tier=CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD,
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
                storage_pool_option = CONST_STORAGE_POOL_OPTION_NVME
            elif is_ephemeralDisk_localssd_enabled:
                pool_option = CONST_STORAGE_POOL_OPTION_SSD.lower()
                storage_pool_option = CONST_STORAGE_POOL_OPTION_SSD

    # Step 1: Perform validation if accepted by user
    if perform_validation:
        config_settings = [
            {"global.cli.storagePool.disable.validation": True},
            {"global.cli.storagePool.disable.type": storage_pool_type},
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

        try:
            update_result = k8s_extension_custom_mod.update_k8s_extension(
                cmd,
                client,
                resource_group,
                cluster_name,
                CONST_ACSTOR_V1_EXT_INSTALLATION_NAME,
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
                CONST_ACSTOR_V1_EXT_INSTALLATION_NAME,
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
                CONST_ACSTOR_V1_EXT_INSTALLATION_NAME,
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
        updated_enable_ephemeral_bypass_annotation = (
            existing_ephemeral_disk_volume_type.lower() == CONST_DISK_TYPE_PV_WITH_ANNOTATION.lower()
        )
        updated_ephemeral_nvme_perf_tier = existing_ephemeral_nvme_perf_tier
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

            # If we are disabling ephemeral nvme, reset the following params:
            # 1. ephemeral_disk_volume_type
            # 2. ephemeral_disk_nvme_per_tier
            if not ephemeral_disk_nvme_enabled:
                updated_enable_ephemeral_bypass_annotation = False
                updated_ephemeral_nvme_perf_tier = CONST_EPHEMERAL_NVME_PERF_TIER_STANDARD

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
            {
                "global.cli.storagePool.ephemeralDisk.enableEphemeralBypassAnnotation":
                updated_enable_ephemeral_bypass_annotation
            },
            {"global.cli.storagePool.ephemeralDisk.nvme.perfTier": updated_ephemeral_nvme_perf_tier},
        ]

        config_settings.extend(reset_install_settings)

        # Define the new resource values for ioEngine and hugepages.
        resource_args = get_desired_resource_value_args(
            storage_pool_type,
            storage_pool_option,
            existing_ephemeral_nvme_perf_tier,
            current_core_value,
            is_azureDisk_enabled,
            is_elasticSan_enabled,
            is_ephemeralDisk_localssd_enabled,
            is_ephemeralDisk_nvme_enabled,
            False,
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
                CONST_ACSTOR_V1_EXT_INSTALLATION_NAME,
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
                existing_ephemeral_nvme_perf_tier,
                current_core_value,
            )

            update_settings.extend(resource_args)

            reset_enable_ephemeral_bypass_annotation = (
                existing_ephemeral_disk_volume_type.lower() == CONST_DISK_TYPE_PV_WITH_ANNOTATION.lower()
            )
            update_settings.extend(
                [
                    {
                        "global.cli.storagePool.ephemeralDisk.enableEphemeralBypassAnnotation":
                        reset_enable_ephemeral_bypass_annotation
                    },
                    {"global.cli.storagePool.ephemeralDisk.nvme.perfTier": existing_ephemeral_nvme_perf_tier},
                ]
            )

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
            CONST_ACSTOR_V1_EXT_INSTALLATION_NAME,
            "managedClusters",
            configuration_settings=update_settings,
            yes=True,
            no_wait=True,
        )

        if not disable_op_failure:
            logger.warning("Azure Container Storage storagepool type %s has been disabled.", storage_pool_type)


def perform_azure_container_storage_update(
    cmd,
    resource_group,
    cluster_name,
    storage_options_to_add,
    is_extension_installed=False,
    storage_options_to_remove=None,
):
    client_factory = get_k8s_extension_module(CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME)
    client = client_factory.cf_k8s_extension_operation(cmd.cli_ctx)
    k8s_extension_custom_mod = get_k8s_extension_module(CONST_K8S_EXTENSION_CUSTOM_MOD_NAME)

    delete_extension = should_delete_extension(storage_options_to_remove)
    delete_extension_auto = False

    if not delete_extension:
        config_settings = []

        storage_options_to_add = storage_options_to_add if isinstance(storage_options_to_add, (list, str)) else []
        storage_options_to_remove = storage_options_to_remove \
            if isinstance(storage_options_to_remove, (list, str)) else []

        if CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK in storage_options_to_remove:
            config_settings.append({"csiDriverConfigs.local-csi-driver.enabled": "False"})
        elif CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK in storage_options_to_add:
            config_settings.append({"csiDriverConfigs.local-csi-driver.enabled": "True"})

        if CONST_STORAGE_POOL_TYPE_ELASTIC_SAN in storage_options_to_remove:
            config_settings.append({"csiDriverConfigs.azuresan-csi-driver.enabled": "False"})
        elif CONST_STORAGE_POOL_TYPE_ELASTIC_SAN in storage_options_to_add:
            config_settings.append({"csiDriverConfigs.azuresan-csi-driver.enabled": "True"})

        try:
            if is_extension_installed:
                result = k8s_extension_custom_mod.update_k8s_extension(
                    cmd,
                    client,
                    resource_group,
                    cluster_name,
                    CONST_ACSTOR_EXT_INSTALLATION_NAME,
                    "managedClusters",
                    configuration_settings=config_settings,
                    yes=True,
                )
                op_text = "Azure Container Storage successfully updated"
            else:
                result = k8s_extension_custom_mod.create_k8s_extension(
                    cmd,
                    client,
                    resource_group,
                    cluster_name,
                    CONST_ACSTOR_EXT_INSTALLATION_NAME,
                    "managedClusters",
                    CONST_ACSTOR_K8S_EXTENSION_NAME,
                    auto_upgrade_minor_version=True,
                    release_train="stable",
                    scope="cluster",
                    release_namespace=CONST_ACSTOR_EXT_INSTALLATION_NAMESPACE,
                    configuration_settings=config_settings,
                )
                op_text = "Azure Container Storage successfully installed"
            long_op_result = LongRunningOperation(cmd.cli_ctx)(result)
            if long_op_result.provisioning_state == "Succeeded":
                logger.warning(op_text)
        except Exception as ex:     # pylint: disable=broad-except
            if is_extension_installed:
                logger.error("Azure Container Storage failed to update.\nError: %s.", ex)
            else:
                logger.error("Azure Container Storage failed to install.\nError: %s", ex)
                delete_extension_auto = True

    if delete_extension or delete_extension_auto:
        if delete_extension_auto:
            logger.warning("Cleaning up the cluster by disabling Azure Container Storage")
        try:
            delete_op_result = k8s_extension_custom_mod.delete_k8s_extension(
                cmd,
                client,
                resource_group,
                cluster_name,
                CONST_ACSTOR_EXT_INSTALLATION_NAME,
                "managedClusters",
                yes=True,
            )

            LongRunningOperation(cmd.cli_ctx)(delete_op_result)
            logger.warning("Azure Container Storage has been disabled.")
            if delete_extension_auto:
                logger.warning(
                    "Please retry enabling Azure Container Storage by running "
                    "`az aks update` along with `--enable-azure-container-storage`"
                )
        except Exception as delete_ex:
            raise UnknownError(
                "Failed to disable Azure Container Storage with error: %s" % delete_ex
            ) from delete_ex
