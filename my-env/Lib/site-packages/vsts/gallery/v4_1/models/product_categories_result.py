# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProductCategoriesResult(Model):
    """ProductCategoriesResult.

    :param categories:
    :type categories: list of :class:`ProductCategory <gallery.v4_1.models.ProductCategory>`
    """

    _attribute_map = {
        'categories': {'key': 'categories', 'type': '[ProductCategory]'}
    }

    def __init__(self, categories=None):
        super(ProductCategoriesResult, self).__init__()
        self.categories = categories
