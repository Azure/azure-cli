# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MavenPomCi(Model):
    """MavenPomCi.

    :param notifiers:
    :type notifiers: list of :class:`MavenPomCiNotifier <maven.v4_1.models.MavenPomCiNotifier>`
    :param system:
    :type system: str
    :param url:
    :type url: str
    """

    _attribute_map = {
        'notifiers': {'key': 'notifiers', 'type': '[MavenPomCiNotifier]'},
        'system': {'key': 'system', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, notifiers=None, system=None, url=None):
        super(MavenPomCi, self).__init__()
        self.notifiers = notifiers
        self.system = system
        self.url = url
