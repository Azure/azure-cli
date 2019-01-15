# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["ams asset get-streaming-locators"] = """
"type": |-
    command
"short-summary": |-
    List streaming locators which are associated with this asset.
"""

helps["ams content-key-policy option add"] = """
"type": |-
    command
"short-summary": |-
    Add a new option to an existing content key policy.
"""

helps["ams streaming-endpoint create"] = """
"type": |-
    command
"short-summary": |-
    Create a streaming endpoint.
"""

helps["ams streaming-endpoint akamai remove"] = """
"type": |-
    command
"short-summary": |-
    Remove an AkamaiAccessControl from an existing streaming endpoint.
"""

helps["ams streaming-locator show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of a streaming locator.
"""

helps["ams account-filter update"] = """
"type": |-
    command
"short-summary": |-
    Update the details of an account filter.
"""

helps["ams content-key-policy list"] = """
"type": |-
    command
"short-summary": |-
    List all the content key policies within an Azure Media Services account.
"""

helps["ams transform output remove"] = """
"type": |-
    command
"short-summary": |-
    Remove an output from an existing transform.
"""

helps["ams transform delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a transform.
"""

helps["ams asset"] = """
"type": |-
    group
"short-summary": |-
    Manage assets for an Azure Media Services account.
"""

helps["ams content-key-policy option"] = """
"type": |-
    group
"short-summary": |-
    Manage options for an existing content key policy.
"""

helps["ams asset delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an asset.
"examples":
-   "name": |-
        Delete an asset.
    "text": |-
        az ams asset delete --name MyAsset --account-name MyAccount --resource-group MyResourceGroup
"""

helps["ams transform list"] = """
"type": |-
    command
"short-summary": |-
    List all the transforms of an Azure Media Services account.
"""

helps["ams live-output show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of a live output.
"""

helps["ams asset update"] = """
"type": |-
    command
"short-summary": |-
    Update the details of an asset.
"""

helps["ams account mru set"] = """
"type": |-
    command
"short-summary": |-
    Set the type and number of media reserved units for an Azure Media Services account.
"""

helps["ams live-output delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a live output.
"""

helps["ams account storage sync-storage-keys"] = """
"type": |-
    command
"short-summary": |-
    Synchronize storage account keys for a storage account associated with an Azure Media Services account.
"""

helps["ams content-key-policy delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a content key policy.
"""

helps["ams streaming-policy"] = """
"type": |-
    group
"short-summary": |-
    Manage streaming policies for an Azure Media Services account.
"""

helps["ams live-event update"] = """
"type": |-
    command
"short-summary": |-
    Update the details of a live event.
"""

helps["ams account-filter"] = """
"type": |-
    group
"short-summary": |-
    Manage account filters for an Azure Media Services account.
"""

helps["ams job"] = """
"type": |-
    group
"short-summary": |-
    Manage jobs for a transform.
"""

helps["ams account storage"] = """
"type": |-
    group
"short-summary": |-
    Manage storage for an Azure Media Services account.
"""

helps["ams asset list"] = """
"type": |-
    command
"short-summary": |-
    List all the assets of an Azure Media Services account.
"""

helps["ams content-key-policy show"] = """
"type": |-
    command
"short-summary": |-
    Show an existing content key policy.
"""

helps["ams asset-filter create"] = """
"type": |-
    command
"short-summary": |-
    Create an asset filter.
"""

helps["ams transform create"] = """
"type": |-
    command
"short-summary": |-
    Create a transform.
"""

helps["ams account sp create"] = """
"type": |-
    command
"short-summary": |-
    Create a service principal and configure its access to an Azure Media Services account.
"long-summary": |-
    Service principal propagation throughout Azure Active Directory may take some extra seconds to complete.
"""

helps["ams live-event"] = """
"type": |-
    group
"short-summary": |-
    Manage live events for an Azure Media Service account.
"""

helps["ams transform output add"] = """
"type": |-
    command
"short-summary": |-
    Add an output to an existing transform.
"""

helps["ams live-event start"] = """
"type": |-
    command
"short-summary": |-
    Start a live event.
"""

helps["ams live-event reset"] = """
"type": |-
    command
"short-summary": |-
    Reset a live event.
"""

helps["ams transform output"] = """
"type": |-
    group
"short-summary": |-
    Manage transform outputs for an Azure Media Services account.
"""

helps["ams asset get-sas-urls"] = """
"type": |-
    command
"short-summary": |-
    Lists storage container URLs with shared access signatures (SAS) for uploading and downloading Asset content. The signatures are derived from the storage account keys.
"""

helps["ams live-event create"] = """
"type": |-
    command
"short-summary": |-
    Create a live event.
"""

helps["ams streaming-endpoint start"] = """
"type": |-
    command
"short-summary": |-
    Start a streaming endpoint.
"""

helps["ams content-key-policy"] = """
"type": |-
    group
"short-summary": |-
    Manage content key policies for an Azure Media Services account.
"""

helps["ams job start"] = """
"type": |-
    command
"short-summary": |-
    Start a job.
"""

helps["ams account create"] = """
"type": |-
    command
"short-summary": |-
    Create an Azure Media Services account.
"""

helps["ams job show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of a job.
"""

helps["ams streaming-endpoint scale"] = """
"type": |-
    command
"short-summary": |-
    Set the scale of a streaming endpoint.
"""

helps["ams live-event delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a live event.
"""

helps["ams streaming-endpoint show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of a streaming endpoint.
"""

helps["ams asset show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of an asset.
"""

helps["ams streaming-endpoint list"] = """
"type": |-
    command
"short-summary": |-
    List all the streaming endpoints within an Azure Media Services account.
"""

helps["ams account list"] = """
"type": |-
    command
"short-summary": |-
    List Azure Media Services accounts for the entire subscription.
"""

helps["ams transform"] = """
"type": |-
    group
"short-summary": |-
    Manage transforms for an Azure Media Services account.
"""

helps["ams account-filter list"] = """
"type": |-
    command
"short-summary": |-
    List all the account filters of an Azure Media Services account.
"""

helps["ams streaming-locator list"] = """
"type": |-
    command
"short-summary": |-
    List all the streaming locators within an Azure Media Services account.
"""

helps["ams account update"] = """
"type": |-
    command
"short-summary": |-
    Update the details of an Azure Media Services account.
"""

helps["ams account storage add"] = """
"type": |-
    command
"short-summary": |-
    Attach a secondary storage to an Azure Media Services account.
"""

helps["ams live-event show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of a live event.
"""

helps["ams asset-filter show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of an asset filter.
"""

helps["ams streaming-locator create"] = """
"type": |-
    command
"short-summary": |-
    Create a streaming locator.
"""

helps["ams account-filter delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an account filter.
"""

helps["ams account show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of an Azure Media Services account.
"""

helps["ams streaming-endpoint stop"] = """
"type": |-
    command
"short-summary": |-
    Stop a streaming endpoint.
"""

helps["ams asset-filter delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an asset filter.
"""

helps["ams streaming-endpoint akamai add"] = """
"type": |-
    command
"short-summary": |-
    Add an AkamaiAccessControl to an existing streaming endpoint.
"""

helps["ams asset-filter list"] = """
"type": |-
    command
"short-summary": |-
    List all the asset filters of an Azure Media Services account.
"""

helps["ams job list"] = """
"type": |-
    command
"short-summary": |-
    List all the jobs of a transform within an Azure Media Services account.
"""

helps["ams"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Media Services resources.
"""

helps["ams streaming-policy create"] = """
"type": |-
    command
"short-summary": |-
    Create a streaming policy.
"""

helps["ams asset-filter update"] = """
"type": |-
    command
"short-summary": |-
    Update the details of an asset filter.
"""

helps["ams streaming-policy show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of a streaming policy.
"""

helps["ams asset create"] = """
"type": |-
    command
"short-summary": |-
    Create an asset.
"""

helps["ams transform show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of a transform.
"""

helps["ams streaming-endpoint akamai"] = """
"type": |-
    group
"short-summary": |-
    Manage AkamaiAccessControl objects to be used on streaming endpoints.
"""

helps["ams live-output"] = """
"type": |-
    group
"short-summary": |-
    Manage live outputs for an Azure Media Service account.
"""

helps["ams account-filter create"] = """
"type": |-
    command
"short-summary": |-
    Create an account filter.
"""

helps["ams job cancel"] = """
"type": |-
    command
"short-summary": |-
    Cancel a job.
"""

helps["ams account delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an Azure Media Services account.
"""

helps["ams account"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Media Services accounts.
"""

helps["ams live-output list"] = """
"type": |-
    command
"short-summary": |-
    List all the live outputs in a live event.
"""

helps["ams account-filter show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of an account filter.
"""

helps["ams job delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a job.
"""

helps["ams content-key-policy option update"] = """
"type": |-
    command
"short-summary": |-
    Update an option from an existing content key policy.
"""

helps["ams streaming-policy list"] = """
"type": |-
    command
"short-summary": |-
    List all the streaming policies within an Azure Media Services account.
"""

helps["ams streaming-locator get-content-keys"] = """
"type": |-
    command
"short-summary": |-
    List content keys used by a streaming locator.
"""

helps["ams content-key-policy create"] = """
"type": |-
    command
"short-summary": |-
    Create a new content key policy.
"""

helps["ams streaming-locator"] = """
"type": |-
    group
"short-summary": |-
    Manage streaming locators for an Azure Media Services account.
"""

helps["ams transform update"] = """
"type": |-
    command
"short-summary": |-
    Update the details of a transform.
"""

helps["ams account mru"] = """
"type": |-
    group
"short-summary": |-
    Manage media reserved units for an Azure Media Services account.
"""

helps["ams live-event list"] = """
"type": |-
    command
"short-summary": |-
    List all the live events of an Azure Media Services account.
"""

helps["ams account sp"] = """
"type": |-
    group
"short-summary": |-
    Manage service principal and role based access for an Azure Media Services account.
"""

helps["ams streaming-endpoint"] = """
"type": |-
    group
"short-summary": |-
    Manage streaming endpoints for an Azure Media Service account.
"""

helps["ams account storage remove"] = """
"type": |-
    command
"short-summary": |-
    Detach a secondary storage from an Azure Media Services account.
"""

helps["ams account check-name"] = """
"type": |-
    command
"short-summary": |-
    Checks whether the Media Service resource name is available.
"""

helps["ams job update"] = """
"type": |-
    command
"short-summary": |-
    Update an existing job.
"""

helps["ams content-key-policy update"] = """
"type": |-
    command
"short-summary": |-
    Update an existing content key policy.
"""

helps["ams asset-filter"] = """
"type": |-
    group
"short-summary": |-
    Manage asset filters for an Azure Media Services account.
"""

helps["ams live-event stop"] = """
"type": |-
    command
"short-summary": |-
    Stop a live event.
"""

helps["ams account mru show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of media reserved units for an Azure Media Services account.
"""

helps["ams live-output create"] = """
"type": |-
    command
"short-summary": |-
    Create a live output.
"""

helps["ams content-key-policy option remove"] = """
"type": |-
    command
"short-summary": |-
    Remove an option from an existing content key policy.
"""

helps["ams streaming-endpoint update"] = """
"type": |-
    command
"short-summary": |-
    Update the details of a streaming endpoint.
"""

helps["ams streaming-locator get-paths"] = """
"type": |-
    command
"short-summary": |-
    List paths supported by a streaming locator.
"""

helps["ams streaming-endpoint delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a streaming endpoint.
"""

helps["ams asset get-encryption-key"] = """
"type": |-
    command
"short-summary": |-
    Get the asset storage encryption keys used to decrypt content created by version 2 of the Media Services API.
"""

helps["ams account sp reset-credentials"] = """
"type": |-
    command
"short-summary": |-
    Generate a new client secret for a service principal configured for an Azure Media Services account.
"""

