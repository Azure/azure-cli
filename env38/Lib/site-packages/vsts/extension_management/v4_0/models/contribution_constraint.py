# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ContributionConstraint(Model):
    """ContributionConstraint.

    :param group: An optional property that can be specified to group constraints together. All constraints within a group are AND'd together (all must be evaluate to True in order for the contribution to be included). Different groups of constraints are OR'd (only one group needs to evaluate to True for the contribution to be included).
    :type group: int
    :param inverse: If true, negate the result of the filter (include the contribution if the applied filter returns false instead of true)
    :type inverse: bool
    :param name: Name of the IContributionFilter class
    :type name: str
    :param properties: Properties that are fed to the contribution filter class
    :type properties: :class:`object <extension-management.v4_0.models.object>`
    :param relationships: Constraints can be optionally be applied to one or more of the relationships defined in the contribution. If no relationships are defined then all relationships are associated with the constraint. This means the default behaviour will elimiate the contribution from the tree completely if the constraint is applied.
    :type relationships: list of str
    """

    _attribute_map = {
        'group': {'key': 'group', 'type': 'int'},
        'inverse': {'key': 'inverse', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'properties': {'key': 'properties', 'type': 'object'},
        'relationships': {'key': 'relationships', 'type': '[str]'}
    }

    def __init__(self, group=None, inverse=None, name=None, properties=None, relationships=None):
        super(ContributionConstraint, self).__init__()
        self.group = group
        self.inverse = inverse
        self.name = name
        self.properties = properties
        self.relationships = relationships
