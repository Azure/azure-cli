# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitImportRequest(Model):
    """GitImportRequest.

    :param _links: Links to related resources.
    :type _links: :class:`ReferenceLinks <git.v4_1.models.ReferenceLinks>`
    :param detailed_status: Detailed status of the import, including the current step and an error message, if applicable.
    :type detailed_status: :class:`GitImportStatusDetail <git.v4_1.models.GitImportStatusDetail>`
    :param import_request_id: The unique identifier for this import request.
    :type import_request_id: int
    :param parameters: Parameters for creating the import request.
    :type parameters: :class:`GitImportRequestParameters <git.v4_1.models.GitImportRequestParameters>`
    :param repository: The target repository for this import.
    :type repository: :class:`GitRepository <git.v4_1.models.GitRepository>`
    :param status: Current status of the import.
    :type status: object
    :param url: A link back to this import request resource.
    :type url: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'detailed_status': {'key': 'detailedStatus', 'type': 'GitImportStatusDetail'},
        'import_request_id': {'key': 'importRequestId', 'type': 'int'},
        'parameters': {'key': 'parameters', 'type': 'GitImportRequestParameters'},
        'repository': {'key': 'repository', 'type': 'GitRepository'},
        'status': {'key': 'status', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, _links=None, detailed_status=None, import_request_id=None, parameters=None, repository=None, status=None, url=None):
        super(GitImportRequest, self).__init__()
        self._links = _links
        self.detailed_status = detailed_status
        self.import_request_id = import_request_id
        self.parameters = parameters
        self.repository = repository
        self.status = status
        self.url = url
