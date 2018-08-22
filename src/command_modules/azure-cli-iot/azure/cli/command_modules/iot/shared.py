# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
shared: Define shared data types(enums).

"""

from enum import Enum


# pylint: disable=too-few-public-methods
class EndpointType(Enum):
    """
    Type of the Routing Endpoint.
    """
    EventHub = 'eventhub'
    ServiceBusQueue = 'servicebusqueue'
    ServiceBusTopic = 'servicebustopic'
    AzureStorageContainer = 'azurestoragecontainer'
