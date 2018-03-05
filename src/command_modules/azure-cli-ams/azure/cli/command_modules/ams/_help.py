# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['ams'] = """
    type: group
    short-summary: Manage Azure Media Services.
"""

helps['ams create'] = """
    type: command
    short-summary: Create an Azure Media Service.
"""

helps['ams list'] = """
    type: command
    short-summary: List Azure Media Services for the entire subscription.
"""

helps['ams show'] = """
    type: command
    short-summary: Show the details of an Azure Media Service.
"""

helps['ams storage'] = """
    type: command
    short-summary: Manage secondary storage for an Azure Media Service.
"""

helps['ams storage add'] = """
    type: command
    short-summary: Attach a secondary storage to an Azure Media Service.
"""

helps['ams storage remove'] = """
    type: command
    short-summary: Detach a secondary storage from an Azure Media Service.
"""