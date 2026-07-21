# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
from datetime import datetime, timedelta

from azure.cli.core.profiles import ResourceType, get_sdk
from azure.cli.core.util import sdk_no_wait
from azure.cli.core.azclierror import AzureResponseError, FileOperationError
from azure.cli.command_modules.storage.util import (filter_none, collect_blobs, collect_blob_objects,
                                                    collect_files_track2, mkdir_p, guess_content_type,
                                                    normalize_blob_file_path, check_precondition_success)
from azure.core.exceptions import ResourceExistsError, ResourceModifiedError, HttpResponseError

from knack.log import get_logger
from knack.util import CLIError
from .._transformers import transform_response_with_bytearray
from ..util import get_datetime_from_string

logger = get_logger(__name__)


def set_legal_hold(cmd, client, container_name, account_name, tags, allow_protected_append_writes_all,
                   resource_group_name=None):
    LegalHold = cmd.get_models('LegalHold', resource_type=ResourceType.MGMT_STORAGE)
    legal_hold = LegalHold(tags=tags, allow_protected_append_writes_all=allow_protected_append_writes_all)
    return client.set_legal_hold(resource_group_name, account_name, container_name, legal_hold)


def clear_legal_hold(cmd, client, container_name, account_name, tags, allow_protected_append_writes_all,
                     resource_group_name=None):
    LegalHold = cmd.get_models('LegalHold', resource_type=ResourceType.MGMT_STORAGE)
    legal_hold = LegalHold(tags=tags, allow_protected_append_writes_all=allow_protected_append_writes_all)
    return client.clear_legal_hold(resource_group_name, account_name, container_name, legal_hold)


def create_or_update_immutability_policy(cmd, client, container_name, account_name,
                                         resource_group_name=None, allow_protected_append_writes=None,
                                         allow_protected_append_writes_all=None,
                                         period=None, if_match=None):
    ImmutabilityPolicy = cmd.get_models('ImmutabilityPolicy', resource_type=ResourceType.MGMT_STORAGE)
    immutability_policy = ImmutabilityPolicy(immutability_period_since_creation_in_days=period,
                                             allow_protected_append_writes=allow_protected_append_writes,
                                             allow_protected_append_writes_all=allow_protected_append_writes_all)
    return client.create_or_update_immutability_policy(resource_group_name, account_name, container_name,
                                                       if_match, immutability_policy)


def extend_immutability_policy(cmd, client, container_name, account_name, if_match,
                               resource_group_name=None, allow_protected_append_writes=None,
                               allow_protected_append_writes_all=None,
                               period=None):
    ImmutabilityPolicy = cmd.get_models('ImmutabilityPolicy', resource_type=ResourceType.MGMT_STORAGE)
    immutability_policy = ImmutabilityPolicy(immutability_period_since_creation_in_days=period,
                                             allow_protected_append_writes=allow_protected_append_writes,
                                             allow_protected_append_writes_all=allow_protected_append_writes_all)
    return client.extend_immutability_policy(resource_group_name, account_name, container_name,
                                             if_match, immutability_policy)


def create_container_rm(cmd, client, container_name, resource_group_name, account_name,
                        metadata=None, public_access=None, fail_on_exist=False,
                        default_encryption_scope=None, deny_encryption_scope_override=None, enable_vlw=None,
                        enable_nfs_v3_root_squash=None, enable_nfs_v3_all_squash=None):
    if fail_on_exist and container_rm_exists(client, resource_group_name=resource_group_name,
                                             account_name=account_name, container_name=container_name):
        raise CLIError('The specified container already exists.')

    BlobContainer = cmd.get_models('BlobContainer', resource_type=ResourceType.MGMT_STORAGE)
    blob_container = BlobContainer(public_access=public_access,
                                   default_encryption_scope=default_encryption_scope,
                                   deny_encryption_scope_override=deny_encryption_scope_override,
                                   metadata=metadata,
                                   enable_nfs_v3_all_squash=enable_nfs_v3_all_squash,
                                   enable_nfs_v3_root_squash=enable_nfs_v3_root_squash)
    if enable_vlw is not None:
        ImmutableStorageWithVersioning = cmd.get_models('ImmutableStorageWithVersioning',
                                                        resource_type=ResourceType.MGMT_STORAGE)
        blob_container.immutable_storage_with_versioning = ImmutableStorageWithVersioning(enabled=enable_vlw)
    return client.create(resource_group_name=resource_group_name, account_name=account_name,
                         container_name=container_name, blob_container=blob_container)


def update_container_rm(cmd, instance, metadata=None, public_access=None,
                        enable_nfs_v3_root_squash=None, enable_nfs_v3_all_squash=None):
    BlobContainer = cmd.get_models('BlobContainer', resource_type=ResourceType.MGMT_STORAGE)

    blob_container = BlobContainer(
        metadata=metadata if metadata is not None else instance.metadata,
        public_access=public_access if public_access is not None else instance.public_access,
        enable_nfs_v3_all_squash=enable_nfs_v3_all_squash
        if enable_nfs_v3_all_squash is not None else instance.enable_nfs_v3_all_squash,
        enable_nfs_v3_root_squash=enable_nfs_v3_root_squash
        if enable_nfs_v3_root_squash is not None else instance.enable_nfs_v3_root_squash
    )
    return blob_container


def list_container_rm(cmd, client, resource_group_name, account_name, include_deleted=None):
    ListContainersInclude = cmd.get_models('ListContainersInclude', resource_type=ResourceType.MGMT_STORAGE)
    include = ListContainersInclude("deleted") if include_deleted is not None else None

    return client.list(resource_group_name=resource_group_name, account_name=account_name, include=include)


def container_rm_exists(client, resource_group_name, account_name, container_name):
    try:
        container = client.get(resource_group_name=resource_group_name,
                               account_name=account_name, container_name=container_name)
        return container is not None
    except HttpResponseError as err:
        if err.status_code == 404:
            return False
        raise err


# pylint: disable=unused-argument
def create_container(client, container_name, resource_group_name=None,
                     metadata=None, public_access=None, fail_on_exist=False, timeout=None,
                     default_encryption_scope=None, prevent_encryption_scope_override=None):
    encryption_scope = None
    if default_encryption_scope is not None or prevent_encryption_scope_override is not None:
        encryption_scope = {
            'default_encryption_scope': default_encryption_scope,
            'prevent_encryption_scope_override': prevent_encryption_scope_override
        }
    try:
        container = client.create_container(container_name, metadata=metadata,
                                            public_access=public_access,
                                            container_encryption_scope=encryption_scope,
                                            timeout=timeout)
        return container is not None
    except ResourceExistsError as ex:
        if not fail_on_exist:
            return False
        raise ex


def delete_container(client, container_name, fail_not_exist=False, lease_id=None, if_modified_since=None,
                     if_unmodified_since=None, timeout=None, bypass_immutability_policy=False,
                     processed_resource_group=None, processed_account_name=None, mgmt_client=None):
    from azure.core.exceptions import ResourceNotFoundError
    if bypass_immutability_policy:
        mgmt_client.blob_containers.delete(processed_resource_group, processed_account_name, container_name)
        return True
    try:
        client.delete_container(container_name, lease=lease_id,
                                if_modified_since=if_modified_since,
                                if_unmodified_since=if_unmodified_since,
                                timeout=timeout)
        return True
    except ResourceNotFoundError as ex:
        if not fail_not_exist:
            return False
        raise ex


def set_container_permission(client, public_access=None, **kwargs):
    acl_response = client.get_container_access_policy()
    signed_identifiers = {}
    if acl_response.get('signed_identifiers'):
        for identifier in acl_response["signed_identifiers"]:
            signed_identifiers[identifier.id] = identifier.access_policy
    return client.set_container_access_policy(signed_identifiers=signed_identifiers,
                                              public_access=public_access, **kwargs)


def list_blobs(client, delimiter=None, include=None, marker=None, num_results=None, prefix=None,
               show_next_marker=None, **kwargs):
    from ..track2_util import list_generator

    if delimiter:
        generator = client.walk_blobs(
            name_starts_with=prefix, include=include, results_per_page=num_results, delimiter=delimiter, **kwargs)
    else:
        generator = client.list_blobs(name_starts_with=prefix, include=include, results_per_page=num_results, **kwargs)

    pages = generator.by_page(continuation_token=marker)  # BlobPropertiesPaged
    result = list_generator(pages=pages, num_results=num_results)

    if show_next_marker:
        next_marker = {"nextMarker": pages.continuation_token}
        result.append(next_marker)
    else:
        if pages.continuation_token:
            logger.warning('Next Marker:')
            logger.warning(pages.continuation_token)

    return result


def list_containers(client, include_metadata=False, include_deleted=False, marker=None,
                    num_results=None, prefix=None, show_next_marker=None, **kwargs):
    from ..track2_util import list_generator

    generator = client.list_containers(name_starts_with=prefix, include_metadata=include_metadata,
                                       include_deleted=include_deleted, results_per_page=num_results, **kwargs)

    pages = generator.by_page(continuation_token=marker)  # ContainerPropertiesPaged
    result = list_generator(pages=pages, num_results=num_results)

    if show_next_marker:
        next_marker = {"nextMarker": pages.continuation_token}
        result.append(next_marker)
    else:
        if pages.continuation_token:
            logger.warning('Next Marker:')
            logger.warning(pages.continuation_token)

    return result


def restore_blob_ranges(cmd, client, resource_group_name, account_name, time_to_restore, blob_ranges=None,
                        no_wait=False):
    if blob_ranges is None:
        BlobRestoreRange = cmd.get_models("BlobRestoreRange")
        blob_ranges = [BlobRestoreRange(start_range="", end_range="")]
    restore_parameters = cmd.get_models("BlobRestoreParameters")(time_to_restore=time_to_restore,
                                                                 blob_ranges=blob_ranges)
    return sdk_no_wait(no_wait, client.begin_restore_blob_ranges, resource_group_name=resource_group_name,
                       account_name=account_name, parameters=restore_parameters)


def set_blob_tier(client, container_name, blob_name, tier, blob_type='block', timeout=None):
    if blob_type == 'block':
        return client.set_standard_blob_tier(container_name=container_name, blob_name=blob_name,
                                             standard_blob_tier=tier, timeout=timeout)
    if blob_type == 'page':
        return client.set_premium_page_blob_tier(container_name=container_name, blob_name=blob_name,
                                                 premium_page_blob_tier=tier, timeout=timeout)
    raise ValueError('Blob tier is only applicable to block or page blob.')


def set_delete_policy(client, enable=None, days_retained=None):
    policy = client.get_service_properties()['delete_retention_policy']

    if enable is not None:
        policy.enabled = enable == 'true'
    if days_retained is not None:
        policy.days = days_retained
        if not 1 <= days_retained <= 365:
            raise CLIError("Retention days must be greater than 0 and less than or equal to 365 days")

    if policy.enabled and not policy.days:
        raise CLIError("must specify days-retained")

    client.set_service_properties(delete_retention_policy=policy)
    return client.get_service_properties()['delete_retention_policy']


def set_immutability_policy(cmd, client, expiry_time=None, policy_mode=None, **kwargs):
    ImmutabilityPolicy = cmd.get_models("_models#ImmutabilityPolicy", resource_type=ResourceType.DATA_STORAGE_BLOB)
    if not expiry_time and not policy_mode:
        from azure.cli.core.azclierror import InvalidArgumentValueError
        raise InvalidArgumentValueError('Please specify --expiry-time | --policy-mode')
    immutability_policy = ImmutabilityPolicy(expiry_time=expiry_time, policy_mode=policy_mode)
    return client.set_immutability_policy(immutability_policy=immutability_policy, **kwargs)


def set_service_properties(client, parameters, delete_retention=None, delete_retention_period=None,
                           static_website=None, index_document=None, error_document_404_path=None):
    # update
    kwargs = {}
    if hasattr(parameters, 'delete_retention_policy'):
        kwargs['delete_retention_policy'] = parameters.delete_retention_policy
    if delete_retention is not None:
        parameters.delete_retention_policy.enabled = delete_retention
    if delete_retention_period is not None:
        parameters.delete_retention_policy.days = delete_retention_period

    if hasattr(parameters, 'static_website'):
        kwargs['static_website'] = parameters.static_website
    elif any(param is not None for param in [static_website, index_document, error_document_404_path]):
        raise CLIError('Static websites are only supported for StorageV2 (general-purpose v2) accounts.')
    if static_website is not None:
        parameters.static_website.enabled = static_website
    if index_document is not None:
        parameters.static_website.index_document = index_document
    if error_document_404_path is not None:
        parameters.static_website.error_document_404_path = error_document_404_path
    if hasattr(parameters, 'hour_metrics'):
        kwargs['hour_metrics'] = parameters.hour_metrics
    if hasattr(parameters, 'logging'):
        kwargs['logging'] = parameters.logging
    if hasattr(parameters, 'minute_metrics'):
        kwargs['minute_metrics'] = parameters.minute_metrics
    if hasattr(parameters, 'cors'):
        kwargs['cors'] = parameters.cors

    # checks
    policy = kwargs.get('delete_retention_policy', None)
    if policy and policy.enabled and not policy.days:
        raise CLIError("must specify days-retained")

    client.set_blob_service_properties(**kwargs)
    return client.get_blob_service_properties()


# pylint: disable=too-few-public-methods
class BlobServiceProperties:
    pass


def transform_blob_generic_output(instance):
    r = BlobServiceProperties()
    for key in instance:
        setattr(r, key, instance[key])
    setattr(r, 'logging', getattr(r, 'analytics_logging'))
    delattr(r, 'analytics_logging')
    return r


def set_service_properties_track2(client, parameters, delete_retention=None, delete_retention_period=None,
                                  static_website=None, index_document=None, error_document_404_path=None):
    # update
    kwargs = {}
    if hasattr(parameters, 'delete_retention_policy'):
        kwargs['delete_retention_policy'] = parameters.delete_retention_policy
    if delete_retention is not None:
        parameters.delete_retention_policy.enabled = delete_retention
    if delete_retention_period is not None:
        parameters.delete_retention_policy.days = delete_retention_period

    if hasattr(parameters, 'static_website'):
        kwargs['static_website'] = parameters.static_website
    if index_document is not None:
        parameters.static_website.index_document = index_document
    if error_document_404_path is not None:
        parameters.static_website.error_document404_path = error_document_404_path
    if static_website is not None:
        parameters.static_website.enabled = static_website
        if not static_website:
            parameters.static_website.index_document = None
            parameters.static_website.error_document404_path = None
    if hasattr(parameters, 'hour_metrics'):
        kwargs['hour_metrics'] = parameters.hour_metrics
    if hasattr(parameters, 'logging'):
        kwargs['analytics_logging'] = parameters.logging
    if hasattr(parameters, 'minute_metrics'):
        kwargs['minute_metrics'] = parameters.minute_metrics
    if hasattr(parameters, 'cors'):
        kwargs['cors'] = parameters.cors

    if not parameters.hour_metrics.enabled:
        parameters.hour_metrics.include_apis = None
    if not parameters.minute_metrics.enabled:
        parameters.minute_metrics.include_apis = None

    # checks
    policy = kwargs.get('delete_retention_policy', None)
    if policy and policy.enabled and not policy.days:
        raise CLIError("must specify days-retained")

    client.set_service_properties(**kwargs)
    return client.get_service_properties()


def storage_blob_copy_batch(cmd, client, source_client, container_name=None, destination_path=None,
                            source_container=None, source_share=None, source_sas=None, pattern=None, dryrun=False,
                            source_account_name=None, source_account_key=None, **kwargs):
    """Copy a group of blob or files to a blob container."""
    if dryrun:
        logger.warning('copy files or blobs to blob container')
        logger.warning('    account %s', client.account_name)
        logger.warning('  container %s', container_name)
        logger.warning('     source %s', source_container or source_share)
        logger.warning('source type %s', 'blob' if source_container else 'file')
        logger.warning('    pattern %s', pattern)
        logger.warning(' operations')

    if source_container:
        # copy blobs for blob container, skip empty dir
        # pylint: disable=inconsistent-return-statements
        if source_client is None:
            source_client = client

        def action_blob_copy(blob_name):
            if dryrun:
                logger.warning('  - copy blob %s', blob_name)
            else:
                return _copy_blob_to_blob_container(cmd, blob_service=client, source_blob_service=source_client,
                                                    destination_container=container_name,
                                                    destination_path=destination_path,
                                                    source_container=source_container,
                                                    source_blob_name=blob_name,
                                                    source_sas=source_sas,
                                                    **kwargs)
        return list(filter_none(action_blob_copy(blob) for blob in collect_blobs(source_client,
                                                                                 source_container,
                                                                                 pattern)))

    if source_share:
        # copy blob from file share, skip empty dir
        # pylint: disable=inconsistent-return-statements
        if source_client is None:
            t_share_service = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_FILESHARE,
                                      '_share_service_client#ShareServiceClient')
            account_url = client.url.replace('blob', 'file')
            if client.credential and client.credential.account_key:
                credential = {
                    "account_name": client.credential.account_name,
                    "account_key": client.credential.account_key
                }
                source_client = t_share_service(account_url=account_url, credential=credential)
            else:
                source_client = t_share_service(account_url=account_url, credential=client.credential)

        def action_file_copy(file_info):
            dir_name, file_name = file_info
            if dryrun:
                logger.warning('  - copy file %s', '/'.join(dir_name, file_name))
            else:
                return _copy_file_to_blob_container(cmd, client, source_client, container_name, destination_path,
                                                    source_share, source_sas, dir_name, file_name)

        return list(filter_none(action_file_copy(file) for file in collect_files_track2(source_client,
                                                                                        source_share,
                                                                                        pattern)))
    raise ValueError('Fail to find source. Neither blob container nor file share is specified')


# pylint: disable=unused-argument
def storage_blob_download_batch(client, source, destination, source_container_name, pattern=None, dryrun=False,
                                progress_callback=None, overwrite=False, **kwargs):
    @check_precondition_success
    def _download_blob(*args, **kwargs):
        blob = download_blob(*args, **kwargs)
        return blob.name

    source_blobs = collect_blobs(client, source_container_name, pattern)
    blobs_to_download = {}
    for blob_name in source_blobs:
        # remove starting path seperator and normalize
        normalized_blob_name = normalize_blob_file_path(None, blob_name)
        if normalized_blob_name in blobs_to_download:
            raise CLIError('Multiple blobs with download path: `{}`. As a solution, use the `--pattern` parameter '
                           'to select for a subset of blobs to download OR utilize the `storage blob download` '
                           'command instead to download individual blobs.'.format(normalized_blob_name))
        blobs_to_download[normalized_blob_name] = blob_name

    if dryrun:
        logger.warning('download action: from %s to %s', source, destination)
        logger.warning('    pattern %s', pattern)
        logger.warning('  container %s', source_container_name)
        logger.warning('      total %d', len(source_blobs))
        logger.warning(' operations')
        for b in source_blobs:
            logger.warning('  - %s', b)
        return []

    # Tell progress reporter to reuse the same hook
    if progress_callback:
        progress_callback.reuse = True

    results = []
    for index, blob_normed in enumerate(blobs_to_download):
        # add blob name and number to progress message
        if progress_callback:
            progress_callback.message = '{}/{}: "{}"'.format(
                index + 1, len(blobs_to_download), blobs_to_download[blob_normed])
        blob_client = client.get_blob_client(container=source_container_name,
                                             blob=blobs_to_download[blob_normed])
        destination_path = os.path.join(destination, os.path.normpath(blob_normed))
        destination_folder = os.path.dirname(destination_path)
        # Failed when there is same name for file and folder
        if os.path.isfile(destination_path) and os.path.exists(destination_folder) and not overwrite:
            raise FileOperationError("%s already exists in %s. Please rename existing file or choose another "
                                     "destination folder. " % (blob_normed, destination))
        if not os.path.exists(destination_folder):
            mkdir_p(destination_folder)
        include, result = _download_blob(client=blob_client, file_path=destination_path,
                                         progress_callback=progress_callback, overwrite=overwrite, **kwargs)
        if include:
            results.append(result)

    # end progress hook
    if progress_callback:
        progress_callback.hook.end()

    num_failures = len(blobs_to_download) - len(results)
    if num_failures:
        logger.warning('%s of %s files not downloaded due to "Failed Precondition"',
                       num_failures, len(blobs_to_download))
    return results


def storage_blob_upload_batch(cmd, client, source, destination, pattern=None,  # pylint: disable=too-many-locals
                              source_files=None, destination_path=None,
                              destination_container_name=None, blob_type=None,
                              content_settings=None, metadata=None, validate_content=False,
                              maxsize_condition=None, max_connections=2, lease_id=None, progress_callback=None,
                              if_modified_since=None, if_unmodified_since=None, if_match=None,
                              if_none_match=None, timeout=None, dryrun=False, socket_timeout=None, **kwargs):
    def _create_return_result(blob_content_settings, blob_client, upload_result=None):
        return {
            'Blob': blob_client.url,
            'Type': blob_content_settings.content_type,
            'Last Modified': upload_result['last_modified'] if upload_result else None,
            'eTag': upload_result['etag'] if upload_result else None}

    source_files = source_files or []
    t_content_settings = cmd.get_models('_models#ContentSettings', resource_type=cmd.command_kwargs['resource_type'])

    results = []
    if dryrun:
        logger.info('upload action: from %s to %s', source, destination)
        logger.info('    pattern %s', pattern)
        logger.info('  container %s', destination_container_name)
        logger.info('       type %s', blob_type)
        logger.info('      total %d', len(source_files))
        results = []
        for src, dst in source_files:
            blob_client = client.get_blob_client(container=destination_container_name,
                                                 blob=normalize_blob_file_path(destination_path, dst))
            results.append(_create_return_result(blob_content_settings=guess_content_type(src, content_settings,
                                                                                          t_content_settings),
                                                 blob_client=blob_client))
    else:
        @check_precondition_success
        def _upload_blob(*args, **kwargs):
            return upload_blob(*args, **kwargs)

        # Tell progress reporter to reuse the same hook
        if progress_callback:
            progress_callback.reuse = True

        for index, source_file in enumerate(source_files):
            src, dst = source_file
            # logger.warning('uploading %s', src)
            guessed_content_settings = guess_content_type(src, content_settings, t_content_settings)

            # add blob name and number to progress message
            if progress_callback:
                progress_callback.message = '{}/{}: "{}"'.format(
                    index + 1, len(source_files), normalize_blob_file_path(destination_path, dst))
            blob_client = client.get_blob_client(container=destination_container_name,
                                                 blob=normalize_blob_file_path(destination_path, dst))
            try:
                include, result = _upload_blob(cmd, blob_client, file_path=src,
                                               blob_type=blob_type, content_settings=guessed_content_settings,
                                               metadata=metadata, validate_content=validate_content,
                                               maxsize_condition=maxsize_condition, max_connections=max_connections,
                                               lease_id=lease_id, progress_callback=progress_callback,
                                               if_modified_since=if_modified_since,
                                               if_unmodified_since=if_unmodified_since, if_match=if_match,
                                               if_none_match=if_none_match, timeout=timeout, **kwargs)
                if include:
                    results.append(_create_return_result(blob_content_settings=guessed_content_settings,
                                                         blob_client=blob_client, upload_result=result))
            except (ResourceModifiedError, AzureResponseError) as ex:
                logger.error(ex)

        # end progress hook
        if progress_callback:
            progress_callback.hook.end()
        num_failures = len(source_files) - len(results)
        if num_failures:
            logger.warning('%s of %s files not uploaded due to "Failed Precondition"', num_failures, len(source_files))
    return results


def transform_blob_type(cmd, blob_type):
    """
    get_blob_types() will get ['block', 'page', 'append']
    transform it to BlobType in track2
    """
    BlobType = cmd.get_models('_models#BlobType', resource_type=ResourceType.DATA_STORAGE_BLOB)
    if blob_type == 'block':
        return BlobType.BlockBlob
    if blob_type == 'page':
        return BlobType.PageBlob
    if blob_type == 'append':
        return BlobType.AppendBlob
    return None


# pylint: disable=protected-access
def _adjust_block_blob_size(client, blob_type, length):
    if not blob_type or blob_type == 'page' or length is None:
        return

    # increase the block size to 8MB when blob size is >= 8MB to enable high throughput block/append blob
    if length >= 8 * 1024 * 1024:
        client._config.max_block_size = 8 * 1024 * 1024
        client._config.max_single_put_size = 256 * 1024 * 1024

    # increase the block size to 100MB when the block list will contain more than 50,000 blocks(each block 4MB)
    if length > 50000 * 4 * 1024 * 1024:
        client._config.max_block_size = 100 * 1024 * 1024
        client._config.max_single_put_size = 256 * 1024 * 1024

    if blob_type == 'append':
        return

    # increase the block size to 4000MB when the block list will contain more than 50,000 blocks(each block 100MB)
    if length > 50000 * 100 * 1024 * 1024:
        client._config.max_block_size = 4000 * 1024 * 1024
        client._config.max_single_put_size = 5000 * 1024 * 1024


# pylint: disable=too-many-locals
def upload_blob(cmd, client, file_path=None, container_name=None, blob_name=None, blob_type=None,
                metadata=None, validate_content=False, maxsize_condition=None, max_connections=2, lease_id=None,
                if_modified_since=None, if_unmodified_since=None, if_match=None, if_none_match=None,
                timeout=None, progress_callback=None, encryption_scope=None, overwrite=None, data=None,
                length=None, **kwargs):
    """Upload a blob to a container."""
    upload_args = {
        'blob_type': transform_blob_type(cmd, blob_type),
        'lease': lease_id,
        'max_concurrency': max_connections
    }

    if file_path and 'content_settings' in kwargs:
        t_blob_content_settings = cmd.get_models('_models#ContentSettings',
                                                 resource_type=ResourceType.DATA_STORAGE_BLOB)
        kwargs['content_settings'] = guess_content_type(file_path, kwargs['content_settings'], t_blob_content_settings)

    if overwrite is not None:
        upload_args['overwrite'] = overwrite
    if maxsize_condition:
        upload_args['maxsize_condition'] = maxsize_condition

    upload_args['validate_content'] = validate_content

    if progress_callback:
        upload_args['progress_hook'] = progress_callback

    check_blob_args = {
        'if_modified_since': if_modified_since,
        'if_unmodified_since': if_unmodified_since,
        'if_match': if_match,
        'if_none_match': if_none_match,
    }

    # used to check for the preconditions as upload_append_blob() cannot
    if blob_type == 'append':
        if client.exists(timeout=timeout):
            client.get_blob_properties(lease=lease_id, timeout=timeout, **check_blob_args)
        upload_args['max_concurrency'] = 1
    else:
        upload_args['if_modified_since'] = if_modified_since
        upload_args['if_unmodified_since'] = if_unmodified_since
        upload_args['if_match'] = if_match
        upload_args['if_none_match'] = if_none_match

    # Because the contents of the uploaded file may be too large, it should be passed into the a stream object,
    # upload_blob() read file data in batches to avoid OOM problems
    try:
        if file_path:
            length = os.path.getsize(file_path)
            _adjust_block_blob_size(client, blob_type, length)
            with open(file_path, 'rb') as stream:
                response = client.upload_blob(data=stream, length=length, metadata=metadata,
                                              encryption_scope=encryption_scope,
                                              **upload_args, **kwargs)
        if data is not None:
            _adjust_block_blob_size(client, blob_type, length)
            try:
                response = client.upload_blob(data=data, length=length, metadata=metadata,
                                              encryption_scope=encryption_scope,
                                              **upload_args, **kwargs)
            except UnicodeEncodeError:
                response = client.upload_blob(data=data.encode('UTF-8', 'ignore').decode('UTF-8'),
                                              length=length, metadata=metadata,
                                              encryption_scope=encryption_scope,
                                              **upload_args, **kwargs)
    except ResourceExistsError as ex:
        raise AzureResponseError(
            "{}\nIf you want to overwrite the existing one, please add --overwrite in your command.".format(ex.message))

    # PageBlobChunkUploader verifies the file when uploading the chunk data, If the contents of the file are
    # all null byte("\x00"), the file will not be uploaded, and the response will be none.
    # Therefore, the compatibility logic for response is added to keep it consistent with track 1
    if response is None:
        return {
            "etag": None,
            "lastModified": None
        }

    from msrest import Serializer
    if 'content_md5' in response and response['content_md5'] is not None:
        response['content_md5'] = Serializer.serialize_bytearray(response['content_md5'])
    if 'content_crc64' in response and response['content_crc64'] is not None:
        response['content_crc64'] = Serializer.serialize_bytearray(response['content_crc64'])
    return response


def download_blob(client, file_path=None, open_mode='wb', start_range=None, end_range=None,
                  progress_callback=None, overwrite=True, **kwargs):
    offset = None
    length = None
    if start_range is not None and end_range is not None:
        offset = start_range
        length = end_range - start_range + 1
    if progress_callback:
        kwargs['progress_hook'] = progress_callback
    if not file_path:
        kwargs['max_concurrency'] = 1
    download_stream = client.download_blob(offset=offset, length=length, **kwargs)
    if file_path:
        if os.path.isfile(file_path) and not overwrite:
            raise FileOperationError("%s already exists. Please rename existing file or use --overwrite" % (file_path))
        with open(file_path, open_mode) as stream:
            download_stream.readinto(stream)
        return download_stream.properties
    with os.fdopen(sys.stdout.fileno(), open_mode) as stream:
        download_stream.readinto(stream)
    return


def get_block_ids(content_length, block_length):
    """Get the block id arrary from block blob length, block size"""
    block_count = 0
    if block_length:
        block_count = content_length // block_length
    if block_count * block_length != content_length:
        block_count += 1
    block_ids = []
    for i in range(block_count):
        chunk_offset = i * block_length
        block_id = '{0:032d}'.format(chunk_offset)
        block_ids.append(block_id)
    return block_ids


def rewrite_blob(cmd, client, source_url, encryption_scope=None, **kwargs):
    src_properties = client.from_blob_url(source_url).get_blob_properties()
    BlobType = cmd.get_models('_models#BlobType', resource_type=ResourceType.DATA_STORAGE_BLOB)
    if src_properties.blob_type != BlobType.BlockBlob:
        from azure.cli.core.azclierror import ValidationError
        raise ValidationError("Currently only support block blob! The source blob is {}.".format(
            src_properties.blob_type))
    src_content_length = src_properties.size
    if src_content_length <= 5000 * 1024 * 1024:
        return client.upload_blob_from_url(source_url=source_url, overwrite=True, encryption_scope=encryption_scope,
                                           destination_lease=kwargs.pop('lease', None), **kwargs)

    block_length = 4000 * 1024 * 1024  # using max block size
    block_ids = get_block_ids(src_content_length, block_length)

    copyoffset = 0
    for block_id in block_ids:
        block_size = block_length
        if copyoffset + block_size > src_content_length:
            block_size = src_content_length - copyoffset
        client.stage_block_from_url(
            block_id=block_id,
            source_url=source_url,
            source_offset=copyoffset,
            source_length=block_size,
            encryption_scope=encryption_scope)
        copyoffset += block_size
    response = client.commit_block_list(block_list=block_ids, content_settings=src_properties.content_settings,
                                        metadata=src_properties.metadata, encryption_scope=encryption_scope, **kwargs)
    return transform_response_with_bytearray(response)


def show_blob(cmd, client, container_name, blob_name, snapshot=None, lease_id=None,
              if_modified_since=None, if_unmodified_since=None, if_match=None,
              if_none_match=None, timeout=None):
    blob = client.get_blob_properties(
        container_name, blob_name, snapshot=snapshot, lease_id=lease_id,
        if_modified_since=if_modified_since, if_unmodified_since=if_unmodified_since, if_match=if_match,
        if_none_match=if_none_match, timeout=timeout)

    try:
        page_ranges = None
        if blob.properties.blob_type == cmd.get_models('blob.models#_BlobTypes').PageBlob:
            page_ranges = client.get_page_ranges(
                container_name, blob_name, snapshot=snapshot, lease_id=lease_id, if_modified_since=if_modified_since,
                if_unmodified_since=if_unmodified_since, if_match=if_match, if_none_match=if_none_match,
                timeout=timeout)

        blob.properties.page_ranges = page_ranges
    except HttpResponseError as ex:
        logger.warning("GetPageRanges failed with status code: %d, message: %s", ex.status_code, ex.message)

    return blob


def storage_blob_delete_batch(client, source, source_container_name, pattern=None, lease_id=None,
                              delete_snapshots=None, if_modified_since=None, if_unmodified_since=None, if_match=None,
                              if_none_match=None, timeout=None, dryrun=False):
    container_client = client.get_container_client(source_container_name)

    from datetime import timezone
    if if_modified_since and not if_modified_since.tzinfo:
        if_modified_since = if_modified_since.replace(tzinfo=timezone.utc)
    if if_unmodified_since and not if_unmodified_since.tzinfo:
        if_unmodified_since = if_unmodified_since.replace(tzinfo=timezone.utc)

    @check_precondition_success
    def _delete_blob(blob_name):
        delete_blob_args = {
            'blob': blob_name,
            'lease': lease_id,
            'delete_snapshots': delete_snapshots,
            'if_modified_since': if_modified_since,
            'if_unmodified_since': if_unmodified_since,
            'if_match': if_match,
            'if_none_match': if_none_match,
            'timeout': timeout
        }
        try:
            container_client.delete_blob(**delete_blob_args)
            return blob_name
        except HttpResponseError as ex:
            logger.debug(ex.exc_msg)
            return None

    source_blobs = list(collect_blob_objects(client, source_container_name, pattern))

    if dryrun:
        delete_blobs = []
        for blob in source_blobs:
            if not if_modified_since or blob[1].last_modified >= if_modified_since:
                if not if_unmodified_since or blob[1].last_modified <= if_unmodified_since:
                    delete_blobs.append(blob[0])
        logger.warning('delete action: from %s', source)
        logger.warning('    pattern %s', pattern)
        logger.warning('  container %s', source_container_name)
        logger.warning('      total %d', len(delete_blobs))
        logger.warning(' operations')
        for blob in delete_blobs:
            logger.warning('  - %s', blob)
        return []

    results = [result for (include, result) in (_delete_blob(blob[0]) for blob in source_blobs) if result]
    num_failures = len(source_blobs) - len(results)
    if num_failures:
        logger.warning('%s of %s blobs not deleted due to "Failed Precondition"', num_failures, len(source_blobs))


def generate_sas_blob_uri(cmd, client, permission=None, expiry=None, start=None, id=None, ip=None,  # pylint: disable=redefined-builtin
                          protocol=None, cache_control=None, content_disposition=None,
                          content_encoding=None, content_language=None,
                          content_type=None, full_uri=False, as_user=False, snapshot=None, user_delegation_oid=None,
                          **kwargs):
    from ..url_quote_util import encode_url_path
    from urllib.parse import quote
    t_generate_blob_sas = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_BLOB,
                                  '_shared_access_signature#generate_blob_sas')

    account_name = client.account_name
    user_delegation_key = None
    account_key = None
    if as_user:
        user_delegation_key = client.get_user_delegation_key(
            get_datetime_from_string(start) if start else datetime.utcnow(), get_datetime_from_string(expiry))
    else:
        account_key = client.credential.account_key

    blob_url = kwargs.pop('blob_url')
    container_name = kwargs.pop('container_name')
    blob_name = kwargs.pop('blob_name')
    t_blob_client = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_BLOB, '_blob_client#BlobClient')
    if blob_url:
        if as_user:
            credential = client.credential._credential
        else:
            credential = client.credential.account_key
        blob_client = t_blob_client.from_blob_url(blob_url=blob_url, credential=credential, snapshot=snapshot)
        container_name = blob_client.container_name
        blob_name = blob_client.blob_name
    else:
        blob_client = client.get_blob_client(container=container_name, blob=blob_name, snapshot=snapshot)
        blob_url = blob_client.url

    sas_token = t_generate_blob_sas(account_name=account_name, container_name=container_name, blob_name=blob_name,
                                    snapshot=snapshot, account_key=account_key, user_delegation_key=user_delegation_key,
                                    permission=permission, expiry=expiry, start=start, policy_id=id, ip=ip,
                                    protocol=protocol, cache_control=cache_control,
                                    content_disposition=content_disposition, content_encoding=content_encoding,
                                    content_language=content_language, content_type=content_type,
                                    user_delegation_oid=user_delegation_oid, **kwargs)

    if full_uri:
        blob_client = t_blob_client(account_url=client.url, container_name=container_name, blob_name=blob_name,
                                    snapshot=snapshot, credential=quote(sas_token, safe='&%()$=\',~'))
        return encode_url_path(blob_client.url, safe='/()$=\',~%')
    return quote(sas_token, safe='&%()$=\',~')


# pylint: disable=redefined-builtin
def generate_container_shared_access_signature(cmd, client, container_name, permission=None, expiry=None,
                                               start=None, id=None, ip=None, protocol=None, cache_control=None,
                                               content_disposition=None, content_encoding=None, content_language=None,
                                               content_type=None, user_delegation_oid=None, as_user=False, **kwargs):
    t_generate_container_sas = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_BLOB,
                                       '_shared_access_signature#generate_container_sas')

    account_name = client.account_name
    user_delegation_key = None
    account_key = None
    if as_user:
        user_delegation_key = client.get_user_delegation_key(
            get_datetime_from_string(start) if start else datetime.utcnow(), get_datetime_from_string(expiry))
    else:
        account_key = client.credential.account_key

    return t_generate_container_sas(account_name=account_name, container_name=container_name,
                                    account_key=account_key, user_delegation_key=user_delegation_key,
                                    permission=permission, expiry=expiry, start=start, policy_id=id, ip=ip,
                                    protocol=protocol, cache_control=cache_control,
                                    content_disposition=content_disposition, content_encoding=content_encoding,
                                    content_language=content_language, content_type=content_type,
                                    user_delegation_oid=user_delegation_oid, **kwargs)


def create_blob_url(client, container_name, blob_name, snapshot, protocol='https'):
    if blob_name:
        blob_client = client.get_blob_client(container=container_name, blob=blob_name, snapshot=snapshot)
        url = blob_client.url
    else:
        container_client = client.get_container_client(container=container_name)
        url = container_client.url if '?' in container_client.url else container_client.url + '/'
    if protocol == 'http':
        return url.replace('https', 'http', 1)
    return url


def _copy_blob_to_blob_container(cmd, blob_service, source_blob_service, destination_container, destination_path,
                                 source_container, source_blob_name, source_sas, **kwargs):
    t_blob_client = cmd.get_models('_blob_client#BlobClient')
    # if blob_service and source_blob_service are the same
    if blob_service == source_blob_service:
        source_client = source_blob_service.get_blob_client(container=source_container, blob=source_blob_name)
    else:
        # generate sas for oauth copy source
        if not source_sas:
            from ..util import create_short_lived_blob_sas_v2
            start = datetime.utcnow()
            expiry = datetime.utcnow() + timedelta(days=1)
            source_user_delegation_key = source_blob_service.get_user_delegation_key(start, expiry)
            source_sas = create_short_lived_blob_sas_v2(cmd, source_blob_service.account_name, source_container,
                                                        source_blob_name,
                                                        user_delegation_key=source_user_delegation_key)
        source_client = t_blob_client(account_url=source_blob_service.url, container_name=source_container,
                                      blob_name=source_blob_name, credential=source_sas)
    source_blob_url = source_client.url

    destination_blob_name = normalize_blob_file_path(destination_path, source_blob_name)
    try:
        blob_client = blob_service.get_blob_client(container=destination_container, blob=destination_blob_name)
        copy_blob(cmd, blob_client, source_blob_url, source_client=source_client, metadata=None, requires_sync=False,
                  **kwargs)
        return blob_client.url
    except HttpResponseError as ex:
        if 'One of the request inputs is not valid' in str(ex):
            # ignore error when copy from Data Lake Gen2 to Data Lake Gen2 and source blob is directory
            pass
        else:
            error_template = 'Failed to copy blob {} to container {}. {}'
            raise CLIError(error_template.format(source_blob_name, destination_container, ex))


def _copy_file_to_blob_container(cmd, blob_service, source_file_service, destination_container, destination_path,
                                 source_share, source_sas, source_file_dir, source_file_name):
    t_share_client = source_file_service.get_share_client(source_share)
    source_path = os.path.join(source_file_dir, source_file_name) if source_file_dir else source_file_name
    source_path = normalize_blob_file_path(None, source_path)
    t_file_client = t_share_client.get_file_client(source_path)
    if source_sas is None:
        t_generate_share_sas = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_FILESHARE,
                                       '_shared_access_signature#generate_share_sas')
        t_file_permissions = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE_FILESHARE,
                                     '_models#FileSasPermissions')
        start = datetime.utcnow()
        expiry = datetime.utcnow() + timedelta(days=1)
        source_sas = t_generate_share_sas(account_name=t_file_client.account_name, share_name=source_share,
                                          account_key=t_file_client.credential.account_key,
                                          permission=t_file_permissions(read=True),
                                          expiry=expiry, start=start)
        from urllib.parse import quote
        source_sas = quote(source_sas, safe='&%()$=\',~')
    if '?' not in t_file_client.url:
        source_file_url = '{}?{}'.format(t_file_client.url, source_sas)
    else:
        source_file_url = t_file_client.url

    destination_blob_name = normalize_blob_file_path(destination_path, source_path)
    try:
        blob_client = blob_service.get_blob_client(container=destination_container, blob=destination_blob_name)
        blob_client.start_copy_from_url(source_url=source_file_url, incremental_copy=False)
        return blob_client.url
    except HttpResponseError as ex:
        error_template = 'Failed to copy share {} to container {}. {}'
        raise CLIError(error_template.format(source_path, destination_container, ex))


def show_blob_v2(cmd, client, **kwargs):
    blob = client.get_blob_properties(**kwargs)

    try:
        page_ranges = None
        if blob.blob_type == cmd.get_models('_models#BlobType', resource_type=ResourceType.DATA_STORAGE_BLOB).PageBlob:
            page_ranges = client.get_page_ranges(**kwargs)

        blob.page_ranges = page_ranges
    except HttpResponseError as ex:
        logger.warning("GetPageRanges failed with status code: %d, message: %s", ex.status_code, ex.message)

    return blob


def set_blob_tier_v2(client, tier, blob_type='block', rehydrate_priority=None, timeout=None):
    if blob_type == 'block':
        return client.set_standard_blob_tier(standard_blob_tier=tier, rehydrate_priority=rehydrate_priority,
                                             timeout=timeout)
    if blob_type == 'page':
        return client.set_premium_page_blob_tier(premium_page_blob_tier=tier, timeout=timeout)
    raise ValueError('Blob tier is only applicable to block or page blob.')


def acquire_blob_lease(client, lease_duration=-1, **kwargs):
    client.acquire(lease_duration=lease_duration, **kwargs)
    return client.id


def renew_blob_lease(client, **kwargs):
    client.renew(**kwargs)
    return client.id


def add_progress_callback_v2(cmd, namespace):
    def _update_progress(response):
        if response.http_response.status_code not in [200, 201]:
            return

        message = getattr(_update_progress, 'message', 'Alive')
        reuse = getattr(_update_progress, 'reuse', False)
        current = response.context['upload_stream_current']
        total = response.context['data_stream_total']

        if total:
            hook.add(message=message, value=current, total_val=total)
            if total == current and not reuse:
                hook.end()

    hook = cmd.cli_ctx.get_progress_controller(det=True)
    _update_progress.hook = hook

    if not namespace.no_progress:
        namespace.progress_callback = _update_progress
    del namespace.no_progress


def query_blob(client, query_expression, input_config=None, output_config=None, result_file=None, **kwargs):
    reader = client.query_blob(query_expression=query_expression, blob_format=input_config, output_format=output_config,
                               **kwargs)

    if result_file is not None:
        with open(result_file, 'wb') as stream:
            reader.readinto(stream)
        stream.close()
        return None

    return reader.readall().decode("utf-8")


def copy_blob(cmd, client, source_url, metadata=None, **kwargs):
    if not kwargs['requires_sync']:
        kwargs.pop('requires_sync')
    blob_type = kwargs.pop('destination_blob_type', None)
    src_client = kwargs.pop('source_client', None)
    if src_client is None:
        src_client = client.from_blob_url(source_url)
        if src_client.account_name == client.account_name:
            src_client = client.from_blob_url(source_url, credential=client.credential)
    StandardBlobTier = cmd.get_models('_models#StandardBlobTier')
    if blob_type is not None and blob_type != 'Detect':
        blob_service_client = src_client._get_container_client()._get_blob_service_client()
        if blob_service_client.credential is not None:
            as_user = True
            if hasattr(blob_service_client.credential, 'account_key'):
                as_user = False
            expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
            source_url = generate_sas_blob_uri(cmd, blob_service_client, full_uri=True, blob_url=source_url,
                                               blob_name=None, container_name=None, as_user=as_user,
                                               expiry=expiry, permission='r')

        params = {"source_if_modified_since": kwargs.get("source_if_modified_since"),
                  "source_if_unmodified_since": kwargs.get("source_if_unmodified_since"),
                  "if_modified_since": kwargs.get("if_modified_since"),
                  "if_unmodified_since": kwargs.get("if_unmodified_since"),
                  "timeout": kwargs.get("timeout")}

        if blob_type == 'AppendBlob':
            params.update({"lease": kwargs.get("destination_lease")})
            client.create_append_blob()
            res = client.append_block_from_url(copy_source_url=source_url, **params)
            return transform_response_with_bytearray(res)
        if blob_type == 'BlockBlob':
            standard_blob_tier = getattr(StandardBlobTier, (kwargs.get("tier"))) if (kwargs.get("tier")) else None
            params.update({"overwrite": True, "tags": kwargs.get("tags"),
                           "destination_lease": kwargs.get("destination_lease"),
                           "standard_blob_tier": standard_blob_tier})
            return client.upload_blob_from_url(source_url=source_url, **params)
        if blob_type == 'PageBlob':
            params.update({"lease": kwargs.get("destination_lease")})
            source_blob_client = client.from_blob_url(source_url)
            blob_length = source_blob_client.get_blob_properties().size
            if blob_length % 512 != 0:
                raise ValueError("Source blob size must be an integer that aligns with 512 page size")
            client.create_page_blob(size=blob_length)
            res = client.upload_pages_from_url(source_url=source_url, offset=0, length=blob_length,
                                               source_offset=0, **params)
            return transform_response_with_bytearray(res)
    if kwargs.get('tier') is not None:
        tier = kwargs.pop('tier')
        try:
            kwargs["standard_blob_tier"] = getattr(StandardBlobTier, tier)
        except AttributeError:
            PremiumPageBlobTier = cmd.get_models('_models#PremiumPageBlobTier')
            kwargs["premium_page_blob_tier"] = getattr(PremiumPageBlobTier, tier)
    return client.start_copy_from_url(source_url=source_url, metadata=metadata, incremental_copy=False, **kwargs)


def exists(client, container_name, blob_name, snapshot, timeout):
    if blob_name:
        client = client.get_blob_client(container=container_name, blob=blob_name, snapshot=snapshot)
    else:
        client = client.get_container_client(container=container_name)
    return client.exists(timeout=timeout)


def incremental_copy_start(client, cmd, copy_source=None, metadata=None,
                           destination_if_modified_since=None, destination_if_unmodified_since=None,
                           destination_if_match=None, destination_if_none_match=None, **kwargs):
    from ..aaz.latest.storage.blob.incremental_copy import Start

    cmd_args = {
        "x_ms_version": "2025-07-05",
        "account_name": client.account_name,
        "destination_blob": client.blob_name,
        "destination_container": client.container_name,
        "source_uri": copy_source,
        "comp": 'incrementalcopy',
        "destination_if_modified_since": destination_if_modified_since,
        "destination_if_unmodified_since": destination_if_unmodified_since,
        "destination_if_match": destination_if_match,
        "destination_if_none_match": destination_if_none_match,
    }
    _Start = Start(cli_ctx=cmd.cli_ctx)

    def on_202(self, session):
        result = dict(session.http_response.headers._store)
        output = {
            "completionTime": None,
            "id": result.get('x-ms-copy-id')[1],
            "progress": None,
            "source": None,
            "status": result.get('x-ms-copy-status')[1],
            "statusDescription": None
        }
        self.ctx.vars._output = output

    _Start.PageBlobCopyIncremental.on_202 = on_202

    _Start(command_args=cmd_args)
    return _Start.ctx.vars._output
