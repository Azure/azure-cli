# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

from azure.cli.command_modules.monitor.aaz.latest.monitor.diagnostic_settings._create \
    import Create as _DiagnosticSettingsCreate
from azure.cli.command_modules.monitor.operations.diagnostics_settings import (
    create_resource_parameters, update_resource_parameters,
)
from azure.cli.core.azclierror import ArgumentUsageError
from knack.util import CLIError


class DiagnosticSettingsCreate(_DiagnosticSettingsCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        arg_schema = super()._build_arguments_schema(*args, **kwargs)
        create_resource_parameters(arg_schema, arg_group="Target Resource")

        from azure.cli.core.aaz import AAZBoolArg
        arg_schema.export_to_resource_specific = AAZBoolArg(
            options=['--export-to-resource-specific'],
            help="Indicate that the export to LA must be done to a resource specific table, a.k.a. "
                 "dedicated or fixed schema table, as opposed to the default dynamic schema table called "
                 "AzureDiagnostics. This argument is effective only when the argument --workspace is also given. "
                 "Allowed values: false, true."
        )
        arg_schema.log_analytics_destination_type._registered = False
        arg_schema.service_bus_rule_id._registered = False
        return arg_schema

    def pre_operations(self):
        ctx = self.ctx
        from azure.cli.core.aaz import has_value
        from azure.mgmt.core.tools import is_valid_resource_id, resource_id, parse_resource_id
        update_resource_parameters(ctx)
        args = ctx.args
        rg = args.resource_group_name.to_serialized_data()

        if not has_value(rg):
            rg = parse_resource_id(args.resource.to_serialized_data())['resource_group']
            args.resource_group_name = rg

        storage_account = args.storage_account.to_serialized_data()
        if has_value(storage_account) and not is_valid_resource_id(storage_account):
            storage_account = resource_id(subscription=ctx.subscription_id,
                                          resource_group=rg,
                                          namespace='microsoft.Storage',
                                          type='storageAccounts',
                                          name=storage_account)
            args.storage_account = storage_account

        workspace = args.workspace.to_serialized_data()
        if has_value(workspace) and not is_valid_resource_id(workspace):
            workspace = resource_id(subscription=ctx.subscription_id,
                                    resource_group=rg,
                                    namespace='microsoft.OperationalInsights',
                                    type='workspaces',
                                    name=workspace)
            args.workspace = workspace

        event_hub = args.event_hub.to_serialized_data()
        if has_value(event_hub) and is_valid_resource_id(event_hub):
            event_hub = parse_resource_id(event_hub)['name']
            args.event_hub = event_hub

        event_hub_rule = args.event_hub_rule.to_serialized_data()
        if has_value(event_hub_rule):
            if not is_valid_resource_id(event_hub_rule):
                if not has_value(event_hub):
                    raise CLIError('usage error: --event-hub-rule ID | --event-hub-rule NAME --event-hub NAME')
                # use value from --event-hub if the rule is a name
                event_hub_rule = resource_id(
                    subscription=ctx.subscription_id,
                    resource_group=rg,
                    namespace='Microsoft.EventHub',
                    type='namespaces',
                    name=event_hub,
                    child_type_1='AuthorizationRules',
                    child_name_1=event_hub_rule)
                args.event_hub_rule = event_hub_rule

            elif not has_value(event_hub):
                # extract the event hub name from `--event-hub-rule` if provided as an ID
                event_hub = parse_resource_id(event_hub_rule)['name']
                args.event_hub = event_hub
        if not (has_value(storage_account) or has_value(workspace) or has_value(event_hub)):
            raise CLIError(
                'usage error - expected one or more:  --storage-account NAME_OR_ID | --workspace NAME_OR_ID '
                '| --event-hub NAME_OR_ID | --event-hub-rule ID')

        export_to_resource_specific = args.export_to_resource_specific.to_serialized_data()
        if has_value(export_to_resource_specific) and export_to_resource_specific:
            args.log_analytics_destination_type = 'Dedicated'
            if not has_value(workspace):
                raise ArgumentUsageError('usage error: --workspace and --export-to-specific-resource')
        else:
            args.log_analytics_destination_type = None
