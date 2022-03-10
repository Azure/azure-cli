# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from azure.cli.command_modules.acs._client_factory import cf_snapshots
from azure.cli.core.azclierror import (
    AzureInternalError,
    AzureResponseError,
    BadRequestError,
    ClientRequestError,
    ForbiddenError,
    InvalidArgumentValueError,
    ResourceNotFoundError,
    ServiceError,
    UnauthorizedError,
    UnclassifiedUserFault,
)
from azure.core.exceptions import AzureError, HttpResponseError, ServiceRequestError, ServiceResponseError


def map_azure_error_to_cli_error(azure_error):
    error_message = getattr(azure_error, "message", str(azure_error))
    if isinstance(azure_error, HttpResponseError):
        status_code = getattr(azure_error, "status_code", None)
        if status_code:
            status_code = int(status_code)
            if status_code == 400:
                return BadRequestError(error_message)
            elif status_code == 401:
                return UnauthorizedError(error_message)
            elif status_code == 403:
                return ForbiddenError(error_message)
            elif status_code == 404:
                return ResourceNotFoundError(error_message)
            elif status_code >= 400 and status_code < 500:
                return UnclassifiedUserFault(error_message)
            elif status_code >= 500 and status_code < 600:
                return AzureInternalError(error_message)
        return ServiceError(error_message)
    elif isinstance(azure_error, ServiceRequestError):
        return ClientRequestError(error_message)
    elif isinstance(azure_error, ServiceResponseError):
        return AzureResponseError(error_message)
    else:
        return ServiceError(error_message)


def get_snapshot_by_snapshot_id(cli_ctx, snapshot_id):
    _re_snapshot_resource_id = re.compile(
        r"/subscriptions/(.*?)/resourcegroups/(.*?)/providers/microsoft.containerservice/snapshots/(.*)",
        flags=re.IGNORECASE,
    )
    snapshot_id = snapshot_id.lower()
    match = _re_snapshot_resource_id.search(snapshot_id)
    if match:
        resource_group_name = match.group(2)
        snapshot_name = match.group(3)
        return get_snapshot(cli_ctx, resource_group_name, snapshot_name)
    raise InvalidArgumentValueError("Cannot parse snapshot name from provided resource id '{}'.".format(snapshot_id))


def get_snapshot(cli_ctx, resource_group_name, snapshot_name):
    snapshot_client = cf_snapshots(cli_ctx)
    try:
        snapshot = snapshot_client.get(resource_group_name, snapshot_name)
    except AzureError as ex:
        if "not found" in ex.message:
            raise ResourceNotFoundError("Snapshot '{}' not found.".format(snapshot_name))
        raise map_azure_error_to_cli_error(ex)
    return snapshot
