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

    def none_placement_policies_returns_none_test(self):
        self.assertIs(sf_c.sup_placement_policies(None), None)

    def empty_placement_policies_returns_none_test(self):
        self.assertIs(sf_c.sup_placement_policies([]), None)

    def single_valid_placement_policy_returns_single_policy_test(self):
        # pylint: disable=line-too-long
        from azure.servicefabric.models.service_placement_prefer_primary_domain_policy_description import (  # noqa: justification, no way to shorten
            ServicePlacementPreferPrimaryDomainPolicyDescription
        )

        req = [{"type": "PreferPrimaryDomain", "domain_name": "test_a"}]
        res = sf_c.sup_placement_policies(req)

        self.assertEqual(len(res), 1)
        self.assertIsInstance(res[0], ServicePlacementPreferPrimaryDomainPolicyDescription)
        self.assertEqual(res[0].domain_name, "test_a")

    def invalid_move_cost_raises_cli_error_test(self):
        with self.assertRaises(CLIError):
            sf_c.sup_validate_move_cost("Derp")

    def none_move_cost_valid_test(self):
        sf_c.sup_validate_move_cost(None)

    def none_stateful_flags_returns_zero_test(self):
        self.assertEqual(sf_c.sup_stateful_flags(None, None, None), 0)

    def all_stateful_flags_returns_seven_test(self):
        self.assertEqual(sf_c.sup_stateful_flags("10", "30", "50"), 7)

    def none_service_update_flags_returns_zero_test(self):
        self.assertEqual(sf_c.sup_service_update_flags(), "0")

    def either_instance_count_or_target_replica_set_size_are_considered_update_test(self):
        with_instance = sf_c.sup_service_update_flags(instance_count=-1)
        with_target = sf_c.sup_service_update_flags(target_rep_size=30)
        self.assertEqual(with_instance, with_target)
