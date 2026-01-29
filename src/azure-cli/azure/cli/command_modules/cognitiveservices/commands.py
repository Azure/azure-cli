# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.cognitiveservices._client_factory import cf_accounts, cf_resource_skus, \
    cf_deleted_accounts, cf_deployments, cf_commitment_plans, cf_commitment_tiers, cf_models, cf_usages, \
    cf_ai_projects, cf_account_connections, cf_projects, cf_project_connections


def load_command_table(self, _):
    accounts_type = CliCommandType(
        operations_tmpl='azure.mgmt.cognitiveservices.operations#AccountsOperations.{}',
        client_factory=cf_accounts
    )

    deployments_type = CliCommandType(
        operations_tmpl='azure.mgmt.cognitiveservices.operations#DeploymentsOperations.{}',
        client_factory=cf_deployments
    )

    commitment_plans_type = CliCommandType(
        operations_tmpl='azure.mgmt.cognitiveservices.operations#CommitmentPlansOperations.{}',
        client_factory=cf_commitment_plans
    )

    commitment_tiers_type = CliCommandType(
        operations_tmpl='azure.mgmt.cognitiveservices.operations#CommitmentTiersOperations.{}',
        client_factory=cf_commitment_tiers
    )

    models_type = CliCommandType(
        operations_tmpl='azure.mgmt.cognitiveservices.operations#ModelsOperations.{}',
        client_factory=cf_models
    )

    usages_type = CliCommandType(
        operations_tmpl='azure.mgmt.cognitiveservices.operations#UsagesOperations.{}',
        client_factory=cf_usages
    )

    projects_type = CliCommandType(
        operations_tmpl='azure.mgmt.cognitiveservices.operations#ProjectsOperations.{}',
        client_factory=cf_projects
    )

    account_connections_type = CliCommandType(
        operations_tmpl='azure.mgmt.cognitiveservices.operations#AccountConnectionsOperations.{}',
        client_factory=cf_account_connections
    )
    project_connections_type = CliCommandType(
        operations_tmpl='azure.mgmt.cognitiveservices.operations#ProjectConnectionsOperations.{}',
        client_factory=cf_project_connections
    )

    with self.command_group('cognitiveservices account', accounts_type, client_factory=cf_accounts) as g:
        g.custom_command('create', 'create')
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.custom_command('update', 'update')
        g.custom_command('list', 'list_resources')
        g.show_command('show-deleted', 'get',
                       operations_tmpl='azure.mgmt.cognitiveservices.operations#DeletedAccountsOperations.{}',
                       client_factory=cf_deleted_accounts)
        g.command('list-deleted', 'list',
                  operations_tmpl='azure.mgmt.cognitiveservices.operations#DeletedAccountsOperations.{}',
                  client_factory=cf_deleted_accounts)
        g.command('purge', 'begin_purge',
                  operations_tmpl='azure.mgmt.cognitiveservices.operations#DeletedAccountsOperations.{}',
                  client_factory=cf_deleted_accounts)
        g.custom_command('recover', 'recover')
        g.custom_command('list-skus', 'list_skus')
        g.command('list-models', 'list_models')
        g.custom_command('list-usage', 'list_usages')
        g.custom_command('list-kinds', 'list_kinds', client_factory=cf_resource_skus)

    with self.command_group('cognitiveservices account keys', accounts_type) as g:
        g.command('regenerate', 'regenerate_key')
        g.command('list', 'list_keys')

    # deprecating this
    with self.command_group('cognitiveservices', client_factory=cf_accounts) as g:
        g.custom_command('list', 'list_resources',
                         deprecate_info=g.deprecate(redirect='az cognitiveservices account list', hide=True))

    with self.command_group('cognitiveservices account network-rule', accounts_type, client_factory=cf_accounts) as g:
        g.custom_command('add', 'add_network_rule')
        g.custom_command('list', 'list_network_rules')
        g.custom_command('remove', 'remove_network_rule')

    with self.command_group('cognitiveservices account identity', accounts_type, client_factory=cf_accounts) as g:
        g.custom_command('assign', 'identity_assign')
        g.custom_command('remove', 'identity_remove')
        g.custom_show_command('show', 'identity_show')

    with self.command_group(
            'cognitiveservices account deployment', deployments_type,
            client_factory=cf_deployments) as g:
        g.custom_command('create', 'deployment_begin_create_or_update')
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.command('list', 'list')

    with self.command_group(
            'cognitiveservices account commitment-plan', commitment_plans_type,
            client_factory=cf_commitment_plans) as g:
        g.custom_command('create', 'commitment_plan_create_or_update')
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.command('list', 'list')

    with self.command_group('cognitiveservices commitment-tier', commitment_tiers_type) as g:
        g.command('list', 'list')

    with self.command_group('cognitiveservices model', models_type) as g:
        g.command('list', 'list')

    with self.command_group('cognitiveservices usage', usages_type) as g:
        g.command('list', 'list')

    with self.command_group('cognitiveservices agent', client_factory=cf_ai_projects, is_preview=True) as g:
        g.custom_command('create', 'agent_create')
        g.custom_command('update', 'agent_update')
        g.custom_command('stop', 'agent_stop')
        g.custom_command('start', 'agent_start')
        g.custom_show_command('status', 'agent_status')
        g.custom_command('delete-deployment', 'agent_delete_deployment')
        g.custom_command('delete', 'agent_delete')
        g.custom_command('list', 'agent_list')
        g.custom_command('list-versions', 'agent_versions_list')
        g.custom_show_command('show', 'agent_show')

    with self.command_group('cognitiveservices agent logs', client_factory=cf_ai_projects, is_preview=True) as g:
        g.custom_show_command('show', 'agent_logs_show')

    with self.command_group(
            'cognitiveservices account project', projects_type,
            client_factory=cf_projects) as g:
        g.custom_command('create', 'project_create')
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.custom_command('update', 'project_update')

    with self.command_group(
            'cognitiveservices account project connection', project_connections_type,
            client_factory=cf_project_connections) as g:
        g.custom_command('create', 'project_connection_create')
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.generic_update_command(
            'update',
            setter_name='update',
            setter_arg_name='connection',
            custom_func_name='project_connection_update')

    with self.command_group(
            'cognitiveservices account connection', account_connections_type,
            client_factory=cf_account_connections) as g:
        g.custom_command('create', 'account_connection_create')
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.generic_update_command(
            'update',
            setter_name='update',
            setter_arg_name='connection',
            custom_func_name='account_connection_update')
