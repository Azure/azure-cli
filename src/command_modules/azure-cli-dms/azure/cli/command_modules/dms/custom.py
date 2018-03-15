# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.datamigration.models import (DataMigrationService, ServiceSku)

# region Service

def check_service_name_availability(cmd, client, location, service_name):
    return client.services.check_name_availability(
        location=location,
        name=service_name,
        type='services')

def check_service_status(cmd, client, resource_group_name, service_name):
    return client.services.check_status(
        group_name=resource_group_name,
        service_name=service_name)

def create_service(cmd, client, resource_group_name, service_name, virtual_subnet_id, sku_name, location):
    parameters = DataMigrationService(
        location=location,
        sku=ServiceSku(name=sku_name),
        virtual_subnet_id=virtual_subnet_id)

    return client.services.create_or_update(
        parameters=parameters,
        group_name=resource_group_name,
        service_name=service_name)

def delete_service(cmd, client, resource_group_name, service_name, delete_running_tasks=None):
    return client.services.delete(
        group_name=resource_group_name,
        service_name=service_name,
        delete_running_tasks=delete_running_tasks)

def get_service(cmd, client, resource_group_name, service_name):
    return client.services.get(
        group_name=resource_group_name,
        service_name=service_name)

def list_services(cmd, client, resource_group_name=None):
    list_func = client.services.list_by_resource_group(group_name=resource_group_name) \
        if resource_group_name else client.services.list()
    return list_func

# endregion

# region Tasks

def list_tasks(cmd, client, resource_group_name, service_name, project_name, task_type=None):
    return list(
        client.tasks.list(
            group_name=resource_group_name,
            service_name=service_name,
            project_name=project_name,
            task_type=task_type))



# endregion