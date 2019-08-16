# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['managedservices'] = """
type: group
short-summary: Manage the registration assignments and definitions in Azure.
"""

helps['managedservices assignment'] = """
type: group
short-summary: Manage the registration assignments in Azure.
"""

helps['managedservices assignment delete'] = """
type: command
short-summary: Deletes the registration assignment.
examples:
  - name: Deletes an assignment given its identifier under the default subscription scope.
    text: az managedservices assignment delete --assignment d3087cf0-e180-4cca-b147-54ae00c7b504
  - name: Deletes an assignment given its fully qualified resource id.
    text: az managedservices assignment delete --assignment /subscriptions/a62076fa-768a-403c-9d9d-6a9919aae441/providers/Microsoft.ManagedServices/registrationAssignments/0c3e9687-b461-4615-b6e4-74d54998d6e4
"""

helps['managedservices assignment list'] = """
type: command
short-summary: List all the registration assignments.
examples:
  - name: Lists all the registration assignments under the default scope.
    text: az managedservices assignment list
  - name: Lists all the registration assignments under the given resource group.
    text: az managedservices assignment list --resource-group mygroup
  - name: Lists all the registration assignments under the default scope along with the associated registration definition details.
    text: az managedservices assignment list --include-definition true
"""

helps['managedservices assignment show'] = """
type: command
short-summary: Gets a registration assignment.
examples:
  - name: Get an assignment given its identifier under the default subscription scope.
    text: az managedservices assignment show --assignment d3087cf0-e180-4cca-b147-54ae00c7b504
  - name: Get an assignment given its fully qualified resource id.
    text: az managedservices assignment show --assignment /subscriptions/a62076fa-768a-403c-9d9d-6a9919aae441/providers/Microsoft.ManagedServices/registrationAssignments/0c3e9687-b461-4615-b6e4-74d54998d6e4
  - name: Get an assignment given its identifier under the default subscription scope with the registration definition details.
    text: az managedservices assignment show --assignment d3087cf0-e180-4cca-b147-54ae00c7b504 --include-definition true
"""

helps['managedservices definition'] = """
type: group
short-summary: Manage the registration definitions in Azure.
"""

helps['managedservices definition delete'] = """
type: command
short-summary: Deletes a registration.
examples:
  - name: Deletes the registration definition given its identifier under the default subscription scope.
    text: az managedservices definition delete --definition af8772a0-fd9c-4ddc-8ad0-7d4b3913d7dd
  - name: Deletes the registration definition given its fully qualified resource id.
    text: az managedservices definition delete --definition /subscriptions/39033314-9b39-4c7b-84fd-0e26e55f15dc/providers/Microsoft.ManagedServices/registrationDefinitions/1d693e4f-9e79-433a-b3a2-afce1f8b61ec
"""

helps['managedservices definition list'] = """
type: command
short-summary: List all the registration definitions under the default scope or under the subscription provided.
examples:
  - name: Lists all the registration definitions under the default subscription scope.
    text: az managedservices definition list
"""

helps['managedservices definition show'] = """
type: command
short-summary: Gets a registration definition.
examples:
  - name: Gets the registration definition given its identifier under the default subscription scope.
    text: az managedservices definition show --definition af8772a0-fd9c-4ddc-8ad0-7d4b3913d7dd
  - name: Gets the registration definition given its fully qualified resource id.
    text: az managedservices definition show --definition /subscriptions/39033314-9b39-4c7b-84fd-0e26e55f15dc/providers/Microsoft.ManagedServices/registrationDefinitions/1d693e4f-9e79-433a-b3a2-afce1f8b61ec
"""
