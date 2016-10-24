#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

#pylint: disable=unused-import
from azure.mgmt.web.operations import (SitesOperations, ServerFarmsOperations,
                                       ProviderOperations, GlobalModelOperations)
from azure.cli.core.commands import LongRunningOperation, cli_command
from azure.cli.core.commands.arm import cli_generic_update_command

from ._params import web_client_factory
from .custom import (create_webapp, show_webapp, list_webapp,
                     delete_webapp, stop_webapp, restart_webapp,
                     enable_local_git, set_deployment_user,
                     get_git_url, view_in_browser, create_app_service_plan,
                     update_app_service_plan, config_diagnostics,
                     get_streaming_log, download_historical_logs,
                     create_webapp_slot, config_slot_auto_swap,
                     get_site_configs, update_site_configs,
                     get_app_settings, update_app_settings, delete_app_settings,
                     add_hostname, list_hostnames, delete_hostname,
                     update_container_settings, delete_container_settings,
                     list_container_settings)

cli_command('appservice web create', create_webapp)
cli_command('appservice web list', list_webapp)
cli_command('appservice web show', show_webapp)
cli_command('appservice web delete', delete_webapp)
cli_command('appservice web stop', stop_webapp)
cli_command('appservice web restart', restart_webapp)

cli_command('appservice web config update', update_site_configs)
cli_command('appservice web config show', get_site_configs)
cli_command('appservice web config appsettings show', get_app_settings)
cli_command('appservice web config appsettings update', update_app_settings)
cli_command('appservice web config appsettings delete', delete_app_settings)
cli_command('appservice web config hostname add', add_hostname)
cli_command('appservice web config hostname list', list_hostnames)
cli_command('appservice web config hostname delete', delete_hostname)
cli_command('appservice web config container update', update_container_settings)
cli_command('appservice web config container delete', delete_container_settings)
cli_command('appservice web config container list', list_container_settings)

factory = lambda _: web_client_factory().sites
cli_command('appservice web show-publish-profile',
            SitesOperations.list_site_publishing_credentials, factory)

cli_command('appservice web git enable-local', enable_local_git)
cli_command('appservice web git show-url', get_git_url)
cli_command('appservice web log tail', get_streaming_log)
cli_command('appservice web log download', download_historical_logs)
cli_command('appservice web log config', config_diagnostics)
cli_command('appservice web browse', view_in_browser)

cli_command('appservice web deployment slot list', SitesOperations.get_site_slots, factory)
cli_command('appservice web deployment slot auto-swap', config_slot_auto_swap)
cli_command('appservice web deployment slot swap', SitesOperations.swap_slots_slot, factory)
cli_command('appservice web deployment slot create', create_webapp_slot)
cli_command('appservice web deployment user set', set_deployment_user)
cli_command('appservice web deployment list-site-credentials',
            SitesOperations.list_site_publishing_credentials, factory)

factory = lambda _: web_client_factory().provider
cli_command('appservice web deployment user show', ProviderOperations.get_publishing_user, factory)

factory = lambda _: web_client_factory().server_farms
cli_command('appservice plan create', create_app_service_plan)
cli_command('appservice plan delete', ServerFarmsOperations.delete_server_farm, factory)
cli_generic_update_command('appservice plan update', ServerFarmsOperations.get_server_farm,
                           ServerFarmsOperations.create_or_update_server_farm,
                           custom_function=update_app_service_plan,
                           setter_arg_name='server_farm_envelope', factory=factory)
cli_command('appservice plan list', ServerFarmsOperations.get_server_farms, factory)
cli_command('appservice plan show', ServerFarmsOperations.get_server_farm, factory)
cli_command('appservice list-locations', GlobalModelOperations.get_subscription_geo_regions,
            factory)

#Functionalities covered by better custom commands, so not exposed for now
#cli_command('webapp get-source-control', SitesOperations.get_site_source_control, factory)
#cli_command('webapp source-control list', ProviderOperations.get_source_controls, factory)

#Not for ignite release
#cli_command('webapp plan update-vnet-route', ServerFarmsOperations.update_vnet_route, factory)
#cli_command('webapp plan update-vnet-gateway',
#             ServerFarmsOperations.update_server_farm_vnet_gateway,factory)
#cli_command('webapp plan update-vnet-route', ServerFarmsOperations.update_vnet_route, factory)

