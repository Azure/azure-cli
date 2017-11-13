# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

# pylint: disable=line-too-long, too-many-lines

helps['monitor'] = """
    type: group
    short-summary: Manage the Azure Monitor Service.
"""

helps['monitor alert'] = """
    type: group
    short-summary: Manage metric-based alert rules.
"""

helps['monitor alert create'] = """
    type: command
    short-summary: Create a metric-based alert rule.
    parameters:
        - name: --action -a
          short-summary: Add an action to fire when the alert is triggered.
          long-summary: |
            Usage:   --action TYPE KEY [ARG ...]
            Email:   --action email bob@contoso.com ann@contoso.com
            Webhook: --action webhook https://www.contoso.com/alert apiKey=value
            Webhook: --action webhook https://www.contoso.com/alert?apiKey=value
            Multiple actions can be specified by using more than one `--action` argument.
        - name: --description
          short-summary: Free-text description of the rule. Defaults to the condition expression.
        - name: --disabled
          short-summary: Create the rule in a disabled state.
        - name: --condition
          short-summary: The condition which triggers the rule.
          long-summary: >
            The form of a condition is "METRIC {>,>=,<,<=} THRESHOLD {avg,min,max,total,last} PERIOD".
            Values for METRIC and appropriate THRESHOLD values can be obtained from `az monitor metric` commands,
            and PERIOD is of the form "##h##m##s".
        - name: --email-service-owners
          short-summary: Email the service owners if an alert is triggered.
    examples:
        - name: Create a high CPU usage alert on a VM with no actions.
          text: >
            az monitor alert create -n rule1 -g {RG} --target {VM ID} --condition "Percentage CPU > 90 avg 5m"
        - name: Create a high CPU usage alert on a VM with email and webhook actions.
          text: |
            az monitor alert create -n rule1 -g {RG} --target {VM ID} \\
                --condition "Percentage CPU > 90 avg 5m" \\
                --action email bob@contoso.com ann@contoso.com --email-service-owners \\
                --action webhook https://www.contoso.com/alerts?type=HighCPU \\
                --action webhook https://alerts.contoso.com apiKey={KEY} type=HighCPU
"""

helps['monitor alert update'] = """
    type: command
    short-summary: Update a metric-based alert rule.
    parameters:
        - name: --target
          short-summary: ID of the resource to target for the alert rule.
        - name: --description
          short-summary: Description of the rule.
        - name: --condition
          short-summary: The condition which triggers the rule.
          long-summary: >
            The form of a condition is "METRIC {>,>=,<,<=} THRESHOLD {avg,min,max,total,last} PERIOD".
            Values for METRIC and appropriate THRESHOLD values can be obtained from `az monitor metric` commands,
            and PERIOD is of the form "##h##m##s".
        - name: --add-action -a
          short-summary: Add an action to fire when the alert is triggered.
          long-summary: |
            Usage:   --add-action TYPE KEY [ARG ...]
            Email:   --add-action email bob@contoso.com ann@contoso.com
            Webhook: --add-action webhook https://www.contoso.com/alert apiKey=value
            Webhook: --add-action webhook https://www.contoso.com/alert?apiKey=value
            Multiple actions can be specified by using more than one `--add-action` argument.
        - name: --remove-action -r
          short-summary: Remove one or more actions.
          long-summary: |
            Usage:   --remove-action TYPE KEY [KEY ...]
            Email:   --remove-action email bob@contoso.com ann@contoso.com
            Webhook: --remove-action webhook https://contoso.com/alert https://alerts.contoso.com
        - name: --email-service-owners
          short-summary: Email the service owners if an alert is triggered.
        - name: --metric
          short-summary: Name of the metric to base the rule on.
          populator-commands:
            - az monitor metrics list-definitions
        - name: --operator
          short-summary: How to compare the metric against the threshold.
        - name: --threshold
          short-summary: Numeric threshold at which to trigger the alert.
        - name: --aggregation
          short-summary: Type of aggregation to apply based on --period.
        - name: --period
          short-summary: >
            Time span over which to apply --aggregation, in nDnHnMnS shorthand or full ISO8601 format.
"""

helps['monitor alert delete'] = """
    type: command
    short-summary: Delete an alert rule.
    """

helps['monitor alert list'] = """
    type: command
    short-summary: List alert rules in a resource group.
    """

helps['monitor alert show'] = """
    type: command
    short-summary: Show an alert rule.
    """

helps['monitor alert show-incident'] = """
    type: command
    short-summary: Get the details of an alert rule incident.
    """

helps['monitor alert list-incidents'] = """
    type: command
    short-summary: List all incidents for an alert rule.
    """

helps['monitor metrics'] = """
    type: group
    short-summary: View Azure resource metrics.
"""

helps['monitor metrics list'] = """
    type: command
    short-summary: List the metric values for a resource.
    parameters:
        - name: --aggregation
          type: string
          short-summary: The list of aggregation types (space separated) to retrieve.
        - name: --interval
          type: string
          short-summary: The interval of the metric query. In ISO 8601 duration format, eg "PT1M"
        - name: --start-time
          type: string
          short-summary: The start time of the query. In ISO format with explicit indication of timezone,
                         1970-01-01T00:00:00Z, 1970-01-01T00:00:00-0500. Defaults to 1 Hour prior to the current time.
        - name: --end-time
          type: string
          short-summary: The end time of the query. In ISO format with explicit indication of timezone,
                         1970-01-01T00:00:00Z, 1970-01-01T00:00:00-0500. Defaults to current time.
        - name: --filter
          type: string
          short-summary: A string used to reduce the set of metric data returned. eg. "BlobType eq '*'"
        - name: --metadata
          short-summary: Returns the metadata values instead of metric data
        - name: --dimension
          type: string
          short-summary: The list of dimensions (space separated) the metrics are queried into.
    examples:
        - name: List a VM's CPU usage for the past hour
          text: >
              az monitor metrics list --resource <resource id> --metric "Percentage CPU"
        - name: List success E2E latency of a storage account and split the data series based on API name
          text: >
              az monitor metrics list --resource <resource id> --metric SuccessE2ELatency \\
                                      --dimension ApiName
        - name: List success E2E latency of a storage account and split the data series based on both API name and geo type
          text: >
              az monitor metrics list --resource <resource id> --metric SuccessE2ELatency \\
                                      --dimension ApiName GeoType
        - name: List success E2E latency of a storage account and split the data series based on both API name and geo type using "--filter" parameter
          text: >
              az monitor metrics list --resource <resource id> --metric SuccessE2ELatency \\
                                      --filter "ApiName eq '*' and GeoType eq '*'"
        - name: List success E2E latency of a storage account and split the data series based on both API name and geo type. Limits the api name to 'DeleteContainer'
          text: >
              az monitor metrics list --resource <resource id> --metric SuccessE2ELatency \\
                                      --filter "ApiName eq 'DeleteContainer' and GeoType eq '*'"
              Filter string reference: https://docs.microsoft.com/en-us/rest/api/monitor/metrics/list
        - name: List transactions of a storage account per day since 2017-01-01
          text: >
              az monitor metrics list --resource <resource id> --metric Transactions \\
                                      --start-time 2017-01-01T00:00:00Z \\
                                      --interval PT24H
        - name: List the metadata values for a storage account under transaction metric's api name dimension since 2017
          text: >
              az monitor metrics list --resource <resource id> --metric Transactions \\
                                      --filter "ApiName eq '*'" \\
                                      --start-time 2017-01-01T00:00:00Z
"""

helps['monitor metrics list-definitions'] = """
    type: command
    short-summary: Lists the metric definitions for the resource.
    parameters:
        - name: --metric-names
          type: string
          short-summary: The list of the metrics definitions to be shown.
"""

# endregion

helps['monitor log-profiles'] = """
            type: group
            short-summary: Manage log profiles.
            """
helps['monitor log-profiles update'] = """
            type: command
            short-summary: Update a log profile.
            """
helps['monitor diagnostic-settings'] = """
            type: group
            short-summary: Manage service diagnostic settings.
            """
helps['monitor diagnostic-settings create'] = """
            type: command
            short-summary: Create diagnostic settings for the specified resource.
            parameters:
                - name: --resource-id
                  type: string
                  short-summary: The identifier of the resource.
                - name: --resource-group -g
                  type: string
                  short-summary: Name of the resource group.
                - name: --logs
                  type: string
                  short-summary: JSON encoded list of logs settings. Use @{file} to load from a file.
                - name: --event-hub-name
                  type: string
                  short-summary: The name of the event hub. If none is specified, the default event hub will be
                                 selected.
                - name: --metrics
                  type: string
                  short-summary: JSON encoded list of metric settings. Use @{file} to load from a file.
                - name: --storage-account
                  type: string
                  short-summary: Name or ID of the storage account to send diagnostic logs to.
                - name: --namespace
                  type: string
                  short-summary: Name or ID of the Service Bus namespace.
                - name: --rule-name
                  type: string
                  short-summary: Name of the Service Bus authorization rule.
                - name: --workspace
                  type: string
                  short-summary: Name or ID of the Log Analytics workspace to send diagnostic logs to.
                - name: --tags
                  short-summary: Space separated tags in 'key[=value]' format. Use '' to clear existing tags
            """
helps['monitor diagnostic-settings update'] = """
            type: command
            short-summary: Update diagnostic settings.
            """
helps['monitor autoscale-settings'] = """
            type: group
            short-summary: Manage autoscale settings.
            """
helps['monitor autoscale-settings update'] = """
            type: command
            short-summary: Updates an autoscale setting.
            """

helps['monitor activity-log'] = """
    type: group
    short-summary: Manage activity logs.
"""

helps['monitor action-group'] = """
    type: group
    short-summary: Manage action groups
"""

helps['monitor action-group list'] = """
    type: command
    short-summary: List action groups under a resource group or the current subscription
    parameters:
        - name: --resource-group -g
          type: string
          short-summary: Name of the resource group under which the action groups are being listed. If it is omitted,
                         all the action groups under the current subscription are listed.
"""

helps['monitor action-group show'] = """
    type: command
    short-summary: Show the details of an action group
"""

helps['monitor action-group create'] = """
    type: command
    short-summary: Create a new action group
    parameters:
        - name: --action -a
          short-summary: Add receivers to the action group during the creation
          long-summary: |
            Usage:   --action TYPE NAME [ARG ...]
            Email:   --action email bob bob@contoso.com
            SMS:     --action sms charli 1 5551234567
            Webhook: --action webhook alert_hook https://www.contoso.com/alert
            Multiple actions can be specified by using more than one `--action` argument.
        - name: --short-name
          short-summary: The short name of the action group
"""

helps['monitor action-group update'] = """
    type: command
    short-summary: Update an action group
    parameters:
        - name: --short-name
          short-summary: Update the group short name of the action group
        - name: --add-action -a
          short-summary: Add receivers to the action group
          long-summary: |
            Usage:   --add-action TYPE NAME [ARG ...]
            Email:   --add-action email bob bob@contoso.com
            SMS:     --add-action sms charli 1 5551234567
            Webhook: --add-action https://www.contoso.com/alert
            Multiple actions can be specified by using more than one `--add-action` argument.
        - name: --remove-action -r
          short-summary: Remove receivers from the action group. Accept space separated list of receiver names.
"""

helps['monitor activity-log alert'] = """
    type: group
    short-summary: Manage activity log alerts
"""

helps['monitor activity-log alert list'] = """
    type: command
    short-summary: List activity log alerts under a resource group or the current subscription.
    parameters:
        - name: --resource-group -g
          short-summary: Name of the resource group under which the activity log alerts are being listed. If it is
                         omitted, all the activity log alerts under the current subscription are listed.
"""

helps['monitor activity-log alert create'] = """
    type: command
    short-summary: Create a default activity log alert
    long-summary: This command will create a default activity log with one condition which compares if the activities
                  logs 'category' field equals to 'ServiceHealth'. The newly created activity log alert does not have
                  any action groups attached to it.
    parameters:
        - name: --name -n
          short-summary: Name of the activity log alerts
        - name: --scope -s
          short-summary: A list of string that will be used as prefixes. The alert will only apply to activityLogs
                         with resourceIds that fall under one of these prefixes. If not provided, the path to this
                         resource group will be used.
        - name: --disable
          short-summary: Disable the activity log alert after it is created.
        - name: --description
          short-summary: A description of this activity log alert
        - name: --condition -c
          short-summary: A condition expression represents the condition that will cause the alert to activate. The
                         format is FIELD=VALUE[ and FILED=VALUE...]. The possible values for the field are 'resourceId',
                         'category', 'caller', 'level', 'operationName', 'resourceGroup', 'resourceProvider', 'status',
                         'subStatus', 'resourceType', or anything beginning with 'properties.'.
        - name: --action-group -a
          short-summary: Add action group. Accept space separated action groups identifiers. The identify can be the
                         action group's name or its resource id.
        - name: --webhook-properties -w
          short-summary: Space separated web hook properties in 'key[=value]' format. These properties will be
                         associated with the action groups added in this command. For any webhook receiver in these
                         action group, these data are appended to the webhook payload. To attach different webhook
                         properties to different action groups, add the action groups in separate update-action
                         commands.
    examples:
        - name: Create an alert with default settings.
          text: >
              az monitor activity-log alert create -n {ALERT_NAME} -g {RG}

        - name: Create an alert with condition about error level service health log.
          text: >
              az monitor activity-log alert create -n {ALERT_NAME} -g {RG} \\
                --condition category=ServiceHealth and level=Error

        - name: Create an alert with an action group and specify webhook properties.
          text: >
              az monitor activity-log alert create -n {ALERT_NAME} -g {RG} \\
                -a /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/microsoft.insights/actionGroups/example_action_group
                -w usage=test owner=jane

        - name: Create an alert is disabled initially.
          text: >
              az monitor activity-log alert create -n {ALERT_NAME} -g {RG} --disable
"""

helps['monitor activity-log alert update'] = """
    type: command
    short-summary: Update the details of this activity log alert
    parameters:
        - name: --description
          short-summary: A description of this activity log alert.
        - name: --condition -c
          short-summary: A condition expression represents the condition that will cause the alert to activate. The
                         format is FIELD=VALUE[ and FILED=VALUE...]. The possible values for the field are 'resourceId',
                         'category', 'caller', 'level', 'operationName', 'resourceGroup', 'resourceProvider', 'status',
                         'subStatus', 'resourceType', or anything beginning with 'properties.'.
        - name: --enable
          short-summary: Enable or disable this activity log alert.
    examples:
        - name: Update the condition
          text: >
              az monitor activity-log alert update -n {ALERT_NAME} -g {RG} \\
                --condition category=ServiceHealth and level=Error

        - name: Disable an alert
          text: >
              az monitor activity-log alert update -n {ALERT_NAME} -g {RG} --enable false
"""

helps['monitor activity-log alert action-group'] = """
    type: group
    short-summary: Manage action groups for activity log alerts
"""

helps['monitor activity-log alert action-group add'] = """
    type: command
    short-summary: Add action groups to this activity log alert. It can also be used to overwrite existing webhook
                   properties of particular action groups.
    parameters:
        - name: --name -n
          short-summary: Name of the activity log alerts
        - name: --action-group -a
          short-summary: The names or the resource ids of the action groups to be added.
        - name: --reset
          short-summary: Remove all the existing action groups before add new conditions.
        - name: --webhook-properties -w
          short-summary: Space separated web hook properties in 'key[=value]' format. These properties will be
                         associated with the action groups added in this command. For any webhook receiver in these
                         action group, these data are appended to the webhook payload. To attach different webhook
                         properties to different action groups, add the action groups in separate update-action
                         commands.
        - name: --strict
          short-summary: Fails the command if an action group to be added will change existing webhook properties.
    examples:
        - name: Add an action group and specify webhook properties.
          text: >
              az monitor activity-log alert action-group add -n {ALERT_NAME} -g {RG} \\
                --action /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/microsoft.insights/actionGroups/example_action_group
                --webhook-properties usage=test owner=jane

        - name: Overwite an existing action group's webhook properties.
          text: >
              az monitor activity-log alert action-group add -n {ALERT_NAME} -g {RG} \\
                -a /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/microsoft.insights/actionGroups/example_action_group
                --webhook-properties usage=test owner=john

        - name: Remove webhook properties from an existing action group.
          text: >
              az monitor activity-log alert action-group add -n {ALERT_NAME} -g {RG} \\
                -a /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/microsoft.insights/actionGroups/example_action_group

        - name: Add new action groups but prevent the command from accidently overwrite existing webhook properties
          text: >
              az monitor activity-log alert action-group add -n {ALERT_NAME} -g {RG} --strict \\
                --action-group {A_LIST_OF_RESOURCE_IDS}
"""

helps['monitor activity-log alert action-group remove'] = """
    type: command
    short-summary: Remove action groups from this activity log alert
    parameters:
        - name: --name -n
          short-summary: Name of the activity log alerts
        - name: --action-group -a
          short-summary: The names or the resource ids of the action groups to be added.
"""

helps['monitor activity-log alert scope'] = """
    type: group
    short-summary: Manage scopes for activity log alerts
"""

helps['monitor activity-log alert scope add'] = """
    type: command
    short-summary: Add scopes to this activity log alert.
    parameters:
        - name: --name -n
          short-summary: Name of the activity log alerts
        - name: --scope -s
          short-summary: The scopes to add
        - name: --reset
          short-summary: Remove all the existing scopes before add new scopes.
"""

helps['monitor activity-log alert scope remove'] = """
    type: command
    short-summary: Removes scopes from this activity log alert.
    parameters:
        - name: --name -n
          short-summary: Name of the activity log alerts
        - name: --scope -s
          short-summary: The scopes to remove
"""

helps['monitor activity-log list-categories'] = """
    type: command
    short-summary: List the event categories of activity logs.
"""
