# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.application import APPLICATION
from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import cli_generic_update_command
from azure.cli.core.util import empty_on_404
from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE

from ._client_factory import cf_web_client, cf_plans, cf_webapps


def deprecate(argv):
    if len(argv) > 1 and argv[0] == 'appservice' and argv[1] == 'web':
        from azure.cli.core.util import CLIError
        raise CLIError("All 'appservice web' commands have been renamed to 'webapp'")


APPLICATION.register(APPLICATION.COMMAND_PARSER_PARSING, deprecate)


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
        from azure.cli.core.util import CLIError
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


custom_path = 'azure.cli.command_modules.appservice.custom#'

cli_command(__name__, 'webapp create', custom_path + 'create_webapp', exception_handler=ex_handler_factory())
cli_command(__name__, 'webapp list', custom_path + 'list_webapp', table_transformer=transform_web_list_output)
cli_command(__name__, 'webapp show', custom_path + 'show_webapp', exception_handler=empty_on_404, table_transformer=transform_web_output)
cli_command(__name__, 'webapp delete', custom_path + 'delete_webapp')
cli_command(__name__, 'webapp stop', custom_path + 'stop_webapp')
cli_command(__name__, 'webapp start', custom_path + 'start_webapp')
cli_command(__name__, 'webapp restart', custom_path + 'restart_webapp')
cli_generic_update_command(__name__, 'webapp update', 'azure.mgmt.web.operations.web_apps_operations#WebAppsOperations.get',
                           'azure.mgmt.web.operations.web_apps_operations#WebAppsOperations.create_or_update',
                           custom_function_op=custom_path + 'update_webapp',
                           setter_arg_name='site_envelope', factory=cf_webapps)

cli_command(__name__, 'webapp traffic-routing set', custom_path + 'set_traffic_routing')
cli_command(__name__, 'webapp traffic-routing show', custom_path + 'show_traffic_routing')
cli_command(__name__, 'webapp traffic-routing clear', custom_path + 'clear_traffic_routing')

cli_command(__name__, 'webapp config set', custom_path + 'update_site_configs')
cli_command(__name__, 'webapp config show', custom_path + 'get_site_configs', exception_handler=empty_on_404)
cli_command(__name__, 'webapp config appsettings list', custom_path + 'get_app_settings', exception_handler=empty_on_404)
cli_command(__name__, 'webapp config appsettings set', custom_path + 'update_app_settings')
cli_command(__name__, 'webapp config appsettings delete', custom_path + 'delete_app_settings')
cli_command(__name__, 'webapp config connection-string list', custom_path + 'get_connection_strings', exception_handler=empty_on_404)
cli_command(__name__, 'webapp config connection-string set', custom_path + 'update_connection_strings')
cli_command(__name__, 'webapp config connection-string delete', custom_path + 'delete_connection_strings')

cli_command(__name__, 'webapp config hostname add', custom_path + 'add_hostname', exception_handler=ex_handler_factory())
cli_command(__name__, 'webapp config hostname list', custom_path + 'list_hostnames')
cli_command(__name__, 'webapp config hostname delete', custom_path + 'delete_hostname')
cli_command(__name__, 'webapp config hostname get-external-ip', custom_path + 'get_external_ip')
cli_command(__name__, 'webapp config container set', custom_path + 'update_container_settings')
cli_command(__name__, 'webapp config container delete', custom_path + 'delete_container_settings')
cli_command(__name__, 'webapp config container show', custom_path + 'show_container_settings', exception_handler=empty_on_404)

cli_command(__name__, 'webapp config ssl upload', custom_path + 'upload_ssl_cert', exception_handler=ex_handler_factory())
cli_command(__name__, 'webapp config ssl list', custom_path + 'list_ssl_certs')
cli_command(__name__, 'webapp config ssl bind', custom_path + 'bind_ssl_cert', exception_handler=ex_handler_factory())
cli_command(__name__, 'webapp config ssl unbind', custom_path + 'unbind_ssl_cert')
cli_command(__name__, 'webapp config ssl delete', custom_path + 'delete_ssl_cert')

cli_command(__name__, 'webapp config backup list', custom_path + 'list_backups')
cli_command(__name__, 'webapp config backup show', custom_path + 'show_backup_configuration', exception_handler=empty_on_404)
cli_command(__name__, 'webapp config backup create', custom_path + 'create_backup', exception_handler=ex_handler_factory())
cli_command(__name__, 'webapp config backup update', custom_path + 'update_backup_schedule', exception_handler=ex_handler_factory())
cli_command(__name__, 'webapp config backup restore', custom_path + 'restore_backup', exception_handler=ex_handler_factory())

cli_command(__name__, 'webapp deployment source config-local-git', custom_path + 'enable_local_git')
cli_command(__name__, 'webapp deployment source config', custom_path + 'config_source_control', exception_handler=ex_handler_factory())
cli_command(__name__, 'webapp deployment source sync', custom_path + 'sync_site_repo', exception_handler=ex_handler_factory())
cli_command(__name__, 'webapp deployment source show', custom_path + 'show_source_control', exception_handler=empty_on_404)
cli_command(__name__, 'webapp deployment source delete', custom_path + 'delete_source_control')
cli_command(__name__, 'webapp deployment source update-token', custom_path + 'update_git_token', exception_handler=ex_handler_factory())

cli_command(__name__, 'webapp log tail', custom_path + 'get_streaming_log')
cli_command(__name__, 'webapp log download', custom_path + 'download_historical_logs')
cli_command(__name__, 'webapp log config', custom_path + 'config_diagnostics')
cli_command(__name__, 'webapp log show', custom_path + 'show_diagnostic_settings')
cli_command(__name__, 'webapp browse', custom_path + 'view_in_browser')

cli_command(__name__, 'webapp deployment slot list', custom_path + 'list_slots', table_transformer=output_slots_in_table)
cli_command(__name__, 'webapp deployment slot delete', custom_path + 'delete_slot')
cli_command(__name__, 'webapp deployment slot auto-swap', custom_path + 'config_slot_auto_swap')
cli_command(__name__, 'webapp deployment slot swap', custom_path + 'swap_slot', exception_handler=ex_handler_factory())
cli_command(__name__, 'webapp deployment slot create', custom_path + 'create_webapp_slot', exception_handler=ex_handler_factory())

cli_command(__name__, 'webapp deployment user set', custom_path + 'set_deployment_user')
cli_command(__name__, 'webapp deployment list-publishing-profiles',
            custom_path + 'list_publish_profiles')
cli_command(__name__, 'webapp deployment container config',
            custom_path + 'enable_cd')
cli_command(__name__, 'webapp deployment container show-cd-url',
            custom_path + 'show_container_cd_url')
cli_command(__name__, 'webapp deployment user show', 'azure.mgmt.web.web_site_management_client#WebSiteManagementClient.get_publishing_user', cf_web_client, exception_handler=empty_on_404)
cli_command(__name__, 'webapp list-runtimes', custom_path + 'list_runtimes')

cli_command(__name__, 'webapp auth show', custom_path + 'get_auth_settings')
cli_command(__name__, 'webapp auth update', custom_path + 'update_auth_settings')


if not supported_api_version(PROFILE_TYPE, max_api='2017-03-09-profile'):
    cli_command(__name__, 'appservice plan create', custom_path + 'create_app_service_plan', exception_handler=ex_handler_factory(creating_plan=True))
    cli_command(__name__, 'appservice plan delete', 'azure.mgmt.web.operations.app_service_plans_operations#AppServicePlansOperations.delete', cf_plans, confirmation=True)
    cli_command(__name__, 'appservice plan list', custom_path + 'list_app_service_plans')
    cli_command(__name__, 'appservice plan show', 'azure.mgmt.web.operations.app_service_plans_operations#AppServicePlansOperations.get', cf_plans, exception_handler=empty_on_404)
    cli_generic_update_command(__name__, 'appservice plan update', 'azure.mgmt.web.operations.app_service_plans_operations#AppServicePlansOperations.get',
                               'azure.mgmt.web.operations.app_service_plans_operations#AppServicePlansOperations.create_or_update',
                               custom_function_op=custom_path + 'update_app_service_plan',
                               setter_arg_name='app_service_plan', factory=cf_plans)
    cli_command(__name__, 'appservice list-locations', 'azure.mgmt.web.web_site_management_client#WebSiteManagementClient.list_geo_regions', cf_web_client, transform=transform_list_location_output)

    cli_command(__name__, 'functionapp create', custom_path + 'create_function')
    cli_command(__name__, 'functionapp list', custom_path + 'list_function_app', table_transformer=transform_web_list_output)
    cli_command(__name__, 'functionapp show', custom_path + 'show_webapp', exception_handler=empty_on_404, table_transformer=transform_web_output)
    cli_command(__name__, 'functionapp delete', custom_path + 'delete_function_app')
    cli_command(__name__, 'functionapp stop', custom_path + 'stop_webapp')
    cli_command(__name__, 'functionapp start', custom_path + 'start_webapp')
    cli_command(__name__, 'functionapp restart', custom_path + 'restart_webapp')
    cli_command(__name__, 'functionapp list-consumption-locations', custom_path + 'list_consumption_locations')
    cli_command(__name__, 'functionapp config appsettings list', custom_path + 'get_app_settings', exception_handler=empty_on_404)
    cli_command(__name__, 'functionapp config appsettings set', custom_path + 'update_app_settings')
    cli_command(__name__, 'functionapp config appsettings delete', custom_path + 'delete_app_settings')
    cli_command(__name__, 'functionapp config hostname add', custom_path + 'add_hostname', exception_handler=ex_handler_factory())
    cli_command(__name__, 'functionapp config hostname list', custom_path + 'list_hostnames')
    cli_command(__name__, 'functionapp config hostname delete', custom_path + 'delete_hostname')
    cli_command(__name__, 'functionapp config hostname get-external-ip', custom_path + 'get_external_ip')
    cli_command(__name__, 'functionapp config ssl upload', custom_path + 'upload_ssl_cert', exception_handler=ex_handler_factory())
    cli_command(__name__, 'functionapp config ssl list', custom_path + 'list_ssl_certs')
    cli_command(__name__, 'functionapp config ssl bind', custom_path + 'bind_ssl_cert', exception_handler=ex_handler_factory())
    cli_command(__name__, 'functionapp config ssl unbind', custom_path + 'unbind_ssl_cert')
    cli_command(__name__, 'functionapp config ssl delete', custom_path + 'delete_ssl_cert')
    cli_command(__name__, 'functionapp deployment source config-local-git', custom_path + 'enable_local_git')
    cli_command(__name__, 'functionapp deployment source config', custom_path + 'config_source_control', exception_handler=ex_handler_factory())
    cli_command(__name__, 'functionapp deployment source sync', custom_path + 'sync_site_repo')
    cli_command(__name__, 'functionapp deployment source show', custom_path + 'show_source_control', exception_handler=empty_on_404)
    cli_command(__name__, 'functionapp deployment source delete', custom_path + 'delete_source_control')
    cli_command(__name__, 'functionapp deployment source update-token', custom_path + 'update_git_token', exception_handler=ex_handler_factory())
    cli_command(__name__, 'functionapp deployment user set', custom_path + 'set_deployment_user')
    cli_command(__name__, 'functionapp deployment list-publishing-profiles',
                custom_path + 'list_publish_profiles')
    cli_command(__name__, 'functionapp deployment user show', 'azure.mgmt.web.web_site_management_client#WebSiteManagementClient.get_publishing_user', cf_web_client, exception_handler=empty_on_404)
