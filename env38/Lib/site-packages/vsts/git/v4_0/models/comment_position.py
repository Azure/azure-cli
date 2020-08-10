# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CommentPosition(Model):
    """CommentPosition.

    :param line: Position line starting with one.
    :type line: int
    :param offset: Position offset starting with zero.
    :type offset: int
    """

    _attribute_map = {
        'line': {'key': 'line', 'type': 'int'},
        'offset': {'key': 'offset', 'type': 'int'}
    }

    def __init__(self, line=None, offset=None):
        super(CommentPosition, self).__init__()
        self.line = line
        self.offset = offset
