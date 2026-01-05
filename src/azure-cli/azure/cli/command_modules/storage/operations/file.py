# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

"""
Commands for storage file share operations
"""

import os
from knack.log import get_logger

from azure.cli.command_modules.storage.util import (filter_none, collect_blobs, collect_files_track2,
                                                    guess_content_type)
from azure.cli.core.profiles import ResourceType, get_sdk
from azure.cli.core.aaz import has_value
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError, ResourceExistsError
from .fileshare import _get_client
from ..aaz.latest.storage.share_rm import Create as _ShareRmCreate
from ..aaz.latest.storage.share_rm import Update as _ShareRmUpdate
from ..aaz.latest.storage.share_rm import Delete as _ShareRmDelete
from ..aaz.latest.storage.share_rm import Show as _ShareRmShow
from ..aaz.latest.storage.share_rm import List as _ShareRmList
from ..util import get_datetime_from_string

logger = get_logger(__name__)


def snapshot_share_rm(cmd, client, resource_group_name, account_name, share_name, metadata=None, share_quota=None,
                      enabled_protocols=None, root_squash=None, access_tier=None):
    return _create_share_rm(cmd, client, resource_group_name, account_name, share_name, metadata=metadata,
                            share_quota=share_quota, enabled_protocols=enabled_protocols, root_squash=root_squash,
                            access_tier=access_tier, snapshot=True)


def _create_share_rm(cmd, client, resource_group_name, account_name, share_name, metadata=None, share_quota=None,
                     enabled_protocols=None, root_squash=None, access_tier=None, snapshot=None):
    FileShare = cmd.get_models('FileShare', resource_type=ResourceType.MGMT_STORAGE)

    file_share = FileShare()
    expand = None
    if share_quota is not None:
        file_share.share_quota = share_quota
    if enabled_protocols is not None:
        file_share.enabled_protocols = enabled_protocols
    if root_squash is not None:
        file_share.root_squash = root_squash
    if metadata is not None:
        file_share.metadata = metadata
    if access_tier is not None:
        file_share.access_tier = access_tier
    if snapshot:
        expand = 'snapshots'

    return client.create(resource_group_name=resource_group_name, account_name=account_name, share_name=share_name,
                         file_share=file_share, expand=expand)


def get_stats(client, resource_group_name, account_name, share_name):
    return client.get(resource_group_name=resource_group_name, account_name=account_name, share_name=share_name,
                      expand='stats')


def restore_share_rm(cmd, client, resource_group_name, account_name, share_name, deleted_version, restored_name=None):
    restored_name = restored_name if restored_name else share_name

    deleted_share = cmd.get_models('DeletedShare',
                                   resource_type=ResourceType.MGMT_STORAGE)(deleted_share_name=share_name,
                                                                            deleted_share_version=deleted_version)

    return client.restore(resource_group_name=resource_group_name, account_name=account_name,
                          share_name=restored_name, deleted_share=deleted_share)


def create_share_url(client, share_name, unc=None, protocol=None):
    url = client.make_file_url(share_name, None, '', protocol=protocol).rstrip('/')
    if unc:
        url = ':'.join(url.split(':')[1:])
    return url


def create_file_url(client, protocol=None, **kwargs):
    client = _get_client(client, kwargs)
    url = client.url
    if url.endswith(client.share_name):
        url = url + '/'
    if protocol == 'http':
        return url.replace('https', 'http', 1)
    return url


def list_share_files(cmd, client, directory_name=None, timeout=None, exclude_dir=False, exclude_extended_info=False,
                     num_results=None, marker=None):
    from ..track2_util import list_generator
    # since get_share_properties requires share level read access, skip it, assume SMB share first
    results = None
    try:
        include = [] if exclude_extended_info else ["timestamps", "Etag", "Attributes", "PermissionKey"]
        generator = client.list_directories_and_files(directory_name=directory_name, include=include,
                                                      timeout=timeout, results_per_page=num_results)
        pages = generator.by_page(continuation_token=marker)
        results = list_generator(pages=pages, num_results=num_results)
    except HttpResponseError as ex:
        if ex.error_code == "UnsupportedQueryParameter":
            # try NFS share if include fails:
            if exclude_extended_info:
                logger.warning('--exclude-extended-info is not supported for NFS shares.')
            include = None
            generator = client.list_directories_and_files(directory_name=directory_name, include=include,
                                                          timeout=timeout, results_per_page=num_results)
            pages = generator.by_page(continuation_token=marker)
            results = list_generator(pages=pages, num_results=num_results)
        else:
            raise ex

    if pages.continuation_token:
        logger.warning('Next Marker:')
        logger.warning(pages.continuation_token)

    if exclude_dir:
        t_file_properties = cmd.get_models('_models#FileProperties', resource_type=ResourceType.DATA_STORAGE_FILESHARE)
        return [f for f in results if isinstance(f, t_file_properties)]
    return results


def storage_file_upload(client, local_file_path, content_settings=None,
                        metadata=None, validate_content=False, progress_callback=None, max_connections=2, timeout=None,
                        file_mode=None, owner=None, group=None):
    upload_args = {
        'content_settings': content_settings,
        'metadata': metadata,
        'validate_content': validate_content,
        'max_concurrency': max_connections,
        'timeout': timeout
    }
    if progress_callback:
        upload_args['progress_hook'] = progress_callback
    # Because the contents of the uploaded file may be too large, it should be passed into a stream object,
    # upload_file() read file data in batches to avoid OOM problems
    count = os.path.getsize(local_file_path)
    with open(local_file_path, 'rb') as stream:
        response = client.upload_file(data=stream, length=count, **upload_args)

    if 'content_md5' in response:
        if isinstance(response['content_md5'], bytearray):
            response['content_md5'] = ''.join(hex(x) for x in response['content_md5'])

    if not (file_mode is None and owner is None and group is None):
        nfs_args = {
            'file_mode': file_mode,
            'owner': owner,
            'group': group
        }
        client.set_http_headers(content_settings, **nfs_args)

    return response


def _execute_in_parallel(max_workers, fn, args_list):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    if len(args_list) == 0:
        return []
    max_workers = min(max_workers, len(args_list))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fn, *args) for args in args_list]
        return list(f.result() for f in as_completed(futures))


def storage_file_upload_batch(cmd, client, destination, source, destination_path=None, pattern=None, dryrun=False,
                              validate_content=False, content_settings=None, max_connections=1, metadata=None,
                              progress_callback=None):
    """ Upload local files to Azure Storage File Share in batch """

    from azure.cli.command_modules.storage.util import glob_files_locally, normalize_blob_file_path

    source_files = list(glob_files_locally(source, pattern))
    settings_class = cmd.get_models('_models#ContentSettings', resource_type=ResourceType.DATA_STORAGE_FILESHARE)

    if dryrun:
        logger.info('upload files to file share')
        logger.info('    account %s', client.account_name)
        logger.info('      share %s', destination)
        logger.info('      total %d', len(source_files))
        res = []
        for src, dst in source_files:
            formatted_dst = normalize_blob_file_path(destination_path, dst)
            kwargs = {
                'directory_name': os.path.dirname(formatted_dst),
                'file_name': os.path.basename(formatted_dst)
            }
            file = create_file_url(client, **kwargs)
            guessed_type = guess_content_type(src, content_settings, settings_class).content_type
            res.append({'File': file, 'Type': guessed_type})
        return res

    def _upload_action(src, dst2):
        dst2 = normalize_blob_file_path(destination_path, dst2)
        dir_name = os.path.dirname(dst2)
        file_name = os.path.basename(dst2)

        _make_directory_in_files_share(client, dir_name)

        logger.warning('uploading %s', src)
        storage_file_upload(client.get_file_client(dst2), src, content_settings, metadata, validate_content,
                            progress_callback, max_connections)

        args = {
            'directory_name': dir_name,
            'file_name': file_name
        }
        return create_file_url(client, **args)

    # 1. Upload files in parallel
    # 2. Return the list of uploaded files
    return _execute_in_parallel(max_connections, _upload_action, source_files)


def download_file(client, destination_path=None, timeout=None, max_connections=2, open_mode='wb', **kwargs):
    from azure.cli.command_modules.storage.util import mkdir_p
    destination_folder = os.path.dirname(destination_path) if destination_path else ""
    if destination_folder and not os.path.exists(destination_folder):
        mkdir_p(destination_folder)

    if not destination_folder or os.path.isdir(destination_path):
        file = client.get_file_properties(timeout=timeout)
        file_name = file.name.split("/")[-1]
        destination_path = os.path.join(destination_path, file_name) \
            if destination_path else file_name

    kwargs['progress_hook'] = kwargs.pop("progress_callback", None)

    with open(destination_path, open_mode) as stream:
        start_range = kwargs.pop('start_range', None)
        end_range = kwargs.pop('end_range', None)
        length = None
        if start_range is not None and end_range is not None:
            length = end_range - start_range + 1
        download = client.download_file(offset=start_range, length=length, timeout=timeout,
                                        max_concurrency=max_connections, **kwargs)
        download.readinto(stream)
    return client.get_file_properties()


def storage_file_download_batch(client, source, destination, pattern=None, dryrun=False, validate_content=False,
                                max_connections=1, progress_callback=None):
    """
    Download files from file share to local directory in batch
    """

    from azure.cli.command_modules.storage.util import glob_files_remotely_track2, normalize_blob_file_path

    source_files = glob_files_remotely_track2(client, source, pattern, is_share_client=True)

    if dryrun:
        source_files_list = list(source_files)

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
        path = os.path.join(*pair)
        local_path = os.path.join(destination, *pair)
        path = normalize_blob_file_path(None, path)
        file_client = client.get_file_client(path)

        download_file(file_client, destination_path=local_path, max_connections=max_connections,
                      progress_callback=progress_callback, validate_content=validate_content)

        return file_client.url

    return list(_download_action(f) for f in source_files)


def storage_file_copy(client, copy_source, **kwargs):
    result = client.start_copy_from_url(source_url=copy_source, **kwargs)
    result['id'] = result['copy_id']
    result['status'] = result['copy_status']
    del result['copy_id']
    del result['copy_status']
    return result


def storage_file_copy_batch(cmd, client, source_client, share_name=None, destination_path=None,
                            source_container=None, source_share=None, source_sas=None, pattern=None, dryrun=False,
                            metadata=None, timeout=None, **kwargs):
    """
    Copy a group of files asynchronously
    """
    if dryrun:
        logger.warning('copy files or blobs to file share')
        logger.warning('    account %s', client.account_name)
        logger.warning('      share %s', share_name)
        logger.warning('       path %s', destination_path)
        logger.warning('    source account %s', kwargs.get('source_account_name', ""))
        logger.warning('     source %s', source_container or source_share)
        logger.warning('source type %s', 'blob' if source_container else 'file')
        logger.warning('    pattern %s', pattern)
        logger.warning(' operations')

    if source_container:
        # copy blobs to file share

        # the cache of existing directories in the destination file share. the cache helps to avoid
        # repeatedly create existing directory so as to optimize the performance.
        existing_dirs = set()

        if source_client is None:
            t_blob_service_client = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_BLOB,
                                            '_blob_service_client#BlobServiceClient')
            account_url = '/'.join(client.url.replace('file', 'blob').split('/')[:-1])
            if client.credential and client.credential.account_key:
                credential = {
                    "account_name": client.credential.account_name,
                    "account_key": client.credential.account_key
                }
                source_client = t_blob_service_client(account_url=account_url, credential=credential)
            else:
                source_client = t_blob_service_client(account_url=account_url, credential=client.credential)

        # pylint: disable=inconsistent-return-statements
        def action_blob_copy(blob_name):
            if dryrun:
                logger.warning('  - copy blob %s', blob_name)
            else:
                return _create_file_and_directory_from_blob(cmd, client, source_client, share_name, source_container,
                                                            source_sas, blob_name, destination_dir=destination_path,
                                                            metadata=metadata, timeout=timeout,
                                                            existing_dirs=existing_dirs)

        return list(
            filter_none(action_blob_copy(blob) for blob in collect_blobs(source_client, source_container, pattern)))

    if source_share:
        # copy files from share to share

        # the cache of existing directories in the destination file share. the cache helps to avoid
        # repeatedly create existing directory so as to optimize the performance.
        existing_dirs = set()

        if source_client is None:
            t_share_service = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_FILESHARE,
                                      '_share_service_client#ShareServiceClient')
            account_url = '/'.join(client.url.split('/')[:-1])
            source_client = t_share_service(account_url=account_url, credential=client.credential)

        # pylint: disable=inconsistent-return-statements
        def action_file_copy(file_info):
            dir_name, file_name = file_info
            if dryrun:
                logger.warning('  - copy file %s', os.path.join(dir_name, file_name))
            else:
                return _create_file_and_directory_from_file(cmd, client, source_client, share_name, source_share,
                                                            source_sas, dir_name, file_name,
                                                            destination_dir=destination_path, metadata=metadata,
                                                            timeout=timeout, existing_dirs=existing_dirs)

        return list(filter_none(
            action_file_copy(file) for file in collect_files_track2(source_client, source_share, pattern)))
    # won't happen, the validator should ensure either source_container or source_share is set
    raise ValueError('Fail to find source. Neither blob container or file share is specified.')


def storage_file_delete_batch(client, source, pattern=None, dryrun=False, timeout=None):
    """
    Delete files from file share in batch
    """
    from azure.cli.command_modules.storage.util import normalize_blob_file_path

    def delete_action(pair):
        path = os.path.join(*pair)
        path = normalize_blob_file_path(None, path)
        file_client = client.get_file_client(path)
        return file_client.delete_file(timeout=timeout)

    from azure.cli.command_modules.storage.util import glob_files_remotely_track2
    source_files = list(glob_files_remotely_track2(client, source, pattern, is_share_client=True))

    if dryrun:
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


# pylint: disable=too-many-locals
def _create_file_and_directory_from_blob(cmd, file_service, blob_service, share, container, sas, blob_name,
                                         destination_dir=None, metadata=None, timeout=None, existing_dirs=None):
    """
    Copy a blob to file share and create the directory if needed.
    """
    from azure.common import AzureException
    from azure.cli.command_modules.storage.util import normalize_blob_file_path

    t_blob_client = cmd.get_models('_blob_client#BlobClient', resource_type=ResourceType.DATA_STORAGE_BLOB)
    if sas is None:
        t_generate_blob_sas = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_BLOB,
                                      '_shared_access_signature#generate_blob_sas')
        t_blob_permissions = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_BLOB,
                                     '_models#BlobSasPermissions')
        from datetime import datetime, timedelta
        start = datetime.utcnow()
        expiry = datetime.utcnow() + timedelta(days=1)
        source_sas = t_generate_blob_sas(account_name=blob_service.account_name, container_name=container,
                                         blob_name=blob_name,
                                         account_key=blob_service.credential.account_key,
                                         permission=t_blob_permissions(read=True),
                                         expiry=expiry, start=start)
        from urllib.parse import quote
        sas = quote(source_sas, safe='&%()$=\',~')

    source_client = t_blob_client(account_url=blob_service.url, container_name=container,
                                  blob_name=blob_name, credential=sas)
    blob_url = source_client.url

    full_path = normalize_blob_file_path(destination_dir, blob_name)
    dir_name = os.path.dirname(full_path)
    _make_directory_in_files_share(file_service, dir_name, existing_dirs)

    try:
        file_client = file_service.get_file_client(full_path)
        file_client.start_copy_from_url(source_url=blob_url, metadata=metadata, timeout=timeout)
        return file_client.url
    except AzureException:
        error_template = 'Failed to copy blob {} to file share {}. Please check if you have permission to read ' \
                         'source or set a correct sas token.'
        from knack.util import CLIError
        raise CLIError(error_template.format(blob_name, share))


# pylint: disable=too-many-locals
def _create_file_and_directory_from_file(cmd, file_service, source_file_service, share, source_share, sas,
                                         source_file_dir, source_file_name, destination_dir=None, metadata=None,
                                         timeout=None, existing_dirs=None):
    """
    Copy a file from one file share to another
    """
    from azure.common import AzureException
    from azure.cli.command_modules.storage.util import normalize_blob_file_path

    file_path = source_file_name
    if source_file_dir:
        file_path = source_file_dir + '/' + file_path
    t_file_client = cmd.get_models('_file_client#ShareFileClient', resource_type=ResourceType.DATA_STORAGE_FILESHARE)
    if sas is None:
        t_generate_share_sas = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_FILESHARE,
                                       '_shared_access_signature#generate_share_sas')
        t_file_permissions = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_FILESHARE,
                                     '_models#FileSasPermissions')
        from datetime import datetime, timedelta
        start = datetime.utcnow()
        expiry = datetime.utcnow() + timedelta(days=1)
        source_sas = t_generate_share_sas(account_name=source_file_service.account_name, share_name=source_share,
                                          account_key=source_file_service.credential.account_key,
                                          permission=t_file_permissions(read=True),
                                          expiry=expiry, start=start)
        from urllib.parse import quote
        sas = quote(source_sas, safe='&%()$=\',~')

    source_client = t_file_client(account_url=source_file_service.url, share_name=source_share, file_path=file_path,
                                  credential=sas)
    file_url = source_client.url

    full_path = normalize_blob_file_path(destination_dir, os.path.join(source_file_dir, source_file_name))
    file_name = os.path.basename(full_path)
    dir_name = os.path.dirname(full_path)
    _make_directory_in_files_share(file_service, dir_name, existing_dirs)

    try:
        file_client = file_service.get_file_client(full_path)
        file_client.start_copy_from_url(source_url=file_url, metadata=metadata, timeout=timeout)
        return file_client.url
    except AzureException:
        error_template = 'Failed to copy file {} from share {} to file share {}. Please check if ' \
                         'you have right permission to read source or set a correct sas token.'
        from knack.util import CLIError
        raise CLIError(error_template.format(file_name, source_share, share))


def _make_directory_in_files_share(file_service, directory_path, existing_dirs=None):
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
            file_service.create_directory(directory_name=dir_name)
        except ResourceExistsError:
            pass
        except AzureHttpError:
            from knack.util import CLIError
            raise CLIError('Failed to create directory {}'.format(dir_name))

        if existing_dirs:
            existing_dirs.add(directory_path)


def _file_share_exists(client, resource_group_name, account_name, share_name):
    try:
        file_share = client.get(resource_group_name, account_name, share_name, expand=None)
        return file_share is not None
    except HttpResponseError:
        return False


# pylint: disable=redefined-builtin
def generate_sas_file(cmd, client, share_name=None, directory_name=None, file_name=None, permission=None, expiry=None,
                      start=None, id=None, ip=None, protocol=None, as_user=False, user_delegation_oid=None, **kwargs):
    t_generate_file_sas = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_FILESHARE,
                                  '_shared_access_signature#generate_file_sas')
    file_path = file_name
    if directory_name:
        file_path = directory_name + '/' + file_path
    file_path = file_path.split('/')

    account_key = None
    user_delegation_key = None
    if as_user:
        from datetime import datetime
        user_delegation_key = client.get_user_delegation_key(
            start=get_datetime_from_string(start) if start else datetime.utcnow(),
            expiry=get_datetime_from_string(expiry))
    else:
        account_key = client.credential.account_key

    sas_token = t_generate_file_sas(account_name=client.account_name, share_name=share_name, file_path=file_path,
                                    account_key=account_key, permission=permission, expiry=expiry,
                                    start=start, policy_id=id, ip=ip, protocol=protocol,
                                    user_delegation_key=user_delegation_key, user_delegation_oid=user_delegation_oid,
                                    **kwargs)
    from urllib.parse import quote
    return quote(sas_token, safe='&%()$=\',~')


def file_exists(client, **kwargs):
    try:
        res = client.get_file_properties(**kwargs)
        return bool(res)
    except ResourceNotFoundError:
        return False
    except HttpResponseError as ex:
        raise ex


def file_updates(client, **kwargs):
    return client.set_http_headers(**kwargs)


def _format_storage_account_id(args_schema):
    from azure.cli.core.aaz import AAZResourceIdArgFormat
    args_schema.storage_account._fmt = AAZResourceIdArgFormat(
        template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Storage/"
                 "storageAccounts/{}"
    )
    args_schema.resource_group._required = False


class ShareRmCreate(_ShareRmCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        _format_storage_account_id(args_schema)
        return args_schema

    def pre_operations(self):
        from .._validators import parse_storage_account_aaz
        args = self.ctx.args
        parse_storage_account_aaz(self, args)

    def post_operations(self):
        result = self.ctx.vars.instance
        new_result = _transform_share_rm_output(result)
        self.ctx.vars.instance = new_result


class ShareRmUpdate(_ShareRmUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        _format_storage_account_id(args_schema)
        return args_schema

    def pre_operations(self):
        from .._validators import parse_storage_account_aaz
        args = self.ctx.args
        parse_storage_account_aaz(self, args)

    def post_instance_update(self, instance):
        args = self.ctx.args
        if args.metadata:
            instance.properties.metadata = args.metadata

    def post_operations(self):
        result = self.ctx.vars.instance
        new_result = _transform_share_rm_output(result)
        self.ctx.vars.instance = new_result


class ShareRmDelete(_ShareRmDelete):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        _format_storage_account_id(args_schema)
        return args_schema

    def pre_operations(self):
        from .._validators import parse_storage_account_aaz
        args = self.ctx.args
        parse_storage_account_aaz(self, args)


def _transform_share_rm_output(result):
    from datetime import datetime
    try:
        if hasattr(result, 'properties'):
            if hasattr(result.properties, 'next_allowed_quota_downgrade_time') \
                    and result.properties.next_allowed_quota_downgrade_time:
                time_str = str(result.properties.next_allowed_quota_downgrade_time)
                time_obj = datetime.strptime(time_str, '%a, %d %b %Y %H:%M:%S %Z')
                result.properties.next_allowed_quota_downgrade_time = \
                    time_obj.strftime("%Y-%m-%dT%H:%M:%S.%f0Z")
            if hasattr(result.properties, 'next_allowed_provisioned_iops_downgrade_time') \
                    and result.properties.next_allowed_provisioned_iops_downgrade_time:
                time_str = str(result.properties.next_allowed_provisioned_iops_downgrade_time)
                time_obj = datetime.strptime(time_str, '%a, %d %b %Y %H:%M:%S %Z')
                result.properties.next_allowed_provisioned_iops_downgrade_time = \
                    time_obj.strftime("%Y-%m-%dT%H:%M:%S.%f0Z")
            if hasattr(result.properties, 'next_allowed_provisioned_bandwidth_downgrade_time') \
                    and result.properties.next_allowed_provisioned_bandwidth_downgrade_time:
                time_str = str(result.properties.next_allowed_provisioned_bandwidth_downgrade_time)
                time_obj = datetime.strptime(time_str, '%a, %d %b %Y %H:%M:%S %Z')
                result.properties.next_allowed_provisioned_bandwidth_downgrade_time = \
                    time_obj.strftime("%Y-%m-%dT%H:%M:%S.%f0Z")
            return result
    except ValueError:  # make sure service side fix does not break
        return result


class ShareRmShow(_ShareRmShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        _format_storage_account_id(args_schema)
        return args_schema

    def pre_operations(self):
        from .._validators import parse_storage_account_aaz
        args = self.ctx.args
        parse_storage_account_aaz(self, args)

    def post_operations(self):
        result = self.ctx.vars.instance
        new_result = _transform_share_rm_output(result)
        self.ctx.vars.instance = new_result


class ShareRmList(_ShareRmList):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZBoolArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.include_deleted = AAZBoolArg(
            options=["--include-deleted"],
            help="Include soft deleted file shares when specified."
        )
        args_schema.include_snapshot = AAZBoolArg(
            options=["--include-snapshot"],
            help="Include file share snapshots when specified."
        )
        _format_storage_account_id(args_schema)

        args_schema.include_deleted._registered = True
        args_schema.include_snapshot._registered = True
        args_schema.expand._registered = False
        return args_schema

    def pre_operations(self):
        from .._validators import parse_storage_account_aaz
        args = self.ctx.args
        expand_item = []
        if has_value(args.include_deleted):
            expand_item.append('deleted')
        if has_value(args.include_snapshot):
            expand_item.append('snapshots')
        if expand_item:
            args.expand = ','.join(expand_item)

        parse_storage_account_aaz(self, args)

    def post_operations(self):
        result = self.ctx.vars.instance.value
        new_result = []
        for item in result:
            new_result.append(_transform_share_rm_output(item))
        self.ctx.vars.instance.value = new_result
