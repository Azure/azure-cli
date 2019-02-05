# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
# pylint: disable=unused-import

from knack.help_files import helps

helps['relay'] = """
    type: group
    short-summary: Manage Azure Relay Service namespaces, WCF relays, hybrid connections, and rules
"""

helps['relay namespace'] = """
    type: group
    short-summary: Manage Azure Relay Service Namespace
"""

helps['relay namespace authorization-rule'] = """
    type: group
    short-summary: Manage Azure Relay Service Namespace Authorization Rule
"""

helps['relay namespace authorization-rule keys'] = """
    type: group
    short-summary: Manage Azure Authorization Rule connection strings for Namespace
"""

helps['relay wcfrelay'] = """
    type: group
    short-summary: Manage Azure Relay Service WCF Relay and Authorization Rule
"""

helps['relay wcfrelay authorization-rule'] = """
    type: group
    short-summary: Manage Azure Relay Service WCF Relay Authorization Rule
"""

helps['relay wcfrelay authorization-rule keys'] = """
    type: group
    short-summary: Manage Azure Authorization Rule keys for Relay Service WCF Relay
"""

helps['relay hyco'] = """
    type: group
    short-summary: Manage Azure Relay Service Hybrid Connection and Authorization Rule
"""

helps['relay hyco authorization-rule'] = """
    type: group
    short-summary: Manage Azure Relay Service Hybrid Connection Authorization Rule
"""

helps['relay hyco authorization-rule keys'] = """
    type: group
    short-summary: Manage Azure Authorization Rule keys for Relay Service Hybrid Connection
"""

helps['relay namespace exists'] = """
    type: command
    short-summary: check for the availability of the given name for the Namespace
    examples:
        - name: check for the availability of mynamespace for the Namespace
          text: az relay namespace exists --name mynamespace
"""

helps['relay namespace create'] = """
    type: command
    short-summary: Create a Relay Service Namespace
    examples:
        - name: Create a Relay Service Namespace.
          text: az relay namespace create --resource-group myresourcegroup --name mynamespace --location westus --tags tag1=value1 tag2=value2
"""

helps['relay namespace update'] = """
    type: command
    short-summary: Updates a Relay Service Namespace
    examples:
        - name: Updates a Relay Service Namespace.
          text: az relay namespace update --resource-group myresourcegroup --name mynamespace --tags tag=value
"""

helps['relay namespace show'] = """
    type: command
    short-summary: Shows the Relay Service Namespace details
    examples:
        - name: shows the Namespace details.
          text: az relay namespace show --resource-group myresourcegroup --name mynamespace
"""

helps['relay namespace list'] = """
    type: command
    short-summary: List the Relay Service Namespaces
    examples:
        - name: Get the Relay Service Namespaces by resource group
          text: az relay namespace list --resource-group myresourcegroup
        - name: Get the Relay Service Namespaces by Subscription.
          text: az relay namespace list
"""

helps['relay namespace delete'] = """
    type: command
    short-summary: Deletes the Relay Service Namespace
    examples:
        - name: Deletes the Relay Service Namespace
          text: az relay namespace delete --resource-group myresourcegroup --name mynamespace
"""

helps['relay namespace authorization-rule create'] = """
    type: command
    short-summary: Create Authorization Rule for the given Relay Service Namespace
    examples:
        - name: Create Authorization Rule 'myrule' for the given Relay Service Namespace 'mynamespace' in resourcegroup
          text: az relay namespace authorization-rule create --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule --rights Send Listen
"""

helps['relay namespace authorization-rule update'] = """
    type: command
    short-summary: Updates Authorization Rule for the given Relay Service Namespace
    examples:
        - name: Updates Authorization Rule 'myrule' for the given Relay Service Namespace 'mynamespace' in resourcegroup
          text: az relay namespace authorization-rule update --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule --rights Send
"""

helps['relay namespace authorization-rule show'] = """
    type: command
    short-summary: Shows the details of Relay Service Namespace Authorization Rule
    examples:
        - name: Shows the details of Relay Service Namespace Authorization Rule
          text: az relay namespace authorization-rule show --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule
"""

helps['relay namespace authorization-rule list'] = """
    type: command
    short-summary: Shows the list of Authorization Rule by Relay Service Namespace
    examples:
        - name: Shows the list of Authorization Rule by Relay Service Namespace
          text: az relay namespace authorization-rule list --resource-group myresourcegroup --namespace-name mynamespace
"""

helps['relay namespace authorization-rule keys list'] = """
    type: command
    short-summary: List the keys and connection strings of Authorization Rule for Relay Service Namespace
    examples:
        - name: List the keys and connection strings of Authorization Rule for Relay Service Namespace
          text: az relay namespace authorization-rule keys list --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule
"""

helps['relay namespace authorization-rule keys renew'] = """
    type: command
    short-summary: Regenerate keys of Authorization Rule for the Relay Service Namespace.
    examples:
        - name: Regenerate keys of Authorization Rule for the Relay Service Namespace.
          text: az relay namespace authorization-rule keys renew --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule --key PrimaryKey
"""

helps['relay namespace authorization-rule delete'] = """
    type: command
    short-summary: Deletes the Authorization Rule of the Relay Service Namespace.
    examples:
        - name: Deletes the Authorization Rule of the Relay Service Namespace.
          text: az relay namespace authorization-rule delete --resource-group myresourcegroup --namespace-name mynamespace --name myauthorule
"""

helps['relay wcfrelay create'] = """
    type: command
    short-summary: Create the Relay Service WCF Relay
    examples:
        - name: Create Relay Service WCF Relay.
          text: az relay wcfrelay create --resource-group myresourcegroup --namespace-name mynamespace --name myrelay --relay-type NetTcp
"""

helps['relay wcfrelay update'] = """
    type: command
    short-summary: Updates existing Relay Service WCF Relay
    examples:
        - name: Updates Relay Service WCF Relay.
          text: az relay wcfrelay update --resource-group myresourcegroup --namespace-name mynamespace --name myrelay
"""

helps['relay wcfrelay show'] = """
    type: command
    short-summary: shows the Relay Service WCF Relay Details
    examples:
        - name: Shows the Relay Service WCF Relay Details
          text: az relay wcfrelay show --resource-group myresourcegroup --namespace-name mynamespace --name myrelay
"""

helps['relay wcfrelay list'] = """
    type: command
    short-summary: List the WCF Relay by Relay Service Namepsace
    examples:
        - name: Get the WCF Relays by Relay Service Namespace.
          text: az relay wcfrelay list --resource-group myresourcegroup --namespace-name mynamespace
"""

helps['relay wcfrelay delete'] = """
    type: command
    short-summary: Deletes the Relay Service WCF Relay
    examples:
        - name: Deletes the wcfrelay
          text: az relay wcfrelay delete --resource-group myresourcegroup --namespace-name mynamespace --name myrelay
"""

helps['relay wcfrelay authorization-rule create'] = """
    type: command
    short-summary: Create Authorization Rule for the given Relay Service WCF Relay.
    examples:
        - name: Create Authorization Rule for WCF Relay
          text: az relay wcfrelay authorization-rule create --resource-group myresourcegroup --namespace-name mynamespace --relay-name myrelay --name myauthorule --rights Listen
"""

helps['relay wcfrelay authorization-rule update'] = """
    type: command
    short-summary: Update Authorization Rule for the given Relay Service WCF Relay.
    examples:
        - name: Update Authorization Rule for WCF Relay
          text: az relay wcfrelay authorization-rule update --resource-group myresourcegroup --namespace-name mynamespace --relay-name myrelay --name myauthorule --rights Send
"""

helps['relay wcfrelay authorization-rule show'] = """
    type: command
    short-summary: show properties of Authorization Rule for the given Relay Service WCF Relay.
    examples:
        - name: show properties of Authorization Rule
          text: az relay wcfrelay authorization-rule show --resource-group myresourcegroup --namespace-name mynamespace --relay-name myrelay --name myauthorule
"""

helps['relay wcfrelay authorization-rule list'] = """
    type: command
    short-summary: List of Authorization Rule by Relay Service WCF Relay.
    examples:
        - name: List of Authorization Rule by WCF Relay
          text: az relay wcfrelay authorization-rule list --resource-group myresourcegroup --namespace-name mynamespace --relay-name myrelay
"""

helps['relay wcfrelay authorization-rule keys list'] = """
    type: command
    short-summary: List the keys and connection strings of Authorization Rule for the given Relay Service WCF Relay
    examples:
        - name: List the keys and connection strings of Authorization Rule for the given Relay Service WCF Relay
          text: az relay wcfrelay authorization-rule keys list --resource-group myresourcegroup --namespace-name mynamespace --relay-name myrelay --name myauthorule
"""

helps['relay wcfrelay authorization-rule keys renew'] = """
    type: command
    short-summary: Regenerate keys of Authorization Rule for Relay Service WCF Relay
    examples:
        - name: Regenerate keys of Authorization Rule for Relay Service WCF Relay
          text: az relay wcfrelay authorization-rule keys renew --resource-group myresourcegroup --namespace-name mynamespace --relay-name myrelay --name myauthorule --key PrimaryKey
"""

helps['relay wcfrelay authorization-rule delete'] = """
    type: command
    short-summary: Delete the Authorization Rule of Relay Service WCF Relay
    examples:
        - name: Delete the Authorization Rule of Relay Service WCF Relay
          text: az relay wcfrelay authorization-rule delete --resource-group myresourcegroup --namespace-name mynamespace --relay-name myrelay --name myauthorule
"""

helps['relay hyco create'] = """
    type: command
    short-summary: Create the Relay Service Hybrid Connection
    examples:
        - name: Create a new Relay Service Hybrid Connection
          text: az relay hyco create --resource-group myresourcegroup --namespace-name mynamespace --name myhyco
"""

helps['relay hyco update'] = """
    type: command
    short-summary: Updates the Relay Service Hybrid Connection
    examples:
        - name: Updates existing Relay Service Hybrid Connection.
          text: az relay hyco update --resource-group myresourcegroup --namespace-name mynamespace --name myhyco
"""

helps['relay hyco show'] = """
    type: command
    short-summary: Shows the Relay Service Hybrid Connection Details
    examples:
        - name: Shows the Hybrid Connection details.
          text: az relay hyco show --resource-group myresourcegroup --namespace-name mynamespace --name myhyco
"""

helps['relay hyco list'] = """
    type: command
    short-summary: List the Hybrid Connection by Relay Service Namepsace
    examples:
        - name: Get the Hybrid Connections by Namespace.
          text: az relay hyco list --resource-group myresourcegroup --namespace-name mynamespace
"""

helps['relay hyco delete'] = """
    type: command
    short-summary: Deletes the Relay Service Hybrid Connection
    examples:
        - name: Deletes the Relay Service Hybrid Connection
          text: az relay hyco delete --resource-group myresourcegroup --namespace-name mynamespace --name myhyco
"""

helps['relay hyco authorization-rule create'] = """
    type: command
    short-summary: Create Authorization Rule for given Relay Service Hybrid Connection
    examples:
        - name: Create Authorization Rule for given Relay Service Hybrid Connection
          text: az relay hyco authorization-rule create --resource-group myresourcegroup --namespace-name mynamespace --hybrid-connection-name myhyco --name myauthorule --rights Send Listen
"""

helps['relay hyco authorization-rule update'] = """
    type: command
    short-summary: Create Authorization Rule for given Relay Service Hybrid Connection
    examples:
        - name: Create Authorization Rule for given Relay Service Hybrid Connection
          text: az relay hyco authorization-rule update --resource-group myresourcegroup --namespace-name mynamespace --hybrid-connection-name myhyco --name myauthorule --rights Send
"""

helps['relay hyco authorization-rule show'] = """
    type: command
    short-summary: Shows the details of Authorization Rule for given Relay Service Hybrid Connection
    examples:
        - name: Shows the details of Authorization Rule for given Relay Service Hybrid Connection
          text: az relay hyco authorization-rule show --resource-group myresourcegroup --namespace-name mynamespace --hybrid-connection-name myhyco --name myauthorule
"""

helps['relay hyco authorization-rule list'] = """
    type: command
    short-summary: shows list of Authorization Rule by Relay Service Hybrid Connection
    examples:
        - name: shows list of Authorization Rule by Relay Service Hybrid Connection
          text: az relay hyco authorization-rule list --resource-group myresourcegroup --namespace-name mynamespace --hybrid-connection-name myhyco
"""

helps['relay hyco authorization-rule keys list'] = """
    type: command
    short-summary: List the keys and connection strings of Authorization Rule for Relay Service Hybrid Connection.
    examples:
        - name: List the keys and connection strings of Authorization Rule for Relay Service Hybrid Connection.
          text: az relay hyco authorization-rule keys list --resource-group myresourcegroup --namespace-name mynamespace --hybrid-connection-name myhyco --name myauthorule
"""

helps['relay hyco authorization-rule keys renew'] = """
    type: command
    short-summary: Regenerate keys of Authorization Rule for Relay Service Hybrid Connection.
    examples:
        - name: Regenerate key of Relay Service Hybrid Connection.
          text: az relay hyco authorization-rule keys renew --resource-group myresourcegroup --namespace-name mynamespace --hybrid-connection-name myhyco --name myauthorule --key PrimaryKey
"""

helps['relay hyco authorization-rule delete'] = """
    type: command
    short-summary: Deletes the Authorization Rule of the given Relay Service Hybrid Connection.
    examples:
        - name: Deletes the Authorization Rule of Relay Service Hybrid Connection.
          text: az relay hyco authorization-rule delete --resource-group myresourcegroup --namespace-name mynamespace --hybrid-connection-name myhyco --name myauthorule
"""
