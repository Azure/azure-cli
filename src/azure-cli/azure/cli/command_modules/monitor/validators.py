# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.validators import validate_tags, get_default_location_from_resource_group
from azure.cli.core.azclierror import RequiredArgumentMissingError, InvalidArgumentValueError

from knack.util import CLIError


def process_autoscale_create_namespace(cmd, namespace):
    from msrestazure.tools import parse_resource_id

    validate_tags(namespace)
    get_target_resource_validator('resource', required=True, preserve_resource_group_parameter=True)(cmd, namespace)
    if not namespace.resource_group_name:
        namespace.resource_group_name = parse_resource_id(namespace.resource).get('resource_group', None)
    get_default_location_from_resource_group(cmd, namespace)


def validate_autoscale_recurrence(namespace):
    from azure.mgmt.monitor.models import Recurrence, RecurrentSchedule, RecurrenceFrequency

    def _validate_weekly_recurrence(namespace):
        # Construct days
        valid_days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        days = []
        for partial in namespace.recurrence[1:]:
            if len(partial) < 2:
                raise CLIError('specifying fewer than 2 characters for day is ambiguous.')
            try:
                match = next(x for x in valid_days if x.lower().startswith(partial.lower()))
            except StopIteration:
                raise CLIError("No match for day '{}'.".format(partial))
            days.append(match)
            valid_days.remove(match)

        # validate, but don't process start and end time
        recurrence_obj = Recurrence(
            frequency=RecurrenceFrequency.week,
            schedule=RecurrentSchedule(
                time_zone=namespace.timezone,
                days=days,
                hours=[],  # will be filled in during custom command
                minutes=[]  # will be filled in during custom command
            )
        )
        return recurrence_obj

    valid_recurrence = {
        'week': {
            'usage': '-r week [DAY DAY ...]',
            'validator': _validate_weekly_recurrence
        }
    }
    if namespace.recurrence:
        raw_values = namespace.recurrence
        try:
            delimiter = raw_values[0].lower()
            usage = valid_recurrence[delimiter]['usage']
            try:
                namespace.recurrence = valid_recurrence[delimiter]['validator'](namespace)
            except CLIError as ex:
                raise CLIError('{} invalid usage: {}'.format(ex, usage))
        except KeyError:
            raise CLIError('invalid usage: -r {{{}}} [ARG ARG ...]'.format(','.join(valid_recurrence)))


def validate_autoscale_timegrain(namespace):
    from azure.mgmt.monitor.models import MetricTrigger
    from azure.cli.command_modules.monitor.actions import get_period_type
    from azure.cli.command_modules.monitor.util import get_autoscale_statistic_map

    values = namespace.timegrain
    if len(values) == 1:
        # workaround because CMD.exe eats > character... Allows condition to be
        # specified as a quoted expression
        values = values[0].split(' ')
    name_offset = 0
    try:
        time_grain = get_period_type()(values[1])
        name_offset += 1
    except ValueError:
        time_grain = get_period_type()('1m')
    try:
        statistic = get_autoscale_statistic_map()[values[0]]
        name_offset += 1
    except KeyError:
        statistic = get_autoscale_statistic_map()['avg']
    timegrain = MetricTrigger(
        metric_name=None,
        metric_resource_uri=None,
        time_grain=time_grain,
        statistic=statistic,
        time_window=None,
        time_aggregation=None,
        operator=None,
        threshold=None
    )
    namespace.timegrain = timegrain


def get_target_resource_validator(dest, required, preserve_resource_group_parameter=False, alias='resource'):
    def _validator(cmd, namespace):
        from msrestazure.tools import is_valid_resource_id
        name_or_id = getattr(namespace, dest)
        rg = namespace.resource_group_name
        res_ns = namespace.namespace
        parent = namespace.parent
        res_type = namespace.resource_type

        usage_error = CLIError('usage error: --{0} ID | --{0} NAME --resource-group NAME '
                               '--{0}-type TYPE [--{0}-parent PARENT] '
                               '[--{0}-namespace NAMESPACE]'.format(alias))
        if not name_or_id and required:
            raise usage_error
        if name_or_id:
            if is_valid_resource_id(name_or_id) and any((res_ns, parent, res_type)):
                raise usage_error
            if not is_valid_resource_id(name_or_id):
                from azure.cli.core.commands.client_factory import get_subscription_id
                if res_type and '/' in res_type:
                    res_ns = res_ns or res_type.rsplit('/', 1)[0]
                    res_type = res_type.rsplit('/', 1)[1]
                if not all((rg, res_ns, res_type, name_or_id)):
                    raise usage_error

                setattr(namespace, dest,
                        '/subscriptions/{}/resourceGroups/{}/providers/{}/{}{}/{}'.format(
                            get_subscription_id(cmd.cli_ctx), rg, res_ns, parent + '/' if parent else '',
                            res_type, name_or_id))

        del namespace.namespace
        del namespace.parent
        del namespace.resource_type
        if not preserve_resource_group_parameter:
            del namespace.resource_group_name

    return _validator


def validate_metrics_alert_dimension(namespace):
    from azure.cli.command_modules.monitor.grammar.metric_alert.MetricAlertConditionValidator import dim_op_conversion
    for keyword, value in dim_op_conversion.items():
        if namespace.operator == value:
            namespace.operator = keyword


def validate_metrics_alert_condition(namespace):
    from azure.cli.command_modules.monitor.grammar.metric_alert.MetricAlertConditionValidator import op_conversion, \
        agg_conversion, sens_conversion
    for keyword, value in agg_conversion.items():
        if namespace.aggregation == value:
            namespace.aggregation = keyword
            break
    for keyword, value in op_conversion.items():
        if namespace.operator == value:
            namespace.operator = keyword
            break

    if namespace.condition_type == 'static':
        if namespace.threshold is None:
            raise RequiredArgumentMissingError('Parameter --threshold is required for static threshold.')
        if namespace.operator not in ('=', '!=', '>', '>=', '<', '<='):
            raise InvalidArgumentValueError('Parameter --operator {} is invalid for static threshold.'.format(
                op_conversion[namespace.operator]
            ))
    elif namespace.condition_type == 'dynamic':
        if namespace.operator not in ('>', '<', '><'):
            raise InvalidArgumentValueError('Parameter --operator {} is invalid for dynamic threshold.'.format(
                op_conversion[namespace.operator]
            ))
        if namespace.alert_sensitivity is None:
            raise RequiredArgumentMissingError('Parameter --sensitivity is required for dynamic threshold.')
        for keyword, value in sens_conversion.items():
            if namespace.alert_sensitivity == value:
                namespace.alert_sensitivity = keyword
                break

        if namespace.number_of_evaluation_periods is None:
            setattr(namespace, 'number_of_evaluation_periods', 4)

        if namespace.number_of_evaluation_periods < 1 or namespace.number_of_evaluation_periods > 6:
            raise InvalidArgumentValueError('Parameter --num-periods {} should in range 1-6.'.format(
                namespace.number_of_evaluation_periods
            ))

        if namespace.min_failing_periods_to_alert is None:
            setattr(namespace, 'min_failing_periods_to_alert', min(4, namespace.number_of_evaluation_periods))

        if namespace.min_failing_periods_to_alert < 1 or namespace.min_failing_periods_to_alert > 6:
            raise InvalidArgumentValueError('Parameter --num-violations {} should in range 1-6.'.format(
                namespace.min_failing_periods_to_alert
            ))

        if namespace.min_failing_periods_to_alert > namespace.number_of_evaluation_periods:
            raise InvalidArgumentValueError(
                'Parameter --num-violations {} should be less than or equal to parameter --num-periods {}.'.format(
                    namespace.min_failing_periods_to_alert, namespace.number_of_evaluation_periods))
    else:
        raise NotImplementedError()


def validate_diagnostic_settings(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id, parse_resource_id

    get_target_resource_validator('resource_uri', required=True, preserve_resource_group_parameter=True)(cmd, namespace)
    if not namespace.resource_group_name:
        namespace.resource_group_name = parse_resource_id(namespace.resource_uri)['resource_group']

    if namespace.storage_account and not is_valid_resource_id(namespace.storage_account):
        namespace.storage_account = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                                resource_group=namespace.resource_group_name,
                                                namespace='microsoft.Storage',
                                                type='storageAccounts',
                                                name=namespace.storage_account)

    if namespace.workspace and not is_valid_resource_id(namespace.workspace):
        namespace.workspace = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                          resource_group=namespace.resource_group_name,
                                          namespace='microsoft.OperationalInsights',
                                          type='workspaces',
                                          name=namespace.workspace)

    if namespace.event_hub and is_valid_resource_id(namespace.event_hub):
        namespace.event_hub = parse_resource_id(namespace.event_hub)['name']

    if namespace.event_hub_rule:
        if not is_valid_resource_id(namespace.event_hub_rule):
            if not namespace.event_hub:
                raise CLIError('usage error: --event-hub-rule ID | --event-hub-rule NAME --event-hub NAME')
            # use value from --event-hub if the rule is a name
            namespace.event_hub_rule = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.EventHub',
                type='namespaces',
                name=namespace.event_hub,
                child_type_1='AuthorizationRules',
                child_name_1=namespace.event_hub_rule)
        elif not namespace.event_hub:
            # extract the event hub name from `--event-hub-rule` if provided as an ID
            namespace.event_hub = parse_resource_id(namespace.event_hub_rule)['name']

    if not any([namespace.storage_account, namespace.workspace, namespace.event_hub]):
        raise CLIError(
            'usage error - expected one or more:  --storage-account NAME_OR_ID | --workspace NAME_OR_ID '
            '| --event-hub NAME_OR_ID | --event-hub-rule ID')

    try:
        del namespace.resource_group_name
    except AttributeError:
        pass


def _validate_tags(namespace):
    """ Extracts multiple space-separated tags in key[=value] format """
    if isinstance(namespace.tags, list):
        tags_dict = {}
        for item in namespace.tags:
            tags_dict.update(_validate_tag(item))
        namespace.tags = tags_dict


def _validate_tag(string):
    """ Extracts a single tag in key[=value] format """
    result = {}
    if string:
        comps = string.split('=', 1)
        result = {comps[0]: comps[1]} if len(comps) > 1 else {string: ''}
    return result


def process_action_group_detail_for_creation(namespace):
    from azure.mgmt.monitor.models import ActionGroupResource, EmailReceiver, SmsReceiver, WebhookReceiver, \
        ArmRoleReceiver, AzureAppPushReceiver, ItsmReceiver, AutomationRunbookReceiver, \
        VoiceReceiver, LogicAppReceiver, AzureFunctionReceiver, EventHubReceiver

    _validate_tags(namespace)

    ns = vars(namespace)
    name = ns['action_group_name']
    receivers = ns.pop('receivers') or []
    action_group_resource_properties = {
        'location': 'global',  # as of now, 'global' is the only available location for action group
        'group_short_name': ns.pop('short_name') or name[:12],  # '12' is the short name length limitation
        'email_receivers': [r for r in receivers if isinstance(r, EmailReceiver)],
        'sms_receivers': [r for r in receivers if isinstance(r, SmsReceiver)],
        'webhook_receivers': [r for r in receivers if isinstance(r, WebhookReceiver)],
        'arm_role_receivers': [r for r in receivers if isinstance(r, ArmRoleReceiver)],
        'itsm_receivers': [r for r in receivers if isinstance(r, ItsmReceiver)],
        'azure_app_push_receivers': [r for r in receivers if isinstance(r, AzureAppPushReceiver)],
        'automation_runbook_receivers': [r for r in receivers if isinstance(r, AutomationRunbookReceiver)],
        'voice_receivers': [r for r in receivers if isinstance(r, VoiceReceiver)],
        'logic_app_receivers': [r for r in receivers if isinstance(r, LogicAppReceiver)],
        'azure_function_receivers': [r for r in receivers if isinstance(r, AzureFunctionReceiver)],
        'event_hub_receivers': [r for r in receivers if isinstance(r, EventHubReceiver)],
        'tags': ns.get('tags') or None
    }
    if hasattr(namespace, 'tags'):
        del namespace.tags

    ns['action_group'] = ActionGroupResource(**action_group_resource_properties)


def validate_metric_dimension(namespace):

    if not namespace.dimension:
        return

    if namespace.filters:
        raise CLIError('usage: --dimension and --filter parameters are mutually exclusive.')

    namespace.filters = ' and '.join("{} eq '*'".format(d) for d in namespace.dimension)


def process_webhook_prop(namespace):
    if not isinstance(namespace.webhook_properties, list):
        return

    result = {}
    for each in namespace.webhook_properties:
        if each:
            if '=' in each:
                key, value = each.split('=', 1)
            else:
                key, value = each, ''
            result[key] = value

    namespace.webhook_properties = result


def get_action_group_validator(dest):
    def validate_action_groups(cmd, namespace):
        action_groups = getattr(namespace, dest, None)

        if not action_groups:
            return

        from msrestazure.tools import is_valid_resource_id, resource_id
        from azure.cli.core.commands.client_factory import get_subscription_id

        subscription = get_subscription_id(cmd.cli_ctx)
        resource_group = namespace.resource_group_name
        for group in action_groups:
            if not is_valid_resource_id(group.action_group_id):
                group.action_group_id = resource_id(
                    subscription=subscription,
                    resource_group=resource_group,
                    namespace='microsoft.insights',
                    type='actionGroups',
                    name=group.action_group_id
                )
    return validate_action_groups


def get_action_group_id_validator(dest):
    def validate_action_group_ids(cmd, namespace):
        action_groups = getattr(namespace, dest, None)

        if not action_groups:
            return

        from msrestazure.tools import is_valid_resource_id, resource_id
        from azure.cli.core.commands.client_factory import get_subscription_id

        action_group_ids = []
        subscription = get_subscription_id(cmd.cli_ctx)
        resource_group = namespace.resource_group_name
        for group in action_groups:
            if not is_valid_resource_id(group):
                group = resource_id(
                    subscription=subscription,
                    resource_group=resource_group,
                    namespace='microsoft.insights',
                    type='actionGroups',
                    name=group
                )
            action_group_ids.append(group.lower())
        setattr(namespace, dest, action_group_ids)
    return validate_action_group_ids


def validate_private_endpoint_connection_id(namespace):
    if namespace.connection_id:
        from azure.cli.core.util import parse_proxy_resource_id
        result = parse_proxy_resource_id(namespace.connection_id)
        namespace.resource_group_name = result['resource_group']
        namespace.scope_name = result['name']
        namespace.private_endpoint_connection_name = result['child_name_1']

    if not all([namespace.scope_name, namespace.resource_group_name, namespace.private_endpoint_connection_name]):
        raise CLIError('incorrect usage. Please provide [--id ID] or [--name NAME --scope-name NAME -g NAME]')

    del namespace.connection_id


def validate_storage_accounts_name_or_id(cmd, namespace):
    if namespace.storage_account_ids:
        from msrestazure.tools import is_valid_resource_id, resource_id
        from azure.cli.core.commands.client_factory import get_subscription_id
        for index, storage_account_id in enumerate(namespace.storage_account_ids):
            if not is_valid_resource_id(storage_account_id):
                namespace.storage_account_ids[index] = resource_id(
                    subscription=get_subscription_id(cmd.cli_ctx),
                    resource_group=namespace.resource_group_name,
                    namespace='Microsoft.Storage',
                    type='storageAccounts',
                    name=storage_account_id
                )


def process_subscription_id(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    namespace.subscription_id = get_subscription_id(cmd.cli_ctx)


def process_workspace_data_export_destination(namespace):
    if namespace.destination:
        from azure.mgmt.core.tools import is_valid_resource_id, resource_id, parse_resource_id
        if not is_valid_resource_id(namespace.destination):
            raise CLIError('usage error: --destination should be a storage account, '
                           'an evenhug namespace or an event hub resource id.')
        result = parse_resource_id(namespace.destination)
        if result['namespace'].lower() == 'microsoft.storage' and result['type'].lower() == 'storageaccounts':
            namespace.data_export_type = 'StorageAccount'
        elif result['namespace'].lower() == 'microsoft.eventhub' and result['type'].lower() == 'namespaces':
            namespace.data_export_type = 'EventHub'
            namespace.destination = resource_id(
                subscription=result['subscription'],
                resource_group=result['resource_group'],
                namespace=result['namespace'],
                type=result['type'],
                name=result['name']
            )
            if 'child_type_1' in result and result['child_type_1'].lower() == 'eventhubs':
                namespace.event_hub_name = result['child_name_1']
        else:
            raise CLIError('usage error: --destination should be a storage account, '
                           'an evenhug namespace or an event hub resource id.')
