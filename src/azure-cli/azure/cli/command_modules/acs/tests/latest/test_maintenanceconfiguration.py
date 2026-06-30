# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import datetime
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

    def test_add_default_maintenance_configuration_with_schedule_type_and_weekday(self):
        cmd = SimpleNamespace()
        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "default",
            "weekday": "Monday",
            "start_hour": 1,
            "schedule_type": "Weekly",
        }

        err = ("--weekday and --start-hour cannot be used together with --schedule-type for default maintenance configuration.")
        with self.assertRaises(MutuallyExclusiveArgumentError) as cm:
            aks_maintenanceconfiguration_update_internal(cmd, None, raw_parameters)
        self.assertEqual(str(cm.exception), err)

    def test_add_default_maintenance_configuration_with_invalid_schedule_type(self):
        cmd = MockCmd(self.cli_ctx)
        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "default",
            "weekday": None,
            "start_hour": None,
            "schedule_type": "Daily",
            "interval_days": 3,
            "interval_weeks": None,
            "interval_months": None,
            "day_of_week": None,
            "day_of_month": None,
            "week_index": None,
        }

        err = ("--schedule-type for default maintenance configuration must be Weekly.")
        with self.assertRaises(InvalidArgumentValueError) as cm:
            aks_maintenanceconfiguration_update_internal(cmd, None, raw_parameters)
        self.assertEqual(str(cm.exception), err)

    def test_add_default_maintenance_configuration_rejects_interval_weeks(self):
        cmd = MockCmd(self.cli_ctx)
        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "default",
            "weekday": None,
            "start_hour": None,
            "schedule_type": "Weekly",
            "interval_days": None,
            "interval_weeks": 3,
            "interval_months": None,
            "day_of_week": "Monday",
            "day_of_month": None,
            "week_index": None,
        }

        err = ("--interval-weeks cannot be specified for default maintenance configuration; the interval is always 1 week.")
        with self.assertRaises(InvalidArgumentValueError) as cm:
            aks_maintenanceconfiguration_update_internal(cmd, None, raw_parameters)
        self.assertEqual(str(cm.exception), err)

    def test_add_default_maintenance_configuration_rejects_interval_weeks_even_if_1(self):
        """interval_weeks=1 is also rejected; users must simply omit --interval-weeks."""
        cmd = MockCmd(self.cli_ctx)
        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "default",
            "weekday": None,
            "start_hour": None,
            "schedule_type": "Weekly",
            "interval_days": None,
            "interval_weeks": 1,
            "interval_months": None,
            "day_of_week": "Monday",
            "day_of_month": None,
            "week_index": None,
        }

        err = ("--interval-weeks cannot be specified for default maintenance configuration; the interval is always 1 week.")
        with self.assertRaises(InvalidArgumentValueError) as cm:
            aks_maintenanceconfiguration_update_internal(cmd, None, raw_parameters)
        self.assertEqual(str(cm.exception), err)

    def test_add_default_maintenance_configuration_rejects_inapplicable_schedule_params(self):
        """interval_days, interval_months, day_of_month, week_index are rejected for default config."""
        for param in ("interval_days", "interval_months", "day_of_month", "week_index"):
            with self.subTest(param=param):
                cmd = MockCmd(self.cli_ctx)
                raw_parameters = {
                    "resource_group_name": "test_rg",
                    "cluster_name": "test_cluster",
                    "config_name": "default",
                    "weekday": None,
                    "start_hour": None,
                    "schedule_type": "Weekly",
                    "interval_days": None,
                    "interval_weeks": None,
                    "interval_months": None,
                    "day_of_week": "Monday",
                    "day_of_month": None,
                    "week_index": None,
                }
                raw_parameters[param] = 1
                expected_flag = "--" + param.replace("_", "-")
                with self.assertRaises(MutuallyExclusiveArgumentError) as cm:
                    aks_maintenanceconfiguration_update_internal(cmd, None, raw_parameters)
                self.assertIn(expected_flag, str(cm.exception))
                self.assertIn("cannot be used for default maintenance configuration", str(cm.exception))

    def test_add_default_maintenance_configuration_rejects_multiple_inapplicable_params(self):
        """Error message names all offending flags when multiple inapplicable params are passed together."""
        cmd = MockCmd(self.cli_ctx)
        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "default",
            "weekday": None,
            "start_hour": None,
            "schedule_type": "Weekly",
            "interval_days": 2,
            "interval_weeks": None,
            "interval_months": None,
            "day_of_week": "Monday",
            "day_of_month": 15,
            "week_index": None,
        }
        with self.assertRaises(MutuallyExclusiveArgumentError) as cm:
            aks_maintenanceconfiguration_update_internal(cmd, None, raw_parameters)
        msg = str(cm.exception)
        self.assertIn("--interval-days", msg)
        self.assertIn("--day-of-month", msg)
        self.assertIn("cannot be used for default maintenance configuration", msg)
        # flags not passed should not appear in the message
        self.assertNotIn("--interval-months", msg)
        self.assertNotIn("--week-index", msg)

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

    def test_add_default_maintenance_configuration_with_weekly_schedule_type(self):
        cmd = MockCmd(self.cli_ctx)

        class MockMaintenanceConfigClient:
            def create_or_update(self, **kwargs):
                return kwargs.get('parameters')

        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "default",
            "weekday": None,
            "start_hour": None,
            "schedule_type": "Weekly",
            "interval_days": None,
            "interval_weeks": None,
            "interval_months": None,
            "day_of_week": "Monday",
            "day_of_month": None,
            "week_index": None,
            "start_time": "09:00",
            "duration_hours": 4,
            "utc_offset": None,
            "start_date": None,
        }

        result = aks_maintenanceconfiguration_update_internal(cmd, MockMaintenanceConfigClient(), raw_parameters)

        self.assertIsNotNone(result.maintenance_window)
        self.assertEqual(result.maintenance_window.start_time, "09:00")
        self.assertEqual(result.maintenance_window.duration_hours, 4)
        self.assertIsNotNone(result.maintenance_window.schedule)
        self.assertIsNotNone(result.maintenance_window.schedule.weekly)
        self.assertIsNone(getattr(result, 'time_in_week', None))

    def test_add_default_maintenance_configuration_with_weekly_schedule_type_omits_interval_weeks(self):
        """interval_weeks should default to 1 when omitted for the default config."""
        cmd = MockCmd(self.cli_ctx)

        class MockMaintenanceConfigClient:
            def create_or_update(self, **kwargs):
                return kwargs.get('parameters')

        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "default",
            "weekday": None,
            "start_hour": None,
            "schedule_type": "Weekly",
            "interval_days": None,
            "interval_weeks": None,
            "interval_months": None,
            "day_of_week": "Monday",
            "day_of_month": None,
            "week_index": None,
            "start_time": "09:00",
            "duration_hours": 4,
            "utc_offset": None,
            "start_date": None,
        }

        result = aks_maintenanceconfiguration_update_internal(cmd, MockMaintenanceConfigClient(), raw_parameters)

        self.assertIsNotNone(result.maintenance_window)
        self.assertIsNotNone(result.maintenance_window.schedule)
        self.assertIsNotNone(result.maintenance_window.schedule.weekly)
        self.assertEqual(result.maintenance_window.schedule.weekly.interval_weeks, 1)
        self.assertIsNone(raw_parameters["interval_weeks"])
        self.assertIsNone(getattr(result, 'time_in_week', None))

    def test_add_default_maintenance_configuration_with_utc_offset_and_start_date(self):
        """utc_offset and start_date must be passed through to the constructed maintenance_window."""
        cmd = MockCmd(self.cli_ctx)

        class MockMaintenanceConfigClient:
            def create_or_update(self, **kwargs):
                return kwargs.get('parameters')

        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "default",
            "weekday": None,
            "start_hour": None,
            "schedule_type": "Weekly",
            "interval_days": None,
            "interval_weeks": None,
            "interval_months": None,
            "day_of_week": "Monday",
            "day_of_month": None,
            "week_index": None,
            "start_time": "09:00",
            "duration_hours": 4,
            "utc_offset": "+05:30",
            "start_date": "2026-01-15",
        }

        result = aks_maintenanceconfiguration_update_internal(cmd, MockMaintenanceConfigClient(), raw_parameters)

        self.assertIsNotNone(result.maintenance_window)
        self.assertEqual(result.maintenance_window.utc_offset, "+05:30")
        self.assertEqual(result.maintenance_window.start_date, datetime.date(2026, 1, 15))

    def test_add_default_maintenance_configuration_requires_day_of_week(self):
        """--schedule-type Weekly without --day-of-week must raise a clear error for default config."""
        cmd = MockCmd(self.cli_ctx)

        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "config_name": "default",
            "weekday": None,
            "start_hour": None,
            "schedule_type": "Weekly",
            "interval_days": None,
            "interval_weeks": None,
            "interval_months": None,
            "day_of_week": None,
            "day_of_month": None,
            "week_index": None,
            "start_time": "09:00",
            "duration_hours": 4,
            "utc_offset": None,
            "start_date": None,
        }

        with self.assertRaises(RequiredArgumentMissingError) as cm:
            aks_maintenanceconfiguration_update_internal(cmd, None, raw_parameters)
        self.assertIn("--day-of-week", str(cm.exception))
