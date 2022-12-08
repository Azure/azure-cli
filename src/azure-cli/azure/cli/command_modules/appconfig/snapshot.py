# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-statements, too-many-locals, too-many-branches

from ._constants import StatusCodes, SearchFilterOptions
from ._snapshot_custom_client import AppConfigSnapshotClient
from ._utils import get_appconfig_data_client
from azure.cli.core.azclierror import CLIError, AzureResponseError, ResourceNotFoundError
from azure.core.exceptions import HttpResponseError


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

    _client = _get_snapshot_client(cmd, name, connection_string, auth_mode, endpoint)

    try :
        return _client.create_snapshot(snapshot_name, filters, composition_type, retention_period, tags)
    
    except HttpResponseError as exception:
        if exception.status_code == StatusCodes.CONFLICT:
            raise AzureResponseError("A snapshot with name '{}' already exists.".format(snapshot_name))

        raise AzureResponseError(str(exception))
    
    except Exception as exception:
        raise CLIError("Failed to create snapshot. {}".format(str(exception)))


def show_snapshot(cmd,
                  snapshot_name,
                  name=None,
                  connection_string=None,
                  auth_mode='key',
                  endpoint=None):

    _client = _get_snapshot_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        return _client.get_snapshot(snapshot_name)

    except HttpResponseError as exception:
        if exception.status_code == StatusCodes.NOT_FOUND:
            raise ResourceNotFoundError("No snapshot with name {} was found.".format(snapshot_name))
        
        raise AzureResponseError(str(exception))

    except Exception as exception:
        raise CLIError("Request failed. {}".format(str(exception)))


def list_snapshots(cmd,
                   snapshot_name=SearchFilterOptions.ANY_KEY,
                   status=SearchFilterOptions.ANY_KEY,
                   name=None,
                   connection_string=None,
                   auth_mode='key',
                   endpoint=None):

    _client = _get_snapshot_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        return _client.list_snapshots(
            name=snapshot_name,
            status=status
        )

    except HttpResponseError as exception:
        raise AzureResponseError(str(exception))

    except Exception as exception:
        raise CLIError('Request failed, {}'.format(str(exception)))


def archive_snapshot(cmd,
                     snapshot_name,
                     name=None,
                     connection_string=None,
                     auth_mode='key',
                     endpoint=None):

    _client = _get_snapshot_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        return _client.archive_snapshot(snapshot_name)

    except HttpResponseError as exception:
        if exception.status_code == StatusCodes.NOT_FOUND:
            raise ResourceNotFoundError("No snapshot with name {} was found.".format(snapshot_name))

        raise AzureResponseError(str(exception))

    except Exception as exception:
        raise CLIError("Failed to archive snapshot. {}".format(str(exception)))


def recover_snapshot(cmd,
                     snapshot_name,
                     name=None,
                     connection_string=None,
                     auth_mode='key',
                     endpoint=None):

    _client = _get_snapshot_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        return _client.recover_snapshot(snapshot_name)

    except HttpResponseError as exception:
        if exception.status_code == StatusCodes.NOT_FOUND:
            raise ResourceNotFoundError("No snapshot with name {} was found.".format(snapshot_name))

        raise AzureResponseError(str(exception))

    except Exception as exception:
        raise CLIError("Failed to recover snapshot. {}".format(str(exception)))