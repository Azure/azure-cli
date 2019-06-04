# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import

helps['managedservices'] = """
    type: group
    short-summary: Manage the registration assignments and definitions in Azure.
"""

helps['managedservices definitions create'] = """
    type: command
    short-summary: Creates a new registration definition.
    long-summary: Creates a new registration definition under the default scope or under the subscription provided.
    parameters:
        - name: --name -n
          long-summary: |
             The name of the registration definition.
        - name: --managed-by-tenant-id
          long-summary: |
             The managed by tenant id.
        - name: --principal-id 
          long-summary: |
             The principal id.             
        - name: --role-definition-id  
          long-summary: |
             The role definition id.                          
        - name: --api-version
          long-summary: |
             Optional: The API version to target.
        - name: --description
          long-summary: |
             Optional: The friendly description.
        - name: --plan-name
          long-summary: |
             Optional: The plan name.
        - name: --plan-product
          long-summary: |
             Optional: The plan product.
        - name: --plan-publisher
          long-summary: |
             Optional: The plan publisher.
        - name: --plan-version
          long-summary: |
             Optional: The plan version.
        - name: --subscription
          long-summary: | 
             Optional: Used to override the default subscription.
        - name: --registration-definition-id
          long-summary: |
             Optional:  Can be used to override the generated registration definition id.           
    examples:
        - name: Creates a registration definition under the default subscription scope with the required parameters.
          text: az managedservices definitions create --name mydef --managed-by-tenant-id dab3375b-6197-4a15-a44b-16c41faa91d7 --principal-id b6f6c88a-5b7a-455e-ba40-ce146d4d3671 --role-definition-id ccdd72a7-3385-48ef-bd42-f606fba81ae7
        - name: Creates a registration definition under the given subscription scope with the required parameters.
          text: az managedservices definitions create --name mydef --managed-by-tenant-id dab3375b-6197-4a15-a44b-16c41faa91d7 --principal-id b6f6c88a-5b7a-455e-ba40-ce146d4d3671 --role-definition-id ccdd72a7-3385-48ef-bd42-f606fba81ae7 --subscription e716db1e-393d-4f2a-81fe-2577e92c9200
"""

helps['managedservices definitions show'] = """
    type: command
    short-summary: Gets a registration definition.
    long-summary: Gets a registration definition when given its identifier or the fully qualified resource id. When resource id is provided, the subscription paramter is ignored.
    parameters:
        - name: --api-version
          long-summary: |
             Optional: The API version to target.   
        - name: --subscription
          long-summary: | 
             Optional, but can be used to override the default subscription.
    examples:
        - name: Gets the registration definition given its identifier under the default subscription scope.
          text: az managedservices definitions show --name-or-id af8772a0-fd9c-4ddc-8ad0-7d4b3913d7dd
        - name: Gets the registration definition given its identifier and subscription id.
          text: az managedservices definitions show --name-or-id af8772a0-fd9c-4ddc-8ad0-7d4b3913d7dd --subscription 39033314-9b39-4c7b-84fd-0e26e55f15dc
        - name: Gets the registration definition given its fully qualified resource id.
          text: az managedservices definitions show --name-or-id /subscriptions/39033314-9b39-4c7b-84fd-0e26e55f15dc/providers/Microsoft.ManagedServices/registrationDefinitions/1d693e4f-9e79-433a-b3a2-afce1f8b61ec
"""

helps['managedservices definitions delete'] = """
    type: command
    short-summary: Deletes a registration definition.
    long-summary: Deletes a registration definition when given its identifier or the fully qualified resource id. When resource id is provided, the subscription paramter is ignored.
    parameters:
        - name: --api-version
          long-summary: |
             Optional: The API version to target.   
        - name: --subscription
          long-summary: | 
             Optional, but can be used to override the default subscription.
    examples:
        - name: Deletes the registration definition given its identifier under the default subscription scope.
          text: az managedservices definitions delete --name-or-id af8772a0-fd9c-4ddc-8ad0-7d4b3913d7dd
        - name: Deletes the registration definition given its identifier and subscription id.
          text: az managedservices definitions delete --name-or-id af8772a0-fd9c-4ddc-8ad0-7d4b3913d7dd --subscription 39033314-9b39-4c7b-84fd-0e26e55f15dc
        - name: Deletes the registration definition given its fully qualified resource id.
          text: az managedservices definitions delete --name-or-id /subscriptions/39033314-9b39-4c7b-84fd-0e26e55f15dc/providers/Microsoft.ManagedServices/registrationDefinitions/1d693e4f-9e79-433a-b3a2-afce1f8b61ec             
"""

helps['managedservices definitions list'] = """
    type: command
    short-summary: List all the registration definitions.
    long-summary: Lists all the registration definitions under the default scope or under the subscription provided.
    parameters:
        - name: --api-version
          long-summary: |
             Optional: The API version to target.   
        - name: --subscription
          long-summary: | 
             Optional, but can be used to override the default subscription.
    examples:
        - name: Lists all the registration definitions under the default subscription scope.
          text: az managedservices definitions list
        - name: Lists all the registration definitions under the given subscription scope.
          text: az managedservices definitions list --subscription 0c3e9687-b461-4615-b6e4-74d54998d6e4
"""

helps['managedservices assignments create'] = """
    type: command
    short-summary: Creates a new registration assignment.
    long-summary: Creates a new registration assignment when given the fully qualified resource id of the registration definition.
    parameters:
        - name: --registration-definition-id
          long-summary: |
             The fully qualified resource id of the registration definition.
        - name: --registration-assignment-id
          long-summary: | 
             Optional: Can be used to override the generated registration assignment id.
        - name: --subscription
          long-summary: | 
             Optional, but can be used to override the default subscription.
        - name: --resource-group -g
          long-summary: | 
             Optional. When provided the assignment will be created under the resource group scope. Ex: /subscriptions/id/resourceGroups/rgName/
        - name: --api-version
          long-summary: |
             Optional: The API version to target.             
    examples:
        - name: Create an assignment under the default subscription scope.
          text: az managedservices assignments create --registration-definition-id "/subscriptions/a62076fa-768a-403c-9d9d-6a9919aae441/providers/Microsoft.ManagedServices/registrationDefinitions/0c3e9687-b461-4615-b6e4-74d54998d6e4"
        - name: Create an assignment under a given subscription and resource group scope.
          text: az managedservices assignments create --registration-definition-id "/subscriptions/a62076fa-768a-403c-9d9d-6a9919aae441/providers/Microsoft.ManagedServices/registrationDefinitions/0c3e9687-b461-4615-b6e4-74d54998d6e4" --subscription 59ebfa63-a27a-421d-8c99-9c09c9cfed99 --resource-group mygroup
"""

helps['managedservices assignments show'] = """
    type: command
    short-summary: Gets a registration assignment.
    long-summary: Gets the registration assignment given its identifier (guid) or the fully qualified resource id. When resource id is used, subscription id and resource group parameters are ignored.
    parameters:
        - name: --subscription
          long-summary: | 
             Optional, but can be used to override the default subscription.
        - name: --resource-group -g
          long-summary: | 
             Optional. When provided the assignment will be created under the resource group scope. Ex: /subscriptions/id/resourceGroups/rgName/
        - name: --api-version
          long-summary: |
             Optional: The API version to target.
        - name: --expand-registration-definition
          long-summary: |
            Optional: When provided, gets the associated registration definition details.
    examples:
        - name: Get an assignment given its identifier under the default subscription scope.
          text: az managedservices assignments show --name-or-id d3087cf0-e180-4cca-b147-54ae00c7b504
        - name: Get an assignment given its fully qualified resource id.
          text: az managedservices assignments show --name-or-id /subscriptions/a62076fa-768a-403c-9d9d-6a9919aae441/providers/Microsoft.ManagedServices/registrationAssignments/0c3e9687-b461-4615-b6e4-74d54998d6e4
        - name: Get an assignment given its identifier under the default subscription scope with the registration definition details.
          text: az managedservices assignments show --name-or-id d3087cf0-e180-4cca-b147-54ae00c7b504 --expand-registration-definition
"""

helps['managedservices assignments delete'] = """
    type: command
    short-summary: Deletes the registration assignment.
    long-summary: Deletes the registration assignment given its identifier (guid) or the fully qualified resource id. When resource id is used, subscription id and resource group parameters are ignored.
    parameters:
        - name: --subscription
          long-summary: | 
             Optional, but can be used to override the default subscription.
        - name: --resource-group -g
          long-summary: | 
             Optional. When provided the assignment will be created under the resource group scope. Ex: /subscriptions/id/resourceGroups/rgName/
        - name: --api-version
          long-summary: |
             Optional: The API version to target.
    examples:
        - name: Deletes an assignment given its identifier under the default subscription scope.
          text: az managedservices assignments delete --name-or-id d3087cf0-e180-4cca-b147-54ae00c7b504
        - name: Deletes an assignment given its fully qualified resource id.
          text: az managedservices assignments delete --name-or-id /subscriptions/a62076fa-768a-403c-9d9d-6a9919aae441/providers/Microsoft.ManagedServices/registrationAssignments/0c3e9687-b461-4615-b6e4-74d54998d6e4
"""

helps['managedservices assignments list'] = """
    type: command
    short-summary: List all the registration assignments.
    long-summary: List all the registration assignments. Subscription id and resource group parameters can be used to override default values.
    parameters:
        - name: --subscription
          long-summary: | 
             Optional, but can be used to override the default subscription.
        - name: --resource-group -g
          long-summary: | 
             Optional. When provided the assignment will be created under the resource group scope. Ex: /subscriptions/id/resourceGroups/rgName/
        - name: --api-version
          long-summary: |
             Optional: The API version to target.
        - name: --expand-registration-definition
          long-summary: |
            Optional: When provided, gets the associated registration definition details.             
    examples:
        - name: Lists all the registration assignments under the default scope.
          text: az managedservices assignments list
        - name: Lists all the registration assignments under the given subscription.
          text: az managedservices assignments list --subscription 06bff45d-bf7d-4c1f-b826-f95cd6f34f4a
        - name: Lists all the registration assignments under the given subscription and resource group.
          text: az managedservices assignments list --subscription 06bff45d-bf7d-4c1f-b826-f95cd6f34f4a --resource-group mygroup
        - name: Lists all the registration assignments under the default scope along with the associated registration definition details.
          text: az managedservices assignments list --expand-registration-definition                    
"""