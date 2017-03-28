# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class StorageProperties(Model):
    """StorageProperties.

    :param status_of_primary: Gets the status of the storage account
    :type status_of_primary: str
    :param id: Gets the resource ID of the storage account
    :type id: str
    :param account_type: Gets the account type of the storage account
    :type account_type: str
    """

    _attribute_map = {
        'status_of_primary': {'key': 'statusOfPrimary', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'account_type': {'key': 'accountType', 'type': 'str'},
    }

    def __init__(self, status_of_primary=None, id=None, account_type=None):
        self.status_of_primary = status_of_primary
        self.id = id
        self.account_type = account_type
