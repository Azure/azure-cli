# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from azure.cli.core.commands import CliCommandType


def load_command_table(self, _):
    from azure.cli.command_modules.relay._client_factory import namespaces_mgmt_client_factory, \
        wcfrelays_mgmt_client_factory, hycos_mgmt_client_factory
    from azure.cli.command_modules.relay.custom import empty_on_404

    sb_namespace_util = CliCommandType(
        operations_tmpl='azure.mgmt.relay.operations#NamespacesOperations.{}',
        client_factory=namespaces_mgmt_client_factory
    )

    sb_wcfrelay_util = CliCommandType(
        operations_tmpl='azure.mgmt.relay.operations#WCFRelaysOperations.{}',
        client_factory=wcfrelays_mgmt_client_factory
    )

    sb_hyco_util = CliCommandType(
        operations_tmpl='azure.mgmt.relay.operations#HybridConnectionsOperations.{}',
        client_factory=hycos_mgmt_client_factory
    )

# Namespace Region
    custom_tmpl = 'azure.cli.command_modules.relay.custom#{}'
    relay_custom = CliCommandType(operations_tmpl=custom_tmpl)
    with self.command_group('relay namespace', sb_namespace_util, client_factory=namespaces_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_namespace_create')
        g.show_command('show')
        g.custom_command('list', 'cli_namespace_list', exception_handler=empty_on_404)
        g.command('delete', 'delete')
        g.command('exists', 'check_name_availability_method')
        g.generic_update_command('update', custom_func_name='cli_namespace_update', custom_func_type=relay_custom)

    with self.command_group('relay namespace authorization-rule', sb_namespace_util, client_factory=namespaces_mgmt_client_factory) as g:
        g.command('create', 'create_or_update_authorization_rule',)
        g.show_command('show', 'get_authorization_rule')
        g.command('list', 'list_authorization_rules', exception_handler=empty_on_404)
        g.command('keys list', 'list_keys')
        g.command('keys renew', 'regenerate_keys')
        g.command('delete', 'delete_authorization_rule')
        g.generic_update_command('update', getter_name='get_authorization_rule', setter_name='create_or_update_authorization_rule', custom_func_name='cli_namespaceautho_update')

# WCF Relay Region
    with self.command_group('relay wcfrelay', sb_wcfrelay_util, client_factory=wcfrelays_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_wcfrelay_create')
        g.show_command('show')
        g.command('list', 'list_by_namespace', exception_handler=empty_on_404)
        g.command('delete', 'delete')
        g.generic_update_command('update', custom_func_name='cli_wcfrelay_update')

    with self.command_group('relay wcfrelay authorization-rule', sb_wcfrelay_util, client_factory=wcfrelays_mgmt_client_factory) as g:
        g.command('create', 'create_or_update_authorization_rule',)
        g.show_command('show', 'get_authorization_rule')
        g.command('list', 'list_authorization_rules', exception_handler=empty_on_404)
        g.command('keys list', 'list_keys')
        g.command('keys renew', 'regenerate_keys')
        g.command('delete', 'delete_authorization_rule')
        g.generic_update_command('update', getter_name='get_authorization_rule', setter_name='create_or_update_authorization_rule', custom_func_name='cli_namespaceautho_update')

# Hybrid Connections Region
    with self.command_group('relay hyco', sb_hyco_util, client_factory=hycos_mgmt_client_factory) as g:
        g.custom_command('create', 'cli_hyco_create')
        g.show_command('show')
        g.command('list', 'list_by_namespace', exception_handler=empty_on_404)
        g.command('delete', 'delete')
        g.generic_update_command('update', custom_func_name='cli_hyco_update')

    with self.command_group('relay hyco authorization-rule', sb_hyco_util, client_factory=hycos_mgmt_client_factory) as g:
        g.command('create', 'create_or_update_authorization_rule')
        g.show_command('show', 'get_authorization_rule')
        g.command('list', 'list_authorization_rules', exception_handler=empty_on_404)
        g.command('keys list', 'list_keys')
        g.command('keys renew', 'regenerate_keys')
        g.command('delete', 'delete_authorization_rule')
        g.generic_update_command('update', getter_name='get_authorization_rule', setter_name='create_or_update_authorization_rule', custom_func_name='cli_namespaceautho_update')
