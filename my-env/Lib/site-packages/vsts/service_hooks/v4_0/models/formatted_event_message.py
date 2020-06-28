# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FormattedEventMessage(Model):
    """FormattedEventMessage.

    :param html: Gets or sets the html format of the message
    :type html: str
    :param markdown: Gets or sets the markdown format of the message
    :type markdown: str
    :param text: Gets or sets the raw text of the message
    :type text: str
    """

    _attribute_map = {
        'html': {'key': 'html', 'type': 'str'},
        'markdown': {'key': 'markdown', 'type': 'str'},
        'text': {'key': 'text', 'type': 'str'}
    }

    def __init__(self, html=None, markdown=None, text=None):
        super(FormattedEventMessage, self).__init__()
        self.html = html
        self.markdown = markdown
        self.text = text
