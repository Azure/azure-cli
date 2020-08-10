# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CommentIterationContext(Model):
    """CommentIterationContext.

    :param first_comparing_iteration: The iteration of the file on the left side of the diff when the thread was created. If this value is equal to SecondComparingIteration, then this version is the common commit between the source and target branches of the pull request.
    :type first_comparing_iteration: int
    :param second_comparing_iteration: The iteration of the file on the right side of the diff when the thread was created.
    :type second_comparing_iteration: int
    """

    _attribute_map = {
        'first_comparing_iteration': {'key': 'firstComparingIteration', 'type': 'int'},
        'second_comparing_iteration': {'key': 'secondComparingIteration', 'type': 'int'}
    }

    def __init__(self, first_comparing_iteration=None, second_comparing_iteration=None):
        super(CommentIterationContext, self).__init__()
        self.first_comparing_iteration = first_comparing_iteration
        self.second_comparing_iteration = second_comparing_iteration
