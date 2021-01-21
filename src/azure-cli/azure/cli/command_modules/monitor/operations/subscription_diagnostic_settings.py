# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=unused-argument, line-too-long
def create_subscription_diagnostic_settings(cmd, client,
                                            name, logs,
                                            location,
                                            event_hub_name=None,
                                            event_hub_auth_rule=None,
                                            storage_account=None,
                                            service_bus_rule=None,
                                            workspace=None):
    from azure.mgmt.monitor.models import SubscriptionDiagnosticSettingsResource
    from azure.cli.core.commands.client_factory import get_subscription_id
    parameters = SubscriptionDiagnosticSettingsResource(storage_account_id=storage_account,
                                                        workspace_id=workspace,
                                                        event_hub_name=event_hub_name,
                                                        event_hub_authorization_rule_id=event_hub_auth_rule,
                                                        service_bus_rule_id=service_bus_rule,
                                                        logs=logs,
                                                        location=location)
    return client.create_or_update(subscription_id=get_subscription_id(cmd.cli_ctx), parameters=parameters, name=name)


def update_subscription_diagnostic_settings(cmd, instance, event_hub_name=None, logs=None,
                                            event_hub_auth_rule=None, storage_account=None,
                                            service_bus_rule=None, workspace=None):
    with cmd.update_context(instance) as c:
        c.set_param('storage_account_id', storage_account)
        c.set_param('workspace_id', workspace)
        c.set_param('event_hub_name', event_hub_name)
        c.set_param('event_hub_authorization_rule_id', event_hub_auth_rule)
        c.set_param('service_bus_rule_id', service_bus_rule)
        c.set_param('logs', logs)
    return instance
