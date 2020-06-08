# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=unused-argument, line-too-long
def create_diagnostics_settings(client, name, resource_uri,
                                logs=None,
                                metrics=None,
                                event_hub=None,
                                event_hub_rule=None,
                                storage_account=None,
                                workspace=None,
                                export_to_resource_specific=None):
    from azure.mgmt.monitor.models import DiagnosticSettingsResource
    from knack.util import CLIError
    if export_to_resource_specific and workspace is None:
        raise CLIError('usage error: --workspace and --export-to-specific-resource')
    parameters = DiagnosticSettingsResource(storage_account_id=storage_account,
                                            workspace_id=workspace,
                                            event_hub_name=event_hub,
                                            event_hub_authorization_rule_id=event_hub_rule,
                                            metrics=metrics,
                                            logs=logs,
                                            log_analytics_destination_type='Dedicated' if export_to_resource_specific else None)

    return client.create_or_update(resource_uri=resource_uri, parameters=parameters, name=name)
