# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError


logger = get_logger(__name__)


DEFAULT_PROFILE_NAME = 'default'


def scaffold_autoscale_settings_parameters(client):  # pylint: disable=unused-argument
    """Scaffold fully formed autoscale-settings' parameters as json template """

    import os.path
    from azure.cli.core.util import get_file_json

    # Autoscale settings parameter scaffold file path
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    autoscale_settings_parameter_file_path = os.path.join(
        curr_dir, 'autoscale-parameters-template.json')

    if not os.path.exists(autoscale_settings_parameter_file_path):
        raise CLIError('File {} not found.'.format(autoscale_settings_parameter_file_path))

    return get_file_json(autoscale_settings_parameter_file_path)


# pylint: disable=too-many-locals
def autoscale_create(client, resource, count, autoscale_name=None, resource_group_name=None,
                     min_count=None, max_count=None, location=None, tags=None, disabled=None,
                     actions=None, email_administrator=None, email_coadministrators=None):

    from azure.mgmt.monitor.models import (
        AutoscaleSettingResource, AutoscaleProfile, AutoscaleNotification, ScaleCapacity,
        EmailNotification, WebhookNotification)
    if not autoscale_name:
        from msrestazure.tools import parse_resource_id
        autoscale_name = parse_resource_id(resource)['name']
    min_count = min_count or count
    max_count = max_count or count
    default_profile = AutoscaleProfile(
        name=DEFAULT_PROFILE_NAME,
        capacity=ScaleCapacity(default=count, minimum=min_count, maximum=max_count),
        rules=[]
    )
    notification = AutoscaleNotification(
        email=EmailNotification(
            custom_emails=[],
            send_to_subscription_administrator=email_administrator,
            send_to_subscription_co_administrators=email_coadministrators
        ),
        webhooks=[]
    )
    for action in actions or []:
        if isinstance(action, EmailNotification):
            for email in action.custom_emails:
                notification.email.custom_emails.append(email)
        elif isinstance(action, WebhookNotification):
            notification.webhooks.append(action)
    autoscale = AutoscaleSettingResource(
        location=location,
        profiles=[default_profile],
        tags=tags,
        notifications=[notification],
        enabled=not disabled,
        autoscale_setting_resource_name=autoscale_name,
        target_resource_uri=resource
    )
    if not (min_count == count and max_count == count):
        logger.warning('Follow up with `az monitor autoscale rule create` to add scaling rules.')
    return client.create_or_update(resource_group_name, autoscale_name, autoscale)


# pylint: disable=too-many-locals
def autoscale_update(instance, count=None, min_count=None, max_count=None, tags=None, enabled=None,
                     add_actions=None, remove_actions=None, email_administrator=None,
                     email_coadministrators=None):
    import json
    from azure.mgmt.monitor.models import EmailNotification, WebhookNotification
    from azure.cli.command_modules.monitor._autoscale_util import build_autoscale_profile

    if tags is not None:
        instance.tags = tags
    if enabled is not None:
        instance.enabled = enabled

    if any([count, min_count, max_count]):

        # resolve the interrelated aspects of capacity
        default_profile, _ = build_autoscale_profile(instance)
        curr_count = default_profile.capacity.default
        curr_min = default_profile.capacity.minimum
        curr_max = default_profile.capacity.maximum
        is_fixed_count = curr_count == curr_min and curr_count == curr_max

        # check for special case where count is used to indicate fixed value and only
        # count is updated
        if count is not None and is_fixed_count and min_count is None and max_count is None:
            min_count = count
            max_count = count

        count = curr_count if count is None else count
        min_count = curr_min if min_count is None else min_count
        max_count = curr_max if max_count is None else max_count

        # There may be multiple "default" profiles. All need to updated.
        for profile in instance.profiles:
            if profile.fixed_date:
                continue
            if profile.recurrence:
                try:
                    # portal denotes the "default" pairs by using a JSON string for their name
                    # so if it can be decoded, we know this is a default profile
                    json.loads(profile.name)
                except ValueError:
                    continue
            profile.capacity.default = count
            profile.capacity.minimum = min_count
            profile.capacity.maximum = max_count

    if not instance.notifications:
        return instance

    notification = next(x for x in instance.notifications if x.operation.lower() == 'scale')

    # process removals
    if remove_actions is not None:
        removed_emails, removed_webhooks = _parse_action_removals(remove_actions)
        notification.email.custom_emails = \
            [x for x in notification.email.custom_emails if x not in removed_emails]
        notification.webhooks = \
            [x for x in notification.webhooks if x.service_uri not in removed_webhooks]

    # process additions
    for action in add_actions or []:
        if isinstance(action, EmailNotification):
            for email in action.custom_emails:
                notification.email.custom_emails.append(email)
        elif isinstance(action, WebhookNotification):
            notification.webhooks.append(action)

    if email_administrator is not None:
        notification.email.send_to_subscription_administrator = email_administrator
    if email_coadministrators is not None:
        notification.email.send_to_subscription_co_administrators = email_coadministrators

    return instance


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
        copy_profile = next(x for x in autoscale_settings.profiles if x.name == copy_rules)
        if copy_profile:
            new_profile.rules = copy_profile.rules[:]


def _create_fixed_profile(autoscale_settings, profile_name, start, end, capacity,
                          copy_rules=None, timezone=None):
    from azure.mgmt.monitor.models import AutoscaleProfile, TimeWindow
    if not (start and end):
        raise CLIError('usage error: fixed schedule: --start DATETIME --end DATETIME')
    profile = AutoscaleProfile(
        name=profile_name,
        capacity=capacity,
        rules=[],
        fixed_date=TimeWindow(start=start, end=end, time_zone=timezone),
    )
    _apply_copy_rules(autoscale_settings, profile, copy_rules)
    autoscale_settings.profiles.append(profile)


# pylint: disable=unused-argument
def _create_recurring_profile(autoscale_settings, profile_name, start, end, recurrence, capacity,
                              copy_rules=None, timezone=None):
    from azure.mgmt.monitor.models import (
        AutoscaleProfile, Recurrence, RecurrentSchedule)
    from azure.cli.command_modules.monitor._autoscale_util import build_autoscale_profile, validate_autoscale_profile
    import dateutil
    from datetime import time
    import json

    def _build_recurrence(base, time):
        recurrence = Recurrence(
            frequency=base.frequency,
            schedule=RecurrentSchedule(
                time_zone=base.schedule.time_zone,
                days=base.schedule.days,
                hours=[time.hour],
                minutes=[time.minute]
            )
        )
        return recurrence

    start_time = dateutil.parser.parse(start).time() if start else time(hour=0, minute=0)
    end_time = dateutil.parser.parse(end).time() if end else time(hour=23, minute=59)

    default_profile, autoscale_profile = build_autoscale_profile(autoscale_settings)
    validate_autoscale_profile(autoscale_profile, start_time, end_time, recurrence)

    start_profile = AutoscaleProfile(
        name=profile_name,
        capacity=capacity,
        rules=[],
        recurrence=_build_recurrence(recurrence, start_time)
    )
    _apply_copy_rules(autoscale_settings, start_profile, copy_rules)

    end_profile = AutoscaleProfile(
        name=json.dumps({'name': default_profile.name, 'for': profile_name}),
        capacity=default_profile.capacity,
        rules=default_profile.rules,
        recurrence=_build_recurrence(recurrence, end_time)
    )
    autoscale_settings.profiles.append(start_profile)
    autoscale_settings.profiles.append(end_profile)


def autoscale_profile_create(client, autoscale_name, resource_group_name, profile_name,
                             count, timezone, start=None, end=None, copy_rules=None, min_count=None,
                             max_count=None, recurrence=None):
    from azure.mgmt.monitor.models import ScaleCapacity
    autoscale_settings = client.get(resource_group_name, autoscale_name)
    capacity = ScaleCapacity(
        default=count,
        minimum=min_count or count,
        maximum=max_count or count
    )
    if recurrence:
        _create_recurring_profile(
            autoscale_settings, profile_name, start, end, recurrence, capacity, copy_rules, timezone)
    else:
        _create_fixed_profile(
            autoscale_settings, profile_name, start, end, capacity, copy_rules, timezone)
    autoscale_settings = client.create_or_update(resource_group_name, autoscale_name, autoscale_settings)
    profile = next(x for x in autoscale_settings.profiles if x.name == profile_name)
    return profile


def autoscale_profile_list(cmd, client, autoscale_name, resource_group_name):
    autoscale_settings = client.get(resource_group_name, autoscale_name)
    return autoscale_settings.profiles


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


def autoscale_profile_show(cmd, client, autoscale_name, resource_group_name, profile_name):
    autoscale_settings = client.get(resource_group_name, autoscale_name)
    return _identify_profile(autoscale_settings.profiles, profile_name)


def autoscale_profile_delete(cmd, client, autoscale_name, resource_group_name, profile_name):
    from azure.cli.command_modules.monitor._autoscale_util import build_autoscale_profile
    import json

    autoscale_settings = client.get(resource_group_name, autoscale_name)
    default_profile, _ = build_autoscale_profile(autoscale_settings)

    def _should_retain_profile(profile):
        name = profile.name
        try:
            name = json.loads(profile.name)['for']
        except ValueError:
            pass
        return name.lower() != profile_name.lower()

    autoscale_settings.profiles = [x for x in autoscale_settings.profiles if _should_retain_profile(x)]

    # if we removed the last "default" of a recurring pair, we need to preserve it
    new_default, _ = build_autoscale_profile(autoscale_settings)
    if not new_default:
        autoscale_settings.profiles.append(default_profile)

    autoscale_settings = client.create_or_update(resource_group_name, autoscale_name, autoscale_settings)


def autoscale_rule_create(cmd, client, autoscale_name, resource_group_name, condition,
                          scale, profile_name=DEFAULT_PROFILE_NAME, cooldown=5, source=None,
                          timegrain="avg 1m"):
    from azure.mgmt.monitor.models import ScaleRule, ScaleAction, ScaleDirection
    autoscale_settings = client.get(resource_group_name, autoscale_name)
    profile = _identify_profile(autoscale_settings.profiles, profile_name)
    condition.metric_resource_uri = source or autoscale_settings.target_resource_uri
    condition.statistic = timegrain.statistic
    condition.time_grain = timegrain.time_grain
    rule = ScaleRule(
        metric_trigger=condition,
        scale_action=ScaleAction(
            direction=scale.direction,
            type=scale.type,
            cooldown='PT{}M'.format(cooldown),
            value=scale.value)
    )
    profile.rules.append(rule)
    autoscale_settings = client.create_or_update(resource_group_name, autoscale_name, autoscale_settings)

    # determine if there are unbalanced rules
    scale_out_rule_count = len([x for x in profile.rules if x.scale_action.direction == ScaleDirection.increase])
    scale_in_rule_count = len([x for x in profile.rules if x.scale_action.direction == ScaleDirection.decrease])
    if scale_out_rule_count and not scale_in_rule_count:
        logger.warning("Profile '%s' has rules to scale out but none to scale in. "
                       "Recommend creating at least 1 scale in rule.", profile_name)
    elif scale_in_rule_count and not scale_out_rule_count:
        logger.warning("Profile '%s' has rules to scale in but none to scale out. "
                       "Recommend creating at least 1 scale out rule.", profile_name)
    return rule


def autoscale_rule_list(cmd, client, autoscale_name, resource_group_name, profile_name=DEFAULT_PROFILE_NAME):
    autoscale_settings = client.get(resource_group_name, autoscale_name)
    profile = _identify_profile(autoscale_settings.profiles, profile_name)
    index = 0
    # we artificially add indices to the rules so the user can target them with the remove command
    for rule in profile.rules:
        setattr(rule, 'index', index)
        index += 1
    return profile.rules


def autoscale_rule_delete(cmd, client, autoscale_name, resource_group_name, index, profile_name=DEFAULT_PROFILE_NAME):
    autoscale_settings = client.get(resource_group_name, autoscale_name)
    profile = _identify_profile(autoscale_settings.profiles, profile_name)
    # delete the indices provided
    if '*' in index:
        profile.rules = []
    else:
        for i in index:
            del profile.rules[int(i)]
    autoscale_settings = client.create_or_update(resource_group_name, autoscale_name, autoscale_settings)


def autoscale_rule_copy(cmd, client, autoscale_name, resource_group_name, dest_profile, index,
                        source_profile=DEFAULT_PROFILE_NAME):
    autoscale_settings = client.get(resource_group_name, autoscale_name)
    src_profile = _identify_profile(autoscale_settings.profiles, source_profile)
    dst_profile = _identify_profile(autoscale_settings.profiles, dest_profile)
    if '*' in index:
        dst_profile.rules = src_profile.rules
    else:
        for i in index:
            dst_profile.rules.append(src_profile.rules[int(i)])
    autoscale_settings = client.create_or_update(resource_group_name, autoscale_name, autoscale_settings)


def _identify_profile(profiles, profile_name):
    try:
        profile = next(x for x in profiles if x.name == profile_name)
    except StopIteration:
        raise CLIError('Cannot find profile {}. '
                       'Please double check the name of the autoscale profile.'.format(profile_name))
    return profile
