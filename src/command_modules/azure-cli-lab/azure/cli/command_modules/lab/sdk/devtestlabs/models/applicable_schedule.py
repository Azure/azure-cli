# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class ApplicableSchedule(Model):
    """ApplicableSchedule.

    :param lab_vms_shutdown: The auto-shutdown schedule, if one has been set
     at the lab or lab resource level.
    :type lab_vms_shutdown: :class:`Schedule
     <azure.mgmt.devtestlabs.models.Schedule>`
    :param lab_vms_startup: The auto-startup schedule, if one has been set at
     the lab or lab resource level.
    :type lab_vms_startup: :class:`Schedule
     <azure.mgmt.devtestlabs.models.Schedule>`
    :param id: The identifier of the resource.
    :type id: str
    :param name: The name of the resource.
    :type name: str
    :param type: The type of the resource.
    :type type: str
    :param location: The location of the resource.
    :type location: str
    :param tags: The tags of the resource.
    :type tags: dict
    """

    _attribute_map = {
        'lab_vms_shutdown': {'key': 'properties.labVmsShutdown', 'type': 'Schedule'},
        'lab_vms_startup': {'key': 'properties.labVmsStartup', 'type': 'Schedule'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'location': {'key': 'location', 'type': 'str'},
        'tags': {'key': 'tags', 'type': '{str}'},
    }

    def __init__(self, lab_vms_shutdown=None, lab_vms_startup=None, id=None, name=None, type=None, location=None, tags=None):
        self.lab_vms_shutdown = lab_vms_shutdown
        self.lab_vms_startup = lab_vms_startup
        self.id = id
        self.name = name
        self.type = type
        self.location = location
        self.tags = tags
