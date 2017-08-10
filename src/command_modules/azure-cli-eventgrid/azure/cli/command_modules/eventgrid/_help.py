# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.help_files import helps


helps['eventgrid'] = """
    type: group
    short-summary: Manage Azure EventGrid Topics and Event Subscriptions.
    """
helps['eventgrid topic'] = """
    type: group
    short-summary: Manage topics and their event subscriptions.
    """
helps['eventgrid topic create'] = """
    type: command
    short-summary: Create a topic.
    examples:
        - name: Create a new topic
          text: az eventgrid topic create -g rg1 --name topic1
    """
helps['eventgrid topic delete'] = """
    type: command
    short-summary: Delete a topic.
    """
helps['eventgrid topic list'] = """
    type: command
    short-summary: List all topics in a subscription or resource group.
    """
helps['eventgrid topic show'] = """
    type: command
    short-summary: Get properties of a topic.
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
        - name: Create a new event subscription with default filters
          text: az eventgrid topic event-subscription create -g rg1 --topic-name topic1 --name es1 --endpoint https://<yourfunction>.azurewebsites.net/api/f1?code=<code>
        - name: Create a new event subscription with a filter specifying a subject prefix
          text: az eventgrid topic event-subscription create -g rg1 --topic-name topic1 --name es1 --endpoint https://<yourfunction>.azurewebsites.net/api/f1?code=<code> --subject-begins-with mysubject_prefix
        - name: Create a new event subscription with default filters and with additional labels
          text: az eventgrid topic event-subscription create -g rg1 --topic-name topic1 --name es1 --endpoint https://<yourfunction>.azurewebsites.net/api/f1?code=<code> --labels Finance HR
    """
helps['eventgrid topic event-subscription delete'] = """
    type: command
    short-summary: Delete an event subscription for a topic.
    """
helps['eventgrid topic event-subscription list'] = """
    type: command
    short-summary: List the event subscriptions for a topic.
    """
helps['eventgrid topic event-subscription show'] = """
    type: command
    short-summary: Get the properties of an event subscription for a topic.
    """
helps['eventgrid topic event-subscription show-endpoint-url'] = """
    type: command
    short-summary: Get the full endpoint URL of an event subscription for a topic.
    """
helps['eventgrid event-subscription'] = """
    type: group
    short-summary: Manage event subscriptions for a subscription or resource group.
    """
helps['eventgrid event-subscription create'] = """
    type: command
    short-summary: Create a new event subscription to a subscription or resource group.
    examples:
        - name: Create a new event subscription to a subscription, using default filters.
          text: az eventgrid event-subscription create --name es2 --endpoint https://<yourfunction>.azurewebsites.net/api/f1?code=<code>
        - name: Create a new event subscription to a resource group, using default filters.
          text: az eventgrid event-subscription create -g rg1 --name es3 --endpoint https://<yourfunction>.azurewebsites.net/api/f1?code=<code>
        - name: Create a new event subscription to a subscription, with a filter specifying a subject prefix
          text: az eventgrid event-subscription create --name es4 --endpoint https://<yourfunction>.azurewebsites.net/api/f1?code=<code> --subject-begins-with mysubject_prefix
        - name: Create a new event subscription to a resource group, with a filter specifying a subject suffix
          text: az eventgrid event-subscription create -g rg2 --name es5 --endpoint https://<yourfunction>.azurewebsites.net/api/f1?code=<code> --subject-ends-with mysubject_suffix

    """
helps['eventgrid event-subscription delete'] = """
    type: command
    short-summary: Delete an event subscription for a subscription or resource group.
    """
helps['eventgrid event-subscription list'] = """
    type: command
    short-summary: List the event subscriptions for a subscription or resource group.
    """
helps['eventgrid event-subscription show'] = """
    type: command
    short-summary: Get the properties of an event subscription for a subscription or resource group.
    """
helps['eventgrid event-subscription show-endpoint-url'] = """
    type: command
    short-summary: Get the full endpoint URL of an event subscription for a a subscription or resource group.
    """
helps['eventgrid resource'] = """
    type: group
    short-summary: Manage event subscriptions for a resource.
    """
helps['eventgrid resource event-subscription'] = """
    type: group
    short-summary: Manage event subscriptions for a resource.
    """
helps['eventgrid resource event-subscription create'] = """
    type: command
    short-summary: Create a new event subscription to a resource.
    examples:
        - name: Create a new event subscription to subscribe to events from an Azure Event Hubs namespace, using default filters
          text: az eventgrid resource event-subscription create -g rg1 --provider-namespace Microsoft.EventHub --resource-type namespaces --resource-name EHNamespace1 --name es1 --endpoint https://<yourfunction>.azurewebsites.net/api/f1?code=<code>
        - name: Create a new event subscription to subscribe to events from an Azure Storage account, using a filter specifying a subject prefix
          text: az eventgrid resource event-subscription create -g rg1 --provider-namespace Microsoft.Storage --resource-type storageAccounts --resource-name sa1 --name es1 --endpoint https://<yourfunction>.azurewebsites.net/api/f1?code=<code> --subject-begins-with mysubject_prefix
        - name: Create a new event subscription to subscribe to events from an Azure Event Hubs namespace, using default filters and additional labels
          text: az eventgrid resource event-subscription create -g rg1 --provider-namespace Microsoft.EventHub --resource-type namespaces --resource-name EHNamespace1 --name es1 --endpoint https://<yourfunction>.azurewebsites.net/api/f1?code=<code> --labels Finance HR
    """
helps['eventgrid resource event-subscription delete'] = """
    type: command
    short-summary: Delete an event subscription for a resource.
    """
helps['eventgrid resource event-subscription list'] = """
    type: command
    short-summary: List the event subscriptions for a resource.
    """
helps['eventgrid resource event-subscription show'] = """
    type: command
    short-summary: Get the properties of an event subscription for a resource.
    """
helps['eventgrid resource event-subscription show-endpoint-url'] = """
    type: command
    short-summary: Get the full endpoint URL of an event subscription for a resource.
    """
helps['eventgrid topic-type'] = """
    type: group
    short-summary: Get information about topic types.
    """
helps['eventgrid topic-type list'] = """
    type: command
    short-summary: List all registered topic types.
    """
helps['eventgrid topic-type show'] = """
    type: command
    short-summary: Get the properties of a topic type.
    """
helps['eventgrid topic-type list-event-types'] = """
    type: command
    short-summary: List the event types supported by a topic type.
    """
