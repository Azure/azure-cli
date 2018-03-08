# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
# pylint: disable=unused-import

from knack.help_files import helps

helps['servicebus'] = """
    type: group
    short-summary: Manage Azure Service Bus namespaces, queues, topics, subscriptions, rules and geo disaster recovery configurations - alias
"""

helps['servicebus namespace'] = """
    type: group
    short-summary: Manage Azure Service Bus Namespace
"""

helps['servicebus namespace authorization-rule'] = """
    type: group
    short-summary: Manage Azure Service Bus Namespace Authorization Rule
"""

helps['servicebus namespace authorization-rule keys'] = """
    type: group
    short-summary: Manage Azure Authorization Rule connection strings for Namespace
"""

helps['servicebus queue'] = """
    type: group
    short-summary: Manage Azure Service Bus Queue and authorization rule
"""

helps['servicebus queue authorization-rule'] = """
    type: group
    short-summary: Manage Azure Service Bus Queue Authorization Rule
"""

helps['servicebus queue authorization-rule keys'] = """
    type: group
    short-summary: Manage Azure Authorization Rule connection strings for Service Bus Queue
"""

helps['servicebus topic'] = """
    type: group
    short-summary: Manage Azure Service Bus Topic and authorization rule
"""

helps['servicebus topic authorization-rule'] = """
    type: group
    short-summary: Manage Azure Service Bus Topic Authorization Rule
"""

helps['servicebus topic authorization-rule keys'] = """
    type: group
    short-summary: Manage Azure Authorization Rule connection strings for Service Bus Topic
"""

helps['servicebus topic subscription'] = """
    type: group
    short-summary: Manage Azure Service Bus Subscription
"""

helps['servicebus topic subscription rule'] = """
    type: group
    short-summary: Manage Azure Service Bus Rule
"""

helps['servicebus georecovery-alias'] = """
    type: group
    short-summary: Manage Azure Service Bus Geo Disaster Recovery Configuration - Alias
"""

helps['servicebus georecovery-alias authorization-rule'] = """
    type: group
    short-summary: Manage Azure Service Bus Authorization Rule for Namespace with GeoDRAlias
"""

helps['servicebus georecovery-alias authorization-rule keys'] = """
    type: group
    short-summary: Manage Azure Authorization Rule connection strings for Service Bus Namespace
"""

helps['servicebus namespace exists'] = """
    type: command
    short-summary: check for the availability of the given name for the Namespace
    examples:
        - name: check for the availability of mynamespace for the Namespace
          text: az servicebus namespace exists --name mynamespace
"""

helps['servicebus namespace create'] = """
    type: command
    short-summary: Creates a Service Bus Namespace
    examples:
        - name: Create a Service Bus Namespace.
          text: az servicebus namespace create --resource-group myresourcegroup --name mynamespace --location westus --tags tag1=value1 tag2=value2 --sku Standard
"""

helps['servicebus namespace update'] = """
    type: command
    short-summary: Updates a Service Bus Namespace
    examples:
        - name: Updates a Service Bus Namespace.
          text: az servicebus namespace update --resource-group myresourcegroup --name mynamespace --tags tag=value
"""

helps['servicebus namespace show'] = """
    type: command
    short-summary: Shows the Service Bus Namespace details
    examples:
        - name: shows the Namespace details.
          text: az servicebus namespace show --resource-group myresourcegroup --name mynamespace
"""

helps['servicebus namespace list'] = """
    type: command
    short-summary: List the Service Bus Namespaces
    examples:
        - name: Get the Service Bus Namespaces by resource group
          text: az servicebus namespace list --resource-group myresourcegroup
        - name: Get the Service Bus Namespaces by Subscription.
          text: az servicebus namespace list
"""

helps['servicebus namespace delete'] = """
    type: command
    short-summary: Deletes the Service Bus Namespace
    examples:
        - name: Deletes the Service Bus Namespace
          text: az servicebus namespace delete --resource-group myresourcegroup --name mynamespace
"""

helps['servicebus namespace authorization-rule create'] = """
    type: command
    short-summary: Creates Authorization Rule for the given Service Bus Namespace
    examples:
        - name: Creates Authorization Rule 'myauthorule' for the given Service Bus Namespace 'mynamepsace' in resourcegroup
          text: az servicebus namespace authorization-rule create --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule --rights Send Listen
"""

helps['servicebus namespace authorization-rule update'] = """
    type: command
    short-summary: Updates Authorization Rule for the given Service Bus Namespace
    examples:
        - name: Updates Authorization Rule 'myauthorule' for the given Service Bus Namespace 'mynamepsace' in resourcegroup
          text: az servicebus namespace authorization-rule update --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule --rights Send
"""

helps['servicebus namespace authorization-rule show'] = """
    type: command
    short-summary: Shows the details of Service Bus Namespace Authorization Rule
    examples:
        - name: Shows the details of Service Bus Namespace Authorization Rule
          text: az servicebus namespace authorization-rule show --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule
"""

helps['servicebus namespace authorization-rule list'] = """
    type: command
    short-summary: Shows the list of Authorization Rule by Service Bus Namespace
    examples:
        - name: Shows the list of Authorization Rule by Service Bus Namespace
          text: az servicebus namespace authorization-rule show --resource-group myresourcegroup --namespace-name mynamespace
"""

helps['servicebus namespace authorization-rule keys list'] = """
    type: command
    short-summary: Shows the connection strings of Authorization Rule for the Service Bus Namespace
    examples:
        - name: Shows the connection strings of Authorization Rule for the namespace.
          text: az servicebus namespace authorization-rule list-keys --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule
"""

helps['servicebus namespace authorization-rule keys renew'] = """
    type: command
    short-summary: Regenerate the connection strings of Authorization Rule for the Service Bus Namespace.
    examples:
        - name: Regenerate the connection strings of Authorization Rule for the Service Bus Namespace.
          text: az servicebus namespace authorization-rule regenerate-keys --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule --key PrimaryKey
"""

helps['servicebus namespace authorization-rule delete'] = """
    type: command
    short-summary: Deletes the Authorization Rule of the Service Bus Namespace.
    examples:
        - name: Deletes the Authorization Rule of the Service Bus Namespace.
          text: az servicebus namespace authorization-rule delete --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule
"""

helps['servicebus queue create'] = """
    type: command
    short-summary: Creates the Service Bus Queue
    examples:
        - name: Creates Service Bus Queue.
          text: az servicebus queue create --resource-group myresourcegroup --namespace-name mynamespace --name myqueue
"""

helps['servicebus queue update'] = """
    type: command
    short-summary: Updates existing Service Bus Queue
    examples:
        - name: Updates Service Bus Queue.
          text: az servicebus queue update --resource-group myresourcegroup --namespace-name mynamespace --name myqueue --auto-delete-on-idle PT3M
"""

helps['servicebus queue show'] = """
    type: command
    short-summary: shows the Service Bus Queue Details
    examples:
        - name: Shows the Service Bus Queue Details
          text: az servicebus queue show --resource-group myresourcegroup --namespace-name mynamespace --name myqueue
"""

helps['servicebus queue list'] = """
    type: command
    short-summary: List the Queue by Service Bus Namepsace
    examples:
        - name: Get the Queues by Service Bus Namespace.
          text: az servicebus queue list --resource-group myresourcegroup --namespace-name mynamespace
"""

helps['servicebus queue delete'] = """
    type: command
    short-summary: Deletes the Service Bus Queue
    examples:
        - name: Deletes the queue
          text: az servicebus queue delete --resource-group myresourcegroup --namespace-name mynamespace --name myqueue
"""

helps['servicebus queue authorization-rule create'] = """
    type: command
    short-summary: Creates Authorization rule for the given Service Bus Queue.
    examples:
        - name: Creates Authorization rules for Queue
          text: az servicebus queue authorization-rule create --resource-group myresourcegroup --namespace-name mynamespace --queue-name myqueue --name myauthorule --rights Listen
"""

helps['servicebus queue authorization-rule update'] = """
    type: command
    short-summary: Updates Authorization rule for the given Service Bus Queue.
    examples:
        - name: Updates Authorization rules for Queue
          text: az servicebus queue authorization-rule update --resource-group myresourcegroup --namespace-name mynamespace --queue-name myqueue --name myauthorule --rights Send
"""

helps['servicebus queue authorization-rule show'] = """
    type: command
    short-summary: shows the details of Authorization Rule for the given Service Bus Queue.
    examples:
        - name: shows the details of Authorization Rule
          text: az servicebus queue authorization-rule show --resource-group myresourcegroup --namespace-name mynamespace --queue-name myqueue --name myauthorule
"""

helps['servicebus queue authorization-rule list'] = """
    type: command
    short-summary: shows the list of Authorization Rule by Service Bus Queue.
    examples:
        - name: shows the list of Authorization Rule by Queue
          text: az servicebus queue authorization-rule show --resource-group myresourcegroup --namespace-name mynamespace --queue-name myqueue
"""

helps['servicebus queue authorization-rule keys list'] = """
    type: command
    short-summary: Shows the connection strings of Authorization Rule for the given Service Bus Queue.
    examples:
        - name: Shows the connection strings of Authorization Rule for the queue.
          text: az servicebus queue authorization-rule list-keys --resource-group myresourcegroup --namespace-name mynamespace --queue-name myqueue --name myauthorule
"""

helps['servicebus queue authorization-rule keys renew'] = """
    type: command
    short-summary: Regenerate the connection strings of Authorization Rule for the given Service Bus Queue.
    examples:
        - name: Regenerate the connection strings of Authorization Rule for the namespace.
          text: az servicebus queue authorization-rule regenerate-keys --resource-group myresourcegroup --namespace-name mynamespace --queue-name myqueue --name myauthorule --key PrimaryKey
"""

helps['servicebus queue authorization-rule delete'] = """
    type: command
    short-summary: Deletes the Authorization Rule of the given Service Bus Queue.
    examples:
        - name: Deletes the Authorization Rule of the given Service Bus Queue.
          text: az servicebus queue authorization-rule delete --resource-group myresourcegroup --namespace-name mynamespace --queue-name myqueue --name myauthorule
"""

helps['servicebus topic create'] = """
    type: command
    short-summary: Creates the Service Bus Topic
    examples:
        - name: Create a new Service Bus Topic
          text: az servicebus topic create --resource-group myresourcegroup --namespace-name mynamespace --name mytopic
"""

helps['servicebus topic update'] = """
    type: command
    short-summary: Updates the Service Bus Topic
    examples:
        - name: Updates existing Service Bus Topic.
          text: az servicebus topic update --resource-group myresourcegroup --namespace-name mynamespace --name mytopic --support-ordering True
"""

helps['servicebus topic show'] = """
    type: command
    short-summary: Shows the Service Bus Topic Details
    examples:
        - name: Shows the Topic details.
          text: az servicebus topic show --resource-group myresourcegroup --namespace-name mynamespace --name mytopic
"""

helps['servicebus topic list'] = """
    type: command
    short-summary: List the Topic by Service Bus Namepsace
    examples:
        - name: Get the Topics by Namespace.
          text: az servicebus topic list --resource-group myresourcegroup --namespace-name mynamespace
"""

helps['servicebus topic delete'] = """
    type: command
    short-summary: Deletes the Service Bus Topic
    examples:
        - name: Deletes the Service Bus Topic
          text: az servicebus topic delete --resource-group myresourcegroup --namespace-name mynamespace --name mytopic
"""

helps['servicebus topic authorization-rule create'] = """
    type: command
    short-summary: Creates Authorization Rule for given Service Bus Topic
    examples:
        - name: Creates Authorization rules for given Service Bus Topic
          text: az servicebus topic authorization-rule create --resource-group myresourcegroup --namespace-name mynamespace --topic-name mytopic --name myauthorule --rights Send Listen
"""

helps['servicebus topic authorization-rule update'] = """
    type: command
    short-summary: Creates Authorization Rule for given Service Bus Topic
    examples:
        - name: Creates Authorization rules for given Service Bus Topic
          text: az servicebus topic authorization-rule update --resource-group myresourcegroup --namespace-name mynamespace --topic-name mytopic --name myauthorule --rights Send
"""

helps['servicebus topic authorization-rule show'] = """
    type: command
    short-summary: Shows the details of Authorization Rule for given Service Bus Topic
    examples:
        - name: Shows the details of Authorization Rule for given Service Bus Topic
          text: az servicebus topic authorization-rule get --resource-group myresourcegroup --namespace-name mynamespace --topic-name mytopic --name myauthorule
"""

helps['servicebus topic authorization-rule list'] = """
    type: command
    short-summary: shows list of Authorization Rule by Service Bus Topic
    examples:
        - name: shows list of Authorization Rule by Service Bus Topic
          text: az servicebus topic authorization-rule get --resource-group myresourcegroup --namespace-name mynamespace --topic-name mytopic
"""

helps['servicebus topic authorization-rule keys list'] = """
    type: command
    short-summary: shows connection strings of Authorization Rule for given Service Bus Topic.
    examples:
        - name: shows connection strings of Authorization Rule for given Service Bus Topic.
          text: az servicebus topic authorization-rule listkeys --resource-group myresourcegroup --namespace-name mynamespace --topic-name mytopic --name myauthorule
"""

helps['servicebus topic authorization-rule keys renew'] = """
    type: command
    short-summary: Regenerate the connection strings of Authorization Rule for Service Bus Topic.
    examples:
        - name: Regenerate Primary/Secondary key of connection string for Service Bus Topic.
          text: az servicebus topic authorization-rule regenerate_keys --resource-group myresourcegroup --namespace-name mynamespace --topic-name mytopic --name myauthorule --key PrimaryKey
"""

helps['servicebus topic authorization-rule delete'] = """
    type: command
    short-summary: Deletes the Authorization Rule of the given Service Bus Topic.
    examples:
        - name: Deletes the Authorization Rule of Service Bus Topic.
          text: az servicebus topic authorization-rule delete --resource-group myresourcegroup --namespace-name mynamespace --topic-name mytopic --name myauthorule
"""

helps['servicebus topic subscription create'] = """
    type: command
    short-summary: Creates the ServiceBus Subscription
    examples:
        - name: Create a new Subscription.
          text: az servicebus topic subscription create --resource-group myresourcegroup --namespace-name mynamespace --topic-name mytopic --name mysubscription

    """

helps['servicebus topic subscription update'] = """
    type: command
    short-summary: Updates the ServiceBus Subscription
    examples:
        - name: Update a new Subscription.
          text: az servicebus topic subscription update --resource-group myresourcegroup --namespace-name mynamespace --topic-name mytopic --name mysubscription --lock-duration PT3M
    """

helps['servicebus topic subscription show'] = """
    type: command
    short-summary: Shows Service Bus Subscription Details
    examples:
        - name: Shows the Subscription details.
          text: az servicebus topic subscription get --resource-group myresourcegroup --namespace-name mynamespace --topic-name mytopic --name mysubscription
"""

helps['servicebus topic subscription list'] = """
    type: command
    short-summary: List the Subscription by Service Bus Topic
    examples:
        - name: Shows the Subscription by Service Bus Topic.
          text: az servicebus topic subscription list --resource-group myresourcegroup --namespace-name mynamespace
"""

helps['servicebus topic subscription delete'] = """
    type: command
    short-summary: Deletes the Service Bus Subscription
    examples:
        - name: Deletes the Subscription
          text: az servicebus topic subscription delete --resource-group myresourcegroup --namespace-name mynamespace --topic-name mytopic --name mysubscription
"""

helps['servicebus topic subscription rule create'] = """
    type: command
    short-summary: Creates the ServiceBus Rule for Subscription
    examples:
        - name: Creates Rule.
          text: az servicebus topic subscription rule create --resource-group myresourcegroup --namespace-name mynamespace --topic-name mytopic --subscription-name mysubscription --name myrule --filter-sql-expression myproperty=myvalue
"""

helps['servicebus topic subscription rule update'] = """
    type: command
    short-summary: Updates the ServiceBus Rule for Subscription
    examples:
        - name: Updates Rule.
          text: az servicebus topic subscription rule update --resource-group myresourcegroup --namespace-name mynamespace --topic-name mytopic --subscription-name mysubscription --name myrule --filter-sql-expression myproperty=myupdatedvalue
"""

helps['servicebus topic subscription rule show'] = """
    type: command
    short-summary: Shows ServiceBus Rule Details
    examples:
        - name: Shows the ServiceBus Rule details.
          text: az servicebus topic subscription rule show --resource-group myresourcegroup --namespace-name mynamespace --topic-name mytopic --subscription-name mysubscription --name myrule
"""

helps['servicebus topic subscription rule list'] = """
    type: command
    short-summary: List the ServiceBus Rule by Subscription
    examples:
        - name: Shows the Rule ServiceBus by Subscription.
          text: az servicebus topic subscription rule list --resource-group myresourcegroup --namespace-name mynamespace
           --subscription-name mysubscription
"""

helps['servicebus topic subscription rule delete'] = """
    type: command
    short-summary: Deletes the ServiceBus Rule
    examples:
        - name: Deletes the ServiceBus Rule
          text: az servicebus topic subscription rule delete --resource-group myresourcegroup --namespace-name mynamespace --topic-name mytopic --subscription-name mysubscription --name myrule
"""

helps['servicebus georecovery-alias exists'] = """
    type: command
    short-summary: Checks if Geo Recovery Alias Name is available
    examples:
        - name: Check the availability of the Geo Disaster Recovery configuration - Alias Name
          text: az servicebus georecovery-alias exists --resource-group myresourcegroup --namespace-name primarynamespace --alias myaliasname
"""

helps['servicebus georecovery-alias set'] = """
    type: command
    short-summary: Sets Service Bus Geo Recovery Alias for the give Namespace
    examples:
        - name: Sets Geo Disaster Recovery configuration - Alias for the give Namespace
          text: az servicebus georecovery-alias set --resource-group myresourcegroup --namespace-name primarynamespace --alias myaliasname --partner-namespace armresourceid
"""

helps['servicebus georecovery-alias show'] = """
    type: command
    short-summary: shows details of Service Bus Geo Recovery Alias for Primay/Secondary Namespace
    examples:
        - name:  show details of Alias (Geo DR Configuration)  of the Primary Namespace
          text: az servicebus georecovery-alias show  --resource-group myresourcegroup --namespace-name primarynamespace --alias myaliasname
        - name:  Get details of Alias (Geo DR Configuration)  of the Secondary Namespace
          text: az servicebus georecovery-alias show  --resource-group myresourcegroup --namespace-name secondarynamespace --alias myaliasname
"""

helps['servicebus georecovery-alias authorization-rule list'] = """
    type: command
    short-summary: Shows the list of Authorization Rule by Service Bus Namespace
    examples:
        - name: Shows the list of Authorization Rule by Service Bus Namespace
          text: az servicebus georecovery-alias authorization-rule show --resource-group myresourcegroup --namespace-name mynamespace
"""

helps['servicebus georecovery-alias authorization-rule keys list'] = """
    type: command
    short-summary: Shows the connection strings of Authorization Rule for the Service Bus Namespace
    examples:
        - name: Shows the connection strings of Authorization Rule for the namespace.
          text: az servicebus georecovery-alias authorization-rule keys list --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule
"""

helps['servicebus georecovery-alias break-pair'] = """
    type: command
    short-summary: Disables Service Bus Geo Recovery Alias and stops replicating changes from primary to secondary namespaces
    examples:
        - name:  Disables the Disaster Recovery and stops replicating changes from primary to secondary namespaces
          text: az servicebus georecovery-alias break-pair --resource-group myresourcegroup --namespace-name primarynamespace --alias myaliasname
"""

helps['servicebus georecovery-alias fail-over'] = """
    type: command
    short-summary: Invokes Service Bus Geo Recovery Alias failover and re-configure the alias to point to the secondary namespace
    examples:
        - name:  Invokes Geo Disaster Recovery  failover and reconfigure the alias to point to the secondary namespace
          text: az servicebus georecovery-alias fail-over --resource-group myresourcegroup --namespace-name secondarynamespace --alias myaliasname
"""

helps['servicebus georecovery-alias delete'] = """
    type: command
    short-summary: Deletes Service Bus Geo Recovery Alias request accepted
    examples:
        - name:  Deletes Alias(Disaster Recovery configuration) request accepted
          text: az servicebus georecovery-alias delete --resource-group myresourcegroup --namespace-name secondarynamespace --alias myaliasname
"""
