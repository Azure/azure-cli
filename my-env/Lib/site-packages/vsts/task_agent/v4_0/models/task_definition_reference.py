# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskDefinitionReference(Model):
    """TaskDefinitionReference.

    :param definition_type: Gets or sets the definition type. Values can be 'task' or 'metaTask'.
    :type definition_type: str
    :param id: Gets or sets the unique identifier of task.
    :type id: str
    :param version_spec: Gets or sets the version specification of task.
    :type version_spec: str
    """

    _attribute_map = {
        'definition_type': {'key': 'definitionType', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'version_spec': {'key': 'versionSpec', 'type': 'str'}
    }

    def __init__(self, definition_type=None, id=None, version_spec=None):
        super(TaskDefinitionReference, self).__init__()
        self.definition_type = definition_type
        self.id = id
        self.version_spec = version_spec
