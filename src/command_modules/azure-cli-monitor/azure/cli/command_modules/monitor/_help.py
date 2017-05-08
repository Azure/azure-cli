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
# MANAGEMENT COMMANDS HELPS

# region Alerts

helps['monitor alert'] = """
    type: group
    short-summary: Commands to manage alerts on Azure resources.
    """

helps['monitor alert rule'] = """
    type: group
    short-summary: Commands to manage alert rules.
    """

helps['monitor alert rule create'] = """
    type: command
    short-summary: Create an alert rule.
    """

helps['monitor alert rule update'] = """
    type: command
    short-summary: Update an alert rule.
    """

helps['monitor alert rule delete'] = """
    type: command
    short-summary: Delete an alert rule.
    """

helps['monitor alert rule list'] = """
    type: command
    short-summary: List alert rules in a resource group.
    """

helps['monitor alert rule show'] = """
    type: command
    short-summary: Show an alert rule.
    """

helps['monitor alert incident'] = """
    type: group
    short-summary: Get information on alert incidents.
    """

helps['monitor alert incident show'] = """
    type: command
    short-summary: Show details of an alert rule incident.
    """

helps['monitor alert incident list'] = """
    type: command
    short-summary: List all incidents for an alert rule.
    """

helps['monitor alert action'] = """
    type: group
    short-summary: Manage actions associated with alert rules.
    """

helps['monitor alert action add-email'] = """
    type: command
    short-summary: Send an email when an alert fires.
    """

helps['monitor alert action add-webhook'] = """
    type: command
    short-summary: Trigger a webhook when an alert fires.
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
# DATA COMMANDS HELPS
helps['monitor activity-log'] = """
            type: group
            short-summary: Commands to manage activity log.
            """
helps['monitor metrics'] = """
            type: group
            short-summary: Commands to manage metrics.
            """
helps['monitor metric-definitions'] = """
            type: group
            short-summary: Commands to manage metric definitions.
            """
