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

helps['managedservices assignment create'] = """
type: command
short-summary: Creates a new registration assignment.
parameters:
  - name: --definition
    short-summary: |
        The fully qualified resource id of the registration definition.
  - name: --assignment-id
    short-summary: |
        Can be used to override the generated registration assignment id.
examples:
  - name: Create an assignment under the default subscription scope.
    text: az managedservices assignment create --definition "/subscriptions/a62076fa-768a-403c-9d9d-6a9919aae441/providers/Microsoft.ManagedServices/registrationDefinitions/0c3e9687-b461-4615-b6e4-74d54998d6e4"
  - name: Create an assignment under a given resource group scope.
    text: az managedservices assignment create --definition "/subscriptions/a62076fa-768a-403c-9d9d-6a9919aae441/providers/Microsoft.ManagedServices/registrationDefinitions/0c3e9687-b461-4615-b6e4-74d54998d6e4" --resource-group mygroup
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

helps['managedservices definition create'] = """
type: command
short-summary: Creates a new registration definition.
parameters:
  - name: --name
    short-summary: |
        The name of the registration definition.
  - name: --tenant-id
    short-summary: |
        The managed by tenant id.
  - name: --principal-id
    short-summary: |
        The principal id.
  - name: --role-definition-id
    short-summary: |
        The role definition id.
  - name: --description
    short-summary: |
        The friendly description.
  - name: --plan-name
    short-summary: |
        The plan name.
  - name: --plan-product
    short-summary: |
        The plan product.
  - name: --plan-publisher
    short-summary: |
        The plan publisher.
  - name: --plan-version
    short-summary: |
        The plan version.
  - name: --definition-id
    short-summary: |
        Can be used to override the generated registration definition id.
examples:
  - name: Creates a registration definition under the default subscription scope with the required parameters.
    text: az managedservices definition create --name mydef --tenant-id dab3375b-6197-4a15-a44b-16c41faa91d7 --principal-id b6f6c88a-5b7a-455e-ba40-ce146d4d3671 --role-definition-id ccdd72a7-3385-48ef-bd42-f606fba81ae7
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
