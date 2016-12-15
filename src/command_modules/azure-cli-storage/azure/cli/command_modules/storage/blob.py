# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
from collections import namedtuple
from datetime import datetime
from azure.storage.blob import BlockBlobService
from azure.storage.blob.models import Include
from azure.cli.core._logging import get_az_logger


BlobCopyResult = namedtuple('BlobCopyResult', ['name', 'copy_id'])


# pylint: disable=too-many-arguments
def storage_blob_copy_batch(client, source_account, source_container, destination_container,
                            source_sas=None, prefix=None, recursive=False, snapshots=False,
                            exclude_old=False, exclude_new=False):
    """
    Copy blobs between containers and storage accounts. This is a server-side copy operation
    therefore the command is asynchronous.

    :param str source_account:
        The account name of the source storage account

    :param str source_container:
        The source blob container

    :param str source_sas:
        The shared access signature used to access the source container. It is not required if
        either a connection string is given or the source container doesn't require a sas.

    :param str destination_container:
        The destination blob container

    :param str prefix:
        If option --recursive is specified, then this command interprets the specified the pattern
        given as a blob prefix. If option --recursive is not specified, then the given pattern
        matches the against exact blob names.

    :param bool recursive:
        Copy all the files to the given container and maintain the folder structure.

    :param bool snapshots:
        Copy both the blobs and their snapshots.

    :param bool exclude_old:
        Excludes an older source resource. The resource will not be copied if the last modified time
        of the source is the same or older than destination.

    :param bool exclude_new:
        Excludes a newer source resource. The resource will not be copied if the last modified time
        of the source is the same or newer than destination.

    :return: A BlobCopyTicket instance summarize the operations
    """

    # TODO:
    # 1. Page the result list (using num_result and marker)
    # 2. Support connection string for source
    # 3. stop using 'baseblobservice.exists' function. it doesn't provide performance gain
    #    since it invoked the get_blob_properties any way.

    # Question:
    # 1. Performance of creating a source blob service
    src_client = BlockBlobService(account_name=source_account, sas_token=source_sas)

    def _get_blob_name(source_blob):
        name = source_blob.name
        if source_blob.snapshot is not None:
            # the snapshot time string has seven digital in the microseconds, which make strptime
            # nearly unusable. therefore characters after dot are thrown away
            time_string = source_blob.snapshot[:source_blob.snapshot.rfind('.')]
            snapshot_time = datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%S')

            # insert the date time string before the file extension
            dot = name.rfind('.')
            dot = len(name) if dot == -1 else dot
            name = '{0}({1}){2}'.format(name[0:dot],
                                        snapshot_time.strftime('%Y-%m-%d %H%M%S'),
                                        name[dot:])
        return name

    def _get_blob_url(source_blob):
        # to be removed once this issue is fixed:
        # https://github.com/Azure/azure-storage-python/issues/233
        src_url = src_client.make_blob_url(source_container, source_blob.name, sas_token=source_sas)

        if source_blob.snapshot is not None:
            # this is a blob snapshot
            if '?' in src_url:
                src_url += '&snapshot=' + str(source_blob.snapshot)
            else:
                src_url += '?snapshot=' + str(source_blob.snapshot)

        return src_url

    def _copy_single_blob(source_blob):
        kwargs = {
            "container_name": destination_container,
            "blob_name": _get_blob_name(source_blob),
            "copy_source": _get_blob_url(source_blob)
        }

        if (exclude_new or exclude_old) and client.exists(destination_container, source_blob.name):
            if exclude_old:
                destination_blob = client.get_blob_properties(destination_container,
                                                              source_blob.name)
                kwargs["source_if_modified_since"] = destination_blob.properties.last_modified
            if exclude_new:
                kwargs["destination_if_modified_since"] = source_blob.properties.last_modified

        return client.copy_blob(**kwargs)

    if recursive:
        source_blobs = src_client.list_blobs(
            source_container,
            prefix=prefix,
            include=Include(snapshots=True) if snapshots else None)
    elif src_client.exists(source_container, prefix):
        source_blobs = [src_client.get_blob_properties(source_container, prefix)]
    else:
        source_blobs = []

    return [BlobCopyResult(b.name, _copy_single_blob(b).id) for b in source_blobs]


# pylint: disable=unused-argument
def storage_blob_download_batch(client, source, destination, source_container_name, pattern=None,
                                dryrun=False):
    """
    Download blobs in a container recursively

    :param str source:
        The string represents the source of this download operation. The source can be the
        container URL or the container name. When the source is the container URL, the storage
        account name will parsed from the URL.

    :param str destination:
        The string represents the destination folder of this download operation. The folder must
        exist.

    :param bool dryrun:
        Show the summary of the operations to be taken instead of actually download the file(s)

    :param str pattern:
        The pattern is used for files globbing. The supported patterns are '*', '?', '[seq]',
        and '[!seq]'.
    """
    from .util import collect_blobs
    source_blobs = collect_blobs(client, source_container_name, pattern)

    if dryrun:
        logger = get_az_logger(__name__)
        logger.warning('download action: from %s to %s', source, destination)
        logger.warning('    pattern %s', pattern)
        logger.warning('  container %s', source_container_name)
        logger.warning('      total %d', len(source_blobs))
        logger.warning(' operations')
        for b in source_blobs or []:
            logger.warning('  - %s', b)
        return []
    else:
        return list(_download_blob(client, source_container_name, destination, blob) for blob in
                    source_blobs)


def storage_blob_upload_batch(client, source, destination, pattern=None, source_files=None,
                              destination_container_name=None, blob_type=None,
                              content_settings=None, metadata=None, validate_content=False,
                              maxsize_condition=None, max_connections=2, lease_id=None,
                              if_modified_since=None, if_unmodified_since=None, if_match=None,
                              if_none_match=None, timeout=None, dryrun=False):
    """
    Upload files to storage container as blobs

    :param str source:
        The directory where the files to be uploaded.

    :param str destination:
        The string represents the destination of this upload operation. The source can be the
        container URL or the container name. When the source is the container URL, the storage
        account name will parsed from the URL.

    :param str pattern:
        The pattern is used for files globbing. The supported patterns are '*', '?', '[seq]',
        and '[!seq]'.

    :param bool dryrun:
        Show the summary of the operations to be taken instead of actually upload the file(s)

    :param string if_match:
        An ETag value, or the wildcard character (*). Specify this header to perform the operation
        only if the resource's ETag matches the value specified.

    :param string if_none_match:
        An ETag value, or the wildcard character (*). Specify this header to perform the
        operation only if the resource's ETag does not match the value specified. Specify the
        wildcard character (*) to perform the operation only if the resource does not exist,
        and fail the operation if it does exist.
    """
    def _append_blob(file_path, blob_name):
        if not client.exists(destination_container_name, blob_name):
            client.create_blob(
                container_name=destination_container_name,
                blob_name=blob_name,
                content_settings=content_settings,
                metadata=metadata,
                lease_id=lease_id,
                if_modified_since=if_modified_since,
                if_match=if_match,
                if_none_match=if_none_match,
                timeout=timeout)

        return client.append_blob_from_path(
            container_name=destination_container_name,
            blob_name=blob_name,
            file_path=file_path,
            progress_callback=lambda c, t: None,
            validate_content=validate_content,
            maxsize_condition=maxsize_condition,
            lease_id=lease_id,
            timeout=timeout)

    def _upload_blob(file_path, blob_name):
        return client.create_blob_from_path(
            container_name=destination_container_name,
            blob_name=blob_name,
            file_path=file_path,
            progress_callback=lambda c, t: None,
            content_settings=content_settings,
            metadata=metadata,
            validate_content=validate_content,
            max_connections=max_connections,
            lease_id=lease_id,
            if_modified_since=if_modified_since,
            if_unmodified_since=if_unmodified_since,
            if_match=if_match,
            if_none_match=if_none_match,
            timeout=timeout)

    upload_action = _upload_blob if blob_type == 'block' or blob_type == 'page' else _append_blob

    if dryrun:
        logger = get_az_logger(__name__)
        logger.warning('upload action: from %s to %s', source, destination)
        logger.warning('    pattern %s', pattern)
        logger.warning('  container %s', destination_container_name)
        logger.warning('       type %s', blob_type)
        logger.warning('      total %d', len(source_files))
        logger.warning(' operations')
        for f in source_files or []:
            logger.warning('  - %s => %s', *f)
    else:
        for f in source_files or []:
            print('uploading {}'.format(f[0]))
            upload_action(*f)


def _download_blob(blob_service, container, destination_folder, blob_name):
    # TODO: try catch IO exception

    import os.path
    from .util import mkdir_p

    destination_path = os.path.join(destination_folder, blob_name)
    destination_folder = os.path.dirname(destination_path)
    if not os.path.exists(destination_folder):
        mkdir_p(destination_folder)

    blob = blob_service.get_blob_to_path(container, blob_name, destination_path)
    return blob.name
