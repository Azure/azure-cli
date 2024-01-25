# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re

from azure.cli.command_modules.acs.azurecontainerstorage._consts import (
    CONST_ACSTOR_IO_ENGINE_LABEL_KEY,
    CONST_STORAGE_POOL_OPTION_NVME,
    CONST_STORAGE_POOL_SKU_PREMIUM_LRS,
    CONST_STORAGE_POOL_SKU_PREMIUM_ZRS,
    CONST_STORAGE_POOL_TYPE_ELASTIC_SAN,
    CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK,
)
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
)
from knack.log import get_logger


elastic_san_supported_skus = [
    CONST_STORAGE_POOL_SKU_PREMIUM_LRS,
    CONST_STORAGE_POOL_SKU_PREMIUM_ZRS,
]

logger = get_logger(__name__)


def validate_disable_azure_container_storage_params(
    storage_pool_type,
    is_extension_installed,
    storage_pool_name,
    storage_pool_sku,
    storage_pool_option,
    storage_pool_size,
    nodepool_list,
    is_azureDisk_enabled,
    is_elasticSan_enabled,
    is_ephemeralDisk_enabled,
    ephemeral_disk_type_installed,
):
    if not is_extension_installed:
        raise InvalidArgumentValueError(
            'Invalid usage of --disable-azure-container-storage. '
            'Azure Container Storage is not enabled on the cluster. '
        )

    if storage_pool_name is not None:
        raise MutuallyExclusiveArgumentError(
            'Conflicting flags. Cannot define --storage-pool-name value '
            'when --disable-azure-container-storage is set.'
        )

    if storage_pool_sku is not None:
        raise MutuallyExclusiveArgumentError(
            'Conflicting flags. Cannot define --storage-pool-sku value '
            'when --disable-azure-container-storage is set.'
        )

    if storage_pool_size is not None:
        raise MutuallyExclusiveArgumentError(
            'Conflicting flags. Cannot define --storage-pool-size value '
            'when --disable-azure-container-storage is set.'
        )

    if storage_pool_option is not None:
        raise MutuallyExclusiveArgumentError(
            'Conflicting flags. Cannot define --storage-pool-option value '
            'when --disable-azure-container-storage is set.'
        )

    if nodepool_list is not None:
        raise MutuallyExclusiveArgumentError(
            'Conflicting flags. Cannot define --azure-container-storage-nodepools value '
            'when --disable-azure-container-storage is set.'
        )

    if (storage_pool_type == CONST_STORAGE_POOL_TYPE_AZURE_DISK and \
       not is_azureDisk_enabled) or \
       (storage_pool_type == CONST_STORAGE_POOL_TYPE_ELASTIC_SAN and \
       not is_elasticSan_enabled) or \
       (storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK and \
       not is_ephemeralDisk_enabled):
        raise ArgumentUsageError(
            'Invalid --disable-azure-container-storage value. '
            'Azure Container Storage is not enabled for storagepool '
            f'type {storage_pool_type} in the cluster.'
        )


def validate_enable_azure_container_storage_params(
    storage_pool_type,
    is_extension_installed,
    storage_pool_name,
    storage_pool_sku,
    storage_pool_option,
    storage_pool_size,
    nodepool_list,
    agentpool_details,
    is_azureDisk_enabled,
    is_elasticSan_enabled,
    is_ephemeralDisk_localssd_enabled,
    is_ephemeralDisk_nvme_enabled,
):
    if storage_pool_name is not None:
        pattern = r'[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*'
        is_pool_name_valid = re.fullmatch(pattern, storage_pool_name)
        if not is_pool_name_valid:
            raise InvalidArgumentValueError(
                "Invalid --storage-pool-name value. "
                "Accepted values are lowercase alphanumeric characters, "
                "'-' or '.', and must start and end with an alphanumeric character.")

    if storage_pool_sku is not None:
        if storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK:
            raise ArgumentUsageError(
                'Cannot set --storage-pool-sku when --enable-azure-container-storage is ephemeralDisk.'
            )
        if (
            storage_pool_type == CONST_STORAGE_POOL_TYPE_ELASTIC_SAN and
            storage_pool_sku not in elastic_san_supported_skus
        ):
            supported_skus_str = ", ".join(elastic_san_supported_skus)
            raise ArgumentUsageError(
                'Invalid --storage-pool-sku value. '
                f'Supported value for --storage-pool-sku are {supported_skus_str} '
                'when --enable-azure-container-storage is set to elasticSan.'
            )

    if storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK:
        if storage_pool_option is None:
            raise ArgumentUsageError(
                'Cannot set --storage-pool-option when --enable-azure-container-storage is not ephemeralDisk.'
            )
        if storage_pool_option == CONST_STORAGE_POOL_OPTION_NVME:
            _validate_nodepools_for_ephemeral_nvme_storagepool(agentpool_details)

    else:
        if storage_pool_option is not None:
            raise RequiredArgumentMissingError(
                'Value of --storage-pool-option must be defined when --enable-azure-container-storage is set to ephemeralDisk.'
            )

    _validate_storage_pool_size(storage_pool_size,  storage_pool_type)

    if is_extension_installed:
        if nodepool_list is not None:
            raise ArgumentUsageError(
                'Cannot set --azure-container-storage-nodepools while using '
                '--enable-azure-container-storage to enable a type of storagepool '
                'in a cluster where Azure Container Storage is already installed.'
            )
        _validate_azure_container_storage_label_present(agentpool_details, storage_pool_type)

        if (is_azureDisk_enabled and \
           storage_pool_type == CONST_STORAGE_POOL_TYPE_AZURE_DISK) or \
           (is_elasticSan_enabled and \
           storage_pool_type == CONST_STORAGE_POOL_TYPE_ELASTIC_SAN):
            raise ArgumentUsageError(
                'Invalid --enable-azure-container-storage value. '
                'Azure Container Storage is already enabled for storagepool type '
                f'{storage_pool_type} in the cluster. '
            )

        if (is_ephemeralDisk_localssd_enabled or is_ephemeralDisk_nvme_enabled) and \
           storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK:
            ephemeral_disk_type_installed = CONST_STORAGE_POOL_OPTION_SSD if \
                                            is_ephemeralDisk_localssd_enabled else \
                                            CONST_STORAGE_POOL_OPTION_NVME 
            raise ArgumentUsageError(
                'Invalid --enable-azure-container-storage value. '
                'Azure Container Storage is already enabled for storagepool type '
                f'{CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK} and option {ephemeral_disk_type_installed} '
                'in the cluster.'
            )
    else:
        _validate_nodepool_names(nodepool_list, agentpool_details)


# _Validate_storage_pool_size validates that the storage_pool_size is
# string of a combination of a float number immediately followed by
# Ti or Gi e.g. 2Ti, 512Gi, 1.5Ti. The function also validates that the
# minimum storage pool size for an elastic san storagepool should be 1Ti.
def _validate_storage_pool_size(storage_pool_size, storage_pool_type):
    if storage_pool_size is not None:
        pattern = r'^\d+(\.\d+)?[GT]i$'
        match = re.match(pattern, storage_pool_size)
        if match is None:
            raise ArgumentUsageError(
                'Value for --storage-pool-size should be defined '
                'with size followed by Gi or Ti e.g. 512Gi or 2Ti.'
            )
        if storage_pool_type == CONST_STORAGE_POOL_TYPE_ELASTIC_SAN:
            pool_size_qty = float(storage_pool_size[:-2])
            pool_size_unit = storage_pool_size[-2:]

            if (
                (pool_size_unit == "Gi" and pool_size_qty < 1024) or
                (pool_size_unit == "Ti" and pool_size_qty < 1)
            ):
                raise ArgumentUsageError(
                    'Value for --storage-pool-size must be at least 1Ti when '
                    '--enable-azure-container-storage is elasticSan.'
                )

        elif storage_pool_type == CONST_STORAGE_POOL_TYPE_EPHEMERAL_DISK:
            logger.warning(
                'Storage pools using Ephemeral disk use all capacity available on the local device. '
                ' --storage-pool-size will be ignored.'
            )


# _validate_nodepool_names validates that the nodepool_list is a comma separated
# string consisting of valid nodepool names i.e. a lower alphanumeric
# characters and the first character should be lowercase letter.
def _validate_nodepool_names(nodepool_names, agentpool_details):
    pattern = r'^[a-z][a-z0-9]*(?:,[a-z][a-z0-9]*)*$'
    if re.fullmatch(pattern, nodepool_names) is None:
        raise InvalidArgumentValueError(
            "Invalid --azure-container-storage-nodepools value. "
            "Accepted value is a comma separated string of valid nodepool "
            "names without any spaces.\nA valid nodepool name may only contain lowercase "
            "alphanumeric characters and must begin with a lowercase letter."
        )

    agentpool_names = []
    for details in agentpool_details:
        agentpool_names.append(details.get("name"))

    nodepool_list = nodepool_names.split(',')
    for nodepool in nodepool_list:
        if nodepool not in agentpool_names:
            if len(agentpool_names) > 1:
                raise InvalidArgumentValueError(
                    f'Nodepool: {nodepool} not found. '
                    'Please provide a comma separated string of existing nodepool names '
                    'in --azure-container-storage-nodepools.'
                    f"\nNodepools available in the cluster are: {', '.join(agentpool_names)}."
                    '\nAborting installation of Azure Container Storage.'
                )
            raise InvalidArgumentValueError(
                f'Nodepool: {nodepool} not found. '
                'Please provide a comma separated string of existing nodepool names '
                'in --azure-container-storage-nodepools.'
                f'\nNodepool available in the cluster is: {agentpool_names[0]}.'
                '\nAborting installation of Azure Container Storage.'
            )


def _validate_azure_container_storage_label_present(agentpool_details, pool_type):
    for agentpool in agentpool_details:
        node_labels = agentpool.get("node_labels")
        if node_labels is not None and \
           node_labels.get(CONST_ACSTOR_IO_ENGINE_LABEL_KEY) is not None:
           break
    else:
        raise ArgumentUsageError(
            f'Cannot enable storagepool of type {pool_type} for azure container storage since '
            'none of the nodepools in the cluster are labelled for Azure Container Storage.'
        )


def _validate_nodepools_for_ephemeral_nvme_storagepool(agentpool_details):
    for agentpool in agentpool_details:
        vm_size = agentpool.get("vm_size")
        if vm_size is not None and vm_size.lower().startswith('standard_l'):
            break
    else:
        raise ArgumentUsageError(
            f'Cannot set --storage-pool-option as {CONST_STORAGE_POOL_OPTION_NVME} '
            'as no supporting nodepool found which can support ephemeral NVMe disk.'
        )
