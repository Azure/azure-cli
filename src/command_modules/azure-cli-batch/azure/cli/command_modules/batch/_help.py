# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

# pylint: disable=line-too-long

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

helps['batch account set'] = """
    type: command
    short-summary: Updates the properties of the specified Batch account. Properties that are not specified remain unchanged.
"""

helps['batch account autostorage-keys'] = """
    type: group
    short-summary: Commands to manage the access keys for the auto storage account configured for your Batch account.
"""

helps['batch account keys'] = """
    type: group
    short-summary: Commands to manage your Batch account keys.
"""

helps['batch account login'] = """
    type: command
    short-summary: Log in with specified Batch account through Azure Active Directory or Shared Key authentication.
"""

helps['batch application'] = """
    type: group
    short-summary: Commands to manage your Batch applications.
"""

helps['batch application set'] = """
    type: command
    short-summary: Updates the properties of the specified application. Properties that are not specified remain unchanged.
"""

helps['batch application package'] = """
    type: group
    short-summary: Commands to manage your Batch application packages.
"""

helps['batch application package create'] = """
    type: command
    short-summary: Creates an application package record and attempts to activate it.
"""

helps['batch application package activate'] = """
    type: command
    short-summary: Activates the specified application package. This step is unnecessary if the package has already been successfully activated by the 'create' command.
"""

helps['batch application summary'] = """
    type: group
    short-summary: Commands to view a summary of your Batch application packages.
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
    short-summary: Commands to manage your Batch certificates.
"""

helps['batch task file'] = """
    type: group
    short-summary: Commands to manage your Batch task files.
"""

helps['batch task file download'] = """
    type: command
    short-summary: Downloads the content of the specified task file.
"""

helps['batch node file'] = """
    type: group
    short-summary: Commands to manage your Batch compute node files.
"""

helps['batch node file download'] = """
    type: command
    short-summary: Downloads the content of the specified node file.
"""

helps['batch job'] = """
    type: group
    short-summary: Commands to manage your Batch jobs.
"""

helps['batch job all-statistics'] = """
    type: group
    short-summary: Commands to view statistics of all the jobs under your Batch account
"""

helps['batch job all-statistics show'] = """
    type: command
    short-summary: Gets lifetime summary statistics for all of the jobs in the specified account. Statistics are aggregated across all jobs that have ever existed in the account, from account creation to the last update time of the statistics.
"""

helps['batch job prep-release-status'] = """
    type: group
    short-summary: Commands to view the status of your job preparation and release tasks.
"""

helps['batch job-schedule'] = """
    type: group
    short-summary: Commands to manage your Batch job schedules.
"""

helps['batch node user'] = """
    type: group
    short-summary: Commands to manage your Batch compute node users.
"""

helps['batch node user create'] = """
    type: command
    short-summary: Adds a user account to the specified compute node.
"""

helps['batch node user reset'] = """
    type: command
    short-summary: Updates the properties of a user account on the specified compute node. All updatable properties are replaced with the values specified or reset if unspecified.
"""

helps['batch node'] = """
    type: group
    short-summary: Commands to manage your Batch compute nodes.
"""

helps['batch node remote-login-settings'] = """
    type: group
    short-summary: Commands to retrieve the remote login settings for a Batch compute node.
"""

helps['batch node remote-desktop'] = """
    type: group
    short-summary: Commands to retrieve the remote desktop protocol for a Batch compute node.
"""

helps['batch node scheduling'] = """
    type: group
    short-summary: Commands to manage task scheduling for a Batch compute node.
"""

helps['batch pool'] = """
    type: group
    short-summary: Commands to manage your Batch pools.
"""

helps['batch pool os'] = """
    type: group
    short-summary: Commands to manage the operating system of your Batch pools.
"""

helps['batch pool autoscale'] = """
    type: group
    short-summary: Commands to manage automatic scaling of your Batch pools.
"""

helps['batch pool all-statistics'] = """
    type: group
    short-summary: Commands to view statistics of all pools under your Batch account.
"""

helps['batch pool all-statistics show'] = """
    type: command
    short-summary: Gets lifetime summary statistics for all of the pools in the specified account. Statistics are aggregated across all pools that have ever existed in the account, from account creation to the last update time of the statistics.
"""

helps['batch pool usage-metrics'] = """
    type: group
    short-summary: Commands to view usage metrics of your Batch pools.
"""

helps['batch pool node-agent-skus'] = """
    type: group
    short-summary: Commands to retrieve node agent SKUs of pools using a Virtual Machine Configuration.
"""

helps['batch task'] = """
    type: group
    short-summary: Commands to manage your Batch tasks.
"""

helps['batch task subtask'] = """
    type: group
    short-summary: Commands to manage subtask information of your Batch task.
"""

helps['batch certificate create'] = """
    type: command
    short-summary: Adds a certificate.
"""

helps['batch certificate delete'] = """
    type: command
    short-summary: Deletes the specified Batch certificate.
"""

helps['batch pool create'] = """
    type: command
    short-summary: Creates a pool in the specified account. When creating a pool, please chose arguments from either Cloud Services Configuration or Virtual Machine Configuration.
"""

helps['batch pool set'] = """
    type: command
    short-summary: Updates the properties of the specified pool. Properties can be updated independently, but please note that an updated property in a sub-group (i.e. 'start task') will result in all properties of that group being reset.
"""

helps['batch pool reset'] = """
    type: command
    short-summary: Updates the properties of the specified pool. All updatable properties are replaced with the values specified or cleared/defaulted if unspecified.
"""

helps['batch pool resize'] = """
    type: command
    short-summary: Resizes (or stops resizing) the Batch pool.
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
    short-summary: Updates the properties of a job. Properties can be updated independently, but please note that an updated property in a sub-group (i.e. 'constraints' and 'pool info') will result in all properties of that group being reset.
"""

helps['batch job reset'] = """
    type: command
    short-summary: Updates the properties of a job. All updatable properties are replaced with the values specified or cleared/defaulted if unspecified.
"""

helps['batch job-schedule create'] = """
    type: command
    short-summary: Adds a job schedule to the specified account.
"""

helps['batch job-schedule set'] = """
    type: command
    short-summary: Updates the properties of the specified job schedule. You can independently update the 'schedule' and/or the 'job specification', but note that any change to either of these entities will reset all properties in that entity.
"""

helps['batch job-schedule reset'] = """
    type: command
    short-summary: Updates the properties of the specified job schedule. All updatable properties are replaced with the values specified or cleared if unspecified. An updated job-specification will only apply to new jobs.
"""

helps['batch task create'] = """
    type: command
    short-summary: Creates a single Batch task or multiple Batch tasks.
"""

helps['batch task reset'] = """
    type: command
    short-summary: Updates the properties of the specified task. All updatable properties are replaced with the values specified or reset if unspecified.
"""
