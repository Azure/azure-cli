# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument
from knack.util import CLIError, to_snake_case

from azure.cli.core.cloud import (Cloud,
                                  get_clouds,
                                  get_cloud,
                                  remove_cloud,
                                  add_cloud,
                                  _get_cloud_name,
                                  switch_active_cloud,
                                  update_cloud,
                                  get_active_cloud_name,
                                  cloud_is_registered,
                                  CloudAlreadyRegisteredException,
                                  CloudNotRegisteredException,
                                  CannotUnregisterCloudException)


def list_clouds(cmd):
    return get_clouds(cmd.cli_ctx)


def show_cloud(cmd, cloud_name=None):
    if not cloud_name:
        cloud_name = cmd.cli_ctx.cloud.name
    try:
        return get_cloud(cmd.cli_ctx, cloud_name)
    except CloudNotRegisteredException as e:
        raise CLIError(e)


def _build_cloud(cli_ctx, cloud_name, cloud_config=None, cloud_args=None):
    from msrestazure.azure_cloud import _populate_from_metadata_endpoint, MetadataEndpointError
    from azure.cli.core.cloud import CloudEndpointNotSetException
    if cloud_config:
        # Using JSON format so convert the keys to snake case
        cloud_args = {to_snake_case(k): v for k, v in cloud_config.items()}
    c = Cloud(cloud_name)
    c.profile = cloud_args.get('profile', None)
    try:
        endpoints = cloud_args['endpoints']
        for arg in endpoints:
            setattr(c.endpoints, to_snake_case(arg), endpoints[arg])
    except KeyError:
        pass
    try:
        suffixes = cloud_args['suffixes']
        for arg in suffixes:
            setattr(c.suffixes, to_snake_case(arg), suffixes[arg])
    except KeyError:
        pass

    for arg in cloud_args:
        if arg.startswith('endpoint_') and cloud_args[arg] is not None:
            setattr(c.endpoints, arg.replace('endpoint_', ''), cloud_args[arg])
        elif arg.startswith('suffix_') and cloud_args[arg] is not None:
            setattr(c.suffixes, arg.replace('suffix_', ''), cloud_args[arg])

    try:
        arm_endpoint = c.endpoints.resource_manager
    except CloudEndpointNotSetException:
        arm_endpoint = None
    try:
        _populate_from_metadata_endpoint(c, arm_endpoint)
    except MetadataEndpointError as err:
        raise CLIError(err)
    required_endpoints = {'resource_manager': '--endpoint-resource-manager',
                          'active_directory': '--endpoint-active-directory',
                          'active_directory_resource_id': '--endpoint-active-directory-resource-id',
                          'active_directory_graph_resource_id': '--endpoint-active-directory-graph-resource-id'}
    missing_endpoints = [e_param for e_name, e_param in required_endpoints.items()
                         if not c.endpoints.has_endpoint_set(e_name)]
    if missing_endpoints and not cloud_is_registered(cli_ctx, cloud_name):
        raise CLIError("The following endpoints are required for the CLI to function and were not specified on the "
                       "command line, in the cloud config or could not be autodetected.\n"
                       "Specify them on the command line or through the cloud config file:\n"
                       "{}".format(', '.join(missing_endpoints)))
    return c


def register_cloud(cmd,
                   cloud_name,
                   cloud_config=None,
                   profile=None,
                   endpoint_management=None,
                   endpoint_resource_manager=None,
                   endpoint_sql_management=None,
                   endpoint_gallery=None,
                   endpoint_active_directory=None,
                   endpoint_active_directory_resource_id=None,
                   endpoint_active_directory_graph_resource_id=None,
                   endpoint_active_directory_data_lake_resource_id=None,
                   endpoint_vm_image_alias_doc=None,
                   suffix_sql_server_hostname=None,
                   suffix_storage_endpoint=None,
                   suffix_keyvault_dns=None,
                   suffix_azure_datalake_store_file_system_endpoint=None,
                   suffix_azure_datalake_analytics_catalog_and_job_endpoint=None,
                   suffix_acr_login_server_endpoint=None):
    c = _build_cloud(cmd.cli_ctx, cloud_name, cloud_config=cloud_config,
                     cloud_args=locals())
    try:
        add_cloud(cmd.cli_ctx, c)
    except CloudAlreadyRegisteredException as e:
        raise CLIError(e)


def modify_cloud(cmd,
                 cloud_name=None,
                 cloud_config=None,
                 profile=None,
                 endpoint_management=None,
                 endpoint_resource_manager=None,
                 endpoint_sql_management=None,
                 endpoint_gallery=None,
                 endpoint_active_directory=None,
                 endpoint_active_directory_resource_id=None,
                 endpoint_active_directory_graph_resource_id=None,
                 endpoint_active_directory_data_lake_resource_id=None,
                 endpoint_vm_image_alias_doc=None,
                 suffix_sql_server_hostname=None,
                 suffix_storage_endpoint=None,
                 suffix_keyvault_dns=None,
                 suffix_azure_datalake_store_file_system_endpoint=None,
                 suffix_azure_datalake_analytics_catalog_and_job_endpoint=None,
                 suffix_acr_login_server_endpoint=None):
    if not cloud_name:
        cloud_name = cmd.cli_ctx.cloud.name
    c = _build_cloud(cmd.cli_ctx, cloud_name, cloud_config=cloud_config,
                     cloud_args=locals())
    try:
        update_cloud(cmd.cli_ctx, c)
    except CloudNotRegisteredException as e:
        raise CLIError(e)


def unregister_cloud(cmd, cloud_name):
    try:
        return remove_cloud(cmd.cli_ctx, cloud_name)
    except CloudNotRegisteredException as e:
        raise CLIError(e)
    except CannotUnregisterCloudException as e:
        raise CLIError(e)


def set_cloud(cmd, cloud_name, profile=None):
    try:
        cloud_name = _get_cloud_name(cmd.cli_ctx, cloud_name)
        switch_active_cloud(cmd.cli_ctx, cloud_name)
        if profile:
            modify_cloud(cmd, cloud_name=cloud_name, profile=profile)
    except CloudNotRegisteredException as e:
        raise CLIError(e)


def list_profiles(cmd, cloud_name=None, show_all=False):
    from azure.cli.core.profiles import API_PROFILES
    if not cloud_name:
        cloud_name = get_active_cloud_name(cmd.cli_ctx.cloud)
    return list(API_PROFILES)
