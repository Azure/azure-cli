# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument
from azure.cli.core.util import CLIError, to_snake_case

from azure.cli.core.cloud import (Cloud,
                                  get_clouds,
                                  get_cloud,
                                  remove_cloud,
                                  add_cloud,
                                  switch_active_cloud,
                                  update_cloud,
                                  get_active_cloud_name,
                                  CloudAlreadyRegisteredException,
                                  CloudNotRegisteredException,
                                  CannotUnregisterCloudException)


# The exact API version doesn't matter too much right now. It just has to be YYYY-MM-DD format.
METADATA_ENDPOINT_SUFFIX = '/metadata/endpoints?api-version=2015-01-01'


def list_clouds():
    return get_clouds()


def show_cloud(cloud_name=None):
    if not cloud_name:
        cloud_name = get_active_cloud_name()
    try:
        return get_cloud(cloud_name)
    except CloudNotRegisteredException as e:
        raise CLIError(e)


def _populate_from_metadata_endpoint(cloud, arm_endpoint):
    endpoints_in_metadata = ['active_directory_graph_resource_id',
                             'active_directory_resource_id', 'active_directory']
    if not arm_endpoint or all([cloud.endpoints.has_endpoint_set(n) for n in endpoints_in_metadata]):
        return
    try:
        error_msg_fmt = "Unable to get endpoints from the cloud.\n{}"
        import requests
        metadata_endpoint = arm_endpoint + METADATA_ENDPOINT_SUFFIX
        response = requests.get(metadata_endpoint)
        if response.status_code == 200:
            metadata = response.json()
            if not cloud.endpoints.has_endpoint_set('gallery'):
                setattr(cloud.endpoints, 'gallery', metadata.get('galleryEndpoint'))
            if not cloud.endpoints.has_endpoint_set('active_directory_graph_resource_id'):
                setattr(cloud.endpoints, 'active_directory_graph_resource_id', metadata.get('graphEndpoint'))
            if not cloud.endpoints.has_endpoint_set('active_directory'):
                setattr(cloud.endpoints, 'active_directory', metadata['authentication'].get('loginEndpoint'))
            if not cloud.endpoints.has_endpoint_set('active_directory_resource_id'):
                setattr(cloud.endpoints, 'active_directory_resource_id', metadata['authentication']['audiences'][0])
        else:
            msg = 'Server returned status code {} for {}'.format(response.status_code, metadata_endpoint)
            raise CLIError(error_msg_fmt.format(msg))
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as err:
        msg = 'Please ensure you have network connection. Error detail: {}'.format(str(err))
        raise CLIError(error_msg_fmt.format(msg))
    except ValueError as err:
        msg = 'Response body does not contain valid json. Error detail: {}'.format(str(err))
        raise CLIError(error_msg_fmt.format(msg))


def _build_cloud(cloud_name, cloud_config=None, cloud_args=None):
    if cloud_config:
        # Using JSON format so convert the keys to snake case
        for key in cloud_config:
            cloud_config[to_snake_case(key)] = cloud_config.pop(key)
        cloud_args = cloud_config
    c = Cloud(cloud_name)
    c.profile = cloud_args.get('profile', None)
    for arg in cloud_args:
        if arg.startswith('endpoint_') and cloud_args[arg] is not None:
            setattr(c.endpoints, arg.replace('endpoint_', ''), cloud_args[arg])
        elif arg.startswith('suffix_') and cloud_args[arg] is not None:
            setattr(c.suffixes, arg.replace('suffix_', ''), cloud_args[arg])
    arm_endpoint = cloud_args.get('endpoint_resource_manager', None)
    _populate_from_metadata_endpoint(c, arm_endpoint)
    return c


def register_cloud(cloud_name,
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
                   suffix_azure_datalake_analytics_catalog_and_job_endpoint=None):
    c = _build_cloud(cloud_name, cloud_config=cloud_config,
                     cloud_args=locals())
    try:
        add_cloud(c)
    except CloudAlreadyRegisteredException as e:
        raise CLIError(e)


def modify_cloud(cloud_name=None,
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
                 suffix_azure_datalake_analytics_catalog_and_job_endpoint=None):
    if not cloud_name:
        cloud_name = get_active_cloud_name()
    c = _build_cloud(cloud_name, cloud_config=cloud_config,
                     cloud_args=locals())
    try:
        update_cloud(c)
    except CloudNotRegisteredException as e:
        raise CLIError(e)


def unregister_cloud(cloud_name):
    try:
        return remove_cloud(cloud_name)
    except CloudNotRegisteredException as e:
        raise CLIError(e)
    except CannotUnregisterCloudException as e:
        raise CLIError(e)


def set_cloud(cloud_name, profile=None):
    try:
        switch_active_cloud(cloud_name)
        if profile:
            modify_cloud(cloud_name=cloud_name, profile=profile)
    except CloudNotRegisteredException as e:
        raise CLIError(e)


def list_profiles(cloud_name=None, show_all=False):
    from azure.cli.core.profiles import API_PROFILES
    if not cloud_name:
        cloud_name = get_active_cloud_name()
    return list(API_PROFILES)
