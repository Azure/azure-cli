# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

from azure.cli.command_modules.monitor.aaz.latest.monitor.log_analytics.workspace.data_export import \
    Create as _WorkspaceDataExportCreate, \
    Update as _WorkspaceDataExportUpdate
from azure.cli.command_modules.monitor.aaz.latest.monitor.log_analytics.workspace.table import \
    Create as _WorkspaceTableCreate, \
    Update as _WorkspaceTableUpdate
from azure.cli.command_modules.monitor.aaz.latest.monitor.log_analytics.workspace.table.search_job \
    import Cancel as _WorkspaceTableSearchJobCancel

from azure.cli.core.azclierror import ArgumentUsageError, InvalidArgumentValueError, RequiredArgumentMissingError
from azure.cli.core.commands.transform import _parse_id
from azure.cli.core.aaz import has_value


def list_deleted_log_analytics_workspaces(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def recover_log_analytics_workspace(cmd, workspace_name, resource_group_name=None, no_wait=False):
    from azure.cli.command_modules.monitor.aaz.latest.monitor.log_analytics.workspace import Create, \
        ListDeletedWorkspaces

    deleted_workspaces = ListDeletedWorkspaces(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name
    })

    for deleted_workspace in deleted_workspaces:
        if deleted_workspace['name'].lower() == workspace_name.lower():
            resource_group_name = _parse_id(deleted_workspace['id'])['resource-group']
            location = deleted_workspace['location']
            return Create(cli_ctx=cmd.cli_ctx)(command_args={
                "workspace_name": deleted_workspace['name'],
                "resource_group": resource_group_name,
                "location": location,
                "no_wait": no_wait,
            })

    raise InvalidArgumentValueError('{} is not a deleted workspace and you can only recover a deleted workspace '
                                    'within 14 days.'.format(workspace_name))


def _format_tags(tags):
    if tags:
        tags = [{"name": key, "value": value} for key, value in tags.items()]
    return tags


def create_log_analytics_workspace_saved_search(cmd, workspace_name, resource_group_name, saved_search_id,
                                                category, display_name, saved_query,
                                                function_alias=None, function_parameters=None,
                                                tags=None):
    from azure.cli.command_modules.monitor.aaz.latest.monitor.log_analytics.workspace.saved_search import Create

    command_args = {
        "resource_group": resource_group_name,
        "saved_search_name": saved_search_id,
        "workspace_name": workspace_name,
        "category": category,
        "display_name": display_name,
        "saved_query": saved_query,
    }
    if function_alias is not None:
        command_args['func_alias'] = function_alias
    if function_parameters is not None:
        command_args['func_param'] = function_parameters
    if tags is not None:
        command_args['tags'] = _format_tags(tags)
    return Create(cli_ctx=cmd.cli_ctx)(
        command_args=command_args
    )


def update_log_analytics_workspace_saved_search(cmd, workspace_name, resource_group_name, saved_search_id,
                                                category=None, display_name=None, saved_query=None,
                                                function_alias=None, function_parameters=None,
                                                tags=None):
    from azure.cli.command_modules.monitor.aaz.latest.monitor.log_analytics.workspace.saved_search import Update
    command_args = {
        "resource_group": resource_group_name,
        "saved_search_name": saved_search_id,
        "workspace_name": workspace_name,
    }

    if category is not None:
        command_args['category'] = category
    if display_name is not None:
        command_args['display_name'] = display_name
    if saved_query is not None:
        command_args['saved_query'] = saved_query
    if function_alias is not None:
        command_args['func_alias'] = function_alias
    if function_parameters is not None:
        command_args['func_param'] = function_parameters
    if tags is not None:
        command_args['tags'] = _format_tags(tags)
    return Update(cli_ctx=cmd.cli_ctx)(
        command_args=command_args
    )


class WorkspaceDataExportCreate(_WorkspaceDataExportCreate):

    def pre_operations(self):
        args = self.ctx.args
        destination = str(args.destination)
        from azure.mgmt.core.tools import is_valid_resource_id, resource_id, parse_resource_id
        if not is_valid_resource_id(destination):
            raise InvalidArgumentValueError('usage error: --destination should be a storage account,'
                                            ' an evenhug namespace or an event hub resource id.')
        result = parse_resource_id(destination)
        if result['namespace'].lower() == 'microsoft.eventhub' and result['type'].lower() == 'namespaces':
            args.destination = resource_id(
                subscription=result['subscription'],
                resource_group=result['resource_group'],
                namespace=result['namespace'],
                type=result['type'],
                name=result['name']
            )
            if 'child_type_1' in result and result['child_type_1'].lower() == 'eventhubs':
                args.event_hub_name = result['child_name_1']
        elif result['namespace'].lower() == 'microsoft.storage' and result['type'].lower() == 'storageaccounts':
            pass
        else:
            raise InvalidArgumentValueError('usage error: --destination should be a storage account,'
                                            ' an evenhug namespace or an event hub resource id.')


class WorkspaceDataExportUpdate(_WorkspaceDataExportUpdate):

    def pre_operations(self):
        args = self.ctx.args
        if args.destination:
            destination = str(args.destination)
            from azure.mgmt.core.tools import is_valid_resource_id, resource_id, parse_resource_id
            if not is_valid_resource_id(destination):
                raise InvalidArgumentValueError('usage error: --destination should be a storage account,'
                                                ' an evenhug namespace or an event hub resource id.')
            result = parse_resource_id(destination)
            if result['namespace'].lower() == 'microsoft.eventhub' and result['type'].lower() == 'namespaces':
                args.destination = resource_id(
                    subscription=result['subscription'],
                    resource_group=result['resource_group'],
                    namespace=result['namespace'],
                    type=result['type'],
                    name=result['name']
                )
                if 'child_type_1' in result and result['child_type_1'].lower() == 'eventhubs':
                    args.event_hub_name = result['child_name_1']
            elif result['namespace'].lower() == 'microsoft.storage' and result['type'].lower() == 'storageaccounts':
                pass
            else:
                raise InvalidArgumentValueError('usage error: --destination should be a storage account,'
                                                ' an evenhug namespace or an event hub resource id.')


class WorkspaceTableCreate(_WorkspaceTableCreate):

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


class WorkspaceTableSearchJobCancel(_WorkspaceTableSearchJobCancel):
    def pre_operations(self):
        args = self.ctx.args
        table_name = args.table_name.to_serialized_data()

        if table_name and not table_name.endswith("_SRCH"):
            raise InvalidArgumentValueError('usage: The table name needs to end with _SRCH')


# pylint:disable=too-many-locals
def create_log_analytics_workspace_table(cmd, resource_group_name, workspace_name, table_name, columns=None,
                                         retention_in_days=None, total_retention_in_days=None, plan=None,
                                         description=None, no_wait=False):
    if retention_in_days and total_retention_in_days:
        if total_retention_in_days < retention_in_days:
            raise InvalidArgumentValueError('InvalidArgumentValueError: The specified value of --retention-time'
                                            ' should be less than --total-retention-time')
    columns_list = None
    if columns:
        columns_list = []
        for col in columns:
            if '=' in col:
                n, t = col.split('=', 1)
            else:
                raise ArgumentUsageError('Usage error: --columns should be provided in colunm_name=colunm_type format')
            columns_list.append({"name": n, "type": t})

    if columns or description is not None:
        if not columns:
            raise RequiredArgumentMissingError('Usage error: When using --description, --columns must be provided')
    return WorkspaceTableCreate(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "table_name": table_name,
        "workspace_name": workspace_name,
        "retention_in_days": retention_in_days,
        "total_retention_in_days": total_retention_in_days,
        "plan": plan,
        "schema": {
            "columns": columns_list,
            "description": description,
            "name": table_name,
        },
        "no_wait": no_wait,
    })


def create_log_analytics_workspace_table_search_job(cmd, resource_group_name, workspace_name, table_name,
                                                    search_query, start_search_time, end_search_time,
                                                    retention_in_days=None, total_retention_in_days=None, limit=None,
                                                    no_wait=False):
    return WorkspaceTableCreate(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "table_name": table_name,
        "workspace_name": workspace_name,
        "retention_in_days": retention_in_days,
        "total_retention_in_days": total_retention_in_days,
        "search_results": {
            "query": search_query,
            "limit": limit,
            "start_search_time": start_search_time,
            "end_search_time": end_search_time,
        },
        "no_wait": no_wait,
    })


def create_log_analytics_workspace_table_restore(cmd, resource_group_name, workspace_name, table_name,
                                                 start_restore_time, end_restore_time, restore_source_table,
                                                 no_wait=False):
    return WorkspaceTableCreate(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "table_name": table_name,
        "workspace_name": workspace_name,
        "restored_logs": {
            "start_restore_time": start_restore_time,
            "end_restore_time": end_restore_time,
            "source_table": restore_source_table,
        },
        "no_wait": no_wait,
    })


def update_log_analytics_workspace_table(cmd, resource_group_name, workspace_name, table_name, columns=None,
                                         retention_in_days=None, total_retention_in_days=None, plan=None,
                                         description=None, no_wait=False):
    columns_list = None
    if columns:
        columns_list = []
        for col in columns:
            if '=' in col:
                n, t = col.split('=', 1)
            else:
                raise ArgumentUsageError('Usage error: --columns should be provided in colunm_name=colunm_type format')
            columns_list.append({"name": n, "type": t})

    command_args = {
        "resource_group": resource_group_name,
        "table_name": table_name,
        "workspace_name": workspace_name,
        "no_wait": no_wait,
    }
    if retention_in_days is not None:
        command_args["retention_in_days"] = retention_in_days
    if total_retention_in_days is not None:
        command_args["total_retention_in_days"] = total_retention_in_days
    if plan is not None:
        command_args["plan"] = plan
    if columns_list or description is not None:
        command_args["schema"] = {"name": table_name}
    if columns_list is not None:
        command_args["schema"]["columns"] = columns_list
    if description is not None:
        command_args["schema"]["description"] = description
    return WorkspaceTableUpdate(cli_ctx=cmd.cli_ctx)(command_args=command_args)
