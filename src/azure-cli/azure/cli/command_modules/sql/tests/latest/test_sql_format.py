# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.mgmt.sql.models import ElasticPool, ElasticPoolPerDatabaseSettings, Sku

from azure.cli.command_modules.sql._format import elastic_pool_list_transform, elastic_pool_transform
from azure.cli.core.util import todict


class SqlElasticPoolTransformTest(unittest.TestCase):
    # SQL SDK 5.0 must preserve the legacy calculated output without mutating generated models.

    def test_dtu_pool_preserves_compatibility_fields_after_serialization(self):
        for tier in ('Basic', 'Standard', 'Premium'):
            with self.subTest(tier=tier):
                pool = ElasticPool(
                    location='indiasouthcentral', sku=Sku(name=tier + 'Pool', tier=tier, capacity=125),
                    max_size_bytes=53687091200,
                    per_database_settings=ElasticPoolPerDatabaseSettings(min_capacity=0, max_capacity=50))

                result = todict(elastic_pool_transform(pool))

                self.assertEqual(result['edition'], tier)
                self.assertEqual(result['storageMb'], 51200)
                self.assertEqual(result['dtu'], 125)
                self.assertEqual(result['databaseDtuMin'], 0)
                self.assertEqual(result['databaseDtuMax'], 50)
                self.assertEqual(result['sku']['tier'], tier)
                self.assertEqual(result['perDatabaseSettings']['maxCapacity'], 50)

    def test_vcore_pool_list_does_not_expose_vcores_as_dtus(self):
        pools = [
            ElasticPool(
                location='indiasouthcentral', sku=Sku(name='GP_Gen5', tier='GeneralPurpose', capacity=2),
                max_size_bytes=34359738368,
                per_database_settings=ElasticPoolPerDatabaseSettings(min_capacity=0, max_capacity=2)),
            ElasticPool(
                location='indiasouthcentral', sku=Sku(name='PremiumPool', tier='Premium', capacity=125),
                max_size_bytes=53687091200,
                per_database_settings=ElasticPoolPerDatabaseSettings(min_capacity=0, max_capacity=50)),
        ]

        result = todict(elastic_pool_list_transform(pools))

        self.assertEqual(result[0]['edition'], 'GeneralPurpose')
        self.assertEqual(result[0]['storageMb'], 32768)
        self.assertIsNone(result[0]['dtu'])
        self.assertIsNone(result[0]['databaseDtuMin'])
        self.assertIsNone(result[0]['databaseDtuMax'])
        self.assertEqual(result[1]['edition'], 'Premium')
        self.assertEqual(result[1]['dtu'], 125)
