# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AgentGroupAccessData(Model):
    """AgentGroupAccessData.

    :param details:
    :type details: str
    :param storage_connection_string:
    :type storage_connection_string: str
    :param storage_end_point:
    :type storage_end_point: str
    :param storage_name:
    :type storage_name: str
    :param storage_type:
    :type storage_type: str
    """

    _attribute_map = {
        'details': {'key': 'details', 'type': 'str'},
        'storage_connection_string': {'key': 'storageConnectionString', 'type': 'str'},
        'storage_end_point': {'key': 'storageEndPoint', 'type': 'str'},
        'storage_name': {'key': 'storageName', 'type': 'str'},
        'storage_type': {'key': 'storageType', 'type': 'str'}
    }

    def __init__(self, details=None, storage_connection_string=None, storage_end_point=None, storage_name=None, storage_type=None):
        super(AgentGroupAccessData, self).__init__()
        self.details = details
        self.storage_connection_string = storage_connection_string
        self.storage_end_point = storage_end_point
        self.storage_name = storage_name
        self.storage_type = storage_type
