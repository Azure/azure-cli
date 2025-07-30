# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.util import sdk_no_wait, send_raw_request

from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.azclierror import (ResourceNotFoundError, ValidationError, RequiredArgumentMissingError,
                                       InvalidArgumentValueError, UnauthorizedError)
from azure.mgmt.core.tools import parse_resource_id
from knack.log import get_logger
from urllib.parse import urlparse
import uuid
from datetime import datetime, timedelta

from .utils import normalize_sku_for_staticapp, raise_missing_token_suggestion, raise_missing_ado_token_suggestion
from .custom import show_app, _build_identities_info
from ._client_factory import providers_client_factory


logger = get_logger(__name__)


# remove irrelevant attributes from staticsites printed to the user
def _format_staticsite(site, format_site=False):
    if format_site:
        props_to_remove = {"allow_config_file_updates",
                           "build_properties",
                           "content_distribution_endpoint",
                           "key_vault_reference_identity",
                           "kind",
                           "private_endpoint_connections",
                           "repository_token",
                           "staging_environment_policy",
                           "template_properties"}
        sku_props_to_remove = {"capabilities",
                               "capacity",
                               "family",
                               "locations",
                               "size",
                               "sku_capacity"}
        for p in sku_props_to_remove:
            if hasattr(site.sku, p):
                delattr(site.sku, p)
        for p in props_to_remove:
            if hasattr(site, p):
                delattr(site, p)
    return site


def list_staticsites(cmd, resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if resource_group_name:
        return list(client.get_static_sites_by_resource_group(resource_group_name))
    return list(client.list())


def show_staticsite(cmd, name, resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    return client.get_static_site(resource_group_name, name)


def disconnect_staticsite(cmd, name, resource_group_name=None, no_wait=False):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    return sdk_no_wait(no_wait, client.begin_detach_static_site,
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


def delete_staticsite_environment(cmd, name, environment_name='default', resource_group_name=None, no_wait=False):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    return sdk_no_wait(no_wait, client.begin_delete_static_site_build,
                       resource_group_name, name, environment_name)


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


def set_staticsite_domain(cmd, name, hostname, resource_group_name=None, no_wait=False,
                          validation_method="cname-delegation"):
    from azure.mgmt.web.models import StaticSiteCustomDomainRequestPropertiesARMResource

    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    domain_envelope = StaticSiteCustomDomainRequestPropertiesARMResource(validation_method=validation_method)

    client.begin_validate_custom_domain_can_be_added_to_static_site(resource_group_name,
                                                                    name, hostname, domain_envelope)

    if validation_method.lower() == "dns-txt-token":
        validation_cmd = ("az staticwebapp hostname show -n {} -g {} "
                          "--hostname {} --query \"validationToken\"".format(name,
                                                                             resource_group_name,
                                                                             hostname))
        logger.warning("To get the TXT validation token, please run '%s'. "
                       "It may take a few minutes to generate the validation token.", validation_cmd)

    if no_wait is False:
        logger.warning("Waiting for validation to finish...")

    return sdk_no_wait(no_wait, client.begin_create_or_update_static_site_custom_domain,
                       resource_group_name=resource_group_name, name=name, domain_name=hostname,
                       static_site_custom_domain_request_properties_envelope=domain_envelope)


def get_staticsite_domain(cmd, name, hostname, resource_group_name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.get_static_site_custom_domain(resource_group_name=resource_group_name,
                                                name=name, domain_name=hostname)


def delete_staticsite_domain(cmd, name, hostname, resource_group_name=None, no_wait=False):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    logger.warning("After deleting a custom domain, there can be a 15 minute delay for the change to propagate.")
    return sdk_no_wait(no_wait, client.begin_delete_static_site_custom_domain,
                       resource_group_name=resource_group_name, name=name, domain_name=hostname)


def show_identity(cmd, resource_group_name, name):
    return show_staticsite(cmd, name, resource_group_name).identity


def assign_identity(cmd, resource_group_name, name, assign_identities=None, role='Contributor', scope=None):
    #  TODO : A lot of this code is duplicated, we should reuse the existing code
    ManagedServiceIdentity, ResourceIdentityType = cmd.get_models('ManagedServiceIdentity',
                                                                  'ManagedServiceIdentityType')
    UserAssignedIdentitiesValue = cmd.get_models('UserAssignedIdentity')
    _, _, external_identities, enable_local_identity = _build_identities_info(assign_identities)

    def getter():
        client = _get_staticsites_client_factory(cmd.cli_ctx)
        return client.get_static_site(resource_group_name=resource_group_name, name=name)

    def setter(staticsite):
        if staticsite.identity and staticsite.identity.type == ResourceIdentityType.system_assigned_user_assigned:
            identity_types = ResourceIdentityType.system_assigned_user_assigned
        elif staticsite.identity and staticsite.identity.type == ResourceIdentityType.system_assigned and external_identities:  # pylint: disable=line-too-long
            identity_types = ResourceIdentityType.system_assigned_user_assigned
        elif staticsite.identity and staticsite.identity.type == ResourceIdentityType.user_assigned and enable_local_identity:  # pylint: disable=line-too-long
            identity_types = ResourceIdentityType.system_assigned_user_assigned
        elif external_identities and enable_local_identity:
            identity_types = ResourceIdentityType.system_assigned_user_assigned
        elif external_identities:
            identity_types = ResourceIdentityType.user_assigned
        else:
            identity_types = ResourceIdentityType.system_assigned

        if staticsite.identity:
            staticsite.identity.type = identity_types
        else:
            staticsite.identity = ManagedServiceIdentity(type=identity_types)
        if external_identities:
            if not staticsite.identity.user_assigned_identities:
                staticsite.identity.user_assigned_identities = {}
            for identity in external_identities:
                staticsite.identity.user_assigned_identities[identity] = UserAssignedIdentitiesValue()

        client = _get_staticsites_client_factory(cmd.cli_ctx)
        poller = client.begin_create_or_update_static_site(resource_group_name, name, staticsite)

        return LongRunningOperation(cmd.cli_ctx)(poller)

    from azure.cli.core.commands.arm import assign_identity as _assign_identity
    staticsite = _assign_identity(cmd.cli_ctx, getter, setter, role, scope)
    return staticsite.identity


def remove_identity(cmd, resource_group_name, name, remove_identities=None):
    IdentityType = cmd.get_models('ManagedServiceIdentityType')
    UserAssignedIdentitiesValue = cmd.get_models('Components1Jq1T4ISchemasManagedserviceidentityPropertiesUserassignedidentitiesAdditionalproperties')  # pylint: disable=line-too-long
    _, _, external_identities, remove_local_identity = _build_identities_info(remove_identities)

    def getter():
        client = _get_staticsites_client_factory(cmd.cli_ctx)
        return client.get_static_site(resource_group_name=resource_group_name, name=name)

    def setter(staticsite):
        if staticsite.identity is None:
            return staticsite
        to_remove = []
        existing_identities = {x.lower() for x in list((staticsite.identity.user_assigned_identities or {}).keys())}
        if external_identities:
            to_remove = {x.lower() for x in external_identities}
            non_existing = to_remove.difference(existing_identities)
            if non_existing:
                raise ValidationError("'{}' are not associated with '{}'".format(','.join(non_existing), name))
            if not list(existing_identities - to_remove):
                if staticsite.identity.type == IdentityType.user_assigned:
                    staticsite.identity.type = IdentityType.none
                elif staticsite.identity.type == IdentityType.system_assigned_user_assigned:
                    staticsite.identity.type = IdentityType.system_assigned

        staticsite.identity.user_assigned_identities = None
        if remove_local_identity:
            staticsite.identity.type = (IdentityType.none
                                        if staticsite.identity.type == IdentityType.system_assigned or
                                        staticsite.identity.type == IdentityType.none
                                        else IdentityType.user_assigned)

        if staticsite.identity.type not in [IdentityType.none, IdentityType.system_assigned]:
            staticsite.identity.user_assigned_identities = {}
        if to_remove:
            for identity in list(existing_identities - to_remove):
                staticsite.identity.user_assigned_identities[identity] = UserAssignedIdentitiesValue()
        else:
            for identity in list(existing_identities):
                staticsite.identity.user_assigned_identities[identity] = UserAssignedIdentitiesValue()

        client = _get_staticsites_client_factory(cmd.cli_ctx)
        poller = client.begin_create_or_update_static_site(resource_group_name, name, staticsite)
        return LongRunningOperation(cmd.cli_ctx)(poller)

    from azure.cli.core.commands.arm import assign_identity as _assign_identity
    staticsite = _assign_identity(cmd.cli_ctx, getter, setter)
    return staticsite.identity


def list_staticsite_functions(cmd, name, resource_group_name=None, environment_name='default'):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    return client.list_static_site_build_functions(resource_group_name, name, environment_name)


def list_staticsite_app_settings(cmd, name, resource_group_name=None, environment_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    if not environment_name:
        return client.list_static_site_app_settings(resource_group_name, name)

    return client.list_static_site_build_app_settings(resource_group_name, name, environment_name)


def set_staticsite_app_settings(cmd, name, setting_pairs, resource_group_name=None, environment_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    setting_dict = {}
    for pair in setting_pairs:
        key, value = _parse_pair(pair, "=")
        setting_dict[key] = value

    # fetch current settings to prevent deleting existing app settings
    app_settings = list_staticsite_app_settings(cmd, name, resource_group_name, environment_name)
    for k, v in setting_dict.items():
        app_settings.properties[k] = v

    if not environment_name:
        result = client.create_or_update_static_site_app_settings(
            resource_group_name, name, app_settings=app_settings)
    else:
        result = client.create_or_update_static_site_build_app_settings(
            resource_group_name, name, environment_name, app_settings=app_settings)

    return _redact_appsettings(result)


def delete_staticsite_app_settings(cmd, name, setting_names, resource_group_name=None, environment_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    app_settings = list_staticsite_app_settings(cmd, name, resource_group_name, environment_name)

    for key in setting_names:
        if key in app_settings.properties:
            app_settings.properties.pop(key)
        else:
            logger.warning("key '%s' not found in app settings", key)

    if not environment_name:
        result = client.create_or_update_static_site_app_settings(
            resource_group_name, name, app_settings=app_settings)
    else:
        result = client.create_or_update_static_site_build_app_settings(
            resource_group_name, name, environment_name, app_settings=app_settings)

    return _redact_appsettings(result)


def _redact_appsettings(payload):
    logger.warning('App settings have been redacted. Use `az staticwebapp appsettings list` to view.')
    for x in payload.properties:
        payload.properties[x] = None
    return payload


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
    from azure.mgmt.web.models import StaticSiteUserARMResource

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
        raise RequiredArgumentMissingError("Either user id or user details is required.")

    user_envelope = StaticSiteUserARMResource(roles=roles)

    return client.update_static_site_user(resource_group_name,
                                          name, authentication_provider, user_id,
                                          static_site_user_envelope=user_envelope)


def _get_ado_token(cmd, source):
    ado_organization = [p for p in urlparse(source).path.split("/") if p][0]
    resource = cmd.cli_ctx.cloud.endpoints.active_directory_resource_id

    url = "https://app.vssps.visualstudio.com/_apis/profile/profiles/me?api-version=5.1"
    user_id = send_raw_request(cmd.cli_ctx, "GET", url, resource=resource).json()["id"]

    url = f"https://app.vssps.visualstudio.com/_apis/accounts?api-version=5.1&memberId={user_id}"
    orgs = send_raw_request(cmd.cli_ctx, "GET", url, resource=resource).json()["value"]
    org_id = [o for o in orgs if o["accountName"].lower() == ado_organization.lower()][0]["accountId"]

    url = f"https://vssps.dev.azure.com/{ado_organization}/_apis/tokens/pats?api-version=7.1-preview.1"
    body = {
        "displayName": f"SWA Deployment Token (created via the Azure CLI) - {uuid.uuid4().hex}",
        "scope": "vso.build_execute vso.code_full vso.variablegroups_manage",
        "validTo": (datetime.utcnow() + timedelta(days=6 * 30)).isoformat(),
        "allOrgs": False,
        "targetAccounts": [org_id],
    }
    return send_raw_request(cmd.cli_ctx,
                            "POST",
                            url,
                            resource=resource,
                            body=json.dumps(body)).json()["patToken"]["token"]


def create_staticsites(cmd, resource_group_name, name, location="centralus",  # pylint: disable=too-many-locals,
                       source=None, branch=None, token=None,
                       app_location="/", api_location=None, output_location=None,
                       tags=None, no_wait=False, sku='Free', login_with_github=False, login_with_ado=False,
                       format_output=True):
    from azure.core.exceptions import ResourceNotFoundError as _ResourceNotFoundError

    try:
        site = show_staticsite(cmd, name, resource_group_name)
        logger.warning("Static Web App %s already exists in resource group %s", name, resource_group_name)
        return site
    except _ResourceNotFoundError:
        pass

    is_github = source and "github.com/" in source

    if source and ("https://" not in source and "http://" not in source):
        source = f"https://{source}"  # urlparse doesn't split the url properly without a scheme

    if source or branch or login_with_github or login_with_ado or token:
        if not source:
            raise ValidationError("--source is required to make a static web app connected to a repo")
        if not branch:
            raise ValidationError("--branch is required to make a static web app connected to a repo")
        if not token and not (login_with_github or login_with_ado):
            if is_github:
                raise_missing_token_suggestion()
            else:
                raise_missing_ado_token_suggestion()
        elif not token:
            if login_with_github:
                from ._github_oauth import get_github_access_token
                scopes = ["admin:repo_hook", "repo", "workflow"]
                token = get_github_access_token(cmd, scopes)
            if login_with_ado:
                token = _get_ado_token(cmd, source)
        else:
            if login_with_github:
                logger.warning("Both token and --login-with-github flag are provided. Will use provided token")
            if login_with_ado:
                logger.warning("Both token and --login-with-ado flag are provided. Will use provided token")

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
    if not no_wait and format_output:
        client.begin_create_or_update_static_site(resource_group_name=resource_group_name, name=name,
                                                  static_site_envelope=staticsite_deployment_properties)
        return show_staticsite(cmd, name, resource_group_name)
    return sdk_no_wait(no_wait, client.begin_create_or_update_static_site,
                       resource_group_name=resource_group_name, name=name,
                       static_site_envelope=staticsite_deployment_properties)


def update_staticsite(cmd, name, resource_group_name=None, source=None, branch=None, token=None,
                      tags=None, sku=None, no_wait=False):
    existing_staticsite = show_staticsite(cmd, name, resource_group_name)
    if not existing_staticsite:
        raise ResourceNotFoundError(f"No static web app found with name {name} in group {resource_group_name}")

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
    if resource_group_name is None:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)
    return sdk_no_wait(no_wait, client.update_static_site,
                       resource_group_name=resource_group_name, name=name,
                       static_site_envelope=staticsite_deployment_properties)


def delete_staticsite(cmd, name, resource_group_name=None, no_wait=False):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    return sdk_no_wait(no_wait, client.begin_delete_static_site,
                       resource_group_name=resource_group_name, name=name)


def _parse_pair(pair, delimiter):
    if delimiter not in pair:
        raise InvalidArgumentValueError("invalid format of pair {0}".format(pair))

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

    raise ResourceNotFoundError(f"Static site was '{static_site_name}' not found in subscription "
                                f"and resource group '{resource_group_name}'.")


def _get_resource_group_name_of_staticsite(client, static_site_name):
    static_sites = client.list()
    for static_site in static_sites:
        if static_site.name.lower() == static_site_name.lower():
            resource_group = _parse_resource_group_from_arm_id(static_site.id)
            if resource_group:
                return resource_group

    raise ResourceNotFoundError(f"Static site was '{static_site_name}' not found in subscription.")


def _parse_resource_group_from_arm_id(arm_id):
    components = parse_resource_id(arm_id)
    rg_key = 'resource_group'
    if rg_key not in components:
        return None

    return components['resource_group']


def _get_staticsites_client_factory(cli_ctx, api_version=None):
    from azure.mgmt.web import WebSiteManagementClient
    client = get_mgmt_service_client(cli_ctx, WebSiteManagementClient, api_version=api_version).static_sites
    if api_version:
        client.api_version = api_version
    return client


def _find_authentication_provider(client, resource_group_name, name, user_id, authentication_provider):
    users = client.list_static_site_users(resource_group_name, name, 'all')
    for user in users:
        if user.name.lower() == user_id.lower():
            authentication_provider = user.provider

    if not authentication_provider:
        raise ResourceNotFoundError("user id was not found.")

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
        raise ResourceNotFoundError("user details and authentication provider was not found.")

    return user_id, authentication_provider


def list_staticsite_secrets(cmd, name, resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    return client.list_static_site_secrets(resource_group_name=resource_group_name, name=name)


def reset_staticsite_api_key(cmd, name, resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if not resource_group_name:
        resource_group_name = _get_resource_group_name_of_staticsite(client, name)

    existing_staticsite = show_staticsite(cmd, name, resource_group_name)
    ResetPropertiesEnvelope = cmd.get_models('StaticSiteResetPropertiesARMResource')
    reset_envelope = ResetPropertiesEnvelope(repository_token=existing_staticsite.repository_token)
    return client.reset_static_site_api_key(resource_group_name=resource_group_name,
                                            name=name,
                                            reset_properties_envelope=reset_envelope)


def link_user_function(
    cmd,
    name,
    resource_group_name,
    function_resource_id,
    environment_name=None,
    force=False,
):
    from azure.mgmt.web.models import StaticSiteUserProvidedFunctionAppARMResource

    if force:
        logger.warning("--force: overwriting static webapp connection with this function if one exists")

    parsed_rid = parse_resource_id(function_resource_id)
    function_name = parsed_rid["name"]
    function_group = parsed_rid["resource_group"]
    function_location = show_app(cmd, resource_group_name=function_group, name=function_name).location

    client = _get_staticsites_client_factory(cmd.cli_ctx)
    function = StaticSiteUserProvidedFunctionAppARMResource(function_app_resource_id=function_resource_id,
                                                            function_app_region=function_location)

    if environment_name is None:
        # Special casing since the type of the created resource differ
        return client.begin_register_user_provided_function_app_with_static_site(
            name=name,
            resource_group_name=resource_group_name,
            function_app_name=function_name,
            static_site_user_provided_function_envelope=function,
            is_forced=force)

    return client.begin_register_user_provided_function_app_with_static_site_build(
        name=name,
        resource_group_name=resource_group_name,
        function_app_name=function_name,
        environment_name=environment_name,
        static_site_user_provided_function_envelope=function,
        is_forced=force)


def unlink_user_function(cmd, name, resource_group_name):
    function_name = list(get_user_function(cmd, name, resource_group_name))[0].name
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.detach_user_provided_function_app_from_static_site(
        name=name,
        resource_group_name=resource_group_name,
        function_app_name=function_name)


def get_user_function(cmd, name, resource_group_name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.get_user_provided_function_apps_for_static_site(name=name, resource_group_name=resource_group_name)


def validate_backend(cmd, name, resource_group_name, backend_resource_id,
                     backend_region=None, environment_name='default'):
    from azure.mgmt.web.models import StaticSiteLinkedBackendARMResource

    parsed_rid = parse_resource_id(backend_resource_id)
    backend_name = parsed_rid["name"]

    backend = StaticSiteLinkedBackendARMResource(
        backend_resource_id=backend_resource_id,
        region=backend_region)

    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.begin_validate_backend_for_build(
        name=name,
        resource_group_name=resource_group_name,
        linked_backend_name=backend_name,
        static_site_linked_backend_envelope=backend,
        environment_name=environment_name)


def link_backend(cmd, name, resource_group_name, backend_resource_id, backend_region=None, environment_name='default'):
    from azure.mgmt.web.models import StaticSiteLinkedBackendARMResource

    parsed_rid = parse_resource_id(backend_resource_id)
    backend_name = parsed_rid["name"]

    backend = StaticSiteLinkedBackendARMResource(
        backend_resource_id=backend_resource_id,
        region=backend_region)

    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.begin_link_backend_to_build(
        name=name,
        resource_group_name=resource_group_name,
        linked_backend_name=backend_name,
        static_site_linked_backend_envelope=backend,
        environment_name=environment_name)


def unlink_backend(cmd, name, resource_group_name, remove_backend_auth=False, environment_name='default'):
    if remove_backend_auth:
        logger.warning("Please note that using parameter --remove-backend-auth will "
                       "remove auth configuration from backend")

    backend_name = list(get_backend(cmd, name, resource_group_name, environment_name))[0].name

    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.unlink_backend_from_build(
        name=name,
        resource_group_name=resource_group_name,
        linked_backend_name=backend_name,
        environment_name=environment_name,
        is_cleaning_auth_config=remove_backend_auth)


def get_backend(cmd, name, resource_group_name, environment_name='default'):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.get_linked_backends_for_build(
        name=name,
        resource_group_name=resource_group_name,
        environment_name=environment_name)


def _enterprise_edge_warning():
    logger.warning("For optimal experience and availability please check our documentation https://aka.ms/swaedge")


def _update_enterprise_edge(cmd, name, resource_group_name, enable: bool):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    site = client.get_static_site(resource_group_name, name)
    site.enterprise_grade_cdn_status = "enabled" if enable else "disabled"
    return client.update_static_site(resource_group_name=resource_group_name, name=name, static_site_envelope=site)


def _register_cdn_provider(cmd):
    from azure.mgmt.resource.resources.models import ProviderRegistrationRequest, ProviderConsentDefinition

    namespace = "Microsoft.CDN"
    properties = ProviderRegistrationRequest(third_party_provider_consent=ProviderConsentDefinition(
        consent_to_authorization=True))

    client = providers_client_factory(cmd.cli_ctx)
    try:
        client.register(namespace, properties=properties)
    except Exception as e:
        msg = "Server responded with error message : {} \n"\
              "Enabling enterprise-grade edge requires reregistration for the Azure Front "\
              "Door Microsoft.CDN resource provider. We were unable to perform that reregistration on your "\
              "behalf. Please check with your admin on permissions and review the documentation available at "\
              "https://go.microsoft.com/fwlink/?linkid=2185350. "\
              "Or try running registration manually with: az provider register --wait --namespace Microsoft.CDN"
        raise UnauthorizedError(msg.format(e.args)) from e


def enable_staticwebapp_enterprise_edge(cmd, name, resource_group_name, no_register=False):
    _enterprise_edge_warning()
    if not no_register:
        _register_cdn_provider(cmd)
    _update_enterprise_edge(cmd, name, resource_group_name, enable=True)
    return _get_enterprise_edge_status(cmd, name, resource_group_name)


def disable_staticwebapp_enterprise_edge(cmd, name, resource_group_name):
    _enterprise_edge_warning()
    _update_enterprise_edge(cmd, name, resource_group_name, enable=False)
    return _get_enterprise_edge_status(cmd, name, resource_group_name)


def _get_enterprise_edge_status(cmd, name, resource_group_name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    site = client.get_static_site(resource_group_name, name)
    return {"enterpriseGradeCdnStatus": site.enterprise_grade_cdn_status}


def show_staticwebapp_enterprise_edge_status(cmd, name, resource_group_name):
    _enterprise_edge_warning()
    return _get_enterprise_edge_status(cmd, name, resource_group_name)
