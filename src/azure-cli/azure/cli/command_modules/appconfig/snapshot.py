# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-statements, too-many-locals, too-many-branches

from azure.cli.core.azclierror import CLIError, AzureResponseError, ResourceNotFoundError
from azure.core.exceptions import HttpResponseError

from ._constants import StatusCodes, SearchFilterOptions
from ._snapshot_custom_client import AppConfigSnapshotClient
from ._snapshotmodels import SnapshotQueryFields
from ._utils import get_appconfig_data_client


def _get_snapshot_client(cmd,
                         name,
                         connection_string,
                         auth_mode,
                         endpoint):
    return AppConfigSnapshotClient(get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint))


# Snapshot commands #

def create_snapshot(cmd,
                    snapshot_name,
                    filters,
                    name=None,
                    connection_string=None,
                    auth_mode='key',
                    endpoint=None,
                    retention_period=None,
                    composition_type=None,
                    tags=None
                    ):

    client = _get_snapshot_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        return client.begin_create_snapshot(snapshot_name, filters, composition_type, retention_period, tags)

    except HttpResponseError as exception:
        if exception.status_code == StatusCodes.CONFLICT:
            raise AzureResponseError("A snapshot with name '{}' already exists.".format(snapshot_name))

        raise AzureResponseError(str(exception))

    except Exception as exception:
        raise CLIError("Failed to create snapshot. {}".format(str(exception)))


def show_snapshot(cmd,
                  snapshot_name,
                  name=None,
                  fields=None,
                  connection_string=None,
                  auth_mode='key',
                  endpoint=None):

    query_fields = []

    if fields:
        for field in fields:
            if field == SnapshotQueryFields.ALL:
                query_fields.clear()
                break
            query_fields.append(field.name.lower())

    client = _get_snapshot_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        snapshot = client.get_snapshot(snapshot_name, fields=query_fields)

    except HttpResponseError as exception:
        if exception.status_code == StatusCodes.NOT_FOUND:
            raise ResourceNotFoundError("No snapshot with name '{}' was found.".format(snapshot_name))

        raise AzureResponseError(str(exception))

    except Exception as exception:
        raise CLIError("Request failed. {}".format(str(exception)))

    if not query_fields:
        return snapshot

    partial_snapshot = {}

    for field in query_fields:
        partial_snapshot[field] = snapshot.__dict__[field]

    return partial_snapshot


def list_snapshots(cmd,
                   snapshot_name=SearchFilterOptions.ANY_KEY,
                   status=None,
                   fields=None,
                   name=None,
                   top=None,
                   all_=None,
                   connection_string=None,
                   auth_mode='key',
                   endpoint=None):

    query_fields = []

    if fields:
        for field in fields:
            if field == SnapshotQueryFields.ALL:
                query_fields.clear()
                break
            query_fields.append(field.name.lower())

    client = _get_snapshot_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        snapshots_iterable = client.list_snapshots(name=snapshot_name, status=status, fields=query_fields)

    except HttpResponseError as exception:
        raise AzureResponseError(str(exception))

    except Exception as exception:
        raise CLIError('Request failed, {}'.format(str(exception)))

    if all_:
        top = float('inf')
    elif top is None:
        top = 100

    snapshots = []
    current_snapshot_count = 0

    for snapshot in snapshots_iterable:
        if query_fields:
            partial_snapshot = {}
            for field in query_fields:
                partial_snapshot[field] = snapshot.__dict__[field]
            snapshots.append(partial_snapshot)
        else:
            snapshots.append(snapshot)

        current_snapshot_count += 1

        if current_snapshot_count >= top:
            break

    return snapshots


def archive_snapshot(cmd,
                     snapshot_name,
                     name=None,
                     connection_string=None,
                     auth_mode='key',
                     endpoint=None):

    client = _get_snapshot_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        return client.archive_snapshot(snapshot_name)

    except HttpResponseError as exception:
        if exception.status_code == StatusCodes.NOT_FOUND:
            raise ResourceNotFoundError("No snapshot with name '{}' was found.".format(snapshot_name))

        raise AzureResponseError(str(exception))

    except Exception as exception:
        raise CLIError("Failed to archive snapshot. {}".format(str(exception)))


def recover_snapshot(cmd,
                     snapshot_name,
                     name=None,
                     connection_string=None,
                     auth_mode='key',
                     endpoint=None):

    client = _get_snapshot_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        return client.recover_snapshot(snapshot_name)

    except HttpResponseError as exception:
        if exception.status_code == StatusCodes.NOT_FOUND:
            raise ResourceNotFoundError("No snapshot with name '{}' was found.".format(snapshot_name))

        raise AzureResponseError(str(exception))

    except Exception as exception:
        raise CLIError("Failed to recover snapshot. {}".format(str(exception)))
