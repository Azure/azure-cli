# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=unused-import,line-too-long
from azure.cli.core.commands import LongRunningOperation, cli_command
from azure.cli.core.commands.arm import cli_generic_update_command

from ._client_factory import web_client_factory

cli_command(__name__, 'appservice web create', 'azure.cli.command_modules.appservice.custom#create_webapp')
cli_command(__name__, 'appservice web list', 'azure.cli.command_modules.appservice.custom#list_webapp')
cli_command(__name__, 'appservice web show', 'azure.cli.command_modules.appservice.custom#show_webapp')
cli_command(__name__, 'appservice web delete', 'azure.cli.command_modules.appservice.custom#delete_webapp')
cli_command(__name__, 'appservice web stop', 'azure.cli.command_modules.appservice.custom#stop_webapp')
cli_command(__name__, 'appservice web start', 'azure.cli.command_modules.appservice.custom#start_webapp')
cli_command(__name__, 'appservice web restart', 'azure.cli.command_modules.appservice.custom#restart_webapp')

cli_command(__name__, 'appservice web config update', 'azure.cli.command_modules.appservice.custom#update_site_configs')
cli_command(__name__, 'appservice web config show', 'azure.cli.command_modules.appservice.custom#get_site_configs')
cli_command(__name__, 'appservice web config appsettings show', 'azure.cli.command_modules.appservice.custom#get_app_settings')
cli_command(__name__, 'appservice web config appsettings update', 'azure.cli.command_modules.appservice.custom#update_app_settings')
cli_command(__name__, 'appservice web config appsettings delete', 'azure.cli.command_modules.appservice.custom#delete_app_settings')
cli_command(__name__, 'appservice web config hostname add', 'azure.cli.command_modules.appservice.custom#add_hostname')
cli_command(__name__, 'appservice web config hostname list', 'azure.cli.command_modules.appservice.custom#list_hostnames')
cli_command(__name__, 'appservice web config hostname delete', 'azure.cli.command_modules.appservice.custom#delete_hostname')
cli_command(__name__, 'appservice web config container update', 'azure.cli.command_modules.appservice.custom#update_container_settings')
cli_command(__name__, 'appservice web config container delete', 'azure.cli.command_modules.appservice.custom#delete_container_settings')
cli_command(__name__, 'appservice web config container show', 'azure.cli.command_modules.appservice.custom#show_container_settings')

factory = lambda _: web_client_factory().sites
cli_command(__name__, 'appservice web source-control config-local-git', 'azure.cli.command_modules.appservice.custom#enable_local_git')
cli_command(__name__, 'appservice web source-control config', 'azure.cli.command_modules.appservice.custom#config_source_control')
cli_command(__name__, 'appservice web source-control sync', 'azure.cli.command_modules.appservice.custom#sync_site_repo')
cli_command(__name__, 'appservice web source-control show', 'azure.cli.command_modules.appservice.custom#show_source_control')
cli_command(__name__, 'appservice web source-control delete', 'azure.cli.command_modules.appservice.custom#delete_source_control')

cli_command(__name__, 'appservice web log tail', 'azure.cli.command_modules.appservice.custom#get_streaming_log')
cli_command(__name__, 'appservice web log download', 'azure.cli.command_modules.appservice.custom#download_historical_logs')
cli_command(__name__, 'appservice web log config', 'azure.cli.command_modules.appservice.custom#config_diagnostics')
cli_command(__name__, 'appservice web browse', 'azure.cli.command_modules.appservice.custom#view_in_browser')

cli_command(__name__, 'appservice web deployment slot list', 'azure.mgmt.web.operations.sites_operations#SitesOperations.get_site_slots', factory)
cli_command(__name__, 'appservice web deployment slot delete', 'azure.cli.command_modules.appservice.custom#delete_slot')
cli_command(__name__, 'appservice web deployment slot auto-swap', 'azure.cli.command_modules.appservice.custom#config_slot_auto_swap')
cli_command(__name__, 'appservice web deployment slot swap', 'azure.cli.command_modules.appservice.custom#swap_slot')
cli_command(__name__, 'appservice web deployment slot create', 'azure.cli.command_modules.appservice.custom#create_webapp_slot')
cli_command(__name__, 'appservice web deployment user set', 'azure.cli.command_modules.appservice.custom#set_deployment_user')
cli_command(__name__, 'appservice web deployment list-site-credentials',
            'azure.mgmt.web.operations.sites_operations#SitesOperations.list_site_publishing_credentials', factory)

factory = lambda _: web_client_factory().provider
cli_command(__name__, 'appservice web deployment user show', 'azure.mgmt.web.operations.provider_operations#ProviderOperations.get_publishing_user', factory)

factory = lambda _: web_client_factory().server_farms
cli_command(__name__, 'appservice plan create', 'azure.cli.command_modules.appservice.custom#create_app_service_plan')
cli_command(__name__, 'appservice plan delete', 'azure.mgmt.web.operations.server_farms_operations#ServerFarmsOperations.delete_server_farm', factory)
cli_generic_update_command(__name__, 'appservice plan update', 'azure.mgmt.web.operations.server_farms_operations#ServerFarmsOperations.get_server_farm',
                           'azure.mgmt.web.operations.server_farms_operations#ServerFarmsOperations.create_or_update_server_farm',
                           custom_function_op='azure.cli.command_modules.appservice.custom#update_app_service_plan',
                           setter_arg_name='server_farm_envelope', factory=factory)

cli_command(__name__, 'appservice plan list', 'azure.cli.command_modules.appservice.custom#list_app_service_plans')
cli_command(__name__, 'appservice plan show', 'azure.mgmt.web.operations.server_farms_operations#ServerFarmsOperations.get_server_farm', factory)
factory = lambda _: web_client_factory().global_model
cli_command(__name__, 'appservice list-locations', 'azure.mgmt.web.operations.global_model_operations#GlobalModelOperations.get_subscription_geo_regions',
            factory)


#Not for ignite release
#cli_command(__name__, 'webapp plan update-vnet-route',
            #   ServerFarmsOperations.update_vnet_route, factory)
#cli_command(__name__, 'webapp plan update-vnet-gateway',
#             ServerFarmsOperations.update_server_farm_vnet_gateway,factory)
#cli_command(__name__, 'webapp plan update-vnet-route',
                # ServerFarmsOperations.update_vnet_route, factory)
