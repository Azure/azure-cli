# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
from collections import namedtuple
from datetime import datetime
from azure.storage.blob import BlockBlobService
from azure.storage.blob.models import Include

BlobCopyResult = namedtuple('BlobCopyResult', ['name', 'copy_id'])


#pylint: disable=too-many-arguments
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

