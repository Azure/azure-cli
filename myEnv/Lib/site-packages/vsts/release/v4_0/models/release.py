# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Release(Model):
    """Release.

    :param _links: Gets links to access the release.
    :type _links: :class:`ReferenceLinks <release.v4_0.models.ReferenceLinks>`
    :param artifacts: Gets or sets the list of artifacts.
    :type artifacts: list of :class:`Artifact <release.v4_0.models.Artifact>`
    :param comment: Gets or sets comment.
    :type comment: str
    :param created_by: Gets or sets the identity who created.
    :type created_by: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param created_on: Gets date on which it got created.
    :type created_on: datetime
    :param definition_snapshot_revision: Gets revision number of definition snapshot.
    :type definition_snapshot_revision: int
    :param description: Gets or sets description of release.
    :type description: str
    :param environments: Gets list of environments.
    :type environments: list of :class:`ReleaseEnvironment <release.v4_0.models.ReleaseEnvironment>`
    :param id: Gets the unique identifier of this field.
    :type id: int
    :param keep_forever: Whether to exclude the release from retention policies.
    :type keep_forever: bool
    :param logs_container_url: Gets logs container url.
    :type logs_container_url: str
    :param modified_by: Gets or sets the identity who modified.
    :type modified_by: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param modified_on: Gets date on which it got modified.
    :type modified_on: datetime
    :param name: Gets name.
    :type name: str
    :param pool_name: Gets pool name.
    :type pool_name: str
    :param project_reference: Gets or sets project reference.
    :type project_reference: :class:`ProjectReference <release.v4_0.models.ProjectReference>`
    :param properties:
    :type properties: :class:`object <release.v4_0.models.object>`
    :param reason: Gets reason of release.
    :type reason: object
    :param release_definition: Gets releaseDefinitionReference which specifies the reference of the release definition to which this release is associated.
    :type release_definition: :class:`ReleaseDefinitionShallowReference <release.v4_0.models.ReleaseDefinitionShallowReference>`
    :param release_name_format: Gets release name format.
    :type release_name_format: str
    :param status: Gets status.
    :type status: object
    :param tags: Gets or sets list of tags.
    :type tags: list of str
    :param url:
    :type url: str
    :param variable_groups: Gets the list of variable groups.
    :type variable_groups: list of :class:`VariableGroup <release.v4_0.models.VariableGroup>`
    :param variables: Gets or sets the dictionary of variables.
    :type variables: dict
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'artifacts': {'key': 'artifacts', 'type': '[Artifact]'},
        'comment': {'key': 'comment', 'type': 'str'},
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'created_on': {'key': 'createdOn', 'type': 'iso-8601'},
        'definition_snapshot_revision': {'key': 'definitionSnapshotRevision', 'type': 'int'},
        'description': {'key': 'description', 'type': 'str'},
        'environments': {'key': 'environments', 'type': '[ReleaseEnvironment]'},
        'id': {'key': 'id', 'type': 'int'},
        'keep_forever': {'key': 'keepForever', 'type': 'bool'},
        'logs_container_url': {'key': 'logsContainerUrl', 'type': 'str'},
        'modified_by': {'key': 'modifiedBy', 'type': 'IdentityRef'},
        'modified_on': {'key': 'modifiedOn', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'pool_name': {'key': 'poolName', 'type': 'str'},
        'project_reference': {'key': 'projectReference', 'type': 'ProjectReference'},
        'properties': {'key': 'properties', 'type': 'object'},
        'reason': {'key': 'reason', 'type': 'object'},
        'release_definition': {'key': 'releaseDefinition', 'type': 'ReleaseDefinitionShallowReference'},
        'release_name_format': {'key': 'releaseNameFormat', 'type': 'str'},
        'status': {'key': 'status', 'type': 'object'},
        'tags': {'key': 'tags', 'type': '[str]'},
        'url': {'key': 'url', 'type': 'str'},
        'variable_groups': {'key': 'variableGroups', 'type': '[VariableGroup]'},
        'variables': {'key': 'variables', 'type': '{ConfigurationVariableValue}'}
    }

    def __init__(self, _links=None, artifacts=None, comment=None, created_by=None, created_on=None, definition_snapshot_revision=None, description=None, environments=None, id=None, keep_forever=None, logs_container_url=None, modified_by=None, modified_on=None, name=None, pool_name=None, project_reference=None, properties=None, reason=None, release_definition=None, release_name_format=None, status=None, tags=None, url=None, variable_groups=None, variables=None):
        super(Release, self).__init__()
        self._links = _links
        self.artifacts = artifacts
        self.comment = comment
        self.created_by = created_by
        self.created_on = created_on
        self.definition_snapshot_revision = definition_snapshot_revision
        self.description = description
        self.environments = environments
        self.id = id
        self.keep_forever = keep_forever
        self.logs_container_url = logs_container_url
        self.modified_by = modified_by
        self.modified_on = modified_on
        self.name = name
        self.pool_name = pool_name
        self.project_reference = project_reference
        self.properties = properties
        self.reason = reason
        self.release_definition = release_definition
        self.release_name_format = release_name_format
        self.status = status
        self.tags = tags
        self.url = url
        self.variable_groups = variable_groups
        self.variables = variables
