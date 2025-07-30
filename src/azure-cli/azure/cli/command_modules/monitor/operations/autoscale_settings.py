# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, protected-access
import json
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.aaz import has_value, AAZListArg, AAZStrArg, AAZIntArg, AAZBoolArg
from azure.cli.command_modules.monitor.actions import AAZCustomListArg
from azure.cli.command_modules.monitor._autoscale_util import get_autoscale_default_profile
from ..aaz.latest.monitor.autoscale import Create as _AutoScaleCreate, Update as _AutoScaleUpdate, \
    Show as _AutoScaleShow, List as _AutoScaleList
from azure.cli.command_modules.network.custom import _convert_to_snake_case
from azure.cli.core.azclierror import InvalidArgumentValueError

logger = get_logger(__name__)


DEFAULT_PROFILE_NAME = 'default'


class AutoScaleCreate(_AutoScaleCreate):

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined
        if has_value(self.ctx.vars.instance.properties.name):
            self.ctx.vars.instance.properties.name = AAZUndefined
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class AutoScaleShow(_AutoScaleShow):

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined
        # When the name field conflicts, the name in inner layer is ignored and the outer layer is applied
        if has_value(self.ctx.vars.instance.properties.name):
            self.ctx.vars.instance.properties.name = AAZUndefined
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


def update_add_actions(args):
    add_actions = []
    for add_action_item in args.add_actions:
        add_action_item_arr = add_action_item.to_serialized_data()
        _type = add_action_item_arr[0].lower()
        if _type == "email":
            add_actions.append({
                "key": "email",
                "value": {
                    "customEmails": add_action_item_arr[1:]
                }
            })
        elif _type == "webhook":
            uri = add_action_item_arr[1]
            try:
                properties = dict(x.split('=', 1) for x in add_action_item_arr[2:])
            except ValueError:
                raise InvalidArgumentValueError('webhook URI [KEY=VALUE ...]')
            add_actions.append({
                "key": "webhook",
                "value": {
                    "serviceUri": uri,
                    "properties": properties
                }
            })
        else:
            raise InvalidArgumentValueError('TYPE KEY [ARGS]')
    return add_actions


def update_remove_actions(args):
    remove_actions = []
    for remove_action_item in args.remove_actions:
        values = remove_action_item.to_serialized_data()
        _type = values[0].lower()
        if _type not in ['email', 'webhook']:
            raise InvalidArgumentValueError('TYPE KEY [KEY ...]')
        remove_actions.append(values[1:])
    return remove_actions


class AutoScaleUpdate(_AutoScaleUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.notifications._registered = False
        args_schema.profiles._registered = False
        args_schema.target_resource_location._registered = False
        args_schema.target_resource_uri._registered = False
        args_schema.count = AAZIntArg(
            options=["--count"],
            help='The numer of instances to use. If used with --min/max-count, the default number of instances to use.',
            arg_group="Instance Limit",
        )
        args_schema.min_count = AAZIntArg(
            options=["--min-count"],
            help='The minimum number of instances.',
            arg_group="Instance Limit",
        )
        args_schema.max_count = AAZIntArg(
            options=["--max-count"],
            help='The maximum number of instances.',
            arg_group="Instance Limit",
        )
        args_schema.add_actions = AAZCustomListArg(
            options=["--add-actions"],
            singular_options=['--add-action', '-a'],
            help="Add an action to fire when a scaling event occurs." + '''
        Usage:   --add-action TYPE KEY [ARG ...]
        Email:   --add-action email bob@contoso.com ann@contoso.com
        Webhook: --add-action webhook https://www.contoso.com/alert apiKey=value
        Webhook: --add-action webhook https://www.contoso.com/alert?apiKey=value
        Multiple actions can be specified by using more than one `--add-action` argument.
        ''',
            arg_group="Notification",
        )
        args_schema.add_actions.Element = AAZCustomListArg()
        args_schema.add_actions.Element.Element = AAZStrArg()

        args_schema.remove_actions = AAZCustomListArg(
            options=["--remove-actions"],
            singular_options=['--remove-action', '-r'],
            help="Remove one or more actions." + '''
        Usage:   --remove-action TYPE KEY [KEY ...]
        Email:   --remove-action email bob@contoso.com ann@contoso.com
        Webhook: --remove-action webhook https://contoso.com/alert https://alerts.contoso.com.
        ''',
            arg_group="Notification",
        )
        args_schema.remove_actions.Element = AAZCustomListArg()
        args_schema.remove_actions.Element.Element = AAZStrArg()

        args_schema.email_administrator = AAZBoolArg(
            options=["--email-administrator"],
            help='Send email to subscription administrator on scaling.',
            arg_group="Notification",
        )
        args_schema.email_coadministrators = AAZBoolArg(
            options=["--email-coadministrators"],
            help='Send email to subscription co-administrators on scaling.',
            arg_group="Notification",
        )

        return args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args
        add_actions = update_add_actions(args)
        remove_actions = update_remove_actions(args)
        if has_value(args.count) or has_value(args.min_count) or has_value(args.max_count):
            default_profile = get_autoscale_default_profile(instance)
            curr_count = default_profile["capacity"]["default"]
            curr_min = default_profile["capacity"]["minimum"]
            curr_max = default_profile["capacity"]["maximum"]
            is_fixed_count = curr_count == curr_min and curr_count == curr_max

            # check for special case where count is used to indicate fixed value and only
            # count is updated
            if has_value(args.count) and is_fixed_count and not has_value(args.min_count) and not has_value(args.max_count):
                args.min_count = args.count.to_serialized_data()
                args.max_count = args.count.to_serialized_data()

            count = curr_count if not has_value(args.count) else args.count.to_serialized_data()
            min_count = curr_min if not has_value(args.min_count) else args.min_count.to_serialized_data()
            max_count = curr_max if not has_value(args.max_count) else args.max_count.to_serialized_data()

            # There may be multiple "default" profiles. All need to updated.
            for profile in instance.properties.profiles:
                if has_value(profile.fixed_date):
                    continue
                if has_value(profile.recurrence):
                    try:
                        # portal denotes the "default" pairs by using a JSON string for their name
                        # so if it can be decoded, we know this is a default profile
                        json.loads(profile.name.to_serialized_data())
                    except ValueError:
                        continue
                profile.capacity.default = str(count)
                profile.capacity.minimum = str(min_count)
                profile.capacity.maximum = str(max_count)
        updated_notification = None
        if instance.properties.notifications:
            retained_notification = []
            for x in instance.properties.notifications:
                note = x.to_serialized_data()
                if note['operation'].lower() == 'scale':
                    updated_notification = note
                else:
                    retained_notification.append(note)
            instance.properties.notifications = retained_notification
        else:
            instance.properties.notifications = []

        if updated_notification is None:
            updated_notification = {
                "operation": "scale",
                "email": {
                    "customEmails": []
                },
                "webhooks": []
            }

        # process removals
        if len(remove_actions) > 0:
            removed_emails, removed_webhooks = _parse_action_removals(remove_actions)
            updated_notification['email']['customEmails'] = \
                [x for x in updated_notification['email']['customEmails'] if x not in removed_emails]
            updated_notification['webhooks'] = \
                [x for x in updated_notification['webhooks'] if x['serviceUri'] not in removed_webhooks]

        # process additions
        for action in add_actions:
            if action["key"] == "email":
                for email in action["value"]["customEmails"]:
                    updated_notification['email']['customEmails'].append(email)
            elif action["key"] == "webhook":
                updated_notification['webhooks'].append(action["value"])
        if has_value(args.email_administrator):
            updated_notification['email']['sendToSubscriptionAdministrator'] = args.email_administrator.to_serialized_data()
        if has_value(args.email_coadministrators):
            updated_notification['email']['sendToSubscriptionCoAdministrators'] = args.email_coadministrators.to_serialized_data()

        instance.properties.notifications.append(updated_notification)

        if has_value(args.scale_look_ahead_time) and not has_value(args.scale_mode) \
                and not has_value(instance.properties.predictive_autoscale_policy):
            raise InvalidArgumentValueError('scale-mode is required for setting scale-look-ahead-time.')

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined
        # When the name field conflicts, the name in inner layer is ignored and the outer layer is applied
        if has_value(self.ctx.vars.instance.properties.name):
            self.ctx.vars.instance.properties.name = AAZUndefined
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


class AutoScaleList(_AutoScaleList):

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined
        # When the name field conflicts, the name in inner layer is ignored and the outer layer is applied
        for value in self.ctx.vars.instance.value:
            if has_value(value.properties):
                value.properties.name = AAZUndefined
        result = self.deserialize_output(self.ctx.vars.instance.value, client_flatten=True)
        next_link = self.deserialize_output(self.ctx.vars.instance.next_link)
        return result, next_link


# pylint: disable=too-many-locals
def autoscale_create(cmd, resource, count, autoscale_name=None, resource_group_name=None,
                     min_count=None, max_count=None, location=None, tags=None, disabled=None,
                     actions=None, email_administrator=None, email_coadministrators=None,
                     scale_mode=None, scale_look_ahead_time=None):

    if not autoscale_name:
        from azure.mgmt.core.tools import parse_resource_id
        autoscale_name = parse_resource_id(resource)['name']
    min_count = min_count or count
    max_count = max_count or count
    args = {}
    default_profile = {
        "name": DEFAULT_PROFILE_NAME,
        "capacity": {
            "default": str(count),
            "minimum": str(min_count),
            "maximum": str(max_count)
        },
        "rules": []
    }

    notification = {
        "operation": "scale",
        "email": {
            "custom_emails": [],
            "send_to_subscription_administrator": email_administrator,
            "send_to_subscription_co_administrators": email_coadministrators,
        },
        "webhooks": []
    }

    for action in actions or []:
        key = action["key"]
        value = action["value"]
        if key == "email":
            for email in value["custom_emails"]:
                notification["email"]["custom_emails"].append(email)
        elif key == "webhook":
            notification["webhooks"].append(value)

    if scale_mode is not None and scale_look_ahead_time is not None:
        args["scale_mode"] = scale_mode
        args["scale_look_ahead_time"] = scale_look_ahead_time
    elif scale_mode is not None:
        args["scale_mode"] = scale_mode
    elif scale_look_ahead_time is not None:
        raise InvalidArgumentValueError('scale-mode is required for setting predictive autoscale policy.')
    args["location"] = location
    args["profiles"] = [default_profile]
    args["tags"] = tags
    args["notifications"] = [notification]
    args["enabled"] = not disabled
    args["autoscale_name"] = autoscale_name
    args["target_resource_uri"] = resource
    args["resource_group"] = resource_group_name

    if not (min_count == count and max_count == count):
        logger.warning('Follow up with `az monitor autoscale rule create` to add scaling rules.')
    return AutoScaleCreate(cli_ctx=cmd.cli_ctx)(command_args=args)


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


def _apply_copy_rules(autoscale_settings, new_profile, copy_rules):
    if copy_rules:
        copy_profile = next(x for x in autoscale_settings["profiles"] if x["name"] == copy_rules)
        if copy_profile:
            new_profile["rules"] = copy_profile["rules"]


def _create_fixed_profile(autoscale_settings, profile_name, start, end, capacity, copy_rules=None, timezone=None):
    if not (start and end):
        raise CLIError('usage error: fixed schedule: --start DATETIME --end DATETIME')
    profile = {
        "name": profile_name,
        "capacity": capacity,
        "rules": [],
        "fixed_date": {
            "start": start + "+00:00",  # use UTC for AAZDateTimeArg timezone
            "end": end + "+00:00",  # use UTC for AAZDateTimeArg timezone
            "time_zone": timezone
        }
    }
    _apply_copy_rules(autoscale_settings, profile, copy_rules)
    autoscale_settings["profiles"].append(profile)


# pylint: disable=unused-argument
def _create_recurring_profile(autoscale_settings, profile_name, start, end, recurrence, capacity,
                              copy_rules=None, timezone=None):
    from azure.cli.command_modules.monitor._autoscale_util import build_autoscale_profile_dict, \
        validate_autoscale_profile_dict
    import dateutil
    from datetime import time

    def _build_recurrence(base, time):
        recur = {
            "frequency": base["frequency"],
            "schedule": {
                "time_zone": base["schedule"]["time_zone"],
                "days": base["schedule"]["days"],
                "hours": [time.hour],
                "minutes": [time.minute]
            }
        }
        return recur

    start_time = dateutil.parser.parse(start).time() if start else time(hour=0, minute=0)
    end_time = dateutil.parser.parse(end).time() if end else time(hour=23, minute=59)

    default_profile, autoscale_profile = build_autoscale_profile_dict(autoscale_settings)
    validate_autoscale_profile_dict(autoscale_profile, start_time, end_time, recurrence)
    start_profile = {
        "name": profile_name,
        "capacity": capacity,
        "rules": [],
        "recurrence": _build_recurrence(recurrence, start_time)
    }

    _apply_copy_rules(autoscale_settings, start_profile, copy_rules)
    end_profile = {
        "name": json.dumps({'name': default_profile["name"], 'for': profile_name}),
        "capacity": default_profile["capacity"],
        "rules": default_profile["rules"],
        "recurrence": _build_recurrence(recurrence, end_time)
    }
    autoscale_settings["profiles"].append(start_profile)
    autoscale_settings["profiles"].append(end_profile)


def get_autoscale_instance(cmd, resource_group_name, autoscale_name):
    rets = AutoScaleShow(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "autoscale_name": autoscale_name
    })

    rets = _convert_to_snake_case(rets)
    autoscale_settings = {
        "resource_group": resource_group_name,
        "autoscale_name": autoscale_name,
        "enabled": rets.get("enabled", False),
        "tags": rets.get("tags", None),
        "target_resource_location": rets.get("target_resource_location", None),
        "target_resource_uri": rets.get("target_resource_uri", None)
    }
    scale_policy = rets.get("predictive_autoscale_policy", None)
    if scale_policy:
        autoscale_settings["scale_look_ahead_time"] = scale_policy.get("scale_look_ahead_time", None)
        autoscale_settings["scale_mode"] = scale_policy.get("scale_mode", None)
    if rets.get("notifications", None):
        autoscale_settings["notifications"] = rets["notifications"]
    if rets.get("profiles", None):
        autoscale_settings["profiles"] = rets["profiles"]
    return autoscale_settings


def autoscale_profile_create(cmd, autoscale_name, resource_group_name, profile_name,
                             count, timezone, start=None, end=None, copy_rules=None, min_count=None,
                             max_count=None, recurrence=None):
    autoscale_settings = get_autoscale_instance(cmd, resource_group_name, autoscale_name)
    capacity = {
        "default": str(count),
        "minimum": str(min_count) if min_count else str(count),
        "maximum": str(max_count) if max_count else str(count)
    }
    if recurrence:
        _create_recurring_profile(autoscale_settings, profile_name, start, end, recurrence, capacity, copy_rules,
                                  timezone)
    else:
        _create_fixed_profile(autoscale_settings, profile_name, start, end, capacity, copy_rules, timezone)
    updated_rets = AutoScaleUpdate(cli_ctx=cmd.cli_ctx)(command_args=autoscale_settings)
    profile = next(x for x in updated_rets["profiles"] if x["name"] == profile_name)
    return profile


def autoscale_profile_list(cmd, autoscale_name, resource_group_name):
    autoscale_settings = AutoScaleShow(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "autoscale_name": autoscale_name})
    return autoscale_settings["profiles"]


def autoscale_profile_list_timezones(cmd, client, offset=None, search_query=None):
    from azure.cli.command_modules.monitor._autoscale_util import AUTOSCALE_TIMEZONES
    timezones = []
    for zone in AUTOSCALE_TIMEZONES:
        if search_query and search_query.lower() not in zone['name'].lower():
            continue
        if offset and offset not in zone['offset']:
            continue
        timezones.append(zone)
    return timezones


def autoscale_profile_show(cmd, autoscale_name, resource_group_name, profile_name):
    autoscale_settings = AutoScaleShow(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "autoscale_name": autoscale_name})
    return _identify_profile_cg(autoscale_settings["profiles"], profile_name)


class AutoScaleProfileDelete(_AutoScaleUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.profile_name = AAZStrArg(
            options=["--profile-name"],
            help='Name of the autoscale profile.',
            required=True,
            registered=False,
        )
        return args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args
        profile_name = args.profile_name.to_serialized_data()
        default_profile = get_autoscale_default_profile(instance)

        def _should_retain_profile(profile):
            name = profile.name.to_serialized_data()
            try:
                name = json.loads(profile.name.to_serialized_data())['for']
            except ValueError:
                pass
            return name.lower() != profile_name.lower()

        retained_profiles = [x for x in instance.properties.profiles if _should_retain_profile(x)]
        instance.properties.profiles = retained_profiles

        # if we removed the last "default" of a recurring pair, we need to preserve it
        new_default = get_autoscale_default_profile(instance)
        if not new_default:
            instance.properties.profiles.append(default_profile)

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined
        if has_value(self.ctx.vars.instance.properties.name):
            self.ctx.vars.instance.properties.name = AAZUndefined
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


def autoscale_profile_delete(cmd, autoscale_name, resource_group_name, profile_name):
    AutoScaleProfileDelete(cli_ctx=cmd.cli_ctx)(command_args={
        "autoscale_name": autoscale_name,
        "resource_group": resource_group_name,
        "profile_name": profile_name,
    })


def get_condition_from_model(condition):
    condition_obj = {
        "metric_name": condition.metric_name,
        "metric_namespace": condition.metric_namespace,
        "metric_resource_location": condition.metric_resource_location,
        "metric_resource_uri": condition.metric_resource_uri,
        "operator": condition.operator.value,
        "statistic": condition.statistic.value,
        "threshold": float(condition.threshold),
        "time_aggregation": condition.time_aggregation.value,
        "time_grain": condition.time_grain,
        "time_window": condition.time_window
    }
    if condition.divide_per_instance is not None:
        condition_obj["divide_per_instance"] = condition.divide_per_instance
    if condition.dimensions:
        dim_objs = []
        for dim in condition.dimensions:
            dim_objs.append({
                "dimension_name": dim.dimension_name,
                "operator": dim.operator,
                "values": dim.values
            })
        condition_obj["dimensions"] = dim_objs
    return condition_obj


def autoscale_rule_create(cmd, autoscale_name, resource_group_name, condition,
                          scale, profile_name=DEFAULT_PROFILE_NAME, cooldown=5, source=None,
                          timegrain="avg 1m"):
    from azure.mgmt.core.tools import parse_resource_id, resource_id
    autoscale_settings = get_autoscale_instance(cmd, resource_group_name, autoscale_name)
    profile = _identify_profile_cg(autoscale_settings["profiles"], profile_name)
    condition.metric_resource_uri = source or autoscale_settings["target_resource_uri"]
    condition.statistic = timegrain.statistic
    condition.time_grain = timegrain.time_grain

    def preprocess_for_spring_cloud_service():
        try:
            result = parse_resource_id(autoscale_settings["target_resource_uri"])
            if result['namespace'].lower() == 'microsoft.appplatform' and result['type'].lower() == 'spring':
                if condition.metric_namespace is None:
                    condition.metric_namespace = "Microsoft.AppPlatform/Spring"
                    logger.warning('Set metricNamespace to Microsoft.AppPlatform/Spring')
                if source is None:
                    condition.metric_resource_uri = resource_id(
                        subscription=result['subscription'],
                        resource_group=result['resource_group'],
                        namespace=result['namespace'],
                        type=result['type'],
                        name=result['name']
                    )
                    logger.warning('Set metricResourceUri to Spring Cloud service')
        except KeyError:
            pass

    preprocess_for_spring_cloud_service()

    condition_obj = get_condition_from_model(condition)

    rule = {
        "metric_trigger": condition_obj,
        "scale_action": {
            "direction": scale.direction,
            "type": scale.type,
            "cooldown": 'PT{}M'.format(cooldown),
            "value": scale.value
        }
    }
    profile["rules"].append(rule)
    updated_rets = AutoScaleUpdate(cli_ctx=cmd.cli_ctx)(command_args=autoscale_settings)
    updated_profile = _identify_profile_cg(updated_rets["profiles"], profile_name)
    # determine if there are unbalanced rules
    scale_out_rule_count = len([x for x in updated_profile["rules"] if x["scaleAction"]["direction"] == "Increase"])
    scale_in_rule_count = len([x for x in updated_profile["rules"] if x["scaleAction"]["direction"] == "Decrease"])
    if scale_out_rule_count and not scale_in_rule_count:
        logger.warning("Profile '%s' has rules to scale out but none to scale in. "
                       "Recommend creating at least 1 scale in rule.", profile_name)
    elif scale_in_rule_count and not scale_out_rule_count:
        logger.warning("Profile '%s' has rules to scale in but none to scale out. "
                       "Recommend creating at least 1 scale out rule.", profile_name)
    return updated_profile["rules"][-1]


def autoscale_rule_list(cmd, autoscale_name, resource_group_name, profile_name=DEFAULT_PROFILE_NAME):
    autoscale_settings = AutoScaleShow(cli_ctx=cmd.cli_ctx)(command_args={
        "resource_group": resource_group_name,
        "autoscale_name": autoscale_name})
    profile = _identify_profile_cg(autoscale_settings["profiles"], profile_name)
    index = 0
    # we artificially add indices to the rules so the user can target them with the remove command
    for rule in profile["rules"]:
        rule["index"] = index
        index += 1
    return profile["rules"]


def autoscale_rule_delete(cmd, autoscale_name, resource_group_name, index, profile_name=DEFAULT_PROFILE_NAME):
    autoscale_settings = get_autoscale_instance(cmd, resource_group_name, autoscale_name)
    profile = _identify_profile_cg(autoscale_settings["profiles"], profile_name)
    if '*' in index:
        profile["rules"] = []
    else:
        remained_rule = []
        for i, rule in enumerate(profile["rules"]):
            if str(i) in index:
                continue
            remained_rule.append(rule)
        profile["rules"] = remained_rule
    AutoScaleUpdate(cli_ctx=cmd.cli_ctx)(command_args=autoscale_settings)


class AutoScaleRuleCopy(_AutoScaleUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.source_profile = AAZStrArg(
            options=["--source-profile"],
            help='Name of the autoscale profile.',
            required=True,
            registered=False,
            default=DEFAULT_PROFILE_NAME
        )
        args_schema.dest_profile = AAZStrArg(
            options=["--dest-profile"],
            help='Name of the autoscale profile.',
            required=True,
            registered=False,
        )
        args_schema.index = AAZListArg(
            options=["--index"],
            help="Space-separated list of rule indices to remove, or '*' to clear all rules.",
            registered=False,
        )
        args_schema.index.Element = AAZStrArg()
        return args_schema

    def pre_instance_update(self, instance):
        args = self.ctx.args
        source_profile_name = args.source_profile.to_serialized_data()
        dest_profile_name = args.dest_profile.to_serialized_data()
        index = args.index.to_serialized_data()

        src_profile = _identify_profile(instance.properties.profiles, source_profile_name)
        dst_profile = _identify_profile(instance.properties.profiles, dest_profile_name)
        if '*' in index:
            dst_profile.rules = src_profile.rules
        else:
            for i in index:
                dst_profile.rules.append(src_profile.rules[int(i)])

    def _output(self, *args, **kwargs):
        from azure.cli.core.aaz import AAZUndefined
        if has_value(self.ctx.vars.instance.properties.name):
            self.ctx.vars.instance.properties.name = AAZUndefined
        result = self.deserialize_output(self.ctx.vars.instance, client_flatten=True)
        return result


def autoscale_rule_copy(cmd, autoscale_name, resource_group_name, dest_profile, index,
                        source_profile=DEFAULT_PROFILE_NAME):
    AutoScaleRuleCopy(cli_ctx=cmd.cli_ctx)(command_args={
        "autoscale_name": autoscale_name,
        "resource_group": resource_group_name,
        "source_profile": source_profile,
        "dest_profile": dest_profile,
        "index": index
    })


def _identify_profile(profiles, profile_name):
    try:
        profile = next(x for x in profiles if x.name == profile_name)
    except StopIteration:
        raise CLIError('Cannot find profile {}. '
                       'Please double check the name of the autoscale profile.'.format(profile_name))
    return profile


def _identify_profile_cg(profiles, profile_name):
    try:
        profile = next(x for x in profiles if x["name"] == profile_name)
    except StopIteration:
        raise CLIError('Cannot find profile {}. '
                       'Please double check the name of the autoscale profile.'.format(profile_name))
    return profile
