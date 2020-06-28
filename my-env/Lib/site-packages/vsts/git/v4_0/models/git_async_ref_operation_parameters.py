# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitAsyncRefOperationParameters(Model):
    """GitAsyncRefOperationParameters.

    :param generated_ref_name:
    :type generated_ref_name: str
    :param onto_ref_name:
    :type onto_ref_name: str
    :param repository:
    :type repository: :class:`GitRepository <git.v4_0.models.GitRepository>`
    :param source:
    :type source: :class:`GitAsyncRefOperationSource <git.v4_0.models.GitAsyncRefOperationSource>`
    """

    _attribute_map = {
        'generated_ref_name': {'key': 'generatedRefName', 'type': 'str'},
        'onto_ref_name': {'key': 'ontoRefName', 'type': 'str'},
        'repository': {'key': 'repository', 'type': 'GitRepository'},
        'source': {'key': 'source', 'type': 'GitAsyncRefOperationSource'}
    }

    def __init__(self, generated_ref_name=None, onto_ref_name=None, repository=None, source=None):
        super(GitAsyncRefOperationParameters, self).__init__()
        self.generated_ref_name = generated_ref_name
        self.onto_ref_name = onto_ref_name
        self.repository = repository
        self.source = source
