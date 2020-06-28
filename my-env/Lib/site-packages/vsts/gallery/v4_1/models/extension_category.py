# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionCategory(Model):
    """ExtensionCategory.

    :param associated_products: The name of the products with which this category is associated to.
    :type associated_products: list of str
    :param category_id:
    :type category_id: int
    :param category_name: This is the internal name for a category
    :type category_name: str
    :param language: This parameter is obsolete. Refer to LanguageTitles for langauge specific titles
    :type language: str
    :param language_titles: The list of all the titles of this category in various languages
    :type language_titles: list of :class:`CategoryLanguageTitle <gallery.v4_1.models.CategoryLanguageTitle>`
    :param parent_category_name: This is the internal name of the parent if this is associated with a parent
    :type parent_category_name: str
    """

    _attribute_map = {
        'associated_products': {'key': 'associatedProducts', 'type': '[str]'},
        'category_id': {'key': 'categoryId', 'type': 'int'},
        'category_name': {'key': 'categoryName', 'type': 'str'},
        'language': {'key': 'language', 'type': 'str'},
        'language_titles': {'key': 'languageTitles', 'type': '[CategoryLanguageTitle]'},
        'parent_category_name': {'key': 'parentCategoryName', 'type': 'str'}
    }

    def __init__(self, associated_products=None, category_id=None, category_name=None, language=None, language_titles=None, parent_category_name=None):
        super(ExtensionCategory, self).__init__()
        self.associated_products = associated_products
        self.category_id = category_id
        self.category_name = category_name
        self.language = language
        self.language_titles = language_titles
        self.parent_category_name = parent_category_name
