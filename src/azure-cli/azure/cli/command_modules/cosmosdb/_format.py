# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict


def list_database_output(result):
    table = []
    for item in result:
        table.append(database_output(item))
    return table


def database_output(result):
    result = OrderedDict([('Database Id', result['id']),
                          ('_colls', result['_colls']),
                          ('_etag', result['_etag']),
                          ('_rid', result['_rid']),
                          ('_self', result['_self']),
                          ('_ts', result['_ts']),
                          ('_users', result['_users'])])
    return result


def list_collection_output(result):
    table = []
    for item in result:
        table.append(collection_output_helper(item))
    return table


def collection_output(result):
    return collection_output_helper(result['collection'])


def collection_output_helper(result):
    result = OrderedDict([('Collection Id', result['id']),
                          ('_conflicts', result['_conflicts']),
                          ('_docs', result['_docs']),
                          ('_etag', result['_etag']),
                          ('_rid', result['_rid']),
                          ('_self', result['_self']),
                          ('_sprocs', result['_sprocs']),
                          ('_triggers', result['_triggers']),
                          ('_ts', result['_ts'])])
    return result


def list_connection_strings_output(result):
    table = []
    for item in result['connectionStrings']:
        table.append(item)
    return table
