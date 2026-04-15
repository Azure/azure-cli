# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.command_modules.monitor.aaz.latest.monitor.log_analytics.workspace.table.search_job._cancel \
    import Cancel as _WorkspaceTableSearchJobCancel


class WorkspaceTableSearchJobCancel(_WorkspaceTableSearchJobCancel):
    def pre_operations(self):
        args = self.ctx.args
        table_name = args.table_name.to_serialized_data()

        if table_name and not table_name.endswith("_SRCH"):
            raise InvalidArgumentValueError('usage: The table name needs to end with _SRCH')
