# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TfvcPolicyOverrideInfo(Model):
    """TfvcPolicyOverrideInfo.

    :param comment:
    :type comment: str
    :param policy_failures:
    :type policy_failures: list of :class:`TfvcPolicyFailureInfo <tfvc.v4_1.models.TfvcPolicyFailureInfo>`
    """

    _attribute_map = {
        'comment': {'key': 'comment', 'type': 'str'},
        'policy_failures': {'key': 'policyFailures', 'type': '[TfvcPolicyFailureInfo]'}
    }

    def __init__(self, comment=None, policy_failures=None):
        super(TfvcPolicyOverrideInfo, self).__init__()
        self.comment = comment
        self.policy_failures = policy_failures
