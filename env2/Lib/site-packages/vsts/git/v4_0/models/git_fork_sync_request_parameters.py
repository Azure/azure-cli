# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitForkSyncRequestParameters(Model):
    """GitForkSyncRequestParameters.

    :param source: Fully-qualified identifier for the source repository.
    :type source: :class:`GlobalGitRepositoryKey <git.v4_0.models.GlobalGitRepositoryKey>`
    :param source_to_target_refs: If supplied, the set of ref mappings to use when performing a "sync" or create. If missing, all refs will be synchronized.
    :type source_to_target_refs: list of :class:`SourceToTargetRef <git.v4_0.models.SourceToTargetRef>`
    """

    _attribute_map = {
        'source': {'key': 'source', 'type': 'GlobalGitRepositoryKey'},
        'source_to_target_refs': {'key': 'sourceToTargetRefs', 'type': '[SourceToTargetRef]'}
    }

    def __init__(self, source=None, source_to_target_refs=None):
        super(GitForkSyncRequestParameters, self).__init__()
        self.source = source
        self.source_to_target_refs = source_to_target_refs
