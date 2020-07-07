# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseDefinition(Model):
    """ReleaseDefinition.

    :param _links: Gets links to access the release definition.
    :type _links: :class:`ReferenceLinks <release.v4_1.models.ReferenceLinks>`
    :param artifacts: Gets or sets the list of artifacts.
    :type artifacts: list of :class:`Artifact <release.v4_1.models.Artifact>`
    :param comment: Gets or sets comment.
    :type comment: str
    :param created_by: Gets or sets the identity who created.
    :type created_by: :class:`IdentityRef <release.v4_1.models.IdentityRef>`
    :param created_on: Gets date on which it got created.
    :type created_on: datetime
    :param description: Gets or sets the description.
    :type description: str
    :param environments: Gets or sets the list of environments.
    :type environments: list of :class:`ReleaseDefinitionEnvironment <release.v4_1.models.ReleaseDefinitionEnvironment>`
    :param id: Gets the unique identifier of this field.
    :type id: int
    :param is_deleted: Whether release definition is deleted.
    :type is_deleted: bool
    :param last_release: Gets the reference of last release.
    :type last_release: :class:`ReleaseReference <release.v4_1.models.ReleaseReference>`
    :param modified_by: Gets or sets the identity who modified.
    :type modified_by: :class:`IdentityRef <release.v4_1.models.IdentityRef>`
    :param modified_on: Gets date on which it got modified.
    :type modified_on: datetime
    :param name: Gets or sets the name.
    :type name: str
    :param path: Gets or sets the path.
    :type path: str
    :param pipeline_process: Gets or sets pipeline process.
    :type pipeline_process: :class:`PipelineProcess <release.v4_1.models.PipelineProcess>`
    :param properties: Gets or sets properties.
    :type properties: :class:`object <release.v4_1.models.object>`
    :param release_name_format: Gets or sets the release name format.
    :type release_name_format: str
    :param retention_policy:
    :type retention_policy: :class:`RetentionPolicy <release.v4_1.models.RetentionPolicy>`
    :param revision: Gets the revision number.
    :type revision: int
    :param source: Gets or sets source of release definition.
    :type source: object
    :param tags: Gets or sets list of tags.
    :type tags: list of str
    :param triggers: Gets or sets the list of triggers.
    :type triggers: list of :class:`object <release.v4_1.models.object>`
    :param url: Gets url to access the release definition.
    :type url: str
    :param variable_groups: Gets or sets the list of variable groups.
    :type variable_groups: list of int
    :param variables: Gets or sets the dictionary of variables.
    :type variables: dict
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'artifacts': {'key': 'artifacts', 'type': '[Artifact]'},
        'comment': {'key': 'comment', 'type': 'str'},
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'created_on': {'key': 'createdOn', 'type': 'iso-8601'},
        'description': {'key': 'description', 'type': 'str'},
        'environments': {'key': 'environments', 'type': '[ReleaseDefinitionEnvironment]'},
        'id': {'key': 'id', 'type': 'int'},
        'is_deleted': {'key': 'isDeleted', 'type': 'bool'},
        'last_release': {'key': 'lastRelease', 'type': 'ReleaseReference'},
        'modified_by': {'key': 'modifiedBy', 'type': 'IdentityRef'},
        'modified_on': {'key': 'modifiedOn', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'path': {'key': 'path', 'type': 'str'},
        'pipeline_process': {'key': 'pipelineProcess', 'type': 'PipelineProcess'},
        'properties': {'key': 'properties', 'type': 'object'},
        'release_name_format': {'key': 'releaseNameFormat', 'type': 'str'},
        'retention_policy': {'key': 'retentionPolicy', 'type': 'RetentionPolicy'},
        'revision': {'key': 'revision', 'type': 'int'},
        'source': {'key': 'source', 'type': 'object'},
        'tags': {'key': 'tags', 'type': '[str]'},
        'triggers': {'key': 'triggers', 'type': '[object]'},
        'url': {'key': 'url', 'type': 'str'},
        'variable_groups': {'key': 'variableGroups', 'type': '[int]'},
        'variables': {'key': 'variables', 'type': '{ConfigurationVariableValue}'}
    }

    def __init__(self, _links=None, artifacts=None, comment=None, created_by=None, created_on=None, description=None, environments=None, id=None, is_deleted=None, last_release=None, modified_by=None, modified_on=None, name=None, path=None, pipeline_process=None, properties=None, release_name_format=None, retention_policy=None, revision=None, source=None, tags=None, triggers=None, url=None, variable_groups=None, variables=None):
        super(ReleaseDefinition, self).__init__()
        self._links = _links
        self.artifacts = artifacts
        self.comment = comment
        self.created_by = created_by
        self.created_on = created_on
        self.description = description
        self.environments = environments
        self.id = id
        self.is_deleted = is_deleted
        self.last_release = last_release
        self.modified_by = modified_by
        self.modified_on = modified_on
        self.name = name
        self.path = path
        self.pipeline_process = pipeline_process
        self.properties = properties
        self.release_name_format = release_name_format
        self.retention_policy = retention_policy
        self.revision = revision
        self.source = source
        self.tags = tags
        self.triggers = triggers
        self.url = url
        self.variable_groups = variable_groups
        self.variables = variables
