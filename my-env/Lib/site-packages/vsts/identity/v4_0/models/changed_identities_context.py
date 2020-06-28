# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ChangedIdentitiesContext(Model):
    """ChangedIdentitiesContext.

    :param group_sequence_id: Last Group SequenceId
    :type group_sequence_id: int
    :param identity_sequence_id: Last Identity SequenceId
    :type identity_sequence_id: int
    """

    _attribute_map = {
        'group_sequence_id': {'key': 'groupSequenceId', 'type': 'int'},
        'identity_sequence_id': {'key': 'identitySequenceId', 'type': 'int'}
    }

    def __init__(self, group_sequence_id=None, identity_sequence_id=None):
        super(ChangedIdentitiesContext, self).__init__()
        self.group_sequence_id = group_sequence_id
        self.identity_sequence_id = identity_sequence_id
