# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azure.cli.core.util import empty_on_404

from ._client_factory import cf_web_client, cf_plans, cf_webapps
from ._validators import (validate_onedeploy_params, validate_staticsite_link_function, validate_staticsite_sku,
                          validate_vnet_integration, validate_asp_create, validate_functionapp_asp_create)


def output_slots_in_table(slots):
    return [{'name': s['name'], 'status': s['state'], 'plan': s['appServicePlan']} for s in slots]


def transform_list_location_output(result):
    return [{'name': x.name} for x in result]


def transform_web_output(web):
    props = ['name', 'state', 'location', 'resourceGroup', 'defaultHostName', 'appServicePlanId', 'ftpPublishingUrl']
    result = {k: web[k] for k in web if k in props}
    # to get width under control, also the plan usually is in the same RG
    result['appServicePlan'] = result.pop('appServicePlanId').split('/')[-1]
    return result


def transform_web_list_output(webs):
    return [transform_web_output(w) for w in webs]


def ex_handler_factory(creating_plan=False):
    def _ex_handler(ex):
        ex = _polish_bad_errors(ex, creating_plan)
        raise ex
    return _ex_handler


def update_function_ex_handler_factory():
    from azure.cli.core.azclierror import ClientRequestError

    def _ex_handler(ex):
        http_error_response = False
        if hasattr(ex, 'response'):
            http_error_response = True
        ex = _polish_bad_errors(ex, False)
        # only include if an update was attempted and failed on the backend
        if http_error_response:
            try:
                detail = ('If using \'--plan\', a consumption plan may be unable to migrate '
                          'to a given premium plan. Please confirm that the premium plan '
                          'exists in the same resource group and region. Note: Not all '
                          'functionapp plans support premium instances. If you have verified '
                          'your resource group and region and are still unable to migrate, '
                          'please redeploy on a premium functionapp plan.')
                ex = ClientRequestError(ex.args[0] + '\n\n' + detail)
            except Exception:  # pylint: disable=broad-except
                pass
        raise ex
    return _ex_handler


def _polish_bad_errors(ex, creating_plan):
    import json
    from knack.util import CLIError
    try:
        if hasattr(ex, "response"):
            if 'text/plain' in ex.response.headers['Content-Type']:  # HTML Response
                detail = ex.response.text
            else:
                detail = json.loads(ex.response.text())['Message']
                if creating_plan:
                    if 'Requested features are not supported in region' in detail:
                        detail = ("Plan with requested features is not supported in current region. \n"
                                  "If creating an App Service Plan with --zone-redundant/-z, "
                                  "please see supported regions here: "
                                  "https://docs.microsoft.com/en-us/azure/app-service/how-to-zone-redundancy#requirements")
                    elif 'Not enough available reserved instance servers to satisfy' in detail:
                        detail = ("Plan with Linux worker can only be created in a group " +
                                  "which has never contained a Windows worker, and vice versa. " +
                                  "Please use a new resource group. Original error:" + detail)
        else:
            detail = json.loads(ex.error_msg.response.text())['Message']
        ex = CLIError(detail)
    except Exception:  # pylint: disable=broad-except
        pass
    return ex


# pylint: disable=too-many-statements
def load_command_table(self, _):
    webclient_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.web.operations#WebSiteManagementClientOperationsMixin.{}',
        client_factory=cf_web_client
    )
    appservice_plan_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.web.operations#AppServicePlansOperations.{}',
        client_factory=cf_plans
    )
    webapp_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.web.operations#WebAppsOperations.{}',
        client_factory=cf_webapps
    )

    appservice_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.appservice.custom#{}')

    webapp_access_restrictions = CliCommandType(operations_tmpl='azure.cli.command_modules.appservice.access_restrictions#{}')

    appservice_environment = CliCommandType(operations_tmpl='azure.cli.command_modules.appservice.appservice_environment#{}')

    staticsite_sdk = CliCommandType(operations_tmpl='azure.cli.command_modules.appservice.static_sites#{}')

    appservice_domains = CliCommandType(operations_tmpl='azure.cli.command_modules.appservice.appservice_domains#{}')

    logicapp_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.appservice.logicapp.custom#{}')

    with self.command_group('webapp', webapp_sdk) as g:
        g.custom_command('create', 'create_webapp', exception_handler=ex_handler_factory(), validator=validate_vnet_integration)
        g.custom_command('up', 'webapp_up', exception_handler=ex_handler_factory())
        g.custom_command('ssh', 'ssh_webapp', exception_handler=ex_handler_factory(), is_preview=True)
        g.custom_command('list', 'list_webapp', table_transformer=transform_web_list_output)
        g.custom_show_command('show', 'show_webapp', table_transformer=transform_web_output)
        g.custom_command('delete', 'delete_webapp')
        g.custom_command('stop', 'stop_webapp')
        g.custom_command('start', 'start_webapp')
        g.custom_command('restart', 'restart_webapp')
        g.custom_command('browse', 'view_in_browser')
        g.custom_command('list-instances', 'list_instances')
        g.custom_command('list-runtimes', 'list_runtimes')
        g.custom_command('identity assign', 'assign_identity')
        g.custom_show_command('identity show', 'show_identity')
        g.custom_command('identity remove', 'remove_identity')
        g.custom_command('create-remote-connection', 'create_tunnel', exception_handler=ex_handler_factory())
        g.custom_command('deploy', 'perform_onedeploy', validator=validate_onedeploy_params, is_preview=True)
        g.generic_update_command('update', getter_name='get_webapp', setter_name='set_webapp',
                                 custom_func_name='update_webapp', command_type=appservice_custom)

    with self.command_group('webapp traffic-routing') as g:
        g.custom_command('set', 'set_traffic_routing')
        g.custom_show_command('show', 'show_traffic_routing')
        g.custom_command('clear', 'clear_traffic_routing')

    with self.command_group('webapp cors') as g:
        g.custom_command('add', 'add_cors')
        g.custom_command('remove', 'remove_cors')
        g.custom_show_command('show', 'show_cors')

    with self.command_group('webapp config') as g:
        g.custom_command('set', 'update_site_configs')
        g.custom_show_command('show', 'get_site_configs')

    with self.command_group('webapp config appsettings') as g:
        g.custom_command('list', 'get_app_settings', exception_handler=empty_on_404)
        g.custom_command('set', 'update_app_settings')
        g.custom_command('delete', 'delete_app_settings')

    with self.command_group('webapp config connection-string') as g:
        g.custom_command('list', 'get_connection_strings', exception_handler=empty_on_404)
        g.custom_command('set', 'update_connection_strings')
        g.custom_command('delete', 'delete_connection_strings')

    with self.command_group('webapp config storage-account') as g:
        g.custom_command('list', 'get_azure_storage_accounts', exception_handler=empty_on_404)
        g.custom_command('add', 'add_azure_storage_account')
        g.custom_command('update', 'update_azure_storage_account')
        g.custom_command('delete', 'delete_azure_storage_accounts')

    with self.command_group('webapp config hostname') as g:
        g.custom_command('add', 'add_hostname', exception_handler=ex_handler_factory())
        g.custom_command('list', 'list_hostnames')
        g.custom_command('delete', 'delete_hostname')
        g.custom_command('get-external-ip', 'get_external_ip')

    with self.command_group('webapp config container') as g:
        g.custom_command('set', 'update_container_settings')
        g.custom_command('delete', 'delete_container_settings')
        g.custom_show_command('show', 'show_container_settings')

    with self.command_group('webapp config ssl') as g:
        g.custom_command('upload', 'upload_ssl_cert')
        g.custom_command('list', 'list_ssl_certs', exception_handler=ex_handler_factory())
        g.custom_show_command('show', 'show_ssl_cert', exception_handler=ex_handler_factory())
        g.custom_command('bind', 'bind_ssl_cert', exception_handler=ex_handler_factory())
        g.custom_command('unbind', 'unbind_ssl_cert')
        g.custom_command('delete', 'delete_ssl_cert', exception_handler=ex_handler_factory())
        g.custom_command('import', 'import_ssl_cert', exception_handler=ex_handler_factory())
        g.custom_command('create', 'create_managed_ssl_cert', exception_handler=ex_handler_factory(), is_preview=True)

    with self.command_group('webapp config backup') as g:
        g.custom_command('list', 'list_backups')
        g.custom_show_command('show', 'show_backup_configuration')
        g.custom_command('create', 'create_backup', exception_handler=ex_handler_factory())
        g.custom_command('update', 'update_backup_schedule', exception_handler=ex_handler_factory())
        g.custom_command('restore', 'restore_backup', exception_handler=ex_handler_factory())

    with self.command_group('webapp config snapshot') as g:
        g.custom_command('list', 'list_snapshots')
        g.custom_command('restore', 'restore_snapshot')

    with self.command_group('webapp webjob continuous') as g:
        g.custom_command('list', 'list_continuous_webjobs', exception_handler=ex_handler_factory())
        g.custom_command('remove', 'remove_continuous_webjob', exception_handler=ex_handler_factory())
        g.custom_command('start', 'start_continuous_webjob', exception_handler=ex_handler_factory())
        g.custom_command('stop', 'stop_continuous_webjob', exception_handler=ex_handler_factory())

    with self.command_group('webapp webjob triggered') as g:
        g.custom_command('list', 'list_triggered_webjobs', exception_handler=ex_handler_factory())
        g.custom_command('remove', 'remove_triggered_webjob', exception_handler=ex_handler_factory())
        g.custom_command('run', 'run_triggered_webjob', exception_handler=ex_handler_factory())
        g.custom_command('log', 'get_history_triggered_webjob', exception_handler=ex_handler_factory())

    with self.command_group('webapp deployment source') as g:
        g.custom_command('config-local-git', 'enable_local_git')
        g.custom_command('config-zip', 'enable_zip_deploy_webapp')
        g.custom_command('config', 'config_source_control', exception_handler=ex_handler_factory())
        g.custom_command('sync', 'sync_site_repo', exception_handler=ex_handler_factory())
        g.custom_show_command('show', 'show_source_control')
        g.custom_command('delete', 'delete_source_control')
        g.custom_command('update-token', 'update_git_token', exception_handler=ex_handler_factory())

    with self.command_group('webapp log') as g:
        g.custom_command('tail', 'get_streaming_log')
        g.custom_command('download', 'download_historical_logs')
        g.custom_command('config', 'config_diagnostics')
        g.custom_show_command('show', 'show_diagnostic_settings')

    with self.command_group('webapp log deployment', is_preview=True) as g:
        g.custom_show_command('show', 'show_deployment_log')
        g.custom_command('list', 'list_deployment_logs')

    with self.command_group('functionapp log deployment', is_preview=True) as g:
        g.custom_show_command('show', 'show_deployment_log')
        g.custom_command('list', 'list_deployment_logs')

    with self.command_group('webapp deployment slot') as g:
        g.custom_command('list', 'list_slots', table_transformer=output_slots_in_table)
        g.custom_command('delete', 'delete_slot')
        g.custom_command('auto-swap', 'config_slot_auto_swap')
        g.custom_command('swap', 'swap_slot', exception_handler=ex_handler_factory())
        g.custom_command('create', 'create_webapp_slot', exception_handler=ex_handler_factory())

    with self.command_group('webapp deployment') as g:
        g.custom_command('list-publishing-profiles', 'list_publish_profiles')
        g.custom_command('list-publishing-credentials', 'list_publishing_credentials')

    with self.command_group('webapp deployment user', webclient_sdk) as g:
        g.custom_show_command('show', 'get_publishing_user')
        g.custom_command('set', 'set_deployment_user', exception_handler=ex_handler_factory())

    with self.command_group('webapp deployment container') as g:
        g.custom_command('config', 'enable_cd')
        g.custom_command('show-cd-url', 'show_container_cd_url')

    with self.command_group('webapp deployment github-actions', is_preview=True) as g:
        g.custom_command('add', 'add_github_actions')
        g.custom_command('remove', 'remove_github_actions')

    with self.command_group('webapp auth') as g:
        g.custom_show_command('show', 'get_auth_settings')
        g.custom_command('update', 'update_auth_settings')

    with self.command_group('webapp deleted', is_preview=True) as g:
        g.custom_command('list', 'list_deleted_webapp')
        g.custom_command('restore', 'restore_deleted_webapp')

    with self.command_group('webapp hybrid-connection') as g:
        g.custom_command('list', 'list_hc')
        g.custom_command('add', 'add_hc')
        g.custom_command('remove', 'remove_hc')

    with self.command_group('functionapp hybrid-connection') as g:
        g.custom_command('list', 'list_hc')
        g.custom_command('add', 'add_hc')
        g.custom_command('remove', 'remove_hc')

    with self.command_group('appservice hybrid-connection') as g:
        g.custom_command('set-key', 'set_hc_key')

    with self.command_group('webapp vnet-integration') as g:
        g.custom_command('add', 'add_webapp_vnet_integration')
        g.custom_command('list', 'list_vnet_integration')
        g.custom_command('remove', 'remove_vnet_integration')

    with self.command_group('functionapp vnet-integration') as g:
        g.custom_command('add', 'add_functionapp_vnet_integration')
        g.custom_command('list', 'list_vnet_integration')
        g.custom_command('remove', 'remove_vnet_integration')

    with self.command_group('appservice plan', appservice_plan_sdk) as g:
        g.custom_command('create', 'create_app_service_plan', supports_no_wait=True,
                         exception_handler=ex_handler_factory(creating_plan=True), validator=validate_asp_create)
        g.command('delete', 'delete', confirmation=True)
        g.custom_command('list', 'list_app_service_plans')
        g.custom_show_command('show', 'show_plan')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_app_service_plan',
                                 setter_arg_name='app_service_plan', supports_no_wait=True,
                                 exception_handler=ex_handler_factory())

    with self.command_group('appservice') as g:
        g.custom_command('list-locations', 'list_locations', transform=transform_list_location_output)

    with self.command_group('appservice vnet-integration') as g:
        g.custom_command('list', 'appservice_list_vnet')

    with self.command_group('functionapp') as g:
        g.custom_command('create', 'create_functionapp', exception_handler=ex_handler_factory(),
                         validator=validate_vnet_integration)
        g.custom_command('list-runtimes', 'list_function_app_runtimes')
        g.custom_command('list', 'list_function_app', table_transformer=transform_web_list_output)
        g.custom_show_command('show', 'show_functionapp', table_transformer=transform_web_output)
        g.custom_command('delete', 'delete_function_app')
        g.custom_command('stop', 'stop_webapp')
        g.custom_command('start', 'start_webapp')
        g.custom_command('restart', 'restart_webapp')
        g.custom_command('list-consumption-locations', 'list_consumption_locations')
        g.custom_command('identity assign', 'assign_identity')
        g.custom_show_command('identity show', 'show_identity')
        g.custom_command('identity remove', 'remove_identity')
        g.custom_command('deploy', 'perform_onedeploy', validator=validate_onedeploy_params, is_preview=True)
        g.generic_update_command('update', getter_name="get_functionapp", setter_name='set_functionapp', exception_handler=update_function_ex_handler_factory(),
                                 custom_func_name='update_functionapp', getter_type=appservice_custom, setter_type=appservice_custom, command_type=webapp_sdk)

    with self.command_group('functionapp config') as g:
        g.custom_command('set', 'update_site_configs')
        g.custom_show_command('show', 'get_site_configs')

    with self.command_group('functionapp config appsettings') as g:
        g.custom_command('list', 'get_app_settings', exception_handler=empty_on_404)
        g.custom_command('set', 'update_app_settings', exception_handler=ex_handler_factory())
        g.custom_command('delete', 'delete_app_settings', exception_handler=ex_handler_factory())

    with self.command_group('functionapp config hostname') as g:
        g.custom_command('add', 'add_hostname', exception_handler=ex_handler_factory())
        g.custom_command('list', 'list_hostnames')
        g.custom_command('delete', 'delete_hostname')
        g.custom_command('get-external-ip', 'get_external_ip')

    with self.command_group('functionapp config ssl') as g:
        g.custom_command('upload', 'upload_ssl_cert', exception_handler=ex_handler_factory())
        g.custom_command('list', 'list_ssl_certs')
        g.custom_show_command('show', 'show_ssl_cert')
        g.custom_command('bind', 'bind_ssl_cert', exception_handler=ex_handler_factory())
        g.custom_command('unbind', 'unbind_ssl_cert')
        g.custom_command('delete', 'delete_ssl_cert')
        g.custom_command('import', 'import_ssl_cert', exception_handler=ex_handler_factory())
        g.custom_command('create', 'create_managed_ssl_cert', exception_handler=ex_handler_factory(), is_preview=True)

    with self.command_group('functionapp deployment source') as g:
        g.custom_command('config-local-git', 'enable_local_git')
        g.custom_command('config-zip', 'enable_zip_deploy_functionapp')
        g.custom_command('config', 'config_source_control', exception_handler=ex_handler_factory())
        g.custom_command('sync', 'sync_site_repo')
        g.custom_show_command('show', 'show_source_control')
        g.custom_command('delete', 'delete_source_control')
        g.custom_command('update-token', 'update_git_token', exception_handler=ex_handler_factory())

    with self.command_group('functionapp deployment user', webclient_sdk) as g:
        g.custom_command('set', 'set_deployment_user', exception_handler=ex_handler_factory())
        g.show_command('show', 'get_publishing_user')

    with self.command_group('functionapp deployment') as g:
        g.custom_command('list-publishing-profiles', 'list_publish_profiles')
        g.custom_command('list-publishing-credentials', 'list_publishing_credentials')

    with self.command_group('functionapp cors') as g:
        g.custom_command('add', 'add_cors')
        g.custom_command('remove', 'remove_cors')
        g.custom_show_command('show', 'show_cors')

    with self.command_group('functionapp plan', appservice_plan_sdk) as g:
        g.custom_command('create', 'create_functionapp_app_service_plan',
                         exception_handler=ex_handler_factory(creating_plan=True),
                         validator=validate_functionapp_asp_create)
        g.generic_update_command('update', setter_name='begin_create_or_update',
                                 custom_func_name='update_functionapp_app_service_plan',
                                 setter_arg_name='app_service_plan', exception_handler=ex_handler_factory())
        g.command('delete', 'delete', confirmation=True)
        g.custom_command('list', 'list_app_service_plans')
        g.show_command('show', 'get')

    with self.command_group('functionapp deployment container') as g:
        g.custom_command('config', 'enable_cd')
        g.custom_command('show-cd-url', 'show_container_cd_url')

    with self.command_group('functionapp config container') as g:
        g.custom_command('set', 'update_container_settings_functionapp')
        g.custom_command('delete', 'delete_container_settings')
        g.custom_show_command('show', 'show_container_settings_functionapp')

    with self.command_group('functionapp deployment slot') as g:
        g.custom_command('list', 'list_slots', table_transformer=output_slots_in_table)
        g.custom_command('delete', 'delete_slot')
        g.custom_command('auto-swap', 'config_slot_auto_swap')
        g.custom_command('swap', 'swap_slot', exception_handler=ex_handler_factory())
        g.custom_command('create', 'create_functionapp_slot', exception_handler=ex_handler_factory())

    with self.command_group('functionapp keys') as g:
        g.custom_command('set', 'update_host_key')
        g.custom_command('list', 'list_host_keys')
        g.custom_command('delete', 'delete_host_key')

    with self.command_group('functionapp function') as g:
        g.custom_command('show', 'show_function')  # pylint: disable=show-command
        g.custom_command('delete', 'delete_function')

    with self.command_group('functionapp function keys') as g:
        g.custom_command('set', 'update_function_key')
        g.custom_command('list', 'list_function_keys')
        g.custom_command('delete', 'delete_function_key')

    with self.command_group('webapp config access-restriction', custom_command_type=webapp_access_restrictions) as g:
        g.custom_show_command('show', 'show_webapp_access_restrictions')
        g.custom_command('add', 'add_webapp_access_restriction')
        g.custom_command('remove', 'remove_webapp_access_restriction')
        g.custom_command('set', 'set_webapp_access_restriction')

    with self.command_group('functionapp config access-restriction', custom_command_type=webapp_access_restrictions) as g:
        g.custom_show_command('show', 'show_webapp_access_restrictions')
        g.custom_command('add', 'add_webapp_access_restriction')
        g.custom_command('remove', 'remove_webapp_access_restriction')
        g.custom_command('set', 'set_webapp_access_restriction')

    with self.command_group('appservice ase', custom_command_type=appservice_environment) as g:
        g.custom_command('list', 'list_appserviceenvironments')
        g.custom_command('list-addresses', 'list_appserviceenvironment_addresses')
        g.custom_command('list-plans', 'list_appserviceenvironment_plans')
        g.custom_show_command('show', 'show_appserviceenvironment')
        g.custom_command('create', 'create_appserviceenvironment_arm', supports_no_wait=True)
        g.custom_command('update', 'update_appserviceenvironment', supports_no_wait=True)
        g.custom_command('delete', 'delete_appserviceenvironment', supports_no_wait=True, confirmation=True)
        g.custom_command('create-inbound-services', 'create_ase_inbound_services', is_preview=True)

    with self.command_group('appservice domain', custom_command_type=appservice_domains, is_preview=True) as g:
        g.custom_command('create', 'create_domain')
        g.custom_command('show-terms', 'show_domain_purchase_terms')

    with self.command_group('staticwebapp', custom_command_type=staticsite_sdk) as g:
        g.custom_command('list', 'list_staticsites')
        g.custom_show_command('show', 'show_staticsite')
        g.custom_command('create', 'create_staticsites', supports_no_wait=True)
        g.custom_command('delete', 'delete_staticsite', supports_no_wait=True, confirmation=True)
        g.custom_command('disconnect', 'disconnect_staticsite', supports_no_wait=True)
        g.custom_command('reconnect', 'reconnect_staticsite', supports_no_wait=True)
        g.custom_command('update', 'update_staticsite', supports_no_wait=True)

    with self.command_group('staticwebapp environment', custom_command_type=staticsite_sdk) as g:
        g.custom_command('list', 'list_staticsite_environments')
        g.custom_show_command('show', 'show_staticsite_environment')
        g.custom_command('functions', 'list_staticsite_functions')
        g.custom_command('delete', 'delete_staticsite_environment', confirmation=True)

    with self.command_group('staticwebapp hostname', custom_command_type=staticsite_sdk) as g:
        g.custom_command('list', 'list_staticsite_domains')
        g.custom_command('set', 'set_staticsite_domain', supports_no_wait=True)
        g.custom_command('delete', 'delete_staticsite_domain', supports_no_wait=True, confirmation=True)
        g.custom_show_command('show', 'get_staticsite_domain')

    with self.command_group('staticwebapp identity', custom_command_type=staticsite_sdk) as g:
        g.custom_command('assign', 'assign_identity')
        g.custom_command('remove', 'remove_identity', confirmation=True)
        g.custom_show_command('show', 'show_identity')

    with self.command_group('staticwebapp appsettings', custom_command_type=staticsite_sdk) as g:
        g.custom_command('list', 'list_staticsite_app_settings')
        g.custom_command('set', 'set_staticsite_app_settings')
        g.custom_command('delete', 'delete_staticsite_app_settings')

    with self.command_group('staticwebapp users', custom_command_type=staticsite_sdk) as g:
        g.custom_command('list', 'list_staticsite_users')
        g.custom_command('invite', 'invite_staticsite_users')
        g.custom_command('update', 'update_staticsite_users')

    with self.command_group('staticwebapp secrets', custom_command_type=staticsite_sdk) as g:
        g.custom_command('list', 'list_staticsite_secrets')
        g.custom_command('reset-api-key', 'reset_staticsite_api_key', supports_no_wait=True)

    with self.command_group('staticwebapp functions', custom_command_type=staticsite_sdk) as g:
        g.custom_command('link', 'link_user_function', validator=validate_staticsite_link_function)
        g.custom_command('unlink', 'unlink_user_function', validator=validate_staticsite_sku)
        g.custom_show_command('show', 'get_user_function', validator=validate_staticsite_sku)

    with self.command_group('logicapp') as g:
        g.custom_command('delete', 'delete_function_app', confirmation=True)
        g.custom_command('stop', 'stop_webapp')
        g.custom_command('start', 'start_webapp')
        g.custom_command('restart', 'restart_webapp')

    with self.command_group('logicapp', custom_command_type=logicapp_custom) as g:
        g.custom_command('create', 'create_logicapp', exception_handler=ex_handler_factory())
        g.custom_command('list', 'list_logicapp', table_transformer=transform_web_list_output)
        g.custom_show_command('show', 'show_logicapp', table_transformer=transform_web_output)
