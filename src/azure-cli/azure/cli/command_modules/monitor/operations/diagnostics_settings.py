# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.monitor.aaz.latest.monitor.diagnostic_settings import List as _DiagnosticSettingsList


class DiagnosticSettingsList(_DiagnosticSettingsList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceGroupNameArg, AAZStrArg, AAZResourceIdArgFormat
        arg_schema = super()._build_arguments_schema(*args, **kwargs)

        arg_schema.resource_group_name = AAZResourceGroupNameArg()
        arg_schema.namespace = AAZStrArg(
            options=['--resource-namespace'],
            help="Target resource provider namespace.",
        )
        arg_schema.parent = AAZStrArg(
            options=['--resource-parent'],
            help="Target resource parent path, if applicable.",
        )
        arg_schema.resource_type = AAZStrArg(
            options=['--resource-type'],
            help="Target resource type. Can also accept namespace/type format (Ex: 'Microsoft.Compute/virtualMachines')",
        )

        return arg_schema

    def pre_operations(self):
        from msrestazure.tools import is_valid_resource_id
        from azure.mgmt.core.tools import parse_resource_id
        from azure.cli.core.aaz import has_value
        args = self.ctx.args
        name_or_id = args.resource.to_serialized_data()
        if is_valid_resource_id(name_or_id):
            if has_value(args.namespace) or has_value(args.parent) or has_value(args.resource_type):
                raise ValueError()
            parsed_id = parse_resource_id(name_or_id)
            subscription_id = parsed_id.get('subscription', None)
            if subscription_id:
                # update subscription_id to support cross tenants
                self.ctx.update_aux_subscriptions(subscription_id)
        else:
            res_ns = args.namespace.to_serialized_data()
            rg = args.resource_group_name.to_serialized_data()
            res_type = args.resource_type.to_serialized_data()
            parent = args.parent.to_serialized_data()
            if has_value(res_type):
                if '/' in res_type:
                    res_ns = res_ns or res_type.rsplit('/', 1)[0]
                    res_type = res_type.rsplit('/', 1)[1]

            if not res_ns or not rg or not res_type or not name_or_id:
                raise ValueError()

            args.resource = f"/subscriptions/{self.ctx.subscription_id}/resourceGroups/{rg}/providers/{res_ns}/{parent + '/' if parent else ''}{res_type}/{name_or_id}"


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
