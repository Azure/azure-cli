# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.util import sdk_no_wait

def list_staticsites(cmd, resource_group_name=None):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    if resource_group_name:
        result = list(client.get_static_sites_by_resource_group(resource_group_name))
    else:
        result = list(client.list())
    return result

def show_staticsite(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.get_static_site(resource_group_name, name)

def list_staticsite_domains(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.list_static_site_custom_domains(resource_group_name, name)

def list_staticsite_secrets(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.list_static_site_secrets(resource_group_name, name)

def list_staticsite_functions(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.list_static_site_functions(resource_group_name, name)

def list_staticsite_function_app_settings(cmd, resource_group_name, name):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return client.list_static_site_function_app_settings(resource_group_name, name)

def _get_staticsites_client_factory(cli_ctx, api_version=None):
    from azure.mgmt.web import WebSiteManagementClient
    client = get_mgmt_service_client(cli_ctx, WebSiteManagementClient).static_sites
    if api_version:
        client.api_version = api_version
    return client

# def create_staticsites(cmd):
#     # # The current SDK has a couple of challenges creating ASE. The current swagger version used,
#     # # did not have 201 as valid response code, and thus will fail with polling operations.
#     # # The Load Balancer Type is an Enum Flag, that is expressed as a simple string enum in swagger,
#     # # and thus will not allow you to define an Internal ASE (combining web and publishing flag).
#     # # Therefore the current method use direct ARM.
#     # location = location or _get_location_from_resource_group(cmd.cli_ctx, resource_group_name)
#     # subnet_id = _validate_subnet_id(cmd.cli_ctx, subnet, vnet_name, resource_group_name)

#     # _validate_subnet_empty(cmd.cli_ctx, subnet_id)
#     # if not ignore_subnet_size_validation:
#     #     _validate_subnet_size(cmd.cli_ctx, subnet_id)
#     # if not ignore_route_table:
#     #     _ensure_route_table(cmd.cli_ctx, resource_group_name, name, location, subnet_id, force_route_table)
#     # if not ignore_network_security_group:
#     #     _ensure_network_security_group(cmd.cli_ctx, resource_group_name, name, location,
#     #                                    subnet_id, force_network_security_group)

#     # logger.info('Create App Service Environment...')
#     # deployment_name = _get_unique_deployment_name('cli_ase_deploy_')
#     # ase_deployment_properties = _build_ase_deployment_properties(name, location, subnet_id, virtual_ip_type,
#     #                                                              front_end_scale_factor, front_end_sku, None)
#     # deployment_client = _get_deployment_client_factory(cmd.cli_ctx)
#     # return sdk_no_wait(no_wait, deployment_client.create_or_update,
#     #                    resource_group_name, deployment_name, ase_deployment_properties)
#     return

# def update_staticsites(cmd):
#     return

def delete_staticsite(cmd, resource_group_name, name, no_wait=False):
    client = _get_staticsites_client_factory(cmd.cli_ctx)
    return sdk_no_wait(no_wait, client.delete_static_site,
                       resource_group_name=resource_group_name, name=name)
