# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=no-self-use,too-many-arguments,too-many-lines
from __future__ import print_function
import json
import threading
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse # pylint: disable=import-error
import OpenSSL.crypto

from msrestazure.azure_exceptions import CloudError

from azure.mgmt.web.models import (Site, SiteConfig, User, AppServicePlan,
                                   SkuDescription, SslState, HostNameBinding,
                                   BackupRequest, DatabaseBackupSetting, BackupSchedule,
                                   RestoreRequest, FrequencyUnit, Certificate, HostNameSslState)

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.arm import is_valid_resource_id, parse_resource_id
from azure.cli.core.commands import LongRunningOperation

from azure.cli.core.prompting import prompt_pass, NoTTYException
import azure.cli.core.azlogging as azlogging
from azure.cli.core._util import CLIError
from ._params import web_client_factory, _generic_site_operation

logger = azlogging.get_az_logger(__name__)

#pylint:disable=no-member

#workaround that app service's error doesn't comform to LRO spec
class AppServiceLongRunningOperation(LongRunningOperation): #pylint: disable=too-few-public-methods

    def __init__(self, creating_plan=False):
        super(AppServiceLongRunningOperation, self).__init__(self)
        self._creating_plan = creating_plan

    def __call__(self, poller):
        try:
            return super(AppServiceLongRunningOperation, self).__call__(poller)
        except Exception as ex:
            raise self._get_detail_error(ex)

    def _get_detail_error(self, ex):
        try:
            detail = json.loads(ex.response.text)['Message']
            if self._creating_plan:
                if 'Requested features are not supported in region' in detail:
                    detail = ("Plan with linux worker is not supported in current region. For " +
                              "supported regions, please refer to https://docs.microsoft.com/en-us/"
                              "azure/app-service-web/app-service-linux-intro")
                elif 'Not enough available reserved instance servers to satisfy' in detail:
                    detail = ("Plan with Linux worker can only be created in a group " +
                              "which has never contained a Windows worker. Please use " +
                              "a new resource group. Original error:" + detail)
            return CLIError(detail)
        except: #pylint: disable=bare-except
            return ex

def create_webapp(resource_group_name, name, plan):
    client = web_client_factory()
    if is_valid_resource_id(plan):
        plan = parse_resource_id(plan)['name']
    location = _get_location_from_app_service_plan(client, resource_group_name, plan)
    webapp_def = Site(server_farm_id=plan, location=location)
    poller = client.web_apps.create_or_update(resource_group_name, name, webapp_def)
    return AppServiceLongRunningOperation()(poller)

def show_webapp(resource_group_name, name, slot=None):
    webapp = _generic_site_operation(resource_group_name, name, 'get', slot)
    return _rename_server_farm_props(webapp)

def list_webapp(resource_group_name=None):
    client = web_client_factory()
    if resource_group_name:
        result = client.web_apps.list_by_resource_group(resource_group_name)
    else:
        result = client.web_apps.list()
    for webapp in result:
        _rename_server_farm_props(webapp)
    return result

def _rename_server_farm_props(webapp):
    #Should be renamed in SDK in a future release
    setattr(webapp, 'app_service_plan_id', webapp.server_farm_id)
    del webapp.server_farm_id
    return webapp

def delete_webapp(resource_group_name, name, slot=None):
    return _generic_site_operation(resource_group_name, name, 'delete', slot)

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
    return result.properties

#for any modifications to the non-optional parameters, adjust the reflection logic accordingly
#in the method
def update_site_configs(resource_group_name, name, slot=None,
                        php_version=None, python_version=None,#pylint: disable=unused-argument
                        node_version=None, net_framework_version=None, #pylint: disable=unused-argument
                        java_version=None, java_container=None, java_container_version=None,#pylint: disable=unused-argument
                        remote_debugging_enabled=None, web_sockets_enabled=None,#pylint: disable=unused-argument
                        always_on=None, auto_heal_enabled=None,#pylint: disable=unused-argument
                        use32_bit_worker_process=None,#pylint: disable=unused-argument
                        app_command_line=None):#pylint: disable=unused-argument
    configs = get_site_configs(resource_group_name, name, slot)
    import inspect
    frame = inspect.currentframe()
    bool_flags = ['remote_debugging_enabled', 'web_sockets_enabled', 'always_on',
                  'auto_heal_enabled', 'use32_bit_worker_process']
    #note: getargvalues is used already in azure.cli.core.commands.
    #and no simple functional replacement for this deprecating method for 3.5
    args, _, _, values = inspect.getargvalues(frame) #pylint: disable=deprecated-method
    for arg in args[3:]:
        if arg is not None:
            setattr(configs, arg, values[arg] if arg not in bool_flags else values[arg] == 'true')

    return _generic_site_operation(resource_group_name, name, 'update_configuration', slot, configs)

def update_app_settings(resource_group_name, name, settings, slot=None):
    app_settings = _generic_site_operation(resource_group_name, name,
                                           'list_application_settings', slot)
    for name_value in settings:
        #split at the first '=', appsetting should not have '=' in the name
        settings_name, value = name_value.split('=', 1)
        app_settings.properties[settings_name] = value

    result = _generic_site_operation(resource_group_name, name, 'update_application_settings',
                                     slot, app_settings)
    return result.properties

def delete_app_settings(resource_group_name, name, setting_names, slot=None):
    app_settings = _generic_site_operation(resource_group_name, name,
                                           'list_application_settings', slot)
    for setting_name in setting_names:
        app_settings.properties.pop(setting_name, None)

    return _generic_site_operation(resource_group_name, name, 'update_application_settings',
                                   slot, app_settings)

CONTAINER_APPSETTING_NAMES = ['DOCKER_REGISTRY_SERVER_URL', 'DOCKER_REGISTRY_SERVER_USERNAME',
                              'DOCKER_REGISTRY_SERVER_PASSWORD', 'DOCKER_CUSTOM_IMAGE_NAME']

def update_container_settings(resource_group_name, name, docker_registry_server_url=None,
                              docker_custom_image_name=None, docker_registry_server_user=None,
                              docker_registry_server_password=None, slot=None):
    settings = []
    if docker_registry_server_url is not None:
        settings.append('DOCKER_REGISTRY_SERVER_URL=' + docker_registry_server_url)
    if docker_registry_server_user is not None:
        settings.append('DOCKER_REGISTRY_SERVER_USERNAME=' + docker_registry_server_user)
    if docker_registry_server_password is not None:
        settings.append('DOCKER_REGISTRY_SERVER_PASSWORD=' + docker_registry_server_password)
    if docker_custom_image_name is not None:
        settings.append('DOCKER_CUSTOM_IMAGE_NAME=' + docker_custom_image_name)
    settings = update_app_settings(resource_group_name, name, settings, slot)
    return _filter_for_container_settings(settings)

def delete_container_settings(resource_group_name, name, slot=None):
    delete_app_settings(resource_group_name, name, CONTAINER_APPSETTING_NAMES, slot)

def show_container_settings(resource_group_name, name, slot=None):
    settings = get_app_settings(resource_group_name, name, slot)
    return _filter_for_container_settings(settings)

def _filter_for_container_settings(settings):
    return {x: settings[x] for x in settings if x in CONTAINER_APPSETTING_NAMES}

def add_hostname(resource_group_name, webapp_name, name, slot=None):
    client = web_client_factory()
    webapp = client.web_apps.get(resource_group_name, webapp_name)
    binding = HostNameBinding(webapp.location, host_name_binding_name=name, site_name=webapp.name)
    if slot is None:
        return client.web_apps.create_or_update_host_name_binding(
            resource_group_name, webapp.name, name, binding)
    else:
        return client.web_apps.create_or_update_host_name_binding_slot(
            resource_group_name, webapp.name, name, binding, slot)

def delete_hostname(resource_group_name, webapp_name, name, slot=None):
    client = web_client_factory()
    if slot is None:
        return client.web_apps.delete_host_name_binding(resource_group_name, webapp_name, name)
    else:
        return client.web_apps.delete_host_name_binding_slot(resource_group_name,
                                                             webapp_name, slot, name)

def list_hostnames(resource_group_name, webapp_name, slot=None):
    return _generic_site_operation(resource_group_name, webapp_name, 'list_host_name_bindings',
                                   slot)

#TODO: figure out the 'configuration_source' and add related param descriptions
def create_webapp_slot(resource_group_name, webapp, slot, configuration_source=None):
    client = web_client_factory()
    site = client.web_apps.get(resource_group_name, webapp)
    location = site.location
    if configuration_source is None:
        slot_def = Site(server_farm_id=site.server_farm_id, location=location)
    elif configuration_source.lower() == webapp.lower(): #clone from production
        slot_def = site #pylint: disable=redefined-variable-type
    else: # from other slot
        slot_def = client.web_apps.get_slot(resource_group_name, webapp, slot)

    poller = client.web_apps.create_or_update_slot(resource_group_name, webapp, slot_def, slot)
    return AppServiceLongRunningOperation()(poller)


def config_source_control(resource_group_name, name, repo_url, repository_type=None, branch=None,
                          git_token=None, manual_integration=None, slot=None):
    from azure.mgmt.web.models import SiteSourceControl, SourceControl
    client = web_client_factory()
    location = _get_location_from_webapp(client, resource_group_name, name)
    if git_token:
        sc = SourceControl(location, name='GitHub', token=git_token)
        client.update_source_control('GitHub', sc)

    source_control = SiteSourceControl(location, repo_url=repo_url, branch=branch,
                                       is_manual_integration=manual_integration,
                                       is_mercurial=(repository_type != 'git'))
    return _generic_site_operation(resource_group_name, name,
                                   'create_or_update_source_control',
                                   slot, source_control)


def update_git_token(git_token=None):
    '''
    Update source control token cached in Azure app service. If no token is provided,
    the command will clean up existing token.
    '''
    client = web_client_factory()
    from azure.mgmt.web.models import SourceControl
    sc = SourceControl('not-really-needed', name='GitHub', token=git_token or '')
    return client.update_source_control('GitHub', sc)


def show_source_control(resource_group_name, name, slot=None):
    return _generic_site_operation(resource_group_name, name, 'get_source_control', slot)

def delete_source_control(resource_group_name, name, slot=None):
    return _generic_site_operation(resource_group_name, name, 'delete_source_control', slot)

def enable_local_git(resource_group_name, name, slot=None):
    client = web_client_factory()
    location = _get_location_from_webapp(client, resource_group_name, name)
    site_config = SiteConfig(location)
    site_config.scm_type = 'LocalGit'
    if slot is None:
        client.web_apps.create_or_update_configuration(resource_group_name, name, site_config)
    else:
        client.web_apps.create_or_update_configuration_slot(resource_group_name, name,
                                                            site_config, slot)

    return {'url' : _get_local_git_url(client, resource_group_name, name, slot)}

def sync_site_repo(resource_group_name, name, slot=None):
    return _generic_site_operation(resource_group_name, name, 'sync_repository',
                                   slot)

def list_app_service_plans(resource_group_name=None):
    client = web_client_factory()
    if resource_group_name is None:
        return client.app_service_plans.list()
    else:
        return client.app_service_plans.list_by_resource_group(resource_group_name)

def create_app_service_plan(resource_group_name, name, is_linux, sku='B1', number_of_workers=None,
                            location=None):
    client = web_client_factory()
    sku = _normalize_sku(sku)
    if location is None:
        location = _get_location_from_resource_group(resource_group_name)

    #the api is odd on parameter naming, have to live with it for now
    sku_def = SkuDescription(tier=_get_sku_name(sku), name=sku, capacity=number_of_workers)
    plan_def = AppServicePlan(location, app_service_plan_name=name,
                              sku=sku_def, reserved=(is_linux or None))
    poller = client.app_service_plans.create_or_update(resource_group_name, name, plan_def)
    return AppServiceLongRunningOperation(creating_plan=True)(poller)

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
    else:
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
    if slot:
        return client.web_apps.update_backup_configuration_slot(resource_group_name, webapp_name,
                                                                backup_request, slot)
    else:
        return client.web_apps.update_backup_configuration(resource_group_name, webapp_name,
                                                           backup_request)

def restore_backup(resource_group_name, webapp_name, storage_account_url, backup_name,
                   db_name=None, db_type=None, db_connection_string=None,
                   target_name=None, overwrite=None, ignore_hostname_conflict=None, slot=None):
    client = web_client_factory()
    storage_blob_name = backup_name
    if not storage_blob_name.lower().endswith('.zip'):
        storage_blob_name += '.zip'
    location = _get_location_from_webapp(client, resource_group_name, webapp_name)
    db_setting = _create_db_setting(db_name, db_type, db_connection_string)
    restore_request = RestoreRequest(location, storage_account_url=storage_account_url,
                                     blob_name=storage_blob_name, overwrite=overwrite,
                                     site_name=target_name, databases=db_setting,
                                     ignore_conflicting_host_names=ignore_hostname_conflict)
    if slot:
        return client.web_apps.restore(resource_group_name, webapp_name, 0, restore_request, slot)
    else:
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
        # pylint: disable=redefined-variable-type
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
    else:
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
    elif tier in ['P1', 'P2', 'P3']:
        return 'PREMIUM'
    else:
        raise CLIError("Invalid sku(pricing tier), please refer to command help for valid values")

def _get_location_from_resource_group(resource_group_name):
    from azure.mgmt.resource.resources import ResourceManagementClient
    client = get_mgmt_service_client(ResourceManagementClient)
    group = client.resource_groups.get(resource_group_name)
    return group.location

def _get_location_from_webapp(client, resource_group_name, webapp):
    webapp = client.web_apps.get(resource_group_name, webapp)
    return webapp.location

def _get_location_from_app_service_plan(client, resource_group_name, plan):
    plan = client.app_service_plans.get(resource_group_name, plan)
    return plan.location

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
    user = User(location='not-really-needed') #TODO: open bug for this one is not needed
    user.publishing_user_name = user_name
    if password is None:
        try:
            password = prompt_pass(msg='Password: ', confirm=True)
        except NoTTYException:
            raise CLIError('Please specify both username and password in non-interactive mode.')

    user.publishing_password = password
    result = client.update_publishing_user(user)
    return result

def view_in_browser(resource_group_name, name, slot=None):
    import webbrowser
    site = _generic_site_operation(resource_group_name, name, 'get', slot)
    url = site.default_host_name
    ssl_host = next((h for h in site.host_name_ssl_states
                     if h.ssl_state != SslState.disabled), None)
    url = ('https' if ssl_host else 'http') + '://' + url
    webbrowser.open(url, new=2) # 2 means: open in a new tab, if possible

#TODO: expose new blob suport
def config_diagnostics(resource_group_name, name, level=None,
                       application_logging=None, web_server_logging=None,
                       detailed_error_messages=None, failed_request_tracing=None,
                       slot=None):
    from azure.mgmt.web.models import (FileSystemApplicationLogsConfig, ApplicationLogsConfig,
                                       SiteLogsConfig, HttpLogsConfig,
                                       FileSystemHttpLogsConfig, EnabledConfig)
    client = web_client_factory()
    #TODO: ensure we call get_site only once
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
        #100 mb max log size, retenting last 3 days. Yes we hard code it, portal does too
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


def config_slot_auto_swap(resource_group_name, webapp, slot, auto_swap_slot=None, disable=None):
    client = web_client_factory()
    site_config = client.web_apps.get_configuration_slot(resource_group_name, webapp, slot)
    site_config.auto_swap_slot_name = '' if disable else (auto_swap_slot or 'production')
    return client.web_apps.update_configuration_slot(resource_group_name, webapp, site_config, slot)

def swap_slot(resource_group_name, webapp, slot, target_slot=None):
    client = web_client_factory()
    if target_slot is None:
        poller = client.web_apps.swap_slot_with_production(resource_group_name, webapp, slot, True)
    else:
        poller = client.web_apps.swap_slot_slot(resource_group_name, webapp,
                                                slot, target_slot, True)

    return AppServiceLongRunningOperation()(poller)

def delete_slot(resource_group_name, webapp, slot):
    client = web_client_factory()
    #TODO: once swagger finalized, expose other parameters like: delete_all_slots, etc...
    client.web_apps.delete_slot(resource_group_name, webapp, slot)

def get_streaming_log(resource_group_name, name, provider=None, slot=None):
    scm_url = _get_scm_url(resource_group_name, name, slot)
    streaming_url = scm_url + '/logstream'
    import time
    if provider:
        streaming_url += ('/' + provider.lstrip('/'))

    client = web_client_factory()
    user, password = _get_site_credential(client, resource_group_name, name)
    t = threading.Thread(target=_stream_trace, args=(streaming_url, user, password))
    t.daemon = True
    t.start()

    while True:
        time.sleep(100) #so that ctrl+c can stop the command

def download_historical_logs(resource_group_name, name, log_file=None, slot=None):
    '''
    Download historical logs as a zip file
    '''
    scm_url = _get_scm_url(resource_group_name, name, slot)
    url = scm_url.rstrip('/') + '/dump'
    import requests
    r = requests.get(url, stream=True)
    with open(log_file, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    logger.warning('Downloaded logs to %s', log_file)

def _get_site_credential(client, resource_group_name, name):
    creds = client.web_apps.list_publishing_credentials(resource_group_name, name)
    creds = creds.result()
    return (creds.publishing_user_name, creds.publishing_password)

def _stream_trace(streaming_url, user_name, password):
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
        streaming_url,
        headers=headers,
        preload_content=False
    )
    for chunk in r.stream():
        if chunk:
            # Extra encode() and decode for stdout which does not surpport 'utf-8'
            print(chunk.decode(encoding='utf-8', errors='replace')
                  .encode(std_encoding, errors='replace')
                  .decode(std_encoding, errors='replace'), end='') # each line of log has CRLF.
    r.release_conn()

def upload_ssl_cert(resource_group_name, name, certificate_password, certificate_file):
    client = web_client_factory()
    webapp = _generic_site_operation(resource_group_name, name, 'get')
    cert_file = open(certificate_file, 'rb')
    cert_contents = cert_file.read()
    hosting_environment_profile_param = webapp.hosting_environment_profile
    if hosting_environment_profile_param is None:
        hosting_environment_profile_param = ""

    thumb_print = _get_cert(certificate_password, certificate_file)
    cert_name = _generate_cert_name(thumb_print, hosting_environment_profile_param,
                                    webapp.location, resource_group_name)
    cert = Certificate(password=certificate_password, pfx_blob=cert_contents,
                       location=webapp.location)
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

def list_ssl_certs(resource_group_name):
    client = web_client_factory()
    return client.certificates.list_by_resource_group(resource_group_name)

def delete_ssl_cert(resource_group_name, name, certificate_thumbprint):
    client = web_client_factory()
    error_str_1 = "Certificate for thumbprint '{}' found, but not for webapp '{}'"
    error_str_2 = "Certificate for thumbprint '{}' not found"
    webapp_certs = client.certificates.list_by_resource_group(resource_group_name)
    for webapp_cert in webapp_certs:
        if webapp_cert.thumbprint == certificate_thumbprint:
            for hostname in webapp_cert.host_names:
                if name in hostname:
                    return client.certificates.delete(resource_group_name,
                                                      webapp_cert.name)
                raise CLIError(error_str_1.format(certificate_thumbprint, name))
            raise CLIError(error_str_2.format(certificate_thumbprint))

def _update_host_name_ssl_state(resource_group_name, webapp_name, location,
                                host_name, ssl_state, thumbprint, slot=None):
    updated_webapp = Site(host_name_ssl_states=
                          [HostNameSslState
                           (
                               name=host_name,
                               ssl_state=ssl_state,
                               thumbprint=thumbprint,
                               to_update=True
                           )
                          ],
                          location=location)
    name = '{}({})'.format(webapp_name, slot) if slot else webapp_name
    return _generic_site_operation(resource_group_name, name, 'create_or_update',
                                   slot, updated_webapp)

def _update_ssl_binding(resource_group_name, name, certificate_thumbprint, ssl_type, slot=None):
    client = web_client_factory()
    webapp = _generic_site_operation(resource_group_name, name, 'get')
    webapp_certs = client.certificates.list_by_resource_group(resource_group_name)
    for webapp_cert in webapp_certs:
        if webapp_cert.thumbprint == certificate_thumbprint:
            return _update_host_name_ssl_state(resource_group_name, name, webapp.location,
                                               webapp_cert.host_names[0], ssl_type,
                                               certificate_thumbprint, slot)
    raise CLIError("Certificate for thumbprint '{}' not found.".format(certificate_thumbprint))

def bind_ssl_cert(resource_group_name, name, certificate_thumbprint, ssl_type, slot=None):
    if ssl_type == 'SNI':
        return _update_ssl_binding(resource_group_name, name,
                                   certificate_thumbprint, SslState.sni_enabled, slot)
    else:
        return _update_ssl_binding(resource_group_name, name,
                                   certificate_thumbprint, SslState.ip_based_enabled, slot)

def unbind_ssl_cert(resource_group_name, name, certificate_thumbprint, slot=None):
    return _update_ssl_binding(resource_group_name, name,
                               certificate_thumbprint, SslState.disabled, slot)
