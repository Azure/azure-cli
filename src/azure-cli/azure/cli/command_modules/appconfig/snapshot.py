# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-statements, too-many-locals, too-many-branches

from ._snapshot_custom_client import AppConfigSnapshotClient
from ._utils import get_appconfig_data_client
from azure.cli.core.azclierror import CLIError, AzureResponseError, RequiredArgumentMissingError, InvalidArgumentValueError
from ._constants import StatusCodes
from azure.core.exceptions import HttpResponseError

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

    _client = AppConfigSnapshotClient(get_appconfig_data_client(cmd, name, connection_string, auth_mode, endpoint))

    try :
        return _client.create_snapshot(snapshot_name, filters, composition_type, str(retention_period), tags)
    
    except HttpResponseError as exception:
        if exception.status_code == StatusCodes.CONFLICT:
            raise AzureResponseError("The snapshot with name {} already exists.".format(snapshot_name))

        raise AzureResponseError(str(exception))
    
    except Exception as exception:
        raise CLIError("Failed to create snapshot. {}".format(str(exception)))