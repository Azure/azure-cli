# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long, import-outside-toplevel, raise-missing-from
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.core.paging import ItemPaged
from ._client_factory import cf_postgres_flexible_location_capabilities, cf_postgres_flexible_server_capabilities


def get_postgres_location_capability_info(cmd, location):
    list_location_capability_client = cf_postgres_flexible_location_capabilities(cmd.cli_ctx, '_')
    list_location_capability_result = list_location_capability_client.execute(location)
    return _postgres_parse_list_capability(list_location_capability_result)


def get_postgres_server_capability_info(cmd, resource_group, server_name):
    list_server_capability_client = cf_postgres_flexible_server_capabilities(cmd.cli_ctx, '_')
    list_server_capability_result = list_server_capability_client.list(resource_group_name=resource_group, server_name=server_name)
    return _postgres_parse_list_capability(list_server_capability_result)


def _postgres_parse_list_capability(result):
    result = _get_list_from_paged_response(result)

    if not result:
        raise InvalidArgumentValueError("No available SKUs in this location")

    if result[0].restricted == "Enabled":
        raise InvalidArgumentValueError("The location is restricted for provisioning of flexible servers. Please try using another region.")

    if result[0].restricted != "Disabled":
        raise InvalidArgumentValueError("No available SKUs in this location.")

    single_az = result[0].zone_redundant_ha_supported != "Enabled"
    geo_backup_supported = result[0].geo_backup_supported == "Enabled"

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
            for storage_info in storage_edition.supported_storage_mb:
                storage_sizes.add(int(storage_info.storage_size_mb // 1024))

        tier_dict["skus"] = skus
        tier_dict["storage_sizes"] = storage_sizes

        tiers_dict[tier_name] = tier_dict

    versions = set()
    for version in result[0].supported_server_versions:
        versions.add(version.name)

    return {'sku_info': tiers_dict,
            'single_az': single_az,
            'geo_backup_supported': geo_backup_supported,
            'zones': zones,
            'server_versions': versions
            }


def _get_list_from_paged_response(obj_list):
    return list(obj_list) if isinstance(obj_list, ItemPaged) else obj_list
