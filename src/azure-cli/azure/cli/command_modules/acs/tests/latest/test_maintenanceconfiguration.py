# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from types import SimpleNamespace

# from azure.cli.core.util import CLIError
from azure.cli.core.azclierror import (
    InvalidArgumentValueError,
    RequiredArgumentMissingError,
    MutuallyExclusiveArgumentError,
)

from azure.cli.command_modules.acs.maintenanceconfiguration import aks_maintenanceconfiguration_update_internal
from azure.cli.command_modules.acs.tests.latest.mocks import MockCLI, MockCmd
from azure.cli.core.profiles import ResourceType

class TestAddMaintenanceConfiguration(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.resource_type = ResourceType.MGMT_CONTAINERSERVICE
    def test_add_maintenance_configuration_with_invalid_name(self):
        cmd = SimpleNamespace()
        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "something",
        }

        err = ("--config-name must be one of default, aksManagedAutoUpgradeSchedule or aksManagedNodeOSUpgradeSchedule, not something")
        with self.assertRaises(InvalidArgumentValueError) as cm:
            aks_maintenanceconfiguration_update_internal(cmd, None, raw_parameters)
        self.assertEqual(str(cm.exception), err)

    def test_add_default_maintenance_configuration_with_schedule_type(self):
        cmd = SimpleNamespace()
        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "default",
            "weekday": "Monday",
            "start_hour": 1,
            "schedule_type": "Weekly",
        }

        err = ("--schedule-type is not supported for default maintenance configuration.")
        with self.assertRaises(MutuallyExclusiveArgumentError) as cm:
            aks_maintenanceconfiguration_update_internal(cmd, None, raw_parameters)
        self.assertEqual(str(cm.exception), err)
    
    def test_add_non_default_schedule_with_weekday(self):
        cmd = SimpleNamespace()
        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "aksManagedAutoUpgradeSchedule",
            "weekday": "Monday",
        }

        err = ("--weekday and --start-hour are only applicable to default maintenance configuration.")
        with self.assertRaises(MutuallyExclusiveArgumentError) as cm:
            aks_maintenanceconfiguration_update_internal(cmd, None, raw_parameters)
        self.assertEqual(str(cm.exception), err)
    
    def test_add_daily_schedule_with_missing_options(self):
        cli_ctx = MockCLI()
        cmd = MockCmd(cli_ctx)
        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "aksManagedAutoUpgradeSchedule",
            "schedule_type": "Daily",
        }

        err = ("Please specify --interval-days when using daily schedule.")
        with self.assertRaises(RequiredArgumentMissingError) as cm:
            aks_maintenanceconfiguration_update_internal(cmd, None, raw_parameters)
        self.assertEqual(str(cm.exception), err)
    
    def test_add_daily_schedule_with_invalid_options(self):
        cmd = MockCmd(self.cli_ctx)
        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "aksManagedAutoUpgradeSchedule",
            "schedule_type": "Daily",
            "interval_days": 3,
            "day_of_week": "Monday",
        }

        err = ("--interval-weeks, --interval-months, --day-of-week, --day-of-month and --week-index cannot be used for Daily schedule.")
        with self.assertRaises(MutuallyExclusiveArgumentError) as cm:
            aks_maintenanceconfiguration_update_internal(cmd, None, raw_parameters)
        self.assertEqual(str(cm.exception), err)

    def test_add_weekly_schedule_with_invalid_options(self):
        cmd = MockCmd(self.cli_ctx)
        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "aksManagedAutoUpgradeSchedule",
            "schedule_type": "Weekly",
            "day_of_week": "Monday",
            "interval_weeks": 3,
            "week_index": "First",
        }

        err = ("--interval-months, --day-of-month and --week-index cannot be used for Weekly schedule.")
        with self.assertRaises(MutuallyExclusiveArgumentError) as cm:
            aks_maintenanceconfiguration_update_internal(cmd, None, raw_parameters)
        self.assertEqual(str(cm.exception), err)
    
    def test_add_absolute_monthly_schedule_with_missing_options(self):
        cmd = MockCmd(self.cli_ctx)
        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "aksManagedAutoUpgradeSchedule",
            "schedule_type": "AbsoluteMonthly",
            "day_of_week": "Monday",
            "interval_months": 3,
        }

        err = ("Please specify --interval-months and --day-of-month when using absolute monthly schedule.")
        with self.assertRaises(RequiredArgumentMissingError) as cm:
            aks_maintenanceconfiguration_update_internal(cmd, None, raw_parameters)
        self.assertEqual(str(cm.exception), err)

    def test_add_absolute_monthly_schedule_with_invalid_options(self):
        cmd = MockCmd(self.cli_ctx)
        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "aksManagedAutoUpgradeSchedule",
            "schedule_type": "AbsoluteMonthly",
            "day_of_month": 15,
            "interval_months": 3,
            "week_index": "First",
        }

        err = ("--interval-days, --interval-weeks, --day-of-week and --week-index cannot be used for AbsoluteMonthly schedule.")
        with self.assertRaises(MutuallyExclusiveArgumentError) as cm:
            aks_maintenanceconfiguration_update_internal(cmd, None, raw_parameters)
        self.assertEqual(str(cm.exception), err)
    
    def test_add_relative_monthly_schedule_with_missing_options(self):
        cmd = MockCmd(self.cli_ctx)
        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "aksManagedAutoUpgradeSchedule",
            "schedule_type": "RelativeMonthly",
            "day_of_week": "Monday",
            "interval_months": 3,
        }

        err = ("Please specify --interval-months, --day-of-week and --week-index when using relative monthly schedule.")
        with self.assertRaises(RequiredArgumentMissingError) as cm:
            aks_maintenanceconfiguration_update_internal(cmd, None, raw_parameters)
        self.assertEqual(str(cm.exception), err)
    
    def test_add_dedicated_schedule_with_missing_options(self):
        cmd = MockCmd(self.cli_ctx)
        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "aksManagedAutoUpgradeSchedule",
            "schedule_type": "AbsoluteMonthly",
            "day_of_month": 1,
            "interval_months": 3,
            "start_time": "00:00",
        }

        err = ("Please specify --duration for maintenance window.")
        with self.assertRaises(RequiredArgumentMissingError) as cm:
            aks_maintenanceconfiguration_update_internal(cmd, None, raw_parameters)
        self.assertEqual(str(cm.exception), err)
        