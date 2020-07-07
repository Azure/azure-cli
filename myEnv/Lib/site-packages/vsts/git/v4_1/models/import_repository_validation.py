# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ImportRepositoryValidation(Model):
    """ImportRepositoryValidation.

    :param git_source:
    :type git_source: :class:`GitImportGitSource <git.v4_1.models.GitImportGitSource>`
    :param password:
    :type password: str
    :param tfvc_source:
    :type tfvc_source: :class:`GitImportTfvcSource <git.v4_1.models.GitImportTfvcSource>`
    :param username:
    :type username: str
    """

    _attribute_map = {
        'git_source': {'key': 'gitSource', 'type': 'GitImportGitSource'},
        'password': {'key': 'password', 'type': 'str'},
        'tfvc_source': {'key': 'tfvcSource', 'type': 'GitImportTfvcSource'},
        'username': {'key': 'username', 'type': 'str'}
    }

    def __init__(self, git_source=None, password=None, tfvc_source=None, username=None):
        super(ImportRepositoryValidation, self).__init__()
        self.git_source = git_source
        self.password = password
        self.tfvc_source = tfvc_source
        self.username = username
