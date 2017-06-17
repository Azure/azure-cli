# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps


helps['batch'] = """
    type: group
    short-summary: Manage Azure Batch.
"""

helps['batch account'] = """
    type: group
    short-summary: Manage your Batch accounts.
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
    short-summary: Update the properties of the specified Batch account. Properties that are not specified remain unchanged.
"""

helps['batch account autostorage-keys'] = """
    type: group
    short-summary: Manage the access keys for the auto storage account configured for your Batch account.
"""

helps['batch account keys'] = """
    type: group
    short-summary: Manage your Batch account keys.
"""

helps['batch account login'] = """
    type: command
    short-summary: Log in with specified Batch account through Azure Active Directory or Shared Key authentication.
"""

helps['batch application'] = """
    type: group
    short-summary: Manage your Batch applications.
"""

helps['batch application set'] = """
    type: command
    short-summary: Update the properties of the specified application. Properties that are not specified remain unchanged.
"""

helps['batch application package'] = """
    type: group
    short-summary: Manage your Batch application packages.
"""

helps['batch application package create'] = """
    type: command
    short-summary: Create an application package record and activate it.
"""

helps['batch application package activate'] = """
    type: command
    short-summary: Activates the specified application package. This step is unnecessary if the package has already been successfully activated by the 'create' command.
"""

helps['batch application summary'] = """
    type: group
    short-summary: View a summary of your Batch application packages.
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
    short-summary: Manage your Batch certificates.
"""

helps['batch task file'] = """
    type: group
    short-summary: Manage your Batch task files.
"""

helps['batch task file download'] = """
    type: command
    short-summary: Download the content of the specified task file.
"""

helps['batch node file'] = """
    type: group
    short-summary: Manage your Batch compute node files.
"""

helps['batch node file download'] = """
    type: command
    short-summary: Download the content of the specified node file.
"""

helps['batch job'] = """
    type: group
    short-summary: Manage your Batch jobs.
"""

helps['batch job all-statistics'] = """
    type: group
    short-summary: View statistics of all the jobs under your Batch account.
"""

helps['batch job all-statistics show'] = """
    type: command
    short-summary: Get lifetime summary statistics for all of the jobs in the specified account. Statistics are aggregated across all jobs that have ever existed in the account, from account creation to the last update time of the statistics.
"""

helps['batch job prep-release-status'] = """
    type: group
    short-summary: View the status of your job preparation and release tasks.
"""

helps['batch job-schedule'] = """
    type: group
    short-summary: Manage your Batch job schedules.
"""

helps['batch node user'] = """
    type: group
    short-summary: Manage the user accounts of your Batch compute node.
"""

helps['batch node user create'] = """
    type: command
    short-summary: Add a user account to the specified compute node.
"""

helps['batch node user reset'] = """
    type: command
    short-summary: Update the properties of a user account on the specified compute node. All updatable properties are replaced with the values specified or reset if unspecified.
"""

helps['batch node'] = """
    type: group
    short-summary: Manage your Batch compute nodes.
"""

helps['batch node remote-login-settings'] = """
    type: group
    short-summary: Retrieve the remote login settings for a Batch compute node.
"""

helps['batch node remote-desktop'] = """
    type: group
    short-summary: Retrieve the remote desktop protocol for a Batch compute node.
"""

helps['batch node scheduling'] = """
    type: group
    short-summary: Manage task scheduling for a Batch compute node.
"""

helps['batch pool'] = """
    type: group
    short-summary: Manage your Batch pools.
"""

helps['batch pool os'] = """
    type: group
    short-summary: Manage the operating system of your Batch pools.
"""

helps['batch pool autoscale'] = """
    type: group
    short-summary: Manage automatic scaling of your Batch pools.
"""

helps['batch pool all-statistics'] = """
    type: group
    short-summary: View statistics of all pools under your Batch account.
"""

helps['batch pool all-statistics show'] = """
    type: command
    short-summary: Get lifetime summary statistics for all of the pools in the specified account. Statistics are aggregated across all pools that have ever existed in the account, from account creation to the last update time of the statistics.
"""

helps['batch pool usage-metrics'] = """
    type: group
    short-summary: View usage metrics of your Batch pools.
"""

helps['batch pool node-agent-skus'] = """
    type: group
    short-summary: Retrieve node agent SKUs of pools using a Virtual Machine Configuration.
"""

helps['batch task'] = """
    type: group
    short-summary: Manage your Batch tasks.
"""

helps['batch task subtask'] = """
    type: group
    short-summary: Manage subtask information of your Batch task.
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
    short-summary: Create a pool in the specified account. When creating a pool, choose arguments from either Cloud Services Configuration or Virtual Machine Configuration.
"""

helps['batch pool set'] = """
    type: command
    short-summary: Update the properties of the specified pool. Properties can be updated independently, but when a property is updated in a sub-group, for example 'start task', all properties of that group are reset.
"""

helps['batch pool reset'] = """
    type: command
    short-summary: Update the properties of the specified pool. All updatable properties are replaced with the values specified or reset to default values if unspecified.
"""

helps['batch pool resize'] = """
    type: command
    short-summary: Resize (or stop resizing) the Batch pool.
"""

helps['batch job create'] = """
    type: command
    short-summary: Add a job to the specified account.
"""

helps['batch job list'] = """
    type: command
    short-summary: List all of the jobs in the specified account or the specified job schedule.
"""

helps['batch job set'] = """
    type: command
    short-summary: Update the properties of a job. Properties can be updated independently, but when a property is updated in a sub-group, for example 'constraints' or 'pool info', all properties of that group are reset.
"""

helps['batch job reset'] = """
    type: command
    short-summary: Update the properties of a job. All updatable properties are replaced with the values specified or reset to default vaules if unspecified.
"""

helps['batch job-schedule create'] = """
    type: command
    short-summary: Add a job schedule to the specified account.
"""

helps['batch job-schedule set'] = """
    type: command
    short-summary: Update the properties of the specified job schedule. You can independently update the 'schedule' and the 'job specification', but any change to either of these entities will reset all properties in that entity.
"""

helps['batch job-schedule reset'] = """
    type: command
    short-summary: Update the properties of the specified job schedule. All updatable properties are replaced with the values specified or reset to default values if unspecified. An updated job specification only applies to new jobs.
"""

helps['batch task create'] = """
    type: command
    short-summary: Create a single Batch task or multiple Batch tasks.
"""

helps['batch task reset'] = """
    type: command
    short-summary: Update the properties of the specified task. All updatable properties are replaced with the values specified or reset if unspecified.
"""
