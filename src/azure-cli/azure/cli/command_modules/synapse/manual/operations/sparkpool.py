# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-argument, line-too-long, too-many-locals
from azure.cli.core.util import sdk_no_wait, read_file_content
from azure.mgmt.synapse.models import BigDataPoolResourceInfo, AutoScaleProperties, AutoPauseProperties, LibraryRequirements, NodeSizeFamily, LibraryInfo, SparkConfigProperties
from .._client_factory import cf_synapse_client_workspace_factory
from .artifacts import get_workspace_package
from pathlib import Path


# Synapse sparkpool
def get_spark_pool(cmd, client, resource_group_name, workspace_name, spark_pool_name):
    return client.get(resource_group_name, workspace_name, spark_pool_name)


def create_spark_pool(cmd, client, resource_group_name, workspace_name, spark_pool_name,
                      spark_version, node_size, node_count,
                      node_size_family=NodeSizeFamily.memory_optimized.value, enable_auto_scale=None,
                      min_node_count=None, max_node_count=None, spark_config_file_path=None,
                      enable_auto_pause=None, delay=None, spark_events_folder="/events",
                      spark_log_folder="/logs", tags=None, no_wait=False):

    workspace_client = cf_synapse_client_workspace_factory(cmd.cli_ctx)
    workspace_object = workspace_client.get(resource_group_name, workspace_name)
    location = workspace_object.location

    big_data_pool_info = BigDataPoolResourceInfo(location=location, spark_version=spark_version, node_size=node_size,
                                                 node_count=node_count, node_size_family=node_size_family,
                                                 spark_events_folder=spark_events_folder,
                                                 spark_log_folder=spark_log_folder, tags=tags)

    big_data_pool_info.auto_scale = AutoScaleProperties(enabled=enable_auto_scale, min_node_count=min_node_count,
                                                        max_node_count=max_node_count)

    big_data_pool_info.auto_pause = AutoPauseProperties(enabled=enable_auto_pause,
                                                        delay_in_minutes=delay)

    if spark_config_file_path:
        filename = Path(spark_config_file_path).stem
        try:
            with open(spark_config_file_path, 'r') as stream:
                content = stream.read()
        except:
            from azure.cli.core.azclierror import InvalidArgumentValueError
            err_msg = 'Spark config file path is invalid'
            raise InvalidArgumentValueError(err_msg)
        big_data_pool_info.spark_config_properties = SparkConfigProperties(content=content,
                                                                           filename=filename)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, workspace_name, spark_pool_name,
                       big_data_pool_info)


def update_spark_pool(cmd, client, resource_group_name, workspace_name, spark_pool_name,
                      node_size=None, node_count=None, enable_auto_scale=None,
                      min_node_count=None, max_node_count=None,
                      enable_auto_pause=None, delay=None,
                      library_requirements=None, spark_config_file_path=None,
                      package_action=None, package=None,
                      tags=None, force=False, no_wait=False):
    existing_spark_pool = client.get(resource_group_name, workspace_name, spark_pool_name)

    if node_size:
        existing_spark_pool.node_size = node_size
    if node_count:
        existing_spark_pool.node_count = node_count

    if library_requirements:
        library_requirements_content = read_file_content(library_requirements)
        existing_spark_pool.library_requirements = LibraryRequirements(filename=library_requirements,
                                                                       content=library_requirements_content)
    if tags:
        existing_spark_pool.tags = tags

    if existing_spark_pool.auto_scale is not None:
        if enable_auto_scale is not None:
            existing_spark_pool.auto_scale.enabled = enable_auto_scale
        if min_node_count:
            existing_spark_pool.auto_scale.min_node_count = min_node_count
        if max_node_count:
            existing_spark_pool.auto_scale.max_node_count = max_node_count
    else:
        existing_spark_pool.auto_scale = AutoScaleProperties(enabled=enable_auto_scale, min_node_count=min_node_count,
                                                             max_node_count=max_node_count)

    if existing_spark_pool.auto_pause is not None:
        if enable_auto_pause is not None:
            existing_spark_pool.auto_pause.enabled = enable_auto_pause
        if delay:
            existing_spark_pool.auto_pause.delay_in_minutes = delay
    else:
        existing_spark_pool.auto_pause = AutoPauseProperties(enabled=enable_auto_pause,
                                                             delay_in_minutes=delay)

    if package_action and package:
        if package_action == "Add":
            if existing_spark_pool.custom_libraries is None:
                existing_spark_pool.custom_libraries = []
            for item in package:
                package_get = get_workspace_package(cmd, workspace_name, item)
                library = LibraryInfo(name=package_get.name, type=package_get.properties.type,
                                      path=package_get.properties.path, container_name=package_get.properties.container_name,
                                      uploaded_timestamp=package_get.properties.uploaded_timestamp)
                existing_spark_pool.custom_libraries.append(library)
        if package_action == "Remove":
            existing_spark_pool.custom_libraries = [library for library in existing_spark_pool.custom_libraries if library.name not in package]

    if spark_config_file_path:
        filename = Path(spark_config_file_path).stem
        try:
            with open(spark_config_file_path, 'r') as stream:
                content = stream.read()
        except:
            from azure.cli.core.azclierror import InvalidArgumentValueError
            err_msg = 'Spark config file path is invalid'
            raise InvalidArgumentValueError(err_msg)
        existing_spark_pool.spark_config_properties = SparkConfigProperties(content=content,
                                                                            filename=filename)
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, workspace_name, spark_pool_name,
                       existing_spark_pool, force=force)


def delete_spark_pool(cmd, client, resource_group_name, workspace_name, spark_pool_name, no_wait=False):
    return sdk_no_wait(no_wait, client.begin_delete, resource_group_name, workspace_name, spark_pool_name)
