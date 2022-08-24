# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

import uuid
from knack.util import CLIError
from azure.cli.core.util import sdk_no_wait
from azure.mgmt.apimanagement.models import (ApiVersionSetContract, VersioningScheme)


def list_api_version_set(client, resource_group_name, service_name):
    """Lists a collection of API Version Sets in the specified service instance."""
    return client.list_by_service(resource_group_name, service_name)


def show_api_version_set(client, resource_group_name, service_name, version_set_id):
    """Gets the details of the Api Version Set specified by its identifier."""
    return client.get(resource_group_name, service_name, version_set_id)


def create_api_version_set(client, resource_group_name, service_name, display_name, versioning_scheme, version_set_id=None, if_match=None,
                    description=None, version_query_name=None, version_header_name=None, no_wait=False):
    """Creates or Updates a Api Version Set."""
    if version_set_id is None:
        version_set_id = uuid.uuid4().hex

    resource = ApiVersionSetContract(
        description=description,
        versioning_scheme=versioning_scheme,
        display_name=display_name)

    if versioning_scheme == VersioningScheme.header:
        if version_header_name is None:
            raise CLIError("Please specify version header name while using 'header' as version scheme.")

        resource.version_header_name = version_header_name

    if versioning_scheme == VersioningScheme.query:
        if version_query_name is None:
            raise CLIError("Please specify version query name while using 'query' as version scheme.")

        resource.version_query_name = version_query_name

    return sdk_no_wait(
        no_wait,
        client.create_or_update,
        resource_group_name=resource_group_name,
        service_name=service_name,
        version_set_id=version_set_id,
        parameters=resource,
        if_match="*" if if_match is None else if_match)


def update_api_version_set(instance, versioning_scheme=None, description=None, display_name=None, version_header_name=None, version_query_name=None):
    """Updates the details of the Api VersionSet specified by its identifier."""
    if display_name is not None:
        instance.display_name = display_name

    if versioning_scheme is not None:
        instance.versioning_scheme = versioning_scheme
        if versioning_scheme == VersioningScheme.header:
            if version_header_name is None:
                raise CLIError("Please specify version header name while using 'header' as version scheme.")

            instance.version_header_name = version_header_name
            instance.version_query_name = None
        if versioning_scheme == VersioningScheme.query:
            if version_query_name is None:
                raise CLIError("Please specify version query name while using 'query' as version scheme.")

            instance.version_query_name = version_query_name
            instance.version_header_name = None

    if description is None:
        instance.description = description

    return instance


def delete_api_version_set(client, resource_group_name, service_name, version_set_id, if_match=None, no_wait=False):
    """Deletes specific Api Version Set."""
    return sdk_no_wait(
        no_wait,
        client.delete,
        resource_group_name=resource_group_name,
        service_name=service_name,
        version_set_id=version_set_id,
        if_match="*" if if_match is None else if_match)
