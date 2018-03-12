# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_media(cli_ctx, *_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mediav3 import AzureMediaServices
    return get_mgmt_service_client(cli_ctx, AzureMediaServices)


def get_mediaservices_client(cli_ctx, *_):
    return cf_media(cli_ctx).mediaservices
