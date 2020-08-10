# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class LanguageStatistics(Model):
    """LanguageStatistics.

    :param bytes:
    :type bytes: long
    :param bytes_percentage:
    :type bytes_percentage: float
    :param files:
    :type files: int
    :param files_percentage:
    :type files_percentage: float
    :param name:
    :type name: str
    :param weighted_bytes_percentage:
    :type weighted_bytes_percentage: float
    """

    _attribute_map = {
        'bytes': {'key': 'bytes', 'type': 'long'},
        'bytes_percentage': {'key': 'bytesPercentage', 'type': 'float'},
        'files': {'key': 'files', 'type': 'int'},
        'files_percentage': {'key': 'filesPercentage', 'type': 'float'},
        'name': {'key': 'name', 'type': 'str'},
        'weighted_bytes_percentage': {'key': 'weightedBytesPercentage', 'type': 'float'}
    }

    def __init__(self, bytes=None, bytes_percentage=None, files=None, files_percentage=None, name=None, weighted_bytes_percentage=None):
        super(LanguageStatistics, self).__init__()
        self.bytes = bytes
        self.bytes_percentage = bytes_percentage
        self.files = files
        self.files_percentage = files_percentage
        self.name = name
        self.weighted_bytes_percentage = weighted_bytes_percentage
