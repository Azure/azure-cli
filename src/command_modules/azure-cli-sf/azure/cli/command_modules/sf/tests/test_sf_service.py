# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import azure.cli.command_modules.sf.custom as sf_c
from knack.util import CLIError


# pylint: disable=too-many-public-methods
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
        from azure.servicefabric.models.service_placement_prefer_primary_domain_policy_description import (
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

    def none_move_cost_valid_test(self):  # pylint: disable=no-self-use
        sf_c.sup_validate_move_cost(None)

    def none_stateful_flags_returns_zero_test(self):
        self.assertEqual(sf_c.sup_stateful_flags(None, None, None), 0)

    def all_stateful_flags_returns_seven_test(self):
        self.assertEqual(sf_c.sup_stateful_flags("10", "30", "50"), 7)

    def none_service_update_flags_returns_zero_test(self):
        self.assertEqual(sf_c.sup_service_update_flags(), "0")

    def either_instance_count_or_target_replica_set_size_are_considered_update_flags_test(self):
        with_instance = sf_c.sup_service_update_flags(instance_count=-1)
        with_target = sf_c.sup_service_update_flags(target_rep_size=30)
        self.assertEqual(with_instance, with_target)

    def service_create_missing_service_type_raises_cli_error_test(self):
        with self.assertRaises(CLIError):
            sf_c.validate_service_create_params(False, False, True, False, False, -1, None, None)

    def service_create_missing_partition_scheme_raises_cli_error_test(self):
        with self.assertRaises(CLIError):
            sf_c.validate_service_create_params(True, False, False, False, False, None, 7, 5)

    def service_create_missing_instance_count_raises_cli_error_test(self):
        with self.assertRaises(CLIError):
            sf_c.validate_service_create_params(False, True, True, False, False, None, None, None)

    def service_create_partition_policy_none_returns_none_test(self):
        self.assertIs(sf_c.parse_partition_policy(None, None, None, None, None, None, None), None)

    def service_create_partition_policy_no_named_list_raises_cli_error_test(self):
        with self.assertRaises(CLIError):
            sf_c.parse_partition_policy(True, None, None, None, None, None, None)

    def service_create_partition_policy_incomplete_int_scheme_raises_cli_error_test(self):
        with self.assertRaises(CLIError):
            sf_c.parse_partition_policy(None, None, True, 3, None, 100, None)

    def invalid_activation_mode_raises_cli_error_test(self):
        with self.assertRaises(CLIError):
            sf_c.validate_activation_mode("derp")

    def service_update_invalid_instance_count_raises_cli_error_test(self):
        with self.assertRaises(CLIError):
            sf_c.validate_update_service_params(False, True, None, None, None, None, None, 10)

    def service_update_invalid_replica_restart_wait_raises_cli_error_test(self):
        with self.assertRaises(CLIError):
            sf_c.validate_update_service_params(True, False, None, None, 10, None, None, None)

    def none_health_app_type_policy_returns_none_test(self):
        self.assertIs(sf_c.parse_app_health_map(None), None)

    def empty_health_app_type_policy_returns_none_test(self):
        self.assertIs(sf_c.parse_app_health_map([]), None)

    def single_health_app_type_policy_returns_single_test(self):
        # pylint: disable=line-too-long
        from azure.servicefabric.models.application_type_health_policy_map_item import (  # noqa: justification, no way to shorten
            ApplicationTypeHealthPolicyMapItem
        )

        res = sf_c.parse_app_health_map([{"key": "derp_app", "value": 10}])
        self.assertEqual(len(res), 1)
        self.assertIsInstance(res[0], ApplicationTypeHealthPolicyMapItem)
        self.assertEqual(res[0].key, "derp_app")
        self.assertEqual(res[0].value, 10)
