# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from datetime import datetime

from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import sdk_no_wait
from azure.cli.command_modules.storage.url_quote_util import encode_for_url, make_encoded_file_url_and_params
from azure.cli.command_modules.storage.util import (create_blob_service_from_storage_client,
                                                    create_file_share_from_storage_client,
                                                    create_short_lived_share_sas,
                                                    create_short_lived_container_sas,
                                                    filter_none, collect_blobs, collect_blob_objects, collect_files,
                                                    mkdir_p, guess_content_type, normalize_blob_file_path,
                                                    check_precondition_success)
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

    if cmd.supported_api_version(min_api='2019-06-01', resource_type=ResourceType.MGMT_STORAGE):
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
    return client.create(resource_group_name=resource_group_name, account_name=account_name,
                         container_name=container_name, public_access=public_access, metadata=metadata)


def update_container_rm(cmd, instance, metadata=None, public_access=None,
                        default_encryption_scope=None, deny_encryption_scope_override=None,
                        enable_nfs_v3_root_squash=None, enable_nfs_v3_all_squash=None):
    BlobContainer = cmd.get_models('BlobContainer', resource_type=ResourceType.MGMT_STORAGE)
    blob_container = BlobContainer(
        metadata=metadata if metadata is not None else instance.metadata,
        public_access=public_access if public_access is not None else instance.public_access,
        default_encryption_scope=default_encryption_scope
        if default_encryption_scope is not None else instance.default_encryption_scope,
        deny_encryption_scope_override=deny_encryption_scope_override
        if deny_encryption_scope_override is not None else instance.deny_encryption_scope_override,
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
    from azure.core.exceptions import HttpResponseError
    try:
        container = client.get(resource_group_name=resource_group_name,
                               account_name=account_name, container_name=container_name)
        return container is not None
    except HttpResponseError as err:
        if err.status_code == 404:
            return False
        raise err


def create_container(cmd, container_name, resource_group_name=None, account_name=None,
                     metadata=None, public_access=None, fail_on_exist=False, timeout=None,
                     default_encryption_scope=None, prevent_encryption_scope_override=None, **kwargs):
    if default_encryption_scope is not None or prevent_encryption_scope_override is not None:
        from .._client_factory import storage_client_factory
        client = storage_client_factory(cmd.cli_ctx).blob_containers
        BlobContainer = cmd.get_models('BlobContainer', resource_type=ResourceType.MGMT_STORAGE)
        blob_container = BlobContainer(default_encryption_scope=default_encryption_scope,
                                       deny_encryption_scope_override=prevent_encryption_scope_override)
        container = client.create(resource_group_name=resource_group_name, account_name=account_name,
                                  container_name=container_name, blob_container=blob_container)
        return container is not None

    from .._client_factory import blob_data_service_factory
    kwargs['account_name'] = account_name
    client = blob_data_service_factory(cmd.cli_ctx, kwargs)
    return client.create_container(container_name, metadata=metadata, public_access=public_access,
                                   fail_on_exist=fail_on_exist, timeout=timeout)


def delete_container(client, container_name, fail_not_exist=False, lease_id=None, if_modified_since=None,
                     if_unmodified_since=None, timeout=None, bypass_immutability_policy=False,
                     processed_resource_group=None, processed_account_name=None, mgmt_client=None):
    if bypass_immutability_policy:
        mgmt_client.blob_containers.delete(processed_resource_group, processed_account_name, container_name)
        return True
    return client.delete_container(
        container_name, fail_not_exist=fail_not_exist, lease_id=lease_id, if_modified_since=if_modified_since,
        if_unmodified_since=if_unmodified_since, timeout=timeout)


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
    policy = client.get_blob_service_properties().delete_retention_policy

    if enable is not None:
        policy.enabled = enable == 'true'
    if days_retained is not None:
        policy.days = days_retained

    if policy.enabled and not policy.days:
        raise CLIError("must specify days-retained")

    client.set_blob_service_properties(delete_retention_policy=policy)
    return client.get_blob_service_properties().delete_retention_policy


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


def storage_blob_copy_batch(cmd, client, source_client, container_name=None,
                            destination_path=None, source_container=None, source_share=None,
                            source_sas=None, pattern=None, dryrun=False):
    """Copy a group of blob or files to a blob container."""

    if dryrun:
        logger.warning('copy files or blobs to blob container')
        logger.warning('    account %s', client.account_name)
        logger.warning('  container %s', container_name)
        logger.warning('     source %s', source_container or source_share)
        logger.warning('source type %s', 'blob' if source_container else 'file')
        logger.warning('    pattern %s', pattern)
        logger.warning(' operations')

    source_sas = source_sas.lstrip('?') if source_sas else source_sas
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
                return _copy_blob_to_blob_container(client, source_client, container_name, destination_path,
                                                    source_container, source_sas, blob_name)

        return list(filter_none(action_blob_copy(blob) for blob in collect_blobs(source_client,
                                                                                 source_container,
                                                                                 pattern)))

    if source_share:
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
                return _copy_file_to_blob_container(client, source_client, container_name, destination_path,
                                                    source_share, source_sas, dir_name, file_name)

        return list(filter_none(action_file_copy(file) for file in collect_files(cmd,
                                                                                 source_client,
                                                                                 source_share,
                                                                                 pattern)))
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
        results.append(_download_blob(
            client, source_container_name, destination, blob_normed, blobs_to_download[blob_normed]))

    # end progress hook
    if progress_callback:
        progress_callback.hook.end()

    return results


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

    source_files = source_files or []
    t_content_settings = cmd.get_models('blob.models#ContentSettings')

    results = []
    if dryrun:
        logger.info('upload action: from %s to %s', source, destination)
        logger.info('    pattern %s', pattern)
        logger.info('  container %s', destination_container_name)
        logger.info('       type %s', blob_type)
        logger.info('      total %d', len(source_files))
        results = []
        for src, dst in source_files:
            results.append(_create_return_result(dst, guess_content_type(src, content_settings, t_content_settings)))
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

            include, result = _upload_blob(cmd, client, file_path=src, container_name=destination_container_name,
                                           blob_name=normalize_blob_file_path(destination_path, dst),
                                           blob_type=blob_type, content_settings=guessed_content_settings,
                                           metadata=metadata, validate_content=validate_content,
                                           maxsize_condition=maxsize_condition, max_connections=max_connections,
                                           lease_id=lease_id, progress_callback=progress_callback,
                                           if_modified_since=if_modified_since,
                                           if_unmodified_since=if_unmodified_since, if_match=if_match,
                                           if_none_match=if_none_match, timeout=timeout)
            if include:
                results.append(_create_return_result(dst, guessed_content_settings, result))
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
    if not blob_type or blob_type != 'block':
        return

    # increase the block size to 4000MB when the block list will contain more than
    # 50,000 blocks(each block 100MB)
    if length > 50000 * 100 * 1024 * 1024:
        client._config.max_block_size = 4000 * 1024 * 1024
        client._config.max_single_put_size = 5000 * 1024 * 1024


# pylint: disable=too-many-locals
def upload_blob(cmd, client, file_path, container_name=None, blob_name=None, blob_type=None, content_settings=None,
                metadata=None, validate_content=False, maxsize_condition=None, max_connections=2, lease_id=None,
                tier=None, if_modified_since=None, if_unmodified_since=None, if_match=None, if_none_match=None,
                timeout=None, progress_callback=None, encryption_scope=None):
    """Upload a blob to a container."""

    if encryption_scope:
        count = os.path.getsize(file_path)
        with open(file_path, 'rb') as stream:
            data = stream.read(count)
        from azure.core import MatchConditions
        upload_args = {
            'content_settings': content_settings,
            'metadata': metadata,
            'timeout': timeout,
            'if_modified_since': if_modified_since,
            'if_unmodified_since': if_unmodified_since,
            'blob_type': transform_blob_type(cmd, blob_type),
            'validate_content': validate_content,
            'lease': lease_id,
            'max_concurrency': max_connections,
        }

        if cmd.supported_api_version(min_api='2017-04-17') and tier:
            upload_args['premium_page_blob_tier'] = tier
        if maxsize_condition:
            upload_args['maxsize_condition'] = maxsize_condition
        if cmd.supported_api_version(min_api='2016-05-31'):
            upload_args['validate_content'] = validate_content

        # Precondition Check
        if if_match:
            if if_match == '*':
                upload_args['match_condition'] = MatchConditions.IfPresent
            else:
                upload_args['etag'] = if_match
                upload_args['match_condition'] = MatchConditions.IfNotModified

        if if_none_match:
            upload_args['etag'] = if_none_match
            upload_args['match_condition'] = MatchConditions.IfModified
        _adjust_block_blob_size(client, blob_type, length=count)
        response = client.upload_blob(data=data, length=count, encryption_scope=encryption_scope, **upload_args)
        return transform_response_with_bytearray(response)

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

    source_blobs = list(collect_blob_objects(client, source_container_name, pattern))

    if dryrun:
        from datetime import timezone
        delete_blobs = []
        if_modified_since_utc = if_modified_since.replace(tzinfo=timezone.utc) if if_modified_since else None
        if_unmodified_since_utc = if_unmodified_since.replace(tzinfo=timezone.utc) if if_unmodified_since else None
        for blob in source_blobs:
            if not if_modified_since or blob[1].properties.last_modified >= if_modified_since_utc:
                if not if_unmodified_since or blob[1].properties.last_modified <= if_unmodified_since_utc:
                    delete_blobs.append(blob[0])
        logger.warning('delete action: from %s', source)
        logger.warning('    pattern %s', pattern)
        logger.warning('  container %s', source_container_name)
        logger.warning('      total %d', len(delete_blobs))
        logger.warning(' operations')
        for blob in delete_blobs:
            logger.warning('  - %s', blob)
        return []

    results = [result for include, result in (_delete_blob(blob[0]) for blob in source_blobs) if include]
    num_failures = len(source_blobs) - len(results)
    if num_failures:
        logger.warning('%s of %s blobs not deleted due to "Failed Precondition"', num_failures, len(source_blobs))


def generate_sas_blob_uri(client, container_name, blob_name, permission=None,
                          expiry=None, start=None, id=None, ip=None,  # pylint: disable=redefined-builtin
                          protocol=None, cache_control=None, content_disposition=None,
                          content_encoding=None, content_language=None,
                          content_type=None, full_uri=False, as_user=False):
    from ..url_quote_util import encode_url_path
    from urllib.parse import quote
    if as_user:
        user_delegation_key = client.get_user_delegation_key(
            get_datetime_from_string(start) if start else datetime.utcnow(), get_datetime_from_string(expiry))
        sas_token = client.generate_blob_shared_access_signature(
            container_name, blob_name, permission=permission, expiry=expiry, start=start, id=id, ip=ip,
            protocol=protocol, cache_control=cache_control, content_disposition=content_disposition,
            content_encoding=content_encoding, content_language=content_language, content_type=content_type,
            user_delegation_key=user_delegation_key)
    else:
        sas_token = client.generate_blob_shared_access_signature(
            container_name, blob_name, permission=permission, expiry=expiry, start=start, id=id, ip=ip,
            protocol=protocol, cache_control=cache_control, content_disposition=content_disposition,
            content_encoding=content_encoding, content_language=content_language, content_type=content_type)
    if full_uri:
        return encode_url_path(client.make_blob_url(container_name, blob_name, protocol=protocol,
                                                    sas_token=quote(sas_token, safe='&%()$=\',~')))
    return quote(sas_token, safe='&%()$=\',~')


def generate_container_shared_access_signature(client, container_name, permission=None,
                                               expiry=None, start=None, id=None, ip=None,  # pylint: disable=redefined-builtin
                                               protocol=None, cache_control=None, content_disposition=None,
                                               content_encoding=None, content_language=None,
                                               content_type=None, as_user=False):
    user_delegation_key = None
    if as_user:
        user_delegation_key = client.get_user_delegation_key(
            get_datetime_from_string(start) if start else datetime.utcnow(), get_datetime_from_string(expiry))

    return client.generate_container_shared_access_signature(
        container_name, permission=permission, expiry=expiry, start=start, id=id, ip=ip,
        protocol=protocol, cache_control=cache_control, content_disposition=content_disposition,
        content_encoding=content_encoding, content_language=content_language, content_type=content_type,
        user_delegation_key=user_delegation_key)


def create_blob_url(client, container_name, blob_name, protocol=None, snapshot=None):
    return client.make_blob_url(
        container_name, blob_name, protocol=protocol, snapshot=snapshot, sas_token=client.sas_token)


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
        error_template = 'Failed to copy file {} to container {}. {}'
        raise CLIError(error_template.format(source_file_name, destination_container, ex))


def show_blob_v2(cmd, client, lease_id=None, **kwargs):

    blob = client.get_blob_properties(lease=lease_id, **kwargs)

    page_ranges = None
    if blob.blob_type == cmd.get_models('_models#BlobType', resource_type=ResourceType.DATA_STORAGE_BLOB).PageBlob:
        page_ranges = client.get_page_ranges(lease=lease_id, **kwargs)

    blob.page_ranges = page_ranges

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


def copy_blob(client, source_url, metadata=None, **kwargs):
    if not kwargs['requires_sync']:
        kwargs.pop('requires_sync')
    return client.start_copy_from_url(source_url=source_url, metadata=metadata, incremental_copy=False, **kwargs)
