# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import azure.cli.command_modules.sf.custom as sf_c


class SfAppTests(unittest.TestCase):

    def empty_parse_params_returns_empty_test(self):
        self.assertEqual(sf_c.parse_app_params({}), [])

    def none_parse_params_returns_none_test(self):
        self.assertIsNone(sf_c.parse_app_params(None))

    def parse_params_returns_app_param_test(self):
        from azure.servicefabric.models.application_parameter import ApplicationParameter

        res = sf_c.parse_app_params({"tree": "green"})
        self.assertEqual(len(res), 1)
        self.assertIsInstance(res[0], ApplicationParameter)
        self.assertEqual(res[0].key, "tree")
        self.assertEqual(res[0].value, "green")

    def empty_parse_metrics_returns_empty_test(self):
        self.assertEqual(sf_c.parse_app_metrics([]), [])

    def none_parse_metrics_returns_none_test(self):
        self.assertEqual(sf_c.parse_app_metrics(None), None)

    def parse_metrics_returns_metrics_desc_test(self):
        from azure.servicefabric.models.application_metric_description import ApplicationMetricDescription

        res = sf_c.parse_app_metrics([{"name": "derp", "maximum_capacity": 3}])
        self.assertEqual(len(res), 1)
        self.assertIsInstance(res[0], ApplicationMetricDescription)

    def empty_parse_service_health_policy_returns_zeros_test(self):
        from azure.servicefabric.models.service_type_health_policy import ServiceTypeHealthPolicy

        res = sf_c.parse_default_service_health_policy({})
        self.assertIsInstance(res, ServiceTypeHealthPolicy)
        self.assertEqual(res.max_percent_unhealthy_partitions_per_service, 0)
        self.assertEqual(res.max_percent_unhealthy_replicas_per_partition, 0)
        self.assertEqual(res.max_percent_unhealthy_services, 0)

    def none_parse_service_health_policy_returns_none_test(self):
        res = sf_c.parse_default_service_health_policy(None)
        self.assertIs(res, None)
