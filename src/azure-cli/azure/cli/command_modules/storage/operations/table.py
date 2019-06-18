# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def insert_table_entity(client, table_name, entity, if_exists='fail', timeout=None):
    if if_exists == 'fail':
        return client.insert_entity(table_name, entity, timeout)
    if if_exists == 'merge':
        return client.insert_or_merge_entity(table_name, entity, timeout)
    if if_exists == 'replace':
        return client.insert_or_replace_entity(table_name, entity, timeout)
    from knack.util import CLIError
    raise CLIError("Unrecognized value '{}' for --if-exists".format(if_exists))
