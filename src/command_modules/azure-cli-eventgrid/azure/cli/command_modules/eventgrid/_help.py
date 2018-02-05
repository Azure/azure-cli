# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from knack.help_files import helps  # pylint: disable=unused-import


helps['eventgrid'] = """
    type: group
    short-summary: Manage Azure Event Grid topics and subscriptions.
    """
helps['eventgrid topic'] = """
    type: group
    short-summary: Manage Azure Event Grid topics.
    """
helps['eventgrid topic create'] = """
    type: command
    short-summary: Create a topic.
    examples:
        - name: Create a new topic.
          text: az eventgrid topic create -g rg1 --name topic1 -l westus2
    """
helps['eventgrid topic update'] = """
    type: command
    short-summary: Update a topic.
    examples:
        - name: Update the properties of an existing topic.
          text: az eventgrid topic update -g rg1 --name topic1 --tags Dept=IT
    """
helps['eventgrid topic delete'] = """
    type: command
    short-summary: Delete a topic.
    examples:
        - name: Delete a topic.
          text: az eventgrid topic delete -g rg1 --name topic1
    """
helps['eventgrid topic list'] = """
    type: command
    short-summary: List available topics.
    examples:
        - name: List all topics in the current Azure subscription.
          text: az eventgrid topic list
        - name: List all topics in a resource group.
          text: az eventgrid topic list -g rg1
    """
helps['eventgrid topic show'] = """
    type: command
    short-summary: Get the details of a topic.
    examples:
        - name: Show the details of a topic.
          text: az eventgrid topic show -g rg1 -n topic1
        - name: Show the details of a topic based on resource ID.
          text: az eventgrid topic show --ids /subscriptions/55f3dcd4-cac7-43b4-990b-a139d62a1eb2/resourceGroups/kalstest/providers/Microsoft.EventGrid/topics/topic1
    """
helps['eventgrid topic key'] = """
    type: group
    short-summary: Manage shared access keys of a topic.
    """
helps['eventgrid topic key list'] = """
    type: command
    short-summary: List shared access keys of a topic.
    """
helps['eventgrid topic key regenerate'] = """
    type: command
    short-summary: Regenerate a shared access key of a topic.
    """
helps['eventgrid event-subscription'] = """
    type: group
    short-summary: Manage event subscriptions for an Event Grid topic or for an Azure resource.
    """
helps['eventgrid event-subscription create'] = """
    type: command
    short-summary: Create a new event subscription for an Event Grid topic or for an Azure resource.
    examples:
        - name: Create a new event subscription for an Event Grid topic, using default filters.
          text: |
            az eventgrid event-subscription create -g rg1 --topic-name topic1 --name es1 \\
                --endpoint https://contoso.azurewebsites.net/api/f1?code=code
        - name: Create a new event subscription for a subscription, using default filters.
          text: |
            az eventgrid event-subscription create --name es2 \\
                --endpoint https://contoso.azurewebsites.net/api/f1?code=code
        - name: Create a new event subscription for a resource group, using default filters.
          text: |
            az eventgrid event-subscription create -g rg1 --name es3 \\
                --endpoint https://contoso.azurewebsites.net/api/f1?code=code
        - name: Create a new event subscription for a storage account, using default filters.
          text: |
            az eventgrid event-subscription create --resource-id "/subscriptions/55f3dcd4-cac7-43b4-990b-a139d62a1eb2/resourceGroups/kalstest/providers/Microsoft.Storage/storageaccounts/kalsegblob" --name es3 \\
                --endpoint https://contoso.azurewebsites.net/api/f1?code=code
        - name: Create a new event subscription for a subscription, with a filter specifying a subject prefix.
          text: |
            az eventgrid event-subscription create --name es4 \\
                --endpoint https://contoso.azurewebsites.net/api/f1?code=code \\
                --subject-begins-with mysubject_prefix
        - name: Create a new event subscription for a resource group, with a filter specifying a subject suffix.
          text: |
            az eventgrid event-subscription create -g rg2 --name es5 \\
                --endpoint https://contoso.azurewebsites.net/api/f1?code=code \\
                --subject-ends-with mysubject_suffix
        - name: Create a new event subscription for a subscription, using default filters, and an EventHub as a destination.
          text: |
            az eventgrid event-subscription create --name es2 --endpoint-type eventhub \\
                --endpoint /subscriptions/55f3dcd4-cac7-43b4-990b-a139d62a1eb2/resourceGroups/TestRG/providers/Microsoft.EventHub/namespaces/ContosoNamespace/eventhubs/EH1
    """
helps['eventgrid event-subscription update'] = """
    type: command
    short-summary: Update an event subscription.
    examples:
        - name: Update an event subscription for an Event Grid topic to specify a new endpoint.
          text: |
            az eventgrid event-subscription update -g rg1 --topic-name topic1 --name es1 \\
                --endpoint https://contoso.azurewebsites.net/api/f1?code=code
        - name: Update an event subscription for a subscription to specify a new subject-ends-with filter.
          text: |
            az eventgrid event-subscription update --name es2 --subject-ends-with .jpg
        - name: Update an event subscription for a resource group to specify a new endpoint and a new subject-ends-with filter.
          text: |
            az eventgrid event-subscription update -g rg1 --name es3  --subject-ends-with .png \\
                --endpoint https://contoso.azurewebsites.net/api/f1?code=code
        - name: Update an event subscription for a storage account to specify a new list of included event types.
          text: |
            az eventgrid event-subscription update --resource-id "/subscriptions/55f3dcd4-cac7-43b4-990b-a139d62a1eb2/resourceGroups/kalstest/providers/microsoft.storage/storageaccounts/kalsegblob" --name es3 \\
                --included-event-types Microsoft.Storage.BlobCreated Microsoft.Storage.BlobDeleted
    """
helps['eventgrid event-subscription delete'] = """
    type: command
    short-summary: Delete an event subscription.
    examples:
        - name: Delete an event subscription for an Event Grid topic.
          text: |
            az eventgrid event-subscription delete -g rg1 --topic-name topic1 --name es1
        - name: Delete an event subscription for a subscription.
          text: |
            az eventgrid event-subscription delete --name es2
        - name: Delete an event subscription for a resource group.
          text: |
            az eventgrid event-subscription delete -g rg1 --name es3
        - name: Delete an event subscription for a storage account.
          text: |
            az eventgrid event-subscription delete --resource-id "/subscriptions/55f3dcd4-cac7-43b4-990b-a139d62a1eb2/resourceGroups/kalstest/providers/microsoft.storage/storageaccounts/kalsegblob" --name es3
    """
helps['eventgrid event-subscription list'] = """
    type: command
    short-summary: List event subscriptions.
    examples:
        - name: List all event subscriptions for an Event Grid topic.
          text: |
            az eventgrid event-subscription list -g rg1 --topic-name topic1
        - name: List all event subscriptions for a storage account.
          text: |
            az eventgrid event-subscription list --resource-id /subscriptions/55f3dcd4-cac7-43b4-990b-a139d62a1eb2/resourceGroups/kalstest/providers/Microsoft.Storage/storageaccounts/kalsegblob
        - name: List all event subscriptions for a topic-type in a specific location (under the currently selected Azure subscription).
          text: |
            az eventgrid event-subscription list --topic-type Microsoft.Storage.StorageAccounts --location westus2
        - name: List all event subscriptions for a topic-type in a specific location under a specified resource group.
          text: |
            az eventgrid event-subscription list --topic-type Microsoft.Storage.StorageAccounts --location westus2 --resource-group kalstest
        - name: List all regional event subscriptions in a specific location (under the currently selected Azure subscription).
          text: |
            az eventgrid event-subscription list --location westus2
        - name: List all event subscriptions in a specific location under a specified resource group.
          text: |
            az eventgrid event-subscription list --location westus2 --resource-group kalstest
        - name: List all global event subscriptions (under the currently selected Azure subscription).
          text: |
            az eventgrid event-subscription list
        - name: List all global event subscriptions under the currently selected resource group.
          text: |
            az eventgrid event-subscription list --resource-group kalstest
    """
helps['eventgrid event-subscription show'] = """
    type: command
    short-summary: Get the details of an event subscription.
    examples:
        - name: Show the details of an event subscription for an Event Grid topic.
          text: |
            az eventgrid event-subscription show -g rg1 --topic-name topic1 --name es1
        - name: Show the details of an event subscription for a subscription.
          text: |
            az eventgrid event-subscription show --name es2
        - name: Show the details of an event subscription for a resource group.
          text: |
            az eventgrid event-subscription show -g rg1 --name es3
        - name: Show the details of an event subscription for a storage account.
          text: |
            az eventgrid event-subscription show --resource-id "/subscriptions/55f3dcd4-cac7-43b4-990b-a139d62a1eb2/resourceGroups/kalstest/providers/microsoft.storage/storageaccounts/kalsegblob" --name es3
    """
helps['eventgrid topic-type'] = """
    type: group
    short-summary: Get details for topic types.
    """
helps['eventgrid topic-type list'] = """
    type: command
    short-summary: List registered topic types.
    """
helps['eventgrid topic-type show'] = """
    type: command
    short-summary: Get the details for a topic type.
    """
helps['eventgrid topic-type list-event-types'] = """
    type: command
    short-summary: List the event types supported by a topic type.
    """
