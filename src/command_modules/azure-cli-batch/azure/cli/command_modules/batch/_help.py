# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

#pylint: disable=line-too-long

helps['batch'] = """
    type: group
    short-summary: Commands for working with Azure Batch.
"""

helps['batch account'] = """
    type: group
    short-summary: Commands to manage your Batch accounts.
"""

helps['batch account list'] = """
    type: command
    short-summary: Lists the Batch accounts associated with a subscription or resource group.
"""

helps['batch account create'] = """
    type: command
    short-summary: Creates a new Batch account with the specified parameters.
"""

helps['batch account autostorage-keys'] = """
    type: group
    short-summary: Commands to manage the access keys for the auto storage account configured for your Batch account.
"""

helps['batch account keys'] = """
    type: group
    short-summary: Commands to manage your Batch account keys.
"""

helps['batch application'] = """
    type: group
    short-summary: Commands to manage your Batch applications.
"""

helps['batch application package'] = """
    type: group
    short-summary: Commands to manage your Batch application packages.
"""

helps['batch location'] = """
    type: group
    short-summary: Commands to manage Batch service options for a subscription at the region level.
"""

helps['batch location quotas'] = """
    type: group
    short-summary: Commands to manage Batch service quotas at the region level.
"""

helps['batch certificate'] = """
    type: group
    short-summary: Commands to manage your Batch certificate.
"""

helps['batch task file'] = """
    type: group
    short-summary: Commands to manage your Batch task files.
"""

helps['batch node file'] = """
    type: group
    short-summary: Commands to manage your Batch compute node files.
"""

helps['batch job'] = """
    type: group
    short-summary: Commands to manage your Batch jobs.
"""

helps['batch job all-stats'] = """
    type: group
    short-summary: Commands to manage all the jobs under your Batch account.
"""

helps['batch job prep-release-status'] = """
    type: group
    short-summary: Commands to manage the status of your job preparation and release tasks.
"""

helps['batch job-schedule'] = """
    type: group
    short-summary: Commands to manage your Batch job schedules.
"""

helps['batch node-user'] = """
    type: group
    short-summary: Commands to manage your Batch compute node users.
"""

helps['batch node-user create'] = """
    type: command
    short-summary: Adds a user account to the specified compute node.
"""

helps['batch node'] = """
    type: group
    short-summary: Commands to manage your Batch compute nodes.
"""

helps['batch node remote-login-settings'] = """
    type: group
    short-summary: The remote login settings for a Batch compute node.
"""

helps['batch node remote-desktop'] = """
    type: group
    short-summary: The remote desktop protocol for a Batch compute node.
"""

helps['batch node scheduling'] = """
    type: group
    short-summary: Commands to manage the scheduling property for a Batch compute node.
"""

helps['batch pool'] = """
    type: group
    short-summary: Commands to manage your Batch pools.
"""

helps['batch pool os'] = """
    type: group
    short-summary: Commands to manage operationg system of your Batch pools.
"""

helps['batch pool autoscale'] = """
    type: group
    short-summary: Commands to manage autoscale of your Batch pools.
"""

helps['batch pool all-stats'] = """
    type: group
    short-summary: Commands to manage all the pools under your Batch account.
"""

helps['batch pool usage-metrics'] = """
    type: group
    short-summary: Commands to manage usage metrics of your Batch pools'.
"""

helps['batch pool node-agent-skus'] = """
    type: group
    short-summary: Commands to manage node agent skus of IaaS pools'.
"""

helps['batch task'] = """
    type: group
    short-summary: Commands to manage your Batch tasks.
"""

helps['batch task subtasks'] = """
    type: group
    short-summary: Commands to manage subtask information of your Batch task.
"""

helps['batch certificate create'] = """
    type: command
    short-summary: Add a certificate.
"""

helps['batch certificate delete'] = """
    type: command
    short-summary: Delete the specified Batch certificate.
"""

helps['batch pool create'] = """
    type: command
    short-summary: Create a Batch pool.
"""

helps['batch pool set'] = """
    type: command
    short-summary: Patch the properties of the specified Batch pool.
"""

helps['batch pool reset'] = """
    type: command
    short-summary: Update the properties of the specified Batch pool.
"""

helps['batch pool resize'] = """
    type: command
    short-summary: Resize (or stop resizing) the Batch pool.
"""

helps['batch job create'] = """
    type: command
    short-summary: Adds a job to the specified account.
"""

helps['batch job list'] = """
    type: command
    short-summary: Lists all of the jobs in the specified account or the specified job schedule.
"""

helps['batch job set'] = """
    type: command
    short-summary: Patch the properties of a job.
"""

helps['batch job reset'] = """
    type: command
    short-summary: Update the properties of a job.
"""

helps['batch job-schedule create'] = """
    type: command
    short-summary: Adds a job schedule to the specified account.
"""

helps['batch job-schedule set'] = """
    type: command
    short-summary: Patch the properties of the specified job schedule.
"""

helps['batch job-schedule reset'] = """
    type: command
    short-summary: Update the properties of the specified job schedule.
"""

helps['batch task create'] = """
    type: command
    short-summary: Create a single Batch task or multiple Batch tasks.
"""
