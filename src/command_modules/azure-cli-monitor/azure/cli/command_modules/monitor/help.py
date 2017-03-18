# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps


helps['monitor'] = """
            type: group
            short-summary: Commands to manage Azure Monitor service.
            """
# MANAGEMENT COMMANDS HELPS
helps['monitor alert-rules'] = """
            type: group
            short-summary: Commands to manage alerts assigned to Azure resources.
            """
helps['monitor alert-rules update'] = """
            type: command
            short-summary: Updates an alert rule.
            """
helps['monitor alert-rule-incidents'] = """
            type: group
            short-summary: Commands to manage alert rule incidents.
            """
helps['monitor log-profiles'] = """
            type: group
            short-summary: Commands to manage the log profiles assigned to Azure subscription.
            """
helps['monitor log-profiles update'] = """
            type: command
            short-summary: Update a log profile assigned to Azure subscription.
            """
helps['monitor service-diagnostic-settings'] = """
            type: group
            short-summary: Commands to manage service diagnostic settings.
            """
helps['monitor service-diagnostic-settings update'] = """
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
helps['monitor event-categories'] = """
            type: group
            short-summary: Commands to manage event categories.
            """
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
