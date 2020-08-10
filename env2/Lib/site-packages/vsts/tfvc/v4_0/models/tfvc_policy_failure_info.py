# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TfvcPolicyFailureInfo(Model):
    """TfvcPolicyFailureInfo.

    :param message:
    :type message: str
    :param policy_name:
    :type policy_name: str
    """

    _attribute_map = {
        'message': {'key': 'message', 'type': 'str'},
        'policy_name': {'key': 'policyName', 'type': 'str'}
    }

    def __init__(self, message=None, policy_name=None):
        super(TfvcPolicyFailureInfo, self).__init__()
        self.message = message
        self.policy_name = policy_name
