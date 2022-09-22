# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.monitor._client_factory import _log_analytics_client_factory
from azure.cli.core.commands.transform import _parse_id
from azure.mgmt.loganalytics.models import WorkspaceSkuNameEnum, Workspace, WorkspaceSku, WorkspaceCapping, Table,\
    Schema, Column, SearchResults, RestoredLogs, ColumnTypeEnum
from azure.cli.core.util import sdk_no_wait
from azure.cli.core.azclierror import ArgumentUsageError, InvalidArgumentValueError, RequiredArgumentMissingError
from knack.util import CLIError

from azure.cli.command_modules.monitor.aaz.latest.monitor.log_analytics.workspace.data_export import \
    Create as _WorkspaceDataExportCreate, \
    Update as _WorkspaceDataExportUpdate

def list_deleted_log_analytics_workspaces(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def recover_log_analytics_workspace(cmd, workspace_name, resource_group_name=None, no_wait=False):
    deleted_workspaces_client = _log_analytics_client_factory(cmd.cli_ctx).deleted_workspaces
    workspace_client = _log_analytics_client_factory(cmd.cli_ctx).workspaces
    deleted_workspaces = list(list_deleted_log_analytics_workspaces(deleted_workspaces_client, resource_group_name))
    for deleted_workspace in deleted_workspaces:
        if deleted_workspace.name.lower() == workspace_name.lower():
            workspace_instance = Workspace(location=deleted_workspace.location)

            return sdk_no_wait(no_wait, workspace_client.begin_create_or_update,
                               _parse_id(deleted_workspace.id)['resource-group'],
                               workspace_name, workspace_instance)

    raise CLIError('{} is not a deleted workspace and you can only recover a deleted workspace within 14 days.'
                   .format(workspace_name))


def _format_tags(tags):
    from azure.mgmt.loganalytics.models import Tag
    if tags:
        tags = [Tag(name=key, value=value) for key, value in tags.items()]
    return tags


def create_log_analytics_workspace_saved_search(client, workspace_name, resource_group_name, saved_search_id,
                                                category, display_name, saved_query,
                                                function_alias=None, function_parameters=None,
                                                tags=None):
    from azure.mgmt.loganalytics.models import SavedSearch
    saved_search = SavedSearch(category=category,
                               display_name=display_name,
                               query=saved_query,
                               function_alias=function_alias,
                               function_parameters=function_parameters,
                               tags=_format_tags(tags))
    return client.create_or_update(resource_group_name=resource_group_name,
                                   workspace_name=workspace_name,
                                   saved_search_id=saved_search_id,
                                   parameters=saved_search)


def update_log_analytics_workspace_saved_search(cmd, instance, category=None, display_name=None, saved_query=None,
                                                function_alias=None, function_parameters=None,
                                                tags=None):
    with cmd.update_context(instance) as c:
        c.set_param('category', category)
        c.set_param('display_name', display_name)
        c.set_param('query', saved_query)
        c.set_param('function_alias', function_alias)
        c.set_param('function_parameters', function_parameters)
        c.set_param('tags', _format_tags(tags))
    return instance


class WorkspaceDataExportCreate(_WorkspaceDataExportCreate):

    def pre_operations(self):
        args = self.ctx.args
        destination = str(args.destination)
        from azure.mgmt.core.tools import is_valid_resource_id, resource_id, parse_resource_id
        from azure.cli.core.azclierror import InvalidArgumentValueError
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
            from azure.cli.core.azclierror import InvalidArgumentValueError
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


# pylint:disable=too-many-locals dangerous-default-value
def create_log_analytics_workspace_table(client, resource_group_name, workspace_name, table_name, columns=[],
                                         retention_in_days=None, total_retention_in_days=None, plan=None,
                                         description=None, no_wait=False):
    if retention_in_days and total_retention_in_days:
        if total_retention_in_days < retention_in_days:
            InvalidArgumentValueError('InvalidArgumentValueError: The specified value of --retention-time'
                                      ' should be less than --total-retention-time')
    columns_list = [] if columns else None
    for col in columns:
        if '=' in col:
            n, t = col.split('=', 1)
            if t.lower() not in [x.value.lower() for x in ColumnTypeEnum]:
                raise InvalidArgumentValueError('InvalidArgumentValueError: "{}" is not a valid value for type_name. '
                                                'Allowed values: string, int, long, real, boolean, dateTime, guid, '
                                                'dynamic".'.format(t))
        else:
            raise ArgumentUsageError('Usage error: --columns should be provided in colunm_name=colunm_type format')
        columns_list.append(Column(name=n, type=t))
    schema = None
    if columns or description is not None:
        if not columns:
            raise RequiredArgumentMissingError('Usage error: When using --description, --columns must be provided')
        schema = Schema(name=table_name, columns=columns_list, description=description)
    table = Table(retention_in_days=retention_in_days,
                  total_retention_in_days=total_retention_in_days,
                  schema=schema,
                  plan=plan
                  )
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name,
                       workspace_name, table_name, table)


def create_log_analytics_workspace_table_search_job(client, resource_group_name, workspace_name, table_name,
                                                    search_query, start_search_time, end_search_time,
                                                    retention_in_days=None, total_retention_in_days=None, limit=None,
                                                    no_wait=False):
    search_results = SearchResults(query=search_query, limit=limit, start_search_time=start_search_time,
                                   end_search_time=end_search_time)
    table = Table(retention_in_days=retention_in_days,
                  total_retention_in_days=total_retention_in_days,
                  search_results=search_results,
                  )
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name,
                       workspace_name, table_name, table)


def create_log_analytics_workspace_table_restore(client, resource_group_name, workspace_name, table_name,
                                                 start_restore_time, end_restore_time, restore_source_table,
                                                 no_wait=False):
    restored_logs = RestoredLogs(start_restore_time=start_restore_time,
                                 end_restore_time=end_restore_time,
                                 source_table=restore_source_table)
    table = Table(restored_logs=restored_logs)
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name,
                       workspace_name, table_name, table)


def update_log_analytics_workspace_table(client, resource_group_name, workspace_name, table_name, columns=[],
                                         retention_in_days=None, total_retention_in_days=None, plan=None,
                                         description=None, no_wait=False):
    columns_list = [] if columns else None
    for col in columns:
        if '=' in col:
            n, t = col.split('=', 1)
            if t.lower() not in [x.value.lower() for x in ColumnTypeEnum]:
                raise InvalidArgumentValueError('InvalidArgumentValueError: "{}" is not a valid value for type_name. '
                                                'Allowed values: string, int, long, real, boolean, dateTime, guid, '
                                                'dynamic".'.format(t))
        else:
            raise ArgumentUsageError('Usage error: --columns should be provided in colunm_name=colunm_type format')
        columns_list.append(Column(name=n, type=t))
    schema = None
    if columns or description is not None:
        schema = Schema(name=table_name, columns=columns_list, description=description)
    table = Table(retention_in_days=retention_in_days,
                  total_retention_in_days=total_retention_in_days,
                  schema=schema,
                  plan=plan
                  )
    return sdk_no_wait(no_wait, client.begin_update, resource_group_name, workspace_name, table_name, table)
