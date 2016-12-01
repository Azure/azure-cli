# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Commands for storage file share operations
"""

#pylint: disable=too-many-arguments

import os.path
from azure.cli.core._logging import get_az_logger


def storage_file_upload_batch(client, destination, source, pattern=None, dryrun=False,
                              validate_content=False, content_settings=None, max_connections=1,
                              metadata=None):
    """
    Upload local files to Azure Storage File Share in batch
    """

    from .files_helpers import glob_files_locally
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
    # 1. Avoid create directory repeatedly
    # 2. Upload files in parallel
    def _upload_action(source_pair):
        dir_name = os.path.dirname(source_pair[1])
        file_name = os.path.basename(source_pair[1])
        if dir_name and len(dir_name) > 0:
            client.create_directory(share_name=destination,
                                    directory_name=dir_name,
                                    fail_on_exist=False)

        client.create_file_from_path(share_name=destination,
                                     directory_name=dir_name,
                                     file_name=file_name,
                                     local_file_path=source_pair[0],
                                     content_settings=content_settings,
                                     metadata=metadata,
                                     max_connections=max_connections,
                                     validate_content=validate_content)

        return client.make_file_url(destination, dir_name, file_name)

    return list(_upload_action(f) for f in source_files)


def storage_file_download_batch(client, source, destination, pattern=None, dryrun=False,
                                validate_content=False, max_connections=1):
    """
    Download files from file share to local directory in batch
    """

    from .files_helpers import glob_files_remotely, mkdir_p

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
        client.get_file_to_path(source,
                                directory_name=pair[0],
                                file_name=pair[1],
                                file_path=os.path.join(destination, *pair),
                                validate_content=validate_content,
                                max_connections=max_connections)
        return client.make_file_url(source, *pair)

    return list(_download_action(f) for f in source_files)
