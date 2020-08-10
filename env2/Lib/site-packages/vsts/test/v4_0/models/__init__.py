# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .aggregated_data_for_result_trend import AggregatedDataForResultTrend
from .aggregated_results_analysis import AggregatedResultsAnalysis
from .aggregated_results_by_outcome import AggregatedResultsByOutcome
from .aggregated_results_difference import AggregatedResultsDifference
from .build_configuration import BuildConfiguration
from .build_coverage import BuildCoverage
from .build_reference import BuildReference
from .clone_operation_information import CloneOperationInformation
from .clone_options import CloneOptions
from .clone_statistics import CloneStatistics
from .code_coverage_data import CodeCoverageData
from .code_coverage_statistics import CodeCoverageStatistics
from .code_coverage_summary import CodeCoverageSummary
from .coverage_statistics import CoverageStatistics
from .custom_test_field import CustomTestField
from .custom_test_field_definition import CustomTestFieldDefinition
from .dtl_environment_details import DtlEnvironmentDetails
from .failing_since import FailingSince
from .function_coverage import FunctionCoverage
from .identity_ref import IdentityRef
from .last_result_details import LastResultDetails
from .linked_work_items_query import LinkedWorkItemsQuery
from .linked_work_items_query_result import LinkedWorkItemsQueryResult
from .module_coverage import ModuleCoverage
from .name_value_pair import NameValuePair
from .plan_update_model import PlanUpdateModel
from .point_assignment import PointAssignment
from .points_filter import PointsFilter
from .point_update_model import PointUpdateModel
from .property_bag import PropertyBag
from .query_model import QueryModel
from .release_environment_definition_reference import ReleaseEnvironmentDefinitionReference
from .release_reference import ReleaseReference
from .result_retention_settings import ResultRetentionSettings
from .results_filter import ResultsFilter
from .run_create_model import RunCreateModel
from .run_filter import RunFilter
from .run_statistic import RunStatistic
from .run_update_model import RunUpdateModel
from .shallow_reference import ShallowReference
from .shared_step_model import SharedStepModel
from .suite_create_model import SuiteCreateModel
from .suite_entry import SuiteEntry
from .suite_entry_update_model import SuiteEntryUpdateModel
from .suite_test_case import SuiteTestCase
from .team_context import TeamContext
from .team_project_reference import TeamProjectReference
from .test_action_result_model import TestActionResultModel
from .test_attachment import TestAttachment
from .test_attachment_reference import TestAttachmentReference
from .test_attachment_request_model import TestAttachmentRequestModel
from .test_case_result import TestCaseResult
from .test_case_result_attachment_model import TestCaseResultAttachmentModel
from .test_case_result_identifier import TestCaseResultIdentifier
from .test_case_result_update_model import TestCaseResultUpdateModel
from .test_configuration import TestConfiguration
from .test_environment import TestEnvironment
from .test_failure_details import TestFailureDetails
from .test_failures_analysis import TestFailuresAnalysis
from .test_iteration_details_model import TestIterationDetailsModel
from .test_message_log_details import TestMessageLogDetails
from .test_method import TestMethod
from .test_operation_reference import TestOperationReference
from .test_plan import TestPlan
from .test_plan_clone_request import TestPlanCloneRequest
from .test_point import TestPoint
from .test_points_query import TestPointsQuery
from .test_resolution_state import TestResolutionState
from .test_result_create_model import TestResultCreateModel
from .test_result_document import TestResultDocument
from .test_result_history import TestResultHistory
from .test_result_history_details_for_group import TestResultHistoryDetailsForGroup
from .test_result_model_base import TestResultModelBase
from .test_result_parameter_model import TestResultParameterModel
from .test_result_payload import TestResultPayload
from .test_results_context import TestResultsContext
from .test_results_details import TestResultsDetails
from .test_results_details_for_group import TestResultsDetailsForGroup
from .test_results_query import TestResultsQuery
from .test_result_summary import TestResultSummary
from .test_result_trend_filter import TestResultTrendFilter
from .test_run import TestRun
from .test_run_coverage import TestRunCoverage
from .test_run_statistic import TestRunStatistic
from .test_session import TestSession
from .test_settings import TestSettings
from .test_suite import TestSuite
from .test_suite_clone_request import TestSuiteCloneRequest
from .test_summary_for_work_item import TestSummaryForWorkItem
from .test_to_work_item_links import TestToWorkItemLinks
from .test_variable import TestVariable
from .work_item_reference import WorkItemReference
from .work_item_to_test_links import WorkItemToTestLinks

__all__ = [
    'AggregatedDataForResultTrend',
    'AggregatedResultsAnalysis',
    'AggregatedResultsByOutcome',
    'AggregatedResultsDifference',
    'BuildConfiguration',
    'BuildCoverage',
    'BuildReference',
    'CloneOperationInformation',
    'CloneOptions',
    'CloneStatistics',
    'CodeCoverageData',
    'CodeCoverageStatistics',
    'CodeCoverageSummary',
    'CoverageStatistics',
    'CustomTestField',
    'CustomTestFieldDefinition',
    'DtlEnvironmentDetails',
    'FailingSince',
    'FunctionCoverage',
    'IdentityRef',
    'LastResultDetails',
    'LinkedWorkItemsQuery',
    'LinkedWorkItemsQueryResult',
    'ModuleCoverage',
    'NameValuePair',
    'PlanUpdateModel',
    'PointAssignment',
    'PointsFilter',
    'PointUpdateModel',
    'PropertyBag',
    'QueryModel',
    'ReleaseEnvironmentDefinitionReference',
    'ReleaseReference',
    'ResultRetentionSettings',
    'ResultsFilter',
    'RunCreateModel',
    'RunFilter',
    'RunStatistic',
    'RunUpdateModel',
    'ShallowReference',
    'SharedStepModel',
    'SuiteCreateModel',
    'SuiteEntry',
    'SuiteEntryUpdateModel',
    'SuiteTestCase',
    'TeamContext',
    'TeamProjectReference',
    'TestActionResultModel',
    'TestAttachment',
    'TestAttachmentReference',
    'TestAttachmentRequestModel',
    'TestCaseResult',
    'TestCaseResultAttachmentModel',
    'TestCaseResultIdentifier',
    'TestCaseResultUpdateModel',
    'TestConfiguration',
    'TestEnvironment',
    'TestFailureDetails',
    'TestFailuresAnalysis',
    'TestIterationDetailsModel',
    'TestMessageLogDetails',
    'TestMethod',
    'TestOperationReference',
    'TestPlan',
    'TestPlanCloneRequest',
    'TestPoint',
    'TestPointsQuery',
    'TestResolutionState',
    'TestResultCreateModel',
    'TestResultDocument',
    'TestResultHistory',
    'TestResultHistoryDetailsForGroup',
    'TestResultModelBase',
    'TestResultParameterModel',
    'TestResultPayload',
    'TestResultsContext',
    'TestResultsDetails',
    'TestResultsDetailsForGroup',
    'TestResultsQuery',
    'TestResultSummary',
    'TestResultTrendFilter',
    'TestRun',
    'TestRunCoverage',
    'TestRunStatistic',
    'TestSession',
    'TestSettings',
    'TestSuite',
    'TestSuiteCloneRequest',
    'TestSummaryForWorkItem',
    'TestToWorkItemLinks',
    'TestVariable',
    'WorkItemReference',
    'WorkItemToTestLinks',
]
