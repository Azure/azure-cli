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

    :param first_comparing_iteration: The first comparing iteration being viewed. Threads will be tracked if this is greater than 0.
    :type first_comparing_iteration: int
    :param orig_left_file_end: Original position of last character of the comment in left file.
    :type orig_left_file_end: :class:`CommentPosition <git.v4_0.models.CommentPosition>`
    :param orig_left_file_start: Original position of first character of the comment in left file.
    :type orig_left_file_start: :class:`CommentPosition <git.v4_0.models.CommentPosition>`
    :param orig_right_file_end: Original position of last character of the comment in right file.
    :type orig_right_file_end: :class:`CommentPosition <git.v4_0.models.CommentPosition>`
    :param orig_right_file_start: Original position of first character of the comment in right file.
    :type orig_right_file_start: :class:`CommentPosition <git.v4_0.models.CommentPosition>`
    :param second_comparing_iteration: The second comparing iteration being viewed. Threads will be tracked if this is greater than 0.
    :type second_comparing_iteration: int
    """

    _attribute_map = {
        'first_comparing_iteration': {'key': 'firstComparingIteration', 'type': 'int'},
        'orig_left_file_end': {'key': 'origLeftFileEnd', 'type': 'CommentPosition'},
        'orig_left_file_start': {'key': 'origLeftFileStart', 'type': 'CommentPosition'},
        'orig_right_file_end': {'key': 'origRightFileEnd', 'type': 'CommentPosition'},
        'orig_right_file_start': {'key': 'origRightFileStart', 'type': 'CommentPosition'},
        'second_comparing_iteration': {'key': 'secondComparingIteration', 'type': 'int'}
    }

    def __init__(self, first_comparing_iteration=None, orig_left_file_end=None, orig_left_file_start=None, orig_right_file_end=None, orig_right_file_start=None, second_comparing_iteration=None):
        super(CommentTrackingCriteria, self).__init__()
        self.first_comparing_iteration = first_comparing_iteration
        self.orig_left_file_end = orig_left_file_end
        self.orig_left_file_start = orig_left_file_start
        self.orig_right_file_end = orig_right_file_end
        self.orig_right_file_start = orig_right_file_start
        self.second_comparing_iteration = second_comparing_iteration
