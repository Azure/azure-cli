#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.mgmt.redis.models import (
    ImportRDBParameters,
    ExportRDBParameters,
    RedisCreateOrUpdateParameters,
)

def cli_redis_export(client, resource_group_name, name, prefix, container, file_format=None):
    # pylint:disable=too-many-arguments
    parameters = ExportRDBParameters(prefix, container, file_format)
    return client.export(resource_group_name, name, parameters)

def cli_redis_import_method(client, resource_group_name, name, file_format, files):
    parameters = ImportRDBParameters(files, file_format)
    return client.import_method(resource_group_name, name, files, parameters)

def cli_redis_update_settings(client, resource_group_name, name, redis_configuration):
    existing = client.get(resource_group_name, name)
    existing.redis_configuration.update(redis_configuration)

    # Due to swagger/mgmt SDK quirkiness, we have to manually copy over
    # the resource retrieved to a create_or_update_parameters object
    update_params = RedisCreateOrUpdateParameters(
        existing.location,
        existing.sku,
        existing.tags,
        existing.redis_version,
        existing.redis_configuration,
        existing.enable_non_ssl_port,
        existing.tenant_settings,
        existing.shard_count,
        existing.subnet_id,
        existing.static_ip,
        )
    return client.create_or_update(resource_group_name, name, parameters=update_params)
