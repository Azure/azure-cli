# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

from azure.cli.core.aaz import has_value, AAZStrArg
from azure.cli.core.commands.validators import validate_tags
from azure.cli.command_modules.monitor.actions import AAZCustomListArg
from azure.cli.command_modules.monitor.aaz.latest.monitor.action_group._create import Create as _ActionGroupCreate
from azure.cli.command_modules.monitor.operations.action_groups import update_action_group_receivers


class ActionGroupCreate(_ActionGroupCreate):

    def __init__(self, *args, **kwargs):
        from azure.cli.command_modules.monitor.transformers import action_group_list_table
        super().__init__(*args, **kwargs)
        self.table_transformer = action_group_list_table

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.receiver_actions = AAZCustomListArg(
            options=["--actions"],
            singular_options=["--action", "-a"],
            help='''
        Add receivers to the action group during the creation.\n\n
        Usage:   --action TYPE NAME [ARG ...]\n\n
        Email:\n\n
            Format:     --action email NAME EMAIL_ADDRESS [usecommonalertschema]\n\n
            Example:    --action email bob bob@contoso.com\n\n
        SMS:\n\n
            Format:     --action sms NAME COUNTRY_CODE PHONE_NUMBER\n\n
            Example:    --action sms charli 1 5551234567\n\n
        Webhook:\n\n
            Format:     --action webhook NAME URI [useaadauth OBJECT_ID IDENTIFIER URI] [usecommonalertschema]\n\n
            Example:    --action webhook alert_hook https://www.contoso.com/alert useaadauth testobj http://identifier usecommonalertschema\n\n
        Arm Role:\n\n
            Format:     --action armrole NAME ROLE_ID [usecommonalertschema]\n\n
            Example:    --action armole owner_role 8e3af657-a8ff-443c-a75c-2fe8c4bcb635\n\n
        Azure App Push:\n\n
            Format:     --action azureapppush NAME EMAIL_ADDRESS\n\n
            Example:    --action azureapppush test_apppush bob@contoso.com\n\n
        ITSM:\n\n
            Format:     --action itsm NAME WORKSPACE_ID CONNECTION_ID TICKET_CONFIGURATION REGION\n\n
            Example:    --action itsm test_itsm test_workspace test_conn ticket_blob useast\n\n
        Automation runbook:\n\n
            Format:     --action automationrunbook NAME AUTOMATION_ACCOUNT_ID RUNBOOK_NAME WEBHOOK_RESOURCE_ID SERVICE_URI [isglobalrunbook] [usecommonalertschema]\n\n
            Example:    --action automationrunbook test_runbook test_acc test_book test_webhook test_rsrc http://example.com isglobalrunbook usecommonalertschema\n\n
        Voice:\n\n
            Format:     --action voice NAME COUNTRY_CODE PHONE_NUMBER\n\n
            Example:    --action voice charli 1 4441234567\n\n
        Logic App:\n\n
            Format:     --action logicapp NAME RESOURCE_ID CALLBACK_URL [usecommonalertschema]\n\n
            Example:    --action logicapp test_logicapp test_rsrc http://callback\n\n
        Azure Function:\n\n
            Format:     --action azurefunction NAME FUNCTION_APP_RESOURCE_ID FUNCTION_NAME HTTP_TRIGGER_URL [usecommonalertschema]\n\n
            Example:    --action azurefunction test_function test_rsrc test_func http://trigger usecommonalertschema\n\n
        Event Hub:\n\n
            Format:     --action eventhub NAME SUBSCRIPTION_ID EVENT_HUB_NAME_SPACE EVENT_HUB_NAME [usecommonalertschema]\n\n
            Example:    --action eventhub test_eventhub 5def922a-3ed4-49c1-b9fd-05ec533819a3 eventhubNameSpace testEventHubName usecommonalertschema\n\n
        Multiple actions can be specified by using more than one `--add-action` argument.\n\n
        'useaadauth', 'isglobalrunbook' and 'usecommonalertschema' are optional arguements that only need to be passed to set the respective parameter to True.\n\n
        If the 'useaadauth' argument is passed, then the OBJECT_ID and IDENTIFIER_URI values are required as well.
        ''',
            arg_group="Actions",
        )
        args_schema.receiver_actions.Element = AAZCustomListArg()
        args_schema.receiver_actions.Element.Element = AAZStrArg()
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        args.enabled = True
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
