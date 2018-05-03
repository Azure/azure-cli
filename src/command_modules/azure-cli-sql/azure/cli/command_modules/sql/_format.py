# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict

from azure.mgmt.sql.models import ElasticPoolEdition

from .custom import is_available


def _last_segment(resource_id):
    return resource_id.split('/')[-1] if resource_id else None


_units = [(1024 * 1024 * 1024 * 1024, 'TB'),
          (1024 * 1024 * 1024, 'GB'),
          (1024 * 1024, 'MB'),
          (1024, 'kB'),
          (1, 'B')]


def _bytes_to_friendly_string(b):
    '''
    Formats the specified integer count of bytes as a friendly string
    with units, e.g. 1024 -> "1kB"
    '''

    # Find the largest unit that evenly divides the input
    unit = next(u for u in _units if (b % u[0]) == 0)

    # Format the value with the chosen unit
    return str((b // unit[0])) + unit[1]


###############################################
#                sql db                       #
###############################################


def db_list_transform(results):
    return [db_show_transform(r) for r in results]


def db_show_transform(result):
    '''
    Transforms the json response for a database.
    '''

    # Add properties in order to improve backwards compatibility with api-version 2014-04-01
    result.edition = result.sku.tier
    result.elastic_pool_name = _last_segment(result.elastic_pool_id)

    return result


def db_list_table_format(results):
    '''
    Formats a list of databases as summary results for display with "-o table".
    '''

    return [_db_table_format(r) for r in results]


def db_show_table_format(result):
    '''
    Formats a database as summary results for display with "-o table".
    '''

    return [_db_table_format(result)]


def _db_table_format(result):
    '''
    Formats a database as summary results for display with "-o table".
    '''

    return OrderedDict([
        ('name', result['name']),
        ('tier', result['sku']['tier']),
        ('family', result['sku']['family'] or ' '),
        ('capacity', result['sku']['capacity'] or ' '),
        ('maxSize', _bytes_to_friendly_string(result['maxSizeBytes'])),
        ('elasticPool', _last_segment(result['elasticPoolId']) or ' '),
    ])


def db_edition_list_table_format(editions):
    '''
    Formats a list of database editions as summary results for display with "-o table".
    '''

    return list(_db_edition_list_table_format(editions))


def _db_edition_list_table_format(editions):
    '''
    Formats a database edition as summary results for display with "-o table".
    '''

    for e in editions:
        for slo in e['supportedServiceLevelObjectives']:
            sku = slo['sku']
            yield OrderedDict([
                ('serviceObjective', slo['name']),
                ('edition', e['name']),
                # Dummy ' ' value ensures that value is not skipped, which
                # would cause the column to not show up in the correct order
                ('family', sku['family'] or ' '),
                ('capacity', sku['capacity']),
                ('unit', slo['performanceLevel']['unit']),
                ('available', is_available(slo['status'])),
            ])


###############################################
#                sql elastic-pool             #
###############################################


def elastic_pool_list_transform(results):
    return [elastic_pool_show_transform(r) for r in results]


def elastic_pool_show_transform(result):
    '''
    Transforms the json response for an elastic pool.
    '''

    # Add properties in order to improve backwards compatibility with api-version 2014-04-01
    result.edition = result.sku.tier
    result.storageMb = result.max_size_bytes / 1024 / 1024

    is_dtu = result.sku.tier in (
        ElasticPoolEdition.basic.value,
        ElasticPoolEdition.standard.value,
        ElasticPoolEdition.premium.value)

    result.dtu = result.sku.capacity if is_dtu else None
    result.database_dtu_min = int(result.per_database_settings.min_capacity) if is_dtu else None
    result.database_dtu_max = int(result.per_database_settings.max_capacity) if is_dtu else None

    return result


def elastic_pool_list_table_format(results):
    '''
    Formats a list of elastic pools as summary results for display with "-o table".
    '''

    return [_elastic_pool_table_format(r) for r in results]


def elastic_pool_show_table_format(result):
    '''
    Formats an elastic pool as summary results for display with "-o table".
    '''

    return [_elastic_pool_table_format(result)]


def _elastic_pool_table_format(result):
    '''
    Formats an elastic pool as summary results for display with "-o table".
    '''

    return OrderedDict([
        ('name', result['name']),
        ('tier', result['sku']['tier']),
        ('family', result['sku']['family'] or ' '),
        ('capacity', result['sku']['capacity'] or ' '),
        ('maxSize', _bytes_to_friendly_string(result['maxSizeBytes']))
    ])


def elastic_pool_edition_list_table_format(editions):
    '''
    Formats a list of elastic pool editions as summary results for display with "-o table".
    '''

    return list(_elastic_pool_edition_list_table_format(editions))


def _elastic_pool_edition_list_table_format(editions):
    '''
    Formats an elastic pool editions as summary results for display with "-o table".
    '''

    for e in editions:
        for slo in e['supportedElasticPoolPerformanceLevels']:
            sku = slo['sku']
            yield OrderedDict([
                ('edition', e['name']),
                # Dummy ' ' value ensures that value is not skipped, which
                # would cause the column to not show up in the correct order
                ('family', sku['family'] or ' '),
                ('capacity', sku['capacity']),
                ('unit', slo['performanceLevel']['unit']),
                ('available', is_available(slo['status'])),
            ])
