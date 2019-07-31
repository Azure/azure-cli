from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.alertsmanagement._client_factory import (
    alerts_mgmt_client_factory,
    smart_groups_mgmt_client_factory,
    action_rules_mgmt_client_factory)
from ._exception_handler import alertsmanagement_exception_handler


def load_command_table(self, _):
    alertsmanagement_alert_util = CliCommandType(
        operations_tmpl='azure.mgmt.alertsmanagement.operations#AlertsOperations.{}',
        client_factory=alerts_mgmt_client_factory,
        exception_handler=alertsmanagement_exception_handler
    )

    alertsmanagement_smart_group_util = CliCommandType(
        operations_tmpl='azure.mgmt.alertsmanagement.operations#SmartGroupsOperations.{}',
        client_factory=smart_groups_mgmt_client_factory,
        exception_handler=alertsmanagement_exception_handler
    )

    alertsmanagement_action_rule_util = CliCommandType(
        operations_tmpl='azure.mgmt.alertsmanagement.operations#ActionRulesOperations.{}',
        client_factory=action_rules_mgmt_client_factory,
        exception_handler=alertsmanagement_exception_handler
    )

    with self.command_group('alertsmanagement alert', alertsmanagement_alert_util,
                            client_factory=alerts_mgmt_client_factory) as g:
        g.command('list', 'get_all')
        g.command('list-summary', 'get_summary')
        g.show_command('show', 'get_by_id')
        g.show_command('show-history', 'get_history')

    with self.command_group('alertsmanagement smart-group', alertsmanagement_smart_group_util,
                            client_factory=smart_groups_mgmt_client_factory) as g:
        g.command('list', 'get_all')
        g.show_command('show', 'get_by_id')
        g.show_command('show-history', 'get_history')

    with self.command_group('alertsmanagement action-rule', alertsmanagement_action_rule_util,
                            client_factory=action_rules_mgmt_client_factory) as g:
        g.command('list', 'cli_alertsmanagement_list_by_subscription')
        g.show_command('show', 'get_by_name')
        g.command('delete', 'delete')
        g.command('set', 'create_update')
        g.command('update', 'update')
