# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import os.path
from collections import namedtuple

from knack.util import CLIError
from knack.log import get_logger

from azure.common import AzureException
from azure.cli.command_modules.storage.util import (create_blob_service_from_storage_client,
                                                    create_file_share_from_storage_client,
                                                    create_short_lived_share_sas,
                                                    create_short_lived_container_sas,
                                                    filter_none, collect_blobs, collect_files,
                                                    mkdir_p, guess_content_type)
from azure.cli.command_modules.storage.url_quote_util import encode_for_url, make_encoded_file_url_and_params

BlobCopyResult = namedtuple('BlobCopyResult', ['name', 'copy_id'])


def set_blob_tier(client, container_name, blob_name, tier, blob_type='block', timeout=None):
    if blob_type == 'block':
        return client.set_standard_blob_tier(container_name=container_name, blob_name=blob_name,
                                             standard_blob_tier=tier, timeout=timeout)
    elif blob_type == 'page':
        return client.set_premium_page_blob_tier(container_name=container_name, blob_name=blob_name,
                                                 premium_page_blob_tier=tier, timeout=timeout)
    else:
        raise ValueError('Blob tier is only applicable to block or page blob.')


def storage_blob_copy_batch(cmd, client, source_client,
                            destination_container=None, source_container=None, source_share=None,
                            source_sas=None, pattern=None, dryrun=False):
    """Copy a group of blob or files to a blob container."""
    logger = None
    if dryrun:
        logger = get_logger(__name__)
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
        source_client = source_client or create_blob_service_from_storage_client(cmd, client)

        if not source_sas:
            source_sas = create_short_lived_container_sas(cmd, source_client.account_name, source_client.account_key,
                                                          source_container)

        # pylint: disable=inconsistent-return-statements
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
        source_client = source_client or create_file_share_from_storage_client(cmd, client)

        if not source_sas:
            source_sas = create_short_lived_share_sas(cmd, source_client.account_name, source_client.account_key,
                                                      source_share)

        # pylint: disable=inconsistent-return-statements
        def action_file_copy(file_info):
            dir_name, file_name = file_info
            if dryrun:
                logger.warning('  - copy file %s', os.path.join(dir_name, file_name))
            else:
                return _copy_file_to_blob_container(client, source_client, destination_container,
                                                    source_share, source_sas, dir_name, file_name)

        return list(filter_none(action_file_copy(file) for file in collect_files(cmd,
                                                                                 source_client,
                                                                                 source_share,
                                                                                 pattern)))
    else:
        raise ValueError('Fail to find source. Neither blob container or file share is specified')


# pylint: disable=unused-argument
def storage_blob_download_batch(client, source, destination, source_container_name, pattern=None, dryrun=False):
    source_blobs = list(collect_blobs(client, source_container_name, pattern))

    if dryrun:
        logger = get_logger(__name__)
        logger.warning('download action: from %s to %s', source, destination)
        logger.warning('    pattern %s', pattern)
        logger.warning('  container %s', source_container_name)
        logger.warning('      total %d', len(source_blobs))
        logger.warning(' operations')
        for b in source_blobs:
            logger.warning('  - %s', b)
        return []

    return list(_download_blob(client, source_container_name, destination, blob) for blob in source_blobs)


def storage_blob_upload_batch(cmd, client, source, destination, pattern=None,  # pylint: disable=too-many-locals
                              source_files=None,
                              destination_container_name=None, blob_type=None,
                              content_settings=None, metadata=None, validate_content=False,
                              maxsize_condition=None, max_connections=2, lease_id=None,
                              if_modified_since=None, if_unmodified_since=None, if_match=None,
                              if_none_match=None, timeout=None, dryrun=False):
    def _create_return_result(blob_name, blob_content_settings, upload_result=None):
        return {
            'Blob': client.make_blob_url(destination_container_name, blob_name),
            'Type': blob_content_settings.content_type,
            'Last Modified': upload_result.last_modified if upload_result else None,
            'eTag': upload_result.etag if upload_result else None}

    logger = get_logger(__name__)
    t_content_settings = cmd.get_models('blob.models#ContentSettings')

    results = []
    if dryrun:
        logger.info('upload action: from %s to %s', source, destination)
        logger.info('    pattern %s', pattern)
        logger.info('  container %s', destination_container_name)
        logger.info('       type %s', blob_type)
        logger.info('      total %d', len(source_files))
        results = []
        for src, dst in source_files or []:
            results.append(_create_return_result(dst, guess_content_type(src, content_settings, t_content_settings)))
    else:
        for src, dst in source_files or []:
            logger.warning('uploading %s', src)
            guessed_content_settings = guess_content_type(src, content_settings, t_content_settings)
            result = upload_blob(cmd, client, destination_container_name, dst, src,
                                 blob_type=blob_type, content_settings=guessed_content_settings, metadata=metadata,
                                 validate_content=validate_content, maxsize_condition=maxsize_condition,
                                 max_connections=max_connections, lease_id=lease_id,
                                 if_modified_since=if_modified_since, if_unmodified_since=if_unmodified_since,
                                 if_match=if_match, if_none_match=if_none_match, timeout=timeout)
            results.append(_create_return_result(dst, guessed_content_settings, result))
    return results


def upload_blob(cmd, client, container_name, blob_name, file_path, blob_type=None, content_settings=None, metadata=None,
                validate_content=False, maxsize_condition=None, max_connections=2, lease_id=None, tier=None,
                if_modified_since=None, if_unmodified_since=None, if_match=None, if_none_match=None, timeout=None):
    """Upload a blob to a container."""

    t_content_settings = cmd.get_models('blob.models#ContentSettings')
    content_settings = guess_content_type(file_path, content_settings, t_content_settings)

    def upload_append_blob():
        if not client.exists(container_name, blob_name):
            client.create_blob(
                container_name=container_name,
                blob_name=blob_name,
                content_settings=content_settings,
                metadata=metadata,
                lease_id=lease_id,
                if_modified_since=if_modified_since,
                if_match=if_match,
                if_none_match=if_none_match,
                timeout=timeout)

        append_blob_args = {
            'container_name': container_name,
            'blob_name': blob_name,
            'file_path': file_path,
            'progress_callback': get_update_progress_fn(cmd),
            'maxsize_condition': maxsize_condition,
            'lease_id': lease_id,
            'timeout': timeout
        }

        if cmd.supported_api_version(min_api='2016-05-31'):
            append_blob_args['validate_content'] = validate_content

        return client.append_blob_from_path(**append_blob_args)

    def upload_block_blob():
        # increase the block size to 100MB when the file is larger than 200GB
        if os.path.isfile(file_path) and os.stat(file_path).st_size > 200 * 1024 * 1024 * 1024:
            client.MAX_BLOCK_SIZE = 100 * 1024 * 1024
            client.MAX_SINGLE_PUT_SIZE = 256 * 1024 * 1024

        create_blob_args = {
            'container_name': container_name,
            'blob_name': blob_name,
            'file_path': file_path,
            'progress_callback': get_update_progress_fn(cmd),
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

        if cmd.supported_api_version(min_api='2017-04-17') and tier:
            create_blob_args['premium_page_blob_tier'] = tier

        if cmd.supported_api_version(min_api='2016-05-31'):
            create_blob_args['validate_content'] = validate_content

        return client.create_blob_from_path(**create_blob_args)

    type_func = {
        'append': upload_append_blob,
        'block': upload_block_blob,
        'page': upload_block_blob  # same implementation
    }
    return type_func[blob_type]()


def storage_blob_delete_batch(client, source, source_container_name, pattern=None, lease_id=None,
                              delete_snapshots=None, if_modified_since=None, if_unmodified_since=None, if_match=None,
                              if_none_match=None, timeout=None, dryrun=False):
    def _delete_blob(blob_name):
        delete_blob_args = {
            'container_name': source_container_name,
            'blob_name': blob_name,
            'lease_id': lease_id,
            'delete_snapshots': delete_snapshots,
            'if_modified_since': if_modified_since,
            'if_unmodified_since': if_unmodified_since,
            'if_match': if_match,
            'if_none_match': if_none_match,
            'timeout': timeout
        }
        response = client.delete_blob(**delete_blob_args)
        return response

    source_blobs = list(collect_blobs(client, source_container_name, pattern))

    if dryrun:
        logger = get_logger(__name__)
        logger.warning('delete action: from %s', source)
        logger.warning('    pattern %s', pattern)
        logger.warning('  container %s', source_container_name)
        logger.warning('      total %d', len(source_blobs))
        logger.warning(' operations')
        for blob in source_blobs:
            logger.warning('  - %s', blob)
        return []

    return [_delete_blob(blob) for blob in source_blobs]


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
    source_blob_url = source_blob_service.make_blob_url(source_container, encode_for_url(source_blob_name),
                                                        sas_token=source_sas)

    try:
        blob_service.copy_blob(destination_container, source_blob_name, source_blob_url)
        return blob_service.make_blob_url(destination_container, source_blob_name)
    except AzureException:
        error_template = 'Failed to copy blob {} to container {}.'
        raise CLIError(error_template.format(source_blob_name, destination_container))


def _copy_file_to_blob_container(blob_service, source_file_service, destination_container,
                                 source_share, source_sas, source_file_dir, source_file_name):
    file_url, source_file_dir, source_file_name = \
        make_encoded_file_url_and_params(source_file_service, source_share, source_file_dir,
                                         source_file_name, source_sas)

    blob_name = os.path.join(source_file_dir, source_file_name) \
        if source_file_dir else source_file_name

    try:
        blob_service.copy_blob(destination_container, blob_name=blob_name, copy_source=file_url)
        return blob_service.make_blob_url(destination_container, blob_name)
    except AzureException as ex:
        error_template = 'Failed to copy file {} to container {}. {}'
        raise CLIError(error_template.format(source_file_name, destination_container, ex))


def get_update_progress_fn(cmd):
    def _update_progress(current, total):
        hook = cmd.cli_ctx.get_progress_controller(det=True)

        if total:
            hook.add(message='Alive', value=current, total_val=total)
            if total == current:
                hook.end()

    return _update_progress
