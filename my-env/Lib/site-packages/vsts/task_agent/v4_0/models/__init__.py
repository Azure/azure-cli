# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .aad_oauth_token_request import AadOauthTokenRequest
from .aad_oauth_token_result import AadOauthTokenResult
from .authorization_header import AuthorizationHeader
from .azure_subscription import AzureSubscription
from .azure_subscription_query_result import AzureSubscriptionQueryResult
from .data_source import DataSource
from .data_source_binding import DataSourceBinding
from .data_source_binding_base import DataSourceBindingBase
from .data_source_details import DataSourceDetails
from .dependency_binding import DependencyBinding
from .dependency_data import DependencyData
from .depends_on import DependsOn
from .deployment_group import DeploymentGroup
from .deployment_group_metrics import DeploymentGroupMetrics
from .deployment_group_reference import DeploymentGroupReference
from .deployment_machine import DeploymentMachine
from .deployment_machine_group import DeploymentMachineGroup
from .deployment_machine_group_reference import DeploymentMachineGroupReference
from .endpoint_authorization import EndpointAuthorization
from .endpoint_url import EndpointUrl
from .help_link import HelpLink
from .identity_ref import IdentityRef
from .input_descriptor import InputDescriptor
from .input_validation import InputValidation
from .input_validation_request import InputValidationRequest
from .input_value import InputValue
from .input_values import InputValues
from .input_values_error import InputValuesError
from .metrics_column_meta_data import MetricsColumnMetaData
from .metrics_columns_header import MetricsColumnsHeader
from .metrics_row import MetricsRow
from .package_metadata import PackageMetadata
from .package_version import PackageVersion
from .project_reference import ProjectReference
from .publish_task_group_metadata import PublishTaskGroupMetadata
from .reference_links import ReferenceLinks
from .result_transformation_details import ResultTransformationDetails
from .secure_file import SecureFile
from .service_endpoint import ServiceEndpoint
from .service_endpoint_authentication_scheme import ServiceEndpointAuthenticationScheme
from .service_endpoint_details import ServiceEndpointDetails
from .service_endpoint_execution_data import ServiceEndpointExecutionData
from .service_endpoint_execution_record import ServiceEndpointExecutionRecord
from .service_endpoint_execution_records_input import ServiceEndpointExecutionRecordsInput
from .service_endpoint_request import ServiceEndpointRequest
from .service_endpoint_request_result import ServiceEndpointRequestResult
from .service_endpoint_type import ServiceEndpointType
from .task_agent import TaskAgent
from .task_agent_authorization import TaskAgentAuthorization
from .task_agent_job_request import TaskAgentJobRequest
from .task_agent_message import TaskAgentMessage
from .task_agent_pool import TaskAgentPool
from .task_agent_pool_maintenance_definition import TaskAgentPoolMaintenanceDefinition
from .task_agent_pool_maintenance_job import TaskAgentPoolMaintenanceJob
from .task_agent_pool_maintenance_job_target_agent import TaskAgentPoolMaintenanceJobTargetAgent
from .task_agent_pool_maintenance_options import TaskAgentPoolMaintenanceOptions
from .task_agent_pool_maintenance_retention_policy import TaskAgentPoolMaintenanceRetentionPolicy
from .task_agent_pool_maintenance_schedule import TaskAgentPoolMaintenanceSchedule
from .task_agent_pool_reference import TaskAgentPoolReference
from .task_agent_public_key import TaskAgentPublicKey
from .task_agent_queue import TaskAgentQueue
from .task_agent_reference import TaskAgentReference
from .task_agent_session import TaskAgentSession
from .task_agent_session_key import TaskAgentSessionKey
from .task_agent_update import TaskAgentUpdate
from .task_agent_update_reason import TaskAgentUpdateReason
from .task_definition import TaskDefinition
from .task_definition_endpoint import TaskDefinitionEndpoint
from .task_definition_reference import TaskDefinitionReference
from .task_execution import TaskExecution
from .task_group import TaskGroup
from .task_group_definition import TaskGroupDefinition
from .task_group_revision import TaskGroupRevision
from .task_group_step import TaskGroupStep
from .task_hub_license_details import TaskHubLicenseDetails
from .task_input_definition import TaskInputDefinition
from .task_input_definition_base import TaskInputDefinitionBase
from .task_input_validation import TaskInputValidation
from .task_orchestration_owner import TaskOrchestrationOwner
from .task_output_variable import TaskOutputVariable
from .task_package_metadata import TaskPackageMetadata
from .task_reference import TaskReference
from .task_source_definition import TaskSourceDefinition
from .task_source_definition_base import TaskSourceDefinitionBase
from .task_version import TaskVersion
from .validation_item import ValidationItem
from .variable_group import VariableGroup
from .variable_group_provider_data import VariableGroupProviderData
from .variable_value import VariableValue

__all__ = [
    'AadOauthTokenRequest',
    'AadOauthTokenResult',
    'AuthorizationHeader',
    'AzureSubscription',
    'AzureSubscriptionQueryResult',
    'DataSource',
    'DataSourceBinding',
    'DataSourceBindingBase',
    'DataSourceDetails',
    'DependencyBinding',
    'DependencyData',
    'DependsOn',
    'DeploymentGroup',
    'DeploymentGroupMetrics',
    'DeploymentGroupReference',
    'DeploymentMachine',
    'DeploymentMachineGroup',
    'DeploymentMachineGroupReference',
    'EndpointAuthorization',
    'EndpointUrl',
    'HelpLink',
    'IdentityRef',
    'InputDescriptor',
    'InputValidation',
    'InputValidationRequest',
    'InputValue',
    'InputValues',
    'InputValuesError',
    'MetricsColumnMetaData',
    'MetricsColumnsHeader',
    'MetricsRow',
    'PackageMetadata',
    'PackageVersion',
    'ProjectReference',
    'PublishTaskGroupMetadata',
    'ReferenceLinks',
    'ResultTransformationDetails',
    'SecureFile',
    'ServiceEndpoint',
    'ServiceEndpointAuthenticationScheme',
    'ServiceEndpointDetails',
    'ServiceEndpointExecutionData',
    'ServiceEndpointExecutionRecord',
    'ServiceEndpointExecutionRecordsInput',
    'ServiceEndpointRequest',
    'ServiceEndpointRequestResult',
    'ServiceEndpointType',
    'TaskAgent',
    'TaskAgentAuthorization',
    'TaskAgentJobRequest',
    'TaskAgentMessage',
    'TaskAgentPool',
    'TaskAgentPoolMaintenanceDefinition',
    'TaskAgentPoolMaintenanceJob',
    'TaskAgentPoolMaintenanceJobTargetAgent',
    'TaskAgentPoolMaintenanceOptions',
    'TaskAgentPoolMaintenanceRetentionPolicy',
    'TaskAgentPoolMaintenanceSchedule',
    'TaskAgentPoolReference',
    'TaskAgentPublicKey',
    'TaskAgentQueue',
    'TaskAgentReference',
    'TaskAgentSession',
    'TaskAgentSessionKey',
    'TaskAgentUpdate',
    'TaskAgentUpdateReason',
    'TaskDefinition',
    'TaskDefinitionEndpoint',
    'TaskDefinitionReference',
    'TaskExecution',
    'TaskGroup',
    'TaskGroupDefinition',
    'TaskGroupRevision',
    'TaskGroupStep',
    'TaskHubLicenseDetails',
    'TaskInputDefinition',
    'TaskInputDefinitionBase',
    'TaskInputValidation',
    'TaskOrchestrationOwner',
    'TaskOutputVariable',
    'TaskPackageMetadata',
    'TaskReference',
    'TaskSourceDefinition',
    'TaskSourceDefinitionBase',
    'TaskVersion',
    'ValidationItem',
    'VariableGroup',
    'VariableGroupProviderData',
    'VariableValue',
]
