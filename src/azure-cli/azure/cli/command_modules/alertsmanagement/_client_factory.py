
def cf_alertsmanagement(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.alertsmanagement import AlertsManagementClient
    return get_mgmt_service_client(cli_ctx, AlertsManagementClient)


def alerts_mgmt_client_factory(cli_ctx, kwargs):
    return cf_alertsmanagement(cli_ctx, **kwargs).alerts


def smart_groups_mgmt_client_factory(cli_ctx, kwargs):
    return cf_alertsmanagement(cli_ctx, **kwargs).smart_groups


def action_rules_mgmt_client_factory(cli_ctx, kwargs):
    print("Client factory start")
    client = cf_alertsmanagement(cli_ctx, **kwargs).action_rules
    print("Client factory return")
    return client
