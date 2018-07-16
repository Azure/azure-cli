# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

logger = get_logger(__name__)

def execute_query(client, workspace, kql, timespan=None, workspaces=None):
    """Executes a query against the provided Log Analytics workspace."""
    from azure.loganalytics.models import QueryBody
    return client.query(workspace, QueryBody(query=kql, timespan=timespan, workspaces=workspaces))
