# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

logger = get_logger(__name__)


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
    else:
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


def generate_sas(client, table_name, permission=None, expiry=None, start=None, id=None,
                 ip=None, protocol=None, start_pk=None, start_rk=None, end_pk=None, end_rk=None):
    from azure.data.tables._table_shared_access_signature import generate_table_sas
    return generate_table_sas(client.credential, table_name, permission=permission, expiry=expiry, start=start,
                              policy_id=id, ip_address_or_range=ip, protocol=protocol,
                              start_pk=start_pk, start_rk=start_rk, end_pk=end_pk, end_rk=end_rk)


def insert_table_entity(client, entity, if_exists='fail'):
    if if_exists == 'fail':
        return client.upsert_entity(entity, mode='merge')
    if if_exists == 'merge' or if_exists == 'replace':
        return client.upsert_entity(entity, mode=if_exists)
    from knack.util import CLIError
    raise CLIError("Unrecognized value '{}' for --if-exists".format(if_exists))


def _update_table_entity(client, entity, mode, if_match='*'):
    if not if_match or if_match == '*':
        return client.update_entity(entity, mode)
    else:
        from azure.core import MatchConditions
        return client.update_entity(entity, mode, etag=if_match, match_condition=MatchConditions.IfNotModified)


def replace_table_entity(client, entity, if_match='*'):
    return _update_table_entity(client, entity, mode='replace', if_match=if_match)


def merge_table_entity(client, entity, if_match='*'):
    return _update_table_entity(client, entity, mode='merge', if_match=if_match)


def delete_table_entity(client, partition_key, row_key, if_match='*'):
    if not if_match or if_match == '*':
        return client.delete_entity(partition_key=partition_key, row_key=row_key)
    else:
        from azure.core import MatchConditions
        return client.delete_entity(partition_key=partition_key, row_key=row_key, etag=if_match, match_condition=MatchConditions.IfNotModified)


def query_table_entity(client, filter=None, select=None, num_results=None, marker=None):
    def _convert_marker_to_ct(marker):
        if not marker:
            return None
        ct = {
            'PartitionKey': marker.get('nextpartitionkey'),
            'RowKey': marker.get('nextrowkey')
        }
        return ct

    def _convert_ct_to_next_marker(ct):
        if not ct:
            return {}
        marker = {
            'nextpartitionkey': ct.get('PartitionKey'),
            'nextrowkey': ct.get('RowKey')
        }
        return marker

    from ..track2_util import list_generator
    generator = client.query_entities(query_filter=filter, results_per_page=num_results, select=select)
    pages = generator.by_page(continuation_token=_convert_marker_to_ct(marker))
    items = list_generator(pages=pages, num_results=num_results)

    result = {
        'items': items,
        'nextMarker': _convert_ct_to_next_marker(pages.continuation_token)
    }
    return result
