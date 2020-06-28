# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CommentThreadContext(Model):
    """CommentThreadContext.

    :param file_path: File path relative to the root of the repository. It's up to the client to use any path format.
    :type file_path: str
    :param left_file_end: Position of last character of the thread's span in left file.
    :type left_file_end: :class:`CommentPosition <git.v4_1.models.CommentPosition>`
    :param left_file_start: Position of first character of the thread's span in left file.
    :type left_file_start: :class:`CommentPosition <git.v4_1.models.CommentPosition>`
    :param right_file_end: Position of last character of the thread's span in right file.
    :type right_file_end: :class:`CommentPosition <git.v4_1.models.CommentPosition>`
    :param right_file_start: Position of first character of the thread's span in right file.
    :type right_file_start: :class:`CommentPosition <git.v4_1.models.CommentPosition>`
    """

    _attribute_map = {
        'file_path': {'key': 'filePath', 'type': 'str'},
        'left_file_end': {'key': 'leftFileEnd', 'type': 'CommentPosition'},
        'left_file_start': {'key': 'leftFileStart', 'type': 'CommentPosition'},
        'right_file_end': {'key': 'rightFileEnd', 'type': 'CommentPosition'},
        'right_file_start': {'key': 'rightFileStart', 'type': 'CommentPosition'}
    }

    def __init__(self, file_path=None, left_file_end=None, left_file_start=None, right_file_end=None, right_file_start=None):
        super(CommentThreadContext, self).__init__()
        self.file_path = file_path
        self.left_file_end = left_file_end
        self.left_file_start = left_file_start
        self.right_file_end = right_file_end
        self.right_file_start = right_file_start
