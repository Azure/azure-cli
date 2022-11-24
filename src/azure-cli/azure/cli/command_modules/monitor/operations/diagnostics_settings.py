# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.monitor.aaz.latest.monitor.diagnostic_settings import List as _DiagnosticSettingsList
from azure.cli.command_modules.monitor.aaz.latest.monitor.diagnostic_settings import Show as _DiagnosticSettingsShow
from azure.cli.command_modules.monitor.aaz.latest.monitor.diagnostic_settings import Delete as _DiagnosticSettingsDelete
from azure.cli.command_modules.monitor.aaz.latest.monitor.diagnostic_settings.categories import List as _DiagnosticSettingsCategoryList
from azure.cli.command_modules.monitor.aaz.latest.monitor.diagnostic_settings.categories import Show as _DiagnosticSettingsCategoryShow
from azure.cli.command_modules.monitor.aaz.latest.monitor.diagnostic_settings.subscription import Delete as _SubscriptionDiagnosticSettingsDelete
from azure.cli.command_modules.monitor.aaz.latest.monitor.diagnostic_settings.subscription import Show as _SubscriptionDiagnosticSettingsShow
from azure.cli.command_modules.monitor.aaz.latest.monitor.diagnostic_settings.subscription import List as _SubscriptionDiagnosticSettingsList
from knack.util import CLIError

def create_resource_parameters(arg_schema, arg_group=None):
    from azure.cli.core.aaz import AAZResourceGroupNameArg, AAZStrArg, AAZResourceIdArgFormat
    arg_schema.resource_group_name = AAZResourceGroupNameArg(arg_group=arg_group)
    arg_schema.namespace = AAZStrArg(
        options=['--resource-namespace'],
        help="Target resource provider namespace.",
        arg_group=arg_group,
    )
    arg_schema.parent = AAZStrArg(
        options=['--resource-parent'],
        help="Target resource parent path, if applicable.",
        arg_group=arg_group,
    )
    arg_schema.resource_type = AAZStrArg(
        options=['--resource-type'],
        help="Target resource type. Can also accept namespace/type format (Ex: 'Microsoft.Compute/virtualMachines')",
        arg_group=arg_group,
    )

def update_resource_parameters(ctx, alias="resource"):
    args = ctx.args
    from msrestazure.tools import is_valid_resource_id
    from azure.mgmt.core.tools import parse_resource_id
    from azure.cli.core.aaz import has_value
    name_or_id = args.resource.to_serialized_data()
    usage_error = CLIError('usage error: --{0} ID | --{0} NAME --resource-group NAME '
                           '--{0}-type TYPE [--{0}-parent PARENT] '
                           '[--{0}-namespace NAMESPACE]'.format(alias))
    if is_valid_resource_id(name_or_id):
        if has_value(args.namespace) or has_value(args.parent) or has_value(args.resource_type):
            raise usage_error
        parsed_id = parse_resource_id(name_or_id)
        subscription_id = parsed_id.get('subscription', None)
        if subscription_id:
            # update subscription_id to support cross tenants
            ctx.update_aux_subscriptions(subscription_id)
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
            raise usage_error

        args.resource = f"/subscriptions/{ctx.subscription_id}/resourceGroups/{rg}/providers/{res_ns}/{parent + '/' if parent else ''}{res_type}/{name_or_id}"

class DiagnosticSettingsShow(_DiagnosticSettingsShow):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        arg_schema = super()._build_arguments_schema(*args, **kwargs)
        create_resource_parameters(arg_schema, arg_group="Target Resource")
        return arg_schema

    def pre_operations(self):
        ctx = self.ctx
        update_resource_parameters(ctx)


class DiagnosticSettingsList(_DiagnosticSettingsList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        arg_schema = super()._build_arguments_schema(*args, **kwargs)
        create_resource_parameters(arg_schema, arg_group="Target Resource")
        return arg_schema

    def pre_operations(self):
        ctx = self.ctx
        update_resource_parameters(ctx)

class DiagnosticSettingsDelete(_DiagnosticSettingsDelete):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        arg_schema = super()._build_arguments_schema(*args, **kwargs)
        create_resource_parameters(arg_schema, arg_group="Target Resource")
        return arg_schema

    def pre_operations(self):
        ctx = self.ctx
        update_resource_parameters(ctx)


class DiagnosticSettingsCategoryList(_DiagnosticSettingsCategoryList):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        arg_schema = super()._build_arguments_schema(*args, **kwargs)
        create_resource_parameters(arg_schema)
        return arg_schema

    def pre_operations(self):
        ctx = self.ctx
        update_resource_parameters(ctx)

class DiagnosticSettingsCategoryShow(_DiagnosticSettingsCategoryShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        arg_schema = super()._build_arguments_schema(*args, **kwargs)
        create_resource_parameters(arg_schema)
        return arg_schema

    def pre_operations(self):
        ctx = self.ctx
        update_resource_parameters(ctx)

class SubscriptionDiagnosticSettingsShow(_SubscriptionDiagnosticSettingsShow):
    pass

class SubscriptionDiagnosticSettingsDelete(_SubscriptionDiagnosticSettingsDelete):
    pass

class SubscriptionDiagnosticSettingsList(_SubscriptionDiagnosticSettingsList):
    pass


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
