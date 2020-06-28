# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProductCategory(Model):
    """ProductCategory.

    :param children:
    :type children: list of :class:`ProductCategory <gallery.v4_0.models.ProductCategory>`
    :param has_children: Indicator whether this is a leaf or there are children under this category
    :type has_children: bool
    :param id: Individual Guid of the Category
    :type id: str
    :param title: Category Title in the requested language
    :type title: str
    """

    _attribute_map = {
        'children': {'key': 'children', 'type': '[ProductCategory]'},
        'has_children': {'key': 'hasChildren', 'type': 'bool'},
        'id': {'key': 'id', 'type': 'str'},
        'title': {'key': 'title', 'type': 'str'}
    }

    def __init__(self, children=None, has_children=None, id=None, title=None):
        super(ProductCategory, self).__init__()
        self.children = children
        self.has_children = has_children
        self.id = id
        self.title = title
