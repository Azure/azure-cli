# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Answers(Model):
    """Answers.

    :param vSMarketplace_extension_name: Gets or sets the vs marketplace extension name
    :type vSMarketplace_extension_name: str
    :param vSMarketplace_publisher_name: Gets or sets the vs marketplace publsiher name
    :type vSMarketplace_publisher_name: str
    """

    _attribute_map = {
        'vSMarketplace_extension_name': {'key': 'vSMarketplaceExtensionName', 'type': 'str'},
        'vSMarketplace_publisher_name': {'key': 'vSMarketplacePublisherName', 'type': 'str'}
    }

    def __init__(self, vSMarketplace_extension_name=None, vSMarketplace_publisher_name=None):
        super(Answers, self).__init__()
        self.vSMarketplace_extension_name = vSMarketplace_extension_name
        self.vSMarketplace_publisher_name = vSMarketplace_publisher_name
