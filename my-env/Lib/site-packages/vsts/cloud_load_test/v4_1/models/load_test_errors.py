# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class LoadTestErrors(Model):
    """LoadTestErrors.

    :param count:
    :type count: int
    :param occurrences:
    :type occurrences: int
    :param types:
    :type types: list of :class:`object <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.object>`
    :param url:
    :type url: str
    """

    _attribute_map = {
        'count': {'key': 'count', 'type': 'int'},
        'occurrences': {'key': 'occurrences', 'type': 'int'},
        'types': {'key': 'types', 'type': '[object]'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, count=None, occurrences=None, types=None, url=None):
        super(LoadTestErrors, self).__init__()
        self.count = count
        self.occurrences = occurrences
        self.types = types
        self.url = url
