# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

logger = get_logger(__name__)


def insert_table_entity(client, table_name, entity, if_exists='fail', timeout=None):
    if if_exists == 'fail':
        return client.insert_entity(table_name, entity, timeout)
    if if_exists == 'merge':
        return client.insert_or_merge_entity(table_name, entity, timeout)
    if if_exists == 'replace':
        return client.insert_or_replace_entity(table_name, entity, timeout)
    from knack.util import CLIError
    raise CLIError("Unrecognized value '{}' for --if-exists".format(if_exists))


def create_table(client, table_name, fail_on_exist=False):
    if fail_on_exist:
        client.create_table(table_name)
    else:
        client.create_table_if_not_exists(table_name)
    return True


def delete_table(client, table_name, fail_not_exist=False):
    if exists(client, table_name):
        client.delete_table(table_name)
        return True
    if fail_not_exist:
        from azure.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("The specified resource does not exist.")
    return False


def list_tables(client, num_results=None, marker=None, show_next_marker=None):
    from ..track2_util import list_generator
    generator = client.list_tables(results_per_page=num_results)
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


def exists(client, table_name):
    generator = client.query_tables("TableName eq '{}'".format(table_name))
    return list(next(generator.by_page())) != []


# pylint: disable=redefined-builtin
def generate_sas(client, table_name, permission=None, expiry=None, start=None, id=None,
                 ip=None, protocol=None, start_pk=None, start_rk=None, end_pk=None, end_rk=None):
    from azure.data.tables._table_shared_access_signature import generate_table_sas
    return generate_table_sas(client.credential, table_name, permission=permission, expiry=expiry, start=start,
                              policy_id=id, ip_address_or_range=ip, protocol=protocol,
                              start_pk=start_pk, start_rk=start_rk, end_pk=end_pk, end_rk=end_rk)


def insert_entity(client, entity, if_exists='fail'):
    from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError
    if if_exists == 'fail':
        partition_key = entity.get('PartitionKey')
        row_key = entity.get('RowKey')
        try:
            client.get_entity(partition_key, row_key)
            raise ResourceExistsError("The specified entity already exists.")
        except ResourceNotFoundError:
            return client.upsert_entity(entity)
    if if_exists == 'merge' or if_exists == 'replace':
        return client.upsert_entity(entity, mode=if_exists)
    from knack.util import CLIError
    raise CLIError("Unrecognized value '{}' for --if-exists".format(if_exists))


def _update_entity(client, entity, mode, if_match='*'):
    if not if_match or if_match == '*':
        return client.update_entity(entity, mode)
    from azure.core import MatchConditions
    return client.update_entity(entity, mode, etag=if_match, match_condition=MatchConditions.IfNotModified)


def replace_entity(client, entity, if_match='*'):
    return _update_entity(client, entity, mode='replace', if_match=if_match)


def merge_entity(client, entity, if_match='*'):
    return _update_entity(client, entity, mode='merge', if_match=if_match)


def delete_entity(client, partition_key, row_key, if_match='*'):
    if not if_match or if_match == '*':
        return client.delete_entity(partition_key=partition_key, row_key=row_key)
    from azure.core import MatchConditions
    return client.delete_entity(partition_key=partition_key, row_key=row_key,
                                etag=if_match, match_condition=MatchConditions.IfNotModified)


# pylint: disable=redefined-builtin
def query_entity(client, filter=None, select=None, num_results=None, marker=None):
    def _convert_marker_to_continuation_token(mk):
        if not mk:
            return None
        ct = {
            'PartitionKey': mk.get('nextpartitionkey'),
            'RowKey': mk.get('nextrowkey')
        }
        return ct

    def _convert_continuation_token_to_next_marker(ct):
        if not ct:
            return {}
        mk = {
            'nextpartitionkey': ct.get('PartitionKey'),
            'nextrowkey': ct.get('RowKey')
        }
        return mk

    from ..track2_util import list_generator
    generator = client.query_entities(query_filter=filter, results_per_page=num_results, select=select)
    pages = generator.by_page(continuation_token=_convert_marker_to_continuation_token(marker))
    items = list_generator(pages=pages, num_results=num_results)

    result = {
        'items': items,
        'nextMarker': _convert_continuation_token_to_next_marker(pages.continuation_token)
    }
    return result
