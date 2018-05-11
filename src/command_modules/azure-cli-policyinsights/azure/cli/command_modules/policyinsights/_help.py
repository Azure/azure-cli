# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

# pylint: disable=line-too-long, too-many-lines

helps['policyinsights'] = """
    type: group
    short-summary: Manage policy insights.
"""
helps['policyinsights event'] = """
    type: group
    short-summary: Manage policy events.
"""
helps['policyinsights event list'] = """
    type: command
    short-summary: List policy events.
    parameters:
        - name: --management-group-name -mg
          type: string
          short-summary: Management group name

        - name: --subscription-id -s
          type: string
          short-summary: Subscription ID

        - name: --resource-group-name -rg
          type: string
          short-summary: Resource group name

        - name: --resource-id -r
          type: string
          short-summary: Resource ID

        - name: --policy-set-definition-name -psd
          type: string
          short-summary: Policy set definition name

        - name: --policy-definition-name -pd
          type: string
          short-summary: Policy definition name

        - name: --policy-assignment-name -pa
          type: string
          short-summary: Policy assignment name

        - name: --from
          type: datetime
          short-summary: ISO 8601 formatted timestamp specifying the start time of the interval to query. When not specified, defaults to 'to' parameter value minus 1 day.

        - name: --to
          type: datetime
          short-summary: ISO 8601 formatted timestamp specifying the end time of the interval to query. When not specified, defaults to time of request.

        - name: --order-by -o
          type: string
          short-summary: Ordering expression using OData notation. One or more comma-separated column names with an optional 'desc' (the default) or 'asc'.

        - name: --select -s
          type: string
          short-summary: Select expression using OData notation. One or more comma-separated column names. Limits the columns on each record to just those requested.

        - name: --top -t
          type: long
          short-summary: Maximum number of records to return

        - name: --filter -f
          type: string
          short-summary: Filter expression using OData notation

        - name: --apply -a
          type: string
          short-summary: Apply expression for aggregations using OData notation
    examples:
        - name: Get policy events in the different scopes.
          text: |
              az policyinsights event list -mg {mymg} 

              az policyinsights event list -s {subscriptionid} 
"""
helps['policyinsights state'] = """
    type: group
    short-summary: Manage policy compliance states.
"""
helps['policyinsights state list'] = """
    type: command
    short-summary: List policy compliance states.
"""
helps['policyinsights state summarize'] = """
    type: command
    short-summary: Summarize policy compliance states.
"""
