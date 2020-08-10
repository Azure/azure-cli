# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CategoryLanguageTitle(Model):
    """CategoryLanguageTitle.

    :param lang: The language for which the title is applicable
    :type lang: str
    :param lcid: The language culture id of the lang parameter
    :type lcid: int
    :param title: Actual title to be shown on the UI
    :type title: str
    """

    _attribute_map = {
        'lang': {'key': 'lang', 'type': 'str'},
        'lcid': {'key': 'lcid', 'type': 'int'},
        'title': {'key': 'title', 'type': 'str'}
    }

    def __init__(self, lang=None, lcid=None, title=None):
        super(CategoryLanguageTitle, self).__init__()
        self.lang = lang
        self.lcid = lcid
        self.title = title
