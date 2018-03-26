# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.mgmt.datamigration.models import (DataMigrationService, ServiceSku)

virtual_subnet_id_template = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'

# region Service

def check_service_name_availability(cmd, client, service_name, location):
    return client.services.check_name_availability(
        location=location,
        name=service_name,
        type='services')

def check_service_status(cmd, client, service_name, resource_group_name):
    return client.services.check_status(
        group_name=resource_group_name,
        service_name=service_name)

def create_service(cmd, client, service_name, resource_group_name, location, virtual_network_name, subnet_name, sku_name, tags=None):
    from msrestazure.tools import resource_id
    parameters = DataMigrationService(
        location=location,
        virtual_subnet_id=resource_id(subscription=client.config.subscription_id,
                                      resource_group=resource_group_name,
                                      namespace='Microsoft.Network',
                                      type='virtualNetworks',
                                      name=virtual_network_name,
                                      child_type_1='subnets',
                                      child_name_1=subnet_name),
        sku=ServiceSku(name=sku_name),
        tags=tags)

    return client.services.create_or_update(
        parameters=parameters,
        group_name=resource_group_name,
        service_name=service_name)

def delete_service(cmd, client, service_name, resource_group_name, delete_running_tasks=None):
    return client.services.delete(
        group_name=resource_group_name,
        service_name=service_name,
        delete_running_tasks=delete_running_tasks)

def get_service(cmd, client, service_name, resource_group_name):
    return client.services.get(
        group_name=resource_group_name,
        service_name=service_name)

def list_services(cmd, client, resource_group_name=None):
    list_func = client.services.list_by_resource_group(group_name=resource_group_name) \
        if resource_group_name else client.services.list()
    return list_func

def list_skus(cmd, client):
    return client.resource_skus.list_skus()

def start_service(cmd, client, service_name, resource_group_name):
    return client.services.start(
        group_name=resource_group_name,
        service_name=service_name)

def stop_service(cmd, client, service_name, resource_group_name):
    return client.services.stop(
        group_name=resource_group_name,
        service_name=service_name)

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