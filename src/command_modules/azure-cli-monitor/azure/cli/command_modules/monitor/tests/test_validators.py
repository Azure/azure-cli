# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azure.cli.command_modules.monitor.validators import (_validate_logs,
                                                          _validate_metrics)


class ValidatorsTest(unittest.TestCase):
    def test_validate_logs(self):
        logs = [{"category": "OperationalLogs", "enabled": False, "retentionPolicy": {"days": 0, "enabled": False}}]

        validated_logs = _validate_logs(logs)
        if not validated_logs or not isinstance(validated_logs, list):
            assert False
        for validated_log in validated_logs:
            if 'retentionPolicy' in validated_log or 'retention_policy' not in validated_log:
                assert False

    def test_validate_metrics(self):
        metrics = [{"timeGrain": "PT1M", "enabled": False, "retentionPolicy": {"days": 0, "enabled": False}}]

        validated_metrics = _validate_metrics(metrics)
        if not validated_metrics or not isinstance(validated_metrics, list):
            assert False
        for validated_metric in validated_metrics:
            if 'retentionPolicy' in validated_metric \
                    or 'retention_policy' not in validated_metric \
                    or 'timeGrain' in validated_metric \
                    or 'time_grain' not in validated_metric:
                assert False
