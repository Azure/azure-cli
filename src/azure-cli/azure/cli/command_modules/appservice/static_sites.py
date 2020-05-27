# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.util import sdk_no_wait


def list_staticsites(cmd, resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if resource_group_name:
        result = list(client.get_static_sites_by_resource_group(resource_group_name))
    else:
        result = list(client.list())
    return result


def show_staticsite(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.get_static_site(resource_group_name, name)


def list_staticsite_domains(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.list_static_site_custom_domains(resource_group_name, name)


def list_staticsite_secrets(cmd, resource_group_name, name):
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


def create_staticsites(cmd, resource_group_name, name, location,
                       repository_url, repository_token, branch='master',
                       app_location='/', api_location='api', app_artifact_location=None,
                       custom_domains=None, tags=None, no_wait=False):
    StaticSiteARMResource, StaticSiteBuildProperties, SkuDescription = cmd.get_models(
        'StaticSiteARMResource', 'StaticSiteBuildProperties', 'SkuDescription')

    build = StaticSiteBuildProperties(
        app_location=app_location,
        api_location=api_location,
        app_artifact_location=app_artifact_location)

    sku = SkuDescription(name='Free', tier='Free')

    staticsite_deployment_properties = StaticSiteARMResource(
        name=name,
        location=location,
        type='Microsoft.Web/staticsites',
        tags=tags,
        repository_url=repository_url,
        branch=branch,
        custom_domains=custom_domains,
        repository_token=repository_token,
        build_properties=build,
        sku=sku)

    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return sdk_no_wait(no_wait, client.create_or_update_static_site,
                       resource_group_name=resource_group_name, name=name,
                       static_site_envelope=staticsite_deployment_properties)


def update_staticsites(cmd, no_wait=False):
    return


def delete_staticsite(cmd, resource_group_name, name, no_wait=False):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return sdk_no_wait(no_wait, client.delete_static_site,
                       resource_group_name=resource_group_name, name=name)
