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
    Type of the routing endpoint.
    """
    EventHub = 'eventhub'
    ServiceBusQueue = 'servicebusqueue'
    ServiceBusTopic = 'servicebustopic'
    AzureStorageContainer = 'azurestoragecontainer'


# pylint: disable=too-few-public-methods
class RouteSourceType(Enum):
    """
    Type of the route source.
    """
    Invalid = 'invalid'
    DeviceMessages = 'devicemessages'
    TwinChangeEvents = 'twinchangeevents'
    DeviceLifecycleEvents = 'devicelifecycleevents'
    DeviceJobLifecycleEvents = 'devicejoblifecycleevents'
    DigitalTwinChangeEvents = 'digitaltwinchangeevents'
    DeviceConnectionStateEvents = 'deviceconnectionstateevents'


# pylint: disable=too-few-public-methods
class EncodingFormat(Enum):
    """
    Type of the encoding format for the container.
    """
    JSON = 'json'
    AVRO = 'avro'


# pylint: disable=too-few-public-methods
class RenewKeyType(Enum):
    """
    Type of the RegenerateKey for the authorization policy.
    """
    Primary = 'primary'
    Secondary = 'secondary'
    Swap = 'swap'


# pylint: disable=too-few-public-methods
class AuthenticationType(Enum):
    """
    Type of the Authentication for the routing endpoint.
    """
    KeyBased = 'keyBased'
    IdentityBased = 'identityBased'


# pylint: disable=too-few-public-methods
class IdentityType(Enum):
    """
    Type of managed identity for the IoT Hub.
    """
    system_assigned = "SystemAssigned"
    user_assigned = "UserAssigned"
    system_assigned_user_assigned = "SystemAssigned, UserAssigned"
    none = "None"
