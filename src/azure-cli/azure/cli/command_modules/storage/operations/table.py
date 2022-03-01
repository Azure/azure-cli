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


def insert_table_entity(client, table_name, entity, if_exists='fail', timeout=None):
    if if_exists == 'fail':
        return client.insert_entity(table_name, entity, timeout)
    if if_exists == 'merge':
        return client.insert_or_merge_entity(table_name, entity, timeout)
    if if_exists == 'replace':
        return client.insert_or_replace_entity(table_name, entity, timeout)
    from knack.util import CLIError
    raise CLIError("Unrecognized value '{}' for --if-exists".format(if_exists))
