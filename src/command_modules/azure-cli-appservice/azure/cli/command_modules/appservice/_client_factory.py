# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def web_client_factory(**_):
    from azure.mgmt.web import WebSiteManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(WebSiteManagementClient)


def cf_plans(_):
    return web_client_factory().app_service_plans


def cf_web_client(_):
    return web_client_factory()
