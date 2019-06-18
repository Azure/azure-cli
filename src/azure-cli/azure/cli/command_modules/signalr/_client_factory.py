# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _signalr_client_factory(cli_ctx, *_):
    from azure.mgmt.signalr import SignalRManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, SignalRManagementClient)


def cf_signalr(cli_ctx, *_):
    return _signalr_client_factory(cli_ctx).signal_r
