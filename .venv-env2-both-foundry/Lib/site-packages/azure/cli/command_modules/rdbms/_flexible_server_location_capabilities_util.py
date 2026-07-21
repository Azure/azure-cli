# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long, import-outside-toplevel, raise-missing-from


def get_performance_tiers_for_storage(storage_edition, storage_size):
    performance_tiers = []
    storage_size_mb = None if storage_size is None else storage_size * 1024
    for storage_info in storage_edition.supported_storage_mb:
        if storage_size_mb == storage_info.storage_size_mb:
            for performance_tier in storage_info.supported_iops_tiers:
                performance_tiers.append(performance_tier.name)
    return performance_tiers


def get_performance_tiers(storage_edition):
    performance_tiers = []
    for storage_info in storage_edition.supported_storage_mb:
        for performance_tier in storage_info.supported_iops_tiers:
            if performance_tier.name not in performance_tiers:
                performance_tiers.append(performance_tier.name)
    return performance_tiers
