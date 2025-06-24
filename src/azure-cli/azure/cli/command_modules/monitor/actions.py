# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access, too-few-public-methods
import copy
import argparse

from knack.arguments import CLIArgumentType
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.command_modules.monitor.util import get_autoscale_scale_direction_map

from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.core.aaz._arg import AAZCompoundTypeArg, AAZListType
from azure.cli.core.aaz._arg_fmt import AAZListArgFormat
from azure.cli.core.aaz._base import AAZUndefined, AAZBlankArgValue
from azure.cli.core.aaz._arg_action import AAZCompoundTypeArgAction, AAZArgActionOperations, \
    _ELEMENT_APPEND_KEY, AAZSimpleTypeArgAction
from azure.cli.core.aaz._help import AAZShowHelp
from azure.cli.core.aaz.exceptions import AAZInvalidValueError
from azure.cli.core.aaz._prompt import AAZPromptInput

logger = get_logger(__name__)


def timezone_name_type(value):
    from azure.cli.command_modules.monitor._autoscale_util import AUTOSCALE_TIMEZONES
    zone = next((x['name'] for x in AUTOSCALE_TIMEZONES if x['name'].lower() == value.lower()), None)
    if not zone:
        raise InvalidArgumentValueError(
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
        raise InvalidArgumentValueError('Offset out of range: -12 to +14')

    if 0 <= hour < 10:
        value = '+0{}'.format(hour)
    elif hour >= 10:
        value = '+{}'.format(hour)
    elif -10 < hour < 0:
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
            raise ValueError('PERIOD should be of the form "##h##m##s" or ISO8601')
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


# pylint: disable=redefined-builtin
def get_date_midnight_type(help=None):

    help_string = help + ' ' if help else ''
    accepted_formats = ['date (yyyy-mm-dd)', 'time (hh:mm:ss.xxxxx)', 'timezone (+/-hh:mm)']
    help_string = help_string + 'Format: ' + ' '.join(accepted_formats)

    # pylint: disable=too-few-public-methods
    class DateAction(argparse.Action):

        def __call__(self, parser, namespace, values, option_string=None):
            """ Parse a date value and return the ISO8601 string. """
            import dateutil.parser
            import dateutil.tz

            value_string = ' '.join(values)
            dt_val = None
            try:
                # attempt to parse ISO 8601
                dt_val = dateutil.parser.parse(value_string)
            except ValueError:
                pass

            # TODO: custom parsing attempts here
            if not dt_val:
                raise CLIError("Unable to parse: '{}'. Expected format: {}".format(value_string, help_string))
            if dt_val.tzinfo:
                logger.warning('Timezone info will be ignored in %s.', value_string)
            dt_val = dt_val.replace(tzinfo=dateutil.tz.tzutc())

            # Issue warning if any supplied time will be ignored
            if any([dt_val.hour, dt_val.minute, dt_val.second, dt_val.microsecond]):
                logger.warning('Time info will be set to midnight UTC for %s.', value_string)
            date_midnight = dt_val.replace(hour=0, minute=0, second=0, microsecond=0)
            format_string = date_midnight.isoformat()
            logger.info('Time info set to midnight UTC from %s to %s', value_string, format_string)
            setattr(namespace, self.dest, format_string)

    return CLIArgumentType(action=DateAction, nargs='+', help=help_string)


# pylint: disable=protected-access, too-few-public-methods
class MetricAlertConditionAction(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        # antlr4 is not available everywhere, restrict the import scope so that commands
        # that do not need it don't fail when it is absent
        import antlr4

        from azure.cli.command_modules.monitor.grammar.metric_alert import (
            MetricAlertConditionLexer, MetricAlertConditionParser, MetricAlertConditionValidator)

        usage = 'usage error: --condition {avg,min,max,total,count} [NAMESPACE.]METRIC\n' \
                '                         [{=,!=,>,>=,<,<=} THRESHOLD]\n' \
                '                         [{<,>,><} dynamic SENSITIVITY VIOLATION of EVALUATION [since DATETIME]]\n' \
                '                         [where DIMENSION {includes,excludes} VALUE [or VALUE ...]\n' \
                '                         [and   DIMENSION {includes,excludes} VALUE [or VALUE ...] ...]]\n' \
                '                         [with skipmetricvalidation]'

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
            if "static" in metric_condition:
                # static metric criteria
                for item in ['time_aggregation', 'metric_name', 'operator', 'threshold']:
                    if item not in metric_condition["static"]:
                        raise InvalidArgumentValueError(usage)
            elif "dynamic" in metric_condition:
                # dynamic metric criteria
                for item in ['time_aggregation', 'metric_name', 'operator', 'alert_sensitivity', 'failing_periods']:
                    if item not in metric_condition["dynamic"]:
                        raise InvalidArgumentValueError(usage)
            else:
                raise NotImplementedError()
        except (AttributeError, TypeError, KeyError):
            raise InvalidArgumentValueError(usage)
        super().__call__(parser, namespace, metric_condition, option_string)


# pylint: disable=protected-access, too-few-public-methods
class MetricAlertAddAction(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        action_group_id = values[0]
        try:
            webhook_property_candidates = dict(x.split('=', 1) for x in values[1:]) if len(values) > 1 else None
        except ValueError:
            err_msg = "value of {} is invalid. Please refer to --help to get insight of correct format".format(
                option_string
            )
            raise InvalidArgumentValueError(err_msg)

        action = {
            "action_group_id": action_group_id,
            "web_hook_properties": webhook_property_candidates
        }
        action["odatatype"] = "Microsoft.WindowsAzure.Management.Monitoring.Alerts.Models.Microsoft.AppInsights." \
                              "Nexus.DataContracts.Resources.ScheduledQueryRules.Action"
        super().__call__(parser, namespace, action, option_string)


class AlertRemoveAction(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super().__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        # TYPE is artificially enforced to create consistency with the --add-action argument
        # but it could be enhanced to do additional validation in the future.
        _type = values[0].lower()
        if _type not in ['email', 'webhook']:
            raise InvalidArgumentValueError('{} TYPE KEY [KEY ...]'.format(option_string))
        return values[1:]


# pylint: disable=protected-access
class AutoscaleCreateAction(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super().__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        _type = values[0].lower()
        if _type == 'email':
            return {
                "key": "email",
                "value": {
                    "custom_emails": values[1:]
                }
            }
        if _type == 'webhook':
            uri = values[1]
            try:
                properties = dict(x.split('=', 1) for x in values[2:])
            except ValueError:
                raise InvalidArgumentValueError('{} webhook URI [KEY=VALUE ...]'.format(option_string))
            return {
                "key": "webhook",
                "value": {
                    "service_uri": uri,
                    "properties": properties
                }
            }
        raise InvalidArgumentValueError('{} TYPE KEY [ARGS]'.format(option_string))


# pylint: disable=protected-access
class AutoscaleAddAction(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super().__call__(parser, namespace, action, option_string)

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
                raise InvalidArgumentValueError('{} webhook URI [KEY=VALUE ...]'.format(option_string))
            return WebhookNotification(service_uri=uri, properties=properties)
        raise InvalidArgumentValueError('{} TYPE KEY [ARGS]'.format(option_string))


class AutoscaleRemoveAction(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        action = self.get_action(values, option_string)
        super().__call__(parser, namespace, action, option_string)

    def get_action(self, values, option_string):  # pylint: disable=no-self-use
        # TYPE is artificially enforced to create consistency with the --add-action argument
        # but it could be enhanced to do additional validation in the future.
        _type = values[0].lower()
        if _type not in ['email', 'webhook']:
            raise InvalidArgumentValueError('{} TYPE KEY [KEY ...]'.format(option_string))
        return values[1:]


class AutoscaleConditionAction(argparse.Action):  # pylint: disable=protected-access
    def __call__(self, parser, namespace, values, option_string=None):
        # antlr4 is not available everywhere, restrict the import scope so that commands
        # that do not need it don't fail when it is absent
        import antlr4

        from azure.cli.command_modules.monitor.grammar.autoscale import (
            AutoscaleConditionLexer, AutoscaleConditionParser, AutoscaleConditionValidator)

        # pylint: disable=line-too-long
        usage = '--condition ["NAMESPACE"] METRIC {==,!=,>,>=,<,<=} THRESHOLD {avg,min,max,total,count} PERIOD\n' \
                '            [where DIMENSION {==,!=} VALUE [or VALUE ...]\n' \
                '            [and   DIMENSION {==,!=} VALUE [or VALUE ...] ...]]'

        string_val = ' '.join(values)

        lexer = AutoscaleConditionLexer(antlr4.InputStream(string_val))
        stream = antlr4.CommonTokenStream(lexer)
        parser = AutoscaleConditionParser(stream)
        tree = parser.expression()

        try:
            validator = AutoscaleConditionValidator()
            walker = antlr4.ParseTreeWalker()
            walker.walk(validator, tree)
            autoscale_condition = validator.result()
            for item in ['time_aggregation', 'metric_name', 'threshold', 'operator', 'time_window']:
                if not getattr(autoscale_condition, item, None):
                    raise InvalidArgumentValueError(usage)
        except (AttributeError, TypeError, KeyError):
            raise InvalidArgumentValueError(usage)

        namespace.condition = autoscale_condition


class AutoscaleScaleAction(argparse.Action):  # pylint: disable=protected-access
    def __call__(self, parser, namespace, values, option_string=None):
        from azure.mgmt.monitor.models import ScaleAction, ScaleType
        if len(values) == 1:
            # workaround because CMD.exe eats > character... Allows condition to be
            # specified as a quoted expression
            values = values[0].split(' ')
        if len(values) != 2:
            raise InvalidArgumentValueError('--scale {in,out,to} VALUE[%]')
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
            super().__call__(parser,
                             namespace,
                             self.deserialize_object(type_name, type_properties),
                             option_string)
        except KeyError:
            raise InvalidArgumentValueError('the type "{}" is not recognizable.'.format(type_name))
        except TypeError:
            raise InvalidArgumentValueError(
                'Failed to parse "{}" as object of type "{}".'.format(' '.join(values), type_name))
        except ValueError as ex:
            raise InvalidArgumentValueError(
                'Failed to parse "{}" as object of type "{}". {}'.format(
                    ' '.join(values), type_name, str(ex)))

    def deserialize_object(self, type_name, type_properties):
        raise NotImplementedError()


class ActionGroupReceiverParameterAction(MultiObjectsDeserializeAction):
    def deserialize_object(self, type_name, type_properties):
        from azure.mgmt.monitor.models import EmailReceiver, SmsReceiver, WebhookReceiver, \
            ArmRoleReceiver, AzureAppPushReceiver, ItsmReceiver, AutomationRunbookReceiver, \
            VoiceReceiver, LogicAppReceiver, AzureFunctionReceiver, EventHubReceiver
        syntax = {
            'email': 'NAME EMAIL_ADDRESS [usecommonalertschema]',
            'sms': 'NAME COUNTRY_CODE PHONE_NUMBER',
            'webhook': 'NAME URI [useaadauth OBJECT_ID IDENTIFIER URI] [usecommonalertschema]',
            'armrole': 'NAME ROLE_ID [usecommonalertschema]',
            'azureapppush': 'NAME EMAIL_ADDRESS',
            'itsm': 'NAME WORKSPACE_ID CONNECTION_ID TICKET_CONFIG REGION',
            'automationrunbook': 'NAME AUTOMATION_ACCOUNT_ID RUNBOOK_NAME WEBHOOK_RESOURCE_ID '
                                 'SERVICE_URI [isglobalrunbook] [usecommonalertschema]',
            'voice': 'NAME COUNTRY_CODE PHONE_NUMBER',
            'logicapp': 'NAME RESOURCE_ID CALLBACK_URL [usecommonalertschema]',
            'azurefunction': 'NAME FUNCTION_APP_RESOURCE_ID '
                             'FUNCTION_NAME HTTP_TRIGGER_URL [usecommonalertschema]',
            'eventhub': 'NAME SUBSCRIPTION_ID EVENT_HUB_NAME_SPACE EVENT_HUB_NAME [usecommonalertschema] '
        }

        receiver = None
        useCommonAlertSchema = 'usecommonalertschema' in (property.lower() for property in type_properties)
        try:
            if type_name == 'email':
                receiver = EmailReceiver(name=type_properties[0], email_address=type_properties[1],
                                         use_common_alert_schema=useCommonAlertSchema)
            elif type_name == 'sms':
                receiver = SmsReceiver(
                    name=type_properties[0],
                    country_code=type_properties[1],
                    phone_number=type_properties[2]
                )
            elif type_name == 'webhook':
                useAadAuth = len(type_properties) >= 3 and type_properties[2] == 'useaadauth'
                object_id = type_properties[3] if useAadAuth else None
                identifier_uri = type_properties[4] if useAadAuth else None
                receiver = WebhookReceiver(name=type_properties[0], service_uri=type_properties[1],
                                           use_common_alert_schema=useCommonAlertSchema,
                                           use_aad_auth=useAadAuth, object_id=object_id,
                                           identifier_uri=identifier_uri)
            elif type_name == 'armrole':
                receiver = ArmRoleReceiver(name=type_properties[0], role_id=type_properties[1],
                                           use_common_alert_schema=useCommonAlertSchema)
            elif type_name == 'azureapppush':
                receiver = AzureAppPushReceiver(name=type_properties[0], email_address=type_properties[1])
            elif type_name == 'itsm':
                receiver = ItsmReceiver(name=type_properties[0], workspace_id=type_properties[1],
                                        connection_id=type_properties[2], ticket_configuration=type_properties[3],
                                        region=type_properties[4])
            elif type_name == 'automationrunbook':
                isGlobalRunbook = 'isglobalrunbook' in (property.lower() for property in type_properties)
                receiver = AutomationRunbookReceiver(name=type_properties[0], automation_account_id=type_properties[1],
                                                     runbook_name=type_properties[2],
                                                     webhook_resource_id=type_properties[3],
                                                     service_uri=type_properties[4],
                                                     is_global_runbook=isGlobalRunbook,
                                                     use_common_alert_schema=useCommonAlertSchema)
            elif type_name == 'voice':
                receiver = VoiceReceiver(
                    name=type_properties[0],
                    country_code=type_properties[1],
                    phone_number=type_properties[2]
                )
            elif type_name == 'logicapp':
                receiver = LogicAppReceiver(name=type_properties[0], resource_id=type_properties[1],
                                            callback_url=type_properties[2],
                                            use_common_alert_schema=useCommonAlertSchema)
            elif type_name == 'azurefunction':
                receiver = AzureFunctionReceiver(name=type_properties[0], function_app_resource_id=type_properties[1],
                                                 function_name=type_properties[2],
                                                 http_trigger_url=type_properties[3],
                                                 use_common_alert_schema=useCommonAlertSchema)
            elif type_name == 'eventhub':
                receiver = EventHubReceiver(name=type_properties[0], subscription_id=type_properties[1],
                                            event_hub_name_space=type_properties[2], event_hub_name=type_properties[3],
                                            use_common_alert_schema=useCommonAlertSchema)
            else:
                raise InvalidArgumentValueError('The type "{}" is not recognizable.'.format(type_name))

        except IndexError:
            raise InvalidArgumentValueError('--action {}'.format(syntax[type_name]))
        return receiver


class AAZCustomListArgAction(AAZCompoundTypeArgAction):

    def __call__(self, parser, namespace, values, option_string=None):
        if not isinstance(getattr(namespace, self.dest), AAZArgActionOperations):
            # overwrite existing namespace value which is not an instance of AAZArgActionOperations.
            # especially the default value of argument.
            setattr(namespace, self.dest, AAZArgActionOperations())
        dest_ops = getattr(namespace, self.dest)
        try:
            if self._schema.singular_options and option_string in self._schema.singular_options:
                # if singular option is used then parsed values by element action
                action = self._schema.Element._build_cmd_action()
                action.setup_operations(dest_ops, values, prefix_keys=[_ELEMENT_APPEND_KEY])
            else:
                self.setup_operations(dest_ops, values)
        except (ValueError, KeyError) as ex:
            raise InvalidArgumentValueError(f"Failed to parse '{option_string}' argument: {ex}") from ex
        except AAZShowHelp as aaz_help:
            aaz_help.keys = (option_string, *aaz_help.keys)
            self.show_aaz_help(parser, aaz_help)

    @classmethod
    def setup_operations(cls, dest_ops, values, prefix_keys=None):
        if prefix_keys is None:
            prefix_keys = []
        if values is None or values == []:
            if cls._schema._blank == AAZUndefined:
                raise AAZInvalidValueError("argument cannot be blank")
            assert not isinstance(cls._schema._blank, AAZPromptInput), "Prompt input is not supported in List args."
            dest_ops.add(copy.deepcopy(cls._schema._blank), *prefix_keys)
        else:
            assert isinstance(values, list)
            ops = []

            # This part of logic is to support Separate Elements Expression which is widely used in current command,
            # such as:
            #       --args val1 val2 val3.
            # The standard expression of it should be:
            #       --args [val1,val2,val3]

            element_action = cls._schema.Element._build_cmd_action()
            if not issubclass(element_action, AAZSimpleTypeArgAction):
                # Separate Elements Expression only supported for simple type element array
                raise AAZInvalidValueError("Element action is not nullable")

            # dest_ops
            try:
                element_ops = AAZArgActionOperations()
                for value in values:
                    element_action.setup_operations(element_ops, value, prefix_keys=[_ELEMENT_APPEND_KEY])
            except AAZShowHelp as aaz_help:
                aaz_help.schema = cls._schema
                aaz_help.keys = (0, *aaz_help.keys)
                raise aaz_help

            elements = []
            for _, data in element_ops._ops:
                elements.append(data)
            ops = [([], elements)]

        for key_parts, data in ops:
            dest_ops.add(data, *prefix_keys, *key_parts)

    @classmethod
    def format_data(cls, data):
        if data == AAZBlankArgValue:
            if cls._schema._blank == AAZUndefined:
                raise AAZInvalidValueError("argument value cannot be blank")
            assert not isinstance(cls._schema._blank, AAZPromptInput), "Prompt input is not supported in List args."
            data = copy.deepcopy(cls._schema._blank)

        if data is None:
            if cls._schema._nullable:
                return data
            raise AAZInvalidValueError("field is not nullable")

        if isinstance(data, list):
            result = []
            action = cls._schema.Element._build_cmd_action()
            for idx, value in enumerate(data):
                try:
                    result.append(action.format_data(value))
                except AAZInvalidValueError as ex:
                    raise AAZInvalidValueError(f"Invalid at [{idx}] : {ex}") from ex
            return result

        raise AAZInvalidValueError(f"list type value expected, got '{data}'({type(data)})")


class AAZCustomListArg(AAZCompoundTypeArg, AAZListType):

    def __init__(self, fmt=None, singular_options=None, **kwargs):
        fmt = fmt or AAZListArgFormat()
        super().__init__(fmt=fmt, **kwargs)
        self.singular_options = singular_options

    def to_cmd_arg(self, name, **kwargs):
        arg = super().to_cmd_arg(name, **kwargs)
        if self.singular_options:
            assert arg.options_list
            arg.options_list.extend(self.singular_options)  # support to parse singular options

        if self._blank != AAZUndefined:
            arg.nargs = '*'
        else:
            arg.nargs = '+'
        return arg

    def _build_cmd_action(self):
        class Action(AAZCustomListArgAction):
            _schema = self  # bind action class with current schema

        return Action

    @property
    def _type_in_help(self):
        return f"List<{self.Element._type_in_help}>"
