# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Commands for storage file share operations
"""

import os
from knack.log import get_logger

from azure.cli.command_modules.storage.util import (filter_none, collect_blobs, collect_files,
                                                    create_blob_service_from_storage_client,
                                                    create_short_lived_container_sas, create_short_lived_share_sas,
                                                    guess_content_type)
from azure.cli.command_modules.storage.url_quote_util import encode_for_url, make_encoded_file_url_and_params


def create_share_url(client, share_name, unc=None, protocol=None):
    url = client.make_file_url(share_name, None, '', protocol=protocol).rstrip('/')
    if unc:
        url = ':'.join(url.split(':')[1:])
    return url


def create_file_url(client, share_name, directory_name, file_name, protocol=None):
    return client.make_file_url(
        share_name, directory_name, file_name, protocol=protocol, sas_token=client.sas_token)


def list_share_files(cmd, client, share_name, directory_name=None, timeout=None, exclude_dir=False, snapshot=None,
                     num_results=None, marker=None):
    if cmd.supported_api_version(min_api='2017-04-17'):
        generator = client.list_directories_and_files(
            share_name, directory_name, timeout=timeout, num_results=num_results, marker=marker, snapshot=snapshot)
    else:
        generator = client.list_directories_and_files(
            share_name, directory_name, timeout=timeout, num_results=num_results, marker=marker)

    if exclude_dir:
        t_file_properties = cmd.get_models('file.models#FileProperties')

        return list(f for f in generator if isinstance(f.properties, t_file_properties))

    return generator


def storage_file_upload_batch(cmd, client, destination, source, destination_path=None, pattern=None, dryrun=False,
                              validate_content=False, content_settings=None, max_connections=1, metadata=None,
                              progress_callback=None):
    """ Upload local files to Azure Storage File Share in batch """

    from azure.cli.command_modules.storage.util import glob_files_locally, normalize_blob_file_path

    source_files = [c for c in glob_files_locally(source, pattern)]
    logger = get_logger(__name__)
    settings_class = cmd.get_models('file.models#ContentSettings')

    if dryrun:
        logger.info('upload files to file share')
        logger.info('    account %s', client.account_name)
        logger.info('      share %s', destination)
        logger.info('      total %d', len(source_files))
        return [{'File': client.make_file_url(destination, os.path.dirname(dst) or None, os.path.basename(dst)),
                 'Type': guess_content_type(src, content_settings, settings_class).content_type} for src, dst in
                source_files]

    # TODO: Performance improvement
    # 1. Upload files in parallel
    def _upload_action(src, dst):
        dst = normalize_blob_file_path(destination_path, dst)
        dir_name = os.path.dirname(dst)
        file_name = os.path.basename(dst)

        _make_directory_in_files_share(client, destination, dir_name)
        create_file_args = {'share_name': destination, 'directory_name': dir_name, 'file_name': file_name,
                            'local_file_path': src, 'progress_callback': progress_callback,
                            'content_settings': guess_content_type(src, content_settings, settings_class),
                            'metadata': metadata, 'max_connections': max_connections}

        if cmd.supported_api_version(min_api='2016-05-31'):
            create_file_args['validate_content'] = validate_content

        logger.warning('uploading %s', src)
        client.create_file_from_path(**create_file_args)

        return client.make_file_url(destination, dir_name, file_name)

    return list(_upload_action(src, dst) for src, dst in source_files)


def storage_file_download_batch(cmd, client, source, destination, pattern=None, dryrun=False, validate_content=False,
                                max_connections=1, progress_callback=None):
    """
    Download files from file share to local directory in batch
    """

    from azure.cli.command_modules.storage.util import glob_files_remotely, mkdir_p

    source_files = glob_files_remotely(cmd, client, source, pattern)

    if dryrun:
        source_files_list = list(source_files)

        logger = get_logger(__name__)
        logger.warning('download files from file share')
        logger.warning('    account %s', client.account_name)
        logger.warning('      share %s', source)
        logger.warning('destination %s', destination)
        logger.warning('    pattern %s', pattern)
        logger.warning('      total %d', len(source_files_list))
        logger.warning(' operations')
        for f in source_files_list:
            logger.warning('  - %s/%s => %s', f[0], f[1], os.path.join(destination, *f))

        return []

    def _download_action(pair):
        destination_dir = os.path.join(destination, pair[0])
        mkdir_p(destination_dir)

        get_file_args = {'share_name': source, 'directory_name': pair[0], 'file_name': pair[1],
                         'file_path': os.path.join(destination, *pair), 'max_connections': max_connections,
                         'progress_callback': progress_callback}

        if cmd.supported_api_version(min_api='2016-05-31'):
            get_file_args['validate_content'] = validate_content

        client.get_file_to_path(**get_file_args)
        return client.make_file_url(source, *pair)

    return list(_download_action(f) for f in source_files)


def storage_file_copy_batch(cmd, client, source_client, destination_share=None, destination_path=None,
                            source_container=None, source_share=None, source_sas=None, pattern=None, dryrun=False,
                            metadata=None, timeout=None):
    """
    Copy a group of files asynchronously
    """
    logger = None
    if dryrun:
        logger = get_logger(__name__)
        logger.warning('copy files or blobs to file share')
        logger.warning('    account %s', client.account_name)
        logger.warning('      share %s', destination_share)
        logger.warning('       path %s', destination_path)
        logger.warning('     source %s', source_container or source_share)
        logger.warning('source type %s', 'blob' if source_container else 'file')
        logger.warning('    pattern %s', pattern)
        logger.warning(' operations')

    if source_container:
        # copy blobs to file share

        # if the source client is None, recreate one from the destination client.
        source_client = source_client or create_blob_service_from_storage_client(cmd, client)

        # the cache of existing directories in the destination file share. the cache helps to avoid
        # repeatedly create existing directory so as to optimize the performance.
        existing_dirs = set([])

        if not source_sas:
            source_sas = create_short_lived_container_sas(cmd, source_client.account_name, source_client.account_key,
                                                          source_container)

        # pylint: disable=inconsistent-return-statements
        def action_blob_copy(blob_name):
            if dryrun:
                logger.warning('  - copy blob %s', blob_name)
            else:
                return _create_file_and_directory_from_blob(client, source_client, destination_share, source_container,
                                                            source_sas, blob_name, destination_dir=destination_path,
                                                            metadata=metadata, timeout=timeout,
                                                            existing_dirs=existing_dirs)

        return list(
            filter_none(action_blob_copy(blob) for blob in collect_blobs(source_client, source_container, pattern)))

    elif source_share:
        # copy files from share to share

        # if the source client is None, assume the file share is in the same storage account as
        # destination, therefore client is reused.
        source_client = source_client or client

        # the cache of existing directories in the destination file share. the cache helps to avoid
        # repeatedly create existing directory so as to optimize the performance.
        existing_dirs = set([])

        if not source_sas:
            source_sas = create_short_lived_share_sas(cmd, source_client.account_name, source_client.account_key,
                                                      source_share)

        # pylint: disable=inconsistent-return-statements
        def action_file_copy(file_info):
            dir_name, file_name = file_info
            if dryrun:
                logger.warning('  - copy file %s', os.path.join(dir_name, file_name))
            else:
                return _create_file_and_directory_from_file(client, source_client, destination_share, source_share,
                                                            source_sas, dir_name, file_name,
                                                            destination_dir=destination_path, metadata=metadata,
                                                            timeout=timeout, existing_dirs=existing_dirs)

        return list(filter_none(
            action_file_copy(file) for file in collect_files(cmd, source_client, source_share, pattern)))
    else:
        # won't happen, the validator should ensure either source_container or source_share is set
        raise ValueError('Fail to find source. Neither blob container or file share is specified.')


def storage_file_delete_batch(cmd, client, source, pattern=None, dryrun=False, timeout=None):
    """
    Delete files from file share in batch
    """

    def delete_action(file_pair):
        delete_file_args = {'share_name': source, 'directory_name': file_pair[0], 'file_name': file_pair[1],
                            'timeout': timeout}

        return client.delete_file(**delete_file_args)

    from azure.cli.command_modules.storage.util import glob_files_remotely
    source_files = list(glob_files_remotely(cmd, client, source, pattern))

    if dryrun:
        logger = get_logger(__name__)
        logger.warning('delete files from %s', source)
        logger.warning('    pattern %s', pattern)
        logger.warning('      share %s', source)
        logger.warning('      total %d', len(source_files))
        logger.warning(' operations')
        for f in source_files:
            logger.warning('  - %s/%s', f[0], f[1])
        return []

    for f in source_files:
        delete_action(f)


def _create_file_and_directory_from_blob(file_service, blob_service, share, container, sas, blob_name,
                                         destination_dir=None, metadata=None, timeout=None, existing_dirs=None):
    """
    Copy a blob to file share and create the directory if needed.
    """
    from azure.common import AzureException
    from azure.cli.command_modules.storage.util import normalize_blob_file_path

    blob_url = blob_service.make_blob_url(container, encode_for_url(blob_name), sas_token=sas)
    full_path = normalize_blob_file_path(destination_dir, blob_name)
    file_name = os.path.basename(full_path)
    dir_name = os.path.dirname(full_path)
    _make_directory_in_files_share(file_service, share, dir_name, existing_dirs)

    try:
        file_service.copy_file(share, dir_name, file_name, blob_url, metadata, timeout)
        return file_service.make_file_url(share, dir_name, file_name)
    except AzureException:
        error_template = 'Failed to copy blob {} to file share {}. Please check if you have permission to read ' \
                         'source or set a correct sas token.'
        from knack.util import CLIError
        raise CLIError(error_template.format(blob_name, share))


def _create_file_and_directory_from_file(file_service, source_file_service, share, source_share, sas, source_file_dir,
                                         source_file_name, destination_dir=None, metadata=None, timeout=None,
                                         existing_dirs=None):
    """
    Copy a file from one file share to another
    """
    from azure.common import AzureException
    from azure.cli.command_modules.storage.util import normalize_blob_file_path

    file_url, source_file_dir, source_file_name = make_encoded_file_url_and_params(source_file_service, source_share,
                                                                                   source_file_dir, source_file_name,
                                                                                   sas_token=sas)

    full_path = normalize_blob_file_path(destination_dir, os.path.join(source_file_dir, source_file_name))
    file_name = os.path.basename(full_path)
    dir_name = os.path.dirname(full_path)
    _make_directory_in_files_share(file_service, share, dir_name, existing_dirs)

    try:
        file_service.copy_file(share, dir_name, file_name, file_url, metadata, timeout)
        return file_service.make_file_url(share, dir_name or None, file_name)
    except AzureException:
        error_template = 'Failed to copy file {} from share {} to file share {}. Please check if ' \
                         'you have right permission to read source or set a correct sas token.'
        from knack.util import CLIError
        raise CLIError(error_template.format(file_name, source_share, share))


def _make_directory_in_files_share(file_service, file_share, directory_path, existing_dirs=None):
    """
    Create directories recursively.

    This method accept a existing_dirs set which serves as the cache of existing directory. If the
    parameter is given, the method will search the set first to avoid repeatedly create directory
    which already exists.
    """
    from azure.common import AzureHttpError

    if not directory_path:
        return

    parents = [directory_path]
    p = os.path.dirname(directory_path)
    while p:
        parents.append(p)
        p = os.path.dirname(p)

    for dir_name in reversed(parents):
        if existing_dirs and (dir_name in existing_dirs):
            continue

        try:
            file_service.create_directory(share_name=file_share, directory_name=dir_name, fail_on_exist=False)
        except AzureHttpError:
            from knack.util import CLIError
            raise CLIError('Failed to create directory {}'.format(dir_name))

        if existing_dirs:
            existing_dirs.add(directory_path)
