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


class ProjectAnalysisClient(VssClient):
    """ProjectAnalysis
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(ProjectAnalysisClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = '7658fa33-b1bf-4580-990f-fac5896773d3'

    def get_project_language_analytics(self, project):
        """GetProjectLanguageAnalytics.
        [Preview API]
        :param str project: Project ID or project name
        :rtype: :class:`<ProjectLanguageAnalytics> <project-analysis.v4_1.models.ProjectLanguageAnalytics>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        response = self._send(http_method='GET',
                              location_id='5b02a779-1867-433f-90b7-d23ed5e33e57',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('ProjectLanguageAnalytics', response)

    def get_project_activity_metrics(self, project, from_date, aggregation_type):
        """GetProjectActivityMetrics.
        [Preview API]
        :param str project: Project ID or project name
        :param datetime from_date:
        :param str aggregation_type:
        :rtype: :class:`<ProjectActivityMetrics> <project-analysis.v4_1.models.ProjectActivityMetrics>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if from_date is not None:
            query_parameters['fromDate'] = self._serialize.query('from_date', from_date, 'iso-8601')
        if aggregation_type is not None:
            query_parameters['aggregationType'] = self._serialize.query('aggregation_type', aggregation_type, 'str')
        response = self._send(http_method='GET',
                              location_id='e40ae584-9ea6-4f06-a7c7-6284651b466b',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('ProjectActivityMetrics', response)

    def get_git_repositories_activity_metrics(self, project, from_date, aggregation_type, skip, top):
        """GetGitRepositoriesActivityMetrics.
        [Preview API] Retrieves git activity metrics for repositories matching a specified criteria.
        :param str project: Project ID or project name
        :param datetime from_date: Date from which, the trends are to be fetched.
        :param str aggregation_type: Bucket size on which, trends are to be aggregated.
        :param int skip: The number of repositories to ignore.
        :param int top: The number of repositories for which activity metrics are to be retrieved.
        :rtype: [RepositoryActivityMetrics]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if from_date is not None:
            query_parameters['fromDate'] = self._serialize.query('from_date', from_date, 'iso-8601')
        if aggregation_type is not None:
            query_parameters['aggregationType'] = self._serialize.query('aggregation_type', aggregation_type, 'str')
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        response = self._send(http_method='GET',
                              location_id='df7fbbca-630a-40e3-8aa3-7a3faf66947e',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[RepositoryActivityMetrics]', self._unwrap_collection(response))

    def get_repository_activity_metrics(self, project, repository_id, from_date, aggregation_type):
        """GetRepositoryActivityMetrics.
        [Preview API]
        :param str project: Project ID or project name
        :param str repository_id:
        :param datetime from_date:
        :param str aggregation_type:
        :rtype: :class:`<RepositoryActivityMetrics> <project-analysis.v4_1.models.RepositoryActivityMetrics>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if from_date is not None:
            query_parameters['fromDate'] = self._serialize.query('from_date', from_date, 'iso-8601')
        if aggregation_type is not None:
            query_parameters['aggregationType'] = self._serialize.query('aggregation_type', aggregation_type, 'str')
        response = self._send(http_method='GET',
                              location_id='df7fbbca-630a-40e3-8aa3-7a3faf66947e',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('RepositoryActivityMetrics', response)

