# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest import Serializer, Deserializer
from ...vss_client import VssClient
from . import models


class MavenClient(VssClient):
    """Maven
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(MavenClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = '6f7f8c07-ff36-473c-bcf3-bd6cc9b6c066'

    def delete_package_version_from_recycle_bin(self, feed, group_id, artifact_id, version):
        """DeletePackageVersionFromRecycleBin.
        [Preview API]
        :param str feed:
        :param str group_id:
        :param str artifact_id:
        :param str version:
        """
        route_values = {}
        if feed is not None:
            route_values['feed'] = self._serialize.url('feed', feed, 'str')
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        if artifact_id is not None:
            route_values['artifactId'] = self._serialize.url('artifact_id', artifact_id, 'str')
        if version is not None:
            route_values['version'] = self._serialize.url('version', version, 'str')
        self._send(http_method='DELETE',
                   location_id='f67e10eb-1254-4953-add7-d49b83a16c9f',
                   version='4.1-preview.1',
                   route_values=route_values)

    def get_package_version_metadata_from_recycle_bin(self, feed, group_id, artifact_id, version):
        """GetPackageVersionMetadataFromRecycleBin.
        [Preview API]
        :param str feed:
        :param str group_id:
        :param str artifact_id:
        :param str version:
        :rtype: :class:`<MavenPackageVersionDeletionState> <maven.v4_1.models.MavenPackageVersionDeletionState>`
        """
        route_values = {}
        if feed is not None:
            route_values['feed'] = self._serialize.url('feed', feed, 'str')
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        if artifact_id is not None:
            route_values['artifactId'] = self._serialize.url('artifact_id', artifact_id, 'str')
        if version is not None:
            route_values['version'] = self._serialize.url('version', version, 'str')
        response = self._send(http_method='GET',
                              location_id='f67e10eb-1254-4953-add7-d49b83a16c9f',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('MavenPackageVersionDeletionState', response)

    def restore_package_version_from_recycle_bin(self, package_version_details, feed, group_id, artifact_id, version):
        """RestorePackageVersionFromRecycleBin.
        [Preview API]
        :param :class:`<MavenRecycleBinPackageVersionDetails> <maven.v4_1.models.MavenRecycleBinPackageVersionDetails>` package_version_details:
        :param str feed:
        :param str group_id:
        :param str artifact_id:
        :param str version:
        """
        route_values = {}
        if feed is not None:
            route_values['feed'] = self._serialize.url('feed', feed, 'str')
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        if artifact_id is not None:
            route_values['artifactId'] = self._serialize.url('artifact_id', artifact_id, 'str')
        if version is not None:
            route_values['version'] = self._serialize.url('version', version, 'str')
        content = self._serialize.body(package_version_details, 'MavenRecycleBinPackageVersionDetails')
        self._send(http_method='PATCH',
                   location_id='f67e10eb-1254-4953-add7-d49b83a16c9f',
                   version='4.1-preview.1',
                   route_values=route_values,
                   content=content)

    def get_package_version(self, feed, group_id, artifact_id, version, show_deleted=None):
        """GetPackageVersion.
        [Preview API]
        :param str feed:
        :param str group_id:
        :param str artifact_id:
        :param str version:
        :param bool show_deleted:
        :rtype: :class:`<Package> <maven.v4_1.models.Package>`
        """
        route_values = {}
        if feed is not None:
            route_values['feed'] = self._serialize.url('feed', feed, 'str')
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        if artifact_id is not None:
            route_values['artifactId'] = self._serialize.url('artifact_id', artifact_id, 'str')
        if version is not None:
            route_values['version'] = self._serialize.url('version', version, 'str')
        query_parameters = {}
        if show_deleted is not None:
            query_parameters['showDeleted'] = self._serialize.query('show_deleted', show_deleted, 'bool')
        response = self._send(http_method='GET',
                              location_id='180ed967-377a-4112-986b-607adb14ded4',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('Package', response)

    def package_delete(self, feed, group_id, artifact_id, version):
        """PackageDelete.
        [Preview API] Fulfills delete package requests.
        :param str feed: Name or ID of the feed.
        :param str group_id: Group ID of the package.
        :param str artifact_id: Artifact ID of the package.
        :param str version: Version of the package.
        """
        route_values = {}
        if feed is not None:
            route_values['feed'] = self._serialize.url('feed', feed, 'str')
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        if artifact_id is not None:
            route_values['artifactId'] = self._serialize.url('artifact_id', artifact_id, 'str')
        if version is not None:
            route_values['version'] = self._serialize.url('version', version, 'str')
        self._send(http_method='DELETE',
                   location_id='180ed967-377a-4112-986b-607adb14ded4',
                   version='4.1-preview.1',
                   route_values=route_values)

