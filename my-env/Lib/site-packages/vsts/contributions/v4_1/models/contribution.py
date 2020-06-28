# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .contribution_base import ContributionBase


class Contribution(ContributionBase):
    """Contribution.

    :param description: Description of the contribution/type
    :type description: str
    :param id: Fully qualified identifier of the contribution/type
    :type id: str
    :param visible_to: VisibleTo can be used to restrict whom can reference a given contribution/type. This value should be a list of publishers or extensions access is restricted too.  Examples: "ms" - Means only the "ms" publisher can reference this. "ms.vss-web" - Means only the "vss-web" extension from the "ms" publisher can reference this.
    :type visible_to: list of str
    :param constraints: List of constraints (filters) that should be applied to the availability of this contribution
    :type constraints: list of :class:`ContributionConstraint <contributions.v4_1.models.ContributionConstraint>`
    :param includes: Includes is a set of contributions that should have this contribution included in their targets list.
    :type includes: list of str
    :param properties: Properties/attributes of this contribution
    :type properties: :class:`object <contributions.v4_1.models.object>`
    :param restricted_to: List of demanded claims in order for the user to see this contribution (like anonymous, public, member...).
    :type restricted_to: list of str
    :param targets: The ids of the contribution(s) that this contribution targets. (parent contributions)
    :type targets: list of str
    :param type: Id of the Contribution Type
    :type type: str
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'visible_to': {'key': 'visibleTo', 'type': '[str]'},
        'constraints': {'key': 'constraints', 'type': '[ContributionConstraint]'},
        'includes': {'key': 'includes', 'type': '[str]'},
        'properties': {'key': 'properties', 'type': 'object'},
        'restricted_to': {'key': 'restrictedTo', 'type': '[str]'},
        'targets': {'key': 'targets', 'type': '[str]'},
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, description=None, id=None, visible_to=None, constraints=None, includes=None, properties=None, restricted_to=None, targets=None, type=None):
        super(Contribution, self).__init__(description=description, id=id, visible_to=visible_to)
        self.constraints = constraints
        self.includes = includes
        self.properties = properties
        self.restricted_to = restricted_to
        self.targets = targets
        self.type = type
