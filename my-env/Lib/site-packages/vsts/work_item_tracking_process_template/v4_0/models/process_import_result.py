# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProcessImportResult(Model):
    """ProcessImportResult.

    :param help_url:
    :type help_url: str
    :param id:
    :type id: str
    :param promote_job_id:
    :type promote_job_id: str
    :param validation_results:
    :type validation_results: list of :class:`ValidationIssue <work-item-tracking-process-template.v4_0.models.ValidationIssue>`
    """

    _attribute_map = {
        'help_url': {'key': 'helpUrl', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'promote_job_id': {'key': 'promoteJobId', 'type': 'str'},
        'validation_results': {'key': 'validationResults', 'type': '[ValidationIssue]'}
    }

    def __init__(self, help_url=None, id=None, promote_job_id=None, validation_results=None):
        super(ProcessImportResult, self).__init__()
        self.help_url = help_url
        self.id = id
        self.promote_job_id = promote_job_id
        self.validation_results = validation_results
