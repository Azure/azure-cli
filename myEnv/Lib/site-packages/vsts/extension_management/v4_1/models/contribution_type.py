# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .contribution_base import ContributionBase


class ContributionType(ContributionBase):
    """ContributionType.

    :param description: Description of the contribution/type
    :type description: str
    :param id: Fully qualified identifier of the contribution/type
    :type id: str
    :param visible_to: VisibleTo can be used to restrict whom can reference a given contribution/type. This value should be a list of publishers or extensions access is restricted too.  Examples: "ms" - Means only the "ms" publisher can reference this. "ms.vss-web" - Means only the "vss-web" extension from the "ms" publisher can reference this.
    :type visible_to: list of str
    :param indexed: Controls whether or not contributions of this type have the type indexed for queries. This allows clients to find all extensions that have a contribution of this type.  NOTE: Only TrustedPartners are allowed to specify indexed contribution types.
    :type indexed: bool
    :param name: Friendly name of the contribution/type
    :type name: str
    :param properties: Describes the allowed properties for this contribution type
    :type properties: dict
    """

    _attribute_map = {
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'visible_to': {'key': 'visibleTo', 'type': '[str]'},
        'indexed': {'key': 'indexed', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'properties': {'key': 'properties', 'type': '{ContributionPropertyDescription}'}
    }

    def __init__(self, description=None, id=None, visible_to=None, indexed=None, name=None, properties=None):
        super(ContributionType, self).__init__(description=description, id=id, visible_to=visible_to)
        self.indexed = indexed
        self.name = name
        self.properties = properties
