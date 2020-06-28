# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PackageMetadata(Model):
    """PackageMetadata.

    :param created_on: The date the package was created
    :type created_on: datetime
    :param download_url: A direct link to download the package.
    :type download_url: str
    :param filename: The UI uses this to display instructions, i.e. "unzip MyAgent.zip"
    :type filename: str
    :param hash_value: MD5 hash as a base64 string
    :type hash_value: str
    :param info_url: A link to documentation
    :type info_url: str
    :param platform: The platform (win7, linux, etc.)
    :type platform: str
    :param type: The type of package (e.g. "agent")
    :type type: str
    :param version: The package version.
    :type version: :class:`PackageVersion <task-agent.v4_1.models.PackageVersion>`
    """

    _attribute_map = {
        'created_on': {'key': 'createdOn', 'type': 'iso-8601'},
        'download_url': {'key': 'downloadUrl', 'type': 'str'},
        'filename': {'key': 'filename', 'type': 'str'},
        'hash_value': {'key': 'hashValue', 'type': 'str'},
        'info_url': {'key': 'infoUrl', 'type': 'str'},
        'platform': {'key': 'platform', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'version': {'key': 'version', 'type': 'PackageVersion'}
    }

    def __init__(self, created_on=None, download_url=None, filename=None, hash_value=None, info_url=None, platform=None, type=None, version=None):
        super(PackageMetadata, self).__init__()
        self.created_on = created_on
        self.download_url = download_url
        self.filename = filename
        self.hash_value = hash_value
        self.info_url = info_url
        self.platform = platform
        self.type = type
        self.version = version
