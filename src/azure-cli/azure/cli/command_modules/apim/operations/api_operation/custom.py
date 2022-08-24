# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

import uuid
from azure.cli.core.util import sdk_no_wait
from azure.mgmt.apimanagement.models import OperationContract


def list_api_operation(client, resource_group_name, service_name, api_id):
    """List a collection of the operations for the specified API."""
    return client.list_by_api(resource_group_name, service_name, api_id)


def get_api_operation(client, resource_group_name, service_name, api_id, operation_id):
    """Gets the details of the API Operation specified by its identifier."""
    return client.get(resource_group_name, service_name, api_id, operation_id)


def create_api_operation(client, resource_group_name, service_name, api_id, url_template, method, display_name, template_parameters=None, operation_id=None, description=None, if_match=None, no_wait=False):
    """Creates a new operation in the API or updates an existing one."""
    if operation_id is None:
        operation_id = uuid.uuid4().hex

    resource = OperationContract(
        description=description,
        display_name=display_name,
        method=method,
        url_template=url_template,
        template_parameters=template_parameters)

    return sdk_no_wait(
        no_wait,
        client.create_or_update,
        resource_group_name=resource_group_name,
        service_name=service_name,
        api_id=api_id,
        operation_id=operation_id,
        parameters=resource,
        if_match="*" if if_match is None else if_match)


def update_api_operation(instance, display_name=None, description=None, method=None, url_template=None):
    """Updates the details of the operation in the API specified by its identifier."""

    if display_name is not None:
        instance.display_name = display_name

    if description is not None:
        instance.description = description

    if method is not None:
        instance.method = method

    if url_template is not None:
        instance.url_template = url_template

    return instance


def delete_api_operation(client, resource_group_name, service_name, api_id, operation_id, if_match=None, no_wait=False):
    """Deletes the specified operation in the API."""

    return sdk_no_wait(
        no_wait,
        client.delete,
        resource_group_name=resource_group_name,
        service_name=service_name,
        api_id=api_id,
        operation_id=operation_id,
        if_match="*" if if_match is None else if_match)
