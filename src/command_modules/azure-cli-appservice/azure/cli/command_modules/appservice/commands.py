# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azure.cli.core.util import empty_on_404

from ._client_factory import cf_web_client, cf_plans, cf_webapps


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
    def _polish_bad_errors(ex):
        import json
        from knack.util import CLIError
        try:
            detail = json.loads(ex.response.text)['Message']
            if creating_plan:
                if 'Requested features are not supported in region' in detail:
                    detail = ("Plan with linux worker is not supported in current region. For " +
                              "supported regions, please refer to https://docs.microsoft.com/en-us/"
                              "azure/app-service-web/app-service-linux-intro")
                elif 'Not enough available reserved instance servers to satisfy' in detail:
                    detail = ("Plan with Linux worker can only be created in a group " +
                              "which has never contained a Windows worker, and vice versa. " +
                              "Please use a new resource group. Original error:" + detail)
            ex = CLIError(detail)
        except Exception:  # pylint: disable=broad-except
            pass
        raise ex
    return _polish_bad_errors


# pylint: disable=too-many-statements
def load_command_table(self, _):
    webclient_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.web.web_site_management_client#WebSiteManagementClient.{}',
        client_factory=cf_web_client
    )
    appservice_plan_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.web.operations.app_service_plans_operations#AppServicePlansOperations.{}',
        client_factory=cf_plans
    )
    webapp_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.web.operations.web_apps_operations#WebAppsOperations.{}',
        client_factory=cf_webapps
    )
    appservice_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.appservice.custom#{}')

    with self.command_group('webapp', webapp_sdk) as g:
        g.custom_command('create', 'create_webapp', exception_handler=ex_handler_factory())
        g.custom_command('list', 'list_webapp', table_transformer=transform_web_list_output)
        g.custom_show_command('show', 'show_webapp', table_transformer=transform_web_output)
        g.custom_command('delete', 'delete_webapp')
        g.custom_command('stop', 'stop_webapp')
        g.custom_command('start', 'start_webapp')
        g.custom_command('restart', 'restart_webapp')
        g.custom_command('browse', 'view_in_browser')
        g.custom_command('list-runtimes', 'list_runtimes')
        g.custom_command('identity assign', 'assign_identity')
        g.custom_command('identity show', 'show_identity')
        g.custom_command('identity remove', 'remove_identity')
        g.generic_update_command('update', getter_name='get_webapp', setter_name='set_webapp', custom_func_name='update_webapp', command_type=appservice_custom)

    with self.command_group('webapp traffic-routing') as g:
        g.custom_command('set', 'set_traffic_routing')
        g.custom_show_command('show', 'show_traffic_routing')
        g.custom_command('clear', 'clear_traffic_routing')

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
        g.custom_command('upload', 'upload_ssl_cert', exception_handler=ex_handler_factory())
        g.custom_command('list', 'list_ssl_certs')
        g.custom_command('bind', 'bind_ssl_cert', exception_handler=ex_handler_factory())
        g.custom_command('unbind', 'unbind_ssl_cert')
        g.custom_command('delete', 'delete_ssl_cert')

    with self.command_group('webapp config backup') as g:
        g.custom_command('list', 'list_backups')
        g.custom_show_command('show', 'show_backup_configuration')
        g.custom_command('create', 'create_backup', exception_handler=ex_handler_factory())
        g.custom_command('update', 'update_backup_schedule', exception_handler=ex_handler_factory())
        g.custom_command('restore', 'restore_backup', exception_handler=ex_handler_factory())

    with self.command_group('webapp deployment source') as g:
        g.custom_command('config-local-git', 'enable_local_git')
        g.custom_command('config-zip', 'enable_zip_deploy')
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

    with self.command_group('webapp deployment slot') as g:
        g.custom_command('list', 'list_slots', table_transformer=output_slots_in_table)
        g.custom_command('delete', 'delete_slot')
        g.custom_command('auto-swap', 'config_slot_auto_swap')
        g.custom_command('swap', 'swap_slot', exception_handler=ex_handler_factory())
        g.custom_command('create', 'create_webapp_slot', exception_handler=ex_handler_factory())

    with self.command_group('webapp deployment') as g:
        g.custom_command('list-publishing-profiles', 'list_publish_profiles')

    with self.command_group('webapp deployment user', webclient_sdk) as g:
        g.show_command('show', 'get_publishing_user')
        g.custom_command('set', 'set_deployment_user', exception_handler=ex_handler_factory())

    with self.command_group('webapp deployment container') as g:
        g.custom_command('config', 'enable_cd')
        g.custom_command('show-cd-url', 'show_container_cd_url')

    with self.command_group('webapp auth') as g:
        g.custom_show_command('show', 'get_auth_settings')
        g.custom_command('update', 'update_auth_settings')

    with self.command_group('appservice plan', appservice_plan_sdk) as g:
        g.custom_command('create', 'create_app_service_plan', exception_handler=ex_handler_factory(creating_plan=True))
        g.command('delete', 'delete', confirmation=True)
        g.custom_command('list', 'list_app_service_plans')
        g.show_command('show', 'get')
        g.generic_update_command('update', custom_func_name='update_app_service_plan', setter_arg_name='app_service_plan')
    with self.command_group('appservice') as g:
        g.custom_command('list-locations', 'list_locations', transform=transform_list_location_output)

    with self.command_group('functionapp') as g:
        g.custom_command('create', 'create_function')
        g.custom_command('list', 'list_function_app', table_transformer=transform_web_list_output)
        g.custom_show_command('show', 'show_webapp', table_transformer=transform_web_output)
        g.custom_command('delete', 'delete_function_app')
        g.custom_command('stop', 'stop_webapp')
        g.custom_command('start', 'start_webapp')
        g.custom_command('restart', 'restart_webapp')
        g.custom_command('list-consumption-locations', 'list_consumption_locations')
        g.custom_command('identity assign', 'assign_identity')
        g.custom_command('identity show', 'show_identity')
        g.custom_command('identity remove', 'remove_identity')
        g.generic_update_command('update', setter_name='set_functionapp', setter_type=appservice_custom, command_type=webapp_sdk)

    with self.command_group('functionapp config appsettings') as g:
        g.custom_command('list', 'get_app_settings', exception_handler=empty_on_404)
        g.custom_command('set', 'update_app_settings')
        g.custom_command('delete', 'delete_app_settings')

    with self.command_group('functionapp config hostname') as g:
        g.custom_command('add', 'add_hostname', exception_handler=ex_handler_factory())
        g.custom_command('list', 'list_hostnames')
        g.custom_command('delete', 'delete_hostname')
        g.custom_command('get-external-ip', 'get_external_ip')

    with self.command_group('functionapp config ssl') as g:
        g.custom_command('upload', 'upload_ssl_cert', exception_handler=ex_handler_factory())
        g.custom_command('list', 'list_ssl_certs')
        g.custom_command('bind', 'bind_ssl_cert', exception_handler=ex_handler_factory())
        g.custom_command('unbind', 'unbind_ssl_cert')
        g.custom_command('delete', 'delete_ssl_cert')

    with self.command_group('functionapp deployment source') as g:
        g.custom_command('config-local-git', 'enable_local_git')
        g.custom_command('config-zip', 'enable_zip_deploy')
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
