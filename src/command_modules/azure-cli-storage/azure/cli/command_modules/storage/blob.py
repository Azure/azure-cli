# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import os.path
from collections import namedtuple
from azure.common import AzureException

from azure.cli.core.util import CLIError
from azure.cli.core.azlogging import get_az_logger
from azure.cli.core.profiles import supported_api_version, ResourceType
from azure.cli.command_modules.storage.util import (create_blob_service_from_storage_client,
                                                    create_file_share_from_storage_client,
                                                    create_short_lived_share_sas,
                                                    create_short_lived_container_sas,
                                                    filter_none, collect_blobs, collect_files,
                                                    mkdir_p)

BlobCopyResult = namedtuple('BlobCopyResult', ['name', 'copy_id'])


def storage_blob_copy_batch(client, source_client,
                            destination_container=None, source_container=None, source_share=None,
                            source_sas=None, pattern=None, dryrun=False):
    """Copy a group of blob or files to a blob container."""
    logger = None
    if dryrun:
        logger = get_az_logger(__name__)
        logger.warning('copy files or blobs to blob container')
        logger.warning('    account %s', client.account_name)
        logger.warning('  container %s', destination_container)
        logger.warning('     source %s', source_container or source_share)
        logger.warning('source type %s', 'blob' if source_container else 'file')
        logger.warning('    pattern %s', pattern)
        logger.warning(' operations')

    if source_container:
        # copy blobs for blob container

        # if the source client is None, recreate one from the destination client.
        source_client = source_client or create_blob_service_from_storage_client(client)

        if not source_sas and client.account_name != source_client.account_name:
            # when the blob is copied across storage account without sas, generate a short lived
            # sas for it
            source_sas = create_short_lived_container_sas(source_client.account_name,
                                                          source_client.account_key,
                                                          source_container)

        def action_blob_copy(blob_name):
            if dryrun:
                logger.warning('  - copy blob %s', blob_name)
            else:
                return _copy_blob_to_blob_container(client, source_client, destination_container,
                                                    source_container, source_sas, blob_name)

        return list(filter_none(action_blob_copy(blob) for blob in collect_blobs(source_client,
                                                                                 source_container,
                                                                                 pattern)))

    elif source_share:
        # copy blob from file share

        # if the source client is None, recreate one from the destination client.
        source_client = source_client or create_file_share_from_storage_client(client)

        if not source_sas and client.account_name != source_client.account_name:
            # when the file is copied across storage account without sas, generate a short lived sas
            source_sas = create_short_lived_share_sas(source_client.account_name,
                                                      source_client.account_key,
                                                      source_share)

        def action_file_copy(file_info):
            dir_name, file_name = file_info
            if dryrun:
                logger.warning('  - copy file %s', os.path.join(dir_name, file_name))
            else:
                return _copy_file_to_blob_container(client, source_client, destination_container,
                                                    source_share, source_sas, dir_name, file_name)

        return list(filter_none(action_file_copy(file) for file in collect_files(source_client,
                                                                                 source_share,
                                                                                 pattern)))
    else:
        raise ValueError('Fail to find source. Neither blob container or file share is specified')


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
    source_blobs = list(collect_blobs(client, source_container_name, pattern))

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

    return list(_download_blob(client, source_container_name, destination, blob) for blob in source_blobs)


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

        append_blob_args = {
            'container_name': destination_container_name,
            'blob_name': blob_name,
            'file_path': file_path,
            'progress_callback': lambda c, t: None,
            'maxsize_condition': maxsize_condition,
            'lease_id': lease_id,
            'timeout': timeout
        }

        if supported_api_version(ResourceType.DATA_STORAGE, min_api='2016-05-31'):
            append_blob_args['validate_content'] = validate_content

        return client.append_blob_from_path(**append_blob_args)

    def _upload_blob(file_path, blob_name):

        create_blob_args = {
            'container_name': destination_container_name,
            'blob_name': blob_name,
            'file_path': file_path,
            'progress_callback': lambda c, t: None,
            'content_settings': content_settings,
            'metadata': metadata,
            'max_connections': max_connections,
            'lease_id': lease_id,
            'if_modified_since': if_modified_since,
            'if_unmodified_since': if_unmodified_since,
            'if_match': if_match,
            'if_none_match': if_none_match,
            'timeout': timeout
        }

        if supported_api_version(ResourceType.DATA_STORAGE, min_api='2016-05-31'):
            create_blob_args['validate_content'] = validate_content

        return client.create_blob_from_path(**create_blob_args)

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
    destination_path = os.path.join(destination_folder, blob_name)
    destination_folder = os.path.dirname(destination_path)
    if not os.path.exists(destination_folder):
        mkdir_p(destination_folder)

    blob = blob_service.get_blob_to_path(container, blob_name, destination_path)
    return blob.name


def _copy_blob_to_blob_container(blob_service, source_blob_service, destination_container,
                                 source_container, source_sas, source_blob_name):
    source_blob_url = source_blob_service.make_blob_url(source_container, source_blob_name,
                                                        sas_token=source_sas)

    try:
        blob_service.copy_blob(destination_container, source_blob_name, source_blob_url)
        return blob_service.make_blob_url(destination_container, source_blob_name)
    except AzureException:
        error_template = 'Failed to copy blob {} to container {}.'
        raise CLIError(error_template.format(source_blob_name, destination_container))


def _copy_file_to_blob_container(blob_service, source_file_service, destination_container,
                                 source_share, source_sas, source_file_dir, source_file_name):
    source_file_dir = source_file_dir if source_file_dir else None
    file_url = source_file_service.make_file_url(source_share, source_file_dir, source_file_name,
                                                 sas_token=source_sas)

    blob_name = os.path.join(source_file_dir, source_file_name) \
        if source_file_dir else source_file_name

    try:
        blob_service.copy_blob(destination_container, blob_name=blob_name, copy_source=file_url)
        return blob_service.make_blob_url(destination_container, blob_name)
    except AzureException as ex:
        error_template = 'Failed to copy file {} to container {}. {}'
        raise CLIError(error_template.format(source_file_name, destination_container, ex))
