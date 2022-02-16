# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.command_modules.monitor._client_factory import _log_analytics_client_factory
from azure.cli.core.commands.transform import _parse_id
from azure.mgmt.loganalytics.models import WorkspaceSkuNameEnum, Workspace, WorkspaceSku, WorkspaceCapping, Table,\
    Schema, Column, SearchResults, ColumnTypeEnum
from azure.cli.core.util import sdk_no_wait
from azure.cli.core.azclierror import ArgumentUsageError, InvalidArgumentValueError
from knack.util import CLIError


def create_log_analytics_workspace(client, resource_group_name, workspace_name, location=None, tags=None,
                                   sku=WorkspaceSkuNameEnum.per_gb2018.value, capacity_reservation_level=None,
                                   retention_time=None, daily_quota_gb=None,
                                   public_network_access_for_query=None, public_network_access_for_ingestion=None,
                                   no_wait=False):
    if sku.lower() == WorkspaceSkuNameEnum.capacity_reservation.value.lower() and capacity_reservation_level is None:
        raise CLIError('--capacity-reservation-level must be set when sku is CapacityReservation.')
    if sku.lower() != WorkspaceSkuNameEnum.capacity_reservation.value.lower() and capacity_reservation_level:
        raise CLIError('--capacity-reservation-level can be set only when sku is CapacityReservation.')

    workspace_client = client
    sku = WorkspaceSku(name=sku, capacity_reservation_level=capacity_reservation_level)
    workspace_capping = WorkspaceCapping(daily_quota_gb=daily_quota_gb)
    workspace_instance = Workspace(location=location,
                                   tags=tags,
                                   sku=sku,
                                   workspace_capping=workspace_capping,
                                   retention_in_days=retention_time,
                                   public_network_access_for_query=public_network_access_for_query,
                                   public_network_access_for_ingestion=public_network_access_for_ingestion)
    return sdk_no_wait(no_wait, workspace_client.begin_create_or_update, resource_group_name,
                       workspace_name, workspace_instance)


def update_log_analytics_workspace(instance, tags=None, capacity_reservation_level=None,
                                   retention_time=None, daily_quota_gb=None,
                                   public_network_access_for_query=None, public_network_access_for_ingestion=None,
                                   default_data_collection_rule_resource_id=None):
    if tags is not None:
        instance.tags = tags
    if capacity_reservation_level is not None:
        if instance.sku.name.lower() != WorkspaceSkuNameEnum.capacity_reservation.value.lower():
            raise CLIError('--capacity-reservation-level can be set only when sku is CapacityReservation.')
        instance.sku.capacity_reservation_level = capacity_reservation_level
    if retention_time is not None:
        instance.retention_in_days = retention_time
    if daily_quota_gb is not None:
        instance.workspace_capping.daily_quota_gb = daily_quota_gb
    if public_network_access_for_query is not None:
        instance.public_network_access_for_query = public_network_access_for_query
    if public_network_access_for_ingestion is not None:
        instance.public_network_access_for_ingestion = public_network_access_for_ingestion
    if default_data_collection_rule_resource_id is not None:
        instance.default_data_collection_rule_resource_id = default_data_collection_rule_resource_id
    return instance


def list_log_analytics_workspace(client, resource_group_name=None):
    workspace_client = client
    if resource_group_name:
        return workspace_client.list_by_resource_group(resource_group_name)
    return workspace_client.list()


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


def create_log_analytics_workspace_data_exports(client, workspace_name, resource_group_name, data_export_name,
                                                destination, data_export_type, table_names,
                                                event_hub_name=None, enable=None):
    from azure.mgmt.loganalytics.models import DataExport
    data_export = DataExport(resource_id=destination,
                             data_export_type=data_export_type,
                             table_names=table_names,
                             event_hub_name=event_hub_name,
                             enable=enable)
    return client.create_or_update(resource_group_name, workspace_name, data_export_name, data_export)


def update_log_analytics_workspace_data_exports(cmd, instance, table_names, destination=None, data_export_type=None,
                                                event_hub_name=None, enable=None):
    with cmd.update_context(instance) as c:
        c.set_param('resource_id', destination)
        c.set_param('data_export_type', data_export_type)
        c.set_param('table_names', table_names)
        c.set_param('event_hub_name', event_hub_name)
        c.set_param('enable', enable)
    return instance


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
            raise ArgumentUsageError('Usage error: When using --description, --columns must be provided')
        schema = Schema(name=table_name, columns=columns_list, description=description)
    table = Table(retention_in_days=retention_in_days,
                  total_retention_in_days=total_retention_in_days,
                  schema=schema,
                  plan=plan
                  )
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name,
                       workspace_name, table_name, table)


def create_log_analytics_workspace_table_search_job(client, resource_group_name, workspace_name, table_name,
                                                    retention_in_days=None, total_retention_in_days=None,
                                                    search_query=None, limit=None, start_search_time=None,
                                                    end_search_time=None, no_wait=False):
    search_results = None
    if search_query is not None or limit is not None or start_search_time is not None or end_search_time is not None:
        search_results = SearchResults(query=search_query, limit=limit, start_search_time=start_search_time,
                                       end_search_time=end_search_time)
    table = Table(retention_in_days=retention_in_days,
                  total_retention_in_days=total_retention_in_days,
                  search_results=search_results,
                  )
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
