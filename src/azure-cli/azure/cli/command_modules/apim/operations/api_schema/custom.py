# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.util import sdk_no_wait
from azure.cli.core.azclierror import (RequiredArgumentMissingError, MutuallyExclusiveArgumentError)
from azure.mgmt.apimanagement.models import SchemaContract


def create_api_schema(client, resource_group_name, service_name, api_id, schema_id, schema_type,
                      schema_name=None, schema_path=None, schema_content=None,
                      resource_type=None, no_wait=False):

    if schema_path is not None and schema_content is None:
        api_file = open(schema_path, 'r')
        content_value = api_file.read()
        value = content_value
    elif schema_content is not None and schema_path is None:
        value = schema_content
    elif schema_path is not None and schema_content is not None:
        raise MutuallyExclusiveArgumentError(
            "Can't specify schema_path and schema_content at the same time.")
    else:
        raise RequiredArgumentMissingError(
            "Please either specify schema_path or schema_content.")

    parameters = SchemaContract(
        id=schema_id,
        name=schema_name,
        type=resource_type,
        content_type=schema_type,
        value=value
    )

    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name=resource_group_name,
                       service_name=service_name, api_id=api_id, schema_id=schema_id, parameters=parameters)


def delete_api_schema(client, resource_group_name, service_name, api_id, schema_id, if_match=None, no_wait=False):
    return sdk_no_wait(no_wait, client.delete,
                       resource_group_name=resource_group_name,
                       service_name=service_name, api_id=api_id, schema_id=schema_id,
                       if_match="*" if if_match is None else if_match)


def get_api_schema(client, resource_group_name, service_name, api_id, schema_id):
    return client.get(resource_group_name, service_name, api_id, schema_id)


def get_api_schema_entity_tag(client, resource_group_name, service_name, api_id, schema_id):
    return client.get_entity_tag(resource_group_name, service_name, api_id, schema_id)


def list_api_schema(client, resource_group_name, api_id, service_name, filter_display_name=None, top=None, skip=None):
    return client.list_by_api(resource_group_name,
                              service_name, api_id,
                              filter=filter_display_name,
                              skip=skip, top=top)
