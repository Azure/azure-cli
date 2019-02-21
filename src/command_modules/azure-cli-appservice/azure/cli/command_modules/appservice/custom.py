# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import threading
import time


try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse  # pylint: disable=import-error
from six.moves.urllib.request import urlopen  # pylint: disable=import-error, ungrouped-imports
from binascii import hexlify
from os import urandom
import json
import ssl
import sys
import OpenSSL.crypto

from fabric import Connection


from knack.prompting import prompt_pass, NoTTYException
from knack.util import CLIError
from knack.log import get_logger

from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import is_valid_resource_id, parse_resource_id

from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.web.models import (Site, SiteConfig, User, AppServicePlan, SiteConfigResource,
                                   SkuDescription, SslState, HostNameBinding, NameValuePair,
                                   BackupRequest, DatabaseBackupSetting, BackupSchedule,
                                   RestoreRequest, FrequencyUnit, Certificate, HostNameSslState,
                                   RampUpRule, UnauthenticatedClientAction, ManagedServiceIdentity,
                                   DeletedAppRestoreRequest, DefaultErrorResponseException,
                                   SnapshotRestoreRequest, SnapshotRecoverySource)
from azure.mgmt.applicationinsights import ApplicationInsightsManagementClient

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.util import in_cloud_console, shell_safe_json_parse, open_page_in_browser, get_json_object

from .tunnel import TunnelServer

from .vsts_cd_provider import VstsContinuousDeliveryProvider
from ._params import AUTH_TYPES, MULTI_CONTAINER_TYPES, LINUX_RUNTIMES, WINDOWS_RUNTIMES
from ._client_factory import web_client_factory, ex_handler_factory
from ._appservice_utils import _generic_site_operation
from ._create_util import (zip_contents_from_dir, get_runtime_version_details, create_resource_group,
                           should_create_new_rg, set_location, should_create_new_asp, should_create_new_app,
                           get_lang_from_content)
from ._constants import (NODE_RUNTIME_NAME, OS_DEFAULT, STATIC_RUNTIME_NAME, PYTHON_RUNTIME_NAME)

logger = get_logger(__name__)

# pylint:disable=no-member,too-many-lines,too-many-locals

# region "Common routines shared with quick-start extensions."
# Please maintain compatibility in both interfaces and functionalities"


def create_webapp(cmd, resource_group_name, name, plan, runtime=None, startup_file=None,  # pylint: disable=too-many-statements
                  deployment_container_image_name=None, deployment_source_url=None, deployment_source_branch='master',
                  deployment_local_git=None, multicontainer_config_type=None, multicontainer_config_file=None,
                  tags=None):
    if deployment_source_url and deployment_local_git:
        raise CLIError('usage error: --deployment-source-url <url> | --deployment-local-git')
    client = web_client_factory(cmd.cli_ctx)
    if is_valid_resource_id(plan):
        parse_result = parse_resource_id(plan)
        plan_info = client.app_service_plans.get(parse_result['resource_group'], parse_result['name'])
    else:
        plan_info = client.app_service_plans.get(resource_group_name, plan)
    if not plan_info:
        raise CLIError("The plan '{}' doesn't exist".format(plan))
    is_linux = plan_info.reserved
    node_default_version = '8.11.1'
    location = plan_info.location
    site_config = SiteConfig(app_settings=[])
    webapp_def = Site(location=location, site_config=site_config, server_farm_id=plan_info.id, tags=tags)
    helper = _StackRuntimeHelper(client, linux=is_linux)

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
                               "Please invoke 'list-runtimes' to cross check".format(runtime))
        elif deployment_container_image_name:
            site_config.linux_fx_version = _format_fx_version(deployment_container_image_name)
            site_config.app_settings.append(NameValuePair(name="WEBSITES_ENABLE_APP_SERVICE_STORAGE",
                                                          value="false"))
        elif multicontainer_config_type and multicontainer_config_file:
            encoded_config_file = _get_linux_multicontainer_encoded_config_from_file(multicontainer_config_file)
            site_config.linux_fx_version = _format_fx_version(encoded_config_file, multicontainer_config_type)

    elif plan_info.is_xenon:  # windows container webapp
        site_config.windows_fx_version = _format_fx_version(deployment_container_image_name)

    elif runtime:  # windows webapp with runtime specified
        if any([startup_file, deployment_container_image_name, multicontainer_config_file, multicontainer_config_type]):
            raise CLIError("usage error: --startup-file or --deployment-container-image-name or "
                           "--multicontainer-config-type and --multicontainer-config-file is "
                           "only appliable on linux webapp")
        match = helper.resolve(runtime)
        if not match:
            raise CLIError("Runtime '{}' is not supported. Please invoke 'list-runtimes' to cross check".format(runtime))  # pylint: disable=line-too-long
        match['setter'](match, site_config)
        # Be consistent with portal: any windows webapp should have this even it doesn't have node in the stack
        if not match['displayName'].startswith('node'):
            site_config.app_settings.append(NameValuePair(name="WEBSITE_NODE_DEFAULT_VERSION",
                                                          value=node_default_version))
    else:  # windows webapp without runtime specified
        site_config.app_settings.append(NameValuePair(name="WEBSITE_NODE_DEFAULT_VERSION",
                                                      value=node_default_version))

    if site_config.app_settings:
        for setting in site_config.app_settings:
            logger.info('Will set appsetting %s', setting)

    poller = client.web_apps.create_or_update(resource_group_name, name, webapp_def)
    webapp = LongRunningOperation(cmd.cli_ctx)(poller)

    # Ensure SCC operations follow right after the 'create', no precedent appsetting update commands
    _set_remote_or_local_git(cmd, webapp, resource_group_name, name, deployment_source_url,
                             deployment_source_branch, deployment_local_git)

    _fill_ftp_publishing_url(cmd, webapp, resource_group_name, name)

    return webapp


def validate_container_app_create_options(runtime=None, deployment_container_image_name=None,
                                          multicontainer_config_type=None, multicontainer_config_file=None):
    if bool(multicontainer_config_type) != bool(multicontainer_config_file):
        return False
    opts = [runtime, deployment_container_image_name, multicontainer_config_type]
    return len([x for x in opts if x]) == 1  # you can only specify one out the combinations


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
    from azure.mgmt.web.models import AzureStorageInfoValue

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
    from azure.mgmt.web.models import AzureStorageInfoValue

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


def enable_zip_deploy(cmd, resource_group_name, name, src, timeout=None, slot=None):
    user_name, password = _get_site_credential(cmd.cli_ctx, resource_group_name, name, slot)
    scm_url = _get_scm_url(cmd, resource_group_name, name, slot)
    zip_url = scm_url + '/api/zipdeploy?isAsync=true'
    deployment_status_url = scm_url + '/api/deployments/latest'

    import urllib3
    authorization = urllib3.util.make_headers(basic_auth='{0}:{1}'.format(user_name, password))
    headers = authorization
    headers['content-type'] = 'application/octet-stream'

    import requests
    import os
    # Read file content
    with open(os.path.realpath(os.path.expanduser(src)), 'rb') as fs:
        zip_content = fs.read()
        requests.post(zip_url, data=zip_content, headers=headers)
    # check the status of async deployment
    response = _check_zip_deployment_status(deployment_status_url, authorization, timeout)
    return response


def get_sku_name(tier):  # pylint: disable=too-many-return-statements
    tier = tier.upper()
    if tier == 'F1' or tier == "FREE":
        return 'FREE'
    elif tier == 'D1' or tier == "SHARED":
        return 'SHARED'
    elif tier in ['B1', 'B2', 'B3', 'BASIC']:
        return 'BASIC'
    elif tier in ['S1', 'S2', 'S3']:
        return 'STANDARD'
    elif tier in ['P1', 'P2', 'P3']:
        return 'PREMIUM'
    elif tier in ['P1V2', 'P2V2', 'P3V2']:
        return 'PREMIUMV2'
    elif tier in ['PC2', 'PC3', 'PC4']:
        return 'PremiumContainer'
    elif tier in ['EP1', 'EP2', 'EP3']:
        return 'ElasticPremium'
    else:
        raise CLIError("Invalid sku(pricing tier), please refer to command help for valid values")


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
    result = list(client.deleted_web_apps.list())
    if resource_group_name:
        result = [r for r in result if r.resource_group == resource_group_name]
    if name:
        result = [r for r in result if r.deleted_site_name.lower() == name.lower()]
    if slot:
        result = [r for r in result if r.slot.lower() == slot.lower()]
    return result


def assign_identity(cmd, resource_group_name, name, role='Contributor', slot=None, scope=None):
    def getter():
        return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)

    def setter(webapp):
        webapp.identity = ManagedServiceIdentity(type='SystemAssigned')
        poller = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'create_or_update', slot, webapp)
        return LongRunningOperation(cmd.cli_ctx)(poller)

    from azure.cli.core.commands.arm import assign_identity as _assign_identity
    webapp = _assign_identity(cmd.cli_ctx, getter, setter, role, scope)
    return webapp.identity


def show_identity(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot).identity


def remove_identity(cmd, resource_group_name, name, slot=None):
    def getter():
        return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get', slot)

    def setter(webapp):
        webapp.identity = ManagedServiceIdentity(type='None')
        poller = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'create_or_update', slot, webapp)
        return LongRunningOperation(cmd.cli_ctx)(poller)

    from azure.cli.core.commands.arm import assign_identity as _assign_identity
    webapp = _assign_identity(cmd.cli_ctx, getter, setter)
    return webapp.identity


def get_auth_settings(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get_auth_settings', slot)


def update_auth_settings(cmd, resource_group_name, name, enabled=None, action=None,  # pylint: disable=unused-argument
                         client_id=None, token_store_enabled=None,  # pylint: disable=unused-argument
                         token_refresh_extension_hours=None,  # pylint: disable=unused-argument
                         allowed_external_redirect_urls=None, client_secret=None,  # pylint: disable=unused-argument
                         allowed_audiences=None, issuer=None, facebook_app_id=None,  # pylint: disable=unused-argument
                         facebook_app_secret=None, facebook_oauth_scopes=None,  # pylint: disable=unused-argument
                         twitter_consumer_key=None, twitter_consumer_secret=None,  # pylint: disable=unused-argument
                         google_client_id=None, google_client_secret=None,  # pylint: disable=unused-argument
                         google_oauth_scopes=None, microsoft_account_client_id=None,  # pylint: disable=unused-argument
                         microsoft_account_client_secret=None,  # pylint: disable=unused-argument
                         microsoft_account_oauth_scopes=None, slot=None):  # pylint: disable=unused-argument
    auth_settings = get_auth_settings(cmd, resource_group_name, name, slot)

    if action == 'AllowAnonymous':
        auth_settings.unauthenticated_client_action = UnauthenticatedClientAction.allow_anonymous
    elif action:
        auth_settings.unauthenticated_client_action = UnauthenticatedClientAction.redirect_to_login_page
        auth_settings.default_provider = AUTH_TYPES[action]

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


def list_runtimes(cmd, linux=False):
    client = web_client_factory(cmd.cli_ctx)
    runtime_helper = _StackRuntimeHelper(client, linux)

    return [s['displayName'] for s in runtime_helper.stacks]


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


def get_connection_strings(cmd, resource_group_name, name, slot=None):
    result = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'list_connection_strings', slot)
    client = web_client_factory(cmd.cli_ctx)
    slot_constr_names = client.web_apps.list_slot_configuration_names(resource_group_name, name) \
                              .connection_string_names or []
    result = [{'name': p,
               'value': result.properties[p],
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
def update_site_configs(cmd, resource_group_name, name, slot=None,
                        linux_fx_version=None, windows_fx_version=None, php_version=None, python_version=None,  # pylint: disable=unused-argument
                        net_framework_version=None,  # pylint: disable=unused-argument
                        java_version=None, java_container=None, java_container_version=None,  # pylint: disable=unused-argument
                        remote_debugging_enabled=None, web_sockets_enabled=None,  # pylint: disable=unused-argument
                        always_on=None, auto_heal_enabled=None,  # pylint: disable=unused-argument
                        use32_bit_worker_process=None,  # pylint: disable=unused-argument
                        min_tls_version=None,  # pylint: disable=unused-argument
                        http20_enabled=None,  # pylint: disable=unused-argument
                        app_command_line=None,  # pylint: disable=unused-argument
                        ftps_state=None,  # pylint: disable=unused-argument
                        generic_configurations=None):
    configs = get_site_configs(cmd, resource_group_name, name, slot)
    if linux_fx_version:
        if linux_fx_version.strip().lower().startswith('docker|'):
            update_app_settings(cmd, resource_group_name, name, ["WEBSITES_ENABLE_APP_SERVICE_STORAGE=false"])
        else:
            delete_app_settings(cmd, resource_group_name, name, ["WEBSITES_ENABLE_APP_SERVICE_STORAGE"])

    import inspect
    frame = inspect.currentframe()
    bool_flags = ['remote_debugging_enabled', 'web_sockets_enabled', 'always_on',
                  'auto_heal_enabled', 'use32_bit_worker_process', 'http20_enabled']
    # note: getargvalues is used already in azure.cli.core.commands.
    # and no simple functional replacement for this deprecating method for 3.5
    args, _, _, values = inspect.getargvalues(frame)  # pylint: disable=deprecated-method
    for arg in args[3:]:
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
    if docker_custom_image_name is not None:
        _add_fx_version(cmd, resource_group_name, name, docker_custom_image_name, slot)
    if websites_enable_app_service_storage:
        settings.append('WEBSITES_ENABLE_APP_SERVICE_STORAGE=' + websites_enable_app_service_storage)

    if docker_registry_server_user or docker_registry_server_password or docker_registry_server_url or websites_enable_app_service_storage:  # pylint: disable=line-too-long
        update_app_settings(cmd, resource_group_name, name, settings, slot)
    settings = get_app_settings(cmd, resource_group_name, name, slot)

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
    client = web_client_factory(cmd.cli_ctx)
    site = client.web_apps.get(resource_group_name, webapp)
    if not site:
        raise CLIError("'{}' app doesn't exist".format(webapp))
    location = site.location
    slot_def = Site(server_farm_id=site.server_farm_id, location=location)
    clone_from_prod = None
    slot_def.site_config = SiteConfig()

    poller = client.web_apps.create_or_update_slot(resource_group_name, webapp, slot_def, slot)
    result = LongRunningOperation(cmd.cli_ctx)(poller)
    if configuration_source:
        clone_from_prod = configuration_source.lower() == webapp.lower()
        site_config = get_site_configs(cmd, resource_group_name, webapp,
                                       None if clone_from_prod else configuration_source)
        _generic_site_operation(cmd.cli_ctx, resource_group_name, webapp,
                                'update_configuration', slot, site_config)

    # slot create doesn't clone over the app-settings and connection-strings, so we do it here
    # also make sure slot settings don't get propagated.
    if configuration_source:
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

    result.name = result.name.split('/')[-1]
    return result


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
    else:
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
        plans = list(client.app_service_plans.list())
    else:
        plans = list(client.app_service_plans.list_by_resource_group(resource_group_name))
    for plan in plans:
        # prune a few useless fields
        del plan.geo_region
        del plan.subscription
    return plans


def create_app_service_plan(cmd, resource_group_name, name, is_linux, hyper_v, sku='B1', number_of_workers=None,
                            location=None, tags=None):
    if is_linux and hyper_v:
        raise CLIError('usage error: --is-linux | --hyper-v')
    client = web_client_factory(cmd.cli_ctx)
    sku = _normalize_sku(sku)
    if location is None:
        location = _get_location_from_resource_group(cmd.cli_ctx, resource_group_name)
    # the api is odd on parameter naming, have to live with it for now
    sku_def = SkuDescription(tier=get_sku_name(sku), name=sku, capacity=number_of_workers)
    plan_def = AppServicePlan(location=location, tags=tags, sku=sku_def,
                              reserved=(is_linux or None), hyper_v=(hyper_v or None), name=name)
    return client.app_service_plans.create_or_update(resource_group_name, name, plan_def)


def update_app_service_plan(instance, sku=None, number_of_workers=None,
                            admin_site_name=None):
    sku_def = instance.sku
    if sku is not None:
        sku = _normalize_sku(sku)
        sku_def.tier = get_sku_name(sku)
        sku_def.name = sku

    if number_of_workers is not None:
        sku_def.capacity = number_of_workers

    instance.sku = sku_def
    instance.sku = sku_def
    if admin_site_name is not None:
        instance.admin_site_name = admin_site_name
    return instance


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
    client = web_client_factory(cmd.cli_ctx)
    if backup_name and backup_name.lower().endswith('.zip'):
        backup_name = backup_name[:-4]
    db_setting = _create_db_setting(db_name, db_type, db_connection_string)
    backup_request = BackupRequest(backup_request_name=backup_name,
                                   storage_account_url=storage_account_url, databases=db_setting)
    if slot:
        return client.web_apps.backup_slot(resource_group_name, webapp_name, backup_request, slot)

    return client.web_apps.backup(resource_group_name, webapp_name, backup_request)


def update_backup_schedule(cmd, resource_group_name, webapp_name, storage_account_url=None,
                           frequency=None, keep_at_least_one_backup=None,
                           retention_period_in_days=None, db_name=None,
                           db_connection_string=None, db_type=None, backup_name=None, slot=None):
    configuration = None
    if backup_name and backup_name.lower().endswith('.zip'):
        backup_name = backup_name[:-4]
    if not backup_name:
        from datetime import datetime
        backup_name = '{0}_{1}'.format(webapp_name, datetime.utcnow().strftime('%Y%m%d%H%M'))

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
        frequency_num, frequency_unit = _parse_frequency(frequency)
    else:
        frequency_num = configuration.backup_schedule.frequency_interval
        frequency_unit = configuration.backup_schedule.frequency_unit

    if configuration and configuration.databases:
        db = configuration.databases[0]
        db_type = db_type or db.database_type
        db_name = db_name or db.name
        db_connection_string = db_connection_string or db.connection_string

    db_setting = _create_db_setting(db_name, db_type, db_connection_string)

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
    client = web_client_factory(cmd.cli_ctx)
    storage_blob_name = backup_name
    if not storage_blob_name.lower().endswith('.zip'):
        storage_blob_name += '.zip'
    db_setting = _create_db_setting(db_name, db_type, db_connection_string)
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
    elif any([source_resource_group, source_name]):
        raise CLIError('usage error: --source-resource-group and --source-name must both be specified if one is used')
    else:
        # Overwrite app with its own snapshot
        request = SnapshotRestoreRequest(overwrite=True, snapshot_time=time, recover_configuration=recover_config)
        if slot:
            return client.web_apps.restore_snapshot_slot(resource_group_name, name, request, slot)
        return client.web_apps.restore_snapshot(resource_group_name, name, request)


# pylint: disable=inconsistent-return-statements
def _create_db_setting(db_name, db_type, db_connection_string):
    if all([db_name, db_type, db_connection_string]):
        return [DatabaseBackupSetting(database_type=db_type, name=db_name, connection_string=db_connection_string)]
    elif any([db_name, db_type, db_connection_string]):
        raise CLIError('usage error: --db-name NAME --db-type TYPE --db-connection-string STRING')


def _parse_frequency(frequency):
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


def _normalize_sku(sku):
    sku = sku.upper()
    if sku == 'FREE':
        return 'F1'
    elif sku == 'SHARED':
        return 'D1'
    return sku


def _get_location_from_resource_group(cli_ctx, resource_group_name):
    from azure.mgmt.resource import ResourceManagementClient
    client = get_mgmt_service_client(cli_ctx, ResourceManagementClient)
    group = client.resource_groups.get(resource_group_name)
    return group.location


def _get_location_from_webapp(client, resource_group_name, webapp):
    webapp = client.web_apps.get(resource_group_name, webapp)
    if not webapp:
        raise CLIError("'{}' app doesn't exist".format(webapp))
    return webapp.location


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


def set_deployment_user(cmd, user_name, password=None):
    '''
    Update deployment credentials.(Note, all webapps in your subscription will be impacted)
    '''
    client = web_client_factory(cmd.cli_ctx)
    user = User(publishing_user_name=user_name)
    if password is None:
        try:
            password = prompt_pass(msg='Password: ', confirm=True)
        except NoTTYException:
            raise CLIError('Please specify both username and password in non-interactive mode.')

    user.publishing_password = password
    return client.update_publishing_user(user)


def list_publish_profiles(cmd, resource_group_name, name, slot=None):
    import xmltodict

    content = _generic_site_operation(cmd.cli_ctx, resource_group_name, name,
                                      'list_publishing_profile_xml_with_secrets', slot)
    full_xml = ''
    for f in content:
        full_xml += f.decode()

    profiles = xmltodict.parse(full_xml, xml_attribs=True)['publishData']['publishProfile']
    converted = []
    for profile in profiles:
        new = {}
        for key in profile:
            # strip the leading '@' xmltodict put in for attributes
            new[key.lstrip('@')] = profile[key]
        converted.append(new)

    return converted


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
        profiles = list_publish_profiles(cmd, resource_group_name, name, slot)
        for profile in profiles:
            if profile['publishMethod'] == 'MSDeploy':
                scmUrl = profile['publishUrl'].replace(":443", "")
                cd_url = 'https://' + profile['userName'] + ':' + profile['userPWD'] + '@' + scmUrl + '/docker/hook'
                cd_settings['CI_CD_URL'] = cd_url
                break
    else:
        cd_settings['CI_CD_URL'] = ''

    return cd_settings


def view_in_browser(cmd, resource_group_name, name, slot=None, logs=False):
    url = _get_url(cmd, resource_group_name, name, slot)
    open_page_in_browser(url)
    if logs:
        get_streaming_log(cmd, resource_group_name, name, provider=None, slot=slot)


def _get_url(cmd, resource_group_name, name, slot=None):
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
    elif action == 'preview':
        if target_slot is None:
            result = client.web_apps.apply_slot_config_to_production(resource_group_name,
                                                                     webapp, slot, True)
        else:
            result = client.web_apps.apply_slot_configuration_slot(resource_group_name, webapp,
                                                                   slot, target_slot, True)
        return result
    else:  # reset
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
    client = web_client_factory(cmd.cli_ctx)
    site = client.web_apps.get(resource_group_name, name)
    if not site:
        raise CLIError("'{}' app doesn't exist".format(name))
    configs = get_site_configs(cmd, resource_group_name, name)
    host_name_suffix = '.' + site.default_host_name.split('.', 1)[1]
    configs.experiments.ramp_up_rules = []
    for r in distribution:
        slot, percentage = r.split('=')
        configs.experiments.ramp_up_rules.append(RampUpRule(action_host_name=slot + host_name_suffix,
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


def upload_ssl_cert(cmd, resource_group_name, name, certificate_password, certificate_file):
    client = web_client_factory(cmd.cli_ctx)
    webapp = _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'get')
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


def _update_host_name_ssl_state(cli_ctx, resource_group_name, webapp_name, location,
                                host_name, ssl_state, thumbprint, slot=None):
    updated_webapp = Site(host_name_ssl_states=[HostNameSslState(name=host_name,
                                                                 ssl_state=ssl_state,
                                                                 thumbprint=thumbprint,
                                                                 to_update=True)],
                          location=location)
    name = '{}({})'.format(webapp_name, slot) if slot else webapp_name
    return _generic_site_operation(cli_ctx, resource_group_name, name, 'create_or_update',
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
                return _update_host_name_ssl_state(cmd.cli_ctx, resource_group_name, name, webapp.location,
                                                   webapp_cert.host_names[0], ssl_type,
                                                   certificate_thumbprint, slot)

            query_result = list_hostnames(cmd, resource_group_name, name, slot)
            hostnames_in_webapp = [x.name.split('/')[-1] for x in query_result]
            to_update = _match_host_names_from_cert(webapp_cert.host_names, hostnames_in_webapp)
            for h in to_update:
                _update_host_name_ssl_state(cmd.cli_ctx, resource_group_name, name, webapp.location,
                                            h, ssl_type, certificate_thumbprint, slot)

            return show_webapp(cmd, resource_group_name, name, slot)

    raise CLIError("Certificate for thumbprint '{}' not found.".format(certificate_thumbprint))


def bind_ssl_cert(cmd, resource_group_name, name, certificate_thumbprint, ssl_type, slot=None):
    return _update_ssl_binding(cmd, resource_group_name, name, certificate_thumbprint,
                               SslState.sni_enabled if ssl_type == 'SNI' else SslState.ip_based_enabled, slot)


def unbind_ssl_cert(cmd, resource_group_name, name, certificate_thumbprint, slot=None):
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
class _StackRuntimeHelper(object):

    def __init__(self, client, linux=False):
        self._client = client
        self._linux = linux
        self._stacks = []

    def resolve(self, display_name):
        self._load_stacks()
        return next((s for s in self._stacks if s['displayName'].lower() == display_name.lower()),
                    None)

    @property
    def stacks(self):
        self._load_stacks()
        return self._stacks

    @staticmethod
    def update_site_config(stack, site_config):
        for k, v in stack['configs'].items():
            setattr(site_config, k, v)
        return site_config

    @staticmethod
    def update_site_appsettings(stack, site_config):
        if site_config.app_settings is None:
            site_config.app_settings = []
        site_config.app_settings += [NameValuePair(name=k, value=v) for k, v in stack['configs'].items()]
        return site_config

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


def create_functionapp_app_service_plan(cmd, resource_group_name, name, sku,
                                        number_of_workers=None, location=None, tags=None):
    # This command merely shadows 'az appservice plan create' except with a few parameters
    return create_app_service_plan(cmd, resource_group_name, name, is_linux=None, hyper_v=None,
                                   sku=sku, number_of_workers=number_of_workers, location=location, tags=tags)


def is_plan_Elastic_Premium(plan_info):
    if isinstance(plan_info, AppServicePlan):
        if isinstance(plan_info.sku, SkuDescription):
            return plan_info.sku.tier == 'ElasticPremium'
    return False


def create_function(cmd, resource_group_name, name, storage_account, plan=None,
                    os_type=None, runtime=None, consumption_plan_location=None,
                    app_insights=None, app_insights_key=None, deployment_source_url=None,
                    deployment_source_branch='master', deployment_local_git=None,
                    deployment_container_image_name=None, tags=None):
    # pylint: disable=too-many-statements, too-many-branches
    if deployment_source_url and deployment_local_git:
        raise CLIError('usage error: --deployment-source-url <url> | --deployment-local-git')
    if bool(plan) == bool(consumption_plan_location):
        raise CLIError("usage error: --plan NAME_OR_ID | --consumption-plan-location LOCATION")

    site_config = SiteConfig(app_settings=[])
    functionapp_def = Site(location=None, site_config=site_config, tags=tags)
    client = web_client_factory(cmd.cli_ctx)
    plan_info = None

    if consumption_plan_location:
        locations = list_consumption_locations(cmd)
        location = next((l for l in locations if l['name'].lower() == consumption_plan_location.lower()), None)
        if location is None:
            raise CLIError("Location is invalid. Use: az functionapp list-consumption-locations")
        functionapp_def.location = consumption_plan_location
        functionapp_def.kind = 'functionapp'
        # if os_type is None, the os type is windows
        is_linux = os_type and os_type.lower() == 'linux'

        # for linux consumption plan app the os_type should be Linux & should have a runtime specified
        # currently in other cases the runtime is ignored
        if is_linux and not runtime:
            raise CLIError("usage error: --runtime RUNTIME required for linux functions apps with consumption plan.")

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

    if runtime:
        if is_linux and runtime not in LINUX_RUNTIMES:
            raise CLIError("usage error: Currently supported runtimes (--runtime) in linux function apps are: {}."
                           .format(', '.join(LINUX_RUNTIMES)))
        elif not is_linux and runtime not in WINDOWS_RUNTIMES:
            raise CLIError("usage error: Currently supported runtimes (--runtime) in windows function apps are: {}."
                           .format(', '.join(WINDOWS_RUNTIMES)))
        site_config.app_settings.append(NameValuePair(name='FUNCTIONS_WORKER_RUNTIME', value=runtime))

    con_string = _validate_and_get_connection_string(cmd.cli_ctx, resource_group_name, storage_account)

    if is_linux:
        functionapp_def.kind = 'functionapp,linux'
        functionapp_def.reserved = True
        if consumption_plan_location:
            site_config.app_settings.append(NameValuePair(name='FUNCTIONS_EXTENSION_VERSION', value='~2'))
        else:
            site_config.app_settings.append(NameValuePair(name='FUNCTIONS_EXTENSION_VERSION', value='beta'))
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
                site_config.linux_fx_version = _format_fx_version('appsvc/azure-functions-runtime')
    else:
        functionapp_def.kind = 'functionapp'
        site_config.app_settings.append(NameValuePair(name='FUNCTIONS_EXTENSION_VERSION', value='~2'))
    # adding appsetting to site to make it a function
    site_config.app_settings.append(NameValuePair(name='AzureWebJobsStorage', value=con_string))
    site_config.app_settings.append(NameValuePair(name='AzureWebJobsDashboard', value=con_string))
    site_config.app_settings.append(NameValuePair(name='WEBSITE_NODE_DEFAULT_VERSION', value='8.11.1'))

    if consumption_plan_location is None and not is_plan_Elastic_Premium(plan_info):
        site_config.always_on = True
    else:
        site_config.app_settings.append(NameValuePair(name='WEBSITE_CONTENTAZUREFILECONNECTIONSTRING',
                                                      value=con_string))
        site_config.app_settings.append(NameValuePair(name='WEBSITE_CONTENTSHARE', value=name.lower()))

    if app_insights_key is not None:
        site_config.app_settings.append(NameValuePair(name='APPINSIGHTS_INSTRUMENTATIONKEY',
                                                      value=app_insights_key))
    elif app_insights is not None:
        instrumentation_key = get_app_insights_key(cmd.cli_ctx, resource_group_name, app_insights)
        site_config.app_settings.append(NameValuePair(name='APPINSIGHTS_INSTRUMENTATIONKEY',
                                                      value=instrumentation_key))

    poller = client.web_apps.create_or_update(resource_group_name, name, functionapp_def)
    functionapp = LongRunningOperation(cmd.cli_ctx)(poller)

    if consumption_plan_location and is_linux:
        logger.warning("Your Linux function app '%s', that uses a consumption plan has been successfully"
                       "created but is not active until content is published using"
                       "Azure Portal or the Functions Core Tools.", name)
    else:
        _set_remote_or_local_git(cmd, functionapp, resource_group_name, name, deployment_source_url,
                                 deployment_source_branch, deployment_local_git)

    return functionapp


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
    sku = storage_properties.sku.name.value
    allowed_storage_types = ['Standard_GRS', 'Standard_LRS', 'Standard_ZRS', 'Premium_LRS']

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
    client = web_client_factory(cmd.cli_ctx)
    full_sku = get_sku_name(sku)
    return client.list_geo_regions(full_sku, linux_workers_enabled)


def _check_zip_deployment_status(deployment_status_url, authorization, timeout=None):
    import requests
    total_trials = (int(timeout) // 2) if timeout else 450
    num_trials = 0
    while num_trials < total_trials:
        time.sleep(2)
        response = requests.get(deployment_status_url, headers=authorization)
        res_dict = response.json()
        num_trials = num_trials + 1
        if res_dict.get('status', 0) == 3:
            raise CLIError("Zip deployment failed.")
        elif res_dict.get('status', 0) == 4:
            break
        if 'progress' in res_dict:
            logger.info(res_dict['progress'])  # show only in debug mode, customers seem to find this confusing
    # if the deployment is taking longer than expected
    if res_dict.get('status', 0) != 4:
        raise CLIError("""Deployment is taking longer than expected. Please verify
                            status at '{}' beforing launching the app""".format(deployment_status_url))
    return res_dict


def list_continuous_webjobs(cmd, resource_group_name, name, slot=None):
    return _generic_site_operation(cmd.cli_ctx, resource_group_name, name, 'list_continuous_web_jobs', slot)


def start_continuous_webjob(cmd, resource_group_name, name, webjob_name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        client.web_apps.start_continuous_web_job(resource_group_name, name, webjob_name, slot)
        return client.web_apps.get_continuous_web_job_slot(resource_group_name, name, webjob_name, slot)
    client.web_apps.start_continuous_web_job(resource_group_name, name, webjob_name)
    return client.web_apps.get_continuous_web_job(resource_group_name, name, webjob_name)


def stop_continuous_webjob(cmd, resource_group_name, name, webjob_name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        client.web_apps.stop_continuous_web_job(resource_group_name, name, webjob_name, slot)
        return client.web_apps.get_continuous_web_job_slot(resource_group_name, name, webjob_name, slot)
    client.web_apps.stop_continuous_web_job(resource_group_name, name, webjob_name)
    return client.web_apps.get_continuous_web_job(resource_group_name, name, webjob_name)


def remove_continuous_webjob(cmd, resource_group_name, name, webjob_name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        return client.web_apps.delete_continuous_web_job(resource_group_name, name, webjob_name, slot)
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
        return client.web_apps.delete_triggered_web_job(resource_group_name, name, webjob_name, slot)
    return client.web_apps.delete_triggered_web_job(resource_group_name, name, webjob_name)


def get_history_triggered_webjob(cmd, resource_group_name, name, webjob_name, slot=None):
    client = web_client_factory(cmd.cli_ctx)
    if slot:
        return client.web_apps.list_triggered_web_job_history_slot(resource_group_name, name, webjob_name, slot)
    return client.web_apps.list_triggered_web_job_history(resource_group_name, name, webjob_name)


def create_deploy_webapp(cmd, name, location=None, sku=None, dryrun=False):  # pylint: disable=too-many-statements
    import os
    client = web_client_factory(cmd.cli_ctx)
    # the code to deploy is expected to be the current directory the command is running from
    src_dir = os.getcwd()
    # if dir is empty, show a message in dry run
    do_deployment = False if os.listdir(src_dir) == [] else True
    _create_new_rg = True
    _create_new_asp = True
    _create_new_app = True
    _set_build_appSetting = False

    # determine the details for app to be created from src contents
    lang_details = get_lang_from_content(src_dir)
    # we support E2E create and deploy for selected stacks, any other stack, set defaults for os & runtime
    # and skip deployment
    if lang_details['language'] is None:
        do_deployment = False
        sku = sku | 'F1'
        os_val = OS_DEFAULT
        detected_version = '-'
        runtime_version = '-'
    else:
        # update SKU to user set value
        if sku is None:
            sku = lang_details.get("default_sku")
        else:
            sku = sku
        language = lang_details.get("language")
        is_skip_build = language.lower() == STATIC_RUNTIME_NAME
        os_val = "Linux" if language.lower() == NODE_RUNTIME_NAME \
            or language.lower() == PYTHON_RUNTIME_NAME else OS_DEFAULT
        # detect the version
        data = get_runtime_version_details(lang_details.get('file_loc'), language)
        version_used_create = data.get('to_create')
        detected_version = data.get('detected')
        runtime_version = "{}|{}".format(language, version_used_create) if \
            version_used_create != "-" else version_used_create

    full_sku = get_sku_name(sku)
    location = set_location(cmd, sku, location)
    loc_name = location.replace(" ", "").lower()
    is_linux = True if os_val == 'Linux' else False
    asp = "appsvc_asp_{}_{}".format(os_val, loc_name)
    rg_name = "appsvc_rg_{}_{}".format(os_val, loc_name)
    # Resource group: check if default RG is set
    default_rg = cmd.cli_ctx.config.get('defaults', 'group', fallback=None)
    _create_new_rg = should_create_new_rg(cmd, default_rg, rg_name, is_linux)

    src_path = "{}".format(src_dir.replace("\\", "\\\\"))
    rg_str = "{}".format(rg_name)
    dry_run_str = r""" {
            "name" : "%s",
            "serverfarm" : "%s",
            "resourcegroup" : "%s",
            "sku": "%s",
            "os": "%s",
            "location" : "%s",
            "src_path" : "%s",
            "version_detected": "%s",
            "version_to_create": "%s"
            }
            """ % (name, asp, rg_str, full_sku, os_val, location, src_path,
                   detected_version, runtime_version)
    create_json = json.loads(dry_run_str)

    if dryrun:
        logger.warning("Web app will be created with the below configuration,re-run command "
                       "without the --dryrun flag to create & deploy a new app")
        return create_json

    # create RG if the RG doesn't already exist
    if _create_new_rg:
        logger.warning("Creating Resource group '%s' ...", rg_name)
        create_resource_group(cmd, rg_name, location)
        logger.warning("Resource group creation complete")
        _create_new_asp = True
    else:
        logger.warning("Resource group '%s' already exists.", rg_name)
        _create_new_asp = should_create_new_asp(cmd, rg_name, asp, location)
    # create new ASP if an existing one cannot be used
    if _create_new_asp:
        logger.warning("Creating App service plan '%s' ...", asp)
        sku_def = SkuDescription(tier=full_sku, name=sku, capacity=(1 if is_linux else None))
        plan_def = AppServicePlan(location=loc_name, app_service_plan_name=asp,
                                  sku=sku_def, reserved=(is_linux or None))
        client.app_service_plans.create_or_update(rg_name, asp, plan_def)
        logger.warning("App service plan creation complete")
        _create_new_app = True
    else:
        logger.warning("App service plan '%s' already exists.", asp)
        _create_new_app = should_create_new_app(cmd, rg_name, name)
    # create the app
    if _create_new_app:
        logger.warning("Creating app '%s' ....", name)
        create_webapp(cmd, rg_name, name, asp, runtime_version if is_linux else None)
        logger.warning("Webapp creation complete")
        _set_build_appSetting = True
    else:
        logger.warning("App '%s' already exists", name)
        if do_deployment and not is_skip_build:
            # setting the appsettings causes a app restart so we avoid if not needed
            _app_settings = get_app_settings(cmd, rg_name, name)
            if all(not d for d in _app_settings):
                _set_build_appSetting = True
            elif '"name": "SCM_DO_BUILD_DURING_DEPLOYMENT", "value": "true"' not in json.dumps(_app_settings[0]):
                _set_build_appSetting = True
            else:
                _set_build_appSetting = False

    # update create_json to include the app_url
    url = _get_url(cmd, rg_name, name)

    if _set_build_appSetting:
        # setting to build after deployment
        logger.warning("Updating app settings to enable build after deployment")
        update_app_settings(cmd, rg_name, name, ["SCM_DO_BUILD_DURING_DEPLOYMENT=true"])

    if do_deployment:
        logger.warning("Creating zip with contents of dir %s ...", src_dir)
        # zip contents & deploy
        zip_file_path = zip_contents_from_dir(src_dir, language)

        logger.warning("Preparing to deploy %s contents to app."
                       "This operation can take a while to complete ...",
                       '' if is_skip_build else 'and build')
        enable_zip_deploy(cmd, rg_name, name, zip_file_path)
        # Remove the file afer deployment, handling exception if user removed the file manually
        try:
            os.remove(zip_file_path)
        except OSError:
            pass
    create_json.update({'app_url': url})
    logger.warning("All done.")
    return create_json


def _ping_scm_site(cmd, resource_group, name):
    #  wakeup kudu, by making an SCM call
    import requests
    #  work around until the timeout limits issue for linux is investigated & fixed
    user_name, password = _get_site_credential(cmd.cli_ctx, resource_group, name)
    scm_url = _get_scm_url(cmd, resource_group, name)
    import urllib3
    authorization = urllib3.util.make_headers(basic_auth='{}:{}'.format(user_name, password))
    requests.get(scm_url + '/api/settings', headers=authorization)


def is_webapp_up(tunnel_server):
    return tunnel_server.is_webapp_up()


def create_tunnel_and_session(cmd, resource_group_name, name, port=None, slot=None):
    webapp = show_webapp(cmd, resource_group_name, name, slot)
    is_linux = webapp.reserved
    if not is_linux:
        raise CLIError("Only Linux App Service Plans supported, Found a Windows App Service Plan")

    profiles = list_publish_profiles(cmd, resource_group_name, name, slot)
    profile_user_name = next(p['userName'] for p in profiles)
    profile_user_password = next(p['userPWD'] for p in profiles)

    ssh_user_name = 'root'
    ssh_user_password = 'Docker!'

    if port is None:
        port = 0  # Will auto-select a free port from 1024-65535
        logger.info('No port defined, creating on random free port')
    host_name = name

    if slot is not None:
        host_name += "-" + slot

    tunnel_server = TunnelServer('', port, host_name, profile_user_name, profile_user_password)
    _ping_scm_site(cmd, resource_group_name, name)

    _wait_for_webapp(tunnel_server)

    t = threading.Thread(target=_start_tunnel, args=(tunnel_server,))
    t.daemon = True
    t.start()

    s = threading.Thread(target=_start_ssh_session,
                         args=('localhost', tunnel_server.get_port(), ssh_user_name, ssh_user_password))
    s.daemon = True
    s.start()

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
            raise CLIError("Timeout Error, Unable to establish a connection")
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


def ssh_webapp(cmd, resource_group_name, name, slot=None):  # pylint: disable=too-many-statements
    import platform
    if platform.system() == "Windows":
        raise CLIError('webapp ssh is only supported on linux and mac')
    else:
        create_tunnel_and_session(cmd, resource_group_name, name, port=None, slot=slot)


def create_devops_build(cmd, functionapp_name=None, organization_name=None, project_name=None,
                        overwrite_yaml=None, use_local_settings=None, local_git=None):
    from .azure_devops_build_iteractive import AzureDevopsBuildInteractive
    azure_devops_build_interactive = AzureDevopsBuildInteractive(cmd, logger, functionapp_name,
                                                                 organization_name, project_name,
                                                                 overwrite_yaml, use_local_settings,
                                                                 local_git)
    return azure_devops_build_interactive.interactive_azure_devops_build()
