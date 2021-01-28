# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def list_action_groups(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list_by_subscription_id()


def update_action_groups(instance, tags=None, short_name=None, add_receivers=None, remove_receivers=None):
    if tags:
        instance.tags = tags

    if short_name:
        instance.group_short_name = short_name

    if remove_receivers:
        remove_receivers = set(remove_receivers)

        def filter_receivers(collection):
            return [receiver for receiver in collection if receiver.name not in remove_receivers]

        instance.email_receivers = filter_receivers(instance.email_receivers)
        instance.sms_receivers = filter_receivers(instance.sms_receivers)
        instance.webhook_receivers = filter_receivers(instance.webhook_receivers)
        instance.arm_role_receivers = filter_receivers(instance.arm_role_receivers)
        instance.azure_app_push_receivers = filter_receivers(instance.azure_app_push_receivers)
        instance.itsm_receivers = filter_receivers(instance.itsm_receivers)
        instance.automation_runbook_receivers = filter_receivers(instance.automation_runbook_receivers)
        instance.voice_receivers = filter_receivers(instance.voice_receivers)
        instance.logic_app_receivers = filter_receivers(instance.logic_app_receivers)
        instance.azure_function_receivers = filter_receivers(instance.azure_function_receivers)

    if add_receivers:
        from azure.mgmt.monitor.models import EmailReceiver, SmsReceiver, WebhookReceiver, \
            ArmRoleReceiver, AzureAppPushReceiver, ItsmReceiver, AutomationRunbookReceiver, \
            VoiceReceiver, LogicAppReceiver, AzureFunctionReceiver
        for r in add_receivers:
            if isinstance(r, EmailReceiver):
                instance.email_receivers.append(r)
            elif isinstance(r, SmsReceiver):
                instance.sms_receivers.append(r)
            elif isinstance(r, WebhookReceiver):
                instance.webhook_receivers.append(r)
            elif isinstance(r, ArmRoleReceiver):
                instance.arm_role_receivers.append(r)
            elif isinstance(r, AzureAppPushReceiver):
                instance.azure_app_push_receivers.append(r)
            elif isinstance(r, ItsmReceiver):
                instance.itsm_receivers.append(r)
            elif isinstance(r, AutomationRunbookReceiver):
                instance.automation_runbook_receivers.append(r)
            elif isinstance(r, VoiceReceiver):
                instance.voice_receivers.append(r)
            elif isinstance(r, LogicAppReceiver):
                instance.logic_app_receivers.append(r)
            elif isinstance(r, AzureFunctionReceiver):
                instance.azure_function_receivers.append(r)

    return instance


def enable_receiver(client, resource_group_name, action_group_name, receiver_name):
    from azure.mgmt.monitor.models import EnableRequest
    enable_request = EnableRequest(receiver_name=receiver_name)
    return client.enable_receiver(resource_group_name=resource_group_name,
                                  action_group_name=action_group_name,
                                  enable_request=enable_request)
