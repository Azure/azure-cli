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


class PolicyClient(VssClient):
    """Policy
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(PolicyClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = 'fb13a388-40dd-4a04-b530-013a739c72ef'

    def create_policy_configuration(self, configuration, project, configuration_id=None):
        """CreatePolicyConfiguration.
        Create a policy configuration of a given policy type.
        :param :class:`<PolicyConfiguration> <policy.v4_1.models.PolicyConfiguration>` configuration: The policy configuration to create.
        :param str project: Project ID or project name
        :param int configuration_id:
        :rtype: :class:`<PolicyConfiguration> <policy.v4_1.models.PolicyConfiguration>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if configuration_id is not None:
            route_values['configurationId'] = self._serialize.url('configuration_id', configuration_id, 'int')
        content = self._serialize.body(configuration, 'PolicyConfiguration')
        response = self._send(http_method='POST',
                              location_id='dad91cbe-d183-45f8-9c6e-9c1164472121',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('PolicyConfiguration', response)

    def delete_policy_configuration(self, project, configuration_id):
        """DeletePolicyConfiguration.
        Delete a policy configuration by its ID.
        :param str project: Project ID or project name
        :param int configuration_id: ID of the policy configuration to delete.
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if configuration_id is not None:
            route_values['configurationId'] = self._serialize.url('configuration_id', configuration_id, 'int')
        self._send(http_method='DELETE',
                   location_id='dad91cbe-d183-45f8-9c6e-9c1164472121',
                   version='4.1',
                   route_values=route_values)

    def get_policy_configuration(self, project, configuration_id):
        """GetPolicyConfiguration.
        Get a policy configuration by its ID.
        :param str project: Project ID or project name
        :param int configuration_id: ID of the policy configuration
        :rtype: :class:`<PolicyConfiguration> <policy.v4_1.models.PolicyConfiguration>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if configuration_id is not None:
            route_values['configurationId'] = self._serialize.url('configuration_id', configuration_id, 'int')
        response = self._send(http_method='GET',
                              location_id='dad91cbe-d183-45f8-9c6e-9c1164472121',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('PolicyConfiguration', response)

    def get_policy_configurations(self, project, scope=None, policy_type=None):
        """GetPolicyConfigurations.
        Get a list of policy configurations in a project.
        :param str project: Project ID or project name
        :param str scope: The scope on which a subset of policies is applied.
        :param str policy_type: Filter returned policies to only this type
        :rtype: [PolicyConfiguration]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if scope is not None:
            query_parameters['scope'] = self._serialize.query('scope', scope, 'str')
        if policy_type is not None:
            query_parameters['policyType'] = self._serialize.query('policy_type', policy_type, 'str')
        response = self._send(http_method='GET',
                              location_id='dad91cbe-d183-45f8-9c6e-9c1164472121',
                              version='4.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[PolicyConfiguration]', self._unwrap_collection(response))

    def update_policy_configuration(self, configuration, project, configuration_id):
        """UpdatePolicyConfiguration.
        Update a policy configuration by its ID.
        :param :class:`<PolicyConfiguration> <policy.v4_1.models.PolicyConfiguration>` configuration: The policy configuration to update.
        :param str project: Project ID or project name
        :param int configuration_id: ID of the existing policy configuration to be updated.
        :rtype: :class:`<PolicyConfiguration> <policy.v4_1.models.PolicyConfiguration>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if configuration_id is not None:
            route_values['configurationId'] = self._serialize.url('configuration_id', configuration_id, 'int')
        content = self._serialize.body(configuration, 'PolicyConfiguration')
        response = self._send(http_method='PUT',
                              location_id='dad91cbe-d183-45f8-9c6e-9c1164472121',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('PolicyConfiguration', response)

    def get_policy_evaluation(self, project, evaluation_id):
        """GetPolicyEvaluation.
        [Preview API] Gets the present evaluation state of a policy.
        :param str project: Project ID or project name
        :param str evaluation_id: ID of the policy evaluation to be retrieved.
        :rtype: :class:`<PolicyEvaluationRecord> <policy.v4_1.models.PolicyEvaluationRecord>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if evaluation_id is not None:
            route_values['evaluationId'] = self._serialize.url('evaluation_id', evaluation_id, 'str')
        response = self._send(http_method='GET',
                              location_id='46aecb7a-5d2c-4647-897b-0209505a9fe4',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('PolicyEvaluationRecord', response)

    def requeue_policy_evaluation(self, project, evaluation_id):
        """RequeuePolicyEvaluation.
        [Preview API] Requeue the policy evaluation.
        :param str project: Project ID or project name
        :param str evaluation_id: ID of the policy evaluation to be retrieved.
        :rtype: :class:`<PolicyEvaluationRecord> <policy.v4_1.models.PolicyEvaluationRecord>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if evaluation_id is not None:
            route_values['evaluationId'] = self._serialize.url('evaluation_id', evaluation_id, 'str')
        response = self._send(http_method='PATCH',
                              location_id='46aecb7a-5d2c-4647-897b-0209505a9fe4',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('PolicyEvaluationRecord', response)

    def get_policy_evaluations(self, project, artifact_id, include_not_applicable=None, top=None, skip=None):
        """GetPolicyEvaluations.
        [Preview API] Retrieves a list of all the policy evaluation statuses for a specific pull request.
        :param str project: Project ID or project name
        :param str artifact_id: A string which uniquely identifies the target of a policy evaluation.
        :param bool include_not_applicable: Some policies might determine that they do not apply to a specific pull request. Setting this parameter to true will return evaluation records even for policies which don't apply to this pull request.
        :param int top: The number of policy evaluation records to retrieve.
        :param int skip: The number of policy evaluation records to ignore. For example, to retrieve results 101-150, set top to 50 and skip to 100.
        :rtype: [PolicyEvaluationRecord]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if artifact_id is not None:
            query_parameters['artifactId'] = self._serialize.query('artifact_id', artifact_id, 'str')
        if include_not_applicable is not None:
            query_parameters['includeNotApplicable'] = self._serialize.query('include_not_applicable', include_not_applicable, 'bool')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        response = self._send(http_method='GET',
                              location_id='c23ddff5-229c-4d04-a80b-0fdce9f360c8',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[PolicyEvaluationRecord]', self._unwrap_collection(response))

    def get_policy_configuration_revision(self, project, configuration_id, revision_id):
        """GetPolicyConfigurationRevision.
        Retrieve a specific revision of a given policy by ID.
        :param str project: Project ID or project name
        :param int configuration_id: The policy configuration ID.
        :param int revision_id: The revision ID.
        :rtype: :class:`<PolicyConfiguration> <policy.v4_1.models.PolicyConfiguration>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if configuration_id is not None:
            route_values['configurationId'] = self._serialize.url('configuration_id', configuration_id, 'int')
        if revision_id is not None:
            route_values['revisionId'] = self._serialize.url('revision_id', revision_id, 'int')
        response = self._send(http_method='GET',
                              location_id='fe1e68a2-60d3-43cb-855b-85e41ae97c95',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('PolicyConfiguration', response)

    def get_policy_configuration_revisions(self, project, configuration_id, top=None, skip=None):
        """GetPolicyConfigurationRevisions.
        Retrieve all revisions for a given policy.
        :param str project: Project ID or project name
        :param int configuration_id: The policy configuration ID.
        :param int top: The number of revisions to retrieve.
        :param int skip: The number of revisions to ignore. For example, to retrieve results 101-150, set top to 50 and skip to 100.
        :rtype: [PolicyConfiguration]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if configuration_id is not None:
            route_values['configurationId'] = self._serialize.url('configuration_id', configuration_id, 'int')
        query_parameters = {}
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        response = self._send(http_method='GET',
                              location_id='fe1e68a2-60d3-43cb-855b-85e41ae97c95',
                              version='4.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[PolicyConfiguration]', self._unwrap_collection(response))

    def get_policy_type(self, project, type_id):
        """GetPolicyType.
        Retrieve a specific policy type by ID.
        :param str project: Project ID or project name
        :param str type_id: The policy ID.
        :rtype: :class:`<PolicyType> <policy.v4_1.models.PolicyType>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if type_id is not None:
            route_values['typeId'] = self._serialize.url('type_id', type_id, 'str')
        response = self._send(http_method='GET',
                              location_id='44096322-2d3d-466a-bb30-d1b7de69f61f',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('PolicyType', response)

    def get_policy_types(self, project):
        """GetPolicyTypes.
        Retrieve all available policy types.
        :param str project: Project ID or project name
        :rtype: [PolicyType]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        response = self._send(http_method='GET',
                              location_id='44096322-2d3d-466a-bb30-d1b7de69f61f',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('[PolicyType]', self._unwrap_collection(response))

