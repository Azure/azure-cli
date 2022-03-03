# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import ast
import threading
import time

from urllib.parse import urlparse
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

import OpenSSL.crypto
from fabric import Connection

from knack.prompting import prompt_pass, NoTTYException, prompt_y_n
from knack.util import CLIError
from knack.log import get_logger

from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import is_valid_resource_id, parse_resource_id, resource_id

from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.applicationinsights import ApplicationInsightsManagementClient
from azure.mgmt.relay.models import AccessRights
from azure.mgmt.web.models import KeyInfo
from azure.cli.command_modules.relay._client_factory import hycos_mgmt_client_factory, namespaces_mgmt_client_factory
from azure.cli.command_modules.network._client_factory import network_client_factory

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.util import in_cloud_console, shell_safe_json_parse, open_page_in_browser, get_json_object, \
    ConfiguredDefaultSetter, sdk_no_wait
from azure.cli.core.util import get_az_user_agent, send_raw_request, get_file_json
from azure.cli.core.profiles import ResourceType, get_sdk
from azure.cli.core.azclierror import (InvalidArgumentValueError, MutuallyExclusiveArgumentError, ResourceNotFoundError,
                                       RequiredArgumentMissingError, ValidationError, CLIInternalError,
                                       UnclassifiedUserFault, AzureResponseError, AzureInternalError,
                                       ArgumentUsageError)

from .tunnel import TunnelServer

from ._params import AUTH_TYPES, MULTI_CONTAINER_TYPES
from ._client_factory import web_client_factory, ex_handler_factory, providers_client_factory
from ._appservice_utils import _generic_site_operation, _generic_settings_operation
from .utils import (_normalize_sku,
                    get_sku_tier,
                    retryable_method,
                    raise_missing_token_suggestion,
                    _get_location_from_resource_group,
                    _list_app,
                    _rename_server_farm_props,
                    _get_location_from_webapp,
                    _normalize_location,
                    get_pool_manager, use_additional_properties, get_app_service_plan_from_webapp,
                    get_resource_if_exists)
from ._create_util import (zip_contents_from_dir, get_runtime_version_details, create_resource_group, get_app_details,
                           check_resource_group_exists, set_location, get_site_availability, get_profile_username,
                           get_plan_to_use, get_lang_from_content, get_rg_to_use, get_sku_to_use,
                           detect_os_form_src, get_current_stack_from_runtime, generate_default_app_name)
from ._constants import (FUNCTIONS_STACKS_API_KEYS, FUNCTIONS_LINUX_RUNTIME_VERSION_REGEX,
                         FUNCTIONS_WINDOWS_RUNTIME_VERSION_REGEX, FUNCTIONS_NO_V2_REGIONS, PUBLIC_CLOUD,
                         LINUX_GITHUB_ACTIONS_WORKFLOW_TEMPLATE_PATH, WINDOWS_GITHUB_ACTIONS_WORKFLOW_TEMPLATE_PATH,
                         DOTNET_RUNTIME_NAME, NETCORE_RUNTIME_NAME, ASPDOTNET_RUNTIME_NAME, LINUX_OS_NAME,
                         WINDOWS_OS_NAME)
from ._github_oauth import (get_github_access_token)
from ._validators import validate_and_convert_to_int, validate_range_of_int_flag

logger = get_logger(__name__)

# pylint:disable=no-member,too-many-lines,too-many-locals

# region "Common routines shared with quick-start extensions."
# Please maintain compatibility in both interfaces and functionalities"


def create_webapp(cmd, resource_group_name, name, plan, runtime=None, startup_file=None,  # pylint: disable=too-many-statements,too-many-branches
                  deployment_container_image_name=None, deployment_source_url=None, deployment_source_branch='master',
                  deployment_local_git=None, docker_registry_server_password=None, docker_registry_server_user=None,
                  multicontainer_config_type=None, multicontainer_config_file=None, tags=None,
                  using_webapp_up=False, language=None, assign_identities=None,
                  role='Contributor', scope=None, vnet=None, subnet=None, https_only=False):
    from azure.mgmt.web.models import Site
    SiteConfig, SkuDescription, NameValuePair = cmd.get_models(
        'SiteConfig', 'SkuDescription', 'NameValuePair')

    if deployment_source_url and deployment_local_git:
        raise MutuallyExclusiveArgumentError('usage error: --deployment-source-url <url> | --deployment-local-git')

    docker_registry_server_url = parse_docker_image_name(deployment_container_image_name)

    client = web_client_factory(cmd.cli_ctx)
    if is_valid_resource_id(plan):
        parse_result = parse_resource_id(plan)
        plan_info = client.app_service_plans.get(parse_result['resource_group'], parse_result['name'])
    else:
        plan_info = client.app_service_plans.get(name=plan, resource_group_name=resource_group_name)
    if not plan_info:
        raise ResourceNotFoundError("The plan '{}' doesn't exist in the resource group '{}".format(plan,
                                                                                                   resource_group_name))
    is_linux = plan_info.reserved
    helper = _StackRuntimeHelper(cmd, linux=is_linux, windows=not is_linux)
    location = plan_info.location
    # This is to keep the existing appsettings for a newly created webapp on existing webapp name.
    name_validation = get_site_availability(cmd, name)
    if not name_validation.name_available:
        if name_validation.reason == 'Invalid':
            raise ValidationError(name_validation.message)
        logger.warning("Webapp '%s' already exists. The command will use the existing app's settings.", name)
        app_details = get_app_details(cmd, name)
        if app_details is None:
            raise ResourceNotFoundError("Unable to retrieve details of the existing app '{}'. Please check that "
                                        "the app is a part of the current subscription".format(name))
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
        site_config.vnet_route_all_enabled = True
        subnet_resource_id = subnet_info["subnet_resource_id"]
    else:
        subnet_resource_id = None

    if using_webapp_up:
        https_only = using_webapp_up

    webapp_def = Site(location=location, site_config=site_config, server_farm_id=plan_info.id, tags=tags,
                      https_only=https_only, virtual_network_subnet_id=subnet_resource_id)
    if runtime:
        runtime = helper.remove_delimiters(runtime)

    current_stack = None
    if is_linux:
        if not validate_container_app_create_options(runtime, deployment_container_image_name,
                                                     multicontainer_config_type, multicontainer_config_file):
            raise ArgumentUsageError("usage error: --runtime | --deployment-container-image-name |"
                                     " --multicontainer-config-type TYPE --multicontainer-config-file FILE")
        if startup_file:
            site_config.app_command_line = startup_file

        if runtime:
            match = helper.resolve(runtime, is_linux)
            if not match:
                raise ValidationError("Linux Runtime '{}' is not supported."
                                      " Please invoke 'az webapp list-runtimes --linux' to cross check".format(runtime))
            helper.get_site_config_setter(match, linux=is_linux)(cmd=cmd, stack=match, site_config=site_config)
        elif deployment_container_image_name:
            site_config.linux_fx_version = _format_fx_version(deployment_container_image_name)
            if name_validation.name_available:
                site_config.app_settings.append(NameValuePair(name="WEBSITES_ENABLE_APP_SERVICE_STORAGE",
                                                              value="false"))
        elif multicontainer_config_type and multicontainer_config_file:
            encoded_config_file = _get_linux_multicontainer_encoded_config_from_file(multicontainer_config_file)
            site_config.linux_fx_version = _format_fx_version(encoded_config_file, multicontainer_config_type)

    elif plan_info.is_xenon:  # windows container webapp
        if deployment_container_image_name:
            site_config.windows_fx_version = _format_fx_version(deployment_container_image_name)
        # set the needed app settings for container image validation
        if name_validation.name_available:
            site_config.app_settings.append(NameValuePair(name="DOCKER_REGISTRY_SERVER_USERNAME",
                                                          value=docker_registry_server_user))
            site_config.app_settings.append(NameValuePair(name="DOCKER_REGISTRY_SERVER_PASSWORD",
                                                          value=docker_registry_server_password))
            site_config.app_settings.append(NameValuePair(name="DOCKER_REGISTRY_SERVER_URL",
                                                          value=docker_registry_server_url))

    elif runtime:  # windows webapp with runtime specified
        if any([startup_file, deployment_container_image_name, multicontainer_config_file, multicontainer_config_type]):
            raise ArgumentUsageError("usage error: --startup-file or --deployment-container-image-name or "
                                     "--multicontainer-config-type and --multicontainer-config-file is "
                                     "only appliable on linux webapp")
        match = helper.resolve(runtime, linux=is_linux)
        if not match:
            raise ValidationError("Windows runtime '{}' is not supported. "
                                  "Please invoke 'az webapp list-runtimes' to cross check".format(runtime))
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

    # TO DO: (Check with Calvin) This seems to be something specific to portal client use only & should be removed
    if current_stack:
        _update_webapp_current_stack_property_if_needed(cmd, resource_group_name, name, current_stack)

    # Ensure SCC operations follow right after the 'create', no precedent appsetting update commands
    _set_remote_or_local_git(cmd, webapp, resource_group_name, name, deployment_source_url,
                             deployment_source_branch, deployment_local_git)

    _fill_ftp_publishing_url(cmd, webapp, resource_group_name, name)

    if deployment_container_image_name:
        logger.info("Updating container settings")
        update_container_settings(cmd, resource_group_name, name, docker_registry_server_url,
                                  deployment_container_image_name, docker_registry_server_user,
                                  docker_registry_server_password=docker_registry_server_password)

    if assign_identities is not None:
        identity = assign_identity(cmd, resource_group_name, name, assign_identities,
                                   role, None, scope)
        webapp.identity = identity

    return webapp


def _validate_vnet_integration_location(cmd, subnet_resource_group, vnet_name, webapp_location, vnet_sub_id=None):
    from azure.cli.core.commands.client_factory import get_subscription_id

    current_sub_id = get_subscription_id(cmd.cli_ctx)
    if vnet_sub_id:
        cmd.cli_ctx.data['subscription_id'] = vnet_sub_id

    vnet_client = network_client_factory(cmd.cli_ctx).virtual_networks
    vnet_location = vnet_client.get(resource_group_name=subnet_resource_group,
                                    virtual_network_name=vnet_name).location

    cmd.cli_ctx.data['subscription_id'] = current_sub_id

    vnet_location = _normalize_location(cmd, vnet_location)
    asp_location = _normalize_location(cmd, webapp_location)
    if vnet_location != asp_location:
        raise ArgumentUsageError("Unable to create webapp: vnet and App Service Plan must be in the same location. "
                                 "vnet location: {}. Plan location: {}.".format(vnet_location, asp_location))


def _get_subnet_info(cmd, resource_group_name, vnet, subnet):
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
        logger.warning("Assuming subnet resource group is the same as webapp. "
                       "Use a resource ID for --subnet or --vnet to use a different resource group.")
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


def validate_container_app_create_options(runtime=None, deployment_container_image_name=None,
                                          multicontainer_config_type=None, multicontainer_config_file=None):
    if bool(multicontainer_config_type) != bool(multicontainer_config_file):
        return False
    opts = [runtime, deployment_container_image_name, multicontainer_config_type]
    return len([x for x in opts if x]) == 1  # you can only specify one out the combinations


def parse_docker_image_name(deployment_container_image_name):
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
    return "https://{}".format(hostname)


def update_app_settings(cmd, resource_group_name, name, settings=None, slot=None, slot_settings=None):
    if not settings and not slot_settings:
        raise CLIError('Usage Error: --settings |--slot-settings')

    settings = settings or []
    slot_settings = slot_settings or []

    app_settings = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                           'list_application_settings', slot)
    result, slot_result = {}, {}
    # pylint: disable=too-many-nested-blocks
    for src, dest, setting_type in [(settings, result, "Settings"), (slot_settings, slot_result, "SlotSettings")]:
        for s in src:
            try:
                temp = shell_safe_json_parse(s)
                if isinstance(temp, list):  # a bit messy, but we'd like accept the output of the "list" command
                    for t in temp:
                        if 'slotSetting' in t.keys():
                            slot_result[t['name']] = t['slotSetting']
                        if setting_type == "SlotSettings":
                            slot_result[t['name']] = True
                        result[t['name']] = t['value']
                else:
                    dest.update(temp)
            except CLIError:
                setting_name, value = s.split('=', 1)
                dest[setting_name] = value
                result.update(dest)

    for setting_name, value in result.items():
        app_settings.properties[setting_name] = value
    client = web_client_factory(cmd.cli_ctx)

    result = _generic_settings_operation(cmd.cli_ctx, resource_group_name, name,
                                         'update_application_settings',
                                         app_settings, slot, client)

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

    return _build_app_settings_output(result.properties, app_settings_slot_cfg_names)


def add_azure_storage_account(cmd, resource_group_name, name, custom_id, storage_type, account_name,
                              share_name, access_key, mount_path=None, slot=None, slot_setting=False):
    AzureStorageInfoValue = cmd.get_models('AzureStorageInfoValue')
    azure_storage_accounts = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                                     'list_azure_storage_accounts', slot)

    if custom_id in azure_storage_accounts.properties:
        raise CLIError("Site already configured with an Azure storage account with the id '{}'. "
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

    return result.properties


def update_azure_storage_account(cmd, resource_group_name, name, custom_id, storage_type=None, account_name=None,
                                 share_name=None, access_key=None, mount_path=None, slot=None, slot_setting=False):
    AzureStorageInfoValue = cmd.get_models('AzureStorageInfoValue')

    azure_storage_accounts = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                                     'list_azure_storage_accounts', slot)

    existing_account_config = azure_storage_accounts.properties.pop(custom_id, None)

    if not existing_account_config:
        raise CLIError("No Azure storage account configuration found with the id '{}'. "
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

    return result.properties


def enable_zip_deploy_functionapp(cmd, resource_group_name, name, src, build_remote=False, timeout=None, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    app = client.web_apps.get(resource_group_name, name)
    if app is None:
        raise CLIError('The function app \'{}\' was not found in resource group \'{}\'. '
                       'Please make sure these values are correct.'.format(name, resource_group_name))
    parse_plan_id = parse_resource_id(app.server_farm_id)
    plan_info = None
    retry_delay = 10  # seconds
    # We need to retry getting the plan because sometimes if the plan is created as part of function app,
    # it can take a couple of tries before it gets the plan
    for _ in range(5):
        plan_info = client.app_service_plans.get(parse_plan_id['resource_group'],
                                                 parse_plan_id['name'])
        if plan_info is not None:
            break
        time.sleep(retry_delay)

    is_consumption = is_plan_consumption(cmd, plan_info)
    if (not build_remote) and is_consumption and app.reserved:
        return upload_zip_to_storage(cmd, resource_group_name, name, src, slot)
    if build_remote and app.reserved:
        add_remote_build_app_settings(cmd, resource_group_name, name, slot)
    elif app.reserved:
        remove_remote_build_app_settings(cmd, resource_group_name, name, slot)

    return enable_zip_deploy(cmd, resource_group_name, name, src, timeout, slot)


def enable_zip_deploy_webapp(cmd, resource_group_name, name, src, timeout=None, slot=None):
    return enable_zip_deploy(cmd, resource_group_name, name, src, timeout=timeout, slot=slot)


def enable_zip_deploy(cmd, resource_group_name, name, src, timeout=None, slot=None):
    logger.warning("Getting scm site credentials for zip deployment")
    user_name, password = _get_site_credential(cmd.cli_ctx, resource_group_name, name, slot)

    try:
        scm_url = _get_scm_url(cmd, resource_group_name, name, slot)
    except ValueError:
        raise CLIError('Failed to fetch scm url for function app')

    zip_url = scm_url + '/api/zipdeploy?isAsync=true'
    deployment_status_url = scm_url + '/api/deployments/latest'

    import urllib3
    authorization = urllib3.util.make_headers(basic_auth='{0}:{1}'.format(user_name, password))
    headers = authorization
    headers['Content-Type'] = 'application/octet-stream'
    headers['Cache-Control'] = 'no-cache'
    headers['User-Agent'] = get_az_user_agent()

    import requests
    import os
    from azure.cli.core.util import should_disable_connection_verify
    # Read file content
    with open(os.path.realpath(os.path.expanduser(src)), 'rb') as fs:
        zip_content = fs.read()
        logger.warning("Starting zip deployment. This operation can take a while to complete ...")
        res = requests.post(zip_url, data=zip_content, headers=headers, verify=not should_disable_connection_verify())
        logger.warning("Deployment endpoint responded with status code %d", res.status_code)

    # check the status of async deployment
    if res.status_code == 202:
        response = _check_zip_deployment_status(cmd, resource_group_name, name, deployment_status_url,
                                                authorization, timeout)
        return response

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
        value = keyval['value'].lower()
        if keyval['name'] == 'SCM_DO_BUILD_DURING_DEPLOYMENT':
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


def upload_zip_to_storage(cmd, resource_group_name, name, src, slot=None):
    settings = get_app_settings(cmd, resource_group_name, name, slot)

    storage_connection = None
    for keyval in settings:
        if keyval['name'] == 'AzureWebJobsStorage':
            storage_connection = str(keyval['value'])

    if storage_connection is None:
        raise CLIError('Could not find a \'AzureWebJobsStorage\' application setting')

    container_name = "function-releases"
    blob_name = "{}-{}.zip".format(datetime.datetime.today().strftime('%Y%m%d%H%M%S'), str(uuid.uuid4()))
    BlockBlobService = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE, 'blob#BlockBlobService')
    block_blob_service = BlockBlobService(connection_string=storage_connection)
    if not block_blob_service.exists(container_name):
        block_blob_service.create_container(container_name)

    # https://gist.github.com/vladignatyev/06860ec2040cb497f0f3
    def progress_callback(current, total):
        total_length = 30
        filled_length = int(round(total_length * current) / float(total))
        percents = round(100.0 * current / float(total), 1)
        progress_bar = '=' * filled_length + '-' * (total_length - filled_length)
        progress_message = 'Uploading {} {}%'.format(progress_bar, percents)
        cmd.cli_ctx.get_progress_controller().add(message=progress_message)

    block_blob_service.create_blob_from_path(container_name, blob_name, src, validate_content=True,
                                             progress_callback=progress_callback)

    now = datetime.datetime.utcnow()
    blob_start = now - datetime.timedelta(minutes=10)
    blob_end = now + datetime.timedelta(weeks=520)
    BlobPermissions = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE, 'blob#BlobPermissions')
    blob_token = block_blob_service.generate_blob_shared_access_signature(container_name,
                                                                          blob_name,
                                                                          permission=BlobPermissions(read=True),
                                                                          expiry=blob_end,
                                                                          start=blob_start)

    blob_uri = block_blob_service.make_blob_url(container_name, blob_name, sas_token=blob_token)
    website_run_from_setting = "WEBSITE_RUN_FROM_PACKAGE={}".format(blob_uri)
    update_app_settings(cmd, resource_group_name, name, settings=[website_run_from_setting])
    client = web_client_factory(cmd.cli_ctx)

    try:
        logger.info('\nSyncing Triggers...')
        if slot is not None:
            client.web_apps.sync_function_triggers_slot(resource_group_name, name, slot)
        else:
            client.web_apps.sync_function_triggers(resource_group_name, name)
    except CloudError as ex:
        # This SDK function throws an error if Status Code is 200
        if ex.status_code != 200:
            raise ex
    except Exception as ex:  # pylint: disable=broad-except
        if ex.response.status_code != 200:
            raise ex


def show_webapp(cmd, resource_group_name, name, slot=None):
    return _show_app(cmd, resource_group_name, name, "webapp", slot)


# for generic updater
def get_webapp(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)


def set_webapp(cmd, resource_group_name, name, slot=None, skip_dns_registration=None,  # pylint: disable=unused-argument
               skip_custom_domain_verification=None, force_dns_registration=None, ttl_in_seconds=None, **kwargs):  # pylint: disable=unused-argument
    instance = kwargs['parameters']
    client = web_client_factory(cmd.cli_ctx)
    updater = client.web_apps.begin_create_or_update_slot if slot else client.web_apps.begin_create_or_update
    kwargs = dict(resource_group_name=resource_group_name, name=name, site_envelope=instance)
    if slot:
        kwargs['slot'] = slot

    return updater(**kwargs)


def update_webapp(cmd, instance, client_affinity_enabled=None, https_only=None, minimum_elastic_instance_count=None,
                  prewarmed_instance_count=None):
    if 'function' in instance.kind:
        raise ValidationError("please use 'az functionapp update' to update this function app")
    if minimum_elastic_instance_count or prewarmed_instance_count:
        args = ["--minimum-elastic-instance-count", "--prewarmed-instance-count"]
        plan = get_app_service_plan_from_webapp(cmd, instance, api_version="2021-01-15")
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


def set_functionapp(cmd, resource_group_name, name, **kwargs):
    instance = kwargs['parameters']
    client = web_client_factory(cmd.cli_ctx)
    return client.web_apps.begin_create_or_update(resource_group_name, name, site_envelope=instance)


def get_functionapp(cmd, resource_group_name, name, slot=None):
    function_app = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    if not function_app or 'function' not in function_app.kind:
        raise ResourceNotFoundError("Unable to find App {} in resource group {}".format(name, resource_group_name))
    return function_app


def show_functionapp(cmd, resource_group_name, name, slot=None):
    return _show_app(cmd, resource_group_name, name, 'functionapp', slot)


def list_webapp(cmd, resource_group_name=None):
    full_list = _list_app(cmd.cli_ctx, resource_group_name)
    # ignore apps with kind==null & not functions apps
    return list(filter(lambda x: x.kind is not None and "function" not in x.kind.lower(), full_list))


def list_deleted_webapp(cmd, resource_group_name=None, name=None, slot=None):
    result = _list_deleted_app(cmd.cli_ctx, resource_group_name, name, slot)
    return sorted(result, key=lambda site: site.deleted_site_id)


def restore_deleted_webapp(cmd, deleted_id, resource_group_name, name, slot=None, restore_content_only=None):
    DeletedAppRestoreRequest = cmd.get_models('DeletedAppRestoreRequest')
    request = DeletedAppRestoreRequest(deleted_site_id=deleted_id, recover_configuration=not restore_content_only)
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'begin_restore_from_deleted_app',
                                   slot, request)


def list_function_app(cmd, resource_group_name=None):
    return list(filter(lambda x: x.kind is not None and "function" in x.kind.lower(),
                       _list_app(cmd.cli_ctx, resource_group_name)))


def _show_app(cmd, resource_group_name, name, cmd_app_type, slot=None):
    app = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    if not app:
        raise ResourceNotFoundError("Unable to find {} '{}', in RG '{}'."
                                    .format(cmd_app_type, name, resource_group_name))
    app_type = _kind_to_app_type(app.kind) if app else None
    if app_type != cmd_app_type:
        raise ResourceNotFoundError(
            "Unable to find {app_type} '{name}', in resource group '{resource_group}'".format(
                app_type=cmd_app_type, name=name, resource_group=resource_group_name),
            "Use 'az {app_type} show' to show {app_type}s".format(app_type=app_type))
    app.site_config = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get_configuration',
                                              slot, api_version="2021-01-15")
    _rename_server_farm_props(app)
    _fill_ftp_publishing_url(cmd, app, resource_group_name, name, slot)
    return app


def _kind_to_app_type(kind):
    if "workflow" in kind:
        return "logicapp"
    if "function" in kind:
        return "functionapp"
    return "webapp"


def _list_app(cli_ctx, resource_group_name=None):
    client = web_client_factory(cli_ctx)
    if resource_group_name:
        result = list(client.web_apps.list_by_resource_group(resource_group_name))
    else:
        result = list(client.web_apps.list())
    for webapp in result:
        _rename_server_farm_props(webapp)
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
    from ._appservice_utils import MSI_LOCAL_ID
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


def assign_identity(cmd, resource_group_name, name, assign_identities=None, role='Contributor', slot=None, scope=None):
    ManagedServiceIdentity, ResourceIdentityType = cmd.get_models('ManagedServiceIdentity',
                                                                  'ManagedServiceIdentityType')
    UserAssignedIdentitiesValue = cmd.get_models('Components1Jq1T4ISchemasManagedserviceidentityPropertiesUserassignedidentitiesAdditionalproperties')  # pylint: disable=line-too-long
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
    webapp = _assign_identity(cmd.cli_ctx, getter, setter, role, scope)
    return webapp.identity


def show_identity(cmd, resource_group_name, name, slot=None):
    web_app = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    if not web_app:
        raise ResourceNotFoundError("Unable to find App {} in resource group {}".format(name, resource_group_name))
    return web_app.identity


def remove_identity(cmd, resource_group_name, name, remove_identities=None, slot=None):
    IdentityType = cmd.get_models('ManagedServiceIdentityType')
    UserAssignedIdentitiesValue = cmd.get_models('Components1Jq1T4ISchemasManagedserviceidentityPropertiesUserassignedidentitiesAdditionalproperties')  # pylint: disable=line-too-long
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
                raise CLIError("'{}' are not associated with '{}'".format(','.join(non_existing), name))
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
        raise CLIError('Usage Error: --runtime-version set to invalid value')

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


def list_runtimes(cmd, os_type=None, linux=False):
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
    return runtime_helper.get_stack_names_only(delimiter=":")


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


def delete_function_app(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'delete', slot)


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
    slot_app_setting_names = client.web_apps.list_slot_configuration_names(resource_group_name, name).app_setting_names
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


@retryable_method(3, 5)
def _get_app_settings_from_scm(cmd, resource_group_name, name, slot=None):
    scm_url = _get_scm_url(cmd, resource_group_name, name, slot)
    settings_url = '{}/api/settings'.format(scm_url)
    username, password = _get_site_credential(cmd.cli_ctx, resource_group_name, name, slot)
    headers = {
        'Content-Type': 'application/octet-stream',
        'Cache-Control': 'no-cache',
        'User-Agent': get_az_user_agent()
    }

    import requests
    response = requests.get(settings_url, headers=headers, auth=(username, password), timeout=3)

    return response.json() or {}


def get_connection_strings(cmd, resource_group_name, name, slot=None):
    result = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'list_connection_strings', slot)
    client = web_client_factory(cmd.cli_ctx)
    slot_constr_names = client.web_apps.list_slot_configuration_names(resource_group_name, name) \
                              .connection_string_names or []
    result = [{'name': p,
               'value': result.properties[p].value,
               'type':result.properties[p].type,
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
        raise CLIError("'{}' app doesn't exist in resource group {}".format(name, resource_group_name))
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
        raise CLIError("Cannot decode config that is not one of the"
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


# for any modifications to the non-optional parameters, adjust the reflection logic accordingly
# in the method
# pylint: disable=unused-argument
def update_site_configs(cmd, resource_group_name, name, slot=None, number_of_workers=None, linux_fx_version=None,
                        windows_fx_version=None, pre_warmed_instance_count=None, php_version=None,
                        python_version=None, net_framework_version=None,
                        java_version=None, java_container=None, java_container_version=None,
                        remote_debugging_enabled=None, web_sockets_enabled=None,
                        always_on=None, auto_heal_enabled=None,
                        use32_bit_worker_process=None,
                        min_tls_version=None,
                        http20_enabled=None,
                        app_command_line=None,
                        ftps_state=None,
                        vnet_route_all_enabled=None,
                        generic_configurations=None):
    configs = get_site_configs(cmd, resource_group_name, name, slot)
    if number_of_workers is not None:
        number_of_workers = validate_range_of_int_flag('--number-of-workers', number_of_workers, min_val=0, max_val=20)
    if linux_fx_version:
        if linux_fx_version.strip().lower().startswith('docker|'):
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
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'update_configuration', slot, configs)


def delete_app_settings(cmd, resource_group_name, name, setting_names, slot=None):
    app_settings = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'list_application_settings', slot)
    client = web_client_factory(cmd.cli_ctx)

    slot_cfg_names = client.web_apps.list_slot_configuration_names(resource_group_name, name)
    is_slot_settings = False
    for setting_name in setting_names:
        app_settings.properties.pop(setting_name, None)
        if slot_cfg_names.app_setting_names and setting_name in slot_cfg_names.app_setting_names:
            slot_cfg_names.app_setting_names.remove(setting_name)
            is_slot_settings = True

    if is_slot_settings:
        client.web_apps.update_slot_configuration_names(resource_group_name, name, slot_cfg_names)

    result = _generic_settings_operation(cmd.cli_ctx, resource_group_name, name,
                                         'update_application_settings',
                                         app_settings, slot, client)

    return _build_app_settings_output(result.properties, slot_cfg_names.app_setting_names)


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

    return result.properties


def _ssl_context():
    if sys.version_info < (3, 4) or (in_cloud_console() and sys.platform.system() == 'Windows'):
        try:
            return ssl.SSLContext(ssl.PROTOCOL_TLS)  # added in python 2.7.13 and 3.6
        except AttributeError:
            return ssl.SSLContext(ssl.PROTOCOL_TLSv1)

    return ssl.create_default_context()


def _build_app_settings_output(app_settings, slot_cfg_names):
    slot_cfg_names = slot_cfg_names or []
    return [{'name': p,
             'value': app_settings[p],
             'slotSetting': p in slot_cfg_names} for p in _mask_creds_related_appsettings(app_settings)]


def update_connection_strings(cmd, resource_group_name, name, connection_string_type,
                              settings=None, slot=None, slot_settings=None):
    from azure.mgmt.web.models import ConnStringValueTypePair
    if not settings and not slot_settings:
        raise CLIError('Usage Error: --settings |--slot-settings')

    settings = settings or []
    slot_settings = slot_settings or []

    conn_strings = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                           'list_connection_strings', slot)
    for name_value in settings + slot_settings:
        # split at the first '=', connection string should not have '=' in the name
        conn_string_name, value = name_value.split('=', 1)
        if value[0] in ["'", '"']:  # strip away the quots used as separators
            value = value[1:-1]
        conn_strings.properties[conn_string_name] = ConnStringValueTypePair(value=value,
                                                                            type=connection_string_type)
    client = web_client_factory(cmd.cli_ctx)
    result = _generic_settings_operation(cmd.cli_ctx, resource_group_name, name,
                                         'update_connection_strings',
                                         conn_strings, slot, client)

    if slot_settings:
        new_slot_setting_names = [n.split('=', 1)[0] for n in slot_settings]
        slot_cfg_names = client.web_apps.list_slot_configuration_names(resource_group_name, name)
        slot_cfg_names.connection_string_names = slot_cfg_names.connection_string_names or []
        slot_cfg_names.connection_string_names += new_slot_setting_names
        client.web_apps.update_slot_configuration_names(resource_group_name, name, slot_cfg_names)

    return result.properties


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

    return _generic_settings_operation(cmd.cli_ctx, resource_group_name, name,
                                       'update_connection_strings',
                                       conn_strings, slot, client)


CONTAINER_APPSETTING_NAMES = ['DOCKER_REGISTRY_SERVER_URL', 'DOCKER_REGISTRY_SERVER_USERNAME',
                              'DOCKER_REGISTRY_SERVER_PASSWORD', "WEBSITES_ENABLE_APP_SERVICE_STORAGE"]
APPSETTINGS_TO_MASK = ['DOCKER_REGISTRY_SERVER_PASSWORD']


def update_container_settings(cmd, resource_group_name, name, docker_registry_server_url=None,
                              docker_custom_image_name=None, docker_registry_server_user=None,
                              websites_enable_app_service_storage=None, docker_registry_server_password=None,
                              multicontainer_config_type=None, multicontainer_config_file=None, slot=None):
    settings = []
    if docker_registry_server_url is not None:
        settings.append('DOCKER_REGISTRY_SERVER_URL=' + docker_registry_server_url)

    if (not docker_registry_server_user and not docker_registry_server_password and
            docker_registry_server_url and '.azurecr.io' in docker_registry_server_url):
        logger.warning('No credential was provided to access Azure Container Registry. Trying to look up...')
        parsed = urlparse(docker_registry_server_url)
        registry_name = (parsed.netloc if parsed.scheme else parsed.path).split('.')[0]
        try:
            docker_registry_server_user, docker_registry_server_password = _get_acr_cred(cmd.cli_ctx, registry_name)
        except Exception as ex:  # pylint: disable=broad-except
            logger.warning("Retrieving credentials failed with an exception:'%s'", ex)  # consider throw if needed

    if docker_registry_server_user is not None:
        settings.append('DOCKER_REGISTRY_SERVER_USERNAME=' + docker_registry_server_user)
    if docker_registry_server_password is not None:
        settings.append('DOCKER_REGISTRY_SERVER_PASSWORD=' + docker_registry_server_password)
    if websites_enable_app_service_storage:
        settings.append('WEBSITES_ENABLE_APP_SERVICE_STORAGE=' + websites_enable_app_service_storage)

    if docker_registry_server_user or docker_registry_server_password or docker_registry_server_url or websites_enable_app_service_storage:  # pylint: disable=line-too-long
        update_app_settings(cmd, resource_group_name, name, settings, slot)
    settings = get_app_settings(cmd, resource_group_name, name, slot)
    if docker_custom_image_name is not None:
        _add_fx_version(cmd, resource_group_name, name, docker_custom_image_name, slot)

    if multicontainer_config_file and multicontainer_config_type:
        encoded_config_file = _get_linux_multicontainer_encoded_config_from_file(multicontainer_config_file)
        linux_fx_version = _format_fx_version(encoded_config_file, multicontainer_config_type)
        update_site_configs(cmd, resource_group_name, name, linux_fx_version=linux_fx_version, slot=slot)
    elif multicontainer_config_file or multicontainer_config_type:
        logger.warning('Must change both settings --multicontainer-config-file FILE --multicontainer-config-type TYPE')

    return _mask_creds_related_appsettings(_filter_for_container_settings(cmd, resource_group_name, name, settings,
                                                                          slot=slot))


def update_container_settings_functionapp(cmd, resource_group_name, name, docker_registry_server_url=None,
                                          docker_custom_image_name=None, docker_registry_server_user=None,
                                          docker_registry_server_password=None, slot=None):
    return update_container_settings(cmd, resource_group_name, name, docker_registry_server_url,
                                     docker_custom_image_name, docker_registry_server_user, None,
                                     docker_registry_server_password, multicontainer_config_type=None,
                                     multicontainer_config_file=None, slot=slot)


def _get_acr_cred(cli_ctx, registry_name):
    from azure.mgmt.containerregistry import ContainerRegistryManagementClient
    from azure.cli.core.commands.parameters import get_resources_in_subscription
    client = get_mgmt_service_client(cli_ctx, ContainerRegistryManagementClient).registries

    result = get_resources_in_subscription(cli_ctx, 'Microsoft.ContainerRegistry/registries')
    result = [item for item in result if item.name.lower() == registry_name]
    if not result or len(result) > 1:
        raise CLIError("No resource or more than one were found with name '{}'.".format(registry_name))
    resource_group_name = parse_resource_id(result[0].id)['resource_group']

    registry = client.get(resource_group_name, registry_name)

    if registry.admin_user_enabled:  # pylint: disable=no-member
        cred = client.list_credentials(resource_group_name, registry_name)
        return cred.username, cred.passwords[0].value
    raise CLIError("Failed to retrieve container registry credentials. Please either provide the "
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
        raise CLIError("'{}' app doesn't exist".format(webapp_name))
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
        raise CLIError("'{}' app doesn't exist".format(webapp_name))
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


def create_webapp_slot(cmd, resource_group_name, webapp, slot, configuration_source=None):
    Site, SiteConfig, NameValuePair = cmd.get_models('Site', 'SiteConfig', 'NameValuePair')
    client = web_client_factory(cmd.cli_ctx)
    site = client.web_apps.get(resource_group_name, webapp)
    site_config = get_site_configs(cmd, resource_group_name, webapp, None)
    if not site:
        raise CLIError("'{}' app doesn't exist".format(webapp))
    if 'functionapp' in site.kind:
        raise CLIError("'{}' is a function app. Please use `az functionapp deployment slot create`.".format(webapp))
    location = site.location
    slot_def = Site(server_farm_id=site.server_farm_id, location=location)
    slot_def.site_config = SiteConfig()

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
        update_slot_configuration_from_source(cmd, client, resource_group_name, webapp, slot, configuration_source)

    result.name = result.name.split('/')[-1]
    return result


def create_functionapp_slot(cmd, resource_group_name, name, slot, configuration_source=None):
    Site = cmd.get_models('Site')
    client = web_client_factory(cmd.cli_ctx)
    site = client.web_apps.get(resource_group_name, name)
    if not site:
        raise CLIError("'{}' function app doesn't exist".format(name))
    location = site.location
    slot_def = Site(server_farm_id=site.server_farm_id, location=location)

    poller = client.web_apps.begin_create_or_update_slot(resource_group_name, name, site_envelope=slot_def, slot=slot)
    result = LongRunningOperation(cmd.cli_ctx)(poller)

    if configuration_source:
        update_slot_configuration_from_source(cmd, client, resource_group_name, name, slot, configuration_source)

    result.name = result.name.split('/')[-1]
    return result


def update_slot_configuration_from_source(cmd, client, resource_group_name, webapp, slot, configuration_source=None):
    clone_from_prod = configuration_source.lower() == webapp.lower()
    site_config = get_site_configs(cmd, resource_group_name, webapp,
                                   None if clone_from_prod else configuration_source)
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
            return LongRunningOperation(cmd.cli_ctx)(poller)
        except Exception as ex:  # pylint: disable=broad-except
            import re
            ex = ex_handler_factory(no_throw=True)(ex)
            # for non server errors(50x), just throw; otherwise retry 4 times
            if i == 4 or not re.findall(r'\(50\d\)', str(ex)):
                raise
            logger.warning('retrying %s/4', i + 1)
            time.sleep(5)   # retry in a moment


def update_git_token(cmd, git_token=None):
    '''
    Update source control token cached in Azure app service. If no token is provided,
    the command will clean up existing token.
    '''
    client = web_client_factory(cmd.cli_ctx)
    from azure.mgmt.web.models import SourceControl
    sc = SourceControl(name='not-really-needed', source_control_name='GitHub', token=git_token or '')
    return client.update_source_control('GitHub', sc)


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
    except CloudError as ex:  # Because of bad spec, sdk throws on 200. We capture it here
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


def create_app_service_plan(cmd, resource_group_name, name, is_linux, hyper_v, per_site_scaling=False,
                            app_service_environment=None, sku='B1', number_of_workers=None, location=None,
                            tags=None, no_wait=False, zone_redundant=False):
    HostingEnvironmentProfile, SkuDescription, AppServicePlan = cmd.get_models(
        'HostingEnvironmentProfile', 'SkuDescription', 'AppServicePlan')

    client = web_client_factory(cmd.cli_ctx)
    if app_service_environment:
        if hyper_v:
            raise ArgumentUsageError('Windows containers is not yet supported in app service environment')
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
            err_msg = "App service environment '{}' not found in subscription.".format(app_service_environment)
            raise ResourceNotFoundError(err_msg)
    else:  # Non-ASE
        ase_def = None
        if location is None:
            location = _get_location_from_resource_group(cmd.cli_ctx, resource_group_name)

    # the api is odd on parameter naming, have to live with it for now
    sku_def = SkuDescription(tier=get_sku_tier(sku), name=_normalize_sku(sku), capacity=number_of_workers)
    plan_def = AppServicePlan(location=location, tags=tags, sku=sku_def,
                              reserved=(is_linux or None), hyper_v=(hyper_v or None), name=name,
                              per_site_scaling=per_site_scaling, hosting_environment_profile=ase_def)

    if sku.upper() in ['WS1', 'WS2', 'WS3']:
        existing_plan = get_resource_if_exists(client.app_service_plans,
                                               resource_group_name=resource_group_name, name=name)
        if existing_plan and existing_plan.sku.tier != "WorkflowStandard":
            raise ValidationError("Plan {} in resource group {} already exists and "
                                  "cannot be updated to a logic app SKU (WS1, WS2, or WS3)")
        plan_def.type = "elastic"

    if zone_redundant:
        _enable_zone_redundant(plan_def, sku_def, number_of_workers)

    return sdk_no_wait(no_wait, client.app_service_plans.begin_create_or_update, name=name,
                       resource_group_name=resource_group_name, app_service_plan=plan_def)


def update_app_service_plan(instance, sku=None, number_of_workers=None, elastic_scale=None,
                            max_elastic_worker_count=None):
    if number_of_workers is None and sku is None and elastic_scale is None and max_elastic_worker_count is None:
        args = ["--number-of-workers", "--sku", "--elastic-scale", "--max-elastic-worker-count"]
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
        if get_sku_tier(sku) not in ["PREMIUMV2", "PREMIUMV3"]:
            raise ValidationError("--number-of-workers and --elastic-scale can only be used on premium V2/V3 SKUs. "
                                  "Use command help to see all available SKUs")

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

    instance.sku = sku_def
    return instance


def show_plan(cmd, resource_group_name, name):
    from azure.cli.core.commands.client_factory import get_subscription_id
    client = web_client_factory(cmd.cli_ctx)
    serverfarm_url_base = 'subscriptions/{}/resourceGroups/{}/providers/Microsoft.Web/serverfarms/{}?api-version={}'
    subscription_id = get_subscription_id(cmd.cli_ctx)
    serverfarm_url = serverfarm_url_base.format(subscription_id, resource_group_name, name, client.DEFAULT_API_VERSION)
    request_url = cmd.cli_ctx.cloud.endpoints.resource_manager + serverfarm_url
    response = send_raw_request(cmd.cli_ctx, "GET", request_url)
    return response.json()


def update_functionapp_app_service_plan(cmd, instance, sku=None, number_of_workers=None, max_burst=None):
    instance = update_app_service_plan(instance, sku, number_of_workers)
    if max_burst is not None:
        if not is_plan_elastic_premium(cmd, instance):
            raise CLIError("Usage error: --max-burst is only supported for Elastic Premium (EP) plans")
        max_burst = validate_range_of_int_flag('--max-burst', max_burst, min_val=0, max_val=20)
        instance.maximum_elastic_worker_count = max_burst
    if number_of_workers is not None:
        number_of_workers = validate_range_of_int_flag('--number-of-workers / --min-instances',
                                                       number_of_workers, min_val=0, max_val=20)
    return update_app_service_plan(instance, sku, number_of_workers)


def show_backup_configuration(cmd, resource_group_name, webapp_name, slot=None):
    try:
        return _generic_site_operation(cmd.cli_ctx, resource_group_name, webapp_name,
                                       'get_backup_configuration', slot)
    except Exception:  # pylint: disable=broad-except
        raise CLIError('Backup configuration not found')


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
        return client.web_apps.backup_slot(resource_group_name, webapp_name, backup_request, slot)

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
            raise CLIError('No backup configuration found. A configuration must be created. ' +
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

    backup_schedule = BackupSchedule(frequency_interval=frequency_num, frequency_unit=frequency_unit.name,
                                     keep_at_least_one_backup=keep_at_least_one_backup,
                                     retention_period_in_days=retention_period_in_days)
    backup_request = BackupRequest(backup_request_name=backup_name, backup_schedule=backup_schedule,
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
        return client.web_apps.restore_slot(resource_group_name, webapp_name, 0, restore_request, slot)

    return client.web_apps.restore(resource_group_name, webapp_name, 0, restore_request)


def list_snapshots(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'list_snapshots',
                                   slot)


def restore_snapshot(cmd, resource_group_name, name, time, slot=None, restore_content_only=False,  # pylint: disable=redefined-outer-name
                     source_resource_group=None, source_name=None, source_slot=None):
    from azure.cli.core.commands.client_factory import get_subscription_id
    SnapshotRecoverySource, SnapshotRestoreRequest = cmd.get_models('SnapshotRecoverySource', 'SnapshotRestoreRequest')
    client = web_client_factory(cmd.cli_ctx)
    recover_config = not restore_content_only
    if all([source_resource_group, source_name]):
        # Restore from source app to target app
        sub_id = get_subscription_id(cmd.cli_ctx)
        source_id = "/subscriptions/" + sub_id + "/resourceGroups/" + source_resource_group + \
            "/providers/Microsoft.Web/sites/" + source_name
        if source_slot:
            source_id = source_id + "/slots/" + source_slot
        source = SnapshotRecoverySource(id=source_id)
        request = SnapshotRestoreRequest(overwrite=False, snapshot_time=time, recovery_source=source,
                                         recover_configuration=recover_config)
        if slot:
            return client.web_apps.restore_snapshot_slot(resource_group_name, name, request, slot)
        return client.web_apps.restore_snapshot(resource_group_name, name, request)
    if any([source_resource_group, source_name]):
        raise CLIError('usage error: --source-resource-group and --source-name must both be specified if one is used')
    # Overwrite app with its own snapshot
    request = SnapshotRestoreRequest(overwrite=True, snapshot_time=time, recover_configuration=recover_config)
    if slot:
        return client.web_apps.restore_snapshot_slot(resource_group_name, name, request, slot)
    return client.web_apps.restore_snapshot(resource_group_name, name, request)


# pylint: disable=inconsistent-return-statements
def _create_db_setting(cmd, db_name, db_type, db_connection_string):
    DatabaseBackupSetting = cmd.get_models('DatabaseBackupSetting')
    if all([db_name, db_type, db_connection_string]):
        return [DatabaseBackupSetting(database_type=db_type, name=db_name, connection_string=db_connection_string)]
    if any([db_name, db_type, db_connection_string]):
        raise CLIError('usage error: --db-name NAME --db-type TYPE --db-connection-string STRING')


def _parse_frequency(cmd, frequency):
    FrequencyUnit = cmd.get_models('FrequencyUnit')
    unit_part = frequency.lower()[-1]
    if unit_part == 'd':
        frequency_unit = FrequencyUnit.day
    elif unit_part == 'h':
        frequency_unit = FrequencyUnit.hour
    else:
        raise CLIError('Frequency must end with d or h for "day" or "hour"')

    try:
        frequency_num = int(frequency[:-1])
    except ValueError:
        raise CLIError('Frequency must start with a number')

    if frequency_num < 0:
        raise CLIError('Frequency must be positive')

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
    raise ValueError('Failed to retrieve Scm Uri')


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
            raise CLIError('Please specify both username and password in non-interactive mode.')

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
        raise CLIError("'{}' app doesn't exist".format(name))
    url = site.enabled_host_names[0]  # picks the custom domain URL incase a domain is assigned
    ssl_host = next((h for h in site.host_name_ssl_states
                     if h.ssl_state != SslState.disabled), None)
    return ('https' if ssl_host else 'http') + '://' + url


# TODO: expose new blob suport
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
        raise CLIError("'{}' app doesn't exist".format(name))
    location = site.location

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
    site_log_config = SiteLogsConfig(location=location,
                                     application_logs=application_logs,
                                     http_logs=http_logs,
                                     failed_requests_tracing=failed_request_tracing_logs,
                                     detailed_error_messages=detailed_error_messages_logs)

    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'update_diagnostic_logs_config',
                                   slot, site_log_config)


def show_diagnostic_settings(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get_diagnostic_logs_configuration', slot)


def show_deployment_log(cmd, resource_group, name, slot=None, deployment_id=None):
    import urllib3
    import requests

    scm_url = _get_scm_url(cmd, resource_group, name, slot)
    username, password = _get_site_credential(cmd.cli_ctx, resource_group, name, slot)
    headers = urllib3.util.make_headers(basic_auth='{}:{}'.format(username, password))

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
    scm_url = _get_scm_url(cmd, resource_group, name, slot)
    deployment_log_url = '{}/api/deployments/'.format(scm_url)
    username, password = _get_site_credential(cmd.cli_ctx, resource_group, name, slot)

    import urllib3
    headers = urllib3.util.make_headers(basic_auth='{}:{}'.format(username, password))

    import requests
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
        raise CLIError("'{}' app doesn't exist".format(name))
    configs = get_site_configs(cmd, resource_group_name, name)
    host_name_split = site.default_host_name.split('.', 1)
    host_name_suffix = '.' + host_name_split[1]
    host_name_val = host_name_split[0]
    configs.experiments.ramp_up_rules = []
    for r in distribution:
        slot, percentage = r.split('=')
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
    scm_url = _get_scm_url(cmd, resource_group_name, name, slot)
    streaming_url = scm_url + '/logstream'
    if provider:
        streaming_url += ('/' + provider.lstrip('/'))

    user, password = _get_site_credential(cmd.cli_ctx, resource_group_name, name, slot)
    t = threading.Thread(target=_get_log, args=(streaming_url, user, password))
    t.daemon = True
    t.start()

    while True:
        time.sleep(100)  # so that ctrl+c can stop the command


def download_historical_logs(cmd, resource_group_name, name, log_file=None, slot=None):
    scm_url = _get_scm_url(cmd, resource_group_name, name, slot)
    url = scm_url.rstrip('/') + '/dump'
    user_name, password = _get_site_credential(cmd.cli_ctx, resource_group_name, name, slot)
    _get_log(url, user_name, password, log_file)
    logger.warning('Downloaded logs to %s', log_file)


def _get_site_credential(cli_ctx, resource_group_name, name, slot=None):
    creds = _generic_site_operation(cli_ctx, resource_group_name, name, 'begin_list_publishing_credentials', slot)
    creds = creds.result()
    return (creds.publishing_user_name, creds.publishing_password)


def _get_log(url, user_name, password, log_file=None):
    import urllib3
    try:
        import urllib3.contrib.pyopenssl
        urllib3.contrib.pyopenssl.inject_into_urllib3()
    except ImportError:
        pass

    http = get_pool_manager(url)
    headers = urllib3.util.make_headers(basic_auth='{0}:{1}'.format(user_name, password))
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
        for chunk in r.stream():
            if chunk:
                # Extra encode() and decode for stdout which does not surpport 'utf-8'
                logger.warning(chunk.decode(encoding='utf-8', errors='replace')
                               .encode(std_encoding, errors='replace')
                               .decode(std_encoding, errors='replace')
                               .rstrip('\n\r'))  # each line of log has CRLF.
    r.release_conn()


def upload_ssl_cert(cmd, resource_group_name, name, certificate_password, certificate_file, slot=None):
    Certificate = cmd.get_models('Certificate')
    client = web_client_factory(cmd.cli_ctx)
    webapp = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    cert_file = open(certificate_file, 'rb')
    cert_contents = cert_file.read()
    hosting_environment_profile_param = (webapp.hosting_environment_profile.name
                                         if webapp.hosting_environment_profile else '')

    thumb_print = _get_cert(certificate_password, certificate_file)
    cert_name = _generate_cert_name(thumb_print, hosting_environment_profile_param,
                                    webapp.location, resource_group_name)
    cert = Certificate(password=certificate_password, pfx_blob=cert_contents,
                       location=webapp.location, server_farm_id=webapp.server_farm_id)
    return client.certificates.create_or_update(resource_group_name, cert_name, cert)


def _generate_cert_name(thumb_print, hosting_environment, location, resource_group_name):
    return "%s_%s_%s_%s" % (thumb_print, hosting_environment, location, resource_group_name)


def _get_cert(certificate_password, certificate_file):
    ''' Decrypts the .pfx file '''
    p12 = OpenSSL.crypto.load_pkcs12(open(certificate_file, 'rb').read(), certificate_password)
    cert = p12.get_certificate()
    digest_algorithm = 'sha1'
    thumbprint = cert.digest(digest_algorithm).decode("utf-8").replace(':', '')
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
    raise CLIError("Certificate for thumbprint '{}' not found".format(certificate_thumbprint))


def import_ssl_cert(cmd, resource_group_name, name, key_vault, key_vault_certificate_name):
    Certificate = cmd.get_models('Certificate')
    client = web_client_factory(cmd.cli_ctx)
    webapp = client.web_apps.get(resource_group_name, name)
    if not webapp:
        raise CLIError("'{}' app doesn't exist in resource group {}".format(name, resource_group_name))
    server_farm_id = webapp.server_farm_id
    location = webapp.location
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
                 '\naz .. ssl import -n {1} -g {2} --key-vault-certificate-name {3} ' \
                 '--key-vault /subscriptions/[sub id]/resourceGroups/[rg]/providers/Microsoft.KeyVault/' \
                 'vaults/{0}'.format(key_vault, name, resource_group_name, key_vault_certificate_name)
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
            ascs = diff_subscription_client.app_service_certificate_orders.list()
        else:
            ascs = client.app_service_certificate_orders.list()

        kv_secret_name = None
        for asc in ascs:
            if asc.name == key_vault_certificate_name:
                kv_secret_name = asc.certificates[key_vault_certificate_name].key_vault_secret_name

    # if kv_secret_name is not populated, it is not an appservice certificate, proceed for KV certificates
    if not kv_secret_name:
        kv_secret_name = key_vault_certificate_name

    cert_name = '{}-{}-{}'.format(resource_group_name, kv_name, key_vault_certificate_name)
    lnk = 'https://azure.github.io/AppService/2016/05/24/Deploying-Azure-Web-App-Certificate-through-Key-Vault.html'
    lnk_msg = 'Find more details here: {}'.format(lnk)
    if not _check_service_principal_permissions(cmd, kv_resource_group_name, kv_name, kv_subscription):
        logger.warning('Unable to verify Key Vault permissions.')
        logger.warning('You may need to grant Microsoft.Azure.WebSites service principal the Secret:Get permission')
        logger.warning(lnk_msg)

    kv_cert_def = Certificate(location=location, key_vault_id=kv_id, password='',
                              key_vault_secret_name=kv_secret_name, server_farm_id=server_farm_id)

    return client.certificates.create_or_update(name=cert_name, resource_group_name=resource_group_name,
                                                certificate_envelope=kv_cert_def)


def create_managed_ssl_cert(cmd, resource_group_name, name, hostname, slot=None):
    Certificate = cmd.get_models('Certificate')
    hostname = hostname.lower()
    client = web_client_factory(cmd.cli_ctx)
    webapp = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    if not webapp:
        slot_text = "Deployment slot {} in ".format(slot) if slot else ''
        raise CLIError("{0}app {1} doesn't exist in resource group {2}".format(slot_text, name, resource_group_name))

    parsed_plan_id = parse_resource_id(webapp.server_farm_id)
    plan_info = client.app_service_plans.get(parsed_plan_id['resource_group'], parsed_plan_id['name'])
    if plan_info.sku.tier.upper() == 'FREE' or plan_info.sku.tier.upper() == 'SHARED':
        raise CLIError('Managed Certificate is not supported on Free and Shared tier.')

    if not _verify_hostname_binding(cmd, resource_group_name, name, hostname, slot):
        slot_text = " --slot {}".format(slot) if slot else ""
        raise CLIError("Hostname (custom domain) '{0}' is not registered with {1}. "
                       "Use 'az webapp config hostname add --resource-group {2} "
                       "--webapp-name {1}{3} --hostname {0}' "
                       "to register the hostname.".format(hostname, name, resource_group_name, slot_text))

    server_farm_id = webapp.server_farm_id
    location = webapp.location
    easy_cert_def = Certificate(location=location, canonical_name=hostname,
                                server_farm_id=server_farm_id, password='')

    # TODO: Update manual polling to use LongRunningOperation once backend API & new SDK supports polling
    try:
        return client.certificates.create_or_update(name=hostname, resource_group_name=resource_group_name,
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
                           " to view your certificate once it is created", resource_group_name, hostname)
            return
        raise CLIError(ex)


def _check_service_principal_permissions(cmd, resource_group_name, key_vault_name, key_vault_subscription):
    from azure.cli.command_modules.role._client_factory import _graph_client_factory
    from azure.graphrbac.models import GraphErrorException
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
    graph_sp_client = _graph_client_factory(cmd.cli_ctx).service_principals
    for policy in vault.properties.access_policies:
        try:
            sp = graph_sp_client.get(policy.object_id)
            if sp.app_id == AZURE_PUBLIC_WEBSITES_APP_ID or sp.app_id == AZURE_GOV_WEBSITES_APP_ID:
                for perm in policy.permissions.secrets:
                    if perm == "Get":
                        return True
        except GraphErrorException:
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


def _update_ssl_binding(cmd, resource_group_name, name, certificate_thumbprint, ssl_type, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    webapp = client.web_apps.get(resource_group_name, name)
    if not webapp:
        raise ResourceNotFoundError("'{}' app doesn't exist".format(name))

    cert_resource_group_name = parse_resource_id(webapp.server_farm_id)['resource_group']
    webapp_certs = client.certificates.list_by_resource_group(cert_resource_group_name)

    found_cert = None
    for webapp_cert in webapp_certs:
        if webapp_cert.thumbprint == certificate_thumbprint:
            found_cert = webapp_cert
    if not found_cert:
        webapp_certs = client.certificates.list_by_resource_group(resource_group_name)
        for webapp_cert in webapp_certs:
            if webapp_cert.thumbprint == certificate_thumbprint:
                found_cert = webapp_cert
    if found_cert:
        if len(found_cert.host_names) == 1 and not found_cert.host_names[0].startswith('*'):
            return _update_host_name_ssl_state(cmd, resource_group_name, name, webapp,
                                               found_cert.host_names[0], ssl_type,
                                               certificate_thumbprint, slot)

        query_result = list_hostnames(cmd, resource_group_name, name, slot)
        hostnames_in_webapp = [x.name.split('/')[-1] for x in query_result]
        to_update = _match_host_names_from_cert(found_cert.host_names, hostnames_in_webapp)
        for h in to_update:
            _update_host_name_ssl_state(cmd, resource_group_name, name, webapp,
                                        h, ssl_type, certificate_thumbprint, slot)

        return show_webapp(cmd, resource_group_name, name, slot)

    raise ResourceNotFoundError("Certificate for thumbprint '{}' not found.".format(certificate_thumbprint))


def bind_ssl_cert(cmd, resource_group_name, name, certificate_thumbprint, ssl_type, slot=None):
    SslState = cmd.get_models('SslState')
    return _update_ssl_binding(cmd, resource_group_name, name, certificate_thumbprint,
                               SslState.sni_enabled if ssl_type == 'SNI' else SslState.ip_based_enabled, slot)


def unbind_ssl_cert(cmd, resource_group_name, name, certificate_thumbprint, slot=None):
    SslState = cmd.get_models('SslState')
    return _update_ssl_binding(cmd, resource_group_name, name,
                               certificate_thumbprint, SslState.disabled, slot)


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
        self._client = web_client_factory(cmd.cli_ctx, api_version="2021-01-01")
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
    # pylint: disable=too-few-public-methods
    class Runtime:
        def __init__(self, display_name=None, configs=None, github_actions_properties=None, linux=False):
            self.display_name = display_name
            self.configs = configs if configs is not None else dict()
            self.github_actions_properties = github_actions_properties
            self.linux = linux

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
        self.default_delimeter = "|"  # character that separates runtime name from version
        self.allowed_delimeters = "|:"  # delimiters allowed: '|', ':'
        super().__init__(cmd, linux=linux, windows=windows)

    def get_stack_names_only(self, delimiter=None):
        windows_stacks = [s.display_name for s in self.stacks if not s.linux]
        linux_stacks = [s.display_name for s in self.stacks if s.linux]
        if delimiter is not None:
            windows_stacks = [n.replace(self.default_delimeter, delimiter) for n in windows_stacks]
            linux_stacks = [n.replace(self.default_delimeter, delimiter) for n in linux_stacks]
        if self._linux and not self._windows:
            return linux_stacks
        if self._windows and not self._linux:
            return windows_stacks
        return {LINUX_OS_NAME: linux_stacks, WINDOWS_OS_NAME: windows_stacks}

    def _get_raw_stacks_from_api(self):
        return list(self._client.provider.get_web_app_stacks(stack_os_type=None))

    def _parse_raw_stacks(self, stacks):
        for lang in stacks:
            if lang.display_text.lower() == "java":
                continue  # info on java stacks is taken from the "java containers" stacks
            for major_version in lang.major_versions:
                if self._linux:
                    self._parse_major_version_linux(major_version, self._stacks)
                if self._windows:
                    self._parse_major_version_windows(major_version, self._stacks, self.windows_config_mappings)

    def remove_delimiters(self, runtime):
        import re
        runtime = re.split("[{}]".format(self.allowed_delimeters), runtime)
        return self.default_delimeter.join(filter(None, runtime))

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
        import re
        t = display_text.upper()
        t = t.replace(".NET CORE", NETCORE_RUNTIME_NAME.upper())
        t = t.replace("ASP.NET", ASPDOTNET_RUNTIME_NAME.upper())
        t = t.replace(".NET", DOTNET_RUNTIME_NAME)
        t = re.sub(r"\(.*\)", "", t)  # remove "(LTS)"
        return t.replace(" ", "|", 1).replace(" ", "")

    @classmethod
    def _is_valid_runtime_setting(cls, runtime_setting):
        return runtime_setting is not None and not runtime_setting.is_hidden and not runtime_setting.is_deprecated

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
        minor_java_versions = self._get_valid_minor_versions(major_version, linux=False, java=True)
        default_java_version = next(iter(minor_java_versions), None)
        if default_java_version:
            container_settings = default_java_version.stack_settings.windows_container_settings
            # TODO get the API to return java versions in a more parseable way
            for java_version in ["1.8", "11"]:
                java_container = container_settings.java_container
                container_version = container_settings.java_container_version
                if container_version.upper() == "SE":
                    java_container = "Java SE"
                    if java_version == "1.8":
                        container_version = "8"
                    else:
                        container_version = "11"
                runtime_name = "{}|{}|{}|{}".format("java",
                                                    java_version,
                                                    java_container,
                                                    container_version)
                gh_actions_version = "8" if java_version == "1.8" else java_version
                gh_actions_runtime = "{}, {}, {}".format(java_version,
                                                         java_container.lower().replace(" se", ""),
                                                         container_settings.java_container_version.lower())
                if java_container == "Java SE":  # once runtime name is set, reset configs to correct values
                    java_container = "JAVA"
                    container_version = "SE"
                runtime = self.Runtime(display_name=runtime_name,
                                       configs={"java_version": java_version,
                                                "java_container": java_container,
                                                "java_container_version": container_version},
                                       github_actions_properties={"github_actions_version": gh_actions_version,
                                                                  "app_runtime": "java",
                                                                  "app_runtime_version": gh_actions_runtime},
                                       linux=False)
                parsed_results.append(runtime)
        else:
            minor_versions = self._get_valid_minor_versions(major_version, linux=False, java=False)
            for minor_version in minor_versions:
                settings = minor_version.stack_settings.windows_runtime_settings
                runtime_name = self._format_windows_display_text(minor_version.display_text)

                runtime = self.Runtime(display_name=runtime_name, linux=False)
                lang_name = runtime_name.split("|")[0].lower()
                config_key = config_mappings.get(lang_name)

                if config_key:
                    runtime.configs[config_key] = settings.runtime_version
                gh_properties = settings.git_hub_action_settings
                if gh_properties.is_supported:
                    runtime.github_actions_properties = {"github_actions_version": gh_properties.supported_version}

                parsed_results.append(runtime)

    def _parse_major_version_linux(self, major_version, parsed_results):
        minor_java_versions = self._get_valid_minor_versions(major_version, linux=True, java=True)
        default_java_version_linux = next(iter(minor_java_versions), None)
        if default_java_version_linux:
            linux_container_settings = default_java_version_linux.stack_settings.linux_container_settings
            runtimes = [(linux_container_settings.java11_runtime, "11"), (linux_container_settings.java8_runtime, "8")]
            for runtime_name, version in [(r, v) for (r, v) in runtimes if r is not None]:
                runtime = self.Runtime(display_name=runtime_name,
                                       configs={"linux_fx_version": runtime_name},
                                       github_actions_properties={"github_actions_version": version},
                                       linux=True,
                                       )
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


class _FunctionAppStackRuntimeHelper(_AbstractStackRuntimeHelper):
    # pylint: disable=too-few-public-methods,too-many-instance-attributes
    class Runtime:
        def __init__(self, name=None, version=None, is_preview=False, supported_func_versions=None, linux=False,
                     app_settings_dict=None, site_config_dict=None, app_insights=False, default=False):
            self.name = name
            self.version = version
            self.is_preview = is_preview
            self.supported_func_versions = [] if not supported_func_versions else supported_func_versions
            self.linux = linux
            self.app_settings_dict = dict() if not app_settings_dict else app_settings_dict
            self.site_config_dict = dict() if not site_config_dict else site_config_dict
            self.app_insights = app_insights
            self.default = default

            self.display_name = "{}|{}".format(name, version) if version else name

        # used for displaying stacks
        def to_dict(self):
            return {"runtime": self.name,
                    "version": self.version,
                    "supported_functions_versions": self.supported_func_versions}

    def __init__(self, cmd, linux=False, windows=False):
        self.disallowed_functions_versions = {"~1", "~2"}
        self.KEYS = FUNCTIONS_STACKS_API_KEYS()
        super().__init__(cmd, linux=linux, windows=windows)

    def resolve(self, runtime, version=None, functions_version=None, linux=False):
        stacks = self.stacks
        runtimes = [r for r in stacks if r.linux == linux and runtime == r.name]
        os = LINUX_OS_NAME if linux else WINDOWS_OS_NAME
        if not runtimes:
            supported_runtimes = [r.name for r in stacks if r.linux == linux]
            raise ValidationError("Runtime {0} not supported for os {1}. Supported runtimes for os {1} are: {2}. "
                                  "Run 'az functionapp list-runtimes' for more details on supported runtimes. "
                                  .format(runtime, os, supported_runtimes))
        if version is None:
            return self.get_default_version(runtime, functions_version, linux)
        matched_runtime_version = next((r for r in runtimes if r.version == version), None)
        if not matched_runtime_version:
            # help convert previously acceptable versions into correct ones if match not found
            old_to_new_version = {
                "11": "11.0",
                "8": "8.0"
            }
            new_version = old_to_new_version.get(version)
            matched_runtime_version = next((r for r in runtimes if r.version == new_version), None)
        if not matched_runtime_version:
            versions = [r.version for r in runtimes]
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

    def get_default_version(self, runtime, functions_version, linux=False):
        runtimes = [r for r in self.stacks if r.linux == linux and r.name == runtime]
        runtimes.sort(key=lambda r: r.default, reverse=True)  # make runtimes with default=True appear first
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
        import re
        return re.sub(r"[^\d\.]", "", name)

    # format version names while maintaining uniqueness
    def _format_version_names(self, runtime_to_version):
        formatted_runtime_to_version = {}
        for runtime, versions in runtime_to_version.items():
            formatted_runtime_to_version[runtime] = formatted_runtime_to_version.get(runtime, dict())
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
                }

                runtime_name = (runtime_settings.app_settings_dictionary.get(self.KEYS.FUNCTIONS_WORKER_RUNTIME) or
                                major_version_name)
                runtime_to_version[runtime_name] = runtime_to_version.get(runtime_name, dict())
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
                            )

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

                    if linux_settings is not None:
                        self._parse_minor_version(runtime_settings=linux_settings,
                                                  major_version_name=runtime.name,
                                                  minor_version_name=runtime_version,
                                                  runtime_to_version=runtime_to_version_linux)

                    if windows_settings is not None:
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
        raise CLIError("App Insights {} under resource group {} was not found.".format(name, resource_group))
    return appinsights.instrumentation_key


def create_functionapp_app_service_plan(cmd, resource_group_name, name, is_linux, sku, number_of_workers=None,
                                        max_burst=None, location=None, tags=None, zone_redundant=False):
    SkuDescription, AppServicePlan = cmd.get_models('SkuDescription', 'AppServicePlan')
    sku = _normalize_sku(sku)
    tier = get_sku_tier(sku)

    client = web_client_factory(cmd.cli_ctx)
    if location is None:
        location = _get_location_from_resource_group(cmd.cli_ctx, resource_group_name)
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


def is_plan_elastic_premium(cmd, plan_info):
    SkuDescription, AppServicePlan = cmd.get_models('SkuDescription', 'AppServicePlan')
    if isinstance(plan_info, AppServicePlan):
        if isinstance(plan_info.sku, SkuDescription):
            return plan_info.sku.tier == 'ElasticPremium'
    return False


def create_functionapp(cmd, resource_group_name, name, storage_account, plan=None,
                       os_type=None, functions_version=None, runtime=None, runtime_version=None,
                       consumption_plan_location=None, app_insights=None, app_insights_key=None,
                       disable_app_insights=None, deployment_source_url=None,
                       deployment_source_branch='master', deployment_local_git=None,
                       docker_registry_server_password=None, docker_registry_server_user=None,
                       deployment_container_image_name=None, tags=None, assign_identities=None,
                       role='Contributor', scope=None, vnet=None, subnet=None):
    # pylint: disable=too-many-statements, too-many-branches
    if functions_version is None:
        logger.warning("No functions version specified so defaulting to 3. In the future, specifying a version will "
                       "be required. To create a 3.x function you would pass in the flag `--functions-version 3`")
        functions_version = '3'
    if deployment_source_url and deployment_local_git:
        raise MutuallyExclusiveArgumentError('usage error: --deployment-source-url <url> | --deployment-local-git')
    if bool(plan) == bool(consumption_plan_location):
        raise MutuallyExclusiveArgumentError("usage error: --plan NAME_OR_ID | --consumption-plan-location LOCATION")
    from azure.mgmt.web.models import Site
    SiteConfig, NameValuePair = cmd.get_models('SiteConfig', 'NameValuePair')
    docker_registry_server_url = parse_docker_image_name(deployment_container_image_name)
    disable_app_insights = (disable_app_insights == "true")

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
                               subnet_name=subnet_info["subnet_name"])
        site_config.vnet_route_all_enabled = True
        subnet_resource_id = subnet_info["subnet_resource_id"]
    else:
        subnet_resource_id = None

    functionapp_def = Site(location=None, site_config=site_config, tags=tags,
                           virtual_network_subnet_id=subnet_resource_id)

    plan_info = None
    if runtime is not None:
        runtime = runtime.lower()

    if consumption_plan_location:
        locations = list_consumption_locations(cmd)
        location = next((loc for loc in locations if loc['name'].lower() == consumption_plan_location.lower()), None)
        if location is None:
            raise ValidationError("Location is invalid. Use: az functionapp list-consumption-locations")
        functionapp_def.location = consumption_plan_location
        functionapp_def.kind = 'functionapp'
        # if os_type is None, the os type is windows
        is_linux = bool(os_type and os_type.lower() == LINUX_OS_NAME)

    else:  # apps with SKU based plan
        if is_valid_resource_id(plan):
            parse_result = parse_resource_id(plan)
            plan_info = client.app_service_plans.get(parse_result['resource_group'], parse_result['name'])
        else:
            plan_info = client.app_service_plans.get(resource_group_name, plan)
        if not plan_info:
            raise CLIError("The plan '{}' doesn't exist".format(plan))
        location = plan_info.location
        is_linux = bool(plan_info.reserved)
        functionapp_def.server_farm_id = plan
        functionapp_def.location = location

    if functions_version == '2' and functionapp_def.location in FUNCTIONS_NO_V2_REGIONS:
        raise ValidationError("2.x functions are not supported in this region. To create a 3.x function, "
                              "pass in the flag '--functions-version 3'")

    if is_linux and not runtime and (consumption_plan_location or not deployment_container_image_name):
        raise ArgumentUsageError(
            "usage error: --runtime RUNTIME required for linux functions apps without custom image.")

    if runtime is None and runtime_version is not None:
        raise ArgumentUsageError('Must specify --runtime to use --runtime-version')

    runtime_helper = _FunctionAppStackRuntimeHelper(cmd, linux=is_linux, windows=(not is_linux))
    matched_runtime = runtime_helper.resolve("dotnet" if not runtime else runtime,
                                             runtime_version, functions_version, is_linux)

    site_config_dict = matched_runtime.site_config_dict
    app_settings_dict = matched_runtime.app_settings_dict

    con_string = _validate_and_get_connection_string(cmd.cli_ctx, resource_group_name, storage_account)

    if is_linux:
        functionapp_def.kind = 'functionapp,linux'
        functionapp_def.reserved = True
        is_consumption = consumption_plan_location is not None
        if not is_consumption:
            site_config.app_settings.append(NameValuePair(name='MACHINEKEY_DecryptionKey',
                                                          value=str(hexlify(urandom(32)).decode()).upper()))
            if deployment_container_image_name:
                functionapp_def.kind = 'functionapp,linux,container'
                site_config.app_settings.append(NameValuePair(name='DOCKER_CUSTOM_IMAGE_NAME',
                                                              value=deployment_container_image_name))
                site_config.app_settings.append(NameValuePair(name='FUNCTION_APP_EDIT_MODE', value='readOnly'))
                site_config.app_settings.append(NameValuePair(name='WEBSITES_ENABLE_APP_SERVICE_STORAGE',
                                                              value='false'))
                site_config.linux_fx_version = _format_fx_version(deployment_container_image_name)

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

    # set site configs
    for prop, value in site_config_dict.as_dict().items():
        snake_case_prop = _convert_camel_to_snake_case(prop)
        setattr(site_config, snake_case_prop, value)

    # temporary workaround for dotnet-isolated linux consumption apps
    if is_linux and consumption_plan_location is not None and runtime == 'dotnet-isolated':
        site_config.linux_fx_version = ''

    # adding app settings
    for app_setting, value in app_settings_dict.items():
        site_config.app_settings.append(NameValuePair(name=app_setting, value=value))

    site_config.app_settings.append(NameValuePair(name='FUNCTIONS_EXTENSION_VERSION',
                                                  value=_get_extension_version_functionapp(functions_version)))
    site_config.app_settings.append(NameValuePair(name='AzureWebJobsStorage', value=con_string))

    # If plan is not consumption or elastic premium, we need to set always on
    if consumption_plan_location is None and not is_plan_elastic_premium(cmd, plan_info):
        site_config.always_on = True

    # If plan is elastic premium or consumption, we need these app settings
    if is_plan_elastic_premium(cmd, plan_info) or consumption_plan_location is not None:
        site_config.app_settings.append(NameValuePair(name='WEBSITE_CONTENTAZUREFILECONNECTIONSTRING',
                                                      value=con_string))
        site_config.app_settings.append(NameValuePair(name='WEBSITE_CONTENTSHARE', value=_get_content_share_name(name)))

    create_app_insights = False

    if app_insights_key is not None:
        site_config.app_settings.append(NameValuePair(name='APPINSIGHTS_INSTRUMENTATIONKEY',
                                                      value=app_insights_key))
    elif app_insights is not None:
        instrumentation_key = get_app_insights_key(cmd.cli_ctx, resource_group_name, app_insights)
        site_config.app_settings.append(NameValuePair(name='APPINSIGHTS_INSTRUMENTATIONKEY',
                                                      value=instrumentation_key))
    elif disable_app_insights or not matched_runtime.app_insights:
        # set up dashboard if no app insights
        site_config.app_settings.append(NameValuePair(name='AzureWebJobsDashboard', value=con_string))
    elif not disable_app_insights and matched_runtime.app_insights:
        create_app_insights = True

    poller = client.web_apps.begin_create_or_update(resource_group_name, name, functionapp_def)
    functionapp = LongRunningOperation(cmd.cli_ctx)(poller)

    if consumption_plan_location and is_linux:
        logger.warning("Your Linux function app '%s', that uses a consumption plan has been successfully "
                       "created but is not active until content is published using "
                       "Azure Portal or the Functions Core Tools.", name)
    else:
        _set_remote_or_local_git(cmd, functionapp, resource_group_name, name, deployment_source_url,
                                 deployment_source_branch, deployment_local_git)

    if create_app_insights:
        try:
            try_create_application_insights(cmd, functionapp)
        except Exception:  # pylint: disable=broad-except
            logger.warning('Error while trying to create and configure an Application Insights for the Function App. '
                           'Please use the Azure Portal to create and configure the Application Insights, if needed.')
            update_app_settings(cmd, functionapp.resource_group, functionapp.name,
                                ['AzureWebJobsDashboard={}'.format(con_string)])

    if deployment_container_image_name:
        update_container_settings_functionapp(cmd, resource_group_name, name, docker_registry_server_url,
                                              deployment_container_image_name, docker_registry_server_user,
                                              docker_registry_server_password)

    if assign_identities is not None:
        identity = assign_identity(cmd, resource_group_name, name, assign_identities,
                                   role, None, scope)
        functionapp.identity = identity

    return functionapp


def _get_extension_version_functionapp(functions_version):
    if functions_version is not None:
        return '~{}'.format(functions_version)
    return '~2'


def _get_app_setting_set_functionapp(site_config, app_setting):
    return list(filter(lambda x: x.name == app_setting, site_config.app_settings))


def _convert_camel_to_snake_case(text):
    return reduce(lambda x, y: x + ('_' if y.isupper() else '') + y, text).lower()


def _get_runtime_version_functionapp(version_string, is_linux):
    import re
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


def _get_content_share_name(app_name):
    # content share name should be up to 63 characters long, lowercase letter and digits, and random
    # so take the first 50 characters of the app name and add the last 12 digits of a random uuid
    share_name = app_name[0:50]
    suffix = str(uuid.uuid4()).split('-')[-1]
    return share_name.lower() + suffix


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

    update_app_settings(cmd, functionapp.resource_group, functionapp.name,
                        ['APPINSIGHTS_INSTRUMENTATIONKEY={}'.format(appinsights.instrumentation_key)])


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


def list_consumption_locations(cmd):
    client = web_client_factory(cmd.cli_ctx)
    regions = client.list_geo_regions(sku='Dynamic')
    return [{'name': x.name.lower().replace(' ', '')} for x in regions]


def list_locations(cmd, sku, linux_workers_enabled=None):
    web_client = web_client_factory(cmd.cli_ctx)
    full_sku = get_sku_tier(sku)
    web_client_geo_regions = web_client.list_geo_regions(sku=full_sku, linux_workers_enabled=linux_workers_enabled)

    providers_client = providers_client_factory(cmd.cli_ctx)
    providers_client_locations_list = getattr(providers_client.get('Microsoft.Web'), 'resource_types', [])
    for resource_type in providers_client_locations_list:
        if resource_type.resource_type == 'sites':
            providers_client_locations_list = resource_type.locations
            break

    return [geo_region for geo_region in web_client_geo_regions if geo_region.name in providers_client_locations_list]


def _check_zip_deployment_status(cmd, rg_name, name, deployment_status_url, authorization, timeout=None):
    import requests
    from azure.cli.core.util import should_disable_connection_verify
    total_trials = (int(timeout) // 2) if timeout else 450
    num_trials = 0
    while num_trials < total_trials:
        time.sleep(2)
        response = requests.get(deployment_status_url, headers=authorization,
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
    hy_co_client = hycos_mgmt_client_factory(cmd.cli_ctx, cmd.cli_ctx)
    namespace_client = namespaces_mgmt_client_factory(cmd.cli_ctx, cmd.cli_ctx)

    hy_co_id = ''
    for n in namespace_client.list():
        logger.warning(n.name)
        if n.name == namespace:
            hy_co_id = n.id

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
    hy_co = hy_co_client.get(hy_co_resource_group, namespace, hybrid_connection)

    # if the hybrid connection does not have a default sender authorization
    # rule, create it
    hy_co_rules = hy_co_client.list_authorization_rules(hy_co_resource_group, namespace, hybrid_connection)
    has_default_sender_key = False
    for r in hy_co_rules:
        if r.name.lower() == "defaultsender":
            for z in r.rights:
                if z == z.send:
                    has_default_sender_key = True

    if not has_default_sender_key:
        rights = [AccessRights.send]
        hy_co_client.create_or_update_authorization_rule(hy_co_resource_group, namespace, hybrid_connection,
                                                         "defaultSender", rights)

    hy_co_keys = hy_co_client.list_keys(hy_co_resource_group, namespace, hybrid_connection, "defaultSender")
    hy_co_info = hy_co.id
    hy_co_metadata = ast.literal_eval(hy_co.user_metadata)
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
                          send_key_value=hy_co_keys.primary_key,
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

    hy_co_client = hycos_mgmt_client_factory(cmd.cli_ctx, cmd.cli_ctx)
    # calling the relay function to obtain information about the hc in question
    hy_co = hy_co_client.get(relay_resource_group, namespace, hybrid_connection)

    # if the hybrid connection does not have a default sender authorization
    # rule, create it
    hy_co_rules = hy_co_client.list_authorization_rules(relay_resource_group, namespace, hybrid_connection)
    has_default_sender_key = False
    for r in hy_co_rules:
        if r.name.lower() == "defaultsender":
            for z in r.rights:
                if z == z.send:
                    has_default_sender_key = True

    if not has_default_sender_key:
        rights = [AccessRights.send]
        hy_co_client.create_or_update_authorization_rule(relay_resource_group, namespace, hybrid_connection,
                                                         "defaultSender", rights)

    hy_co_keys = hy_co_client.list_keys(relay_resource_group, namespace, hybrid_connection, "defaultSender")
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
        key = hy_co_keys.primary_key
    elif key_type.lower() == "secondary":
        key = hy_co_keys.secondary_key
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
    linux_webapp = show_webapp(cmd, resource_group_name, name, slot)
    is_linux = linux_webapp.reserved
    if is_linux:
        return logger.warning("hybrid connections not supported on a linux app.")

    client = web_client_factory(cmd.cli_ctx)
    if slot is None:
        return_hc = client.web_apps.delete_hybrid_connection(resource_group_name, name, namespace, hybrid_connection)
    else:
        return_hc = client.web_apps.delete_hybrid_connection_slot(resource_group_name, name, namespace,
                                                                  hybrid_connection, slot)
    return return_hc


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
    return _add_vnet_integration(cmd, name, resource_group_name, vnet, subnet, slot, skip_delegation_check)


def _add_vnet_integration(cmd, name, resource_group_name, vnet, subnet, slot=None, skip_delegation_check=False):
    subnet_info = _get_subnet_info(cmd=cmd,
                                   resource_group_name=resource_group_name,
                                   subnet=subnet,
                                   vnet=vnet)
    client = web_client_factory(cmd.cli_ctx, api_version="2021-01-01")

    app = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot, client=client)

    parsed_plan = parse_resource_id(app.server_farm_id)
    plan_info = client.app_service_plans.get(parsed_plan['resource_group'], parsed_plan["name"])

    if skip_delegation_check:
        logger.warning('Skipping delegation check. Ensure that subnet is delegated to Microsoft.Web/serverFarms.'
                       ' Missing delegation can cause "Bad Request" error.')
    else:
        _vnet_delegation_check(cmd, subnet_subscription_id=subnet_info["subnet_subscription_id"],
                               vnet_resource_group=subnet_info["resource_group_name"],
                               vnet_name=subnet_info["vnet_name"],
                               subnet_name=subnet_info["subnet_name"])

    app.virtual_network_subnet_id = subnet_info["subnet_resource_id"]

    _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'begin_create_or_update', slot,
                            client=client, extra_parameter=app)

    # Enable Route All configuration
    config = get_site_configs(cmd, resource_group_name, name, slot)
    if config.vnet_route_all_enabled is not True:
        config = update_site_configs(cmd, resource_group_name, name, slot=slot, vnet_route_all_enabled='true')

    return {
        "id": subnet_info["vnet_resource_id"],
        "location": plan_info.location,  # must be the same as vnet location bc of validation check
        "name": subnet_info["vnet_name"],
        "resourceGroup": subnet_info["resource_group_name"],
        "subnetResourceId": subnet_info["subnet_resource_id"]
    }


def _vnet_delegation_check(cmd, subnet_subscription_id, vnet_resource_group, vnet_name, subnet_name):
    from azure.cli.core.commands.client_factory import get_subscription_id
    Delegation = cmd.get_models('Delegation', resource_type=ResourceType.MGMT_NETWORK)
    vnet_client = network_client_factory(cmd.cli_ctx)

    if get_subscription_id(cmd.cli_ctx).lower() != subnet_subscription_id.lower():
        logger.warning('Cannot validate subnet in other subscription for delegation to Microsoft.Web/serverFarms.'
                       ' Missing delegation can cause "Bad Request" error.')
        logger.warning('To manually add a delegation, use the command: az network vnet subnet update '
                       '--resource-group %s '
                       '--name %s '
                       '--vnet-name %s '
                       '--delegations Microsoft.Web/serverFarms', vnet_resource_group, subnet_name, vnet_name)
    else:
        subnetObj = vnet_client.subnets.get(vnet_resource_group, vnet_name, subnet_name)
        delegations = subnetObj.delegations
        delegated = False
        for d in delegations:
            if d.service_name.lower() == "microsoft.web/serverfarms".lower():
                delegated = True

        if not delegated:
            subnetObj.delegations = [Delegation(name="delegation", service_name="Microsoft.Web/serverFarms")]
            vnet_client.subnets.begin_create_or_update(vnet_resource_group, vnet_name, subnet_name,
                                                       subnet_parameters=subnetObj)


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
    vnet_client = network_client_factory(cli_ctx)
    list_all_vnets = vnet_client.virtual_networks.list_all()

    vnets = []
    for v in list_all_vnets:
        if vnet in (v.name, v.id):
            vnet_details = parse_resource_id(v.id)
            vnet_resource_group = vnet_details['resource_group']
            vnets.append((v.id, v.name, vnet_resource_group))

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
              app_service_environment=None):
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
    os_name = os_type if os_type else detect_os_form_src(src_dir, html)
    _is_linux = os_name.lower() == LINUX_OS_NAME
    helper = _StackRuntimeHelper(cmd, linux=_is_linux, windows=not _is_linux)

    if runtime and html:
        raise MutuallyExclusiveArgumentError('Conflicting parameters: cannot have both --runtime and --html specified.')

    if runtime:
        runtime = helper.remove_delimiters(runtime)
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
            raise CLIError("Unable to retrieve details of the existing app '{}'. Please check that the app "
                           "is a part of the current subscription if updating an existing app. If creating "
                           "a new app, app names must be globally unique. Please try a more unique name or "
                           "leave unspecified to receive a randomly generated name.".format(name))
        current_rg = app_details.resource_group
        if resource_group_name is not None and (resource_group_name.lower() != current_rg.lower()):
            raise CLIError("The webapp '{}' exists in ResourceGroup '{}' and does not "
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
            raise CLIError("The plan name entered '{}' does not match the plan name that the webapp is hosted in '{}'."
                           "Please check if you have configured defaults for plan name and re-run command."
                           .format(plan, current_plan))
        plan = plan or plan_details['name']
        plan_info = client.app_service_plans.get(plan_details['resource_group'], plan)
        sku = plan_info.sku.name if isinstance(plan_info, AppServicePlan) else 'Free'
        current_os = 'Linux' if plan_info.reserved else 'Windows'
        # Raise error if current OS of the app is different from the current one
        if current_os.lower() != os_name.lower():
            raise CLIError("The webapp '{}' is a {} app. The code detected at '{}' will default to "
                           "'{}'. Please create a new app "
                           "to continue this operation. For more information on default behaviors, "
                           "see https://docs.microsoft.com/cli/azure/webapp?view=azure-cli-latest#az_webapp_up."
                           .format(name, current_os, src_dir, os_name))
        _is_linux = plan_info.reserved
        # for an existing app check if the runtime version needs to be updated
        # Get site config to check the runtime version
        site_config = client.web_apps.get_configuration(rg_name, name)
    else:  # need to create new app, check if we need to use default RG or use user entered values
        logger.warning("The webapp '%s' doesn't exist", name)
        sku = get_sku_to_use(src_dir, html, sku, runtime)
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
    logger.warning("Creating AppServicePlan '%s' ...", plan)
    # we will always call the ASP create or update API so that in case of re-deployment, if the SKU or plan setting are
    # updated we update those
    try:
        create_app_service_plan(cmd, rg_name, plan, _is_linux, hyper_v=False, per_site_scaling=False, sku=sku,
                                number_of_workers=1 if _is_linux else None, location=loc,
                                app_service_environment=app_service_environment)
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
    # Zip contents & Deploy
    logger.warning("Creating zip with contents of dir %s ...", src_dir)
    # zip contents & deploy
    zip_file_path = zip_contents_from_dir(src_dir, language)
    enable_zip_deploy(cmd, rg_name, name, zip_file_path)

    if launch_browser:
        logger.warning("Launching app using default browser")
        view_in_browser(cmd, rg_name, name, None, logs)
    else:
        _url = _get_url(cmd, rg_name, name)
        logger.warning("You can launch the app at %s", _url)
        create_json.update({'URL': _url})

    if logs:
        _configure_default_logging(cmd, rg_name, name)
        return get_streaming_log(cmd, rg_name, name)

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
    update_needed = False
    if 'node' in runtime_version:
        settings = []
        for k, v in match.configs.items():
            for app_setting in site_config.app_settings:
                if app_setting.name == k and app_setting.value != v:
                    update_needed = True
                    settings.append('%s=%s', k, v)
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
    user_name, password = _get_site_credential(cmd.cli_ctx, resource_group, name)
    scm_url = _get_scm_url(cmd, resource_group, name)
    import urllib3
    authorization = urllib3.util.make_headers(basic_auth='{}:{}'.format(user_name, password))
    cookies = {}
    if instance is not None:
        cookies['ARRAffinity'] = instance
    requests.get(scm_url + '/api/settings', headers=authorization, verify=not should_disable_connection_verify(),
                 cookies=cookies)


def is_webapp_up(tunnel_server):
    return tunnel_server.is_webapp_up()


def get_tunnel(cmd, resource_group_name, name, port=None, slot=None, instance=None):
    webapp = show_webapp(cmd, resource_group_name, name, slot)
    is_linux = webapp.reserved
    if not is_linux:
        raise CLIError("Only Linux App Service Plans supported, Found a Windows App Service Plan")

    profiles = list_publish_profiles(cmd, resource_group_name, name, slot)
    profile_user_name = next(p['userName'] for p in profiles)
    profile_user_password = next(p['userPWD'] for p in profiles)

    if port is None:
        port = 0  # Will auto-select a free port from 1024-65535
        logger.info('No port defined, creating on random free port')

    # Validate that we have a known instance (case-sensitive)
    if instance is not None:
        instances = list_instances(cmd, resource_group_name, name, slot=slot)
        instance_names = set(i.name for i in instances)
        if instance not in instance_names:
            if slot is not None:
                raise CLIError("The provided instance '{}' is not valid for this webapp and slot.".format(instance))
            raise CLIError("The provided instance '{}' is not valid for this webapp.".format(instance))

    scm_url = _get_scm_url(cmd, resource_group_name, name, slot)

    tunnel_server = TunnelServer('', port, scm_url, profile_user_name, profile_user_password, instance)
    _ping_scm_site(cmd, resource_group_name, name, instance=instance)

    _wait_for_webapp(tunnel_server)
    return tunnel_server


def create_tunnel(cmd, resource_group_name, name, port=None, slot=None, timeout=None, instance=None):
    tunnel_server = get_tunnel(cmd, resource_group_name, name, port, slot, instance)

    t = threading.Thread(target=_start_tunnel, args=(tunnel_server,))
    t.daemon = True
    t.start()

    logger.warning('Opening tunnel on port: %s', tunnel_server.local_port)

    config = get_site_configs(cmd, resource_group_name, name, slot)
    if config.remote_debugging_enabled:
        logger.warning('Tunnel is ready, connect on port %s', tunnel_server.local_port)
    else:
        ssh_user_name = 'root'
        ssh_user_password = 'Docker!'
        logger.warning('SSH is available { username: %s, password: %s }', ssh_user_name, ssh_user_password)

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


def perform_onedeploy(cmd,
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
# pylint: enable=too-many-instance-attributes,too-few-public-methods


def _build_onedeploy_url(params):
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
        deploy_url = deploy_url + '&path=' + params.target_path

    return deploy_url


def _get_onedeploy_status_url(params):
    scm_url = _get_scm_url(params.cmd, params.resource_group_name, params.webapp_name, params.slot)
    return scm_url + '/api/deployments/latest'


def _get_basic_headers(params):
    import urllib3

    user_name, password = _get_site_credential(params.cmd.cli_ctx, params.resource_group_name,
                                               params.webapp_name, params.slot)

    if params.src_path:
        content_type = 'application/octet-stream'
    elif params.src_url:
        content_type = 'application/json'
    else:
        raise CLIError('Unable to determine source location of the artifact being deployed')

    headers = urllib3.util.make_headers(basic_auth='{0}:{1}'.format(user_name, password))
    headers['Cache-Control'] = 'no-cache'
    headers['User-Agent'] = get_az_user_agent()
    headers['Content-Type'] = content_type

    return headers


def _get_onedeploy_request_body(params):
    import os

    if params.src_path:
        logger.info('Deploying from local path: %s', params.src_path)
        try:
            with open(os.path.realpath(os.path.expanduser(params.src_path)), 'rb') as fs:
                body = fs.read()
        except Exception as e:  # pylint: disable=broad-except
            raise CLIError("Either '{}' is not a valid local file path or you do not have permissions to access it"
                           .format(params.src_path)) from e
    elif params.src_url:
        logger.info('Deploying from URL: %s', params.src_url)
        body = json.dumps({
            "packageUri": params.src_url
        })
    else:
        raise CLIError('Unable to determine source location of the artifact being deployed')

    return body


def _update_artifact_type(params):
    import ntpath

    if params.artifact_type is not None:
        return

    # Interpret deployment type from the file extension if the type parameter is not passed
    file_name = ntpath.basename(params.src_path)
    file_extension = file_name.split(".", 1)[1]
    if file_extension in ('war', 'jar', 'ear', 'zip'):
        params.artifact_type = file_extension
    elif file_extension in ('sh', 'bat'):
        params.artifact_type = 'startup'
    else:
        params.artifact_type = 'static'
    logger.warning("Deployment type: %s. To override deployment type, please specify the --type parameter. "
                   "Possible values: war, jar, ear, zip, startup, script, static", params.artifact_type)


def _make_onedeploy_request(params):
    import requests

    from azure.cli.core.util import (
        should_disable_connection_verify,
    )

    # Build the request body, headers, API URL and status URL
    body = _get_onedeploy_request_body(params)
    headers = _get_basic_headers(params)
    deploy_url = _build_onedeploy_url(params)
    deployment_status_url = _get_onedeploy_status_url(params)

    logger.info("Deployment API: %s", deploy_url)
    response = requests.post(deploy_url, data=body, headers=headers, verify=not should_disable_connection_verify())

    # For debugging purposes only, you can change the async deployment into a sync deployment by polling the API status
    # For that, set poll_async_deployment_for_debugging=True
    poll_async_deployment_for_debugging = True

    # check the status of async deployment
    if response.status_code == 202 or response.status_code == 200:
        response_body = None
        if poll_async_deployment_for_debugging:
            logger.info('Polling the status of async deployment')
            response_body = _check_zip_deployment_status(params.cmd, params.resource_group_name, params.webapp_name,
                                                         deployment_status_url, headers, params.timeout)
            logger.info('Async deployment complete. Server response: %s', response_body)
        return response_body

    # API not available yet!
    if response.status_code == 404:
        raise CLIError("This API isn't available in this environment yet!")

    # check if there's an ongoing process
    if response.status_code == 409:
        raise CLIError("Another deployment is in progress. Please wait until that process is complete before "
                       "starting a new deployment. You can track the ongoing deployment at {}"
                       .format(deployment_status_url))

    # check if an error occured during deployment
    if response.status_code:
        raise CLIError("An error occured during deployment. Status Code: {}, Details: {}"
                       .format(response.status_code, response.text))


# OneDeploy
def _perform_onedeploy_internal(params):

    # Update artifact type, if required
    _update_artifact_type(params)

    # Now make the OneDeploy API call
    logger.info("Initiating deployment")
    response = _make_onedeploy_request(params)
    logger.info("Deployment has completed successfully")
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
        webapp = show_webapp(cmd, resource_group_name, name, slot)
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
                              docker_container_logging='true')


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
        return client.web_apps.create_or_update_host_secret_slot(resource_group_name,
                                                                 name,
                                                                 key_type,
                                                                 key_name,
                                                                 slot, key=key_info)
    return client.web_apps.create_or_update_host_secret(resource_group_name,
                                                        name,
                                                        key_type,
                                                        key_name, key=key_info)


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
        return client.web_apps.create_or_update_function_secret_slot(resource_group_name,
                                                                     name,
                                                                     function_name,
                                                                     key_name,
                                                                     slot,
                                                                     key_info)
    return client.web_apps.create_or_update_function_secret(resource_group_name,
                                                            name,
                                                            function_name,
                                                            key_name,
                                                            key_info)


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
        raise CLIError("Could not authenticate to the repository. Please create a Personal Access Token and use "
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
    if(app_runtime_info and app_runtime_info['display_name']):
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
        raise CLIError('Could not detect runtime. Please specify using the --runtime flag.')

    if not _runtime_supports_github_actions(cmd=cmd, runtime_string=app_runtime_string, is_linux=is_linux):
        raise CLIError("Runtime %s is not supported for GitHub Actions deployments." % app_runtime_string)

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
        raise CLIError("The Resource 'Microsoft.Web/sites/%s' under resource group '%s' was not found." %
                       (name, resource_group))
    app_details = get_app_details(cmd, name)
    if app_details is None:
        raise CLIError("Unable to retrieve details of the existing app %s. "
                       "Please check that the app is a part of the current subscription" % name)
    current_rg = app_details.resource_group
    if resource_group is not None and (resource_group.lower() != current_rg.lower()):
        raise CLIError("The webapp %s exists in ResourceGroup %s and does not match "
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
        raise CLIError("Could not authenticate to the repository. Please create a Personal Access Token and use "
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


def _get_publish_profile_from_workflow_file(workflow_file):
    import re
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


def _get_template_file_path(runtime_string, is_linux):
    if not runtime_string:
        raise CLIError('Unable to retrieve workflow template')

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
        raise CLIError('Unable to retrieve workflow template.')
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
        raise CLIError('Unable to retrieve publish profile.')

    # Add publish profile with secrets as a GitHub Actions Secret in the repo
    headers = {}
    headers['Authorization'] = 'Token {}'.format(token)
    headers['Content-Type'] = 'application/json;'
    headers['Accept'] = 'application/json;'

    public_key_url = "https://api.github.com/repos/{}/actions/secrets/public-key".format(repo)
    public_key = requests.get(public_key_url, headers=headers)
    if not public_key.ok:
        raise CLIError('Request to GitHub for public key failed.')
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
    helper = _StackRuntimeHelper(cmd, linux=(is_linux), windows=(not is_linux))
    matched_runtime = helper.resolve(runtime_string, is_linux)
    if not matched_runtime:
        return False
    if matched_runtime.github_actions_properties:
        return True
    return False


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


def _get_app_runtime_info_helper(cmd, app_runtime, app_runtime_version, is_linux):
    helper = _StackRuntimeHelper(cmd, linux=(is_linux), windows=(not is_linux))
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


def _encrypt_github_actions_secret(public_key, secret_value):
    # Encrypt a Unicode string using the public key
    from base64 import b64encode
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")
