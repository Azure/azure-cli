# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BrowserMix(Model):
    """BrowserMix.

    :param browser_name:
    :type browser_name: str
    :param browser_percentage:
    :type browser_percentage: int
    """

    _attribute_map = {
        'browser_name': {'key': 'browserName', 'type': 'str'},
        'browser_percentage': {'key': 'browserPercentage', 'type': 'int'}
    }

    def __init__(self, browser_name=None, browser_percentage=None):
        super(BrowserMix, self).__init__()
        self.browser_name = browser_name
        self.browser_percentage = browser_percentage
