# coding=utf-8
# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.service_client import ServiceClient
from msrest import Serializer, Deserializer
from msrestazure import AzureConfiguration
from .version import VERSION
from .operations.lab_operations import LabOperations
from .operations.global_schedule_operations import GlobalScheduleOperations
from .operations.artifact_source_operations import ArtifactSourceOperations
from .operations.arm_template_operations import ArmTemplateOperations
from .operations.artifact_operations import ArtifactOperations
from .operations.cost_operations import CostOperations
from .operations.custom_image_operations import CustomImageOperations
from .operations.formula_operations import FormulaOperations
from .operations.gallery_image_operations import GalleryImageOperations
from .operations.notification_channel_operations import NotificationChannelOperations
from .operations.policy_set_operations import PolicySetOperations
from .operations.policy_operations import PolicyOperations
from .operations.schedule_operations import ScheduleOperations
from .operations.service_runner_operations import ServiceRunnerOperations
from .operations.user_operations import UserOperations
from .operations.disk_operations import DiskOperations
from .operations.environment_operations import EnvironmentOperations
from .operations.secret_operations import SecretOperations
from .operations.virtual_machine_operations import VirtualMachineOperations
from .operations.virtual_machine_schedule_operations import VirtualMachineScheduleOperations
from .operations.virtual_network_operations import VirtualNetworkOperations
from . import models


class DevTestLabsClientConfiguration(AzureConfiguration):
    """Configuration for DevTestLabsClient
    Note that all parameters used to create this instance are saved as instance
    attributes.

    :param credentials: Credentials needed for the client to connect to Azure.
    :type credentials: :mod:`A msrestazure Credentials
     object<msrestazure.azure_active_directory>`
    :param subscription_id: The subscription ID.
    :type subscription_id: str
    :param str base_url: Service URL
    """

    def __init__(
            self, credentials, subscription_id, base_url=None):

        if credentials is None:
            raise ValueError("Parameter 'credentials' must not be None.")
        if subscription_id is None:
            raise ValueError("Parameter 'subscription_id' must not be None.")
        if not isinstance(subscription_id, str):
            raise TypeError("Parameter 'subscription_id' must be str.")
        if not base_url:
            base_url = 'https://management.azure.com'

        super(DevTestLabsClientConfiguration, self).__init__(base_url)

        self.add_user_agent('devtestlabs/{}'.format(VERSION))
        self.add_user_agent('Azure-SDK-For-Python')

        self.credentials = credentials
        self.subscription_id = subscription_id


class DevTestLabsClient(object):
    """The DevTest Labs Client.

    :ivar config: Configuration for client.
    :vartype config: DevTestLabsClientConfiguration

    :ivar lab: Lab operations
    :vartype lab: .operations.LabOperations
    :ivar global_schedule: GlobalSchedule operations
    :vartype global_schedule: .operations.GlobalScheduleOperations
    :ivar artifact_source: ArtifactSource operations
    :vartype artifact_source: .operations.ArtifactSourceOperations
    :ivar arm_template: ArmTemplate operations
    :vartype arm_template: .operations.ArmTemplateOperations
    :ivar artifact: Artifact operations
    :vartype artifact: .operations.ArtifactOperations
    :ivar cost: Cost operations
    :vartype cost: .operations.CostOperations
    :ivar custom_image: CustomImage operations
    :vartype custom_image: .operations.CustomImageOperations
    :ivar formula: Formula operations
    :vartype formula: .operations.FormulaOperations
    :ivar gallery_image: GalleryImage operations
    :vartype gallery_image: .operations.GalleryImageOperations
    :ivar notification_channel: NotificationChannel operations
    :vartype notification_channel: .operations.NotificationChannelOperations
    :ivar policy_set: PolicySet operations
    :vartype policy_set: .operations.PolicySetOperations
    :ivar policy: Policy operations
    :vartype policy: .operations.PolicyOperations
    :ivar schedule: Schedule operations
    :vartype schedule: .operations.ScheduleOperations
    :ivar service_runner: ServiceRunner operations
    :vartype service_runner: .operations.ServiceRunnerOperations
    :ivar user: User operations
    :vartype user: .operations.UserOperations
    :ivar disk: Disk operations
    :vartype disk: .operations.DiskOperations
    :ivar environment: Environment operations
    :vartype environment: .operations.EnvironmentOperations
    :ivar secret: Secret operations
    :vartype secret: .operations.SecretOperations
    :ivar virtual_machine: VirtualMachine operations
    :vartype virtual_machine: .operations.VirtualMachineOperations
    :ivar virtual_machine_schedule: VirtualMachineSchedule operations
    :vartype virtual_machine_schedule: .operations.VirtualMachineScheduleOperations
    :ivar virtual_network: VirtualNetwork operations
    :vartype virtual_network: .operations.VirtualNetworkOperations

    :param credentials: Credentials needed for the client to connect to Azure.
    :type credentials: :mod:`A msrestazure Credentials
     object<msrestazure.azure_active_directory>`
    :param subscription_id: The subscription ID.
    :type subscription_id: str
    :param str base_url: Service URL
    """

    def __init__(
            self, credentials, subscription_id, base_url=None):

        self.config = DevTestLabsClientConfiguration(credentials, subscription_id, base_url)
        self._client = ServiceClient(self.config.credentials, self.config)

        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self.api_version = '2016-05-15'
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

        self.lab = LabOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.global_schedule = GlobalScheduleOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.artifact_source = ArtifactSourceOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.arm_template = ArmTemplateOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.artifact = ArtifactOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.cost = CostOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.custom_image = CustomImageOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.formula = FormulaOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.gallery_image = GalleryImageOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.notification_channel = NotificationChannelOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.policy_set = PolicySetOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.policy = PolicyOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.schedule = ScheduleOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.service_runner = ServiceRunnerOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.user = UserOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.disk = DiskOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.environment = EnvironmentOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.secret = SecretOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.virtual_machine = VirtualMachineOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.virtual_machine_schedule = VirtualMachineScheduleOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.virtual_network = VirtualNetworkOperations(
            self._client, self.config, self._serialize, self._deserialize)
