# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ContributionBase(Model):
    """ContributionBase.

    :param description: Description of the contribution/type
    :type description: str
    :param id: Fully qualified identifier of the contribution/type
    :type id: str
    :param visible_to: VisibleTo can be used to restrict whom can reference a given contribution/type. This value should be a list of publishers or extensions access is restricted too.  Examples: "ms" - Means only the "ms" publisher can reference this. "ms.vss-web" - Means only the "vss-web" extension from the "ms" publisher can reference this.
    :type visible_to: list of str
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'visible_to': {'key': 'visibleTo', 'type': '[str]'}
    }

    def __init__(self, description=None, id=None, visible_to=None):
        super(ContributionBase, self).__init__()
        self.description = description
        self.id = id
        self.visible_to = visible_to
