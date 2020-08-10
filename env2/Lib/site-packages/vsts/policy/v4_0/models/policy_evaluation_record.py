# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PolicyEvaluationRecord(Model):
    """PolicyEvaluationRecord.

    :param _links:
    :type _links: :class:`ReferenceLinks <policy.v4_0.models.ReferenceLinks>`
    :param artifact_id:
    :type artifact_id: str
    :param completed_date:
    :type completed_date: datetime
    :param configuration:
    :type configuration: :class:`PolicyConfiguration <policy.v4_0.models.PolicyConfiguration>`
    :param context:
    :type context: :class:`object <policy.v4_0.models.object>`
    :param evaluation_id:
    :type evaluation_id: str
    :param started_date:
    :type started_date: datetime
    :param status:
    :type status: object
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'artifact_id': {'key': 'artifactId', 'type': 'str'},
        'completed_date': {'key': 'completedDate', 'type': 'iso-8601'},
        'configuration': {'key': 'configuration', 'type': 'PolicyConfiguration'},
        'context': {'key': 'context', 'type': 'object'},
        'evaluation_id': {'key': 'evaluationId', 'type': 'str'},
        'started_date': {'key': 'startedDate', 'type': 'iso-8601'},
        'status': {'key': 'status', 'type': 'object'}
    }

    def __init__(self, _links=None, artifact_id=None, completed_date=None, configuration=None, context=None, evaluation_id=None, started_date=None, status=None):
        super(PolicyEvaluationRecord, self).__init__()
        self._links = _links
        self.artifact_id = artifact_id
        self.completed_date = completed_date
        self.configuration = configuration
        self.context = context
        self.evaluation_id = evaluation_id
        self.started_date = started_date
        self.status = status
