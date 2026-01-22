# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import ast
import threading
import time
import re
from xml.etree import ElementTree

from urllib.parse import quote, urlparse
from urllib.request import urlopen

from binascii import hexlify
from os import urandom
import datetime
import json
import ssl
import sys
import uuid
from functools import reduce
import invoke
from nacl import encoding, public

from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import hashes
from fabric import Connection

from knack.prompting import prompt_pass, NoTTYException, prompt_y_n
from knack.util import CLIError
from knack.log import get_logger

from azure.core.exceptions import HttpResponseError
from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id, resource_id

from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.applicationinsights import ApplicationInsightsManagementClient
from azure.mgmt.web.models import KeyInfo, SiteContainer, AuthType
from azure.mgmt.web import WebSiteManagementClient

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.progress import IndeterminateProgressBar
from azure.cli.core.util import shell_safe_json_parse, open_page_in_browser, get_json_object, \
    ConfiguredDefaultSetter
from azure.cli.core.util import get_az_user_agent, send_raw_request, get_file_json
from azure.cli.core.profiles import ResourceType, get_sdk
from azure.cli.core.azclierror import (InvalidArgumentValueError, MutuallyExclusiveArgumentError, ResourceNotFoundError,
                                       RequiredArgumentMissingError, ValidationError, CLIInternalError,
                                       UnclassifiedUserFault, AzureResponseError, AzureInternalError,
                                       ArgumentUsageError, FileOperationError)

from .tunnel import TunnelServer

from ._params import AUTH_TYPES, MULTI_CONTAINER_TYPES
from ._client_factory import (web_client_factory, ex_handler_factory, providers_client_factory,
                              appcontainers_client_factory)
from ._appservice_utils import _generic_site_operation, _generic_settings_operation
from ._appservice_utils import MSI_LOCAL_ID
from .utils import (_normalize_sku,
                    get_sku_tier,
                    retryable_method,
                    raise_missing_token_suggestion,
                    _get_location_from_resource_group,
                    _list_app,
                    is_functionapp,
                    is_linux_webapp,
                    _rename_server_farm_props,
                    _get_location_from_webapp,
                    _normalize_flex_location,
                    _normalize_location,
                    get_pool_manager, use_additional_properties, get_app_service_plan_from_webapp,
                    get_resource_if_exists, repo_url_to_name, get_token,
                    app_service_plan_exists, is_centauri_functionapp, is_flex_functionapp,
                    _remove_list_duplicates, get_raw_functionapp,
                    register_app_provider,
                    is_sku_tier_enabled_for_managed_instance)
from ._create_util import (zip_contents_from_dir, get_runtime_version_details, create_resource_group, get_app_details,
                           check_resource_group_exists, set_location, get_site_availability,
                           get_regional_site_availability, get_profile_username,
                           get_plan_to_use, get_lang_from_content, get_rg_to_use, get_sku_to_use,
                           detect_os_from_src, get_current_stack_from_runtime, generate_default_app_name,
                           get_or_create_default_workspace, get_or_create_default_resource_group,
                           get_workspace)
from ._constants import (FUNCTIONS_STACKS_API_KEYS, FUNCTIONS_LINUX_RUNTIME_VERSION_REGEX,
                         FUNCTIONS_WINDOWS_RUNTIME_VERSION_REGEX, PUBLIC_CLOUD,
                         LINUX_GITHUB_ACTIONS_WORKFLOW_TEMPLATE_PATH, WINDOWS_GITHUB_ACTIONS_WORKFLOW_TEMPLATE_PATH,
                         DOTNET_RUNTIME_NAME, NETCORE_RUNTIME_NAME, ASPDOTNET_RUNTIME_NAME, LINUX_OS_NAME,
                         WINDOWS_OS_NAME, LINUX_FUNCTIONAPP_GITHUB_ACTIONS_WORKFLOW_TEMPLATE_PATH,
                         WINDOWS_FUNCTIONAPP_GITHUB_ACTIONS_WORKFLOW_TEMPLATE_PATH, DEFAULT_CENTAURI_IMAGE,
                         VERSION_2022_09_01, FLEX_SUBNET_DELEGATION,
                         RUNTIME_STATUS_TEXT_MAP, LANGUAGE_EOL_DEPRECATION_NOTICES,
                         STORAGE_BLOB_DATA_CONTRIBUTOR_ROLE_ID)
from ._github_oauth import (get_github_access_token, cache_github_token)
from ._validators import validate_and_convert_to_int, validate_range_of_int_flag

from .aaz.latest.network.vnet import List as VNetList, Show as VNetShow
from .aaz.latest.network.vnet.subnet import Show as SubnetShow, Update as SubnetUpdate
from .aaz.latest.relay.hyco import Show as HyCoShow
from .aaz.latest.relay.hyco.authorization_rule import List as HycoAuthoList, Create as HycoAuthoCreate
from .aaz.latest.relay.hyco.authorization_rule.keys import List as HycoAuthoKeysList
from .aaz.latest.relay.namespace import List as NamespaceList
from .aaz.latest.appservice import ListLocations as AppServiceListLocations
from .aaz.latest.appservice.plan import (Show as AppServicePlanShow, Create as AppServicePlanCreate,
                                         Update as AppServicePlanUpdate)
from .aaz.latest.appservice.plan.managed_instance import (ShowRdpPassword
                                                          as AppServicePlanManagedInstanceShowRdpPassword)
from .aaz.latest.appservice.plan.managed_instance.instance import (List as AppServicePlanManagedInstanceList,
                                                                   Recycle as AppServicePlanManagedInstanceRecycle)

logger = get_logger(__name__)

# pylint:disable=no-member,too-many-lines,too-many-locals

# region "Common routines shared with quick-start extensions."
# Please maintain compatibility in both interfaces and functionalities"


def create_webapp(cmd, resource_group_name, name, plan, runtime=None, startup_file=None,  # pylint: disable=too-many-statements,too-many-branches
                  deployment_container_image_name=None, deployment_source_url=None, deployment_source_branch='master',
                  deployment_local_git=None, sitecontainers_app=None,
                  container_registry_password=None, container_registry_user=None,
                  container_registry_url=None, container_image_name=None,
                  multicontainer_config_type=None, multicontainer_config_file=None, tags=None,
                  using_webapp_up=False, language=None, assign_identities=None,
                  role='Contributor', scope=None, vnet=None, subnet=None, https_only=False,
                  public_network_access=None, acr_use_identity=False, acr_identity=None, basic_auth="",
                  auto_generated_domain_name_label_scope=None):
    from azure.mgmt.web.models import Site
    from azure.core.exceptions import ResourceNotFoundError as _ResourceNotFoundError
    SiteConfig, SkuDescription, NameValuePair = cmd.get_models(
        'SiteConfig', 'SkuDescription', 'NameValuePair')

    if deployment_source_url and deployment_local_git:
        raise MutuallyExclusiveArgumentError('usage error: --deployment-source-url <url> | --deployment-local-git')
    if deployment_container_image_name and container_image_name:
        raise MutuallyExclusiveArgumentError('Cannot use both --deployment-container-image-name'
                                             ' and --container-image-name')
    if container_registry_url and not container_image_name:
        raise ArgumentUsageError('Please specify both --container-registry-url and --container-image-name')

    if container_registry_url:
        container_registry_url = parse_container_registry_url(container_registry_url)
    else:
        container_registry_url = parse_docker_image_name(deployment_container_image_name)

    if container_image_name:
        container_image_name = container_image_name if not container_registry_url else "{}/{}".format(
            urlparse(container_registry_url).hostname,
            container_image_name[1:] if container_image_name.startswith('/') else container_image_name)
    if deployment_container_image_name:
        container_image_name = deployment_container_image_name

    client = web_client_factory(cmd.cli_ctx)
    plan_info = None
    if is_valid_resource_id(plan):
        parse_result = parse_resource_id(plan)
        plan_info = client.app_service_plans.get(parse_result['resource_group'], parse_result['name'])
    else:
        try:
            plan_info = client.app_service_plans.get(name=plan, resource_group_name=resource_group_name)
        except _ResourceNotFoundError:
            plan_info = None
        if not plan_info:
            plans = list(client.app_service_plans.list(detailed=True))
            for user_plan in plans:
                if user_plan.name.lower() == plan.lower():
                    if plan_info:
                        raise InvalidArgumentValueError("There are multiple plans with name {}.".format(plan),
                                                        "Try using the plan resource ID instead.")
                    parse_result = parse_resource_id(user_plan.id)
                    plan_info = client.app_service_plans.get(parse_result['resource_group'], parse_result['name'])
    if not plan_info:
        raise ResourceNotFoundError("The plan '{}' doesn't exist.".format(plan))
    is_linux = plan_info.reserved
    helper = _StackRuntimeHelper(cmd, linux=is_linux, windows=not is_linux)
    location = plan_info.location
    # This is to keep the existing appsettings for a newly created webapp on existing webapp name.
    if auto_generated_domain_name_label_scope:
        name_validation = get_regional_site_availability(cmd,
                                                         location,
                                                         name,
                                                         resource_group_name,
                                                         auto_generated_domain_name_label_scope)
    else:
        name_validation = get_site_availability(cmd, name)

    if not name_validation.name_available:
        if name_validation.reason == 'Invalid':
            raise ValidationError(name_validation.message)
        logger.warning("Webapp '%s' already exists. The command will use the existing app's settings.", name)
        app_details = get_app_details(cmd, name)
        if app_details is None:
            raise ResourceNotFoundError("Unable to retrieve details of the existing app '{}'. Please check that "
                                        "the app is a part of the current subscription. If "
                                        "creating a new app, app names must be globally unique. Please try a more "
                                        "unique name".format(name))
        current_rg = app_details.resource_group
        if resource_group_name is not None and (resource_group_name.lower() != current_rg.lower()):
            raise ValidationError("The webapp '{}' exists in resource group '{}' and does not "
                                  "match the value entered '{}'. Please re-run command with the "
                                  "correct parameters.". format(name, current_rg, resource_group_name))
        existing_app_settings = _generic_site_operation(cmd.cli_ctx, resource_group_name,
                                                        name, 'list_application_settings')
        settings = []
        for k, v in existing_app_settings.properties.items():
            settings.append(NameValuePair(name=k, value=v))
        site_config = SiteConfig(app_settings=settings)
    else:
        site_config = SiteConfig(app_settings=[])
    if isinstance(plan_info.sku, SkuDescription) and plan_info.sku.name.upper() not in ['F1', 'FREE', 'SHARED', 'D1',
                                                                                        'B1', 'B2', 'B3', 'BASIC']:
        site_config.always_on = True

    if subnet or vnet:
        subnet_info = _get_subnet_info(cmd=cmd,
                                       resource_group_name=resource_group_name,
                                       subnet=subnet,
                                       vnet=vnet)
        _validate_vnet_integration_location(cmd=cmd, webapp_location=plan_info.location,
                                            subnet_resource_group=subnet_info["resource_group_name"],
                                            vnet_name=subnet_info["vnet_name"],
                                            vnet_sub_id=subnet_info["subnet_subscription_id"])
        _vnet_delegation_check(cmd, subnet_subscription_id=subnet_info["subnet_subscription_id"],
                               vnet_resource_group=subnet_info["resource_group_name"],
                               vnet_name=subnet_info["vnet_name"],
                               subnet_name=subnet_info["subnet_name"])
        subnet_resource_id = subnet_info["subnet_resource_id"]
        vnet_route_all_enabled = True
    else:
        subnet_resource_id = None
        vnet_route_all_enabled = None

    if using_webapp_up:
        https_only = using_webapp_up

    if acr_use_identity:
        site_config.acr_use_managed_identity_creds = acr_use_identity

    webapp_def = Site(location=location, site_config=site_config, server_farm_id=plan_info.id, tags=tags,
                      https_only=https_only, virtual_network_subnet_id=subnet_resource_id,
                      public_network_access=public_network_access, vnet_route_all_enabled=vnet_route_all_enabled,
                      auto_generated_domain_name_label_scope=auto_generated_domain_name_label_scope)
    if runtime:
        runtime = _StackRuntimeHelper.remove_delimiters(runtime)

    current_stack = None
    if is_linux:
        if not validate_container_app_create_options(runtime, container_image_name,
                                                     multicontainer_config_type, multicontainer_config_file,
                                                     sitecontainers_app):
            if deployment_container_image_name:
                raise ArgumentUsageError('Please specify both --multicontainer-config-type TYPE '
                                         'and --multicontainer-config-file FILE, '
                                         'and only specify one out of --runtime, '
                                         '--deployment-container-image-name, --multicontainer-config-type '
                                         'or --sitecontainers_app')
            raise ArgumentUsageError('Please specify both --multicontainer-config-type TYPE '
                                     'and --multicontainer-config-file FILE, '
                                     'and only specify one out of --runtime, '
                                     '--container-image-name, --multicontainer-config-type '
                                     'or --sitecontainers_app')
        if startup_file:
            site_config.app_command_line = startup_file
        if sitecontainers_app:
            site_config.linux_fx_version = 'SITECONTAINERS'
        elif runtime:
            match = helper.resolve(runtime, is_linux)
            if not match:
                raise ValidationError("Linux Runtime '{}' is not supported."
                                      "Run 'az webapp list-runtimes --os-type linux' to cross check".format(runtime))
            helper.get_site_config_setter(match, linux=is_linux)(cmd=cmd, stack=match, site_config=site_config)
        elif container_image_name:
            site_config.linux_fx_version = _format_fx_version(container_image_name)
            if name_validation.name_available:
                site_config.app_settings.append(NameValuePair(name="WEBSITES_ENABLE_APP_SERVICE_STORAGE",
                                                              value="false"))
        elif multicontainer_config_type and multicontainer_config_file:
            encoded_config_file = _get_linux_multicontainer_encoded_config_from_file(multicontainer_config_file)
            site_config.linux_fx_version = _format_fx_version(encoded_config_file, multicontainer_config_type)

    elif plan_info.is_xenon:  # windows container webapp
        if container_image_name:
            site_config.windows_fx_version = _format_fx_version(container_image_name)
        # set the needed app settings for container image validation
        if name_validation.name_available:
            site_config.app_settings.append(NameValuePair(name="DOCKER_REGISTRY_SERVER_USERNAME",
                                                          value=container_registry_user))
            site_config.app_settings.append(NameValuePair(name="DOCKER_REGISTRY_SERVER_PASSWORD",
                                                          value=container_registry_password))
            site_config.app_settings.append(NameValuePair(name="DOCKER_REGISTRY_SERVER_URL",
                                                          value=container_registry_url))

    elif runtime:  # windows webapp with runtime specified
        if any([startup_file, deployment_container_image_name, container_image_name, multicontainer_config_file,
                multicontainer_config_type]):
            raise ArgumentUsageError("usage error: --startup-file or --deployment-container-image-name or "
                                     "--container-image-name or "
                                     "--multicontainer-config-type and --multicontainer-config-file is "
                                     "only appliable on linux webapp")
        match = helper.resolve(runtime, linux=is_linux)
        if not match:
            raise ValidationError("Windows runtime '{}' is not supported."
                                  "Run 'az webapp list-runtimes --os-type windows' to cross check".format(runtime))
        helper.get_site_config_setter(match, linux=is_linux)(cmd=cmd, stack=match, site_config=site_config)

        # TODO: Ask Calvin the purpose of this - seems like unneeded set of calls
        # portal uses the current_stack propety in metadata to display stack for windows apps
        current_stack = get_current_stack_from_runtime(runtime)

    else:  # windows webapp without runtime specified
        if name_validation.name_available:  # If creating new webapp
            node_default_version = helper.get_default_version("node", is_linux, get_windows_config_version=True)
            site_config.app_settings.append(NameValuePair(name="WEBSITE_NODE_DEFAULT_VERSION",
                                                          value=node_default_version))

    if site_config.app_settings:
        for setting in site_config.app_settings:
            logger.info('Will set appsetting %s', setting)
    if using_webapp_up:  # when the routine is invoked as a help method for webapp up
        if name_validation.name_available:
            logger.info("will set appsetting for enabling build")
            site_config.app_settings.append(NameValuePair(name="SCM_DO_BUILD_DURING_DEPLOYMENT", value=True))
    if language is not None and language.lower() == 'dotnetcore':
        if name_validation.name_available:
            site_config.app_settings.append(NameValuePair(name='ANCM_ADDITIONAL_ERROR_PAGE_LINK',
                                                          value='https://{}.scm.azurewebsites.net/detectors'
                                                          .format(name)))

    poller = client.web_apps.begin_create_or_update(resource_group_name, name, webapp_def)
    webapp = LongRunningOperation(cmd.cli_ctx)(poller)

    if current_stack:
        _update_webapp_current_stack_property_if_needed(cmd, resource_group_name, name, current_stack)

    # Ensure SCC operations follow right after the 'create', no precedent appsetting update commands
    _set_remote_or_local_git(cmd, webapp, resource_group_name, name, deployment_source_url,
                             deployment_source_branch, deployment_local_git)

    _fill_ftp_publishing_url(cmd, webapp, resource_group_name, name)

    if container_image_name:
        logger.info("Updating container settings")
        update_container_settings(cmd, resource_group_name, name, container_registry_url,
                                  container_image_name, container_registry_user,
                                  container_registry_password=container_registry_password)

    if assign_identities is not None:
        identity = assign_identity(cmd, resource_group_name, name, assign_identities,
                                   role, None, scope)
        webapp.identity = identity

    if acr_identity:
        update_site_configs(cmd, resource_group_name, name, acr_identity=acr_identity)

    _enable_basic_auth(cmd, name, None, resource_group_name, basic_auth.lower())
    return webapp


def _enable_basic_auth(cmd, app_name, slot_name, resource_group, enabled):
    if not enabled or enabled == "":
        return
    CsmPublishingCredentialsPoliciesEntity = cmd.get_models("CsmPublishingCredentialsPoliciesEntity")
    csmPublishingCredentialsPoliciesEntity = CsmPublishingCredentialsPoliciesEntity(allow=enabled == "enabled")
    _generic_site_operation(cmd.cli_ctx, resource_group, app_name,
                            'update_ftp_allowed', slot_name, csmPublishingCredentialsPoliciesEntity)
    _generic_site_operation(cmd.cli_ctx, resource_group, app_name,
                            'update_scm_allowed', slot_name, csmPublishingCredentialsPoliciesEntity)


def _validate_vnet_integration_location(cmd, subnet_resource_group, vnet_name, webapp_location, vnet_sub_id=None):
    from azure.cli.core.commands.client_factory import get_subscription_id

    current_sub_id = get_subscription_id(cmd.cli_ctx)
    if vnet_sub_id:
        cmd.cli_ctx.data['subscription_id'] = vnet_sub_id

    vnet_location = VNetShow(cli_ctx=cmd.cli_ctx)(command_args={
        "name": vnet_name,
        "resource_group": subnet_resource_group
    })["location"]

    cmd.cli_ctx.data['subscription_id'] = current_sub_id

    vnet_location = _normalize_location(cmd, vnet_location)
    asp_location = _normalize_location(cmd, webapp_location)

    if vnet_location != asp_location:
        raise ArgumentUsageError("Unable to create webapp: vnet and App Service Plan must be in the same location. "
                                 "vnet location: {}. Plan location: {}.".format(vnet_location, asp_location))


def _get_subnet_info(cmd, resource_group_name, vnet, subnet, attached_resource="webapp"):
    from azure.cli.core.commands.client_factory import get_subscription_id
    subnet_info = {"vnet_name": None,
                   "subnet_name": None,
                   "resource_group_name": None,
                   "subnet_resource_id": None,
                   "subnet_subscription_id": None,
                   "vnet_resource_id": None}

    if is_valid_resource_id(subnet):
        if vnet:
            logger.warning("--subnet argument is a resource ID. Ignoring --vnet argument.")

        parsed_sub_rid = parse_resource_id(subnet)

        subnet_info["vnet_name"] = parsed_sub_rid["name"]
        subnet_info["subnet_name"] = parsed_sub_rid["resource_name"]
        subnet_info["resource_group_name"] = parsed_sub_rid["resource_group"]
        subnet_info["subnet_resource_id"] = subnet
        subnet_info["subnet_subscription_id"] = parsed_sub_rid["subscription"]

        vnet_fmt = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}"
        subnet_info["vnet_resource_id"] = vnet_fmt.format(parsed_sub_rid["subscription"],
                                                          parsed_sub_rid["resource_group"],
                                                          parsed_sub_rid["name"])
        return subnet_info
    subnet_name = subnet

    if is_valid_resource_id(vnet):
        parsed_vnet = parse_resource_id(vnet)
        subnet_rg = parsed_vnet["resource_group"]
        vnet_name = parsed_vnet["name"]
        subscription_id = parsed_vnet["subscription"]
        subnet_info["vnet_resource_id"] = vnet
    else:
        logger.warning("Assuming subnet resource group is the same as %s. "
                       "Use a resource ID for --subnet or --vnet to use a different resource group.", attached_resource)
        subnet_rg = resource_group_name
        vnet_name = vnet
        subscription_id = get_subscription_id(cmd.cli_ctx)
        vnet_fmt = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}"
        subnet_info["vnet_resource_id"] = vnet_fmt.format(subscription_id,
                                                          subnet_rg,
                                                          vnet)

    subnet_id_fmt = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}"
    subnet_rid = subnet_id_fmt.format(subscription_id, subnet_rg, vnet_name, subnet_name)

    subnet_info["vnet_name"] = vnet_name
    subnet_info["subnet_name"] = subnet_name
    subnet_info["resource_group_name"] = subnet_rg
    subnet_info["subnet_resource_id"] = subnet_rid
    subnet_info["subnet_subscription_id"] = subscription_id
    return subnet_info


def get_managed_environment(cmd, resource_group_name, environment_name):
    try:
        appcontainers_client = appcontainers_client_factory(cmd.cli_ctx)
        return appcontainers_client.managed_environments.get(resource_group_name, environment_name)
    except Exception as ex:  # pylint: disable=broad-except
        error_message = ("Retrieving managed environment failed with an exception:\n{}"
                         "\nThe environment does not exist".format(ex))
        recommendation_message = "Please verify the managed environment is valid."
        raise ResourceNotFoundError(error_message, recommendation_message)


def validate_container_app_create_options(runtime=None, container_image_name=None,
                                          multicontainer_config_type=None, multicontainer_config_file=None,
                                          sitecontainers_app=None):
    if bool(multicontainer_config_type) != bool(multicontainer_config_file):
        return False
    opts = [runtime, container_image_name, multicontainer_config_type, sitecontainers_app]
    return len([x for x in opts if x]) == 1  # you can only specify one out the combinations


def parse_container_registry_url(container_registry_url):
    parsed_url = urlparse(container_registry_url)
    if parsed_url.scheme:
        return "{}://{}".format(parsed_url.scheme, parsed_url.hostname)
    hostname = urlparse("https://{}".format(container_registry_url)).hostname
    return "https://{}".format(hostname)


def parse_docker_image_name(deployment_container_image_name, environment=None):
    if not deployment_container_image_name:
        return None
    non_url = "/" not in deployment_container_image_name
    non_url = non_url or ("." not in deployment_container_image_name and ":" not in deployment_container_image_name)
    if non_url:
        return None
    parsed_url = urlparse(deployment_container_image_name)
    if parsed_url.scheme:
        return parsed_url.hostname
    hostname = urlparse("https://{}".format(deployment_container_image_name)).hostname
    if environment:
        return hostname
    return "https://{}".format(hostname)


def check_language_runtime(cmd, resource_group_name, name):
    client = web_client_factory(cmd.cli_ctx)
    app = client.web_apps.get(resource_group_name, name)
    is_linux = app.reserved
    if is_functionapp(app):
        try:
            is_flex = is_flex_functionapp(cmd.cli_ctx, resource_group_name, name)
            runtime_info = _get_functionapp_runtime_info(cmd, resource_group_name, name, None, is_linux)
            runtime = runtime_info['app_runtime']
            runtime_version = runtime_info['app_runtime_version']
            functions_version = runtime_info['functionapp_version']
            if runtime and runtime_version:
                if not is_flex:
                    runtime_helper = _FunctionAppStackRuntimeHelper(cmd=cmd, linux=is_linux, windows=not is_linux)
                    runtime_helper.resolve(runtime, runtime_version, functions_version, is_linux)
                else:
                    location = app.location
                    runtime_helper = _FlexFunctionAppStackRuntimeHelper(cmd, location, runtime, runtime_version)
                    runtime_helper.resolve(runtime, runtime_version)
        except ValidationError as e:
            logger.warning(e.error_msg)


def update_app_settings_functionapp(cmd, resource_group_name, name, settings=None, slot=None, slot_settings=None):
    check_language_runtime(cmd, resource_group_name, name)
    return update_app_settings(cmd, resource_group_name, name, settings, slot, slot_settings)


def _parse_json_setting(s, result, slot_result, setting_type):
    """
    Parse JSON format settings.

    Parameters:
        s (str): The input string containing JSON-formatted settings.
        result (dict): A dictionary to store the parsed key-value pairs from the settings.
        slot_result (dict): A dictionary to store slot setting flags for each key.
        setting_type (str): The type of settings being parsed, either "SlotSettings" or "Settings".

    Returns:
        bool: True if parsing was successful, False otherwise.
    """
    try:
        temp = shell_safe_json_parse(s)
        if isinstance(temp, list):  # Accept the output of the "list" command
            for t in temp:
                if 'slotSetting' in t.keys():
                    slot_result[t['name']] = t['slotSetting']
                elif setting_type == "SlotSettings":
                    slot_result[t['name']] = True
                result[t['name']] = t['value']
        else:
            # Handle JSON objects: setting_type is either "SlotSettings" or "Settings"
            # Different logic needed for slot settings vs regular settings
            if setting_type == "SlotSettings":
                # For slot settings JSON objects, add values to result and mark as slot settings
                result.update(temp)
                for key in temp:
                    slot_result[key] = True
            else:
                # For regular settings JSON objects, add values to result only
                result.update(temp)
        return True
    except InvalidArgumentValueError:
        return False


def update_app_settings(cmd, resource_group_name, name, settings=None, slot=None, slot_settings=None):
    if not settings and not slot_settings:
        raise MutuallyExclusiveArgumentError('Please provide either --settings or --slot-settings parameter.')

    settings = settings or []
    slot_settings = slot_settings or []

    app_settings = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                           'list_application_settings', slot)
    result, slot_result = {}, {}

    for src, setting_type in [(settings, "Settings"), (slot_settings, "SlotSettings")]:
        for s in src:
            # Try simple key=value parsing first
            if '=' in s and not s.lstrip().startswith(('{"', "[", "{")) and not s.startswith('@'):
                k, v = s.split('=', 1)
                result[k] = v
                if setting_type == "SlotSettings":
                    slot_result[k] = True
                continue

            # Try JSON parsing
            if _parse_json_setting(s, result, slot_result, setting_type):
                continue

            # Fallback to key=value parsing with error handling
            try:
                k, v = s.split('=', 1)
            except ValueError as ex:
                raise InvalidArgumentValueError(
                    f"Invalid setting format: '{s}'. Expected 'key=value' format or valid JSON.",
                    recommendation="Use 'key=value' format or provide valid JSON like '{\"key\": \"value\"}'."
                ) from ex

            result[k] = v
            if setting_type == "SlotSettings":
                slot_result[k] = True

    for setting_name, value in result.items():
        app_settings.properties[setting_name] = value
    client = web_client_factory(cmd.cli_ctx)

    # Process slot configurations before updating application settings to ensure proper configuration order.
    app_settings_slot_cfg_names = []
    if slot_result:
        slot_cfg_names = client.web_apps.list_slot_configuration_names(resource_group_name, name)
        slot_cfg_names.app_setting_names = slot_cfg_names.app_setting_names or []
        # Slot settings logic to add a new setting(s) or remove an existing setting(s)
        for slot_setting_name, value in slot_result.items():
            if value and slot_setting_name not in slot_cfg_names.app_setting_names:
                slot_cfg_names.app_setting_names.append(slot_setting_name)
            elif not value and slot_setting_name in slot_cfg_names.app_setting_names:
                slot_cfg_names.app_setting_names.remove(slot_setting_name)
        app_settings_slot_cfg_names = slot_cfg_names.app_setting_names
        client.web_apps.update_slot_configuration_names(resource_group_name, name, slot_cfg_names)

# TODO: Centauri currently return wrong payload for update appsettings, remove this once backend has the fix.
    if is_centauri_functionapp(cmd, resource_group_name, name):
        update_application_settings_polling(cmd, resource_group_name, name, app_settings, slot, client)
        result = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'list_application_settings', slot)
    else:
        result = _generic_settings_operation(cmd.cli_ctx, resource_group_name, name,
                                             'update_application_settings',
                                             app_settings, slot, client)

    return _build_app_settings_output(result.properties, app_settings_slot_cfg_names, redact=True)


# TODO: Update manual polling to use LongRunningOperation once backend API & new SDK supports polling
def update_application_settings_polling(cmd, resource_group_name, name, app_settings, slot, client):
    try:
        _generic_settings_operation(cmd.cli_ctx, resource_group_name, name,
                                    'update_application_settings',
                                    app_settings, slot, client)
    except Exception as ex:  # pylint: disable=broad-except
        poll_url = ex.response.headers['Location'] if 'Location' in ex.response.headers else None
        if ex.response.status_code == 202 and poll_url:
            r = send_raw_request(cmd.cli_ctx, method='get', url=poll_url)
            poll_timeout = time.time() + 60 * 2  # 2 minute timeout

            while r.status_code != 200 and time.time() < poll_timeout:
                time.sleep(5)
                r = send_raw_request(cmd.cli_ctx, method='get', url=poll_url)
        else:
            raise AzureResponseError(f"Failed to update application settings: {str(ex)}") from ex


def add_azure_storage_account(cmd, resource_group_name, name, custom_id, storage_type, account_name,
                              share_name, access_key, mount_path=None, slot=None, slot_setting=False):
    AzureStorageInfoValue = cmd.get_models('AzureStorageInfoValue')
    azure_storage_accounts = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                                     'list_azure_storage_accounts', slot)

    if custom_id in azure_storage_accounts.properties:
        raise ValidationError("Site already configured with an Azure storage account with the id '{}'. "
                              "Use 'az webapp config storage-account update' to update an existing "
                              "Azure storage account configuration.".format(custom_id))

    azure_storage_accounts.properties[custom_id] = AzureStorageInfoValue(type=storage_type, account_name=account_name,
                                                                         share_name=share_name, access_key=access_key,
                                                                         mount_path=mount_path)
    client = web_client_factory(cmd.cli_ctx)

    result = _generic_settings_operation(cmd.cli_ctx, resource_group_name, name,
                                         'update_azure_storage_accounts', azure_storage_accounts,
                                         slot, client)

    if slot_setting:
        slot_cfg_names = client.web_apps.list_slot_configuration_names(resource_group_name, name)

        slot_cfg_names.azure_storage_config_names = slot_cfg_names.azure_storage_config_names or []
        if custom_id not in slot_cfg_names.azure_storage_config_names:
            slot_cfg_names.azure_storage_config_names.append(custom_id)
            client.web_apps.update_slot_configuration_names(resource_group_name, name, slot_cfg_names)

    return _redact_storage_accounts(result.properties)


def update_azure_storage_account(cmd, resource_group_name, name, custom_id, storage_type=None, account_name=None,
                                 share_name=None, access_key=None, mount_path=None, slot=None, slot_setting=False):
    AzureStorageInfoValue = cmd.get_models('AzureStorageInfoValue')

    azure_storage_accounts = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                                     'list_azure_storage_accounts', slot)

    existing_account_config = azure_storage_accounts.properties.pop(custom_id, None)

    if not existing_account_config:
        raise ResourceNotFoundError("No Azure storage account configuration found with the id '{}'. "
                                    "Use 'az webapp config storage-account add' to add a new "
                                    "Azure storage account configuration.".format(custom_id))

    new_account_config = AzureStorageInfoValue(
        type=storage_type or existing_account_config.type,
        account_name=account_name or existing_account_config.account_name,
        share_name=share_name or existing_account_config.share_name,
        access_key=access_key or existing_account_config.access_key,
        mount_path=mount_path or existing_account_config.mount_path
    )

    azure_storage_accounts.properties[custom_id] = new_account_config

    client = web_client_factory(cmd.cli_ctx)
    result = _generic_settings_operation(cmd.cli_ctx, resource_group_name, name,
                                         'update_azure_storage_accounts', azure_storage_accounts,
                                         slot, client)

    if slot_setting:
        slot_cfg_names = client.web_apps.list_slot_configuration_names(resource_group_name, name)
        slot_cfg_names.azure_storage_config_names = slot_cfg_names.azure_storage_config_names or []
        if custom_id not in slot_cfg_names.azure_storage_config_names:
            slot_cfg_names.azure_storage_config_names.append(custom_id)
            client.web_apps.update_slot_configuration_names(resource_group_name, name, slot_cfg_names)

    return _redact_storage_accounts(result.properties)


def enable_zip_deploy_functionapp(cmd, resource_group_name, name, src, build_remote=None, timeout=None, slot=None):
    check_language_runtime(cmd, resource_group_name, name)
    client = web_client_factory(cmd.cli_ctx)
    app = client.web_apps.get(resource_group_name, name)
    if app is None:
        raise ResourceNotFoundError('The function app \'{}\' was not found in resource group \'{}\'. '
                                    'Please make sure these values are correct.'.format(name, resource_group_name))
    parse_plan_id = parse_resource_id(app.server_farm_id)
    plan_info = None
    retry_delay = 10  # seconds
    # We need to retry getting the plan because sometimes if the plan is created as part of function app,
    # it can take a couple of tries before it gets the plan
    for _ in range(5):
        try:
            plan_info = client.app_service_plans.get(parse_plan_id['resource_group'],
                                                     parse_plan_id['name'])
        except:  # pylint: disable=bare-except
            pass
        if plan_info is not None:
            break
        time.sleep(retry_delay)

    is_consumption = is_plan_consumption(cmd, plan_info)

    # if linux consumption, validate that AzureWebJobsStorage app setting exists
    if is_consumption and app.reserved:
        validate_zip_deploy_app_setting_exists(cmd, resource_group_name, name, slot)

    if is_flex_functionapp(cmd.cli_ctx, resource_group_name, name):
        enable_zip_deploy_flex(cmd, resource_group_name, name, src, timeout, slot, build_remote)
        response = check_flex_app_after_deployment(cmd, resource_group_name, name)
        return response
    build_remote = build_remote is True or build_remote == 'true'
    if (not build_remote) and is_consumption and app.reserved:
        return upload_zip_to_storage(cmd, resource_group_name, name, src, slot)
    if build_remote and app.reserved:
        add_remote_build_app_settings(cmd, resource_group_name, name, slot)
    elif app.reserved:
        remove_remote_build_app_settings(cmd, resource_group_name, name, slot)

    return enable_zip_deploy(cmd, resource_group_name, name, src, timeout, slot)


def enable_zip_deploy_webapp(cmd, resource_group_name, name, src, timeout=None, slot=None, track_status=True,
                             enable_kudu_warmup=True):
    return enable_zip_deploy(cmd, resource_group_name, name, src, timeout, slot, track_status, enable_kudu_warmup)


def check_flex_app_after_deployment(cmd, resource_group_name, name):
    import requests
    from azure.cli.core.util import should_disable_connection_verify

    logger.warning("Waiting for sync triggers...")
    time.sleep(60)
    logger.warning("Checking the health of the function app")

    try:
        host_url = _get_host_url(cmd, resource_group_name, name)
    except ValueError:
        raise ResourceNotFoundError('Failed to fetch host url for function app')

    try:
        master_key = list_host_keys(cmd, resource_group_name, name).master_key
    except:
        raise ResourceNotFoundError('Failed to fetch host key to check for function app status')

    host_status_url = host_url + '/admin/host/status'
    headers = {"x-functions-key": master_key}

    total_trials = 15
    num_trials = 0
    while num_trials < total_trials:
        time.sleep(2)
        response = requests.get(host_status_url, headers=headers,
                                verify=not should_disable_connection_verify())
        if 200 <= response.status_code <= 299:
            break

    if response.status_code != 200:
        raise CLIError("Deployment was successful but the app appears to be unhealthy. Please "
                       "check the app logs.")
    return "Deployment was successful."


def enable_zip_deploy_flex(cmd, resource_group_name, name, src, timeout=None, slot=None, build_remote=None):
    logger.warning("Getting scm site credentials for zip deployment")

    try:
        scm_url = _get_scm_url(cmd, resource_group_name, name, slot)
    except ValueError:
        raise ResourceNotFoundError('Failed to fetch scm url for function app')

    runtime_config = get_runtime_config(cmd, resource_group_name, name)
    runtime = runtime_config.get("name", "")
    build_remote = build_remote or runtime == 'python'

    zip_url = scm_url + '/api/publish?RemoteBuild={}&Deployer=az_cli'.format(build_remote)
    deployment_status_url = scm_url + '/api/deployments/latest'

    additional_headers = {"Content-Type": "application/zip", "Cache-Control": "no-cache"}
    headers = get_scm_site_headers_flex(cmd.cli_ctx, additional_headers=additional_headers)

    import os
    import requests
    from azure.cli.core.util import should_disable_connection_verify
    # Read file content

    with open(os.path.realpath(os.path.expanduser(src)), 'rb') as fs:
        zip_content = fs.read()
        logger.warning("Starting zip deployment. This operation can take a while to complete ...")
        res = requests.post(zip_url, data=zip_content, headers=headers, verify=not should_disable_connection_verify())
        logger.warning("Deployment endpoint responded with status code %d for deployment id %s",
                       res.status_code, res.content.decode("utf-8"))

    # check the status of async deployment
    if res.status_code == 202:
        response = _check_zip_deployment_status_flex(cmd, resource_group_name, name, deployment_status_url,
                                                     timeout)
        return response

    # check if there's an ongoing process
    if res.status_code == 409:
        raise UnclassifiedUserFault("There may be an ongoing deployment. Please track your deployment in {}"
                                    .format(deployment_status_url))

    # check if an error occured during deployment
    if res.status_code:
        raise AzureInternalError("An error occured during deployment. Status Code: {}, Details: {}"
                                 .format(res.status_code, res.text))


# This funtion performs deployment using /zipdeploy for both function app and web app
def enable_zip_deploy(cmd, resource_group_name, name, src, timeout=None, slot=None,
                      track_status=False, enable_kudu_warmup=True):
    logger.warning("Getting scm site credentials for zip deployment")

    try:
        scm_url = _get_scm_url(cmd, resource_group_name, name, slot)
    except ValueError:
        raise ResourceNotFoundError('Failed to fetch scm url for function app')

    client = web_client_factory(cmd.cli_ctx)
    app = client.web_apps.get(resource_group_name, name)
    deployer = '&Deployer=az_cli_functions' if is_functionapp(app) else ''
    zip_url = scm_url + '/api/zipdeploy?isAsync=true' + deployer
    deployment_status_url = scm_url + '/api/deployments/latest'

    additional_headers = {"Content-Type": "application/octet-stream", "Cache-Control": "no-cache"}
    headers = get_scm_site_headers(cmd.cli_ctx, name, resource_group_name, slot,
                                   additional_headers=additional_headers)

    import os
    import requests
    from azure.cli.core.util import should_disable_connection_verify
    # check if the app is a linux web app
    app_is_linux_webapp = is_linux_webapp(app)
    app_is_function_app = is_functionapp(app)

    # Read file content
    with open(os.path.realpath(os.path.expanduser(src)), 'rb') as fs:
        zip_content = fs.read()
        logger.warning("Starting zip deployment. This operation can take a while to complete ...")
        if app_is_linux_webapp and track_status is not None and track_status:
            headers["x-ms-artifact-checksum"] = _compute_checksum(zip_content)

        if app_is_linux_webapp and not app_is_function_app and enable_kudu_warmup:
            try:
                logger.warning("Warming up Kudu before deployment.")
                cookies = _warmup_kudu_and_get_cookie_internal(cmd, resource_group_name, name, slot)
                if cookies is None:
                    logger.info("Failed to fetch affinity cookie. Deployment "
                                "will proceed without pre-warming a Kudu instance.")
                    res = requests.post(zip_url, data=zip_content, headers=headers,
                                        verify=not should_disable_connection_verify())
                else:
                    res = requests.post(zip_url, data=zip_content, headers=headers, cookies=cookies,
                                        verify=not should_disable_connection_verify())
            except Exception as ex:  # pylint: disable=broad-except
                logger.info("Failed to deploy using affinity cookie. "
                            "Deployment will proceed without pre-warming a Kudu instance. Exception: %s", ex)
                res = requests.post(zip_url, data=zip_content, headers=headers,
                                    verify=not should_disable_connection_verify())
        else:
            res = requests.post(zip_url, data=zip_content, headers=headers,
                                verify=not should_disable_connection_verify())
        logger.warning("Deployment endpoint responded with status code %d", res.status_code)

    # check the status of async deployment
    if res.status_code == 202:
        response_body = None
        if track_status:
            response_body = _check_runtimestatus_with_deploymentstatusapi(cmd, resource_group_name, name, slot,
                                                                          deployment_status_url, is_async=True,
                                                                          timeout=timeout)
        else:
            response_body = _check_zip_deployment_status(cmd, resource_group_name, name, deployment_status_url,
                                                         slot, timeout)
        return response_body

    # check if there's an ongoing process
    if res.status_code == 409:
        raise UnclassifiedUserFault("There may be an ongoing deployment or your app setting has "
                                    "WEBSITE_RUN_FROM_PACKAGE. Please track your deployment in {} and ensure the "
                                    "WEBSITE_RUN_FROM_PACKAGE app setting is removed. Use 'az webapp config "
                                    "appsettings list --name MyWebapp --resource-group MyResourceGroup --subscription "
                                    "MySubscription' to list app settings and 'az webapp config appsettings delete "
                                    "--name MyWebApp --resource-group MyResourceGroup --setting-names <setting-names> "
                                    "to delete them.".format(deployment_status_url))

    # check if an error occured during deployment
    if res.status_code:
        raise AzureInternalError("An error occured during deployment. Status Code: {}, Details: {}"
                                 .format(res.status_code, res.text))


def add_remote_build_app_settings(cmd, resource_group_name, name, slot):
    settings = get_app_settings(cmd, resource_group_name, name, slot)
    scm_do_build_during_deployment = None
    website_run_from_package = None
    enable_oryx_build = None

    app_settings_should_not_have = []
    app_settings_should_contain = {}

    for keyval in settings:
        value = keyval['value'].lower()
        if keyval['name'] == 'SCM_DO_BUILD_DURING_DEPLOYMENT':
            scm_do_build_during_deployment = value in ('true', '1')
        if keyval['name'] == 'WEBSITE_RUN_FROM_PACKAGE':
            website_run_from_package = value
        if keyval['name'] == 'ENABLE_ORYX_BUILD':
            enable_oryx_build = value

    if scm_do_build_during_deployment is not True:
        logger.warning("Setting SCM_DO_BUILD_DURING_DEPLOYMENT to true")
        update_app_settings(cmd, resource_group_name, name, [
            "SCM_DO_BUILD_DURING_DEPLOYMENT=true"
        ], slot)
        app_settings_should_contain['SCM_DO_BUILD_DURING_DEPLOYMENT'] = 'true'

    if website_run_from_package:
        logger.warning("Removing WEBSITE_RUN_FROM_PACKAGE app setting")
        delete_app_settings(cmd, resource_group_name, name, [
            "WEBSITE_RUN_FROM_PACKAGE"
        ], slot)
        app_settings_should_not_have.append('WEBSITE_RUN_FROM_PACKAGE')

    if enable_oryx_build:
        logger.warning("Removing ENABLE_ORYX_BUILD app setting")
        delete_app_settings(cmd, resource_group_name, name, [
            "ENABLE_ORYX_BUILD"
        ], slot)
        app_settings_should_not_have.append('ENABLE_ORYX_BUILD')

    # Wait for scm site to get the latest app settings
    if app_settings_should_not_have or app_settings_should_contain:
        logger.warning("Waiting SCM site to be updated with the latest app settings")
        scm_is_up_to_date = False
        retries = 10
        while not scm_is_up_to_date and retries >= 0:
            scm_is_up_to_date = validate_app_settings_in_scm(
                cmd, resource_group_name, name, slot,
                should_contain=app_settings_should_contain,
                should_not_have=app_settings_should_not_have)
            retries -= 1
            time.sleep(5)

        if retries < 0:
            logger.warning("App settings may not be propagated to the SCM site.")


def remove_remote_build_app_settings(cmd, resource_group_name, name, slot):
    settings = get_app_settings(cmd, resource_group_name, name, slot)
    scm_do_build_during_deployment = None

    app_settings_should_contain = {}

    for keyval in settings:
        if keyval['name'] == 'SCM_DO_BUILD_DURING_DEPLOYMENT':
            value = keyval['value'].lower()
            scm_do_build_during_deployment = value in ('true', '1')

    if scm_do_build_during_deployment is not False:
        logger.warning("Setting SCM_DO_BUILD_DURING_DEPLOYMENT to false")
        update_app_settings(cmd, resource_group_name, name, [
            "SCM_DO_BUILD_DURING_DEPLOYMENT=false"
        ], slot)
        app_settings_should_contain['SCM_DO_BUILD_DURING_DEPLOYMENT'] = 'false'

    # Wait for scm site to get the latest app settings
    if app_settings_should_contain:
        logger.warning("Waiting SCM site to be updated with the latest app settings")
        scm_is_up_to_date = False
        retries = 10
        while not scm_is_up_to_date and retries >= 0:
            scm_is_up_to_date = validate_app_settings_in_scm(
                cmd, resource_group_name, name, slot,
                should_contain=app_settings_should_contain)
            retries -= 1
            time.sleep(5)

        if retries < 0:
            logger.warning("App settings may not be propagated to the SCM site")


def _is_linux_consumption_function_app(cmd, site):
    web_client = get_mgmt_service_client(cmd.cli_ctx, WebSiteManagementClient)

    if site.kind != 'functionapp,linux':
        return False

    if not is_valid_resource_id(site.server_farm_id):
        return False

    try:
        parsed_plan_id = parse_resource_id(site.server_farm_id)
        plan_info = web_client.app_service_plans.get(parsed_plan_id['resource_group'], parsed_plan_id['name'])
        if plan_info is None:
            return False
        return plan_info.sku.tier.lower() == 'dynamic'
    except Exception:  # pylint: disable=broad-except
        return False


def list_flex_migration_candidates(cmd):
    from azure.cli.core.commands.client_factory import get_subscription_id

    subscription_id = get_subscription_id(cmd.cli_ctx)
    web_client = get_mgmt_service_client(cmd.cli_ctx, WebSiteManagementClient)

    print(f"Searching for function apps under the subscription '{subscription_id}' that are eligible for Flex "
          "Consumption migration...\n")

    all_sites = list(web_client.web_apps.list())
    eligible_sites = []
    ineligible_sites = []

    flex_regions = [region['name'] for region in list_flexconsumption_locations(cmd)]

    for site in all_sites:
        if not _is_linux_consumption_function_app(cmd, site):
            continue

        try:
            if validate_flex_migration_eligibility_for_linux_consumption_app(cmd, site, flex_regions):
                site_entry = {
                    'name': site.name,
                    'resource_group': site.resource_group,
                }

                has_slots = len(list_slots(cmd, site.resource_group, site.name)) > 0

                if has_slots:
                    slots_warning = (f"The site '{site.name}' has slots configured. This will not block migration, "
                                     f"but please note that slots are not supported in Flex Consumption.")
                    site_entry['note'] = slots_warning

                eligible_sites.append(site_entry)

        except Exception as e:  # pylint: disable=broad-except
            ineligible_sites.append({
                'name': site.name,
                'resource_group': site.resource_group,
                'reason': str(e)
            })

    return {
        'eligible_apps': eligible_sites,
        'ineligible_apps': ineligible_sites
    }


def validate_flex_migration_eligibility_for_linux_consumption_app(cmd, site, flex_regions):
    # Validating that the site is in a Flex Consumption-supported region
    normalized_site_location = _normalize_location(cmd, site.location)
    if normalized_site_location not in flex_regions:
        raise ValidationError("The site '{}' is not in a region supported in Flex Consumption. "
                              "Please see the list regions supported in Flex Consumption by running az functionapp "
                              "list-flexconsumption-locations".format(site.name))

    # Validating that the site is using a Flex Consumption-supported runtime
    site_config = get_site_configs(cmd, site.resource_group, site.name)
    linux_fx_version = getattr(site_config, 'linux_fx_version', None)
    runtime_info = _get_functionapp_runtime_info_helper(cmd, linux_fx_version, None, None, True)
    runtime = runtime_info['app_runtime']
    runtime_version = runtime_info['app_runtime_version']

    runtime_helper = _FlexFunctionAppStackRuntimeHelper(cmd, normalized_site_location, runtime)
    runtime_helper.resolve(runtime, runtime_version)

    # Validating that the site does not have SSL bindings configured
    for ssl_state in site.host_name_ssl_states or []:
        if ssl_state.ssl_state != 'Disabled':
            raise ValidationError("The site '{}' is using TSL/SSL certificates. "
                                  "TSL/SSL certificates are not supported in Flex Consumption.".format(site.name))

    # Validating that the site does not have WEBSITE_LOAD_CERTIFICATES app setting configured
    app_settings = get_app_settings(cmd, site.resource_group, site.name)
    for setting in app_settings:
        if setting['name'] == 'WEBSITE_LOAD_CERTIFICATES':
            raise ValidationError("The site '{}' has the WEBSITE_LOAD_CERTIFICATES app setting configured. "
                                  "Certificate loading is not supported in Flex Consumption.".format(site.name))

    # Validating that the site has triggers supported in Flex Consumption
    functions = list_functions(cmd, site.resource_group, site.name)
    unsupported_blob_triggers = []

    for function in functions:
        bindings = function.config.get('bindings', [])
        for binding in bindings:
            if binding.get('type', None) == 'blobTrigger' and binding.get('source', None) != 'EventGrid':
                unsupported_blob_triggers.append(function.name)

    if unsupported_blob_triggers:
        function_list = '\n'.join(unsupported_blob_triggers)
        raise ValidationError("The site '{}' has blob storage trigger(s) that don't use Event Grid "
                              "as the source:\n{}\nFlex Consumption only supports Event Grid-based blob triggers. "
                              "Please convert these triggers to use Event Grid or replace them with Event Grid "
                              "triggers before migration.".format(site.name, function_list))

    return True


def get_storage_account_from_functionapp(cmd, resource_group_name, name):
    from azure.cli.command_modules.storage.operations.account import list_storage_accounts

    storage_account_name = None
    app_settings = get_app_settings(cmd, resource_group_name, name)
    for setting in app_settings:
        if setting['name'] == 'AzureWebJobsStorage':
            for part in setting['value'].split(';'):
                if part.startswith('AccountName='):
                    storage_account_name = part.split('=')[1]
                    break

        if setting['name'] == 'AzureWebJobsStorage__accountName':
            storage_account_name = setting['value']
            break

        if setting['name'] == 'AzureWebJobsStorage__blobServiceUri':
            match = re.match(r'https?://([^.]+)\.blob\.core\.windows\.net', setting['value'])
            if match:
                storage_account_name = match.group(1)
                break

    if not storage_account_name:
        raise ResourceNotFoundError("Unable to obtain storage account name from app settings for function app '{}'. "
                                    .format(name))

    storage_accounts_rg = list_storage_accounts(cmd, resource_group_name)
    for storage_account in storage_accounts_rg:
        if storage_account.name == storage_account_name:
            return storage_account.id

    storage_accounts_sub = list_storage_accounts(cmd)
    for storage_account in storage_accounts_sub:
        if storage_account.name == storage_account_name:
            return storage_account.id

    raise ResourceNotFoundError("Storage account '{}' referenced by function app '{}' was not found in subscription."
                                .format(storage_account_name, name))


def migrate_consumption_to_flex(cmd, source_resource_group, source_name, resource_group, name, storage_account=None,
                                maximum_instance_count=None, skip_managed_identities=False,
                                skip_access_restrictions=False, skip_storage_mount=False, skip_hostnames=False,
                                skip_cors=False):

    web_client = get_mgmt_service_client(cmd.cli_ctx, WebSiteManagementClient)

    # Validate that the app is eligible for Flex Consumption migration
    print(f"Validating that the app '{source_name}' is eligible for Flex Consumption migration...")
    flex_regions = [region['name'] for region in list_flexconsumption_locations(cmd)]
    source = web_client.web_apps.get(source_resource_group, source_name)

    if not _is_linux_consumption_function_app(cmd, source):
        raise ValidationError("The site '{}' is not on a Linux Dynamic (Consumption) plan. Flex Consumption "
                              "migration is only supported for Function Apps on Linux Consumption plans."
                              .format(source.name))

    if validate_flex_migration_eligibility_for_linux_consumption_app(cmd, source, flex_regions):
        slots = list_slots(cmd, source_resource_group, source_name)
        if len(slots) > 0:
            print(f"The site '{source_name}' has slots configured. This will not block migration, "
                  f"but please note that slots are not supported in Flex Consumption.")
        print(f"Source app '{source_name}' is eligible for Flex Consumption migration.")

    source_site_configs = get_site_configs(cmd, source_resource_group, source_name)
    source_linux_fx_version = getattr(source_site_configs, 'linux_fx_version', None)
    source_runtime_info = _get_functionapp_runtime_info_helper(cmd, source_linux_fx_version, None, None, True)
    source_runtime = source_runtime_info['app_runtime']
    source_runtime_version = source_runtime_info['app_runtime_version']

    print(f"\nCreating Flex Consumption function app '{name}' in resource group '{resource_group}'...")

    if not storage_account:
        storage_account = get_storage_account_from_functionapp(cmd, source_resource_group, source_name)
        storage_account_name = parse_resource_id(storage_account)['name']
        print(f"Using source app's storage account '{storage_account_name}' for function app '{name}'")

    try:
        create_functionapp(cmd, resource_group, name, storage_account, flexconsumption_location=source.location,
                           runtime=source_runtime, runtime_version=source_runtime_version,
                           maximum_instance_count=maximum_instance_count)
    except Exception:
        logger.error("There was an error creating the Flex Consumption function app. Please address the issue "
                     "and try again.")
        raise

    print(f"Flex Consumption function app '{name}' created successfully")

    # Migrate app settings, site configs and site properties
    _migrate_app_settings(cmd, source_resource_group, source_name, resource_group, name, storage_account)
    _migrate_site_configs(cmd, source_site_configs, source_name, resource_group, name)
    _migrate_site_properties(cmd, source, resource_group, name)
    _migrate_basic_publishing_credentials_policies(cmd, source_resource_group, source_name, resource_group, name)

    # CORS migration
    if not skip_cors:
        _migrate_cors_settings(cmd, source_site_configs, source_name, resource_group, name)
    else:
        print("\nSkipping CORS settings migration")

    # Custom hostname migration
    if not skip_hostnames:
        _migrate_custom_hostnames(cmd, source_resource_group, source_name, resource_group, name)
    else:
        print("\nSkipping custom hostname migration")

    # Storage mount migration
    if not skip_storage_mount:
        _migrate_storage_mounts(cmd, source_resource_group, source_name, resource_group, name)
    else:
        print("\nSkipping storage mount migration")

    # Access restrictions migration
    if not skip_access_restrictions:
        _migrate_access_restrictions(cmd, source_resource_group, source_name, resource_group, name)
    else:
        print("\nSkipping access restrictions migration")

    # Managed identities migration
    if not skip_managed_identities:
        _migrate_managed_identities_and_roles(cmd, source, resource_group, name)
    else:
        print("\nSkipping managed identities migration")

    print(f"\nInitial migration steps complete. Function app '{source_name}' migrated to Flex Consumption app "
          f"'{name}'. Next: deploy code, test functions, then delete the source app."
          f"\nFor more details on the migration, please visit: "
          f"https://learn.microsoft.com/en-us/azure/azure-functions/migration/migrate-plan-consumption-to-flex")

    return get_functionapp(cmd, resource_group, name)


def _migrate_app_settings(cmd, source_resource_group, source_name, resource_group, name, storage_account):
    print(f"\nMigrating app settings from source function app '{source_name}' to target function app '{name}'...")

    try:
        source_app_settings = get_app_settings(cmd, source_resource_group, source_name)

        excluded_settings = {
            'WEBSITE_USE_PLACEHOLDER_DOTNETISOLATED',
            'WEBSITE_MOUNT_ENABLED',
            'ENABLE_ORYX_BUILD',
            'FUNCTIONS_EXTENSION_VERSION',
            'FUNCTIONS_WORKER_RUNTIME',
            'FUNCTIONS_WORKER_RUNTIME_VERSION',
            'FUNCTIONS_MAX_HTTP_CONCURRENCY',
            'FUNCTIONS_WORKER_PROCESS_COUNT',
            'FUNCTIONS_WORKER_DYNAMIC_CONCURRENCY_ENABLED',
            'SCM_DO_BUILD_DURING_DEPLOYMENT',
            'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING',
            'WEBSITE_CONTENTOVERVNET',
            'WEBSITE_CONTENTSHARE',
            'WEBSITE_DNS_SERVER',
            'WEBSITE_MAX_DYNAMIC_APPLICATION_SCALE_OUT',
            'WEBSITE_NODE_DEFAULT_VERSION',
            'WEBSITE_RUN_FROM_PACKAGE',
            'WEBSITE_SKIP_CONTENTSHARE_VALIDATION',
            'WEBSITE_VNET_ROUTE_ALL',
            'APPLICATIONINSIGHTS_CONNECTION_STRING',
            'AZUREWEBJOBSDASHBOARD'
        }

        if is_valid_resource_id(storage_account):
            storage_account = parse_resource_id(storage_account)['name']

        migrated_app_settings = []
        for setting in source_app_settings:
            setting_name = setting['name'].upper()

            # for the storage account, we format the app setting just like the source app
            if setting_name == 'AZUREWEBJOBSSTORAGE':
                continue

            if setting_name == 'AZUREWEBJOBSSTORAGE__ACCOUNTNAME':
                migrated_app_settings.append(f"AzureWebJobsStorage__accountName={storage_account}")
                delete_app_settings(cmd, resource_group, name, ['AzureWebJobsStorage'])

            elif setting_name == 'AZUREWEBJOBSSTORAGE__BLOBSERVICEURI':
                migrated_app_settings.append(f"AzureWebJobsStorage__blobServiceUri="
                                             f"https://{storage_account}.blob.core.windows.net")
                delete_app_settings(cmd, resource_group, name, ['AzureWebJobsStorage'])

            elif setting_name not in excluded_settings:
                migrated_app_settings.append(f"{setting['name']}={setting['value']}")

        if migrated_app_settings:
            setting_names = [setting.split('=')[0] for setting in migrated_app_settings]
            update_app_settings(cmd, resource_group, name, migrated_app_settings)
            print(f"Successfully migrated {len(migrated_app_settings)} app settings: {', '.join(setting_names)}")
        else:
            print("No app settings to migrate")
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Failed to migrate app settings: %s. This step will be skipped. "
                     "Run 'az functionapp config appsettings set' to add them manually", str(e))


def _migrate_site_configs(cmd, source_site_configs, source_name, resource_group, name):
    print(f"\nMigrating site configs from source function app '{source_name}' to target function app '{name}'...")

    try:
        site_configs = {
            'http20_enabled': str(source_site_configs.http20_enabled).lower(),
            'min_tls_version': source_site_configs.min_tls_version,
            'min_tls_cipher_suite': source_site_configs.min_tls_cipher_suite
        }

        update_site_configs(cmd, resource_group, name, **site_configs)
        print(f"Successfully migrated the following site configs: {', '.join(site_configs.keys())}")
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Failed to migrate site configs: %s. This step will be skipped. "
                     "Run 'az functionapp config set' to add them manually", str(e))


def _migrate_site_properties(cmd, source, resource_group, name):
    print(f"\nMigrating site properties from source function app '{source.name}' to target function app '{name}'...")

    try:
        functionapp = get_functionapp(cmd, resource_group, name)
        functionapp.https_only = source.https_only
        functionapp.client_cert_enabled = source.client_cert_enabled
        functionapp.client_cert_mode = source.client_cert_mode
        functionapp.client_cert_exclusion_paths = source.client_cert_exclusion_paths

        poller = set_functionapp(cmd, resource_group, name, parameters=functionapp)
        LongRunningOperation(cmd.cli_ctx)(poller)

        print("Successfully migrated the following properties: "
              "https_only, client_cert_enabled, client_cert_mode, client_cert_exclusion_paths")
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Failed to migrate site properties: %s. This step will be skipped. "
                     "Run 'az functionapp update' to configure the site properties manually",
                     str(e))


def _migrate_basic_publishing_credentials_policies(cmd, source_resource_group, source_name, resource_group, name):
    print(f"\nMigrating SCM basic authentication setting from source function app '{source_name}' to target "
          f"function app '{name}'...")

    try:
        source_scm_basic_auth_enabled = basic_auth_supported(cmd.cli_ctx, source_name, source_resource_group)

        if source_scm_basic_auth_enabled:

            CsmPublishingCredentialsPoliciesEntity = cmd.get_models("CsmPublishingCredentialsPoliciesEntity")
            csmPublishingCredentialsPoliciesEntity = CsmPublishingCredentialsPoliciesEntity(allow=True)
            _generic_site_operation(cmd.cli_ctx, resource_group, name,
                                    'update_scm_allowed', None, csmPublishingCredentialsPoliciesEntity)

            print("Successfully enabled SCM basic authentication setting")

        else:
            print("SCM basic authentication is disabled in the source function app. "
                  "No action needed.")

    except Exception as e:  # pylint: disable=broad-except
        logger.error("Failed to migrate SCM basic authentication setting: %s. This step will be skipped. "
                     "Run 'az resource update' to configure it manually", str(e))


def _migrate_cors_settings(cmd, source_site_configs, source_name, resource_group, name):
    print(f"\nMigrating CORS settings from source function app '{source_name}' to target function app '{name}'...")

    try:
        source_cors_settings = source_site_configs.cors

        if source_cors_settings:
            if source_cors_settings.allowed_origins:
                add_cors(cmd, resource_group, name, source_cors_settings.allowed_origins)
                cors_allowed_origins = ', '.join(source_cors_settings.allowed_origins)
                print(f"Successfully migrated CORS allowed origins: {cors_allowed_origins}")

            if source_cors_settings.support_credentials:
                enable_credentials(cmd, resource_group, name, enable=True)
                print("Successfully enabled Access-Control-Allow-Credentials setting")
        else:
            print("No CORS settings found to migrate")

    except Exception as e:  # pylint: disable=broad-except
        logger.error("Failed to migrate CORS settings: %s. This step will be skipped. "
                     "Run 'az functionapp cors add' to configure them manually", str(e))


def _migrate_custom_hostnames(cmd, source_resource_group, source_name, resource_group, name):
    print(f"\nMigrating custom hostnames from source function app '{source_name}' to target function app '{name}'...")

    try:
        source_hostnames = list_hostnames(cmd, source_resource_group, source_name)

        custom_hostnames = []
        for hostname_binding in source_hostnames:
            hostname = hostname_binding.name
            if not hostname.endswith('.azurewebsites.net'):
                custom_hostnames.append(hostname)

        if custom_hostnames:
            print(f"Found {len(custom_hostnames)} custom domain(s) to migrate:")
            for hostname in custom_hostnames:
                print(hostname)

            for hostname in custom_hostnames:
                add_hostname(cmd, resource_group, name, hostname)
                print(f"Successfully migrated hostname: {hostname}")
        else:
            print("No custom domains found to migrate")

    except Exception as e:  # pylint: disable=broad-except
        logger.error("Failed to migrate hostnames: %s. This step will be skipped. "
                     "Run 'az functionapp config hostname add' to add them manually",
                     str(e))


def _migrate_storage_mounts(cmd, source_resource_group, source_name, resource_group, name):
    print(f"\nMigrating storage mounts from source function app '{source_name}' to target function app '{name}'...")

    try:
        source_storage_accounts = get_azure_storage_accounts(cmd, source_resource_group, source_name)

        if not source_storage_accounts:
            print("No storage mounts found to migrate")
            return

        for storage_config in source_storage_accounts:
            try:
                custom_id = storage_config['name']
                storage_info = storage_config['value']

                add_azure_storage_account(
                    cmd=cmd,
                    resource_group_name=resource_group,
                    name=name,
                    custom_id=custom_id,
                    storage_type=storage_info.type,
                    account_name=storage_info.account_name,
                    share_name=storage_info.share_name,
                    access_key=storage_info.access_key,
                    mount_path=storage_info.mount_path,
                    slot=None,
                    slot_setting=False
                )
                print(f"Successfully migrated storage mount '{custom_id}' (Account: {storage_info.account_name}, "
                      f"Share: {storage_info.share_name})")

            except Exception as e:  # pylint: disable=broad-except
                logger.error("Failed to migrate storage mount '%s': %s. This step will be skipped. "
                             "Run 'az webapp config storage-account add' to add it manually", custom_id, str(e))
                continue

    except Exception as e:  # pylint: disable=broad-except
        logger.error("Failed to migrate storage mounts: %s. This step will be skipped. "
                     "Run 'az webapp config storage-account add' to add them manually", str(e))


def _migrate_access_restrictions(cmd, source_resource_group, source_name, resource_group, name):
    print(f"\nMigrating access restrictions from source function app '{source_name}' to target function app "
          f"'{name}'...")

    try:
        from . import access_restrictions

        source_restrictions = access_restrictions.show_webapp_access_restrictions(
            cmd, source_resource_group, source_name
        )

        if not source_restrictions:
            print("No access restrictions found to migrate")
            return

        ip_restrictions = source_restrictions.get('ipSecurityRestrictions', [])
        scm_restrictions = source_restrictions.get('scmIpSecurityRestrictions', [])
        scm_use_main = source_restrictions.get('scmIpSecurityRestrictionsUseMain', False)
        default_action = source_restrictions.get('ipSecurityRestrictionsDefaultAction')
        scm_default_action = source_restrictions.get('scmIpSecurityRestrictionsDefaultAction')

        if scm_use_main or default_action or scm_default_action:
            try:
                access_restrictions.set_webapp_access_restriction(
                    cmd, resource_group, name,
                    use_same_restrictions_for_scm_site=scm_use_main,
                    default_action=default_action,
                    scm_default_action=scm_default_action
                )

                print(f"Successfully set access restriction configurations: scmUseMain={scm_use_main}, "
                      f"defaultAction={default_action}, scmDefaultAction={scm_default_action}")

            except Exception as e:  # pylint: disable=broad-except
                logger.error("Failed to set access restriction configurations: %s. This step will be skipped. "
                             "Run 'az webapp config access-restriction set' to configure them manually", str(e))

        for restriction in ip_restrictions:
            _add_single_access_restriction(
                cmd, resource_group, name, restriction, scm_site=False
            )

        if not scm_use_main and scm_restrictions:
            for restriction in scm_restrictions:
                _add_single_access_restriction(
                    cmd, resource_group, name, restriction, scm_site=True
                )

    except Exception as e:  # pylint: disable=broad-except
        logger.error("Failed to migrate access restrictions: %s. This step will be skipped. "
                     "Run 'az webapp config access-restriction add' to add them manually",
                     str(e))


def _add_single_access_restriction(cmd, resource_group, name, restriction, scm_site=False):
    from . import access_restrictions

    rule_name = restriction.get('name')
    priority = restriction.get('priority')
    action = restriction.get('action', 'Allow')
    description = restriction.get('description')
    tag = restriction.get('tag', 'Default')
    ip_address = restriction.get('ip_address')
    subnet_id = restriction.get('vnet_subnet_resource_id')
    headers = restriction.get('headers')

    if not ip_address and not subnet_id:
        print(f"Skipping restriction with no valid IP address or subnet: {rule_name or 'unnamed'}")
        return

    try:
        if subnet_id:
            access_restrictions.add_webapp_access_restriction(
                cmd=cmd,
                resource_group_name=resource_group,
                name=name,
                priority=priority,
                rule_name=rule_name,
                action=action,
                subnet=subnet_id,
                description=description,
                scm_site=scm_site,
                ignore_missing_vnet_service_endpoint=True,
                http_headers=_format_headers(headers) if headers else None
            )
            print(f"Successfully migrated {'SCM' if scm_site else 'main'} subnet restriction: "
                  f"{rule_name or subnet_id} (Priority: {priority})")

        elif ip_address:
            if tag == 'ServiceTag':
                access_restrictions.add_webapp_access_restriction(
                    cmd=cmd,
                    resource_group_name=resource_group,
                    name=name,
                    priority=priority,
                    rule_name=rule_name,
                    action=action,
                    service_tag=ip_address,
                    description=description,
                    scm_site=scm_site,
                    http_headers=_format_headers(headers) if headers else None
                )
                print(f"Successfully migrated {'SCM' if scm_site else 'main'} service tag restriction: "
                      f"{rule_name or ip_address} (Priority: {priority})")

            else:
                access_restrictions.add_webapp_access_restriction(
                    cmd=cmd,
                    resource_group_name=resource_group,
                    name=name,
                    priority=priority,
                    rule_name=rule_name,
                    action=action,
                    ip_address=ip_address,
                    description=description,
                    scm_site=scm_site,
                    http_headers=_format_headers(headers) if headers else None
                )
                print(f"Successfully migrated {'SCM' if scm_site else 'main'} IP restriction: "
                      f"{rule_name or ip_address} (Priority: {priority})")

    except Exception as e:  # pylint: disable=broad-except
        logger.error("Failed to add %s restriction '%s': %s. This step will be skipped. "
                     "Run 'az webapp config access-restriction add' to add it manually",
                     "SCM" if scm_site else "main",
                     rule_name or ip_address or subnet_id or 'unnamed',
                     str(e))


def _format_headers(headers_dict):
    if not headers_dict:
        return None

    headers_list = []
    for header_name, header_values in headers_dict.items():
        for value in header_values:
            headers_list.append(f"{header_name}={value}")

    return headers_list if headers_list else None


def _migrate_managed_identities_and_roles(cmd, source, resource_group, name):
    print(f"\nMigrating managed identities and role assignments from source function app '{source.name}' "
          f"to target function app '{name}'...")

    try:
        from azure.cli.command_modules.role.custom import list_role_assignments

        source_identity = source.identity

        if source_identity:
            if 'SystemAssigned' in source_identity.type:
                system_role_assignments = list_role_assignments(cmd,
                                                                assignee_object_id=source_identity.principal_id,
                                                                show_all=True)

                assign_identity(cmd, resource_group, name, assign_identities=['[system]'])
                target_identity = show_identity(cmd, resource_group, name)
                print(f"Successfully assigned system-assigned identity with principal ID "
                      f"'{target_identity.principal_id}'")
                _migrate_role_assignments(cmd, system_role_assignments, target_identity.principal_id)

            if source_identity.user_assigned_identities:
                user_identity_ids = list(source_identity.user_assigned_identities.keys())
                assign_identity(cmd, resource_group, name, assign_identities=user_identity_ids)
                print(f"Successfully assigned user-assigned identities: {', '.join(user_identity_ids)}")
        else:
            print("No managed identities found in the source function app. No action needed.")

    except Exception as e:  # pylint: disable=broad-except
        logger.error("Failed to migrate managed identities and role assignments: %s. This step will be skipped. "
                     "Run 'az functionapp identity assign' and 'az role assignment create' to configure "
                     "them manually", str(e))


def _migrate_role_assignments(cmd, source_role_assignments, target_principal_id):
    from azure.cli.command_modules.role.custom import create_role_assignment

    for assignment in source_role_assignments:
        try:
            role_definition_id = assignment['roleDefinitionId']
            role_name = role_definition_id.split('/')[-1]
            scope = assignment['scope']

            create_role_assignment(
                cmd=cmd,
                role=role_name,
                scope=scope,
                assignee_object_id=target_principal_id,
                assignee_principal_type='ServicePrincipal'
            )

            print(f"Created role assignment for scope '{scope}' with role "
                  f"'{assignment.get('roleDefinitionName', role_name)}' for principal ID '{target_principal_id}'")

        except Exception as e:  # pylint: disable=broad-except
            logger.error("Failed to create role assignment for scope '%s': %s. This step will be skipped. "
                         "Run 'az role assignment create' to add it manually",
                         scope, str(e))
            continue


def validate_zip_deploy_app_setting_exists(cmd, resource_group_name, name, slot=None):
    settings = get_app_settings(cmd, resource_group_name, name, slot)

    storage_connection = None
    for keyval in settings:
        if keyval['name'] == 'AzureWebJobsStorage':
            storage_connection = str(keyval['value'])

    if storage_connection is None:
        raise ValidationError('The Azure CLI does not support this deployment path. Please '
                              'configure the app to deploy from a remote package using the steps here: '
                              'https://aka.ms/deployfromurl')


def upload_zip_to_storage(cmd, resource_group_name, name, src, slot=None):
    settings = get_app_settings(cmd, resource_group_name, name, slot)

    storage_connection = None
    for keyval in settings:
        if keyval['name'] == 'AzureWebJobsStorage':
            storage_connection = str(keyval['value'])

    container_name = "function-releases"
    blob_name = "{}-{}.zip".format(datetime.datetime.today().strftime('%Y%m%d%H%M%S'), str(uuid.uuid4()))
    BlobServiceClient = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_BLOB,
                                '_blob_service_client#BlobServiceClient')
    blob_service_client = BlobServiceClient.from_connection_string(conn_str=storage_connection)
    container_client = blob_service_client.get_container_client(container_name)
    if not container_client.exists():
        container_client.create_container()

    # https://gist.github.com/vladignatyev/06860ec2040cb497f0f3
    def progress_callback(current, total):
        total_length = 30
        filled_length = int(round(total_length * current) / float(total))
        percents = round(100.0 * current / float(total), 1)
        progress_bar = '=' * filled_length + '-' * (total_length - filled_length)
        progress_message = 'Uploading {} {}%'.format(progress_bar, percents)
        cmd.cli_ctx.get_progress_controller().add(message=progress_message)

    blob_client = None
    import os
    with open(os.path.realpath(os.path.expanduser(src)), 'rb') as fs:
        zip_content = fs.read()
        blob_client = container_client.upload_blob(blob_name, zip_content, validate_content=True,
                                                   progress_hook=progress_callback)

    now = datetime.datetime.utcnow()
    blob_start = now - datetime.timedelta(minutes=10)
    blob_end = now + datetime.timedelta(weeks=520)
    BlobSharedAccessSignature = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_BLOB,
                                        '_shared_access_signature#BlobSharedAccessSignature')

    BlobSasPermissions = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_BLOB, '_models#BlobSasPermissions')
    sas_client = BlobSharedAccessSignature(blob_service_client.account_name,
                                           account_key=blob_service_client.credential.account_key)
    blob_token = sas_client.generate_blob(container_name, blob_name, permission=BlobSasPermissions(read=True),
                                          expiry=blob_end, start=blob_start)

    blob_uri = blob_client.url
    if '?' not in blob_uri:
        blob_uri += '?' + blob_token
    website_run_from_setting = "WEBSITE_RUN_FROM_PACKAGE={}".format(blob_uri)
    update_app_settings(cmd, resource_group_name, name, settings=[website_run_from_setting], slot=slot)
    client = web_client_factory(cmd.cli_ctx)

    try:
        logger.info('\nSyncing Triggers...')
        if slot is not None:
            client.web_apps.sync_function_triggers_slot(resource_group_name, name, slot)
        else:
            client.web_apps.sync_function_triggers(resource_group_name, name)
    except HttpResponseError as ex:
        # This SDK function throws an error if Status Code is 200
        if ex.status_code != 200:
            raise ex
    except Exception as ex:  # pylint: disable=broad-except
        if ex.response.status_code != 200:
            raise ex


class SiteContainerSpec:
    # pylint: disable=too-many-instance-attributes,too-few-public-methods
    from azure.mgmt.web.models import VolumeMount, EnvironmentVariable

    def __init__(self, name: str, image: str, target_port: str, is_main: bool, start_up_command: str = None,
                 auth_type: str = None, user_name: str = None, password_secret: str = None,
                 user_managed_identity_client_id: str = None, volume_mounts: list[VolumeMount] = None,
                 environment_variables: list[EnvironmentVariable] = None):
        self.name = name
        self.image = image
        self.target_port = target_port
        self.is_main = is_main
        self.start_up_command = start_up_command
        self.auth_type = auth_type
        self.user_name = user_name
        self.password_secret = password_secret
        self.user_managed_identity_client_id = user_managed_identity_client_id
        self.volume_mounts = volume_mounts
        self.environment_variables = environment_variables

    @classmethod
    def from_json(cls, json_data):
        name = json_data.get("name")
        properties = {k.lower(): v for k, v in json_data.get("properties", {}).items()}
        volume_mounts = properties.get("volumemounts")
        if volume_mounts:
            for mount in volume_mounts:
                mount = {k.lower(): v for k, v in mount.items()}
                if "containermountpath" in mount:
                    mount["container_mount_path"] = mount.pop("containermountpath")
                if "volumesubpath" in mount:
                    mount["volume_sub_path"] = mount.pop("volumesubpath")
                if "readonly" in mount:
                    mount["read_only"] = mount.pop("readonly")
        return cls(
            name=name,
            image=properties.get("image"),
            target_port=properties.get("targetport"),
            is_main=properties.get("ismain"),
            start_up_command=properties.get("startupcommand"),
            auth_type=properties.get("authtype"),
            user_name=properties.get("username"),
            password_secret=properties.get("passwordsecret"),
            user_managed_identity_client_id=properties.get("usermanagedidentityclientid"),
            volume_mounts=volume_mounts,
            environment_variables=properties.get("environmentvariables")
        )

    @classmethod
    def from_sitecontainer(cls, sitecontainer_name, sitecontainer):
        return cls(
            name=sitecontainer_name,  # Required explicitly as SiteContainer.name is read-only in SiteContainer model
            image=sitecontainer.image,
            target_port=sitecontainer.target_port,
            is_main=sitecontainer.is_main,
            start_up_command=sitecontainer.start_up_command,
            auth_type=sitecontainer.auth_type,
            user_name=sitecontainer.user_name,
            password_secret=sitecontainer.password_secret,
            user_managed_identity_client_id=sitecontainer.user_managed_identity_client_id,
            volume_mounts=sitecontainer.volume_mounts,
            environment_variables=sitecontainer.environment_variables
        )


def create_webapp_sitecontainers(cmd, name, resource_group, slot=None, container_name=None, image=None,
                                 target_port=None, startup_cmd=None, is_main=None, system_assigned_identity=None,
                                 user_assigned_identity=None, registry_username=None,
                                 registry_password=None, sitecontainers_spec_file=None):
    import os
    response = None
    is_system_identity_enabled, user_assigned_identities, app_settings = _get_site_props_for_sitecontainer_app_internal(
        cmd, resource_group, name, slot)

    # check if sitecontainers_spec_file is provided
    if sitecontainers_spec_file:
        response = []
        logger.warning("Using sitecontainer-spec-file to create sitecontainer(s)")
        if not os.path.exists(sitecontainers_spec_file):
            raise ValidationError("The sitecontainer-spec-file does not exist at the path '{}'"
                                  .format(sitecontainers_spec_file))
        with open(sitecontainers_spec_file, 'r') as file:
            sitecontainers_spec_json = None
            try:
                sitecontainers_spec_json = json.load(file)
            except Exception as ex:
                raise ValidationError("The sitecontainer-spec-file is not a valid JSON. Error: {}".format(str(ex)))

            if not isinstance(sitecontainers_spec_json, list):
                raise ValidationError("The sitecontainer-spec-file should contain a list of sitecontainers.")
            try:
                sitecontainers_spec = [SiteContainerSpec.from_json(container) for container in sitecontainers_spec_json]
            except Exception as ex:
                raise ValidationError("Failed to parse the sitecontainer-spec-file. Error: {}".format(str(ex)))
            if sitecontainers_spec is None or len(sitecontainers_spec) == 0:
                raise ValidationError("No sitecontainers found in the sitecontainers spec file.")
            for spec in sitecontainers_spec:
                existing_sitecontainers = list_webapp_sitecontainers(cmd, name, resource_group, slot)
                existing_sitecontainers_spec = [SiteContainerSpec.from_sitecontainer(container.name, container)
                                                for container in existing_sitecontainers]
                try:
                    _validate_sitecontainer_internal(spec, existing_sitecontainers_spec, is_system_identity_enabled,
                                                     user_assigned_identities, app_settings)
                except ValidationError as ex:
                    logger.error(("Validation failed for sitecontainer '%s'. "
                                 "This sitecontainer will be skipped. Error: %s"), spec.name, ex.error_msg)
                    continue
                sitecontainer = SiteContainer(image=spec.image, target_port=spec.target_port,
                                              start_up_command=spec.start_up_command,
                                              is_main=spec.is_main, auth_type=spec.auth_type, user_name=spec.user_name,
                                              password_secret=spec.password_secret,
                                              user_managed_identity_client_id=spec.user_managed_identity_client_id,
                                              volume_mounts=spec.volume_mounts,
                                              environment_variables=spec.environment_variables)
                response.append(_create_or_update_webapp_sitecontainer_internal(cmd, name, resource_group,
                                                                                spec.name, sitecontainer, slot))
                logger.warning("Sitecontainer '%s' added successfully.", spec.name)
    else:
        if container_name is None or is_main is None or image is None:
            raise RequiredArgumentMissingError(("The following arguments are required if argument "
                                                "--sitecontainers-spec-file "
                                                "is not provided: --container-name, --image, --is-main"))
        auth_type = AuthType.ANONYMOUS
        if system_assigned_identity is True:
            auth_type = AuthType.SYSTEM_IDENTITY
        elif user_assigned_identity:
            auth_type = AuthType.USER_ASSIGNED
        elif registry_username and registry_password:
            auth_type = AuthType.USER_CREDENTIALS

        sitecontainer = SiteContainer(image=image, target_port=target_port, start_up_command=startup_cmd,
                                      is_main=is_main, auth_type=auth_type, user_name=registry_username,
                                      password_secret=registry_password,
                                      user_managed_identity_client_id=user_assigned_identity)
        existing_sitecontainers = list_webapp_sitecontainers(cmd, name, resource_group, slot)
        existing_sitecontainers_spec = [SiteContainerSpec.from_sitecontainer(container.name, container)
                                        for container in existing_sitecontainers]
        _validate_sitecontainer_internal(SiteContainerSpec.from_sitecontainer(container_name, sitecontainer),
                                         existing_sitecontainers_spec, is_system_identity_enabled,
                                         user_assigned_identities, app_settings)
        response = _create_or_update_webapp_sitecontainer_internal(cmd, name, resource_group,
                                                                   container_name, sitecontainer, slot)
    return response


def _validate_sitecontainer_internal(new_sitecontainer_spec, existing_sitecontainers_spec,
                                     is_system_assigned_identity_enabled, user_assigned_identities, appsettings):
    # ensure that isMain=true is unique
    existing_main_sitecontainer = next((spec for spec in existing_sitecontainers_spec
                                        if spec.is_main and spec.name != new_sitecontainer_spec.name), None)
    if new_sitecontainer_spec.is_main and existing_main_sitecontainer:
        raise ValidationError(("SiteContainer '{}' with isMain=true already exists. "
                               "Cannot add SiteContainer '{}' as the main sitecontainer.")
                              .format(existing_main_sitecontainer.name, new_sitecontainer_spec.name))
    # ensure that targetPort is in range 1 to 65535
    if new_sitecontainer_spec.target_port is not None:
        target_port = int(new_sitecontainer_spec.target_port)
        if target_port < 1 or target_port > 65535:
            raise ValidationError(("Invalid targetPort '{}' for SiteContainer '{}'. "
                                  "targetPort must be in the range 1 to 65535.")
                                  .format(new_sitecontainer_spec.target_port, new_sitecontainer_spec.name))
    # ensure that targetPort is unique
    existing_same_port_sitecontainer = next((spec for spec in existing_sitecontainers_spec
                                             if (spec.target_port is not None and
                                                 new_sitecontainer_spec.target_port is not None and
                                                 spec.target_port == new_sitecontainer_spec.target_port and
                                                 spec.name != new_sitecontainer_spec.name)), None)
    if existing_same_port_sitecontainer:
        raise ValidationError(("SiteContainer '{}' with targetPort '{}' already exists. "
                              "targetPort must be unique for SiteContainer '{}'.")
                              .format(existing_same_port_sitecontainer.name, new_sitecontainer_spec.target_port,
                                      new_sitecontainer_spec.name))
    # ensure that environment variable value should be a key in appsettings
    if new_sitecontainer_spec.environment_variables:
        for env_var in new_sitecontainer_spec.environment_variables:
            if env_var['value'] not in [setting['name'] for setting in appsettings]:
                raise ValidationError("The value of env variable '{}' for SiteContainer '{}' is not an app setting."
                                      .format(env_var['name'], new_sitecontainer_spec.name))
    # if authType is systemAssigned, ensure that systemAssignedIdentity is enabled
    if new_sitecontainer_spec.auth_type == AuthType.SYSTEM_IDENTITY and not is_system_assigned_identity_enabled:
        raise ValidationError(("System assigned identity is not enabled for the site. "
                              "Cannot use this auth type for SiteContainer '{}'.").format(new_sitecontainer_spec.name))
    # if authType is userAssigned, ensure that userAssignedIdentity that is provided is enabled for the site
    if new_sitecontainer_spec.auth_type == AuthType.USER_ASSIGNED and \
            new_sitecontainer_spec.user_managed_identity_client_id not in user_assigned_identities:
        raise ValidationError(("User assigned identity with ClientID '{}' is not added for the site. "
                              "Cannot use this identity for SiteContainer '{}'.").format(
            new_sitecontainer_spec.user_managed_identity_client_id, new_sitecontainer_spec.name))


def _get_site_props_for_sitecontainer_app_internal(cmd, resource_group, name, slot):
    client = web_client_factory(cmd.cli_ctx)
    app = client.web_apps.get_slot(resource_group, name, slot) if slot else client.web_apps.get(resource_group, name)
    if not is_linux_webapp(app):
        raise ValidationError("Site is not a linux webapp. Sitecontainers are only supported for linux webapps.")
    is_system_identity_enabled = False
    user_assigned_identities = []
    if app.identity:
        is_system_identity_enabled = 'SystemAssigned' in app.identity.type
        if app.identity.user_assigned_identities:
            user_assigned_identities = [identity.client_id
                                        for identity in app.identity.user_assigned_identities.values()]
    app_settings = get_app_settings(cmd, resource_group, name, slot)
    return is_system_identity_enabled, user_assigned_identities, app_settings


def _create_or_update_webapp_sitecontainer_internal(cmd, name, resource_group, container_name,
                                                    sitecontainer, slot=None):
    web_client = get_mgmt_service_client(cmd.cli_ctx, WebSiteManagementClient).web_apps
    try:
        if slot:
            return web_client.create_or_update_site_container_slot(resource_group, name,
                                                                   slot, container_name, sitecontainer)
        return web_client.create_or_update_site_container(resource_group, name, container_name, sitecontainer)
    except Exception as ex:
        raise AzureInternalError("Failed to create or update sitecontainer {}. Error: {}"
                                 .format(container_name, str(ex)))


def update_webapp_sitecontainer(cmd, name, resource_group, container_name, slot=None, image=None, target_port=None,
                                startup_cmd=None, is_main=None, system_assigned_identity=None,
                                user_assigned_identity=None, registry_username=None, registry_password=None):
    # get the sitecontainer
    site_container = None
    try:
        site_container = get_webapp_sitecontainer(cmd, name, resource_group, container_name, slot)
    except:
        raise ResourceNotFoundError("Sitecontainer '{}' does not exist, failed to update the sitecontainer."
                                    .format(container_name))
    site_container.image = image or site_container.image
    site_container.target_port = target_port
    site_container.start_up_command = startup_cmd
    if is_main is not None:
        site_container.is_main = is_main
    if system_assigned_identity is not None:
        site_container.auth_type = AuthType.SYSTEM_IDENTITY
    if user_assigned_identity:
        site_container.auth_type = AuthType.USER_ASSIGNED
        site_container.user_managed_identity_client_id = user_assigned_identity
    if registry_username and registry_password:
        site_container.auth_type = AuthType.USER_CREDENTIALS
        site_container.user_name = registry_username
        site_container.password_secret = registry_password

    # ensure that the updated sitecontainer specs are valid
    is_system_identity_enabled, user_assigned_identities, app_settings = \
        _get_site_props_for_sitecontainer_app_internal(cmd, resource_group, name, slot)
    site_container_specs = SiteContainerSpec.from_sitecontainer(container_name, site_container)
    existing_sitecontainers = list_webapp_sitecontainers(cmd, name, resource_group, slot)
    existing_sitecontainers_spec = [SiteContainerSpec.from_sitecontainer(container.name, container)
                                    for container in existing_sitecontainers]
    _validate_sitecontainer_internal(site_container_specs, existing_sitecontainers_spec, is_system_identity_enabled,
                                     user_assigned_identities, app_settings)
    return _create_or_update_webapp_sitecontainer_internal(cmd, name, resource_group,
                                                           container_name, site_container, slot)


def get_webapp_sitecontainer(cmd, name, resource_group, container_name, slot=None):
    web_client = get_mgmt_service_client(cmd.cli_ctx, WebSiteManagementClient).web_apps
    try:
        if slot:
            return web_client.get_site_container_slot(resource_group, name, slot, container_name)
        return web_client.get_site_container(resource_group, name, container_name)
    except Exception as ex:
        raise ResourceNotFoundError("Failed to fetch sitecontainer '{}'. Error: {}".format(container_name, str(ex)))


def delete_webapp_sitecontainer(cmd, name, resource_group, container_name, slot=None):
    web_client = get_mgmt_service_client(cmd.cli_ctx, WebSiteManagementClient).web_apps
    response = None
    try:
        if slot:
            response = web_client.delete_site_container_slot(resource_group, name, slot,
                                                             container_name, cls=lambda x, y, z: x)
        else:
            response = web_client.delete_site_container(resource_group, name, container_name, cls=lambda x, y, z: x)
        if response and response.http_response.status_code in (200, 204):
            # TODO: Validate deletion via response status code once api bug is fixed,
            # Status 200 -> container existed and was deleted successfully
            # Status 204 -> container does not exist
            logger.warning("Sitecontainer %s was deleted successfully.", container_name)
        else:
            logger.error("Failed to delete sitecontainer %s.", container_name)
    except Exception as ex:
        raise AzureInternalError("Failed to delete sitecontainer '{}'. Error: {}".format(container_name, str(ex)))


def list_webapp_sitecontainers(cmd, name, resource_group, slot=None):
    web_client = get_mgmt_service_client(cmd.cli_ctx, WebSiteManagementClient).web_apps
    site_containers = None
    try:
        if slot:
            site_containers = web_client.list_site_containers_slot(resource_group, name, slot)
        else:
            site_containers = web_client.list_site_containers(resource_group, name)
    except Exception as ex:
        raise ResourceNotFoundError("Failed to fetch sitecontainers. Error: {}".format(str(ex)))
    # the PageIterator returned by SDK throws an exception during extraction if there are 0 containers
    try:
        site_containers = list(site_containers)
    except:  # pylint: disable=bare-except
        return []
    return site_containers


def get_webapp_sitecontainers_status(cmd, name, resource_group, container_name=None, slot=None):
    import requests
    scm_url = _get_scm_url(cmd, resource_group, name, slot)
    site_container_status_url = scm_url + '/api/sitecontainers/' + (container_name
                                                                    if container_name is not None else "")
    headers = get_scm_site_headers(cmd.cli_ctx, name, resource_group, slot)
    try:
        response = requests.get(site_container_status_url, headers=headers)
        return response.json()
    except Exception as ex:
        raise AzureInternalError("Failed to fetch sitecontainer status. Error: {}".format(str(ex)))


def get_webapp_sitecontainer_log(cmd, name, resource_group, container_name, slot=None):
    scm_url = _get_scm_url(cmd, resource_group, name, slot)
    site_container_logs_url = scm_url + '/api/sitecontainers/' + container_name + '/logs'
    headers = get_scm_site_headers(cmd.cli_ctx, name, resource_group, slot)
    try:
        t = threading.Thread(target=_get_log, args=(site_container_logs_url, headers))
        t.daemon = True
        t.start()
        while True:
            time.sleep(100)  # so that ctrl+c can stop the command
    except Exception as ex:
        raise AzureInternalError("Failed to fetch sitecontainer logs. Error: {}".format(str(ex)))


def convert_webapp_sitecontainers(cmd, name, resource_group, mode, slot=None):
    """
    Convert a webapp between classic (docker) and sitecontainers mode.

    :param cmd: CLI command context
    :param name: Name of the webapp
    :param resource_group: Resource group of the webapp
    :param mode: Target mode, either 'docker' or 'sitecontainers'
    :param slot: Optional deployment slot
    """
    if mode == 'sitecontainers':
        _convert_webapp_to_sitecontainers(cmd, name, resource_group, slot)
    elif mode == 'docker':
        _convert_webapp_to_docker(cmd, name, resource_group, slot)
    else:
        raise InvalidArgumentValueError(
            "Invalid mode '{}'. Allowed values: docker, sitecontainers.".format(mode)
        )
    return {"result": "success", "mode": mode}


# for generic updater
def get_webapp(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)


def set_webapp(cmd, resource_group_name, name, slot=None, skip_dns_registration=None, basic_auth="",  # pylint: disable=unused-argument
               skip_custom_domain_verification=None, force_dns_registration=None, ttl_in_seconds=None, **kwargs):  # pylint: disable=unused-argument
    instance = kwargs['parameters']
    client = web_client_factory(cmd.cli_ctx)
    updater = client.web_apps.begin_create_or_update_slot if slot else client.web_apps.begin_create_or_update
    kwargs = {"resource_group_name": resource_group_name, "name": name, "site_envelope": instance}
    if slot:
        kwargs['slot'] = slot

    _enable_basic_auth(cmd, name, slot, resource_group_name, basic_auth.lower())

    return updater(**kwargs)


def update_webapp(cmd, instance, client_affinity_enabled=None, https_only=None, minimum_elastic_instance_count=None,
                  prewarmed_instance_count=None):
    if 'function' in instance.kind:
        raise ValidationError("please use 'az functionapp update' to update this function app")
    if minimum_elastic_instance_count or prewarmed_instance_count:
        args = ["--minimum-elastic-instance-count", "--prewarmed-instance-count"]
        plan = get_app_service_plan_from_webapp(cmd, instance)
        sku = _normalize_sku(plan.sku.name)
        if get_sku_tier(sku) not in ["PREMIUMV2", "PREMIUMV3"]:
            raise ValidationError("{} are only supported for elastic premium V2/V3 SKUs".format(str(args)))
        if not plan.elastic_scale_enabled:
            raise ValidationError("Elastic scale is not enabled on the App Service Plan. Please update the plan ")
        if (minimum_elastic_instance_count or 0) > plan.maximum_elastic_worker_count:
            raise ValidationError("--minimum-elastic-instance-count: Minimum elastic instance count is greater than "
                                  "the app service plan's maximum Elastic worker count. "
                                  "Please choose a lower count or update the plan's maximum ")
        if (prewarmed_instance_count or 0) > plan.maximum_elastic_worker_count:
            raise ValidationError("--prewarmed-instance-count: Prewarmed instance count is greater than "
                                  "the app service plan's maximum Elastic worker count. "
                                  "Please choose a lower count or update the plan's maximum ")

    if client_affinity_enabled is not None:
        instance.client_affinity_enabled = client_affinity_enabled == 'true'
    if https_only is not None:
        instance.https_only = https_only == 'true'

    if minimum_elastic_instance_count is not None:
        from azure.mgmt.web.models import SiteConfig
        # Need to create a new SiteConfig object to ensure that the new property is included in request body
        conf = SiteConfig(**instance.site_config.as_dict())
        conf.minimum_elastic_instance_count = minimum_elastic_instance_count
        instance.site_config = conf

    if prewarmed_instance_count is not None:
        instance.site_config.pre_warmed_instance_count = prewarmed_instance_count

    return instance


def update_functionapp(cmd, instance, plan=None, force=False):
    client = web_client_factory(cmd.cli_ctx)
    if plan is not None:
        if is_valid_resource_id(plan):
            dest_parse_result = parse_resource_id(plan)
            dest_plan_info = client.app_service_plans.get(dest_parse_result['resource_group'],
                                                          dest_parse_result['name'])
        else:
            dest_plan_info = client.app_service_plans.get(instance.resource_group, plan)
        if dest_plan_info is None:
            raise ResourceNotFoundError("The plan '{}' doesn't exist".format(plan))
        validate_plan_switch_compatibility(cmd, client, instance, dest_plan_info, force)
        instance.server_farm_id = dest_plan_info.id
    return instance


def validate_plan_switch_compatibility(cmd, client, src_functionapp_instance, dest_plan_instance, force):
    general_switch_msg = 'Currently the switch is only allowed between a Consumption or an Elastic Premium plan.'
    src_parse_result = parse_resource_id(src_functionapp_instance.server_farm_id)
    src_plan_info = client.app_service_plans.get(src_parse_result['resource_group'],
                                                 src_parse_result['name'])

    if src_plan_info is None:
        raise ResourceNotFoundError('Could not determine the current plan of the functionapp')

    # Ensure all plans involved are windows. Reserved = true indicates Linux.
    if src_plan_info.reserved or dest_plan_instance.reserved:
        raise ValidationError('This feature currently supports windows to windows plan migrations. For other '
                              'migrations, please redeploy.')

    src_is_premium = is_plan_elastic_premium(cmd, src_plan_info)
    dest_is_consumption = is_plan_consumption(cmd, dest_plan_instance)

    if not (is_plan_consumption(cmd, src_plan_info) or src_is_premium):
        raise ValidationError('Your functionapp is not using a Consumption or an Elastic Premium plan. ' +
                              general_switch_msg)
    if not (dest_is_consumption or is_plan_elastic_premium(cmd, dest_plan_instance)):
        raise ValidationError('You are trying to move to a plan that is not a Consumption or an '
                              'Elastic Premium plan. ' +
                              general_switch_msg)

    if src_is_premium and dest_is_consumption:
        logger.warning('WARNING: Moving a functionapp from Premium to Consumption might result in loss of '
                       'functionality and cause the app to break. Please ensure the functionapp is compatible '
                       'with a Consumption plan and is not using any features only available in Premium.')
        if not force:
            raise RequiredArgumentMissingError('If you want to migrate a functionapp from a Premium to Consumption '
                                               'plan, please re-run this command with the \'--force\' flag.')


def set_functionapp(cmd, resource_group_name, name, slot=None, **kwargs):
    instance = kwargs['parameters']
    client = web_client_factory(cmd.cli_ctx)
    updater = client.web_apps.begin_create_or_update_slot if slot else client.web_apps.begin_create_or_update
    kwargs = {"resource_group_name": resource_group_name, "name": name, "site_envelope": instance}
    if slot:
        kwargs['slot'] = slot

    return updater(**kwargs)


def get_functionapp(cmd, resource_group_name, name, slot=None):
    function_app = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    if not function_app or 'function' not in function_app.kind:
        raise ResourceNotFoundError("Unable to find App {} in resource group {}".format(name, resource_group_name))
    return function_app


def list_webapp(cmd, resource_group_name=None, show_details=False):
    full_list = _list_app(cmd.cli_ctx, resource_group_name, show_details=show_details)
    # ignore apps with kind==null & not functions apps
    return list(filter(lambda x: x.kind is not None and "function" not in x.kind.lower(), full_list))


def list_deleted_webapp(cmd, resource_group_name=None, name=None, slot=None):
    result = _list_deleted_app(cmd.cli_ctx, resource_group_name, name, slot)
    return sorted(result, key=lambda site: site.deleted_site_id)


def webapp_exists(cmd, resource_group_name, name, slot=None):
    from azure.core.exceptions import ResourceNotFoundError as RNFR
    exists = True
    try:
        if slot:
            get_webapp(cmd, resource_group_name=resource_group_name, name=name, slot=slot)
        else:
            get_webapp(cmd, resource_group_name=resource_group_name, name=name)
    except RNFR:
        exists = False
    return exists


def restore_deleted_webapp(cmd, deleted_id, resource_group_name, name, slot=None, restore_content_only=None,
                           target_app_svc_plan=None):
    # If web app doesn't exist, Try creating it in the provided app service plan
    if not webapp_exists(cmd, resource_group_name, name, slot):
        logger.debug('Web app %s with slot %s not found under resource group %s', name, slot, resource_group_name)
        if not target_app_svc_plan:
            raise ValidationError(
                f'Target app "{name}" does not exist. '
                'Specify --target-app-svc-plan for it to be created automatically.')
        if not app_service_plan_exists(cmd, resource_group_name, target_app_svc_plan):
            raise ValidationError(
                f'Target app service plan "{target_app_svc_plan}" not found '
                f'in the target resource group "{resource_group_name}"')
        # create webapp in the plan
        create_webapp(cmd, resource_group_name, name, target_app_svc_plan)
        logger.debug(
            'Web app %s is created on plan %s, resource group %s', name, target_app_svc_plan, resource_group_name)

    DeletedAppRestoreRequest = cmd.get_models('DeletedAppRestoreRequest')
    request = DeletedAppRestoreRequest(deleted_site_id=deleted_id, recover_configuration=not restore_content_only)
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'begin_restore_from_deleted_app',
                                   slot, request)


def list_function_app(cmd, resource_group_name=None):
    return list(filter(lambda x: x.kind is not None and is_functionapp(x),
                _list_app(cmd.cli_ctx, resource_group_name)))


def show_functionapp(cmd, resource_group_name, name, slot=None):
    if is_flex_functionapp(cmd.cli_ctx, resource_group_name, name):
        return get_raw_functionapp(cmd.cli_ctx, resource_group_name, name)
    app = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    if not app:
        raise ResourceNotFoundError("Unable to find resource'{}', in ResourceGroup '{}'.".format(name,
                                                                                                 resource_group_name))
    app.site_config = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get_configuration',
                                              slot)
    if not is_centauri_functionapp(cmd, resource_group_name, name):
        _rename_server_farm_props(app)
        _fill_ftp_publishing_url(cmd, app, resource_group_name, name, slot)
    return app


def show_app(cmd, resource_group_name, name, slot=None):
    app = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    if not app:
        raise ResourceNotFoundError("Unable to find resource'{}', in ResourceGroup '{}'.".format(name,
                                                                                                 resource_group_name))
    app.site_config = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get_configuration',
                                              slot)
    if not is_centauri_functionapp(cmd, resource_group_name, name):
        _rename_server_farm_props(app)
        _fill_ftp_publishing_url(cmd, app, resource_group_name, name, slot)
        _remove_list_duplicates(app)
    return app


def _list_app(cli_ctx, resource_group_name=None, show_details=False):
    client = web_client_factory(cli_ctx)
    if resource_group_name:
        result = list(client.web_apps.list_by_resource_group(resource_group_name))
    else:
        result = list(client.web_apps.list())
    for webapp in result:
        _rename_server_farm_props(webapp)
        if show_details:
            if not resource_group_name:
                webapp_resource_group_name = webapp.resource_group
            else:
                webapp_resource_group_name = resource_group_name
            webapp.site_config = _generic_site_operation(
                cli_ctx, webapp_resource_group_name, webapp.name, 'get_configuration')
    return result


def _list_deleted_app(cli_ctx, resource_group_name=None, name=None, slot=None):
    client = web_client_factory(cli_ctx)
    locations = _get_deleted_apps_locations(cli_ctx)
    result = []
    for location in locations:
        result = result + list(client.deleted_web_apps.list_by_location(location))
    if resource_group_name:
        result = [r for r in result if r.resource_group == resource_group_name]
    if name:
        result = [r for r in result if r.deleted_site_name.lower() == name.lower()]
    if slot:
        result = [r for r in result if r.slot.lower() == slot.lower()]
    return result


def _build_identities_info(identities):
    identities = identities or []
    identity_types = []
    if not identities or MSI_LOCAL_ID in identities:
        identity_types.append('SystemAssigned')
    external_identities = [x for x in identities if x != MSI_LOCAL_ID]
    if external_identities:
        identity_types.append('UserAssigned')
    identity_types = ','.join(identity_types)
    info = {'type': identity_types}
    if external_identities:
        info['userAssignedIdentities'] = {e: {} for e in external_identities}
    return (info, identity_types, external_identities, 'SystemAssigned' in identity_types)


def _build_plan_default_identity(default_identity):
    """Transform default_identity parameter into the proper structure for plan creation."""
    if not default_identity:
        return None

    if default_identity.lower() == '[system]':
        return {
            'identity_type': "SystemAssigned"
        }

    return {
        'identity_type': "UserAssigned",
        'user_assigned_identity_resource_id': default_identity
    }


def _build_plan_default_identity_sdk(default_identity):
    """Transform default_identity parameter into the proper structure for SDK-style operations."""
    if not default_identity:
        return None

    if default_identity.lower() == '[system]':
        return {
            'identityType': "SystemAssigned"
        }

    return {
        'identityType': "UserAssigned",
        'userAssignedIdentityResourceId': default_identity
    }


def _convert_webapp_to_sitecontainers(cmd, name, resource_group, slot):
    site_config = get_site_configs(cmd, resource_group, name, slot)
    linux_fx_version = getattr(site_config, "linux_fx_version", None)

    if linux_fx_version and not linux_fx_version.startswith('DOCKER|'):
        raise ValidationError("Cannot convert to sitecontainers mode as site is not a "
                              "classic custom container (docker) app.")

    acr_use_managed_identity_creds = getattr(site_config, "acr_use_managed_identity_creds", None)
    acr_user_managed_identity_id = getattr(site_config, "acr_user_managed_identity_id", None)
    acr_user_name = None
    acr_user_password = None

    # Get app settings to check for ACR credentials
    from azure.cli.core.commands.client_factory import get_subscription_id
    subscription_id = get_subscription_id(cmd.cli_ctx)
    slot_segment = f"/slots/{slot}" if slot else ""
    url = (
        f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/"
        f"providers/Microsoft.Web/sites/{name}{slot_segment}/config/appsettings/list?api-version=2023-12-01"
    )
    request_url = cmd.cli_ctx.cloud.endpoints.resource_manager + url
    response = send_raw_request(cmd.cli_ctx, "POST", request_url)
    app_settings_raw = response.json()
    app_settings = app_settings_raw.get("properties", {})

    acr_user_password = app_settings.get("DOCKER_REGISTRY_SERVER_PASSWORD", None)
    acr_user_name = app_settings.get("DOCKER_REGISTRY_SERVER_USERNAME", None)
    websites_port = app_settings.get("WEBSITES_PORT", None) or app_settings.get("PORT", None)

    # Get docker image from linux_fx_version
    docker_image = linux_fx_version.replace("DOCKER|", "", 1)
    sidecar_main_container_name = "main"
    startup_cmd = getattr(site_config, "app_command_line", None)

    # Prepare parameters for sitecontainers create
    sitecontainer_kwargs = {
        "name": name,
        "resource_group": resource_group,
        "slot": slot,
        "container_name": sidecar_main_container_name,
        "image": docker_image,
        "target_port": websites_port,
        "startup_cmd": startup_cmd,
        "is_main": True,
    }

    if acr_use_managed_identity_creds:
        if acr_user_managed_identity_id:
            # ACR with User-Assigned Managed Identity
            logger.warning("Site is using User-Assigned Managed Identity for ACR authentication.")
            sitecontainer_kwargs["user_assigned_identity"] = acr_user_managed_identity_id
        else:
            # ACR with System-Assigned Managed Identity
            logger.warning("Site is using System-Assigned Managed Identity for ACR authentication.")
            sitecontainer_kwargs["system_assigned_identity"] = True
    else:
        if acr_user_name and acr_user_password:
            # ACR with User Credentials
            logger.warning("Site is using User Credentials for ACR authentication.")
            sitecontainer_kwargs["registry_username"] = acr_user_name
            sitecontainer_kwargs["registry_password"] = acr_user_password
        else:
            # No ACR authentication, using anonymous access
            logger.warning("Site is using anonymous access for ACR authentication.")
    response = create_webapp_sitecontainers(cmd, **sitecontainer_kwargs)
    if response is None:
        logger.warning("Failed to create sitecontainer, deleting all sitecontainers")
        sitecontainers = list_webapp_sitecontainers(cmd, name, resource_group, slot)
        # Remove all sitecontainers
        for c in sitecontainers:
            delete_webapp_sitecontainer(cmd, name, resource_group, c.name, slot)
        raise AzureInternalError("Failed to create sitecontainer for conversion to sitecontainers mode.")

    # Set linuxFxVersion to SITECONTAINERS
    logger.warning("Setting linuxFxVersion to SITECONTAINERS")
    update_site_configs(cmd, resource_group, name, slot=slot, linux_fx_version="SITECONTAINERS")
    logger.warning("Webapp '%s' converted to sitecontainers mode.", name)


def _convert_webapp_to_docker(cmd, name, resource_group, slot):
    site_config = get_site_configs(cmd, resource_group, name, slot)
    linux_fx_version = getattr(site_config, "linux_fx_version", None)
    if linux_fx_version and not linux_fx_version.lower().startswith('sitecontainers'):
        raise ValidationError("Cannot convert to classic (docker) mode as site is not a SITECONTAINERS app.")

    # Get the main sitecontainer
    sitecontainers = list_webapp_sitecontainers(cmd, name, resource_group, slot)
    main_container = next((c for c in sitecontainers if getattr(c, "is_main", False)), None)
    if not main_container:
        raise ResourceNotFoundError("No main sitecontainer found. Cannot convert to classic mode (docker).")
    if len(sitecontainers) > 1:
        option = prompt_y_n('More than one sitecontainer exists. Do you want to continue with the conversion?')
        if not option:
            raise ValidationError("Skipped converting to classic (docker) mode as more than one sitecontainer exists."
                                  " Please remove all but the main sitecontainer before converting.")

    main_container = update_webapp_sitecontainer(
        cmd, name, resource_group, main_container.name, slot=slot,
        image=main_container.image, target_port=main_container.target_port,
        is_main=main_container.is_main
    )

    # Prepare new linux_fx_version
    docker_image = getattr(main_container, "image", None)
    if not docker_image:
        raise ValidationError("Main sitecontainer does not have an image specified.")

    linux_fx_version = _format_fx_version(docker_image)

    # Prepare app settings for registry credentials if needed
    settings = []
    settings.append(f"DOCKER_REGISTRY_SERVER_URL=https://{main_container.image.split('/')[0]}")
    if main_container.auth_type == AuthType.USER_CREDENTIALS:
        if main_container.user_name:
            settings.append(f"DOCKER_REGISTRY_SERVER_USERNAME={main_container.user_name}")
        if main_container.password_secret:
            settings.append(f"DOCKER_REGISTRY_SERVER_PASSWORD={main_container.password_secret}")
        if main_container.target_port:
            settings.append(f"WEBSITES_PORT={main_container.target_port}")
    elif main_container.auth_type == AuthType.SYSTEM_IDENTITY:
        configs = get_site_configs(cmd, resource_group, name, slot)
        setattr(configs, 'acr_use_managed_identity_creds', True)
        setattr(configs, 'acr_user_managed_identity_id', "")
        _generic_site_operation(cmd.cli_ctx, resource_group, name, 'update_configuration', slot, configs)
    elif main_container.auth_type == AuthType.USER_ASSIGNED:
        client = web_client_factory(cmd.cli_ctx)
        if slot:
            app = client.web_apps.get_slot(resource_group, name, slot)
        else:
            app = client.web_apps.get(resource_group, name)
        if app.identity and app.identity.user_assigned_identities:
            # Find the managed identity key whose client_id matches main_container.user_managed_identity_client_id
            matched_key = None
            for key, identity in app.identity.user_assigned_identities.items():
                if identity.client_id == main_container.user_managed_identity_client_id:
                    matched_key = key
                    break
            if not matched_key:
                raise ResourceNotFoundError(
                    f"Could not find a user-assigned identity with client_id "
                    f"'{main_container.user_managed_identity_client_id}' assigned to the app."
                )
        update_site_configs(cmd, resource_group, name, slot=slot, acr_identity=matched_key)
    elif main_container.auth_type == AuthType.ANONYMOUS:
        configs = get_site_configs(cmd, resource_group, name, slot)
        setattr(configs, 'acr_use_managed_identity_creds', False)
        _generic_site_operation(cmd.cli_ctx, resource_group, name, 'update_configuration', slot, configs)

    logger.warning("Deleting all sitecontainers before converting to classic mode (docker).")
    # Remove all sitecontainers
    for c in sitecontainers:
        delete_webapp_sitecontainer(cmd, name, resource_group, c.name, slot)

    # Set linuxFxVersion to docker
    update_site_configs(cmd, resource_group, name, slot=slot, linux_fx_version=linux_fx_version)
    if settings:
        update_app_settings(cmd, resource_group, name, settings, slot)
    logger.warning("Webapp '%s' converted to classic custom container (docker) mode.", name)


def assign_identity(cmd, resource_group_name, name, assign_identities=None, role='Contributor', slot=None, scope=None):
    ManagedServiceIdentity, ResourceIdentityType = cmd.get_models('ManagedServiceIdentity',
                                                                  'ManagedServiceIdentityType')
    UserAssignedIdentitiesValue = cmd.get_models('UserAssignedIdentity')
    _, _, external_identities, enable_local_identity = _build_identities_info(assign_identities)

    def getter():
        return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)

    def setter(webapp):
        if webapp.identity and webapp.identity.type == ResourceIdentityType.system_assigned_user_assigned:
            identity_types = ResourceIdentityType.system_assigned_user_assigned
        elif webapp.identity and webapp.identity.type == ResourceIdentityType.system_assigned and external_identities:
            identity_types = ResourceIdentityType.system_assigned_user_assigned
        elif webapp.identity and webapp.identity.type == ResourceIdentityType.user_assigned and enable_local_identity:
            identity_types = ResourceIdentityType.system_assigned_user_assigned
        elif external_identities and enable_local_identity:
            identity_types = ResourceIdentityType.system_assigned_user_assigned
        elif external_identities:
            identity_types = ResourceIdentityType.user_assigned
        else:
            identity_types = ResourceIdentityType.system_assigned

        if webapp.identity:
            webapp.identity.type = identity_types
        else:
            webapp.identity = ManagedServiceIdentity(type=identity_types)
        if external_identities:
            if not webapp.identity.user_assigned_identities:
                webapp.identity.user_assigned_identities = {}
            for identity in external_identities:
                webapp.identity.user_assigned_identities[identity] = UserAssignedIdentitiesValue()

        poller = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'begin_create_or_update',
                                         extra_parameter=webapp, slot=slot)
        return LongRunningOperation(cmd.cli_ctx)(poller)

    from azure.cli.core.commands.arm import assign_identity as _assign_identity
    webapp = _assign_identity(cmd.cli_ctx, getter, setter, identity_role=role, identity_scope=scope)
    return webapp.identity


def show_identity(cmd, resource_group_name, name, slot=None):
    web_app = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    if not web_app:
        raise ResourceNotFoundError("Unable to find App {} in resource group {}".format(name, resource_group_name))
    return web_app.identity


def remove_identity(cmd, resource_group_name, name, remove_identities=None, slot=None):
    IdentityType = cmd.get_models('ManagedServiceIdentityType')
    UserAssignedIdentitiesValue = cmd.get_models('UserAssignedIdentity')
    _, _, external_identities, remove_local_identity = _build_identities_info(remove_identities)

    def getter():
        return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)

    def setter(webapp):
        if webapp.identity is None:
            return webapp
        to_remove = []
        existing_identities = {x.lower() for x in list((webapp.identity.user_assigned_identities or {}).keys())}
        if external_identities:
            to_remove = {x.lower() for x in external_identities}
            non_existing = to_remove.difference(existing_identities)
            if non_existing:
                raise ResourceNotFoundError("'{}' are not associated with '{}'".format(','.join(non_existing), name))
            if not list(existing_identities - to_remove):
                if webapp.identity.type == IdentityType.user_assigned:
                    webapp.identity.type = IdentityType.none
                elif webapp.identity.type == IdentityType.system_assigned_user_assigned:
                    webapp.identity.type = IdentityType.system_assigned

        webapp.identity.user_assigned_identities = None
        if remove_local_identity:
            webapp.identity.type = (IdentityType.none
                                    if webapp.identity.type == IdentityType.system_assigned or
                                    webapp.identity.type == IdentityType.none
                                    else IdentityType.user_assigned)

        if webapp.identity.type not in [IdentityType.none, IdentityType.system_assigned]:
            webapp.identity.user_assigned_identities = {}
        if to_remove:
            for identity in list(existing_identities - to_remove):
                webapp.identity.user_assigned_identities[identity] = UserAssignedIdentitiesValue()
        else:
            for identity in list(existing_identities):
                webapp.identity.user_assigned_identities[identity] = UserAssignedIdentitiesValue()

        poller = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'begin_create_or_update', slot, webapp)
        return LongRunningOperation(cmd.cli_ctx)(poller)

    from azure.cli.core.commands.arm import assign_identity as _assign_identity
    webapp = _assign_identity(cmd.cli_ctx, getter, setter)
    return webapp.identity


def get_auth_settings(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get_auth_settings', slot)


def is_auth_runtime_version_valid(runtime_version=None):
    if runtime_version is None:
        return True
    if runtime_version.startswith("~") and len(runtime_version) > 1:
        try:
            int(runtime_version[1:])
        except ValueError:
            return False
        return True
    split_versions = runtime_version.split('.')
    if len(split_versions) != 3:
        return False
    for version in split_versions:
        try:
            int(version)
        except ValueError:
            return False
    return True


def update_auth_settings(cmd, resource_group_name, name, enabled=None, action=None,  # pylint: disable=unused-argument
                         client_id=None, token_store_enabled=None, runtime_version=None,  # pylint: disable=unused-argument
                         token_refresh_extension_hours=None,  # pylint: disable=unused-argument
                         allowed_external_redirect_urls=None, client_secret=None,  # pylint: disable=unused-argument
                         client_secret_certificate_thumbprint=None,  # pylint: disable=unused-argument
                         allowed_audiences=None, issuer=None, facebook_app_id=None,  # pylint: disable=unused-argument
                         facebook_app_secret=None, facebook_oauth_scopes=None,  # pylint: disable=unused-argument
                         twitter_consumer_key=None, twitter_consumer_secret=None,  # pylint: disable=unused-argument
                         google_client_id=None, google_client_secret=None,  # pylint: disable=unused-argument
                         google_oauth_scopes=None, microsoft_account_client_id=None,  # pylint: disable=unused-argument
                         microsoft_account_client_secret=None,  # pylint: disable=unused-argument
                         microsoft_account_oauth_scopes=None, slot=None):  # pylint: disable=unused-argument
    auth_settings = get_auth_settings(cmd, resource_group_name, name, slot)
    UnauthenticatedClientAction = cmd.get_models('UnauthenticatedClientAction')
    if action == 'AllowAnonymous':
        auth_settings.unauthenticated_client_action = UnauthenticatedClientAction.allow_anonymous
    elif action:
        auth_settings.unauthenticated_client_action = UnauthenticatedClientAction.redirect_to_login_page
        auth_settings.default_provider = AUTH_TYPES[action]
    # validate runtime version
    if not is_auth_runtime_version_valid(runtime_version):
        raise InvalidArgumentValueError('Usage Error: --runtime-version set to invalid value')

    import inspect
    frame = inspect.currentframe()
    bool_flags = ['enabled', 'token_store_enabled']
    # note: getargvalues is used already in azure.cli.core.commands.
    # and no simple functional replacement for this deprecating method for 3.5
    args, _, _, values = inspect.getargvalues(frame)  # pylint: disable=deprecated-method

    for arg in args[2:]:
        if values.get(arg, None):
            setattr(auth_settings, arg, values[arg] if arg not in bool_flags else values[arg] == 'true')

    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'update_auth_settings', slot, auth_settings)


def list_instances(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'list_instance_identifiers', slot)


def list_runtimes(cmd, os_type=None, linux=False, show_runtime_details=False):
    if os_type is not None and linux:
        raise MutuallyExclusiveArgumentError("Cannot use both --os-type and --linux")

    if linux:
        linux = True
        windows = False
    else:
        # show both linux and windows stacks by default
        linux = True
        windows = True
        if os_type == WINDOWS_OS_NAME:
            linux = False
        if os_type == LINUX_OS_NAME:
            windows = False

    runtime_helper = _StackRuntimeHelper(cmd=cmd, linux=linux, windows=windows)
    return runtime_helper.get_stack_names_only(delimiter=":", show_runtime_details=show_runtime_details)


def list_function_app_runtimes(cmd, os_type=None):
    # show both linux and windows stacks by default
    linux = True
    windows = True
    if os_type == WINDOWS_OS_NAME:
        linux = False
    if os_type == LINUX_OS_NAME:
        windows = False

    runtime_helper = _FunctionAppStackRuntimeHelper(cmd=cmd, linux=linux, windows=windows)
    linux_stacks = [r.to_dict() for r in runtime_helper.stacks if r.linux]
    windows_stacks = [r.to_dict() for r in runtime_helper.stacks if not r.linux]
    if linux and not windows:
        return linux_stacks
    if windows and not linux:
        return windows_stacks
    return {WINDOWS_OS_NAME: windows_stacks, LINUX_OS_NAME: linux_stacks}


def list_flex_function_app_runtimes(cmd, location, runtime):
    runtime_helper = _FlexFunctionAppStackRuntimeHelper(cmd, location, runtime)
    runtimes = [r for r in runtime_helper.stacks if runtime == r.name]
    if not runtimes:
        raise ValidationError("Runtime '{}' not supported for function apps on the Flex Consumption plan."
                              .format(runtime))
    return runtime_helper.stacks


def delete_logic_app(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'delete', slot)


def delete_function_app(cmd, resource_group_name, name, keep_empty_plan=None, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        client.web_apps.delete_slot(resource_group_name, name, slot,
                                    delete_empty_server_farm=False if keep_empty_plan else None)
    else:
        client.web_apps.delete(resource_group_name, name,
                               delete_empty_server_farm=False if keep_empty_plan else None)


def delete_webapp(cmd, resource_group_name, name, keep_metrics=None, keep_empty_plan=None,
                  keep_dns_registration=None, slot=None):  # pylint: disable=unused-argument
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        client.web_apps.delete_slot(resource_group_name, name, slot,
                                    delete_metrics=False if keep_metrics else None,
                                    delete_empty_server_farm=False if keep_empty_plan else None)
    else:
        client.web_apps.delete(resource_group_name, name,
                               delete_metrics=False if keep_metrics else None,
                               delete_empty_server_farm=False if keep_empty_plan else None)


def stop_webapp(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'stop', slot)


def start_webapp(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'start', slot)


def restart_webapp(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'restart', slot)


def get_site_configs(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get_configuration', slot)


def get_app_settings(cmd, resource_group_name, name, slot=None):
    result = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'list_application_settings', slot)
    client = web_client_factory(cmd.cli_ctx)
    is_centauri = is_centauri_functionapp(cmd, resource_group_name, name)
    is_flex = is_flex_functionapp(cmd.cli_ctx, resource_group_name, name)
    slot_app_setting_names = [] if (is_centauri or is_flex) \
        else client.web_apps.list_slot_configuration_names(resource_group_name, name) \
        .app_setting_names
    return _build_app_settings_output(result.properties, slot_app_setting_names)


# Check if the app setting is propagated to the Kudu site correctly by calling api/settings endpoint
# should_have [] is a list of app settings which are expected to be set
# should_not_have [] is a list of app settings which are expected to be absent
# should_contain {} is a dictionary of app settings which are expected to be set with precise values
# Return True if validation succeeded
def validate_app_settings_in_scm(cmd, resource_group_name, name, slot=None,
                                 should_have=None, should_not_have=None, should_contain=None):
    scm_settings = _get_app_settings_from_scm(cmd, resource_group_name, name, slot)
    scm_setting_keys = set(scm_settings.keys())

    if should_have and not set(should_have).issubset(scm_setting_keys):
        return False

    if should_not_have and set(should_not_have).intersection(scm_setting_keys):
        return False

    temp_setting = scm_settings.copy()
    temp_setting.update(should_contain or {})
    if temp_setting != scm_settings:
        return False

    return True


@retryable_method(retries=3, interval_sec=5)
def _get_app_settings_from_scm(cmd, resource_group_name, name, slot=None):
    scm_url = _get_scm_url(cmd, resource_group_name, name, slot)
    settings_url = '{}/api/settings'.format(scm_url)
    additional_headers = {
        'Content-Type': 'application/octet-stream',
        'Cache-Control': 'no-cache',
    }
    headers = get_scm_site_headers(cmd.cli_ctx, name, resource_group_name, slot, additional_headers=additional_headers)

    import requests
    response = requests.get(settings_url, headers=headers, timeout=30)
    return response.json() or {}


def get_connection_strings(cmd, resource_group_name, name, slot=None):
    result = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'list_connection_strings', slot)
    client = web_client_factory(cmd.cli_ctx)
    slot_constr_names = client.web_apps.list_slot_configuration_names(resource_group_name, name) \
                              .connection_string_names or []
    result = [{'name': p,
               'value': result.properties[p].value,
               'type': result.properties[p].type,
               'slotSetting': p in slot_constr_names} for p in result.properties]
    return result


def get_azure_storage_accounts(cmd, resource_group_name, name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    result = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                     'list_azure_storage_accounts', slot)

    slot_azure_storage_config_names = client.web_apps.list_slot_configuration_names(resource_group_name, name) \
                                                     .azure_storage_config_names or []

    return [{'name': p,
             'value': result.properties[p],
             'slotSetting': p in slot_azure_storage_config_names} for p in result.properties]


def _fill_ftp_publishing_url(cmd, webapp, resource_group_name, name, slot=None):
    profiles = list_publish_profiles(cmd, resource_group_name, name, slot)
    try:
        url = next(p['publishUrl'] for p in profiles if p['publishMethod'] == 'FTP')
        setattr(webapp, 'ftpPublishingUrl', url)
    except StopIteration:
        pass
    return webapp


def _format_fx_version(custom_image_name, container_config_type=None):
    lower_custom_image_name = custom_image_name.lower()
    if "https://" in lower_custom_image_name or "http://" in lower_custom_image_name:
        custom_image_name = lower_custom_image_name.replace("https://", "").replace("http://", "")
    fx_version = custom_image_name.strip()
    fx_version_lower = fx_version.lower()
    # handles case of only spaces
    if fx_version:
        if container_config_type:
            fx_version = '{}|{}'.format(container_config_type, custom_image_name)
        elif not fx_version_lower.startswith('docker|'):
            fx_version = '{}|{}'.format('DOCKER', custom_image_name)
    else:
        fx_version = ' '
    return fx_version


def _add_fx_version(cmd, resource_group_name, name, custom_image_name, slot=None):
    fx_version = _format_fx_version(custom_image_name)
    web_app = get_webapp(cmd, resource_group_name, name, slot)
    if not web_app:
        raise ResourceNotFoundError("'{}' app doesn't exist in resource group {}".format(name, resource_group_name))
    linux_fx = fx_version if (web_app.reserved or not web_app.is_xenon) else None
    windows_fx = fx_version if web_app.is_xenon else None
    return update_site_configs(cmd, resource_group_name, name,
                               linux_fx_version=linux_fx, windows_fx_version=windows_fx, slot=slot)


def _delete_linux_fx_version(cmd, resource_group_name, name, slot=None):
    return update_site_configs(cmd, resource_group_name, name, linux_fx_version=' ', slot=slot)


def _get_fx_version(cmd, resource_group_name, name, slot=None):
    site_config = get_site_configs(cmd, resource_group_name, name, slot)
    return site_config.linux_fx_version or site_config.windows_fx_version or ''


def url_validator(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc, result.path])
    except ValueError:
        return False


def _get_linux_multicontainer_decoded_config(cmd, resource_group_name, name, slot=None):
    from base64 import b64decode
    linux_fx_version = _get_fx_version(cmd, resource_group_name, name, slot)
    if not any(linux_fx_version.startswith(s) for s in MULTI_CONTAINER_TYPES):
        raise ValidationError("Cannot decode config that is not one of the"
                              " following types: {}".format(','.join(MULTI_CONTAINER_TYPES)))
    return b64decode(linux_fx_version.split('|')[1].encode('utf-8'))


def _get_linux_multicontainer_encoded_config_from_file(file_name):
    from base64 import b64encode
    config_file_bytes = None
    if url_validator(file_name):
        response = urlopen(file_name, context=_ssl_context())
        config_file_bytes = response.read()
    else:
        with open(file_name, 'rb') as f:
            config_file_bytes = f.read()
    # Decode base64 encoded byte array into string
    return b64encode(config_file_bytes).decode('utf-8')


def get_deployment_configs(cmd, resource_group_name, name):
    functionapp = get_raw_functionapp(cmd.cli_ctx, resource_group_name, name)
    return functionapp.get("properties", {}).get("functionAppConfig", {}).get(
        "deployment", {})


def update_deployment_configs(cmd, resource_group_name, name,  # pylint: disable=too-many-branches
                              deployment_storage_name=None,
                              deployment_storage_container_name=None, deployment_storage_auth_type=None,
                              deployment_storage_auth_value=None):

    if (deployment_storage_name is not None) != (deployment_storage_container_name is not None):
        raise ArgumentUsageError("Please provide both --deployment-storage-name and "
                                 "--deployment-storage-container-name or neither.")

    if deployment_storage_auth_type == 'UserAssignedIdentity' and not deployment_storage_auth_value:
        raise ArgumentUsageError('--deployment-storage-auth-value is required when '
                                 '--deployment-storage-auth-type is set to UserAssignedIdentity.')

    if deployment_storage_auth_value and deployment_storage_auth_type == 'SystemAssignedIdentity':
        raise ArgumentUsageError(
            '--deployment-storage-auth-value is only a valid input when '
            '--deployment-storage-auth-type is set to UserAssignedIdentity or StorageAccountConnectionString. '
            'Please try again with --deployment-storage-auth-type set to UserAssignedIdentity or '
            'StorageAccountConnectionString.'
        )

    functionapp = get_raw_functionapp(cmd.cli_ctx, resource_group_name, name)

    functionapp_deployment_storage = functionapp["properties"]["functionAppConfig"]["deployment"]["storage"]

    deployment_storage = None

    # Storage
    deployment_config_storage_value = None
    if deployment_storage_name is not None:
        deployment_storage = _validate_and_get_deployment_storage(cmd.cli_ctx,
                                                                  resource_group_name,
                                                                  deployment_storage_name)
        _validate_and_get_deployment_storage_container(cmd, resource_group_name,
                                                       deployment_storage_name,
                                                       deployment_storage_container_name)
        endpoints = deployment_storage.primary_endpoints
        deployment_config_storage_value = getattr(endpoints, 'blob') + deployment_storage_container_name
        functionapp_deployment_storage["value"] = deployment_config_storage_value
    else:
        existing_deployment_storage_name = urlparse(functionapp_deployment_storage["value"]).hostname.split(".")[0]
        deployment_storage = _validate_and_get_deployment_storage(cmd.cli_ctx,
                                                                  resource_group_name,
                                                                  existing_deployment_storage_name)

    # Authentication
    assign_identities = None
    if deployment_storage_auth_type is not None:
        deployment_storage_auth_config = functionapp_deployment_storage["authentication"]
        deployment_storage_auth_config["type"] = deployment_storage_auth_type
        if deployment_storage_auth_type == 'StorageAccountConnectionString':
            deployment_storage_conn_string = _get_storage_connection_string(cmd.cli_ctx, deployment_storage)
            conn_string_app_setting = deployment_storage_auth_value or 'DEPLOYMENT_STORAGE_CONNECTION_STRING'
            update_app_settings(cmd, resource_group_name, name,
                                ["{}={}".format(conn_string_app_setting, deployment_storage_conn_string)])
            deployment_storage_auth_config["userAssignedIdentityResourceId"] = None
            deployment_storage_auth_config["storageAccountConnectionStringName"] = \
                conn_string_app_setting
        elif deployment_storage_auth_type == 'SystemAssignedIdentity':
            assign_identities = ['[system]']
            deployment_storage_auth_config["userAssignedIdentityResourceId"] = None
            deployment_storage_auth_config["storageAccountConnectionStringName"] = None
        elif deployment_storage_auth_type == 'UserAssignedIdentity':
            deployment_storage_user_assigned_identity = _get_or_create_user_assigned_identity(
                cmd,
                resource_group_name,
                name,
                deployment_storage_auth_value,
                None)
            deployment_storage_auth_config["userAssignedIdentityResourceId"] = \
                deployment_storage_user_assigned_identity.id
            deployment_storage_auth_config["storageAccountConnectionStringName"] = None
            assign_identities = [deployment_storage_user_assigned_identity.id]
        else:
            raise ValidationError("Invalid value for --deployment-storage-auth-type. Please try "
                                  "again with a valid value.")

    functionapp["properties"]["functionAppConfig"]["deployment"]["storage"] = functionapp_deployment_storage

    result = update_flex_functionapp(cmd, resource_group_name, name, functionapp)

    if deployment_storage_auth_type == 'UserAssignedIdentity':
        assign_identity(cmd, resource_group_name, name, assign_identities)
        if not _has_deployment_storage_role_assignment_on_resource(
                cmd.cli_ctx,
                deployment_storage,
                deployment_storage_user_assigned_identity.principal_id):
            _assign_deployment_storage_managed_identity_role(cmd.cli_ctx, deployment_storage,
                                                             deployment_storage_user_assigned_identity.principal_id)
        else:
            logger.warning("User assigned identity '%s' already has the role assignment on the storage account '%s'",
                           deployment_storage_user_assigned_identity.principal_id, deployment_storage_name)
    elif deployment_storage_auth_type == 'SystemAssignedIdentity':
        assign_identity(cmd, resource_group_name, name, assign_identities, 'Storage Blob Data Contributor',
                        None, deployment_storage.id)

    return result.get("properties", {}).get("functionAppConfig", {}).get("deployment", {})


# for any modifications to the non-optional parameters, adjust the reflection logic accordingly
# in the method
# pylint: disable=unused-argument
def update_site_configs(cmd, resource_group_name, name, slot=None, number_of_workers=None, linux_fx_version=None,  # pylint: disable=too-many-statements,too-many-branches
                        windows_fx_version=None, pre_warmed_instance_count=None, php_version=None,
                        python_version=None, net_framework_version=None, power_shell_version=None,
                        java_version=None, java_container=None, java_container_version=None, runtime=None,
                        remote_debugging_enabled=None, web_sockets_enabled=None,
                        always_on=None, auto_heal_enabled=None,
                        use32_bit_worker_process=None,
                        min_tls_version=None,
                        http20_enabled=None,
                        app_command_line=None,
                        ftps_state=None,
                        vnet_route_all_enabled=None,
                        generic_configurations=None,
                        min_replicas=None,
                        max_replicas=None,
                        acr_use_identity=None,
                        acr_identity=None,
                        min_tls_cipher_suite=None):
    configs = get_site_configs(cmd, resource_group_name, name, slot)
    app_settings = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                           'list_application_settings', slot)

    if runtime and (java_version or java_container or java_container_version or net_framework_version):
        raise MutuallyExclusiveArgumentError("Cannot use --java-version or --java-container"
                                             "or --java-container-version or --net-framework-version"
                                             "with --runtime")
    if runtime and linux_fx_version:
        raise MutuallyExclusiveArgumentError("Cannot use both --runtime and --linux-fx-version")
    if runtime:
        runtime = _StackRuntimeHelper.remove_delimiters(runtime)
        config_is_linux = False
        if configs.linux_fx_version:
            config_is_linux = True
            helper = _StackRuntimeHelper(cmd, linux=config_is_linux, windows=not config_is_linux)
            match = helper.resolve(runtime, linux=config_is_linux)
            if not match:
                raise ValidationError("Linux Runtime '{}' is not supported."
                                      "Run 'az webapp list-runtimes --os-type linux' to cross check".format(runtime))
            helper.get_site_config_setter(match, linux=config_is_linux)(cmd=cmd, stack=match, site_config=configs)
        else:
            helper = _StackRuntimeHelper(cmd, linux=config_is_linux, windows=not config_is_linux)
            match = helper.resolve(runtime, linux=config_is_linux)
            if not match:
                raise ValidationError("Windows runtime '{}' is not supported."
                                      "Run 'az webapp list-runtimes --os-type windows' to cross check".format(runtime))
            if not ('java_version' in match.configs or 'java_container' in match.configs or 'java_container_version' in match.configs):    # pylint: disable=line-too-long
                setattr(configs, 'java_version', None)
                setattr(configs, 'java_container', None)
                setattr(configs, 'java_container_version', None)
            helper.get_site_config_setter(match, linux=config_is_linux)(cmd=cmd, stack=match, site_config=configs)
            language = runtime.split('|')[0]
            version_used_create = '|'.join(runtime.split('|')[1:])
            runtime_version = "{}|{}".format(language, version_used_create) if \
                version_used_create != "-" else version_used_create
            current_stack = get_current_stack_from_runtime(runtime_version) if \
                get_current_stack_from_runtime(runtime_version) != "tomcat" else "java"
            _update_webapp_current_stack_property_if_needed(cmd, resource_group_name, name, current_stack)

    if linux_fx_version:
        if (linux_fx_version.strip().lower().startswith('docker|') or
                linux_fx_version.strip().lower().startswith('sitecontainers')):
            if ('WEBSITES_ENABLE_APP_SERVICE_STORAGE' not in app_settings.properties or
                    app_settings.properties['WEBSITES_ENABLE_APP_SERVICE_STORAGE'] != 'true'):
                update_app_settings(cmd, resource_group_name, name, ["WEBSITES_ENABLE_APP_SERVICE_STORAGE=false"])
        else:
            delete_app_settings(cmd, resource_group_name, name, ["WEBSITES_ENABLE_APP_SERVICE_STORAGE"])

    if pre_warmed_instance_count is not None:
        pre_warmed_instance_count = validate_range_of_int_flag('--prewarmed-instance-count', pre_warmed_instance_count,
                                                               min_val=0, max_val=20)

    import inspect
    frame = inspect.currentframe()
    bool_flags = ['remote_debugging_enabled', 'web_sockets_enabled', 'always_on',
                  'auto_heal_enabled', 'use32_bit_worker_process', 'http20_enabled', 'vnet_route_all_enabled']
    int_flags = ['pre_warmed_instance_count', 'number_of_workers']
    # note: getargvalues is used already in azure.cli.core.commands.
    # and no simple functional replacement for this deprecating method for 3.5
    args, _, _, values = inspect.getargvalues(frame)  # pylint: disable=deprecated-method
    for arg in args[3:]:
        if arg in int_flags and values[arg] is not None:
            values[arg] = validate_and_convert_to_int(arg, values[arg])
        if arg != 'generic_configurations' and values.get(arg, None):
            setattr(configs, arg, values[arg] if arg not in bool_flags else values[arg] == 'true')

    generic_configurations = generic_configurations or []
    # https://github.com/Azure/azure-cli/issues/14857
    updating_ip_security_restrictions = False

    result = {}
    for s in generic_configurations:
        try:
            json_object = get_json_object(s)
            for config_name in json_object:
                if config_name.lower() == 'ip_security_restrictions':
                    updating_ip_security_restrictions = True
            result.update(json_object)
        except CLIError:
            config_name, value = s.split('=', 1)
            result[config_name] = value

    for config_name, value in result.items():
        if config_name.lower() == 'ip_security_restrictions':
            updating_ip_security_restrictions = True
        setattr(configs, config_name, value)

    if not updating_ip_security_restrictions:
        setattr(configs, 'ip_security_restrictions', None)
        setattr(configs, 'scm_ip_security_restrictions', None)

    if acr_identity:
        if not configs.acr_use_managed_identity_creds:
            setattr(configs, 'acr_use_managed_identity_creds', True)
        acr_user_managed_identity_id = ''
        if acr_identity.casefold() != MSI_LOCAL_ID:
            if acr_identity.endswith('/'):
                acr_identity = acr_identity[:len(acr_identity) - 1]
            web_app = get_webapp(cmd, resource_group_name, name, slot)
            webapp_identity = web_app.identity
            matched_key = None
            for key in webapp_identity.user_assigned_identities.keys():
                if key.casefold() == acr_identity.casefold():
                    matched_key = key
            matched_identity = None if matched_key is None else webapp_identity.user_assigned_identities[matched_key]
            if not matched_identity:
                raise ResourceNotFoundError("Unable to retrieve identity {}, "
                                            "please make sure the identity resource id you provide is correct "
                                            "and it is assigned to this webapp. "
                                            "When seeing this error while creating webapp "
                                            "please remove created webapp before trying again "
                                            "or set up user managed identity used for acr manually"
                                            .format(acr_identity))
            acr_user_managed_identity_id = matched_identity.client_id
        setattr(configs, 'acr_user_managed_identity_id', acr_user_managed_identity_id)

    if acr_use_identity is not None:
        acr_use_identity = values['acr_use_identity'].casefold() == 'true'
        if not acr_use_identity:
            setattr(configs, 'acr_user_managed_identity_id', "")
        setattr(configs, 'acr_use_managed_identity_creds', acr_use_identity)

    if is_centauri_functionapp(cmd, resource_group_name, name):
        if min_replicas is not None:
            setattr(configs, 'minimum_elastic_instance_count', min_replicas)
        if max_replicas is not None:
            setattr(configs, 'function_app_scale_limit', max_replicas)
        return update_configuration_polling(cmd, resource_group_name, name, slot, configs)
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'update_configuration', slot, configs)


def update_configuration_polling(cmd, resource_group_name, name, slot, configs):
    try:
        return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'update_configuration', slot, configs)
    except Exception as ex:  # pylint: disable=broad-except
        poll_url = ex.response.headers['Location'] if 'Location' in ex.response.headers else None
        if ex.response.status_code == 202 and poll_url:
            r = send_raw_request(cmd.cli_ctx, method='get', url=poll_url)
            poll_timeout = time.time() + 60 * 2  # 2 minute timeout

            while r.status_code != 200 and time.time() < poll_timeout:
                time.sleep(5)
                r = send_raw_request(cmd.cli_ctx, method='get', url=poll_url)

            if r.status_code == 200:
                return r.json()
        else:
            raise CLIError(ex)


def update_flex_functionapp(cmd, resource_group_name, name, functionapp):
    from azure.cli.core.commands.client_factory import get_subscription_id
    subscription_id = get_subscription_id(cmd.cli_ctx)
    url_base = 'subscriptions/{}/resourceGroups/{}/providers/Microsoft.Web/sites/{}?api-version={}'
    url = url_base.format(subscription_id, resource_group_name, name, '2023-12-01')
    request_url = cmd.cli_ctx.cloud.endpoints.resource_manager + url
    body = json.dumps(functionapp)
    response = send_raw_request(cmd.cli_ctx, "PUT", request_url, body=body)
    return response.json()


def delete_always_ready_settings(cmd, resource_group_name, name, setting_names):
    functionapp = get_raw_functionapp(cmd.cli_ctx, resource_group_name, name)

    always_ready_config = functionapp["properties"]["functionAppConfig"]["scaleAndConcurrency"].get("alwaysReady", [])

    updated_always_ready_config = [x for x in always_ready_config if x["name"] not in setting_names]

    functionapp["properties"]["functionAppConfig"]["scaleAndConcurrency"]["alwaysReady"] = updated_always_ready_config

    result = update_flex_functionapp(cmd, resource_group_name, name, functionapp)

    return result.get("properties", {}).get("functionAppConfig", {}).get(
        "scaleAndConcurrency", {})


def get_runtime_config(cmd, resource_group_name, name):
    functionapp = get_raw_functionapp(cmd.cli_ctx, resource_group_name, name)

    return functionapp.get("properties", {}).get("functionAppConfig", {}).get(
        "runtime", {})


def update_runtime_config(cmd, resource_group_name, name, runtime_version):
    functionapp = get_raw_functionapp(cmd.cli_ctx, resource_group_name, name)

    runtime_info = _get_functionapp_runtime_info(cmd, resource_group_name, name, None, True)
    runtime = runtime_info['app_runtime']

    location = functionapp["location"]
    runtime_helper = _FlexFunctionAppStackRuntimeHelper(cmd, location, runtime, runtime_version)
    matched_runtime = runtime_helper.resolve(runtime, runtime_version)
    flex_sku = matched_runtime.sku
    version = flex_sku['functionAppConfigProperties']['runtime']['version']

    functionapp["properties"]["functionAppConfig"]["runtime"]["version"] = version

    result = update_flex_functionapp(cmd, resource_group_name, name, functionapp)

    return result.get("properties", {}).get("functionAppConfig", {}).get(
        "runtime", {})


def update_always_ready_settings(cmd, resource_group_name, name, settings):
    functionapp = get_raw_functionapp(cmd.cli_ctx, resource_group_name, name)

    if functionapp["properties"]["functionAppConfig"]["scaleAndConcurrency"].get("alwaysReady") is None:
        functionapp["properties"]["functionAppConfig"]["scaleAndConcurrency"]["alwaysReady"] = []

    always_ready_config = functionapp["properties"]["functionAppConfig"]["scaleAndConcurrency"].get("alwaysReady", [])

    updated_always_ready_dict = _parse_key_value_pairs(settings)
    updated_always_ready_config = []

    for key, value in updated_always_ready_dict.items():
        updated_always_ready_config.append(
            {
                "name": key,
                "instanceCount": max(0, validate_and_convert_to_int(key, value))
            }
        )

    for always_ready_setting in always_ready_config:
        if always_ready_setting["name"] not in updated_always_ready_dict:
            updated_always_ready_config.append(always_ready_setting)

    functionapp["properties"]["functionAppConfig"]["scaleAndConcurrency"]["alwaysReady"] = updated_always_ready_config

    result = update_flex_functionapp(cmd, resource_group_name, name, functionapp)

    return result.get("properties", {}).get("functionAppConfig", {}).get(
        "scaleAndConcurrency", {})


def get_scale_config(cmd, resource_group_name, name):
    functionapp = get_raw_functionapp(cmd.cli_ctx, resource_group_name, name)

    return functionapp.get("properties", {}).get("functionAppConfig", {}).get(
        "scaleAndConcurrency", {})


def update_scale_config(cmd, resource_group_name, name, maximum_instance_count=None,
                        instance_memory=None, trigger_type=None, trigger_settings=None):
    if (trigger_type is not None) != (trigger_settings is not None):
        raise RequiredArgumentMissingError("usage error: --trigger-type must be used with parameter "
                                           "--trigger-settings.")

    functionapp = get_raw_functionapp(cmd.cli_ctx, resource_group_name, name)

    scale_config = functionapp["properties"]["functionAppConfig"]["scaleAndConcurrency"]

    if maximum_instance_count:
        scale_config["maximumInstanceCount"] = maximum_instance_count

    if instance_memory:
        scale_config["instanceMemoryMB"] = instance_memory

    if trigger_type:
        if not getattr(scale_config, 'triggers', None):
            scale_config["triggers"] = {}
        if not getattr(scale_config["triggers"], trigger_type, None):
            scale_config["triggers"][trigger_type] = {}
        triggers_dict = _parse_key_value_pairs(trigger_settings)
        for key, value in triggers_dict.items():
            scale_config["triggers"][trigger_type][key] = validate_and_convert_to_int(key, value)

    functionapp["properties"]["functionAppConfig"]["scaleAndConcurrency"] = scale_config

    result = update_flex_functionapp(cmd, resource_group_name, name, functionapp)

    return result.get("properties", {}).get("functionAppConfig", {}).get(
        "scaleAndConcurrency", {})


def delete_app_settings(cmd, resource_group_name, name, setting_names, slot=None):
    app_settings = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'list_application_settings', slot)
    client = web_client_factory(cmd.cli_ctx)
    is_centauri = is_centauri_functionapp(cmd, resource_group_name, name)
    is_flex = is_flex_functionapp(cmd.cli_ctx, resource_group_name, name)
    slot_cfg_names = {} if (is_centauri or is_flex) \
        else client.web_apps.list_slot_configuration_names(resource_group_name, name)
    is_slot_settings = False

    for setting_name in setting_names:
        app_settings.properties.pop(setting_name, None)
        if slot_cfg_names and slot_cfg_names.app_setting_names and setting_name in slot_cfg_names.app_setting_names:
            slot_cfg_names.app_setting_names.remove(setting_name)
            is_slot_settings = True

    if is_slot_settings:
        client.web_apps.update_slot_configuration_names(resource_group_name, name, slot_cfg_names)

# TODO: Centauri currently return wrong payload for update appsettings, remove this once backend has the fix.
    if is_centauri:
        update_application_settings_polling(cmd, resource_group_name, name, app_settings, slot, client)
        result = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'list_application_settings', slot)
    else:
        result = _generic_settings_operation(cmd.cli_ctx, resource_group_name, name,
                                             'update_application_settings',
                                             app_settings, slot, client)

    return _build_app_settings_output(result.properties,
                                      slot_cfg_names.app_setting_names if slot_cfg_names else [],
                                      redact=True)


def delete_azure_storage_accounts(cmd, resource_group_name, name, custom_id, slot=None):
    azure_storage_accounts = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                                     'list_azure_storage_accounts', slot)
    client = web_client_factory(cmd.cli_ctx)

    slot_cfg_names = client.web_apps.list_slot_configuration_names(resource_group_name, name)
    is_slot_settings = False

    azure_storage_accounts.properties.pop(custom_id, None)
    if slot_cfg_names.azure_storage_config_names and custom_id in slot_cfg_names.azure_storage_config_names:
        slot_cfg_names.azure_storage_config_names.remove(custom_id)
        is_slot_settings = True

    if is_slot_settings:
        client.web_apps.update_slot_configuration_names(resource_group_name, name, slot_cfg_names)

    result = _generic_settings_operation(cmd.cli_ctx, resource_group_name, name,
                                         'update_azure_storage_accounts', azure_storage_accounts,
                                         slot, client)

    return _redact_storage_accounts(result.properties)


def _redact_storage_accounts(properties):
    logger.warning('Storage account access keys have been redacted. '
                   'Use `az webapp config storage-account list` to view.')
    for account in properties:
        properties[account].accessKey = None
    return properties


def _ssl_context():
    return ssl.create_default_context()


def _build_app_settings_output(app_settings, slot_cfg_names, redact=False):
    slot_cfg_names = slot_cfg_names or []
    return [{'name': p,
             'value': app_settings[p],
             'slotSetting': p in slot_cfg_names} for p in (_redact_appsettings(app_settings) if redact
                                                           else _mask_creds_related_appsettings(app_settings))]


def _redact_appsettings(settings):
    # Removing the redaction message as it's breaking people's pipelines
    # Addresses https://github.com/Azure/azure-cli/issues/27724
    # logger.warning('App settings have been redacted. '
    #                'Use `az webapp/logicapp/functionapp config appsettings list` to view.')
    for x in settings:
        settings[x] = None
    return settings


def _build_app_settings_input(settings, connection_string_type):
    if not settings:
        return []
    try:
        # check if its a json file
        settings_str = ''.join([i.rstrip() for i in settings])
        json_obj = json.loads(settings_str)
        json_obj = json_obj if isinstance(json_obj, list) else [json_obj]
        for i in json_obj:
            keys = i.keys()
            if 'value' not in keys or 'name' not in keys or 'type' not in keys:
                raise KeyError
        return json_obj
    except KeyError:
        raise ArgumentUsageError("In json settings, 'value', 'name' and 'type' is required; 'slotSetting' is optional")
    except json.decoder.JSONDecodeError:
        # this may not be a json file
        if not connection_string_type:
            raise ArgumentUsageError('either --connection-string-type is required if not using json, or bad json file')
        results = []
        for name_value in settings:
            conn_string_name, value = name_value.split('=', 1)
            if value[0] in ["'", '"']:  # strip away the quots used as separators
                value = value[1:-1]
            results.append({'name': conn_string_name, 'value': value, 'type': connection_string_type})
        return results


def update_connection_strings(cmd, resource_group_name, name, connection_string_type=None,
                              settings=None, slot=None, slot_settings=None):
    from azure.mgmt.web.models import ConnStringValueTypePair
    if not settings and not slot_settings:
        raise ArgumentUsageError('Usage Error: --settings |--slot-settings')
    settings = _build_app_settings_input(settings, connection_string_type)
    sticky_slot_settings = _build_app_settings_input(slot_settings, connection_string_type)
    rm_sticky_slot_settings = set()

    conn_strings = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                           'list_connection_strings', slot)

    for name_value_type in settings + sticky_slot_settings:
        # split at the first '=', connection string should not have '=' in the name
        conn_strings.properties[name_value_type['name']] = ConnStringValueTypePair(value=name_value_type['value'],
                                                                                   type=name_value_type['type'])
        if 'slotSetting' in name_value_type:
            if name_value_type['slotSetting']:
                sticky_slot_settings.append(name_value_type)
            else:
                rm_sticky_slot_settings.add(name_value_type['name'])

    client = web_client_factory(cmd.cli_ctx)
    result = _generic_settings_operation(cmd.cli_ctx, resource_group_name, name,
                                         'update_connection_strings',
                                         conn_strings, slot, client)

    if sticky_slot_settings or rm_sticky_slot_settings:
        new_slot_setting_names = set(n['name'] for n in sticky_slot_settings)  # add setting name
        slot_cfg_names = client.web_apps.list_slot_configuration_names(resource_group_name, name)
        slot_cfg_names.connection_string_names = set(slot_cfg_names.connection_string_names or [])
        slot_cfg_names.connection_string_names.update(new_slot_setting_names)
        slot_cfg_names.connection_string_names -= rm_sticky_slot_settings
        client.web_apps.update_slot_configuration_names(resource_group_name, name, slot_cfg_names)

    return _redact_connection_strings(result.properties)


def delete_connection_strings(cmd, resource_group_name, name, setting_names, slot=None):
    conn_strings = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                           'list_connection_strings', slot)
    client = web_client_factory(cmd.cli_ctx)

    slot_cfg_names = client.web_apps.list_slot_configuration_names(resource_group_name, name)
    is_slot_settings = False
    for setting_name in setting_names:
        conn_strings.properties.pop(setting_name, None)
        if slot_cfg_names.connection_string_names and setting_name in slot_cfg_names.connection_string_names:
            slot_cfg_names.connection_string_names.remove(setting_name)
            is_slot_settings = True

    if is_slot_settings:
        client.web_apps.update_slot_configuration_names(resource_group_name, name, slot_cfg_names)

    result = _generic_settings_operation(cmd.cli_ctx, resource_group_name, name,
                                         'update_connection_strings',
                                         conn_strings, slot, client)
    _redact_connection_strings(result.properties)
    return result


def _redact_connection_strings(properties):
    # Removing the redaction message as it's breaking people's pipelines
    # Addresses https://github.com/Azure/azure-cli/issues/27724
    # logger.warning('Connection string values have been redacted. '
    #                'Use `az webapp config connection-string list` to view.')
    for setting in properties:
        properties[setting].value = None
    return properties


CONTAINER_APPSETTING_NAMES = ['DOCKER_REGISTRY_SERVER_URL', 'DOCKER_REGISTRY_SERVER_USERNAME',
                              'DOCKER_REGISTRY_SERVER_PASSWORD', "WEBSITES_ENABLE_APP_SERVICE_STORAGE"]
APPSETTINGS_TO_MASK = ['DOCKER_REGISTRY_SERVER_PASSWORD']


def update_container_settings(cmd, resource_group_name, name, container_registry_url=None,
                              container_image_name=None, container_registry_user=None,
                              websites_enable_app_service_storage=None, container_registry_password=None,
                              multicontainer_config_type=None, multicontainer_config_file=None,
                              slot=None, min_replicas=None, max_replicas=None):
    settings = []
    if container_registry_url is not None:
        settings.append('DOCKER_REGISTRY_SERVER_URL=' + container_registry_url)

    if (not container_registry_user and not container_registry_password and
            container_registry_url and '.azurecr.io' in container_registry_url):
        logger.warning('No credential was provided to access Azure Container Registry. Trying to look up...')
        parsed = urlparse(container_registry_url)
        registry_name = (parsed.netloc if parsed.scheme else parsed.path).split('.')[0]
        try:
            container_registry_user, container_registry_password = _get_acr_cred(cmd.cli_ctx, registry_name)
        except Exception as ex:  # pylint: disable=broad-except
            logger.warning("Retrieving credentials failed with an exception:'%s'", ex)  # consider throw if needed

    if container_registry_user is not None:
        settings.append('DOCKER_REGISTRY_SERVER_USERNAME=' + container_registry_user)
    if container_registry_password is not None:
        settings.append('DOCKER_REGISTRY_SERVER_PASSWORD=' + container_registry_password)
    if websites_enable_app_service_storage:
        settings.append('WEBSITES_ENABLE_APP_SERVICE_STORAGE=' + websites_enable_app_service_storage)

    if container_registry_user or container_registry_password or container_registry_url or websites_enable_app_service_storage:  # pylint: disable=line-too-long
        update_app_settings(cmd, resource_group_name, name, settings, slot)
    settings = get_app_settings(cmd, resource_group_name, name, slot)
    if container_image_name is not None:
        _add_fx_version(cmd, resource_group_name, name, container_image_name, slot)

    if multicontainer_config_file and multicontainer_config_type:
        encoded_config_file = _get_linux_multicontainer_encoded_config_from_file(multicontainer_config_file)
        linux_fx_version = _format_fx_version(encoded_config_file, multicontainer_config_type)
        update_site_configs(cmd, resource_group_name, name, linux_fx_version=linux_fx_version, slot=slot)
    elif multicontainer_config_file or multicontainer_config_type:
        logger.warning('Must change both settings --multicontainer-config-file FILE --multicontainer-config-type TYPE')

    if min_replicas is not None or max_replicas is not None:
        update_site_configs(cmd, resource_group_name, name, min_replicas=min_replicas, max_replicas=max_replicas)

    return _mask_creds_related_appsettings(_filter_for_container_settings(cmd, resource_group_name, name, settings,
                                                                          slot=slot))


def update_site_configs_functionapp(cmd, resource_group_name, name, slot=None, number_of_workers=None,
                                    linux_fx_version=None, windows_fx_version=None, pre_warmed_instance_count=None,
                                    php_version=None, python_version=None, net_framework_version=None,
                                    power_shell_version=None, java_version=None, java_container=None,
                                    java_container_version=None, remote_debugging_enabled=None,
                                    web_sockets_enabled=None, always_on=None, auto_heal_enabled=None,
                                    use32_bit_worker_process=None, min_tls_version=None,
                                    http20_enabled=None, app_command_line=None, ftps_state=None,
                                    vnet_route_all_enabled=None, generic_configurations=None, min_replicas=None,
                                    max_replicas=None):
    check_language_runtime(cmd, resource_group_name, name)
    return update_site_configs(cmd, resource_group_name, name, slot, number_of_workers=number_of_workers,
                               linux_fx_version=linux_fx_version, windows_fx_version=windows_fx_version,
                               pre_warmed_instance_count=pre_warmed_instance_count, php_version=php_version,
                               python_version=python_version, net_framework_version=net_framework_version,
                               power_shell_version=power_shell_version, java_version=java_version,
                               java_container=java_container, java_container_version=java_container_version,
                               remote_debugging_enabled=remote_debugging_enabled,
                               web_sockets_enabled=web_sockets_enabled, always_on=always_on,
                               auto_heal_enabled=auto_heal_enabled, use32_bit_worker_process=use32_bit_worker_process,
                               min_tls_version=min_tls_version, http20_enabled=http20_enabled,
                               app_command_line=app_command_line, ftps_state=ftps_state,
                               vnet_route_all_enabled=vnet_route_all_enabled,
                               generic_configurations=generic_configurations, min_replicas=min_replicas,
                               max_replicas=max_replicas)


def update_container_settings_functionapp(cmd, resource_group_name, name, registry_server=None,
                                          image=None, registry_username=None,
                                          registry_password=None, slot=None, min_replicas=None, max_replicas=None,
                                          enable_dapr=None, dapr_app_id=None, dapr_app_port=None,
                                          dapr_http_max_request_size=None, dapr_http_read_buffer_size=None,
                                          dapr_log_level=None, dapr_enable_api_logging=None,
                                          workload_profile_name=None, cpu=None, memory=None):
    check_language_runtime(cmd, resource_group_name, name)
    if is_centauri_functionapp(cmd, resource_group_name, name):
        _validate_cpu_momory_functionapp(cpu, memory)
        if any([enable_dapr, dapr_app_id, dapr_app_port, dapr_http_max_request_size, dapr_http_read_buffer_size,
                dapr_log_level, dapr_enable_api_logging, cpu, memory, workload_profile_name]):
            update_dapr_and_workload_config(cmd, resource_group_name, name, enable_dapr, dapr_app_id, dapr_app_port,
                                            dapr_http_max_request_size, dapr_http_read_buffer_size, dapr_log_level,
                                            dapr_enable_api_logging, workload_profile_name, cpu, memory)
    return update_container_settings(cmd, resource_group_name, name, registry_server,
                                     image, registry_username, None,
                                     registry_password, multicontainer_config_type=None,
                                     multicontainer_config_file=None, slot=slot,
                                     min_replicas=min_replicas, max_replicas=max_replicas)


def _get_acr_cred(cli_ctx, registry_name):
    from azure.mgmt.containerregistry import ContainerRegistryManagementClient
    from azure.cli.core.commands.parameters import get_resources_in_subscription
    client = get_mgmt_service_client(cli_ctx, ContainerRegistryManagementClient).registries

    result = get_resources_in_subscription(cli_ctx, 'Microsoft.ContainerRegistry/registries')
    result = [item for item in result if item.name.lower() == registry_name]
    if not result or len(result) > 1:
        raise ResourceNotFoundError("No resource or more than one were found with name '{}'.".format(registry_name))
    resource_group_name = parse_resource_id(result[0].id)['resource_group']

    registry = client.get(resource_group_name, registry_name)

    if registry.admin_user_enabled:  # pylint: disable=no-member
        cred = client.list_credentials(resource_group_name, registry_name)
        return cred.username, cred.passwords[0].value
    raise ResourceNotFoundError("Failed to retrieve container registry credentials. Please either provide the "
                                "credentials or run 'az acr update -n {} --admin-enabled true' to enable "
                                "admin first.".format(registry_name))


def delete_container_settings(cmd, resource_group_name, name, slot=None):
    _delete_linux_fx_version(cmd, resource_group_name, name, slot)
    delete_app_settings(cmd, resource_group_name, name, CONTAINER_APPSETTING_NAMES, slot)


def show_container_settings(cmd, resource_group_name, name, show_multicontainer_config=None, slot=None):
    settings = get_app_settings(cmd, resource_group_name, name, slot)
    return _mask_creds_related_appsettings(_filter_for_container_settings(cmd, resource_group_name, name, settings,
                                                                          show_multicontainer_config, slot))


def show_container_settings_functionapp(cmd, resource_group_name, name, slot=None):
    return show_container_settings(cmd, resource_group_name, name, show_multicontainer_config=None, slot=slot)


def _filter_for_container_settings(cmd, resource_group_name, name, settings,
                                   show_multicontainer_config=None, slot=None):
    result = [x for x in settings if x['name'] in CONTAINER_APPSETTING_NAMES]
    fx_version = _get_fx_version(cmd, resource_group_name, name, slot).strip()
    if fx_version:
        added_image_name = {'name': 'DOCKER_CUSTOM_IMAGE_NAME',
                            'value': fx_version}
        result.append(added_image_name)
        if show_multicontainer_config:
            decoded_value = _get_linux_multicontainer_decoded_config(cmd, resource_group_name, name, slot)
            decoded_image_name = {'name': 'DOCKER_CUSTOM_IMAGE_NAME_DECODED',
                                  'value': decoded_value}
            result.append(decoded_image_name)
    return result


# TODO: remove this when #3660(service tracking issue) is resolved
def _mask_creds_related_appsettings(settings):
    for x in [x1 for x1 in settings if x1 in APPSETTINGS_TO_MASK]:
        settings[x] = None
    return settings


def add_hostname(cmd, resource_group_name, webapp_name, hostname, slot=None):
    from azure.mgmt.web.models import HostNameBinding
    client = web_client_factory(cmd.cli_ctx)
    webapp = client.web_apps.get(resource_group_name, webapp_name)
    if not webapp:
        raise ResourceNotFoundError("'{}' app doesn't exist".format(webapp_name))
    binding = HostNameBinding(site_name=webapp.name)
    if slot is None:
        return client.web_apps.create_or_update_host_name_binding(resource_group_name=resource_group_name,
                                                                  name=webapp.name, host_name=hostname,
                                                                  host_name_binding=binding)

    return client.web_apps.create_or_update_host_name_binding_slot(resource_group_name=resource_group_name,
                                                                   name=webapp.name, host_name=hostname,
                                                                   slot=slot, host_name_binding=binding)


def delete_hostname(cmd, resource_group_name, webapp_name, hostname, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot is None:
        return client.web_apps.delete_host_name_binding(resource_group_name, webapp_name, hostname)

    return client.web_apps.delete_host_name_binding_slot(resource_group_name, webapp_name, slot, hostname)


def list_hostnames(cmd, resource_group_name, webapp_name, slot=None):
    result = list(_generic_site_operation(cmd.cli_ctx, resource_group_name, webapp_name,
                                          'list_host_name_bindings', slot))
    for r in result:
        r.name = r.name.split('/')[-1]
    return result


def get_external_ip(cmd, resource_group_name, webapp_name):
    SslState = cmd.get_models('SslState')
    # logics here are ported from portal
    client = web_client_factory(cmd.cli_ctx)
    webapp = client.web_apps.get(resource_group_name, webapp_name)
    if not webapp:
        raise ResourceNotFoundError("'{}' app doesn't exist".format(webapp_name))
    if webapp.hosting_environment_profile:
        address = client.app_service_environments.list_vips(
            resource_group_name, webapp.hosting_environment_profile.name)
        if address.internal_ip_address:
            ip_address = address.internal_ip_address
        else:
            vip = next((s for s in webapp.host_name_ssl_states if s.ssl_state == SslState.ip_based_enabled), None)
            ip_address = vip.virtual_ip if vip else address.service_ip_address
    else:
        ip_address = _resolve_hostname_through_dns(webapp.default_host_name)

    return {'ip': ip_address}


def _resolve_hostname_through_dns(hostname):
    import socket
    return socket.gethostbyname(hostname)


def create_webapp_slot(cmd, resource_group_name, webapp, slot, configuration_source=None,
                       deployment_container_image_name=None,
                       container_registry_url=None, container_image_name=None,
                       container_registry_password=None, container_registry_user=None):
    container_args = (deployment_container_image_name or container_registry_password or container_registry_user) or (
        container_registry_password or container_registry_user or container_image_name)
    if container_args and not configuration_source:
        if deployment_container_image_name:
            raise ArgumentUsageError("Cannot use arguments --deployment-container-image-name, "
                                     "--container-registry-password, or --container-registry-user without argument "
                                     "--configuration-source")
        raise ArgumentUsageError("Cannot use arguments --container-image-name, "
                                 "--container-registry-password, or --container-registry-user without argument "
                                 "--configuration-source")
    if deployment_container_image_name and container_image_name:
        raise MutuallyExclusiveArgumentError('Cannot use both --deployment-container-image-name'
                                             ' and --container-image-name')
    if container_registry_url and not container_image_name:
        raise ArgumentUsageError('Please specify both --container-registry-url and --container-image-name')

    if container_registry_url:
        container_registry_url = parse_container_registry_url(container_registry_url)
    else:
        container_registry_url = parse_docker_image_name(deployment_container_image_name)

    if container_image_name:
        container_image_name = container_image_name if not container_registry_url else "{}/{}".format(
            urlparse(container_registry_url).hostname,
            container_image_name[1:] if container_image_name.startswith('/') else container_image_name)
    if deployment_container_image_name:
        container_image_name = deployment_container_image_name

    Site, SiteConfig, NameValuePair = cmd.get_models('Site', 'SiteConfig', 'NameValuePair')
    client = web_client_factory(cmd.cli_ctx)
    site = client.web_apps.get(resource_group_name, webapp)
    site_config = get_site_configs(cmd, resource_group_name, webapp, None)
    if not site:
        raise ResourceNotFoundError("'{}' app doesn't exist".format(webapp))
    if 'functionapp' in site.kind:
        raise ValidationError("'{}' is a function app. Please use "
                              "`az functionapp deployment slot create`.".format(webapp))
    location = site.location
    slot_def = Site(server_farm_id=site.server_farm_id, location=location)
    slot_def.site_config = SiteConfig()

    # Do not clone site config when cloning from production
    if configuration_source and configuration_source.lower() == webapp.lower():
        slot_def.site_config = None

    # Match cloned site settings from Azure portal
    slot_def.https_only = site.https_only
    slot_def.client_cert_enabled = site.client_cert_enabled
    slot_def.client_cert_mode = site.client_cert_mode
    slot_def.client_cert_exclusion_paths = site.client_cert_exclusion_paths
    slot_def.public_network_access = site.public_network_access

    # if it is a Windows Container site, at least pass the necessary
    # app settings to perform the container image validation:
    if configuration_source and site_config.windows_fx_version:
        # get settings from the source
        clone_from_prod = configuration_source.lower() == webapp.lower()
        src_slot = None if clone_from_prod else configuration_source
        app_settings = _generic_site_operation(cmd.cli_ctx, resource_group_name, webapp,
                                               'list_application_settings', src_slot)
        settings = []
        for k, v in app_settings.properties.items():
            if k in ("DOCKER_REGISTRY_SERVER_USERNAME", "DOCKER_REGISTRY_SERVER_PASSWORD",
                     "DOCKER_REGISTRY_SERVER_URL"):
                settings.append(NameValuePair(name=k, value=v))
        slot_def.site_config = SiteConfig(app_settings=settings)
    poller = client.web_apps.begin_create_or_update_slot(resource_group_name, webapp, site_envelope=slot_def, slot=slot)
    result = LongRunningOperation(cmd.cli_ctx)(poller)

    if configuration_source:
        update_slot_configuration_from_source(cmd, client, resource_group_name, webapp, slot, configuration_source,
                                              container_image_name, container_registry_password,
                                              container_registry_user,
                                              container_registry_url=container_registry_url)

    result.name = result.name.split('/')[-1]
    return result


def create_functionapp_slot(cmd, resource_group_name, name, slot, configuration_source=None,
                            image=None, registry_password=None,
                            registry_username=None, https_only=True):
    container_args = image or registry_password or registry_username
    if container_args and not configuration_source:
        raise ArgumentUsageError("Cannot use image, password and username arguments without "
                                 "--configuration-source argument")

    docker_registry_server_url = parse_docker_image_name(image)

    Site = cmd.get_models('Site')
    client = web_client_factory(cmd.cli_ctx)
    site = client.web_apps.get(resource_group_name, name)
    if not site:
        raise ResourceNotFoundError("'{}' function app doesn't exist".format(name))
    location = site.location
    slot_def = Site(server_farm_id=site.server_farm_id, location=location, https_only=https_only)

    poller = client.web_apps.begin_create_or_update_slot(resource_group_name, name, site_envelope=slot_def, slot=slot)
    result = LongRunningOperation(cmd.cli_ctx)(poller)

    if configuration_source:
        update_slot_configuration_from_source(cmd, client, resource_group_name, name, slot, configuration_source,
                                              image, registry_password,
                                              registry_username,
                                              container_registry_url=docker_registry_server_url)

    result.name = result.name.split('/')[-1]
    return result


def _resolve_storage_account_resource_group(cmd, name):
    from azure.cli.command_modules.storage.operations.account import list_storage_accounts
    accounts = [a for a in list_storage_accounts(cmd) if a.name == name]
    if accounts:
        return parse_resource_id(accounts[0].id).get("resource_group")


def _set_site_config_storage_keys(cmd, site_config):
    from azure.cli.command_modules.storage._client_factory import cf_sa_for_keys

    for _, acct in site_config.azure_storage_accounts.items():
        if acct.access_key is None:
            scf = cf_sa_for_keys(cmd.cli_ctx, None)
            acct_rg = _resolve_storage_account_resource_group(cmd, acct.account_name)
            keys = scf.list_keys(acct_rg, acct.account_name, logging_enable=False).keys
            if keys:
                key = keys[0]
                logger.info("Retreived key %s", key.key_name)
                acct.access_key = key.value


def update_slot_configuration_from_source(cmd, client, resource_group_name, webapp, slot, configuration_source=None,
                                          container_image_name=None, container_registry_password=None,
                                          container_registry_user=None, container_registry_url=None):

    clone_from_prod = configuration_source.lower() == webapp.lower()
    site_config = get_site_configs(cmd, resource_group_name, webapp,
                                   None if clone_from_prod else configuration_source)
    if site_config.azure_storage_accounts:
        logger.warning("The configuration source has storage accounts. Looking up their access keys...")
        _set_site_config_storage_keys(cmd, site_config)

    _generic_site_operation(cmd.cli_ctx, resource_group_name, webapp,
                            'update_configuration', slot, site_config)

    # slot create doesn't clone over the app-settings and connection-strings, so we do it here
    # also make sure slot settings don't get propagated.

    slot_cfg_names = client.web_apps.list_slot_configuration_names(resource_group_name, webapp)
    src_slot = None if clone_from_prod else configuration_source
    app_settings = _generic_site_operation(cmd.cli_ctx, resource_group_name, webapp,
                                           'list_application_settings',
                                           src_slot)
    for a in slot_cfg_names.app_setting_names or []:
        app_settings.properties.pop(a, None)

    connection_strings = _generic_site_operation(cmd.cli_ctx, resource_group_name, webapp,
                                                 'list_connection_strings',
                                                 src_slot)
    for a in slot_cfg_names.connection_string_names or []:
        connection_strings.properties.pop(a, None)

    _generic_settings_operation(cmd.cli_ctx, resource_group_name, webapp,
                                'update_application_settings',
                                app_settings, slot, client)
    _generic_settings_operation(cmd.cli_ctx, resource_group_name, webapp,
                                'update_connection_strings',
                                connection_strings, slot, client)

    if container_image_name or container_registry_password or container_registry_user:
        update_container_settings(cmd, resource_group_name, webapp,
                                  container_image_name=container_image_name, slot=slot,
                                  container_registry_user=container_registry_user,
                                  container_registry_password=container_registry_password,
                                  container_registry_url=container_registry_url)


def config_source_control(cmd, resource_group_name, name, repo_url, repository_type='git', branch=None,  # pylint: disable=too-many-locals
                          manual_integration=None, git_token=None, slot=None, github_action=None):
    client = web_client_factory(cmd.cli_ctx)
    location = _get_location_from_webapp(client, resource_group_name, name)

    from azure.mgmt.web.models import SiteSourceControl, SourceControl
    if git_token:
        sc = SourceControl(location=location, source_control_name='GitHub', token=git_token)
        client.update_source_control('GitHub', sc)

    source_control = SiteSourceControl(location=location, repo_url=repo_url, branch=branch,
                                       is_manual_integration=manual_integration,
                                       is_mercurial=(repository_type != 'git'), is_git_hub_action=bool(github_action))

    # SCC config can fail if previous commands caused SCMSite shutdown, so retry here.
    for i in range(5):
        try:
            poller = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                             'begin_create_or_update_source_control',
                                             slot, source_control)
            response = LongRunningOperation(cmd.cli_ctx)(poller)
            if response.git_hub_action_configuration and \
                response.git_hub_action_configuration.container_configuration and \
                    response.git_hub_action_configuration.container_configuration.password:
                logger.warning("GitHub action password has been redacted. Use "
                               "`az webapp/functionapp deployment source show` to view.")
                response.git_hub_action_configuration.container_configuration.password = None
            return response
        except Exception as ex:  # pylint: disable=broad-except
            ex = ex_handler_factory(no_throw=True)(ex)
            # for non server errors(50x), just throw; otherwise retry 4 times
            if i == 4 or not re.findall(r'\(50\d\)', str(ex)):
                raise
            logger.warning('retrying %s/4', i + 1)
            time.sleep(5)   # retry in a moment


def update_git_token(cmd, git_token=None):
    '''
    Update source control token cached in Azure app service. If no token is provided,
    the command will clean up existing token. Note that tokens are now redacted in the result.
    '''
    client = web_client_factory(cmd.cli_ctx)
    from azure.mgmt.web.models import SourceControl
    sc = SourceControl(name='not-really-needed', source_control_name='GitHub', token=git_token or '')
    response = client.update_source_control('GitHub', sc)
    logger.warning('Tokens have been redacted.')
    response.refresh_token = None
    response.token = None
    response.token_secret = None
    return response


def show_source_control(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get_source_control', slot)


def delete_source_control(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'delete_source_control', slot)


def enable_local_git(cmd, resource_group_name, name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    site_config = get_site_configs(cmd, resource_group_name, name, slot)
    site_config.scm_type = 'LocalGit'
    _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'create_or_update_configuration', slot, site_config)
    return {'url': _get_local_git_url(cmd.cli_ctx, client, resource_group_name, name, slot)}


def sync_site_repo(cmd, resource_group_name, name, slot=None):
    try:
        return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'sync_repository', slot)
    except HttpResponseError as ex:  # Because of bad spec, sdk throws on 200. We capture it here
        if ex.status_code not in [200, 204]:
            raise ex


def list_app_service_plans(cmd, resource_group_name=None):
    client = web_client_factory(cmd.cli_ctx)
    if resource_group_name is None:
        plans = list(client.app_service_plans.list(detailed=True))  # enables querying "numberOfSites"
    else:
        plans = list(client.app_service_plans.list_by_resource_group(resource_group_name))
    for plan in plans:
        # prune a few useless fields
        del plan.geo_region
        del plan.subscription
    return plans


# TODO use zone_redundant field on ASP model when we switch to SDK version 5.0.0
def _enable_zone_redundant(plan_def, sku_def, number_of_workers):
    plan_def.enable_additional_properties_sending()
    existing_properties = plan_def.serialize()["properties"]
    plan_def.additional_properties["properties"] = existing_properties
    plan_def.additional_properties["properties"]["zoneRedundant"] = True
    if number_of_workers is None:
        sku_def.capacity = 3
    else:
        sku_def.capacity = max(3, number_of_workers)


# Progress bar for serverfarm async scaling operations
class PlanProgressBar(IndeterminateProgressBar):
    STATUS_CHECK_INTERVAL_SEC = 60

    def __init__(self, cli_ctx, resource_group_name, plan_name):
        self.client = web_client_factory(cli_ctx).app_service_plans
        self.rg = resource_group_name
        self.plan_name = plan_name
        self._last_msg = None
        self._last_status_check = None
        super().__init__(cli_ctx)

    def _emit(self, msg):
        if msg != self._last_msg:
            logger.warning(msg)
            self._last_msg = msg

    def begin(self):
        self._emit(f"Starting to scale App Service plan {self.plan_name}...")
        super().begin()

    def update_progress_with_msg(self, message):
        self._safe_update_progress_message(message)
        super().update_progress_with_msg(message)

    def end(self):
        plan = self.client.get(self.rg, self.plan_name)
        capacity = None
        sku_name = None

        if getattr(plan, 'sku', None):
            capacity = getattr(plan.sku, 'capacity', None)
            sku_name = getattr(plan.sku, 'name', None)

        if capacity is not None and sku_name is not None:
            self._emit(f"Successfully scaled to {capacity} workers in pricing tier {sku_name}.")

        super().end()

    def stop(self):
        logger.error("Operation wait cancelled. The async scaling operation is still in progress. "
                     "Please update the plan to stop scaling.")
        super().stop()

    def _safe_update_progress_message(self, message):
        # Only check real status periodically to avoid hammering API
        now = time.monotonic()
        if (self._last_status_check is not None and
                now - self._last_status_check < PlanProgressBar.STATUS_CHECK_INTERVAL_SEC):
            return

        try:
            plan = self.client.get(self.rg, self.plan_name)
            capacity = None
            skuName = None
            if getattr(plan, 'sku', None):
                capacity = getattr(plan.sku, 'capacity', None)
                skuName = getattr(plan.sku, 'name', None)

            status = message or "InProgress"
            details = f"Status: {status} — Scaled to {capacity} workers of pricing tier {skuName}."
            self._last_status_check = now
            self._emit(details)
        except Exception:  # pylint: disable=broad-except
            self._emit("Scaling in progress...")


def is_async_response(poller, timeout_seconds=30):
    for _ in range(timeout_seconds):
        if poller.done():
            break

        if hasattr(poller._polling_method, '_initial_response'):  # pylint: disable=protected-access
            break

        time.sleep(1)

    # pylint: disable=protected-access
    if (
        not hasattr(poller._polling_method, '_initial_response') or
        not hasattr(poller._polling_method._initial_response, 'http_response') or
        not hasattr(poller._polling_method._initial_response.http_response, 'status_code')
    ):
        return False

    # Check if this is an asynchronous operation (202)
    status_code = poller._polling_method._initial_response.http_response.status_code
    # pylint: enable=protected-access
    return status_code == 202


def create_app_service_plan(cmd, resource_group_name, name, is_linux, hyper_v, per_site_scaling=False,
                            app_service_environment=None, sku='B1', number_of_workers=None, location=None,
                            tags=None, no_wait=False, zone_redundant=False, async_scaling_enabled=None,
                            is_managed_instance=None, mi_system_assigned=None, mi_user_assigned=None,
                            default_identity=None, rdp_enabled=None, vnet=None, subnet=None,
                            registry_adapters=None, install_scripts=None, storage_mounts=None):
    HostingEnvironmentProfile, SkuDescription, AppServicePlan = cmd.get_models(
        'HostingEnvironmentProfile', 'SkuDescription', 'AppServicePlan')

    client = web_client_factory(cmd.cli_ctx)
    if app_service_environment:
        # Method app_service_environments.list can only list ASE form the same subscription.
        ase_list = client.app_service_environments.list()
        ase_found = False
        ase = None
        for ase in ase_list:
            if ase.name.lower() == app_service_environment.lower() or ase.id.lower() == app_service_environment.lower():
                ase_def = HostingEnvironmentProfile(id=ase.id)
                location = ase.location
                ase_found = True
                break
        if not ase_found:
            if is_valid_resource_id(app_service_environment):
                ase_def = HostingEnvironmentProfile(id=app_service_environment)
                if location is None:
                    location = _get_location_from_resource_group(cmd.cli_ctx, resource_group_name)
            else:
                err_msg = "App service environment '{}' not found in subscription. If you want to create the \
app service plan in different subscription than the app service environment, please use the resource ID for \
--app-service-environment parameter. Additionally if the resource group is in different region than the \
app service environment, please use --location parameter and specify the region where the app service environment \
has been deployed ".format(app_service_environment)
                raise ResourceNotFoundError(err_msg)
        if hyper_v and ase.kind in ('ASEV1', 'ASEV2'):
            raise ArgumentUsageError('Windows containers are only supported on App Service Environment v3')
    else:  # Non-ASE
        ase_def = None
        if location is None:
            location = _get_location_from_resource_group(cmd.cli_ctx, resource_group_name)

    # the api is odd on parameter naming, have to live with it for now
    sku_def = SkuDescription(tier=get_sku_tier(sku), name=_normalize_sku(sku), capacity=number_of_workers)
    plan_def = AppServicePlan(location=location, tags=tags, sku=sku_def,
                              reserved=(is_linux or None), hyper_v=(hyper_v or None),
                              per_site_scaling=per_site_scaling, hosting_environment_profile=ase_def,
                              async_scaling_enabled=async_scaling_enabled)

    if sku.upper() in ['WS1', 'WS2', 'WS3']:
        existing_plan = get_resource_if_exists(client.app_service_plans,
                                               resource_group_name=resource_group_name, name=name)
        if existing_plan and existing_plan.sku.tier != "WorkflowStandard":
            raise ValidationError("Plan {} in resource group {} already exists and "
                                  "cannot be updated to a logic app SKU (WS1, WS2, or WS3)")
        plan_def.type = "elastic"

    if zone_redundant:
        _enable_zone_redundant(plan_def, sku_def, number_of_workers)

    if subnet or vnet:
        subnet_info = _get_subnet_info(cmd=cmd,
                                       resource_group_name=resource_group_name,
                                       subnet=subnet,
                                       vnet=vnet,
                                       attached_resource="app service plan")
        _validate_vnet_integration_location(cmd=cmd, webapp_location=location,
                                            subnet_resource_group=subnet_info["resource_group_name"],
                                            vnet_name=subnet_info["vnet_name"],
                                            vnet_sub_id=subnet_info["subnet_subscription_id"])
        _vnet_delegation_check(cmd, subnet_subscription_id=subnet_info["subnet_subscription_id"],
                               vnet_resource_group=subnet_info["resource_group_name"],
                               vnet_name=subnet_info["vnet_name"],
                               subnet_name=subnet_info["subnet_name"])
        subnet_resource_id = subnet_info["subnet_resource_id"]
    else:
        subnet_resource_id = None

    # Transform default_identity parameter into the proper structure
    plan_default_identity = _build_plan_default_identity(default_identity)

    hosting_environment_profile = None
    if plan_def.hosting_environment_profile:
        hosting_environment_profile = plan_def.hosting_environment_profile.__dict__

    class AppServicePlanCreateWithNoWait(AppServicePlanCreate):
        def pre_operations(self):
            args = self.ctx.args
            args.no_wait = no_wait

    poller = AppServicePlanCreateWithNoWait(cli_ctx=cmd.cli_ctx)(command_args={
        "name": name,
        "resource_group": resource_group_name,
        "location": location,
        "tags": tags,
        "sku": sku_def.__dict__,
        "reserved": plan_def.reserved,
        "hyper_v": plan_def.hyper_v,
        "per_site_scaling": plan_def.per_site_scaling,
        "hosting_environment_profile": hosting_environment_profile,
        "async_scaling_enabled": plan_def.async_scaling_enabled,
        "zone_redundant": zone_redundant if zone_redundant else None,
        "is_custom_mode": is_managed_instance,
        "network": {
            "virtual_network_subnet_id": subnet_resource_id,
        } if subnet_resource_id else None,
        "rdp_enabled": rdp_enabled,
        "mi_system_assigned": str(mi_system_assigned) if mi_system_assigned else None,
        "mi_user_assigned": mi_user_assigned,
        "plan_default_identity": plan_default_identity,
        "registry_adapters": registry_adapters,
        "install_scripts": install_scripts,
        "storage_mounts": storage_mounts,
    })

    if no_wait:
        return poller.result()

    # Check if this is an asynchronous operation
    is_async = is_async_response(poller)

    if not is_async:
        # for synchronous operations, or if we are unable to get the initial response, directly return poller result
        return poller.result()

    # Asynchronous operation (202 response), use custom progress bar
    progress_bar = PlanProgressBar(cmd.cli_ctx, resource_group_name, name)
    return LongRunningOperation(cmd.cli_ctx, progress_bar=progress_bar)(poller)


def update_app_service_plan_with_progress(cmd, resource_group_name, name, app_service_plan):
    client = web_client_factory(cmd.cli_ctx)

    # For regular execution, apply conditional progress logic
    poller = client.app_service_plans.begin_create_or_update(resource_group_name, name, app_service_plan)

    if poller.done():
        # Synchronous operation (200 response), return result directly
        return poller.result()

    # Asynchronous operation (202 response), use custom progress bar
    progress_bar = PlanProgressBar(cmd.cli_ctx, resource_group_name, name)
    return LongRunningOperation(cmd.cli_ctx, progress_bar=progress_bar)(poller)


def update_app_service_plan(cmd, instance, sku=None, number_of_workers=None, elastic_scale=None,
                            max_elastic_worker_count=None, async_scaling_enabled=None,
                            default_identity=None, rdp_enabled=None, vnet=None, subnet=None,
                            registry_adapters=None, install_scripts=None, storage_mounts=None):
    has_updates = any(param is not None for param in [
        number_of_workers, sku, elastic_scale, max_elastic_worker_count,
        async_scaling_enabled, default_identity, rdp_enabled, vnet, subnet,
        registry_adapters, install_scripts, storage_mounts
    ])

    if not has_updates:
        safe_params = cmd.cli_ctx.data['safe_params']
        if '--set' not in safe_params:
            args = ["--number-of-workers",
                    "--sku",
                    "--elastic-scale",
                    "--max-elastic-worker-count",
                    "--async-scaling-enabled",
                    "--default-identity",
                    "--rdp-enabled",
                    "--vnet",
                    "--subnet",
                    "--registry-adapter",
                    "--install-script",
                    "--storage-mount"]
            logger.warning('Nothing to update. Set one of the following parameters to make an update: %s', str(args))
    sku_def = instance.sku
    if sku is not None:
        sku = _normalize_sku(sku)
        sku_def.tier = get_sku_tier(sku)
        sku_def.name = sku

    if number_of_workers is not None:
        sku_def.capacity = number_of_workers
    else:
        number_of_workers = sku_def.capacity

    if elastic_scale is not None or max_elastic_worker_count is not None:
        if sku is None:
            sku = instance.sku.name
        if get_sku_tier(sku) not in ["PREMIUMV2", "PREMIUMV3", "WorkflowStandard"]:
            raise ValidationError("--number-of-workers and --elastic-scale can only "
                                  "be used on premium V2/V3 or workflow SKUs. "
                                  "Use command help to see all available SKUs.")

    if elastic_scale is not None:
        # TODO use instance.elastic_scale_enabled once the ASP client factories are updated
        use_additional_properties(instance)
        instance.additional_properties["properties"]["elasticScaleEnabled"] = elastic_scale

    if max_elastic_worker_count is not None:
        instance.maximum_elastic_worker_count = max_elastic_worker_count
        if max_elastic_worker_count < number_of_workers:
            raise InvalidArgumentValueError("--max-elastic-worker-count must be greater than or equal to the "
                                            "plan's number of workers. To update the plan's number of workers, use "
                                            "--number-of-workers ")
        # TODO use instance.maximum_elastic_worker_count once the ASP client factories are updated
        use_additional_properties(instance)
        instance.additional_properties["properties"]["maximumElasticWorkerCount"] = max_elastic_worker_count

    if async_scaling_enabled is not None:
        instance.async_scaling_enabled = async_scaling_enabled

    # Handle VNet integration
    subnet_resource_id = None
    if subnet or vnet:
        subnet_info = _get_subnet_info(cmd=cmd,
                                       resource_group_name=instance.resource_group,
                                       subnet=subnet,
                                       vnet=vnet,
                                       attached_resource="app service plan")
        _validate_vnet_integration_location(cmd=cmd, webapp_location=instance.location,
                                            subnet_resource_group=subnet_info["resource_group_name"],
                                            vnet_name=subnet_info["vnet_name"],
                                            vnet_sub_id=subnet_info["subnet_subscription_id"])
        _vnet_delegation_check(cmd, subnet_subscription_id=subnet_info["subnet_subscription_id"],
                               vnet_resource_group=subnet_info["resource_group_name"],
                               vnet_name=subnet_info["vnet_name"],
                               subnet_name=subnet_info["subnet_name"])
        subnet_resource_id = subnet_info["subnet_resource_id"]

    # Transform default_identity parameter into the proper structure
    plan_default_identity = _build_plan_default_identity_sdk(default_identity)

    # Configure managed instance properties
    _enable_managed_instance_properties(instance,
                                        default_identity=plan_default_identity,
                                        subnet_resource_id=subnet_resource_id,
                                        rdp_enabled=rdp_enabled,
                                        registry_adapters=registry_adapters,
                                        install_scripts=install_scripts,
                                        storage_mounts=storage_mounts)

    instance.sku = sku_def
    return instance


def _enable_managed_instance_properties(plan_def, default_identity=None, subnet_resource_id=None, rdp_enabled=None,
                                        registry_adapters=None, install_scripts=None, storage_mounts=None):
    """Configure additional properties for managed instance App Service Plan features."""
    # Only enable additional properties if we have managed instance features to configure
    has_managed_instance_features = any([
        default_identity,
        subnet_resource_id,
        rdp_enabled is not None,
        registry_adapters,
        install_scripts,
        storage_mounts
    ])

    if not has_managed_instance_features:
        return

    plan_def.enable_additional_properties_sending()

    # Only set properties if they haven't been set already (e.g., by elastic scale)
    if "properties" not in plan_def.additional_properties:
        existing_properties = plan_def.serialize()["properties"]
        plan_def.additional_properties["properties"] = existing_properties

    # Configure network (VNet integration)
    if subnet_resource_id:
        plan_def.additional_properties["properties"]["network"] = {
            "virtualNetworkSubnetId": subnet_resource_id
        }

    # Configure RDP access
    if rdp_enabled is not None:
        plan_def.additional_properties["properties"]["rdpEnabled"] = rdp_enabled

    # Configure default identity
    if default_identity:
        plan_def.additional_properties["properties"]["planDefaultIdentity"] = default_identity

    # Configure registry adapters
    if registry_adapters:
        plan_def.additional_properties["properties"]["registryAdapters"] = registry_adapters

    # Configure install scripts
    if install_scripts:
        plan_def.additional_properties["properties"]["installScripts"] = install_scripts

    # Configure storage mounts
    if storage_mounts:
        plan_def.additional_properties["properties"]["storageMounts"] = storage_mounts


def show_plan(cmd, resource_group_name, name):
    from azure.cli.core.commands.client_factory import get_subscription_id
    client = web_client_factory(cmd.cli_ctx)
    serverfarm_url_base = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Web/serverfarms/{}?api-version={}'
    subscription_id = get_subscription_id(cmd.cli_ctx)
    serverfarm_url = serverfarm_url_base.format(subscription_id, resource_group_name, name, client.DEFAULT_API_VERSION)
    request_url = cmd.cli_ctx.cloud.endpoints.resource_manager + serverfarm_url
    response = send_raw_request(cmd.cli_ctx, "GET", request_url)
    return response.json()


def update_functionapp_app_service_plan(cmd, instance, sku=None, number_of_workers=None, max_burst=None):
    instance = update_app_service_plan(cmd, instance, sku, number_of_workers)
    if max_burst is not None:
        if not is_plan_elastic_premium(cmd, instance):
            raise ValidationError("Usage error: --max-burst is only supported for Elastic Premium (EP) plans")
        max_burst = validate_range_of_int_flag('--max-burst', max_burst, min_val=0, max_val=20)
        instance.maximum_elastic_worker_count = max_burst
    if number_of_workers is not None:
        number_of_workers = validate_range_of_int_flag('--number-of-workers / --min-instances',
                                                       number_of_workers, min_val=0, max_val=20)
    if is_plan_flex(cmd, instance):
        return update_flex_app_service_plan(instance)

    return update_app_service_plan(cmd, instance, sku, number_of_workers)


def list_plan_managed_instance_registry_adapters(cmd, resource_group_name, name):
    plan_show_cmd = AppServicePlanShow(cli_ctx=cmd.cli_ctx)
    plan_result = plan_show_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    return plan_result.get('registryAdapters', [])


def _update_plan_registry_adapters(cmd, resource_group_name, name, adapters, current_plan):
    plan_create_cmd = AppServicePlanCreate(cli_ctx=cmd.cli_ctx)
    poller = plan_create_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name,
        'location': current_plan.get('location'),
        'sku': current_plan.get('sku', {}),
        'registry_adapters': adapters
    })

    # Wait for the operation to complete and get the result
    plan_result = poller.result()

    # Return the updated registry adapters directly from the result
    return plan_result.get('registryAdapters', [])


def add_plan_managed_instance_registry_adapter(cmd, resource_group_name, name,
                                               registry_key, adapter_type, secret_uri):
    plan_show_cmd = AppServicePlanShow(cli_ctx=cmd.cli_ctx)
    plan_result = plan_show_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    # Extract current adapters directly from the plan result
    existing_adapters = plan_result.get('registryAdapters', [])
    updated_adapters = []
    adapter_found = False

    # New adapter
    adapter_obj = {
        'registryKey': registry_key,
        'type': adapter_type,
        'keyVaultSecretReference': {
            'secretUri': secret_uri
        }
    }

    for adapter in existing_adapters:
        if adapter.get('registryKey', '').lower() == registry_key.lower():
            # Replace the existing adapter in the same position
            updated_adapters.append(adapter_obj)
            adapter_found = True
        else:
            # Keep existing adapter
            updated_adapters.append(adapter)

    if not adapter_found:
        updated_adapters.append(adapter_obj)

    return _update_plan_registry_adapters(cmd, resource_group_name, name, updated_adapters, plan_result)


def remove_plan_managed_instance_registry_adapter(cmd, resource_group_name, name, registry_key):
    plan_show_cmd = AppServicePlanShow(cli_ctx=cmd.cli_ctx)
    plan_result = plan_show_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    # Extract current adapters directly from the plan result
    adapters = plan_result.get('registryAdapters', [])

    # Remove adapter by case-insensitive registry key
    updated_adapters = [a for a in adapters if a.get('registryKey', '').lower() != registry_key.lower()]
    if len(adapters) == len(updated_adapters):
        raise ResourceNotFoundError("Registry key {} not found".format(registry_key))

    return _update_plan_registry_adapters(cmd, resource_group_name, name, updated_adapters, plan_result)


def list_plan_managed_instance_install_scripts(cmd, resource_group_name, name):
    plan_show_cmd = AppServicePlanShow(cli_ctx=cmd.cli_ctx)
    plan_result = plan_show_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    return plan_result.get('installScripts', [])


def _update_plan_install_scripts(cmd, resource_group_name, name, scripts, current_plan):
    plan_create_cmd = AppServicePlanCreate(cli_ctx=cmd.cli_ctx)
    poller = plan_create_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name,
        'location': current_plan.get('location'),
        'sku': current_plan.get('sku', {}),
        'install_scripts': scripts
    })

    plan_result = poller.result()

    return plan_result.get('installScripts', [])


def add_plan_managed_instance_install_script(cmd, resource_group_name, name,
                                             install_script_name, source_uri, install_script_type):
    plan_show_cmd = AppServicePlanShow(cli_ctx=cmd.cli_ctx)
    plan_result = plan_show_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    # Extract current scripts directly from the plan result
    existing_scripts = plan_result.get('installScripts', [])
    updated_scripts = []
    script_found = False

    # New script object
    script_obj = {
        'name': install_script_name,
        'source': {
            'sourceUri': source_uri,
            'type': install_script_type
        }
    }

    # Replace existing script in the same position or add to end
    for script in existing_scripts:
        if script.get('name', '').lower() == install_script_name.lower():
            # Replace the existing script in the same position
            updated_scripts.append(script_obj)
            script_found = True
        else:
            # Keep existing script
            updated_scripts.append(script)

    # If script wasn't found, add it to the end
    if not script_found:
        updated_scripts.append(script_obj)

    return _update_plan_install_scripts(cmd, resource_group_name, name, updated_scripts, plan_result)


def remove_plan_managed_instance_install_script(cmd, resource_group_name, name, install_script_name):
    plan_show_cmd = AppServicePlanShow(cli_ctx=cmd.cli_ctx)
    plan_result = plan_show_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    # Extract current scripts directly from the plan result
    scripts = plan_result.get('installScripts', [])

    # Remove script by case-insensitive name
    updated_scripts = [s for s in scripts if s.get('name', '').lower() != install_script_name.lower()]

    if len(scripts) == len(updated_scripts):
        raise ResourceNotFoundError("Install script with name {} not found".format(install_script_name))

    return _update_plan_install_scripts(cmd, resource_group_name, name, updated_scripts, plan_result)


def list_plan_managed_instance_storage_mounts(cmd, resource_group_name, name):
    plan_show_cmd = AppServicePlanShow(cli_ctx=cmd.cli_ctx)
    plan_result = plan_show_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    return plan_result.get('storageMounts', [])


def _update_plan_storage_mounts(cmd, resource_group_name, name, mounts, current_plan):
    plan_create_cmd = AppServicePlanCreate(cli_ctx=cmd.cli_ctx)
    poller = plan_create_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name,
        'location': current_plan.get('location'),
        'sku': current_plan.get('sku', {}),
        'storage_mounts': mounts
    })

    plan_result = poller.result()

    return plan_result.get('storageMounts', [])


def add_plan_managed_instance_storage_mount(cmd, resource_group_name, name,
                                            mount_name, mount_type,
                                            destination_path, source=None, credentials_secret_uri=None):
    if not source and mount_type.lower() != "localstorage":
        raise InvalidArgumentValueError("--source argument is required for mount type {}".format(mount_type))

    plan_show_cmd = AppServicePlanShow(cli_ctx=cmd.cli_ctx)
    plan_result = plan_show_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    # Extract current mounts directly from the plan result
    existing_mounts = plan_result.get('storageMounts', [])
    updated_mounts = []
    mount_found = False

    # New mount object
    mount_obj = {
        'name': mount_name,
        'source': source,
        'type': mount_type,
        'destinationPath': destination_path
    }

    # Add credentials key vault reference if provided
    if credentials_secret_uri:
        mount_obj['credentialsKeyVaultReference'] = {
            'secretUri': credentials_secret_uri
        }

    # Replace existing mount in the same position or add to end
    for mount in existing_mounts:
        if mount.get('name', '').lower() == mount_name.lower():
            # Replace the existing mount in the same position
            updated_mounts.append(mount_obj)
            mount_found = True
        else:
            # Keep existing mount
            updated_mounts.append(mount)

    # If mount wasn't found, add it to the end
    if not mount_found:
        updated_mounts.append(mount_obj)

    return _update_plan_storage_mounts(cmd, resource_group_name, name, updated_mounts, plan_result)


def remove_plan_managed_instance_storage_mount(cmd, resource_group_name, name, mount_name):
    plan_show_cmd = AppServicePlanShow(cli_ctx=cmd.cli_ctx)
    plan_result = plan_show_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    # Extract current mounts directly from the plan result
    mounts = plan_result.get('storageMounts', [])

    # Remove mount by case-insensitive name
    updated_mounts = [m for m in mounts if m.get('name', '').lower() != mount_name.lower()]
    if len(mounts) == len(updated_mounts):
        raise ResourceNotFoundError("Storage mount with name {} not found".format(mount_name))

    return _update_plan_storage_mounts(cmd, resource_group_name, name, updated_mounts, plan_result)


def show_plan_managed_instance_network(cmd, resource_group_name, name):
    plan_show_cmd = AppServicePlanShow(cli_ctx=cmd.cli_ctx)
    plan_result = plan_show_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    # Return the whole network information from the plan result
    return plan_result.get('network', {})


def _update_plan_network(cmd, resource_group_name, name, subnet_resource_id, current_plan):
    plan_create_cmd = AppServicePlanCreate(cli_ctx=cmd.cli_ctx)

    # Handle None, empty string, and actual resource IDs properly
    if subnet_resource_id is None:
        network_config = None
    else:
        network_config = {
            'virtual_network_subnet_id': subnet_resource_id
        }

    poller = plan_create_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name,
        'location': current_plan.get('location'),
        'sku': current_plan.get('sku', {}),
        'network': network_config
    })

    plan_result = poller.result()

    # Return the whole network information from the updated plan result
    return plan_result.get('network', {})


def add_plan_managed_instance_network(cmd, resource_group_name, name, vnet=None, subnet=None):
    # Validate that both vnet and subnet are provided
    if not subnet and not vnet:
        raise RequiredArgumentMissingError('Either --subnet or both --vnet and --subnet arguments are required.')

    plan_show_cmd = AppServicePlanShow(cli_ctx=cmd.cli_ctx)
    plan_result = plan_show_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    location = plan_result.get('location')

    if subnet or vnet:
        subnet_info = _get_subnet_info(cmd=cmd,
                                       resource_group_name=resource_group_name,
                                       subnet=subnet,
                                       vnet=vnet,
                                       attached_resource="app service plan")
        _validate_vnet_integration_location(cmd=cmd, webapp_location=location,
                                            subnet_resource_group=subnet_info["resource_group_name"],
                                            vnet_name=subnet_info["vnet_name"],
                                            vnet_sub_id=subnet_info["subnet_subscription_id"])
        _vnet_delegation_check(cmd, subnet_subscription_id=subnet_info["subnet_subscription_id"],
                               vnet_resource_group=subnet_info["resource_group_name"],
                               vnet_name=subnet_info["vnet_name"],
                               subnet_name=subnet_info["subnet_name"])
        subnet_resource_id = subnet_info["subnet_resource_id"]
    else:
        subnet_resource_id = None

    return _update_plan_network(cmd, resource_group_name, name, subnet_resource_id, plan_result)


def remove_plan_managed_instance_network(cmd, resource_group_name, name):
    plan_show_cmd = AppServicePlanShow(cli_ctx=cmd.cli_ctx)
    plan_result = plan_show_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    # Explicitly set to empty string to remove network configuration
    return _update_plan_network(cmd, resource_group_name, name, "", plan_result)


def show_plan_identity(cmd, resource_group_name, name):
    plan_show_cmd = AppServicePlanShow(cli_ctx=cmd.cli_ctx)
    plan_result = plan_show_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    return plan_result.get('identity', {})


def _determine_identity_type(system_assigned, user_assigned_identities):
    has_system = system_assigned is not None and system_assigned
    has_user = user_assigned_identities and len(user_assigned_identities) > 0

    if has_system and has_user:
        return "SystemAssigned,UserAssigned"
    if has_system:
        return "SystemAssigned"
    if has_user:
        return "UserAssigned"

    return "None"


def _update_plan_identity(cmd, resource_group_name, name, identity_type, user_assigned_identities, current_plan):
    class IdentityUpdate(AppServicePlanUpdate):
        def pre_instance_update(self, instance):
            instance.properties.storageMounts = None  # need this due to backend bug
            # Construct the appropriate identity object based on the desired identity_type
            if identity_type == "None":
                # Explicitly clear the identity
                instance.identity = {"type": "None"}
            elif identity_type == "SystemAssigned":
                instance.identity = {"type": "SystemAssigned"}
            elif identity_type == "UserAssigned":
                # For user-assigned identity, we need to include the user assigned identities
                user_assigned_dict = {}
                if user_assigned_identities:
                    for identity_id in user_assigned_identities:
                        user_assigned_dict[identity_id] = {}  # Empty object as required by the API
                instance.identity = {
                    "type": "UserAssigned",
                    "userAssignedIdentities": user_assigned_dict
                }
            elif identity_type == "SystemAssigned,UserAssigned":
                # For combined identity, include both system and user assigned
                user_assigned_dict = {}
                if user_assigned_identities:
                    for identity_id in user_assigned_identities:
                        user_assigned_dict[identity_id] = {}  # Empty object as required by the API
                instance.identity = {
                    "type": "SystemAssigned,UserAssigned",
                    "userAssignedIdentities": user_assigned_dict
                }

    identity_update_cmd = IdentityUpdate(cli_ctx=cmd.cli_ctx)
    update_args = {
        'resource_group': resource_group_name,
        'location': current_plan.get('location'),
        'sku': current_plan.get('sku', {}),
        'name': name,
    }

    poller = identity_update_cmd(command_args=update_args)

    # Wait for the operation to complete and get the result
    plan_result = poller.result()

    # Return the updated identity directly from the result
    return plan_result.get('identity', {})


def assign_plan_identity(cmd, resource_group_name, name, system_assigned=None, user_assigned=None):
    # Parse the identities parameter similar to webapp pattern
    if not system_assigned and not user_assigned:
        raise InvalidArgumentValueError("No identities specified. "
                                        "Either --system-assigned or --user-assigned must be specified.")

    # Determine what identities to assign
    system_assigned = bool(system_assigned)
    user_assigned = user_assigned if user_assigned else []

    # Get the current plan to understand existing identity
    plan_show_cmd = AppServicePlanShow(cli_ctx=cmd.cli_ctx)
    plan_result = plan_show_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    current_identity = plan_result.get('identity', {})
    current_type = current_identity.get('type', 'None')
    current_user_assigned = current_identity.get('userAssignedIdentities', {})

    # Determine what the new identity should be
    has_existing_system = current_type and 'SystemAssigned' in current_type
    has_existing_user = current_type and 'UserAssigned' in current_type

    # Merge existing user-assigned identities with new ones
    final_user_assigned = []
    if has_existing_user and current_user_assigned:
        final_user_assigned.extend(list(current_user_assigned.keys()))

    # Add new user-assigned identities (avoid duplicates with case-insensitive comparison)
    for identity in user_assigned:
        if not any(existing.lower() == identity.lower() for existing in final_user_assigned):
            final_user_assigned.append(identity)

    # Determine final system assignment
    final_system_assigned = has_existing_system or system_assigned

    # Determine the correct identity type
    identity_type = _determine_identity_type(final_system_assigned, final_user_assigned)

    return _update_plan_identity(cmd, resource_group_name, name, identity_type, final_user_assigned, plan_result)


def remove_plan_identity(cmd, resource_group_name, name, system_assigned=None, user_assigned=None):
    # Parse the identities parameter similar to webapp pattern
    if not system_assigned and user_assigned is None:
        raise InvalidArgumentValueError("No identities specified. "
                                        "Either --system-assigned or --user-assigned must be specified.")

    # Determine what identities to remove
    remove_system = bool(system_assigned)
    remove_user_assigned = user_assigned if user_assigned else []
    remove_all_user_assigned = user_assigned == []

    if remove_all_user_assigned:
        logger.warning('--user-assigned specified without any resource IDs. '
                       'Removing all user-assigned identities from app service plan.')

    # Get the current plan to understand existing identity
    plan_show_cmd = AppServicePlanShow(cli_ctx=cmd.cli_ctx)
    plan_result = plan_show_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    current_identity = plan_result.get('identity', {})
    current_type = current_identity.get('type', 'None')
    current_user_assigned = current_identity.get('userAssignedIdentities', {})

    # Validate current state
    has_system = current_type and 'SystemAssigned' in current_type
    has_user = current_type and 'UserAssigned' in current_type

    if remove_system and not has_system:
        logger.warning("System-assigned identity is not associated with plan '%s'", name)

    if not has_user and (remove_user_assigned or remove_all_user_assigned):
        logger.warning("No user-assigned identities are associated with plan '%s'", name)

    # Check if user-assigned identities exist
    if remove_user_assigned:
        existing_user_ids = set(id.lower() for id in current_user_assigned.keys()) if current_user_assigned else set()
        remove_user_ids = set(id.lower() for id in remove_user_assigned)
        non_existing = remove_user_ids - existing_user_ids
        if non_existing:
            # Find the original casing for error message
            original_non_existing = []
            for remove_id in remove_user_assigned:
                if remove_id.lower() in non_existing:
                    original_non_existing.append(remove_id)
            logger.warning("User-assigned identities '%s' are not associated with plan '%s'",
                           ', '.join(original_non_existing), name)

    # Calculate what should remain
    final_system_assigned = has_system and not remove_system

    final_user_assigned = []
    if has_user and current_user_assigned and not remove_all_user_assigned:
        # Keep existing user-assigned identities except those being removed (case insensitive comparison)
        remove_user_ids_lower = set(id.lower() for id in remove_user_assigned)
        final_user_assigned = [uid for uid in current_user_assigned.keys() if uid.lower() not in remove_user_ids_lower]

    # Determine the correct identity type
    identity_type = _determine_identity_type(final_system_assigned, final_user_assigned)

    return _update_plan_identity(cmd, resource_group_name, name, identity_type, final_user_assigned, plan_result)


def set_plan_default_identity(cmd, resource_group_name, name, identity=None):
    # Validate that identity is provided
    if not identity:
        raise InvalidArgumentValueError("Identity is required. Use '[system]' for system-assigned identity "
                                        "or provide user-assigned identity resource ID.")

    # Get the current plan
    plan_show_cmd = AppServicePlanShow(cli_ctx=cmd.cli_ctx)
    plan_result = plan_show_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    location = plan_result.get('location')

    # Determine identity type and resource ID
    if identity.lower() == '[system]':
        identity_type = "SystemAssigned"
        user_assigned_identity_resource_id = None
    else:
        identity_type = "UserAssigned"
        user_assigned_identity_resource_id = identity

    # Update the plan with the default identity
    plan_create_cmd = AppServicePlanCreate(cli_ctx=cmd.cli_ctx)
    update_args = {
        'resource_group': resource_group_name,
        'name': name,
        'location': location,
        'sku': plan_result.get('sku', {}),
        'plan_default_identity': {
            'identity_type': identity_type
        }
    }

    # Add user assigned identity resource ID if it's a user-assigned identity
    if user_assigned_identity_resource_id:
        update_args['plan_default_identity']['user_assigned_identity_resource_id'] = user_assigned_identity_resource_id

    poller = plan_create_cmd(command_args=update_args)

    # Wait for the operation to complete and get the result
    plan_result = poller.result()

    # Return the updated plan default identity
    return plan_result.get('planDefaultIdentity', {})


def recycle_plan_managed_instance(cmd, resource_group_name, name, instance_name):
    recycle_cmd = AppServicePlanManagedInstanceRecycle(cli_ctx=cmd.cli_ctx)
    _ = recycle_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name,
        'worker_name': instance_name
    })

    logger.warning("Initiated recycle for instance %s", instance_name)


def connect_to_plan_instance(cmd, resource_group_name, name, instance_name,
                             bastion_name, bastion_resource_group_name=None):
    from azure.cli.core.util import run_az_cmd

    # 1. Default bastion RG to plan RG if not supplied
    if not bastion_resource_group_name:
        bastion_resource_group_name = resource_group_name

    # 2. List instances to locate the target instance and its IP address
    instances_cmd = AppServicePlanManagedInstanceList(cli_ctx=cmd.cli_ctx)
    instances_payload = instances_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    instances = instances_payload.get('instances', []) if isinstance(instances_payload, dict) else []

    # Search for the specified instance using the documented shape {"instanceName": ..., "ipAddress": ...}
    target_instance = None
    for inst in instances:
        inst_instance_name = inst.get('instanceName')
        if inst_instance_name and inst_instance_name.lower() == instance_name.lower():
            target_instance = inst
            break

    if not target_instance:
        raise ResourceNotFoundError(f"Instance '{instance_name}' not found in plan '{name}'.")

    # Resolve IP address field (try a few possible keys)
    target_ip = target_instance.get('ipAddress')
    if not target_ip:
        raise InvalidArgumentValueError("Could not determine target IP address from instance metadata.")

    # 3. Retrieve RDP password after validating instance exists
    password_cmd = AppServicePlanManagedInstanceShowRdpPassword(cli_ctx=cmd.cli_ctx)
    password_response = password_cmd(command_args={
        'resource_group': resource_group_name,
        'name': name
    })

    password_value = password_response.get('rdpPassword')
    if not password_value:
        raise UnclassifiedUserFault("Double check that the app service plan is set with rdp-enabled and try again.")

    logger.warning("Use the following credentials to login:")
    logger.warning("RDP username: Administrator")
    logger.warning("RDP password: [copied to clipboard]")
    _copy_string_to_clipboard(password_value)

    # 4. Invoke the Bastion RDP command
    bastion_cmd = [
        'az', 'network', 'bastion', 'rdp',
        '--name', bastion_name,
        '--resource-group', bastion_resource_group_name,
        '--target-ip-address', target_ip
    ]

    run_az_cmd(bastion_cmd)


def _copy_string_to_clipboard(string_value):
    from azure.cli.core.util import run_cmd
    run_cmd(["cmd.exe", "/c", "echo", "|", "set", "/p={}|".format(string_value), "clip"], check=False)


def show_backup_configuration(cmd, resource_group_name, webapp_name, slot=None):
    try:
        return _generic_site_operation(cmd.cli_ctx, resource_group_name, webapp_name,
                                       'get_backup_configuration', slot)
    except Exception:  # pylint: disable=broad-except
        raise ResourceNotFoundError('Backup configuration not found')


def list_backups(cmd, resource_group_name, webapp_name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, webapp_name, 'list_backups', slot)


def create_backup(cmd, resource_group_name, webapp_name, storage_account_url,
                  db_name=None, db_type=None,
                  db_connection_string=None, backup_name=None, slot=None):
    BackupRequest = cmd.get_models('BackupRequest')
    client = web_client_factory(cmd.cli_ctx)
    if backup_name and backup_name.lower().endswith('.zip'):
        backup_name = backup_name[:-4]
    db_setting = _create_db_setting(cmd, db_name, db_type=db_type, db_connection_string=db_connection_string)
    backup_request = BackupRequest(backup_name=backup_name,
                                   storage_account_url=storage_account_url, databases=db_setting)
    if slot:
        return client.web_apps.backup_slot(resource_group_name=resource_group_name,
                                           name=webapp_name, request=backup_request, slot=slot)
    return client.web_apps.backup(resource_group_name, webapp_name, backup_request)


def update_backup_schedule(cmd, resource_group_name, webapp_name, storage_account_url=None,
                           frequency=None, keep_at_least_one_backup=None,
                           retention_period_in_days=None, db_name=None,
                           db_connection_string=None, db_type=None, backup_name=None, slot=None):
    BackupSchedule, BackupRequest = cmd.get_models('BackupSchedule', 'BackupRequest')
    configuration = None
    if backup_name and backup_name.lower().endswith('.zip'):
        backup_name = backup_name[:-4]
    if not backup_name:
        backup_name = '{0}_{1}'.format(webapp_name, datetime.datetime.utcnow().strftime('%Y%m%d%H%M'))

    try:
        configuration = _generic_site_operation(cmd.cli_ctx, resource_group_name, webapp_name,
                                                'get_backup_configuration', slot)
    except Exception:  # pylint: disable=broad-except
        # No configuration set yet
        if not all([storage_account_url, frequency, retention_period_in_days,
                    keep_at_least_one_backup]):
            raise ResourceNotFoundError('No backup configuration found. A configuration must be created. ' +
                                        'Usage: --container-url URL --frequency TIME --retention DAYS ' +
                                        '--retain-one TRUE/FALSE')

    # If arguments were not specified, use the values in the current backup schedule
    if storage_account_url is None:
        storage_account_url = configuration.storage_account_url

    if retention_period_in_days is None:
        retention_period_in_days = configuration.backup_schedule.retention_period_in_days

    if keep_at_least_one_backup is None:
        keep_at_least_one_backup = configuration.backup_schedule.keep_at_least_one_backup
    else:
        keep_at_least_one_backup = keep_at_least_one_backup.lower() == 'true'

    if frequency:
        # Parse schedule frequency
        frequency_num, frequency_unit = _parse_frequency(cmd, frequency)
    else:
        frequency_num = configuration.backup_schedule.frequency_interval
        frequency_unit = configuration.backup_schedule.frequency_unit

    if configuration and configuration.databases:
        db = configuration.databases[0]
        db_type = db_type or db.database_type
        db_name = db_name or db.name
        db_connection_string = db_connection_string or db.connection_string

    db_setting = _create_db_setting(cmd, db_name, db_type=db_type, db_connection_string=db_connection_string)

    backup_schedule = BackupSchedule(frequency_interval=frequency_num, frequency_unit=frequency_unit,
                                     keep_at_least_one_backup=keep_at_least_one_backup,
                                     retention_period_in_days=retention_period_in_days)
    backup_request = BackupRequest(backup_name=backup_name, backup_schedule=backup_schedule,
                                   enabled=True, storage_account_url=storage_account_url,
                                   databases=db_setting)
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, webapp_name, 'update_backup_configuration',
                                   slot, backup_request)


def restore_backup(cmd, resource_group_name, webapp_name, storage_account_url, backup_name,
                   db_name=None, db_type=None, db_connection_string=None,
                   target_name=None, overwrite=None, ignore_hostname_conflict=None, slot=None):
    RestoreRequest = cmd.get_models('RestoreRequest')
    client = web_client_factory(cmd.cli_ctx)
    storage_blob_name = backup_name
    if not storage_blob_name.lower().endswith('.zip'):
        storage_blob_name += '.zip'
    db_setting = _create_db_setting(cmd, db_name, db_type=db_type, db_connection_string=db_connection_string)
    restore_request = RestoreRequest(storage_account_url=storage_account_url,
                                     blob_name=storage_blob_name, overwrite=overwrite,
                                     site_name=target_name, databases=db_setting,
                                     ignore_conflicting_host_names=ignore_hostname_conflict)
    if slot:
        return client.web_apps.begin_restore_slot(resource_group_name, webapp_name, 0, slot, restore_request)

    return client.web_apps.begin_restore(resource_group_name, webapp_name, 0, restore_request)


def delete_backup(cmd, resource_group_name, webapp_name, backup_id, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        return client.web_apps.delete_backup_slot(resource_group_name, webapp_name, backup_id, slot)
    return client.web_apps.delete_backup(resource_group_name, webapp_name, backup_id)


def list_snapshots(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'list_snapshots',
                                   slot)


def restore_snapshot(cmd, resource_group_name, name, time, slot=None, restore_content_only=False,  # pylint: disable=redefined-outer-name
                     source_resource_group=None, source_name=None, source_slot=None):
    SnapshotRecoverySource, SnapshotRestoreRequest = cmd.get_models('SnapshotRecoverySource', 'SnapshotRestoreRequest')
    client = web_client_factory(cmd.cli_ctx)
    recover_config = not restore_content_only
    if all([source_resource_group, source_name]):
        # Restore from source app to target app
        src_webapp = _generic_site_operation(cmd.cli_ctx, source_resource_group, source_name, 'get', source_slot)

        source = SnapshotRecoverySource(id=src_webapp.id, location=src_webapp.location)
        request = SnapshotRestoreRequest(overwrite=False, snapshot_time=time, recovery_source=source,
                                         recover_configuration=recover_config)
        if slot:
            return client.web_apps.begin_restore_snapshot_slot(resource_group_name, name, slot, request)
        return client.web_apps.begin_restore_snapshot(resource_group_name, name, request)
    if any([source_resource_group, source_name]):
        raise ArgumentUsageError('usage error: --source-resource-group and '
                                 '--source-name must both be specified if one is used')
    # Overwrite app with its own snapshot
    request = SnapshotRestoreRequest(overwrite=True, snapshot_time=time, recover_configuration=recover_config)
    if slot:
        return client.web_apps.begin_restore_snapshot_slot(resource_group_name, name, slot, request)
    return client.web_apps.begin_restore_snapshot(resource_group_name, name, request)


# pylint: disable=inconsistent-return-statements
def _create_db_setting(cmd, db_name, db_type, db_connection_string):
    DatabaseBackupSetting = cmd.get_models('DatabaseBackupSetting')
    if all([db_name, db_type, db_connection_string]):
        return [DatabaseBackupSetting(database_type=db_type, name=db_name, connection_string=db_connection_string)]
    if any([db_name, db_type, db_connection_string]):
        raise ArgumentUsageError('usage error: --db-name NAME --db-type TYPE --db-connection-string STRING')


def _parse_frequency(cmd, frequency):
    FrequencyUnit = cmd.get_models('FrequencyUnit')
    unit_part = frequency.lower()[-1]
    if unit_part == 'd':
        frequency_unit = FrequencyUnit.day
    elif unit_part == 'h':
        frequency_unit = FrequencyUnit.hour
    else:
        raise InvalidArgumentValueError('Frequency must end with d or h for "day" or "hour"')

    try:
        frequency_num = int(frequency[:-1])
    except ValueError:
        raise InvalidArgumentValueError('Frequency must start with a number')

    if frequency_num < 0:
        raise InvalidArgumentValueError('Frequency must be positive')

    return frequency_num, frequency_unit


def _get_deleted_apps_locations(cli_ctx):
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    web_provider = client.providers.get('Microsoft.Web')
    del_sites_resource = next((x for x in web_provider.resource_types if x.resource_type == 'deletedSites'), None)
    if del_sites_resource:
        return del_sites_resource.locations
    return []


def _get_local_git_url(cli_ctx, client, resource_group_name, name, slot=None):
    user = client.get_publishing_user()
    result = _generic_site_operation(cli_ctx, resource_group_name, name, 'get_source_control', slot)
    parsed = urlparse(result.repo_url)
    return '{}://{}@{}/{}.git'.format(parsed.scheme, user.publishing_user_name,
                                      parsed.netloc, name)


def _get_scm_url(cmd, resource_group_name, name, slot=None):
    from azure.mgmt.web.models import HostType
    app = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    for host in app.host_name_ssl_states or []:
        if host.host_type == HostType.repository:
            return "https://{}".format(host.name)

    # this should not happen, but throw anyway
    raise ResourceNotFoundError('Failed to retrieve Scm Uri')


def _get_host_url(cmd, resource_group_name, name):
    from azure.mgmt.web.models import HostType
    app = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get')
    for host in app.host_name_ssl_states or []:
        if host.host_type == HostType.standard:
            return "https://{}".format(host.name)

    # this should not happen, but throw anyway
    raise ResourceNotFoundError('Failed to retrieve Host Uri')


def get_publishing_user(cmd):
    client = web_client_factory(cmd.cli_ctx)
    return client.get_publishing_user()


def set_deployment_user(cmd, user_name, password=None):
    '''
    Update deployment credentials.(Note, all webapps in your subscription will be impacted)
    '''
    User = cmd.get_models('User')
    client = web_client_factory(cmd.cli_ctx)
    user = User(publishing_user_name=user_name)
    if password is None:
        try:
            password = prompt_pass(msg='Password: ', confirm=True)
        except NoTTYException:
            raise ArgumentUsageError('Please specify both username and password in non-interactive mode.')

    user.publishing_password = password
    return client.update_publishing_user(user)


def list_publishing_credentials(cmd, resource_group_name, name, slot=None):
    content = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                      'begin_list_publishing_credentials', slot)
    return content.result()


def list_publish_profiles(cmd, resource_group_name, name, slot=None, xml=False):
    import xmltodict
    content = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                      'list_publishing_profile_xml_with_secrets', slot, {"format": "WebDeploy"})
    full_xml = ''
    for f in content:
        full_xml += f.decode()

    if not xml:
        profiles = xmltodict.parse(full_xml, xml_attribs=True)['publishData']['publishProfile']
        converted = []

        if not isinstance(profiles, list):
            profiles = [profiles]

        for profile in profiles:
            new = {}
            for key in profile:
                # strip the leading '@' xmltodict put in for attributes
                new[key.lstrip('@')] = profile[key]
            converted.append(new)
        return converted

    cmd.cli_ctx.invocation.data['output'] = 'tsv'
    return full_xml


def enable_cd(cmd, resource_group_name, name, enable, slot=None):
    settings = []
    settings.append("DOCKER_ENABLE_CI=" + enable)

    update_app_settings(cmd, resource_group_name, name, settings, slot)

    return show_container_cd_url(cmd, resource_group_name, name, slot)


def show_container_cd_url(cmd, resource_group_name, name, slot=None):
    settings = get_app_settings(cmd, resource_group_name, name, slot)
    docker_enabled = False
    for setting in settings:
        if setting['name'] == 'DOCKER_ENABLE_CI' and setting['value'] == 'true':
            docker_enabled = True
            break

    cd_settings = {}
    cd_settings['DOCKER_ENABLE_CI'] = docker_enabled

    if docker_enabled:
        credentials = list_publishing_credentials(cmd, resource_group_name, name, slot)
        if credentials:
            cd_url = credentials.scm_uri + '/docker/hook'
            cd_settings['CI_CD_URL'] = cd_url
    else:
        cd_settings['CI_CD_URL'] = ''

    return cd_settings


def view_in_browser(cmd, resource_group_name, name, slot=None, logs=False):
    url = _get_url(cmd, resource_group_name, name, slot)
    open_page_in_browser(url)
    if logs:
        get_streaming_log(cmd, resource_group_name, name, provider=None, slot=slot)


def _get_url(cmd, resource_group_name, name, slot=None):
    SslState = cmd.get_models('SslState')
    site = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    if not site:
        raise ResourceNotFoundError("'{}' app doesn't exist".format(name))
    url = site.enabled_host_names[0]  # picks the custom domain URL incase a domain is assigned
    ssl_host = next((h for h in site.host_name_ssl_states
                     if h.ssl_state != SslState.disabled), None)
    return ('https' if ssl_host else 'http') + '://' + url


# TODO: expose new blob support
def config_diagnostics(cmd, resource_group_name, name, level=None,
                       application_logging=None, web_server_logging=None,
                       docker_container_logging=None, detailed_error_messages=None,
                       failed_request_tracing=None, slot=None):
    from azure.mgmt.web.models import (FileSystemApplicationLogsConfig, ApplicationLogsConfig,
                                       AzureBlobStorageApplicationLogsConfig, SiteLogsConfig,
                                       HttpLogsConfig, FileSystemHttpLogsConfig,
                                       EnabledConfig)
    client = web_client_factory(cmd.cli_ctx)
    # TODO: ensure we call get_site only once
    site = client.web_apps.get(resource_group_name, name)
    if not site:
        raise ResourceNotFoundError("'{}' app doesn't exist".format(name))

    application_logs = None
    if application_logging:
        fs_log = None
        blob_log = None
        level = level if application_logging != 'off' else False
        level = True if level is None else level
        if application_logging in ['filesystem', 'off']:
            fs_log = FileSystemApplicationLogsConfig(level=level)
        if application_logging in ['azureblobstorage', 'off']:
            blob_log = AzureBlobStorageApplicationLogsConfig(level=level, retention_in_days=3,
                                                             sas_url=None)
        application_logs = ApplicationLogsConfig(file_system=fs_log,
                                                 azure_blob_storage=blob_log)

    http_logs = None
    server_logging_option = web_server_logging or docker_container_logging
    if server_logging_option:
        # TODO: az blob storage log config currently not in use, will be impelemented later.
        # Tracked as Issue: #4764 on Github
        filesystem_log_config = None
        turned_on = server_logging_option != 'off'
        if server_logging_option in ['filesystem', 'off']:
            # 100 mb max log size, retention lasts 3 days. Yes we hard code it, portal does too
            filesystem_log_config = FileSystemHttpLogsConfig(retention_in_mb=100, retention_in_days=3,
                                                             enabled=turned_on)
        http_logs = HttpLogsConfig(file_system=filesystem_log_config, azure_blob_storage=None)

    detailed_error_messages_logs = (None if detailed_error_messages is None
                                    else EnabledConfig(enabled=detailed_error_messages))
    failed_request_tracing_logs = (None if failed_request_tracing is None
                                   else EnabledConfig(enabled=failed_request_tracing))
    site_log_config = SiteLogsConfig(application_logs=application_logs,
                                     http_logs=http_logs,
                                     failed_requests_tracing=failed_request_tracing_logs,
                                     detailed_error_messages=detailed_error_messages_logs)

    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'update_diagnostic_logs_config',
                                   slot, site_log_config)


def show_diagnostic_settings(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get_diagnostic_logs_configuration', slot)


def show_deployment_log(cmd, resource_group, name, slot=None, deployment_id=None):
    import requests
    scm_url = _get_scm_url(cmd, resource_group, name, slot)
    headers = get_scm_site_headers(cmd.cli_ctx, name, resource_group, slot)

    deployment_log_url = ''
    if deployment_id:
        deployment_log_url = '{}/api/deployments/{}/log'.format(scm_url, deployment_id)
    else:
        deployments_url = '{}/api/deployments/'.format(scm_url)
        response = requests.get(deployments_url, headers=headers)

        if response.status_code != 200:
            raise CLIError("Failed to connect to '{}' with status code '{}' and reason '{}'".format(
                deployments_url, response.status_code, response.reason))

        sorted_logs = sorted(
            response.json(),
            key=lambda x: x['start_time'],
            reverse=True
        )
        if sorted_logs and sorted_logs[0]:
            deployment_log_url = sorted_logs[0].get('log_url', '')

    if deployment_log_url:
        response = requests.get(deployment_log_url, headers=headers)
        if response.status_code != 200:
            raise CLIError("Failed to connect to '{}' with status code '{}' and reason '{}'".format(
                deployment_log_url, response.status_code, response.reason))
        return response.json()
    return []


def list_deployment_logs(cmd, resource_group, name, slot=None):
    import requests

    scm_url = _get_scm_url(cmd, resource_group, name, slot)
    headers = get_scm_site_headers(cmd.cli_ctx, name, resource_group, slot)
    deployment_log_url = '{}/api/deployments/'.format(scm_url)

    response = requests.get(deployment_log_url, headers=headers)

    if response.status_code != 200:
        raise CLIError("Failed to connect to '{}' with status code '{}' and reason '{}'".format(
            scm_url, response.status_code, response.reason))

    return response.json() or []


def config_slot_auto_swap(cmd, resource_group_name, webapp, slot, auto_swap_slot=None, disable=None):
    client = web_client_factory(cmd.cli_ctx)
    site_config = client.web_apps.get_configuration_slot(resource_group_name, webapp, slot)
    site_config.auto_swap_slot_name = '' if disable else (auto_swap_slot or 'production')
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, webapp, 'update_configuration', slot, site_config)


def list_slots(cmd, resource_group_name, webapp):
    client = web_client_factory(cmd.cli_ctx)
    slots = list(client.web_apps.list_slots(resource_group_name, webapp))
    for slot in slots:
        slot.name = slot.name.split('/')[-1]
        setattr(slot, 'app_service_plan', parse_resource_id(slot.server_farm_id)['name'])
        del slot.server_farm_id
    return slots


def swap_slot(cmd, resource_group_name, webapp, slot, target_slot=None, preserve_vnet=None, action='swap'):
    client = web_client_factory(cmd.cli_ctx)
    # Default isPreserveVnet to 'True' if preserve_vnet is 'None'
    isPreserveVnet = preserve_vnet if preserve_vnet is not None else 'true'
    # converstion from string to Boolean
    isPreserveVnet = bool(isPreserveVnet == 'true')
    CsmSlotEntity = cmd.get_models('CsmSlotEntity')
    slot_swap_entity = CsmSlotEntity(target_slot=target_slot or 'production', preserve_vnet=isPreserveVnet)
    if action == 'swap':
        poller = client.web_apps.begin_swap_slot(resource_group_name, webapp, slot, slot_swap_entity)
        return poller
    if action == 'preview':
        if slot is None:
            result = client.web_apps.apply_slot_config_to_production(resource_group_name, webapp, slot_swap_entity)
        else:
            result = client.web_apps.apply_slot_configuration_slot(resource_group_name, webapp, slot, slot_swap_entity)
        return result
    # we will reset both source slot and target slot
    if target_slot is None:
        client.web_apps.reset_production_slot_config(resource_group_name, webapp)
    else:
        client.web_apps.reset_slot_configuration_slot(resource_group_name, webapp, target_slot)
    return None


def delete_slot(cmd, resource_group_name, webapp, slot):
    client = web_client_factory(cmd.cli_ctx)
    # TODO: once swagger finalized, expose other parameters like: delete_all_slots, etc...
    client.web_apps.delete_slot(resource_group_name, webapp, slot)


def set_traffic_routing(cmd, resource_group_name, name, distribution):
    RampUpRule = cmd.get_models('RampUpRule')
    client = web_client_factory(cmd.cli_ctx)
    site = client.web_apps.get(resource_group_name, name)
    if not site:
        raise ResourceNotFoundError("'{}' app doesn't exist".format(name))
    configs = get_site_configs(cmd, resource_group_name, name)
    host_name_split = site.default_host_name.split('.', 1)
    host_name_suffix = '.' + host_name_split[1]
    host_name_val = host_name_split[0]
    configs.experiments.ramp_up_rules = []
    for r in distribution:
        slot, percentage = r.split('=')
        host_name_val = host_name_val[:40] if len(host_name_val) > 40 else host_name_val
        action_host_name_slot = host_name_val + "-" + slot
        configs.experiments.ramp_up_rules.append(RampUpRule(action_host_name=action_host_name_slot + host_name_suffix,
                                                            reroute_percentage=float(percentage),
                                                            name=slot))
    _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'update_configuration', None, configs)

    return configs.experiments.ramp_up_rules


def show_traffic_routing(cmd, resource_group_name, name):
    configs = get_site_configs(cmd, resource_group_name, name)
    return configs.experiments.ramp_up_rules


def clear_traffic_routing(cmd, resource_group_name, name):
    set_traffic_routing(cmd, resource_group_name, name, [])


def enable_credentials(cmd, resource_group_name, name, enable, slot=None):
    from azure.mgmt.web.models import CorsSettings
    configs = get_site_configs(cmd, resource_group_name, name, slot)
    if not configs.cors:
        configs.cors = CorsSettings()
    configs.cors.support_credentials = enable
    result = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'update_configuration', slot, configs)
    return result.cors


def add_cors(cmd, resource_group_name, name, allowed_origins, slot=None):
    from azure.mgmt.web.models import CorsSettings
    configs = get_site_configs(cmd, resource_group_name, name, slot)
    if not configs.cors:
        configs.cors = CorsSettings()
    configs.cors.allowed_origins = (configs.cors.allowed_origins or []) + allowed_origins
    result = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'update_configuration', slot, configs)
    return result.cors


def remove_cors(cmd, resource_group_name, name, allowed_origins, slot=None):
    configs = get_site_configs(cmd, resource_group_name, name, slot)
    if configs.cors:
        if allowed_origins:
            configs.cors.allowed_origins = [x for x in (configs.cors.allowed_origins or []) if x not in allowed_origins]
        else:
            configs.cors.allowed_origins = []
        configs = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'update_configuration', slot, configs)
    return configs.cors


def show_cors(cmd, resource_group_name, name, slot=None):
    configs = get_site_configs(cmd, resource_group_name, name, slot)
    return configs.cors


def get_streaming_log(cmd, resource_group_name, name, provider=None, slot=None):
    # ping the site first to ensure that the site container is running
    # logsteam does not work if the site container is not running
    # See https://github.com/Azure/azure-cli/issues/23058
    ping_site(cmd, resource_group_name, name, slot)
    scm_url = _get_scm_url(cmd, resource_group_name, name, slot)
    streaming_url = scm_url + '/logstream'
    if provider:
        streaming_url += ('/' + provider.lstrip('/'))

    headers = get_scm_site_headers(cmd.cli_ctx, name, resource_group_name, slot)
    t = threading.Thread(target=_get_log, args=(streaming_url, headers))
    t.daemon = True
    t.start()

    while True:
        time.sleep(100)  # so that ctrl+c can stop the command


def ping_site(cmd, resource_group_name, name, slot, timeout=230):
    import urllib3
    try:
        site_url = _get_url(cmd, resource_group_name, name, slot)
        http = urllib3.PoolManager(timeout=urllib3.Timeout(connect=timeout, read=timeout))
        http.request('GET', site_url)
    except Exception:  # pylint: disable=broad-except
        logger.warning("Unable to reach the app.")
        raise


def download_historical_logs(cmd, resource_group_name, name, log_file=None, slot=None):
    scm_url = _get_scm_url(cmd, resource_group_name, name, slot)
    url = scm_url.rstrip('/') + '/dump'
    headers = get_scm_site_headers(cmd.cli_ctx, name, resource_group_name, slot)
    _get_log(url, headers, log_file)
    logger.warning('Downloaded logs to %s', log_file)


def _get_site_credential(cli_ctx, resource_group_name, name, slot=None):
    creds = _generic_site_operation(cli_ctx, resource_group_name, name, 'begin_list_publishing_credentials', slot)
    creds = creds.result()
    return (creds.publishing_user_name, creds.publishing_password)


def get_bearer_token(cli_ctx):
    from azure.cli.core._profile import Profile
    from azure.cli.core.auth.util import resource_to_scopes
    profile = Profile(cli_ctx=cli_ctx)
    credential, _, _ = profile.get_login_credentials()
    scopes = resource_to_scopes(cli_ctx.cloud.endpoints.app_service_resource_id)
    bearer_token = credential.get_token(*scopes).token
    return bearer_token


def basic_auth_supported(cli_ctx, name, resource_group_name, slot=None):
    return _generic_site_operation(cli_ctx, resource_group_name, name, 'get_scm_allowed', slot).allow


# auth with basic auth if available
def get_scm_site_headers(cli_ctx, name, resource_group_name, slot=None, additional_headers=None):
    import urllib3

    is_flex = is_flex_functionapp(cli_ctx, resource_group_name, name)

    if not is_flex and basic_auth_supported(cli_ctx, name, resource_group_name, slot):
        logger.info("[AUTH]: basic")
        username, password = _get_site_credential(cli_ctx, resource_group_name, name, slot)
        headers = urllib3.util.make_headers(basic_auth=f"{username}:{password}")
    else:
        logger.info("[AUTH]: AAD")
        headers = urllib3.util.make_headers()
        headers["Authorization"] = f"Bearer {get_bearer_token(cli_ctx)}"
    headers['User-Agent'] = get_az_user_agent()
    headers['x-ms-client-request-id'] = cli_ctx.data['headers']['x-ms-client-request-id']
    # allow setting Content-Type, Cache-Control, etc. headers
    if additional_headers:
        for k, v in additional_headers.items():
            headers[k] = v

    return headers


def get_scm_site_headers_flex(cli_ctx, additional_headers=None):
    import urllib3

    logger.info("[AUTH]: AAD")
    headers = urllib3.util.make_headers()
    headers["Authorization"] = f"Bearer {get_bearer_token(cli_ctx)}"
    headers['User-Agent'] = get_az_user_agent()
    headers['x-ms-client-request-id'] = cli_ctx.data['headers']['x-ms-client-request-id']
    # allow setting Content-Type, Cache-Control, etc. headers
    if additional_headers:
        for k, v in additional_headers.items():
            headers[k] = v

    return headers


def _get_log(url, headers, log_file=None):
    http = get_pool_manager(url)
    r = http.request(
        'GET',
        url,
        headers=headers,
        preload_content=False
    )
    if r.status != 200:
        raise CLIError("Failed to connect to '{}' with status code '{}' and reason '{}'".format(
            url, r.status, r.reason))
    if log_file:  # download logs
        with open(log_file, 'wb') as f:
            while True:
                data = r.read(1024)
                if not data:
                    break
                f.write(data)
    else:  # streaming
        std_encoding = sys.stdout.encoding
        try:
            for chunk in r.stream():
                if chunk:
                    # Extra encode() and decode for stdout which does not support 'utf-8'
                    logger.warning(chunk.decode(encoding='utf-8', errors='replace')
                                   .encode(std_encoding, errors='replace')
                                   .decode(std_encoding, errors='replace')
                                   .rstrip('\n\r'))  # each line of log has CRLF.
        except Exception as ex:  # pylint: disable=broad-except
            logger.error("Log stream interrupted. Exiting live log stream.")
            logger.debug(ex)
        finally:
            r.release_conn()


def upload_ssl_cert(cmd, resource_group_name,
                    name, certificate_password,
                    certificate_file, slot=None,
                    certificate_name=None):
    Certificate = cmd.get_models('Certificate')
    client = web_client_factory(cmd.cli_ctx)
    webapp = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    cert_file = open(certificate_file, 'rb')
    cert_contents = cert_file.read()
    hosting_environment_profile_param = (webapp.hosting_environment_profile.name
                                         if webapp.hosting_environment_profile else '')

    try:
        thumb_print = _get_cert(certificate_password, certificate_file)
    except Exception as e:
        raise UnclassifiedUserFault(f"Failed to get the certificate's thumbprint with error: '{e}'. "
                                    "Please double check the certificate password.") from e
    if certificate_name:
        cert_name = certificate_name
    else:
        cert_name = _generate_cert_name(thumb_print, hosting_environment_profile_param,
                                        webapp.location, resource_group_name)
    cert = Certificate(password=certificate_password, pfx_blob=cert_contents,
                       location=webapp.location, server_farm_id=webapp.server_farm_id)
    return client.certificates.create_or_update(resource_group_name, cert_name, cert)


def _generate_cert_name(thumb_print, hosting_environment, location, resource_group_name):
    return "%s_%s_%s_%s" % (thumb_print, hosting_environment, location, resource_group_name)


def _get_cert(certificate_password, certificate_file):
    ''' Decrypts the .pfx file '''
    cert_password_bytes = certificate_password.encode('utf-8') if certificate_password else None
    with open(certificate_file, 'rb') as f:
        p12 = pkcs12.load_pkcs12(f.read(), cert_password_bytes)
    cert = p12.cert.certificate
    thumbprint = cert.fingerprint(hashes.SHA1()).hex().upper()
    return thumbprint


def list_ssl_certs(cmd, resource_group_name):
    client = web_client_factory(cmd.cli_ctx)
    return client.certificates.list_by_resource_group(resource_group_name)


def show_ssl_cert(cmd, resource_group_name, certificate_name):
    client = web_client_factory(cmd.cli_ctx)
    return client.certificates.get(resource_group_name, certificate_name)


def delete_ssl_cert(cmd, resource_group_name, certificate_thumbprint):
    client = web_client_factory(cmd.cli_ctx)
    webapp_certs = client.certificates.list_by_resource_group(resource_group_name)
    for webapp_cert in webapp_certs:
        if webapp_cert.thumbprint == certificate_thumbprint:
            return client.certificates.delete(resource_group_name, webapp_cert.name)
    raise ResourceNotFoundError("Certificate for thumbprint '{}' not found".format(certificate_thumbprint))


def import_ssl_cert(cmd, resource_group_name, key_vault, key_vault_certificate_name, name=None, certificate_name=None):
    Certificate = cmd.get_models('Certificate')
    client = web_client_factory(cmd.cli_ctx)

    # Webapp name is not required for this command, but the location of the webspace is required since the certificate
    # is associated with the webspace, not the app. All apps and plans in the same webspace will share the same
    # certificates. If the app is not provided, the location of the resource group is used.
    if name:
        webapp = client.web_apps.get(resource_group_name, name)
        if not webapp:
            raise ResourceNotFoundError("'{}' app doesn't exist in resource group {}".format(name, resource_group_name))
        location = webapp.location
    else:
        rg_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
        location = rg_client.resource_groups.get(resource_group_name).location

    kv_id = None
    if not is_valid_resource_id(key_vault):
        kv_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_KEYVAULT)
        key_vaults = kv_client.vaults.list_by_subscription()
        for kv in key_vaults:
            if key_vault == kv.name:
                kv_id = kv.id
                break
    else:
        kv_id = key_vault

    if kv_id is None:
        kv_msg = 'The Key Vault {0} was not found in the subscription in context. ' \
                 'If your Key Vault is in a different subscription, please specify the full Resource ID: ' \
                 '\naz .. ssl import -g {1} --key-vault-certificate-name {2} ' \
                 '--key-vault /subscriptions/[sub id]/resourceGroups/[rg]/providers/Microsoft.KeyVault/' \
                 'vaults/{0}'.format(key_vault, resource_group_name, key_vault_certificate_name)
        logger.warning(kv_msg)
        return

    kv_id_parts = parse_resource_id(kv_id)
    kv_name = kv_id_parts['name']
    kv_resource_group_name = kv_id_parts['resource_group']
    kv_subscription = kv_id_parts['subscription']

    # If in the public cloud, check if certificate is an app service certificate, in the same or a diferent
    # subscription
    kv_secret_name = None
    cloud_type = cmd.cli_ctx.cloud.name
    from azure.cli.core.commands.client_factory import get_subscription_id
    subscription_id = get_subscription_id(cmd.cli_ctx)
    if cloud_type.lower() == PUBLIC_CLOUD.lower():
        if kv_subscription.lower() != subscription_id.lower():
            diff_subscription_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_APPSERVICE,
                                                               subscription_id=kv_subscription)
            ascs = diff_subscription_client.app_service_certificate_orders.list(api_version=VERSION_2022_09_01)
        else:
            ascs = client.app_service_certificate_orders.list(api_version=VERSION_2022_09_01)

        kv_secret_name = None
        for asc in ascs:
            if asc.name == key_vault_certificate_name:
                kv_secret_name = asc.certificates[key_vault_certificate_name].key_vault_secret_name

    # if kv_secret_name is not populated, it is not an appservice certificate, proceed for KV certificates
    if not kv_secret_name:
        kv_secret_name = key_vault_certificate_name

    if certificate_name:
        cert_name = certificate_name
    else:
        cert_name = '{}-{}-{}'.format(resource_group_name, kv_name, key_vault_certificate_name)

    lnk = 'https://azure.github.io/AppService/2016/05/24/Deploying-Azure-Web-App-Certificate-through-Key-Vault.html'
    lnk_msg = 'Find more details here: {}'.format(lnk)
    if not _check_service_principal_permissions(cmd, kv_resource_group_name, kv_name, kv_subscription):
        logger.warning('Unable to verify Key Vault permissions.')
        logger.warning('You may need to grant Microsoft.Azure.WebSites service principal the Secret:Get permission')
        logger.warning(lnk_msg)

    kv_cert_def = Certificate(location=location, key_vault_id=kv_id, password='',
                              key_vault_secret_name=kv_secret_name)

    return client.certificates.create_or_update(name=cert_name, resource_group_name=resource_group_name,
                                                certificate_envelope=kv_cert_def)


def create_managed_ssl_cert(cmd, resource_group_name, name, hostname, slot=None, certificate_name=None):
    Certificate = cmd.get_models('Certificate')
    hostname = hostname.lower()
    client = web_client_factory(cmd.cli_ctx)
    webapp = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    if not webapp:
        slot_text = "Deployment slot {} in ".format(slot) if slot else ''
        raise ResourceNotFoundError("{0}app {1} doesn't exist in resource group {2}".format(slot_text,
                                                                                            name,
                                                                                            resource_group_name))

    parsed_plan_id = parse_resource_id(webapp.server_farm_id)
    plan_info = client.app_service_plans.get(parsed_plan_id['resource_group'], parsed_plan_id['name'])
    if plan_info.sku.tier.upper() == 'FREE' or plan_info.sku.tier.upper() == 'SHARED':
        raise ValidationError('Managed Certificate is not supported on Free and Shared tier.')

    if not _verify_hostname_binding(cmd, resource_group_name, name, hostname, slot):
        slot_text = " --slot {}".format(slot) if slot else ""
        raise ValidationError("Hostname (custom domain) '{0}' is not registered with {1}. "
                              "Use 'az webapp config hostname add --resource-group {2} "
                              "--webapp-name {1}{3} --hostname {0}' "
                              "to register the hostname.".format(hostname, name, resource_group_name, slot_text))

    server_farm_id = webapp.server_farm_id
    location = webapp.location
    easy_cert_def = Certificate(location=location, canonical_name=hostname,
                                server_farm_id=server_farm_id, password='')

    # TODO: Update manual polling to use LongRunningOperation once backend API & new SDK supports polling
    try:
        certificate_name = hostname if not certificate_name else certificate_name
        return client.certificates.create_or_update(name=certificate_name, resource_group_name=resource_group_name,
                                                    certificate_envelope=easy_cert_def)
    except Exception as ex:
        poll_url = ex.response.headers['Location'] if 'Location' in ex.response.headers else None
        if ex.response.status_code == 202 and poll_url:
            r = send_raw_request(cmd.cli_ctx, method='get', url=poll_url)
            poll_timeout = time.time() + 60 * 2  # 2 minute timeout

            while r.status_code != 200 and time.time() < poll_timeout:
                time.sleep(5)
                r = send_raw_request(cmd.cli_ctx, method='get', url=poll_url)

            if r.status_code == 200:
                try:
                    return r.json()
                except ValueError:
                    return r.text
            logger.warning("Managed Certificate creation in progress. Please use the command "
                           "'az webapp config ssl show -g %s --certificate-name %s' "
                           " to view your certificate once it is created", resource_group_name, certificate_name)
            return
        raise CLIError(ex)


def _check_service_principal_permissions(cmd, resource_group_name, key_vault_name, key_vault_subscription):
    from azure.cli.command_modules.role import graph_client_factory, GraphError
    graph_client = graph_client_factory(cmd.cli_ctx)
    from azure.cli.core.commands.client_factory import get_subscription_id
    subscription = get_subscription_id(cmd.cli_ctx)
    # Cannot check if key vault is in another subscription
    if subscription != key_vault_subscription:
        return False
    kv_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_KEYVAULT)
    vault = kv_client.vaults.get(resource_group_name=resource_group_name, vault_name=key_vault_name)
    # Check for Microsoft.Azure.WebSites app registration
    AZURE_PUBLIC_WEBSITES_APP_ID = 'abfa0a7c-a6b6-4736-8310-5855508787cd'
    AZURE_GOV_WEBSITES_APP_ID = '6a02c803-dafd-4136-b4c3-5a6f318b4714'
    for policy in vault.properties.access_policies:
        try:
            sp = graph_client.service_principal_get(policy.object_id)
            if sp['appId'] == AZURE_PUBLIC_WEBSITES_APP_ID or sp['appId'] == AZURE_GOV_WEBSITES_APP_ID:
                for perm in policy.permissions.secrets:
                    if perm == "Get":
                        return True
        except GraphError:
            pass  # Lookup will fail for non service principals (users, groups, etc.)
    return False


def _update_host_name_ssl_state(cmd, resource_group_name, webapp_name, webapp,
                                host_name, ssl_state, thumbprint, slot=None):
    Site, HostNameSslState = cmd.get_models('Site', 'HostNameSslState')
    updated_webapp = Site(host_name_ssl_states=[HostNameSslState(name=host_name,
                                                                 ssl_state=ssl_state,
                                                                 thumbprint=thumbprint,
                                                                 to_update=True)],
                          location=webapp.location, tags=webapp.tags)
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, webapp_name, 'begin_create_or_update',
                                   slot, updated_webapp)


def _update_ssl_binding(cmd, resource_group_name, name, certificate_thumbprint, ssl_type, hostname, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    webapp = client.web_apps.get(resource_group_name, name)
    if not webapp:
        raise ResourceNotFoundError("'{}' app doesn't exist".format(name))

    cert_resource_group_name = parse_resource_id(webapp.server_farm_id)['resource_group']
    webapp_certs = client.certificates.list_by_resource_group(cert_resource_group_name)

    found_cert = None
    # search for a cert that matches in the app service plan's RG
    for webapp_cert in webapp_certs:
        if webapp_cert.thumbprint == certificate_thumbprint:
            found_cert = webapp_cert
    # search for a cert that matches in the webapp's RG
    if not found_cert:
        webapp_certs = client.certificates.list_by_resource_group(resource_group_name)
        for webapp_cert in webapp_certs:
            if webapp_cert.thumbprint == certificate_thumbprint:
                found_cert = webapp_cert
    # search for a cert that matches in the subscription, filtering on the serverfarm
    if not found_cert:
        sub_certs = client.certificates.list(filter=f"ServerFarmId eq '{webapp.server_farm_id}'")
        found_cert = next(iter([c for c in sub_certs if c.thumbprint == certificate_thumbprint]), None)
    if found_cert:
        if not hostname:
            if len(found_cert.host_names) == 1 and not found_cert.host_names[0].startswith('*'):
                return _update_host_name_ssl_state(cmd, resource_group_name, name, webapp,
                                                   found_cert.host_names[0], ssl_type,
                                                   certificate_thumbprint, slot)
            query_result = list_hostnames(cmd, resource_group_name, name, slot)
            hostnames_in_webapp = [x.name.split('/')[-1] for x in query_result]
            to_update = _match_host_names_from_cert(found_cert.host_names, hostnames_in_webapp)
        else:
            to_update = [hostname]
        for h in to_update:
            _update_host_name_ssl_state(cmd, resource_group_name, name, webapp,
                                        h, ssl_type, certificate_thumbprint, slot)

        return show_app(cmd, resource_group_name, name, slot)

    raise ResourceNotFoundError("Certificate for thumbprint '{}' not found.".format(certificate_thumbprint))


def bind_ssl_cert(cmd, resource_group_name, name, certificate_thumbprint, ssl_type, hostname=None, slot=None):
    SslState = cmd.get_models('SslState')
    return _update_ssl_binding(cmd, resource_group_name, name, certificate_thumbprint,
                               SslState.sni_enabled if ssl_type == 'SNI' else SslState.ip_based_enabled, hostname, slot)


def unbind_ssl_cert(cmd, resource_group_name, name, certificate_thumbprint, hostname=None, slot=None):
    SslState = cmd.get_models('SslState')
    return _update_ssl_binding(cmd, resource_group_name, name,
                               certificate_thumbprint, SslState.disabled, hostname, slot)


def _match_host_names_from_cert(hostnames_from_cert, hostnames_in_webapp):
    # the goal is to match '*.foo.com' with host name like 'admin.foo.com', 'logs.foo.com', etc
    matched = set()
    for hostname in hostnames_from_cert:
        if hostname.startswith('*'):
            for h in hostnames_in_webapp:
                if hostname[hostname.find('.'):] == h[h.find('.'):]:
                    matched.add(h)
        elif hostname in hostnames_in_webapp:
            matched.add(hostname)
    return matched


# help class handles runtime stack in format like 'node|6.1', 'php|5.5'
# pylint: disable=too-few-public-methods
class _AbstractStackRuntimeHelper:
    def __init__(self, cmd, linux=False, windows=False):
        self._cmd = cmd
        self._client = web_client_factory(cmd.cli_ctx)
        self._linux = linux
        self._windows = windows
        self._stacks = []

    @property
    def stacks(self):
        self._load_stacks()
        return self._stacks

    def _get_raw_stacks_from_api(self):
        raise NotImplementedError

    # updates self._stacks
    def _parse_raw_stacks(self, stacks):
        raise NotImplementedError

    def _load_stacks(self):
        if self._stacks:
            return
        stacks = self._get_raw_stacks_from_api()
        self._parse_raw_stacks(stacks)


# WebApps stack class
class _StackRuntimeHelper(_AbstractStackRuntimeHelper):
    DEFAULT_DELIMETER = "|"  # character that separates runtime name from version
    ALLOWED_DELIMETERS = "|:"  # delimiters allowed: '|', ':'

    # pylint: disable=too-few-public-methods
    class Runtime:
        def __init__(self,
                     display_name=None,
                     configs=None,
                     github_actions_properties=None,
                     linux=False,
                     is_auto_update=None):
            self.display_name = display_name
            self.configs = configs if configs is not None else {}
            self.github_actions_properties = github_actions_properties
            self.linux = linux
            self.is_auto_update = is_auto_update

    def __init__(self, cmd, linux=False, windows=False):
        # TODO try and get API support for this so it isn't hardcoded
        self.windows_config_mappings = {
            'node': 'WEBSITE_NODE_DEFAULT_VERSION',
            'python': 'python_version',
            'php': 'php_version',
            'aspnet': 'net_framework_version',
            'dotnet': 'net_framework_version',
            'dotnetcore': None
        }
        super().__init__(cmd, linux=linux, windows=windows)

    def get_stack_names_only(self, delimiter=None, show_runtime_details=False):
        windows_stacks = [s.display_name for s in self.stacks if not s.linux and not s.is_auto_update]
        linux_stacks = [s.display_name for s in self.stacks if s.linux and not s.is_auto_update]
        windows_auto_updates = [
            s.display_name for s in self.stacks if not
            s.linux and ('java' not in s.display_name.casefold() or s.is_auto_update)]
        linux_auto_updates = [
            s.display_name for s in self.stacks if
            s.linux and ('java' not in s.display_name.casefold() or s.is_auto_update)]

        def is_valid_runtime_name(name):
            # Accepts names like "node|18-lts", "python|3.11", but not "NODE:lts" or "node"
            parts = name.split(self.DEFAULT_DELIMETER)
            return len(parts) == 2 and parts[1] and not parts[1].lower() in ("lts", "default", "stable")

        windows_stacks = [n for n in windows_stacks if is_valid_runtime_name(n)]
        linux_stacks = [n for n in linux_stacks if is_valid_runtime_name(n)]
        windows_auto_updates = [n for n in windows_auto_updates if is_valid_runtime_name(n)]
        linux_auto_updates = [n for n in linux_auto_updates if is_valid_runtime_name(n)]

        if delimiter is not None:
            windows_stacks = [n.replace(self.DEFAULT_DELIMETER, delimiter) for n in windows_stacks]
            linux_stacks = [n.replace(self.DEFAULT_DELIMETER, delimiter) for n in linux_stacks]
            windows_auto_updates = [n.replace(self.DEFAULT_DELIMETER, delimiter) for n in windows_auto_updates]
            linux_auto_updates = [n.replace(self.DEFAULT_DELIMETER, delimiter) for n in linux_auto_updates]
        if not show_runtime_details:
            linux_stacks = linux_auto_updates
            windows_stacks = windows_auto_updates
        if self._linux and not self._windows:
            return linux_stacks
        if self._windows and not self._linux:
            return windows_stacks
        return {LINUX_OS_NAME: linux_stacks, WINDOWS_OS_NAME: windows_stacks}

    def _get_raw_stacks_from_api(self):
        return list(self._client.provider.get_web_app_stacks(stack_os_type=None))

    def _parse_raw_stacks(self, stacks):
        for lang in stacks:
            for major_version in lang.major_versions:
                if self._linux:
                    if lang.display_text.lower() == "java":
                        continue
                    self._parse_major_version_linux(major_version, self._stacks)
                if self._windows:
                    self._parse_major_version_windows(major_version, self._stacks, self.windows_config_mappings)

    @classmethod
    def remove_delimiters(cls, runtime):
        if not runtime:
            return runtime
        runtime = re.split("[{}]".format(cls.ALLOWED_DELIMETERS), runtime)
        return cls.DEFAULT_DELIMETER.join(filter(None, runtime))

    def resolve(self, display_name, linux=False):
        display_name = display_name.lower()
        stack = next((s for s in self.stacks if s.linux == linux and s.display_name.lower() == display_name), None)
        if stack is None:  # help convert previously acceptable stack names into correct ones if runtime not found
            old_to_new_windows = {
                "node|12-lts": "node|12lts",
                "node|14-lts": "node|14lts",
                "node|16-lts": "node|16lts",
                "dotnet|5.0": "dotnet|5",
                "dotnet|6.0": "dotnet|6",
            }
            old_to_new_linux = {
                "dotnet|5.0": "dotnetcore|5.0",
                "dotnet|6.0": "dotnetcore|6.0",
            }
            if linux:
                display_name = old_to_new_linux.get(display_name)
            else:
                display_name = old_to_new_windows.get(display_name)
            stack = next((s for s in self.stacks if s.linux == linux and s.display_name.lower() == display_name), None)
        return stack

    @classmethod
    def get_site_config_setter(cls, runtime, linux=False):
        if linux:
            return cls.update_site_config
        return cls.update_site_appsettings if 'node' in runtime.display_name.lower() else cls.update_site_config

    # assumes non-java
    def get_default_version(self, lang, linux=False, get_windows_config_version=False):
        versions = self.get_version_list(lang, linux, get_windows_config_version)
        versions.sort()
        if not versions:
            os = WINDOWS_OS_NAME if not linux else LINUX_OS_NAME
            raise ValidationError("Invalid language type {} for OS {}".format(lang, os))
        return versions[0]

    # assumes non-java
    def get_version_list(self, lang, linux=False, get_windows_config_version=False):
        lang = lang.upper()
        versions = []

        for s in self.stacks:
            if s.linux == linux:
                l_name, v, *_ = s.display_name.upper().split("|")
                if l_name == lang:
                    if get_windows_config_version:
                        versions.append(s.configs[self.windows_config_mappings[lang.lower()]])
                    else:
                        versions.append(v)

        return versions

    @staticmethod
    def update_site_config(stack, site_config, cmd=None):
        for k, v in stack.configs.items():
            setattr(site_config, k, v)
        return site_config

    @staticmethod
    def update_site_appsettings(cmd, stack, site_config):
        NameValuePair = cmd.get_models('NameValuePair')
        if site_config.app_settings is None:
            site_config.app_settings = []

        for k, v in stack.configs.items():
            already_in_appsettings = False
            for app_setting in site_config.app_settings:
                if app_setting.name == k:
                    already_in_appsettings = True
                    app_setting.value = v
            if not already_in_appsettings:
                site_config.app_settings.append(NameValuePair(name=k, value=v))
        return site_config

    # format a (non-java) windows runtime display text
    # TODO get API to return more CLI-friendly display text for windows stacks
    @classmethod
    def _format_windows_display_text(cls, display_text):
        t = display_text.upper()
        t = t.replace(".NET CORE", NETCORE_RUNTIME_NAME.upper())
        t = t.replace("ASP.NET", ASPDOTNET_RUNTIME_NAME.upper())
        t = t.replace(".NET", DOTNET_RUNTIME_NAME)
        t = re.sub(r"\(.*\)", "", t)  # remove "(LTS)"
        return t.replace(" ", "|", 1).replace(" ", "")

    @classmethod
    def _is_valid_runtime_setting(cls, runtime_setting):
        # Using datetime module imported at the top level
        if runtime_setting is None or getattr(runtime_setting, 'is_hidden', False):
            return False
        if getattr(runtime_setting, 'is_deprecated', False):
            return False
        end_of_life = getattr(runtime_setting, 'end_of_life_date', None)
        if end_of_life:
            try:
                if isinstance(end_of_life, str):
                    try:
                        end_of_life_dt = datetime.datetime.strptime(
                            end_of_life, "%Y-%m-%dT%H:%M:%S.%fZ"
                        ).replace(tzinfo=datetime.timezone.utc)
                    except ValueError:
                        end_of_life_dt = datetime.datetime.strptime(
                            end_of_life, "%Y-%m-%dT%H:%M:%SZ"
                        ).replace(tzinfo=datetime.timezone.utc)
                else:
                    # If already a datetime, ensure it's timezone-aware
                    if end_of_life.tzinfo is None:
                        end_of_life_dt = end_of_life.replace(tzinfo=datetime.timezone.utc)
                    else:
                        end_of_life_dt = end_of_life
                now_utc = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
                if now_utc >= end_of_life_dt:
                    return False
            except (ValueError, AttributeError):
                pass
        return True

    @classmethod
    def _get_runtime_setting(cls, minor_version, linux, java):
        if not linux:
            if not java:
                return minor_version.stack_settings.windows_runtime_settings
            return minor_version.stack_settings.windows_container_settings
        if not java:
            return minor_version.stack_settings.linux_runtime_settings
        return minor_version.stack_settings.linux_container_settings

    @classmethod
    def _get_valid_minor_versions(cls, major_version, linux, java=False):
        def _filter(minor_version):
            return cls._is_valid_runtime_setting(cls._get_runtime_setting(minor_version, linux, java))
        return [m for m in major_version.minor_versions if _filter(m)]

    def _parse_major_version_windows(self, major_version, parsed_results, config_mappings):
        java_container_minor_versions = self._get_valid_minor_versions(major_version, linux=False, java=True)
        if java_container_minor_versions:
            javas = ["21", "17", "11", "1.8"]
            if len(java_container_minor_versions) > 0:
                leng = len(java_container_minor_versions) if len(java_container_minor_versions) < 3 else 3
                java_container_minor_versions = java_container_minor_versions[:leng]
            for container in java_container_minor_versions:
                container_settings = container.stack_settings.windows_container_settings
                java_container = container_settings.java_container
                container_version = container_settings.java_container_version
                for java in javas:
                    runtime = self.get_windows_java_runtime(
                        java,
                        java_container,
                        container_version,
                        container_settings.is_auto_update)
                    parsed_results.append(runtime)
        else:
            minor_versions = self._get_valid_minor_versions(major_version, linux=False, java=False)
            if "Java" in major_version.display_text:
                if len(minor_versions) > 0:
                    leng = len(minor_versions) if len(minor_versions) < 3 else 3
                    minor_versions = minor_versions[1:leng]
            for minor_version in minor_versions:
                settings = minor_version.stack_settings.windows_runtime_settings
                if "Java" not in minor_version.display_text:
                    runtime_name = self._format_windows_display_text(minor_version.display_text)

                    runtime = self.Runtime(display_name=runtime_name, linux=False)
                    lang_name = runtime_name.split("|")[0].lower()
                    config_key = config_mappings.get(lang_name)

                    if config_key:
                        runtime.configs[config_key] = settings.runtime_version
                    gh_properties = settings.git_hub_action_settings
                    if gh_properties.is_supported:
                        runtime.github_actions_properties = {"github_actions_version": gh_properties.supported_version}
                else:
                    runtime = self.get_windows_java_runtime(settings.runtime_version, "JAVA", "SE", False)

                parsed_results.append(runtime)

    def get_windows_java_runtime(self, java_version=None,
                                 java_container=None, container_version=None,
                                 is_auto_update=False):
        github_action_container_version = container_version
        if container_version.upper() == "SE":
            java_container = "JAVA SE"
            if java_version.startswith("1.8"):
                container_version = "8"
            else:
                container_version = java_version.split('.')[0]
        runtime_name = "{}|{}-{}{}".format(
            java_container,
            container_version,
            "java",
            java_version if not java_version.startswith("1.8") else "8") \
            if java_container != "JAVA SE" else "{}|{}".format(
                "JAVA",
                java_version if not java_version.startswith("1.8") or not is_auto_update else "8")
        gh_actions_version = "8" if java_version == "1.8" else java_version
        gh_actions_runtime = "{}, {}, {}".format(java_version,
                                                 java_container.lower().replace(" se", ""),
                                                 github_action_container_version.lower())
        if java_container == "JAVA SE":  # once runtime name is set, reset configs to correct values
            java_container = "JAVA"
            container_version = "SE"
        return self.Runtime(display_name=runtime_name,
                            configs={"java_version": java_version,
                                     "java_container": java_container,
                                     "java_container_version": container_version},
                            github_actions_properties={"github_actions_version": gh_actions_version,
                                                       "app_runtime": "java",
                                                       "app_runtime_version": gh_actions_runtime},
                            linux=False,
                            is_auto_update=is_auto_update)

    def _parse_major_version_linux(self, major_version, parsed_results):
        minor_java_container_versions = self._get_valid_minor_versions(major_version, linux=True, java=True)
        if "SE" in major_version.display_text:
            se_containers = [minor_java_container_versions[0]]
            for java in ["21", "17", "11", "1.8"]:
                se_java_containers = [c for c in minor_java_container_versions if c.value.startswith(java)]
                se_containers = se_containers + se_java_containers[:len(se_java_containers) if len(se_java_containers) < 2 else 2]    # pylint: disable=line-too-long
            minor_java_container_versions = se_containers
        if minor_java_container_versions:
            leng = len(minor_java_container_versions) if \
                len(minor_java_container_versions) < 3 else 3 if \
                "SE" not in major_version.display_text else len(minor_java_container_versions)
            for minor in minor_java_container_versions[:leng]:
                linux_container_settings = minor.stack_settings.linux_container_settings
                runtimes = [
                    (linux_container_settings.additional_properties.get("java21Runtime"), "21", linux_container_settings.is_auto_update),    # pylint: disable=line-too-long
                    (linux_container_settings.additional_properties.get("java17Runtime"), "17", linux_container_settings.is_auto_update),    # pylint: disable=line-too-long
                    (linux_container_settings.java11_runtime, "11", linux_container_settings.is_auto_update),
                    (linux_container_settings.java8_runtime, "8", linux_container_settings.is_auto_update)]
                # Remove the JBoss'_byol' entries from the output
                runtimes = [(r, v, au) for (r, v, au) in runtimes if r is not None and not r.endswith("_byol")]    # pylint: disable=line-too-long
                for runtime_name, version, auto_update in [(r, v, au) for (r, v, au) in runtimes if r is not None]:
                    runtime = self.Runtime(display_name=runtime_name,
                                           configs={"linux_fx_version": runtime_name},
                                           github_actions_properties={"github_actions_version": version},
                                           linux=True,
                                           is_auto_update=auto_update)
                    parsed_results.append(runtime)
        else:
            minor_versions = self._get_valid_minor_versions(major_version, linux=True, java=False)
            for minor_version in minor_versions:
                settings = minor_version.stack_settings.linux_runtime_settings
                runtime_name = settings.runtime_version
                runtime = self.Runtime(display_name=runtime_name,
                                       configs={"linux_fx_version": runtime_name},
                                       linux=True,
                                       )
                gh_properties = settings.git_hub_action_settings
                if gh_properties.is_supported:
                    runtime.github_actions_properties = {"github_actions_version": gh_properties.supported_version}
                parsed_results.append(runtime)

    # override _load_stacks() to call this method to use hardcoded stacks
    def _load_stacks_hardcoded(self):
        import os
        stacks_file = os.path.abspath(os.path.join(os.path.abspath(__file__), '../resources/WebappRuntimeStacks.json'))
        if self._stacks:
            return
        stacks = []
        if self._linux:
            stacks_json = get_file_json(stacks_file)['linux']
            for r in stacks_json:
                stacks.append(self.Runtime(display_name=r.get("displayName"),
                                           configs=r.get("configs"),
                                           github_actions_properties=r.get("github_actions_properties"),
                                           linux=True))
        if self._windows:  # Windows stacks
            stacks_json = get_file_json(stacks_file)['windows']
            for r in stacks_json:
                stacks.append(self.Runtime(display_name=r.get("displayName"),
                                           configs=r.get("configs"),
                                           github_actions_properties=r.get("github_actions_properties"),
                                           linux=False))
        self._stacks = stacks


class _FlexFunctionAppStackRuntimeHelper:
    class Runtime:
        def __init__(self, name, version, app_insights=False, default=False, sku=None,
                     end_of_life_date=None, github_actions_properties=None):
            self.name = name
            self.version = version
            self.app_insights = app_insights
            self.default = default
            self.sku = sku
            self.end_of_life_date = end_of_life_date
            self.github_actions_properties = github_actions_properties

    class GithubActionsProperties:
        def __init__(self, is_supported, supported_version):
            self.is_supported = is_supported
            self.supported_version = supported_version

    def __init__(self, cmd, location, runtime, runtime_version=None):
        self._cmd = cmd
        self._location = location
        self._runtime = runtime
        self._runtime_version = runtime_version
        self._stacks = []

    @property
    def stacks(self):
        self._load_stacks()
        return self._stacks

    def get_flex_raw_function_app_stacks(self, cmd, location, runtime):
        stacks_api_url = '/providers/Microsoft.Web/locations/{}/functionAppStacks?' \
                         'api-version=2020-10-01&removeHiddenStacks=true&removeDeprecatedStacks=true&stack={}&sku=FC1'
        if runtime == "dotnet-isolated":
            runtime = "dotnet"
        request_url = cmd.cli_ctx.cloud.endpoints.resource_manager + stacks_api_url.format(location, runtime)
        response = send_raw_request(cmd.cli_ctx, "GET", request_url)
        return response.json()['value']

    # remove non-digit or non-"." chars
    @classmethod
    def _format_version_name(cls, name):
        return re.sub(r"[^\d\.]", "", name)

    # format version names while maintaining uniqueness
    def _format_version_names(self, runtime_to_version):
        formatted_runtime_to_version = {}
        for runtime, versions in runtime_to_version.items():
            formatted_runtime_to_version[runtime] = formatted_runtime_to_version.get(runtime, {})
            for version_name, version_info in versions.items():
                formatted_name = self._format_version_name(version_name)
                if formatted_name in formatted_runtime_to_version[runtime]:
                    formatted_name = version_name.lower().replace(" ", "-")
                formatted_runtime_to_version[runtime][formatted_name] = version_info
        return formatted_runtime_to_version

    def _parse_raw_stacks(self, stacks):
        runtime_to_version = {}
        for runtime in stacks:
            for major_version in runtime['properties']['majorVersions']:
                for minor_version in major_version['minorVersions']:
                    runtime_version = minor_version['value']
                    if minor_version['stackSettings'].get('linuxRuntimeSettings') is None:
                        continue

                    runtime_settings = minor_version['stackSettings']['linuxRuntimeSettings']
                    runtime_name = (runtime_settings['appSettingsDictionary']['FUNCTIONS_WORKER_RUNTIME'] or
                                    runtime['name'])

                    skus = runtime_settings['Sku']
                    github_actions_settings = runtime_settings['gitHubActionSettings']
                    if skus is None:
                        continue

                    for sku in skus:
                        if sku['skuCode'] != 'FC1':
                            continue

                        github_actions_properties = {
                            'is_supported': github_actions_settings.get('isSupported', False),
                            'supported_version': github_actions_settings.get('supportedVersion', None)
                        }

                        runtime_version_properties = {
                            'isDefault': runtime_settings.get('isDefault', False),
                            'sku': sku,
                            'applicationInsights': runtime_settings['appInsightsSettings']['isSupported'],
                            'endOfLifeDate': runtime_settings.get('endOfLifeDate'),
                            'github_actions_properties': self.GithubActionsProperties(**github_actions_properties)
                        }

                        runtime_to_version[runtime_name] = runtime_to_version.get(runtime_name, {})
                        runtime_to_version[runtime_name][runtime_version] = runtime_version_properties

        runtime_to_version = self._format_version_names(runtime_to_version)

        for runtime_name, versions in runtime_to_version.items():
            for version_name, version_properties in versions.items():
                r = self._create_runtime_from_properties(runtime_name, version_name, version_properties)
                self._stacks.append(r)

    def _create_runtime_from_properties(self, runtime_name, version_name, version_properties):
        return self.Runtime(name=runtime_name,
                            version=version_name,
                            app_insights=version_properties['applicationInsights'],
                            default=version_properties['isDefault'],
                            sku=version_properties['sku'],
                            end_of_life_date=version_properties['endOfLifeDate'],
                            github_actions_properties=version_properties['github_actions_properties'])

    def _load_stacks(self):
        if self._stacks:
            return
        stacks = self.get_flex_raw_function_app_stacks(self._cmd, self._location, self._runtime)
        self._parse_raw_stacks(stacks)

    def _get_version_variants(self, version):
        variants = {version}

        if '.' in version:
            if version.endswith('.0'):
                variants.add(version[:-2])
        else:
            variants.add(f"{version}.0")

        return variants

    def _find_matching_runtime_version(self, runtimes, version):
        version_variants = self._get_version_variants(version)

        for variant in version_variants:
            matched_runtime = next((r for r in runtimes if r.version == variant), None)
            if matched_runtime:
                return matched_runtime

        return None

    def resolve(self, runtime, version=None):
        runtimes = [r for r in self.stacks if runtime == r.name]
        if not runtimes:
            raise ValidationError("Runtime '{}' not supported for function apps on the Flex Consumption plan."
                                  .format(runtime))
        if version is None:
            return self.get_default_version()

        matched_runtime_version = next((r for r in runtimes if r.version == version), None)

        if not matched_runtime_version:
            matched_runtime_version = self._find_matching_runtime_version(runtimes, version)

        if not matched_runtime_version:
            versions = [r.version for r in runtimes]
            raise ValidationError("Invalid version {0} for runtime {1} for function apps on the Flex Consumption"
                                  " plan. Supported versions for runtime {1} are {2}."
                                  .format(version, runtime, versions))
        return matched_runtime_version

    def get_default_version(self):
        runtimes = self.stacks
        runtimes.sort(key=lambda r: r.default, reverse=True)
        return runtimes[0]


class _FunctionAppStackRuntimeHelper(_AbstractStackRuntimeHelper):
    # pylint: disable=too-few-public-methods,too-many-instance-attributes
    class Runtime:
        def __init__(self, name=None, version=None, is_preview=False, supported_func_versions=None, linux=False,
                     app_settings_dict=None, site_config_dict=None, app_insights=False, default=False,
                     github_actions_properties=None, end_of_life_date=None):
            self.name = name
            self.version = version
            self.is_preview = is_preview
            self.supported_func_versions = [] if not supported_func_versions else supported_func_versions
            self.linux = linux
            self.app_settings_dict = {} if not app_settings_dict else app_settings_dict
            self.site_config_dict = {} if not site_config_dict else site_config_dict
            self.app_insights = app_insights
            self.default = default
            self.github_actions_properties = github_actions_properties
            self.end_of_life_date = end_of_life_date

            self.display_name = "{}|{}".format(name, version) if version else name
            self.deprecation_link = LANGUAGE_EOL_DEPRECATION_NOTICES.get(self.display_name, '')

        # used for displaying stacks
        def to_dict(self):
            d = {"runtime": self.name,
                 "version": self.version,
                 "supported_functions_versions": self.supported_func_versions}
            if self.linux:
                d["linux_fx_version"] = self.site_config_dict.linux_fx_version
            return d

    def __init__(self, cmd, linux=False, windows=False):
        self.disallowed_functions_versions = {"~1", "~2", "~3"}
        self.KEYS = FUNCTIONS_STACKS_API_KEYS()
        super().__init__(cmd, linux=linux, windows=windows)

    def validate_end_of_life_date(self, runtime, version, is_linux):
        from dateutil.relativedelta import relativedelta
        # we would not be able to validate for a custom runtime
        if runtime == 'custom':
            return

        today = datetime.datetime.now(datetime.timezone.utc)
        six_months = today + relativedelta(months=+6)
        runtimes = [r for r in self.stacks if r.linux == is_linux and runtime == r.name]
        runtimes.sort(key=lambda r: r.end_of_life_date or
                      datetime.datetime.min.replace(tzinfo=datetime.timezone.utc), reverse=True)
        matched_runtime = next((r for r in runtimes if r.version == version), None)
        if matched_runtime:
            eol = matched_runtime.end_of_life_date
            runtime_deprecation_link = matched_runtime.deprecation_link
            latest_runtime = runtimes[0].version

            if eol is None:
                return

            if eol < today:
                raise ValidationError('Use {} version {} as {} has reached end-of-life on {} and is '
                                      'no longer supported. {}'
                                      .format(runtime, latest_runtime, version, eol.date(), runtime_deprecation_link))
            if eol < six_months:
                logger.warning('Use %s version %s as %s will reach end-of-life on %s and will no '
                               'longer be supported. %s',
                               runtime, latest_runtime, version, eol.date(), runtime_deprecation_link)

    def resolve(self, runtime, version=None, functions_version=None, is_linux=False, disable_version_error=False):
        stacks = self.stacks
        runtimes = [r for r in stacks if r.linux == is_linux and runtime == r.name]
        os = LINUX_OS_NAME if is_linux else WINDOWS_OS_NAME
        if not runtimes:
            supported_runtimes = [r.name for r in stacks if r.linux == is_linux]
            raise ValidationError("Runtime {0} not supported for os {1}. Supported runtimes for os {1} are: {2}. "
                                  "Run 'az functionapp list-runtimes' for more details on supported runtimes. "
                                  .format(runtime, os, supported_runtimes))
        if version is None:
            matched_runtime_version = self.get_default_version(runtime, functions_version, is_linux)
            self.validate_end_of_life_date(
                matched_runtime_version.name,
                matched_runtime_version.version,
                is_linux
            )
            return matched_runtime_version
        matched_runtime_version = next((r for r in runtimes if r.version == version), None)
        if not matched_runtime_version:
            # help convert previously acceptable versions into correct ones if match not found
            old_to_new_version = {
                "11": "11.0",
                "8": "8.0",
                "8.0": "8",
                "7": "7.0",
                "6.0": "6",
                "1.8": "8.0",
                "17": "17.0"
            }
            new_version = old_to_new_version.get(version)
            matched_runtime_version = next((r for r in runtimes if r.version == new_version), None)
            if matched_runtime_version is not None:
                version = new_version

        self.validate_end_of_life_date(
            runtime,
            version,
            is_linux
        )

        if not matched_runtime_version:
            versions = [r.version for r in runtimes]
            if disable_version_error:
                return None
            raise ValidationError("Invalid version: {0} for runtime {1} and os {2}. Supported versions for runtime "
                                  "{1} and os {2} are: {3}. "
                                  "Run 'az functionapp list-runtimes' for more details on supported runtimes. "
                                  .format(version, runtime, os, versions))
        if functions_version not in matched_runtime_version.supported_func_versions:
            supported_func_versions = matched_runtime_version.supported_func_versions
            raise ValidationError("Functions version {} is not supported for runtime {} with version {} and os {}. "
                                  "Supported functions versions are {}. "
                                  "Run 'az functionapp list-runtimes' for more details on supported runtimes. "
                                  .format(functions_version, runtime, version, os, supported_func_versions))
        return matched_runtime_version

    def get_default_version(self, runtime, functions_version, is_linux=False):
        runtimes = [r for r in self.stacks if r.linux == is_linux and r.name == runtime]
        # sort runtimes by end of life date
        runtimes.sort(key=lambda r: r.end_of_life_date or
                      datetime.datetime.min.replace(tzinfo=datetime.timezone.utc), reverse=True)
        for r in runtimes:
            if functions_version in r.supported_func_versions:
                return r
        raise ValidationError("Could not find a runtime version for runtime {} with functions version {} and os {}"
                              "Run 'az functionapp list-runtimes' for more details on supported runtimes. ")

    def _get_raw_stacks_from_api(self):
        return list(self._client.provider.get_function_app_stacks(stack_os_type=None))

    # remove non-digit or non-"." chars
    @classmethod
    def _format_version_name(cls, name):
        return re.sub(r"[^\d\.]", "", name)

    # format version names while maintaining uniqueness
    def _format_version_names(self, runtime_to_version):
        formatted_runtime_to_version = {}
        for runtime, versions in runtime_to_version.items():
            formatted_runtime_to_version[runtime] = formatted_runtime_to_version.get(runtime, {})
            for version_name, version_info in versions.items():
                formatted_name = self._format_version_name(version_name)
                if formatted_name in formatted_runtime_to_version[runtime]:
                    formatted_name = version_name.lower().replace(" ", "-")
                formatted_runtime_to_version[runtime][formatted_name] = version_info
        return formatted_runtime_to_version

    @classmethod
    def _format_function_version(cls, v):
        return v.replace("~", "")

    def _get_valid_function_versions(self, runtime_settings):
        supported_function_versions = runtime_settings.supported_functions_extension_versions
        valid_versions = []
        for v in supported_function_versions:
            if v not in self.disallowed_functions_versions:
                valid_versions.append(self._format_version_name(v))
        return valid_versions

    def _parse_minor_version(self, runtime_settings, major_version_name, minor_version_name, runtime_to_version):
        runtime_name = (runtime_settings.app_settings_dictionary.get(self.KEYS.FUNCTIONS_WORKER_RUNTIME) or
                        major_version_name)
        if not runtime_settings.is_deprecated:
            functions_versions = self._get_valid_function_versions(runtime_settings)
            if functions_versions:
                runtime_version_properties = {
                    self.KEYS.IS_PREVIEW: runtime_settings.is_preview,
                    self.KEYS.SUPPORTED_EXTENSION_VERSIONS: functions_versions,
                    self.KEYS.APP_SETTINGS_DICT: runtime_settings.app_settings_dictionary,
                    self.KEYS.APPLICATION_INSIGHTS: runtime_settings.app_insights_settings.is_supported,
                    self.KEYS.SITE_CONFIG_DICT: runtime_settings.site_config_properties_dictionary,
                    self.KEYS.IS_DEFAULT: bool(runtime_settings.is_default),
                    self.KEYS.GIT_HUB_ACTION_SETTINGS: runtime_settings.git_hub_action_settings,
                    self.KEYS.END_OF_LIFE_DATE: runtime_settings.end_of_life_date,
                }

                runtime_to_version[runtime_name] = runtime_to_version.get(runtime_name, {})
                runtime_to_version[runtime_name][minor_version_name] = runtime_version_properties

    def _create_runtime_from_properties(self, runtime_name, version_name, version_properties, linux):
        supported_func_versions = version_properties[self.KEYS.SUPPORTED_EXTENSION_VERSIONS]
        return self.Runtime(name=runtime_name,
                            version=version_name,
                            is_preview=version_properties[self.KEYS.IS_PREVIEW],
                            supported_func_versions=supported_func_versions,
                            linux=linux,
                            site_config_dict=version_properties[self.KEYS.SITE_CONFIG_DICT],
                            app_settings_dict=version_properties[self.KEYS.APP_SETTINGS_DICT],
                            app_insights=version_properties[self.KEYS.APPLICATION_INSIGHTS],
                            default=version_properties[self.KEYS.IS_DEFAULT],
                            github_actions_properties=version_properties[self.KEYS.GIT_HUB_ACTION_SETTINGS],
                            end_of_life_date=version_properties[self.KEYS.END_OF_LIFE_DATE])

    def _parse_raw_stacks(self, stacks):
        # build a map of runtime -> runtime version -> runtime version properties
        runtime_to_version_linux = {}
        runtime_to_version_windows = {}
        for runtime in stacks:
            for major_version in runtime.major_versions:
                for minor_version in major_version.minor_versions:
                    runtime_version = minor_version.value
                    linux_settings = minor_version.stack_settings.linux_runtime_settings
                    windows_settings = minor_version.stack_settings.windows_runtime_settings

                    if linux_settings is not None and not linux_settings.is_hidden:
                        self._parse_minor_version(runtime_settings=linux_settings,
                                                  major_version_name=runtime.name,
                                                  minor_version_name=runtime_version,
                                                  runtime_to_version=runtime_to_version_linux)

                    if windows_settings is not None and not windows_settings.is_hidden:
                        self._parse_minor_version(runtime_settings=windows_settings,
                                                  major_version_name=runtime.name,
                                                  minor_version_name=runtime_version,
                                                  runtime_to_version=runtime_to_version_windows)

        runtime_to_version_linux = self._format_version_names(runtime_to_version_linux)
        runtime_to_version_windows = self._format_version_names(runtime_to_version_windows)

        for runtime_name, versions in runtime_to_version_windows.items():
            for version_name, version_properties in versions.items():
                r = self._create_runtime_from_properties(runtime_name, version_name, version_properties, linux=False)
                self._stacks.append(r)

        for runtime_name, versions in runtime_to_version_linux.items():
            for version_name, version_properties in versions.items():
                r = self._create_runtime_from_properties(runtime_name, version_name, version_properties, linux=True)
                self._stacks.append(r)


def get_app_insights_key(cli_ctx, resource_group, name):
    appinsights_client = get_mgmt_service_client(cli_ctx, ApplicationInsightsManagementClient)
    appinsights = appinsights_client.components.get(resource_group, name)
    if appinsights is None or appinsights.instrumentation_key is None:
        raise ResourceNotFoundError("App Insights {} under resource group {} was not found.".format(name,
                                                                                                    resource_group))
    return appinsights.instrumentation_key


def get_app_insights_connection_string(cli_ctx, resource_group, name):
    appinsights_client = get_mgmt_service_client(cli_ctx, ApplicationInsightsManagementClient)
    appinsights = appinsights_client.components.get(resource_group, name)
    if appinsights is None or appinsights.connection_string is None:
        raise ResourceNotFoundError("App Insights {} under resource group {} was not found.".format(name,
                                                                                                    resource_group))
    return appinsights.connection_string


def create_flex_app_service_plan(cmd, resource_group_name, name, location, zone_redundant):
    SkuDescription, AppServicePlan = cmd.get_models('SkuDescription', 'AppServicePlan')
    client = web_client_factory(cmd.cli_ctx)
    sku_def = SkuDescription(tier="FlexConsumption", name="FC1", size="FC", family="FC")
    plan_def = AppServicePlan(
        location=location,
        sku=sku_def,
        reserved=True,
        kind="functionapp"
    )

    if zone_redundant:
        _enable_zone_redundant(plan_def, sku_def, None)

    poller = client.app_service_plans.begin_create_or_update(resource_group_name, name, plan_def)
    return LongRunningOperation(cmd.cli_ctx)(poller)


def update_flex_app_service_plan(instance):
    instance.target_worker_count = None
    instance.target_worker_size = None
    instance.is_xenon = None
    instance.hyper_v = None
    instance.per_site_scaling = None
    instance.maximum_elastic_worker_count = None
    instance.elastic_scale_enabled = None
    instance.is_spot = None
    instance.target_worker_size_id = None
    instance.sku.capacity = None
    return instance


def create_functionapp_app_service_plan(cmd, resource_group_name, name, is_linux, sku, number_of_workers=None,
                                        max_burst=None, location=None, tags=None, zone_redundant=False):
    SkuDescription, AppServicePlan = cmd.get_models('SkuDescription', 'AppServicePlan')
    sku = _normalize_sku(sku)
    tier = get_sku_tier(sku)

    client = web_client_factory(cmd.cli_ctx)
    if location is None:
        location = _get_location_from_resource_group(cmd.cli_ctx, resource_group_name)
    if number_of_workers is not None:
        number_of_workers = validate_range_of_int_flag('--number-of-workers', number_of_workers, min_val=0, max_val=20)
    sku_def = SkuDescription(tier=tier, name=sku, capacity=number_of_workers)
    plan_def = AppServicePlan(location=location, tags=tags, sku=sku_def,
                              reserved=(is_linux or None), maximum_elastic_worker_count=max_burst,
                              hyper_v=None, name=name)

    if zone_redundant:
        _enable_zone_redundant(plan_def, sku_def, number_of_workers)

    return client.app_service_plans.begin_create_or_update(resource_group_name, name, plan_def)


def is_plan_consumption(cmd, plan_info):
    SkuDescription, AppServicePlan = cmd.get_models('SkuDescription', 'AppServicePlan')
    if isinstance(plan_info, AppServicePlan):
        if isinstance(plan_info.sku, SkuDescription):
            return plan_info.sku.tier.lower() == 'dynamic'
    return False


def is_plan_flex(cmd, plan_info):
    SkuDescription, AppServicePlan = cmd.get_models('SkuDescription', 'AppServicePlan')
    if isinstance(plan_info, AppServicePlan):
        if isinstance(plan_info.sku, SkuDescription):
            return plan_info.sku.tier.lower() == 'flexconsumption'
    return False


def is_plan_elastic_premium(cmd, plan_info):
    SkuDescription, AppServicePlan = cmd.get_models('SkuDescription', 'AppServicePlan')
    if isinstance(plan_info, AppServicePlan):
        if isinstance(plan_info.sku, SkuDescription):
            return plan_info.sku.tier == 'ElasticPremium'
    return False


def should_enable_distributed_tracing(consumption_plan_location, flexconsumption_location, matched_runtime, image):
    return consumption_plan_location is None \
        and flexconsumption_location is None \
        and matched_runtime.name.lower() == "java" \
        and image is None


def update_functionapp_polling(cmd, resource_group_name, name, functionapp):
    from azure.cli.core.commands.client_factory import get_subscription_id
    client = web_client_factory(cmd.cli_ctx)
    sub_id = get_subscription_id(cmd.cli_ctx)
    base_url = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Web/sites/{}?api-version={}'.format(
        sub_id,
        resource_group_name,
        name,
        client.DEFAULT_API_VERSION
    )
    url = cmd.cli_ctx.cloud.endpoints.resource_manager + base_url

    site_resource_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Web/sites/{}'.format(
        sub_id,
        resource_group_name,
        name,
    )

    updated_functionapp = json.dumps(
        {
            "id": site_resource_id,
            "name": name,
            "type": "Microsoft.Web/sites",
            "kind": "functionapp,linux,container,azurecontainerapps",
            "location": functionapp.location,
            "properties": {
                "daprConfig": {"enabled": False} if functionapp.dapr_config is None else {
                    "enabled": functionapp.dapr_config.enabled,
                    "appId": functionapp.dapr_config.app_id,
                    "appPort": functionapp.dapr_config.app_port,
                    "httpReadBufferSize": functionapp.dapr_config.http_read_buffer_size or 4,
                    "httpMaxRequestSize": functionapp.dapr_config.http_max_request_size or 4,
                    "logLevel": functionapp.dapr_config.log_level,
                    "enableApiLogging": functionapp.dapr_config.enable_api_logging
                },
                "workloadProfileName": functionapp.workload_profile_name,
                "resourceConfig": {
                    "cpu": functionapp.resource_config.cpu,
                    "memory": functionapp.resource_config.memory
                }
            }
        }
    )
    response = send_raw_request(cmd.cli_ctx, method='PATCH', url=url, body=updated_functionapp)
    poll_url = response.headers.get('location', "")
    if response.status_code == 202 and poll_url:
        response = send_raw_request(cmd.cli_ctx, method='get', url=poll_url)

        while response.status_code != 200:
            time.sleep(5)
            response = send_raw_request(cmd.cli_ctx, method='get', url=poll_url)

        if response.status_code == 200:
            return response

    else:
        return response


def update_dapr_and_workload_config(cmd, resource_group_name, name, enabled=None, app_id=None, app_port=None,
                                    http_max_request_size=None, http_read_buffer_size=None, log_level=None,
                                    enable_api_logging=None, workload_profile_name=None, cpu=None, memory=None):
    site = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get')
    DaprConfig = cmd.get_models('DaprConfig')

    if enabled is None:
        if site.dapr_config and site.dapr_config.enabled is False:
            site.dapr_config = None
    elif enabled == "false":
        site.dapr_config = None
    elif enabled == "true":
        if site.dapr_config is None:
            site.dapr_config = DaprConfig()
            site.dapr_config.enabled = True
        elif site.dapr_config and site.dapr_config.enabled is False:
            site.dapr_config.enabled = True

    if any([app_id, app_port, http_max_request_size, http_read_buffer_size, log_level, enable_api_logging]) \
            and site.dapr_config is None:
        raise ArgumentUsageError("usage error: parameters --dapr-app-id, "
                                 "--dapr-app-port, --dapr-http-max-request-size, "
                                 "--dapr-http-read-buffer-size, --dapr-log-level and "
                                 "--dapr-enable-api-logging must be used with parameter --enable-dapr true.")

    if site.dapr_config is not None:
        import inspect
        frame = inspect.currentframe()
        bool_flags = ['enabled', 'enable_api_logging']
        int_flags = ['app_port', 'http_max_request_size', 'http_read_buffer_size']
        args, _, _, values = inspect.getargvalues(frame)  # pylint: disable=deprecated-method
        for arg in args[3:10]:
            if arg in int_flags and values[arg] is not None:
                values[arg] = validate_and_convert_to_int(arg, values[arg])
            if values.get(arg, None):
                setattr(site.dapr_config, arg, values[arg] if arg not in bool_flags else values[arg] == 'true')

    if cpu is not None and memory is not None:
        setattr(site.resource_config, 'cpu', cpu)
        setattr(site.resource_config, 'memory', memory)

    if workload_profile_name is not None:
        setattr(site, 'workload_profile_name', workload_profile_name)

    update_functionapp_polling(cmd, resource_group_name, name, site)


def is_exactly_one_true(*args):
    found = False
    for i in args:
        if bool(i):
            if found:
                return False
            found = True
    return found


def create_functionapp(cmd, resource_group_name, name, storage_account, plan=None,
                       os_type=None, functions_version=None, runtime=None, runtime_version=None,
                       consumption_plan_location=None, app_insights=None, app_insights_key=None,
                       disable_app_insights=None, deployment_source_url=None,
                       deployment_source_branch=None, deployment_local_git=None,
                       registry_server=None, registry_password=None, registry_username=None,
                       image=None, tags=None, assign_identities=None,
                       role='Contributor', scope=None, vnet=None, subnet=None, https_only=False,
                       environment=None, min_replicas=None, max_replicas=None, workspace=None,
                       enable_dapr=False, dapr_app_id=None, dapr_app_port=None, dapr_http_max_request_size=None,
                       dapr_http_read_buffer_size=None, dapr_log_level=None, dapr_enable_api_logging=False,
                       workload_profile_name=None, cpu=None, memory=None,
                       always_ready_instances=None, maximum_instance_count=None, instance_memory=None,
                       flexconsumption_location=None, deployment_storage_name=None,
                       deployment_storage_container_name=None, deployment_storage_auth_type=None,
                       deployment_storage_auth_value=None, zone_redundant=False, configure_networking_later=None,
                       auto_generated_domain_name_label_scope=None):
    # pylint: disable=too-many-statements, too-many-branches

    if functions_version is None and flexconsumption_location is None:
        logger.warning("No functions version specified so defaulting to 4.")
        functions_version = '4'
    enable_dapr = enable_dapr == "true"
    if deployment_source_url and deployment_local_git:
        raise MutuallyExclusiveArgumentError('usage error: --deployment-source-url <url> | --deployment-local-git')
    if any([cpu, memory, workload_profile_name]) and environment is None:
        raise RequiredArgumentMissingError("usage error: parameters --cpu, -memory, --workload-profile-name "
                                           "must be used with parameter --environment, please provide the "
                                           "name of the container app environment using --environment.")
    if environment is None and not is_exactly_one_true(plan, consumption_plan_location, flexconsumption_location):
        raise MutuallyExclusiveArgumentError("usage error: You must specify one of these parameter "
                                             "--plan NAME_OR_ID | --consumption-plan-location LOCATION |"
                                             " --flexconsumption-location LOCATION")

    if ((min_replicas is not None or max_replicas is not None) and environment is None):
        raise RequiredArgumentMissingError("usage error: parameters --min-replicas and --max-replicas must be "
                                           "used with parameter --environment, please provide the name "
                                           "of the container app environment using --environment.")
    if any([enable_dapr, dapr_app_id, dapr_app_port, dapr_http_max_request_size, dapr_http_read_buffer_size,
            dapr_log_level, dapr_enable_api_logging]) and environment is None:
        raise RequiredArgumentMissingError("usage error: parameters --enable-dapr, --dapr-app-id, "
                                           "--dapr-app-port, --dapr-http-max-request-size, "
                                           "--dapr-http-read-buffer-size, --dapr-log-level and "
                                           "dapr-enable-api-logging must be used with parameter --environment,"
                                           "please provide the name of the container app environment using "
                                           "--environment.")
    if any([dapr_app_id, dapr_app_port, dapr_http_max_request_size, dapr_http_read_buffer_size,
            dapr_log_level, dapr_enable_api_logging]) and not enable_dapr:
        raise ArgumentUsageError("usage error: parameters --dapr-app-id, "
                                 "--dapr-app-port, --dapr-http-max-request-size, "
                                 "--dapr-http-read-buffer-size, --dapr-log-level and "
                                 "dapr-enable-api-logging must be used with parameter --enable-dapr true.")

    from azure.mgmt.web.models import Site
    SiteConfig, NameValuePair, DaprConfig, ResourceConfig = cmd.get_models('SiteConfig', 'NameValuePair',
                                                                           'DaprConfig', 'ResourceConfig')

    if flexconsumption_location is None:
        if zone_redundant:
            raise ArgumentUsageError(
                '--zone-redundant is only valid for the Flex Consumption plan. '
                'Please try again without the --zone-redundant parameter.')

    if flexconsumption_location is not None:
        if image is not None:
            raise ArgumentUsageError(
                '--image is not a valid input for Azure Functions on the Flex Consumption plan. '
                'Please try again without the --image parameter.')

        if deployment_local_git is not None:
            raise ArgumentUsageError(
                '--deployment-local-git is not a valid input for Azure Functions on the Flex Consumption plan. '
                'Please try again without the --deployment-local-git parameter.')

        if deployment_source_url is not None:
            raise ArgumentUsageError(
                '--deployment-source-url is not a valid input for Azure Functions on the Flex Consumption plan. '
                'Please try again without the --deployment-source-url parameter.')

        if deployment_source_branch is not None:
            raise ArgumentUsageError(
                '--deployment-source-branch is not a valid input for Azure Functions on the Flex Consumption plan. '
                'Please try again without the --deployment-source-branch parameter.')

        if os_type and os_type.lower() != LINUX_OS_NAME:
            raise ArgumentUsageError(
                '--os-type windows is not a valid input for Azure Functions on the Flex Consumption plan. '
                'Please try again without the --os-type parameter or set --os-type to be linux.'
            )

        flexconsumption_location = _normalize_flex_location(flexconsumption_location)

    if (any([always_ready_instances, maximum_instance_count, instance_memory, deployment_storage_name,
            deployment_storage_container_name, deployment_storage_auth_type, deployment_storage_auth_value]) and
            flexconsumption_location is None):
        raise RequiredArgumentMissingError("usage error: parameters --always-ready-instances, "
                                           "--maximum-instance-count, --instance-memory, "
                                           "--deployment-storage-name, --deployment-storage-container-name, "
                                           "--deployment-storage-auth-type and --deployment-storage-auth-value "
                                           "must be used with parameter --flexconsumption-location, please "
                                           "provide the name of the flex plan location using "
                                           "--flexconsumption-location.")

    if flexconsumption_location is None:
        deployment_source_branch = deployment_source_branch or 'master'

    disable_app_insights = disable_app_insights == "true"

    site_config = SiteConfig(app_settings=[])
    client = web_client_factory(cmd.cli_ctx)

    if vnet or subnet:
        if plan:
            if is_valid_resource_id(plan):
                parse_result = parse_resource_id(plan)
                plan_info = client.app_service_plans.get(parse_result['resource_group'], parse_result['name'])
            else:
                plan_info = client.app_service_plans.get(resource_group_name, plan)
            webapp_location = plan_info.location
        elif flexconsumption_location:
            webapp_location = flexconsumption_location
            register_app_provider(cmd)
        else:
            webapp_location = consumption_plan_location

        subnet_info = _get_subnet_info(cmd=cmd,
                                       resource_group_name=resource_group_name,
                                       subnet=subnet,
                                       vnet=vnet)
        _validate_vnet_integration_location(cmd=cmd, webapp_location=webapp_location,
                                            subnet_resource_group=subnet_info["resource_group_name"],
                                            vnet_name=subnet_info["vnet_name"],
                                            vnet_sub_id=subnet_info["subnet_subscription_id"])
        _vnet_delegation_check(cmd, subnet_subscription_id=subnet_info["subnet_subscription_id"],
                               vnet_resource_group=subnet_info["resource_group_name"],
                               vnet_name=subnet_info["vnet_name"],
                               subnet_name=subnet_info["subnet_name"],
                               subnet_service_delegation=FLEX_SUBNET_DELEGATION if flexconsumption_location else None)
        subnet_resource_id = subnet_info["subnet_resource_id"]
        site_config.vnet_route_all_enabled = True
    else:
        subnet_resource_id = None

    # if this is a managed function app (Azure Functions on Azure Containers), http20_proxy_flag must be None
    if environment is not None:
        site_config.http20_proxy_flag = None

    functionapp_def = Site(location=None, site_config=site_config, tags=tags,
                           virtual_network_subnet_id=subnet_resource_id, https_only=https_only,
                           auto_generated_domain_name_label_scope=auto_generated_domain_name_label_scope)

    plan_info = None
    if runtime is not None:
        runtime = runtime.lower()

    is_storage_container_created = False
    is_user_assigned_identity_created = False

    if consumption_plan_location:
        locations = list_consumption_locations(cmd)
        location = next((loc for loc in locations if loc['name'].lower() == consumption_plan_location.lower()), None)
        if location is None:
            raise ValidationError("Location is invalid. Use: az functionapp list-consumption-locations")
        functionapp_def.location = consumption_plan_location
        functionapp_def.kind = 'functionapp'
        # if os_type is None, the os type is windows
        is_linux = bool(os_type and os_type.lower() == LINUX_OS_NAME)

    elif plan:  # apps with SKU based plan
        if is_valid_resource_id(plan):
            parse_result = parse_resource_id(plan)
            plan_info = client.app_service_plans.get(parse_result['resource_group'], parse_result['name'])
        else:
            plan_info = client.app_service_plans.get(resource_group_name, plan)
        if not plan_info:
            raise ResourceNotFoundError("The plan '{}' doesn't exist".format(plan))
        location = plan_info.location
        is_linux = bool(plan_info.reserved)
        functionapp_def.server_farm_id = plan
        functionapp_def.location = location

    elif flexconsumption_location:
        locations = list_flexconsumption_locations(cmd)
        location = next((loc for loc in locations if loc['name'].lower() == flexconsumption_location.lower()), None)
        if location is None:
            raise ValidationError("Location is invalid. Use: az functionapp list-flexconsumption-locations")
        is_linux = True

    if environment is not None:
        if consumption_plan_location is not None:
            raise ArgumentUsageError(
                '--consumption-plan-location is not a valid input for Azure Functions on Azure Container App '
                'environments. Please try again without the --consumption-plan-location parameter.')

        if plan is not None:
            raise ArgumentUsageError(
                '--plan is not a valid input for Azure Functions on Azure Container App environments. '
                'Please try again without the --plan parameter.')

        if os_type is not None:
            raise ArgumentUsageError(
                '--os-type is not a valid input for Azure Functions on Azure Container App environments. '
                'Please try again without the --os-type parameter.')

        is_linux = True

        if image is None:
            image = DEFAULT_CENTAURI_IMAGE

    if registry_server:
        docker_registry_server_url = registry_server
    else:
        docker_registry_server_url = parse_docker_image_name(image, environment)

    if is_linux and not runtime and (consumption_plan_location or not image):
        raise ArgumentUsageError(
            "usage error: --runtime RUNTIME required for linux functions apps without custom image.")

    if runtime is None and runtime_version is not None:
        raise ArgumentUsageError('Must specify --runtime to use --runtime-version')

    if flexconsumption_location:
        runtime_helper = _FlexFunctionAppStackRuntimeHelper(cmd, flexconsumption_location, runtime, runtime_version)
        matched_runtime = runtime_helper.resolve(runtime, runtime_version)
    else:
        runtime_helper = _FunctionAppStackRuntimeHelper(cmd, linux=is_linux, windows=not is_linux)
        matched_runtime = runtime_helper.resolve("dotnet" if not runtime else runtime,
                                                 runtime_version, functions_version, is_linux)

    SiteConfigPropertiesDictionary = cmd.get_models('SiteConfigPropertiesDictionary')

    site_config_dict = matched_runtime.site_config_dict if not flexconsumption_location \
        else SiteConfigPropertiesDictionary()
    app_settings_dict = matched_runtime.app_settings_dict if not flexconsumption_location else {}

    if is_storage_account_network_restricted(cmd.cli_ctx, resource_group_name, storage_account):
        if consumption_plan_location is not None:
            raise ValidationError('The Consumption plan does not support storage accounts with network restrictions. '
                                  'If you wish to use virtual networks, please create your app on a different hosting '
                                  'plan.')

        if not vnet and not configure_networking_later:
            raise ValidationError('The storage account you selected "{}" has networking restrictions. No virtual '
                                  'networking was configured so your app will not start. Please try again with '
                                  'virtual networking integration by adding the --vnet and --subnet flags. If '
                                  'you wish to do this at a later time, use the --configure-networking-later '
                                  'flag instead.'.format(storage_account))
        if vnet and configure_networking_later:
            raise ValidationError('The --vnet and --configure-networking-later flags are mutually exclusive.')
        functionapp_def.vnet_content_share_enabled = True

    con_string = _validate_and_get_connection_string(cmd.cli_ctx, resource_group_name, storage_account)

    if environment is not None:
        if docker_registry_server_url is not None:
            site_config.app_settings.append(
                NameValuePair(name='DOCKER_REGISTRY_SERVER_URL', value=docker_registry_server_url)
            )

        if (not registry_username and not registry_password and
                docker_registry_server_url and '.azurecr.io' in str(docker_registry_server_url)):
            logger.warning('No credential was provided to access Azure Container Registry. Trying to look up...')
            parsed = urlparse(docker_registry_server_url)
            registry_name = (parsed.netloc if parsed.scheme else parsed.path).split('.')[0]
            try:
                registry_username, registry_password = _get_acr_cred(cmd.cli_ctx, registry_name)
            except Exception as ex:  # pylint: disable=broad-except
                logger.warning("Retrieving credentials failed with an exception:'%s'", ex)  # consider throw if needed

        if registry_username is not None:
            site_config.app_settings.append(
                NameValuePair(name='DOCKER_REGISTRY_SERVER_USERNAME', value=registry_username)
            )
        if registry_password is not None:
            site_config.app_settings.append(
                NameValuePair(name='DOCKER_REGISTRY_SERVER_PASSWORD', value=registry_password)
            )

        app_settings_dict = {}
        matched_runtime.app_insights = True
    elif is_linux:
        functionapp_def.kind = 'functionapp,linux'
        functionapp_def.reserved = True
        is_consumption = consumption_plan_location is not None or flexconsumption_location is not None
        if not is_consumption:
            site_config.app_settings.append(NameValuePair(name='MACHINEKEY_DecryptionKey',
                                                          value=str(hexlify(urandom(32)).decode()).upper()))
            if image:
                functionapp_def.kind = 'functionapp,linux,container'
                site_config.app_settings.append(NameValuePair(name='DOCKER_CUSTOM_IMAGE_NAME',
                                                              value=image))
                site_config.app_settings.append(NameValuePair(name='FUNCTION_APP_EDIT_MODE', value='readOnly'))
                site_config.app_settings.append(NameValuePair(name='WEBSITES_ENABLE_APP_SERVICE_STORAGE',
                                                              value='false'))
                site_config.linux_fx_version = _format_fx_version(image)

                # clear all runtime specific configs and settings
                site_config_dict.use32_bit_worker_process = False
                app_settings_dict = {}

                # ensure that app insights is created if not disabled
                matched_runtime.app_insights = True
            else:
                site_config.app_settings.append(NameValuePair(name='WEBSITES_ENABLE_APP_SERVICE_STORAGE',
                                                              value='true'))
    else:
        functionapp_def.kind = 'functionapp'

    if site_config_dict.additional_properties:
        for prop, value in site_config_dict.additional_properties.items():
            snake_case_prop = _convert_camel_to_snake_case(prop)
            setattr(site_config, snake_case_prop, value)

    # set site configs
    for prop, value in site_config_dict.as_dict().items():
        snake_case_prop = _convert_camel_to_snake_case(prop)
        setattr(site_config, snake_case_prop, value)

    if environment is not None:
        functionapp_def.kind = 'functionapp,linux,container,azurecontainerapps'
        functionapp_def.reserved = None
        functionapp_def.name = name
        functionapp_def.https_only = None
        functionapp_def.scm_site_also_stopped = None
        functionapp_def.hyper_v = None
        functionapp_def.is_xenon = None
        functionapp_def.type = 'Microsoft.Web/sites'

        # validate cpu and memory parameters.
        _validate_cpu_momory_functionapp(cpu, memory)

        if workload_profile_name is not None:
            functionapp_def.workload_profile_name = workload_profile_name

        if cpu is not None and memory is not None:
            functionapp_def.resource_config = ResourceConfig()
            functionapp_def.resource_config.cpu = cpu
            functionapp_def.resource_config.memory = memory

        site_config.net_framework_version = None
        site_config.java_version = None
        site_config.use32_bit_worker_process = None
        site_config.power_shell_version = None
        site_config.linux_fx_version = _format_fx_version(image)
        site_config.http20_enabled = None
        site_config.local_my_sql_enabled = None
        if min_replicas is not None:
            site_config.minimum_elastic_instance_count = min_replicas
        if max_replicas is not None:
            site_config.function_app_scale_limit = max_replicas

        if enable_dapr:
            logger.warning("Please note while using Dapr Extension for Azure Functions, app port is "
                           "mandatory when using Dapr triggers and should be empty when using only Dapr bindings.")
            dapr_enable_api_logging = dapr_enable_api_logging == "true"
            dapr_config = DaprConfig()
            dapr_config.enabled = True
            dapr_config.app_id = dapr_app_id
            dapr_config.app_port = dapr_app_port
            dapr_config.http_max_request_size = dapr_http_max_request_size or 4
            dapr_config.http_read_buffer_size = dapr_http_read_buffer_size or 4
            dapr_config.log_level = dapr_log_level
            dapr_config.enable_api_logging = dapr_enable_api_logging
            functionapp_def.dapr_config = dapr_config

        managed_environment = get_managed_environment(cmd, resource_group_name, environment)
        location = managed_environment.location
        functionapp_def.location = location

        functionapp_def.managed_environment_id = managed_environment.id

    # adding app settings
    for app_setting, value in app_settings_dict.items():
        site_config.app_settings.append(NameValuePair(name=app_setting, value=value))

    if flexconsumption_location is None:
        site_config.app_settings.append(NameValuePair(name='FUNCTIONS_EXTENSION_VERSION',
                                                      value=_get_extension_version_functionapp(functions_version)))
    site_config.app_settings.append(NameValuePair(name='AzureWebJobsStorage', value=con_string))

    # If plan is not flex, consumption or elastic premium, we need to set always on
    if (flexconsumption_location is None and consumption_plan_location is None and plan_info is not None and
            not is_plan_elastic_premium(cmd, plan_info)):
        site_config.always_on = True

    # If plan is elastic premium or consumption, we need these app settings
    if (plan_info is not None and is_plan_elastic_premium(cmd, plan_info)) or consumption_plan_location is not None:
        site_config.app_settings.append(NameValuePair(name='WEBSITE_CONTENTAZUREFILECONNECTIONSTRING',
                                                      value=con_string))
        content_share_name = _get_content_share_name(name)
        site_config.app_settings.append(NameValuePair(name='WEBSITE_CONTENTSHARE', value=content_share_name))
        if is_storage_account_network_restricted(cmd.cli_ctx, resource_group_name, storage_account):
            create_file_share(cmd.cli_ctx, resource_group_name, storage_account, content_share_name)

    create_app_insights = False

    if app_insights_key is not None:
        site_config.app_settings.append(NameValuePair(name='APPINSIGHTS_INSTRUMENTATIONKEY',
                                                      value=app_insights_key))
    elif app_insights is not None:
        app_insights_conn_string = get_app_insights_connection_string(cmd.cli_ctx, resource_group_name, app_insights)
        site_config.app_settings.append(NameValuePair(name='APPLICATIONINSIGHTS_CONNECTION_STRING',
                                                      value=app_insights_conn_string))
    elif flexconsumption_location is None and (disable_app_insights or not matched_runtime.app_insights):
        # set up dashboard if no app insights
        site_config.app_settings.append(NameValuePair(name='AzureWebJobsDashboard', value=con_string))
    elif not disable_app_insights and matched_runtime.app_insights:
        create_app_insights = True

    if flexconsumption_location is not None:
        if zone_redundant:
            zone_redundant_locations = list_flexconsumption_zone_redundant_locations(cmd)
            zone_redundant_location = next((loc for loc in zone_redundant_locations
                                            if loc['name'].lower() == flexconsumption_location.lower()), None)
            if zone_redundant_location is None:
                raise ValidationError("The specified location '{0}' "
                                      "doesn't support zone redundancy in Flex Consumption. "
                                      "Use: az functionapp list-flexconsumption-locations --zone-redundant "
                                      "for the list of locations that support zone redundancy."
                                      .format(flexconsumption_location))

        site_config.net_framework_version = None
        functionapp_def.reserved = None
        functionapp_def.is_xenon = None

        try:
            plan_name = generatePlanName(resource_group_name)
            plan_info = create_flex_app_service_plan(
                cmd, resource_group_name, plan_name, flexconsumption_location, zone_redundant)
            functionapp_def.server_farm_id = plan_info.id
            functionapp_def.location = flexconsumption_location

            if not deployment_storage_name:
                deployment_storage_name = storage_account
            deployment_storage = _validate_and_get_deployment_storage(cmd.cli_ctx, resource_group_name,
                                                                      deployment_storage_name)

            deployment_storage_container = _get_or_create_deployment_storage_container(
                cmd, resource_group_name, name, deployment_storage_name, deployment_storage_container_name)
            if deployment_storage_container_name is None:
                is_storage_container_created = True
            deployment_storage_container_name = deployment_storage_container.name

            endpoints = deployment_storage.primary_endpoints
            deployment_config_storage_value = getattr(endpoints, 'blob') + deployment_storage_container_name

            deployment_storage_auth_type = deployment_storage_auth_type or 'StorageAccountConnectionString'

            if deployment_storage_auth_value and deployment_storage_auth_type == 'SystemAssignedIdentity':
                raise ArgumentUsageError(
                    '--deployment-storage-auth-value is only a valid input when '
                    '--deployment-storage-auth-type is set to UserAssignedIdentity or StorageAccountConnectionString. '
                    'Please try again with --deployment-storage-auth-type set to UserAssignedIdentity or '
                    'StorageAccountConnectionString.'
                )

            function_app_config = {}
            deployment_storage_auth_config = {
                "type": deployment_storage_auth_type
            }
            function_app_config["deployment"] = {
                "storage": {
                    "type": "blobContainer",
                    "value": deployment_config_storage_value,
                    "authentication": deployment_storage_auth_config
                }
            }

            if deployment_storage_auth_type == 'UserAssignedIdentity':
                deployment_storage_user_assigned_identity = _get_or_create_user_assigned_identity(
                    cmd,
                    resource_group_name,
                    name,
                    deployment_storage_auth_value,
                    flexconsumption_location)
                if deployment_storage_auth_value is None:
                    is_user_assigned_identity_created = True
                deployment_storage_auth_value = deployment_storage_user_assigned_identity.id
                deployment_storage_auth_config["userAssignedIdentityResourceId"] = deployment_storage_auth_value
            elif deployment_storage_auth_type == 'StorageAccountConnectionString':
                deployment_storage_conn_string = _get_storage_connection_string(cmd.cli_ctx, deployment_storage)
                conn_string_app_setting = deployment_storage_auth_value or 'DEPLOYMENT_STORAGE_CONNECTION_STRING'
                site_config.app_settings.append(NameValuePair(name=conn_string_app_setting,
                                                              value=deployment_storage_conn_string))
                deployment_storage_auth_value = conn_string_app_setting
                deployment_storage_auth_config["storageAccountConnectionStringName"] = deployment_storage_auth_value

            flex_sku = matched_runtime.sku
            runtime = flex_sku['functionAppConfigProperties']['runtime']['name']
            version = flex_sku['functionAppConfigProperties']['runtime']['version']
            runtime_config = {
                "name": runtime,
                "version": version
            }
            function_app_config["runtime"] = runtime_config
            always_ready_dict = _parse_key_value_pairs(always_ready_instances)
            always_ready_config = []

            for key, value in always_ready_dict.items():
                always_ready_config.append(
                    {
                        "name": key,
                        "instanceCount": max(0, validate_and_convert_to_int(key, value))
                    }
                )

            default_instance_memory = [x for x in flex_sku['instanceMemoryMB'] if x['isDefault'] is True][0]

            function_app_config["scaleAndConcurrency"] = {
                "maximumInstanceCount": maximum_instance_count or flex_sku['maximumInstanceCount']['defaultValue'],
                "instanceMemoryMB": instance_memory or default_instance_memory['size'],
                "alwaysReady": always_ready_config
            }

            functionapp_def.enable_additional_properties_sending()
            existing_properties = functionapp_def.serialize()["properties"]
            functionapp_def.additional_properties["properties"] = existing_properties
            functionapp_def.additional_properties["properties"]["functionAppConfig"] = function_app_config
            functionapp_def.additional_properties["properties"]["sku"] = "FlexConsumption"
            poller = client.web_apps.begin_create_or_update(resource_group_name, name, functionapp_def,
                                                            api_version='2023-12-01')
            functionapp = LongRunningOperation(cmd.cli_ctx)(poller)
        except Exception as ex:  # pylint: disable=broad-except
            client.app_service_plans.delete(resource_group_name, plan_name)
            if is_storage_container_created:
                delete_storage_container(cmd, resource_group_name, deployment_storage_name,
                                         deployment_storage_container_name)
            if is_user_assigned_identity_created:
                delete_user_assigned_identity(cmd, resource_group_name, deployment_storage_user_assigned_identity.name)
            raise ex
    else:
        poller = client.web_apps.begin_create_or_update(resource_group_name, name, functionapp_def)
        functionapp = LongRunningOperation(cmd.cli_ctx)(poller)

    if environment is not None:
        functionapp = client.web_apps.get(resource_group_name, name)

    if consumption_plan_location and is_linux:
        logger.warning("Your Linux function app '%s', that uses a consumption plan has been successfully "
                       "created but is not active until content is published using "
                       "Azure Portal or the Functions Core Tools.", name)
    else:
        _set_remote_or_local_git(cmd, functionapp, resource_group_name, name, deployment_source_url,
                                 deployment_source_branch, deployment_local_git)

    if create_app_insights:
        try:
            try_create_workspace_based_application_insights(cmd, functionapp, workspace)
            if should_enable_distributed_tracing(consumption_plan_location,
                                                 flexconsumption_location,
                                                 matched_runtime,
                                                 image):
                update_app_settings(cmd, functionapp.resource_group, functionapp.name,
                                    ["APPLICATIONINSIGHTS_ENABLE_AGENT=true"])

        except Exception:  # pylint: disable=broad-except
            logger.warning('Error while trying to create and configure an Application Insights for the Function App. '
                           'Please use the Azure Portal to create and configure the Application Insights, if needed.')
            if flexconsumption_location is None:
                update_app_settings(cmd, functionapp.resource_group, functionapp.name,
                                    ['AzureWebJobsDashboard={}'.format(con_string)])

    if image and environment is None:
        update_container_settings_functionapp(cmd, resource_group_name, name, docker_registry_server_url,
                                              image, registry_username,
                                              registry_password)

    if flexconsumption_location is not None:
        if deployment_storage_auth_type == 'UserAssignedIdentity':
            assign_identity(cmd, resource_group_name, name, [deployment_storage_auth_value])
            if not _has_deployment_storage_role_assignment_on_resource(
                    cmd.cli_ctx,
                    deployment_storage,
                    deployment_storage_user_assigned_identity.principal_id):
                _assign_deployment_storage_managed_identity_role(
                    cmd.cli_ctx,
                    deployment_storage,
                    deployment_storage_user_assigned_identity.principal_id)
            else:
                logger.warning("User assigned identity '%s' already has the role assignment on "
                               "the storage account '%s'",
                               deployment_storage_user_assigned_identity.principal_id, deployment_storage_name)

        elif deployment_storage_auth_type == 'SystemAssignedIdentity':
            assign_identity(cmd, resource_group_name, name, ['[system]'], 'Storage Blob Data Contributor',
                            None, deployment_storage.id)

    if assign_identities is not None:
        identity = assign_identity(cmd, resource_group_name, name, assign_identities,
                                   role, None, scope)
        functionapp.identity = identity

    if flexconsumption_location is not None:
        return get_raw_functionapp(cmd.cli_ctx, resource_group_name, name)

    return functionapp


def _validate_cpu_momory_functionapp(cpu=None, memory=None):
    # validate either both cpu and memory are provided or none is provided. throw error otherwise
    if cpu is None and memory is None:
        return

    if cpu is not None and memory is None:
        raise ArgumentUsageError("The --memory argument is required with --cpu. Please provide both or none.")

    if cpu is None and memory is not None:
        raise ArgumentUsageError("The --cpu argument is required with --memory. Please provide both or none.")

    # validate that memory is number and ends with Gi
    if not memory.lower().endswith("gi"):
        raise ValidationError("The --memory argument should end with Gi. Please provide a correct value. e.g. 4.0Gi.")

    try:
        float(memory[:-2])
    except ValueError:
        raise ValidationError("The --memory argument is not valid. Please provide a correct value. e.g. 4.0Gi.")

    return


def create_file_share(cli_ctx, resource_group_name, storage_account, share_name):

    storage_client = get_mgmt_service_client(cli_ctx, StorageManagementClient)
    from azure.mgmt.storage.models import FileShare

    file_share = FileShare()

    return storage_client.file_shares.create(resource_group_name, storage_account, share_name, file_share=file_share)


def _get_extension_version_functionapp(functions_version):
    if functions_version is not None:
        return '~{}'.format(functions_version)
    return '~4'


def _get_app_setting_set_functionapp(site_config, app_setting):
    return list(filter(lambda x: x.name == app_setting, site_config.app_settings))


def _convert_camel_to_snake_case(text):
    return reduce(lambda x, y: x + ('_' if y.isupper() else '') + y, text).lower()


def _get_runtime_version_functionapp(version_string, is_linux):
    windows_match = re.fullmatch(FUNCTIONS_WINDOWS_RUNTIME_VERSION_REGEX, version_string)
    if windows_match:
        return float(windows_match.group(1))

    linux_match = re.fullmatch(FUNCTIONS_LINUX_RUNTIME_VERSION_REGEX, version_string)
    if linux_match:
        return float(linux_match.group(1))

    try:
        return float(version_string)
    except ValueError:
        return 0


def generatePlanName(resource_group_name):
    suffix = "-" + str(uuid.uuid4())[:4]
    alphanumeric_resource_group_name = re.sub(r"[^a-zA-Z0-9]", '', resource_group_name)
    first_part = 'ASP-{}'.format(alphanumeric_resource_group_name)[:35]
    return '{}{}'.format(first_part, suffix)


def _get_content_share_name(app_name):
    # content share name should be up to 63 characters long, lowercase letter and digits, and random
    # so take the first 50 characters of the app name and add the last 12 digits of a random uuid
    share_name = app_name[0:50]
    suffix = str(uuid.uuid4()).rsplit('-', maxsplit=1)[-1]
    return share_name.lower() + suffix


def try_create_workspace_based_application_insights(cmd, functionapp, workspace_name):
    creation_failed_warn = 'Unable to create the Application Insights for the Function App. ' \
                           'Please use the Azure Portal to manually create and configure the Application Insights, ' \
                           'if needed.'

    ai_resource_group_name = functionapp.resource_group
    ai_name = functionapp.name
    ai_location = _normalize_location(cmd, functionapp.location)

    workspace = get_workspace(cmd, workspace_name)

    if workspace is None:
        default_resource_group = get_or_create_default_resource_group(cmd, ai_location)
        workspace = get_or_create_default_workspace(cmd, ai_location, default_resource_group.name)

    app_insights_client = get_mgmt_service_client(
        cmd.cli_ctx,
        ApplicationInsightsManagementClient,
        api_version='2020-02-02-preview'
    )

    ai_properties = {
        "name": ai_name,
        "location": ai_location,
        "kind": "web",
        "properties": {
            "Application_Type": "web",
            "WorkspaceResourceId": workspace.id
        }
    }

    appinsights = app_insights_client.components.create_or_update(ai_resource_group_name, ai_name, ai_properties)
    if appinsights is None or appinsights.connection_string is None:
        logger.warning(creation_failed_warn)
        return

    # We make this success message as a warning to no interfere with regular JSON output in stdout
    logger.warning('Application Insights \"%s\" was created for this Function App. '
                   'You can visit https://portal.azure.com/#resource%s/overview to view your '
                   'Application Insights component', appinsights.name, appinsights.id)

    update_app_settings(cmd, functionapp.resource_group, functionapp.name,
                        ['APPLICATIONINSIGHTS_CONNECTION_STRING={}'.format(appinsights.connection_string)])


def try_create_application_insights(cmd, functionapp):
    creation_failed_warn = 'Unable to create the Application Insights for the Function App. ' \
                           'Please use the Azure Portal to manually create and configure the Application Insights, ' \
                           'if needed.'

    ai_resource_group_name = functionapp.resource_group
    ai_name = functionapp.name
    ai_location = functionapp.location

    app_insights_client = get_mgmt_service_client(cmd.cli_ctx, ApplicationInsightsManagementClient)
    ai_properties = {
        "name": ai_name,
        "location": ai_location,
        "kind": "web",
        "properties": {
            "Application_Type": "web"
        }
    }
    appinsights = app_insights_client.components.create_or_update(ai_resource_group_name, ai_name, ai_properties)
    if appinsights is None or appinsights.instrumentation_key is None:
        logger.warning(creation_failed_warn)
        return

    # We make this success message as a warning to no interfere with regular JSON output in stdout
    logger.warning('Application Insights \"%s\" was created for this Function App. '
                   'You can visit https://portal.azure.com/#resource%s/overview to view your '
                   'Application Insights component', appinsights.name, appinsights.id)

    if not is_centauri_functionapp(cmd, ai_resource_group_name, ai_name):
        update_app_settings(cmd, functionapp.resource_group, functionapp.name,
                            ['APPINSIGHTS_INSTRUMENTATIONKEY={}'.format(appinsights.instrumentation_key)])
    else:
        update_app_settings(cmd, functionapp.resource_group, functionapp.name,
                            ['APPLICATIONINSIGHTS_CONNECTION_STRING={}'.format(appinsights.connection_string)])


def _set_remote_or_local_git(cmd, webapp, resource_group_name, name, deployment_source_url=None,
                             deployment_source_branch='master', deployment_local_git=None):
    if deployment_source_url:
        logger.warning("Linking to git repository '%s'", deployment_source_url)
        try:
            config_source_control(cmd, resource_group_name, name, deployment_source_url, 'git',
                                  deployment_source_branch, manual_integration=True)
        except Exception as ex:  # pylint: disable=broad-except
            ex = ex_handler_factory(no_throw=True)(ex)
            logger.warning("Link to git repository failed due to error '%s'", ex)

    if deployment_local_git:
        local_git_info = enable_local_git(cmd, resource_group_name, name)
        logger.warning("Local git is configured with url of '%s'", local_git_info['url'])
        setattr(webapp, 'deploymentLocalGitUrl', local_git_info['url'])


def _validate_and_get_deployment_storage(cli_ctx, resource_group_name, deployment_storage_name):
    sa_resource_group = resource_group_name

    if is_valid_resource_id(deployment_storage_name):
        sa_resource_group = parse_resource_id(deployment_storage_name)['resource_group']
        deployment_storage_name = parse_resource_id(deployment_storage_name)['name']

    storage_client = get_mgmt_service_client(cli_ctx, StorageManagementClient)
    storage_properties = storage_client.storage_accounts.get_properties(sa_resource_group, deployment_storage_name)

    endpoints = storage_properties.primary_endpoints
    sku = storage_properties.sku.name
    allowed_storage_types = ['Standard_GRS', 'Standard_RAGRS', 'Standard_LRS', 'Standard_ZRS', 'Premium_LRS',
                             'Standard_GZRS']

    if not getattr(endpoints, 'blob', None):
        raise CLIError("Deployment storage account '{}' has no 'blob' endpoint. It must have blob endpoints "
                       "enabled".format(deployment_storage_name))

    if sku not in allowed_storage_types:
        raise CLIError("Storage type {} is not allowed".format(sku))

    return storage_properties


def _normalize_functionapp_name(functionapp_name):
    return re.sub(r"[^a-zA-Z0-9]", '', functionapp_name).lower()


def delete_storage_container(cmd, resource_group_name, storage_name, container_name):
    storage_client = get_mgmt_service_client(cmd.cli_ctx, StorageManagementClient)

    sa_resource_group = resource_group_name

    if is_valid_resource_id(storage_name):
        sa_resource_group = parse_resource_id(storage_name)['resource_group']
        storage_name = parse_resource_id(storage_name)['name']

    storage_client.blob_containers.delete(sa_resource_group, storage_name, container_name)


def delete_user_assigned_identity(cmd, resource_group_name, identity_name):
    from azure.mgmt.msi import ManagedServiceIdentityClient
    msi_client = get_mgmt_service_client(cmd.cli_ctx, ManagedServiceIdentityClient)
    msi_client.user_assigned_identities.delete(resource_group_name, identity_name)


def _get_or_create_deployment_storage_container(cmd, resource_group_name, functionapp_name,
                                                deployment_storage_name, deployment_storage_container_name):
    sa_resource_group = resource_group_name

    if is_valid_resource_id(deployment_storage_name):
        sa_resource_group = parse_resource_id(deployment_storage_name)['resource_group']
        deployment_storage_name = parse_resource_id(deployment_storage_name)['name']

    storage_client = get_mgmt_service_client(cmd.cli_ctx, StorageManagementClient)
    if deployment_storage_container_name:
        storage_container = storage_client.blob_containers.get(sa_resource_group, deployment_storage_name,
                                                               deployment_storage_container_name)
    else:
        from random import randint
        deployment_storage_container_name = "app-package-{}-{:07}".format(
            _normalize_functionapp_name(functionapp_name)[:32], randint(0, 9999999))
        logger.warning("Creating deployment storage account container '%s' ...", deployment_storage_container_name)

        from azure.mgmt.storage.models import BlobContainer

        storage_container = storage_client.blob_containers.create(sa_resource_group,
                                                                  deployment_storage_name,
                                                                  deployment_storage_container_name,
                                                                  BlobContainer())

    return storage_container


def _validate_and_get_deployment_storage_container(cmd, resource_group_name, deployment_storage_name,
                                                   deployment_storage_container_name):
    storage_client = get_mgmt_service_client(cmd.cli_ctx, StorageManagementClient)
    return storage_client.blob_containers.get(resource_group_name, deployment_storage_name,
                                              deployment_storage_container_name)


def _get_or_create_user_assigned_identity(cmd, resource_group_name, functionapp_name, user_assigned_identity, location):
    from azure.mgmt.msi import ManagedServiceIdentityClient
    msi_client = get_mgmt_service_client(cmd.cli_ctx, ManagedServiceIdentityClient)
    if user_assigned_identity:
        if is_valid_resource_id(user_assigned_identity):
            parse_result = parse_resource_id(user_assigned_identity)
            user_assigned_identity = parse_result['name']
            resource_group_name = parse_result['resource_group']
        identity = msi_client.user_assigned_identities.get(resource_group_name=resource_group_name,
                                                           resource_name=user_assigned_identity)
    else:
        from random import randint
        user_assigned_identity_name = "identity{}{:04}".format(
            _normalize_functionapp_name(functionapp_name)[:10], randint(0, 9999))
        logger.warning("Creating user assigned managed identity '%s' ...", user_assigned_identity_name)

        from azure.mgmt.msi.models import Identity

        identity = msi_client.user_assigned_identities.create_or_update(resource_group_name,
                                                                        user_assigned_identity_name,
                                                                        Identity(location=location))

    return identity


def _get_storage_connection_string(cli_ctx, deployment_storage_account):
    resource_group_name = parse_resource_id(deployment_storage_account.id)['resource_group']
    deployment_storage_name = deployment_storage_account.name
    storage_client = get_mgmt_service_client(cli_ctx, StorageManagementClient)
    access_keys = storage_client.storage_accounts.list_keys(resource_group_name, deployment_storage_name)
    try:
        key = access_keys.keys[0].value
    except AttributeError:
        # Older API versions have a slightly different structure
        key = access_keys.key1

    endpoint_suffix = cli_ctx.cloud.suffixes.storage_endpoint
    connection_string = 'DefaultEndpointsProtocol={};EndpointSuffix={};AccountName={};AccountKey={}'.format(
        "https",
        endpoint_suffix,
        deployment_storage_name,
        key)

    return connection_string


def _assign_deployment_storage_managed_identity_role(cli_ctx, deployment_storage_account, principal_id):
    from azure.cli.core.commands.client_factory import get_subscription_id

    sub_id = get_subscription_id(cli_ctx)
    role_definition_id = "/subscriptions/{}/providers/Microsoft.Authorization/roleDefinitions/{}".format(
        sub_id, STORAGE_BLOB_DATA_CONTRIBUTOR_ROLE_ID)
    auth_client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_AUTHORIZATION)
    RoleAssignmentCreateParameters = get_sdk(cli_ctx, ResourceType.MGMT_AUTHORIZATION, 'RoleAssignmentCreateParameters',
                                             mod='models', operation_group='role_assignments')
    parameters = RoleAssignmentCreateParameters(role_definition_id=role_definition_id, principal_id=principal_id,
                                                principal_type='ServicePrincipal')
    auth_client.role_assignments.create(scope=deployment_storage_account.id,
                                        role_assignment_name=str(uuid.uuid4()), parameters=parameters)


def _has_deployment_storage_role_assignment_on_resource(cli_ctx, deployment_storage_account, principal_id):
    from azure.cli.core.commands.client_factory import get_subscription_id
    auth_client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_AUTHORIZATION)

    sub_id = get_subscription_id(cli_ctx)
    role_definition_id = "/subscriptions/{}/providers/Microsoft.Authorization/roleDefinitions/{}".format(
        sub_id, STORAGE_BLOB_DATA_CONTRIBUTOR_ROLE_ID)

    list_for_scope = auth_client.role_assignments.list_for_scope(deployment_storage_account.id)
    for assignment in list_for_scope:
        if assignment.role_definition_id.lower() == role_definition_id.lower() and \
                assignment.principal_id.lower() == principal_id.lower():
            return True

    return False


def _parse_key_value_pairs(key_value_list):
    key_value_list = key_value_list or []
    result = {}
    for kv in key_value_list:
        try:
            temp = shell_safe_json_parse(kv)
            if isinstance(temp, list):
                for t in temp:
                    result[t['name']] = t['value']
            else:
                result.update(temp)
        except CLIError:
            name, value = kv.split('=', 1)
            result[name] = value
            result.update(result)
    return result


def _validate_and_get_connection_string(cli_ctx, resource_group_name, storage_account):
    sa_resource_group = resource_group_name
    if is_valid_resource_id(storage_account):
        sa_resource_group = parse_resource_id(storage_account)['resource_group']
        storage_account = parse_resource_id(storage_account)['name']
    storage_client = get_mgmt_service_client(cli_ctx, StorageManagementClient)
    storage_properties = storage_client.storage_accounts.get_properties(sa_resource_group,
                                                                        storage_account)
    error_message = ''
    endpoints = storage_properties.primary_endpoints
    sku = storage_properties.sku.name
    allowed_storage_types = ['Standard_GRS', 'Standard_RAGRS', 'Standard_LRS', 'Standard_ZRS', 'Premium_LRS', 'Standard_GZRS']  # pylint: disable=line-too-long

    for e in ['blob', 'queue', 'table']:
        if not getattr(endpoints, e, None):
            error_message = "Storage account '{}' has no '{}' endpoint. It must have table, queue, and blob endpoints all enabled".format(storage_account, e)   # pylint: disable=line-too-long
    if sku not in allowed_storage_types:
        error_message += 'Storage type {} is not allowed'.format(sku)

    if error_message:
        raise CLIError(error_message)

    obj = storage_client.storage_accounts.list_keys(sa_resource_group, storage_account)  # pylint: disable=no-member
    try:
        keys = [obj.keys[0].value, obj.keys[1].value]  # pylint: disable=no-member
    except AttributeError:
        # Older API versions have a slightly different structure
        keys = [obj.key1, obj.key2]  # pylint: disable=no-member

    endpoint_suffix = cli_ctx.cloud.suffixes.storage_endpoint
    connection_string = 'DefaultEndpointsProtocol={};EndpointSuffix={};AccountName={};AccountKey={}'.format(
        "https",
        endpoint_suffix,
        storage_account,
        keys[0])  # pylint: disable=no-member

    return connection_string


def is_storage_account_network_restricted(cli_ctx, resource_group_name, storage_account):
    sa_resource_group = resource_group_name
    if is_valid_resource_id(storage_account):
        sa_resource_group = parse_resource_id(storage_account)['resource_group']
        storage_account = parse_resource_id(storage_account)['name']
    storage_client = get_mgmt_service_client(cli_ctx, StorageManagementClient)
    storage_properties = storage_client.storage_accounts.get_properties(sa_resource_group,
                                                                        storage_account)
    return storage_properties.public_network_access == 'Disabled' or \
        (storage_properties.public_network_access == 'Enabled' and
         storage_properties.network_rule_set.default_action == 'Deny')


def list_consumption_locations(cmd):
    client = web_client_factory(cmd.cli_ctx)
    regions = client.list_geo_regions(sku='Dynamic')
    return [{'name': x.name.lower().replace(' ', '')} for x in regions]


def get_subscription_locations(cli_ctx):
    from azure.cli.core.commands.client_factory import get_subscription_service_client
    subscription_client, subscription_id = get_subscription_service_client(cli_ctx)
    result = list(subscription_client.subscriptions.list_locations(subscription_id))
    return [item.name for item in result]


def list_flexconsumption_locations(cmd, zone_redundant=False, show_details=False, runtime=None):
    client = web_client_factory(cmd.cli_ctx)

    if runtime and not show_details:
        raise ArgumentUsageError(
            '--runtime is only valid with --details parameter. '
            'Please try again without the --details parameter.')

    regions = client.list_geo_regions(sku="FlexConsumption")

    if zone_redundant:
        regions = [x for x in regions if "FCZONEREDUNDANCY" in x.org_domain]

    regions = [x.name.lower().replace(' ', '') for x in regions]
    sub_regions_list = get_subscription_locations(cmd.cli_ctx)
    regions = [x for x in regions if x in sub_regions_list]

    if not show_details:
        return [{'name': x} for x in regions]

    return [{'name': x, 'details': list_flex_function_app_all_runtimes(cmd, x, runtime)} for x in regions]


def list_flex_function_app_all_runtimes(cmd, location, runtime=None):
    runtimes = ["dotnet-isolated", "node", "python", "java", "powershell"]
    if runtime:
        runtimes = [runtime]

    return [{'runtime': x,
             'runtime-details': get_runtime_details_ignore_error(cmd, location, x)}
            for x in runtimes]


def get_runtime_details_ignore_error(cmd, location, runtime):
    try:
        runtime_helper = _FlexFunctionAppStackRuntimeHelper(cmd, location, runtime)
        return runtime_helper.stacks
    except Exception:  # pylint: disable=broad-except
        return None


def list_flexconsumption_zone_redundant_locations(cmd):
    client = web_client_factory(cmd.cli_ctx)
    regions = client.list_geo_regions(sku="FlexConsumption")
    regions = [x for x in regions if "FCZONEREDUNDANCY" in x.org_domain]
    return [{'name': x.name.lower().replace(' ', '')} for x in regions]


def list_locations(cmd, sku, linux_workers_enabled=None, hyperv_workers_enabled=None, managed_instance_enabled=None):
    web_client = web_client_factory(cmd.cli_ctx)
    full_sku = get_sku_tier(sku)

    if managed_instance_enabled:
        # managed_instance_enabled needs to be specially handled due to requiring version 2025-03-01
        # and due to additional validation needed for SKU
        web_client_geo_regions = _list_managed_instance_locations(cmd, full_sku)
    else:
        web_client_geo_regions = web_client.list_geo_regions(sku=full_sku,
                                                             linux_workers_enabled=linux_workers_enabled,
                                                             xenon_workers_enabled=hyperv_workers_enabled)

    providers_client = providers_client_factory(cmd.cli_ctx)
    providers_client_locations_list = getattr(providers_client.get('Microsoft.Web'), 'resource_types', [])
    for resource_type in providers_client_locations_list:
        if resource_type.resource_type == 'sites':
            providers_client_locations_list = resource_type.locations
            break

    return [geo_region for geo_region in web_client_geo_regions if geo_region.name in providers_client_locations_list]


def _list_managed_instance_locations(cmd, sku_tier):
    from types import SimpleNamespace

    if not is_sku_tier_enabled_for_managed_instance(sku_tier):
        return []

    # SKU is validated separately above and not passed into API call
    # due to how the API handles SKU for managed instance
    list_locations_cmd = AppServiceListLocations(cli_ctx=cmd.cli_ctx)
    locations = list_locations_cmd(command_args={
        'custom_mode_workers_enabled': True
    })

    return [SimpleNamespace(**location) for location in locations]


def _check_zip_deployment_status(cmd, rg_name, name, deployment_status_url, slot, timeout=None):
    import requests
    from azure.cli.core.util import should_disable_connection_verify

    headers = get_scm_site_headers(cmd.cli_ctx, name, rg_name, slot)
    total_trials = (int(timeout) // 2) if timeout else 450
    num_trials = 0
    while num_trials < total_trials:
        time.sleep(2)
        response = requests.get(deployment_status_url, headers=headers,
                                verify=not should_disable_connection_verify())
        try:
            res_dict = response.json()
        except json.decoder.JSONDecodeError:
            logger.warning("Deployment status endpoint %s returns malformed data. Retrying...", deployment_status_url)
            res_dict = {}
        finally:
            num_trials = num_trials + 1

        if res_dict.get('status', 0) == 3:
            _configure_default_logging(cmd, rg_name, name)
            raise CLIError("Zip deployment failed. {}. Please run the command az webapp log deployment show "
                           "-n {} -g {}".format(res_dict, name, rg_name))
        if res_dict.get('status', 0) == 4:
            break
        if 'progress' in res_dict:
            logger.info(res_dict['progress'])  # show only in debug mode, customers seem to find this confusing
    # if the deployment is taking longer than expected
    if res_dict.get('status', 0) != 4:
        _configure_default_logging(cmd, rg_name, name)
        raise CLIError("""Timeout reached by the command, however, the deployment operation
                       is still on-going. Navigate to your scm site to check the deployment status""")
    return res_dict


def _get_latest_deployment_id(cmd, rg_name, name, deployment_status_url, slot):
    import requests
    from azure.cli.core.util import should_disable_connection_verify

    headers = get_scm_site_headers(cmd.cli_ctx, name, rg_name, slot)
    total_trials = 30
    num_trials = 0
    while num_trials < total_trials:
        time.sleep(2)
        try:
            response = requests.get(deployment_status_url, headers=headers,
                                    verify=not should_disable_connection_verify())
            try:
                res_dict = response.json()
            except Exception as ex:  # pylint: disable=broad-except
                logger.warning("Deployment status endpoint %s returned malformed data. Exception: %s "
                               "\nRetrying...", deployment_status_url, ex)
                return None
            finally:
                num_trials = num_trials + 1
            if 'id' in res_dict and 'temp' not in res_dict['id']:
                return res_dict['id']
        # catch all errors
        except Exception as ex:  # pylint: disable=broad-except
            logger.warning("Deployment status endpoint %s returned error: %s.", deployment_status_url, ex)
            break
    return None


def _check_runtimestatus_with_deploymentstatusapi(cmd, resource_group_name, name, slot,
                                                  deployment_status_url, is_async, timeout):
    response_body = None
    logger.warning('Polling the status of %s deployment. Start Time: %s UTC',
                   "async" if is_async else "sync",
                   datetime.datetime.now(datetime.timezone.utc))
    # verify if the app is a linux web app
    client = web_client_factory(cmd.cli_ctx)
    app = client.web_apps.get(resource_group_name, name)
    app_is_linux_webapp = is_linux_webapp(app)
    # TODO: enable tracking for slot deployments again once site warmup is fixed for slots
    if not app_is_linux_webapp or slot is not None:
        response_body = _check_zip_deployment_status(cmd, resource_group_name, name, deployment_status_url,
                                                     slot, timeout)
    else:
        # get the deployment id
        # once deploymentstatus/latest is available, we can use it to track the deployment
        deployment_id = _get_latest_deployment_id(cmd, resource_group_name,
                                                  name, deployment_status_url, slot)
        if deployment_id is None:
            logger.warning("Failed to enable tracking runtime status for this deployment. "
                           "Resuming without tracking status.")
            response_body = _check_zip_deployment_status(cmd, resource_group_name, name, deployment_status_url,
                                                         slot, timeout)
        else:
            deploymentstatisapi_url = _build_deploymentstatus_url(cmd, resource_group_name,
                                                                  name, slot, deployment_id)
            response_body = _poll_deployment_runtime_status(cmd, resource_group_name, name, slot,
                                                            deploymentstatisapi_url, deployment_id, timeout)
            # incase we are unable to fetch response from deploymentstatus API
            # fallback to polling kudu for deployment status
            if response_body is None:
                logger.warning("Failed to track the runtime status for this deployment. "
                               "Resuming without tracking status.")
                response_body = _check_zip_deployment_status(cmd, resource_group_name, name, deployment_status_url,
                                                             slot, timeout)
    return response_body


# pylint: disable=too-many-branches
def _poll_deployment_runtime_status(cmd, resource_group_name, webapp_name, slot, deploymentstatusapi_url,
                                    deployment_id, timeout=None):
    max_time_sec = int(timeout) if timeout else 1000
    start_time = time.time()
    time_elapsed = 0
    deployment_status = None
    response_body = None
    while time_elapsed < max_time_sec:
        try:
            response_body = send_raw_request(cmd.cli_ctx, "GET", deploymentstatusapi_url).json()
        except Exception as ex:  # pylint: disable=broad-except
            # we might get a 404 if a new deployment has started and this deployment_id is no longer latest
            logger.warning("Deployment status endpoint %s returned error: %s.", deploymentstatusapi_url, ex)
            break
        deployment_properties = response_body.get('properties')
        deployment_status = deployment_properties.get('status')
        time_elapsed = int(time.time() - start_time)
        status = RUNTIME_STATUS_TEXT_MAP.get(deployment_status)
        status = deployment_status if status is None else status
        logger.warning("Status: %s Time: %s(s)", status, time_elapsed)
        if deployment_status == "RuntimeStarting":
            logger.info("InprogressInstances: %s, SuccessfulInstances: %s",
                        deployment_properties.get('numberOfInstancesInProgress'),
                        deployment_properties.get('numberOfInstancesSuccessful'))
        if deployment_status == "RuntimeSuccessful":
            break
        if deployment_status == "RuntimeFailed":
            error_text = ""
            total_num_instances = int(deployment_properties.get('numberOfInstancesInProgress')) + \
                int(deployment_properties.get('numberOfInstancesSuccessful')) + \
                int(deployment_properties.get('numberOfInstancesFailed'))
            site_started_partially = int(deployment_properties.get('numberOfInstancesSuccessful')) > 0
            if site_started_partially:
                error_text += "Site started with errors: {}/{} instances failed to start successfully\n".format(
                    deployment_properties.get('numberOfInstancesFailed'),
                    total_num_instances)
            else:
                error_text += "Deployment failed because the site failed to start within 10 mins.\n"
                if int(total_num_instances) > 0:
                    error_text += "InprogressInstances: {}, SuccessfulInstances: {}, FailedInstances: {}\n".format(
                        deployment_properties.get('numberOfInstancesInProgress'),
                        deployment_properties.get('numberOfInstancesSuccessful'),
                        deployment_properties.get('numberOfInstancesFailed'))
            errors = deployment_properties.get('errors')
            if errors is not None and len(errors) > 0:
                error_extended_code = errors[0]['extendedCode']
                error_message = errors[0]['message']
                if error_message is not None:
                    error_text += "Error: {}\n".format(error_message)
                else:
                    error_text += "Extended ErrorCode: {}\n".format(error_extended_code)
            failure_logs = deployment_properties.get('failedInstancesLogs')
            if failure_logs is not None and len(failure_logs) > 0:
                failure_logs = failure_logs[0]
            error_text += "Please check the runtime logs for more info: {}\n".format(failure_logs)
            if site_started_partially:
                logger.warning(error_text)
                break
            raise CLIError(error_text)
        if deployment_status == "BuildFailed":
            error_text = "Deployment failed because the build process failed\n"
            errors = deployment_properties.get('errors')
            if errors is not None and len(errors) > 0:
                error_extended_code = errors[0]['extendedCode']
                error_message = errors[0]['message']
                if error_message is not None:
                    error_text += "Error: {}\n".format(error_message)
                else:
                    error_text += "Extended ErrorCode: {}\n".format(error_extended_code)
            deployment_logs = deployment_properties.get('failedInstancesLogs')
            if deployment_logs is None or len(deployment_logs) == 0:
                scm_url = _get_scm_url(cmd, resource_group_name, webapp_name, slot)
                deployment_logs = scm_url + f"/api/deployments/{deployment_id}/log"
            else:
                deployment_logs = deployment_logs[0]
            error_text += "Please check the build logs for more info: {}\n".format(deployment_logs)
            raise CLIError(error_text)
        time.sleep(15)

    if time_elapsed >= max_time_sec and deployment_status != "RuntimeSuccessful":
        scm_url = _get_scm_url(cmd, resource_group_name, webapp_name, slot)
        if deployment_status == "BuildInProgress":
            deployments_log_url = scm_url + f"/api/deployments/{deployment_id}/log"
            raise CLIError("Timeout reached while build was still in progress. "
                           "Navigate to {} to check the build logs for your app.".format(
                               deployments_log_url))
        # For any other status, redirect user to /deployments/<id> endpoint
        deployments_url = scm_url + f"/api/deployments/{deployment_id}"
        error_text = ("Timeout reached while tracking deployment status, however, the deployment"
                      " operation is still on-going. Navigate to {} to check the deployment status"
                      " of your app. \n").format(deployments_url)
        total_num_instances = int(deployment_properties.get('numberOfInstancesInProgress')) + \
            int(deployment_properties.get('numberOfInstancesSuccessful')) + \
            int(deployment_properties.get('numberOfInstancesFailed'))
        if total_num_instances > 0:
            error_text += "InprogressInstances: {}, SuccessfulInstances: {}, FailedInstances: {}".format(
                          deployment_properties.get('numberOfInstancesInProgress'),
                          deployment_properties.get('numberOfInstancesSuccessful'),
                          deployment_properties.get('numberOfInstancesFailed'))
        raise CLIError(error_text)
    return response_body


def _check_zip_deployment_status_flex(cmd, rg_name, name, deployment_status_url, timeout=None):
    import requests
    from azure.cli.core.util import should_disable_connection_verify

    headers = get_scm_site_headers_flex(cmd.cli_ctx)
    total_trials = (int(timeout) // 2) if timeout else 450
    num_trials = 0
    # Indicates whether the status has been non empty in previous calls
    has_response = False
    has_partial_success = False
    while num_trials < total_trials:
        time.sleep(1)
        response = requests.get(deployment_status_url, headers=headers,
                                verify=not should_disable_connection_verify())
        try:
            if response.status_code == 202 and not has_partial_success:
                has_partial_success = True
            if response.status_code == 404 and has_partial_success:
                break
            if (response.status_code == 404 or response.json().get('status') is None) and has_response:
                raise CLIError("Failed to retrieve deployment status. Please try again in a few minutes.")
            if (response.status_code != 404 and response.json().get('status') is not None) and not has_response:
                has_response = True

            res_dict = response.json()
        except json.decoder.JSONDecodeError:
            logger.warning("Deployment status endpoint %s returns malformed data. Retrying...", deployment_status_url)
            res_dict = {}
        finally:
            num_trials = num_trials + 1

        status = res_dict.get('status', 0)

        if status == -1:
            raise CLIError("Deployment was cancelled.")
        if status == 3:
            raise CLIError("Zip deployment failed. {}. These are the deployment logs: \n{}".format(
                           res_dict, json.dumps(show_deployment_log(cmd, rg_name, name))))
        if status == 4:
            break
        if status == 5:
            raise CLIError("Deployment was cancelled and another deployment is in progress.")
        if status == 6:
            raise CLIError("Deployment was partially successful. These are the deployment logs:\n{}".format(
                           json.dumps(show_deployment_log(cmd, rg_name, name))))
        if 'progress' in res_dict:
            logger.info(res_dict['progress'])  # show only in debug mode, customers seem to find this confusing
    # if the deployment is taking longer than expected
    if res_dict.get('status', 0) != 4 and not has_partial_success:
        raise CLIError("""Timeout reached by the command, however, the deployment operation
                       is still on-going. Navigate to your scm site to check the deployment status""")
    return res_dict


def list_continuous_webjobs(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'list_continuous_web_jobs', slot)


def start_continuous_webjob(cmd, resource_group_name, name, webjob_name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        client.web_apps.start_continuous_web_job_slot(resource_group_name, name, webjob_name, slot)
        return client.web_apps.get_continuous_web_job_slot(resource_group_name, name, webjob_name, slot)
    client.web_apps.start_continuous_web_job(resource_group_name, name, webjob_name)
    return client.web_apps.get_continuous_web_job(resource_group_name, name, webjob_name)


def stop_continuous_webjob(cmd, resource_group_name, name, webjob_name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        client.web_apps.stop_continuous_web_job_slot(resource_group_name, name, webjob_name, slot)
        return client.web_apps.get_continuous_web_job_slot(resource_group_name, name, webjob_name, slot)
    client.web_apps.stop_continuous_web_job(resource_group_name, name, webjob_name)
    return client.web_apps.get_continuous_web_job(resource_group_name, name, webjob_name)


def remove_continuous_webjob(cmd, resource_group_name, name, webjob_name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        return client.web_apps.delete_continuous_web_job_slot(resource_group_name, name, webjob_name, slot)
    return client.web_apps.delete_continuous_web_job(resource_group_name, name, webjob_name)


def list_triggered_webjobs(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'list_triggered_web_jobs', slot)


def run_triggered_webjob(cmd, resource_group_name, name, webjob_name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        client.web_apps.run_triggered_web_job_slot(resource_group_name, name, webjob_name, slot)
        return client.web_apps.get_triggered_web_job_slot(resource_group_name, name, webjob_name, slot)
    client.web_apps.run_triggered_web_job(resource_group_name, name, webjob_name)
    return client.web_apps.get_triggered_web_job(resource_group_name, name, webjob_name)


def remove_triggered_webjob(cmd, resource_group_name, name, webjob_name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        return client.web_apps.delete_triggered_web_job_slot(resource_group_name, name, webjob_name, slot)
    return client.web_apps.delete_triggered_web_job(resource_group_name, name, webjob_name)


def list_hc(cmd, name, resource_group_name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot is None:
        listed_vals = client.web_apps.list_hybrid_connections(resource_group_name, name)
    else:
        listed_vals = client.web_apps.list_hybrid_connections_slot(resource_group_name, name, slot)

    # reformats hybrid connection, to prune unnecessary fields
    mod_list = []
    for x in listed_vals.additional_properties["value"]:
        properties = x["properties"]
        resourceGroup = x["id"].split("/")
        mod_hc = {
            "id": x["id"],
            "location": x["location"],
            "name": x["name"],
            "properties": {
                "hostname": properties["hostname"],
                "port": properties["port"],
                "relayArmUri": properties["relayArmUri"],
                "relayName": properties["relayName"],
                "serviceBusNamespace": properties["serviceBusNamespace"],
                "serviceBusSuffix": properties["serviceBusSuffix"]
            },
            "resourceGroup": resourceGroup[4],
            "type": x["type"]
        }
        mod_list.append(mod_hc)
    return mod_list


def add_hc(cmd, name, resource_group_name, namespace, hybrid_connection, slot=None):
    HybridConnection = cmd.get_models('HybridConnection')

    web_client = web_client_factory(cmd.cli_ctx)

    hy_co_id = ''
    for n in NamespaceList(cli_ctx=cmd.cli_ctx)(command_args={}):
        logger.warning(n['name'])
        if n['name'] == namespace:
            hy_co_id = n['id']

    if hy_co_id == '':
        raise ResourceNotFoundError('Azure Service Bus Relay namespace {} was not found.'.format(namespace))

    i = 0
    hy_co_resource_group = ''
    hy_co_split = hy_co_id.split("/")
    for z in hy_co_split:
        if z == "resourceGroups":
            hy_co_resource_group = hy_co_split[i + 1]
        i = i + 1

    # calling the relay API to get information about the hybrid connection
    hy_co = HyCoShow(cli_ctx=cmd.cli_ctx)(command_args={"resource_group": hy_co_resource_group,
                                                        "namespace_name": namespace,
                                                        "name": hybrid_connection})

    # if the hybrid connection does not have a default sender authorization
    # rule, create it
    hy_co_rules = HycoAuthoList(cli_ctx=cmd.cli_ctx)(command_args={"resource_group": hy_co_resource_group,
                                                                   "namespace_name": namespace,
                                                                   "hybrid_connection_name": hybrid_connection})
    has_default_sender_key = False
    for r in hy_co_rules:
        if r['name'].lower() == "defaultsender":
            for z in r['rights']:
                if z[0].lower() == 'send' and len(z) == 1:
                    has_default_sender_key = True

    if not has_default_sender_key:
        rights = ["Send"]
        args = {"resource_group": hy_co_resource_group, "namespace_name": namespace,
                "hybrid_connection_name": hybrid_connection, "name": "defaultSender", "rights": rights}
        HycoAuthoCreate(cli_ctx=cmd.cli_ctx)(command_args=args)
    hy_co_keys = HycoAuthoKeysList(cli_ctx=cmd.cli_ctx)(command_args={"resource_group": hy_co_resource_group,
                                                                      "namespace_name": namespace,
                                                                      "hybrid_connection_name": hybrid_connection,
                                                                      "name": "defaultSender"})
    hy_co_info = hy_co['id']
    hy_co_metadata = ast.literal_eval(hy_co['userMetadata'])
    hy_co_hostname = ''
    for x in hy_co_metadata:
        if x["key"] == "endpoint":
            hy_co_hostname = x["value"]

    hostname_parts = hy_co_hostname.split(":")
    hostname = hostname_parts[0]
    port = hostname_parts[1]
    id_parameters = hy_co_info.split("/")

    # populate object with information from the hybrid connection, and set it
    # on webapp

    hc = HybridConnection(service_bus_namespace=id_parameters[8],
                          relay_name=hybrid_connection,
                          relay_arm_uri=hy_co_info,
                          hostname=hostname,
                          port=port,
                          send_key_name="defaultSender",
                          send_key_value=hy_co_keys['primaryKey'],
                          service_bus_suffix=".servicebus.windows.net")

    if slot is None:
        return_hc = web_client.web_apps.create_or_update_hybrid_connection(resource_group_name, name, namespace,
                                                                           hybrid_connection, hc)
    else:
        return_hc = web_client.web_apps.create_or_update_hybrid_connection_slot(resource_group_name, name, namespace,
                                                                                hybrid_connection, slot, hc)

    # reformats hybrid connection, to prune unnecessary fields
    resourceGroup = return_hc.id.split("/")
    mod_hc = {
        "hostname": return_hc.hostname,
        "id": return_hc.id,
        "location": return_hc.additional_properties["location"],
        "name": return_hc.name,
        "port": return_hc.port,
        "relayArmUri": return_hc.relay_arm_uri,
        "resourceGroup": resourceGroup[4],
        "serviceBusNamespace": return_hc.service_bus_namespace,
        "serviceBusSuffix": return_hc.service_bus_suffix
    }
    return mod_hc


# set the key the apps use to connect with the hybrid connection
def set_hc_key(cmd, plan, resource_group_name, namespace, hybrid_connection, key_type):
    HybridConnection = cmd.get_models('HybridConnection')
    web_client = web_client_factory(cmd.cli_ctx)

    # extract the hybrid connection resource group
    asp_hy_co = web_client.app_service_plans.get_hybrid_connection(resource_group_name, plan,
                                                                   namespace, hybrid_connection)
    arm_uri = asp_hy_co.relay_arm_uri
    split_uri = arm_uri.split("resourceGroups/")
    resource_group_strings = split_uri[1].split('/')
    relay_resource_group = resource_group_strings[0]

    # calling the relay function to obtain information about the hc in question
    hy_co = HyCoShow(cli_ctx=cmd.cli_ctx)(command_args={"resource_group": relay_resource_group,
                                                        "namespace_name": namespace,
                                                        "name": hybrid_connection})

    # if the hybrid connection does not have a default sender authorization
    # rule, create it
    hy_co_rules = HycoAuthoList(cli_ctx=cmd.cli_ctx)(command_args={"resource_group": relay_resource_group,
                                                                   "namespace_name": namespace,
                                                                   "hybrid_connection_name": hybrid_connection})

    has_default_sender_key = False
    for r in hy_co_rules:
        if r['name'].lower() == "defaultsender":
            for z in r['rights']:
                if z[0].lower() == 'send' and len(z) == 1:
                    has_default_sender_key = True

    if not has_default_sender_key:
        rights = ["Send"]
        args = {"resource_group": relay_resource_group, "namespace_name": namespace,
                "hybrid_connection_name": hybrid_connection, "name": "defaultSender", "rights": rights}
        HycoAuthoCreate(cli_ctx=cmd.cli_ctx)(command_args=args)

    hy_co_keys = HycoAuthoKeysList(cli_ctx=cmd.cli_ctx)(command_args={"resource_group": relay_resource_group,
                                                                      "namespace_name": namespace,
                                                                      "hybrid_connection_name": hybrid_connection,
                                                                      "name": "defaultSender"})
    hy_co_metadata = ast.literal_eval(hy_co.user_metadata)
    hy_co_hostname = 0
    for x in hy_co_metadata:
        if x["key"] == "endpoint":
            hy_co_hostname = x["value"]

    hostname_parts = hy_co_hostname.split(":")
    hostname = hostname_parts[0]
    port = hostname_parts[1]

    key = "empty"
    if key_type.lower() == "primary":
        key = hy_co_keys['primaryKey']
    elif key_type.lower() == "secondary":
        key = hy_co_keys['secondaryKey']
    # enures input is correct
    if key == "empty":
        logger.warning("Key type is invalid - must be primary or secondary")
        return

    apps = web_client.app_service_plans.list_web_apps_by_hybrid_connection(resource_group_name, plan, namespace,
                                                                           hybrid_connection)
    # changes the key for every app that uses that hybrid connection
    for x in apps:
        app_info = ast.literal_eval(x)
        app_name = app_info["name"]
        app_id = app_info["id"]
        id_split = app_id.split("/")
        app_resource_group = id_split[4]
        hc = HybridConnection(service_bus_namespace=namespace, relay_name=hybrid_connection,
                              relay_arm_uri=arm_uri, hostname=hostname, port=port, send_key_name="defaultSender",
                              send_key_value=key)
        web_client.web_apps.update_hybrid_connection(app_resource_group, app_name, namespace,
                                                     hybrid_connection, hc)

    return web_client.app_service_plans.list_web_apps_by_hybrid_connection(resource_group_name, plan,
                                                                           namespace, hybrid_connection)


def appservice_list_vnet(cmd, resource_group_name, plan):
    web_client = web_client_factory(cmd.cli_ctx)
    return web_client.app_service_plans.list_vnets(resource_group_name, plan)


def remove_hc(cmd, resource_group_name, name, namespace, hybrid_connection, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot is None:
        return_hc = client.web_apps.delete_hybrid_connection(resource_group_name, name, namespace, hybrid_connection)
    else:
        return_hc = client.web_apps.delete_hybrid_connection_slot(resource_group_name, name, namespace,
                                                                  hybrid_connection, slot)
    return return_hc


def list_functionapp_vnet_integration(cmd, name, resource_group_name, slot=None):
    return list_vnet_integration(cmd, name, resource_group_name, slot=None)


def list_vnet_integration(cmd, name, resource_group_name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot is None:
        result = list(client.web_apps.list_vnet_connections(resource_group_name, name))
    else:
        result = list(client.web_apps.list_vnet_connections_slot(resource_group_name, name, slot))
    mod_list = []

    # reformats the vnet entry, removing unecessary information
    for x in result:
        # removes GUIDs from name and id
        longName = x.name
        if '_' in longName:
            usIndex = longName.index('_')
            shortName = longName[usIndex + 1:]
        else:
            shortName = longName
        v_id = x.id
        lastSlash = v_id.rindex('/')
        shortId = v_id[:lastSlash] + '/' + shortName
        # extracts desired fields
        certThumbprint = x.cert_thumbprint
        location = x.additional_properties["location"]
        v_type = x.type
        vnet_resource_id = x.vnet_resource_id
        id_strings = v_id.split('/')
        resourceGroup = id_strings[4]
        routes = x.routes

        vnet_mod = {"certThumbprint": certThumbprint,
                    "id": shortId,
                    "location": location,
                    "name": shortName,
                    "resourceGroup": resourceGroup,
                    "routes": routes,
                    "type": v_type,
                    "vnetResourceId": vnet_resource_id}
        mod_list.append(vnet_mod)

    return mod_list


def add_webapp_vnet_integration(cmd, name, resource_group_name, vnet, subnet, slot=None, skip_delegation_check=False):
    return _add_vnet_integration(cmd, name, resource_group_name, vnet, subnet, slot, skip_delegation_check)


def add_functionapp_vnet_integration(cmd, name, resource_group_name, vnet, subnet, slot=None,
                                     skip_delegation_check=False):
    client = web_client_factory(cmd.cli_ctx)
    functionapp = get_functionapp(cmd, resource_group_name, name)
    parsed_plan_id = parse_resource_id(functionapp.server_farm_id)
    plan_info = client.app_service_plans.get(parsed_plan_id['resource_group'], parsed_plan_id['name'])
    if plan_info is None:
        raise ResourceNotFoundError('Could not determine the current plan of the functionapp')
    if is_plan_consumption(cmd, plan_info):
        raise ValidationError('Virtual network integration is not allowed for consumption plans')
    if is_flex_functionapp(cmd.cli_ctx, resource_group_name, name):
        register_app_provider(cmd)
    return _add_vnet_integration(cmd, name, resource_group_name, vnet, subnet, slot, skip_delegation_check)


def _add_vnet_integration(cmd, name, resource_group_name, vnet, subnet, slot=None, skip_delegation_check=False):
    subnet_info = _get_subnet_info(cmd=cmd,
                                   resource_group_name=resource_group_name,
                                   subnet=subnet,
                                   vnet=vnet)
    client = web_client_factory(cmd.cli_ctx)

    app = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot, client=client)

    parsed_plan = parse_resource_id(app.server_farm_id)
    plan_info = client.app_service_plans.get(parsed_plan['resource_group'], parsed_plan["name"])
    is_flex = is_flex_functionapp(cmd.cli_ctx, resource_group_name, name)

    if skip_delegation_check:
        logger.warning('Skipping delegation check. Ensure that subnet is delegated to Microsoft.Web/serverFarms.'
                       ' Missing delegation can cause "Bad Request" error.')
    else:
        _vnet_delegation_check(cmd, subnet_subscription_id=subnet_info["subnet_subscription_id"],
                               vnet_resource_group=subnet_info["resource_group_name"],
                               vnet_name=subnet_info["vnet_name"],
                               subnet_name=subnet_info["subnet_name"],
                               subnet_service_delegation=FLEX_SUBNET_DELEGATION if is_flex else None)

    app.virtual_network_subnet_id = subnet_info["subnet_resource_id"]
    app.site_config.vnet_route_all_enabled = True

    _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'begin_create_or_update', slot,
                            client=client, extra_parameter=app)

    return {
        "id": subnet_info["vnet_resource_id"],
        "location": plan_info.location,  # must be the same as vnet location bc of validation check
        "name": subnet_info["vnet_name"],
        "resourceGroup": subnet_info["resource_group_name"],
        "subnetResourceId": subnet_info["subnet_resource_id"]
    }


def _vnet_delegation_check(cmd, subnet_subscription_id, vnet_resource_group, vnet_name, subnet_name,
                           subnet_service_delegation="Microsoft.Web/serverFarms"):
    from azure.cli.core.commands.client_factory import get_subscription_id

    if subnet_service_delegation is None:
        subnet_service_delegation = "Microsoft.Web/serverFarms"

    if get_subscription_id(cmd.cli_ctx).lower() != subnet_subscription_id.lower():
        logger.warning('Cannot validate subnet in other subscription for delegation to Microsoft.Web/serverFarms.'
                       ' Missing delegation can cause "Bad Request" error.')
        logger.warning('To manually add a delegation, use the command: az network vnet subnet update '
                       '--resource-group %s '
                       '--name %s '
                       '--vnet-name %s '
                       '--delegations %s', vnet_resource_group, subnet_name, vnet_name, subnet_service_delegation)
    else:
        subnetObj = SubnetShow(cli_ctx=cmd.cli_ctx)(command_args={
            "name": subnet_name,
            "vnet_name": vnet_name,
            "resource_group": vnet_resource_group
        })
        delegations = subnetObj["delegations"]
        delegated = False
        for d in delegations:
            if d["serviceName"].lower() == subnet_service_delegation.lower():
                delegated = True

        if not delegated:
            poller = SubnetUpdate(cli_ctx=cmd.cli_ctx)(command_args={
                "name": subnet_name,
                "vnet_name": vnet_name,
                "resource_group": vnet_resource_group,
                "delegated_services": [{"name": "delegation", "service_name": subnet_service_delegation}]
            })
            LongRunningOperation(cmd.cli_ctx)(poller)


def _validate_subnet(cli_ctx, subnet, vnet, resource_group_name):
    subnet_is_id = is_valid_resource_id(subnet)
    if subnet_is_id:
        subnet_id_parts = parse_resource_id(subnet)
        vnet_name = subnet_id_parts['name']
        if not (vnet_name.lower() == vnet.lower() or subnet.startswith(vnet)):
            logger.warning('Subnet ID is valid. Ignoring vNet input.')
        return subnet

    vnet_is_id = is_valid_resource_id(vnet)
    if vnet_is_id:
        vnet_id_parts = parse_resource_id(vnet)
        return resource_id(
            subscription=vnet_id_parts['subscription'],
            resource_group=vnet_id_parts['resource_group'],
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet_id_parts['name'],
            child_type_1='subnets',
            child_name_1=subnet)

    # Reuse logic from existing command to stay backwards compatible
    list_all_vnets = VNetList(cli_ctx=cli_ctx)(command_args={})

    vnets = []
    for v in list_all_vnets:
        if vnet in (v["name"], v["id"]):
            vnet_details = parse_resource_id(v["id"])
            vnet_resource_group = vnet_details['resource_group']
            vnets.append((v["id"], v["name"], vnet_resource_group))

    if not vnets:
        return logger.warning("The virtual network %s was not found in the subscription.", vnet)

    # If more than one vnet, try to use one from same resource group. Otherwise, use first and log the vnet resource id
    found_vnet = [v for v in vnets if v[2].lower() == resource_group_name.lower()]
    if not found_vnet:
        found_vnet = [vnets[0]]

    (vnet_id, vnet, vnet_resource_group) = found_vnet[0]
    if len(vnets) > 1:
        logger.warning("Multiple virtual networks of name %s were found. Using virtual network with resource ID: %s. "
                       "To use a different virtual network, specify the virtual network resource ID using --vnet.",
                       vnet, vnet_id)
    vnet_id_parts = parse_resource_id(vnet_id)
    return resource_id(
        subscription=vnet_id_parts['subscription'],
        resource_group=vnet_id_parts['resource_group'],
        namespace='Microsoft.Network',
        type='virtualNetworks',
        name=vnet_id_parts['name'],
        child_type_1='subnets',
        child_name_1=subnet)


def remove_functionapp_vnet_integration(cmd, name, resource_group_name, slot=None):
    return remove_vnet_integration(cmd, name, resource_group_name, slot)


def remove_vnet_integration(cmd, name, resource_group_name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot is None:
        return_vnet = client.web_apps.delete_swift_virtual_network(resource_group_name, name)
    else:
        return_vnet = client.web_apps.delete_swift_virtual_network_slot(resource_group_name, name, slot)
    return return_vnet


def get_history_triggered_webjob(cmd, resource_group_name, name, webjob_name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        return client.web_apps.list_triggered_web_job_history_slot(resource_group_name, name, webjob_name, slot)
    return client.web_apps.list_triggered_web_job_history(resource_group_name, name, webjob_name)


def webapp_up(cmd, name=None, resource_group_name=None, plan=None, location=None, sku=None,  # pylint: disable=too-many-statements,too-many-branches
              os_type=None, runtime=None, dryrun=False, logs=False, launch_browser=False, html=False,
              app_service_environment=None, track_status=True, enable_kudu_warmup=True, basic_auth=""):
    if not name:
        name = generate_default_app_name(cmd)

    import os

    AppServicePlan = cmd.get_models('AppServicePlan')
    src_dir = os.getcwd()
    _src_path_escaped = "{}".format(src_dir.replace(os.sep, os.sep + os.sep))
    client = web_client_factory(cmd.cli_ctx)
    user = get_profile_username()
    _create_new_rg = False
    _site_availability = get_site_availability(cmd, name)
    _create_new_app = _site_availability.name_available
    runtime = _StackRuntimeHelper.remove_delimiters(runtime)
    os_name = os_type if os_type else detect_os_from_src(src_dir, html, runtime)
    _is_linux = os_name.lower() == LINUX_OS_NAME
    helper = _StackRuntimeHelper(cmd, linux=_is_linux, windows=not _is_linux)

    if runtime:
        match = helper.resolve(runtime, _is_linux)
        if not match:
            raise ValidationError("{0} runtime '{1}' is not supported. Please check supported runtimes with: "
                                  "'az webapp list-runtimes --os {0}'".format(os_name, runtime))

        language = runtime.split('|')[0]
        version_used_create = '|'.join(runtime.split('|')[1:])
        detected_version = '-'
    else:
        # detect the version
        _lang_details = get_lang_from_content(src_dir, html, is_linux=_is_linux)
        language = _lang_details.get('language')
        _data = get_runtime_version_details(_lang_details.get('file_loc'), language, helper, _is_linux)
        version_used_create = _data.get('to_create')
        detected_version = _data.get('detected')

    runtime_version = "{}|{}".format(language, version_used_create) if \
        version_used_create != "-" else version_used_create
    site_config = None

    if not _create_new_app:  # App exists, or App name unavailable
        if _site_availability.reason == 'Invalid':
            raise ValidationError(_site_availability.message)
        # Get the ASP & RG info, if the ASP & RG parameters are provided we use those else we need to find those
        logger.warning("Webapp '%s' already exists. The command will deploy contents to the existing app.", name)
        app_details = get_app_details(cmd, name)
        if app_details is None:
            raise ResourceNotFoundError("Unable to retrieve details of the existing app '{}'. Please check that the "
                                        "app is a part of the current subscription if updating an existing app. If "
                                        "creating a new app, app names must be globally unique. Please try a more "
                                        "unique name or leave unspecified to receive a randomly "
                                        "generated name.".format(name))
        current_rg = app_details.resource_group
        if resource_group_name is not None and (resource_group_name.lower() != current_rg.lower()):
            raise ValidationError("The webapp '{}' exists in ResourceGroup '{}' and does not "
                                  "match the value entered '{}'. Please re-run command with the "
                                  "correct parameters.". format(name, current_rg, resource_group_name))
        rg_name = resource_group_name or current_rg
        if location is None:
            loc = app_details.location.replace(" ", "").lower()
        else:
            loc = location.replace(" ", "").lower()
        plan_details = parse_resource_id(app_details.server_farm_id)
        current_plan = plan_details['name']
        if plan is not None and current_plan.lower() != plan.lower():
            raise ValidationError("The plan name entered '{}' does not match the plan name that the webapp is "
                                  "hosted in '{}'. Please check if you have configured defaults for plan name "
                                  "and re-run command.".format(plan, current_plan))
        plan = plan or plan_details['name']
        plan_info = client.app_service_plans.get(plan_details['resource_group'], plan)
        sku = plan_info.sku.name if isinstance(plan_info, AppServicePlan) else 'Free'
        current_os = 'Linux' if plan_info.reserved else 'Windows'
        # Raise error if current OS of the app is different from the current one
        if current_os.lower() != os_name.lower():
            raise ValidationError("The webapp '{}' is a {} app. The code detected at '{}' will default to "
                                  "'{}'. Please create a new app "
                                  "to continue this operation. For more information on default behaviors, "
                                  "see https://learn.microsoft.com/cli/azure/webapp?view=azure-cli-latest#az_webapp_up."
                                  .format(name, current_os, src_dir, os_name))
        _is_linux = plan_info.reserved
        # for an existing app check if the runtime version needs to be updated
        # Get site config to check the runtime version
        site_config = client.web_apps.get_configuration(rg_name, name)
    else:  # need to create new app, check if we need to use default RG or use user entered values
        logger.warning("The webapp '%s' doesn't exist", name)
        sku = get_sku_to_use(src_dir, html, sku, runtime, app_service_environment)
        loc = set_location(cmd, sku, location)
        rg_name = get_rg_to_use(user, resource_group_name)
        _create_new_rg = not check_resource_group_exists(cmd, rg_name)
        plan = get_plan_to_use(cmd=cmd,
                               user=user,
                               loc=loc,
                               sku=sku,
                               create_rg=_create_new_rg,
                               resource_group_name=rg_name,
                               plan=plan,
                               is_linux=_is_linux,
                               client=client)
    dry_run_str = r""" {
                "name" : "%s",
                "appserviceplan" : "%s",
                "resourcegroup" : "%s",
                "sku": "%s",
                "os": "%s",
                "location" : "%s",
                "src_path" : "%s",
                "runtime_version_detected": "%s",
                "runtime_version": "%s"
                }
                """ % (name, plan, rg_name, get_sku_tier(sku), os_name, loc, _src_path_escaped, detected_version,
                       runtime_version)
    create_json = json.loads(dry_run_str)

    if dryrun:
        logger.warning("Web app will be created with the below configuration,re-run command "
                       "without the --dryrun flag to create & deploy a new app")
        return create_json

    if _create_new_rg:
        logger.warning("Creating Resource group '%s' ...", rg_name)
        create_resource_group(cmd, rg_name, loc)
        logger.warning("Resource group creation complete")
    # create ASP
    logger.warning("Creating AppServicePlan '%s' or Updating if already exists", plan)
    # we will always call the ASP create or update API so that in case of re-deployment, if the SKU or plan setting are
    # updated we update those
    try:
        create_app_service_plan(cmd, rg_name, plan, _is_linux, hyper_v=False, per_site_scaling=False, sku=sku,
                                number_of_workers=1 if _is_linux else None, location=loc,
                                app_service_environment=app_service_environment)
    except ResourceNotFoundError as ex:
        raise ex
    except CLIError as ex:
        raise ex
    except Exception as ex:  # pylint: disable=broad-except
        if ex.response.status_code == 409:  # catch 409 conflict when trying to create existing ASP in diff location
            try:
                response_content = json.loads(ex.response._content.decode('utf-8'))  # pylint: disable=protected-access
            except Exception:  # pylint: disable=broad-except
                raise CLIInternalError(ex)
            raise UnclassifiedUserFault(response_content['error']['message'])
        raise AzureResponseError(ex)

    if _create_new_app:
        logger.warning("Creating webapp '%s' ...", name)
        create_webapp(cmd, rg_name, name, plan, runtime_version if not html else None,
                      using_webapp_up=True, language=language)
        _configure_default_logging(cmd, rg_name, name)
    else:  # for existing app if we might need to update the stack runtime settings
        helper = _StackRuntimeHelper(cmd, linux=_is_linux, windows=not _is_linux)
        match = helper.resolve(runtime_version, _is_linux)

        if os_name.lower() == 'linux' and site_config.linux_fx_version != runtime_version:
            if match and site_config.linux_fx_version != match.configs['linux_fx_version']:
                logger.warning('Updating runtime version from %s to %s',
                               site_config.linux_fx_version, match.configs['linux_fx_version'])
                update_site_configs(cmd, rg_name, name, linux_fx_version=match.configs['linux_fx_version'])
                logger.warning('Waiting for runtime version to propagate ...')
                time.sleep(30)  # wait for kudu to get updated runtime before zipdeploy. No way to poll for this
            elif not match:
                logger.warning('Updating runtime version from %s to %s',
                               site_config.linux_fx_version, runtime_version)
                update_site_configs(cmd, rg_name, name, linux_fx_version=runtime_version)
                logger.warning('Waiting for runtime version to propagate ...')
                time.sleep(30)  # wait for kudu to get updated runtime before zipdeploy. No way to poll for this
        elif os_name.lower() == 'windows':
            # may need to update stack runtime settings. For node its site_config.app_settings, otherwise site_config
            if match:
                _update_app_settings_for_windows_if_needed(cmd, rg_name, name, match, site_config, runtime_version)
        create_json['runtime_version'] = runtime_version

    _enable_basic_auth(cmd, name, None, resource_group_name, basic_auth.lower())

    # Zip contents & Deploy
    logger.warning("Creating zip with contents of dir %s ...", src_dir)
    # zip contents & deploy
    zip_file_path = zip_contents_from_dir(src_dir, language)
    enable_zip_deploy(cmd, rg_name, name, zip_file_path, track_status=track_status,
                      enable_kudu_warmup=enable_kudu_warmup)

    if launch_browser:
        logger.warning("Launching app using default browser")
        view_in_browser(cmd, rg_name, name, None, logs)
    else:
        _url = _get_url(cmd, rg_name, name)
        logger.warning("You can launch the app at %s", _url)
        create_json.update({'URL': _url})

    if logs:
        _configure_default_logging(cmd, rg_name, name)
        try:
            return get_streaming_log(cmd, rg_name, name)
        except Exception:  # pylint: disable=broad-except
            logger.warning("Unable to reach the app. Please run 'az webapp log tail' to view the logs.")

    _set_webapp_up_default_args(cmd, rg_name, sku, plan, loc, name)

    return create_json


def _set_webapp_up_default_args(cmd, rg_name, sku, plan, loc, name):
    with ConfiguredDefaultSetter(cmd.cli_ctx.config, True):
        logger.warning("Setting 'az webapp up' default arguments for current directory. "
                       "Manage defaults with 'az configure --scope local'")

        cmd.cli_ctx.config.set_value('defaults', 'group', rg_name)
        logger.warning("--resource-group/-g default: %s", rg_name)

        cmd.cli_ctx.config.set_value('defaults', 'sku', sku)
        logger.warning("--sku default: %s", sku)

        cmd.cli_ctx.config.set_value('defaults', 'appserviceplan', plan)
        logger.warning("--plan/-p default: %s", plan)

        cmd.cli_ctx.config.set_value('defaults', 'location', loc)
        logger.warning("--location/-l default: %s", loc)

        cmd.cli_ctx.config.set_value('defaults', 'web', name)
        logger.warning("--name/-n default: %s", name)


def _update_app_settings_for_windows_if_needed(cmd, rg_name, name, match, site_config, runtime_version):
    app_settings = _generic_site_operation(cmd.cli_ctx, rg_name, name, 'list_application_settings', slot=None)
    update_needed = False
    if 'node' in runtime_version:
        settings = []
        for k, v in match.configs.items():
            for app_setting_name, app_setting_value in app_settings.properties.items():
                if app_setting_name == k and app_setting_value != v:
                    update_needed = True
                    settings.append(f"{k}={v}")
        if update_needed:
            logger.warning('Updating runtime version to %s', runtime_version)
            update_app_settings(cmd, rg_name, name, settings=settings, slot=None, slot_settings=None)
    else:
        for k, v in match.configs.items():
            if getattr(site_config, k, None) != v:
                update_needed = True
                setattr(site_config, k, v)
        if update_needed:
            logger.warning('Updating runtime version to %s', runtime_version)
            update_site_configs(cmd,
                                rg_name,
                                name,
                                net_framework_version=site_config.net_framework_version,
                                php_version=site_config.php_version,
                                python_version=site_config.python_version,
                                java_version=site_config.java_version,
                                java_container=site_config.java_container,
                                java_container_version=site_config.java_container_version)

    current_stack = get_current_stack_from_runtime(runtime_version)
    _update_webapp_current_stack_property_if_needed(cmd, rg_name, name, current_stack)

    if update_needed:
        logger.warning('Waiting for runtime version to propagate ...')
        time.sleep(30)  # wait for kudu to get updated runtime before zipdeploy. No way to poll for this


def _update_webapp_current_stack_property_if_needed(cmd, resource_group, name, current_stack):
    if not current_stack:
        return
    # portal uses this current_stack value to display correct runtime for windows webapps
    client = web_client_factory(cmd.cli_ctx)
    app_metadata = client.web_apps.list_metadata(resource_group, name)
    if 'CURRENT_STACK' not in app_metadata.properties or app_metadata.properties["CURRENT_STACK"] != current_stack:
        app_metadata.properties["CURRENT_STACK"] = current_stack
        client.web_apps.update_metadata(resource_group, name, metadata=app_metadata)


def _ping_scm_site(cmd, resource_group, name, instance=None):
    from azure.cli.core.util import should_disable_connection_verify
    #  wake up kudu, by making an SCM call
    import requests
    #  work around until the timeout limits issue for linux is investigated & fixed
    scm_url = _get_scm_url(cmd, resource_group, name)
    headers = get_scm_site_headers(cmd.cli_ctx, name, resource_group)
    cookies = {}
    if instance is not None:
        cookies['ARRAffinity'] = instance
    requests.get(scm_url + '/api/settings', headers=headers, verify=not should_disable_connection_verify(),
                 cookies=cookies)


def is_webapp_up(tunnel_server):
    return tunnel_server.is_webapp_up()


def get_tunnel(cmd, resource_group_name, name, port=None, slot=None, instance=None):
    webapp = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    is_linux = webapp.reserved
    if not is_linux:
        raise ValidationError("Only Linux App Service Plans supported, Found a Windows App Service Plan")

    if port is None:
        port = 0  # Will auto-select a free port from 1024-65535
        logger.info('No port defined, creating on random free port')

    # Validate that we have a known instance (case-sensitive)
    if instance is not None:
        instances = list_instances(cmd, resource_group_name, name, slot=slot)
        instance_names = set(i.name for i in instances)
        if instance not in instance_names:
            if slot is not None:
                raise ValidationError("The provided instance '{}' is not valid "
                                      "for this webapp and slot.".format(instance))
            raise ValidationError("The provided instance '{}' is not valid for this webapp.".format(instance))

    scm_url = _get_scm_url(cmd, resource_group_name, name, slot)
    headers = get_scm_site_headers(cmd.cli_ctx, name, resource_group_name, slot)
    # basic & bearer auth use different capitalization for whatever reason
    auth_string = headers.get("authorization") or headers.get("Authorization")

    tunnel_server = TunnelServer('127.0.0.1', port, scm_url, auth_string, instance)
    _ping_scm_site(cmd, resource_group_name, name, instance=instance)

    _wait_for_webapp(tunnel_server)
    return tunnel_server


def create_tunnel(cmd, resource_group_name, name, port=None, slot=None, timeout=None, instance=None):
    tunnel_server = get_tunnel(cmd, resource_group_name, name, port, slot, instance)

    t = threading.Thread(target=_start_tunnel, args=(tunnel_server,))
    t.daemon = True
    t.start()
    logger.warning('Opening tunnel on addr: %s', tunnel_server.local_addr)
    logger.warning('Opening tunnel on port: %s', tunnel_server.local_port)

    config = get_site_configs(cmd, resource_group_name, name, slot)
    if config.remote_debugging_enabled:
        logger.warning('Tunnel is ready, connect on port %s', tunnel_server.local_port)
    else:
        ssh_user_name = 'root'
        ssh_user_password = 'Docker!'
        logger.warning('SSH is available { username: %s, password: %s }', ssh_user_name, ssh_user_password)
        logger.warning('Enter a full SSH session with: ssh %s@%s -m hmac-sha1 -p %s', ssh_user_name,
                       tunnel_server.local_addr, tunnel_server.local_port)

    logger.warning('Ctrl + C to close')

    if timeout:
        time.sleep(int(timeout))
    else:
        while t.is_alive():
            time.sleep(5)


def create_tunnel_and_session(cmd, resource_group_name, name, port=None, slot=None, timeout=None, instance=None):
    tunnel_server = get_tunnel(cmd, resource_group_name, name, port, slot, instance)

    t = threading.Thread(target=_start_tunnel, args=(tunnel_server,))
    t.daemon = True
    t.start()

    ssh_user_name = 'root'
    ssh_user_password = 'Docker!'

    s = threading.Thread(target=_start_ssh_session,
                         args=('localhost', tunnel_server.get_port(), ssh_user_name, ssh_user_password))
    s.daemon = True
    s.start()

    if timeout:
        time.sleep(int(timeout))
    else:
        while s.is_alive() and t.is_alive():
            time.sleep(5)


def perform_onedeploy_functionapp(cmd,
                                  resource_group_name,
                                  name,
                                  src_path=None,
                                  src_url=None,
                                  target_path=None,
                                  artifact_type=None,
                                  is_async=None,
                                  restart=None,
                                  clean=None,
                                  ignore_stack=None,
                                  timeout=None,
                                  slot=None):
    params = OneDeployParams()

    params.cmd = cmd
    params.resource_group_name = resource_group_name
    params.webapp_name = name
    params.src_path = src_path
    params.src_url = src_url
    params.target_path = target_path
    params.artifact_type = artifact_type
    params.is_async_deployment = is_async
    params.should_restart = restart
    params.is_clean_deployment = clean
    params.should_ignore_stack = ignore_stack
    params.timeout = timeout
    params.slot = slot
    params.track_status = False
    params.is_functionapp = True

    return _perform_onedeploy_internal(params)


def perform_onedeploy_webapp(cmd,
                             resource_group_name,
                             name,
                             src_path=None,
                             src_url=None,
                             target_path=None,
                             artifact_type=None,
                             is_async=None,
                             restart=None,
                             clean=None,
                             ignore_stack=None,
                             timeout=None,
                             slot=None,
                             track_status=True,
                             enable_kudu_warmup=True):
    params = OneDeployParams()

    params.cmd = cmd
    params.resource_group_name = resource_group_name
    params.webapp_name = name
    params.src_path = src_path
    params.src_url = src_url
    params.target_path = target_path
    params.artifact_type = artifact_type
    params.is_async_deployment = is_async
    params.should_restart = restart
    params.is_clean_deployment = clean
    params.should_ignore_stack = ignore_stack
    params.timeout = timeout
    params.slot = slot
    params.track_status = track_status
    params.enable_kudu_warmup = enable_kudu_warmup

    client = web_client_factory(cmd.cli_ctx)
    app = client.web_apps.get(resource_group_name, name)
    params.is_linux_webapp = is_linux_webapp(app)
    params.is_functionapp = False
    return _perform_onedeploy_internal(params)


# Class for OneDeploy parameters
# pylint: disable=too-many-instance-attributes,too-few-public-methods
class OneDeployParams:
    def __init__(self):
        self.cmd = None
        self.resource_group_name = None
        self.webapp_name = None
        self.src_path = None
        self.src_url = None
        self.artifact_type = None
        self.is_async_deployment = None
        self.target_path = None
        self.should_restart = None
        self.is_clean_deployment = None
        self.should_ignore_stack = None
        self.timeout = None
        self.slot = None
        self.track_status = False
        self.enable_kudu_warmup = None
        self.is_linux_webapp = None
        self.is_functionapp = None
# pylint: enable=too-many-instance-attributes,too-few-public-methods


def _build_onedeploy_url(params, instance_id=None):
    if params.src_url:
        return _build_onedeploy_arm_url(params, instance_id)
    return _build_onedeploy_scm_url(params)


def _build_kudu_warmup_scm_url(params):
    scm_url = _get_scm_url(params.cmd, params.resource_group_name, params.webapp_name, params.slot)
    return scm_url + '/api/deployments?warmup=true'


def _build_kudu_warmup_arm_url(params, instance_id=None):
    from azure.cli.core.commands.client_factory import get_subscription_id
    client = web_client_factory(params.cmd.cli_ctx)
    sub_id = get_subscription_id(params.cmd.cli_ctx)
    instances_segment = f"/instances/{instance_id}" if instance_id is not None else ""
    if not params.slot:
        base_url = (
            f"subscriptions/{sub_id}/resourceGroups/{params.resource_group_name}/providers/Microsoft.Web/sites/"
            f"{params.webapp_name}{instances_segment}/deployments?api-version={client.DEFAULT_API_VERSION}"
            f"&warmup=true"
        )
    else:
        base_url = (
            f"subscriptions/{sub_id}/resourceGroups/{params.resource_group_name}/providers/Microsoft.Web/sites/"
            f"{params.webapp_name}/slots/{params.slot}{instances_segment}/deployments"
            f"?api-version={client.DEFAULT_API_VERSION}&warmup=true"
        )
    return params.cmd.cli_ctx.cloud.endpoints.resource_manager + base_url


def _build_onedeploy_scm_url(params):
    scm_url = _get_scm_url(params.cmd, params.resource_group_name, params.webapp_name, params.slot)
    deploy_url = scm_url + '/api/publish?type=' + params.artifact_type

    if params.is_async_deployment is not None:
        deploy_url = deploy_url + '&async=' + str(params.is_async_deployment)

    if params.should_restart is not None:
        deploy_url = deploy_url + '&restart=' + str(params.should_restart)

    if params.is_clean_deployment is not None:
        deploy_url = deploy_url + '&clean=' + str(params.is_clean_deployment)

    if params.should_ignore_stack is not None:
        deploy_url = deploy_url + '&ignorestack=' + str(params.should_ignore_stack)

    if params.target_path is not None:
        deploy_url = deploy_url + '&path=' + quote(params.target_path)

    return deploy_url


def _build_onedeploy_arm_url(params, instance_id):
    from azure.cli.core.commands.client_factory import get_subscription_id
    client = web_client_factory(params.cmd.cli_ctx)
    sub_id = get_subscription_id(params.cmd.cli_ctx)
    instances_param = f"/instances/{instance_id}" if instance_id is not None else ""
    if not params.slot:
        base_url = (
            f"subscriptions/{sub_id}/resourceGroups/{params.resource_group_name}/providers/Microsoft.Web/sites/"
            f"{params.webapp_name}{instances_param}/extensions/onedeploy?api-version={client.DEFAULT_API_VERSION}"
        )
    else:
        base_url = (
            f"subscriptions/{sub_id}/resourceGroups/{params.resource_group_name}/providers/Microsoft.Web/sites/"
            f"{params.webapp_name}/slots/{params.slot}{instances_param}/extensions/onedeploy"
            f"?api-version={client.DEFAULT_API_VERSION}"
        )
    return params.cmd.cli_ctx.cloud.endpoints.resource_manager + base_url


def _build_deploymentstatus_url(cmd, resource_group_name, webapp_name, slot, deployment_id):
    from azure.cli.core.commands.client_factory import get_subscription_id
    client = web_client_factory(cmd.cli_ctx)
    sub_id = get_subscription_id(cmd.cli_ctx)

    slot_info = "/slots/" + slot if slot else ""
    base_url = (
        f"subscriptions/{sub_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Web/sites/"
        f"{webapp_name}{slot_info}/deploymentStatus/{deployment_id}"
        f"?api-version={client.DEFAULT_API_VERSION}"
    )
    return cmd.cli_ctx.cloud.endpoints.resource_manager + base_url


def _get_ondeploy_headers(params):
    if params.src_path:
        content_type = 'application/octet-stream'
    elif params.src_url:
        content_type = 'application/json'
    else:
        raise RequiredArgumentMissingError('Unable to determine source location of the artifact being deployed')

    additional_headers = {"Content-Type": content_type, "Cache-Control": "no-cache"}

    return get_scm_site_headers(params.cmd.cli_ctx, params.webapp_name, params.resource_group_name, params.slot,
                                additional_headers=additional_headers)


def _get_onedeploy_status_url(params):
    scm_url = _get_scm_url(params.cmd, params.resource_group_name, params.webapp_name, params.slot)
    return scm_url + '/api/deployments/latest'


def _get_onedeploy_request_body(params):
    import os
    file_hash = None
    app_is_linux_webapp = False

    if params.src_path:
        logger.warning('Deploying from local path: %s', params.src_path)

        if params.track_status is not None and params.track_status:
            client = web_client_factory(params.cmd.cli_ctx)
            app = client.web_apps.get(params.resource_group_name, params.webapp_name)
            app_is_linux_webapp = is_linux_webapp(app)

        try:
            with open(os.path.realpath(os.path.expanduser(params.src_path)), 'rb') as fs:
                body = fs.read()
                if app_is_linux_webapp:
                    file_hash = _compute_checksum(body)
        except Exception as e:  # pylint: disable=broad-except
            raise ResourceNotFoundError("Either '{}' is not a valid local file path or you do not have permissions to "
                                        "access it".format(params.src_path)) from e
    elif params.src_url:
        logger.warning('Deploying from URL: %s', params.src_url)
        body = {
            "properties": {
                "packageUri": params.src_url,
                "type": params.artifact_type,
                "path": params.target_path,
                "ignorestack": params.should_ignore_stack,
                "clean": params.is_clean_deployment,
                "restart": params.should_restart,
            }
        }
        body = {"properties": {k: v for k, v in body["properties"].items() if v is not None}}
        body = json.dumps(body)
    else:
        raise ResourceNotFoundError('Unable to determine source location of the artifact being deployed')

    return body, file_hash


def _update_artifact_type(params):
    import os

    if params.artifact_type is not None:
        return

    # Interpret deployment type from the file extension if the type parameter is not passed
    _, file_extension = os.path.splitext(params.src_path)
    file_extension = file_extension[1:]
    if file_extension in ('war', 'jar', 'ear', 'zip'):
        params.artifact_type = file_extension
    elif file_extension in ('sh', 'bat'):
        params.artifact_type = 'startup'
    else:
        params.artifact_type = 'static'
    logger.warning("Deployment type: %s. To override deployment type, please specify the --type parameter. "
                   "Possible values: war, jar, ear, zip, startup, script, static", params.artifact_type)


def _get_instance_id_internal(cmd, resource_group_name, webapp_name, slot):
    from azure.cli.core.commands.client_factory import get_subscription_id
    try:
        client = web_client_factory(cmd.cli_ctx)
        sub_id = get_subscription_id(cmd.cli_ctx)
        if slot:
            base_url = (
                f"subscriptions/{sub_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Web/sites/"
                f"{webapp_name}/slots/{slot}/instances"
                f"?api-version={client.DEFAULT_API_VERSION}"
            )
        else:
            base_url = (
                f"subscriptions/{sub_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Web/sites/"
                f"{webapp_name}/instances?api-version={client.DEFAULT_API_VERSION}"
            )

        url = cmd.cli_ctx.cloud.endpoints.resource_manager + base_url
        response = send_raw_request(cmd.cli_ctx, "GET", url)
        if response.status_code == 200:
            instances = response.json().get("value", [])
            if not instances or len(instances) == 0:
                return None
            sorted_instances = sorted(instances, key=lambda x: x['name'])
            return sorted_instances[0]['name']
        return None
    except Exception as ex:  # pylint: disable=broad-except
        logger.info("Failed to get list of available Kudu instances for deployment. Exception:%s", ex)
        return None


def _warmup_kudu_and_get_cookie_internal(params):
    import requests
    instance_id = _get_instance_id_internal(params.cmd, params.resource_group_name, params.webapp_name, params.slot)

    if instance_id is None:
        logger.info("Failed to get a Kudu instance id...")
        return None
    cookies = {"ARRAffinity": instance_id, "ARRAffinitySameSite": instance_id}
    max_retries = 3
    time_out = 60

    for _ in range(max_retries):
        try:
            if not params.src_url:  # use SCM endpoint for Kudu warmup
                kudu_warmup_url = _build_kudu_warmup_scm_url(params)
                headers = get_scm_site_headers(params.cmd.cli_ctx, params.webapp_name, params.resource_group_name)
                response = requests.get(kudu_warmup_url, headers=headers, cookies=cookies, timeout=time_out)
            else:  # use ARM endpoint for Kudu warmup
                kudu_warmup_url = _build_kudu_warmup_arm_url(params, instance_id)
                response = send_raw_request(params.cmd.cli_ctx, "GET", kudu_warmup_url)

            if response.status_code in (200, 201, 202):
                logger.warning("Warmed up Kudu instance successfully.")
                return cookies
            time_out = 300
        except Exception as ex:  # pylint: disable=broad-except
            logger.info("Error while warming-up Kudu with instanceid: %s, ex: %s", instance_id, ex)
            time_out = 300
    logger.warning("Failed to warm-up Kudu with instanceid: %s, "
                   "the deployment will proceed without pre-warmup.", instance_id)
    return None


def _make_onedeploy_request(params):
    import requests
    from azure.cli.core.util import should_disable_connection_verify

    # Build the request body, headers, API URL and status URL
    body, file_hash = _get_onedeploy_request_body(params)
    deploy_url = _build_onedeploy_url(params)
    deployment_status_url = _get_onedeploy_status_url(params)
    headers = _get_ondeploy_headers(params)

    if file_hash:
        headers["x-ms-artifact-checksum"] = file_hash

    # For debugging purposes only, you can change the async deployment into a sync deployment by polling the API status
    # For that, set poll_async_deployment_for_debugging=True
    logger.info("Deployment API: %s", deploy_url)
    if not params.src_url:  # use SCM endpoint
        # if linux webapp and not function app, then warmup kudu and use warmed up kudu for deployment
        if params.is_linux_webapp and not params.is_functionapp and params.enable_kudu_warmup:
            try:
                logger.warning("Warming up Kudu before deployment.")
                cookies = _warmup_kudu_and_get_cookie_internal(params)
                if cookies is None:
                    logger.info("Failed to fetch affinity cookie for Kudu. "
                                "Deployment will proceed without pre-warming a Kudu instance.")
                    response = requests.post(deploy_url, data=body, headers=headers,
                                             verify=not should_disable_connection_verify())
                else:
                    response = requests.post(deploy_url, data=body, headers=headers, cookies=cookies,
                                             verify=not should_disable_connection_verify())
            except Exception as ex:  # pylint: disable=broad-except
                logger.info("Failed to deploy using affinity cookie. "
                            "Deployment will proceed without pre-warming a Kudu instance. Ex: %s", ex)
                response = requests.post(deploy_url, data=body, headers=headers,
                                         verify=not should_disable_connection_verify())
        else:
            response = requests.post(deploy_url, data=body, headers=headers,
                                     verify=not should_disable_connection_verify())
        poll_async_deployment_for_debugging = True
    else:
        if params.is_linux_webapp and not params.is_functionapp and params.enable_kudu_warmup:
            try:
                logger.warning("Warming up Kudu before deployment.")
                cookies = _warmup_kudu_and_get_cookie_internal(params)
                if cookies is None:
                    logger.info("Failed to fetch affinity cookie for Kudu. "
                                "Deployment will proceed without pre-warming a Kudu instance.")
                    response = send_raw_request(params.cmd.cli_ctx, "PUT", deploy_url, body=body)
                else:
                    deploy_arm_url = _build_onedeploy_url(params, cookies.get("ARRAffinity"))
                    response = send_raw_request(params.cmd.cli_ctx, "PUT", deploy_arm_url, body=body)
            except Exception as ex:  # pylint: disable=broad-except
                logger.info("Failed to deploy using instances endpoint. "
                            "Deployment will proceed without pre-warming a Kudu instance. Ex: %s", ex)
                response = send_raw_request(params.cmd.cli_ctx, "PUT", deploy_url, body=body)
        else:
            response = send_raw_request(params.cmd.cli_ctx, "PUT", deploy_url, body=body)
        poll_async_deployment_for_debugging = False

    # check the status of deployment
    # pylint: disable=too-many-nested-blocks
    if response.status_code == 202 or response.status_code == 200:
        response_body = None
        if poll_async_deployment_for_debugging:
            if params.track_status is not None and params.track_status:
                response_body = _check_runtimestatus_with_deploymentstatusapi(params.cmd, params.resource_group_name,
                                                                              params.webapp_name, params.slot,
                                                                              deployment_status_url,
                                                                              params.is_async_deployment,
                                                                              params.timeout)
            else:
                response_body = _check_zip_deployment_status(params.cmd, params.resource_group_name, params.webapp_name,
                                                             deployment_status_url, params.slot, params.timeout)
            logger.info('Server response: %s', response_body)
        else:
            if 'application/json' in response.headers.get('content-type', ""):
                state = response.json().get("properties", {}).get("provisioningState")
                if state:
                    logger.warning("Deployment status is: \"%s\"", state)
                response_body = response.json().get("properties", {})
        logger.warning("Deployment has completed successfully")
        logger.warning("You can visit your app at: %s", _get_url(params.cmd, params.resource_group_name,
                                                                 params.webapp_name, params.slot))
        return response_body

    # API not available yet!
    if response.status_code == 404:
        raise ResourceNotFoundError("This API isn't available in this environment yet!")

    # check if there's an ongoing process
    if response.status_code == 409:
        raise ValidationError("Another deployment is in progress. Please wait until that process is complete before "
                              "starting a new deployment. You can track the ongoing deployment at {}"
                              .format(deployment_status_url))

    # check if an error occured during deployment
    if response.status_code:
        scm_url = _get_scm_url(params.cmd, params.resource_group_name, params.webapp_name, params.slot)
        latest_deploymentinfo_url = scm_url + "/api/deployments/latest"
        raise CLIError("An error occurred during deployment. Status Code: {}, {} Please visit {}"
                       " to get more information about your deployment"
                       .format(response.status_code, f"Details: {response.text}," if response.text else "",
                               latest_deploymentinfo_url))


# OneDeploy
def _perform_onedeploy_internal(params):

    # Update artifact type, if required
    _update_artifact_type(params)

    # Now make the OneDeploy API call
    logger.warning("Initiating deployment")
    response = _make_onedeploy_request(params)
    return response


def _wait_for_webapp(tunnel_server):
    tries = 0
    while True:
        if is_webapp_up(tunnel_server):
            break
        if tries == 0:
            logger.warning('Connection is not ready yet, please wait')
        if tries == 60:
            raise CLIError('SSH timeout, your app must be running before'
                           ' it can accept SSH connections. '
                           'Use `az webapp log tail` to review the app startup logs.')
        tries = tries + 1
        logger.warning('.')
        time.sleep(1)


def _start_tunnel(tunnel_server):
    tunnel_server.start_server()


def _start_ssh_session(hostname, port, username, password):
    tries = 0
    while True:
        try:
            c = Connection(host=hostname,
                           port=port,
                           user=username,
                           # connect_timeout=60*10,
                           connect_kwargs={"password": password})
            break
        except Exception as ex:  # pylint: disable=broad-except
            logger.info(ex)
            if tries == 0:
                logger.warning('Connection is not ready yet, please wait')
            if tries == 60:
                raise CLIError("Timeout Error, Unable to establish a connection")
            tries = tries + 1
            logger.warning('.')
            time.sleep(1)
    try:
        try:
            c.run('cat /etc/motd', pty=True)
        except invoke.exceptions.UnexpectedExit:
            # Don't crash over a non-existing /etc/motd.
            pass
        c.run('source /etc/profile; exec $SHELL -l', pty=True)
    except Exception as ex:  # pylint: disable=broad-except
        logger.info(ex)
    finally:
        c.close()


def ssh_webapp(cmd, resource_group_name, name, port=None, slot=None, timeout=None, instance=None):  # pylint: disable=too-many-statements
    import platform
    if platform.system() == "Windows":
        webapp = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
        is_linux = webapp.reserved
        if not is_linux:
            raise ValidationError("Only Linux App Service Plans supported, found a Windows App Service Plan")

        scm_url = _get_scm_url(cmd, resource_group_name, name, slot)
        if not instance:
            open_page_in_browser(scm_url + '/webssh/host')
        else:
            open_page_in_browser(scm_url + '/webssh/host?instance={}'.format(instance))
    else:
        config = get_site_configs(cmd, resource_group_name, name, slot)
        if config.remote_debugging_enabled:
            raise ValidationError('Remote debugging is enabled, please disable')
        create_tunnel_and_session(
            cmd, resource_group_name, name, port=port, slot=slot, timeout=timeout, instance=instance)


def _configure_default_logging(cmd, rg_name, name):
    logger.warning("Configuring default logging for the app, if not already enabled")
    return config_diagnostics(cmd, rg_name, name,
                              application_logging=True, web_server_logging='filesystem',
                              docker_container_logging='filesystem')


# TODO remove once appservice-kube extension removes
def _validate_app_service_environment_id(cli_ctx, ase, resource_group_name):
    ase_is_id = is_valid_resource_id(ase)
    if ase_is_id:
        return ase

    from azure.cli.core.commands.client_factory import get_subscription_id
    return resource_id(
        subscription=get_subscription_id(cli_ctx),
        resource_group=resource_group_name,
        namespace='Microsoft.Web',
        type='hostingEnvironments',
        name=ase)


def _format_key_vault_id(cli_ctx, key_vault, resource_group_name):
    key_vault_is_id = is_valid_resource_id(key_vault)
    if key_vault_is_id:
        return key_vault

    from azure.cli.core.commands.client_factory import get_subscription_id
    return resource_id(
        subscription=get_subscription_id(cli_ctx),
        resource_group=resource_group_name,
        namespace='Microsoft.KeyVault',
        type='vaults',
        name=key_vault)


def _verify_hostname_binding(cmd, resource_group_name, name, hostname, slot=None):
    hostname_bindings = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                                'list_host_name_bindings', slot)
    verified_hostname_found = False
    for hostname_binding in hostname_bindings:
        binding_name = hostname_binding.name.split('/')[-1]
        if binding_name.lower() == hostname and (hostname_binding.host_name_type == 'Verified' or
                                                 hostname_binding.host_name_type == 'Managed'):
            verified_hostname_found = True

    return verified_hostname_found


def update_host_key(cmd, resource_group_name, name, key_type, key_name, key_value=None, slot=None):
    # pylint: disable=protected-access
    key_info = KeyInfo(name=key_name, value=key_value)
    KeyInfo._attribute_map = {
        'name': {'key': 'properties.name', 'type': 'str'},
        'value': {'key': 'properties.value', 'type': 'str'},
    }
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        response = client.web_apps.create_or_update_host_secret_slot(resource_group_name,
                                                                     name,
                                                                     key_type,
                                                                     key_name,
                                                                     slot,
                                                                     key=key_info)
    else:
        response = client.web_apps.create_or_update_host_secret(resource_group_name,
                                                                name,
                                                                key_type,
                                                                key_name,
                                                                key=key_info)
    logger.warning('Keys have been redacted. Use `az functionapp keys list` to view.')
    response.value = None
    return response


def list_host_keys(cmd, resource_group_name, name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        return client.web_apps.list_host_keys_slot(resource_group_name, name, slot)
    return client.web_apps.list_host_keys(resource_group_name, name)


def delete_host_key(cmd, resource_group_name, name, key_type, key_name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        return client.web_apps.delete_host_secret_slot(resource_group_name, name, key_type, key_name, slot)
    return client.web_apps.delete_host_secret(resource_group_name, name, key_type, key_name)


def list_functions(cmd, resource_group_name, name):
    client = web_client_factory(cmd.cli_ctx)
    return client.web_apps.list_functions(resource_group_name, name)


def show_function(cmd, resource_group_name, name, function_name):
    client = web_client_factory(cmd.cli_ctx)
    result = client.web_apps.get_function(resource_group_name, name, function_name)
    if result is None:
        return "Function '{}' does not exist in app '{}'".format(function_name, name)
    return result


def delete_function(cmd, resource_group_name, name, function_name):
    client = web_client_factory(cmd.cli_ctx)
    result = client.web_apps.delete_function(resource_group_name, name, function_name)
    return result


def update_function_key(cmd, resource_group_name, name, function_name, key_name, key_value=None, slot=None):
    # pylint: disable=protected-access
    key_info = KeyInfo(name=key_name, value=key_value)
    KeyInfo._attribute_map = {
        'name': {'key': 'properties.name', 'type': 'str'},
        'value': {'key': 'properties.value', 'type': 'str'},
    }
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        response = client.web_apps.create_or_update_function_secret_slot(resource_group_name,
                                                                         name,
                                                                         function_name,
                                                                         key_name,
                                                                         slot,
                                                                         key_info)
    else:
        response = client.web_apps.create_or_update_function_secret(resource_group_name,
                                                                    name,
                                                                    function_name,
                                                                    key_name,
                                                                    key_info)
    logger.warning('Keys have been redacted. Use `az functionapp function keys list` to view.')
    response.value = None
    return response


def list_function_keys(cmd, resource_group_name, name, function_name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        return client.web_apps.list_function_keys_slot(resource_group_name, name, function_name, slot)
    return client.web_apps.list_function_keys(resource_group_name, name, function_name)


def delete_function_key(cmd, resource_group_name, name, key_name, function_name=None, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        return client.web_apps.delete_function_secret_slot(resource_group_name, name, function_name, key_name, slot)
    return client.web_apps.delete_function_secret(resource_group_name, name, function_name, key_name)


def add_github_actions(cmd, resource_group, name, repo, runtime=None, token=None, slot=None,  # pylint: disable=too-many-statements,too-many-branches
                       branch='master', login_with_github=False, force=False):
    runtime = _StackRuntimeHelper(cmd).remove_delimiters(runtime)  # normalize "runtime:version"
    if not token and not login_with_github:
        raise_missing_token_suggestion()
    elif not token:
        scopes = ["admin:repo_hook", "repo", "workflow"]
        token = get_github_access_token(cmd, scopes)
    elif token and login_with_github:
        logger.warning("Both token and --login-with-github flag are provided. Will use provided token")

    # Verify resource group, app
    site_availability = get_site_availability(cmd, name)
    if site_availability.name_available or (not site_availability.name_available and
                                            site_availability.reason == 'Invalid'):
        raise ResourceNotFoundError(
            "The Resource 'Microsoft.Web/sites/%s' under resource group '%s' "
            "was not found." % (name, resource_group))
    app_details = get_app_details(cmd, name)
    if app_details is None:
        raise ResourceNotFoundError(
            "Unable to retrieve details of the existing app %s. Please check that the app is a part of "
            "the current subscription" % name)
    current_rg = app_details.resource_group
    if resource_group is not None and (resource_group.lower() != current_rg.lower()):
        raise ResourceNotFoundError("The webapp %s exists in ResourceGroup %s and does not match the "
                                    "value entered %s. Please re-run command with the correct "
                                    "parameters." % (name, current_rg, resource_group))
    parsed_plan_id = parse_resource_id(app_details.server_farm_id)
    client = web_client_factory(cmd.cli_ctx)
    plan_info = client.app_service_plans.get(parsed_plan_id['resource_group'], parsed_plan_id['name'])
    is_linux = plan_info.reserved

    # Verify github repo
    from github import Github, GithubException
    from github.GithubException import BadCredentialsException, UnknownObjectException

    if repo.strip()[-1] == '/':
        repo = repo.strip()[:-1]

    g = Github(token)
    github_repo = None
    try:
        github_repo = g.get_repo(repo)
        try:
            github_repo.get_branch(branch=branch)
        except GithubException as e:
            error_msg = "Encountered GitHub error when accessing {} branch in {} repo.".format(branch, repo)
            if e.data and e.data['message']:
                error_msg += " Error: {}".format(e.data['message'])
            raise CLIError(error_msg)
        logger.warning('Verified GitHub repo and branch')
    except BadCredentialsException:
        raise ValidationError("Could not authenticate to the repository. Please create a Personal Access Token and use "
                              "the --token argument. Run 'az webapp deployment github-actions add --help' "
                              "for more information.")
    except GithubException as e:
        error_msg = "Encountered GitHub error when accessing {} repo".format(repo)
        if e.data and e.data['message']:
            error_msg += " Error: {}".format(e.data['message'])
        raise CLIError(error_msg)

    # Verify runtime
    app_runtime_info = _get_app_runtime_info(
        cmd=cmd, resource_group=resource_group, name=name, slot=slot, is_linux=is_linux)

    app_runtime_string = None
    if (app_runtime_info and app_runtime_info['display_name']):
        app_runtime_string = app_runtime_info['display_name']

    github_actions_version = None
    if (app_runtime_info and app_runtime_info['github_actions_version']):
        github_actions_version = app_runtime_info['github_actions_version']

    if runtime and app_runtime_string:
        if app_runtime_string.lower() != runtime.lower():
            logger.warning('The app runtime: {app_runtime_string} does not match the runtime specified: '
                           '{runtime}. Using the specified runtime {runtime}.')
            app_runtime_string = runtime
    elif runtime:
        app_runtime_string = runtime

    if not app_runtime_string:
        raise ValidationError('Could not detect runtime. Please specify using the --runtime flag.')

    if not _runtime_supports_github_actions(cmd=cmd, runtime_string=app_runtime_string, is_linux=is_linux):
        raise ValidationError("Runtime %s is not supported for GitHub Actions deployments." % app_runtime_string)

    # Get workflow template
    logger.warning('Getting workflow template using runtime: %s', app_runtime_string)
    workflow_template = _get_workflow_template(github=g, runtime_string=app_runtime_string, is_linux=is_linux)

    # Fill workflow template
    guid = str(uuid.uuid4()).replace('-', '')
    publish_profile_name = "AzureAppService_PublishProfile_{}".format(guid)
    logger.warning(
        'Filling workflow template with name: %s, branch: %s, version: %s, slot: %s',
        name, branch, github_actions_version, slot if slot else 'production')
    completed_workflow_file = _fill_workflow_template(content=workflow_template.decoded_content.decode(), name=name,
                                                      branch=branch, slot=slot, publish_profile=publish_profile_name,
                                                      version=github_actions_version)
    completed_workflow_file = completed_workflow_file.encode()

    # Check if workflow exists in repo, otherwise push
    if slot:
        file_name = "{}_{}({}).yml".format(branch.replace('/', '-'), name.lower(), slot)
    else:
        file_name = "{}_{}.yml".format(branch.replace('/', '-'), name.lower())
    dir_path = "{}/{}".format('.github', 'workflows')
    file_path = "{}/{}".format(dir_path, file_name)
    try:
        existing_workflow_file = github_repo.get_contents(path=file_path, ref=branch)
        existing_publish_profile_name = _get_publish_profile_from_workflow_file(
            workflow_file=str(existing_workflow_file.decoded_content))
        if existing_publish_profile_name:
            completed_workflow_file = completed_workflow_file.decode()
            completed_workflow_file = completed_workflow_file.replace(
                publish_profile_name, existing_publish_profile_name)
            completed_workflow_file = completed_workflow_file.encode()
            publish_profile_name = existing_publish_profile_name
        logger.warning("Existing workflow file found")
        if force:
            logger.warning("Replacing the existing workflow file")
            github_repo.update_file(path=file_path, message="Update workflow using Azure CLI",
                                    content=completed_workflow_file, sha=existing_workflow_file.sha, branch=branch)
        else:
            option = prompt_y_n('Replace existing workflow file?')
            if option:
                logger.warning("Replacing the existing workflow file")
                github_repo.update_file(path=file_path, message="Update workflow using Azure CLI",
                                        content=completed_workflow_file, sha=existing_workflow_file.sha,
                                        branch=branch)
            else:
                logger.warning("Use the existing workflow file")
                if existing_publish_profile_name:
                    publish_profile_name = existing_publish_profile_name
    except UnknownObjectException:
        logger.warning("Creating new workflow file: %s", file_path)
        github_repo.create_file(path=file_path, message="Create workflow using Azure CLI",
                                content=completed_workflow_file, branch=branch)

    # Add publish profile to GitHub
    logger.warning('Adding publish profile to GitHub')
    _add_publish_profile_to_github(cmd=cmd, resource_group=resource_group, name=name, repo=repo,
                                   token=token, github_actions_secret_name=publish_profile_name,
                                   slot=slot)

    # Set site source control properties
    _update_site_source_control_properties_for_gh_action(
        cmd=cmd, resource_group=resource_group, name=name, token=token, repo=repo, branch=branch, slot=slot)

    github_actions_url = "https://github.com/{}/actions".format(repo)
    return github_actions_url


def remove_github_actions(cmd, resource_group, name, repo, token=None, slot=None,  # pylint: disable=too-many-statements
                          branch='master', login_with_github=False):
    if not token and not login_with_github:
        raise_missing_token_suggestion()
    elif not token:
        scopes = ["admin:repo_hook", "repo", "workflow"]
        token = get_github_access_token(cmd, scopes)
    elif token and login_with_github:
        logger.warning("Both token and --login-with-github flag are provided. Will use provided token")

    # Verify resource group, app
    site_availability = get_site_availability(cmd, name)
    if site_availability.name_available or (not site_availability.name_available and
                                            site_availability.reason == 'Invalid'):
        raise ResourceNotFoundError("The Resource 'Microsoft.Web/sites/%s' under resource group '%s' was not found." %
                                    (name, resource_group))
    app_details = get_app_details(cmd, name)
    if app_details is None:
        raise ResourceNotFoundError("Unable to retrieve details of the existing app %s. "
                                    "Please check that the app is a part of the current subscription" % name)
    current_rg = app_details.resource_group
    if resource_group is not None and (resource_group.lower() != current_rg.lower()):
        raise ValidationError("The webapp %s exists in ResourceGroup %s and does not match "
                              "the value entered %s. Please re-run command with the correct "
                              "parameters." % (name, current_rg, resource_group))

    # Verify github repo
    from github import Github, GithubException
    from github.GithubException import BadCredentialsException, UnknownObjectException

    if repo.strip()[-1] == '/':
        repo = repo.strip()[:-1]

    g = Github(token)
    github_repo = None
    try:
        github_repo = g.get_repo(repo)
        try:
            github_repo.get_branch(branch=branch)
        except GithubException as e:
            error_msg = "Encountered GitHub error when accessing {} branch in {} repo.".format(branch, repo)
            if e.data and e.data['message']:
                error_msg += " Error: {}".format(e.data['message'])
            raise CLIError(error_msg)
        logger.warning('Verified GitHub repo and branch')
    except BadCredentialsException:
        raise ValidationError("Could not authenticate to the repository. Please create a Personal Access Token and use "
                              "the --token argument. Run 'az webapp deployment github-actions add --help' "
                              "for more information.")
    except GithubException as e:
        error_msg = "Encountered GitHub error when accessing {} repo".format(repo)
        if e.data and e.data['message']:
            error_msg += " Error: {}".format(e.data['message'])
        raise CLIError(error_msg)

    # Check if workflow exists in repo and remove
    file_name = "{}_{}({}).yml".format(
        branch.replace('/', '-'), name.lower(), slot) if slot else "{}_{}.yml".format(
            branch.replace('/', '-'), name.lower())
    dir_path = "{}/{}".format('.github', 'workflows')
    file_path = "{}/{}".format(dir_path, file_name)
    existing_publish_profile_name = None
    try:
        existing_workflow_file = github_repo.get_contents(path=file_path, ref=branch)
        existing_publish_profile_name = _get_publish_profile_from_workflow_file(
            workflow_file=str(existing_workflow_file.decoded_content))
        logger.warning("Removing the existing workflow file")
        github_repo.delete_file(path=file_path, message="Removing workflow file, disconnecting github actions",
                                sha=existing_workflow_file.sha, branch=branch)
    except UnknownObjectException as e:
        error_msg = "Error when removing workflow file."
        if e.data and e.data['message']:
            error_msg += " Error: {}".format(e.data['message'])
        raise CLIError(error_msg)

    # Remove publish profile from GitHub
    if existing_publish_profile_name:
        logger.warning('Removing publish profile from GitHub')
        _remove_publish_profile_from_github(cmd=cmd, resource_group=resource_group, name=name, repo=repo, token=token,
                                            github_actions_secret_name=existing_publish_profile_name, slot=slot)

    # Remove site source control properties
    delete_source_control(cmd=cmd,
                          resource_group_name=resource_group,
                          name=name,
                          slot=slot)

    return "Disconnected successfully."


def add_functionapp_github_actions(cmd, resource_group, name, repo, runtime=None, runtime_version=None, token=None,  # pylint: disable=too-many-statements,too-many-branches
                                   slot=None, branch='master', build_path=".", login_with_github=False, force=False):
    if login_with_github:
        token = get_github_access_token(cmd, ["admin:repo_hook", "repo", "workflow"], token)
    repo = repo_url_to_name(repo)
    token = get_token(cmd, repo, token)

    # Verify resource group, app
    site_availability = get_site_availability(cmd, name)
    if site_availability.name_available or (not site_availability.name_available and
                                            site_availability.reason == 'Invalid'):
        raise ResourceNotFoundError(
            "The Resource 'Microsoft.Web/sites/%s' under resource group '%s' "
            "was not found." % (name, resource_group))
    app_details = get_app_details(cmd, name)
    if app_details is None:
        raise ResourceNotFoundError(
            "Unable to retrieve details of the existing app %s. Please check that the app is a part of "
            "the current subscription" % name)
    current_rg = app_details.resource_group
    if resource_group is not None and (resource_group.lower() != current_rg.lower()):
        raise ResourceNotFoundError("The webapp %s exists in ResourceGroup %s and does not match the "
                                    "value entered %s. Please re-run command with the correct "
                                    "parameters." % (name, current_rg, resource_group))

    app = show_app(cmd, resource_group, name, slot)
    is_linux = app.reserved

    # Verify github repo
    from github import Github, GithubException
    from github.GithubException import BadCredentialsException, UnknownObjectException

    if repo.strip()[-1] == '/':
        repo = repo.strip()[:-1]

    g = Github(token)
    github_repo = None
    try:
        github_repo = g.get_repo(repo)
        try:
            github_repo.get_branch(branch=branch)
        except GithubException as e:
            error_msg = "Encountered GitHub error when accessing {} branch in {} repo.".format(branch, repo)
            if e.data and e.data['message']:
                error_msg += " Error: {}".format(e.data['message'])
            raise ValidationError(error_msg)
        logger.warning('Verified GitHub repo and branch')
    except BadCredentialsException:
        raise ValidationError("Could not authenticate to the repository. Please create a Personal Access Token and use "
                              "the --token argument. Run 'az functionapp deployment github-actions add --help' "
                              "for more information.")
    except GithubException as e:
        error_msg = "Encountered GitHub error when accessing {} repo".format(repo)
        if e.data and e.data['message']:
            error_msg += " Error: {}".format(e.data['message'])
        raise ValidationError(error_msg)

    # Get runtime info
    app_runtime_info = _get_functionapp_runtime_info(
        cmd=cmd, resource_group=resource_group, name=name, slot=slot, is_linux=is_linux)

    app_runtime_string = app_runtime_info['app_runtime']
    github_actions_version = app_runtime_info['app_runtime_version']

    if runtime:
        if app_runtime_string and app_runtime_string.lower() != runtime.lower():
            logger.warning('The app runtime: %s does not match the runtime specified: '
                           '%s. Using the specified runtime %s.', app_runtime_string, runtime, runtime)
        app_runtime_string = runtime

    if runtime_version:
        if github_actions_version and github_actions_version.lower() != runtime_version.lower():
            logger.warning('The app runtime version: %s does not match the runtime version specified: '
                           '%s. Using the specified runtime %s.', github_actions_version, runtime_version,
                           runtime_version)
        github_actions_version = runtime_version

    if not app_runtime_string and not github_actions_version:
        raise ValidationError('Could not detect runtime or runtime version. Please specify'
                              'using the --runtime and --runtime-version flags.')
    if not app_runtime_string:
        raise ValidationError('Could not detect runtime. Please specify using the --runtime flag.')
    if not github_actions_version:
        raise ValidationError('Could not detect runtime version. Please specify using the --runtime-version flag.')

    # Verify runtime + gh actions support
    functionapp_version = app_runtime_info['functionapp_version']
    location = app.location
    github_actions_version = _get_functionapp_runtime_version(cmd=cmd, location=location,
                                                              name=name,
                                                              resource_group=resource_group,
                                                              runtime_string=app_runtime_string,
                                                              runtime_version=github_actions_version,
                                                              functionapp_version=functionapp_version,
                                                              is_linux=is_linux)
    if not github_actions_version:
        runtime_version = runtime_version if runtime_version else app_runtime_info['app_runtime_version']
        raise ValidationError("Runtime %s version %s is not supported for GitHub Actions deployments "
                              "on os %s." % (app_runtime_string, runtime_version,
                                             "linux" if is_linux else "windows"))

    # Get workflow template
    logger.warning('Getting workflow template using runtime: %s', app_runtime_string)
    workflow_template = _get_functionapp_workflow_template(github=g, runtime_string=app_runtime_string,
                                                           is_linux=is_linux)

    # Fill workflow template
    guid = str(uuid.uuid4()).replace('-', '')
    publish_profile_name = "AZURE_FUNCTIONAPP_PUBLISH_PROFILE_{}".format(guid)
    logger.warning(
        'Filling workflow template with name: %s, branch: %s, version: %s, slot: %s, build_path: %s',
        name, branch, github_actions_version, slot if slot else 'production', build_path)
    completed_workflow_file = _fill_functionapp_workflow_template(content=workflow_template.decoded_content.decode(),
                                                                  name=name, build_path=build_path,
                                                                  version=github_actions_version,
                                                                  publish_profile=publish_profile_name,
                                                                  repo=repo, branch=branch, token=token)
    completed_workflow_file = completed_workflow_file.encode()

    def add_publish_profile(cmd, resource_group, name, repo, token, publish_profile_name, slot):
        logger.warning('Adding publish profile to GitHub')
        _add_publish_profile_to_github(cmd=cmd, resource_group=resource_group, name=name, repo=repo,
                                       token=token, github_actions_secret_name=publish_profile_name,
                                       slot=slot)

    def update_file(cmd,
                    resource_group,
                    name,
                    repo,
                    token,
                    publish_profile_name,
                    slot,
                    logger_message,
                    github_repo,
                    github_message,
                    file_path,
                    completed_workflow_file,
                    existing_workflow_file,
                    branch):
        add_publish_profile(cmd, resource_group, name, repo, token, publish_profile_name, slot)
        logger.warning(logger_message)
        github_repo.update_file(path=file_path, message=github_message,
                                content=completed_workflow_file, sha=existing_workflow_file.sha,
                                branch=branch)

    # Check if workflow exists in repo, otherwise push
    if slot:
        file_name = "{}_{}({}).yml".format(branch.replace('/', '-'), name.lower(), slot)
    else:
        file_name = "{}_{}.yml".format(branch.replace('/', '-'), name.lower())
    dir_path = "{}/{}".format('.github', 'workflows')
    file_path = "{}/{}".format(dir_path, file_name)
    try:
        existing_workflow_file = github_repo.get_contents(path=file_path, ref=branch)
        existing_publish_profile_name = _get_publish_profile_from_workflow_file(
            workflow_file=str(existing_workflow_file.decoded_content))
        if existing_publish_profile_name:
            completed_workflow_file = completed_workflow_file.decode()
            completed_workflow_file = completed_workflow_file.replace(
                publish_profile_name, existing_publish_profile_name)
            completed_workflow_file = completed_workflow_file.encode()
            publish_profile_name = existing_publish_profile_name
        logger.warning("Existing workflow file found")
        if force:
            update_file(cmd,
                        resource_group,
                        name,
                        repo,
                        token,
                        publish_profile_name,
                        slot,
                        "Replacing the existing workflow file",
                        github_repo,
                        "Update workflow using Azure CLI",
                        file_path,
                        completed_workflow_file,
                        existing_workflow_file,
                        branch)
        else:
            option = prompt_y_n('Replace existing workflow file?')
            if option:
                update_file(cmd,
                            resource_group,
                            name,
                            repo,
                            token,
                            publish_profile_name,
                            slot,
                            "Replacing the existing workflow file",
                            github_repo,
                            "Update workflow using Azure CLI",
                            file_path,
                            completed_workflow_file,
                            existing_workflow_file,
                            branch)
            else:
                logger.warning("Use the existing workflow file")
                if existing_publish_profile_name:
                    publish_profile_name = existing_publish_profile_name
                add_publish_profile(cmd, resource_group, name, repo, token, publish_profile_name, slot)
    except UnknownObjectException:
        add_publish_profile(cmd, resource_group, name, repo, token, publish_profile_name, slot)
        logger.warning("Creating new workflow file: %s", file_path)
        github_repo.create_file(path=file_path, message="Create workflow using Azure CLI",
                                content=completed_workflow_file, branch=branch)

    # Set site source control properties
    _update_site_source_control_properties_for_gh_action(
        cmd=cmd, resource_group=resource_group, name=name, token=token, repo=repo, branch=branch, slot=slot)

    cache_github_token(cmd, token, repo)
    github_actions_url = "https://github.com/{}/actions".format(repo)
    return github_actions_url


def remove_functionapp_github_actions(cmd, resource_group, name, repo, token=None, slot=None,  # pylint: disable=too-many-statements
                                      branch='master', login_with_github=False):
    if login_with_github:
        token = get_github_access_token(cmd, ["admin:repo_hook", "repo", "workflow"], token)
    repo = repo_url_to_name(repo)
    token = get_token(cmd, repo, token)
    # Verify resource group, app
    site_availability = get_site_availability(cmd, name)
    if site_availability.name_available or (not site_availability.name_available and
                                            site_availability.reason == 'Invalid'):
        raise ResourceNotFoundError("The Resource 'Microsoft.Web/sites/%s' under resource group '%s' was not found." %
                                    (name, resource_group))
    app_details = get_app_details(cmd, name)
    if app_details is None:
        raise ResourceNotFoundError("Unable to retrieve details of the existing app %s. "
                                    "Please check that the app is a part of the current subscription" % name)
    current_rg = app_details.resource_group
    if resource_group is not None and (resource_group.lower() != current_rg.lower()):
        raise ValidationError("The functionapp %s exists in ResourceGroup %s and does not match "
                              "the value entered %s. Please re-run command with the correct "
                              "parameters." % (name, current_rg, resource_group))

    # Verify github repo
    from github import Github, GithubException
    from github.GithubException import BadCredentialsException, UnknownObjectException

    if repo.strip()[-1] == '/':
        repo = repo.strip()[:-1]

    g = Github(token)
    github_repo = None
    try:
        github_repo = g.get_repo(repo)
        try:
            github_repo.get_branch(branch=branch)
        except GithubException as e:
            error_msg = "Encountered GitHub error when accessing {} branch in {} repo.".format(branch, repo)
            if e.data and e.data['message']:
                error_msg += " Error: {}".format(e.data['message'])
            raise ValidationError(error_msg)
        logger.warning('Verified GitHub repo and branch')
    except BadCredentialsException:
        raise ValidationError("Could not authenticate to the repository. Please create a Personal Access Token and use "
                              "the --token argument. Run 'az functionapp deployment github-actions remove --help' "
                              "for more information.")
    except GithubException as e:
        error_msg = "Encountered GitHub error when accessing {} repo".format(repo)
        if e.data and e.data['message']:
            error_msg += " Error: {}".format(e.data['message'])
        raise ValidationError(error_msg)

    # Check if workflow exists in repo and remove
    file_name = "{}_{}({}).yml".format(
        branch.replace('/', '-'), name.lower(), slot) if slot else "{}_{}.yml".format(
            branch.replace('/', '-'), name.lower())
    dir_path = "{}/{}".format('.github', 'workflows')
    file_path = "{}/{}".format(dir_path, file_name)
    existing_publish_profile_name = None
    try:
        existing_workflow_file = github_repo.get_contents(path=file_path, ref=branch)
        existing_publish_profile_name = _get_publish_profile_from_workflow_file(
            workflow_file=str(existing_workflow_file.decoded_content))
        logger.warning("Removing the existing workflow file")
        github_repo.delete_file(path=file_path, message="Removing workflow file, disconnecting github actions",
                                sha=existing_workflow_file.sha, branch=branch)
    except UnknownObjectException as e:
        error_msg = "Error when removing workflow file."
        if e.data and e.data['message']:
            error_msg += " Error: {}".format(e.data['message'])
        raise FileOperationError(error_msg)

    # Remove publish profile from GitHub
    if existing_publish_profile_name:
        logger.warning('Removing publish profile from GitHub')
        _remove_publish_profile_from_github(cmd=cmd, resource_group=resource_group, name=name, repo=repo, token=token,
                                            github_actions_secret_name=existing_publish_profile_name, slot=slot)

    # Remove site source control properties
    delete_source_control(cmd=cmd,
                          resource_group_name=resource_group,
                          name=name,
                          slot=slot)

    return "Disconnected successfully."


def _get_publish_profile_from_workflow_file(workflow_file):
    publish_profile = None
    regex = re.search(r'publish-profile: \$\{\{ secrets\..*?\}\}', workflow_file)
    if regex:
        publish_profile = regex.group()
        publish_profile = publish_profile.replace('publish-profile: ${{ secrets.', '')
        publish_profile = publish_profile[:-2]

    if publish_profile:
        return publish_profile.strip()
    return None


def _update_site_source_control_properties_for_gh_action(cmd, resource_group, name, token, repo=None,
                                                         branch="master", slot=None):
    if repo:
        repo_url = 'https://github.com/' + repo
    else:
        repo_url = None

    site_source_control = show_source_control(cmd=cmd,
                                              resource_group_name=resource_group,
                                              name=name,
                                              slot=slot)
    if site_source_control:
        if not repo_url:
            repo_url = site_source_control.repo_url

    delete_source_control(cmd=cmd,
                          resource_group_name=resource_group,
                          name=name,
                          slot=slot)
    config_source_control(cmd=cmd,
                          resource_group_name=resource_group,
                          name=name,
                          repo_url=repo_url,
                          repository_type='github',
                          github_action=True,
                          branch=branch,
                          git_token=token,
                          slot=slot)


def _get_workflow_template(github, runtime_string, is_linux):
    from github import GithubException
    from github.GithubException import BadCredentialsException

    file_contents = None
    template_repo_path = 'Azure/actions-workflow-templates'
    template_file_path = _get_template_file_path(runtime_string=runtime_string, is_linux=is_linux)

    try:
        template_repo = github.get_repo(template_repo_path)
        file_contents = template_repo.get_contents(template_file_path)
    except BadCredentialsException:
        raise CLIError("Could not authenticate to the repository. Please create a Personal Access Token and use "
                       "the --token argument. Run 'az webapp deployment github-actions add --help' "
                       "for more information.")
    except GithubException as e:
        error_msg = "Encountered GitHub error when retrieving workflow template"
        if e.data and e.data['message']:
            error_msg += ": {}".format(e.data['message'])
        raise CLIError(error_msg)
    return file_contents


def _get_functionapp_workflow_template(github, runtime_string, is_linux):
    from github import GithubException

    file_contents = None
    template_repo_path = 'Azure/actions-workflow-samples'
    template_path_map = (LINUX_FUNCTIONAPP_GITHUB_ACTIONS_WORKFLOW_TEMPLATE_PATH if is_linux else
                         WINDOWS_FUNCTIONAPP_GITHUB_ACTIONS_WORKFLOW_TEMPLATE_PATH)
    template_file_path = _get_functionapp_template_file_path(runtime_string=runtime_string,
                                                             template_path_map=template_path_map)

    try:
        template_repo = github.get_repo(template_repo_path)
        file_contents = template_repo.get_contents(template_file_path)
    except GithubException as e:
        error_msg = "Encountered GitHub error when retrieving workflow template"
        if e.data and e.data['message']:
            error_msg += ": {}".format(e.data['message'])
        raise CLIError(error_msg)
    return file_contents


def _fill_workflow_template(content, name, branch, slot, publish_profile, version):
    if not slot:
        slot = 'production'

    content = content.replace('${web-app-name}', name)
    content = content.replace('${branch}', branch)
    content = content.replace('${slot-name}', slot)
    content = content.replace('${azure-webapp-publish-profile-name}', publish_profile)
    content = content.replace('${AZURE_WEBAPP_PUBLISH_PROFILE}', publish_profile)
    content = content.replace('${dotnet-core-version}', version)
    content = content.replace('${java-version}', version)
    content = content.replace('${node-version}', version)
    content = content.replace('${python-version}', version)
    return content


def _get_pom_xml_content(repo, branch, token, pom_path="."):
    from github import Github
    import requests

    g = Github(token)
    try:
        r = g.get_repo(repo)
        if not branch:
            branch = r.default_branch
    except Exception as e:
        raise ValidationError(f"Could not find repo {repo}") from e
    try:
        files = r.get_contents(pom_path, ref=branch)
    except Exception as e:
        raise ValidationError(f"Could not find path {pom_path} in branch {branch}") from e
    for f in files:
        if f.path == "pom.xml" or f.path.endswith("/pom.xml"):
            resp = requests.get(f.download_url)
            if resp.ok and resp.content:
                return resp.content.decode("utf-8")
    raise ValidationError("Could not find pom.xml in Github repo/branch. Please ensure it is named 'pom.xml'. "
                          "Set the path with --build-path if not in the root directory.")


def _get_pom_functionapp_name(pom_content: str):
    root = ElementTree.fromstring(pom_content)
    m = re.match(r'\{.*\}', root.tag)
    namespace = m.group(0) if m else ''
    pom_properties = root.find(f"{namespace}properties")
    if pom_properties:
        return pom_properties.find(f"{namespace}functionAppName").text


def _fill_functionapp_workflow_template(content, name, build_path, version, publish_profile, repo, branch, token):
    content = content.replace("AZURE_FUNCTIONAPP_PUBLISH_PROFILE", f"{publish_profile}")
    content = content.replace("AZURE_FUNCTIONAPP_NAME: your-app-name", f"AZURE_FUNCTIONAPP_NAME: '{name}'")
    if "POM_FUNCTIONAPP_NAME" in content:
        pom_app_name = _get_pom_functionapp_name(_get_pom_xml_content(repo, branch, token, build_path))
        content = content.replace("POM_FUNCTIONAPP_NAME: your-app-name", f"POM_FUNCTIONAPP_NAME: '{pom_app_name}'")
    if "AZURE_FUNCTIONAPP_PACKAGE_PATH" not in content and "POM_XML_DIRECTORY" not in content:
        logger.warning("Runtime does not support --build-path, ignoring value.")
    content = content.replace("AZURE_FUNCTIONAPP_PACKAGE_PATH: '.'", f"AZURE_FUNCTIONAPP_PACKAGE_PATH: '{build_path}'")
    content = content.replace("POM_XML_DIRECTORY: '.'", f"POM_XML_DIRECTORY: '{build_path}'")
    content = content.replace("runs-on: ubuntu-18.04", "")  # repair linux python yaml
    if version:
        content = content.replace("DOTNET_VERSION: '2.2.402'", f"DOTNET_VERSION: '{version}'")
        content = content.replace("JAVA_VERSION: '1.8.x'", f"JAVA_VERSION: '{version}'")
        content = content.replace("NODE_VERSION: '10.x'", f"NODE_VERSION: '{version}'")
        content = content.replace("PYTHON_VERSION: '3.7'", f"PYTHON_VERSION: '{version}'")
    return content


def _get_template_file_path(runtime_string, is_linux):
    if not runtime_string:
        raise ResourceNotFoundError('Unable to retrieve workflow template')

    runtime_string = runtime_string.lower()
    runtime_stack = runtime_string.split('|')[0]
    template_file_path = None

    if is_linux:
        template_file_path = LINUX_GITHUB_ACTIONS_WORKFLOW_TEMPLATE_PATH.get(runtime_stack, None)
    else:
        # Handle java naming
        if runtime_stack == 'java':
            java_container_split = runtime_string.split('|')
            if java_container_split and len(java_container_split) >= 2:
                if java_container_split[2] == 'tomcat':
                    runtime_stack = 'tomcat'
                elif java_container_split[2] == 'java se':
                    runtime_stack = 'java'
        template_file_path = WINDOWS_GITHUB_ACTIONS_WORKFLOW_TEMPLATE_PATH.get(runtime_stack, None)

    if not template_file_path:
        raise ResourceNotFoundError('Unable to retrieve workflow template.')
    return template_file_path


def _get_functionapp_template_file_path(runtime_string, template_path_map):
    if not runtime_string:
        raise ResourceNotFoundError('Unable to retrieve workflow template')

    runtime_string = runtime_string.lower()
    runtime_stack = runtime_string.split('|')[0]
    template_file_path = None

    template_file_path = template_path_map.get(runtime_stack)

    if not template_file_path:
        raise ResourceNotFoundError('Unable to retrieve workflow template.')
    return template_file_path


def _add_publish_profile_to_github(cmd, resource_group, name, repo, token, github_actions_secret_name, slot=None):
    # Get publish profile with secrets
    import requests

    logger.warning("Fetching publish profile with secrets for the app '%s'", name)
    publish_profile_bytes = _generic_site_operation(
        cmd.cli_ctx, resource_group, name, 'list_publishing_profile_xml_with_secrets',
        slot, {"format": "WebDeploy"})
    publish_profile = list(publish_profile_bytes)
    if publish_profile:
        publish_profile = publish_profile[0].decode('ascii')
    else:
        raise ResourceNotFoundError('Unable to retrieve publish profile.')

    # Add publish profile with secrets as a GitHub Actions Secret in the repo
    headers = {}
    headers['Authorization'] = 'Token {}'.format(token)
    headers['Content-Type'] = 'application/json;'
    headers['Accept'] = 'application/json;'

    public_key_url = "https://api.github.com/repos/{}/actions/secrets/public-key".format(repo)
    public_key = requests.get(public_key_url, headers=headers)
    if not public_key.ok:
        raise ValidationError('Request to GitHub for public key failed.')
    public_key = public_key.json()

    encrypted_github_actions_secret = _encrypt_github_actions_secret(public_key=public_key['key'],
                                                                     secret_value=str(publish_profile))
    payload = {
        "encrypted_value": encrypted_github_actions_secret,
        "key_id": public_key['key_id']
    }

    store_secret_url = "https://api.github.com/repos/{}/actions/secrets/{}".format(repo, github_actions_secret_name)
    stored_secret = requests.put(store_secret_url, data=json.dumps(payload), headers=headers)
    if str(stored_secret.status_code)[0] != '2':
        raise CLIError('Unable to add publish profile to GitHub. Request status code: %s' % stored_secret.status_code)


def _remove_publish_profile_from_github(cmd, resource_group, name, repo, token, github_actions_secret_name, slot=None):
    headers = {}
    headers['Authorization'] = 'Token {}'.format(token)

    import requests
    store_secret_url = "https://api.github.com/repos/{}/actions/secrets/{}".format(repo, github_actions_secret_name)
    requests.delete(store_secret_url, headers=headers)


def _runtime_supports_github_actions(cmd, runtime_string, is_linux):
    helper = _StackRuntimeHelper(cmd, linux=is_linux, windows=not is_linux)
    matched_runtime = helper.resolve(runtime_string, is_linux)
    if not matched_runtime:
        return False
    if matched_runtime.github_actions_properties:
        return True
    return False


def _get_functionapp_runtime_version(cmd, location, name, resource_group, runtime_string,
                                     runtime_version, functionapp_version, is_linux):
    runtime_version = re.sub(r"[^\d\.]", "", runtime_version).rstrip('.')
    matched_runtime = None
    is_flex = is_flex_functionapp(cmd.cli_ctx, resource_group, name)

    try:
        if not is_flex:
            helper = _FunctionAppStackRuntimeHelper(cmd, linux=is_linux, windows=not is_linux)
            matched_runtime = helper.resolve(runtime_string, runtime_version, functionapp_version, is_linux)
        else:
            runtime_helper = _FlexFunctionAppStackRuntimeHelper(cmd, location, runtime_string, runtime_version)
            matched_runtime = runtime_helper.resolve(runtime_string, runtime_version)
    except ValidationError as e:
        if "Invalid version" in e.error_msg:
            index = e.error_msg.index("Run 'az functionapp list-runtimes' for more details on supported runtimes.")
            error_message = e.error_msg[0:index]
            error_message += "Try passing --runtime-version with a supported version, or "
            error_message += e.error_msg[index:].lower()
            raise ValidationError(error_message)
        raise e

    if not matched_runtime:
        return None
    if matched_runtime.github_actions_properties:
        gh_props = matched_runtime.github_actions_properties
        if gh_props.is_supported:
            return gh_props.supported_version if gh_props.supported_version else runtime_version
    return None


def _get_app_runtime_info(cmd, resource_group, name, slot, is_linux):
    app_settings = None
    app_runtime = None

    if is_linux:
        app_metadata = get_site_configs(cmd=cmd, resource_group_name=resource_group, name=name, slot=slot)
        app_runtime = getattr(app_metadata, 'linux_fx_version', None)
        return _get_app_runtime_info_helper(cmd, app_runtime, "", is_linux)

    app_metadata = _generic_site_operation(cmd.cli_ctx, resource_group, name, 'list_metadata', slot)
    app_metadata_properties = getattr(app_metadata, 'properties', {})
    if 'CURRENT_STACK' in app_metadata_properties:
        app_runtime = app_metadata_properties['CURRENT_STACK']

    # TODO try and get better API support for windows stacks
    if app_runtime and app_runtime.lower() == 'node':
        app_settings = get_app_settings(cmd=cmd, resource_group_name=resource_group, name=name, slot=slot)
        for app_setting in app_settings:
            if 'name' in app_setting and app_setting['name'] == 'WEBSITE_NODE_DEFAULT_VERSION':
                app_runtime_version = app_setting['value'] if 'value' in app_setting else None
                if app_runtime_version:
                    return _get_app_runtime_info_helper(cmd, app_runtime, app_runtime_version, is_linux)
    elif app_runtime and app_runtime.lower() == 'python':
        app_settings = get_site_configs(cmd=cmd, resource_group_name=resource_group, name=name, slot=slot)
        app_runtime_version = getattr(app_settings, 'python_version', '')
        return _get_app_runtime_info_helper(cmd, app_runtime, app_runtime_version, is_linux)
    elif app_runtime and app_runtime.lower() == 'dotnetcore':
        app_runtime_version = '3.1'
        app_runtime_version = ""
        return _get_app_runtime_info_helper(cmd, app_runtime, app_runtime_version, is_linux)
    elif app_runtime and app_runtime.lower() == 'java':
        app_settings = get_site_configs(cmd=cmd, resource_group_name=resource_group, name=name, slot=slot)
        app_runtime_version = "{java_version}, {java_container}, {java_container_version}".format(
            java_version=getattr(app_settings, 'java_version', '').lower(),
            java_container=getattr(app_settings, 'java_container', '').lower(),
            java_container_version=getattr(app_settings, 'java_container_version', '').lower()
        )
        return _get_app_runtime_info_helper(cmd, app_runtime, app_runtime_version, is_linux)


def _get_functionapp_runtime_info(cmd, resource_group, name, slot, is_linux):  # pylint: disable=too-many-return-statements
    app_settings = None
    app_runtime = None
    functionapp_version = None
    app_runtime_version = None

    app_settings = get_app_settings(cmd=cmd, resource_group_name=resource_group, name=name, slot=slot)
    for app_setting in app_settings:
        if 'name' in app_setting and app_setting['name'] == 'FUNCTIONS_EXTENSION_VERSION':
            functionapp_version = app_setting["value"]
            break

    if is_flex_functionapp(cmd.cli_ctx, resource_group, name):
        app_runtime_config = get_runtime_config(cmd, resource_group, name)
        app_runtime = app_runtime_config.get("name", "")
        app_runtime_version = app_runtime_config.get("version", "")
        return _get_functionapp_runtime_info_helper(cmd, app_runtime, app_runtime_version, "~4", None)

    if is_linux:
        app_metadata = get_site_configs(cmd=cmd, resource_group_name=resource_group, name=name, slot=slot)
        app_runtime = getattr(app_metadata, 'linux_fx_version', None)
        return _get_functionapp_runtime_info_helper(cmd, app_runtime, None, functionapp_version, is_linux)

    app_settings = get_app_settings(cmd=cmd, resource_group_name=resource_group, name=name, slot=slot)
    for app_setting in app_settings:
        if 'name' in app_setting and app_setting['name'] == 'FUNCTIONS_WORKER_RUNTIME':
            app_runtime = app_setting["value"]
            break

    if app_runtime and app_runtime.lower() == 'node':
        app_settings = get_app_settings(cmd=cmd, resource_group_name=resource_group, name=name, slot=slot)
        for app_setting in app_settings:
            if 'name' in app_setting and app_setting['name'] == 'WEBSITE_NODE_DEFAULT_VERSION':
                app_runtime_version = app_setting['value'] if 'value' in app_setting else None
                if app_runtime_version:
                    return _get_functionapp_runtime_info_helper(cmd, app_runtime, app_runtime_version,
                                                                functionapp_version, is_linux)
    elif app_runtime and app_runtime.lower() == 'python':
        app_settings = get_site_configs(cmd=cmd, resource_group_name=resource_group, name=name, slot=slot)
        app_runtime_version = getattr(app_settings, 'python_version', '')
        return _get_functionapp_runtime_info_helper(cmd, app_runtime, app_runtime_version, functionapp_version,
                                                    is_linux)
    elif app_runtime and app_runtime.lower() == 'dotnet':
        app_settings = get_site_configs(cmd=cmd, resource_group_name=resource_group, name=name, slot=slot)
        app_runtime_version = getattr(app_settings, 'net_framework_version', '')
        return _get_functionapp_runtime_info_helper(cmd, app_runtime, app_runtime_version, functionapp_version,
                                                    is_linux)
    elif app_runtime and app_runtime.lower() == 'java':
        app_settings = get_site_configs(cmd=cmd, resource_group_name=resource_group, name=name, slot=slot)
        app_runtime_version = getattr(app_settings, 'java_version', '').lower()
        return _get_functionapp_runtime_info_helper(cmd, app_runtime, app_runtime_version, functionapp_version,
                                                    is_linux)
    elif app_runtime and app_runtime.lower() == 'powershell':
        app_settings = get_site_configs(cmd=cmd, resource_group_name=resource_group, name=name, slot=slot)
        app_runtime_version = getattr(app_settings, 'power_shell_version', '').lower()
        return _get_functionapp_runtime_info_helper(cmd, app_runtime, app_runtime_version, functionapp_version,
                                                    is_linux)
    return _get_functionapp_runtime_info_helper(cmd, app_runtime, app_runtime_version, functionapp_version, is_linux)


def _get_app_runtime_info_helper(cmd, app_runtime, app_runtime_version, is_linux):
    helper = _StackRuntimeHelper(cmd, linux=is_linux, windows=not is_linux)
    if not is_linux:
        matched_runtime = helper.resolve("{}|{}".format(app_runtime, app_runtime_version), is_linux)
    else:
        matched_runtime = helper.resolve(app_runtime, is_linux)
    gh_props = None if not matched_runtime else matched_runtime.github_actions_properties
    if gh_props:
        if gh_props.get("github_actions_version"):
            if is_linux:
                return {
                    "display_name": app_runtime,
                    "github_actions_version": gh_props["github_actions_version"]
                }
            if gh_props.get("app_runtime_version").lower() == app_runtime_version.lower():
                return {
                    "display_name": app_runtime,
                    "github_actions_version": gh_props["github_actions_version"]
                }
    return None


def _get_functionapp_runtime_info_helper(cmd, app_runtime, app_runtime_version, functionapp_version, is_linux):
    if is_linux:
        if len(app_runtime.split('|')) < 2:
            raise ValidationError("Could not detect runtime. To configure linuxFxVersion, "
                                  "please visit https://aka.ms/linuxFxVersion")
        app_runtime_version = app_runtime.split('|')[1]
        app_runtime = app_runtime.split('|')[0].lower()

    # Normalize versions
    functionapp_version = functionapp_version if functionapp_version else ""
    app_runtime_version = app_runtime_version if app_runtime_version else ""
    functionapp_version = re.sub(r"[^\d\.]", "", functionapp_version)
    app_runtime_version = re.sub(r"[^\d\.]", "", app_runtime_version)

    return {
        "app_runtime": app_runtime,
        "app_runtime_version": app_runtime_version,
        "functionapp_version": functionapp_version
    }


def _encrypt_github_actions_secret(public_key, secret_value):
    # Encrypt a Unicode string using the public key
    from base64 import b64encode
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


def show_webapp(cmd, resource_group_name, name, slot=None):  # adding this to not break extensions
    return show_app(cmd, resource_group_name, name, slot)


def _compute_checksum(input_bytes):
    file_hash = None
    try:
        import hashlib
        logger.info("Computing checksum of the file ...")
        file_hash = hashlib.sha256(input_bytes).hexdigest()
        logger.info("Computed checksum for deployment request header x-ms-artifact-checksum '%s'", file_hash)
    except Exception as ex:  # pylint: disable=broad-except
        logger.info("Computing the checksum of the file failed with exception:'%s'", ex)

    return file_hash
