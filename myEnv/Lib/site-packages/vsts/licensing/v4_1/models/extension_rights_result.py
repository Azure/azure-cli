# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionRightsResult(Model):
    """ExtensionRightsResult.

    :param entitled_extensions:
    :type entitled_extensions: list of str
    :param host_id:
    :type host_id: str
    :param reason:
    :type reason: str
    :param reason_code:
    :type reason_code: object
    :param result_code:
    :type result_code: object
    """

    _attribute_map = {
        'entitled_extensions': {'key': 'entitledExtensions', 'type': '[str]'},
        'host_id': {'key': 'hostId', 'type': 'str'},
        'reason': {'key': 'reason', 'type': 'str'},
        'reason_code': {'key': 'reasonCode', 'type': 'object'},
        'result_code': {'key': 'resultCode', 'type': 'object'}
    }

    def __init__(self, entitled_extensions=None, host_id=None, reason=None, reason_code=None, result_code=None):
        super(ExtensionRightsResult, self).__init__()
        self.entitled_extensions = entitled_extensions
        self.host_id = host_id
        self.reason = reason
        self.reason_code = reason_code
        self.result_code = result_code
