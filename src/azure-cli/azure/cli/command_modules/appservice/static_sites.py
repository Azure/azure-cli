# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client

def list_staticsites(cmd, resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if resource_group_name:
        result = list(client.get_static_sites_by_resource_group(resource_group_name))
    else:
        result = list(client.list())
    return result

def show_staticsites(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.get_static_site(resource_group_name, name)

def list_staticsites_domains(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.list_static_site_custom_domains(resource_group_name, name)

def list_staticsites_secrets(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.list_static_site_secrets(resource_group_name, name)

def list_staticsite_functions(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.list_static_site_functions(resource_group_name, name)

def list_staticsite_function_app_settings(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.list_static_site_function_app_settings(resource_group_name, name)

def _get_staticsites_client_factory(cli_ctx, api_version=None):
    from azure.mgmt.web import WebSiteManagementClient
    client = get_mgmt_service_client(cli_ctx, WebSiteManagementClient).static_sites
    if api_version:
        client.api_version = api_version
    return client
