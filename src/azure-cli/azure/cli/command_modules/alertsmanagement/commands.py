from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.alertsmanagement._client_factory import (
    alerts_mgmt_client_factory,
    smart_groups_mgmt_client_factory)
from ._exception_handler import alertsmanagement_exception_handler


def load_command_table(self, _):
    alertsmanagement_alert_util = CliCommandType(
        operations_tmpl='azure.mgmt.alertsmanagement.operations#AlertsOperations.{}',
        client_factory=alerts_mgmt_client_factory,
        exception_handler=alertsmanagement_exception_handler
    )

    alertsmanagement_smart_group_util = CliCommandType(
        operations_tmpl='azure.mgmt.alertsmanagement.operations#SmartGroupOperations.{}',
        client_factory=smart_groups_mgmt_client_factory,
        exception_handler=alertsmanagement_exception_handler
    )

    with self.command_group('alert', alertsmanagement_alert_util, client_factory=alerts_mgmt_client_factory) as g:
        g.command('list', 'get_all')
        g.command('list-summary', 'get_history')
        g.show_command('show', 'get_by_id')
        g.show_command('show-history', 'get_history')

    with self.command_group('smart-group', alertsmanagement_smart_group_util, client_factory=smart_groups_mgmt_client_factory) as g:
        g.command('list', 'get_all')
        g.show_command('show', 'get_by_id')
        g.show_command('show-history', 'get_history')

    with self.command_group('action-rule', alertsmanagement_action_rule_util, alerts_mgmt_client_factory=action_rules_mgmt_client_factory) as g:
        g.custom_command('list', 'cli_alertsmanagement_list_action_rules')
        g.show_command('show', 'get_by_name')



