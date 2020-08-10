# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DataProviderContext(Model):
    """DataProviderContext.

    :param properties: Generic property bag that contains context-specific properties that data providers can use when populating their data dictionary
    :type properties: dict
    """

    _attribute_map = {
        'properties': {'key': 'properties', 'type': '{object}'}
    }

    def __init__(self, properties=None):
        super(DataProviderContext, self).__init__()
        self.properties = properties
