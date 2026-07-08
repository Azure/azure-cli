# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access, line-too-long

from azure.cli.core.aaz import AAZStrArg, AAZListArg, AAZBoolArg, register_command
from azure.cli.command_modules.monitor.aaz.latest.monitor.activity_log.alert._update \
    import Update as _ActivityLogAlertUpdate


@register_command("monitor activity-log alert scope add")
class ActivityLogAlertScopeAdd(_ActivityLogAlertUpdate):
    """Add scopes to this activity log alert rule.

    :example: Add scopes to this activity log alert rule.
        az monitor activity-log alert scope add --name MyActivityLogAlerts --resource-group
        MyResourceGroup --scope /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myRG
        /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-
        xxxxxxxxxxxx/resourceGroups/myRG/Microsoft.KeyVault/vaults/mykey
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.enabled._registered = False
        args_schema.all_of._registered = False
        args_schema.action_groups._registered = False
        args_schema.tags._registered = False
        args_schema.description._registered = False
        args_schema.scopes._registered = False
        args_schema.scope_ui = AAZListArg(
            options=["--scope", "-s"],
            required=True,
            help="List of scopes to add. Each scope could be a resource ID or a subscription ID.",
        )
        args_schema.scope_ui.Element = AAZStrArg()

        args_schema.reset = AAZBoolArg(
            options=["--reset"],
            help="Remove all the existing action groups before add new conditions.",
            default=False
        )
        return args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args
        new_scopes = set() if args.reset else set(instance.properties.scopes.to_serialized_data())
        for scope in args.scope_ui.to_serialized_data():
            new_scopes.add(scope)

        args.scopes = list(new_scopes)
