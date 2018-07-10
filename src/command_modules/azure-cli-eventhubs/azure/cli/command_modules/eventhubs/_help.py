# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['eventhubs'] = """
    type: group
    short-summary: Manage Azure Event Hubs namespaces, eventhubs, consumergroups and geo recovery configurations - Alias
"""

helps['eventhubs namespace'] = """
    type: group
    short-summary: Manage Azure Event Hubs namespace and Authorizationrule
"""

helps['eventhubs namespace authorization-rule'] = """
    type: group
    short-summary: Manage Azure Event Hubs Authorizationrule for Namespace
"""

helps['eventhubs namespace authorization-rule keys'] = """
    type: group
    short-summary: Manage Azure Event Hubs Authorizationrule connection strings for Namespace
"""

helps['eventhubs eventhub'] = """
    type: group
    short-summary: Manage Azure Event Hubs eventhub and authorization-rule
"""

helps['eventhubs eventhub authorization-rule'] = """
    type: group
    short-summary: Manage Azure Service Bus Authorizationrule for Eventhub
"""

helps['eventhubs eventhub authorization-rule keys'] = """
    type: group
    short-summary: Manage Azure Authorizationrule connection strings for Eventhub
"""

helps['eventhubs eventhub consumer-group'] = """
    type: group
    short-summary: Manage Azure Event Hubs consumergroup
"""

helps['eventhubs georecovery-alias'] = """
    type:  group
    short-summary: Manage Azure Event Hubs Geo Recovery configuration Alias
"""

helps['eventhubs georecovery-alias authorization-rule'] = """
    type: group
    short-summary: Manage Azure Event Hubs Authorizationrule for Geo Recovery configuration Alias
"""

helps['eventhubs georecovery-alias authorization-rule keys'] = """
    type: group
    short-summary: Manage Azure Event Hubs Authorizationrule connection strings for Geo Recovery configuration Alias
"""

helps['eventhubs namespace exists'] = """
    type: command
    short-summary: check for the availability of the given name for the Namespace
    examples:
        - name: Create a new topic.
          text: az eventhubs namespace exists --name mynamespace
"""

helps['eventhubs namespace create'] = """
    type: command
    short-summary: Creates the Event Hubs Namespace
    examples:
        - name: Creates a new namespace.
          text: az eventhubs namespace create --resource-group myresourcegroup --name mynamespace --location westus
           --tags tag1=value1 tag2=value2 --sku Standard --is-auto-inflate-enabled False --maximum-throughput-units 30
"""

helps['eventhubs namespace update'] = """
    type: command
    short-summary: Updates the Event Hubs Namespace
    examples:
        - name: Update a new namespace.
          text: az eventhubs namespace update --resource-group myresourcegroup --name mynamespace --tags tag=value --is-auto-inflate-enabled True
"""

helps['eventhubs namespace show'] = """
    type: command
    short-summary: shows the Event Hubs Namespace Details
    examples:
        - name: shows the Namespace details.
          text: az eventhubs namespace show --resource-group myresourcegroup --name mynamespace
"""

helps['eventhubs namespace list'] = """
    type: command
    short-summary: Lists the Event Hubs Namespaces
    examples:
        - name: List the Event Hubs Namespaces by resource group.
          text: az eventhubs namespace list --resource-group myresourcegroup
        - name: Get the Namespaces by Subscription.
          text: az eventhubs namespace list
"""

helps['eventhubs namespace delete'] = """
    type: command
    short-summary: Deletes the Namespaces
    examples:
        - name: Deletes the Namespace
          text: az eventhubs namespace delete --resource-group myresourcegroup --name mynamespace
"""

helps['eventhubs namespace authorization-rule create'] = """
    type: command
    short-summary: Creates Authorizationrule for the given Namespace
    examples:
        - name: Creates Authorizationrule
          text: az eventhubs namespace authorization-rule create --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule --rights Send Listen
"""

helps['eventhubs namespace authorization-rule update'] = """
    type: command
    short-summary: Updates Authorizationrule for the given Namespace
    examples:
        - name: Updates Authorizationrule
          text: az eventhubs namespace authorization-rule update --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule --rights Send
"""

helps['eventhubs namespace authorization-rule show'] = """
    type: command
    short-summary: Shows the details of Authorizationrule
    examples:
        - name: Shows the details of Authorizationrule
          text: az eventhubs namespace authorization-rule show --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule
"""

helps['eventhubs namespace authorization-rule list'] = """
    type: command
    short-summary: Shows the list of Authorizationrule by Namespace
    examples:
        - name: Shows the list of Authorizationrule by Namespace
          text: az eventhubs namespace authorization-rule show --resource-group myresourcegroup --namespace-name mynamespace
"""

helps['eventhubs namespace authorization-rule keys list'] = """
    type: command
    short-summary: Shows the connection strings for namespace
    examples:
        - name: Shows the connection strings of Authorizationrule for the namespace.
          text: az eventhubs namespace authorization-rule list-keys --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule
"""

helps['eventhubs namespace authorization-rule keys renew'] = """
    type: command
    short-summary: Regenerate the connection strings of Authorizationrule for the namespace.
    examples:
        - name: Regenerate the connection strings of Authorizationrule for the namespace.
          text: az eventhubs namespace authorization-rule regenerate-keys --resource-group myresourcegroup
           --namespace-name mynamespace --name myauthorule --key PrimaryKey
"""

helps['eventhubs namespace authorization-rule delete'] = """
    type: command
    short-summary: Deletes the Authorizationrule of the namespace.
    examples:
        - name: Deletes the Authorizationrule of the namespace.
          text: az eventhubs namespace authorization-rule delete --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule
"""

helps['eventhubs eventhub create'] = """
    type: command
    short-summary: Creates the Event Hubs Eventhub
    examples:
        - name: Create a new Eventhub.
          text: az eventhubs eventhub create --resource-group myresourcegroup --namespace-name mynamespace --name myeventhub --message-retention 4 ---partition-count 15
"""

helps['eventhubs eventhub update'] = """
    type: command
    short-summary: Updates the Event Hubs Eventhub
    examples:
        - name: Updates a new Eventhub.
          text: az eventhubs eventhub update --resource-group myresourcegroup --namespace-name mynamespace --name myeventhub --message-retention 3 ---partition-count 12
"""

helps['eventhubs eventhub show'] = """
    type: command
    short-summary: shows the Eventhub Details
    examples:
        - name: Shows the Eventhub details.
          text: az eventhubs eventhub show --resource-group myresourcegroup --namespace-name mynamespace --name myeventhub
"""

helps['eventhubs eventhub list'] = """
    type: command
    short-summary: List the EventHub by Namepsace
    examples:
        - name: Get the Eventhubs by Namespace.
          text: az eventhubs eventhub list --resource-group myresourcegroup --namespace-name mynamespace
"""

helps['eventhubs eventhub delete'] = """
    type: command
    short-summary: Deletes the Eventhub
    examples:
        - name: Deletes the Eventhub
          text: az eventhubs eventhub delete --resource-group myresourcegroup --namespace-name mynamespace --name myeventhub
"""

helps['eventhubs eventhub authorization-rule create'] = """
    type: command
    short-summary: Creates Authorizationrule for the given Eventhub
    examples:
        - name: Creates Authorizationrule
          text: az eventhubs eventhub authorization-rule create --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myauthorule --rights Listen
"""

helps['eventhubs eventhub authorization-rule update'] = """
    type: command
    short-summary: Updates Authorizationrule for the given Eventhub
    examples:
        - name: Updates Authorizationrule
          text: az eventhubs eventhub authorization-rule update --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myauthorule --rights Send
"""

helps['eventhubs eventhub authorization-rule show'] = """
    type: command
    short-summary: shows the details of Authorizationrule
    examples:
        - name: shows the details of Authorizationrule
          text: az eventhubs eventhub authorization-rule show --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myauthorule
"""

helps['eventhubs eventhub authorization-rule list'] = """
    type: command
    short-summary: shows the list of Authorizationrule by Eventhub
    examples:
        - name: shows the list of Authorizationrule by Eventhub
          text: az eventhubs eventhub authorization-rule show --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub
"""

helps['eventhubs eventhub authorization-rule keys list'] = """
    type: command
    short-summary: Shows the connection strings of Authorizationrule for the Eventhub.
    examples:
        - name: Shows the connection strings of Authorizationrule for the eventhub.
          text: az eventhubs eventhub authorization-rule keys list --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myauthorule
"""

helps['eventhubs eventhub authorization-rule keys renew'] = """
    type: command
    short-summary: Regenerate the connection strings of Authorizationrule for the namespace.
    examples:
        - name: Regenerate the connection strings of Authorizationrule for the namespace.
          text: az eventhubs eventhub authorization-rule regenerate-keys --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myauthorule --key PrimaryKey
"""

helps['eventhubs eventhub authorization-rule delete'] = """
    type: command
    short-summary: Deletes the Authorizationrule of Eventhub.
    examples:
        - name: Deletes the Authorizationrule of Eventhub.
          text: az eventhubs eventhub authorization-rule delete --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myauthorule
"""

helps['eventhubs eventhub consumer-group create'] = """
    type: command
    short-summary: Creates the EventHub ConsumerGroup
    examples:
        - name: Create EventHub ConsumerGroup.
          text: az eventhubs eventhub consumer-group create --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myconsumergroup
"""

helps['eventhubs eventhub consumer-group update'] = """
    type: command
    short-summary: Updates the EventHub ConsumerGroup
    examples:
        - name: Updates a ConsumerGroup.
          text: az eventhubs eventhub consumer-group update --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myconsumergroup --user-metadata MyUserMetadata
"""

helps['eventhubs eventhub consumer-group show'] = """
    type: command
    short-summary: Shows the ConsumerGroup Details
    examples:
        - name: Shows the ConsumerGroup details.
          text: az eventhubs eventhub consumer-group show --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myconsumergroup
"""

helps['eventhubs eventhub consumer-group list'] = """
    type: command
    short-summary: List the ConsumerGroup by Eventhub
    examples:
        - name: Shows the ConsumerGroup by Eventhub.
          text: az eventhubs eventhub consumer-group get --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub
"""

helps['eventhubs eventhub consumer-group delete'] = """
    type: command
    short-summary: Deletes the ConsumerGroup
    examples:
        - name: Deletes the ConsumerGroup
          text: az eventhubs eventhub consumer-group delete --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myconsumergroup
"""

helps['eventhubs georecovery-alias exists'] = """
    type: command
    short-summary: Check the availability of Geo-Disaster Recovery Configuration Alias Name
    examples:
        - name: Check the availability of Geo-Disaster Recovery Configuration Alias Name
          text: az eventhubs georecovery-alias check-name-availability --resource-group myresourcegroup --namespace-name primarynamespace --alias myaliasname
"""

helps['eventhubs georecovery-alias set'] = """
    type: command
    short-summary: Sets a Geo-Disaster Recovery Configuration Alias for the give Namespace
    examples:
        - name: Sets Geo-Disaster Recovery Configuration Alias for the give Namespace
          text: az eventhubs georecovery-alias set --resource-group myresourcegroup --namespace-name primarynamespace --alias myaliasname --partner-namespace resourcearmid
"""

helps['eventhubs georecovery-alias show'] = """
    type: command
    short-summary: shows properties of Geo-Disaster Recovery Configuration Alias for Primay or Secondary Namespace
    examples:
        - name: Shows properties of Geo-Disaster Recovery Configuration Alias of the Primary Namespace
          text: az eventhubs georecovery-alias show --resource-group myresourcegroup --namespace-name primarynamespace --alias myaliasname
        - name: Shows properties of Geo-Disaster Recovery Configuration Alias of the Secondary Namespace
          text: az eventhubs georecovery-alias show --resource-group myresourcegroup --namespace-name secondarynamespace --alias myaliasname
"""

helps['eventhubs georecovery-alias authorization-rule show'] = """
    type: command
    short-summary: Show properties of Event Hubs Geo-Disaster Recovery Configuration Alias and Namespace Authorizationrule
    examples:
        - name: Show properties Authorizationrule by Event Hubs Namespace
          text: az eventhubs georecovery-alias authorization-rule show --resource-group myresourcegroup --namespace-name mynamespace
"""

helps['eventhubs georecovery-alias authorization-rule list'] = """
    type: command
    short-summary: List of Authorizationrule by Event Hubs Namespace
    examples:
        - name: List of Authorizationrule by Event Hubs Namespace
          text: az eventhubs georecovery-alias authorization-rule list --resource-group myresourcegroup --namespace-name mynamespace
"""

helps['eventhubs georecovery-alias authorization-rule keys list'] = """
    type: command
    short-summary: Shows the keys and connection strings of Authorizationrule for the Event Hubs Namespace
    examples:
        - name: Shows the keys and connection strings of Authorizationrule for the namespace.
          text: az eventhubs georecovery-alias authorization-rule keys list --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule
"""

helps['eventhubs georecovery-alias break-pair'] = """
    type: command
    short-summary: Disables Geo-Disaster Recovery Configuration Alias and stops replicating changes from primary to secondary namespaces
    examples:
        - name:  Disables Geo-Disaster Recovery Configuration Alias and stops replicating changes from primary to secondary namespaces
          text: az eventhubs georecovery-alias break-pair --resource-group myresourcegroup --namespace-name primarynamespace --alias myaliasname
"""

helps['eventhubs georecovery-alias fail-over'] = """
    type: command
    short-summary: Invokes Geo-Disaster Recovery Configuration Alias to point to the secondary namespace
    examples:
        - name:  Invokes GEO DR failover and reconfigure the alias to point to the secondary namespace
          text: az eventhubs georecovery-alias fail-over --resource-group myresourcegroup --namespace-name secondarynamespace --alias myaliasname
"""

helps['eventhubs georecovery-alias delete'] = """
    type: command
    short-summary: Delete Geo-Disaster Recovery Configuration Alias
    examples:
        - name: Delete Geo-Disaster Recovery Configuration Alias
          text: az eventhubs georecovery-alias delete --resource-group myresourcegroup --namespace-name secondarynamespace --alias myaliasname
"""
