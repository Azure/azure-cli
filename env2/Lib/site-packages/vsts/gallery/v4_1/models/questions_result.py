# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class QuestionsResult(Model):
    """QuestionsResult.

    :param has_more_questions: Flag indicating if there are more QnA threads to be shown (for paging)
    :type has_more_questions: bool
    :param questions: List of the QnA threads
    :type questions: list of :class:`Question <gallery.v4_1.models.Question>`
    """

    _attribute_map = {
        'has_more_questions': {'key': 'hasMoreQuestions', 'type': 'bool'},
        'questions': {'key': 'questions', 'type': '[Question]'}
    }

    def __init__(self, has_more_questions=None, questions=None):
        super(QuestionsResult, self).__init__()
        self.has_more_questions = has_more_questions
        self.questions = questions
