# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.validators import validate_tags, get_default_location_from_resource_group


def process_autoscale_create_namespace(cmd, namespace):
    from msrestazure.tools import parse_resource_id

    validate_tags(namespace)
    get_target_resource_validator('resource', required=True, preserve_resource_group_parameter=True)(cmd, namespace)
    if not namespace.resource_group_name:
        namespace.resource_group_name = parse_resource_id(namespace.resource).get('resource_group', None)
    get_default_location_from_resource_group(cmd, namespace)


def validate_autoscale_recurrence(namespace):
    from knack.util import CLIError
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
        except KeyError as ex:
            raise CLIError('invalid usage: -r {{{}}} [ARG ARG ...]'.format(','.join(valid_recurrence)))


def validate_autoscale_timegrain(namespace):
    from azure.mgmt.monitor.models import MetricTrigger
    from azure.cli.command_modules.monitor.actions import period_type
    from azure.cli.command_modules.monitor.util import get_autoscale_statistic_map

    values = namespace.timegrain
    if len(values) == 1:
        # workaround because CMD.exe eats > character... Allows condition to be
        # specified as a quoted expression
        values = values[0].split(' ')
    name_offset = 0
    try:
        time_grain = period_type(values[1])
        name_offset += 1
    except ValueError:
        time_grain = period_type('1m')
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
        from knack.util import CLIError
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
        elif name_or_id:
            if is_valid_resource_id(name_or_id) and any((res_ns, parent, res_type)):
                raise usage_error
            elif not is_valid_resource_id(name_or_id):
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


def validate_diagnostic_settings(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id
    from knack.util import CLIError
    resource_group_error = "--resource-group is required when name is provided for storage account or workspace or " \
                           "service bus namespace and rule. "

    get_target_resource_validator('resource_uri', required=True, preserve_resource_group_parameter=True)(cmd, namespace)

    if namespace.storage_account and not is_valid_resource_id(namespace.storage_account):
        if namespace.resource_group_name is None:
            raise CLIError(resource_group_error)
        namespace.storage_account = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                                resource_group=namespace.resource_group_name,
                                                namespace='microsoft.Storage',
                                                type='storageAccounts',
                                                name=namespace.storage_account)

    if namespace.workspace and not is_valid_resource_id(namespace.workspace):
        if namespace.resource_group_name is None:
            raise CLIError(resource_group_error)
        namespace.workspace = resource_id(subscription=get_subscription_id(cmd.cli_ctx),
                                          resource_group=namespace.resource_group_name,
                                          namespace='microsoft.OperationalInsights',
                                          type='workspaces',
                                          name=namespace.workspace)

    if not namespace.storage_account and not namespace.workspace and not namespace.event_hub:
        raise CLIError(
            'One of the following parameters is expected: --storage-account, --event-hub-name, or --workspace.')

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
    from azure.mgmt.monitor.models import ActionGroupResource, EmailReceiver, SmsReceiver, WebhookReceiver

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
        'tags': ns.get('tags') or None
    }

    ns['action_group'] = ActionGroupResource(**action_group_resource_properties)


def process_metric_timespan(namespace):
    from .util import validate_time_range_and_add_defaults

    ns = vars(namespace)
    start_time = ns.pop('start_time', None)
    end_time = ns.pop('end_time', None)
    ns['timespan'] = validate_time_range_and_add_defaults(start_time, end_time, formatter='{}/{}')


def process_metric_aggregation(namespace):
    ns = vars(namespace)
    aggregation = ns.pop('aggregation', None)
    if aggregation:
        ns['aggregation'] = ','.join(aggregation)


def process_metric_result_type(namespace):
    from azure.mgmt.monitor.models.monitor_management_client_enums import ResultType

    ns = vars(namespace)
    metadata_only = ns.pop('metadata', False)
    if metadata_only:
        ns['result_type'] = ResultType.metadata


def process_metric_dimension(namespace):
    ns = vars(namespace)

    dimensions = ns.pop('dimension', None)
    if not dimensions:
        return

    param_filter = ns.pop('filter', None)
    if param_filter:
        from knack.util import CLIError
        raise CLIError('usage: --dimension and --filter parameters are mutually exclusive.')

    ns['filter'] = ' and '.join("{} eq '*'".format(d) for d in dimensions)


def validate_metric_names(namespace):
    if namespace.metricnames:
        namespace.metricnames = ','.join(namespace.metricnames)


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
