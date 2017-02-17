# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=unused-import,line-too-long
from azure.cli.core.commands import LongRunningOperation, cli_command
from azure.cli.core.commands.arm import cli_generic_update_command
from azure.cli.core._util import empty_on_404

from ._client_factory import web_client_factory

cli_command(__name__, 'appservice web create', 'azure.cli.command_modules.appservice.custom#create_webapp')
cli_command(__name__, 'appservice web list', 'azure.cli.command_modules.appservice.custom#list_webapp')
cli_command(__name__, 'appservice web show', 'azure.cli.command_modules.appservice.custom#show_webapp', exception_handler=empty_on_404)
cli_command(__name__, 'appservice web delete', 'azure.cli.command_modules.appservice.custom#delete_webapp')
cli_command(__name__, 'appservice web stop', 'azure.cli.command_modules.appservice.custom#stop_webapp')
cli_command(__name__, 'appservice web start', 'azure.cli.command_modules.appservice.custom#start_webapp')
cli_command(__name__, 'appservice web restart', 'azure.cli.command_modules.appservice.custom#restart_webapp')

cli_command(__name__, 'appservice web config update', 'azure.cli.command_modules.appservice.custom#update_site_configs')
cli_command(__name__, 'appservice web config show', 'azure.cli.command_modules.appservice.custom#get_site_configs', exception_handler=empty_on_404)
cli_command(__name__, 'appservice web config appsettings show', 'azure.cli.command_modules.appservice.custom#get_app_settings', exception_handler=empty_on_404)
cli_command(__name__, 'appservice web config appsettings update', 'azure.cli.command_modules.appservice.custom#update_app_settings')
cli_command(__name__, 'appservice web config appsettings delete', 'azure.cli.command_modules.appservice.custom#delete_app_settings')
cli_command(__name__, 'appservice web config hostname add', 'azure.cli.command_modules.appservice.custom#add_hostname')
cli_command(__name__, 'appservice web config hostname list', 'azure.cli.command_modules.appservice.custom#list_hostnames')
cli_command(__name__, 'appservice web config hostname delete', 'azure.cli.command_modules.appservice.custom#delete_hostname')
cli_command(__name__, 'appservice web config container update', 'azure.cli.command_modules.appservice.custom#update_container_settings')
cli_command(__name__, 'appservice web config container delete', 'azure.cli.command_modules.appservice.custom#delete_container_settings')
cli_command(__name__, 'appservice web config container show', 'azure.cli.command_modules.appservice.custom#show_container_settings', exception_handler=empty_on_404)

cli_command(__name__, 'appservice web config ssl upload', 'azure.cli.command_modules.appservice.custom#upload_ssl_cert')
cli_command(__name__, 'appservice web config ssl list', 'azure.cli.command_modules.appservice.custom#list_ssl_certs')
cli_command(__name__, 'appservice web config ssl bind', 'azure.cli.command_modules.appservice.custom#bind_ssl_cert')
cli_command(__name__, 'appservice web config ssl unbind', 'azure.cli.command_modules.appservice.custom#unbind_ssl_cert')
cli_command(__name__, 'appservice web config ssl delete', 'azure.cli.command_modules.appservice.custom#delete_ssl_cert')

cli_command(__name__, 'appservice web config backup list', 'azure.cli.command_modules.appservice.custom#list_backups')
cli_command(__name__, 'appservice web config backup show', 'azure.cli.command_modules.appservice.custom#show_backup_configuration', exception_handler=empty_on_404)
cli_command(__name__, 'appservice web config backup create', 'azure.cli.command_modules.appservice.custom#create_backup')
cli_command(__name__, 'appservice web config backup update', 'azure.cli.command_modules.appservice.custom#update_backup_schedule')
cli_command(__name__, 'appservice web config backup restore', 'azure.cli.command_modules.appservice.custom#restore_backup')

factory = lambda _: web_client_factory().web_apps
cli_command(__name__, 'appservice web source-control config-local-git', 'azure.cli.command_modules.appservice.custom#enable_local_git')
cli_command(__name__, 'appservice web source-control config', 'azure.cli.command_modules.appservice.custom#config_source_control')
cli_command(__name__, 'appservice web source-control sync', 'azure.cli.command_modules.appservice.custom#sync_site_repo')
cli_command(__name__, 'appservice web source-control show', 'azure.cli.command_modules.appservice.custom#show_source_control', exception_handler=empty_on_404)
cli_command(__name__, 'appservice web source-control delete', 'azure.cli.command_modules.appservice.custom#delete_source_control')

cli_command(__name__, 'appservice web log tail', 'azure.cli.command_modules.appservice.custom#get_streaming_log')
cli_command(__name__, 'appservice web log download', 'azure.cli.command_modules.appservice.custom#download_historical_logs')
cli_command(__name__, 'appservice web log config', 'azure.cli.command_modules.appservice.custom#config_diagnostics')
cli_command(__name__, 'appservice web browse', 'azure.cli.command_modules.appservice.custom#view_in_browser')

cli_command(__name__, 'appservice web deployment slot list', 'azure.mgmt.web.operations.web_apps_operations#WebAppsOperations.list_slots', factory)
cli_command(__name__, 'appservice web deployment slot delete', 'azure.cli.command_modules.appservice.custom#delete_slot')
cli_command(__name__, 'appservice web deployment slot auto-swap', 'azure.cli.command_modules.appservice.custom#config_slot_auto_swap')
cli_command(__name__, 'appservice web deployment slot swap', 'azure.cli.command_modules.appservice.custom#swap_slot')
cli_command(__name__, 'appservice web deployment slot create', 'azure.cli.command_modules.appservice.custom#create_webapp_slot')
cli_command(__name__, 'appservice web deployment user set', 'azure.cli.command_modules.appservice.custom#set_deployment_user')
cli_command(__name__, 'appservice web deployment list-site-credentials',
            'azure.mgmt.web.operations.web_apps_operations#WebAppsOperations.list_publishing_credentials', factory)

factory = lambda _: web_client_factory()
cli_command(__name__, 'appservice web deployment user show', 'azure.mgmt.web.web_site_management_client#WebSiteManagementClient.get_publishing_user', factory, exception_handler=empty_on_404)

factory = lambda _: web_client_factory().app_service_plans
cli_command(__name__, 'appservice plan create', 'azure.cli.command_modules.appservice.custom#create_app_service_plan')
cli_command(__name__, 'appservice plan delete', 'azure.mgmt.web.operations.app_service_plans_operations#AppServicePlansOperations.delete', factory, confirmation=True)
cli_generic_update_command(__name__, 'appservice plan update', 'azure.mgmt.web.operations.app_service_plans_operations#AppServicePlansOperations.get',
                           'azure.mgmt.web.operations.app_service_plans_operations#AppServicePlansOperations.create_or_update',
                           custom_function_op='azure.cli.command_modules.appservice.custom#update_app_service_plan',
                           setter_arg_name='app_service_plan', factory=factory)

cli_command(__name__, 'appservice plan list', 'azure.cli.command_modules.appservice.custom#list_app_service_plans')
cli_command(__name__, 'appservice plan show', 'azure.mgmt.web.operations.app_service_plans_operations#AppServicePlansOperations.get', factory, exception_handler=empty_on_404)
factory = lambda _: web_client_factory()
cli_command(__name__, 'appservice list-locations', 'azure.mgmt.web.web_site_management_client#WebSiteManagementClient.list_geo_regions',
            factory)


#Not for ignite release
#cli_command(__name__, 'webapp plan update-vnet-route',
            #   ServerFarmsOperations.update_vnet_route, factory)
#cli_command(__name__, 'webapp plan update-vnet-gateway',
#             ServerFarmsOperations.update_server_farm_vnet_gateway,factory)
#cli_command(__name__, 'webapp plan update-vnet-route',
                # ServerFarmsOperations.update_vnet_route, factory)
