# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PermissionEvaluationBatch(Model):
    """PermissionEvaluationBatch.

    :param always_allow_administrators:
    :type always_allow_administrators: bool
    :param evaluations: Array of permission evaluations to evaluate.
    :type evaluations: list of :class:`PermissionEvaluation <security.v4_0.models.PermissionEvaluation>`
    """

    _attribute_map = {
        'always_allow_administrators': {'key': 'alwaysAllowAdministrators', 'type': 'bool'},
        'evaluations': {'key': 'evaluations', 'type': '[PermissionEvaluation]'}
    }

    def __init__(self, always_allow_administrators=None, evaluations=None):
        super(PermissionEvaluationBatch, self).__init__()
        self.always_allow_administrators = always_allow_administrators
        self.evaluations = evaluations
