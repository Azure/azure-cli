# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

from azure.cli.core.aaz import AAZStrArg, AAZListArg
from azure.cli.command_modules.monitor.actions import AAZCustomListArg
from azure.cli.command_modules.monitor.aaz.latest.monitor.action_group.test_notifications._create \
    import Create as _ActionGroupTestNotificationCreate
from azure.cli.command_modules.monitor.operations.action_groups import update_action_group_receivers


class ActionGroupTestNotificationCreate(_ActionGroupTestNotificationCreate):

    def __init__(self, *args, **kwargs):
        from azure.cli.command_modules.monitor.transformers import action_group_list_table
        super().__init__(*args, **kwargs)
        self.table_transformer = action_group_list_table

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
        args_schema.receiver_actions = AAZCustomListArg(
            options=["--add-actions"],
            singular_options=["--add-action", "-a"],
            help='''
        Add receivers to the action group.\n\n
        Usage:   --add-action TYPE NAME [ARG ...]\n\n
        Email:\n\n
            Format:     --add-action email NAME EMAIL_ADDRESS [usecommonalertschema]\n\n
            Example:    --add-action email bob bob@contoso.com\n\n
        SMS:\n\n
            Format:     --add-action sms NAME COUNTRY_CODE PHONE_NUMBER\n\n
            Example:    --add-action sms charli 1 5551234567\n\n
        Webhook:\n\n
            Format:     --add-action webhook NAME URI [useaadauth OBJECT_ID IDENTIFIER URI] [usecommonalertschema]\n\n
            Example:    --add-action https://www.contoso.com/alert useaadauth testobj http://identifier usecommonalertschema\n\n
        Arm Role:\n\n
            Format:     --add-action armrole NAME ROLE_ID [usecommonalertschema]\n\n
            Example:    --add-action armole owner_role 8e3af657-a8ff-443c-a75c-2fe8c4bcb635\n\n
        Azure App Push:\n\n
            Format:     --add-action azureapppush NAME EMAIL_ADDRESS\n\n
            Example:    --add-action azureapppush test_apppush bob@contoso.com\n\n
        ITSM:\n\n
            Format:     --add-action itsm NAME WORKSPACE_ID CONNECTION_ID TICKET_CONFIGURATION REGION\n\n
            Example:    --add-action itsm test_itsm test_workspace test_conn ticket_blob useast\n\n
        Automation runbook:\n\n
            Format:     --add-action automationrunbook NAME AUTOMATION_ACCOUNT_ID RUNBOOK_NAME WEBHOOK_RESOURCE_ID SERVICE_URI [isglobalrunbook] [usecommonalertschema]\n\n
            Example:    --add-action automationrunbook test_runbook test_acc test_book test_webhook test_rsrc http://example.com isglobalrunbook usecommonalertschema\n\n
        Voice:\n\n
            Format:     --add-action voice NAME COUNTRY_CODE PHONE_NUMBER\n\n
            Example:    --add-action voice charli 1 4441234567\n\n
        Logic App:\n\n
            Format:     --add-action logicapp NAME RESOURCE_ID CALLBACK_URL [usecommonalertschema]\n\n
            Example:    --add-action logicapp test_logicapp test_rsrc http://callback\n\n
        Azure Function:\n\n
            Format:     --add-action azurefunction NAME FUNCTION_APP_RESOURCE_ID FUNCTION_NAME HTTP_TRIGGER_URL [usecommonalertschema]\n\n
            Example:    --add-action azurefunction test_function test_rsrc test_func http://trigger usecommonalertschema\n\n
        Event Hub:\n\n
            Format:     --action eventhub NAME SUBSCRIPTION_ID EVENT_HUB_NAME_SPACE EVENT_HUB_NAME [usecommonalertschema]\n\n
            Example:    --action eventhub test_eventhub 5def922a-3ed4-49c1-b9fd-05ec533819a3 eventhubNameSpace testEventHubName usecommonalertschema\n\n
        Multiple actions can be specified by using more than one `--add-action` argument.\n\n
        'useaadauth', 'isglobalrunbook' and 'usecommonalertschema' are optional arguements that only need to be passed to set the respective parameter to True.\n\n
        If the 'useaadauth' argument is passed, then the OBJECT_ID and IDENTIFIER_URI values are required as well.''',
        )
        args_schema.receiver_actions.Element = AAZListArg()
        args_schema.receiver_actions.Element.Element = AAZStrArg()
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        update_action_group_receivers(args)
