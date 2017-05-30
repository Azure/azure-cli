# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Commands for storage file share operations
"""


import os.path
from azure.cli.core.azlogging import get_az_logger
from azure.cli.core.util import CLIError
from azure.common import AzureException, AzureHttpError
from azure.cli.core.profiles import supported_api_version, ResourceType
from azure.cli.command_modules.storage.util import (filter_none, collect_blobs, collect_files,
                                                    create_blob_service_from_storage_client,
                                                    create_short_lived_container_sas,
                                                    create_short_lived_share_sas)


def storage_file_upload_batch(client, destination, source, pattern=None, dryrun=False,
                              validate_content=False, content_settings=None, max_connections=1,
                              metadata=None):
    """
    Upload local files to Azure Storage File Share in batch
    """

    from .util import glob_files_locally
    source_files = [c for c in glob_files_locally(source, pattern)]

    if dryrun:
        logger = get_az_logger(__name__)
        logger.warning('upload files to file share')
        logger.warning('    account %s', client.account_name)
        logger.warning('      share %s', destination)
        logger.warning('      total %d', len(source_files or []))
        logger.warning(' operations')
        for f in source_files or []:
            logger.warning('  - %s => %s', *f)

        return []

    # TODO: Performance improvement
    # 1. Upload files in parallel
    def _upload_action(source_pair):
        dir_name = os.path.dirname(source_pair[1])
        file_name = os.path.basename(source_pair[1])

        _make_directory_in_files_share(client, destination, dir_name)
        create_file_args = {
            'share_name': destination,
            'directory_name': dir_name,
            'file_name': file_name,
            'local_file_path': source_pair[0],
            'content_settings': content_settings,
            'metadata': metadata,
            'max_connections': max_connections,
        }

        if supported_api_version(ResourceType.DATA_STORAGE, min_api='2016-05-31'):
            create_file_args['validate_content'] = validate_content

        client.create_file_from_path(**create_file_args)

        return client.make_file_url(destination, dir_name, file_name)

    return list(_upload_action(f) for f in source_files)


def storage_file_download_batch(client, source, destination, pattern=None, dryrun=False,
                                validate_content=False, max_connections=1):
    """
    Download files from file share to local directory in batch
    """

    from .util import glob_files_remotely, mkdir_p

    source_files = glob_files_remotely(client, source, pattern)

    if dryrun:
        source_files_list = list(source_files)

        logger = get_az_logger(__name__)
        logger.warning('upload files to file share')
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

        get_file_args = {
            'share_name': source,
            'directory_name': pair[0],
            'file_name': pair[1],
            'file_path': os.path.join(destination, *pair),
            'max_connections': max_connections
        }

        if supported_api_version(ResourceType.DATA_STORAGE, min_api='2016-05-31'):
            get_file_args['validate_content'] = validate_content

        client.get_file_to_path(**get_file_args)
        return client.make_file_url(source, *pair)

    return list(_download_action(f) for f in source_files)


def storage_file_copy_batch(client, source_client,
                            destination_share=None, destination_path=None,
                            source_container=None, source_share=None, source_sas=None,
                            pattern=None, dryrun=False, metadata=None, timeout=None):
    """
    Copy a group of files asynchronously
    """
    logger = None
    if dryrun:
        logger = get_az_logger(__name__)
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
        source_client = source_client or create_blob_service_from_storage_client(client)

        # the cache of existing directories in the destination file share. the cache helps to avoid
        # repeatedly create existing directory so as to optimize the performance.
        existing_dirs = set([])

        if not source_sas and client.account_name != source_client.account_name:
            # when blob is copied across storage account without sas, generate a short lived
            # sas for it
            source_sas = create_short_lived_container_sas(source_client.account_name,
                                                          source_client.account_key,
                                                          source_container)

        def action_blob_copy(blob_name):
            if dryrun:
                logger.warning('  - copy blob %s', blob_name)
            else:
                return _create_file_and_directory_from_blob(
                    client, source_client, destination_share, source_container, source_sas,
                    blob_name, destination_dir=destination_path, metadata=metadata, timeout=timeout,
                    existing_dirs=existing_dirs)

        return list(filter_none(action_blob_copy(blob) for blob in
                                collect_blobs(source_client, source_container, pattern)))

    elif source_share:
        # copy files from share to share

        # if the source client is None, assume the file share is in the same storage account as
        # destination, therefore client is reused.
        source_client = source_client or client

        # the cache of existing directories in the destination file share. the cache helps to avoid
        # repeatedly create existing directory so as to optimize the performance.
        existing_dirs = set([])

        if not source_sas and client.account_name != source_client.account_name:
            # when file is copied across storage account without sas, generate a short lived
            # sas for it
            source_sas = create_short_lived_share_sas(source_client.account_name,
                                                      source_client.account_key,
                                                      source_share)

        def action_file_copy(file_info):
            dir_name, file_name = file_info
            if dryrun:
                logger.warning('  - copy file %s', os.path.join(dir_name, file_name))
            else:
                return _create_file_and_directory_from_file(
                    client, source_client, destination_share, source_share, source_sas, dir_name,
                    file_name, destination_dir=destination_path, metadata=metadata,
                    timeout=timeout, existing_dirs=existing_dirs)

        return list(filter_none(action_file_copy(file) for file in
                                collect_files(source_client, source_share, pattern)))
    else:
        # won't happen, the validator should ensure either source_container or source_share is set
        raise ValueError('Fail to find source. Neither blob container or file share is specified.')


def _create_file_and_directory_from_blob(file_service, blob_service, share, container, sas,
                                         blob_name,
                                         destination_dir=None, metadata=None, timeout=None,
                                         existing_dirs=None):
    """
    Copy a blob to file share and create the directory if needed.
    """
    blob_url = blob_service.make_blob_url(container, blob_name, sas_token=sas)
    full_path = os.path.join(destination_dir, blob_name) if destination_dir else blob_name
    file_name = os.path.basename(full_path)
    dir_name = os.path.dirname(full_path)
    _make_directory_in_files_share(file_service, share, dir_name, existing_dirs)

    try:
        file_service.copy_file(share, dir_name, file_name, blob_url, metadata, timeout)
        return file_service.make_file_url(share, dir_name, file_name)
    except AzureException:
        error_template = 'Failed to copy blob {} to file share {}. Please check if you have ' + \
                         'permission to read source or set a correct sas token.'
        raise CLIError(error_template.format(blob_name, share))


def _create_file_and_directory_from_file(file_service, source_file_service, share, source_share,
                                         sas, source_file_dir, source_file_name,
                                         destination_dir=None, metadata=None, timeout=None,
                                         existing_dirs=None):
    """
    Copy a file from one file share to another
    """
    file_url = source_file_service.make_file_url(source_share, source_file_dir or None,
                                                 source_file_name, sas_token=sas)
    full_path = os.path.join(destination_dir, source_file_dir, source_file_name) \
        if destination_dir else os.path.join(source_file_dir, source_file_name)
    file_name = os.path.basename(full_path)
    dir_name = os.path.dirname(full_path)
    _make_directory_in_files_share(file_service, share, dir_name, existing_dirs)

    try:
        file_service.copy_file(share, dir_name, file_name, file_url, metadata, timeout)
        return file_service.make_file_url(share, dir_name or None, file_name)
    except AzureException:
        error_template = 'Failed to copy file {} from share {} to file share {}. Please check if ' \
                         'you have right permission to read source or set a correct sas token.'
        raise CLIError(error_template.format(file_name, source_share, share))


def _make_directory_in_files_share(file_service, file_share, directory_path, existing_dirs=None):
    """
    Create directories recursively.

    This method accept a existing_dirs set which serves as the cache of existing directory. If the
    parameter is given, the method will search the set first to avoid repeatedly create directory
    which already exists.
    """

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
            file_service.create_directory(share_name=file_share,
                                          directory_name=dir_name,
                                          fail_on_exist=False)
        except AzureHttpError:
            raise CLIError('Failed to create directory {}'.format(dir_name))

        if existing_dirs:
            existing_dirs.add(directory_path)
