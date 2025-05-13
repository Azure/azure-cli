# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-locals, line-too-long, protected-access, too-many-nested-blocks
import antlr4

from azure.cli.command_modules.monitor.actions import AAZCustomListArg
from azure.cli.command_modules.monitor.grammar.metric_alert import MetricAlertConditionLexer, \
    MetricAlertConditionParser, MetricAlertConditionValidator
from azure.cli.core.aaz import has_value
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.mgmt.core.tools import is_valid_resource_id, resource_id
from knack.log import get_logger
from msrest.serialization import Serializer

from ..aaz.latest.monitor.metrics.alert import Update as _MetricsAlertUpdate

logger = get_logger(__name__)

_metric_alert_dimension_prefix = '_where_'


def create_metric_alert(cmd, resource_group_name, rule_name, scopes, condition, disabled=False, description=None,
                        tags=None, actions=None, severity=2, window_size='5m', evaluation_frequency='1m',
                        auto_mitigate=None, target_resource_type=None, target_resource_region=None):
    # generate metadata for the conditions
    is_dynamic_threshold_criterion = False
    all_of = []
    single_all_of = []
    for i, cond in enumerate(condition):
        if "dynamic" in cond:
            is_dynamic_threshold_criterion = True
            item = cond["dynamic"]
            item["name"] = f"cond{i}"
            props = {
                "alert_sensitivity": item.pop("alert_sensitivity", None),
                "failing_periods": item.pop("failing_periods", None),
                "operator": item.pop("operator", None),
                "ignore_data_before": Serializer.serialize_iso(dt) if (dt := item.pop("ignore_data_before", None)) else None
            }

            all_of.append({**item, **{"dynamic_threshold_criterion": props}})
            single_all_of.append({**item, **props})
        else:
            item = cond["static"]
            item["name"] = f"cond{i}"
            props = {
                "operator": item.pop("operator", None),
                "threshold": item.pop("threshold", None)
            }

            all_of.append({**item, **{"static_threshold_criterion": props}})
            single_all_of.append({**item, **props})

    criteria = None
    resource_type, scope_type = _parse_resource_and_scope_type(scopes)
    if scope_type in ['resource_group', 'subscription']:
        if target_resource_type is None or target_resource_region is None:
            raise InvalidArgumentValueError('--target-resource-type and --target-resource-region must be provided.')
        criteria = {"microsoft_azure_monitor_multiple_resource_multiple_metric_criteria": {"all_of": all_of}}
    else:
        if len(scopes) == 1:
            if not is_dynamic_threshold_criterion:
                criteria = {"microsoft_azure_monitor_single_resource_multiple_metric_criteria": {"all_of": single_all_of}}
            else:
                criteria = {"microsoft_azure_monitor_multiple_resource_multiple_metric_criteria": {"all_of": all_of}}
        else:
            criteria = {"microsoft_azure_monitor_multiple_resource_multiple_metric_criteria": {"all_of": all_of}}
            target_resource_type = resource_type
            target_resource_region = target_resource_region if target_resource_region else 'global'

    from ..aaz.latest.monitor.metrics.alert import Create
    return Create(cli_ctx=cmd.cli_ctx)(command_args={
        'resource_group': resource_group_name,
        'name': rule_name,
        'description': description,
        'severity': severity,
        'enabled': not disabled,
        'scopes': scopes,
        'evaluation_frequency': evaluation_frequency,
        'window_size': window_size,
        'criteria': criteria,
        'target_resource_type': target_resource_type,
        'target_resource_region': target_resource_region,
        'actions': actions,
        'tags': tags,
        'location': 'global',
        'auto_mitigate': auto_mitigate
    })


class MetricsAlertUpdate(_MetricsAlertUpdate):
    def __init__(self, loader=None, cli_ctx=None, callbacks=None, **kwargs):
        super().__init__(loader, cli_ctx, callbacks, **kwargs)
        self.add_actions = []
        self.add_conditions = []

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZListArg, AAZStrArg, AAZResourceIdArg, AAZResourceIdArgFormat
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.add_actions = AAZCustomListArg(
            options=["--add-actions"],
            singular_options=["--add-action"],
            arg_group="Action",
            help="Add an action group and optional webhook properties to fire when the alert is triggered.\n\n"
                 "Usage: --add-action ACTION_GROUP_NAME_OR_ID [KEY=VAL [KEY=VAL ...]]\n\n"
                 "Multiple action groups can be specified by using more than one `--add-action` argument."
        )
        args_schema.add_actions.Element = AAZCustomListArg()
        args_schema.add_actions.Element.Element = AAZStrArg()
        args_schema.remove_actions = AAZListArg(
            options=["--remove-actions"],
            arg_group="Action",
            help="Space-separated list of action group names to remove."
        )
        args_schema.remove_actions.Element = AAZResourceIdArg(
            fmt=AAZResourceIdArgFormat(
                template="/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Insights"
                         "/actionGroups/{}"
            )
        )
        args_schema.add_conditions = AAZCustomListArg(
            options=["--add-conditions"],
            singular_options=["--add-condition"],
            arg_group="Condition",
            help="Add a condition which triggers the rule.\n\n"
                 "Usage: --add-condition {avg,min,max,total,count} [NAMESPACE.]METRIC\n"
                 "[{=,!=,>,>=,<,<=} THRESHOLD]\n"
                 "[{>,><,<} dynamic SENSITIVITY VIOLATIONS of EVALUATIONS [since DATETIME]]\n"
                 "[where DIMENSION {includes,excludes} VALUE [or VALUE ...]\n"
                 "[and   DIMENSION {includes,excludes} VALUE [or VALUE ...] ...]]\n\n"
                 "Sensitivity can be 'low', 'medium', 'high'.\n\n"
                 "Violations can be the number of violations to trigger an alert. It should be smaller or equal to evaluation.\n\n"
                 "Evaluations can be the number of evaluation periods for dynamic threshold.\n\n"
                 "Datetime can be the date from which to start learning the metric historical data and calculate the dynamic thresholds (in ISO8601 format).\n\n"
                 "Dimensions can be queried by adding the 'where' keyword and multiple dimensions can be queried by combining them with the 'and' keyword.\n\n"
                 "Values for METRIC, DIMENSION and appropriate THRESHOLD values can be obtained from `az monitor metrics list-definitions` command.\n\n"
                 "Due to server limitation, when an alert rule contains multiple criterias, the use of dimensions is limited to one value per dimension within each criterion.\n\n"
                 "Multiple conditions can be specified by using more than one `--add-condition` argument."
        )
        args_schema.add_conditions.Element = AAZListArg()
        args_schema.add_conditions.Element.Element = AAZStrArg()
        args_schema.remove_conditions = AAZListArg(
            options=["--remove-conditions"],
            arg_group="Condition",
            help="Space-separated list of condition names to remove."
        )
        args_schema.remove_conditions.Element = AAZStrArg()

        return args_schema

    def pre_operations(self):
        def complete_action_group_id(name):
            if is_valid_resource_id(name):
                return name

            return resource_id(
                subscription=self.ctx.subscription_id,
                resource_group=self.ctx.args.resource_group,
                namespace="Microsoft.Insights",
                type="actionGroups",
                name=name
            )

        args = self.ctx.args
        if has_value(args.add_actions):
            self.add_actions = []
            for add_action in args.add_actions:
                values = add_action.to_serialized_data()[0].split()
                action_group_id = complete_action_group_id(values[0])
                try:
                    webhook_property_candidates = dict(x.split('=', 1) for x in values[1:]) if len(values) > 1 else None
                except ValueError:
                    err_msg = "Value of --add-action is invalid. Please refer to --help to get insight of correct format."
                    raise InvalidArgumentValueError(err_msg)

                action = {
                    "action_group_id": action_group_id,
                    "web_hook_properties": webhook_property_candidates
                }
                action["odatatype"] = "Microsoft.WindowsAzure.Management.Monitoring.Alerts.Models." \
                                      "Microsoft.AppInsights.Nexus.DataContracts.Resources.ScheduledQueryRules.Action"

                self.add_actions.append(action)

        if has_value(args.add_conditions):
            err_msg = 'usage error: --condition {avg,min,max,total,count} [NAMESPACE.]METRIC\n' \
                      '                         [{=,!=,>,>=,<,<=} THRESHOLD]\n' \
                      '                         [{<,>,><} dynamic SENSITIVITY VIOLATION of EVALUATION [since DATETIME]]\n' \
                      '                         [where DIMENSION {includes,excludes} VALUE [or VALUE ...]\n' \
                      '                         [and   DIMENSION {includes,excludes} VALUE [or VALUE ...] ...]]\n' \
                      '                         [with skipmetricvalidation]'

            self.add_conditions = []
            for add_condition in args.add_conditions:
                string_val = add_condition.to_serialized_data()[0]
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
                                raise InvalidArgumentValueError(err_msg)
                    elif "dynamic" in metric_condition:
                        # dynamic metric criteria
                        for item in ['time_aggregation', 'metric_name', 'operator', 'alert_sensitivity',
                                     'failing_periods']:
                            if item not in metric_condition["dynamic"]:
                                raise InvalidArgumentValueError(err_msg)
                    else:
                        raise NotImplementedError()
                except (AttributeError, TypeError, KeyError):
                    raise InvalidArgumentValueError(err_msg)

                self.add_conditions.append(metric_condition)

    def pre_instance_update(self, instance):
        def get_next_name():
            idx = 0
            while True:
                possible_name = f"cond{idx}"
                match = next((cond for cond in instance.properties.criteria.all_of if cond.name == possible_name), None)
                if match:
                    idx += 1
                    continue

                return possible_name

        args = self.ctx.args
        if has_value(args.remove_actions):
            to_be_removed = set(map(lambda x: x.to_serialized_data().lower(), args.remove_actions))

            new_actions = []
            for action in instance.properties.actions:
                if action.action_group_id.to_serialized_data().lower() not in to_be_removed:
                    new_actions.append(action)

            instance.properties.actions = new_actions

        if has_value(args.add_actions):
            to_be_added = set(map(lambda x: x["action_group_id"].lower(), self.add_actions))

            new_actions = []
            for action in instance.properties.actions:
                if action.action_group_id.to_serialized_data().lower() not in to_be_added:
                    new_actions.append(action)
            new_actions.extend(self.add_actions)

            instance.properties.actions = new_actions

        if has_value(args.remove_conditions):
            to_be_removed = set(map(lambda x: x.to_serialized_data().lower(), args.remove_conditions))

            new_conditions = []
            for cond in instance.properties.criteria.all_of:
                if cond.name.to_serialized_data().lower() not in to_be_removed:
                    new_conditions.append(cond)

            instance.properties.criteria.all_of = new_conditions

        if has_value(args.add_conditions):
            for cond in self.add_conditions:
                if "dynamic" in cond:
                    item = cond["dynamic"]
                    item["name"] = get_next_name()
                    item["criterion_type"] = "DynamicThresholdCriterion"
                    item["ignore_data_before"] = Serializer.serialize_iso(dt) if (dt := item.pop("ignore_data_before", None)) else None

                    instance.properties.criteria.all_of.append(item)
                else:
                    item = cond["static"]
                    item["name"] = get_next_name()
                    item["criterion_type"] = "StaticThresholdCriterion"

                    instance.properties.criteria.all_of.append(item)


def create_metric_alert_dimension(dimension_name, value_list, operator=None):
    values = ' or '.join(value_list)
    return '{} {} {} {}'.format(_metric_alert_dimension_prefix, dimension_name, operator, values)


def create_metric_alert_condition(condition_type, aggregation, metric_name, operator, metric_namespace='',
                                  dimension_list=None, threshold=None, alert_sensitivity=None,
                                  number_of_evaluation_periods=None, min_failing_periods_to_alert=None,
                                  ignore_data_before=None, skip_metric_validation=None):
    if metric_namespace:
        metric_namespace += '.'
    condition = "{} {}'{}' {} ".format(aggregation, metric_namespace, metric_name, operator)
    if condition_type == 'static':
        condition += '{} '.format(threshold)
    elif condition_type == 'dynamic':
        dynamics = 'dynamic {} {} of {} '.format(
            alert_sensitivity, min_failing_periods_to_alert, number_of_evaluation_periods)
        if ignore_data_before:
            dynamics += 'since {} '.format(ignore_data_before)
        condition += dynamics
    else:
        raise NotImplementedError()

    if dimension_list:
        dimensions = ' '.join([t for t in dimension_list if t.strip()])
        if dimensions.startswith(_metric_alert_dimension_prefix):
            dimensions = [t for t in dimensions.split(_metric_alert_dimension_prefix) if t]
            dimensions = 'where' + 'and'.join(dimensions)
        condition += dimensions

    if skip_metric_validation:
        condition += ' with skipmetricvalidation'

    return condition.strip()


def _parse_action_removals(actions):
    """ Separates the combined list of keys to remove into webhooks and emails. """
    flattened = list({x for sublist in actions for x in sublist})
    emails = []
    webhooks = []
    for item in flattened:
        if item.startswith('http://') or item.startswith('https://'):
            webhooks.append(item)
        else:
            emails.append(item)
    return emails, webhooks


def _parse_resource_and_scope_type(scopes):
    from azure.mgmt.core.tools import parse_resource_id

    if not scopes:
        raise InvalidArgumentValueError('scopes cannot be null.')

    namespace = ''
    resource_type = ''
    scope_type = None

    def validate_scope(item_namespace, item_resource_type, item_scope_type):
        if namespace != item_namespace or resource_type != item_resource_type or scope_type != item_scope_type:
            raise InvalidArgumentValueError('Multiple scopes should be the same resource type.')

    def store_scope(item_namespace, item_resource_type, item_scope_type):
        nonlocal namespace
        nonlocal resource_type
        nonlocal scope_type
        namespace = item_namespace
        resource_type = item_resource_type
        scope_type = item_scope_type

    def parse_one_scope_with_action(scope, operation_on_scope):
        result = parse_resource_id(scope)
        if 'namespace' in result and 'resource_type' in result:
            resource_types = [result['type']]
            child_idx = 1
            while 'child_type_{}'.format(child_idx) in result:
                resource_types.append(result['child_type_{}'.format(child_idx)])
                child_idx += 1
            operation_on_scope(result['namespace'], '/'.join(resource_types), 'resource')
        elif 'resource_group' in result:  # It's a resource group.
            operation_on_scope('', '', 'resource_group')
        elif 'subscription' in result:  # It's a subscription.
            operation_on_scope('', '', 'subscription')
        else:
            raise InvalidArgumentValueError('Scope must be a valid resource id.')

    # Store the resource type and scope type from first scope
    parse_one_scope_with_action(scopes[0], operation_on_scope=store_scope)
    # Validate the following scopes
    for item in scopes:
        parse_one_scope_with_action(item, operation_on_scope=validate_scope)

    return namespace + '/' + resource_type, scope_type
