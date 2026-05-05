# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=protected-access


def update_action_group_receivers(args):
    from azure.cli.core.azclierror import ValidationError

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
        type_name = receiver_item_arr[0]
        type_properties = receiver_item_arr[1:]
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
