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


class NpmClient(VssClient):
    """Npm
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(NpmClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = '4c83cfc1-f33a-477e-a789-29d38ffca52e'

    def get_content_scoped_package(self, feed_id, package_scope, unscoped_package_name, package_version, **kwargs):
        """GetContentScopedPackage.
        [Preview API]
        :param str feed_id:
        :param str package_scope:
        :param str unscoped_package_name:
        :param str package_version:
        :rtype: object
        """
        route_values = {}
        if feed_id is not None:
            route_values['feedId'] = self._serialize.url('feed_id', feed_id, 'str')
        if package_scope is not None:
            route_values['packageScope'] = self._serialize.url('package_scope', package_scope, 'str')
        if unscoped_package_name is not None:
            route_values['unscopedPackageName'] = self._serialize.url('unscoped_package_name', unscoped_package_name, 'str')
        if package_version is not None:
            route_values['packageVersion'] = self._serialize.url('package_version', package_version, 'str')
        response = self._send(http_method='GET',
                              location_id='09a4eafd-123a-495c-979c-0eda7bdb9a14',
                              version='4.1-preview.1',
                              route_values=route_values,
                              accept_media_type='application/octet-stream')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_content_unscoped_package(self, feed_id, package_name, package_version, **kwargs):
        """GetContentUnscopedPackage.
        [Preview API]
        :param str feed_id:
        :param str package_name:
        :param str package_version:
        :rtype: object
        """
        route_values = {}
        if feed_id is not None:
            route_values['feedId'] = self._serialize.url('feed_id', feed_id, 'str')
        if package_name is not None:
            route_values['packageName'] = self._serialize.url('package_name', package_name, 'str')
        if package_version is not None:
            route_values['packageVersion'] = self._serialize.url('package_version', package_version, 'str')
        response = self._send(http_method='GET',
                              location_id='75caa482-cb1e-47cd-9f2c-c048a4b7a43e',
                              version='4.1-preview.1',
                              route_values=route_values,
                              accept_media_type='application/octet-stream')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def update_packages(self, batch_request, feed_id):
        """UpdatePackages.
        [Preview API] Update several packages from a single feed in a single request. The updates to the packages do not happen atomically.
        :param :class:`<NpmPackagesBatchRequest> <npm.v4_1.models.NpmPackagesBatchRequest>` batch_request: Information about the packages to update, the operation to perform, and its associated data.
        :param str feed_id: Feed which contains the packages to update.
        """
        route_values = {}
        if feed_id is not None:
            route_values['feedId'] = self._serialize.url('feed_id', feed_id, 'str')
        content = self._serialize.body(batch_request, 'NpmPackagesBatchRequest')
        self._send(http_method='POST',
                   location_id='06f34005-bbb2-41f4-88f5-23e03a99bb12',
                   version='4.1-preview.1',
                   route_values=route_values,
                   content=content)

    def get_readme_scoped_package(self, feed_id, package_scope, unscoped_package_name, package_version, **kwargs):
        """GetReadmeScopedPackage.
        [Preview API]
        :param str feed_id:
        :param str package_scope:
        :param str unscoped_package_name:
        :param str package_version:
        :rtype: object
        """
        route_values = {}
        if feed_id is not None:
            route_values['feedId'] = self._serialize.url('feed_id', feed_id, 'str')
        if package_scope is not None:
            route_values['packageScope'] = self._serialize.url('package_scope', package_scope, 'str')
        if unscoped_package_name is not None:
            route_values['unscopedPackageName'] = self._serialize.url('unscoped_package_name', unscoped_package_name, 'str')
        if package_version is not None:
            route_values['packageVersion'] = self._serialize.url('package_version', package_version, 'str')
        response = self._send(http_method='GET',
                              location_id='6d4db777-7e4a-43b2-afad-779a1d197301',
                              version='4.1-preview.1',
                              route_values=route_values,
                              accept_media_type='text/plain')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_readme_unscoped_package(self, feed_id, package_name, package_version, **kwargs):
        """GetReadmeUnscopedPackage.
        [Preview API]
        :param str feed_id:
        :param str package_name:
        :param str package_version:
        :rtype: object
        """
        route_values = {}
        if feed_id is not None:
            route_values['feedId'] = self._serialize.url('feed_id', feed_id, 'str')
        if package_name is not None:
            route_values['packageName'] = self._serialize.url('package_name', package_name, 'str')
        if package_version is not None:
            route_values['packageVersion'] = self._serialize.url('package_version', package_version, 'str')
        response = self._send(http_method='GET',
                              location_id='1099a396-b310-41d4-a4b6-33d134ce3fcf',
                              version='4.1-preview.1',
                              route_values=route_values,
                              accept_media_type='text/plain')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def delete_scoped_package_version_from_recycle_bin(self, feed_id, package_scope, unscoped_package_name, package_version):
        """DeleteScopedPackageVersionFromRecycleBin.
        [Preview API]
        :param str feed_id:
        :param str package_scope:
        :param str unscoped_package_name:
        :param str package_version:
        """
        route_values = {}
        if feed_id is not None:
            route_values['feedId'] = self._serialize.url('feed_id', feed_id, 'str')
        if package_scope is not None:
            route_values['packageScope'] = self._serialize.url('package_scope', package_scope, 'str')
        if unscoped_package_name is not None:
            route_values['unscopedPackageName'] = self._serialize.url('unscoped_package_name', unscoped_package_name, 'str')
        if package_version is not None:
            route_values['packageVersion'] = self._serialize.url('package_version', package_version, 'str')
        self._send(http_method='DELETE',
                   location_id='220f45eb-94a5-432c-902a-5b8c6372e415',
                   version='4.1-preview.1',
                   route_values=route_values)

    def get_scoped_package_version_metadata_from_recycle_bin(self, feed_id, package_scope, unscoped_package_name, package_version):
        """GetScopedPackageVersionMetadataFromRecycleBin.
        [Preview API]
        :param str feed_id:
        :param str package_scope:
        :param str unscoped_package_name:
        :param str package_version:
        :rtype: :class:`<NpmPackageVersionDeletionState> <npm.v4_1.models.NpmPackageVersionDeletionState>`
        """
        route_values = {}
        if feed_id is not None:
            route_values['feedId'] = self._serialize.url('feed_id', feed_id, 'str')
        if package_scope is not None:
            route_values['packageScope'] = self._serialize.url('package_scope', package_scope, 'str')
        if unscoped_package_name is not None:
            route_values['unscopedPackageName'] = self._serialize.url('unscoped_package_name', unscoped_package_name, 'str')
        if package_version is not None:
            route_values['packageVersion'] = self._serialize.url('package_version', package_version, 'str')
        response = self._send(http_method='GET',
                              location_id='220f45eb-94a5-432c-902a-5b8c6372e415',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('NpmPackageVersionDeletionState', response)

    def restore_scoped_package_version_from_recycle_bin(self, package_version_details, feed_id, package_scope, unscoped_package_name, package_version):
        """RestoreScopedPackageVersionFromRecycleBin.
        [Preview API]
        :param :class:`<NpmRecycleBinPackageVersionDetails> <npm.v4_1.models.NpmRecycleBinPackageVersionDetails>` package_version_details:
        :param str feed_id:
        :param str package_scope:
        :param str unscoped_package_name:
        :param str package_version:
        """
        route_values = {}
        if feed_id is not None:
            route_values['feedId'] = self._serialize.url('feed_id', feed_id, 'str')
        if package_scope is not None:
            route_values['packageScope'] = self._serialize.url('package_scope', package_scope, 'str')
        if unscoped_package_name is not None:
            route_values['unscopedPackageName'] = self._serialize.url('unscoped_package_name', unscoped_package_name, 'str')
        if package_version is not None:
            route_values['packageVersion'] = self._serialize.url('package_version', package_version, 'str')
        content = self._serialize.body(package_version_details, 'NpmRecycleBinPackageVersionDetails')
        self._send(http_method='PATCH',
                   location_id='220f45eb-94a5-432c-902a-5b8c6372e415',
                   version='4.1-preview.1',
                   route_values=route_values,
                   content=content)

    def delete_package_version_from_recycle_bin(self, feed_id, package_name, package_version):
        """DeletePackageVersionFromRecycleBin.
        [Preview API]
        :param str feed_id:
        :param str package_name:
        :param str package_version:
        """
        route_values = {}
        if feed_id is not None:
            route_values['feedId'] = self._serialize.url('feed_id', feed_id, 'str')
        if package_name is not None:
            route_values['packageName'] = self._serialize.url('package_name', package_name, 'str')
        if package_version is not None:
            route_values['packageVersion'] = self._serialize.url('package_version', package_version, 'str')
        self._send(http_method='DELETE',
                   location_id='63a4f31f-e92b-4ee4-bf92-22d485e73bef',
                   version='4.1-preview.1',
                   route_values=route_values)

    def get_package_version_metadata_from_recycle_bin(self, feed_id, package_name, package_version):
        """GetPackageVersionMetadataFromRecycleBin.
        [Preview API]
        :param str feed_id:
        :param str package_name:
        :param str package_version:
        :rtype: :class:`<NpmPackageVersionDeletionState> <npm.v4_1.models.NpmPackageVersionDeletionState>`
        """
        route_values = {}
        if feed_id is not None:
            route_values['feedId'] = self._serialize.url('feed_id', feed_id, 'str')
        if package_name is not None:
            route_values['packageName'] = self._serialize.url('package_name', package_name, 'str')
        if package_version is not None:
            route_values['packageVersion'] = self._serialize.url('package_version', package_version, 'str')
        response = self._send(http_method='GET',
                              location_id='63a4f31f-e92b-4ee4-bf92-22d485e73bef',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('NpmPackageVersionDeletionState', response)

    def restore_package_version_from_recycle_bin(self, package_version_details, feed_id, package_name, package_version):
        """RestorePackageVersionFromRecycleBin.
        [Preview API]
        :param :class:`<NpmRecycleBinPackageVersionDetails> <npm.v4_1.models.NpmRecycleBinPackageVersionDetails>` package_version_details:
        :param str feed_id:
        :param str package_name:
        :param str package_version:
        """
        route_values = {}
        if feed_id is not None:
            route_values['feedId'] = self._serialize.url('feed_id', feed_id, 'str')
        if package_name is not None:
            route_values['packageName'] = self._serialize.url('package_name', package_name, 'str')
        if package_version is not None:
            route_values['packageVersion'] = self._serialize.url('package_version', package_version, 'str')
        content = self._serialize.body(package_version_details, 'NpmRecycleBinPackageVersionDetails')
        self._send(http_method='PATCH',
                   location_id='63a4f31f-e92b-4ee4-bf92-22d485e73bef',
                   version='4.1-preview.1',
                   route_values=route_values,
                   content=content)

    def get_scoped_package_info(self, feed_id, package_scope, unscoped_package_name, package_version):
        """GetScopedPackageInfo.
        [Preview API]
        :param str feed_id:
        :param str package_scope:
        :param str unscoped_package_name:
        :param str package_version:
        :rtype: :class:`<Package> <npm.v4_1.models.Package>`
        """
        route_values = {}
        if feed_id is not None:
            route_values['feedId'] = self._serialize.url('feed_id', feed_id, 'str')
        if package_scope is not None:
            route_values['packageScope'] = self._serialize.url('package_scope', package_scope, 'str')
        if unscoped_package_name is not None:
            route_values['unscopedPackageName'] = self._serialize.url('unscoped_package_name', unscoped_package_name, 'str')
        if package_version is not None:
            route_values['packageVersion'] = self._serialize.url('package_version', package_version, 'str')
        response = self._send(http_method='GET',
                              location_id='e93d9ec3-4022-401e-96b0-83ea5d911e09',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('Package', response)

    def unpublish_scoped_package(self, feed_id, package_scope, unscoped_package_name, package_version):
        """UnpublishScopedPackage.
        [Preview API]
        :param str feed_id:
        :param str package_scope:
        :param str unscoped_package_name:
        :param str package_version:
        :rtype: :class:`<Package> <npm.v4_1.models.Package>`
        """
        route_values = {}
        if feed_id is not None:
            route_values['feedId'] = self._serialize.url('feed_id', feed_id, 'str')
        if package_scope is not None:
            route_values['packageScope'] = self._serialize.url('package_scope', package_scope, 'str')
        if unscoped_package_name is not None:
            route_values['unscopedPackageName'] = self._serialize.url('unscoped_package_name', unscoped_package_name, 'str')
        if package_version is not None:
            route_values['packageVersion'] = self._serialize.url('package_version', package_version, 'str')
        response = self._send(http_method='DELETE',
                              location_id='e93d9ec3-4022-401e-96b0-83ea5d911e09',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('Package', response)

    def update_scoped_package(self, package_version_details, feed_id, package_scope, unscoped_package_name, package_version):
        """UpdateScopedPackage.
        [Preview API]
        :param :class:`<PackageVersionDetails> <npm.v4_1.models.PackageVersionDetails>` package_version_details:
        :param str feed_id:
        :param str package_scope:
        :param str unscoped_package_name:
        :param str package_version:
        :rtype: :class:`<Package> <npm.v4_1.models.Package>`
        """
        route_values = {}
        if feed_id is not None:
            route_values['feedId'] = self._serialize.url('feed_id', feed_id, 'str')
        if package_scope is not None:
            route_values['packageScope'] = self._serialize.url('package_scope', package_scope, 'str')
        if unscoped_package_name is not None:
            route_values['unscopedPackageName'] = self._serialize.url('unscoped_package_name', unscoped_package_name, 'str')
        if package_version is not None:
            route_values['packageVersion'] = self._serialize.url('package_version', package_version, 'str')
        content = self._serialize.body(package_version_details, 'PackageVersionDetails')
        response = self._send(http_method='PATCH',
                              location_id='e93d9ec3-4022-401e-96b0-83ea5d911e09',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Package', response)

    def get_package_info(self, feed_id, package_name, package_version):
        """GetPackageInfo.
        [Preview API]
        :param str feed_id:
        :param str package_name:
        :param str package_version:
        :rtype: :class:`<Package> <npm.v4_1.models.Package>`
        """
        route_values = {}
        if feed_id is not None:
            route_values['feedId'] = self._serialize.url('feed_id', feed_id, 'str')
        if package_name is not None:
            route_values['packageName'] = self._serialize.url('package_name', package_name, 'str')
        if package_version is not None:
            route_values['packageVersion'] = self._serialize.url('package_version', package_version, 'str')
        response = self._send(http_method='GET',
                              location_id='ed579d62-67c9-4271-be66-9b029af5bcf9',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('Package', response)

    def unpublish_package(self, feed_id, package_name, package_version):
        """UnpublishPackage.
        [Preview API]
        :param str feed_id:
        :param str package_name:
        :param str package_version:
        :rtype: :class:`<Package> <npm.v4_1.models.Package>`
        """
        route_values = {}
        if feed_id is not None:
            route_values['feedId'] = self._serialize.url('feed_id', feed_id, 'str')
        if package_name is not None:
            route_values['packageName'] = self._serialize.url('package_name', package_name, 'str')
        if package_version is not None:
            route_values['packageVersion'] = self._serialize.url('package_version', package_version, 'str')
        response = self._send(http_method='DELETE',
                              location_id='ed579d62-67c9-4271-be66-9b029af5bcf9',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('Package', response)

    def update_package(self, package_version_details, feed_id, package_name, package_version):
        """UpdatePackage.
        [Preview API]
        :param :class:`<PackageVersionDetails> <npm.v4_1.models.PackageVersionDetails>` package_version_details:
        :param str feed_id:
        :param str package_name:
        :param str package_version:
        :rtype: :class:`<Package> <npm.v4_1.models.Package>`
        """
        route_values = {}
        if feed_id is not None:
            route_values['feedId'] = self._serialize.url('feed_id', feed_id, 'str')
        if package_name is not None:
            route_values['packageName'] = self._serialize.url('package_name', package_name, 'str')
        if package_version is not None:
            route_values['packageVersion'] = self._serialize.url('package_version', package_version, 'str')
        content = self._serialize.body(package_version_details, 'PackageVersionDetails')
        response = self._send(http_method='PATCH',
                              location_id='ed579d62-67c9-4271-be66-9b029af5bcf9',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Package', response)

