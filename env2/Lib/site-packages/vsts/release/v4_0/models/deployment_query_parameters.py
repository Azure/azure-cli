# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DeploymentQueryParameters(Model):
    """DeploymentQueryParameters.

    :param artifact_source_id:
    :type artifact_source_id: str
    :param artifact_type_id:
    :type artifact_type_id: str
    :param artifact_versions:
    :type artifact_versions: list of str
    :param deployment_status:
    :type deployment_status: object
    :param environments:
    :type environments: list of :class:`DefinitionEnvironmentReference <release.v4_0.models.DefinitionEnvironmentReference>`
    :param expands:
    :type expands: object
    :param is_deleted:
    :type is_deleted: bool
    :param latest_deployments_only:
    :type latest_deployments_only: bool
    :param max_deployments_per_environment:
    :type max_deployments_per_environment: int
    :param max_modified_time:
    :type max_modified_time: datetime
    :param min_modified_time:
    :type min_modified_time: datetime
    :param operation_status:
    :type operation_status: object
    :param query_order:
    :type query_order: object
    """

    _attribute_map = {
        'artifact_source_id': {'key': 'artifactSourceId', 'type': 'str'},
        'artifact_type_id': {'key': 'artifactTypeId', 'type': 'str'},
        'artifact_versions': {'key': 'artifactVersions', 'type': '[str]'},
        'deployment_status': {'key': 'deploymentStatus', 'type': 'object'},
        'environments': {'key': 'environments', 'type': '[DefinitionEnvironmentReference]'},
        'expands': {'key': 'expands', 'type': 'object'},
        'is_deleted': {'key': 'isDeleted', 'type': 'bool'},
        'latest_deployments_only': {'key': 'latestDeploymentsOnly', 'type': 'bool'},
        'max_deployments_per_environment': {'key': 'maxDeploymentsPerEnvironment', 'type': 'int'},
        'max_modified_time': {'key': 'maxModifiedTime', 'type': 'iso-8601'},
        'min_modified_time': {'key': 'minModifiedTime', 'type': 'iso-8601'},
        'operation_status': {'key': 'operationStatus', 'type': 'object'},
        'query_order': {'key': 'queryOrder', 'type': 'object'}
    }

    def __init__(self, artifact_source_id=None, artifact_type_id=None, artifact_versions=None, deployment_status=None, environments=None, expands=None, is_deleted=None, latest_deployments_only=None, max_deployments_per_environment=None, max_modified_time=None, min_modified_time=None, operation_status=None, query_order=None):
        super(DeploymentQueryParameters, self).__init__()
        self.artifact_source_id = artifact_source_id
        self.artifact_type_id = artifact_type_id
        self.artifact_versions = artifact_versions
        self.deployment_status = deployment_status
        self.environments = environments
        self.expands = expands
        self.is_deleted = is_deleted
        self.latest_deployments_only = latest_deployments_only
        self.max_deployments_per_environment = max_deployments_per_environment
        self.max_modified_time = max_modified_time
        self.min_modified_time = min_modified_time
        self.operation_status = operation_status
        self.query_order = query_order
