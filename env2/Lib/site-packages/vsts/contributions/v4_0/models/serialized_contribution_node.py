# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SerializedContributionNode(Model):
    """SerializedContributionNode.

    :param children: List of ids for contributions which are children to the current contribution.
    :type children: list of str
    :param contribution: Contribution associated with this node.
    :type contribution: :class:`Contribution <contributions.v4_0.models.Contribution>`
    :param parents: List of ids for contributions which are parents to the current contribution.
    :type parents: list of str
    """

    _attribute_map = {
        'children': {'key': 'children', 'type': '[str]'},
        'contribution': {'key': 'contribution', 'type': 'Contribution'},
        'parents': {'key': 'parents', 'type': '[str]'}
    }

    def __init__(self, children=None, contribution=None, parents=None):
        super(SerializedContributionNode, self).__init__()
        self.children = children
        self.contribution = contribution
        self.parents = parents
