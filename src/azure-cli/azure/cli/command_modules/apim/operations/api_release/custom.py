# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

import uuid


def list_api_release(client, resource_group_name, service_name, api_id):
    """Lists all releases of an API."""
    return client.list_by_service(resource_group_name, service_name, api_id)


def show_api_release(client, resource_group_name, service_name, api_id, release_id):
    """Returns the details of an API release."""
    return client.get(resource_group_name, service_name, api_id, release_id)


def create_api_release(client, resource_group_name, service_name, api_id, api_revision, release_id=None, if_match=None, notes=None):
    """Creates a new Release for the API."""
    if release_id is None:
        release_id = uuid.uuid4().hex

    api_revision_to_release_and_make_current = "/apis/" + api_id + ";rev=" + api_revision
    if_match = "*" if if_match is None else if_match

    return client.create_or_update(resource_group_name, service_name, api_id, release_id, if_match, api_revision_to_release_and_make_current, notes)


def update_api_release(instance, notes=None):
    """Updates the details of the release of the API specified by its identifier."""
    instance.notes = notes
    return instance


def delete_api_release(client, resource_group_name, service_name, api_id, release_id, if_match=None):
    """Deletes the specified release in the API."""
    return client.delete(resource_group_name, service_name, api_id, release_id, "*" if if_match is None else if_match)
