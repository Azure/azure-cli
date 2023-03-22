# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long, import-outside-toplevel, raise-missing-from
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.core.paging import ItemPaged
from ._client_factory import cf_postgres_flexible_location_capabilities


def get_postgres_location_capability_info(cmd, location, server_name=None):
    list_location_capability_client = cf_postgres_flexible_location_capabilities(cmd.cli_ctx, '_')
    params = {'serverName': server_name} if server_name else None
    list_location_capability_result = list_location_capability_client.execute(location, params=params)
    return _postgres_parse_list_location_capability(list_location_capability_result)


def _postgres_parse_list_location_capability(result):
    result = _get_list_from_paged_response(result)

    if not result:
        raise InvalidArgumentValueError("No available SKUs in this location")

    single_az = 'ZoneRedundant' not in result[0].supported_ha_mode
    geo_backup_supported = result[0].geo_backup_supported

    tiers = result[0].supported_flexible_server_editions
    tiers_dict = {}
    for tier_info in tiers:
        tier_name = tier_info.name
        tier_dict = {}

        skus = set()
        versions = set()
        for version in tier_info.supported_server_versions:
            versions.add(version.name)
            for vcores in version.supported_vcores:
                skus.add(vcores.name)
        tier_dict["skus"] = skus
        tier_dict["versions"] = versions

        storage_info = tier_info.supported_storage_editions[0]
        storage_sizes = set()
        for size in storage_info.supported_storage_mb:
            storage_sizes.add(int(size.storage_size_mb // 1024))
        tier_dict["storage_sizes"] = storage_sizes

        tiers_dict[tier_name] = tier_dict

    zones = set()
    for zoneInfo in result:
        zone = zoneInfo.zone
        zones.add(zone)

    return {'sku_info': tiers_dict,
            'single_az': single_az,
            'geo_backup_supported': geo_backup_supported,
            'zones': zones}


def _get_list_from_paged_response(obj_list):
    return list(obj_list) if isinstance(obj_list, ItemPaged) else obj_list
