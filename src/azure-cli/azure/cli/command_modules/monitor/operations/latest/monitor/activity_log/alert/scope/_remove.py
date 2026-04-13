# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access, line-too-long

from azure.cli.core.aaz import AAZStrArg, AAZListArg, register_command
from azure.cli.command_modules.monitor.aaz.latest.monitor.activity_log.alert._update \
    import Update as _ActivityLogAlertUpdate


@register_command("monitor activity-log alert scope remove")
class ActivityLogAlertScopeRemove(_ActivityLogAlertUpdate):
    """Removes scopes from this activity log alert rule.
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
            help="The scopes to remove.",
        )
        args_schema.scope_ui.Element = AAZStrArg()
        return args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args
        new_scopes = set(instance.properties.scopes.to_serialized_data())
        for scope in args.scope_ui.to_serialized_data():
            try:
                new_scopes.remove(scope)
            except KeyError:
                pass
        args.scopes = list(new_scopes)
