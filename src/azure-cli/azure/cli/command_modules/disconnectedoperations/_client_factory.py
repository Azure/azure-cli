# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def get_disconnectedoperations_management_client(cli_ctx, *_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client

    # pylint: disable=import-error no-name-in-module
    from azure.mgmt.disconnectedoperations import (
        DisconnectedOperationsClient,
    )

    return get_mgmt_service_client(cli_ctx, DisconnectedOperationsClient)


def cf_image(cli_ctx, *_):
    return get_disconnectedoperations_management_client(cli_ctx).image
