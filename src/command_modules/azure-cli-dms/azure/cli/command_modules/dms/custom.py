# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.datamigration.models import (DataMigrationService, ServiceSku)
from azure.cli.core.util import CLIError, sdk_no_wait

virtual_subnet_id_template = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'


# region Service

def check_service_name_availability(cmd, client, service_name, location):
    return client.check_name_availability(location=location,
                                          name=service_name,
                                          type='services')

def create_service(cmd, client, service_name, resource_group_name, location, vnet_name, vnet_resource_group, subnet_name, sku_name, tags=None, no_wait=False):
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

# region Tasks

def list_tasks(cmd, client, resource_group_name, service_name, project_name, task_type=None):
    return list(client.tasks.list(group_name=resource_group_name,
                                  service_name=service_name,
                                  project_name=project_name,
                                  task_type=task_type))

# endregion