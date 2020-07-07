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

    :param help_url: Help URL.
    :type help_url: str
    :param id: ID of the import operation.
    :type id: str
    :param is_new: Whether this imported process is new.
    :type is_new: bool
    :param promote_job_id: The promote job identifier.
    :type promote_job_id: str
    :param validation_results: The list of validation results.
    :type validation_results: list of :class:`ValidationIssue <work-item-tracking-process-template.v4_1.models.ValidationIssue>`
    """

    _attribute_map = {
        'help_url': {'key': 'helpUrl', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'is_new': {'key': 'isNew', 'type': 'bool'},
        'promote_job_id': {'key': 'promoteJobId', 'type': 'str'},
        'validation_results': {'key': 'validationResults', 'type': '[ValidationIssue]'}
    }

    def __init__(self, help_url=None, id=None, is_new=None, promote_job_id=None, validation_results=None):
        super(ProcessImportResult, self).__init__()
        self.help_url = help_url
        self.id = id
        self.is_new = is_new
        self.promote_job_id = promote_job_id
        self.validation_results = validation_results
