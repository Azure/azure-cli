#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core._util import CLIError

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
    cloud_args = cloud_config or locals()
    cloud_to_add = Cloud(cloud_name, endpoints={}, suffixes={})
    for arg in cloud_args:
        if arg.startswith('endpoint_') and cloud_args[arg]:
            cloud_to_add.endpoints[arg.replace('endpoint_', '')] = cloud_args[arg]
        elif arg.startswith('suffix_') and cloud_args[arg]:
            cloud_to_add.suffixes[arg.replace('suffix_', '')] = cloud_args[arg]
    try:
        add_cloud(cloud_to_add)
    except CloudAlreadyRegisteredException as e:
        raise CLIError(e)

def unregister_cloud(cloud_name):
    try:
        return remove_cloud(cloud_name)
    except CloudNotRegisteredException as e:
        raise CLIError(e)
    except CannotUnregisterCloudException as e:
        raise CLIError(e)
