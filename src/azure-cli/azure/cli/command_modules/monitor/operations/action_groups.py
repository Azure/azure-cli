# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.aaz import has_value, AAZStrArg, AAZListArg
from azure.cli.core.commands.validators import validate_tags
from azure.cli.core.azclierror import ValidationError
from ..aaz.latest.monitor.action_group import Create as _ActionGroupCreate, Update as _ActionGroupUpdate
from ..aaz.latest.monitor.action_group.test_notifications import Create as _ActionGroupTestNotificationCreate


def update_action_group_receivers(args):
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
    for receiver_item in args.receiver_actions:
        receiver_item_arr = receiver_item.to_serialized_data()
        type_name = receiver_item_arr[0].to_serialized_data()
        type_properties = [t.to_serialized_data() for t in receiver_item_arr[1:]]
        useCommonAlertSchema = 'usecommonalertschema' in (t_property.lower() for t_property in type_properties)
        try:
            if type_name == 'email':
                args.email_receivers.append({
                    'name': type_properties[0],
                    "email_address": type_properties[1],
                    "use_common_alert_schema": useCommonAlertSchema
                })
            elif type_name == 'sms':
                args.sms_receivers.append({
                    "name": type_properties[0],
                    "country_code": type_properties[1],
                    "phone_number": type_properties[2]
                })
            elif type_name == 'webhook':
                useAadAuth = len(type_properties) >= 3 and type_properties[2] == 'useaadauth'
                object_id = type_properties[3] if useAadAuth else None
                identifier_uri = type_properties[4] if useAadAuth else None
                args.webhook_receivers.append({
                    "name": type_properties[0],
                    "service_uri": type_properties[1],
                    "use_common_alert_schema": useCommonAlertSchema,
                    "use_aad_auth": useAadAuth,
                    "object_id": object_id,
                    "identifier_uri": identifier_uri
                })
            elif type_name == 'armrole':
                args.arm_role_receivers.append({
                    "name": type_properties[0],
                    "role_id": type_properties[1],
                    "use_common_alert_schema": useCommonAlertSchema
                })
            elif type_name == 'azureapppush':
                args.azure_app_push_receivers.append({
                    "name": type_properties[0],
                    "email_address": type_properties[1]
                })
            elif type_name == 'itsm':
                args.itsm_receivers.append({
                    "name": type_properties[0],
                    "workspace_id": type_properties[1],
                    "connection_id": type_properties[2],
                    "ticket_configuration": type_properties[3],
                    "region": type_properties[4]
                })
            elif type_name == 'automationrunbook':
                isGlobalRunbook = 'isglobalrunbook' in (t_property.lower() for t_property in type_properties)
                args.automation_runbook_receivers.append({
                    "name": type_properties[0],
                    "automation_account_id": type_properties[1],
                    "runbook_name": type_properties[2],
                    "webhook_resource_id": type_properties[3],
                    "service_uri": type_properties[4],
                    "is_global_runbook": isGlobalRunbook,
                    "use_common_alert_schema": useCommonAlertSchema
                })
            elif type_name == 'voice':
                args.voice_receivers.append({
                    "name": type_properties[0],
                    "country_code": type_properties[1],
                    "phone_number": type_properties[2]
                })
            elif type_name == 'logicapp':
                args.logic_app_receivers.append({
                    "name": type_properties[0],
                    "resource_id": type_properties[1],
                    "callback_url": type_properties[2],
                    "use_common_alert_schema": useCommonAlertSchema
                })
            elif type_name == 'azurefunction':
                args.azure_function_receivers.append({
                    "name": type_properties[0],
                    "function_app_resource_id": type_properties[1],
                    "function_name": type_properties[2],
                    "http_trigger_url": type_properties[3],
                    "use_common_alert_schema": useCommonAlertSchema
                })
            elif type_name == 'eventhub':
                args.event_hub_receivers.append({
                    "name": type_properties[0],
                    "subscription_id": type_properties[1],
                    "event_hub_name_space": type_properties[2],
                    "event_hub_name": type_properties[3],
                    "use_common_alert_schema": useCommonAlertSchema
                })
            else:
                raise ValidationError('The type "{}" is not recognizable.'.format(type_name))

        except IndexError:
            raise ValidationError('--action {}'.format(syntax[type_name]))


class ActionGroupCreate(_ActionGroupCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.arm_role_receivers._registered = False
        args_schema.automation_runbook_receivers._registered = False
        args_schema.azure_app_push_receivers._registered = False
        args_schema.azure_function_receivers._registered = False
        args_schema.email_receivers._registered = False
        args_schema.enabled._registered = False
        args_schema.event_hub_receivers._registered = False
        args_schema.itsm_receivers._registered = False
        args_schema.logic_app_receivers._registered = False
        args_schema.sms_receivers._registered = False
        args_schema.voice_receivers._registered = False
        args_schema.webhook_receivers._registered = False
        args_schema.receiver_actions = AAZListArg(
            options=["--actions"],
            singular_options=["--action", "-a"],
            help="Add receivers to the action group during the creation.",
            arg_group="Actions",
        )
        args_schema.receiver_actions.Element = AAZListArg()
        args_schema.receiver_actions.Element.Element = AAZStrArg()
        return args_schema

    def pre_operations(self):

        args = self.ctx.args
        validate_tags(args)
        action_group_name = args.action_group_name.to_serialized_data()
        if not has_value(args.location):
            # both inputed or 'global' location are available for action group
            args.location = "Global"
        if not has_value(args.group_short_name):
            # '12' is the short name length limitation
            args.group_short_name = action_group_name[:12]
        if not has_value(args.receiver_actions):
            return
        update_action_group_receivers(args)


class ActionGroupUpdate(_ActionGroupUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.arm_role_receivers._registered = False
        args_schema.automation_runbook_receivers._registered = False
        args_schema.azure_app_push_receivers._registered = False
        args_schema.azure_function_receivers._registered = False
        args_schema.email_receivers._registered = False
        args_schema.enabled._registered = False
        args_schema.event_hub_receivers._registered = False
        args_schema.itsm_receivers._registered = False
        args_schema.logic_app_receivers._registered = False
        args_schema.sms_receivers._registered = False
        args_schema.voice_receivers._registered = False
        args_schema.webhook_receivers._registered = False
        args_schema.receiver_add_actions = AAZListArg(
            options=["--add-actions"],
            singular_options=["--add-action", "-a"],
            help="Add receivers to the action group.",
            arg_group="Actions",
        )
        args_schema.receiver_add_actions.Element = AAZListArg()
        args_schema.receiver_add_actions.Element.Element = AAZStrArg()

        args_schema.receiver_remove_list = AAZListArg(
            options=["--remove-action", "-r"],
            help="Remove receivers from the action group. Accept space-separated list of receiver names.",
            arg_group="Actions",
        )
        args_schema.receiver_remove_list.Element = AAZStrArg()
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        update_action_group_receivers(args)

    def post_instance_delete(self):
        args = self.ctx.args
        instance = self.ctx.vars.instance
        if not has_value(args.receiver_remove_list):
            return
        receiver_remove_list = [t.to_serialized_data() for t in args.receiver_remove_list]

        def filter_receivers(collection):
            return [receiver for receiver in collection if receiver.name not in receiver_remove_list]

        instance.properties.email_receivers = filter_receivers(instance.email_receivers)
        instance.properties.sms_receivers = filter_receivers(instance.sms_receivers)
        instance.properties.webhook_receivers = filter_receivers(instance.webhook_receivers)
        instance.properties.arm_role_receivers = filter_receivers(instance.arm_role_receivers)
        instance.properties.azure_app_push_receivers = filter_receivers(instance.azure_app_push_receivers)
        instance.properties.itsm_receivers = filter_receivers(instance.itsm_receivers)
        instance.properties.automation_runbook_receivers = filter_receivers(instance.automation_runbook_receivers)
        instance.properties.voice_receivers = filter_receivers(instance.voice_receivers)
        instance.properties.logic_app_receivers = filter_receivers(instance.logic_app_receivers)
        instance.properties.azure_function_receivers = filter_receivers(instance.azure_function_receivers)
        instance.properties.event_hub_receivers = filter_receivers(instance.event_hub_receivers)


class ActionGroupTestNotificationCreate(_ActionGroupTestNotificationCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.arm_role_receivers._registered = False
        args_schema.automation_runbook_receivers._registered = False
        args_schema.azure_app_push_receivers._registered = False
        args_schema.azure_function_receivers._registered = False
        args_schema.email_receivers._registered = False

        args_schema.event_hub_receivers._registered = False
        args_schema.itsm_receivers._registered = False
        args_schema.logic_app_receivers._registered = False
        args_schema.sms_receivers._registered = False
        args_schema.voice_receivers._registered = False
        args_schema.webhook_receivers._registered = False
        args_schema.receiver_add_actions = AAZListArg(
            options=["--add-actions"],
            singular_options=["--add-action", "-a"],
            help="Add receivers to the action group.",
            arg_group="Actions",
        )
        args_schema.receiver_add_actions.Element = AAZListArg()
        args_schema.receiver_add_actions.Element.Element = AAZStrArg()
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        update_action_group_receivers(args)
