# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-statements, too-many-locals, too-many-branches

from azure.cli.core.azclierror import CLIError, AzureResponseError, ResourceNotFoundError
from azure.appconfiguration import ConfigurationSettingsFilter
from azure.cli.core.commands.progress import IndeterminateStandardOut
from azure.core.exceptions import HttpResponseError

from ._constants import ProvisioningStatus, StatusCodes, SearchFilterOptions, SnapshotFilterFields
from ._snapshotmodels import SnapshotQueryFields, Snapshot
from ._utils import get_appconfig_data_client


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
                    tags=None):

    client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    configurationSettingsFilters = [ConfigurationSettingsFilter(
        key=x.get(SnapshotFilterFields.KEY),
        label=x.get(SnapshotFilterFields.LABEL),
        tags=x.get(SnapshotFilterFields.TAGS)) for x in filters]

    progress = IndeterminateStandardOut()
    progress.write({"message": "Starting"})

    try:
        config_snapshot_poller = client.begin_create_snapshot(
            snapshot_name,
            configurationSettingsFilters,
            composition_type=composition_type,
            retention_period=retention_period,
            tags=tags)

        # Poll snapshot creation status
        while config_snapshot_poller.status() != ProvisioningStatus.SUCCEEDED:
            progress.spinner.step(label="Running")
            config_snapshot_poller.wait(1)

        return Snapshot.from_configuration_snapshot(config_snapshot_poller.result())

    except HttpResponseError as exception:
        if exception.status_code == StatusCodes.CONFLICT:
            raise AzureResponseError("A snapshot with name '{}' already exists.".format(snapshot_name))

        raise AzureResponseError(str(exception))

    except Exception as exception:
        raise CLIError("Failed to create snapshot. {}".format(str(exception)))

    finally:
        progress.clear()


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

    client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        result = client.get_snapshot(snapshot_name, fields=query_fields)

    except HttpResponseError as exception:
        if exception.status_code == StatusCodes.NOT_FOUND:
            raise ResourceNotFoundError("No snapshot with name '{}' was found.".format(snapshot_name))

        raise AzureResponseError(str(exception))

    except Exception as exception:
        raise CLIError("Request failed. {}".format(str(exception)))

    snapshot = Snapshot.from_configuration_snapshot(result)

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

    client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

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

    for config_snapshot in snapshots_iterable:
        snapshot = Snapshot.from_configuration_snapshot(config_snapshot)
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

    client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        result = client.archive_snapshot(snapshot_name)

        return Snapshot.from_configuration_snapshot(result)

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

    client = get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint)

    try:
        result = client.recover_snapshot(snapshot_name)

        return Snapshot.from_configuration_snapshot(result)

    except HttpResponseError as exception:
        if exception.status_code == StatusCodes.NOT_FOUND:
            raise ResourceNotFoundError("No snapshot with name '{}' was found.".format(snapshot_name))

        raise AzureResponseError(str(exception))

    except Exception as exception:
        raise CLIError("Failed to recover snapshot. {}".format(str(exception)))
