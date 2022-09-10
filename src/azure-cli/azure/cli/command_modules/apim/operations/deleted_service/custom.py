# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.util import sdk_no_wait


def get_deleted_service(client, location, service_name):
    """Get specific soft-deleted Api Management Service."""
    return client.get_by_name(service_name, location)


def list_deleted_service(client):
    """List soft-deleted Api Management Service."""
    return client.list_by_subscription()


def purge_deleted_service(client, service_name, location, no_wait=False):
    """Purge soft-deleted Api Management Service."""
    return sdk_no_wait(no_wait, client.begin_purge, service_name=service_name, location=location)
