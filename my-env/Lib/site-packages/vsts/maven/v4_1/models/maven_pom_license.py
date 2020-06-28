# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .maven_pom_organization import MavenPomOrganization


class MavenPomLicense(MavenPomOrganization):
    """MavenPomLicense.

    :param name:
    :type name: str
    :param url:
    :type url: str
    :param distribution:
    :type distribution: str
    """

    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'distribution': {'key': 'distribution', 'type': 'str'}
    }

    def __init__(self, name=None, url=None, distribution=None):
        super(MavenPomLicense, self).__init__(name=name, url=url)
        self.distribution = distribution
