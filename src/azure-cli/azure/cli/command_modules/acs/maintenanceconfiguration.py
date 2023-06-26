# pylint: disable=too-many-lines
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from knack.log import get_logger
from azure.cli.core.util import get_file_json
from azure.cli.core.azclierror import (
    InvalidArgumentValueError,
    RequiredArgumentMissingError,
    MutuallyExclusiveArgumentError,
)

from acs._consts import (
    CONST_DAILY_MAINTENANCE_SCHEDULE,
    CONST_WEEKLY_MAINTENANCE_SCHEDULE,
    CONST_ABSOLUTEMONTHLY_MAINTENANCE_SCHEDULE,
    CONST_RELATIVEMONTHLY_MAINTENANCE_SCHEDULE,
    CONST_DEFAULT_CONFIGURATION_NAME,
    CONST_AUTOUPGRADE_CONFIGURATION_NAME,
    CONST_NODEOSUPGRADE_CONFIGURATION_NAME,
)

from acs._client_factory import CUSTOM_MGMT_AKS_PREVIEW

logger = get_logger(__name__)


def aks_maintenanceconfiguration_update_internal(cmd, client, raw_parameters):
    resource_group_name = raw_parameters.get("resource_group_name")
    cluster_name = raw_parameters.get("cluster_name")
    config_name = raw_parameters.get("config_name")
    config = getMaintenanceConfiguration(cmd, raw_parameters)
    return client.create_or_update(resource_group_name=resource_group_name, resource_name=cluster_name, config_name=config_name, parameters=config)


def getMaintenanceConfiguration(cmd, raw_parameters):
    config_file = raw_parameters.get("config_file")
    if config_file is not None:
        mcr = get_file_json(config_file)
        logger.info(mcr)
        return mcr

    config_name = raw_parameters.get("config_name")
    if config_name == CONST_DEFAULT_CONFIGURATION_NAME:
        return constructDefaultMaintenanceConfiguration(cmd, raw_parameters)
    elif config_name == CONST_AUTOUPGRADE_CONFIGURATION_NAME or config_name == CONST_NODEOSUPGRADE_CONFIGURATION_NAME:
        return constructDedicatedMaintenanceConfiguration(cmd, raw_parameters)
    else:
        raise InvalidArgumentValueError('--config-name must be one of default, aksManagedAutoUpgradeSchedule or aksManagedNodeOSUpgradeSchedule, not {}'.format(config_name))


def constructDefaultMaintenanceConfiguration(cmd, raw_parameters):
    weekday = raw_parameters.get("weekday")
    start_hour = raw_parameters.get("start_hour")
    schedule_type = raw_parameters.get("schedule_type")

    if weekday is None or start_hour is None:
        raise RequiredArgumentMissingError('Please specify --weekday and --start-hour for default maintenance configuration, or use --config-file instead.')
    if schedule_type is not None:
        raise MutuallyExclusiveArgumentError('--schedule-type is not supported for default maintenance configuration.')

    MaintenanceConfiguration = cmd.get_models('MaintenanceConfiguration', resource_type=CUSTOM_MGMT_AKS_PREVIEW, operation_group='maintenance_configurations')
    TimeInWeek = cmd.get_models('TimeInWeek', resource_type=CUSTOM_MGMT_AKS_PREVIEW, operation_group='maintenance_configurations')

    dict = {}
    dict["day"] = weekday
    dict["hour_slots"] = [start_hour]
    timeInWeek = TimeInWeek(**dict)
    result = MaintenanceConfiguration()
    result.time_in_week = [timeInWeek]
    result.not_allowed_time = []
    return result


def constructDedicatedMaintenanceConfiguration(cmd, raw_parameters):
    weekday = raw_parameters.get("weekday")
    start_hour = raw_parameters.get("start_hour")
    if weekday is not None or start_hour is not None:
        raise MutuallyExclusiveArgumentError('--weekday and --start-hour are only applicable to default maintenance configuration.')

    maintenanceConfiguration = cmd.get_models('MaintenanceConfiguration', resource_type=CUSTOM_MGMT_AKS_PREVIEW, operation_group='maintenance_configurations')
    result = maintenanceConfiguration()
    result.maintenance_window = constructMaintenanceWindow(cmd, raw_parameters)
    return result


def constructMaintenanceWindow(cmd, raw_parameters):
    schedule = constructSchedule(cmd, raw_parameters)
    start_date = raw_parameters.get("start_date")
    start_time = raw_parameters.get("start_time")
    duration_hours = raw_parameters.get("duration_hours")
    utc_offset = raw_parameters.get("utc_offset")

    if start_time is None:
        raise RequiredArgumentMissingError('Please specify --start-time for maintenance window.')
    if duration_hours is None:
        raise RequiredArgumentMissingError('Please specify --duration for maintenance window.')

    MaintenanceWindow = cmd.get_models('MaintenanceWindow', resource_type=CUSTOM_MGMT_AKS_PREVIEW, operation_group='maintenance_configurations')
    maintenanceWindow = MaintenanceWindow(
        schedule=schedule,
        start_date=start_date,
        start_time=start_time,
        duration_hours=duration_hours,
        utc_offset=utc_offset
    )
    return maintenanceWindow


def constructSchedule(cmd, raw_parameters):
    schedule_type = raw_parameters.get("schedule_type")
    interval_days = raw_parameters.get("interval_days")
    interval_weeks = raw_parameters.get("interval_weeks")
    interval_months = raw_parameters.get("interval_months")
    day_of_week = raw_parameters.get("day_of_week")
    day_of_month = raw_parameters.get("day_of_month")
    week_index = raw_parameters.get("week_index")

    Schedule = cmd.get_models('Schedule', resource_type=CUSTOM_MGMT_AKS_PREVIEW, operation_group='maintenance_configurations')
    schedule = Schedule()

    if schedule_type == CONST_DAILY_MAINTENANCE_SCHEDULE:
        schedule.daily = constructDailySchedule(cmd, interval_days, interval_weeks, interval_months, day_of_week, day_of_month, week_index)
    elif schedule_type == CONST_WEEKLY_MAINTENANCE_SCHEDULE:
        schedule.weekly = constructWeeklySchedule(cmd, interval_days, interval_weeks, interval_months, day_of_week, day_of_month, week_index)
    elif schedule_type == CONST_ABSOLUTEMONTHLY_MAINTENANCE_SCHEDULE:
        schedule.absolute_monthly = constructAbsoluteMonthlySchedule(cmd, interval_days, interval_weeks, interval_months, day_of_week, day_of_month, week_index)
    elif schedule_type == CONST_RELATIVEMONTHLY_MAINTENANCE_SCHEDULE:
        schedule.relative_monthly = constructRelativeMonthlySchedule(cmd, interval_days, interval_weeks, interval_months, day_of_week, day_of_month, week_index)
    else:
        raise InvalidArgumentValueError('--schedule-type must be one of Daily, Weekly, AbsoluteMonthly or RelativeMonthly.')
    return schedule


def constructDailySchedule(cmd, interval_days, interval_weeks, interval_months, day_of_week, day_of_month, week_index):
    if interval_days is None:
        raise RequiredArgumentMissingError("Please specify --interval-days when using daily schedule.")
    if interval_weeks is not None or interval_months is not None or day_of_week is not None or day_of_month is not None or week_index is not None:
        raise MutuallyExclusiveArgumentError('--interval-weeks, --interval-months, --day-of-week, --day-of-month and --week-index cannot be used for Daily schedule.')

    DailySchedule = cmd.get_models('DailySchedule', resource_type=CUSTOM_MGMT_AKS_PREVIEW, operation_group='maintenance_configurations')
    dailySchedule = DailySchedule(
        interval_days=interval_days
    )
    return dailySchedule


def constructWeeklySchedule(cmd, interval_days, interval_weeks, interval_months, day_of_week, day_of_month, week_index):
    if interval_weeks is None or day_of_week is None:
        raise RequiredArgumentMissingError("Please specify --interval-weeks and --day-of-week when using weekly schedule.")
    if interval_days is not None or interval_months is not None or day_of_month is not None or week_index is not None:
        raise MutuallyExclusiveArgumentError('--interval-months, --day-of-month and --week-index cannot be used for Weekly schedule.')

    WeeklySchedule = cmd.get_models('WeeklySchedule', resource_type=CUSTOM_MGMT_AKS_PREVIEW, operation_group='maintenance_configurations')
    weeklySchedule = WeeklySchedule(
        interval_weeks=interval_weeks,
        day_of_week=day_of_week
    )
    return weeklySchedule


def constructAbsoluteMonthlySchedule(cmd, interval_days, interval_weeks, interval_months, day_of_week, day_of_month, week_index):
    if interval_months is None or day_of_month is None:
        raise RequiredArgumentMissingError("Please specify --interval-months and --day-of-month when using absolute monthly schedule.")
    if interval_days is not None or interval_weeks is not None or day_of_week is not None or week_index is not None:
        raise MutuallyExclusiveArgumentError('--interval-days, --interval-weeks, --day-of-week and --week-index cannot be used for AbsoluteMonthly schedule.')

    AbsoluteMonthlySchedule = cmd.get_models('AbsoluteMonthlySchedule', resource_type=CUSTOM_MGMT_AKS_PREVIEW, operation_group='maintenance_configurations')
    absoluteMonthlySchedule = AbsoluteMonthlySchedule(
        interval_months=interval_months,
        day_of_month=day_of_month
    )
    return absoluteMonthlySchedule


def constructRelativeMonthlySchedule(cmd, interval_days, interval_weeks, interval_months, day_of_week, day_of_month, week_index):
    if interval_months is None or day_of_week is None or week_index is None:
        raise RequiredArgumentMissingError("Please specify --interval-months, --day-of-week and --week-index when using relative monthly schedule.")
    if interval_days is not None or interval_weeks is not None or day_of_month is not None:
        raise MutuallyExclusiveArgumentError('--interval-days, --interval-weeks and --day-of-month cannot be used for RelativeMonthly schedule.')

    RelativeMonthlySchedule = cmd.get_models('RelativeMonthlySchedule', resource_type=CUSTOM_MGMT_AKS_PREVIEW, operation_group='maintenance_configurations')
    relativeMonthlySchedule = RelativeMonthlySchedule(
        interval_months=interval_months,
        day_of_week=day_of_week,
        week_index=week_index
    )
    return relativeMonthlySchedule