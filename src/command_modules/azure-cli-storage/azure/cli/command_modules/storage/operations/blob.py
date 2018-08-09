# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import os
from knack.log import get_logger

from azure.cli.command_modules.storage.util import (create_blob_service_from_storage_client,
                                                    create_file_share_from_storage_client,
                                                    create_short_lived_share_sas,
                                                    create_short_lived_container_sas,
                                                    filter_none, collect_blobs, collect_files,
                                                    mkdir_p, guess_content_type, normalize_blob_file_path,
                                                    check_precondition_success)
from azure.cli.command_modules.storage.url_quote_util import encode_for_url, make_encoded_file_url_and_params


def set_blob_tier(client, container_name, blob_name, tier, blob_type='block', timeout=None):
    if blob_type == 'block':
        return client.set_standard_blob_tier(container_name=container_name, blob_name=blob_name,
                                             standard_blob_tier=tier, timeout=timeout)
    elif blob_type == 'page':
        return client.set_premium_page_blob_tier(container_name=container_name, blob_name=blob_name,
                                                 premium_page_blob_tier=tier, timeout=timeout)
    else:
        raise ValueError('Blob tier is only applicable to block or page blob.')


def set_delete_policy(client, enable=None, days_retained=None):
    policy = client.get_blob_service_properties().delete_retention_policy

    if enable is not None:
        policy.enabled = enable == 'true'
    if days_retained is not None:
        policy.days = days_retained

    if policy.enabled and not policy.days:
        from knack.util import CLIError
        raise CLIError("must specify days-retained")

    client.set_blob_service_properties(delete_retention_policy=policy)
    return client.get_blob_service_properties().delete_retention_policy


def storage_blob_copy_batch(cmd, client, source_client, destination_container=None,
                            destination_path=None, source_container=None, source_share=None,
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
                return _copy_blob_to_blob_container(client, source_client, destination_container, destination_path,
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
                return _copy_file_to_blob_container(client, source_client, destination_container, destination_path,
                                                    source_share, source_sas, dir_name, file_name)

        return list(filter_none(action_file_copy(file) for file in collect_files(cmd,
                                                                                 source_client,
                                                                                 source_share,
                                                                                 pattern)))
    else:
        raise ValueError('Fail to find source. Neither blob container or file share is specified')


# pylint: disable=unused-argument
def storage_blob_download_batch(client, source, destination, source_container_name, pattern=None, dryrun=False,
                                progress_callback=None, max_connections=2):

    def _download_blob(blob_service, container, destination_folder, normalized_blob_name, blob_name):
        # TODO: try catch IO exception
        destination_path = os.path.join(destination_folder, normalized_blob_name)
        destination_folder = os.path.dirname(destination_path)
        if not os.path.exists(destination_folder):
            mkdir_p(destination_folder)

        blob = blob_service.get_blob_to_path(container, blob_name, destination_path, max_connections=max_connections,
                                             progress_callback=progress_callback)
        return blob.name

    source_blobs = collect_blobs(client, source_container_name, pattern)
    blobs_to_download = {}
    for blob_name in source_blobs:
        # remove starting path seperator and normalize
        normalized_blob_name = normalize_blob_file_path(None, blob_name)
        if normalized_blob_name in blobs_to_download:
            from knack.util import CLIError
            raise CLIError('Multiple blobs with download path: `{}`. As a solution, use the `--pattern` parameter '
                           'to select for a subset of blobs to download OR utilize the `storage blob download` '
                           'command instead to download individual blobs.'.format(normalized_blob_name))
        blobs_to_download[normalized_blob_name] = blob_name

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

    return list(_download_blob(client, source_container_name, destination, blob_normed, blobs_to_download[blob_normed])
                for blob_normed in blobs_to_download)


def storage_blob_upload_batch(cmd, client, source, destination, pattern=None,  # pylint: disable=too-many-locals
                              source_files=None, destination_path=None,
                              destination_container_name=None, blob_type=None,
                              content_settings=None, metadata=None, validate_content=False,
                              maxsize_condition=None, max_connections=2, lease_id=None, progress_callback=None,
                              if_modified_since=None, if_unmodified_since=None, if_match=None,
                              if_none_match=None, timeout=None, dryrun=False):
    def _create_return_result(blob_name, blob_content_settings, upload_result=None):
        blob_name = normalize_blob_file_path(destination_path, blob_name)
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
        @check_precondition_success
        def _upload_blob(*args, **kwargs):
            return upload_blob(*args, **kwargs)

        for src, dst in source_files or []:
            logger.warning('uploading %s', src)
            guessed_content_settings = guess_content_type(src, content_settings, t_content_settings)

            include, result = _upload_blob(cmd, client, destination_container_name,
                                           normalize_blob_file_path(destination_path, dst), src,
                                           blob_type=blob_type, content_settings=guessed_content_settings,
                                           metadata=metadata, validate_content=validate_content,
                                           maxsize_condition=maxsize_condition, max_connections=max_connections,
                                           lease_id=lease_id, progress_callback=progress_callback,
                                           if_modified_since=if_modified_since,
                                           if_unmodified_since=if_unmodified_since, if_match=if_match,
                                           if_none_match=if_none_match, timeout=timeout)
            if include:
                results.append(_create_return_result(dst, guessed_content_settings, result))

        num_failures = len(source_files) - len(results)
        if num_failures:
            logger.warning('%s of %s files not uploaded due to "Failed Precondition"', num_failures, len(source_files))
    return results


def upload_blob(cmd, client, container_name, blob_name, file_path, blob_type=None, content_settings=None, metadata=None,
                validate_content=False, maxsize_condition=None, max_connections=2, lease_id=None, tier=None,
                if_modified_since=None, if_unmodified_since=None, if_match=None, if_none_match=None, timeout=None,
                progress_callback=None):
    """Upload a blob to a container."""

    t_content_settings = cmd.get_models('blob.models#ContentSettings')
    content_settings = guess_content_type(file_path, content_settings, t_content_settings)

    def upload_append_blob():
        check_blob_args = {
            'container_name': container_name,
            'blob_name': blob_name,
            'lease_id': lease_id,
            'if_modified_since': if_modified_since,
            'if_unmodified_since': if_unmodified_since,
            'if_match': if_match,
            'if_none_match': if_none_match,
            'timeout': timeout
        }

        if client.exists(container_name, blob_name):
            # used to check for the preconditions as append_blob_from_path() cannot
            client.get_blob_properties(**check_blob_args)
        else:
            client.create_blob(content_settings=content_settings, metadata=metadata, **check_blob_args)

        append_blob_args = {
            'container_name': container_name,
            'blob_name': blob_name,
            'file_path': file_path,
            'progress_callback': progress_callback,
            'maxsize_condition': maxsize_condition,
            'lease_id': lease_id,
            'timeout': timeout
        }

        if cmd.supported_api_version(min_api='2016-05-31'):
            append_blob_args['validate_content'] = validate_content

        return client.append_blob_from_path(**append_blob_args)

    def upload_block_blob():
        # increase the block size to 100MB when the block list will contain more than 50,000 blocks
        if os.path.isfile(file_path) and os.stat(file_path).st_size > 50000 * 4 * 1024 * 1024:
            client.MAX_BLOCK_SIZE = 100 * 1024 * 1024
            client.MAX_SINGLE_PUT_SIZE = 256 * 1024 * 1024

        create_blob_args = {
            'container_name': container_name,
            'blob_name': blob_name,
            'file_path': file_path,
            'progress_callback': progress_callback,
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


def show_blob(cmd, client, container_name, blob_name, snapshot=None, lease_id=None,
              if_modified_since=None, if_unmodified_since=None, if_match=None,
              if_none_match=None, timeout=None):
    blob = client.get_blob_properties(
        container_name, blob_name, snapshot=snapshot, lease_id=lease_id,
        if_modified_since=if_modified_since, if_unmodified_since=if_unmodified_since, if_match=if_match,
        if_none_match=if_none_match, timeout=timeout)

    page_ranges = None
    if blob.properties.blob_type == cmd.get_models('blob.models#_BlobTypes').PageBlob:
        page_ranges = client.get_page_ranges(
            container_name, blob_name, snapshot=snapshot, lease_id=lease_id, if_modified_since=if_modified_since,
            if_unmodified_since=if_unmodified_since, if_match=if_match, if_none_match=if_none_match, timeout=timeout)

    blob.properties.page_ranges = page_ranges

    return blob


def storage_blob_delete_batch(client, source, source_container_name, pattern=None, lease_id=None,
                              delete_snapshots=None, if_modified_since=None, if_unmodified_since=None, if_match=None,
                              if_none_match=None, timeout=None, dryrun=False):
    @check_precondition_success
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
        return client.delete_blob(**delete_blob_args)

    logger = get_logger(__name__)
    source_blobs = list(collect_blobs(client, source_container_name, pattern))

    if dryrun:
        logger.warning('delete action: from %s', source)
        logger.warning('    pattern %s', pattern)
        logger.warning('  container %s', source_container_name)
        logger.warning('      total %d', len(source_blobs))
        logger.warning(' operations')
        for blob in source_blobs:
            logger.warning('  - %s', blob)
        return []

    results = [result for include, result in (_delete_blob(blob) for blob in source_blobs) if include]
    num_failures = len(source_blobs) - len(results)
    if num_failures:
        logger.warning('%s of %s blobs not deleted due to "Failed Precondition"', num_failures, len(source_blobs))


def _copy_blob_to_blob_container(blob_service, source_blob_service, destination_container, destination_path,
                                 source_container, source_sas, source_blob_name):
    from azure.common import AzureException
    source_blob_url = source_blob_service.make_blob_url(source_container, encode_for_url(source_blob_name),
                                                        sas_token=source_sas)
    destination_blob_name = normalize_blob_file_path(destination_path, source_blob_name)
    try:
        blob_service.copy_blob(destination_container, destination_blob_name, source_blob_url)
        return blob_service.make_blob_url(destination_container, destination_blob_name)
    except AzureException:
        from knack.util import CLIError
        error_template = 'Failed to copy blob {} to container {}.'
        raise CLIError(error_template.format(source_blob_name, destination_container))


def _copy_file_to_blob_container(blob_service, source_file_service, destination_container, destination_path,
                                 source_share, source_sas, source_file_dir, source_file_name):
    from azure.common import AzureException
    file_url, source_file_dir, source_file_name = \
        make_encoded_file_url_and_params(source_file_service, source_share, source_file_dir,
                                         source_file_name, source_sas)

    source_path = os.path.join(source_file_dir, source_file_name) if source_file_dir else source_file_name
    destination_blob_name = normalize_blob_file_path(destination_path, source_path)

    try:
        blob_service.copy_blob(destination_container, destination_blob_name, file_url)
        return blob_service.make_blob_url(destination_container, destination_blob_name)
    except AzureException as ex:
        from knack.util import CLIError
        error_template = 'Failed to copy file {} to container {}. {}'
        raise CLIError(error_template.format(source_file_name, destination_container, ex))
