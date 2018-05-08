# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import LongRunningOperation


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


class LongRunningOperationResultTransform(LongRunningOperation):  # pylint: disable=too-few-public-methods
    '''
    Long-running operation poller that also transforms the json response.
    '''
    def __init__(self, cli_ctx, transform_func):
        super(LongRunningOperationResultTransform, self).__init__(cli_ctx)
        self._transform_func = transform_func

    def __call__(self, result):
        '''
        Function call operator which will do polling (if necessary)
        and then transforms the result.
        '''

        if result is None:
            return None

        from azure.cli.core.util import poller_classes
        if isinstance(result, poller_classes()):
            # Poll for long-running operation result result by calling base class
            result = super(LongRunningOperationResultTransform, self).__call__(result)

        # Apply transform function
        return self._transform_func(result)


###############################################
#                sql db                       #
###############################################


#####
#           sql db transformers for json
#####


def db_list_transform(results):
    '''
    Transforms the json response for a list of databases.
    '''

    return [db_show_transform(r) for r in results]


def db_show_transform(result):
    '''
    Transforms the json response for a database.
    '''

    # Add properties in order to improve backwards compatibility with api-version 2014-04-01
    result.edition = result.sku.tier
    result.elastic_pool_name = _last_segment(result.elastic_pool_id)

    return result


#####
#           sql db table formatters
#####


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
    from collections import OrderedDict

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
    from .custom import is_available
    from collections import OrderedDict

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


#####
#           sql elastic-pool transformers for json
#####


def elastic_pool_list_transform(results):
    return [elastic_pool_show_transform(r) for r in results]


def elastic_pool_show_transform(result):
    '''
    Transforms the json response for an elastic pool.
    '''
    from azure.mgmt.sql.models import ElasticPoolEdition

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


#####
#           sql elastic-pool table formatters
#####


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
    from collections import OrderedDict

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
    from collections import OrderedDict
    from .custom import is_available

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
