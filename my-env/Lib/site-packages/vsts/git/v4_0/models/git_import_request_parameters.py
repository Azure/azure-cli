# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitImportRequestParameters(Model):
    """GitImportRequestParameters.

    :param delete_service_endpoint_after_import_is_done: Option to delete service endpoint when import is done
    :type delete_service_endpoint_after_import_is_done: bool
    :param git_source: Source for importing git repository
    :type git_source: :class:`GitImportGitSource <git.v4_0.models.GitImportGitSource>`
    :param service_endpoint_id: Service Endpoint for connection to external endpoint
    :type service_endpoint_id: str
    :param tfvc_source: Source for importing tfvc repository
    :type tfvc_source: :class:`GitImportTfvcSource <git.v4_0.models.GitImportTfvcSource>`
    """

    _attribute_map = {
        'delete_service_endpoint_after_import_is_done': {'key': 'deleteServiceEndpointAfterImportIsDone', 'type': 'bool'},
        'git_source': {'key': 'gitSource', 'type': 'GitImportGitSource'},
        'service_endpoint_id': {'key': 'serviceEndpointId', 'type': 'str'},
        'tfvc_source': {'key': 'tfvcSource', 'type': 'GitImportTfvcSource'}
    }

    def __init__(self, delete_service_endpoint_after_import_is_done=None, git_source=None, service_endpoint_id=None, tfvc_source=None):
        super(GitImportRequestParameters, self).__init__()
        self.delete_service_endpoint_after_import_is_done = delete_service_endpoint_after_import_is_done
        self.git_source = git_source
        self.service_endpoint_id = service_endpoint_id
        self.tfvc_source = tfvc_source
