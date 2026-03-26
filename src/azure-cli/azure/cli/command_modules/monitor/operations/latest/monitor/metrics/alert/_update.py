# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access, line-too-long, too-many-statements, too-many-locals, too-many-nested-blocks

from knack.log import get_logger

from azure.cli.command_modules.monitor.aaz.latest.monitor.metrics.alert._update import Update as _MetricsAlertUpdate
from azure.cli.command_modules.monitor.actions import AAZCustomListArg
from azure.cli.core.aaz import AAZListArg, AAZResourceIdArg, AAZResourceIdArgFormat, AAZStrArg, has_value
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.mgmt.core.tools import is_valid_resource_id, resource_id

logger = get_logger(__name__)


class MetricsAlertUpdate(_MetricsAlertUpdate):
    def __init__(self, loader=None, cli_ctx=None, callbacks=None, **kwargs):
        super().__init__(loader, cli_ctx, callbacks, **kwargs)
        self.add_actions = []
        self.add_conditions = []

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
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
        import antlr4

        from azure.cli.command_modules.monitor.grammar.metric_alert import (
            MetricAlertConditionLexer,
            MetricAlertConditionParser,
            MetricAlertConditionValidator,
        )

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
        from msrest.serialization import Serializer

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
