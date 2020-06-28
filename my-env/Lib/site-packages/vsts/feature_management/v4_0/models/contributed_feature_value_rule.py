# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ContributedFeatureValueRule(Model):
    """ContributedFeatureValueRule.

    :param name: Name of the IContributedFeatureValuePlugin to run
    :type name: str
    :param properties: Properties to feed to the IContributedFeatureValuePlugin
    :type properties: dict
    """

    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'properties': {'key': 'properties', 'type': '{object}'}
    }

    def __init__(self, name=None, properties=None):
        super(ContributedFeatureValueRule, self).__init__()
        self.name = name
        self.properties = properties
