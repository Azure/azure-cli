# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.core.aaz import has_value
from azure.cli.command_modules.monitor.aaz.latest.monitor.log_analytics.workspace.table._update \
    import Update as _WorkspaceTableUpdate


class WorkspaceTableUpdate(_WorkspaceTableUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZIntArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.total_retention_in_days._fmt = AAZIntArgFormat(
            maximum=4383,
            minimum=-1,
        )
        args_schema.retention_in_days._fmt = AAZIntArgFormat(
            maximum=730,
            minimum=-1,
        )
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.retention_in_days):
            retention_time = args.retention_in_days.to_serialized_data()
            if retention_time == -1 or (4 <= retention_time <= 730):
                pass
            else:
                raise InvalidArgumentValueError("usage error: --retention-time should between 4 and 730. "
                                                "Otherwise setting this property to -1 will default to "
                                                "workspace retention.")

        if has_value(args.total_retention_in_days):
            total_retention_time = args.total_retention_in_days.to_serialized_data()
            if total_retention_time == -1 or (4 <= total_retention_time <= 4383):
                pass
            else:
                raise InvalidArgumentValueError("usage error: --total-retention-time should between 4 and 4383. "
                                                "Otherwise setting this property to -1 will default to "
                                                "table retention.")
