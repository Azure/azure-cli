# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access, line-too-long, too-many-statements

import json

from azure.cli.core.aaz import has_value, AAZIntArg, AAZBoolArg, AAZStrArg
from azure.cli.command_modules.monitor.actions import AAZCustomListArg
from azure.cli.command_modules.monitor._autoscale_util import get_autoscale_default_profile
from azure.cli.command_modules.monitor.aaz.latest.monitor.autoscale._update import Update as _AutoScaleUpdate
from azure.cli.command_modules.monitor.operations.autoscale_settings import (
    update_add_actions, update_remove_actions, _parse_action_removals,
)
from azure.cli.core.azclierror import InvalidArgumentValueError


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
