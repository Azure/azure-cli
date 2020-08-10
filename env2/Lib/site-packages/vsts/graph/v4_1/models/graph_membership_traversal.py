# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GraphMembershipTraversal(Model):
    """GraphMembershipTraversal.

    :param incompleteness_reason: Reason why the subject could not be traversed completely
    :type incompleteness_reason: str
    :param is_complete: When true, the subject is traversed completely
    :type is_complete: bool
    :param subject_descriptor: The traversed subject descriptor
    :type subject_descriptor: :class:`str <graph.v4_1.models.str>`
    :param traversed_subject_ids: Subject descriptor ids of the traversed members
    :type traversed_subject_ids: list of str
    :param traversed_subjects: Subject descriptors of the traversed members
    :type traversed_subjects: list of :class:`str <graph.v4_1.models.str>`
    """

    _attribute_map = {
        'incompleteness_reason': {'key': 'incompletenessReason', 'type': 'str'},
        'is_complete': {'key': 'isComplete', 'type': 'bool'},
        'subject_descriptor': {'key': 'subjectDescriptor', 'type': 'str'},
        'traversed_subject_ids': {'key': 'traversedSubjectIds', 'type': '[str]'},
        'traversed_subjects': {'key': 'traversedSubjects', 'type': '[str]'}
    }

    def __init__(self, incompleteness_reason=None, is_complete=None, subject_descriptor=None, traversed_subject_ids=None, traversed_subjects=None):
        super(GraphMembershipTraversal, self).__init__()
        self.incompleteness_reason = incompleteness_reason
        self.is_complete = is_complete
        self.subject_descriptor = subject_descriptor
        self.traversed_subject_ids = traversed_subject_ids
        self.traversed_subjects = traversed_subjects
