# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class GitSuggestion(Model):
    """GitSuggestion.

    :param properties: Specific properties describing the suggestion.
    :type properties: dict
    :param type: The type of suggestion (e.g. pull request).
    :type type: str
    """

    _attribute_map = {
        'properties': {'key': 'properties', 'type': '{object}'},
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, properties=None, type=None):
        super(GitSuggestion, self).__init__()
        self.properties = properties
        self.type = type
