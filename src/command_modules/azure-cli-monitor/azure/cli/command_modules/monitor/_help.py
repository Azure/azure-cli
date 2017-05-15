# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

# pylint: disable=line-too-long, too-many-lines

helps['monitor'] = """
            type: group
            short-summary: Commands to manage Azure Monitor service.
            """

# region Alerts

helps['monitor alert'] = """
    type: group
    short-summary: Commands to manage metric-based alert rules.
    """

helps['monitor alert create'] = """
    type: command
    short-summary: Create a metric-based alert rule.
    parameters:
        - name: --action -a
          short-summary: Add an action to fire when the alert is triggered.
          long-summary: |
            To specify multiple actions, add multiple --action ARGS entries.
            Usage:   --action TYPE KEY [ARG ...]
            Example: --action email bob@contoso.com
            Example: --action webhook https://www.contoso.com/alert apiKey=value
            Example: --action webhook https://www.contoso.com/alert?apiKey=value
        - name: --description
          short-summary: Free-text description of the rule.
        - name: --condition
          short-summary: The condition expression upon which to trigger the rule.
          long-summary: --condition METRIC {>,>=,<,<=} THRESHOLD {avg,min,max,total,last} PERIOD
        - name: --custom-emails
          short-summary: Space-separated list of addresses to email when the alert is triggered.
        - name: --email-service-owners
          short-summary: Email the service owners if an alert is triggered.
        - name: --webhook
          short-summary: >
            Send a POST request to a web service when the alert is triggered. Usage: --webhook URI [KEY=VALUE ...]
          long-summary: To add multiple webhook actions, use multiple --webhook entries.
    examples:
        - name: Create a High CPU-based alert on a VM.
          text: >
            az vm alert rule create -n rule1 -g <RG> --target <VM ID> --condition "Percentage CPU > 90 avg 5m"
"""

helps['monitor alert update'] = """
    type: command
    short-summary: Update a metric-based alert rule.
    long-summary: |
        To specify the condition:
            --condition METRIC {>,>=,<,<=} THRESHOLD {avg,min,max,total,last} PERIOD
    parameters:
        - name: --target
          short-summary: ID of the resource to target for the alert rule.
        - name: --description
          short-summary: Free-text description of the rule.
        - name: --condition
          short-summary: The condition expression upon which to trigger the rule. If used, do not specify
            other 'Condition Arguments'.
        - name: --add-action -a
          short-summary: Add an action to fire when the alert is triggered.
          long-summary: |
            To specify multiple actions, add multiple --add-action ARGS entries.
            Usage:   --add-action TYPE KEY [ARG ...]
            Example: --add-action email bob@contoso.com
            Example: --add-action webhook https://www.contoso.com/alert apiKey=value
            Example: --add-action webhook https://www.contoso.com/alert?apiKey=value
        - name: --remove-action -r
          short-summary: Remove one or more actions by key (address for emails or URI for webhooks).
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
            Time span over which to apply --aggregation, in nDnHnMnS format or ISO8601 format.
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
    short-summary: Show details of an alert rule incident.
    """

helps['monitor alert list-incidents'] = """
    type: command
    short-summary: List all incidents for an alert rule.
    """

# endregion

# region Metrics

helps['monitor metrics'] = """
    type: group
    short-summary: Commands to view Azure resource metrics.
"""

helps['monitor metrics list'] = """
    type: command
    short-summary: List metric values for a resource.
"""

helps['monitor metrics list-definitions'] = """
    type: command
    short-summary: List metric definitions for a resource.
"""

# endregion

helps['monitor log-profiles'] = """
            type: group
            short-summary: Commands to manage the log profiles assigned to Azure subscription.
            """
helps['monitor log-profiles update'] = """
            type: command
            short-summary: Update a log profile assigned to Azure subscription.
            """
helps['monitor diagnostic-settings'] = """
            type: group
            short-summary: Commands to manage service diagnostic settings.
            """
helps['monitor diagnostic-settings create'] = """
            type: command
            short-summary: Creates diagnostic settings for the specified resource.
            parameters:
                - name: --resource-id
                  type: string
                  short-summary: The identifier of the resource
                - name: --resource-group -g
                  type: string
                  short-summary: Name of the resource group
                - name: --logs
                  type: string
                  short-summary: JSON encoded list of logs settings. Use @{file} to load from a file.
                - name: --metrics
                  type: string
                  short-summary: JSON encoded list of metric settings. Use @{file} to load from a file.
                - name: --storage-account
                  type: string
                  short-summary: Name or ID of the storage account to which you would like to send Diagnostic Logs
                - name: --namespace
                  type: string
                  short-summary: Name or ID of the Service Bus namespace
                - name: --rule-name
                  type: string
                  short-summary: Name of the Service Bus authorization rule
                - name: --workspace
                  type: string
                  short-summary: Name or ID of the Log Analytics workspace to which you would like to send Diagnostic Logs
                - name: --tags
                  short-summary: Space separated tags in 'key[=value]' format. Use '' to clear existing tags
            """
helps['monitor diagnostic-settings update'] = """
            type: command
            short-summary: Update diagnostic settings for the specified resource.
            """
helps['monitor autoscale-settings'] = """
            type: group
            short-summary: Commands to manage autoscale settings.
            """
helps['monitor autoscale-settings update'] = """
            type: command
            short-summary: Updates an autoscale setting.
            """

helps['monitor activity-log'] = """
    type: group
    short-summary: Commands to manage activity log.
"""
