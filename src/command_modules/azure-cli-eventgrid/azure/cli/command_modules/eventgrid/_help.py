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
          text: az eventgrid topic create -g rg1 --name topic1
    """
helps['eventgrid topic delete'] = """
    type: command
    short-summary: Delete a topic.
    """
helps['eventgrid topic list'] = """
    type: command
    short-summary: List available topics.
    """
helps['eventgrid topic show'] = """
    type: command
    short-summary: Get the details of a topic.
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
helps['eventgrid topic event-subscription'] = """
    type: group
    short-summary: Manage event subscriptions for a topic.
    """
helps['eventgrid topic event-subscription create'] = """
    type: command
    short-summary: Create a new event subscription to a topic.
    examples:
        - name: Create a new event subscription with default filters.
          text: |
            az eventgrid topic event-subscription create -g rg1 --topic-name topic1 --name es1 \\
                --endpoint https://contoso.azurewebsites.net/api/f1?code=code
        - name: Create a new event subscription with a filter specifying a subject prefix.
          text: |
            az eventgrid topic event-subscription create -g rg1 --topic-name topic1 --name es1 \\
                --endpoint https://contoso.azurewebsites.net/api/f1?code=code \\
                --subject-begins-with mysubject_prefix
        - name: Create a new event subscription with default filters and additional labels.
          text: |
            az eventgrid topic event-subscription create -g rg1 --topic-name topic1 --name es1 \\
                --endpoint https://contoso.azurewebsites.net/api/f1?code=code \\
                --labels Finance HR
        - name: Create a new event subscription with an EventHub as a destination.
          text: |
            az eventgrid topic event-subscription create -g rg1 --topic-name topic1 --name es1 \\
                --endpoint-type eventhub \\
                --endpoint /subscriptions/55f3dcd4-cac7-43b4-990b-a139d62a1eb2/resourceGroups/TestRG/providers/Microsoft.EventHub/namespaces/ContosoNamespace/eventhubs/EH1 \\
                --labels Finance HR
    """
helps['eventgrid topic event-subscription delete'] = """
    type: command
    short-summary: Delete an event subscription for a topic.
    """
helps['eventgrid topic event-subscription list'] = """
    type: command
    short-summary: List event subscriptions for a topic.
    """
helps['eventgrid topic event-subscription show'] = """
    type: command
    short-summary: Get the details of an event subscription for a topic.
    """
helps['eventgrid topic event-subscription show-endpoint-url'] = """
    type: command
    short-summary: Get the full endpoint URL of an event subscription for a topic.
    """
helps['eventgrid event-subscription'] = """
    type: group
    short-summary: Manage event subscriptions.
    """
helps['eventgrid event-subscription create'] = """
    type: command
    short-summary: Create a new event subscription for an Azure subscription or resource group.
    examples:
        - name: Create a new event subscription for a subscription, using default filters.
          text: |
            az eventgrid event-subscription create --name es2 \\
                --endpoint https://contoso.azurewebsites.net/api/f1?code=code
        - name: Create a new event subscription for a resource group, using default filters.
          text: |
            az eventgrid event-subscription create -g rg1 --name es3 \\
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
helps['eventgrid event-subscription delete'] = """
    type: command
    short-summary: Delete an event subscription.
    """
helps['eventgrid event-subscription list'] = """
    type: command
    short-summary: List event subscriptions.
    """
helps['eventgrid event-subscription show'] = """
    type: command
    short-summary: Get the details of an event subscription.
    """
helps['eventgrid event-subscription show-endpoint-url'] = """
    type: command
    short-summary: Get the full endpoint URL of an event subscription.
    """
helps['eventgrid resource'] = """
    type: group
    short-summary: Manage Azure Event Grid resources.
    """
helps['eventgrid resource event-subscription'] = """
    type: group
    short-summary: Manage event subscriptions for a resource.
    """
helps['eventgrid resource event-subscription create'] = """
    type: command
    short-summary: Create a new event subscription for a resource.
    examples:
        - name: Create a new event subscription to subscribe to events from an Azure Event Hubs namespace, using default filters.
          text: |
            az eventgrid resource event-subscription create -g rg1 --provider-namespace Microsoft.EventHub --resource-type namespaces \\
                --resource-name EHNamespace1 --name es1 --endpoint https://contoso.azurewebsites.net/api/f1?code=code
        - name: Create a new event subscription to subscribe to events from an Azure Storage account, using a filter specifying a subject prefix.
          text: az eventgrid resource event-subscription create -g rg1 --provider-namespace Microsoft.Storage --resource-type storageAccounts \\
                --resource-name sa1 --name es1 --endpoint https://contoso.azurewebsites.net/api/f1?code=code --subject-begins-with mysubject_prefix
        - name: Create a new event subscription to subscribe to events from an Azure Event Hubs namespace, using default filters and additional labels.
          text: az eventgrid resource event-subscription create -g rg1 --provider-namespace Microsoft.EventHub --resource-type namespaces \\
                --resource-name EHNamespace1 --name es1 --endpoint https://contoso.azurewebsites.net/api/f1?code=code --labels Finance HR
    """
helps['eventgrid resource event-subscription delete'] = """
    type: command
    short-summary: Delete an event subscription from a resource.
    """
helps['eventgrid resource event-subscription list'] = """
    type: command
    short-summary: List the event subscriptions for a resource.
    """
helps['eventgrid resource event-subscription show'] = """
    type: command
    short-summary: Get the details of an event subscription for a resource.
    """
helps['eventgrid resource event-subscription show-endpoint-url'] = """
    type: command
    short-summary: Get the full endpoint URL of an event subscription for a resource.
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
