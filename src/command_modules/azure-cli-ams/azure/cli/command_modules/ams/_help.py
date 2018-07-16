# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-lines

from knack.help_files import helps


helps['ams'] = """
    type: group
    short-summary: Manage Azure Media Services resources.
"""

helps['ams account'] = """
    type: group
    short-summary: Manage Azure Media Services accounts.
"""

helps['ams account create'] = """
    type: command
    short-summary: Create an Azure Media Services account.
"""

helps['ams account update'] = """
    type: command
    short-summary: Update the details of an Azure Media Services account.
"""

helps['ams account list'] = """
    type: command
    short-summary: List Azure Media Services accounts for the entire subscription.
"""

helps['ams account show'] = """
    type: command
    short-summary: Show the details of an Azure Media Services account.
"""

helps['ams account delete'] = """
    type: command
    short-summary: Delete an Azure Media Services account.
"""

helps['ams account storage'] = """
    type: group
    short-summary: Manage secondary storage for an Azure Media Services account.
"""

helps['ams account storage add'] = """
    type: command
    short-summary: Attach a secondary storage to an Azure Media Services account.
"""

helps['ams account storage remove'] = """
    type: command
    short-summary: Detach a secondary storage from an Azure Media Services account.
"""

helps['ams account sp'] = """
    type: group
    short-summary: Manage service principal and role based access for an Azure Media Services account.
"""

helps['ams account sp create'] = """
    type: command
    short-summary: Create a service principal and configure its access to an Azure Media Services account.
    examples:
        - name: Create a service principal with password and configure its access to an Azure Media Services account. Output will be in xml format.
          text: >
            az ams account sp create -a {myamsaccount} -g {myresourcegroup} -n {mySpName} -password {mySpPassword} --role {rol} --xml
    """

helps['ams account sp reset-credentials'] = """
    type: command
    short-summary: Generate a new client secret for a service principal configured for an Azure Media Services account.
"""

helps['ams transform'] = """
    type: group
    short-summary: Manage transforms for an Azure Media Services account.
"""

helps['ams transform list'] = """
    type: command
    short-summary: List all the transforms of an Azure Media Services account.
"""

helps['ams transform show'] = """
    type: command
    short-summary: Show the details of a transform.
"""

helps['ams transform create'] = """
    type: command
    short-summary: Create a transform.
"""

helps['ams transform delete'] = """
    type: command
    short-summary: Delete a transform.
"""

helps['ams transform update'] = """
    type: command
    short-summary: Update the details of a transform.
"""

helps['ams transform output'] = """
    type: group
    short-summary: Manage transform outputs for an Azure Media Services account.
"""

helps['ams transform output add'] = """
    type: command
    short-summary: Add an output to an existing transform.
"""

helps['ams transform output remove'] = """
    type: command
    short-summary: Remove an output from an existing transform.
"""

helps['ams asset'] = """
    type: group
    short-summary: Manage assets for an Azure Media Services account.
"""

helps['ams asset show'] = """
    type: command
    short-summary: Show the details of an asset.
"""

helps['ams asset list'] = """
    type: command
    short-summary: List all the assets of an Azure Media Services account.
"""

helps['ams asset create'] = """
    type: command
    short-summary: Create an asset.
"""

helps['ams asset update'] = """
    type: command
    short-summary: Update the details of an asset.
"""

helps['ams asset delete'] = """
    type: command
    short-summary: Delete an asset.
"""

helps['ams asset get-sas-urls'] = """
    type: command
    short-summary: Lists the asset SAS URLs used for uploading and downloading asset content.
"""

helps['ams job'] = """
    type: group
    short-summary: Manage jobs for a transform.
"""

helps['ams job start'] = """
    type: command
    short-summary: Start a job.
"""

helps['ams job list'] = """
    type: command
    short-summary: List all the jobs of a transform within an Azure Media Services account.
"""

helps['ams job show'] = """
    type: command
    short-summary: Show the details of a job.
"""

helps['ams job delete'] = """
    type: command
    short-summary: Delete a job.
"""

helps['ams job cancel'] = """
    type: command
    short-summary: Cancel a job.
"""

helps['ams streaming'] = """
    type: group
    short-summary: Manage streamings for an Azure Media Services account.
"""

helps['ams streaming locator'] = """
    type: group
    short-summary: Manage streaming locators for an Azure Media Services account.
"""

helps['ams streaming locator create'] = """
    type: command
    short-summary: Create a streaming locator.
"""

helps['ams streaming locator list'] = """
    type: command
    short-summary: List all the streaming locators within an Azure Media Services account.
"""

helps['ams streaming locator show'] = """
    type: command
    short-summary: Show the details of a streaming locator.
"""

helps['ams streaming locator get-paths'] = """
    type: command
    short-summary: List paths supported by a streaming locator.
"""

helps['ams streaming policy'] = """
    type: group
    short-summary: Manage streaming policies for an Azure Media Services account.
"""

helps['ams streaming policy create'] = """
    type: command
    short-summary: Create a streaming policy.
"""

helps['ams streaming policy list'] = """
    type: command
    short-summary: List all the streaming policies within an Azure Media Services account.
"""

helps['ams streaming policy show'] = """
    type: command
    short-summary: Show the details of a streaming policy.
"""

helps['ams streaming endpoint'] = """
    type: group
    short-summary: Manage streaming endpoints for an Azure Media Service account.
"""

helps['ams streaming endpoint start'] = """
    type: command
    short-summary: Start a streaming endpoint.
"""

helps['ams streaming endpoint stop'] = """
    type: command
    short-summary: Stop a streaming endpoint.
"""

helps['ams streaming endpoint list'] = """
    type: command
    short-summary: List all the streaming endpoints within an Azure Media Services account.
"""
