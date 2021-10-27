# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_connection_cl(cli_ctx, *_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.servicelinker import MicrosoftServiceLinker

    return get_mgmt_service_client(cli_ctx, MicrosoftServiceLinker, subscription_bound=False)


def cf_linker(cli_ctx, *_):
    return cf_connection_cl(cli_ctx).linker
