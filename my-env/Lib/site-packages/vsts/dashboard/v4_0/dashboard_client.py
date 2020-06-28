# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest import Serializer, Deserializer
from ...vss_client import VssClient
from . import models


class DashboardClient(VssClient):
    """Dashboard
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(DashboardClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = '31c84e0a-3ece-48fd-a29d-100849af99ba'

    def create_dashboard(self, dashboard, team_context):
        """CreateDashboard.
        [Preview API]
        :param :class:`<Dashboard> <dashboard.v4_0.models.Dashboard>` dashboard:
        :param :class:`<TeamContext> <dashboard.v4_0.models.TeamContext>` team_context: The team context for the operation
        :rtype: :class:`<Dashboard> <dashboard.v4_0.models.Dashboard>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        content = self._serialize.body(dashboard, 'Dashboard')
        response = self._send(http_method='POST',
                              location_id='454b3e51-2e6e-48d4-ad81-978154089351',
                              version='4.0-preview.2',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Dashboard', response)

    def delete_dashboard(self, team_context, dashboard_id):
        """DeleteDashboard.
        [Preview API]
        :param :class:`<TeamContext> <dashboard.v4_0.models.TeamContext>` team_context: The team context for the operation
        :param str dashboard_id:
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if dashboard_id is not None:
            route_values['dashboardId'] = self._serialize.url('dashboard_id', dashboard_id, 'str')
        self._send(http_method='DELETE',
                   location_id='454b3e51-2e6e-48d4-ad81-978154089351',
                   version='4.0-preview.2',
                   route_values=route_values)

    def get_dashboard(self, team_context, dashboard_id):
        """GetDashboard.
        [Preview API]
        :param :class:`<TeamContext> <dashboard.v4_0.models.TeamContext>` team_context: The team context for the operation
        :param str dashboard_id:
        :rtype: :class:`<Dashboard> <dashboard.v4_0.models.Dashboard>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if dashboard_id is not None:
            route_values['dashboardId'] = self._serialize.url('dashboard_id', dashboard_id, 'str')
        response = self._send(http_method='GET',
                              location_id='454b3e51-2e6e-48d4-ad81-978154089351',
                              version='4.0-preview.2',
                              route_values=route_values)
        return self._deserialize('Dashboard', response)

    def get_dashboards(self, team_context):
        """GetDashboards.
        [Preview API]
        :param :class:`<TeamContext> <dashboard.v4_0.models.TeamContext>` team_context: The team context for the operation
        :rtype: :class:`<DashboardGroup> <dashboard.v4_0.models.DashboardGroup>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        response = self._send(http_method='GET',
                              location_id='454b3e51-2e6e-48d4-ad81-978154089351',
                              version='4.0-preview.2',
                              route_values=route_values)
        return self._deserialize('DashboardGroup', response)

    def replace_dashboard(self, dashboard, team_context, dashboard_id):
        """ReplaceDashboard.
        [Preview API]
        :param :class:`<Dashboard> <dashboard.v4_0.models.Dashboard>` dashboard:
        :param :class:`<TeamContext> <dashboard.v4_0.models.TeamContext>` team_context: The team context for the operation
        :param str dashboard_id:
        :rtype: :class:`<Dashboard> <dashboard.v4_0.models.Dashboard>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if dashboard_id is not None:
            route_values['dashboardId'] = self._serialize.url('dashboard_id', dashboard_id, 'str')
        content = self._serialize.body(dashboard, 'Dashboard')
        response = self._send(http_method='PUT',
                              location_id='454b3e51-2e6e-48d4-ad81-978154089351',
                              version='4.0-preview.2',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Dashboard', response)

    def replace_dashboards(self, group, team_context):
        """ReplaceDashboards.
        [Preview API]
        :param :class:`<DashboardGroup> <dashboard.v4_0.models.DashboardGroup>` group:
        :param :class:`<TeamContext> <dashboard.v4_0.models.TeamContext>` team_context: The team context for the operation
        :rtype: :class:`<DashboardGroup> <dashboard.v4_0.models.DashboardGroup>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        content = self._serialize.body(group, 'DashboardGroup')
        response = self._send(http_method='PUT',
                              location_id='454b3e51-2e6e-48d4-ad81-978154089351',
                              version='4.0-preview.2',
                              route_values=route_values,
                              content=content)
        return self._deserialize('DashboardGroup', response)

    def create_widget(self, widget, team_context, dashboard_id):
        """CreateWidget.
        [Preview API]
        :param :class:`<Widget> <dashboard.v4_0.models.Widget>` widget:
        :param :class:`<TeamContext> <dashboard.v4_0.models.TeamContext>` team_context: The team context for the operation
        :param str dashboard_id:
        :rtype: :class:`<Widget> <dashboard.v4_0.models.Widget>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if dashboard_id is not None:
            route_values['dashboardId'] = self._serialize.url('dashboard_id', dashboard_id, 'str')
        content = self._serialize.body(widget, 'Widget')
        response = self._send(http_method='POST',
                              location_id='bdcff53a-8355-4172-a00a-40497ea23afc',
                              version='4.0-preview.2',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Widget', response)

    def delete_widget(self, team_context, dashboard_id, widget_id):
        """DeleteWidget.
        [Preview API]
        :param :class:`<TeamContext> <dashboard.v4_0.models.TeamContext>` team_context: The team context for the operation
        :param str dashboard_id:
        :param str widget_id:
        :rtype: :class:`<Dashboard> <dashboard.v4_0.models.Dashboard>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if dashboard_id is not None:
            route_values['dashboardId'] = self._serialize.url('dashboard_id', dashboard_id, 'str')
        if widget_id is not None:
            route_values['widgetId'] = self._serialize.url('widget_id', widget_id, 'str')
        response = self._send(http_method='DELETE',
                              location_id='bdcff53a-8355-4172-a00a-40497ea23afc',
                              version='4.0-preview.2',
                              route_values=route_values)
        return self._deserialize('Dashboard', response)

    def get_widget(self, team_context, dashboard_id, widget_id):
        """GetWidget.
        [Preview API]
        :param :class:`<TeamContext> <dashboard.v4_0.models.TeamContext>` team_context: The team context for the operation
        :param str dashboard_id:
        :param str widget_id:
        :rtype: :class:`<Widget> <dashboard.v4_0.models.Widget>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if dashboard_id is not None:
            route_values['dashboardId'] = self._serialize.url('dashboard_id', dashboard_id, 'str')
        if widget_id is not None:
            route_values['widgetId'] = self._serialize.url('widget_id', widget_id, 'str')
        response = self._send(http_method='GET',
                              location_id='bdcff53a-8355-4172-a00a-40497ea23afc',
                              version='4.0-preview.2',
                              route_values=route_values)
        return self._deserialize('Widget', response)

    def get_widgets(self, team_context, dashboard_id, eTag=None):
        """GetWidgets.
        [Preview API]
        :param :class:`<TeamContext> <dashboard.v4_0.models.TeamContext>` team_context: The team context for the operation
        :param str dashboard_id:
        :param String eTag: Dashboard Widgets Version
        :rtype: :class:`<WidgetsVersionedList> <dashboard.v4_0.models.WidgetsVersionedList>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if dashboard_id is not None:
            route_values['dashboardId'] = self._serialize.url('dashboard_id', dashboard_id, 'str')
        response = self._send(http_method='GET',
                              location_id='bdcff53a-8355-4172-a00a-40497ea23afc',
                              version='4.0-preview.2',
                              route_values=route_values)
        response_object = models.WidgetsVersionedList()
        response_object.widgets = self._deserialize('[Widget]', self._unwrap_collection(response))
        response_object.eTag = response.headers.get('ETag')
        return response_object

    def replace_widget(self, widget, team_context, dashboard_id, widget_id):
        """ReplaceWidget.
        [Preview API]
        :param :class:`<Widget> <dashboard.v4_0.models.Widget>` widget:
        :param :class:`<TeamContext> <dashboard.v4_0.models.TeamContext>` team_context: The team context for the operation
        :param str dashboard_id:
        :param str widget_id:
        :rtype: :class:`<Widget> <dashboard.v4_0.models.Widget>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if dashboard_id is not None:
            route_values['dashboardId'] = self._serialize.url('dashboard_id', dashboard_id, 'str')
        if widget_id is not None:
            route_values['widgetId'] = self._serialize.url('widget_id', widget_id, 'str')
        content = self._serialize.body(widget, 'Widget')
        response = self._send(http_method='PUT',
                              location_id='bdcff53a-8355-4172-a00a-40497ea23afc',
                              version='4.0-preview.2',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Widget', response)

    def replace_widgets(self, widgets, team_context, dashboard_id, eTag=None):
        """ReplaceWidgets.
        [Preview API]
        :param [Widget] widgets:
        :param :class:`<TeamContext> <dashboard.v4_0.models.TeamContext>` team_context: The team context for the operation
        :param str dashboard_id:
        :param String eTag: Dashboard Widgets Version
        :rtype: :class:`<WidgetsVersionedList> <dashboard.v4_0.models.WidgetsVersionedList>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if dashboard_id is not None:
            route_values['dashboardId'] = self._serialize.url('dashboard_id', dashboard_id, 'str')
        content = self._serialize.body(widgets, '[Widget]')
        response = self._send(http_method='PUT',
                              location_id='bdcff53a-8355-4172-a00a-40497ea23afc',
                              version='4.0-preview.2',
                              route_values=route_values,
                              content=content)
        response_object = models.WidgetsVersionedList()
        response_object.widgets = self._deserialize('[Widget]', self._unwrap_collection(response))
        response_object.eTag = response.headers.get('ETag')
        return response_object

    def update_widget(self, widget, team_context, dashboard_id, widget_id):
        """UpdateWidget.
        [Preview API]
        :param :class:`<Widget> <dashboard.v4_0.models.Widget>` widget:
        :param :class:`<TeamContext> <dashboard.v4_0.models.TeamContext>` team_context: The team context for the operation
        :param str dashboard_id:
        :param str widget_id:
        :rtype: :class:`<Widget> <dashboard.v4_0.models.Widget>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if dashboard_id is not None:
            route_values['dashboardId'] = self._serialize.url('dashboard_id', dashboard_id, 'str')
        if widget_id is not None:
            route_values['widgetId'] = self._serialize.url('widget_id', widget_id, 'str')
        content = self._serialize.body(widget, 'Widget')
        response = self._send(http_method='PATCH',
                              location_id='bdcff53a-8355-4172-a00a-40497ea23afc',
                              version='4.0-preview.2',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Widget', response)

    def update_widgets(self, widgets, team_context, dashboard_id, eTag=None):
        """UpdateWidgets.
        [Preview API]
        :param [Widget] widgets:
        :param :class:`<TeamContext> <dashboard.v4_0.models.TeamContext>` team_context: The team context for the operation
        :param str dashboard_id:
        :param String eTag: Dashboard Widgets Version
        :rtype: :class:`<WidgetsVersionedList> <dashboard.v4_0.models.WidgetsVersionedList>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if dashboard_id is not None:
            route_values['dashboardId'] = self._serialize.url('dashboard_id', dashboard_id, 'str')
        content = self._serialize.body(widgets, '[Widget]')
        response = self._send(http_method='PATCH',
                              location_id='bdcff53a-8355-4172-a00a-40497ea23afc',
                              version='4.0-preview.2',
                              route_values=route_values,
                              content=content)
        response_object = models.WidgetsVersionedList()
        response_object.widgets = self._deserialize('[Widget]', self._unwrap_collection(response))
        response_object.eTag = response.headers.get('ETag')
        return response_object

    def get_widget_metadata(self, contribution_id):
        """GetWidgetMetadata.
        [Preview API]
        :param str contribution_id:
        :rtype: :class:`<WidgetMetadataResponse> <dashboard.v4_0.models.WidgetMetadataResponse>`
        """
        route_values = {}
        if contribution_id is not None:
            route_values['contributionId'] = self._serialize.url('contribution_id', contribution_id, 'str')
        response = self._send(http_method='GET',
                              location_id='6b3628d3-e96f-4fc7-b176-50240b03b515',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('WidgetMetadataResponse', response)

    def get_widget_types(self, scope):
        """GetWidgetTypes.
        [Preview API] Returns available widgets in alphabetical order.
        :param str scope:
        :rtype: :class:`<WidgetTypesResponse> <dashboard.v4_0.models.WidgetTypesResponse>`
        """
        query_parameters = {}
        if scope is not None:
            query_parameters['$scope'] = self._serialize.query('scope', scope, 'str')
        response = self._send(http_method='GET',
                              location_id='6b3628d3-e96f-4fc7-b176-50240b03b515',
                              version='4.0-preview.1',
                              query_parameters=query_parameters)
        return self._deserialize('WidgetTypesResponse', response)

