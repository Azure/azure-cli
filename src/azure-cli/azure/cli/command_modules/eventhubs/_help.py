# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['eventhubs'] = """
type: group
short-summary: Manage Azure Event Hubs namespaces, eventhubs, consumergroups and geo recovery configurations - Alias
"""

helps['eventhubs eventhub'] = """
type: group
short-summary: Manage Azure EventHubs eventhub and authorization-rule
"""

helps['eventhubs eventhub authorization-rule'] = """
type: group
short-summary: Manage Azure Service Bus Authorizationrule for Eventhub
"""

helps['eventhubs eventhub authorization-rule create'] = """
type: command
short-summary: Creates Authorizationrule for the given Eventhub
examples:
  - name: Creates Authorizationrule
    text: az eventhubs eventhub authorization-rule create --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myauthorule --rights Listen
"""

helps['eventhubs eventhub authorization-rule delete'] = """
type: command
short-summary: Deletes the Authorizationrule of Eventhub.
examples:
  - name: Deletes the Authorizationrule of Eventhub.
    text: az eventhubs eventhub authorization-rule delete --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myauthorule
"""

helps['eventhubs eventhub authorization-rule keys'] = """
type: group
short-summary: Manage Azure Authorizationrule connection strings for Eventhub
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
    text: az eventhubs eventhub authorization-rule keys renew --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myauthorule --key PrimaryKey
"""

helps['eventhubs eventhub authorization-rule list'] = """
type: command
short-summary: shows the list of Authorization-rules by Eventhub
examples:
  - name: shows the list of Authorization-rules by Eventhub
    text: az eventhubs eventhub authorization-rule list --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub
"""

helps['eventhubs eventhub authorization-rule show'] = """
type: command
short-summary: shows the details of Authorizationrule
examples:
  - name: shows the details of Authorizationrule
    text: az eventhubs eventhub authorization-rule show --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myauthorule
"""

helps['eventhubs eventhub authorization-rule update'] = """
type: command
short-summary: Updates Authorizationrule for the given Eventhub
examples:
  - name: Updates Authorizationrule
    text: az eventhubs eventhub authorization-rule update --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myauthorule --rights Send
"""

helps['eventhubs eventhub consumer-group'] = """
type: group
short-summary: Manage Azure Event Hubs consumergroup
"""

helps['eventhubs eventhub consumer-group create'] = """
type: command
short-summary: Creates the EventHub ConsumerGroup
examples:
  - name: Create EventHub ConsumerGroup.
    text: az eventhubs eventhub consumer-group create --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myconsumergroup
"""

helps['eventhubs eventhub consumer-group delete'] = """
type: command
short-summary: Deletes the ConsumerGroup
examples:
  - name: Deletes the ConsumerGroup
    text: az eventhubs eventhub consumer-group delete --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myconsumergroup
"""

helps['eventhubs eventhub consumer-group list'] = """
type: command
short-summary: List the ConsumerGroup by Eventhub
examples:
  - name: List the ConsumerGroup by Eventhub.
    text: az eventhubs eventhub consumer-group list --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub
"""

helps['eventhubs eventhub consumer-group show'] = """
type: command
short-summary: Shows the ConsumerGroup Details
examples:
  - name: Shows the ConsumerGroup details.
    text: az eventhubs eventhub consumer-group show --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myconsumergroup
"""

helps['eventhubs eventhub consumer-group update'] = """
type: command
short-summary: Updates the EventHub ConsumerGroup
examples:
  - name: Updates a ConsumerGroup.
    text: az eventhubs eventhub consumer-group update --resource-group myresourcegroup --namespace-name mynamespace --eventhub-name myeventhub --name myconsumergroup --user-metadata MyUserMetadata
"""

helps['eventhubs eventhub create'] = """
type: command
short-summary: Creates the EventHubs Eventhub
examples:
  - name: Create a new Eventhub.
    text: az eventhubs eventhub create --resource-group myresourcegroup --namespace-name mynamespace --name myeventhub --message-retention 4 --partition-count 15
"""

helps['eventhubs eventhub delete'] = """
type: command
short-summary: Deletes the Eventhub
examples:
  - name: Deletes the Eventhub
    text: az eventhubs eventhub delete --resource-group myresourcegroup --namespace-name mynamespace --name myeventhub
"""

helps['eventhubs eventhub list'] = """
type: command
short-summary: List the EventHub by Namespace
examples:
  - name: Get the Eventhubs by Namespace.
    text: az eventhubs eventhub list --resource-group myresourcegroup --namespace-name mynamespace
"""

helps['eventhubs eventhub show'] = """
type: command
short-summary: shows the Eventhub Details
examples:
  - name: Shows the Eventhub details.
    text: az eventhubs eventhub show --resource-group myresourcegroup --namespace-name mynamespace --name myeventhub
"""

helps['eventhubs eventhub update'] = """
type: command
short-summary: Updates the EventHubs Eventhub
examples:
  - name: Updates a new Eventhub.
    text: az eventhubs eventhub update --resource-group myresourcegroup --namespace-name mynamespace --name myeventhub --message-retention 3 --partition-count 12
  - name: Updates the EventHubs Eventhub (autogenerated)
    text: az eventhubs eventhub update --name myeventhub --namespace-name mynamespace --partition-count 12 --resource-group myresourcegroup
    crafted: true
  - name: Updates the EventHubs Eventhub (autogenerated)
    text: az eventhubs eventhub update --message-retention 3 --name myeventhub --namespace-name mynamespace --resource-group myresourcegroup --subscription MySubscription
    crafted: true
"""

helps['eventhubs georecovery-alias'] = """
type: group
short-summary: Manage Azure EventHubs Geo Recovery configuration Alias
"""

helps['eventhubs georecovery-alias authorization-rule'] = """
type: group
short-summary: Manage Azure EventHubs Authorizationrule for Geo Recovery configuration Alias
"""

helps['eventhubs georecovery-alias authorization-rule keys'] = """
type: group
short-summary: Manage Azure Event Hubs Authorizationrule connection strings for Geo Recovery configuration Alias
"""

helps['eventhubs georecovery-alias authorization-rule keys list'] = """
type: command
short-summary: Shows the keys and connection strings of Authorizationrule for the EventHubs Namespace
examples:
  - name: Shows the keys and connection strings of Authorizationrule for the namespace.
    text: az eventhubs georecovery-alias authorization-rule keys list --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule --alias myaliasname
"""

helps['eventhubs georecovery-alias authorization-rule list'] = """
type: command
short-summary: List of Authorizationrule by EventHubs Namespace
examples:
  - name: List of Authorizationrule by EventHubs Namespace
    text: az eventhubs georecovery-alias authorization-rule list --resource-group myresourcegroup --namespace-name mynamespace --alias myaliasname
"""

helps['eventhubs georecovery-alias authorization-rule show'] = """
type: command
short-summary: Show properties of EventHubs Geo-Disaster Recovery Configuration Alias and Namespace Authorizationrule
examples:
  - name: Show properties Authorizationrule by EventHubs Namespace
    text: az eventhubs georecovery-alias authorization-rule show --resource-group myresourcegroup --namespace-name mynamespace
"""

helps['eventhubs georecovery-alias break-pair'] = """
type: command
short-summary: Disables Geo-Disaster Recovery Configuration Alias and stops replicating changes from primary to secondary namespaces
examples:
  - name: Disables Geo-Disaster Recovery Configuration Alias and stops replicating changes from primary to secondary namespaces
    text: az eventhubs georecovery-alias break-pair --resource-group myresourcegroup --namespace-name primarynamespace --alias myaliasname
"""

helps['eventhubs georecovery-alias delete'] = """
type: command
short-summary: Delete Geo-Disaster Recovery Configuration Alias
examples:
  - name: Delete Geo-Disaster Recovery Configuration Alias
    text: az eventhubs georecovery-alias delete --resource-group myresourcegroup --namespace-name secondarynamespace --alias myaliasname
"""

helps['eventhubs georecovery-alias exists'] = """
type: command
short-summary: Check the availability of Geo-Disaster Recovery Configuration Alias Name
examples:
  - name: Check the availability of Geo-Disaster Recovery Configuration Alias Name
    text: az eventhubs georecovery-alias exists --resource-group myresourcegroup --namespace-name primarynamespace --alias myaliasname
"""

helps['eventhubs georecovery-alias fail-over'] = """
type: command
short-summary: Invokes Geo-Disaster Recovery Configuration Alias to point to the secondary namespace
examples:
  - name: Invokes GEO DR failover and reconfigure the alias to point to the secondary namespace
    text: az eventhubs georecovery-alias fail-over --resource-group myresourcegroup --namespace-name secondarynamespace --alias myaliasname
"""

helps['eventhubs georecovery-alias set'] = """
type: command
short-summary: Sets a Geo-Disaster Recovery Configuration Alias for the give Namespace
examples:
  - name: Sets Geo-Disaster Recovery Configuration Alias for the give Namespace
    text: az eventhubs georecovery-alias set --resource-group myresourcegroup --namespace-name primarynamespace --alias myaliasname --partner-namespace resourcearmid
  - name: Sets a Geo-Disaster Recovery Configuration Alias for the give Namespace (autogenerated)
    text: az eventhubs georecovery-alias set --alias myaliasname --namespace-name primarynamespace --partner-namespace resourcearmid --resource-group myresourcegroup --subscription MySubscription
    crafted: true
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

helps['eventhubs namespace'] = """
type: group
short-summary: Manage Azure EventHubs namespace and Authorizationrule
"""

helps['eventhubs namespace authorization-rule'] = """
type: group
short-summary: Manage Azure EventHubs Authorizationrule for Namespace
"""

helps['eventhubs namespace authorization-rule create'] = """
type: command
short-summary: Creates Authorizationrule for the given Namespace
examples:
  - name: Creates Authorizationrule
    text: az eventhubs namespace authorization-rule create --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule --rights Send Listen
"""

helps['eventhubs namespace authorization-rule delete'] = """
type: command
short-summary: Deletes the Authorizationrule of the namespace.
examples:
  - name: Deletes the Authorizationrule of the namespace.
    text: az eventhubs namespace authorization-rule delete --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule
"""

helps['eventhubs namespace authorization-rule keys'] = """
type: group
short-summary: Manage Azure EventHubs Authorizationrule connection strings for Namespace
"""

helps['eventhubs namespace authorization-rule keys list'] = """
type: command
short-summary: Shows the connection strings for namespace
examples:
  - name: Shows the connection strings of Authorizationrule for the namespace.
    text: az eventhubs namespace authorization-rule keys list --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule
"""

helps['eventhubs namespace authorization-rule keys renew'] = """
type: command
short-summary: Regenerate the connection strings of Authorizationrule for the namespace.
examples:
  - name: Regenerate the connection strings of Authorizationrule for the namespace.
    text: az eventhubs namespace authorization-rule keys renew --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule --key PrimaryKey
"""

helps['eventhubs namespace authorization-rule list'] = """
type: command
short-summary: Shows the list of Authorizationrule by Namespace
examples:
  - name: Shows the list of Authorizationrule by Namespace
    text: az eventhubs namespace authorization-rule list --resource-group myresourcegroup --namespace-name mynamespace
"""

helps['eventhubs namespace authorization-rule show'] = """
type: command
short-summary: Shows the details of Authorizationrule
examples:
  - name: Shows the details of Authorizationrule
    text: az eventhubs namespace authorization-rule show --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule
"""

helps['eventhubs namespace authorization-rule update'] = """
type: command
short-summary: Updates Authorizationrule for the given Namespace
examples:
  - name: Updates Authorizationrule
    text: az eventhubs namespace authorization-rule update --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule --rights Send
"""

helps['eventhubs namespace create'] = """
type: command
short-summary: Creates the EventHubs Namespace
examples:
  - name: Creates a new namespace.
    text: az eventhubs namespace create --resource-group myresourcegroup --name mynamespace --location westus --tags tag1=value1 tag2=value2 --sku Standard --enable-auto-inflate --maximum-throughput-units 20
"""

helps['eventhubs namespace delete'] = """
type: command
short-summary: Deletes the Namespaces
examples:
  - name: Deletes the Namespace
    text: az eventhubs namespace delete --resource-group myresourcegroup --name mynamespace
"""

helps['eventhubs namespace exists'] = """
type: command
short-summary: check for the availability of the given name for the Namespace
examples:
  - name: Create a new topic.
    text: az eventhubs namespace exists --name mynamespace
  - name: check for the availability of the given name for the Namespace (autogenerated)
    text: az eventhubs namespace exists --name mynamespace --subscription MySubscription
    crafted: true
"""

helps['eventhubs namespace list'] = """
type: command
short-summary: Lists the EventHubs Namespaces
examples:
  - name: List the Event Hubs Namespaces by resource group.
    text: az eventhubs namespace list --resource-group myresourcegroup
  - name: Get the Namespaces by Subscription.
    text: az eventhubs namespace list
"""

helps['eventhubs namespace network-rule'] = """
type: group
short-summary: Manage Azure EventHubs networkruleset for namespace
"""

helps['eventhubs namespace network-rule add'] = """
type: command
short-summary: Add a network rule for a namespace.
examples:
  - name: add a VirtualNetwork rule in NetworkruleSet for a namespace
    text: az eventhubs namespace network-rule add --resource-group myresourcegroup --namespace-name mynamespace --subnet /subscriptions/{subscriptionid}/resourcegroups/{resourcegroupname}/providers/Microsoft.Network/virtualNetworks/{virtualnetworkname}/subnets/{subnetname} --ignore-missing-endpoint True
  - name: add a IP rule in NetworkruleSet for a namespace
    text: az eventhubs namespace network-rule add --resource-group myresourcegroup --namespace-name mynamespace --ip-address 10.6.0.0/24 --action Allow
  - name: Add a network rule for a namespace. (autogenerated)
    text: az eventhubs namespace network-rule add --action Allow --ignore-missing-endpoint true --namespace-name mynamespace --resource-group myresourcegroup --subnet /subscriptions/{subscriptionid}/resourcegroups/{resourcegroupname}/providers/Microsoft.Network/virtualNetworks/{virtualnetworkname}/subnets/{subnetname} --subscription MySubscription --vnet-name MyVnet
    crafted: true
"""

helps['eventhubs namespace network-rule list'] = """
type: command
short-summary: Show properties of Network rule of the given Namespace.
examples:
  - name: Show properties of Network rule of the given Namespace
    text: az eventhubs namespace network-rule list --resource-group myresourcegroup --namespace-name mynamespace
"""

helps['eventhubs namespace network-rule remove'] = """
type: command
short-summary: Remove network rule for a namespace
examples:
  - name: remove VirtualNetwork rule from NetworkruleSet for a namespace
    text: az eventhubs namespace network-rule remove --resource-group myresourcegroup --namespace-name mynamespace --subnet /subscriptions/{subscriptionid}/resourcegroups/{resourcegroupname}/providers/Microsoft.Network/virtualNetworks/{virtualnetworkname}/subnets/{subnetname}
  - name: remove IP rule from NetworkruleSet for a namespace
    text: az eventhubs namespace network-rule remove --resource-group myresourcegroup --namespace-name mynamespace --ip-address 10.6.0.0/24
"""

helps['eventhubs namespace show'] = """
type: command
short-summary: shows the Event Hubs Namespace Details
examples:
  - name: shows the Namespace details.
    text: az eventhubs namespace show --resource-group myresourcegroup --name mynamespace
"""

helps['eventhubs namespace update'] = """
type: command
short-summary: Updates the EventHubs Namespace
examples:
  - name: Update a new namespace.
    text: az eventhubs namespace update --resource-group myresourcegroup --name mynamespace --tags tag=value --enable-auto-inflate True
"""

helps['eventhubs cluster'] = """
type: group
short-summary: Manage Azure EventHubs Clusters
"""

helps['eventhubs cluster create'] = """
type: command
short-summary: Create EventHubs Cluster
examples:
  - name: Create a new cluster.
    text: az eventhubs cluster create --resource-group myresourcegroup --name mycluster --location mylocation --capacity 1 --tags tag=value
"""

helps['eventhubs cluster update'] = """
type: command
short-summary: Update tags of EventHubs Cluster
examples:
  - name: Update tags of a existing cluster.
    text: az eventhubs cluster update --resource-group myresourcegroup --name mycluster --tags tag=value
"""

helps['eventhubs cluster available-region'] = """
type: command
short-summary: List the quantity of available pre-provisioned Event Hubs Clusters, indexed by Azure region.
examples:
  - name: List of available pre-provisioned Event Hubs Clusters, indexed by Azure region.
    text: az eventhubs cluster available-region
"""

helps['eventhubs cluster show'] = """
type: command
short-summary: Get the resource description of the specified Event Hubs Cluster.
examples:
  - name: Get the resource description of the specified Event Hubs Cluster.
    text: az eventhubs cluster show --resource-group myresourcegroup --name mycluster
"""

helps['eventhubs cluster delete'] = """
type: command
short-summary: Delete an existing Event Hubs Cluster.
examples:
  - name: Delete an existing Event Hubs Cluster.
    text: az eventhubs cluster delete --resource-group myresourcegroup --name mycluster
"""

helps['eventhubs cluster list'] = """
type: command
short-summary: List the available Event Hubs Clusters within an ARM resource group.
examples:
  - name: List the available Event Hubs Clusters within an ARM resource group.
    text: az eventhubs cluster list --resource-group myresourcegroup
"""

helps['eventhubs cluster namespace'] = """
type: group
short-summary: Manage Azure EventHubs Cluster for namespace
"""

helps['eventhubs cluster namespace list'] = """
type: command
short-summary: List of Namespaces within given Cluster.
examples:
  - name: List of Namespaces within given Cluster.
    text: az eventhubs cluster namespace list --resource-group myresourcegroup --name mycluster
"""

helps['eventhubs cluster wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the Cluster operation is completed.
"""
