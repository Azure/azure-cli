# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=unused-argument
def create_diagnostics_settings(client, target_resource_id, resource_group=None, logs=None, metrics=None,
                                namespace=None, rule_name=None, tags=None, event_hub_name=None, storage_account=None,
                                workspace=None):
    from azure.mgmt.monitor.models.diagnostic_settings_resource import DiagnosticSettingsResource

    # https://github.com/Azure/azure-rest-api-specs/issues/1058
    parameters = DiagnosticSettingsResource(storage_account_id=storage_account,
                                            event_hub_name=event_hub_name, metrics=metrics, logs=logs,
                                            workspace_id=workspace)

    return client.create_or_update(target_resource_id, parameters)
