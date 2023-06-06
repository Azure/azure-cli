# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

from azure.cli.core.profiles import ResourceType

logger = get_logger(__name__)


def list_queues(client, include_metadata=False, marker=None, num_results=None,
                prefix=None, show_next_marker=None, **kwargs):
    from ..track2_util import list_generator
    generator = client.list_queues(name_starts_with=prefix, include_metadata=include_metadata,
                                   results_per_page=num_results, **kwargs)
    pages = generator.by_page(continuation_token=marker)
    result = list_generator(pages=pages, num_results=num_results)

    if show_next_marker:
        next_marker = {"nextMarker": pages.continuation_token}
        result.append(next_marker)
    else:
        if pages.continuation_token:
            logger.warning('Next Marker:')
            logger.warning(pages.continuation_token)

    return result


def queue_exists(cmd, client, **kwargs):
    from azure.core.exceptions import HttpResponseError
    try:
        client.get_queue_properties(**kwargs)
        return True
    except HttpResponseError as ex:
        from azure.cli.command_modules.storage.track2_util import _dont_fail_on_exist
        StorageErrorCode = cmd.get_models("_shared.models#StorageErrorCode",
                                          resource_type=ResourceType.DATA_STORAGE_QUEUE)
        return _dont_fail_on_exist(ex, StorageErrorCode.queue_not_found)


def generate_queue_sas(cmd, client, permission=None, expiry=None, start=None,
                       policy_id=None, ip=None, protocol=None):
    generate_queue_sas_fn = cmd.get_models('_shared_access_signature#generate_queue_sas')

    sas_kwargs = {'protocol': protocol}
    sas_token = generate_queue_sas_fn(account_name=client.account_name, queue_name=client.queue_name,
                                      account_key=client.credential.account_key, permission=permission,
                                      expiry=expiry, start=start, policy_id=policy_id, ip=ip, **sas_kwargs)

    return sas_token


def create_queue(cmd, client, metadata=None, fail_on_exist=False, timeout=None, **kwargs):
    from azure.core.exceptions import HttpResponseError
    try:
        client.create_queue(metadata=metadata, timeout=timeout, **kwargs)
        return True
    except HttpResponseError as ex:
        from azure.cli.command_modules.storage.track2_util import _dont_fail_on_exist
        StorageErrorCode = cmd.get_models("_shared.models#StorageErrorCode",
                                          resource_type=ResourceType.DATA_STORAGE_QUEUE)
        if not fail_on_exist:
            return _dont_fail_on_exist(ex, StorageErrorCode.queue_already_exists)
        raise ex


def delete_queue(cmd, client, fail_not_exist=False, timeout=None, **kwargs):
    from azure.core.exceptions import HttpResponseError
    try:
        client.delete_queue(timeout=timeout, **kwargs)
        return True
    except HttpResponseError as ex:
        from azure.cli.command_modules.storage.track2_util import _dont_fail_on_exist
        StorageErrorCode = cmd.get_models("_shared.models#StorageErrorCode",
                                          resource_type=ResourceType.DATA_STORAGE_QUEUE)
        if not fail_not_exist:
            return _dont_fail_on_exist(ex, StorageErrorCode.queue_not_found)
        raise ex


def receive_messages(client, **kwargs):
    page_iter = client.receive_messages(**kwargs).by_page()
    try:
        page = next(page_iter)
    except StopIteration:
        return []
    return list(page)
