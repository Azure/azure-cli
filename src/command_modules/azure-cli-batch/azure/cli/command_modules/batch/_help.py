# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


helps['batch'] = """
    type: group
    short-summary: Manage Azure Batch.
"""

helps['batch account'] = """
    type: group
    short-summary: Manage Azure Batch accounts.
"""

helps['batch account list'] = """
    type: command
    short-summary: List the Batch accounts associated with a subscription or resource group.
"""

helps['batch account create'] = """
    type: command
    short-summary: Create a Batch account with the specified parameters.
"""

helps['batch account set'] = """
    type: command
    short-summary: Update properties for a Batch account.
"""

helps['batch account autostorage-keys'] = """
    type: group
    short-summary: Manage the access keys for the auto storage account configured for a Batch account.
"""

helps['batch account keys'] = """
    type: group
    short-summary: Manage Batch account keys.
"""

helps['batch account login'] = """
    type: command
    short-summary: Log in to a Batch account through Azure Active Directory or Shared Key authentication.
"""

helps['batch application'] = """
    type: group
    short-summary: Manage Batch applications.
"""

helps['batch application set'] = """
    type: command
    short-summary: Update properties for a Batch application.
"""

helps['batch application package'] = """
    type: group
    short-summary: Manage Batch application packages.
"""

helps['batch application package create'] = """
    type: command
    short-summary: Create a Batch application package record and activate it.
"""

helps['batch application package activate'] = """
    type: command
    short-summary: Activates a Batch application package.
    long-summary: This step is unnecessary if the package has already been successfully activated by the `create` command.
"""

helps['batch application summary'] = """
    type: group
    short-summary: View a summary of Batch application packages.
"""

helps['batch application summary list'] = """
    type: command
    short-summary: Lists all of the applications available in the specified account.
    long-summary: This operation returns only applications and versions that are available for use on compute nodes; that is, that can be used in an application package reference. For administrator information about applications and versions that are not yet available to compute nodes, use the Azure portal or the 'az batch application list' command.
"""

helps['batch application summary show'] = """
    type: command
    short-summary: Gets information about the specified application.
    long-summary: This operation returns only applications and versions that are available for use on compute nodes; that is, that can be used in an application package reference. For administrator information about applications and versions that are not yet available to compute nodes, use the Azure portal or the 'az batch application list' command.
"""

helps['batch location'] = """
    type: group
    short-summary: Manage Batch service options for a subscription at the region level.
"""

helps['batch location quotas'] = """
    type: group
    short-summary: Manage Batch service quotas at the region level.
"""

helps['batch certificate'] = """
    type: group
    short-summary: Manage Batch certificates.
"""

helps['batch task file'] = """
    type: group
    short-summary: Manage Batch task files.
"""

helps['batch task file download'] = """
    type: command
    short-summary: Download the content of a Batch task file.
"""

helps['batch node file'] = """
    type: group
    short-summary: Manage Batch compute node files.
"""

helps['batch node file download'] = """
    type: command
    short-summary: Download the content of the a node file.
"""

helps['batch job'] = """
    type: group
    short-summary: Manage Batch jobs.
"""

helps['batch job task-counts'] = """
    type: group
    short-summary: View the number of tasks in a Batch job and their states.
"""

helps['batch job all-statistics'] = """
    type: group
    short-summary: View statistics of all jobs under a Batch account.
"""

helps['batch job all-statistics show'] = """
    type: command
    short-summary: Get lifetime summary statistics for all of the jobs in a Batch account.
    long-summary: Statistics are aggregated across all jobs that have ever existed in the account, from account creation to the last update time of the statistics.
"""

helps['batch job prep-release-status'] = """
    type: group
    short-summary: View the status of Batch job preparation and release tasks.
"""

helps['batch job-schedule'] = """
    type: group
    short-summary: Manage Batch job schedules.
"""

helps['batch node service-logs'] = """
    type: group
    short-summary: Manage the service log files of a Batch compute node.
"""

helps['batch node user'] = """
    type: group
    short-summary: Manage the user accounts of a Batch compute node.
"""

helps['batch node user create'] = """
    type: command
    short-summary: Add a user account to a Batch compute node.
"""

helps['batch node user reset'] = """
    type: command
    short-summary: Update the properties of a user account on a Batch compute node. Unspecified properties which can be updated are reset to their defaults.
"""

helps['batch node'] = """
    type: group
    short-summary: Manage Batch compute nodes.
"""

helps['batch node remote-login-settings'] = """
    type: group
    short-summary: Retrieve the remote login settings for a Batch compute node.
"""

helps['batch node remote-desktop'] = """
    type: group
    short-summary: Retrieve the remote desktop protocol file for a Batch compute node.
"""

helps['batch node scheduling'] = """
    type: group
    short-summary: Manage task scheduling for a Batch compute node.
"""

helps['batch pool'] = """
    type: group
    short-summary: Manage Batch pools.
"""

helps['batch pool os'] = """
    type: group
    short-summary: Manage the operating system of Batch pools.
"""

helps['batch pool autoscale'] = """
    type: group
    short-summary: Manage automatic scaling of Batch pools.
"""

helps['batch pool all-statistics'] = """
    type: group
    short-summary: View statistics of all pools under a Batch account.
"""

helps['batch pool all-statistics show'] = """
    type: command
    short-summary: Get lifetime summary statistics for all of the pools in a Batch account.
    long-summary: Statistics are aggregated across all pools that have ever existed in the account, from account creation to the last update time of the statistics.
"""

helps['batch pool usage-metrics'] = """
    type: group
    short-summary: View usage metrics of Batch pools.
"""

helps['batch pool node-counts'] = """
    type: group
    short-summary: Get node counts for Batch pools.
"""

helps['batch pool node-agent-skus'] = """
    type: group
    short-summary: Retrieve node agent SKUs of Batch pools using a Virtual Machine Configuration.
"""

helps['batch task'] = """
    type: group
    short-summary: Manage Batch tasks.
"""

helps['batch task subtask'] = """
    type: group
    short-summary: Manage subtask information of a Batch task.
"""

helps['batch certificate create'] = """
    type: command
    short-summary: Add a certificate to a Batch account.
"""

helps['batch certificate delete'] = """
    type: command
    short-summary: Delete a certificate from a Batch account.
"""

helps['batch pool create'] = """
    type: command
    short-summary: Create a Batch pool in an account. When creating a pool, choose arguments from either Cloud Services Configuration or Virtual Machine Configuration.
"""

helps['batch pool set'] = """
    type: command
    short-summary: Update the properties of a Batch pool. Updating a property in a subgroup will reset the unspecified properties of that group.
"""

helps['batch pool reset'] = """
    type: command
    short-summary: Update the properties of a Batch pool. Unspecified properties which can be updated are reset to their defaults.
"""

helps['batch pool resize'] = """
    type: command
    short-summary: Resize or stop resizing a Batch pool.
"""

helps['batch job create'] = """
    type: command
    short-summary: Add a job to a Batch account.
"""

helps['batch job list'] = """
    type: command
    short-summary: List all of the jobs or job schedule in a Batch account.
"""

helps['batch job set'] = """
    type: command
    short-summary: Update the properties of a Batch job. Updating a property in a subgroup will reset the unspecified properties of that group.
"""

helps['batch job reset'] = """
    type: command
    short-summary: Update the properties of a Batch job. Unspecified properties which can be updated are reset to their defaults.
"""

helps['batch job-schedule create'] = """
    type: command
    short-summary: Add a Batch job schedule to an account.
"""

helps['batch job-schedule set'] = """
    type: command
    short-summary: Update the properties of a job schedule.
    long-summary: You can independently update the schedule and the job specification, but any change to either of these entities will reset all properties in that entity.
"""

helps['batch job-schedule reset'] = """
    type: command
    short-summary: Reset the properties of a job schedule.  An updated job specification only applies to new jobs.
"""

helps['batch task create'] = """
    type: command
    short-summary: Create Batch tasks.
"""

helps['batch task reset'] = """
    type: command
    short-summary: Reset the properties of a Batch task.
"""
