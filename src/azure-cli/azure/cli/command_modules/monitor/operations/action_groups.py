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
        instance.event_hub_receivers = filter_receivers(instance.event_hub_receivers)

    if add_receivers:
        from azure.mgmt.monitor.models import EmailReceiver, SmsReceiver, WebhookReceiver, \
            ArmRoleReceiver, AzureAppPushReceiver, ItsmReceiver, AutomationRunbookReceiver, \
            VoiceReceiver, LogicAppReceiver, AzureFunctionReceiver, EventHubReceiver
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
            elif isinstance(r, EventHubReceiver):
                instance.event_hub_receivers.append(r)

    return instance


def enable_receiver(client, resource_group_name, action_group_name, receiver_name):
    from azure.mgmt.monitor.models import EnableRequest
    enable_request = EnableRequest(receiver_name=receiver_name)
    return client.enable_receiver(resource_group_name=resource_group_name,
                                  action_group_name=action_group_name,
                                  enable_request=enable_request)


# pylint: disable=too-many-locals
# pylint: disable=no-else-return
def post_notifications(client, alert_type, resource_group_name=None, action_group_name=None, add_receivers=None,
                       no_wait=False):
    from azure.mgmt.monitor.models import NotificationRequestBody
    EmailReceivers = []
    SmsReceivers = []
    WebhookReceivers = []
    ItsmReceivers = []
    AzureAppPushReceivers = []
    AutomationRunbookReceivers = []
    VoiceReceivers = []
    LogicAppReceivers = []
    AzureFunctionReceivers = []
    ArmRoleReceivers = []
    EventHubReceivers = []
    for r in add_receivers:
        from azure.mgmt.monitor.models import EmailReceiver, SmsReceiver, WebhookReceiver, ItsmReceiver, \
            AzureAppPushReceiver, AutomationRunbookReceiver, VoiceReceiver, LogicAppReceiver, AzureFunctionReceiver, \
            ArmRoleReceiver, EventHubReceiver
        if isinstance(r, EmailReceiver):
            EmailReceivers.append(EmailReceiver(name=r.name, email_address=r.email_address,
                                                use_common_alert_schema=r.use_common_alert_schema))
        elif isinstance(r, SmsReceiver):
            SmsReceivers.append(SmsReceiver(name=r.name, country_code=r.country_code, phone_number=r.phone_number))
        elif isinstance(r, WebhookReceiver):
            WebhookReceivers.append(WebhookReceiver(name=r.name, service_uri=r.service_uri,
                                                    use_common_alert_schema=r.use_common_alert_schema,
                                                    use_aad_auth=r.use_aad_auth, object_id=r.object_id,
                                                    identifier_uri=r.identifier_uri, tenant_id=r.tenant_id))
        elif isinstance(r, ItsmReceiver):
            ItsmReceivers.append(ItsmReceiver(name=r.name, workspace_id=r.workspace_id, connection_id=r.connection_id,
                                              ticket_configuration=r.ticket_configuration, region=r.region))
        elif isinstance(r, AzureAppPushReceiver):
            AzureAppPushReceivers.append(AzureAppPushReceiver(name=r.name, email_address=r.email_address))
        elif isinstance(r, AutomationRunbookReceiver):
            AutomationRunbookReceivers\
                .append(AutomationRunbookReceiver(automation_account_id=r.automation_account_id,
                                                  runbook_name=r.runbook_name,
                                                  webhook_resource_id=r.webhook_resource_id,
                                                  is_global_runbook=r.is_global_runbook,
                                                  name=r.name,
                                                  service_uri=r.service_uri,
                                                  use_common_alert_schema=r.use_common_alert_schema))
        elif isinstance(r, VoiceReceiver):
            VoiceReceivers.append(VoiceReceiver(name=r.name, country_code=r.country_code, phone_number=r.phone_number))
        elif isinstance(r, LogicAppReceiver):
            LogicAppReceivers.append(LogicAppReceiver(name=r.name, resource_id=r.resource_id,
                                                      callback_url=r.callback_url))
        elif isinstance(r, AzureFunctionReceiver):
            AzureFunctionReceivers.append(AzureFunctionReceiver(name=r.name,
                                                                function_app_resource_id=r.function_app_resource_id,
                                                                function_name=r.function_name,
                                                                http_trigger_url=r.http_trigger_url,
                                                                use_common_alert_schema=r.use_common_alert_schema))
        elif isinstance(r, ArmRoleReceiver):
            ArmRoleReceivers.append(ArmRoleReceiver(name=r.name, role_id=r.role_id,
                                                    use_common_alert_schema=r.use_common_alert_schema))
        elif isinstance(r, EventHubReceiver):
            EventHubReceivers.append(EventHubReceiver(name=r.name,
                                                      event_hub_name_space=r.event_hub_name_space,
                                                      event_hub_name=r.event_hub_name,
                                                      subscription_id=r.subscription_id))

    notification_request = NotificationRequestBody(alert_type=alert_type, email_receivers=EmailReceivers,
                                                   sms_receivers=SmsReceivers, webhook_receivers=WebhookReceivers,
                                                   itsm_receivers=ItsmReceivers,
                                                   azure_app_push_receivers=AzureAppPushReceivers,
                                                   automation_runbook_receivers=AutomationRunbookReceivers,
                                                   voice_receivers=VoiceReceivers,
                                                   logic_app_receivers=LogicAppReceivers,
                                                   azure_function_receivers=AzureFunctionReceivers,
                                                   arm_role_receivers=ArmRoleReceivers,
                                                   event_hub_receivers=EventHubReceivers)
    from azure.cli.core.util import sdk_no_wait
    if action_group_name:
        return sdk_no_wait(no_wait, client.begin_create_notifications_at_action_group_resource_level,
                           resource_group_name, action_group_name, notification_request)
    elif resource_group_name:
        return sdk_no_wait(no_wait, client.begin_create_notifications_at_resource_group_level,
                           resource_group_name, notification_request)
    else:
        return sdk_no_wait(no_wait, client.begin_post_test_notifications, notification_request)
