# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import threading
import time
import ast

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse  # pylint: disable=import-error
from binascii import hexlify
from os import urandom
import datetime
import json
import ssl
import sys
import uuid
from functools import reduce
from http import HTTPStatus

from six.moves.urllib.request import urlopen  # pylint: disable=import-error, ungrouped-imports
import OpenSSL.crypto
from fabric import Connection

from knack.prompting import prompt_pass, NoTTYException
from knack.util import CLIError
from knack.log import get_logger

from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import is_valid_resource_id, parse_resource_id

from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.applicationinsights import ApplicationInsightsManagementClient
from azure.mgmt.relay.models import AccessRights
from azure.mgmt.web.models import KeyInfo, DefaultErrorResponseException
from azure.cli.command_modules.relay._client_factory import hycos_mgmt_client_factory, namespaces_mgmt_client_factory
from azure.cli.command_modules.network._client_factory import network_client_factory

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.util import in_cloud_console, shell_safe_json_parse, open_page_in_browser, get_json_object, \
    ConfiguredDefaultSetter, sdk_no_wait, get_file_json
from azure.cli.core.util import get_az_user_agent
from azure.cli.core.profiles import ResourceType, get_sdk

from .tunnel import TunnelServer

from .vsts_cd_provider import VstsContinuousDeliveryProvider
from ._params import AUTH_TYPES, MULTI_CONTAINER_TYPES
from ._client_factory import web_client_factory, ex_handler_factory, providers_client_factory
from ._appservice_utils import _generic_site_operation
from .utils import _normalize_sku, get_sku_name, retryable_method
from ._create_util import (zip_contents_from_dir, get_runtime_version_details, create_resource_group, get_app_details,
                           should_create_new_rg, set_location, get_site_availability, get_profile_username,
                           get_plan_to_use, get_lang_from_content, get_rg_to_use, get_sku_to_use,
                           detect_os_form_src)
from ._constants import (FUNCTIONS_STACKS_API_JSON_PATHS, FUNCTIONS_STACKS_API_KEYS,
                         FUNCTIONS_LINUX_RUNTIME_VERSION_REGEX, FUNCTIONS_WINDOWS_RUNTIME_VERSION_REGEX,
                         NODE_VERSION_DEFAULT, RUNTIME_STACKS, FUNCTIONS_NO_V2_REGIONS)

logger = get_logger(__name__)

# pylint:disable=no-member,too-many-lines,too-many-locals

# region "Common routines shared with quick-start extensions."
# Please maintain compatibility in both interfaces and functionalities"


def create_webapp(cmd, resource_group_name, name, plan, runtime=None, startup_file=None,  # pylint: disable=too-many-statements,too-many-branches
                  deployment_container_image_name=None, deployment_source_url=None, deployment_source_branch='master',
                  deployment_local_git=None, docker_registry_server_password=None, docker_registry_server_user=None,
                  multicontainer_config_type=None, multicontainer_config_file=None, tags=None,
                  using_webapp_up=False, language=None, assign_identities=None,
                  role='Contributor', scope=None):
    SiteConfig, SkuDescription, Site, NameValuePair = cmd.get_models(
        'SiteConfig', 'SkuDescription', 'Site', 'NameValuePair')
    if deployment_source_url and deployment_local_git:
        raise CLIError('usage error: --deployment-source-url <url> | --deployment-local-git')

    docker_registry_server_url = parse_docker_image_name(deployment_container_image_name)

    client = web_client_factory(cmd.cli_ctx)
    if is_valid_resource_id(plan):
        parse_result = parse_resource_id(plan)
        plan_info = client.app_service_plans.get(parse_result['resource_group'], parse_result['name'])
    else:
        plan_info = client.app_service_plans.get(resource_group_name, plan)
    if not plan_info:
        raise CLIError("The plan '{}' doesn't exist in the resource group '{}".format(plan, resource_group_name))
    is_linux = plan_info.reserved
    node_default_version = NODE_VERSION_DEFAULT
    location = plan_info.location
    # This is to keep the existing appsettings for a newly created webapp on existing webapp name.
    name_validation = client.check_name_availability(name, 'Site')
    if not name_validation.name_available:
        if name_validation.reason == 'Invalid':
            raise CLIError(name_validation.message)
        logger.warning("Webapp '%s' already exists. The command will use the existing app's settings.", name)
        app_details = get_app_details(cmd, name)
        if app_details is None:
            raise CLIError("Unable to retrieve details of the existing app '{}'. Please check that "
                           "the app is a part of the current subscription".format(name))
        current_rg = app_details.resource_group
        if resource_group_name is not None and (resource_group_name.lower() != current_rg.lower()):
            raise CLIError("The webapp '{}' exists in resource group '{}' and does not "
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
    webapp_def = Site(location=location, site_config=site_config, server_farm_id=plan_info.id, tags=tags,
                      https_only=using_webapp_up)
    helper = _StackRuntimeHelper(cmd, client, linux=is_linux)

    if is_linux:
        if not validate_container_app_create_options(runtime, deployment_container_image_name,
                                                     multicontainer_config_type, multicontainer_config_file):
            raise CLIError("usage error: --runtime | --deployment-container-image-name |"
                           " --multicontainer-config-type TYPE --multicontainer-config-file FILE")
        if startup_file:
            site_config.app_command_line = startup_file

        if runtime:
            site_config.linux_fx_version = runtime
            match = helper.resolve(runtime)
            if not match:
                raise CLIError("Linux Runtime '{}' is not supported."
                               " Please invoke 'az webapp list-runtimes --linux' to cross check".format(runtime))
        elif deployment_container_image_name:
            site_config.linux_fx_version = _format_fx_version(deployment_container_image_name)
            if name_validation.name_available:
                site_config.app_settings.append(NameValuePair(name="WEBSITES_ENABLE_APP_SERVICE_STORAGE",
                                                              value="false"))
        elif multicontainer_config_type and multicontainer_config_file:
            encoded_config_file = _get_linux_multicontainer_encoded_config_from_file(multicontainer_config_file)
            site_config.linux_fx_version = _format_fx_version(encoded_config_file, multicontainer_config_type)

    elif plan_info.is_xenon:  # windows container webapp
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
            raise CLIError("usage error: --startup-file or --deployment-container-image-name or "
                           "--multicontainer-config-type and --multicontainer-config-file is "
                           "only appliable on linux webapp")
        match = helper.resolve(runtime)
        if not match:
            raise CLIError("Runtime '{}' is not supported. Please invoke 'az webapp list-runtimes' to cross check".format(runtime))  # pylint: disable=line-too-long
        match['setter'](cmd=cmd, stack=match, site_config=site_config)

        # Be consistent with portal: any windows webapp should have this even it doesn't have node in the stack
        if not match['displayName'].startswith('node'):
            if name_validation.name_available:
                site_config.app_settings.append(NameValuePair(name="WEBSITE_NODE_DEFAULT_VERSION",
                                                              value=node_default_version))
    else:  # windows webapp without runtime specified
        if name_validation.name_available:
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

    poller = client.web_apps.create_or_update(resource_group_name, name, webapp_def)
    webapp = LongRunningOperation(cmd.cli_ctx)(poller)

    # Ensure SCC operations follow right after the 'create', no precedent appsetting update commands
    _set_remote_or_local_git(cmd, webapp, resource_group_name, name, deployment_source_url,
                             deployment_source_branch, deployment_local_git)

    _fill_ftp_publishing_url(cmd, webapp, resource_group_name, name)

    if deployment_container_image_name:
        update_container_settings(cmd, resource_group_name, name, docker_registry_server_url,
                                  deployment_container_image_name, docker_registry_server_user,
                                  docker_registry_server_password=docker_registry_server_password)

    if assign_identities is not None:
        identity = assign_identity(cmd, resource_group_name, name, assign_identities,
                                   role, None, scope)
        webapp.identity = identity

    return webapp


def validate_container_app_create_options(runtime=None, deployment_container_image_name=None,
                                          multicontainer_config_type=None, multicontainer_config_file=None):
    if bool(multicontainer_config_type) != bool(multicontainer_config_file):
        return False
    opts = [runtime, deployment_container_image_name, multicontainer_config_type]
    return len([x for x in opts if x]) == 1  # you can only specify one out the combinations


def parse_docker_image_name(deployment_container_image_name):
    if not deployment_container_image_name:
        return None
    slash_ix = deployment_container_image_name.rfind('/')
    docker_registry_server_url = deployment_container_image_name[0:slash_ix]
    if slash_ix == -1 or ("." not in docker_registry_server_url and ":" not in docker_registry_server_url):
        return None
    return docker_registry_server_url


def update_app_settings(cmd, resource_group_name, name, settings=None, slot=None, slot_settings=None):
    if not settings and not slot_settings:
        raise CLIError('Usage Error: --settings |--slot-settings')

    settings = settings or []
    slot_settings = slot_settings or []

    app_settings = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                           'list_application_settings', slot)
    result, slot_result = {}, {}
    # pylint: disable=too-many-nested-blocks
    for src, dest in [(settings, result), (slot_settings, slot_result)]:
        for s in src:
            try:
                temp = shell_safe_json_parse(s)
                if isinstance(temp, list):  # a bit messy, but we'd like accept the output of the "list" command
                    for t in temp:
                        if t.get('slotSetting', True):
                            slot_result[t['name']] = t['value']
                            # Mark each setting as the slot setting
                        else:
                            result[t['name']] = t['value']
                else:
                    dest.update(temp)
            except CLIError:
                setting_name, value = s.split('=', 1)
                dest[setting_name] = value

    result.update(slot_result)
    for setting_name, value in result.items():
        app_settings.properties[setting_name] = value
    client = web_client_factory(cmd.cli_ctx)

    result = _generic_settings_operation(cmd.cli_ctx, resource_group_name, name,
                                         'update_application_settings',
                                         app_settings.properties, slot, client)

    app_settings_slot_cfg_names = []
    if slot_result:
        new_slot_setting_names = slot_result.keys()
        slot_cfg_names = client.web_apps.list_slot_configuration_names(resource_group_name, name)
        slot_cfg_names.app_setting_names = slot_cfg_names.app_setting_names or []
        slot_cfg_names.app_setting_names += new_slot_setting_names
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
                                         'update_azure_storage_accounts', azure_storage_accounts.properties,
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
                                         'update_azure_storage_accounts', azure_storage_accounts.properties,
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

    if build_remote and not app.reserved:
        raise CLIError('Remote build is only available on Linux function apps')

    is_consumption = is_plan_consumption(cmd, plan_info)
    if (not build_remote) and is_consumption and app.reserved:
        return upload_zip_to_storage(cmd, resource_group_name, name, src, slot)
    if build_remote:
        add_remote_build_app_settings(cmd, resource_group_name, name, slot)
    else:
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

    # check if there's an ongoing process
    if res.status_code == 409:
        raise CLIError("There may be an ongoing deployment or your app setting has WEBSITE_RUN_FROM_PACKAGE. "
                       "Please track your deployment in {} and ensure the WEBSITE_RUN_FROM_PACKAGE app setting "
                       "is removed.".format(deployment_status_url))

    # check the status of async deployment
    response = _check_zip_deployment_status(cmd, resource_group_name, name, deployment_status_url,
                                            authorization, timeout)
    return response


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

    now = datetime.datetime.now()
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
    except CloudError as ce:
        # This SDK function throws an error if Status Code is 200
        if ce.status_code != 200:
            raise ce


def _generic_settings_operation(cli_ctx, resource_group_name, name, operation_name,
                                setting_properties, slot=None, client=None):
    client = client or web_client_factory(cli_ctx)
    operation = getattr(client.web_apps, operation_name if slot is None else operation_name + '_slot')
    if slot is None:
        return operation(resource_group_name, name, str, setting_properties)

    return operation(resource_group_name, name, slot, str, setting_properties)


def show_webapp(cmd, resource_group_name, name, slot=None, app_instance=None):
    webapp = app_instance
    if not app_instance:  # when the routine is invoked as a help method, not through commands
        webapp = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)
    if not webapp:
        raise CLIError("'{}' app doesn't exist".format(name))
    _rename_server_farm_props(webapp)
    _fill_ftp_publishing_url(cmd, webapp, resource_group_name, name, slot)
    return webapp


# for generic updater
def get_webapp(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)


def set_webapp(cmd, resource_group_name, name, slot=None, skip_dns_registration=None,
               skip_custom_domain_verification=None, force_dns_registration=None, ttl_in_seconds=None, **kwargs):
    instance = kwargs['parameters']
    client = web_client_factory(cmd.cli_ctx)
    updater = client.web_apps.create_or_update_slot if slot else client.web_apps.create_or_update
    kwargs = dict(resource_group_name=resource_group_name, name=name, site_envelope=instance,
                  skip_dns_registration=skip_dns_registration,
                  skip_custom_domain_verification=skip_custom_domain_verification,
                  force_dns_registration=force_dns_registration,
                  ttl_in_seconds=ttl_in_seconds)
    if slot:
        kwargs['slot'] = slot

    return updater(**kwargs)


def update_webapp(instance, client_affinity_enabled=None, https_only=None):
    if 'function' in instance.kind:
        raise CLIError("please use 'az functionapp update' to update this function app")
    if client_affinity_enabled is not None:
        instance.client_affinity_enabled = client_affinity_enabled == 'true'
    if https_only is not None:
        instance.https_only = https_only == 'true'

    return instance


def update_functionapp(cmd, instance, plan=None):
    client = web_client_factory(cmd.cli_ctx)
    if plan is not None:
        if is_valid_resource_id(plan):
            dest_parse_result = parse_resource_id(plan)
            dest_plan_info = client.app_service_plans.get(dest_parse_result['resource_group'],
                                                          dest_parse_result['name'])
        else:
            dest_plan_info = client.app_service_plans.get(instance.resource_group, plan)
        if dest_plan_info is None:
            raise CLIError("The plan '{}' doesn't exist".format(plan))
        validate_plan_switch_compatibility(cmd, client, instance, dest_plan_info)
        instance.server_farm_id = dest_plan_info.id
    return instance


def validate_plan_switch_compatibility(cmd, client, src_functionapp_instance, dest_plan_instance):
    general_switch_msg = 'Currently the switch is only allowed between a Consumption or an Elastic Premium plan.'
    src_parse_result = parse_resource_id(src_functionapp_instance.server_farm_id)
    src_plan_info = client.app_service_plans.get(src_parse_result['resource_group'],
                                                 src_parse_result['name'])
    if src_plan_info is None:
        raise CLIError('Could not determine the current plan of the functionapp')
    if not (is_plan_consumption(cmd, src_plan_info) or is_plan_elastic_premium(cmd, src_plan_info)):
        raise CLIError('Your functionapp is not using a Consumption or an Elastic Premium plan. ' + general_switch_msg)
    if not (is_plan_consumption(cmd, dest_plan_instance) or is_plan_elastic_premium(cmd, dest_plan_instance)):
        raise CLIError('You are trying to move to a plan that is not a Consumption or an Elastic Premium plan. ' +
                       general_switch_msg)


def set_functionapp(cmd, resource_group_name, name, **kwargs):
    instance = kwargs['parameters']
    if 'function' not in instance.kind:
        raise CLIError('Not a function app to update')
    client = web_client_factory(cmd.cli_ctx)
    return client.web_apps.create_or_update(resource_group_name, name, site_envelope=instance)


def list_webapp(cmd, resource_group_name=None):
    result = _list_app(cmd.cli_ctx, resource_group_name)
    return [r for r in result if 'function' not in r.kind]


def list_deleted_webapp(cmd, resource_group_name=None, name=None, slot=None):
    result = _list_deleted_app(cmd.cli_ctx, resource_group_name, name, slot)
    return sorted(result, key=lambda site: site.deleted_site_id)


def restore_deleted_webapp(cmd, deleted_id, resource_group_name, name, slot=None, restore_content_only=None):
    DeletedAppRestoreRequest = cmd.get_models('DeletedAppRestoreRequest')
    request = DeletedAppRestoreRequest(deleted_site_id=deleted_id, recover_configuration=not restore_content_only)
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'restore_from_deleted_app', slot, request)


def list_function_app(cmd, resource_group_name=None):
    result = _list_app(cmd.cli_ctx, resource_group_name)
    return [r for r in result if 'function' in r.kind]


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
    result = list()
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
    UserAssignedIdentitiesValue = cmd.get_models('ManagedServiceIdentityUserAssignedIdentitiesValue')
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

        poller = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'create_or_update', slot, webapp)
        return LongRunningOperation(cmd.cli_ctx)(poller)

    from azure.cli.core.commands.arm import assign_identity as _assign_identity
    webapp = _assign_identity(cmd.cli_ctx, getter, setter, role, scope)
    return webapp.identity


def show_identity(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot).identity


def remove_identity(cmd, resource_group_name, name, remove_identities=None, slot=None):
    IdentityType = cmd.get_models('ManagedServiceIdentityType')
    UserAssignedIdentitiesValue = cmd.get_models('ManagedServiceIdentityUserAssignedIdentitiesValue')
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

        poller = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'create_or_update', slot, webapp)
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
    # API Version 2019-08-01 (latest as of writing this code) does not return slot instances, however 2018-02-01 does
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'list_instance_identifiers', slot,
                                   api_version="2018-02-01")


# Currently using hardcoded values instead of this function. This function calls the stacks API;
# Stacks API is updated with Antares deployments,
# which are infrequent and don't line up with stacks EOL schedule.
def list_runtimes(cmd, linux=False):
    client = web_client_factory(cmd.cli_ctx)
    runtime_helper = _StackRuntimeHelper(cmd=cmd, client=client, linux=linux)

    return [s['displayName'] for s in runtime_helper.stacks]


def list_runtimes_hardcoded(linux=False):
    if linux:
        return [s['displayName'] for s in get_file_json(RUNTIME_STACKS)['linux']]
    return [s['displayName'] for s in get_file_json(RUNTIME_STACKS)['windows']]


def _rename_server_farm_props(webapp):
    # Should be renamed in SDK in a future release
    setattr(webapp, 'app_service_plan_id', webapp.server_farm_id)
    del webapp.server_farm_id
    return webapp


def delete_function_app(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'delete', slot)


def delete_webapp(cmd, resource_group_name, name, keep_metrics=None, keep_empty_plan=None,
                  keep_dns_registration=None, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        client.web_apps.delete_slot(resource_group_name, name, slot,
                                    delete_metrics=False if keep_metrics else None,
                                    delete_empty_server_farm=False if keep_empty_plan else None,
                                    skip_dns_registration=False if keep_dns_registration else None)
    else:
        client.web_apps.delete(resource_group_name, name,
                               delete_metrics=False if keep_metrics else None,
                               delete_empty_server_farm=False if keep_empty_plan else None,
                               skip_dns_registration=False if keep_dns_registration else None)


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
    url = next(p['publishUrl'] for p in profiles if p['publishMethod'] == 'FTP')
    setattr(webapp, 'ftpPublishingUrl', url)
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
    linux_fx = fx_version if web_app.reserved else None
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
    if not any([linux_fx_version.startswith(s) for s in MULTI_CONTAINER_TYPES]):
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
                  'auto_heal_enabled', 'use32_bit_worker_process', 'http20_enabled']
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
    result = {}
    for s in generic_configurations:
        try:
            result.update(get_json_object(s))
        except CLIError:
            config_name, value = s.split('=', 1)
            result[config_name] = value

    for config_name, value in result.items():
        setattr(configs, config_name, value)

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
                                         app_settings.properties, slot, client)

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
                                         'update_azure_storage_accounts', azure_storage_accounts.properties,
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
                                         conn_strings.properties, slot, client)

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
                                       conn_strings.properties, slot, client)


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
    HostNameBinding = cmd.get_models('HostNameBinding')
    client = web_client_factory(cmd.cli_ctx)
    webapp = client.web_apps.get(resource_group_name, webapp_name)
    if not webapp:
        raise CLIError("'{}' app doesn't exist".format(webapp_name))
    binding = HostNameBinding(location=webapp.location, site_name=webapp.name)
    if slot is None:
        return client.web_apps.create_or_update_host_name_binding(resource_group_name, webapp.name, hostname, binding)

    return client.web_apps.create_or_update_host_name_binding_slot(resource_group_name, webapp.name, hostname, binding,
                                                                   slot)


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

    poller = client.web_apps.create_or_update_slot(resource_group_name, webapp, slot_def, slot)
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

    poller = client.web_apps.create_or_update_slot(resource_group_name, name, slot_def, slot)
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
                                app_settings.properties, slot, client)
    _generic_settings_operation(cmd.cli_ctx, resource_group_name, webapp,
                                'update_connection_strings',
                                connection_strings.properties, slot, client)


def config_source_control(cmd, resource_group_name, name, repo_url, repository_type='git', branch=None,  # pylint: disable=too-many-locals
                          manual_integration=None, git_token=None, slot=None, cd_app_type=None,
                          app_working_dir=None, nodejs_task_runner=None, python_framework=None,
                          python_version=None, cd_account_create=None, cd_project_url=None, test=None,
                          slot_swap=None, private_repo_username=None, private_repo_password=None):
    client = web_client_factory(cmd.cli_ctx)
    location = _get_location_from_webapp(client, resource_group_name, name)

    if cd_project_url:
        # Add default values
        cd_app_type = 'AspNet' if cd_app_type is None else cd_app_type
        python_framework = 'Django' if python_framework is None else python_framework
        python_version = 'Python 3.5.3 x86' if python_version is None else python_version

        webapp_list = None if test is None else list_webapp(resource_group_name)
        vsts_provider = VstsContinuousDeliveryProvider()
        cd_app_type_details = {
            'cd_app_type': cd_app_type,
            'app_working_dir': app_working_dir,
            'nodejs_task_runner': nodejs_task_runner,
            'python_framework': python_framework,
            'python_version': python_version
        }
        try:
            status = vsts_provider.setup_continuous_delivery(cmd.cli_ctx, resource_group_name, name, repo_url,
                                                             branch, git_token, slot_swap, cd_app_type_details,
                                                             cd_project_url, cd_account_create, location, test,
                                                             private_repo_username, private_repo_password, webapp_list)
        except RuntimeError as ex:
            raise CLIError(ex)
        logger.warning(status.status_message)
        return status
    non_vsts_params = [cd_app_type, app_working_dir, nodejs_task_runner, python_framework,
                       python_version, cd_account_create, test, slot_swap]
    if any(non_vsts_params):
        raise CLIError('Following parameters are of no use when cd_project_url is None: ' +
                       'cd_app_type, app_working_dir, nodejs_task_runner, python_framework,' +
                       'python_version, cd_account_create, test, slot_swap')
    from azure.mgmt.web.models import SiteSourceControl, SourceControl
    if git_token:
        sc = SourceControl(location=location, source_control_name='GitHub', token=git_token)
        client.update_source_control('GitHub', sc)

    source_control = SiteSourceControl(location=location, repo_url=repo_url, branch=branch,
                                       is_manual_integration=manual_integration,
                                       is_mercurial=(repository_type != 'git'))

    # SCC config can fail if previous commands caused SCMSite shutdown, so retry here.
    for i in range(5):
        try:
            poller = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                             'create_or_update_source_control',
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
    SiteConfigResource = cmd.get_models('SiteConfigResource')
    client = web_client_factory(cmd.cli_ctx)
    location = _get_location_from_webapp(client, resource_group_name, name)
    site_config = SiteConfigResource(location=location)
    site_config.scm_type = 'LocalGit'
    if slot is None:
        client.web_apps.create_or_update_configuration(resource_group_name, name, site_config)
    else:
        client.web_apps.create_or_update_configuration_slot(resource_group_name, name,
                                                            site_config, slot)

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


def create_app_service_plan(cmd, resource_group_name, name, is_linux, hyper_v, per_site_scaling=False,
                            app_service_environment=None, sku='B1', number_of_workers=None, location=None,
                            tags=None, no_wait=False):
    HostingEnvironmentProfile, SkuDescription, AppServicePlan = cmd.get_models(
        'HostingEnvironmentProfile', 'SkuDescription', 'AppServicePlan')
    sku = _normalize_sku(sku)
    _validate_asp_sku(app_service_environment, sku)
    if is_linux and hyper_v:
        raise CLIError('usage error: --is-linux | --hyper-v')

    client = web_client_factory(cmd.cli_ctx)
    if app_service_environment:
        if hyper_v:
            raise CLIError('Windows containers is not yet supported in app service environment')
        ase_id = _validate_app_service_environment_id(cmd.cli_ctx, app_service_environment, resource_group_name)
        ase_def = HostingEnvironmentProfile(id=ase_id)
        ase_list = client.app_service_environments.list()
        ase_found = False
        for ase in ase_list:
            if ase.id.lower() == ase_id.lower():
                location = ase.location
                ase_found = True
                break
        if not ase_found:
            raise CLIError("App service environment '{}' not found in subscription.".format(ase_id))
    else:  # Non-ASE
        ase_def = None
        if location is None:
            location = _get_location_from_resource_group(cmd.cli_ctx, resource_group_name)

    # the api is odd on parameter naming, have to live with it for now
    sku_def = SkuDescription(tier=get_sku_name(sku), name=sku, capacity=number_of_workers)
    plan_def = AppServicePlan(location=location, tags=tags, sku=sku_def,
                              reserved=(is_linux or None), hyper_v=(hyper_v or None), name=name,
                              per_site_scaling=per_site_scaling, hosting_environment_profile=ase_def)
    return sdk_no_wait(no_wait, client.app_service_plans.create_or_update, name=name,
                       resource_group_name=resource_group_name, app_service_plan=plan_def)


def update_app_service_plan(instance, sku=None, number_of_workers=None):
    if number_of_workers is None and sku is None:
        logger.warning('No update is done. Specify --sku and/or --number-of-workers.')
    sku_def = instance.sku
    if sku is not None:
        sku = _normalize_sku(sku)
        sku_def.tier = get_sku_name(sku)
        sku_def.name = sku

    if number_of_workers is not None:
        sku_def.capacity = number_of_workers
    instance.sku = sku_def
    return instance


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
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, webapp_name, 'list_backups',
                                   slot)


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
    except DefaultErrorResponseException:
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


def _get_location_from_resource_group(cli_ctx, resource_group_name):
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    group = client.resource_groups.get(resource_group_name)
    return group.location


def _get_location_from_webapp(client, resource_group_name, webapp):
    webapp = client.web_apps.get(resource_group_name, webapp)
    if not webapp:
        raise CLIError("'{}' app doesn't exist".format(webapp))
    return webapp.location


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
    webapp = show_webapp(cmd, resource_group_name, name, slot=slot)
    for host in webapp.host_name_ssl_states or []:
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
                                      'list_publishing_credentials', slot)
    return content.result()


def list_publish_profiles(cmd, resource_group_name, name, slot=None, xml=False):
    import xmltodict

    content = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                      'list_publishing_profile_xml_with_secrets', slot)
    full_xml = ''
    for f in content:
        full_xml += f.decode()

    if not xml:
        profiles = xmltodict.parse(full_xml, xml_attribs=True)['publishData']['publishProfile']
        converted = []
        for profile in profiles:
            new = {}
            for key in profile:
                # strip the leading '@' xmltodict put in for attributes
                new[key.lstrip('@')] = profile[key]
            converted.append(new)
        return converted
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
                                       SiteLogsConfig, HttpLogsConfig, FileSystemHttpLogsConfig,
                                       EnabledConfig)
    client = web_client_factory(cmd.cli_ctx)
    # TODO: ensure we call get_site only once
    site = client.web_apps.get(resource_group_name, name)
    if not site:
        raise CLIError("'{}' app doesn't exist".format(name))
    location = site.location

    application_logs = None
    if application_logging is not None:
        if not application_logging:
            level = 'Off'
        elif level is None:
            level = 'Error'
        fs_log = FileSystemApplicationLogsConfig(level=level)
        application_logs = ApplicationLogsConfig(file_system=fs_log)

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
    return client.web_apps.update_configuration_slot(resource_group_name, webapp, site_config, slot)


def list_slots(cmd, resource_group_name, webapp):
    client = web_client_factory(cmd.cli_ctx)
    slots = list(client.web_apps.list_slots(resource_group_name, webapp))
    for slot in slots:
        slot.name = slot.name.split('/')[-1]
        setattr(slot, 'app_service_plan', parse_resource_id(slot.server_farm_id)['name'])
        del slot.server_farm_id
    return slots


def swap_slot(cmd, resource_group_name, webapp, slot, target_slot=None, action='swap'):
    client = web_client_factory(cmd.cli_ctx)
    if action == 'swap':
        poller = client.web_apps.swap_slot_slot(resource_group_name, webapp,
                                                slot, (target_slot or 'production'), True)
        return poller
    if action == 'preview':
        if target_slot is None:
            result = client.web_apps.apply_slot_config_to_production(resource_group_name,
                                                                     webapp, slot, True)
        else:
            result = client.web_apps.apply_slot_configuration_slot(resource_group_name, webapp,
                                                                   slot, target_slot, True)
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
    creds = _generic_site_operation(cli_ctx, resource_group_name, name, 'list_publishing_credentials', slot)
    creds = creds.result()
    return (creds.publishing_user_name, creds.publishing_password)


def _get_log(url, user_name, password, log_file=None):
    import certifi
    import urllib3
    try:
        import urllib3.contrib.pyopenssl
        urllib3.contrib.pyopenssl.inject_into_urllib3()
    except ImportError:
        pass

    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
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
                print(chunk.decode(encoding='utf-8', errors='replace')
                      .encode(std_encoding, errors='replace')
                      .decode(std_encoding, errors='replace'), end='')  # each line of log has CRLF.
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
    cert_name = '{}-{}-{}'.format(resource_group_name, kv_name, key_vault_certificate_name)
    lnk = 'https://azure.github.io/AppService/2016/05/24/Deploying-Azure-Web-App-Certificate-through-Key-Vault.html'
    lnk_msg = 'Find more details here: {}'.format(lnk)
    if not _check_service_principal_permissions(cmd, kv_resource_group_name, kv_name, kv_subscription):
        logger.warning('Unable to verify Key Vault permissions.')
        logger.warning('You may need to grant Microsoft.Azure.WebSites service principal the Secret:Get permission')
        logger.warning(lnk_msg)

    kv_cert_def = Certificate(location=location, key_vault_id=kv_id, password='',
                              key_vault_secret_name=key_vault_certificate_name, server_farm_id=server_farm_id)

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
    return client.certificates.create_or_update(name=hostname, resource_group_name=resource_group_name,
                                                certificate_envelope=easy_cert_def)


def _check_service_principal_permissions(cmd, resource_group_name, key_vault_name, key_vault_subscription):
    from azure.cli.command_modules.keyvault._client_factory import keyvault_client_vaults_factory
    from azure.cli.command_modules.role._client_factory import _graph_client_factory
    from azure.graphrbac.models import GraphErrorException
    from azure.cli.core.commands.client_factory import get_subscription_id
    subscription = get_subscription_id(cmd.cli_ctx)
    # Cannot check if key vault is in another subscription
    if subscription != key_vault_subscription:
        return False
    kv_client = keyvault_client_vaults_factory(cmd.cli_ctx, None)
    vault = kv_client.get(resource_group_name=resource_group_name, vault_name=key_vault_name)
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
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, webapp_name, 'create_or_update',
                                   slot, updated_webapp)


def _update_ssl_binding(cmd, resource_group_name, name, certificate_thumbprint, ssl_type, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    webapp = client.web_apps.get(resource_group_name, name)
    if not webapp:
        raise CLIError("'{}' app doesn't exist".format(name))

    cert_resource_group_name = parse_resource_id(webapp.server_farm_id)['resource_group']
    webapp_certs = client.certificates.list_by_resource_group(cert_resource_group_name)
    for webapp_cert in webapp_certs:
        if webapp_cert.thumbprint == certificate_thumbprint:
            if len(webapp_cert.host_names) == 1 and not webapp_cert.host_names[0].startswith('*'):
                return _update_host_name_ssl_state(cmd, resource_group_name, name, webapp,
                                                   webapp_cert.host_names[0], ssl_type,
                                                   certificate_thumbprint, slot)

            query_result = list_hostnames(cmd, resource_group_name, name, slot)
            hostnames_in_webapp = [x.name.split('/')[-1] for x in query_result]
            to_update = _match_host_names_from_cert(webapp_cert.host_names, hostnames_in_webapp)
            for h in to_update:
                _update_host_name_ssl_state(cmd, resource_group_name, name, webapp,
                                            h, ssl_type, certificate_thumbprint, slot)

            return show_webapp(cmd, resource_group_name, name, slot)

    raise CLIError("Certificate for thumbprint '{}' not found.".format(certificate_thumbprint))


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
class _StackRuntimeHelper:

    def __init__(self, cmd, client, linux=False):
        self._cmd = cmd
        self._client = client
        self._linux = linux
        self._stacks = []

    def resolve(self, display_name):
        self._load_stacks_hardcoded()
        return next((s for s in self._stacks if s['displayName'].lower() == display_name.lower()),
                    None)

    @property
    def stacks(self):
        self._load_stacks_hardcoded()
        return self._stacks

    @staticmethod
    def update_site_config(stack, site_config, cmd=None):
        for k, v in stack['configs'].items():
            setattr(site_config, k, v)
        return site_config

    @staticmethod
    def update_site_appsettings(cmd, stack, site_config):
        NameValuePair = cmd.get_models('NameValuePair')
        if site_config.app_settings is None:
            site_config.app_settings = []
        site_config.app_settings += [NameValuePair(name=k, value=v) for k, v in stack['configs'].items()]
        return site_config

    def _load_stacks_hardcoded(self):
        if self._stacks:
            return
        result = []
        if self._linux:
            result = get_file_json(RUNTIME_STACKS)['linux']
        else:  # Windows stacks
            result = get_file_json(RUNTIME_STACKS)['windows']
            for r in result:
                r['setter'] = (_StackRuntimeHelper.update_site_appsettings if 'node' in
                               r['displayName'] else _StackRuntimeHelper.update_site_config)
        self._stacks = result

    # Currently using hardcoded values instead of this function. This function calls the stacks API;
    # Stacks API is updated with Antares deployments,
    # which are infrequent and don't line up with stacks EOL schedule.
    def _load_stacks(self):
        if self._stacks:
            return
        os_type = ('Linux' if self._linux else 'Windows')
        raw_stacks = self._client.provider.get_available_stacks(os_type_selected=os_type, raw=True)
        bytes_value = raw_stacks._get_next().content  # pylint: disable=protected-access
        json_value = bytes_value.decode('utf8')
        json_stacks = json.loads(json_value)
        stacks = json_stacks['value']
        result = []
        if self._linux:
            for properties in [(s['properties']) for s in stacks]:
                for major in properties['majorVersions']:
                    default_minor = next((m for m in (major['minorVersions'] or []) if m['isDefault']),
                                         None)
                    result.append({
                        'displayName': (default_minor['runtimeVersion']
                                        if default_minor else major['runtimeVersion'])
                    })
        else:  # Windows stacks
            config_mappings = {
                'node': 'WEBSITE_NODE_DEFAULT_VERSION',
                'python': 'python_version',
                'php': 'php_version',
                'aspnet': 'net_framework_version'
            }

            # get all stack version except 'java'
            for stack in stacks:
                if stack['name'] not in config_mappings:
                    continue
                name, properties = stack['name'], stack['properties']
                for major in properties['majorVersions']:
                    default_minor = next((m for m in (major['minorVersions'] or []) if m['isDefault']),
                                         None)
                    result.append({
                        'displayName': name + '|' + major['displayVersion'],
                        'configs': {
                            config_mappings[name]: (default_minor['runtimeVersion']
                                                    if default_minor else major['runtimeVersion'])
                        }
                    })

            # deal with java, which pairs with java container version
            java_stack = next((s for s in stacks if s['name'] == 'java'))
            java_container_stack = next((s for s in stacks if s['name'] == 'javaContainers'))
            for java_version in java_stack['properties']['majorVersions']:
                for fx in java_container_stack['properties']['frameworks']:
                    for fx_version in fx['majorVersions']:
                        result.append({
                            'displayName': 'java|{}|{}|{}'.format(java_version['displayVersion'],
                                                                  fx['display'],
                                                                  fx_version['displayVersion']),
                            'configs': {
                                'java_version': java_version['runtimeVersion'],
                                'java_container': fx['name'],
                                'java_container_version': fx_version['runtimeVersion']
                            }
                        })

            for r in result:
                r['setter'] = (_StackRuntimeHelper.update_site_appsettings if 'node' in
                               r['displayName'] else _StackRuntimeHelper.update_site_config)
        self._stacks = result


def get_app_insights_key(cli_ctx, resource_group, name):
    appinsights_client = get_mgmt_service_client(cli_ctx, ApplicationInsightsManagementClient)
    appinsights = appinsights_client.components.get(resource_group, name)
    if appinsights is None or appinsights.instrumentation_key is None:
        raise CLIError("App Insights {} under resource group {} was not found.".format(name, resource_group))
    return appinsights.instrumentation_key


def create_functionapp_app_service_plan(cmd, resource_group_name, name, is_linux, sku,
                                        number_of_workers=None, max_burst=None, location=None, tags=None):
    SkuDescription, AppServicePlan = cmd.get_models('SkuDescription', 'AppServicePlan')
    sku = _normalize_sku(sku)
    tier = get_sku_name(sku)
    if max_burst is not None:
        if tier.lower() != "elasticpremium":
            raise CLIError("Usage error: --max-burst is only supported for Elastic Premium (EP) plans")
        max_burst = validate_range_of_int_flag('--max-burst', max_burst, min_val=0, max_val=20)
    if number_of_workers is not None:
        number_of_workers = validate_range_of_int_flag('--number-of-workers / --min-elastic-worker-count',
                                                       number_of_workers, min_val=0, max_val=20)
    client = web_client_factory(cmd.cli_ctx)
    if location is None:
        location = _get_location_from_resource_group(cmd.cli_ctx, resource_group_name)
    sku_def = SkuDescription(tier=tier, name=sku, capacity=number_of_workers)
    plan_def = AppServicePlan(location=location, tags=tags, sku=sku_def,
                              reserved=(is_linux or None), maximum_elastic_worker_count=max_burst,
                              hyper_v=None, name=name)
    return client.app_service_plans.create_or_update(resource_group_name, name, plan_def)


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


def validate_and_convert_to_int(flag, val):
    try:
        return int(val)
    except ValueError:
        raise CLIError("Usage error: {} is expected to have an int value.".format(flag))


def validate_range_of_int_flag(flag_name, value, min_val, max_val):
    value = validate_and_convert_to_int(flag_name, value)
    if min_val > value or value > max_val:
        raise CLIError("Usage error: {} is expected to be between {} and {} (inclusive)".format(flag_name, min_val,
                                                                                                max_val))
    return value


def create_function(cmd, resource_group_name, name, storage_account, plan=None,
                    os_type=None, functions_version=None, runtime=None, runtime_version=None,
                    consumption_plan_location=None, app_insights=None, app_insights_key=None,
                    disable_app_insights=None, deployment_source_url=None,
                    deployment_source_branch='master', deployment_local_git=None,
                    docker_registry_server_password=None, docker_registry_server_user=None,
                    deployment_container_image_name=None, tags=None, assign_identities=None,
                    role='Contributor', scope=None):
    # pylint: disable=too-many-statements, too-many-branches
    if functions_version is None:
        logger.warning("No functions version specified so defaulting to 2. In the future, specifying a version will "
                       "be required. To create a 2.x function you would pass in the flag `--functions-version 2`")
        functions_version = '2'
    if deployment_source_url and deployment_local_git:
        raise CLIError('usage error: --deployment-source-url <url> | --deployment-local-git')
    if bool(plan) == bool(consumption_plan_location):
        raise CLIError("usage error: --plan NAME_OR_ID | --consumption-plan-location LOCATION")
    SiteConfig, Site, NameValuePair = cmd.get_models('SiteConfig', 'Site', 'NameValuePair')
    docker_registry_server_url = parse_docker_image_name(deployment_container_image_name)

    site_config = SiteConfig(app_settings=[])
    functionapp_def = Site(location=None, site_config=site_config, tags=tags)
    KEYS = FUNCTIONS_STACKS_API_KEYS()
    client = web_client_factory(cmd.cli_ctx)
    plan_info = None
    if runtime is not None:
        runtime = runtime.lower()

    if consumption_plan_location:
        locations = list_consumption_locations(cmd)
        location = next((loc for loc in locations if loc['name'].lower() == consumption_plan_location.lower()), None)
        if location is None:
            raise CLIError("Location is invalid. Use: az functionapp list-consumption-locations")
        functionapp_def.location = consumption_plan_location
        functionapp_def.kind = 'functionapp'
        # if os_type is None, the os type is windows
        is_linux = os_type and os_type.lower() == 'linux'

    else:  # apps with SKU based plan
        if is_valid_resource_id(plan):
            parse_result = parse_resource_id(plan)
            plan_info = client.app_service_plans.get(parse_result['resource_group'], parse_result['name'])
        else:
            plan_info = client.app_service_plans.get(resource_group_name, plan)
        if not plan_info:
            raise CLIError("The plan '{}' doesn't exist".format(plan))
        location = plan_info.location
        is_linux = plan_info.reserved
        functionapp_def.server_farm_id = plan
        functionapp_def.location = location

    if functions_version == '2' and functionapp_def.location in FUNCTIONS_NO_V2_REGIONS:
        raise CLIError("2.x functions are not supported in this region. To create a 3.x function, "
                       "pass in the flag '--functions-version 3'")

    if is_linux and not runtime and (consumption_plan_location or not deployment_container_image_name):
        raise CLIError(
            "usage error: --runtime RUNTIME required for linux functions apps without custom image.")

    runtime_stacks_json = _load_runtime_stacks_json_functionapp(is_linux)

    if runtime is None and runtime_version is not None:
        raise CLIError('Must specify --runtime to use --runtime-version')

    # get the matching runtime stack object
    runtime_json = _get_matching_runtime_json_functionapp(runtime_stacks_json, runtime if runtime else 'dotnet')
    if not runtime_json:
        # no matching runtime for os
        os_string = "linux" if is_linux else "windows"
        supported_runtimes = list(map(lambda x: x[KEYS.NAME], runtime_stacks_json))
        raise CLIError("usage error: Currently supported runtimes (--runtime) in {} function apps are: {}."
                       .format(os_string, ', '.join(supported_runtimes)))

    runtime_version_json = _get_matching_runtime_version_json_functionapp(runtime_json,
                                                                          functions_version,
                                                                          runtime_version,
                                                                          is_linux)
    if not runtime_version_json:
        supported_runtime_versions = list(map(lambda x: x[KEYS.DISPLAY_VERSION],
                                              _get_supported_runtime_versions_functionapp(runtime_json,
                                                                                          functions_version)))
        if runtime_version:
            if runtime == 'dotnet':
                raise CLIError('--runtime-version is not supported for --runtime dotnet. Dotnet version is determined '
                               'by --functions-version. Dotnet version {} is not supported by Functions version {}.'
                               .format(runtime_version, functions_version))
            raise CLIError('--runtime-version {} is not supported for the selected --runtime {} and '
                           '--functions-version {}. Supported versions are: {}.'
                           .format(runtime_version,
                                   runtime,
                                   functions_version,
                                   ', '.join(supported_runtime_versions)))

        # if runtime_version was not specified, then that runtime is not supported for that functions version
        raise CLIError('no supported --runtime-version found for the selected --runtime {} and '
                       '--functions-version {}'
                       .format(runtime, functions_version))

    if runtime == 'dotnet':
        logger.warning('--runtime-version is not supported for --runtime dotnet. Dotnet version is determined by '
                       '--functions-version. Dotnet version will be %s for this function app.',
                       runtime_version_json[KEYS.DISPLAY_VERSION])

    site_config_json = runtime_version_json[KEYS.SITE_CONFIG_DICT]
    app_settings_json = runtime_version_json[KEYS.APP_SETTINGS_DICT]

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
            else:
                site_config.app_settings.append(NameValuePair(name='WEBSITES_ENABLE_APP_SERVICE_STORAGE',
                                                              value='true'))
        if deployment_container_image_name is None:
            site_config.linux_fx_version = site_config_json[KEYS.LINUX_FX_VERSION]
    else:
        functionapp_def.kind = 'functionapp'

    # set site configs
    for prop, value in site_config_json.items():
        snake_case_prop = _convert_camel_to_snake_case(prop)
        setattr(site_config, snake_case_prop, value)

    # adding appsetting to site to make it a function
    for app_setting, value in app_settings_json.items():
        site_config.app_settings.append(NameValuePair(name=app_setting, value=value))

    site_config.app_settings.append(NameValuePair(name='FUNCTIONS_EXTENSION_VERSION',
                                                  value=_get_extension_version_functionapp(functions_version)))
    site_config.app_settings.append(NameValuePair(name='AzureWebJobsStorage', value=con_string))

    if disable_app_insights or not runtime_version_json[KEYS.APPLICATION_INSIGHTS]:
        site_config.app_settings.append(NameValuePair(name='AzureWebJobsDashboard', value=con_string))

    # If plan is not consumption or elastic premium, we need to set always on
    if consumption_plan_location is None and not is_plan_elastic_premium(cmd, plan_info):
        site_config.always_on = True

    # If plan is elastic premium or windows consumption, we need these app settings
    is_windows_consumption = consumption_plan_location is not None and not is_linux
    if is_plan_elastic_premium(cmd, plan_info) or is_windows_consumption:
        site_config.app_settings.append(NameValuePair(name='WEBSITE_CONTENTAZUREFILECONNECTIONSTRING',
                                                      value=con_string))
        site_config.app_settings.append(NameValuePair(name='WEBSITE_CONTENTSHARE', value=name.lower()))

    create_app_insights = False

    if app_insights_key is not None:
        site_config.app_settings.append(NameValuePair(name='APPINSIGHTS_INSTRUMENTATIONKEY',
                                                      value=app_insights_key))
    elif app_insights is not None:
        instrumentation_key = get_app_insights_key(cmd.cli_ctx, resource_group_name, app_insights)
        site_config.app_settings.append(NameValuePair(name='APPINSIGHTS_INSTRUMENTATIONKEY',
                                                      value=instrumentation_key))
    elif not disable_app_insights and runtime_version_json[KEYS.APPLICATION_INSIGHTS]:
        create_app_insights = True

    poller = client.web_apps.create_or_update(resource_group_name, name, functionapp_def)
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


def _load_runtime_stacks_json_functionapp(is_linux):
    KEYS = FUNCTIONS_STACKS_API_KEYS()
    if is_linux:
        return get_file_json(FUNCTIONS_STACKS_API_JSON_PATHS['linux'])[KEYS.VALUE]
    return get_file_json(FUNCTIONS_STACKS_API_JSON_PATHS['windows'])[KEYS.VALUE]


def _get_matching_runtime_json_functionapp(stacks_json, runtime):
    KEYS = FUNCTIONS_STACKS_API_KEYS()
    matching_runtime_json = list(filter(lambda x: x[KEYS.NAME] == runtime, stacks_json))
    if matching_runtime_json:
        return matching_runtime_json[0]
    return None


def _get_supported_runtime_versions_functionapp(runtime_json, functions_version):
    KEYS = FUNCTIONS_STACKS_API_KEYS()
    extension_version = _get_extension_version_functionapp(functions_version)
    supported_versions_list = []

    for runtime_version_json in runtime_json[KEYS.PROPERTIES][KEYS.MAJOR_VERSIONS]:
        if extension_version in runtime_version_json[KEYS.SUPPORTED_EXTENSION_VERSIONS]:
            supported_versions_list.append(runtime_version_json)
    return supported_versions_list


def _get_matching_runtime_version_json_functionapp(runtime_json, functions_version, runtime_version, is_linux):
    KEYS = FUNCTIONS_STACKS_API_KEYS()
    extension_version = _get_extension_version_functionapp(functions_version)
    if runtime_version:
        for runtime_version_json in runtime_json[KEYS.PROPERTIES][KEYS.MAJOR_VERSIONS]:
            if (runtime_version_json[KEYS.DISPLAY_VERSION] == runtime_version and
                    extension_version in runtime_version_json[KEYS.SUPPORTED_EXTENSION_VERSIONS]):
                return runtime_version_json
        return None

    # find the matching default runtime version
    supported_versions_list = _get_supported_runtime_versions_functionapp(runtime_json, functions_version)
    default_version_json = {}
    default_version = 0.0
    for current_runtime_version_json in supported_versions_list:
        if current_runtime_version_json[KEYS.IS_DEFAULT]:
            current_version = _get_runtime_version_functionapp(current_runtime_version_json[KEYS.RUNTIME_VERSION],
                                                               is_linux)
            if not default_version_json or default_version < current_version:
                default_version_json = current_runtime_version_json
                default_version = current_version
    return default_version_json


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

    return float(version_string)


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
    allowed_storage_types = ['Standard_GRS', 'Standard_RAGRS', 'Standard_LRS', 'Standard_ZRS', 'Premium_LRS']

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
    full_sku = get_sku_name(sku)
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
            raise CLIError("""Zip deployment failed. {}. Please run the command az webapp log deployment show
                           -n {} -g {}""".format(res_dict, name, rg_name))
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
    linux_webapp = show_webapp(cmd, resource_group_name, name, slot)
    is_linux = linux_webapp.reserved
    if is_linux:
        return logger.warning("hybrid connections not supported on a linux app.")

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
    linux_webapp = show_webapp(cmd, resource_group_name, name, slot)
    is_linux = linux_webapp.reserved
    if is_linux:
        return logger.warning("hybrid connections not supported on a linux app.")

    web_client = web_client_factory(cmd.cli_ctx)
    hy_co_client = hycos_mgmt_client_factory(cmd.cli_ctx, cmd.cli_ctx)
    namespace_client = namespaces_mgmt_client_factory(cmd.cli_ctx, cmd.cli_ctx)

    hy_co_id = ''
    for n in namespace_client.list():
        if n.name == namespace:
            hy_co_id = n.id

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
                                                                                hybrid_connection, hc, slot)

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


def add_vnet_integration(cmd, name, resource_group_name, vnet, subnet, slot=None):
    SwiftVirtualNetwork = cmd.get_models('SwiftVirtualNetwork')
    Delegation = cmd.get_models('Delegation', resource_type=ResourceType.MGMT_NETWORK)
    client = web_client_factory(cmd.cli_ctx)
    vnet_client = network_client_factory(cmd.cli_ctx)

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
    if slot is None:
        swift_connection_info = client.web_apps.get_swift_virtual_network_connection(resource_group_name, name)
    else:
        swift_connection_info = client.web_apps.get_swift_virtual_network_connection_slot(resource_group_name,
                                                                                          name, slot)

    # check to see if the connection would be supported
    if swift_connection_info.swift_supported is not True:
        return logger.warning("""Your app must be in an Azure App Service deployment that is
              capable of scaling up to Premium v2\nLearn more:
              https://go.microsoft.com/fwlink/?linkid=2060115&clcid=0x409""")

    subnetObj = vnet_client.subnets.get(vnet_resource_group, vnet, subnet)
    delegations = subnetObj.delegations
    delegated = False
    for d in delegations:
        if d.service_name.lower() == "microsoft.web/serverfarms".lower():
            delegated = True

    if not delegated:
        subnetObj.delegations = [Delegation(name="delegation", service_name="Microsoft.Web/serverFarms")]
        vnet_client.subnets.create_or_update(vnet_resource_group, vnet, subnet,
                                             subnet_parameters=subnetObj)

    id_subnet = vnet_client.subnets.get(vnet_resource_group, vnet, subnet)
    subnet_resource_id = id_subnet.id
    swiftVnet = SwiftVirtualNetwork(subnet_resource_id=subnet_resource_id,
                                    swift_supported=True)

    if slot is None:
        return_vnet = client.web_apps.create_or_update_swift_virtual_network_connection(resource_group_name, name,
                                                                                        swiftVnet)
    else:
        return_vnet = client.web_apps.create_or_update_swift_virtual_network_connection_slot(resource_group_name, name,
                                                                                             swiftVnet, slot)

    # reformats the vnet entry, removing unecessary information
    id_strings = return_vnet.id.split('/')
    resourceGroup = id_strings[4]
    mod_vnet = {
        "id": return_vnet.id,
        "location": return_vnet.additional_properties["location"],
        "name": return_vnet.name,
        "resourceGroup": resourceGroup,
        "subnetResourceId": return_vnet.subnet_resource_id
    }

    return mod_vnet


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


def webapp_up(cmd, name, resource_group_name=None, plan=None, location=None, sku=None, dryrun=False, logs=False,  # pylint: disable=too-many-statements,
              launch_browser=False, html=False):
    import os
    AppServicePlan = cmd.get_models('AppServicePlan')
    src_dir = os.getcwd()
    _src_path_escaped = "{}".format(src_dir.replace(os.sep, os.sep + os.sep))
    client = web_client_factory(cmd.cli_ctx)
    user = get_profile_username()
    _create_new_rg = False
    _site_availability = get_site_availability(cmd, name)
    _create_new_app = _site_availability.name_available
    os_name = detect_os_form_src(src_dir, html)
    lang_details = get_lang_from_content(src_dir, html)
    language = lang_details.get('language')

    # detect the version
    data = get_runtime_version_details(lang_details.get('file_loc'), language)
    version_used_create = data.get('to_create')
    detected_version = data.get('detected')
    runtime_version = "{}|{}".format(language, version_used_create) if \
        version_used_create != "-" else version_used_create
    site_config = None
    if not _create_new_app:  # App exists, or App name unavailable
        if _site_availability.reason == 'Invalid':
            raise CLIError(_site_availability.message)
        # Get the ASP & RG info, if the ASP & RG parameters are provided we use those else we need to find those
        logger.warning("Webapp '%s' already exists. The command will deploy contents to the existing app.", name)
        app_details = get_app_details(cmd, name)
        if app_details is None:
            raise CLIError("Unable to retrieve details of the existing app '{}'. Please check that the app "
                           "is a part of the current subscription".format(name))
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
        plan_info = client.app_service_plans.get(rg_name, plan)
        sku = plan_info.sku.name if isinstance(plan_info, AppServicePlan) else 'Free'
        current_os = 'Linux' if plan_info.reserved else 'Windows'
        # Raise error if current OS of the app is different from the current one
        if current_os.lower() != os_name.lower():
            raise CLIError("The webapp '{}' is a {} app. The code detected at '{}' will default to "
                           "'{}'. "
                           "Please create a new app to continue this operation.".format(name, current_os, src_dir, os))
        _is_linux = plan_info.reserved
        # for an existing app check if the runtime version needs to be updated
        # Get site config to check the runtime version
        site_config = client.web_apps.get_configuration(rg_name, name)
    else:  # need to create new app, check if we need to use default RG or use user entered values
        logger.warning("The webapp '%s' doesn't exist", name)
        sku = get_sku_to_use(src_dir, html, sku)
        loc = set_location(cmd, sku, location)
        rg_name = get_rg_to_use(cmd, user, loc, os_name, resource_group_name)
        _is_linux = os_name.lower() == 'linux'
        _create_new_rg = should_create_new_rg(cmd, rg_name, _is_linux)
        plan = get_plan_to_use(cmd=cmd,
                               user=user,
                               os_name=os_name,
                               loc=loc,
                               sku=sku,
                               create_rg=_create_new_rg,
                               resource_group_name=rg_name,
                               plan=plan)
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
                """ % (name, plan, rg_name, get_sku_name(sku), os_name, loc, _src_path_escaped, detected_version,
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
    create_app_service_plan(cmd, rg_name, plan, _is_linux, hyper_v=False, per_site_scaling=False, sku=sku,
                            number_of_workers=1 if _is_linux else None, location=loc)

    if _create_new_app:
        logger.warning("Creating webapp '%s' ...", name)
        create_webapp(cmd, rg_name, name, plan, runtime_version if _is_linux else None,
                      using_webapp_up=True, language=language)
        _configure_default_logging(cmd, rg_name, name)
    else:  # for existing app if we might need to update the stack runtime settings
        if os_name.lower() == 'linux' and site_config.linux_fx_version != runtime_version:
            logger.warning('Updating runtime version from %s to %s',
                           site_config.linux_fx_version, runtime_version)
            update_site_configs(cmd, rg_name, name, linux_fx_version=runtime_version)
        elif os_name.lower() == 'windows' and site_config.windows_fx_version != runtime_version:
            logger.warning('Updating runtime version from %s to %s',
                           site_config.windows_fx_version, runtime_version)
            update_site_configs(cmd, rg_name, name, windows_fx_version=runtime_version)
        create_json['runtime_version'] = runtime_version
    # Zip contents & Deploy
    logger.warning("Creating zip with contents of dir %s ...", src_dir)
    # zip contents & deploy
    zip_file_path = zip_contents_from_dir(src_dir, language)
    enable_zip_deploy(cmd, rg_name, name, zip_file_path)
    # Remove the file after deployment, handling exception if user removed the file manually
    try:
        os.remove(zip_file_path)
    except OSError:
        pass

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
    with ConfiguredDefaultSetter(cmd.cli_ctx.config, True):
        cmd.cli_ctx.config.set_value('defaults', 'group', rg_name)
        cmd.cli_ctx.config.set_value('defaults', 'sku', sku)
        cmd.cli_ctx.config.set_value('defaults', 'appserviceplan', plan)
        cmd.cli_ctx.config.set_value('defaults', 'location', loc)
        cmd.cli_ctx.config.set_value('defaults', 'web', name)
    return create_json


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
        while t.isAlive():
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
        while s.isAlive() and t.isAlive():
            time.sleep(5)


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
        c.run('cat /etc/motd', pty=True)
        c.run('source /etc/profile; exec $SHELL -l', pty=True)
    except Exception as ex:  # pylint: disable=broad-except
        logger.info(ex)
    finally:
        c.close()


def ssh_webapp(cmd, resource_group_name, name, port=None, slot=None, timeout=None, instance=None):  # pylint: disable=too-many-statements
    import platform
    if platform.system() == "Windows":
        raise CLIError('webapp ssh is only supported on linux and mac')

    config = get_site_configs(cmd, resource_group_name, name, slot)
    if config.remote_debugging_enabled:
        raise CLIError('remote debugging is enabled, please disable')
    create_tunnel_and_session(cmd, resource_group_name, name, port=port, slot=slot, timeout=timeout, instance=instance)


def create_devops_pipeline(
        cmd,
        functionapp_name=None,
        organization_name=None,
        project_name=None,
        repository_name=None,
        overwrite_yaml=None,
        allow_force_push=None,
        github_pat=None,
        github_repository=None
):
    from .azure_devops_build_interactive import AzureDevopsBuildInteractive
    azure_devops_build_interactive = AzureDevopsBuildInteractive(cmd, logger, functionapp_name,
                                                                 organization_name, project_name, repository_name,
                                                                 overwrite_yaml, allow_force_push,
                                                                 github_pat, github_repository)
    return azure_devops_build_interactive.interactive_azure_devops_build()


def _configure_default_logging(cmd, rg_name, name):
    logger.warning("Configuring default logging for the app, if not already enabled")
    return config_diagnostics(cmd, rg_name, name,
                              application_logging=True, web_server_logging='filesystem',
                              docker_container_logging='true')


def _validate_app_service_environment_id(cli_ctx, ase, resource_group_name):
    ase_is_id = is_valid_resource_id(ase)
    if ase_is_id:
        return ase

    from msrestazure.tools import resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id
    return resource_id(
        subscription=get_subscription_id(cli_ctx),
        resource_group=resource_group_name,
        namespace='Microsoft.Web',
        type='hostingEnvironments',
        name=ase)


def _validate_asp_sku(app_service_environment, sku):
    # Isolated SKU is supported only for ASE
    if sku in ['I1', 'I2', 'I3']:
        if not app_service_environment:
            raise CLIError("The pricing tier 'Isolated' is not allowed for this app service plan. Use this link to "
                           "learn more: https://docs.microsoft.com/en-us/azure/app-service/overview-hosting-plans")
    else:
        if app_service_environment:
            raise CLIError("Only pricing tier 'Isolated' is allowed in this app service plan. Use this link to "
                           "learn more: https://docs.microsoft.com/en-us/azure/app-service/overview-hosting-plans")


def _format_key_vault_id(cli_ctx, key_vault, resource_group_name):
    key_vault_is_id = is_valid_resource_id(key_vault)
    if key_vault_is_id:
        return key_vault

    from msrestazure.tools import resource_id
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
        if binding_name.lower() == hostname and hostname_binding.host_name_type == 'Verified':
            verified_hostname_found = True

    return verified_hostname_found


def update_host_key(cmd, resource_group_name, name, key_type, key_name, key_value=None, slot=None):
    # pylint: disable=protected-access
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
                                                                 slot,
                                                                 name1=key_name,
                                                                 value=key_value)
    return client.web_apps.create_or_update_host_secret(resource_group_name,
                                                        name,
                                                        key_type,
                                                        key_name,
                                                        name1=key_name,
                                                        value=key_value)


def list_host_keys(cmd, resource_group_name, name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        return client.web_apps.list_host_keys_slot(resource_group_name, name, slot)
    return client.web_apps.list_host_keys(resource_group_name, name)


def delete_host_key(cmd, resource_group_name, name, key_type, key_name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        result = client.web_apps.delete_host_secret_slot(resource_group_name, name, key_type, key_name, slot, raw=True)
    result = client.web_apps.delete_host_secret(resource_group_name, name, key_type, key_name, raw=True)

    if result.response.status_code == HTTPStatus.NO_CONTENT:
        return "Successfully deleted key '{}' of type '{}' from function app '{}'".format(key_name, key_type, name)
    if result.response.status_code == HTTPStatus.NOT_FOUND:
        return "Key '{}' of type '{}' does not exist in function app '{}'".format(key_name, key_type, name)
    return result


def show_function(cmd, resource_group_name, name, function_name):
    client = web_client_factory(cmd.cli_ctx)
    result = client.web_apps.get_function(resource_group_name, name, function_name)
    if result is None:
        return "Function '{}' does not exist in app '{}'".format(function_name, name)
    return result


def delete_function(cmd, resource_group_name, name, function_name):
    client = web_client_factory(cmd.cli_ctx)
    result = client.web_apps.delete_function(resource_group_name, name, function_name, raw=True)

    if result.response.status_code == HTTPStatus.NO_CONTENT:
        return "Successfully deleted function '{}' from app '{}'".format(function_name, name)
    if result.response.status_code == HTTPStatus.NOT_FOUND:
        return "Function '{}' does not exist in app '{}'".format(function_name, name)
    return result


def update_function_key(cmd, resource_group_name, name, function_name, key_name, key_value=None, slot=None):
    # pylint: disable=protected-access
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
                                                                     name1=key_name,
                                                                     value=key_value)
    return client.web_apps.create_or_update_function_secret(resource_group_name,
                                                            name,
                                                            function_name,
                                                            key_name,
                                                            name1=key_name,
                                                            value=key_value)


def list_function_keys(cmd, resource_group_name, name, function_name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        return client.web_apps.list_function_keys_slot(resource_group_name, name, function_name, slot)
    return client.web_apps.list_function_keys(resource_group_name, name, function_name)


def delete_function_key(cmd, resource_group_name, name, key_name, function_name=None, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        result = client.web_apps.delete_function_secret_slot(resource_group_name,
                                                             name,
                                                             function_name,
                                                             key_name,
                                                             slot,
                                                             raw=True)
    result = client.web_apps.delete_function_secret(resource_group_name, name, function_name, key_name, raw=True)

    if result.response.status_code == HTTPStatus.NO_CONTENT:
        return "Successfully deleted key '{}' from function '{}'".format(key_name, function_name)
    if result.response.status_code == HTTPStatus.NOT_FOUND:
        return "Key '{}' does not exist in function '{}'".format(key_name, function_name)
    return result
