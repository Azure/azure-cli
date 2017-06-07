# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.core.util import empty_on_404
from azure.cli.core.commands.arm import cli_generic_wait_command
from ._client_factory import _acs_client_factory


cli_command(__name__, 'acs show', 'azure.mgmt.compute.containerservice.operations.container_services_operations#ContainerServicesOperations.get', _acs_client_factory, exception_handler=empty_on_404)
cli_command(__name__, 'acs delete', 'azure.mgmt.compute.containerservice.operations.container_services_operations#ContainerServicesOperations.delete', _acs_client_factory)

# Per conversation with ACS team, hide the update till we have something meaningful to tweak
# from azure.cli.command_modules.acs.custom import update_acs
# cli_generic_update_command(__name__, 'acs update', ContainerServicesOperations.get, ContainerServicesOperations.create_or_update, cf_acs)

# custom commands

cli_command(__name__, 'acs scale', 'azure.cli.command_modules.acs.custom#update_acs', _acs_client_factory)
cli_command(__name__, 'acs list', 'azure.cli.command_modules.acs.custom#list_container_services', _acs_client_factory)
cli_command(__name__, 'acs browse', 'azure.cli.command_modules.acs.custom#acs_browse')
cli_command(__name__, 'acs install-cli', 'azure.cli.command_modules.acs.custom#acs_install_cli')
cli_command(__name__, 'acs dcos browse', 'azure.cli.command_modules.acs.custom#dcos_browse')
cli_command(__name__, 'acs dcos install-cli', 'azure.cli.command_modules.acs.custom#dcos_install_cli')
cli_command(__name__, 'acs create', 'azure.cli.command_modules.acs.custom#acs_create', no_wait_param='no_wait')
cli_generic_wait_command(__name__, 'acs wait', 'azure.mgmt.compute.containerservice.operations.container_services_operations#ContainerServicesOperations.get', _acs_client_factory)
cli_command(__name__, 'acs kubernetes browse', 'azure.cli.command_modules.acs.custom#k8s_browse')
cli_command(__name__, 'acs kubernetes install-cli', 'azure.cli.command_modules.acs.custom#k8s_install_cli')
cli_command(__name__, 'acs kubernetes get-credentials', 'azure.cli.command_modules.acs.custom#k8s_get_credentials')
