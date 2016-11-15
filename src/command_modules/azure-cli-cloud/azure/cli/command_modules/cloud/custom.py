# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core._util import CLIError, to_snake_case

from azure.cli.core.cloud import (Cloud,
                                  get_clouds,
                                  get_cloud,
                                  remove_cloud,
                                  add_cloud,
                                  CloudAlreadyRegisteredException,
                                  CloudNotRegisteredException,
                                  CannotUnregisterCloudException)

def list_clouds():
    return get_clouds()

def show_cloud(cloud_name):
    try:
        return get_cloud(cloud_name)
    except CloudNotRegisteredException as e:
        raise CLIError(e)

 # pylint: disable=unused-argument,too-many-arguments
def register_cloud(cloud_name,
                   cloud_config=None,
                   endpoint_management=None,
                   endpoint_resource_manager=None,
                   endpoint_sql_management=None,
                   endpoint_gallery=None,
                   endpoint_active_directory=None,
                   endpoint_active_directory_resource_id=None,
                   endpoint_active_directory_graph_resource_id=None,
                   suffix_sql_server_hostname=None,
                   suffix_storage_endpoint=None,
                   suffix_keyvault_dns=None,
                   suffix_azure_datalake_store_file_system_endpoint=None,
                   suffix_azure_datalake_analytics_catalog_and_job_endpoint=None):
    if cloud_config:
        # Using JSON format so convert the keys to snake case
        for key in cloud_config:
            cloud_config[to_snake_case(key)] = cloud_config.pop(key)
        cloud_args = cloud_config
    else:
        cloud_args = locals()
    c = Cloud(cloud_name)
    for arg in cloud_args:
        if arg.startswith('endpoint_') and cloud_args[arg]:
            setattr(c.endpoints, arg.replace('endpoint_', ''), cloud_args[arg])
        elif arg.startswith('suffix_') and cloud_args[arg]:
            setattr(c.suffixes, arg.replace('suffix_', ''), cloud_args[arg])
    try:
        add_cloud(c)
    except CloudAlreadyRegisteredException as e:
        raise CLIError(e)

def unregister_cloud(cloud_name):
    try:
        return remove_cloud(cloud_name)
    except CloudNotRegisteredException as e:
        raise CLIError(e)
    except CannotUnregisterCloudException as e:
        raise CLIError(e)
