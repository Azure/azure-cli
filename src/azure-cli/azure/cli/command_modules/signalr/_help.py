# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['signalr'] = """
type: group
short-summary: Manage Azure SignalR Service.
"""

helps['signalr cors'] = """
type: group
short-summary: Manage CORS for Azure SignalR Service.
"""

helps['signalr network-rule'] = """
type: group
short-summary: Manage network rules.
"""

helps['signalr upstream'] = """
type: group
short-summary: Manage upstream settings.
"""

helps['signalr cors add'] = """
type: command
short-summary: Add allowed origins to a SignalR Service
examples:
  - name: Add a list of allowed origins to a SignalR Service
    text: >
        az signalr cors add -n MySignalR -g MyResourceGroup --allowed-origins "http://example1.com" "https://example2.com"
"""

helps['signalr cors list'] = """
type: command
short-summary: List allowed origins of a SignalR Service
"""

helps['signalr cors remove'] = """
type: command
short-summary: Remove allowed origins from a SignalR Service
examples:
  - name: Remove a list of allowed origins from a SignalR Service
    text: >
        az signalr cors remove -n MySignalR -g MyResourceGroup --allowed-origins "http://example1.com" "https://example2.com"
"""

helps['signalr create'] = """
type: command
short-summary: Creates a SignalR Service.
examples:
  - name: Create a SignalR Service with the Standard SKU and serverless mode and enable messaging logs.
    text: >
        az signalr create -n MySignalR -g MyResourceGroup --sku Standard_S1 --unit-count 1 --service-mode Serverless --enable-message-logs True
"""

helps['signalr delete'] = """
type: command
short-summary: Deletes a SignalR Service.
examples:
  - name: Delete a SignalR Service.
    text: >
        az signalr delete -n MySignalR -g MyResourceGroup
"""

helps['signalr key'] = """
type: group
short-summary: Manage keys for Azure SignalR Service.
"""

helps['signalr key list'] = """
type: command
short-summary: List the access keys for a SignalR Service.
examples:
  - name: Get the primary key for a SignalR Service.
    text: >
        az signalr key list -n MySignalR -g MyResourceGroup --query primaryKey -o tsv
"""

helps['signalr key renew'] = """
type: command
short-summary: Regenerate the access key for a SignalR Service.
examples:
  - name: Renew the secondary key for a SignalR Service.
    text: >
        az signalr key renew -n MySignalR -g MyResourceGroup --key-type secondary
"""

helps['signalr list'] = """
type: command
short-summary: Lists all the SignalR Service under the current subscription.
examples:
  - name: List SignalR Service and show the results in a table.
    text: >
        az signalr list -o table
  - name: List SignalR Service in a resource group and show the results in a table.
    text: >
        az signalr list -g MySignalR -o table
"""

helps['signalr restart'] = """
type: command
short-summary: Restart an existing SignalR Service.
examples:
  - name: Restart a SignalR Service instance.
    text: >
        az signalr restart -n MySignalR -g MyResourceGroup
"""

helps['signalr show'] = """
type: command
short-summary: Get the details of a SignalR Service.
examples:
  - name: Get the sku for a SignalR Service.
    text: >
        az signalr show -n MySignalR -g MyResourceGroup --query sku
"""

helps['signalr update'] = """
type: command
short-summary: Update an existing SignalR Service.
examples:
  - name: Update unit count to scale the service.
    text: >
        az signalr update -n MySignalR -g MyResourceGroup --sku Standard_S1 --unit-count 50
  - name: Update service mode.
    text: >
        az signalr update -n MySignalR -g MyResourceGroup --service-mode Serverless
  - name: Update for enabling messaging logs in the service.
    text: >
        az signalr update -n MySignalR -g MyResourceGroup --enable-message-logs True
"""

helps['signalr upstream list'] = """
type: command
short-summary: List upstream settings of an existing SignalR Service.
"""

helps['signalr upstream update'] = """
type: command
short-summary: Update order sensitive upstream settings for an existing SignalR Service.
examples:
  - name: Update two upstream settings to handle messages and connections separately.
    text: >
        az signalr upstream update -n MySignalR -g MyResourceGroup --template url-template="http://host-connections.com" category-pattern="connections" --template url-template="http://host-connections.com" category-pattern="messages"
  - name: Update one upstream setting to handle a specific event in a specific hub.
    text: >
        az signalr upstream update -n MySignalR -g MyResourceGroup --template url-template="http://host.com/{hub}/{event}/{category}" category-pattern="messages" event-pattern="broadcast" hub-pattern="chat"
"""

helps['signalr upstream clear'] = """
type: command
short-summary: List upstream settings of an existing SignalR Service.
"""

helps['signalr network-rule list'] = """
type: command
short-summary: Get the Network access control of SignalR Service.
"""

helps['signalr network-rule update'] = """
type: command
short-summary: Update the Network access control of SignalR Service.
examples:
  - name: Set allowing RESTAPI only for public network.
    text: >
        az signalr network-rule update --public-network -n MySignalR -g MyResourceGroup --allow RESTAPI
  - name: Set allowing client connection and server connection for a private endpoint connection
    text: >
        az signalr network-rule update --connection-name MyPrivateEndpointConnection -n MySignalR -g MyResourceGroup --allow ClientConnection ServerConnection
  - name: Set denying client connection for both public network and private endpoint connections
    text: >
        az signalr network-rule update --public-network --connection-name MyPrivateEndpointConnection1 MyPrivateEndpointConnection2 -n MySignalR -g MyResourceGroup --deny ClientConnection
"""
