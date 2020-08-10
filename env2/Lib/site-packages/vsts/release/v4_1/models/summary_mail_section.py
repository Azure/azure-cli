# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class SummaryMailSection(Model):
    """SummaryMailSection.

    :param html_content:
    :type html_content: str
    :param rank:
    :type rank: int
    :param section_type:
    :type section_type: object
    :param title:
    :type title: str
    """

    _attribute_map = {
        'html_content': {'key': 'htmlContent', 'type': 'str'},
        'rank': {'key': 'rank', 'type': 'int'},
        'section_type': {'key': 'sectionType', 'type': 'object'},
        'title': {'key': 'title', 'type': 'str'}
    }

    def __init__(self, html_content=None, rank=None, section_type=None, title=None):
        super(SummaryMailSection, self).__init__()
        self.html_content = html_content
        self.rank = rank
        self.section_type = section_type
        self.title = title
