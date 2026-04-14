# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access, line-too-long

from azure.cli.core.aaz import has_value, AAZStrArg
from azure.cli.command_modules.monitor.actions import AAZCustomListArg
from azure.cli.command_modules.monitor.aaz.latest.monitor.activity_log.alert._update \
    import Update as _ActivityLogAlertUpdate
from azure.cli.command_modules.monitor.operations.activity_log_alerts import (
    process_condition_parameter_for_alert,
)


class ActivityLogAlertUpdate(_ActivityLogAlertUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.action_groups._registered = False
        args_schema.scopes._registered = False
        args_schema.condition = AAZCustomListArg(
            options=["--condition", "-c"],
            help="The condition that will cause the alert rule to activate. "
                 "The format is FIELD=VALUE[ and FIELD=VALUE...]" + '''
        The possible values for the field are 'resourceId', 'category', 'caller',
        'level', 'operationName', 'resourceGroup', 'resourceProvider', 'status',
        'subStatus', 'resourceType', or anything beginning with 'properties'.
        '''
        )
        args_schema.condition.Element = AAZStrArg()
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        process_condition_parameter_for_alert(args)
        if not has_value(args.all_of):
            args.all_of.append({
                "field": "category",
                "equals": "ServiceHealth",
            })
        else:
            current_all_of = args.all_of.to_serialized_data()
            category_found = False
            for item in current_all_of:
                if item.get("field", None) == "category":
                    category_found = True
                    break
            if not category_found:
                args.all_of.append({
                    "field": "category",
                    "equals": "ServiceHealth",
                })
