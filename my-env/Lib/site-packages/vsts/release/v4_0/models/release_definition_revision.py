# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseDefinitionRevision(Model):
    """ReleaseDefinitionRevision.

    :param api_version: Gets api-version for revision object.
    :type api_version: str
    :param changed_by: Gets the identity who did change.
    :type changed_by: :class:`IdentityRef <release.v4_0.models.IdentityRef>`
    :param changed_date: Gets date on which it got changed.
    :type changed_date: datetime
    :param change_type: Gets type of change.
    :type change_type: object
    :param comment: Gets comments for revision.
    :type comment: str
    :param definition_id: Get id of the definition.
    :type definition_id: int
    :param definition_url: Gets definition url.
    :type definition_url: str
    :param revision: Get revision number of the definition.
    :type revision: int
    """

    _attribute_map = {
        'api_version': {'key': 'apiVersion', 'type': 'str'},
        'changed_by': {'key': 'changedBy', 'type': 'IdentityRef'},
        'changed_date': {'key': 'changedDate', 'type': 'iso-8601'},
        'change_type': {'key': 'changeType', 'type': 'object'},
        'comment': {'key': 'comment', 'type': 'str'},
        'definition_id': {'key': 'definitionId', 'type': 'int'},
        'definition_url': {'key': 'definitionUrl', 'type': 'str'},
        'revision': {'key': 'revision', 'type': 'int'}
    }

    def __init__(self, api_version=None, changed_by=None, changed_date=None, change_type=None, comment=None, definition_id=None, definition_url=None, revision=None):
        super(ReleaseDefinitionRevision, self).__init__()
        self.api_version = api_version
        self.changed_by = changed_by
        self.changed_date = changed_date
        self.change_type = change_type
        self.comment = comment
        self.definition_id = definition_id
        self.definition_url = definition_url
        self.revision = revision
