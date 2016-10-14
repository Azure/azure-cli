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

 # pylint: disable=unused-argument
def register_cloud(cloud_name,
                   endpoint_management=None,
                   endpoint_resource_manager=None,
                   endpoint_sql_management=None,
                   endpoint_gallery=None,
                   endpoint_active_directory=None,
                   endpoint_active_directory_resource_id=None,
                   endpoint_active_directory_graph_resource_id=None,
                   param_sql_server_hostname_suffix=None,
                   param_storage_endpoint_suffix=None,
                   param_keyvault_dns_suffix=None,
                   param_azure_datalake_store_file_system_endpoint_suffix=None,
                   param_azure_datalake_analytics_catalog_and_job_endpoint_suffix=None):
    method_args = locals()
    cloud_to_add = Cloud(cloud_name, endpoints={}, params={})
    for arg in method_args:
        if arg.startswith('endpoint_') and method_args[arg]:
            cloud_to_add.endpoints[arg.replace('endpoint_', '')] = method_args[arg]
        elif arg.startswith('param_') and method_args[arg]:
            cloud_to_add.params[arg.replace('param_', '')] = method_args[arg]
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
