# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os

from azure.mgmt.datamigration.models import (DataMigrationService, ServiceSku, Project, SqlConnectionInfo, DatabaseInfo)
from azure.cli.core.util import CLIError, sdk_no_wait, get_file_json, shell_safe_json_parse
from knack.prompting import prompt_pass

virtual_subnet_id_template = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'


# region Service

def check_service_name_availability(cmd, client, service_name, location):
    return client.check_name_availability(location=location,
                                          name=service_name,
                                          type='services')

def create_service(cmd, client, service_name, resource_group_name, location, vnet_name, vnet_resource_group_name, subnet_name, sku_name, tags=None, no_wait=False):
    from msrestazure.tools import resource_id
    parameters = DataMigrationService(location=location,
                                      virtual_subnet_id=resource_id(subscription=client.config.subscription_id,
                                                                    resource_group=vnet_resource_group_name,
                                                                    namespace='Microsoft.Network',
                                                                    type='virtualNetworks',
                                                                    name=vnet_name,
                                                                    child_type_1='subnets',
                                                                    child_name_1=subnet_name),
                                      sku=ServiceSku(name=sku_name),
                                      tags=tags)

    return sdk_no_wait(no_wait,
                       client.create_or_update,
                       parameters=parameters,
                       group_name=resource_group_name,
                       service_name=service_name)

def delete_service(cmd, client, service_name, resource_group_name, delete_running_tasks=None, no_wait=False):
    return sdk_no_wait(no_wait,
                       client.delete,
                       group_name=resource_group_name,
                       service_name=service_name,
                       delete_running_tasks=delete_running_tasks)

def list_services(cmd, client, resource_group_name=None):
    list_func = client.list_by_resource_group(group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list_func

def start_service(cmd, client, service_name, resource_group_name, no_wait=False):
    return sdk_no_wait(no_wait,
                       client.start,
                       group_name=resource_group_name,
                       service_name=service_name)

def stop_service(cmd, client, service_name, resource_group_name, no_wait=False):
    return sdk_no_wait(no_wait,
                       client.stop,
                       group_name=resource_group_name,
                       service_name=service_name)

# endregion

# region Project

def create_or_update_project(cmd,
                             client,
                             project_name,
                             service_name,
                             resource_group_name,
                             location,
                             source_platform,
                             source_connection_json,
                             target_platform,
                             target_connection_json,
                             database_list,
                             tags=None):
    if os.path.exists(source_connection_json):
        source_connection_json = get_file_json(source_connection_json)
    else:
        source_connection_json = shell_safe_json_parse(source_connection_json)

    if os.path.exists(target_connection_json):
        target_connection_json = get_file_json(target_connection_json)
    else:
        target_connection_json = shell_safe_json_parse(target_connection_json)

    sconn_info = SqlConnectionInfo(user_name=source_connection_json.get('userName', None),
                                   password=source_connection_json.get('password', None),
                                   data_source=source_connection_json.get('dataSource', None),
                                   authentication=source_connection_json.get('authentication', None),
                                   encrypt_connection=source_connection_json.get('encryptConnection', None),
                                   trust_server_certificate=source_connection_json.get('trustServerCertificate', None),
                                   additional_settings=source_connection_json.get('additionalSettings', None))

    tconn_info = SqlConnectionInfo(user_name=target_connection_json.get('userName', None),
                                   password=target_connection_json.get('password', None),
                                   data_source=target_connection_json.get('dataSource', None),
                                   authentication=target_connection_json.get('authentication', None),
                                   encrypt_connection=target_connection_json.get('encryptConnection', None),
                                   trust_server_certificate=target_connection_json.get('trustServerCertificate', None),
                                   additional_settings=target_connection_json.get('additionalSettings', None))

    databases = []
    for d in database_list:
        databases.append(DatabaseInfo(source_database_name=d))
    
    parameters = Project(location=location,
                         source_platform=source_platform,
                         source_connection_info=sconn_info,
                         target_platform=target_platform,
                         target_connection_info=tconn_info,
                         databases_info=databases,
                         tags=tags)

    return client.create_or_update(parameters=parameters,
                                   group_name=resource_group_name,
                                   service_name=service_name,
                                   project_name=project_name)

# endregion

# region Task

def list_tasks(cmd, client, resource_group_name, service_name, project_name, task_type=None):
    return list(client.tasks.list(group_name=resource_group_name,
                                  service_name=service_name,
                                  project_name=project_name,
                                  task_type=task_type))

# endregion