# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import azure.cli.command_modules.sf.custom as sf_c
from azure.cli.core.util import CLIError


class SfServiceTests(unittest.TestCase):

    def none_correlation_scheme_returns_none_test(self):
        self.assertIs(sf_c.sup_correlation_scheme(None, None), None)

    def partial_correlation_scheme_raises_cli_error_test(self):
        with self.assertRaises(CLIError):
            sf_c.sup_correlation_scheme("svc_a", None)

    def valid_correlation_scheme_returns_valid_test(self):
        from azure.servicefabric.models.service_correlation_description import (
            ServiceCorrelationDescription
        )

        res = sf_c.sup_correlation_scheme("svc_a", "pattern")
        self.assertIsInstance(res, ServiceCorrelationDescription)
        self.assertEqual(res.scheme, "pattern")
        self.assertEqual(res.service_name, "svc_a")

    def none_load_metrics_returns_none_test(self):
        self.assertIs(sf_c.sup_load_metrics(None), None)

    def empty_load_metrics_returns_none_test(self):
        self.assertIs(sf_c.sup_load_metrics([]), None)

    def valid_load_metrics_returns_valid_test(self):
        from azure.servicefabric.models.service_load_metric_description import (
            ServiceLoadMetricDescription
        )

        res = sf_c.sup_load_metrics([{"name": "derp", "weight": "low",
                                      "default_load": 15}])

        self.assertEqual(len(res), 1)
        self.assertIsInstance(res[0], ServiceLoadMetricDescription)
        self.assertEqual(res[0].name, "derp")
        self.assertEqual(res[0].default_load, 15)
        self.assertEqual(res[0].weight, "low")
