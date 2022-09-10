# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.util import sdk_no_wait
from azure.cli.core.azclierror import (RequiredArgumentMissingError, MutuallyExclusiveArgumentError)
from azure.mgmt.apimanagement.models import SchemaContract


def create_api_schema(client, resource_group_name, service_name, api_id, schema_id, schema_type,
                      schema_name=None, schema_path=None, schema_content=None, no_wait=False):
    parameters = SchemaContract(
        id=schema_id,
        name=schema_name,
        content_type=schema_type,
        value=_get_schema_file_content(schema_path, schema_content)
    )

    return sdk_no_wait(no_wait, client.begin_create_or_update,
                       resource_group_name=resource_group_name,
                       service_name=service_name, api_id=api_id, schema_id=schema_id, parameters=parameters)


def delete_api_schema(client, resource_group_name, service_name, api_id, schema_id, if_match=None, no_wait=False):
    return sdk_no_wait(no_wait, client.delete,
                       resource_group_name=resource_group_name,
                       service_name=service_name, api_id=api_id, schema_id=schema_id,
                       if_match="*" if if_match is None else if_match)


def get_api_schema(client, resource_group_name, service_name, api_id, schema_id, include_schema_value=False):
    schema = client.get(resource_group_name, service_name, api_id, schema_id, cls=_get_api_schema_cls)

    if not include_schema_value:
        del schema.value

    return schema


def list_api_schema(client, resource_group_name, api_id, service_name, filter_display_name=None, top=None, skip=None):
    return client.list_by_api(resource_group_name,
                              service_name, api_id,
                              filter=filter_display_name,
                              skip=skip, top=top)


def _get_schema_file_content(schema_path, schema_content):
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
    return value


# include ETag, this "constructor" will get called by the client, using its return value as the return of the client method
def _get_api_schema_cls(_, deserialized, response_headers):
    schema = SchemaContract(
        content_type=deserialized.content_type,
        value=deserialized.value,
        definitions=deserialized.definitions,
        components=deserialized.components)

    schema.id = deserialized.id
    schema.name = deserialized.name
    schema.type = deserialized.type
    schema.content_type = deserialized.content_type
    schema.etag = response_headers['ETag'].strip('\"')

    return schema
