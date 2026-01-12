# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import os
import urllib
import urllib3
import certifi
from datetime import datetime

from knack.log import get_logger

from azure.cli.core.azclierror import (RequiredArgumentMissingError, ValidationError, ResourceNotFoundError,
                                       CLIInternalError)
from azure.cli.core.commands.parameters import get_subscription_locations
from azure.cli.core.util import should_disable_connection_verify, send_raw_request
from azure.cli.core.commands.client_factory import get_subscription_id

from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id, resource_id

from ._client_factory import web_client_factory, providers_client_factory
from ._constants import LOGICAPP_KIND, FUNCTIONAPP_KIND, LINUXAPP_KIND

logger = get_logger(__name__)

REQUESTS_CA_BUNDLE = "REQUESTS_CA_BUNDLE"


# get a RID when the name may be an RID
def get_resource_id(cmd, name, resource_group, namespace, type, **rid_kwargs):  # pylint: disable=redefined-builtin
    if is_valid_resource_id(name):
        return name
    return resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                       resource_group=resource_group,
                       name=name,
                       namespace=namespace,
                       type=type,
                       **rid_kwargs)


# get a resource's name and group when the name may be an RID
def get_resource_name_and_group(cmd, name, resource_group, namespace, type, **rid_kwargs):  # pylint: disable=redefined-builtin
    rid = get_resource_id(cmd, name, resource_group, namespace, type, **rid_kwargs)
    rid_parsed = parse_resource_id(rid)
    return rid_parsed.get("name"), rid_parsed.get("resource_group"), rid


def str2bool(v):
    if v == 'true':
        retval = True
    elif v == 'false':
        retval = False
    else:
        retval = None
    return retval


def _normalize_sku(sku):
    sku = sku.upper()
    if sku == 'FREE':
        return 'F1'
    if sku == 'SHARED':
        return 'D1'
    return sku


def get_sku_tier(name):  # pylint: disable=too-many-return-statements
    name = name.upper()
    if name in ['F1', 'FREE']:
        return 'FREE'
    if name in ['D1', "SHARED"]:
        return 'SHARED'
    if name in ['B1', 'B2', 'B3', 'BASIC']:
        return 'BASIC'
    if name in ['S1', 'S2', 'S3']:
        return 'STANDARD'
    if name in ['P1', 'P2', 'P3']:
        return 'PREMIUM'
    if name in ['P1V2', 'P2V2', 'P3V2']:
        return 'PREMIUMV2'
    if name in ['P0V3']:
        return 'PREMIUM0V3'
    if name in ['P1V3', 'P2V3', 'P3V3']:
        return 'PREMIUMV3'
    if name in ['P1MV3', 'P2MV3', 'P3MV3', 'P4MV3', 'P5MV3']:
        return 'PREMIUMMV3'
    if name in ['P0V4', 'P1V4', 'P2V4', 'P3V4']:
        return 'PREMIUMV4'
    if name in ['P1MV4', 'P2MV4', 'P3MV4', 'P4MV4', 'P5MV4']:
        return 'PREMIUMMV4'
    if name in ['PC2', 'PC3', 'PC4']:
        return 'PremiumContainer'
    if name in ['EP1', 'EP2', 'EP3']:
        return 'ElasticPremium'
    if name in ['I1V2', 'I2V2', 'I3V2', 'I4V2', 'I5V2', 'I6V2']:
        return 'IsolatedV2'
    if name in ['I1MV2', 'I2MV2', 'I3MV2', 'I4MV2', 'I5MV2']:
        return 'IsolatedMV2'
    if name in ['WS1', 'WS2', 'WS3']:
        return 'WorkflowStandard'
    raise ValidationError("Invalid sku(pricing tier), please refer to command help for valid values")


# Deprecated; Do not use
# Keeping this for now so that we don't break extensions that use it
def get_sku_name(tier):
    return get_sku_tier(name=tier)


def is_sku_tier_enabled_for_managed_instance(sku_tier):
    sku_tier = sku_tier.upper()
    enabled_skus = ['PREMIUMV4', 'PREMIUMMV4']
    return sku_tier in enabled_skus


# resource is client.web_apps for webapps, client.app_service_plans for ASPs, etc.
def get_resource_if_exists(resource, **kwargs):
    from azure.core.exceptions import ResourceNotFoundError as R

    try:
        return resource.get(**kwargs)
    except (R, ValueError):
        return None


def normalize_sku_for_staticapp(sku):
    if sku.lower() == 'free':
        return 'Free'
    if sku.lower() == 'standard':
        return 'Standard'
    if sku.lower() == 'dedicated':
        return 'Dedicated'
    raise ValidationError("Invalid sku(pricing tier), please refer to command help for valid values")


def retryable_method(retries=3, interval_sec=5, excpt_type=Exception):
    def decorate(func):
        def call(*args, **kwargs):
            current_retry = retries
            while True:
                try:
                    return func(*args, **kwargs)
                except excpt_type:  # pylint: disable=broad-except
                    current_retry -= 1
                    if current_retry <= 0:
                        raise
                time.sleep(interval_sec)
        return call
    return decorate


def register_app_provider(cmd):
    from azure.mgmt.resource.resources.models import ProviderRegistrationRequest, ProviderConsentDefinition

    namespace = "Microsoft.App"
    providers_client = providers_client_factory(cmd.cli_ctx)
    is_registered = False
    try:
        registration_state = providers_client.get(namespace).registration_state
        is_registered = registration_state and registration_state.lower() == 'registered'
    except Exception:  # pylint: disable=broad-except
        logger.warning("An error occurred while trying to get the registration state of the '%s' provider.", namespace)

    if not is_registered:
        try:
            logger.warning("Registering the '%s' provider.", namespace)
            properties = ProviderRegistrationRequest(
                third_party_provider_consent=ProviderConsentDefinition(consent_to_authorization=True))
            providers_client.register(namespace, properties=properties)
            timeout_secs = 120
            start_time = datetime.now()
            while not is_registered:
                time.sleep(5)
                registration_state = providers_client.get(namespace).registration_state
                is_registered = registration_state and registration_state.lower() == 'registered'
                if not is_registered and (datetime.now() - start_time).seconds >= timeout_secs:
                    raise CLIInternalError("Timed out waiting for the '%s' provider to register." % namespace)
            logger.warning("Successfully registered the '%s' provider.", namespace)
        except Exception as ex:  # pylint: disable=broad-except
            logger.warning("An error occurred while trying to register the '%s' provider: %s", namespace, str(ex))


def raise_missing_token_suggestion():
    pat_documentation = "https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line"
    raise RequiredArgumentMissingError("GitHub access token is required to authenticate to your repositories. "
                                       "If you need to create a Github Personal Access Token, "
                                       "please run with the '--login-with-github' flag or follow "
                                       "the steps found at the following link:\n{0}".format(pat_documentation))


def raise_missing_ado_token_suggestion():
    pat_documentation = ("https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-"
                         "tokens-to-authenticate?view=azure-devops&tabs=Windows#create-a-pat")
    raise RequiredArgumentMissingError("If this repo is an Azure Dev Ops repo, please provide a Personal Access Token."
                                       "Please run with the '--login-with-ado' flag or follow "
                                       "the steps found at the following link:\n{0}".format(pat_documentation))


def _get_location_from_resource_group(cli_ctx, resource_group_name):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    group = client.resource_groups.get(resource_group_name)
    return group.location


def is_centauri_functionapp(cmd, resource_group, name):
    client = web_client_factory(cmd.cli_ctx)
    functionapp = client.web_apps.get(resource_group, name)
    return functionapp.managed_environment_id is not None


def is_flex_functionapp(cli_ctx, resource_group, name):
    app = get_raw_functionapp(cli_ctx, resource_group, name)
    if app["properties"]["serverFarmId"] is None:
        return False
    sku = app["properties"]["sku"]
    return sku and sku.lower() == 'flexconsumption'


def _list_app(cli_ctx, resource_group_name=None):
    client = web_client_factory(cli_ctx)
    if resource_group_name:
        result = list(client.web_apps.list_by_resource_group(resource_group_name))
    else:
        result = list(client.web_apps.list())
    for webapp in result:
        _rename_server_farm_props(webapp)
    return result


def _rename_server_farm_props(webapp):
    # Should be renamed in SDK in a future release
    setattr(webapp, 'app_service_plan_id', webapp.server_farm_id)
    del webapp.server_farm_id
    return webapp


def get_raw_functionapp(cli_ctx, resource_group_name, name):
    site_url_base = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Web/sites/{}?api-version={}'
    subscription_id = get_subscription_id(cli_ctx)
    site_url = site_url_base.format(subscription_id, resource_group_name, name, '2023-12-01')
    request_url = cli_ctx.cloud.endpoints.resource_manager + site_url
    response = send_raw_request(cli_ctx, "GET", request_url)
    return response.json()


def _get_location_from_webapp(client, resource_group_name, webapp):
    webapp = client.web_apps.get(resource_group_name, webapp)
    if not webapp:
        raise ResourceNotFoundError("'{}' app doesn't exist".format(webapp))
    return webapp.location


def _normalize_flex_location(location):
    return location.lower().replace(" ", "")


# can't just normalize locations with location.lower().replace(" ", "") because of UAE/UK regions
def _normalize_location(cmd, location):
    location = location.lower()
    locations = get_subscription_locations(cmd.cli_ctx)
    for loc in locations:
        if loc.display_name.lower() == location or loc.name.lower() == location:
            return loc.name
    return location


def _remove_list_duplicates(webapp):
    outbound_ips = webapp.possible_outbound_ip_addresses.split(',')
    outbound_ips_list = list(dict.fromkeys(outbound_ips))
    outbound_ips_list.sort()
    outbound_ips = ','.join(outbound_ips_list)
    del webapp.possible_outbound_ip_addresses
    setattr(webapp, 'possible_outbound_ip_addresses', outbound_ips)


def get_pool_manager(url):
    proxies = urllib.request.getproxies()
    bypass_proxy = urllib.request.proxy_bypass(urllib.parse.urlparse(url).hostname)

    if 'https' in proxies and not bypass_proxy:
        proxy = urllib.parse.urlparse(proxies['https'])

        if proxy.username and proxy.password:
            proxy_headers = urllib3.util.make_headers(proxy_basic_auth='{0}:{1}'.format(proxy.username, proxy.password))
            logger.debug('Setting proxy-authorization header for basic auth')
        else:
            proxy_headers = None

        logger.info('Using proxy for app service tunnel connection')
        http = urllib3.ProxyManager(proxy.geturl(), proxy_headers=proxy_headers)
    else:
        http = urllib3.PoolManager()

    if should_disable_connection_verify():
        http.connection_pool_kw['cert_reqs'] = 'CERT_NONE'
    else:
        http.connection_pool_kw['cert_reqs'] = 'CERT_REQUIRED'
        if REQUESTS_CA_BUNDLE in os.environ:
            ca_bundle_file = os.environ[REQUESTS_CA_BUNDLE]
            logger.debug("Using CA bundle file at '%s'.", ca_bundle_file)
            if not os.path.isfile(ca_bundle_file):
                raise ValidationError('REQUESTS_CA_BUNDLE environment variable is specified with an invalid file path')
        else:
            ca_bundle_file = certifi.where()
        http.connection_pool_kw['ca_certs'] = ca_bundle_file
    return http


def get_app_service_plan_from_webapp(cmd, webapp, api_version=None):
    client = web_client_factory(cmd.cli_ctx, api_version=api_version)
    plan = parse_resource_id(webapp.server_farm_id)
    return client.app_service_plans.get(plan['resource_group'], plan['name'])


def app_service_plan_exists(cmd, resource_group_name, plan, api_version=None):
    from azure.core.exceptions import ResourceNotFoundError as RNFR
    exists = True
    try:
        client = web_client_factory(cmd.cli_ctx, api_version=api_version)
        client.app_service_plans.get(resource_group_name, plan)
    except RNFR:
        exists = False
    return exists


# Allows putting additional properties on an SDK model instance
def use_additional_properties(resource):
    resource.enable_additional_properties_sending()
    existing_properties = resource.serialize().get("properties")
    resource.additional_properties["properties"] = {} if existing_properties is None else existing_properties


def repo_url_to_name(repo_url):
    repo = None
    repo = [s for s in repo_url.split('/') if s]
    if len(repo) >= 2:
        repo = '/'.join(repo[-2:])
    return repo


def get_token(cmd, repo, token):
    from ._github_oauth import load_github_token_from_cache, get_github_access_token
    if not repo:
        return None
    if token:
        return token
    token = load_github_token_from_cache(cmd, repo)
    if not token:
        token = get_github_access_token(cmd, ["admin:repo_hook", "repo", "workflow"], token)
    return token


def is_logicapp(app):
    if app is None or app.kind is None:
        return False
    return LOGICAPP_KIND in app.kind


def is_functionapp(app):
    if app is None or app.kind is None:
        return False
    return not is_logicapp(app) and FUNCTIONAPP_KIND in app.kind


def is_webapp(app):
    if app is None or app.kind is None:
        return False
    return not is_logicapp(app) and not is_functionapp(app) and "app" in app.kind


def is_linux_webapp(app):
    if not is_webapp(app):
        return False
    return LINUXAPP_KIND in app.kind
