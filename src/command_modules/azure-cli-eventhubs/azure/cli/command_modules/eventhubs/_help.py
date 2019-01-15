# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["eventhubs namespace"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Event Hubs namespace and Authorizationrule
"""

helps["eventhubs georecovery-alias set"] = """
"type": |-
    command
"short-summary": |-
    Sets a Geo-Disaster Recovery Configuration Alias for the give Namespace
"""

helps["eventhubs namespace update"] = """
"type": |-
    command
"short-summary": |-
    Updates the Event Hubs Namespace
"""

helps["eventhubs namespace show"] = """
"type": |-
    command
"short-summary": |-
    shows the Event Hubs Namespace Details
"""

helps["eventhubs georecovery-alias authorization-rule keys"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Event Hubs Authorizationrule connection strings for Geo Recovery configuration Alias
"""

helps["eventhubs namespace authorization-rule list"] = """
"type": |-
    command
"short-summary": |-
    Shows the list of Authorizationrule by Namespace
"""

helps["eventhubs eventhub consumer-group create"] = """
"type": |-
    command
"short-summary": |-
    Creates the EventHub ConsumerGroup
"""

helps["eventhubs namespace delete"] = """
"type": |-
    command
"short-summary": |-
    Deletes the Namespaces
"""

helps["eventhubs georecovery-alias authorization-rule show"] = """
"type": |-
    command
"short-summary": |-
    Show properties of Event Hubs Geo-Disaster Recovery Configuration Alias and Namespace Authorizationrule
"""

helps["eventhubs namespace create"] = """
"type": |-
    command
"short-summary": |-
    Creates the Event Hubs Namespace
"""

helps["eventhubs namespace authorization-rule delete"] = """
"type": |-
    command
"short-summary": |-
    Deletes the Authorizationrule of the namespace.
"""

helps["eventhubs eventhub consumer-group delete"] = """
"type": |-
    command
"short-summary": |-
    Deletes the ConsumerGroup
"""

helps["eventhubs"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Event Hubs namespaces, eventhubs, consumergroups and geo recovery configurations - Alias
"""

helps["eventhubs georecovery-alias fail-over"] = """
"type": |-
    command
"short-summary": |-
    Invokes Geo-Disaster Recovery Configuration Alias to point to the secondary namespace
"""

helps["eventhubs eventhub authorization-rule delete"] = """
"type": |-
    command
"short-summary": |-
    Deletes the Authorizationrule of Eventhub.
"""

helps["eventhubs namespace authorization-rule update"] = """
"type": |-
    command
"short-summary": |-
    Updates Authorizationrule for the given Namespace
"""

helps["eventhubs georecovery-alias break-pair"] = """
"type": |-
    command
"short-summary": |-
    Disables Geo-Disaster Recovery Configuration Alias and stops replicating changes from primary to secondary namespaces
"""

helps["eventhubs georecovery-alias show"] = """
"type": |-
    command
"short-summary": |-
    shows properties of Geo-Disaster Recovery Configuration Alias for Primay or Secondary Namespace
"""

helps["eventhubs georecovery-alias"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Event Hubs Geo Recovery configuration Alias
"""

helps["eventhubs namespace authorization-rule show"] = """
"type": |-
    command
"short-summary": |-
    Shows the details of Authorizationrule
"""

helps["eventhubs eventhub authorization-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Service Bus Authorizationrule for Eventhub
"""

helps["eventhubs eventhub consumer-group"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Event Hubs consumergroup
"""

helps["eventhubs georecovery-alias delete"] = """
"type": |-
    command
"short-summary": |-
    Delete Geo-Disaster Recovery Configuration Alias
"""

helps["eventhubs georecovery-alias exists"] = """
"type": |-
    command
"short-summary": |-
    Check the availability of Geo-Disaster Recovery Configuration Alias Name
"""

helps["eventhubs namespace list"] = """
"type": |-
    command
"short-summary": |-
    Lists the Event Hubs Namespaces
"examples":
-   "name": |-
        Lists the Event Hubs Namespaces.
    "text": |-
        az eventhubs namespace list --query [0]
"""

helps["eventhubs eventhub authorization-rule keys list"] = """
"type": |-
    command
"short-summary": |-
    Shows the connection strings of Authorizationrule for the Eventhub.
"""

helps["eventhubs eventhub consumer-group update"] = """
"type": |-
    command
"short-summary": |-
    Updates the EventHub ConsumerGroup
"""

helps["eventhubs namespace authorization-rule keys"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Event Hubs Authorizationrule connection strings for Namespace
"""

helps["eventhubs namespace authorization-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Event Hubs Authorizationrule for Namespace
"""

helps["eventhubs georecovery-alias authorization-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Event Hubs Authorizationrule for Geo Recovery configuration Alias
"""

helps["eventhubs eventhub consumer-group list"] = """
"type": |-
    command
"short-summary": |-
    List the ConsumerGroup by Eventhub
"""

helps["eventhubs eventhub authorization-rule keys renew"] = """
"type": |-
    command
"short-summary": |-
    Regenerate the connection strings of Authorizationrule for the namespace.
"""

helps["eventhubs eventhub authorization-rule create"] = """
"type": |-
    command
"short-summary": |-
    Creates Authorizationrule for the given Eventhub
"""

helps["eventhubs namespace authorization-rule create"] = """
"type": |-
    command
"short-summary": |-
    Creates Authorizationrule for the given Namespace
"""

helps["eventhubs eventhub list"] = """
"type": |-
    command
"short-summary": |-
    List the EventHub by Namepsace
"examples":
-   "name": |-
        List the EventHub by Namepsace.
    "text": |-
        az eventhubs eventhub list --namespace-name mynamespace --output json --resource-group myresourcegroup
"""

helps["eventhubs georecovery-alias authorization-rule list"] = """
"type": |-
    command
"short-summary": |-
    List of Authorizationrule by Event Hubs Namespace
"""

helps["eventhubs eventhub authorization-rule update"] = """
"type": |-
    command
"short-summary": |-
    Updates Authorizationrule for the given Eventhub
"""

helps["eventhubs eventhub"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Event Hubs eventhub and authorization-rule
"""

helps["eventhubs eventhub show"] = """
"type": |-
    command
"short-summary": |-
    shows the Eventhub Details
"""

helps["eventhubs eventhub delete"] = """
"type": |-
    command
"short-summary": |-
    Deletes the Eventhub
"examples":
-   "name": |-
        Deletes the Eventhub.
    "text": |-
        az eventhubs eventhub delete --namespace-name mynamespace --name myeventhub --resource-group myresourcegroup
"""

helps["eventhubs namespace exists"] = """
"type": |-
    command
"short-summary": |-
    check for the availability of the given name for the Namespace
"""

helps["eventhubs eventhub authorization-rule list"] = """
"type": |-
    command
"short-summary": |-
    shows the list of Authorization-rules by Eventhub
"""

helps["eventhubs namespace authorization-rule keys list"] = """
"type": |-
    command
"short-summary": |-
    Shows the connection strings for namespace
"""

helps["eventhubs eventhub create"] = """
"type": |-
    command
"short-summary": |-
    Creates the Event Hubs Eventhub
"examples":
-   "name": |-
        Creates the Event Hubs Eventhub.
    "text": |-
        az eventhubs eventhub create --namespace-name mynamespace --partition-count 15 --message-retention 4 --resource-group myresourcegroup --name myeventhub
"""

helps["eventhubs namespace authorization-rule keys renew"] = """
"type": |-
    command
"short-summary": |-
    Regenerate the connection strings of Authorizationrule for the namespace.
"""

helps["eventhubs georecovery-alias authorization-rule keys list"] = """
"type": |-
    command
"short-summary": |-
    Shows the keys and connection strings of Authorizationrule for the Event Hubs Namespace
"""

helps["eventhubs eventhub authorization-rule show"] = """
"type": |-
    command
"short-summary": |-
    shows the details of Authorizationrule
"""

helps["eventhubs eventhub authorization-rule keys"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Authorizationrule connection strings for Eventhub
"""

helps["eventhubs eventhub update"] = """
"type": |-
    command
"short-summary": |-
    Updates the Event Hubs Eventhub
"""

helps["eventhubs eventhub consumer-group show"] = """
"type": |-
    command
"short-summary": |-
    Shows the ConsumerGroup Details
"""

