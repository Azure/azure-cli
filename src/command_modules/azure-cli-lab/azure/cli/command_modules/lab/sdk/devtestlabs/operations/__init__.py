# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from .lab_operations import LabOperations
from .global_schedule_operations import GlobalScheduleOperations
from .artifact_source_operations import ArtifactSourceOperations
from .arm_template_operations import ArmTemplateOperations
from .artifact_operations import ArtifactOperations
from .cost_operations import CostOperations
from .custom_image_operations import CustomImageOperations
from .formula_operations import FormulaOperations
from .gallery_image_operations import GalleryImageOperations
from .notification_channel_operations import NotificationChannelOperations
from .policy_set_operations import PolicySetOperations
from .policy_operations import PolicyOperations
from .schedule_operations import ScheduleOperations
from .service_runner_operations import ServiceRunnerOperations
from .user_operations import UserOperations
from .disk_operations import DiskOperations
from .environment_operations import EnvironmentOperations
from .secret_operations import SecretOperations
from .virtual_machine_operations import VirtualMachineOperations
from .virtual_machine_schedule_operations import VirtualMachineScheduleOperations
from .virtual_network_operations import VirtualNetworkOperations

__all__ = [
    'LabOperations',
    'GlobalScheduleOperations',
    'ArtifactSourceOperations',
    'ArmTemplateOperations',
    'ArtifactOperations',
    'CostOperations',
    'CustomImageOperations',
    'FormulaOperations',
    'GalleryImageOperations',
    'NotificationChannelOperations',
    'PolicySetOperations',
    'PolicyOperations',
    'ScheduleOperations',
    'ServiceRunnerOperations',
    'UserOperations',
    'DiskOperations',
    'EnvironmentOperations',
    'SecretOperations',
    'VirtualMachineOperations',
    'VirtualMachineScheduleOperations',
    'VirtualNetworkOperations',
]
