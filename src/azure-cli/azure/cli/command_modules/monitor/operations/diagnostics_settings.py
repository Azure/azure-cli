# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ..aaz.latest.monitor.diagnostic_settings import Create as _DiagnosticSettingsCreate
from ..aaz.latest.monitor.diagnostic_settings import List as _DiagnosticSettingsList
from ..aaz.latest.monitor.diagnostic_settings import Show as _DiagnosticSettingsShow
from ..aaz.latest.monitor.diagnostic_settings import Delete as _DiagnosticSettingsDelete
from ..aaz.latest.monitor.diagnostic_settings import Update as _DiagnosticSettingsUpdate
from ..aaz.latest.monitor.diagnostic_settings.categories import List as _DiagnosticSettingsCategoryList
from ..aaz.latest.monitor.diagnostic_settings.categories import Show as _DiagnosticSettingsCategoryShow
from knack.util import CLIError
from azure.cli.core.azclierror import ArgumentUsageError


def create_resource_parameters(arg_schema, arg_group=None):
    from azure.cli.core.aaz import AAZResourceGroupNameArg, AAZStrArg
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
    from azure.mgmt.core.tools import parse_resource_id, is_valid_resource_id
    from azure.cli.core.aaz import has_value
    name_or_id = args.resource.to_serialized_data()
    usage_error = CLIError('usage error: --{0} ID | --{0} NAME --resource-group NAME '
                           '--{0}-type TYPE [--{0}-parent PARENT] '
                           '[--{0}-namespace NAMESPACE]'.format(alias))
    if not name_or_id:
        raise usage_error
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

        args.resource = f"/subscriptions/{ctx.subscription_id}/resourceGroups/{rg}/providers/{res_ns}/" \
                        f"{parent + '/' if parent else ''}{res_type}/{name_or_id}"


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
        arg_schema.log_analytics_destination_type._registered = False  # pylint:disable=protected-access
        arg_schema.service_bus_rule_id._registered = False  # pylint:disable=protected-access
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
        create_resource_parameters(arg_schema)
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


class DiagnosticSettingsUpdate(_DiagnosticSettingsUpdate):

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
