# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ChangedIdentities(Model):
    """ChangedIdentities.

    :param identities: Changed Identities
    :type identities: list of :class:`Identity <identities.v4_1.models.Identity>`
    :param sequence_context: Last Identity SequenceId
    :type sequence_context: :class:`ChangedIdentitiesContext <identities.v4_1.models.ChangedIdentitiesContext>`
    """

    _attribute_map = {
        'identities': {'key': 'identities', 'type': '[Identity]'},
        'sequence_context': {'key': 'sequenceContext', 'type': 'ChangedIdentitiesContext'}
    }

    def __init__(self, identities=None, sequence_context=None):
        super(ChangedIdentities, self).__init__()
        self.identities = identities
        self.sequence_context = sequence_context
