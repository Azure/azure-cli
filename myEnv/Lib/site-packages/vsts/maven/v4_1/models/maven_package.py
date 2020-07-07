# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MavenPackage(Model):
    """MavenPackage.

    :param artifact_id:
    :type artifact_id: str
    :param artifact_index:
    :type artifact_index: :class:`ReferenceLink <maven.v4_1.models.ReferenceLink>`
    :param artifact_metadata:
    :type artifact_metadata: :class:`ReferenceLink <maven.v4_1.models.ReferenceLink>`
    :param deleted_date:
    :type deleted_date: datetime
    :param files:
    :type files: :class:`ReferenceLinks <maven.v4_1.models.ReferenceLinks>`
    :param group_id:
    :type group_id: str
    :param pom:
    :type pom: :class:`MavenPomMetadata <maven.v4_1.models.MavenPomMetadata>`
    :param requested_file:
    :type requested_file: :class:`ReferenceLink <maven.v4_1.models.ReferenceLink>`
    :param snapshot_metadata:
    :type snapshot_metadata: :class:`ReferenceLink <maven.v4_1.models.ReferenceLink>`
    :param version:
    :type version: str
    :param versions:
    :type versions: :class:`ReferenceLinks <maven.v4_1.models.ReferenceLinks>`
    :param versions_index:
    :type versions_index: :class:`ReferenceLink <maven.v4_1.models.ReferenceLink>`
    """

    _attribute_map = {
        'artifact_id': {'key': 'artifactId', 'type': 'str'},
        'artifact_index': {'key': 'artifactIndex', 'type': 'ReferenceLink'},
        'artifact_metadata': {'key': 'artifactMetadata', 'type': 'ReferenceLink'},
        'deleted_date': {'key': 'deletedDate', 'type': 'iso-8601'},
        'files': {'key': 'files', 'type': 'ReferenceLinks'},
        'group_id': {'key': 'groupId', 'type': 'str'},
        'pom': {'key': 'pom', 'type': 'MavenPomMetadata'},
        'requested_file': {'key': 'requestedFile', 'type': 'ReferenceLink'},
        'snapshot_metadata': {'key': 'snapshotMetadata', 'type': 'ReferenceLink'},
        'version': {'key': 'version', 'type': 'str'},
        'versions': {'key': 'versions', 'type': 'ReferenceLinks'},
        'versions_index': {'key': 'versionsIndex', 'type': 'ReferenceLink'}
    }

    def __init__(self, artifact_id=None, artifact_index=None, artifact_metadata=None, deleted_date=None, files=None, group_id=None, pom=None, requested_file=None, snapshot_metadata=None, version=None, versions=None, versions_index=None):
        super(MavenPackage, self).__init__()
        self.artifact_id = artifact_id
        self.artifact_index = artifact_index
        self.artifact_metadata = artifact_metadata
        self.deleted_date = deleted_date
        self.files = files
        self.group_id = group_id
        self.pom = pom
        self.requested_file = requested_file
        self.snapshot_metadata = snapshot_metadata
        self.version = version
        self.versions = versions
        self.versions_index = versions_index
