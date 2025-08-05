# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.util import CLIError

from .aaz.latest.consumption.budget import List as _ConsumptionBudgetsList
from .aaz.latest.consumption.marketplace import List as _ConsumptionMarketplaceList
from .aaz.latest.consumption.pricesheet import Show as _ConsumptionPricesheetShow
from .aaz.latest.consumption.reservation.detail import List as _ConsumptionReservationDetailList
from .aaz.latest.consumption.reservation.summary import List as _ConsumptionReservationSummaryList
from .aaz.latest.consumption.usage import List as _ConsumptionUsageList
from azure.cli.core.aaz import has_value
from datetime import datetime


# pylint: disable=line-too-long, disable=protected-access, consider-using-generator
def validate_both_start_end_dates(args):
    """Validates the existence of both start and end dates in the parameter or neither"""
    if bool(has_value(args.start_date)) != bool(has_value(args.end_date)):
        raise CLIError("usage error: Both --start-date and --end-date need to be supplied or neither.")


def validate_reservation_summary(self):
    """lowercase the data grain for comparison"""
    args = self.ctx.args
    data_grain = args.grain.to_serialized_data().lower()
    if data_grain not in ('daily', 'monthly'):
        raise CLIError("usage error: --grain  can be either daily or monthly.")
    if data_grain == 'daily' and (not has_value(args.start_date) or not has_value(args.end_date)):
        raise CLIError("usage error: Both --start-date and --end-date need to be supplied for daily grain.")


class ConsumptionUsageList(_ConsumptionUsageList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.end_date = AAZStrArg(
            options=["--end-date", "-e"],
            help="End date (YYYY-MM-DD in UTC). If specified, also requires --start-date.",
        )
        args_schema.include_additional_properties = AAZStrArg(
            options=["--include-additional-properties", "-a"],
            help="Include additional properties in the usages.",
            blank="true",
        )
        args_schema.include_meter_details = AAZStrArg(
            options=["--include-meter-details", "-m"],
            help="Include meter details in the usages.",
            blank="true",
        )
        args_schema.start_date = AAZStrArg(
            options=["--start-date", "-s"],
            help="Start date (YYYY-MM-DD in UTC). If specified, also requires --end-date.",
        )
        args_schema.filter._registered = False
        args_schema.skiptoken._registered = False
        args_schema.expand._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        validate_both_start_end_dates(args)
        if has_value(args.include_additional_properties) and has_value(args.include_meter_details):
            args.expand = 'properties/additionalProperties,properties/meterDetails'
        elif has_value(args.include_additional_properties):
            args.expand = 'properties/additionalProperties'
        elif has_value(args.include_meter_details):
            args.expand = 'properties/meterDetails'
        else:
            args.expand = None

        if has_value(args.start_date) and has_value(args.end_date):
            start_date = datetime_type(args.start_date.to_serialized_data())
            end_date = datetime_type(args.end_date.to_serialized_data())
            filter_from = "properties/usageEnd ge \'{}\'".format(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
            filter_to = "properties/usageEnd le \'{}\'".format(end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
            args.filter = "{} and {}".format(filter_from, filter_to)

    def _output(self, *args, **kwargs):
        args = self.ctx.args
        result = self.deserialize_output(self.ctx.vars.instance.value, client_flatten=True)
        result = list(filter(None, [transform_usage_output(item) for item in result]))
        if has_value(args.top):
            next_link = None
        else:
            next_link = self.deserialize_output(self.ctx.vars.instance.next_link)
        return result, next_link


def transform_usage_output(result):
    from dateutil import parser
    usageStart = result.get('usageStart', None)
    usageEnd = result.get('usageEnd', None)
    if usageStart or usageEnd:
        usageStart = parser.parse(usageStart).strftime("%Y-%m-%dT%H:%M:%SZ") if usageStart else None
        usageEnd = parser.parse(usageEnd).strftime("%Y-%m-%dT%H:%M:%SZ") if usageEnd else None
    result['usageStart'] = usageStart
    result['usageEnd'] = usageEnd
    result['usageQuantity'] = str(result.get('usageQuantity', None))
    result['billableQuantity'] = str(result.get('billableQuantity', None))
    result['pretaxCost'] = str(result.get('pretaxCost', None))
    if 'meterDetails' in result:
        result['meterDetails']['totalIncludedQuantity'] = str(result['meterDetails'].get('pretaxStandardRate', None))
        result['meterDetails']['pretaxStandardRate'] = str(result['meterDetails'].get('pretaxStandardRate', None))
    else:
        result['meterDetails'] = None
    return result


def datetime_type(string):
    """ Validates UTC datetime. Examples of accepted forms:
    2017-12-31T01:11:59Z,2017-12-31T01:11Z or 2017-12-31T01Z or 2017-12-31 """
    accepted_date_formats = ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%MZ', '%Y-%m-%dT%HZ', '%Y-%m-%d']
    for form in accepted_date_formats:
        try:
            return datetime.strptime(string, form)
        except ValueError:
            continue
    raise ValueError("Input '{}' not valid. Valid example: 2017-02-11T23:59:59Z".format(string))


class ConsumptionReservationSummaryList(_ConsumptionReservationSummaryList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.end_date = AAZStrArg(
            options=["--end-date", "-e"],
            help="End date (YYYY-MM-DD in UTC). Only needed for daily grain and if specified, also requires --start-date.",
        )
        args_schema.start_date = AAZStrArg(
            options=["--start-date", "-s"],
            help="Start date (YYYY-MM-DD in UTC). Only needed for daily grain and if specified, also requires --end-date.",
        )
        args_schema.filter._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        validate_reservation_summary(self)
        if has_value(args.start_date) and has_value(args.end_date):
            start_date = datetime_type(args.start_date.to_serialized_data())
            end_date = datetime_type(args.end_date.to_serialized_data())
            filter_from = "properties/UsageDate ge {}".format(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
            filter_to = "properties/UsageDate le {}".format(end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
            args.filter = "{} and {}".format(filter_from, filter_to)

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance.value, client_flatten=True)
        result = [reservation_summary_output(item) for item in result]
        next_link = self.deserialize_output(self.ctx.vars.instance.next_link)
        return result, next_link


def reservation_summary_output(result):

    result['reservedHours'] = str(result['reservedHours'])
    usage_date = datetime.strptime(result['usageDate'], "%Y-%m-%dT%H:%M:%SZ")
    result['usageDate'] = usage_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    result['usedHours'] = str(result['usedHours'])
    result['maxUtilizationPercentage'] = str(result['maxUtilizationPercentage'])
    result['minUtilizationPercentage'] = str(result['minUtilizationPercentage'])
    result['avgUtilizationPercentage'] = str(result['avgUtilizationPercentage'])
    return result


class ConsumptionReservationDetailList(_ConsumptionReservationDetailList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.end_date = AAZStrArg(
            options=["--end-date", "-e"],
            help="End date (YYYY-MM-DD in UTC). Only needed for daily grain and if specified, also requires --start-date.",
            required=True,
        )
        args_schema.start_date = AAZStrArg(
            options=["--start-date", "-s"],
            help="Start date (YYYY-MM-DD in UTC). Only needed for daily grain and if specified, also requires --end-date.",
            required=True,
        )
        args_schema.filter._required = False
        args_schema.filter._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.start_date) and has_value(args.end_date):
            start_date = datetime_type(args.start_date.to_serialized_data())
            end_date = datetime_type(args.end_date.to_serialized_data())
            filter_from = "properties/UsageDate ge {}".format(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
            filter_to = "properties/UsageDate le {}".format(end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
            args.filter = "{} and {}".format(filter_from, filter_to)

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance.value, client_flatten=True)
        result = [reservation_detail_output(item) for item in result]
        next_link = self.deserialize_output(self.ctx.vars.instance.next_link)
        return result, next_link


def reservation_detail_output(result):
    result['reservedHours'] = str(result['reservedHours'])
    usage_date = datetime.strptime(result['usageDate'], "%Y-%m-%dT%H:%M:%SZ")
    result['usageDate'] = usage_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    result['usedHours'] = str(result['usedHours'])
    result['totalReservedQuantity'] = str(result['totalReservedQuantity'])
    return result


class ConsumptionPricesheetShow(_ConsumptionPricesheetShow):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.include_meter_details = AAZStrArg(
            options=["--include-meter-details"],
            help="Include meter details in the price sheet.",
        )
        args_schema.expand._registered = False
        args_schema.skiptoken._registered = False
        args_schema.top._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.include_meter_details):
            args.expand = 'properties/meterDetails'
        else:
            args.expand = None

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        result['pricesheets'] = [pricesheet_show_properties(item) for item in result['pricesheets']]
        return result


def pricesheet_show_properties(result):
    result['unitOfMeasure'] = str(result['unitOfMeasure'])
    result['includedQuantity'] = str(result['includedQuantity'])
    result['unitPrice'] = str(result['unitPrice'])
    if 'meterDetails' in result:
        result['meterDetails']['totalIncludedQuantity'] = str(result['meterDetails'].get('pretaxStandardRate', None))
        result['meterDetails']['pretaxStandardRate'] = str(result['meterDetails'].get('pretaxStandardRate', None))
    else:
        result['meterDetails'] = None
    return result


class ConsumptionMarketplaceList(_ConsumptionMarketplaceList):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.end_date = AAZStrArg(
            options=["--end-date", "-e"],
            help="End date (YYYY-MM-DD in UTC). If specified, also requires --start-date.",
        )
        args_schema.start_date = AAZStrArg(
            options=["--start-date", "-s"],
            help="Start date (YYYY-MM-DD in UTC). If specified, also requires --end-date.",
        )
        args_schema.filter._registered = False
        args_schema.skiptoken._registered = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        validate_both_start_end_dates(args)
        if has_value(args.start_date) and has_value(args.end_date):
            start_date = datetime_type(args.start_date.to_serialized_data())
            end_date = datetime_type(args.end_date.to_serialized_data())
            filter_from = "properties/usageEnd ge \'{}\'".format(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
            filter_to = "properties/usageEnd le \'{}\'".format(end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
            args.filter = "{} and {}".format(filter_from, filter_to)

    def _output(self, *args, **kwargs):
        args = self.ctx.args
        result = self.deserialize_output(self.ctx.vars.instance.value, client_flatten=True)
        result = [marketplace_list_output(item) for item in result]
        if has_value(args.top):
            next_link = None
        else:
            next_link = self.deserialize_output(self.ctx.vars.instance.next_link)
        return result, next_link


def marketplace_list_output(result):
    result['pretaxCost'] = str(result['pretaxCost'])
    result['consumedQuantity'] = str(result['consumedQuantity'])
    result['resourceRate'] = str(result['resourceRate'])
    return result


class ConsumptionBudgetsList(_ConsumptionBudgetsList):

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance.value, client_flatten=True)
        from ._transformers import budget_output
        result = [budget_output(item) for item in result]
        next_link = self.deserialize_output(self.ctx.vars.instance.next_link)
        return result, next_link


def cli_consumption_show_budget(cmd, budget_name, resource_group_name=None):
    args = {"budget_name": budget_name}
    if resource_group_name:
        from .aaz.latest.consumption.budget import ShowWithRg
        args['resource_group'] = resource_group_name
        return ShowWithRg(cli_ctx=cmd.cli_ctx)(command_args=args)
    from .aaz.latest.consumption.budget import Show
    return Show(cli_ctx=cmd.cli_ctx)(command_args=args)


def cli_consumption_create_budget(cmd, budget_name, category, amount, time_grain, start_date, end_date, resource_groups=None, resources=None, meters=None, resource_group_name=None):
    args = {
        "budget_name": budget_name,
        "category": category,
        "amount": float(amount),
        "time_grain": time_grain,
        "time_period": {"start_date": str(start_date), "end_date": str(end_date)},
        "filters": {"resource_groups": resource_groups, "meters": meters, "resources": resources},
    }
    if resource_group_name:
        from .aaz.latest.consumption.budget import CreateWithRg
        args['resource_group'] = resource_group_name
        return CreateWithRg(cli_ctx=cmd.cli_ctx)(command_args=args)
    from .aaz.latest.consumption.budget import Create
    return Create(cli_ctx=cmd.cli_ctx)(command_args=args)


def cli_consumption_delete_budget(cmd, budget_name, resource_group_name=None):
    args = {"budget_name": budget_name}
    if resource_group_name:
        args['resource_group'] = resource_group_name
        from .aaz.latest.consumption.budget import DeleteWithRg
        return DeleteWithRg(cli_ctx=cmd.cli_ctx)(command_args=args)
    from .aaz.latest.consumption.budget import Delete
    return Delete(cli_ctx=cmd.cli_ctx)(command_args=args)
