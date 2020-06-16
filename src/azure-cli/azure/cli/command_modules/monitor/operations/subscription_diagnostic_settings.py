# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=unused-argument, line-too-long
def create_subscription_diagnostic_settings(client, name,
                                            subscription_id,
                                            logs=None,
                                            event_hub=None,
                                            event_hub_rule=None,
                                            storage_account=None,
                                            service_bus_rule_id=None,
                                            workspace=None):
    from azure.mgmt.monitor.models import SubscriptionDiagnosticSettingsResource
    from knack.util import CLIError
    parameters = SubscriptionDiagnosticSettingsResource(storage_account_id=storage_account,
                                                        workspace_id=workspace,
                                                        event_hub_name=event_hub,
                                                        event_hub_authorization_rule_id=event_hub_rule,
                                                        service_bus_rule_id=service_bus_rule_id,
                                                        logs=logs)

    return client.create_or_update(subscription_id=subscription_id, parameters=parameters, name=name)
