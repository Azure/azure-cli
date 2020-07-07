# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DropAccessData(Model):
    """DropAccessData.

    :param drop_container_url:
    :type drop_container_url: str
    :param sas_key:
    :type sas_key: str
    """

    _attribute_map = {
        'drop_container_url': {'key': 'dropContainerUrl', 'type': 'str'},
        'sas_key': {'key': 'sasKey', 'type': 'str'}
    }

    def __init__(self, drop_container_url=None, sas_key=None):
        super(DropAccessData, self).__init__()
        self.drop_container_url = drop_container_url
        self.sas_key = sas_key
