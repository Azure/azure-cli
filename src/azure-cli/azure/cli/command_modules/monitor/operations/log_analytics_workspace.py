# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=protected-access


def list_deleted_log_analytics_workspaces(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def recover_log_analytics_workspace(cmd, workspace_name, resource_group_name=None, no_wait=False):
    from azure.cli.core.azclierror import InvalidArgumentValueError
    from azure.cli.core.commands.transform import _parse_id
    from azure.cli.command_modules.monitor.aaz.latest.monitor.log_analytics.workspace._create import Create
    from azure.cli.command_modules.monitor.aaz.latest.monitor.log_analytics.workspace._list_deleted_workspaces \
        import ListDeletedWorkspaces

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
    from azure.cli.command_modules.monitor.aaz.latest.monitor.log_analytics.workspace.saved_search._create \
        import Create

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
    from azure.cli.command_modules.monitor.aaz.latest.monitor.log_analytics.workspace.saved_search._update \
        import Update
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


# pylint:disable=too-many-locals
def create_log_analytics_workspace_table(cmd, resource_group_name, workspace_name, table_name, columns=None,
                                         retention_in_days=None, total_retention_in_days=None, plan=None,
                                         description=None, no_wait=False):
    from azure.cli.core.azclierror import InvalidArgumentValueError, ArgumentUsageError, RequiredArgumentMissingError
    from azure.cli.command_modules.monitor.operations.latest.monitor.log_analytics.workspace.table._create \
        import WorkspaceTableCreate

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
    from azure.cli.command_modules.monitor.operations.latest.monitor.log_analytics.workspace.table._create \
        import WorkspaceTableCreate

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
    from azure.cli.command_modules.monitor.operations.latest.monitor.log_analytics.workspace.table._create \
        import WorkspaceTableCreate

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
    from azure.cli.core.azclierror import ArgumentUsageError
    from azure.cli.command_modules.monitor.operations.latest.monitor.log_analytics.workspace.table._update \
        import WorkspaceTableUpdate

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
