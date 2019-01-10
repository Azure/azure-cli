# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import antlr4
from knack.util import CLIError

from azure.cli.command_modules.monitor.util import (
    get_aggregation_map, get_operator_map, get_autoscale_operator_map,
    get_autoscale_aggregation_map, get_autoscale_scale_direction_map)


def timezone_name_type(value):
    from azure.cli.command_modules.monitor._autoscale_util import AUTOSCALE_TIMEZONES
    zone = next((x['name'] for x in AUTOSCALE_TIMEZONES if x['name'].lower() == value.lower()), None)
    if not zone:
        raise CLIError(
            "Invalid time zone: '{}'. Run 'az monitor autoscale profile list-timezones' for values.".format(value))
    return zone


def timezone_offset_type(value):

    try:
        hour, minute = str(value).split(':')
    except ValueError:
        hour = str(value)
        minute = None

    hour = int(hour)

    if hour > 14 or hour < -12:
        raise CLIError('Offset out of range: -12 to +14')

    if hour >= 0 and hour < 10:
        value = '+0{}'.format(hour)
    elif hour >= 10:
        value = '+{}'.format(hour)
    elif hour < 0 and hour > -10:
        value = '-0{}'.format(-1 * hour)
    else:
        value = str(hour)
    if minute:
        value = '{}:{}'.format(value, minute)
    return value


def get_period_type(as_timedelta=False):

    def period_type(value):

        import re

        def _get_substring(indices):
            if indices == tuple([-1, -1]):
                return ''
            return value[indices[0]: indices[1]]

        regex = r'(p)?(\d+y)?(\d+m)?(\d+d)?(t)?(\d+h)?(\d+m)?(\d+s)?'
        match = re.match(regex, value.lower())
        match_len = match.span(0)
        if match_len != tuple([0, len(value)]):
            raise ValueError
        # simply return value if a valid ISO8601 string is supplied
        if match.span(1) != tuple([-1, -1]) and match.span(5) != tuple([-1, -1]):
            return value

        # if shorthand is used, only support days, minutes, hours, seconds
        # ensure M is interpretted as minutes
        days = _get_substring(match.span(4))
        hours = _get_substring(match.span(6))
        minutes = _get_substring(match.span(7)) or _get_substring(match.span(3))
        seconds = _get_substring(match.span(8))

        if as_timedelta:
            from datetime import timedelta
            return timedelta(
                days=int(days[:-1]) if days else 0,
                hours=int(hours[:-1]) if hours else 0,
                minutes=int(minutes[:-1]) if minutes else 0,
                seconds=int(seconds[:-1]) if seconds else 0
            )
        return 'P{}T{}{}{}'.format(days, minutes, hours, seconds).upper()

    return period_type


# pylint: disable=protected-access, too-few-public-methods
class MetricAlertConditionAction(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        from azure.cli.command_modules.monitor.grammar import (
            MetricAlertConditionLexer, MetricAlertConditionParser, MetricAlertConditionValidator)

        usage = 'usage error: --condition {avg,min,max,total} [NAMESPACE.]METRIC {=,!=,>,>=,<,<=} THRESHOLD\n' \
                '                         [where DIMENSION {includes,excludes} VALUE [or VALUE ...]\n' \
                '                         [and   DIMENSION {includes,excludes} VALUE [or VALUE ...] ...]]'

        string_val = ' '.join(values)

        lexer = MetricAlertConditionLexer(antlr4.InputStream(string_val))
        stream = antlr4.CommonTokenStream(lexer)
        parser = MetricAlertConditionParser(stream)
        tree = parser.expression()

        try:
            validator = MetricAlertConditionValidator()
            walker = antlr4.ParseTreeWalker()
            walker.walk(validator, tree)
            metric_condition = validator.result()
            for item in ['time_aggregation', 'metric_name', 'threshold', 'operator']:
                if not getattr(metric_condition, item, None):
                    raise CLIError(usage)
        except (AttributeError, TypeError, KeyError):
            raise CLIError(usage)
        super(MetricAlertConditionAction, self).__call__(parser, namespace, metric_condition, option_string)


# pylint: disable=protected-access, too-few-public-methods
class MetricAlertAddAction(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        from azure.mgmt.monitor.models import MetricAlertAction
        action = MetricAlertAction(
            action_group_id=values[0],
            webhook_properties=dict(x.split('=', 1) for x in values[1:]) if len(values) > 1 else None
        )
        action.odatatype = 'Microsoft.WindowsAzure.Management.Monitoring.Alerts.Models.Microsoft.AppInsights.Nexus.' \
                           'DataContracts.Resources.ScheduledQueryRules.Action'
        super(MetricAlertAddAction, self).__call__(parser, namespace, action, option_string)


# pylint: disable=too-few-public-methods
class ConditionAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        from azure.mgmt.monitor.models import ThresholdRuleCondition, RuleMetricDataSource
        # get default description if not specified
        if namespace.description is None:
            namespace.description = ' '.join(values)
        if len(values) == 1:
            # workaround because CMD.exe eats > character... Allows condition to be
            # specified as a quoted expression
            values = values[0].split(' ')
        if len(values) < 5:
            raise CLIError('usage error: --condition METRIC {>,>=,<,<=} THRESHOLD {avg,min,max,total,last} DURATION')
        metric_name = ' '.join(values[:-4])
        operator = get_operator_map()[values[-4]]
        threshold = int(values[-3])
        aggregation = get_aggregation_map()[values[-2].lower()]
        window = get_period_type()(values[-1])
        metric = RuleMetricDataSource(resource_uri=None, metric_name=metric_name)  # target URI will be filled in later
        condition = ThresholdRuleCondition(
            operator=operator, threshold=threshold, data_source=metric,
            window_size=window, time_aggregation=aggregation)
        namespace.condition = condition


# pylint: disable=protected-access
class AlertAddAction(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super(AlertAddAction, self).__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        _type = values[0].lower()
        if _type == 'email':
            from azure.mgmt.monitor.models import RuleEmailAction
            return RuleEmailAction(custom_emails=values[1:])
        if _type == 'webhook':
            from azure.mgmt.monitor.models import RuleWebhookAction
            uri = values[1]
            try:
                properties = dict(x.split('=', 1) for x in values[2:])
            except ValueError:
                raise CLIError('usage error: {} webhook URI [KEY=VALUE ...]'.format(option_string))
            return RuleWebhookAction(service_uri=uri, properties=properties)
        raise CLIError('usage error: {} TYPE KEY [ARGS]'.format(option_string))


class AlertRemoveAction(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super(AlertRemoveAction, self).__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        # TYPE is artificially enforced to create consistency with the --add-action argument
        # but it could be enhanced to do additional validation in the future.
        _type = values[0].lower()
        if _type not in ['email', 'webhook']:
            raise CLIError('usage error: {} TYPE KEY [KEY ...]'.format(option_string))
        return values[1:]


# pylint: disable=protected-access
class AutoscaleAddAction(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super(AutoscaleAddAction, self).__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        _type = values[0].lower()
        if _type == 'email':
            from azure.mgmt.monitor.models import EmailNotification
            return EmailNotification(custom_emails=values[1:])
        if _type == 'webhook':
            from azure.mgmt.monitor.models import WebhookNotification
            uri = values[1]
            try:
                properties = dict(x.split('=', 1) for x in values[2:])
            except ValueError:
                raise CLIError('usage error: {} webhook URI [KEY=VALUE ...]'.format(option_string))
            return WebhookNotification(service_uri=uri, properties=properties)
        raise CLIError('usage error: {} TYPE KEY [ARGS]'.format(option_string))


class AutoscaleRemoveAction(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super(AutoscaleRemoveAction, self).__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        # TYPE is artificially enforced to create consistency with the --add-action argument
        # but it could be enhanced to do additional validation in the future.
        _type = values[0].lower()
        if _type not in ['email', 'webhook']:
            raise CLIError('usage error: {} TYPE KEY [KEY ...]'.format(option_string))
        return values[1:]


class AutoscaleConditionAction(argparse.Action):  # pylint: disable=protected-access
    def __call__(self, parser, namespace, values, option_string=None):
        from azure.mgmt.monitor.models import MetricTrigger
        if len(values) == 1:
            # workaround because CMD.exe eats > character... Allows condition to be
            # specified as a quoted expression
            values = values[0].split(' ')
        name_offset = 0
        try:
            metric_name = ' '.join(values[name_offset:-4])
            operator = get_autoscale_operator_map()[values[-4]]
            threshold = int(values[-3])
            aggregation = get_autoscale_aggregation_map()[values[-2].lower()]
            window = get_period_type()(values[-1])
        except (IndexError, KeyError):
            raise CLIError('usage error: --condition METRIC {==,!=,>,>=,<,<=} '
                           'THRESHOLD {avg,min,max,total,count} PERIOD')
        condition = MetricTrigger(
            metric_name=metric_name,
            metric_resource_uri=None,  # will be filled in later
            time_grain=None,  # will be filled in later
            statistic=None,  # will be filled in later
            time_window=window,
            time_aggregation=aggregation,
            operator=operator,
            threshold=threshold
        )
        namespace.condition = condition


class AutoscaleScaleAction(argparse.Action):  # pylint: disable=protected-access
    def __call__(self, parser, namespace, values, option_string=None):
        from azure.mgmt.monitor.models import ScaleAction, ScaleType
        if len(values) == 1:
            # workaround because CMD.exe eats > character... Allows condition to be
            # specified as a quoted expression
            values = values[0].split(' ')
        if len(values) != 2:
            raise CLIError('usage error: --scale {in,out,to} VALUE[%]')
        dir_val = values[0]
        amt_val = values[1]
        scale_type = None
        if dir_val == 'to':
            scale_type = ScaleType.exact_count.value
        elif str(amt_val).endswith('%'):
            scale_type = ScaleType.percent_change_count.value
            amt_val = amt_val[:-1]  # strip off the percent
        else:
            scale_type = ScaleType.change_count.value

        scale = ScaleAction(
            direction=get_autoscale_scale_direction_map()[dir_val],
            type=scale_type,
            cooldown=None,  # this will be filled in later
            value=amt_val
        )
        namespace.scale = scale


class MultiObjectsDeserializeAction(argparse._AppendAction):  # pylint: disable=protected-access
    def __call__(self, parser, namespace, values, option_string=None):
        type_name = values[0]
        type_properties = values[1:]

        try:
            super(MultiObjectsDeserializeAction, self).__call__(parser,
                                                                namespace,
                                                                self.deserialize_object(type_name, type_properties),
                                                                option_string)
        except KeyError:
            raise ValueError('usage error: the type "{}" is not recognizable.'.format(type_name))
        except TypeError:
            raise ValueError(
                'usage error: Failed to parse "{}" as object of type "{}".'.format(' '.join(values), type_name))
        except ValueError as ex:
            raise ValueError(
                'usage error: Failed to parse "{}" as object of type "{}". {}'.format(
                    ' '.join(values), type_name, str(ex)))

    def deserialize_object(self, type_name, type_properties):
        raise NotImplementedError()


class ActionGroupReceiverParameterAction(MultiObjectsDeserializeAction):
    def deserialize_object(self, type_name, type_properties):
        from azure.mgmt.monitor.models import EmailReceiver, SmsReceiver, WebhookReceiver

        if type_name == 'email':
            try:
                return EmailReceiver(name=type_properties[0], email_address=type_properties[1])
            except IndexError:
                raise CLIError('usage error: --action email NAME EMAIL_ADDRESS')
        elif type_name == 'sms':
            try:
                return SmsReceiver(
                    name=type_properties[0],
                    country_code=type_properties[1],
                    phone_number=type_properties[2]
                )
            except IndexError:
                raise CLIError('usage error: --action sms NAME COUNTRY_CODE PHONE_NUMBER')
        elif type_name == 'webhook':
            try:
                return WebhookReceiver(name=type_properties[0], service_uri=type_properties[1])
            except IndexError:
                raise CLIError('usage error: --action webhook NAME URI')
        else:
            raise ValueError('usage error: the type "{}" is not recognizable.'.format(type_name))
