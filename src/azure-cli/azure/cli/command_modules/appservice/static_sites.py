# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.util import sdk_no_wait
from knack.util import CLIError


def list_staticsites(cmd, resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if resource_group_name:
        result = list(client.get_static_sites_by_resource_group(resource_group_name))
    else:
        result = list(client.list())
    return result


def show_staticsite(cmd, name, resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    return client.get_static_site(resource_group_name, name)


def list_staticsite_environments(cmd, name, resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    return client.get_static_site_builds(resource_group_name, name)


def show_staticsite_environment(cmd, name, environment_name='default', resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    return client.get_static_site_build(resource_group_name, name, environment_name)


def list_staticsite_domains(cmd, name, resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    return client.list_static_site_custom_domains(resource_group_name, name)


def set_staticsite_domain(cmd, name, hostname, resource_group_name=None, no_wait=False):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    client.validate_custom_domain_can_be_added_to_static_site(resource_group_name, name, hostname)

    return sdk_no_wait(no_wait, client.create_or_update_static_site_custom_domain,
                           resource_group_name=resource_group_name, name=name, domain_name=hostname)


def delete_staticsite_domain(cmd, name, hostname, resource_group_name=None, no_wait=False):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    print("After deleting a custom domain, there can be a 15 minute delay for the change to propagate.")
    return sdk_no_wait(no_wait, client.delete_static_site_custom_domain,
                       resource_group_name=resource_group_name, name=name, domain_name=hostname)


def list_staticsite_secrets(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.list_static_site_secrets(resource_group_name, name)


def list_staticsite_functions(cmd, name, resource_group_name=None, environment_name='default'):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    return client.list_static_site_build_functions(resource_group_name, name, environment_name)


def list_staticsite_function_app_settings(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.list_static_site_function_app_settings(resource_group_name, name)


def create_staticsites(cmd, resource_group_name, name, location,
                       source, branch, token=None,
                       app_location='/', api_location='api', app_artifact_location=None,
                       custom_domains=None, tags=None, no_wait=False):
    if not token:
        raise CLIError("GitHub access token is required to authenticate to your repositories. "
                       "If you need to create a Github Personal Access Token, "
                       "please follow the steps found at the following link:\n{0}"
                       .format(
                        "https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line"))

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
        repository_url=source,
        branch=branch,
        custom_domains=custom_domains,
        repository_token=token,
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


def _get_resource_group_name_of_staticsite(client, static_site_name):
    static_sites = client.list()
    for static_site in static_sites:
        if static_site.name.lower() == static_site_name.lower():
            from .utils import _get_resource_group_from_id
            return _get_resource_group_from_id(static_site.id)

    raise CLIError("Static site was '{}' not found in subscription.".format(static_site_name))


def _get_staticsites_client_factory(cli_ctx, api_version=None):
    from azure.mgmt.web import WebSiteManagementClient
    client = get_mgmt_service_client(cli_ctx, WebSiteManagementClient).static_sites
    if api_version:
        client.api_version = api_version
    return client
