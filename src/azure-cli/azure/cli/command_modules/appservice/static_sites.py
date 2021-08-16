# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.util import sdk_no_wait
from knack.util import CLIError
from knack.log import get_logger

from .utils import normalize_sku_for_staticapp, raise_missing_token_suggestion

logger = get_logger(__name__)


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


def disconnect_staticsite(cmd, name, resource_group_name=None, no_wait=False):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    return sdk_no_wait(no_wait, client.detach_static_site,
                       resource_group_name=resource_group_name, name=name)


def reconnect_staticsite(cmd, name, source, branch, token=None, resource_group_name=None, login_with_github=False,
                         no_wait=False):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    location = _get_staticsite_location(client, name, resource_group_name)

    return create_staticsites(cmd, resource_group_name, name, location,
                              source, branch, token, login_with_github=login_with_github, no_wait=no_wait)


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

    logger.warning("After deleting a custom domain, there can be a 15 minute delay for the change to propagate.")
    return sdk_no_wait(no_wait, client.delete_static_site_custom_domain,
                       resource_group_name=resource_group_name, name=name, domain_name=hostname)


def list_staticsite_functions(cmd, name, resource_group_name=None, environment_name='default'):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    return client.list_static_site_build_functions(resource_group_name, name, environment_name)


def list_staticsite_function_app_settings(cmd, name, resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    return client.list_static_site_function_app_settings(resource_group_name, name)


def set_staticsite_function_app_settings(cmd, name, setting_pairs, resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    setting_dict = {}
    for pair in setting_pairs:
        key, value = _parse_pair(pair, "=")
        setting_dict[key] = value

    return client.create_or_update_static_site_function_app_settings(
        resource_group_name, name, app_settings=setting_dict)


def delete_staticsite_function_app_settings(cmd, name, setting_names, resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    app_settings = client.list_static_site_function_app_settings(resource_group_name, name).properties

    for key in setting_names:
        if key in app_settings:
            app_settings.pop(key)
        else:
            logger.warning("key '%s' not found in app settings", key)

    return client.create_or_update_static_site_function_app_settings(
        resource_group_name, name, app_settings=app_settings)


def list_staticsite_users(cmd, name, resource_group_name=None, authentication_provider='all'):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    return client.list_static_site_users(resource_group_name, name, authentication_provider)


def invite_staticsite_users(cmd, name, authentication_provider, user_details, domain,
                            roles, invitation_expiration_in_hours, resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    StaticSiteUserInvitationRequestResource = cmd.get_models('StaticSiteUserInvitationRequestResource')

    invite_request = StaticSiteUserInvitationRequestResource(
        domain=domain,
        provider=authentication_provider,
        user_details=user_details,
        roles=roles,
        num_hours_to_expiration=invitation_expiration_in_hours
    )

    return client.create_user_roles_invitation_link(resource_group_name, name, invite_request)


def update_staticsite_users(cmd, name, roles, authentication_provider=None, user_details=None, user_id=None,
                            resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    if not authentication_provider and user_id:
        authentication_provider = _find_authentication_provider(
            client, resource_group_name, name, user_id, authentication_provider)

    if not user_id and user_details:
        user_id, authentication_provider = _find_user_id_and_authentication_provider(
            client, resource_group_name, name, user_id, authentication_provider, user_details)

    if not authentication_provider or not user_id:
        raise CLIError("Either user id or user details is required.")

    return client.update_static_site_user(resource_group_name, name, authentication_provider, user_id, roles=roles)


def create_staticsites(cmd, resource_group_name, name, location,
                       source, branch, token=None,
                       app_location='.', api_location='.', output_location='.github/workflows',
                       tags=None, no_wait=False, sku='Free', login_with_github=False):
    if not token and not login_with_github:
        raise_missing_token_suggestion()
    elif not token:
        from ._github_oauth import get_github_access_token
        scopes = ["admin:repo_hook", "repo", "workflow"]
        token = get_github_access_token(cmd, scopes)
    elif token and login_with_github:
        logger.warning("Both token and --login-with-github flag are provided. Will use provided token")

    StaticSiteARMResource, StaticSiteBuildProperties, SkuDescription = cmd.get_models(
        'StaticSiteARMResource', 'StaticSiteBuildProperties', 'SkuDescription')

    build = StaticSiteBuildProperties(
        app_location=app_location,
        api_location=api_location,
        app_artifact_location=output_location)

    sku_def = SkuDescription(name=normalize_sku_for_staticapp(sku), tier=normalize_sku_for_staticapp(sku))

    staticsite_deployment_properties = StaticSiteARMResource(
        location=location,
        tags=tags,
        repository_url=source,
        branch=branch,
        repository_token=token,
        build_properties=build,
        sku=sku_def)

    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return sdk_no_wait(no_wait, client.create_or_update_static_site,
                       resource_group_name=resource_group_name, name=name,
                       static_site_envelope=staticsite_deployment_properties)


def update_staticsite(cmd, name, source=None, branch=None, token=None,
                      tags=None, sku=None, no_wait=False):
    existing_staticsite = show_staticsite(cmd, name)
    if not existing_staticsite:
        raise CLIError("No static web app found with name {0}".format(name))

    if tags is not None:
        existing_staticsite.tags = tags

    StaticSiteARMResource, SkuDescription = cmd.get_models('StaticSiteARMResource', 'SkuDescription')

    sku_def = None
    if sku is not None:
        sku_def = SkuDescription(name=normalize_sku_for_staticapp(sku), tier=normalize_sku_for_staticapp(sku))

    staticsite_deployment_properties = StaticSiteARMResource(
        location=existing_staticsite.location,
        tags=existing_staticsite.tags,
        repository_url=source or existing_staticsite.repository_url,
        branch=branch or existing_staticsite.branch,
        repository_token=token or existing_staticsite.repository_token,
        build_properties=existing_staticsite.build_properties,
        sku=sku_def or existing_staticsite.sku)

    client = _get_staticsites_client_factory(cmd.cli_ctx)
    resource_group_name = _get_resource_group_name_of_staticsite(client, name)
    return sdk_no_wait(no_wait, client.update_static_site,
                       resource_group_name=resource_group_name, name=name,
                       static_site_envelope=staticsite_deployment_properties)


def delete_staticsite(cmd, name, resource_group_name=None, no_wait=False):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    return sdk_no_wait(no_wait, client.delete_static_site,
                       resource_group_name=resource_group_name, name=name)


def _parse_pair(pair, delimiter):
    if delimiter not in pair:
        CLIError("invalid format of pair {0}".format(pair))

    index = pair.index(delimiter)
    return pair[:index], pair[1 + index:]


def _get_staticsite_location(client, static_site_name, resource_group_name):
    static_sites = client.list()
    for static_site in static_sites:
        if static_site.name.lower() == static_site_name.lower():
            found_rg = _parse_resource_group_from_arm_id(static_site.id)
            if found_rg:
                if found_rg.lower() == resource_group_name.lower():
                    return static_site.location

    raise CLIError("Static site was '{}' not found in subscription and resource group '{}'."
                   .format(static_site_name, resource_group_name))


def _get_resource_group_name_of_staticsite(client, static_site_name):
    static_sites = client.list()
    for static_site in static_sites:
        if static_site.name.lower() == static_site_name.lower():
            resource_group = _parse_resource_group_from_arm_id(static_site.id)
            if resource_group:
                return resource_group

    raise CLIError("Static site was '{}' not found in subscription.".format(static_site_name))


def _parse_resource_group_from_arm_id(arm_id):
    from msrestazure.tools import parse_resource_id
    components = parse_resource_id(arm_id)
    rg_key = 'resource_group'
    if rg_key not in components:
        return None

    return components['resource_group']


def _get_staticsites_client_factory(cli_ctx, api_version=None):
    from azure.mgmt.web import WebSiteManagementClient
    client = get_mgmt_service_client(cli_ctx, WebSiteManagementClient).static_sites
    if api_version:
        client.api_version = api_version
    return client


def _find_authentication_provider(client, resource_group_name, name, user_id, authentication_provider):
    users = client.list_static_site_users(resource_group_name, name, 'all')
    for user in users:
        if user.name.lower() == user_id.lower():
            authentication_provider = user.provider

    if not authentication_provider:
        raise CLIError("user id was not found.")

    return authentication_provider


def _find_user_id_and_authentication_provider(client, resource_group_name, name,
                                              user_id, authentication_provider, user_details):
    users = client.list_static_site_users(resource_group_name, name, 'all')
    for user in users:
        if user.display_name.lower() == user_details.lower():
            if not authentication_provider:
                authentication_provider = user.provider
                user_id = user.name
            else:
                if user.provider.lower() == authentication_provider.lower():
                    user_id = user.name

    if not user_id or not authentication_provider:
        raise CLIError("user details and authentication provider was not found.")

    return user_id, authentication_provider
