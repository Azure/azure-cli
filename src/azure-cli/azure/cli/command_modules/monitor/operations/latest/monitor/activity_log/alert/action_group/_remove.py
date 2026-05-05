# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access, line-too-long

from azure.cli.core.aaz import AAZStrArg, AAZListArg, register_command
from azure.cli.command_modules.monitor.aaz.latest.monitor.activity_log.alert._update \
    import Update as _ActivityLogAlertUpdate
from azure.cli.command_modules.monitor.operations.activity_log_alerts import normalize_names


@register_command("monitor activity-log alert action-group remove")
class ActivityLogAlertActionGroupRemove(_ActivityLogAlertUpdate):
    """Remove action groups from this activity log alert rule.
    """

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.action_groups._registered = False
        args_schema.all_of._registered = False
        args_schema.description._registered = False
        args_schema.enabled._registered = False
        args_schema.scopes._registered = False
        args_schema.tags._registered = False
        args_schema.action_group_ids = AAZListArg(
            options=["--action-group", "-a"],
            required=True,
            help="The names or the resource ids of the action groups to be added.",
        )
        args_schema.action_group_ids.Element = AAZStrArg()
        return args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args
        action_group_ids = args.action_group_ids.to_serialized_data()
        if len(action_group_ids) == 1 and action_group_ids[0] == '*':
            instance.properties.actions.actionGroups = []
        else:
            # normalize the action group ids
            rids = normalize_names(self.cli_ctx, args.action_group_ids.to_serialized_data(), args.resource_group,
                                   'microsoft.insights', 'actionGroups')
            action_groups = []
            for item in instance.properties.actions.actionGroups:
                ac_id = item.actionGroupId.to_serialized_data()
                found = False
                for rid in rids:
                    if ac_id.lower() == rid.lower():  # service returned action group id can be uppercase
                        found = True
                        break
                if not found:
                    action_groups.append(item)
            instance.properties.actions.actionGroups = action_groups
