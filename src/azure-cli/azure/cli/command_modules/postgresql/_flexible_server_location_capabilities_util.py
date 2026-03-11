# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long, import-outside-toplevel, raise-missing-from
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.core.paging import ItemPaged
from ._client_factory import cf_postgres_flexible_location_capabilities, cf_postgres_flexible_server_capabilities
from collections import defaultdict


def get_postgres_location_capability_info(cmd, location, is_offer_restriction_check_required=False):
    list_location_capability_client = cf_postgres_flexible_location_capabilities(cmd.cli_ctx, '_')
    list_location_capability_result = list_location_capability_client.list(location)
    return _postgres_parse_list_capability(list_location_capability_result, is_offer_restriction_check_required)


def get_postgres_server_capability_info(cmd, resource_group, server_name, is_offer_restriction_check_required=False):
    list_server_capability_client = cf_postgres_flexible_server_capabilities(cmd.cli_ctx, '_')
    list_server_capability_result = list_server_capability_client.list(resource_group_name=resource_group, server_name=server_name)
    return _postgres_parse_list_capability(list_server_capability_result, is_offer_restriction_check_required)


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


# pylint: disable=too-many-locals
def _postgres_parse_list_capability(result, is_offer_restriction_check_required=False):
    result = _get_list_from_paged_response(result)

    if not result:
        raise InvalidArgumentValueError("No available SKUs in this location")

    supported_features = result[0].supported_features if result[0].supported_features is not None else []
    offer_restricted = [feature for feature in supported_features if feature.name == "OfferRestricted"]
    restricted = offer_restricted[0].status if offer_restricted else None
    zone_redundant = [feature for feature in supported_features if feature.name == "ZoneRedundantHa"]
    geo_backup = [feature for feature in supported_features if feature.name == "GeoBackup"]
    autonomous_tuning = [feature for feature in supported_features if feature.name == "IndexTuning"]

    # Update once capability calls are corrected for each command
    if restricted == "Enabled" and not is_offer_restriction_check_required:
        raise InvalidArgumentValueError("The location is restricted from performing this operation.")

    if restricted != "Disabled" and not is_offer_restriction_check_required:
        raise InvalidArgumentValueError("No available SKUs in this location.")

    single_az = zone_redundant[0].status != "Enabled" if zone_redundant else True
    geo_backup_supported = geo_backup[0].status == "Enabled" if geo_backup else False
    autonomous_tuning_supported = autonomous_tuning[0].status == "Enabled" if autonomous_tuning else False

    tiers = result[0].supported_server_editions
    tiers_dict = {}
    for tier_info in tiers:
        tier_name = tier_info.name
        tier_dict = {}

        skus = set()
        zones = set()

        for sku in tier_info.supported_server_skus:
            skus.add(sku.name)
            for zone in sku.supported_zones:
                zones.add(zone)

        storage_sizes = set()
        for storage_edition in tier_info.supported_storage_editions:
            if storage_edition.name == "ManagedDisk":
                for storage_info in storage_edition.supported_storage_mb:
                    storage_sizes.add(int(storage_info.storage_size_mb // 1024))
                tier_dict["storage_edition"] = storage_edition
            elif storage_edition.name == "ManagedDiskV2" and len(storage_edition.supported_storage_mb) > 0:
                tier_dict["supported_storageV2_size"] = int(storage_edition.supported_storage_mb[0].storage_size_mb // 1024)
                tier_dict["supported_storageV2_size_max"] = int(storage_edition.supported_storage_mb[0].maximum_storage_size_mb // 1024)
                tier_dict["supported_storageV2_iops"] = storage_edition.supported_storage_mb[0].supported_iops
                tier_dict["supported_storageV2_iops_max"] = storage_edition.supported_storage_mb[0].supported_maximum_iops
                tier_dict["supported_storageV2_throughput"] = storage_edition.supported_storage_mb[0].supported_throughput
                tier_dict["supported_storageV2_throughput_max"] = storage_edition.supported_storage_mb[0].supported_maximum_throughput

        tier_dict["skus"] = skus
        tier_dict["storage_sizes"] = storage_sizes
        tiers_dict[tier_name] = tier_dict

    versions = set()
    for version in result[0].supported_server_versions:
        versions.add(version.name)

    supported_server_versions = defaultdict(list)
    for version in result[0].supported_server_versions:
        supported_server_versions[version.name] = version.supported_versions_to_upgrade

    return {
        'sku_info': tiers_dict,
        'single_az': single_az,
        'geo_backup_supported': geo_backup_supported,
        'zones': zones,
        'server_versions': versions,
        'supported_server_versions': supported_server_versions,
        'autonomous_tuning_supported': autonomous_tuning_supported
    }


def _get_list_from_paged_response(obj_list):
    return list(obj_list) if isinstance(obj_list, ItemPaged) else obj_list
