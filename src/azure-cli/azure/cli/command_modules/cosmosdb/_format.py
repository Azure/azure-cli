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


def mc_cluster_status_output_table(result):
    # iterate on dataCenters, skip connectionErrors and reaperStatus in table output
    return mc_status_dataCenters(result['dataCenters'])


def mc_status_dataCenters(dataCenters):
    dataCentersTable = []
    for dc in dataCenters:
        nodeTable = mc_status_nodes(dc['nodes'], dc['name'])
        for row in nodeTable:
            dataCentersTable.append(row)

    return dataCentersTable


def mc_status_nodes(nodes, dataCenterName):
    table = []
    for node in nodes:
        table.append(mc_status_node(node, dataCenterName))
    return table


def mc_status_node(node, dataCenterName):
    # include dataCenterName in each formated node
    result = OrderedDict([
                        ('dataCenterName', dataCenterName),
                        ('nodeAddress', node['address']),
                        ('rack', node['rack']),
                        ('size', node['size']),
                        ('state', node['state']),
                        ('status', node['status']),
                        ('cassandraProcessStatus', node['cassandraProcessStatus']),
                        ('load', node['load']),
                        ('cpuUsage', node['cpuUsage']),
                        ('diskUsedKb', node['diskUsedKb']),
                        ('diskFreeKb', node['diskFreeKb']),
                        ('memoryBuffersAndCachedKb', node['memoryBuffersAndCachedKb']),
                        ('memoryUsedKb', node['memoryUsedKb']),
                        ('memoryFreeKb', node['memoryFreeKb']),
                        ('memoryTotalKb', node['memoryTotalKb']),
                        ('hostId', node['hostId']),
                        ('timestamp', node['timestamp'])])
    return result
