# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest.mock import Mock
from azure.cli.command_modules.acs.agentpool_decorator import AKSAgentPoolContext, AKSAgentPoolParamDict
from azure.cli.command_modules.acs._consts import AgentPoolDecoratorMode, DecoratorMode
from azure.cli.core.azclierror import InvalidArgumentValueError, MutuallyExclusiveArgumentError
from types import SimpleNamespace
import tempfile
import json
from knack.util import CLIError

kubeDnsOverridesExpected = {
        ".": {
            "cacheDurationInSeconds": 3600,
            "forwardDestination": "ClusterCoreDNS",
            "forwardPolicy": "Sequential",
            "maxConcurrent": 1000,
            "protocol": "PreferUDP",
            "queryLogging": "Error",
            "serveStale": "Verify",
            "serveStaleDurationInSeconds": 3600
        },
        "cluster.local": {
            "cacheDurationInSeconds": 3600,
            "forwardDestination": "ClusterCoreDNS",
            "forwardPolicy": "Sequential",
            "maxConcurrent": 1000,
            "protocol": "ForceTCP",
            "queryLogging": "Error",
            "serveStale": "Immediate",
            "serveStaleDurationInSeconds": 3600
        }
    }

kubeDnsOverridesExpectedDefault = {
     ".": {
         "cacheDurationInSeconds": 3600,
         "forwardDestination": "ClusterCoreDNS",
         "forwardPolicy": "Sequential",
         "maxConcurrent": 1000,
         "protocol": "PreferUDP",
         "queryLogging": "Error",
         "serveStale": "Immediate",
         "serveStaleDurationInSeconds": 3600
      },
      "cluster.local": {
         "cacheDurationInSeconds": 3600,
         "forwardDestination": "ClusterCoreDNS",
         "forwardPolicy": "Sequential",
         "maxConcurrent": 1000,
         "protocol": "ForceTCP",
         "queryLogging": "Error",
         "serveStale": "Immediate",
         "serveStaleDurationInSeconds": 3600
      }
}

vnetDnsOverridesExpected = {
        ".": {
            "cacheDurationInSeconds": 3600,
            "forwardDestination": "VnetDNS",
            "forwardPolicy": "Sequential",
            "maxConcurrent": 1000,
            "protocol": "PreferUDP",
            "queryLogging": "Error",
            "serveStale": "Verify",
            "serveStaleDurationInSeconds": 3600
        },
        "cluster.local": {
            "cacheDurationInSeconds": 3600,
            "forwardDestination": "ClusterCoreDNS",
            "forwardPolicy": "Sequential",
            "maxConcurrent": 1000,
            "protocol": "ForceTCP",
            "queryLogging": "Error",
            "serveStale": "Immediate",
            "serveStaleDurationInSeconds": 3600
        }
    }

vnetDnsOverridesExpectedDefault = {
     ".": {
         "cacheDurationInSeconds": 3600,
         "forwardDestination": "VnetDNS",
         "forwardPolicy": "Sequential",
         "maxConcurrent": 1000,
         "protocol": "PreferUDP",
         "queryLogging": "Error",
         "serveStale": "Immediate",
         "serveStaleDurationInSeconds": 3600
      },
      "cluster.local": {
         "cacheDurationInSeconds": 3600,
         "forwardDestination": "ClusterCoreDNS",
         "forwardPolicy": "Sequential",
         "maxConcurrent": 1000,
         "protocol": "ForceTCP",
         "queryLogging": "Error",
         "serveStale": "Immediate",
         "serveStaleDurationInSeconds": 3600
      }
}

def assert_dns_overrides_equal(actual, expected):
    """Assert that all keys and subkeys in expected are present and equal in actual, case-insensitive for keys."""
    # Lowercase all keys in actual and expected for comparison
    def lower_keys(d):
        return {k.lower(): {sk.lower(): sv for sk, sv in v.items()} for k, v in d.items()}
    actual_lower = lower_keys(actual)
    expected_lower = lower_keys(expected)

    for key, expected_subdict in expected_lower.items():
        assert key in actual_lower, f"Missing key: {key} in actual local DNS profile"
        for subkey, subval in expected_subdict.items():
            assert subkey in actual_lower[key], f"Missing subkey: {subkey} in {key}"
            assert actual_lower[key][subkey] == subval, f"Mismatch for {key}.{subkey}: {actual_lower[key][subkey]} != {subval}"


class TestLocalDNSProfile(unittest.TestCase):
    def setUp(self):
        self.cmd = Mock()
        self.models = Mock()
        self.models.LocalDNSProfile = lambda **kwargs: SimpleNamespace(**kwargs)
        self.agentpool_decorator_mode = AgentPoolDecoratorMode.STANDALONE

    def test_localdns_config_valid(self):
        config = {"mode": "required", "custom": "foo"}
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            json.dump(config, f)
            f.flush()
            ctx = AKSAgentPoolContext(
                self.cmd,
                AKSAgentPoolParamDict({
                    "localdns_config": f.name
                }),
                self.models,
                DecoratorMode.UPDATE,
                self.agentpool_decorator_mode,
            )
            profile = ctx.get_localdns_profile()
            self.assertEqual(profile, config)

    def test_localdns_config_invalid_file(self):
        ctx = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({
                "localdns_config": "nonexistent_file.json"
            }),
            self.models,
            DecoratorMode.UPDATE,
            self.agentpool_decorator_mode,
        )
        with self.assertRaises(InvalidArgumentValueError):
            ctx.get_localdns_profile()

    def test_localdns_config_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            f.write("not a json")
            f.flush()
            ctx = AKSAgentPoolContext(
                self.cmd,
                AKSAgentPoolParamDict({
                    "localdns_config": f.name
                }),
                self.models,
                DecoratorMode.UPDATE,
                self.agentpool_decorator_mode,
            )
            with self.assertRaises(CLIError):
                ctx.get_localdns_profile()

    def test_localdns_config_none(self):
        ctx = AKSAgentPoolContext(
            self.cmd,
            AKSAgentPoolParamDict({
                "localdns_config": None
            }),
            self.models,
            DecoratorMode.UPDATE,
            self.agentpool_decorator_mode,
        )
        profile = ctx.get_localdns_profile()
        self.assertIsNone(profile)

if __name__ == "__main__":
    unittest.main()
