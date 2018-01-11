# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=unused-argument
def create_diagnostics_settings(client, name, resource_uri,
                                logs=None,
                                metrics=None,
                                event_hub=None,
                                event_hub_rule=None,
                                storage_account=None,
                                workspace=None):
    from azure.mgmt.monitor.models.diagnostic_settings_resource import DiagnosticSettingsResource

    parameters = DiagnosticSettingsResource(storage_account_id=storage_account,
                                            workspace_id=workspace,
                                            event_hub_name=event_hub,
                                            event_hub_authorization_rule_id=event_hub_rule,
                                            metrics=metrics,
                                            logs=logs)

    return client.create_or_update(resource_uri=resource_uri, parameters=parameters, name=name)
