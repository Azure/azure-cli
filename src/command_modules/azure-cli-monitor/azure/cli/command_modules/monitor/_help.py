# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["monitor autoscale show"] = """
"type": |-
    command
"short-summary": |-
    Show autoscale setting details.
"""

helps["monitor activity-log alert update"] = """
"type": |-
    command
"short-summary": |-
    Update the details of this activity log alert
"parameters":
-   "name": |-
        --description
    "short-summary": |-
        A description of this activity log alert.
-   "name": |-
        --condition -c
    "short-summary": |-
        The conditional expression that will cause the alert to activate. The format is FIELD=VALUE[ and FIELD=VALUE...].
    "long-summary": |
        The possible values for the field are 'resourceId', 'category', 'caller', 'level', 'operationName', 'resourceGroup', 'resourceProvider', 'status', 'subStatus', 'resourceType', or anything beginning with 'properties.'.
"""

helps["monitor activity-log alert"] = """
"type": |-
    group
"short-summary": |-
    Manage activity log alerts
"""

helps["monitor diagnostic-settings categories"] = """
"type": |-
    group
"short-summary": |-
    Retrieve service diagnostic settings categories.
"""

helps["monitor autoscale profile list"] = """
"type": |-
    command
"short-summary": |-
    List autoscale profiles.
"""

helps["monitor log-profiles"] = """
"type": |-
    group
"short-summary": |-
    Manage log profiles.
"""

helps["monitor log-profiles create"] = """
"type": |-
    command
"short-summary": |-
    Create a log profile.
"parameters":
-   "name": |-
        --name -n
    "short-summary": |-
        The name of the log profile.
-   "name": |-
        --locations
    "short-summary": |-
        Space-separated list of regions for which Activity Log events should be stored.
-   "name": |-
        --categories
    "short-summary": |-
        Space-separated categories of the logs. These categories are created as is convenient to the user. Some values are Write, Delete, and/or Action.
-   "name": |-
        --storage-account-id
    "short-summary": |-
        The resource id of the storage account to which you would like to send the Activity Log.
-   "name": |-
        --service-bus-rule-id
    "short-summary": |-
        The service bus rule ID of the service bus namespace in which you would like to have Event Hubs created for streaming the Activity Log. The rule ID is of the format '{service bus resource ID}/authorizationrules/{key name}'.
-   "name": |-
        --days
    "short-summary": |-
        The number of days for the retention in days. A value of 0 will retain the events indefinitely
-   "name": |-
        --enabled
    "short-summary": |-
        Whether the retention policy is enabled.
"""

helps["monitor autoscale rule list"] = """
"type": |-
    command
"short-summary": |-
    List autoscale rules for a profile.
"""

helps["monitor metrics alert list"] = """
"type": |-
    command
"short-summary": |-
    List metric-based alert rules.
"""

helps["monitor activity-log list"] = """
"type": |-
    command
"short-summary": |-
    List and query activity log events.
"parameters":
-   "name": |-
        --correlation-id
    "short-summary": |-
        Correlation ID to query.
-   "name": |-
        --resource-id
    "short-summary": |-
        ARM ID of a resource.
-   "name": |-
        --namespace
    "short-summary": |-
        Resource provider namespace.
-   "name": |-
        --caller
    "short-summary": |-
        Caller to query for, such as an e-mail address or service principal ID.
-   "name": |-
        --status
    "short-summary": |
        Status to query for (ex: Failed)
-   "name": |-
        --max-events
    "short-summary": |-
        Maximum number of records to return.
-   "name": |-
        --select
    "short-summary": |-
        Space-separated list of properties to return.
-   "name": |-
        --offset
    "short-summary": |
        Time offset of the query range, in ##d##h format.
    "long-summary": |
        Can be used with either --start-time or --end-time. If used with --start-time, then the end time will be calculated by adding the offset. If used with --end-time (default), then the start time will be calculated by subtracting the offset. If --start-time and --end-time are provided, then --offset will be ignored.
"""

helps["monitor autoscale-settings"] = """
"type": |-
    group
"short-summary": |-
    Manage autoscale settings.
"""

helps["monitor autoscale profile list-timezones"] = """
"type": |-
    command
"short-summary": |-
    Look up time zone information.
"""

helps["monitor log-profiles update"] = """
"type": |-
    command
"short-summary": |-
    Update a log profile.
"""

helps["monitor autoscale update"] = """
"type": |-
    command
"short-summary": |-
    Update autoscale settings.
"long-summary": |
    For more information on autoscaling, visit: https://docs.microsoft.com/en-us/azure/monitoring-and-diagnostics/monitoring-understanding-autoscale-settings
"parameters":
-   "name": |-
        --add-action -a
    "short-summary": |-
        Add an action to fire when a scaling event occurs.
    "long-summary": |
        Usage:   --add-action TYPE KEY [ARG ...]
        Email:   --add-action email bob@contoso.com ann@contoso.com
        Webhook: --add-action webhook https://www.contoso.com/alert apiKey=value
        Webhook: --add-action webhook https://www.contoso.com/alert?apiKey=value
        Multiple actions can be specified by using more than one `--add-action` argument.
-   "name": |-
        --remove-action -r
    "short-summary": |-
        Remove one or more actions.
    "long-summary": |
        Usage:   --remove-action TYPE KEY [KEY ...]
        Email:   --remove-action email bob@contoso.com ann@contoso.com
        Webhook: --remove-action webhook https://contoso.com/alert https://alerts.contoso.com
"""

helps["monitor metrics list"] = """
"type": |-
    command
"short-summary": |-
    List the metric values for a resource.
"parameters":
-   "name": |-
        --aggregation
    "short-summary": |-
        The list of aggregation types (space-separated) to retrieve.
-   "name": |-
        --interval
    "short-summary": |
        The interval over which to aggregate metrics, in ##h##m format.
-   "name": |-
        --filter
    "short-summary": |-
        A string used to reduce the set of metric data returned. eg. "BlobType eq '*'"
    "long-summary": |-
        For a full list of filters, see the filter string reference at https://docs.microsoft.com/en-us/rest/api/monitor/metrics/list
-   "name": |-
        --metadata
    "short-summary": |-
        Returns the metadata values instead of metric data
-   "name": |-
        --dimension
    "short-summary": |-
        The list of dimensions (space-separated) the metrics are queried into.
-   "name": |-
        --namespace
    "short-summary": |-
        Namespace to query metric definitions for.
-   "name": |-
        --offset
    "short-summary": |
        Time offset of the query range, in ##d##h format.
    "long-summary": |
        Can be used with either --start-time or --end-time. If used with --start-time, then the end time will be calculated by adding the offset. If used with --end-time (default), then the start time will be calculated by subtracting the offset. If --start-time and --end-time are provided, then --offset will be ignored.
"examples":
-   "name": |-
        Lists the metric definitions for the resource.
    "text": |-
        az monitor metrics list-definitions --resource <resource>
-   "name": |-
        List the metric values for a resource.
    "text": |-
        az monitor metrics list --resource-namespace <resource-namespace> --interval <interval> --resource {ResourceName} --start-time <start-time> --resource-group MyResourceGroup --output json --resource-type <resource-type> --metrics "Percentage CPU" --end-time <end-time> --aggregation Average
"""

helps["monitor autoscale profile"] = """
"type": |-
    group
"short-summary": |-
    Manage autoscaling profiles.
"long-summary": |
    For more information on autoscaling, visit: https://docs.microsoft.com/en-us/azure/monitoring-and-diagnostics/monitoring-understanding-autoscale-settings
"""

helps["monitor autoscale rule delete"] = """
"type": |-
    command
"short-summary": |-
    Remove autoscale rules from a profile.
"""

helps["monitor action-group update"] = """
"type": |-
    command
"short-summary": |-
    Update an action group
"parameters":
-   "name": |-
        --short-name
    "short-summary": |-
        Update the group short name of the action group
-   "name": |-
        --add-action -a
    "short-summary": |-
        Add receivers to the action group
    "long-summary": |
        Usage:   --add-action TYPE NAME [ARG ...]
        Email:   --add-action email bob bob@contoso.com
        SMS:     --add-action sms charli 1 5551234567
        Webhook: --add-action https://www.contoso.com/alert
        Multiple actions can be specified by using more than one `--add-action` argument.
-   "name": |-
        --remove-action -r
    "short-summary": |-
        Remove receivers from the action group. Accept space-separated list of receiver names.
"""

helps["monitor metrics list-definitions"] = """
"type": |-
    command
"short-summary": |-
    Lists the metric definitions for the resource.
"""

helps["monitor autoscale"] = """
"type": |-
    group
"short-summary": |-
    Manage autoscale settings.
"long-summary": |
    For more information on autoscaling, visit: https://docs.microsoft.com/en-us/azure/monitoring-and-diagnostics/monitoring-understanding-autoscale-settings
"""

helps["monitor alert update"] = """
"type": |-
    command
"short-summary": |-
    Update a classic metric-based alert rule.
"parameters":
-   "name": |-
        --description
    "short-summary": |-
        Description of the rule.
-   "name": |-
        --condition
    "short-summary": |-
        The condition which triggers the rule.
    "long-summary": |
        The form of a condition is "METRIC {>,>=,<,<=} THRESHOLD {avg,min,max,total,last} PERIOD". Values for METRIC and appropriate THRESHOLD values can be obtained from `az monitor metric` commands, and PERIOD is of the form "##h##m##s".
-   "name": |-
        --add-action -a
    "short-summary": |-
        Add an action to fire when the alert is triggered.
    "long-summary": |
        Usage:   --add-action TYPE KEY [ARG ...]
        Email:   --add-action email bob@contoso.com ann@contoso.com
        Webhook: --add-action webhook https://www.contoso.com/alert apiKey=value
        Webhook: --add-action webhook https://www.contoso.com/alert?apiKey=value
        Multiple actions can be specified by using more than one `--add-action` argument.
-   "name": |-
        --remove-action -r
    "short-summary": |-
        Remove one or more actions.
    "long-summary": |
        Usage:   --remove-action TYPE KEY [KEY ...]
        Email:   --remove-action email bob@contoso.com ann@contoso.com
        Webhook: --remove-action webhook https://contoso.com/alert https://alerts.contoso.com
-   "name": |-
        --email-service-owners
    "short-summary": |-
        Email the service owners if an alert is triggered.
-   "name": |-
        --metric
    "short-summary": |-
        Name of the metric to base the rule on.
    "populator-commands":
    - |-
        az monitor metrics list-definitions
-   "name": |-
        --operator
    "short-summary": |-
        How to compare the metric against the threshold.
-   "name": |-
        --threshold
    "short-summary": |-
        Numeric threshold at which to trigger the alert.
-   "name": |-
        --aggregation
    "short-summary": |-
        Type of aggregation to apply based on --period.
-   "name": |-
        --period
    "short-summary": |
        Time span over which to apply --aggregation, in nDnHnMnS shorthand or full ISO8601 format.
"""

helps["monitor diagnostic-settings"] = """
"type": |-
    group
"short-summary": |-
    Manage service diagnostic settings.
"""

helps["monitor alert delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an alert rule.
"""

helps["monitor autoscale profile delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an autoscale profile.
"""

helps["monitor metrics alert"] = """
"type": |-
    group
"short-summary": |-
    Manage near-realtime metric alert rules.
"""

helps["monitor action-group"] = """
"type": |-
    group
"short-summary": |-
    Manage action groups
"""

helps["monitor activity-log alert list"] = """
"type": |-
    command
"short-summary": |-
    List activity log alerts under a resource group or the current subscription.
"parameters":
-   "name": |-
        --resource-group -g
    "short-summary": |-
        Name of the resource group under which the activity log alerts are being listed. If it is omitted, all the activity log alerts under the current subscription are listed.
"""

helps["monitor autoscale profile show"] = """
"type": |-
    command
"short-summary": |-
    Show details of an autoscale profile.
"""

helps["monitor activity-log alert action-group"] = """
"type": |-
    group
"short-summary": |-
    Manage action groups for activity log alerts
"""

helps["monitor diagnostic-settings update"] = """
"type": |-
    command
"short-summary": |-
    Update diagnostic settings.
"""

helps["monitor action-group create"] = """
"type": |-
    command
"short-summary": |-
    Create a new action group
"parameters":
-   "name": |-
        --action -a
    "short-summary": |-
        Add receivers to the action group during the creation
    "long-summary": |
        Usage:   --action TYPE NAME [ARG ...]
        Email:   --action email bob bob@contoso.com
        SMS:     --action sms charli 1 5551234567
        Webhook: --action webhook alert_hook https://www.contoso.com/alert
        Multiple actions can be specified by using more than one `--action` argument.
-   "name": |-
        --short-name
    "short-summary": |-
        The short name of the action group
"""

helps["monitor metrics alert delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a metrics-based alert rule.
"""

helps["monitor autoscale rule copy"] = """
"type": |-
    command
"short-summary": |-
    Copy autoscale rules from one profile to another.
"""

helps["monitor metrics alert update"] = """
"type": |-
    command
"short-summary": |-
    Update a metric-based alert rule.
"parameters":
-   "name": |-
        --add-condition
    "short-summary": |-
        Add a condition which triggers the rule.
    "long-summary": |
        Usage:  --add-conditon {avg,min,max,total} [NAMESPACE.]METRIC {=,!=,>,>=,<,<=} THRESHOLD
                               [where DIMENSION {includes,excludes} VALUE [or VALUE ...]
                               [and   DIMENSION {includes,excludes} VALUE [or VALUE ...] ...]]

        Dimensions can be queried by adding the 'where' keyword and multiple dimensions can be queried by combining them with the 'and' keyword.

        Values for METRIC, DIMENSION and appropriate THRESHOLD values can be obtained from `az monitor metrics list-definition` command.

        Multiple conditons can be specified by using more than one `--condition` argument.
-   "name": |-
        --remove-conditions
    "short-summary": |-
        Space-separated list of condition names to remove.
-   "name": |-
        --add-action
    "short-summary": |-
        Add an action group and optional webhook properties to fire when the alert is triggered.
    "long-summary": |
        Usage:   --add-action ACTION_GROUP_NAME_OR_ID [KEY=VAL [KEY=VAL ...]]

        Multiple action groups can be specified by using more than one `--action` argument.
-   "name": |-
        --remove-actions
    "short-summary": |-
        Space-separated list of action group names to remove.
"""

helps["monitor activity-log alert scope"] = """
"type": |-
    group
"short-summary": |-
    Manage scopes for activity log alerts
"""

helps["monitor diagnostic-settings create"] = """
"type": |-
    command
"short-summary": |-
    Create diagnostic settings for the specified resource.
"long-summary": |
    For more information, visit: https://docs.microsoft.com/en-us/rest/api/monitor/diagnosticsettings/createorupdate#metricsettings
"parameters":
-   "name": |-
        --name -n
    "short-summary": |-
        The name of the diagnostic settings.
-   "name": |-
        --resource-group -g
    "type": |-
        string
    "short-summary": |-
        Name of the resource group for the Log Analytics and Storage Account when the name of the service instead of a full resource ID is given.
-   "name": |-
        --logs
    "type": |-
        string
    "short-summary": |-
        JSON encoded list of logs settings. Use '@{file}' to load from a file.
-   "name": |-
        --metrics
    "type": |-
        string
    "short-summary": |-
        JSON encoded list of metric settings. Use '@{file}' to load from a file.
-   "name": |-
        --storage-account
    "type": |-
        string
    "short-summary": |-
        Name or ID of the storage account to send diagnostic logs to.
-   "name": |-
        --workspace
    "type": |-
        string
    "short-summary": |-
        Name or ID of the Log Analytics workspace to send diagnostic logs to.
-   "name": |-
        --event-hub
    "type": |-
        string
    "short-summary": |
        Name or ID an event hub. If none is specified, the default event hub will be selected.
-   "name": |-
        --event-hub-rule
    "short-summary": |-
        Name or ID of the event hub authorization rule.
"""

helps["monitor activity-log alert scope add"] = """
"type": |-
    command
"short-summary": |-
    Add scopes to this activity log alert.
"parameters":
-   "name": |-
        --name -n
    "short-summary": |-
        Name of the activity log alerts
-   "name": |-
        --scope -s
    "short-summary": |-
        The scopes to add
-   "name": |-
        --reset
    "short-summary": |-
        Remove all the existing scopes before add new scopes.
"""

helps["monitor alert show"] = """
"type": |-
    command
"short-summary": |-
    Show an alert rule.
"""

helps["monitor alert create"] = """
"type": |-
    command
"short-summary": |-
    Create a classic metric-based alert rule.
"parameters":
-   "name": |-
        --action -a
    "short-summary": |-
        Add an action to fire when the alert is triggered.
    "long-summary": |
        Usage:   --action TYPE KEY [ARG ...]
        Email:   --action email bob@contoso.com ann@contoso.com
        Webhook: --action webhook https://www.contoso.com/alert apiKey=value
        Webhook: --action webhook https://www.contoso.com/alert?apiKey=value
        Multiple actions can be specified by using more than one `--action` argument.
-   "name": |-
        --description
    "short-summary": |-
        Free-text description of the rule. Defaults to the condition expression.
-   "name": |-
        --disabled
    "short-summary": |-
        Create the rule in a disabled state.
-   "name": |-
        --condition
    "short-summary": |-
        The condition which triggers the rule.
    "long-summary": |
        The form of a condition is "METRIC {>,>=,<,<=} THRESHOLD {avg,min,max,total,last} PERIOD". Values for METRIC and appropriate THRESHOLD values can be obtained from `az monitor metric` commands, and PERIOD is of the form "##h##m##s".
-   "name": |-
        --email-service-owners
    "short-summary": |-
        Email the service owners if an alert is triggered.
"examples":
-   "name": |-
        Create a classic metric-based alert rule.
    "text": |-
        az monitor alert create --action <action> --condition "Percentage CPU > 90 avg 5m" --resource-group {ResourceGroup} --target {VirtualMachineID} --email-service-owners false --name rule1 --target-type <target-type>
"""

helps["monitor alert list-incidents"] = """
"type": |-
    command
"short-summary": |-
    List all incidents for an alert rule.
"""

helps["monitor autoscale create"] = """
"type": |-
    command
"short-summary": |-
    Create new autoscale settings.
"long-summary": |
    For more information on autoscaling, visit: https://docs.microsoft.com/en-us/azure/monitoring-and-diagnostics/monitoring-understanding-autoscale-settings
"parameters":
-   "name": |-
        --action -a
    "short-summary": |-
        Add an action to fire when a scaling event occurs.
    "long-summary": |
        Usage:   --action TYPE KEY [ARG ...]
        Email:   --action email bob@contoso.com ann@contoso.com
        Webhook: --action webhook https://www.contoso.com/alert apiKey=value
        Webhook: --action webhook https://www.contoso.com/alert?apiKey=value
        Multiple actions can be specified by using more than one `--action` argument.
"""

helps["monitor alert show-incident"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an alert rule incident.
"""

helps["monitor activity-log alert create"] = """
"type": |-
    command
"short-summary": |-
    Create a default activity log alert
"long-summary": |-
    This command will create a default activity log with one condition which compares if the activities logs 'category' field equals to 'ServiceHealth'. The newly created activity log alert does not have any action groups attached to it.
"parameters":
-   "name": |-
        --name -n
    "short-summary": |-
        Name of the activity log alerts
-   "name": |-
        --scope -s
    "short-summary": |-
        A list of strings that will be used as prefixes.
    "long-summary": |
        The alert will only apply to activity logs with resourceIDs that fall under one of these prefixes. If not provided, the path to the resource group will be used.
-   "name": |-
        --disable
    "short-summary": |-
        Disable the activity log alert after it is created.
-   "name": |-
        --description
    "short-summary": |-
        A description of this activity log alert
-   "name": |-
        --condition -c
    "short-summary": |-
        The condition that will cause the alert to activate. The format is FIELD=VALUE[ and FIELD=VALUE...].
    "long-summary": |
        The possible values for the field are 'resourceId', 'category', 'caller', 'level', 'operationName', 'resourceGroup', 'resourceProvider', 'status', 'subStatus', 'resourceType', or anything beginning with 'properties.'.
-   "name": |-
        --action-group -a
    "short-summary": |
        Add an action group. Accepts space-separated action group identifiers. The identifier can be the action group's name or its resource ID.
-   "name": |-
        --webhook-properties -w
    "short-summary": |
        Space-separated webhook properties in 'key[=value]' format. These properties are associated with the action groups added in this command.
    "long-summary": |
        For any webhook receiver in these action group, this data is appended to the webhook payload. To attach different webhook properties to different action groups, add the action groups in separate update-action commands.
"""

helps["monitor activity-log"] = """
"type": |-
    group
"short-summary": |-
    Manage activity logs.
"""

helps["monitor metrics alert create"] = """
"type": |-
    command
"short-summary": |-
    Create a metric-based alert rule.
"parameters":
-   "name": |-
        --action -a
    "short-summary": |-
        Add an action group and optional webhook properties to fire when the alert is triggered.
    "long-summary": |
        Usage:   --action ACTION_GROUP_NAME_OR_ID [KEY=VAL [KEY=VAL ...]]

        Multiple action groups can be specified by using more than one `--action` argument.
-   "name": |-
        --disabled
    "short-summary": |-
        Create the rule in a disabled state.
-   "name": |-
        --condition
    "short-summary": |-
        The condition which triggers the rule.
    "long-summary": |
        Usage:  --conditon {avg,min,max,total} [NAMESPACE.]METRIC {=,!=,>,>=,<,<=} THRESHOLD
                           [where DIMENSION {includes,excludes} VALUE [or VALUE ...]
                           [and   DIMENSION {includes,excludes} VALUE [or VALUE ...] ...]]

        Dimensions can be queried by adding the 'where' keyword and multiple dimensions can be queried by combining them with the 'and' keyword.

        Values for METRIC, DIMENSION and appropriate THRESHOLD values can be obtained from `az monitor metrics list-definition` command.

        Multiple conditons can be specified by using more than one `--condition` argument.
"examples":
-   "name": |-
        Create a metric-based alert rule.
    "text": |-
        az monitor metrics alert create --action <action> --condition "avg Percentage CPU > 90" --description "High CPU" --resource-group {ResourceGroup} --name alert1 --scopes {VirtualMachineID} --window-size ##h##m##s --evaluation-frequency ##h##m##s
"""

helps["monitor action-group list"] = """
"type": |-
    command
"short-summary": |-
    List action groups under a resource group or the current subscription
"parameters":
-   "name": |-
        --resource-group -g
    "type": |-
        string
    "short-summary": |
        Name of the resource group under which the action groups are being listed. If it is omitted, all the action groups under the current subscription are listed.
"""

helps["monitor activity-log list-categories"] = """
"type": |-
    command
"short-summary": |-
    List the event categories of activity logs.
"""

helps["monitor"] = """
"type": |-
    group
"short-summary": |-
    Manage the Azure Monitor Service.
"""

helps["monitor activity-log alert action-group add"] = """
"type": |-
    command
"short-summary": |-
    Add action groups to this activity log alert. It can also be used to overwrite existing webhook properties of particular action groups.
"parameters":
-   "name": |-
        --name -n
    "short-summary": |-
        Name of the activity log alerts
-   "name": |-
        --action-group -a
    "short-summary": |-
        The names or the resource ids of the action groups to be added.
-   "name": |-
        --reset
    "short-summary": |-
        Remove all the existing action groups before add new conditions.
-   "name": |-
        --webhook-properties -w
    "short-summary": |
        Space-separated webhook properties in 'key[=value]' format. These properties will be associated with the action groups added in this command.
    "long-summary": |
        For any webhook receiver in these action group, these data are appended to the webhook payload. To attach different webhook properties to different action groups, add the action groups in separate update-action commands.
-   "name": |-
        --strict
    "short-summary": |-
        Fails the command if an action group to be added will change existing webhook properties.
"""

helps["monitor alert list"] = """
"type": |-
    command
"short-summary": |-
    List alert rules in a resource group.
"examples":
-   "name": |-
        List alert rules in a resource group.
    "text": |-
        az monitor alert list --resource-group MyResourceGroup
"""

helps["monitor activity-log alert scope remove"] = """
"type": |-
    command
"short-summary": |-
    Removes scopes from this activity log alert.
"parameters":
-   "name": |-
        --name -n
    "short-summary": |-
        Name of the activity log alerts
-   "name": |-
        --scope -s
    "short-summary": |-
        The scopes to remove
"""

helps["monitor autoscale rule"] = """
"type": |-
    group
"short-summary": |-
    Manage autoscale scaling rules.
"long-summary": |
    For more information on autoscaling, visit: https://docs.microsoft.com/en-us/azure/monitoring-and-diagnostics/monitoring-understanding-autoscale-settings
"""

helps["monitor metrics"] = """
"type": |-
    group
"short-summary": |-
    View Azure resource metrics.
"""

helps["monitor action-group show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of an action group
"""

helps["monitor autoscale rule create"] = """
"type": |-
    command
"short-summary": |-
    Add a new autoscale rule.
"long-summary": |
    For more information on autoscaling, visit: https://docs.microsoft.com/en-us/azure/monitoring-and-diagnostics/monitoring-understanding-autoscale-settings
"parameters":
-   "name": |-
        --condition
    "short-summary": |-
        The condition which triggers the scaling action.
    "long-summary": |
        The form of a condition is "METRIC {==,!=,>,>=,<,<=} THRESHOLD {avg,min,max,total,count} PERIOD". Values for METRIC and appropriate THRESHOLD values can be obtained from the `az monitor metric` command. Format of PERIOD is "##h##m##s".
-   "name": |-
        --scale
    "short-summary": |-
        The direction and amount to scale.
    "long-summary": |
        Usage:          --scale {to,in,out} VAL[%]
        Fixed Count:    --scale to 5
        In by Count:    --scale in 2
        Out by Percent: --scale out 10%
-   "name": |-
        --timegrain
    "short-summary": |
        The way metrics are polled across instances.
    "long-summary": |
        The form of the timegrain is {avg,min,max,sum} VALUE. Values can be obtained from the `az monitor metric` command. Format of VALUE is "##h##m##s".
"""

helps["monitor autoscale profile create"] = """
"type": |-
    command
"short-summary": |-
    Create a fixed or recurring autoscale profile.
"long-summary": |
    For more information on autoscaling, visit: https://docs.microsoft.com/en-us/azure/monitoring-and-diagnostics/monitoring-understanding-autoscale-settings
"parameters":
-   "name": |-
        --timezone
    "short-summary": |-
        Timezone name.
    "populator-commands":
    - |-
        az monitor autoscale profile list-timezones
-   "name": |-
        --recurrence -r
    "short-summary": |-
        When the profile recurs. If omitted, a fixed (non-recurring) profile is created.
    "long-summary": |
        Usage:     --recurrence {week} [ARG ARG ...]
        Weekly:    --recurrence week Sat Sun
-   "name": |-
        --start
    "short-summary": |-
        When the autoscale profile begins. Format depends on the type of profile.
    "long-summary": |
        Fixed:  --start yyyy-mm-dd [hh:mm:ss]
        Weekly: [--start hh:mm]
-   "name": |-
        --end
    "short-summary": |-
        When the autoscale profile ends. Format depends on the type of profile.
    "long-summary": |
        Fixed:  --end yyyy-mm-dd [hh:mm:ss]
        Weekly: [--end hh:mm]
"""

helps["monitor metrics alert show"] = """
"type": |-
    command
"short-summary": |-
    Show a metrics-based alert rule.
"""

helps["monitor activity-log alert action-group remove"] = """
"type": |-
    command
"short-summary": |-
    Remove action groups from this activity log alert
"parameters":
-   "name": |-
        --name -n
    "short-summary": |-
        Name of the activity log alerts
-   "name": |-
        --action-group -a
    "short-summary": |-
        The names or the resource ids of the action groups to be added.
"""

helps["monitor alert"] = """
"type": |-
    group
"short-summary": |-
    Manage classic metric-based alert rules.
"""

helps["monitor autoscale-settings update"] = """
"type": |-
    command
"short-summary": |-
    Updates an autoscale setting.
"""

