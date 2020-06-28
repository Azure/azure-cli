# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CategoriesResult(Model):
    """CategoriesResult.

    :param categories:
    :type categories: list of :class:`ExtensionCategory <gallery.v4_0.models.ExtensionCategory>`
    """

    _attribute_map = {
        'categories': {'key': 'categories', 'type': '[ExtensionCategory]'}
    }

    def __init__(self, categories=None):
        super(CategoriesResult, self).__init__()
        self.categories = categories
