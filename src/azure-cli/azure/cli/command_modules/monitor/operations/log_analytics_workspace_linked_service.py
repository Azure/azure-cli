# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import sdk_no_wait


def create_log_analytics_workspace_linked_service(client, resource_group_name, workspace_name,
                                                  linked_service_name, resource_id=None, write_access_resource_id=None,
                                                  no_wait=False):
    from azure.mgmt.loganalytics.models import LinkedService

    linked_service = LinkedService(resource_id=resource_id,
                                   write_access_resource_id=write_access_resource_id)
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name,
                       workspace_name, linked_service_name, linked_service)


def update_log_analytics_workspace_linked_service(instance, resource_id=None, write_access_resource_id=None):
    if resource_id is not None:
        instance.resource_id = resource_id
    if write_access_resource_id is not None:
        instance.write_access_resource_id = write_access_resource_id
    return instance
