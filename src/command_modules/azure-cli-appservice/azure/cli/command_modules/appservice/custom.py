# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import threading
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse  # pylint: disable=import-error
import OpenSSL.crypto

from msrestazure.azure_exceptions import CloudError

from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.web.models import (Site, SiteConfig, User, AppServicePlan, SiteConfigResource,
                                   SkuDescription, SslState, HostNameBinding, NameValuePair,
                                   BackupRequest, DatabaseBackupSetting, BackupSchedule,
                                   RestoreRequest, FrequencyUnit, Certificate, HostNameSslState,
                                   RampUpRule, UnauthenticatedClientAction)

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.arm import is_valid_resource_id, parse_resource_id
from azure.cli.core.commands import LongRunningOperation

from azure.cli.core.prompting import prompt_pass, NoTTYException
import azure.cli.core.azlogging as azlogging
from azure.cli.core.util import CLIError
from .vsts_cd_provider import VstsContinuousDeliveryProvider
from ._params import _generic_site_operation, _generic_settings_operation, AUTH_TYPES
from ._client_factory import web_client_factory, ex_handler_factory


logger = azlogging.get_az_logger(__name__)

# pylint:disable=no-member,too-many-lines,too-many-locals


def create_webapp(resource_group_name, name, plan, runtime=None, startup_file=None,
                  deployment_container_image_name=None, deployment_source_url=None, deployment_source_branch='master',
                  deployment_local_git=None):
    if deployment_source_url and deployment_local_git:
        raise CLIError('usage error: --deployment-source-url <url> | --deployment-local-git')
    client = web_client_factory()
    if is_valid_resource_id(plan):
        parse_result = parse_resource_id(plan)
        plan_info = client.app_service_plans.get(parse_result['resource_group'], parse_result['name'])
    else:
        plan_info = client.app_service_plans.get(resource_group_name, plan)
    is_linux = plan_info.reserved
    location = plan_info.location
    site_config = SiteConfig(app_settings=[])
    webapp_def = Site(server_farm_id=plan_info.id, location=location, site_config=site_config)

    if is_linux:
        if runtime and deployment_container_image_name:
            raise CLIError('usage error: --runtime | --deployment-container-image-name')
        if startup_file:
            site_config.app_command_line = startup_file

        if runtime:
            site_config.linux_fx_version = runtime
        elif deployment_container_image_name:
            site_config.linux_fx_version = _format_linux_fx_version(deployment_container_image_name)
            site_config.app_settings.append(NameValuePair("WEBSITES_ENABLE_APP_SERVICE_STORAGE", "false"))
        else:  # must specify runtime
            raise CLIError('usage error: must specify --runtime | --deployment-container-image-name')  # pylint: disable=line-too-long

    elif runtime:  # windows webapp
        if startup_file or deployment_container_image_name:
            raise CLIError("usage error: --startup-file or --deployment-container-image-name is "
                           "only appliable on linux webapp")
        helper = _StackRuntimeHelper(client)
        match = helper.resolve(runtime)
        if not match:
            raise CLIError("Runtime '{}' is not supported. Please invoke 'list-runtimes' to cross check".format(runtime))  # pylint: disable=line-too-long
        match['setter'](match, site_config)
        # Be consistent with portal: any windows webapp should have this even it doesn't have node in the stack
        if not match['displayName'].startswith('node'):
            site_config.app_settings.append(NameValuePair("WEBSITE_NODE_DEFAULT_VERSION", "6.9.1"))

    if site_config.app_settings:
        for setting in site_config.app_settings:
            logger.info('Will set appsetting %s', setting)

    poller = client.web_apps.create_or_update(resource_group_name, name, webapp_def)
    webapp = LongRunningOperation()(poller)

    # Ensure SCC operations follow right after the 'create', no precedent appsetting update commands
    _set_remote_or_local_git(webapp, resource_group_name, name, deployment_source_url,
                             deployment_source_branch, deployment_local_git)

    _fill_ftp_publishing_url(webapp, resource_group_name, name)

    return webapp


def show_webapp(resource_group_name, name, slot=None, app_instance=None):
    webapp = app_instance
    if not app_instance:  # when the routine is invoked as a help method, not through commands
        webapp = _generic_site_operation(resource_group_name, name, 'get', slot)
    _rename_server_farm_props(webapp)
    _fill_ftp_publishing_url(webapp, resource_group_name, name, slot)
    return webapp


def update_webapp(instance, client_affinity_enabled=None):
    if client_affinity_enabled is not None:
        instance.client_affinity_enabled = client_affinity_enabled == 'true'
    return instance


def list_webapp(resource_group_name=None):
    return _list_app(['app', 'app,linux'], resource_group_name)


def list_function_app(resource_group_name=None):
    return _list_app(['functionapp'], resource_group_name)


def _list_app(app_types, resource_group_name=None):
    client = web_client_factory()
    if resource_group_name:
        result = list(client.web_apps.list_by_resource_group(resource_group_name))
    else:
        result = list(client.web_apps.list())
    result = [x for x in result if x.kind in app_types]
    for webapp in result:
        _rename_server_farm_props(webapp)
    return result


def get_auth_settings(resource_group_name, name, slot=None):
    return _generic_site_operation(resource_group_name, name, 'get_auth_settings', slot)


def update_auth_settings(resource_group_name, name, enabled=None, action=None,  # pylint: disable=unused-argument
                         client_id=None, token_store_enabled=None,  # pylint: disable=unused-argument
                         runtime_version=None, token_refresh_extension_hours=None,  # pylint: disable=unused-argument
                         allowed_external_redirect_urls=None, client_secret=None,  # pylint: disable=unused-argument
                         allowed_audiences=None, issuer=None, facebook_app_id=None,  # pylint: disable=unused-argument
                         facebook_app_secret=None, facebook_oauth_scopes=None,  # pylint: disable=unused-argument
                         twitter_consumer_key=None, twitter_consumer_secret=None,  # pylint: disable=unused-argument
                         google_client_id=None, google_client_secret=None,  # pylint: disable=unused-argument
                         google_oauth_scopes=None, microsoft_account_client_id=None,  # pylint: disable=unused-argument
                         microsoft_account_client_secret=None,  # pylint: disable=unused-argument
                         microsoft_account_oauth_scopes=None, slot=None):  # pylint: disable=unused-argument
    auth_settings = get_auth_settings(resource_group_name, name, slot)

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
        print(arg, values[arg])
        if values.get(arg, None):
            setattr(auth_settings, arg, values[arg] if arg not in bool_flags else values[arg] == 'true')

    return _generic_site_operation(resource_group_name, name, 'update_auth_settings', slot, auth_settings)


def list_runtimes(linux=False):
    client = web_client_factory()
    if linux:
        # workaround before API is exposed
        logger.warning('You are viewing an offline list of runtimes. For up to date list, '
                       'check out https://aka.ms/linux-stacks')
        return ['node|6.4', 'node|4.5', 'node|6.2', 'node|6.6', 'node|6.9', 'node|6.10',
                'php|5.6', 'php|7.0', 'dotnetcore|1.0', 'dotnetcore|1.1', 'ruby|2.3']

    runtime_helper = _StackRuntimeHelper(client)
    return [s['displayName'] for s in runtime_helper.stacks]


def _rename_server_farm_props(webapp):
    # Should be renamed in SDK in a future release
    setattr(webapp, 'app_service_plan_id', webapp.server_farm_id)
    del webapp.server_farm_id
    return webapp


def delete_function_app(resource_group_name, name, slot=None):
    return _generic_site_operation(resource_group_name, name, 'delete', slot)


def delete_webapp(resource_group_name, name, keep_metrics=None, keep_empty_plan=None,
                  keep_dns_registration=None, slot=None):
    client = web_client_factory()
    delete_method = getattr(client.web_apps, 'delete' if slot is None else 'delete_slot')
    delete_method(resource_group_name, name,
                  delete_metrics=False if keep_metrics else None,
                  delete_empty_server_farm=False if keep_empty_plan else None,
                  skip_dns_registration=False if keep_dns_registration else None)


def stop_webapp(resource_group_name, name, slot=None):
    return _generic_site_operation(resource_group_name, name, 'stop', slot)


def start_webapp(resource_group_name, name, slot=None):
    return _generic_site_operation(resource_group_name, name, 'start', slot)


def restart_webapp(resource_group_name, name, slot=None):
    return _generic_site_operation(resource_group_name, name, 'restart', slot)


def get_site_configs(resource_group_name, name, slot=None):
    return _generic_site_operation(resource_group_name, name, 'get_configuration', slot)


def get_app_settings(resource_group_name, name, slot=None):
    result = _generic_site_operation(resource_group_name, name, 'list_application_settings', slot)
    client = web_client_factory()
    slot_app_setting_names = client.web_apps.list_slot_configuration_names(resource_group_name, name).app_setting_names
    return _build_app_settings_output(result.properties, slot_app_setting_names)


def get_connection_strings(resource_group_name, name, slot=None):
    result = _generic_site_operation(resource_group_name, name, 'list_connection_strings', slot)
    client = web_client_factory()
    slot_constr_names = client.web_apps.list_slot_configuration_names(resource_group_name, name) \
                              .connection_string_names or []
    result = [{'name': p,
               'value': result.properties[p],
               'slotSetting': p in slot_constr_names} for p in result.properties]
    return result


def _fill_ftp_publishing_url(webapp, resource_group_name, name, slot=None):
    profiles = list_publish_profiles(resource_group_name, name, slot)
    url = next(p['publishUrl'] for p in profiles if p['publishMethod'] == 'FTP')
    setattr(webapp, 'ftpPublishingUrl', url)
    return webapp


def _format_linux_fx_version(custom_image_name):
    fx_version = custom_image_name.strip()
    fx_version_lower = fx_version.lower()
    # handles case of only spaces
    if fx_version:
        if not fx_version_lower.startswith('docker|'):
            fx_version = '{}|{}'.format('DOCKER', custom_image_name)
    else:
        fx_version = ' '
    return fx_version


def _add_linux_fx_version(resource_group_name, name, custom_image_name, slot=None):
    fx_version = _format_linux_fx_version(custom_image_name)
    return update_site_configs(resource_group_name, name, linux_fx_version=fx_version, slot=slot)


def _delete_linux_fx_version(resource_group_name, name, slot=None):
    fx_version = ' '
    return update_site_configs(resource_group_name, name, linux_fx_version=fx_version, slot=slot)


def _get_linux_fx_version(resource_group_name, name, slot=None):
    site_config = get_site_configs(resource_group_name, name, slot)
    return site_config.linux_fx_version


# for any modifications to the non-optional parameters, adjust the reflection logic accordingly
# in the method
def update_site_configs(resource_group_name, name, slot=None,
                        linux_fx_version=None, php_version=None, python_version=None,  # pylint: disable=unused-argument
                        net_framework_version=None,  # pylint: disable=unused-argument
                        java_version=None, java_container=None, java_container_version=None,  # pylint: disable=unused-argument
                        remote_debugging_enabled=None, web_sockets_enabled=None,  # pylint: disable=unused-argument
                        always_on=None, auto_heal_enabled=None,  # pylint: disable=unused-argument
                        use32_bit_worker_process=None,  # pylint: disable=unused-argument
                        app_command_line=None):  # pylint: disable=unused-argument
    configs = get_site_configs(resource_group_name, name, slot)
    if linux_fx_version:
        if linux_fx_version.strip().lower().startswith('docker|'):
            update_app_settings(resource_group_name, name, ["WEBSITES_ENABLE_APP_SERVICE_STORAGE=false"])
        else:
            delete_app_settings(resource_group_name, name, ["WEBSITES_ENABLE_APP_SERVICE_STORAGE"])

    import inspect
    frame = inspect.currentframe()
    bool_flags = ['remote_debugging_enabled', 'web_sockets_enabled', 'always_on',
                  'auto_heal_enabled', 'use32_bit_worker_process']
    # note: getargvalues is used already in azure.cli.core.commands.
    # and no simple functional replacement for this deprecating method for 3.5
    args, _, _, values = inspect.getargvalues(frame)  # pylint: disable=deprecated-method
    for arg in args[3:]:
        if values.get(arg, None):
            setattr(configs, arg, values[arg] if arg not in bool_flags else values[arg] == 'true')

    return _generic_site_operation(resource_group_name, name, 'update_configuration', slot, configs)


def update_app_settings(resource_group_name, name, settings=None, slot=None, slot_settings=None):
    if not settings and not slot_settings:
        raise CLIError('Usage Error: --settings |--slot-settings')

    settings = settings or []
    slot_settings = slot_settings or []

    app_settings = _generic_site_operation(resource_group_name, name,
                                           'list_application_settings', slot)
    for name_value in settings + slot_settings:
        # split at the first '=', appsetting should not have '=' in the name
        settings_name, value = name_value.split('=', 1)
        app_settings.properties[settings_name] = value
    client = web_client_factory()

    result = _generic_settings_operation(resource_group_name, name,
                                         'update_application_settings',
                                         app_settings.properties, slot, client)

    app_settings_slot_cfg_names = []
    if slot_settings:
        new_slot_setting_names = [n.split('=', 1)[0] for n in slot_settings]
        slot_cfg_names = client.web_apps.list_slot_configuration_names(resource_group_name, name)
        slot_cfg_names.app_setting_names = slot_cfg_names.app_setting_names or []
        slot_cfg_names.app_setting_names += new_slot_setting_names
        app_settings_slot_cfg_names = slot_cfg_names.app_setting_names
        client.web_apps.update_slot_configuration_names(resource_group_name, name, slot_cfg_names)

    return _build_app_settings_output(result.properties, app_settings_slot_cfg_names)


def delete_app_settings(resource_group_name, name, setting_names, slot=None):
    app_settings = _generic_site_operation(resource_group_name, name, 'list_application_settings', slot)
    client = web_client_factory()

    slot_cfg_names = client.web_apps.list_slot_configuration_names(resource_group_name, name)
    is_slot_settings = False
    for setting_name in setting_names:
        app_settings.properties.pop(setting_name, None)
        if slot_cfg_names.app_setting_names and setting_name in slot_cfg_names.app_setting_names:
            slot_cfg_names.app_setting_names.remove(setting_name)
            is_slot_settings = True

    if is_slot_settings:
        client.web_apps.update_slot_configuration_names(resource_group_name, name, slot_cfg_names)

    result = _generic_settings_operation(resource_group_name, name,
                                         'update_application_settings',
                                         app_settings.properties, slot, client)

    return _build_app_settings_output(result.properties, slot_cfg_names.app_setting_names)


def _build_app_settings_output(app_settings, slot_cfg_names):
    slot_cfg_names = slot_cfg_names or []
    return [{'name': p,
             'value': app_settings[p],
             'slotSetting': p in slot_cfg_names} for p in _mask_creds_related_appsettings(app_settings)]


def update_connection_strings(resource_group_name, name, connection_string_type,
                              settings=None, slot=None, slot_settings=None):
    from azure.mgmt.web.models import ConnStringValueTypePair
    if not settings and not slot_settings:
        raise CLIError('Usage Error: --settings |--slot-settings')

    settings = settings or []
    slot_settings = slot_settings or []

    conn_strings = _generic_site_operation(resource_group_name, name,
                                           'list_connection_strings', slot)
    for name_value in settings + slot_settings:
        # split at the first '=', connection string should not have '=' in the name
        conn_string_name, value = name_value.split('=', 1)
        if value[0] in ["'", '"']:  # strip away the quots used as separators
            value = value[1:-1]
        conn_strings.properties[conn_string_name] = ConnStringValueTypePair(value,
                                                                            connection_string_type)
    client = web_client_factory()
    result = _generic_settings_operation(resource_group_name, name,
                                         'update_connection_strings',
                                         conn_strings.properties, slot, client)

    if slot_settings:
        new_slot_setting_names = [n.split('=', 1)[0] for n in slot_settings]
        slot_cfg_names = client.web_apps.list_slot_configuration_names(resource_group_name, name)
        slot_cfg_names.connection_string_names = slot_cfg_names.connection_string_names or []
        slot_cfg_names.connection_string_names += new_slot_setting_names
        client.web_apps.update_slot_configuration_names(resource_group_name, name, slot_cfg_names)

    return result.properties


def delete_connection_strings(resource_group_name, name, setting_names, slot=None):
    conn_strings = _generic_site_operation(resource_group_name, name,
                                           'list_connection_strings', slot)
    client = web_client_factory()

    slot_cfg_names = client.web_apps.list_slot_configuration_names(resource_group_name, name)
    is_slot_settings = False
    for setting_name in setting_names:
        conn_strings.properties.pop(setting_name, None)
        if slot_cfg_names.connection_string_names and setting_name in slot_cfg_names.connection_string_names:
            slot_cfg_names.connection_string_names.remove(setting_name)
            is_slot_settings = True

    if is_slot_settings:
        client.web_apps.update_slot_configuration_names(resource_group_name, name, slot_cfg_names)

    return _generic_settings_operation(resource_group_name, name,
                                       'update_connection_strings',
                                       conn_strings.properties, slot, client)


CONTAINER_APPSETTING_NAMES = ['DOCKER_REGISTRY_SERVER_URL', 'DOCKER_REGISTRY_SERVER_USERNAME',
                              'DOCKER_REGISTRY_SERVER_PASSWORD', "WEBSITES_ENABLE_APP_SERVICE_STORAGE"]
APPSETTINGS_TO_MASK = ['DOCKER_REGISTRY_SERVER_PASSWORD']


def update_container_settings(resource_group_name, name, docker_registry_server_url=None,
                              docker_custom_image_name=None, docker_registry_server_user=None,
                              websites_enable_app_service_storage=None, docker_registry_server_password=None,
                              slot=None):
    settings = []
    if docker_registry_server_url is not None:
        settings.append('DOCKER_REGISTRY_SERVER_URL=' + docker_registry_server_url)

    if (not docker_registry_server_user and not docker_registry_server_password and
            docker_registry_server_url and '.azurecr.io' in docker_registry_server_url):
        logger.warning('No credential was provided to access Azure Container Registry. Trying to look up...')
        parsed = urlparse(docker_registry_server_url)
        registry_name = (parsed.netloc if parsed.scheme else parsed.path).split('.')[0]
        try:
            docker_registry_server_user, docker_registry_server_password = _get_acr_cred(registry_name)
        except Exception as ex:  # pylint: disable=broad-except
            logger.warning("Retrieving credentials failed with an exception:'%s'", ex)  # consider throw if needed

    if docker_registry_server_user is not None:
        settings.append('DOCKER_REGISTRY_SERVER_USERNAME=' + docker_registry_server_user)
    if docker_registry_server_password is not None:
        settings.append('DOCKER_REGISTRY_SERVER_PASSWORD=' + docker_registry_server_password)
    if docker_custom_image_name is not None:
        _add_linux_fx_version(resource_group_name, name, docker_custom_image_name, slot)
    if websites_enable_app_service_storage:
        settings.append('WEBSITES_ENABLE_APP_SERVICE_STORAGE=' + websites_enable_app_service_storage)

    if docker_registry_server_user or docker_registry_server_password or docker_registry_server_url or websites_enable_app_service_storage:  # pylint: disable=line-too-long
        update_app_settings(resource_group_name, name, settings, slot)
    settings = get_app_settings(resource_group_name, name, slot)

    return _mask_creds_related_appsettings(_filter_for_container_settings(resource_group_name, name, settings))


def _get_acr_cred(registry_name):
    from azure.mgmt.containerregistry import ContainerRegistryManagementClient
    from azure.cli.core.commands.parameters import get_resources_in_subscription
    client = get_mgmt_service_client(ContainerRegistryManagementClient).registries

    result = get_resources_in_subscription('Microsoft.ContainerRegistry/registries')
    result = [item for item in result if item.name.lower() == registry_name]
    if not result or len(result) > 1:
        raise CLIError("No resource or more than one were found with name '{}'.".format(registry_name))
    resource_group_name = parse_resource_id(result[0].id)['resource_group']

    registry = client.get(resource_group_name, registry_name)

    if registry.admin_user_enabled:  # pylint: disable=no-member
        cred = client.list_credentials(resource_group_name, registry_name)
        return cred.username, cred.passwords[0].value
    raise CLIError("Failed to retrieve container registry credentails. Please either provide the "
                   "credentail or run 'az acr update -n {} --admin-enabled true' to enable "
                   "admin first.".format(registry_name))


def delete_container_settings(resource_group_name, name, slot=None):
    _delete_linux_fx_version(resource_group_name, name, slot)
    delete_app_settings(resource_group_name, name, CONTAINER_APPSETTING_NAMES, slot)


def show_container_settings(resource_group_name, name, slot=None):
    settings = get_app_settings(resource_group_name, name, slot)
    return _mask_creds_related_appsettings(_filter_for_container_settings(resource_group_name, name, settings, slot))


def _filter_for_container_settings(resource_group_name, name, settings, slot=None):
    result = [x for x in settings if x['name'] in CONTAINER_APPSETTING_NAMES]
    fx_version = _get_linux_fx_version(resource_group_name, name, slot).strip()
    if fx_version:
        added_image_name = {'name': 'DOCKER_CUSTOM_IMAGE_NAME',
                            'value': fx_version}
        result.append(added_image_name)
    return result


# TODO: remove this when #3660(service tracking issue) is resolved
def _mask_creds_related_appsettings(settings):
    for x in [x1 for x1 in settings if x1 in APPSETTINGS_TO_MASK]:
        settings[x] = None
    return settings


def add_hostname(resource_group_name, webapp_name, hostname, slot=None):
    client = web_client_factory()
    webapp = client.web_apps.get(resource_group_name, webapp_name)
    binding = HostNameBinding(webapp.location, site_name=webapp.name)
    if slot is None:
        return client.web_apps.create_or_update_host_name_binding(resource_group_name, webapp.name, hostname, binding)

    return client.web_apps.create_or_update_host_name_binding_slot(resource_group_name, webapp.name, hostname, binding,
                                                                   slot)


def delete_hostname(resource_group_name, webapp_name, hostname, slot=None):
    client = web_client_factory()
    if slot is None:
        return client.web_apps.delete_host_name_binding(resource_group_name, webapp_name, hostname)

    return client.web_apps.delete_host_name_binding_slot(resource_group_name, webapp_name, slot, hostname)


def list_hostnames(resource_group_name, webapp_name, slot=None):
    result = list(_generic_site_operation(resource_group_name, webapp_name,
                                          'list_host_name_bindings', slot))
    for r in result:
        r.name = r.name.split('/')[-1]
    return result


def get_external_ip(resource_group_name, webapp_name):
    # logics here are ported from portal
    client = web_client_factory()
    webapp_name = client.web_apps.get(resource_group_name, webapp_name)
    if webapp_name.hosting_environment_profile:
        address = client.app_service_environments.list_vips(
            resource_group_name, webapp_name.hosting_environment_profile.name)
        if address.internal_ip_address:
            ip_address = address.internal_ip_address
        else:
            vip = next((s for s in webapp_name.host_name_ssl_states if s.ssl_state == SslState.ip_based_enabled), None)
            ip_address = vip.virtual_ip if vip else address.service_ip_address
    else:
        ip_address = _resolve_hostname_through_dns(webapp_name.default_host_name)

    return {'ip': ip_address}


def _resolve_hostname_through_dns(hostname):
    import socket
    return socket.gethostbyname(hostname)


def create_webapp_slot(resource_group_name, webapp, slot, configuration_source=None):
    client = web_client_factory()
    site = client.web_apps.get(resource_group_name, webapp)
    location = site.location
    slot_def = Site(server_farm_id=site.server_farm_id, location=location)
    clone_from_prod = None
    slot_def.site_config = SiteConfig()

    poller = client.web_apps.create_or_update_slot(resource_group_name, webapp, slot_def, slot)
    result = LongRunningOperation()(poller)
    if configuration_source:
        clone_from_prod = configuration_source.lower() == webapp.lower()
        site_config = get_site_configs(
            resource_group_name, webapp, None if clone_from_prod else configuration_source)
        _generic_site_operation(resource_group_name, webapp,
                                'update_configuration', slot, site_config)

    # slot create doesn't clone over the app-settings and connection-strings, so we do it here
    # also make sure slot settings don't get propagated.
    if configuration_source:
        slot_cfg_names = client.web_apps.list_slot_configuration_names(resource_group_name, webapp)
        src_slot = None if clone_from_prod else configuration_source
        app_settings = _generic_site_operation(resource_group_name, webapp,
                                               'list_application_settings',
                                               src_slot)
        for a in slot_cfg_names.app_setting_names or []:
            app_settings.properties.pop(a, None)

        connection_strings = _generic_site_operation(resource_group_name, webapp,
                                                     'list_connection_strings',
                                                     src_slot)
        for a in slot_cfg_names.connection_string_names or []:
            connection_strings.properties.pop(a, None)

        _generic_settings_operation(resource_group_name, webapp,
                                    'update_application_settings',
                                    app_settings.properties, slot, client)
        _generic_settings_operation(resource_group_name, webapp,
                                    'update_connection_strings',
                                    connection_strings.properties, slot, client)

    result.name = result.name.split('/')[-1]
    return result


def config_source_control(resource_group_name, name, repo_url, repository_type='git', branch=None,  # pylint: disable=too-many-locals
                          manual_integration=None, git_token=None, slot=None, cd_app_type=None,
                          app_working_dir=None, nodejs_task_runner=None, python_framework=None,
                          python_version=None, cd_account_create=None, cd_project_url=None, test=None,
                          slot_swap=None, private_repo_username=None, private_repo_password=None):
    client = web_client_factory()
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
        status = vsts_provider.setup_continuous_delivery(resource_group_name, name, repo_url,
                                                         branch, git_token, slot_swap, cd_app_type_details,
                                                         cd_project_url, cd_account_create, location, test,
                                                         private_repo_username, private_repo_password, webapp_list)
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
            sc = SourceControl(location, source_control_name='GitHub', token=git_token)
            client.update_source_control('GitHub', sc)

        source_control = SiteSourceControl(location, repo_url=repo_url, branch=branch,
                                           is_manual_integration=manual_integration,
                                           is_mercurial=(repository_type != 'git'))

        # SCC config can fail if previous commands caused SCMSite shutdown, so retry here.
        for i in range(5):
            try:
                poller = _generic_site_operation(resource_group_name, name,
                                                 'create_or_update_source_control',
                                                 slot, source_control)
                return LongRunningOperation()(poller)
            except Exception as ex:  # pylint: disable=broad-except
                import re
                import time
                ex = ex_handler_factory(no_throw=True)(ex)
                # for non server errors(50x), just throw; otherwise retry 4 times
                if i == 4 or not re.findall(r'\(50\d\)', str(ex)):
                    raise
                logger.warning('retrying %s/4', i + 1)
                time.sleep(5)   # retry in a moment


def update_git_token(git_token=None):
    '''
    Update source control token cached in Azure app service. If no token is provided,
    the command will clean up existing token.
    '''
    client = web_client_factory()
    from azure.mgmt.web.models import SourceControl
    sc = SourceControl('not-really-needed', source_control_name='GitHub', token=git_token or '')
    return client.update_source_control('GitHub', sc)


def show_source_control(resource_group_name, name, slot=None):
    return _generic_site_operation(resource_group_name, name, 'get_source_control', slot)


def delete_source_control(resource_group_name, name, slot=None):
    return _generic_site_operation(resource_group_name, name, 'delete_source_control', slot)


def enable_local_git(resource_group_name, name, slot=None):
    client = web_client_factory()
    location = _get_location_from_webapp(client, resource_group_name, name)
    site_config = SiteConfigResource(location)
    site_config.scm_type = 'LocalGit'
    if slot is None:
        client.web_apps.create_or_update_configuration(resource_group_name, name, site_config)
    else:
        client.web_apps.create_or_update_configuration_slot(resource_group_name, name,
                                                            site_config, slot)

    return {'url': _get_local_git_url(client, resource_group_name, name, slot)}


def sync_site_repo(resource_group_name, name, slot=None):
    try:
        return _generic_site_operation(resource_group_name, name, 'sync_repository', slot)
    except CloudError as ex:  # Because of bad spec, sdk throws on 200. We capture it here
        if ex.status_code not in [200, 204]:
            raise ex


def list_app_service_plans(resource_group_name=None):
    client = web_client_factory()
    if resource_group_name is None:
        plans = list(client.app_service_plans.list())
    else:
        plans = list(client.app_service_plans.list_by_resource_group(resource_group_name))
    for plan in plans:
        # prune a few useless fields
        del plan.app_service_plan_name
        del plan.geo_region
        del plan.subscription
    return plans


def _linux_sku_check(sku):
    tier = _get_sku_name(sku)
    if tier in ['BASIC', 'STANDARD']:
        return
    format_string = 'usage error: {0} is not a valid sku for linux plan, please use one of the following: {1}'
    raise CLIError(format_string.format(sku, 'B1, B2, B3, S1, S2, S3'))


def create_app_service_plan(resource_group_name, name, is_linux, sku='B1', number_of_workers=None,
                            location=None):
    client = web_client_factory()
    sku = _normalize_sku(sku)
    if location is None:
        location = _get_location_from_resource_group(resource_group_name)
    if is_linux:
        _linux_sku_check(sku)
    # the api is odd on parameter naming, have to live with it for now
    sku_def = SkuDescription(tier=_get_sku_name(sku), name=sku, capacity=number_of_workers)
    plan_def = AppServicePlan(location, app_service_plan_name=name,
                              sku=sku_def, reserved=(is_linux or None))
    return client.app_service_plans.create_or_update(resource_group_name, name, plan_def)


def update_app_service_plan(instance, sku=None, number_of_workers=None,
                            admin_site_name=None):
    sku_def = instance.sku
    if sku is not None:
        sku = _normalize_sku(sku)
        sku_def.tier = _get_sku_name(sku)
        sku_def.name = sku

    if number_of_workers is not None:
        sku_def.capacity = number_of_workers

    instance.sku = sku_def
    if admin_site_name is not None:
        instance.admin_site_name = admin_site_name
    return instance


def show_backup_configuration(resource_group_name, webapp_name, slot=None):
    try:
        return _generic_site_operation(resource_group_name, webapp_name,
                                       'get_backup_configuration', slot)
    except:
        raise CLIError('Backup configuration not found')


def list_backups(resource_group_name, webapp_name, slot=None):
    return _generic_site_operation(resource_group_name, webapp_name, 'list_backups',
                                   slot)


def create_backup(resource_group_name, webapp_name, storage_account_url,
                  db_name=None, db_type=None,
                  db_connection_string=None, backup_name=None, slot=None):
    client = web_client_factory()
    if backup_name and backup_name.lower().endswith('.zip'):
        backup_name = backup_name[:-4]
    location = _get_location_from_webapp(client, resource_group_name, webapp_name)
    db_setting = _create_db_setting(db_name, db_type, db_connection_string)
    backup_request = BackupRequest(location, backup_request_name=backup_name,
                                   storage_account_url=storage_account_url, databases=db_setting)
    if slot:
        return client.web_apps.backup_slot(resource_group_name, webapp_name, backup_request, slot)

    return client.web_apps.backup(resource_group_name, webapp_name, backup_request)


def update_backup_schedule(resource_group_name, webapp_name, storage_account_url=None,
                           frequency=None, keep_at_least_one_backup=None,
                           retention_period_in_days=None, db_name=None,
                           db_connection_string=None, db_type=None, slot=None):
    client = web_client_factory()
    location = _get_location_from_webapp(client, resource_group_name, webapp_name)
    configuration = None

    try:
        configuration = _generic_site_operation(resource_group_name, webapp_name,
                                                'get_backup_configuration', slot)
    except CloudError:
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

    backup_schedule = BackupSchedule(frequency_num, frequency_unit.name,
                                     keep_at_least_one_backup, retention_period_in_days)
    backup_request = BackupRequest(location, backup_schedule=backup_schedule, enabled=True,
                                   storage_account_url=storage_account_url, databases=db_setting)
    return _generic_site_operation(resource_group_name, webapp_name, 'update_backup_configuration',
                                   slot, backup_request)


def restore_backup(resource_group_name, webapp_name, storage_account_url, backup_name,
                   db_name=None, db_type=None, db_connection_string=None,
                   target_name=None, overwrite=None, ignore_hostname_conflict=None, slot=None):
    client = web_client_factory()
    storage_blob_name = backup_name
    webapp_info = client.web_apps.get(resource_group_name, webapp_name)
    app_service_plan = webapp_info.server_farm_id.split('/')[-1]
    if not storage_blob_name.lower().endswith('.zip'):
        storage_blob_name += '.zip'
    location = _get_location_from_webapp(client, resource_group_name, webapp_name)
    db_setting = _create_db_setting(db_name, db_type, db_connection_string)
    restore_request = RestoreRequest(location, storage_account_url=storage_account_url,
                                     blob_name=storage_blob_name, overwrite=overwrite,
                                     site_name=target_name, databases=db_setting,
                                     ignore_conflicting_host_names=ignore_hostname_conflict,
                                     app_service_plan=app_service_plan)
    if slot:
        return client.web_apps.restore_slot(resource_group_name, webapp_name, 0, restore_request, slot)

    return client.web_apps.restore(resource_group_name, webapp_name, 0, restore_request)


def _create_db_setting(db_name, db_type, db_connection_string):
    if all([db_name, db_type, db_connection_string]):
        return [DatabaseBackupSetting(db_type, db_name, connection_string=db_connection_string)]
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


def _get_sku_name(tier):
    tier = tier.upper()
    if tier == 'F1':
        return 'FREE'
    elif tier == 'D1':
        return 'SHARED'
    elif tier in ['B1', 'B2', 'B3']:
        return 'BASIC'
    elif tier in ['S1', 'S2', 'S3']:
        return 'STANDARD'
    elif tier in ['P1', 'P2', 'P3', 'P1V2', 'P2V2', 'P3V2']:
        return 'PREMIUM'
    else:
        raise CLIError("Invalid sku(pricing tier), please refer to command help for valid values")


def _get_location_from_resource_group(resource_group_name):
    from azure.mgmt.resource import ResourceManagementClient
    client = get_mgmt_service_client(ResourceManagementClient)
    group = client.resource_groups.get(resource_group_name)
    return group.location


def _get_location_from_webapp(client, resource_group_name, webapp):
    webapp = client.web_apps.get(resource_group_name, webapp)
    return webapp.location


def _get_local_git_url(client, resource_group_name, name, slot=None):
    user = client.get_publishing_user()
    result = _generic_site_operation(resource_group_name, name, 'get_source_control', slot)
    parsed = urlparse(result.repo_url)
    return '{}://{}@{}/{}.git'.format(parsed.scheme, user.publishing_user_name,
                                      parsed.netloc, name)


def _get_scm_url(resource_group_name, name, slot=None):
    from azure.mgmt.web.models import HostType
    webapp = show_webapp(resource_group_name, name, slot=slot)
    for host in webapp.host_name_ssl_states or []:
        if host.host_type == HostType.repository:
            return "https://{}".format(host.name)

    # this should not happen, but throw anyway
    raise ValueError('Failed to retrieve Scm Uri')


def set_deployment_user(user_name, password=None):
    '''
    Update deployment credentials.(Note, all webapps in your subscription will be impacted)
    '''
    client = web_client_factory()
    user = User()
    user.publishing_user_name = user_name
    if password is None:
        try:
            password = prompt_pass(msg='Password: ', confirm=True)
        except NoTTYException:
            raise CLIError('Please specify both username and password in non-interactive mode.')

    user.publishing_password = password
    result = client.update_publishing_user(user)
    return result


def list_publish_profiles(resource_group_name, name, slot=None):
    import xmltodict

    content = _generic_site_operation(resource_group_name, name,
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


def enable_cd(resource_group_name, name, enable, slot=None):
    settings = []
    settings.append("DOCKER_ENABLE_CI=" + enable)

    update_app_settings(resource_group_name, name, settings, slot)

    return show_container_cd_url(resource_group_name, name, slot)


def show_container_cd_url(resource_group_name, name, slot=None):
    settings = get_app_settings(resource_group_name, name, slot)
    docker_enabled = False
    for setting in settings:
        if setting['name'] == 'DOCKER_ENABLE_CI' and setting['value'] == 'true':
            docker_enabled = True
            break

    cd_settings = {}
    cd_settings['DOCKER_ENABLE_CI'] = docker_enabled

    if docker_enabled:
        profiles = list_publish_profiles(resource_group_name, name, slot)
        for profile in profiles:
            if profile['publishMethod'] == 'MSDeploy':
                scmUrl = profile['publishUrl'].replace(":443", "")
                cd_url = 'https://' + profile['userName'] + ':' + profile['userPWD'] + '@' + scmUrl + '/docker/hook'
                cd_settings['CI_CD_URL'] = cd_url
                break
    else:
        cd_settings['CI_CD_URL'] = ''

    return cd_settings


def view_in_browser(resource_group_name, name, slot=None, logs=False):
    site = _generic_site_operation(resource_group_name, name, 'get', slot)
    url = site.default_host_name
    ssl_host = next((h for h in site.host_name_ssl_states
                     if h.ssl_state != SslState.disabled), None)
    url = ('https' if ssl_host else 'http') + '://' + url
    _open_page_in_browser(url)
    if logs:
        get_streaming_log(resource_group_name, name, provider=None, slot=slot)


def _open_page_in_browser(url):
    import sys
    if sys.platform.lower() == 'darwin':
        # handle 2 things:
        # a. On OSX sierra, 'python -m webbrowser -t <url>' emits out "execution error: <url> doesn't
        #    understand the "open location" message"
        # b. Python 2.x can't sniff out the default browser
        import subprocess
        subprocess.Popen(['open', url])
    else:
        import webbrowser
        webbrowser.open(url, new=2)  # 2 means: open in a new tab, if possible


# TODO: expose new blob suport
def config_diagnostics(resource_group_name, name, level=None,
                       application_logging=None, web_server_logging=None,
                       detailed_error_messages=None, failed_request_tracing=None,
                       slot=None):
    from azure.mgmt.web.models import (FileSystemApplicationLogsConfig, ApplicationLogsConfig,
                                       SiteLogsConfig, HttpLogsConfig,
                                       FileSystemHttpLogsConfig, EnabledConfig)
    client = web_client_factory()
    # TODO: ensure we call get_site only once
    site = client.web_apps.get(resource_group_name, name)
    location = site.location

    application_logs = None
    if application_logging is not None:
        if not application_logging:
            level = 'Off'
        elif level is None:
            level = 'Error'
        fs_log = FileSystemApplicationLogsConfig(level)
        application_logs = ApplicationLogsConfig(fs_log)

    http_logs = None
    if web_server_logging is not None:
        enabled = web_server_logging
        # 100 mb max log size, retenting last 3 days. Yes we hard code it, portal does too
        fs_server_log = FileSystemHttpLogsConfig(100, 3, enabled)
        http_logs = HttpLogsConfig(fs_server_log)

    detailed_error_messages_logs = (None if detailed_error_messages is None
                                    else EnabledConfig(detailed_error_messages))
    failed_request_tracing_logs = (None if failed_request_tracing is None
                                   else EnabledConfig(failed_request_tracing))
    site_log_config = SiteLogsConfig(location,
                                     application_logs=application_logs,
                                     http_logs=http_logs,
                                     failed_requests_tracing=failed_request_tracing_logs,
                                     detailed_error_messages=detailed_error_messages_logs)

    return _generic_site_operation(resource_group_name, name, 'update_diagnostic_logs_config',
                                   slot, site_log_config)


def show_diagnostic_settings(resource_group_name, name, slot=None):
    return _generic_site_operation(resource_group_name, name, 'get_diagnostic_logs_configuration', slot)


def config_slot_auto_swap(resource_group_name, webapp, slot, auto_swap_slot=None, disable=None):
    client = web_client_factory()
    site_config = client.web_apps.get_configuration_slot(resource_group_name, webapp, slot)
    site_config.auto_swap_slot_name = '' if disable else (auto_swap_slot or 'production')
    return client.web_apps.update_configuration_slot(resource_group_name, webapp, site_config, slot)


def list_slots(resource_group_name, webapp):
    client = web_client_factory()
    slots = list(client.web_apps.list_slots(resource_group_name, webapp))
    for slot in slots:
        slot.name = slot.name.split('/')[-1]
        setattr(slot, 'app_service_plan', parse_resource_id(slot.server_farm_id)['name'])
        del slot.server_farm_id
    return slots


def swap_slot(resource_group_name, webapp, slot, target_slot=None, action='swap'):
    client = web_client_factory()
    if action == 'swap':
        if target_slot is None:
            poller = client.web_apps.swap_slot_with_production(resource_group_name,
                                                               webapp, slot, True)
        else:
            poller = client.web_apps.swap_slot_slot(resource_group_name, webapp,
                                                    slot, target_slot, True)
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

        client.web_apps.reset_slot_configuration_slot(resource_group_name, webapp, slot)
        return None


def delete_slot(resource_group_name, webapp, slot):
    client = web_client_factory()
    # TODO: once swagger finalized, expose other parameters like: delete_all_slots, etc...
    client.web_apps.delete_slot(resource_group_name, webapp, slot)


def set_traffic_routing(resource_group_name, name, distribution):
    client = web_client_factory()
    site = client.web_apps.get(resource_group_name, name)
    configs = get_site_configs(resource_group_name, name)
    host_name_suffix = '.' + site.default_host_name.split('.', 1)[1]
    configs.experiments.ramp_up_rules = []
    for r in distribution:
        slot, percentage = r.split('=')
        configs.experiments.ramp_up_rules.append(RampUpRule(action_host_name=slot + host_name_suffix,
                                                            reroute_percentage=float(percentage),
                                                            name=slot))
    _generic_site_operation(resource_group_name, name, 'update_configuration', None, configs)

    return configs.experiments.ramp_up_rules


def show_traffic_routing(resource_group_name, name):
    configs = get_site_configs(resource_group_name, name)
    return configs.experiments.ramp_up_rules


def clear_traffic_routing(resource_group_name, name):
    set_traffic_routing(resource_group_name, name, [])


def get_streaming_log(resource_group_name, name, provider=None, slot=None):
    scm_url = _get_scm_url(resource_group_name, name, slot)
    streaming_url = scm_url + '/logstream'
    import time
    if provider:
        streaming_url += ('/' + provider.lstrip('/'))

    client = web_client_factory()
    user, password = _get_site_credential(client, resource_group_name, name)
    t = threading.Thread(target=_get_log, args=(streaming_url, user, password))
    t.daemon = True
    t.start()

    while True:
        time.sleep(100)  # so that ctrl+c can stop the command


def download_historical_logs(resource_group_name, name, log_file=None, slot=None):
    scm_url = _get_scm_url(resource_group_name, name, slot)
    url = scm_url.rstrip('/') + '/dump'
    client = web_client_factory()
    user_name, password = _get_site_credential(client, resource_group_name, name)
    _get_log(url, user_name, password, log_file)
    logger.warning('Downloaded logs to %s', log_file)


def _get_site_credential(client, resource_group_name, name):
    creds = client.web_apps.list_publishing_credentials(resource_group_name, name)
    creds = creds.result()
    return (creds.publishing_user_name, creds.publishing_password)


def _get_log(url, user_name, password, log_file=None):
    import sys
    import certifi
    import urllib3
    try:
        import urllib3.contrib.pyopenssl
        urllib3.contrib.pyopenssl.inject_into_urllib3()
    except ImportError:
        pass

    std_encoding = sys.stdout.encoding
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
        for chunk in r.stream():
            if chunk:
                # Extra encode() and decode for stdout which does not surpport 'utf-8'
                print(chunk.decode(encoding='utf-8', errors='replace')
                      .encode(std_encoding, errors='replace')
                      .decode(std_encoding, errors='replace'), end='')  # each line of log has CRLF.
    r.release_conn()


def upload_ssl_cert(resource_group_name, name, certificate_password, certificate_file):
    client = web_client_factory()
    webapp = _generic_site_operation(resource_group_name, name, 'get')
    cert_resource_group_name = parse_resource_id(webapp.server_farm_id)['resource_group']
    cert_file = open(certificate_file, 'rb')
    cert_contents = cert_file.read()
    hosting_environment_profile_param = webapp.hosting_environment_profile
    if hosting_environment_profile_param is None:
        hosting_environment_profile_param = ""

    thumb_print = _get_cert(certificate_password, certificate_file)
    cert_name = _generate_cert_name(thumb_print, hosting_environment_profile_param,
                                    webapp.location, cert_resource_group_name)
    cert = Certificate(password=certificate_password, pfx_blob=cert_contents,
                       location=webapp.location)
    return client.certificates.create_or_update(cert_resource_group_name, cert_name, cert)


def _generate_cert_name(thumb_print, hosting_environment, location, resource_group_name):
    return "%s_%s_%s_%s" % (thumb_print, hosting_environment, location, resource_group_name)


def _get_cert(certificate_password, certificate_file):
    ''' Decrypts the .pfx file '''
    p12 = OpenSSL.crypto.load_pkcs12(open(certificate_file, 'rb').read(), certificate_password)
    cert = p12.get_certificate()
    digest_algorithm = 'sha1'
    thumbprint = cert.digest(digest_algorithm).decode("utf-8").replace(':', '')
    return thumbprint


def list_ssl_certs(resource_group_name):
    client = web_client_factory()
    return client.certificates.list_by_resource_group(resource_group_name)


def delete_ssl_cert(resource_group_name, certificate_thumbprint):
    client = web_client_factory()
    webapp_certs = client.certificates.list_by_resource_group(resource_group_name)
    for webapp_cert in webapp_certs:
        if webapp_cert.thumbprint == certificate_thumbprint:
            return client.certificates.delete(resource_group_name, webapp_cert.name)
    raise CLIError("Certificate for thumbprint '{}' not found".format(certificate_thumbprint))


def _update_host_name_ssl_state(resource_group_name, webapp_name, location,
                                host_name, ssl_state, thumbprint, slot=None):
    updated_webapp = Site(host_name_ssl_states=[HostNameSslState(name=host_name,
                                                                 ssl_state=ssl_state,
                                                                 thumbprint=thumbprint,
                                                                 to_update=True)],
                          location=location)
    name = '{}({})'.format(webapp_name, slot) if slot else webapp_name
    return _generic_site_operation(resource_group_name, name, 'create_or_update',
                                   slot, updated_webapp)


def _update_ssl_binding(resource_group_name, name, certificate_thumbprint, ssl_type, slot=None):
    client = web_client_factory()
    webapp = client.web_apps.get(resource_group_name, name)
    cert_resource_group_name = parse_resource_id(webapp.server_farm_id)['resource_group']
    webapp_certs = client.certificates.list_by_resource_group(cert_resource_group_name)
    for webapp_cert in webapp_certs:
        if webapp_cert.thumbprint == certificate_thumbprint:
            if len(webapp_cert.host_names) == 1 and not webapp_cert.host_names[0].startswith('*'):
                return _update_host_name_ssl_state(resource_group_name, name, webapp.location,
                                                   webapp_cert.host_names[0], ssl_type,
                                                   certificate_thumbprint, slot)

            query_result = list_hostnames(resource_group_name, name, slot)
            hostnames_in_webapp = [x.name.split('/')[-1] for x in query_result]
            to_update = _match_host_names_from_cert(webapp_cert.host_names, hostnames_in_webapp)
            for h in to_update:
                _update_host_name_ssl_state(resource_group_name, name, webapp.location,
                                            h, ssl_type, certificate_thumbprint, slot)

            return show_webapp(resource_group_name, name, slot)

    raise CLIError("Certificate for thumbprint '{}' not found.".format(certificate_thumbprint))


def bind_ssl_cert(resource_group_name, name, certificate_thumbprint, ssl_type, slot=None):
    return _update_ssl_binding(
        resource_group_name, name, certificate_thumbprint,
        SslState.sni_enabled if ssl_type == 'SNI' else SslState.ip_based_enabled, slot)


def unbind_ssl_cert(resource_group_name, name, certificate_thumbprint, slot=None):
    return _update_ssl_binding(resource_group_name, name,
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

    def __init__(self, client):
        self._client = client
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
        site_config.app_settings += [NameValuePair(k, v) for k, v in stack['configs'].items()]
        return site_config

    def _load_stacks(self):
        if self._stacks:
            return
        raw_list = self._client.provider.get_available_stacks()
        stacks = raw_list['value']
        config_mappings = {
            'node': 'WEBSITE_NODE_DEFAULT_VERSION',
            'python': 'python_version',
            'php': 'php_version',
            'aspnet': 'net_framework_version'
        }

        result = []
        # get all stack version except 'java'
        for name, properties in [(s['name'], s['properties']) for s in stacks
                                 if s['name'] in config_mappings]:
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


def create_function(resource_group_name, name, storage_account, plan=None,
                    consumption_plan_location=None, deployment_source_url=None,
                    deployment_source_branch='master', deployment_local_git=None):
    if deployment_source_url and deployment_local_git:
        raise CLIError('usage error: --deployment-source-url <url> | --deployment-local-git')
    if bool(plan) == bool(consumption_plan_location):
        raise CLIError("usage error: --plan NAME_OR_ID | --consumption-plan-location LOCATION")

    site_config = SiteConfig(app_settings=[])
    functionapp_def = Site(location=None, site_config=site_config)
    client = web_client_factory()
    if consumption_plan_location:
        locations = list_consumption_locations()
        location = next((l for l in locations if l['name'].lower() == consumption_plan_location.lower()), None)
        if location is None:
            raise CLIError("Location is invalid. Use: az functionapp list-consumption-locations")
        functionapp_def.location = consumption_plan_location
    else:
        if is_valid_resource_id(plan):
            plan = parse_resource_id(plan)['name']
        plan_info = client.app_service_plans.get(resource_group_name, plan)
        location = plan_info.location
        functionapp_def.server_farm_id = plan
        functionapp_def.location = location

    con_string = _validate_and_get_connection_string(resource_group_name, storage_account)
    functionapp_def.kind = 'functionapp'

    # adding appsetting to site to make it a function
    site_config.app_settings.append(NameValuePair('AzureWebJobsStorage', con_string))
    site_config.app_settings.append(NameValuePair('AzureWebJobsDashboard', con_string))
    site_config.app_settings.append(NameValuePair('WEBSITE_NODE_DEFAULT_VERSION', '6.5.0'))
    site_config.app_settings.append(NameValuePair('FUNCTIONS_EXTENSION_VERSION', '~1'))

    if consumption_plan_location is None:
        site_config.always_on = True
    else:
        site_config.app_settings.append(NameValuePair('WEBSITE_CONTENTAZUREFILECONNECTIONSTRING',
                                                      con_string))
        site_config.app_settings.append(NameValuePair('WEBSITE_CONTENTSHARE', name.lower()))

    poller = client.web_apps.create_or_update(resource_group_name, name, functionapp_def)
    functionapp = LongRunningOperation()(poller)

    _set_remote_or_local_git(functionapp, resource_group_name, name, deployment_source_url,
                             deployment_source_branch, deployment_local_git)

    return functionapp


def _set_remote_or_local_git(webapp, resource_group_name, name, deployment_source_url=None,
                             deployment_source_branch='master', deployment_local_git=None):
    if deployment_source_url:
        logger.warning("Linking to git repository '%s'", deployment_source_url)
        try:
            config_source_control(resource_group_name, name, deployment_source_url, 'git',
                                  deployment_source_branch, manual_integration=True)
        except Exception as ex:  # pylint: disable=broad-except
            ex = ex_handler_factory(no_throw=True)(ex)
            logger.warning("Link to git repository failed due to error '%s'", ex)

    if deployment_local_git:
        local_git_info = enable_local_git(resource_group_name, name)
        logger.warning("Local git is configured with url of '%s'", local_git_info['url'])
        setattr(webapp, 'deploymentLocalGitUrl', local_git_info['url'])


def _validate_and_get_connection_string(resource_group_name, storage_account):
    from azure.cli.core._profile import CLOUD
    sa_resource_group = resource_group_name
    if is_valid_resource_id(storage_account):
        sa_resource_group = parse_resource_id(storage_account)['resource_group']
        storage_account = parse_resource_id(storage_account)['name']
    storage_client = get_mgmt_service_client(StorageManagementClient)
    storage_properties = storage_client.storage_accounts.get_properties(sa_resource_group,
                                                                        storage_account)
    error_message = ''
    endpoints = storage_properties.primary_endpoints
    sku = storage_properties.sku.name.value
    allowed_storage_types = ['Standard_GRS', 'Standard_LRS', 'Standard_ZRS', 'Premium_LRS']

    for e in ['blob', 'queue', 'table']:
        if not getattr(endpoints, e, None):
            error_message = "Storage account '{}' has no '{}' endpoint. It must have table, queue, and blob endpoints all enabled".format(e, storage_account)   # pylint: disable=line-too-long
    if sku not in allowed_storage_types:
        error_message += 'Storage type {} is not allowed'.format(sku)

    if error_message:
        raise CLIError(error_message)

    obj = storage_client.storage_accounts.list_keys(resource_group_name, storage_account)  # pylint: disable=no-member
    try:
        keys = [obj.keys[0].value, obj.keys[1].value]  # pylint: disable=no-member
    except AttributeError:
        # Older API versions have a slightly different structure
        keys = [obj.key1, obj.key2]  # pylint: disable=no-member

    endpoint_suffix = CLOUD.suffixes.storage_endpoint
    connection_string = 'DefaultEndpointsProtocol={};EndpointSuffix={};AccountName={};AccountKey={}'.format(
        "https",
        endpoint_suffix,
        storage_account,
        keys[0])  # pylint: disable=no-member

    return connection_string


def list_consumption_locations():
    client = web_client_factory()
    regions = client.list_geo_regions(sku='Dynamic')
    return [{'name': x.name.lower().replace(" ", "")} for x in regions]
