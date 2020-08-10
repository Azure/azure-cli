# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CommentTrackingCriteria(Model):
    """CommentTrackingCriteria.

    :param first_comparing_iteration: The iteration of the file on the left side of the diff that the thread will be tracked to. Threads were tracked if this is greater than 0.
    :type first_comparing_iteration: int
    :param orig_file_path: Original filepath the thread was created on before tracking. This will be different than the current thread filepath if the file in question was renamed in a later iteration.
    :type orig_file_path: str
    :param orig_left_file_end: Original position of last character of the thread's span in left file.
    :type orig_left_file_end: :class:`CommentPosition <git.v4_1.models.CommentPosition>`
    :param orig_left_file_start: Original position of first character of the thread's span in left file.
    :type orig_left_file_start: :class:`CommentPosition <git.v4_1.models.CommentPosition>`
    :param orig_right_file_end: Original position of last character of the thread's span in right file.
    :type orig_right_file_end: :class:`CommentPosition <git.v4_1.models.CommentPosition>`
    :param orig_right_file_start: Original position of first character of the thread's span in right file.
    :type orig_right_file_start: :class:`CommentPosition <git.v4_1.models.CommentPosition>`
    :param second_comparing_iteration: The iteration of the file on the right side of the diff that the thread will be tracked to. Threads were tracked if this is greater than 0.
    :type second_comparing_iteration: int
    """

    _attribute_map = {
        'first_comparing_iteration': {'key': 'firstComparingIteration', 'type': 'int'},
        'orig_file_path': {'key': 'origFilePath', 'type': 'str'},
        'orig_left_file_end': {'key': 'origLeftFileEnd', 'type': 'CommentPosition'},
        'orig_left_file_start': {'key': 'origLeftFileStart', 'type': 'CommentPosition'},
        'orig_right_file_end': {'key': 'origRightFileEnd', 'type': 'CommentPosition'},
        'orig_right_file_start': {'key': 'origRightFileStart', 'type': 'CommentPosition'},
        'second_comparing_iteration': {'key': 'secondComparingIteration', 'type': 'int'}
    }

    def __init__(self, first_comparing_iteration=None, orig_file_path=None, orig_left_file_end=None, orig_left_file_start=None, orig_right_file_end=None, orig_right_file_start=None, second_comparing_iteration=None):
        super(CommentTrackingCriteria, self).__init__()
        self.first_comparing_iteration = first_comparing_iteration
        self.orig_file_path = orig_file_path
        self.orig_left_file_end = orig_left_file_end
        self.orig_left_file_start = orig_left_file_start
        self.orig_right_file_end = orig_right_file_end
        self.orig_right_file_start = orig_right_file_start
        self.second_comparing_iteration = second_comparing_iteration
