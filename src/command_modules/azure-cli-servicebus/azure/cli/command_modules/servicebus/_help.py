# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["servicebus georecovery-alias fail-over"] = """
"type": |-
    command
"short-summary": |-
    Invokes Service Bus Geo-Disaster Recovery Configuration Alias failover and re-configure the alias to point to the secondary namespace
"""

helps["servicebus queue authorization-rule keys"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Authorization Rule keys for Service Bus Queue
"""

helps["servicebus namespace authorization-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Service Bus Namespace Authorization Rule
"""

helps["servicebus georecovery-alias authorization-rule list"] = """
"type": |-
    command
"short-summary": |-
    Shows the list of Authorization Rule by Service Bus Namespace
"""

helps["servicebus topic subscription show"] = """
"type": |-
    command
"short-summary": |-
    Shows Service Bus Subscription Details
"examples":
-   "name": |-
        Shows Service Bus Subscription Details.
    "text": |-
        az servicebus topic subscription show --namespace-name mynamespace --name mysubscription --topic-name mytopic --resource-group myresourcegroup
"""

helps["servicebus queue authorization-rule delete"] = """
"type": |-
    command
"short-summary": |-
    Delete the Authorization Rule of Service Bus Queue
"""

helps["servicebus topic update"] = """
"type": |-
    command
"short-summary": |-
    Updates the Service Bus Topic
"""

helps["servicebus topic show"] = """
"type": |-
    command
"short-summary": |-
    Shows the Service Bus Topic Details
"""

helps["servicebus queue show"] = """
"type": |-
    command
"short-summary": |-
    shows the Service Bus Queue Details
"examples":
-   "name": |-
        Shows the Service Bus Queue Details.
    "text": |-
        az servicebus queue show --namespace-name mynamespace --name myqueue --resource-group myresourcegroup
"""

helps["servicebus georecovery-alias authorization-rule keys"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Authorization Rule keys for Service Bus Namespace
"""

helps["servicebus topic create"] = """
"type": |-
    command
"short-summary": |-
    Create the Service Bus Topic
"""

helps["servicebus topic authorization-rule keys list"] = """
"type": |-
    command
"short-summary": |-
    List the keys and connection strings of Authorization Rule for Service Bus Topic.
"""

helps["servicebus topic list"] = """
"type": |-
    command
"short-summary": |-
    List the Topic by Service Bus Namepsace
"examples":
-   "name": |-
        List the Topic by Service Bus Namepsace.
    "text": |-
        az servicebus topic list --namespace-name mynamespace --resource-group myresourcegroup
"""

helps["servicebus topic authorization-rule keys renew"] = """
"type": |-
    command
"short-summary": |-
    Regenerate keys of Authorization Rule for Service Bus Topic.
"""

helps["servicebus topic authorization-rule create"] = """
"type": |-
    command
"short-summary": |-
    Create Authorization Rule for given Service Bus Topic
"""

helps["servicebus queue authorization-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Service Bus Queue Authorization Rule
"""

helps["servicebus queue authorization-rule keys renew"] = """
"type": |-
    command
"short-summary": |-
    Regenerate keys of Authorization Rule for Service Bus Queue
"""

helps["servicebus queue list"] = """
"type": |-
    command
"short-summary": |-
    List the Queue by Service Bus Namepsace
"examples":
-   "name": |-
        List the Queue by Service Bus Namepsace.
    "text": |-
        az servicebus queue list --namespace-name mynamespace --resource-group myresourcegroup
"""

helps["servicebus topic authorization-rule show"] = """
"type": |-
    command
"short-summary": |-
    Shows the details of Authorization Rule for given Service Bus Topic
"""

helps["servicebus topic subscription list"] = """
"type": |-
    command
"short-summary": |-
    List the Subscription by Service Bus Topic
"examples":
-   "name": |-
        List the Subscription by Service Bus Topic.
    "text": |-
        az servicebus topic subscription list --namespace-name mynamespace --topic-name MyTopic --resource-group myresourcegroup
"""

helps["servicebus namespace authorization-rule list"] = """
"type": |-
    command
"short-summary": |-
    Shows the list of Authorization Rule by Service Bus Namespace
"""

helps["servicebus namespace authorization-rule keys"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Authorization Rule connection strings for Namespace
"""

helps["servicebus topic subscription update"] = """
"type": |-
    command
"short-summary": |-
    Updates the ServiceBus Subscription
"examples":
-   "name": |-
        Updates the ServiceBus Subscription.
    "text": |-
        az servicebus topic subscription update --namespace-name mynamespace --default-message-time-to-live <default-message-time-to-live> --name mysubscription --topic-name mytopic --resource-group myresourcegroup
"""

helps["servicebus migration"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Service Bus Migration of Standard to Premium
"""

helps["servicebus namespace authorization-rule update"] = """
"type": |-
    command
"short-summary": |-
    Updates Authorization Rule for the given Service Bus Namespace
"""

helps["servicebus topic subscription delete"] = """
"type": |-
    command
"short-summary": |-
    Deletes the Service Bus Subscription
"examples":
-   "name": |-
        Deletes the Service Bus Subscription.
    "text": |-
        az servicebus topic subscription delete --namespace-name mynamespace --resource-group myresourcegroup --topic-name mytopic --name mysubscription
"""

helps["servicebus namespace exists"] = """
"type": |-
    command
"short-summary": |-
    check for the availability of the given name for the Namespace
"examples":
-   "name": |-
        Check for the availability of the given name for the Namespace.
    "text": |-
        az servicebus namespace exists --name mynamespace
"""

helps["servicebus georecovery-alias"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Service Bus Geo-Disaster Recovery Configuration Alias
"""

helps["servicebus namespace create"] = """
"type": |-
    command
"short-summary": |-
    Create a Service Bus Namespace
"""

helps["servicebus georecovery-alias delete"] = """
"type": |-
    command
"short-summary": |-
    Deletes Service Bus Geo-Disaster Recovery Configuration Alias request accepted
"""

helps["servicebus queue"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Service Bus Queue and Authorization Rule
"""

helps["servicebus queue authorization-rule update"] = """
"type": |-
    command
"short-summary": |-
    Update Authorization Rule for the given Service Bus Queue.
"""

helps["servicebus topic subscription rule"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Service Bus Rule
"""

helps["servicebus topic subscription rule update"] = """
"type": |-
    command
"short-summary": |-
    Updates the ServiceBus Rule for Subscription
"""

helps["servicebus queue authorization-rule list"] = """
"type": |-
    command
"short-summary": |-
    List of Authorization Rule by Service Bus Queue.
"""

helps["servicebus migration complete"] = """
"type": |-
    command
"short-summary": |-
    Completes the Service Bus Migration of Standard to Premium namespace
"long-summary": |-
    After completing migration, the existing connection strings to standard namespace will connect to premium namespace automatically. Post migration name is the name that can be used to connect to standard namespace after migration is complete.
"""

helps["servicebus namespace"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Service Bus Namespace
"""

helps["servicebus migration start"] = """
"type": |-
    command
"short-summary": |-
    Create and Start Service Bus Migration of Standard to Premium namespace.
"long-summary": |-
    Service Bus Migration requires an empty Premium namespace to replicate entities from Standard namespace.
"""

helps["servicebus queue create"] = """
"type": |-
    command
"short-summary": |-
    Create the Service Bus Queue
"examples":
-   "name": |-
        Create the Service Bus Queue.
    "text": |-
        az servicebus queue create --namespace-name mynamespace --auto-delete-on-idle <auto-delete-on-idle> --default-message-time-to-live <default-message-time-to-live> --name myqueue --resource-group myresourcegroup
"""

helps["servicebus namespace delete"] = """
"type": |-
    command
"short-summary": |-
    Deletes the Service Bus Namespace
"""

helps["servicebus georecovery-alias exists"] = """
"type": |-
    command
"short-summary": |-
    Check if Geo Recovery Alias Name is available
"""

helps["servicebus queue authorization-rule show"] = """
"type": |-
    command
"short-summary": |-
    show properties of Authorization Rule for the given Service Bus Queue.
"""

helps["servicebus topic subscription rule create"] = """
"type": |-
    command
"short-summary": |-
    Create the ServiceBus Rule for Subscription
"examples":
-   "name": |-
        Create the ServiceBus Rule for Subscription.
    "text": |-
        az servicebus topic subscription rule create --filter-sql-expression myproperty=myvalue --topic-name mytopic --name myrule --namespace-name mynamespace --resource-group myresourcegroup --subscription-name mysubscription
"""

helps["servicebus topic subscription rule list"] = """
"type": |-
    command
"short-summary": |-
    List the ServiceBus Rule by Subscription
"examples":
-   "name": |-
        List the ServiceBus Rule by Subscription.
    "text": |-
        az servicebus topic subscription rule list --namespace-name mynamespace --subscription-name mysubscription --topic-name MyTopic --resource-group myresourcegroup
"""

helps["servicebus queue authorization-rule create"] = """
"type": |-
    command
"short-summary": |-
    Create Authorization Rule for the given Service Bus Queue.
"""

helps["servicebus topic authorization-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Service Bus Topic Authorization Rule
"""

helps["servicebus georecovery-alias authorization-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Service Bus Authorization Rule for Namespace with Geo-Disaster Recovery Configuration Alias
"""

helps["servicebus topic subscription rule show"] = """
"type": |-
    command
"short-summary": |-
    Shows ServiceBus Rule Details
"""

helps["servicebus georecovery-alias break-pair"] = """
"type": |-
    command
"short-summary": |-
    Disables Service Bus Geo-Disaster Recovery Configuration Alias and stops replicating changes from primary to secondary namespaces
"""

helps["servicebus namespace update"] = """
"type": |-
    command
"short-summary": |-
    Updates a Service Bus Namespace
"""

helps["servicebus georecovery-alias authorization-rule keys list"] = """
"type": |-
    command
"short-summary": |-
    List the keys and connection strings of Authorization Rule for the Service Bus Namespace
"""

helps["servicebus namespace authorization-rule show"] = """
"type": |-
    command
"short-summary": |-
    Shows the details of Service Bus Namespace Authorization Rule
"""

helps["servicebus namespace list"] = """
"type": |-
    command
"short-summary": |-
    List the Service Bus Namespaces
"""

helps["servicebus topic authorization-rule update"] = """
"type": |-
    command
"short-summary": |-
    Create Authorization Rule for given Service Bus Topic
"""

helps["servicebus queue update"] = """
"type": |-
    command
"short-summary": |-
    Updates existing Service Bus Queue
"""

helps["servicebus queue authorization-rule keys list"] = """
"type": |-
    command
"short-summary": |-
    List the keys and connection strings of Authorization Rule for the given Service Bus Queue
"""

helps["servicebus topic authorization-rule keys"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Authorization Rule keys for Service Bus Topic
"""

helps["servicebus"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Service Bus namespaces, queues, topics, subscriptions, rules and geo-disaster recovery configuration alias
"""

helps["servicebus topic subscription"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Service Bus Subscription
"""

helps["servicebus queue delete"] = """
"type": |-
    command
"short-summary": |-
    Deletes the Service Bus Queue
"examples":
-   "name": |-
        Deletes the Service Bus Queue.
    "text": |-
        az servicebus queue delete --namespace-name mynamespace --name myqueue --resource-group myresourcegroup
"""

helps["servicebus topic authorization-rule delete"] = """
"type": |-
    command
"short-summary": |-
    Deletes the Authorization Rule of the given Service Bus Topic.
"""

helps["servicebus topic"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Service Bus Topic and Authorization Rule
"""

helps["servicebus migration show"] = """
"type": |-
    command
"short-summary": |-
    shows properties of properties of Service Bus Migration
"""

helps["servicebus georecovery-alias set"] = """
"type": |-
    command
"short-summary": |-
    Sets Service Bus Geo-Disaster Recovery Configuration Alias for the give Namespace
"""

helps["servicebus namespace authorization-rule create"] = """
"type": |-
    command
"short-summary": |-
    Create Authorization Rule for the given Service Bus Namespace
"""

helps["servicebus topic authorization-rule list"] = """
"type": |-
    command
"short-summary": |-
    shows list of Authorization Rule by Service Bus Topic
"""

helps["servicebus georecovery-alias show"] = """
"type": |-
    command
"short-summary": |-
    shows properties of Service Bus Geo-Disaster Recovery Configuration Alias for Primay/Secondary Namespace
"""

helps["servicebus migration abort"] = """
"type": |-
    command
"short-summary": |-
    Disable the Service Bus Migration of Standard to Premium namespace
"long-summary": |-
    abort command stops the replication of entities from standard to premium namespaces. The entities replicated to premium namespace before abort command will be available under premium namespace. The aborted migration can not be resumed, its has to restarted.
"""

helps["servicebus namespace authorization-rule keys list"] = """
"type": |-
    command
"short-summary": |-
    List the keys and connection strings of Authorization Rule for Service Bus Namespace
"""

helps["servicebus topic subscription rule delete"] = """
"type": |-
    command
"short-summary": |-
    Deletes the ServiceBus Rule
"""

helps["servicebus namespace show"] = """
"type": |-
    command
"short-summary": |-
    Shows the Service Bus Namespace details
"""

helps["servicebus namespace authorization-rule keys renew"] = """
"type": |-
    command
"short-summary": |-
    Regenerate keys of Authorization Rule for the Service Bus Namespace.
"""

helps["servicebus namespace authorization-rule delete"] = """
"type": |-
    command
"short-summary": |-
    Deletes the Authorization Rule of the Service Bus Namespace.
"""

helps["servicebus topic delete"] = """
"type": |-
    command
"short-summary": |-
    Deletes the Service Bus Topic
"""

helps["servicebus topic subscription create"] = """
"type": |-
    command
"short-summary": |-
    Create the ServiceBus Subscription
"examples":
-   "name": |-
        Create the ServiceBus Subscription.
    "text": |-
        az servicebus topic subscription create --namespace-name mynamespace --name mysubscription --topic-name mytopic --resource-group myresourcegroup
"""

