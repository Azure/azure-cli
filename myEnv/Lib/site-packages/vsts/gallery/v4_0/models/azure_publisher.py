# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AzurePublisher(Model):
    """AzurePublisher.

    :param azure_publisher_id:
    :type azure_publisher_id: str
    :param publisher_name:
    :type publisher_name: str
    """

    _attribute_map = {
        'azure_publisher_id': {'key': 'azurePublisherId', 'type': 'str'},
        'publisher_name': {'key': 'publisherName', 'type': 'str'}
    }

    def __init__(self, azure_publisher_id=None, publisher_name=None):
        super(AzurePublisher, self).__init__()
        self.azure_publisher_id = azure_publisher_id
        self.publisher_name = publisher_name
