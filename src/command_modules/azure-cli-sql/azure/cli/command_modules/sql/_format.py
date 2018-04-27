# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .custom import is_available

from collections import OrderedDict

class DbEditionTableRow(object):  # pylint: disable=too-few-public-methods

    def __init__(self, edition, sku, status):

        self.edition = edition
        self.sku = sku
        self.status = status


###############################################
#                sql db                       #
###############################################


def db_list_table_format(results):
    """"Format a list of daabases as summary results for display with "-o table"."""
    return [_db_table_format(r) for r in results]


def db_show_table_format(result):
    """Format a database as summary results for display with "-o table"."""
    return [_db_table_format(result)]


def _db_table_format(result):
    return OrderedDict([
        ('name', result['name']),
        ('tier', result['sku']['tier']),
        ('family', result['sku']['family'] or ' '),
        ('capacity', result['sku']['capacity'] or ' '),
        ('maxSizeBytes', result['maxSizeBytes']),
        ('elasticPool', result['elasticPoolId'].split('/')[-1] if result['elasticPoolId'] else ' '),
    ])


def db_edition_list_table_format(editions):
    """"Format a list of editions as summary results for display with "-o table"."""
    return list(_db_edition_list_table_format(editions))


def _db_edition_list_table_format(editions):
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

def elastic_pool_list_table_format(results):
    """"Format a list of daabases as summary results for display with "-o table"."""
    return [_elastic_pool_table_format(r) for r in results]


def elastic_pool_show_table_format(result):
    """Format a database as summary results for display with "-o table"."""
    return [_elastic_pool_table_format(result)]


def _elastic_pool_table_format(result):
    return OrderedDict([
        ('name', result['name']),
        ('tier', result['sku']['tier']),
        ('family', result['sku']['family'] or ' '),
        ('capacity', result['sku']['capacity'] or ' '),
        ('maxSizeBytes', result['maxSizeBytes'])
    ])


def elastic_pool_edition_list_table_format(editions):
    """"Format a list of editions as summary results for display with "-o table"."""
    return list(_elastic_pool_edition_list_table_format(editions))


def _elastic_pool_edition_list_table_format(editions):
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
