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


class ReleaseClient(VssClient):
    """Release
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(ReleaseClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = 'efc2f575-36ef-48e9-b672-0c6fb4a48ac5'

    def get_agent_artifact_definitions(self, project, release_id):
        """GetAgentArtifactDefinitions.
        [Preview API] Returns the artifact details that automation agent requires
        :param str project: Project ID or project name
        :param int release_id:
        :rtype: [AgentArtifactDefinition]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        response = self._send(http_method='GET',
                              location_id='f2571c27-bf50-4938-b396-32d109ddef26',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[AgentArtifactDefinition]', self._unwrap_collection(response))

    def get_approvals(self, project, assigned_to_filter=None, status_filter=None, release_ids_filter=None, type_filter=None, top=None, continuation_token=None, query_order=None, include_my_group_approvals=None):
        """GetApprovals.
        [Preview API] Get a list of approvals
        :param str project: Project ID or project name
        :param str assigned_to_filter: Approvals assigned to this user.
        :param str status_filter: Approvals with this status. Default is 'pending'.
        :param [int] release_ids_filter: Approvals for release id(s) mentioned in the filter. Multiple releases can be mentioned by separating them with ',' e.g. releaseIdsFilter=1,2,3,4.
        :param str type_filter: Approval with this type.
        :param int top: Number of approvals to get. Default is 50.
        :param int continuation_token: Gets the approvals after the continuation token provided.
        :param str query_order: Gets the results in the defined order of created approvals. Default is 'descending'.
        :param bool include_my_group_approvals: 'true' to include my group approvals. Default is 'false'.
        :rtype: [ReleaseApproval]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if assigned_to_filter is not None:
            query_parameters['assignedToFilter'] = self._serialize.query('assigned_to_filter', assigned_to_filter, 'str')
        if status_filter is not None:
            query_parameters['statusFilter'] = self._serialize.query('status_filter', status_filter, 'str')
        if release_ids_filter is not None:
            release_ids_filter = ",".join(map(str, release_ids_filter))
            query_parameters['releaseIdsFilter'] = self._serialize.query('release_ids_filter', release_ids_filter, 'str')
        if type_filter is not None:
            query_parameters['typeFilter'] = self._serialize.query('type_filter', type_filter, 'str')
        if top is not None:
            query_parameters['top'] = self._serialize.query('top', top, 'int')
        if continuation_token is not None:
            query_parameters['continuationToken'] = self._serialize.query('continuation_token', continuation_token, 'int')
        if query_order is not None:
            query_parameters['queryOrder'] = self._serialize.query('query_order', query_order, 'str')
        if include_my_group_approvals is not None:
            query_parameters['includeMyGroupApprovals'] = self._serialize.query('include_my_group_approvals', include_my_group_approvals, 'bool')
        response = self._send(http_method='GET',
                              location_id='b47c6458-e73b-47cb-a770-4df1e8813a91',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[ReleaseApproval]', self._unwrap_collection(response))

    def get_approval_history(self, project, approval_step_id):
        """GetApprovalHistory.
        [Preview API] Get approval history.
        :param str project: Project ID or project name
        :param int approval_step_id: Id of the approval.
        :rtype: :class:`<ReleaseApproval> <release.v4_0.models.ReleaseApproval>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if approval_step_id is not None:
            route_values['approvalStepId'] = self._serialize.url('approval_step_id', approval_step_id, 'int')
        response = self._send(http_method='GET',
                              location_id='250c7158-852e-4130-a00f-a0cce9b72d05',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('ReleaseApproval', response)

    def get_approval(self, project, approval_id, include_history=None):
        """GetApproval.
        [Preview API] Get an approval.
        :param str project: Project ID or project name
        :param int approval_id: Id of the approval.
        :param bool include_history: 'true' to include history of the approval. Default is 'false'.
        :rtype: :class:`<ReleaseApproval> <release.v4_0.models.ReleaseApproval>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if approval_id is not None:
            route_values['approvalId'] = self._serialize.url('approval_id', approval_id, 'int')
        query_parameters = {}
        if include_history is not None:
            query_parameters['includeHistory'] = self._serialize.query('include_history', include_history, 'bool')
        response = self._send(http_method='GET',
                              location_id='9328e074-59fb-465a-89d9-b09c82ee5109',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('ReleaseApproval', response)

    def update_release_approval(self, approval, project, approval_id):
        """UpdateReleaseApproval.
        [Preview API] Update status of an approval
        :param :class:`<ReleaseApproval> <release.v4_0.models.ReleaseApproval>` approval: ReleaseApproval object having status, approver and comments.
        :param str project: Project ID or project name
        :param int approval_id: Id of the approval.
        :rtype: :class:`<ReleaseApproval> <release.v4_0.models.ReleaseApproval>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if approval_id is not None:
            route_values['approvalId'] = self._serialize.url('approval_id', approval_id, 'int')
        content = self._serialize.body(approval, 'ReleaseApproval')
        response = self._send(http_method='PATCH',
                              location_id='9328e074-59fb-465a-89d9-b09c82ee5109',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('ReleaseApproval', response)

    def update_release_approvals(self, approvals, project):
        """UpdateReleaseApprovals.
        [Preview API]
        :param [ReleaseApproval] approvals:
        :param str project: Project ID or project name
        :rtype: [ReleaseApproval]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(approvals, '[ReleaseApproval]')
        response = self._send(http_method='PATCH',
                              location_id='c957584a-82aa-4131-8222-6d47f78bfa7a',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[ReleaseApproval]', self._unwrap_collection(response))

    def get_auto_trigger_issues(self, artifact_type, source_id, artifact_version_id):
        """GetAutoTriggerIssues.
        [Preview API]
        :param str artifact_type:
        :param str source_id:
        :param str artifact_version_id:
        :rtype: [AutoTriggerIssue]
        """
        query_parameters = {}
        if artifact_type is not None:
            query_parameters['artifactType'] = self._serialize.query('artifact_type', artifact_type, 'str')
        if source_id is not None:
            query_parameters['sourceId'] = self._serialize.query('source_id', source_id, 'str')
        if artifact_version_id is not None:
            query_parameters['artifactVersionId'] = self._serialize.query('artifact_version_id', artifact_version_id, 'str')
        response = self._send(http_method='GET',
                              location_id='c1a68497-69da-40fb-9423-cab19cfeeca9',
                              version='4.0-preview.1',
                              query_parameters=query_parameters)
        return self._deserialize('[AutoTriggerIssue]', self._unwrap_collection(response))

    def get_release_changes(self, project, release_id, base_release_id=None, top=None):
        """GetReleaseChanges.
        [Preview API]
        :param str project: Project ID or project name
        :param int release_id:
        :param int base_release_id:
        :param int top:
        :rtype: [Change]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        query_parameters = {}
        if base_release_id is not None:
            query_parameters['baseReleaseId'] = self._serialize.query('base_release_id', base_release_id, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        response = self._send(http_method='GET',
                              location_id='8dcf9fe9-ca37-4113-8ee1-37928e98407c',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[Change]', self._unwrap_collection(response))

    def get_definition_environments(self, project, task_group_id=None, property_filters=None):
        """GetDefinitionEnvironments.
        [Preview API]
        :param str project: Project ID or project name
        :param str task_group_id:
        :param [str] property_filters:
        :rtype: [DefinitionEnvironmentReference]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if task_group_id is not None:
            query_parameters['taskGroupId'] = self._serialize.query('task_group_id', task_group_id, 'str')
        if property_filters is not None:
            property_filters = ",".join(property_filters)
            query_parameters['propertyFilters'] = self._serialize.query('property_filters', property_filters, 'str')
        response = self._send(http_method='GET',
                              location_id='12b5d21a-f54c-430e-a8c1-7515d196890e',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[DefinitionEnvironmentReference]', self._unwrap_collection(response))

    def create_release_definition(self, release_definition, project):
        """CreateReleaseDefinition.
        [Preview API] Create a release definition
        :param :class:`<ReleaseDefinition> <release.v4_0.models.ReleaseDefinition>` release_definition: release definition object to create.
        :param str project: Project ID or project name
        :rtype: :class:`<ReleaseDefinition> <release.v4_0.models.ReleaseDefinition>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(release_definition, 'ReleaseDefinition')
        response = self._send(http_method='POST',
                              location_id='d8f96f24-8ea7-4cb6-baab-2df8fc515665',
                              version='4.0-preview.3',
                              route_values=route_values,
                              content=content)
        return self._deserialize('ReleaseDefinition', response)

    def delete_release_definition(self, project, definition_id):
        """DeleteReleaseDefinition.
        [Preview API] Delete a release definition.
        :param str project: Project ID or project name
        :param int definition_id: Id of the release definition.
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if definition_id is not None:
            route_values['definitionId'] = self._serialize.url('definition_id', definition_id, 'int')
        self._send(http_method='DELETE',
                   location_id='d8f96f24-8ea7-4cb6-baab-2df8fc515665',
                   version='4.0-preview.3',
                   route_values=route_values)

    def get_release_definition(self, project, definition_id, property_filters=None):
        """GetReleaseDefinition.
        [Preview API] Get a release definition.
        :param str project: Project ID or project name
        :param int definition_id: Id of the release definition.
        :param [str] property_filters: A comma-delimited list of extended properties to retrieve.
        :rtype: :class:`<ReleaseDefinition> <release.v4_0.models.ReleaseDefinition>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if definition_id is not None:
            route_values['definitionId'] = self._serialize.url('definition_id', definition_id, 'int')
        query_parameters = {}
        if property_filters is not None:
            property_filters = ",".join(property_filters)
            query_parameters['propertyFilters'] = self._serialize.query('property_filters', property_filters, 'str')
        response = self._send(http_method='GET',
                              location_id='d8f96f24-8ea7-4cb6-baab-2df8fc515665',
                              version='4.0-preview.3',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('ReleaseDefinition', response)

    def get_release_definition_revision(self, project, definition_id, revision, **kwargs):
        """GetReleaseDefinitionRevision.
        [Preview API] Get release definition of a given revision.
        :param str project: Project ID or project name
        :param int definition_id: Id of the release definition.
        :param int revision: Revision number of the release definition.
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if definition_id is not None:
            route_values['definitionId'] = self._serialize.url('definition_id', definition_id, 'int')
        query_parameters = {}
        if revision is not None:
            query_parameters['revision'] = self._serialize.query('revision', revision, 'int')
        response = self._send(http_method='GET',
                              location_id='d8f96f24-8ea7-4cb6-baab-2df8fc515665',
                              version='4.0-preview.3',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              accept_media_type='text/plain')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_release_definitions(self, project, search_text=None, expand=None, artifact_type=None, artifact_source_id=None, top=None, continuation_token=None, query_order=None, path=None, is_exact_name_match=None, tag_filter=None, property_filters=None, definition_id_filter=None):
        """GetReleaseDefinitions.
        [Preview API] Get a list of release definitions.
        :param str project: Project ID or project name
        :param str search_text: Get release definitions with names starting with searchText.
        :param str expand: The properties that should be expanded in the list of Release definitions.
        :param str artifact_type: Release definitions with given artifactType will be returned. Values can be Build, Jenkins, GitHub, Nuget, Team Build (external), ExternalTFSBuild, Git, TFVC, ExternalTfsXamlBuild.
        :param str artifact_source_id: Release definitions with given artifactSourceId will be returned. e.g. For build it would be {projectGuid}:{BuildDefinitionId}, for Jenkins it would be {JenkinsConnectionId}:{JenkinsDefinitionId}, for TfsOnPrem it would be {TfsOnPremConnectionId}:{ProjectName}:{TfsOnPremDefinitionId}. For third-party artifacts e.g. TeamCity, BitBucket you may refer 'uniqueSourceIdentifier' inside vss-extension.json at https://github.com/Microsoft/vsts-rm-extensions/blob/master/Extensions.
        :param int top: Number of release definitions to get.
        :param str continuation_token: Gets the release definitions after the continuation token provided.
        :param str query_order: Gets the results in the defined order. Default is 'IdAscending'.
        :param str path: Gets the release definitions under the specified path.
        :param bool is_exact_name_match: 'true'to gets the release definitions with exact match as specified in searchText. Default is 'false'.
        :param [str] tag_filter: A comma-delimited list of tags. Only release definitions with these tags will be returned.
        :param [str] property_filters: A comma-delimited list of extended properties to retrieve.
        :param [str] definition_id_filter: A comma-delimited list of release definitions to retrieve.
        :rtype: [ReleaseDefinition]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if search_text is not None:
            query_parameters['searchText'] = self._serialize.query('search_text', search_text, 'str')
        if expand is not None:
            query_parameters['$expand'] = self._serialize.query('expand', expand, 'str')
        if artifact_type is not None:
            query_parameters['artifactType'] = self._serialize.query('artifact_type', artifact_type, 'str')
        if artifact_source_id is not None:
            query_parameters['artifactSourceId'] = self._serialize.query('artifact_source_id', artifact_source_id, 'str')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        if continuation_token is not None:
            query_parameters['continuationToken'] = self._serialize.query('continuation_token', continuation_token, 'str')
        if query_order is not None:
            query_parameters['queryOrder'] = self._serialize.query('query_order', query_order, 'str')
        if path is not None:
            query_parameters['path'] = self._serialize.query('path', path, 'str')
        if is_exact_name_match is not None:
            query_parameters['isExactNameMatch'] = self._serialize.query('is_exact_name_match', is_exact_name_match, 'bool')
        if tag_filter is not None:
            tag_filter = ",".join(tag_filter)
            query_parameters['tagFilter'] = self._serialize.query('tag_filter', tag_filter, 'str')
        if property_filters is not None:
            property_filters = ",".join(property_filters)
            query_parameters['propertyFilters'] = self._serialize.query('property_filters', property_filters, 'str')
        if definition_id_filter is not None:
            definition_id_filter = ",".join(definition_id_filter)
            query_parameters['definitionIdFilter'] = self._serialize.query('definition_id_filter', definition_id_filter, 'str')
        response = self._send(http_method='GET',
                              location_id='d8f96f24-8ea7-4cb6-baab-2df8fc515665',
                              version='4.0-preview.3',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[ReleaseDefinition]', self._unwrap_collection(response))

    def update_release_definition(self, release_definition, project):
        """UpdateReleaseDefinition.
        [Preview API] Update a release definition.
        :param :class:`<ReleaseDefinition> <release.v4_0.models.ReleaseDefinition>` release_definition: Release definition object to update.
        :param str project: Project ID or project name
        :rtype: :class:`<ReleaseDefinition> <release.v4_0.models.ReleaseDefinition>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(release_definition, 'ReleaseDefinition')
        response = self._send(http_method='PUT',
                              location_id='d8f96f24-8ea7-4cb6-baab-2df8fc515665',
                              version='4.0-preview.3',
                              route_values=route_values,
                              content=content)
        return self._deserialize('ReleaseDefinition', response)

    def get_deployments(self, project, definition_id=None, definition_environment_id=None, created_by=None, min_modified_time=None, max_modified_time=None, deployment_status=None, operation_status=None, latest_attempts_only=None, query_order=None, top=None, continuation_token=None, created_for=None):
        """GetDeployments.
        [Preview API]
        :param str project: Project ID or project name
        :param int definition_id:
        :param int definition_environment_id:
        :param str created_by:
        :param datetime min_modified_time:
        :param datetime max_modified_time:
        :param str deployment_status:
        :param str operation_status:
        :param bool latest_attempts_only:
        :param str query_order:
        :param int top:
        :param int continuation_token:
        :param str created_for:
        :rtype: [Deployment]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if definition_id is not None:
            query_parameters['definitionId'] = self._serialize.query('definition_id', definition_id, 'int')
        if definition_environment_id is not None:
            query_parameters['definitionEnvironmentId'] = self._serialize.query('definition_environment_id', definition_environment_id, 'int')
        if created_by is not None:
            query_parameters['createdBy'] = self._serialize.query('created_by', created_by, 'str')
        if min_modified_time is not None:
            query_parameters['minModifiedTime'] = self._serialize.query('min_modified_time', min_modified_time, 'iso-8601')
        if max_modified_time is not None:
            query_parameters['maxModifiedTime'] = self._serialize.query('max_modified_time', max_modified_time, 'iso-8601')
        if deployment_status is not None:
            query_parameters['deploymentStatus'] = self._serialize.query('deployment_status', deployment_status, 'str')
        if operation_status is not None:
            query_parameters['operationStatus'] = self._serialize.query('operation_status', operation_status, 'str')
        if latest_attempts_only is not None:
            query_parameters['latestAttemptsOnly'] = self._serialize.query('latest_attempts_only', latest_attempts_only, 'bool')
        if query_order is not None:
            query_parameters['queryOrder'] = self._serialize.query('query_order', query_order, 'str')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        if continuation_token is not None:
            query_parameters['continuationToken'] = self._serialize.query('continuation_token', continuation_token, 'int')
        if created_for is not None:
            query_parameters['createdFor'] = self._serialize.query('created_for', created_for, 'str')
        response = self._send(http_method='GET',
                              location_id='b005ef73-cddc-448e-9ba2-5193bf36b19f',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[Deployment]', self._unwrap_collection(response))

    def get_deployments_for_multiple_environments(self, query_parameters, project):
        """GetDeploymentsForMultipleEnvironments.
        [Preview API]
        :param :class:`<DeploymentQueryParameters> <release.v4_0.models.DeploymentQueryParameters>` query_parameters:
        :param str project: Project ID or project name
        :rtype: [Deployment]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(query_parameters, 'DeploymentQueryParameters')
        response = self._send(http_method='POST',
                              location_id='b005ef73-cddc-448e-9ba2-5193bf36b19f',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[Deployment]', self._unwrap_collection(response))

    def get_release_environment(self, project, release_id, environment_id):
        """GetReleaseEnvironment.
        [Preview API]
        :param str project: Project ID or project name
        :param int release_id:
        :param int environment_id:
        :rtype: :class:`<ReleaseEnvironment> <release.v4_0.models.ReleaseEnvironment>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        if environment_id is not None:
            route_values['environmentId'] = self._serialize.url('environment_id', environment_id, 'int')
        response = self._send(http_method='GET',
                              location_id='a7e426b1-03dc-48af-9dfe-c98bac612dcb',
                              version='4.0-preview.4',
                              route_values=route_values)
        return self._deserialize('ReleaseEnvironment', response)

    def update_release_environment(self, environment_update_data, project, release_id, environment_id):
        """UpdateReleaseEnvironment.
        [Preview API] Update the status of a release environment
        :param :class:`<ReleaseEnvironmentUpdateMetadata> <release.v4_0.models.ReleaseEnvironmentUpdateMetadata>` environment_update_data: Environment update meta data.
        :param str project: Project ID or project name
        :param int release_id: Id of the release.
        :param int environment_id: Id of release environment.
        :rtype: :class:`<ReleaseEnvironment> <release.v4_0.models.ReleaseEnvironment>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        if environment_id is not None:
            route_values['environmentId'] = self._serialize.url('environment_id', environment_id, 'int')
        content = self._serialize.body(environment_update_data, 'ReleaseEnvironmentUpdateMetadata')
        response = self._send(http_method='PATCH',
                              location_id='a7e426b1-03dc-48af-9dfe-c98bac612dcb',
                              version='4.0-preview.4',
                              route_values=route_values,
                              content=content)
        return self._deserialize('ReleaseEnvironment', response)

    def create_definition_environment_template(self, template, project):
        """CreateDefinitionEnvironmentTemplate.
        [Preview API]
        :param :class:`<ReleaseDefinitionEnvironmentTemplate> <release.v4_0.models.ReleaseDefinitionEnvironmentTemplate>` template:
        :param str project: Project ID or project name
        :rtype: :class:`<ReleaseDefinitionEnvironmentTemplate> <release.v4_0.models.ReleaseDefinitionEnvironmentTemplate>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(template, 'ReleaseDefinitionEnvironmentTemplate')
        response = self._send(http_method='POST',
                              location_id='6b03b696-824e-4479-8eb2-6644a51aba89',
                              version='4.0-preview.2',
                              route_values=route_values,
                              content=content)
        return self._deserialize('ReleaseDefinitionEnvironmentTemplate', response)

    def delete_definition_environment_template(self, project, template_id):
        """DeleteDefinitionEnvironmentTemplate.
        [Preview API]
        :param str project: Project ID or project name
        :param str template_id:
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if template_id is not None:
            query_parameters['templateId'] = self._serialize.query('template_id', template_id, 'str')
        self._send(http_method='DELETE',
                   location_id='6b03b696-824e-4479-8eb2-6644a51aba89',
                   version='4.0-preview.2',
                   route_values=route_values,
                   query_parameters=query_parameters)

    def get_definition_environment_template(self, project, template_id):
        """GetDefinitionEnvironmentTemplate.
        [Preview API]
        :param str project: Project ID or project name
        :param str template_id:
        :rtype: :class:`<ReleaseDefinitionEnvironmentTemplate> <release.v4_0.models.ReleaseDefinitionEnvironmentTemplate>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if template_id is not None:
            query_parameters['templateId'] = self._serialize.query('template_id', template_id, 'str')
        response = self._send(http_method='GET',
                              location_id='6b03b696-824e-4479-8eb2-6644a51aba89',
                              version='4.0-preview.2',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('ReleaseDefinitionEnvironmentTemplate', response)

    def list_definition_environment_templates(self, project):
        """ListDefinitionEnvironmentTemplates.
        [Preview API]
        :param str project: Project ID or project name
        :rtype: [ReleaseDefinitionEnvironmentTemplate]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        response = self._send(http_method='GET',
                              location_id='6b03b696-824e-4479-8eb2-6644a51aba89',
                              version='4.0-preview.2',
                              route_values=route_values)
        return self._deserialize('[ReleaseDefinitionEnvironmentTemplate]', self._unwrap_collection(response))

    def create_favorites(self, favorite_items, project, scope, identity_id=None):
        """CreateFavorites.
        [Preview API]
        :param [FavoriteItem] favorite_items:
        :param str project: Project ID or project name
        :param str scope:
        :param str identity_id:
        :rtype: [FavoriteItem]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if scope is not None:
            route_values['scope'] = self._serialize.url('scope', scope, 'str')
        query_parameters = {}
        if identity_id is not None:
            query_parameters['identityId'] = self._serialize.query('identity_id', identity_id, 'str')
        content = self._serialize.body(favorite_items, '[FavoriteItem]')
        response = self._send(http_method='POST',
                              location_id='938f7222-9acb-48fe-b8a3-4eda04597171',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('[FavoriteItem]', self._unwrap_collection(response))

    def delete_favorites(self, project, scope, identity_id=None, favorite_item_ids=None):
        """DeleteFavorites.
        [Preview API]
        :param str project: Project ID or project name
        :param str scope:
        :param str identity_id:
        :param str favorite_item_ids:
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if scope is not None:
            route_values['scope'] = self._serialize.url('scope', scope, 'str')
        query_parameters = {}
        if identity_id is not None:
            query_parameters['identityId'] = self._serialize.query('identity_id', identity_id, 'str')
        if favorite_item_ids is not None:
            query_parameters['favoriteItemIds'] = self._serialize.query('favorite_item_ids', favorite_item_ids, 'str')
        self._send(http_method='DELETE',
                   location_id='938f7222-9acb-48fe-b8a3-4eda04597171',
                   version='4.0-preview.1',
                   route_values=route_values,
                   query_parameters=query_parameters)

    def get_favorites(self, project, scope, identity_id=None):
        """GetFavorites.
        [Preview API]
        :param str project: Project ID or project name
        :param str scope:
        :param str identity_id:
        :rtype: [FavoriteItem]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if scope is not None:
            route_values['scope'] = self._serialize.url('scope', scope, 'str')
        query_parameters = {}
        if identity_id is not None:
            query_parameters['identityId'] = self._serialize.query('identity_id', identity_id, 'str')
        response = self._send(http_method='GET',
                              location_id='938f7222-9acb-48fe-b8a3-4eda04597171',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[FavoriteItem]', self._unwrap_collection(response))

    def create_folder(self, folder, project, path):
        """CreateFolder.
        [Preview API] Creates a new folder
        :param :class:`<Folder> <release.v4_0.models.Folder>` folder:
        :param str project: Project ID or project name
        :param str path:
        :rtype: :class:`<Folder> <release.v4_0.models.Folder>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if path is not None:
            route_values['path'] = self._serialize.url('path', path, 'str')
        content = self._serialize.body(folder, 'Folder')
        response = self._send(http_method='POST',
                              location_id='f7ddf76d-ce0c-4d68-94ff-becaec5d9dea',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Folder', response)

    def delete_folder(self, project, path):
        """DeleteFolder.
        [Preview API] Deletes a definition folder for given folder name and path and all it's existing definitions
        :param str project: Project ID or project name
        :param str path:
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if path is not None:
            route_values['path'] = self._serialize.url('path', path, 'str')
        self._send(http_method='DELETE',
                   location_id='f7ddf76d-ce0c-4d68-94ff-becaec5d9dea',
                   version='4.0-preview.1',
                   route_values=route_values)

    def get_folders(self, project, path=None, query_order=None):
        """GetFolders.
        [Preview API] Gets folders
        :param str project: Project ID or project name
        :param str path:
        :param str query_order:
        :rtype: [Folder]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if path is not None:
            route_values['path'] = self._serialize.url('path', path, 'str')
        query_parameters = {}
        if query_order is not None:
            query_parameters['queryOrder'] = self._serialize.query('query_order', query_order, 'str')
        response = self._send(http_method='GET',
                              location_id='f7ddf76d-ce0c-4d68-94ff-becaec5d9dea',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[Folder]', self._unwrap_collection(response))

    def update_folder(self, folder, project, path):
        """UpdateFolder.
        [Preview API] Updates an existing folder at given  existing path
        :param :class:`<Folder> <release.v4_0.models.Folder>` folder:
        :param str project: Project ID or project name
        :param str path:
        :rtype: :class:`<Folder> <release.v4_0.models.Folder>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if path is not None:
            route_values['path'] = self._serialize.url('path', path, 'str')
        content = self._serialize.body(folder, 'Folder')
        response = self._send(http_method='PATCH',
                              location_id='f7ddf76d-ce0c-4d68-94ff-becaec5d9dea',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Folder', response)

    def get_release_history(self, project, release_id):
        """GetReleaseHistory.
        [Preview API]
        :param str project: Project ID or project name
        :param int release_id:
        :rtype: [ReleaseRevision]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        response = self._send(http_method='GET',
                              location_id='23f461c8-629a-4144-a076-3054fa5f268a',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[ReleaseRevision]', self._unwrap_collection(response))

    def get_input_values(self, query, project):
        """GetInputValues.
        [Preview API]
        :param :class:`<InputValuesQuery> <release.v4_0.models.InputValuesQuery>` query:
        :param str project: Project ID or project name
        :rtype: :class:`<InputValuesQuery> <release.v4_0.models.InputValuesQuery>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(query, 'InputValuesQuery')
        response = self._send(http_method='POST',
                              location_id='71dd499b-317d-45ea-9134-140ea1932b5e',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('InputValuesQuery', response)

    def get_issues(self, project, build_id, source_id=None):
        """GetIssues.
        [Preview API]
        :param str project: Project ID or project name
        :param int build_id:
        :param str source_id:
        :rtype: [AutoTriggerIssue]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if build_id is not None:
            route_values['buildId'] = self._serialize.url('build_id', build_id, 'int')
        query_parameters = {}
        if source_id is not None:
            query_parameters['sourceId'] = self._serialize.query('source_id', source_id, 'str')
        response = self._send(http_method='GET',
                              location_id='cd42261a-f5c6-41c8-9259-f078989b9f25',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[AutoTriggerIssue]', self._unwrap_collection(response))

    def get_log(self, project, release_id, environment_id, task_id, attempt_id=None, **kwargs):
        """GetLog.
        [Preview API] Gets logs
        :param str project: Project ID or project name
        :param int release_id: Id of the release.
        :param int environment_id: Id of release environment.
        :param int task_id: ReleaseTask Id for the log.
        :param int attempt_id: Id of the attempt.
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        if environment_id is not None:
            route_values['environmentId'] = self._serialize.url('environment_id', environment_id, 'int')
        if task_id is not None:
            route_values['taskId'] = self._serialize.url('task_id', task_id, 'int')
        query_parameters = {}
        if attempt_id is not None:
            query_parameters['attemptId'] = self._serialize.query('attempt_id', attempt_id, 'int')
        response = self._send(http_method='GET',
                              location_id='e71ba1ed-c0a4-4a28-a61f-2dd5f68cf3fd',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              accept_media_type='text/plain')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_logs(self, project, release_id, **kwargs):
        """GetLogs.
        [Preview API] Get logs for a release Id.
        :param str project: Project ID or project name
        :param int release_id: Id of the release.
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        response = self._send(http_method='GET',
                              location_id='c37fbab5-214b-48e4-a55b-cb6b4f6e4038',
                              version='4.0-preview.2',
                              route_values=route_values,
                              accept_media_type='application/zip')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_task_log(self, project, release_id, environment_id, release_deploy_phase_id, task_id, **kwargs):
        """GetTaskLog.
        [Preview API] Gets the task log of a release as a plain text file.
        :param str project: Project ID or project name
        :param int release_id: Id of the release.
        :param int environment_id: Id of release environment.
        :param int release_deploy_phase_id: Release deploy phase Id.
        :param int task_id: ReleaseTask Id for the log.
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        if environment_id is not None:
            route_values['environmentId'] = self._serialize.url('environment_id', environment_id, 'int')
        if release_deploy_phase_id is not None:
            route_values['releaseDeployPhaseId'] = self._serialize.url('release_deploy_phase_id', release_deploy_phase_id, 'int')
        if task_id is not None:
            route_values['taskId'] = self._serialize.url('task_id', task_id, 'int')
        response = self._send(http_method='GET',
                              location_id='17c91af7-09fd-4256-bff1-c24ee4f73bc0',
                              version='4.0-preview.2',
                              route_values=route_values,
                              accept_media_type='text/plain')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_manual_intervention(self, project, release_id, manual_intervention_id):
        """GetManualIntervention.
        [Preview API]
        :param str project: Project ID or project name
        :param int release_id:
        :param int manual_intervention_id:
        :rtype: :class:`<ManualIntervention> <release.v4_0.models.ManualIntervention>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        if manual_intervention_id is not None:
            route_values['manualInterventionId'] = self._serialize.url('manual_intervention_id', manual_intervention_id, 'int')
        response = self._send(http_method='GET',
                              location_id='616c46e4-f370-4456-adaa-fbaf79c7b79e',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('ManualIntervention', response)

    def get_manual_interventions(self, project, release_id):
        """GetManualInterventions.
        [Preview API]
        :param str project: Project ID or project name
        :param int release_id:
        :rtype: [ManualIntervention]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        response = self._send(http_method='GET',
                              location_id='616c46e4-f370-4456-adaa-fbaf79c7b79e',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[ManualIntervention]', self._unwrap_collection(response))

    def update_manual_intervention(self, manual_intervention_update_metadata, project, release_id, manual_intervention_id):
        """UpdateManualIntervention.
        [Preview API]
        :param :class:`<ManualInterventionUpdateMetadata> <release.v4_0.models.ManualInterventionUpdateMetadata>` manual_intervention_update_metadata:
        :param str project: Project ID or project name
        :param int release_id:
        :param int manual_intervention_id:
        :rtype: :class:`<ManualIntervention> <release.v4_0.models.ManualIntervention>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        if manual_intervention_id is not None:
            route_values['manualInterventionId'] = self._serialize.url('manual_intervention_id', manual_intervention_id, 'int')
        content = self._serialize.body(manual_intervention_update_metadata, 'ManualInterventionUpdateMetadata')
        response = self._send(http_method='PATCH',
                              location_id='616c46e4-f370-4456-adaa-fbaf79c7b79e',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('ManualIntervention', response)

    def get_metrics(self, project, min_metrics_time=None):
        """GetMetrics.
        [Preview API]
        :param str project: Project ID or project name
        :param datetime min_metrics_time:
        :rtype: [Metric]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if min_metrics_time is not None:
            query_parameters['minMetricsTime'] = self._serialize.query('min_metrics_time', min_metrics_time, 'iso-8601')
        response = self._send(http_method='GET',
                              location_id='cd1502bb-3c73-4e11-80a6-d11308dceae5',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[Metric]', self._unwrap_collection(response))

    def get_release_projects(self, artifact_type, artifact_source_id):
        """GetReleaseProjects.
        [Preview API]
        :param str artifact_type:
        :param str artifact_source_id:
        :rtype: [ProjectReference]
        """
        query_parameters = {}
        if artifact_type is not None:
            query_parameters['artifactType'] = self._serialize.query('artifact_type', artifact_type, 'str')
        if artifact_source_id is not None:
            query_parameters['artifactSourceId'] = self._serialize.query('artifact_source_id', artifact_source_id, 'str')
        response = self._send(http_method='GET',
                              location_id='917ace4a-79d1-45a7-987c-7be4db4268fa',
                              version='4.0-preview.1',
                              query_parameters=query_parameters)
        return self._deserialize('[ProjectReference]', self._unwrap_collection(response))

    def get_releases(self, project=None, definition_id=None, definition_environment_id=None, search_text=None, created_by=None, status_filter=None, environment_status_filter=None, min_created_time=None, max_created_time=None, query_order=None, top=None, continuation_token=None, expand=None, artifact_type_id=None, source_id=None, artifact_version_id=None, source_branch_filter=None, is_deleted=None, tag_filter=None, property_filters=None):
        """GetReleases.
        [Preview API] Get a list of releases
        :param str project: Project ID or project name
        :param int definition_id: Releases from this release definition Id.
        :param int definition_environment_id:
        :param str search_text: Releases with names starting with searchText.
        :param str created_by: Releases created by this user.
        :param str status_filter: Releases that have this status.
        :param int environment_status_filter:
        :param datetime min_created_time: Releases that were created after this time.
        :param datetime max_created_time: Releases that were created before this time.
        :param str query_order: Gets the results in the defined order of created date for releases. Default is descending.
        :param int top: Number of releases to get. Default is 50.
        :param int continuation_token: Gets the releases after the continuation token provided.
        :param str expand: The property that should be expanded in the list of releases.
        :param str artifact_type_id: Releases with given artifactTypeId will be returned. Values can be Build, Jenkins, GitHub, Nuget, Team Build (external), ExternalTFSBuild, Git, TFVC, ExternalTfsXamlBuild.
        :param str source_id: Unique identifier of the artifact used. e.g. For build it would be {projectGuid}:{BuildDefinitionId}, for Jenkins it would be {JenkinsConnectionId}:{JenkinsDefinitionId}, for TfsOnPrem it would be {TfsOnPremConnectionId}:{ProjectName}:{TfsOnPremDefinitionId}. For third-party artifacts e.g. TeamCity, BitBucket you may refer 'uniqueSourceIdentifier' inside vss-extension.json https://github.com/Microsoft/vsts-rm-extensions/blob/master/Extensions.
        :param str artifact_version_id: Releases with given artifactVersionId will be returned. E.g. in case of Build artifactType, it is buildId.
        :param str source_branch_filter: Releases with given sourceBranchFilter will be returned.
        :param bool is_deleted: Gets the soft deleted releases, if true.
        :param [str] tag_filter: A comma-delimited list of tags. Only releases with these tags will be returned.
        :param [str] property_filters: A comma-delimited list of extended properties to retrieve.
        :rtype: [Release]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if definition_id is not None:
            query_parameters['definitionId'] = self._serialize.query('definition_id', definition_id, 'int')
        if definition_environment_id is not None:
            query_parameters['definitionEnvironmentId'] = self._serialize.query('definition_environment_id', definition_environment_id, 'int')
        if search_text is not None:
            query_parameters['searchText'] = self._serialize.query('search_text', search_text, 'str')
        if created_by is not None:
            query_parameters['createdBy'] = self._serialize.query('created_by', created_by, 'str')
        if status_filter is not None:
            query_parameters['statusFilter'] = self._serialize.query('status_filter', status_filter, 'str')
        if environment_status_filter is not None:
            query_parameters['environmentStatusFilter'] = self._serialize.query('environment_status_filter', environment_status_filter, 'int')
        if min_created_time is not None:
            query_parameters['minCreatedTime'] = self._serialize.query('min_created_time', min_created_time, 'iso-8601')
        if max_created_time is not None:
            query_parameters['maxCreatedTime'] = self._serialize.query('max_created_time', max_created_time, 'iso-8601')
        if query_order is not None:
            query_parameters['queryOrder'] = self._serialize.query('query_order', query_order, 'str')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        if continuation_token is not None:
            query_parameters['continuationToken'] = self._serialize.query('continuation_token', continuation_token, 'int')
        if expand is not None:
            query_parameters['$expand'] = self._serialize.query('expand', expand, 'str')
        if artifact_type_id is not None:
            query_parameters['artifactTypeId'] = self._serialize.query('artifact_type_id', artifact_type_id, 'str')
        if source_id is not None:
            query_parameters['sourceId'] = self._serialize.query('source_id', source_id, 'str')
        if artifact_version_id is not None:
            query_parameters['artifactVersionId'] = self._serialize.query('artifact_version_id', artifact_version_id, 'str')
        if source_branch_filter is not None:
            query_parameters['sourceBranchFilter'] = self._serialize.query('source_branch_filter', source_branch_filter, 'str')
        if is_deleted is not None:
            query_parameters['isDeleted'] = self._serialize.query('is_deleted', is_deleted, 'bool')
        if tag_filter is not None:
            tag_filter = ",".join(tag_filter)
            query_parameters['tagFilter'] = self._serialize.query('tag_filter', tag_filter, 'str')
        if property_filters is not None:
            property_filters = ",".join(property_filters)
            query_parameters['propertyFilters'] = self._serialize.query('property_filters', property_filters, 'str')
        response = self._send(http_method='GET',
                              location_id='a166fde7-27ad-408e-ba75-703c2cc9d500',
                              version='4.0-preview.4',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[Release]', self._unwrap_collection(response))

    def create_release(self, release_start_metadata, project):
        """CreateRelease.
        [Preview API] Create a release.
        :param :class:`<ReleaseStartMetadata> <release.v4_0.models.ReleaseStartMetadata>` release_start_metadata: Metadata to create a release.
        :param str project: Project ID or project name
        :rtype: :class:`<Release> <release.v4_0.models.Release>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(release_start_metadata, 'ReleaseStartMetadata')
        response = self._send(http_method='POST',
                              location_id='a166fde7-27ad-408e-ba75-703c2cc9d500',
                              version='4.0-preview.4',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Release', response)

    def delete_release(self, project, release_id, comment=None):
        """DeleteRelease.
        [Preview API] Soft delete a release
        :param str project: Project ID or project name
        :param int release_id: Id of the release.
        :param str comment: Comment for deleting a release.
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        query_parameters = {}
        if comment is not None:
            query_parameters['comment'] = self._serialize.query('comment', comment, 'str')
        self._send(http_method='DELETE',
                   location_id='a166fde7-27ad-408e-ba75-703c2cc9d500',
                   version='4.0-preview.4',
                   route_values=route_values,
                   query_parameters=query_parameters)

    def get_release(self, project, release_id, include_all_approvals=None, property_filters=None):
        """GetRelease.
        [Preview API] Get a Release
        :param str project: Project ID or project name
        :param int release_id: Id of the release.
        :param bool include_all_approvals: Include all approvals in the result. Default is 'true'.
        :param [str] property_filters: A comma-delimited list of properties to include in the results.
        :rtype: :class:`<Release> <release.v4_0.models.Release>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        query_parameters = {}
        if include_all_approvals is not None:
            query_parameters['includeAllApprovals'] = self._serialize.query('include_all_approvals', include_all_approvals, 'bool')
        if property_filters is not None:
            property_filters = ",".join(property_filters)
            query_parameters['propertyFilters'] = self._serialize.query('property_filters', property_filters, 'str')
        response = self._send(http_method='GET',
                              location_id='a166fde7-27ad-408e-ba75-703c2cc9d500',
                              version='4.0-preview.4',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('Release', response)

    def get_release_definition_summary(self, project, definition_id, release_count, include_artifact=None, definition_environment_ids_filter=None):
        """GetReleaseDefinitionSummary.
        [Preview API] Get release summary of a given definition Id.
        :param str project: Project ID or project name
        :param int definition_id: Id of the definition to get release summary.
        :param int release_count: Count of releases to be included in summary.
        :param bool include_artifact: Include artifact details.Default is 'false'.
        :param [int] definition_environment_ids_filter:
        :rtype: :class:`<ReleaseDefinitionSummary> <release.v4_0.models.ReleaseDefinitionSummary>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if definition_id is not None:
            query_parameters['definitionId'] = self._serialize.query('definition_id', definition_id, 'int')
        if release_count is not None:
            query_parameters['releaseCount'] = self._serialize.query('release_count', release_count, 'int')
        if include_artifact is not None:
            query_parameters['includeArtifact'] = self._serialize.query('include_artifact', include_artifact, 'bool')
        if definition_environment_ids_filter is not None:
            definition_environment_ids_filter = ",".join(map(str, definition_environment_ids_filter))
            query_parameters['definitionEnvironmentIdsFilter'] = self._serialize.query('definition_environment_ids_filter', definition_environment_ids_filter, 'str')
        response = self._send(http_method='GET',
                              location_id='a166fde7-27ad-408e-ba75-703c2cc9d500',
                              version='4.0-preview.4',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('ReleaseDefinitionSummary', response)

    def get_release_revision(self, project, release_id, definition_snapshot_revision, **kwargs):
        """GetReleaseRevision.
        [Preview API] Get release for a given revision number.
        :param str project: Project ID or project name
        :param int release_id: Id of the release.
        :param int definition_snapshot_revision: Definition snapshot revision number.
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        query_parameters = {}
        if definition_snapshot_revision is not None:
            query_parameters['definitionSnapshotRevision'] = self._serialize.query('definition_snapshot_revision', definition_snapshot_revision, 'int')
        response = self._send(http_method='GET',
                              location_id='a166fde7-27ad-408e-ba75-703c2cc9d500',
                              version='4.0-preview.4',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              accept_media_type='text/plain')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def undelete_release(self, project, release_id, comment):
        """UndeleteRelease.
        [Preview API] Undelete a soft deleted release.
        :param str project: Project ID or project name
        :param int release_id: Id of release to be undeleted.
        :param str comment: Any comment for undeleting.
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        query_parameters = {}
        if comment is not None:
            query_parameters['comment'] = self._serialize.query('comment', comment, 'str')
        self._send(http_method='PUT',
                   location_id='a166fde7-27ad-408e-ba75-703c2cc9d500',
                   version='4.0-preview.4',
                   route_values=route_values,
                   query_parameters=query_parameters)

    def update_release(self, release, project, release_id):
        """UpdateRelease.
        [Preview API] Update a complete release object.
        :param :class:`<Release> <release.v4_0.models.Release>` release: Release object for update.
        :param str project: Project ID or project name
        :param int release_id: Id of the release to update.
        :rtype: :class:`<Release> <release.v4_0.models.Release>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        content = self._serialize.body(release, 'Release')
        response = self._send(http_method='PUT',
                              location_id='a166fde7-27ad-408e-ba75-703c2cc9d500',
                              version='4.0-preview.4',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Release', response)

    def update_release_resource(self, release_update_metadata, project, release_id):
        """UpdateReleaseResource.
        [Preview API] Update few properties of a release.
        :param :class:`<ReleaseUpdateMetadata> <release.v4_0.models.ReleaseUpdateMetadata>` release_update_metadata: Properties of release to update.
        :param str project: Project ID or project name
        :param int release_id: Id of the release to update.
        :rtype: :class:`<Release> <release.v4_0.models.Release>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        content = self._serialize.body(release_update_metadata, 'ReleaseUpdateMetadata')
        response = self._send(http_method='PATCH',
                              location_id='a166fde7-27ad-408e-ba75-703c2cc9d500',
                              version='4.0-preview.4',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Release', response)

    def get_release_settings(self, project):
        """GetReleaseSettings.
        [Preview API] Gets the release settings
        :param str project: Project ID or project name
        :rtype: :class:`<ReleaseSettings> <release.v4_0.models.ReleaseSettings>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        response = self._send(http_method='GET',
                              location_id='c63c3718-7cfd-41e0-b89b-81c1ca143437',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('ReleaseSettings', response)

    def update_release_settings(self, release_settings, project):
        """UpdateReleaseSettings.
        [Preview API] Updates the release settings
        :param :class:`<ReleaseSettings> <release.v4_0.models.ReleaseSettings>` release_settings:
        :param str project: Project ID or project name
        :rtype: :class:`<ReleaseSettings> <release.v4_0.models.ReleaseSettings>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(release_settings, 'ReleaseSettings')
        response = self._send(http_method='PUT',
                              location_id='c63c3718-7cfd-41e0-b89b-81c1ca143437',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('ReleaseSettings', response)

    def get_definition_revision(self, project, definition_id, revision, **kwargs):
        """GetDefinitionRevision.
        [Preview API]
        :param str project: Project ID or project name
        :param int definition_id:
        :param int revision:
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if definition_id is not None:
            route_values['definitionId'] = self._serialize.url('definition_id', definition_id, 'int')
        if revision is not None:
            route_values['revision'] = self._serialize.url('revision', revision, 'int')
        response = self._send(http_method='GET',
                              location_id='258b82e0-9d41-43f3-86d6-fef14ddd44bc',
                              version='4.0-preview.1',
                              route_values=route_values,
                              accept_media_type='text/plain')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_release_definition_history(self, project, definition_id):
        """GetReleaseDefinitionHistory.
        [Preview API] Get revision history for a release definition
        :param str project: Project ID or project name
        :param int definition_id: Id of the definition.
        :rtype: [ReleaseDefinitionRevision]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if definition_id is not None:
            route_values['definitionId'] = self._serialize.url('definition_id', definition_id, 'int')
        response = self._send(http_method='GET',
                              location_id='258b82e0-9d41-43f3-86d6-fef14ddd44bc',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[ReleaseDefinitionRevision]', self._unwrap_collection(response))

    def get_summary_mail_sections(self, project, release_id):
        """GetSummaryMailSections.
        [Preview API]
        :param str project: Project ID or project name
        :param int release_id:
        :rtype: [SummaryMailSection]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        response = self._send(http_method='GET',
                              location_id='224e92b2-8d13-4c14-b120-13d877c516f8',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[SummaryMailSection]', self._unwrap_collection(response))

    def send_summary_mail(self, mail_message, project, release_id):
        """SendSummaryMail.
        [Preview API]
        :param :class:`<MailMessage> <release.v4_0.models.MailMessage>` mail_message:
        :param str project: Project ID or project name
        :param int release_id:
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        content = self._serialize.body(mail_message, 'MailMessage')
        self._send(http_method='POST',
                   location_id='224e92b2-8d13-4c14-b120-13d877c516f8',
                   version='4.0-preview.1',
                   route_values=route_values,
                   content=content)

    def get_source_branches(self, project, definition_id):
        """GetSourceBranches.
        [Preview API]
        :param str project: Project ID or project name
        :param int definition_id:
        :rtype: [str]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if definition_id is not None:
            route_values['definitionId'] = self._serialize.url('definition_id', definition_id, 'int')
        response = self._send(http_method='GET',
                              location_id='0e5def23-78b3-461f-8198-1558f25041c8',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[str]', self._unwrap_collection(response))

    def add_definition_tag(self, project, release_definition_id, tag):
        """AddDefinitionTag.
        [Preview API] Adds a tag to a definition
        :param str project: Project ID or project name
        :param int release_definition_id:
        :param str tag:
        :rtype: [str]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_definition_id is not None:
            route_values['releaseDefinitionId'] = self._serialize.url('release_definition_id', release_definition_id, 'int')
        if tag is not None:
            route_values['tag'] = self._serialize.url('tag', tag, 'str')
        response = self._send(http_method='PATCH',
                              location_id='3d21b4c8-c32e-45b2-a7cb-770a369012f4',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[str]', self._unwrap_collection(response))

    def add_definition_tags(self, tags, project, release_definition_id):
        """AddDefinitionTags.
        [Preview API] Adds multiple tags to a definition
        :param [str] tags:
        :param str project: Project ID or project name
        :param int release_definition_id:
        :rtype: [str]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_definition_id is not None:
            route_values['releaseDefinitionId'] = self._serialize.url('release_definition_id', release_definition_id, 'int')
        content = self._serialize.body(tags, '[str]')
        response = self._send(http_method='POST',
                              location_id='3d21b4c8-c32e-45b2-a7cb-770a369012f4',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[str]', self._unwrap_collection(response))

    def delete_definition_tag(self, project, release_definition_id, tag):
        """DeleteDefinitionTag.
        [Preview API] Deletes a tag from a definition
        :param str project: Project ID or project name
        :param int release_definition_id:
        :param str tag:
        :rtype: [str]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_definition_id is not None:
            route_values['releaseDefinitionId'] = self._serialize.url('release_definition_id', release_definition_id, 'int')
        if tag is not None:
            route_values['tag'] = self._serialize.url('tag', tag, 'str')
        response = self._send(http_method='DELETE',
                              location_id='3d21b4c8-c32e-45b2-a7cb-770a369012f4',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[str]', self._unwrap_collection(response))

    def get_definition_tags(self, project, release_definition_id):
        """GetDefinitionTags.
        [Preview API] Gets the tags for a definition
        :param str project: Project ID or project name
        :param int release_definition_id:
        :rtype: [str]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_definition_id is not None:
            route_values['releaseDefinitionId'] = self._serialize.url('release_definition_id', release_definition_id, 'int')
        response = self._send(http_method='GET',
                              location_id='3d21b4c8-c32e-45b2-a7cb-770a369012f4',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[str]', self._unwrap_collection(response))

    def add_release_tag(self, project, release_id, tag):
        """AddReleaseTag.
        [Preview API] Adds a tag to a releaseId
        :param str project: Project ID or project name
        :param int release_id:
        :param str tag:
        :rtype: [str]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        if tag is not None:
            route_values['tag'] = self._serialize.url('tag', tag, 'str')
        response = self._send(http_method='PATCH',
                              location_id='c5b602b6-d1b3-4363-8a51-94384f78068f',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[str]', self._unwrap_collection(response))

    def add_release_tags(self, tags, project, release_id):
        """AddReleaseTags.
        [Preview API] Adds tag to a release
        :param [str] tags:
        :param str project: Project ID or project name
        :param int release_id:
        :rtype: [str]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        content = self._serialize.body(tags, '[str]')
        response = self._send(http_method='POST',
                              location_id='c5b602b6-d1b3-4363-8a51-94384f78068f',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[str]', self._unwrap_collection(response))

    def delete_release_tag(self, project, release_id, tag):
        """DeleteReleaseTag.
        [Preview API] Deletes a tag from a release
        :param str project: Project ID or project name
        :param int release_id:
        :param str tag:
        :rtype: [str]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        if tag is not None:
            route_values['tag'] = self._serialize.url('tag', tag, 'str')
        response = self._send(http_method='DELETE',
                              location_id='c5b602b6-d1b3-4363-8a51-94384f78068f',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[str]', self._unwrap_collection(response))

    def get_release_tags(self, project, release_id):
        """GetReleaseTags.
        [Preview API] Gets the tags for a release
        :param str project: Project ID or project name
        :param int release_id:
        :rtype: [str]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        response = self._send(http_method='GET',
                              location_id='c5b602b6-d1b3-4363-8a51-94384f78068f',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[str]', self._unwrap_collection(response))

    def get_tags(self, project):
        """GetTags.
        [Preview API]
        :param str project: Project ID or project name
        :rtype: [str]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        response = self._send(http_method='GET',
                              location_id='86cee25a-68ba-4ba3-9171-8ad6ffc6df93',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[str]', self._unwrap_collection(response))

    def get_tasks(self, project, release_id, environment_id, attempt_id=None):
        """GetTasks.
        [Preview API]
        :param str project: Project ID or project name
        :param int release_id:
        :param int environment_id:
        :param int attempt_id:
        :rtype: [ReleaseTask]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        if environment_id is not None:
            route_values['environmentId'] = self._serialize.url('environment_id', environment_id, 'int')
        query_parameters = {}
        if attempt_id is not None:
            query_parameters['attemptId'] = self._serialize.query('attempt_id', attempt_id, 'int')
        response = self._send(http_method='GET',
                              location_id='36b276e0-3c70-4320-a63c-1a2e1466a0d1',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[ReleaseTask]', self._unwrap_collection(response))

    def get_tasks_for_task_group(self, project, release_id, environment_id, release_deploy_phase_id):
        """GetTasksForTaskGroup.
        [Preview API]
        :param str project: Project ID or project name
        :param int release_id:
        :param int environment_id:
        :param int release_deploy_phase_id:
        :rtype: [ReleaseTask]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        if environment_id is not None:
            route_values['environmentId'] = self._serialize.url('environment_id', environment_id, 'int')
        if release_deploy_phase_id is not None:
            route_values['releaseDeployPhaseId'] = self._serialize.url('release_deploy_phase_id', release_deploy_phase_id, 'int')
        response = self._send(http_method='GET',
                              location_id='4259191d-4b0a-4409-9fb3-09f22ab9bc47',
                              version='4.0-preview.2',
                              route_values=route_values)
        return self._deserialize('[ReleaseTask]', self._unwrap_collection(response))

    def get_artifact_type_definitions(self, project):
        """GetArtifactTypeDefinitions.
        [Preview API]
        :param str project: Project ID or project name
        :rtype: [ArtifactTypeDefinition]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        response = self._send(http_method='GET',
                              location_id='8efc2a3c-1fc8-4f6d-9822-75e98cecb48f',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[ArtifactTypeDefinition]', self._unwrap_collection(response))

    def get_artifact_versions(self, project, release_definition_id):
        """GetArtifactVersions.
        [Preview API]
        :param str project: Project ID or project name
        :param int release_definition_id:
        :rtype: :class:`<ArtifactVersionQueryResult> <release.v4_0.models.ArtifactVersionQueryResult>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if release_definition_id is not None:
            query_parameters['releaseDefinitionId'] = self._serialize.query('release_definition_id', release_definition_id, 'int')
        response = self._send(http_method='GET',
                              location_id='30fc787e-a9e0-4a07-9fbc-3e903aa051d2',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('ArtifactVersionQueryResult', response)

    def get_artifact_versions_for_sources(self, artifacts, project):
        """GetArtifactVersionsForSources.
        [Preview API]
        :param [Artifact] artifacts:
        :param str project: Project ID or project name
        :rtype: :class:`<ArtifactVersionQueryResult> <release.v4_0.models.ArtifactVersionQueryResult>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(artifacts, '[Artifact]')
        response = self._send(http_method='POST',
                              location_id='30fc787e-a9e0-4a07-9fbc-3e903aa051d2',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('ArtifactVersionQueryResult', response)

    def get_release_work_items_refs(self, project, release_id, base_release_id=None, top=None):
        """GetReleaseWorkItemsRefs.
        [Preview API]
        :param str project: Project ID or project name
        :param int release_id:
        :param int base_release_id:
        :param int top:
        :rtype: [ReleaseWorkItemRef]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if release_id is not None:
            route_values['releaseId'] = self._serialize.url('release_id', release_id, 'int')
        query_parameters = {}
        if base_release_id is not None:
            query_parameters['baseReleaseId'] = self._serialize.query('base_release_id', base_release_id, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        response = self._send(http_method='GET',
                              location_id='4f165cc0-875c-4768-b148-f12f78769fab',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[ReleaseWorkItemRef]', self._unwrap_collection(response))

