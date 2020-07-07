# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest import Serializer, Deserializer
from ...vss_client import VssClient
from . import models


class TestClient(VssClient):
    """Test
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(TestClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = 'c2aa639c-3ccc-4740-b3b6-ce2a1e1d984e'

    def get_action_results(self, project, run_id, test_case_result_id, iteration_id, action_path=None):
        """GetActionResults.
        :param str project: Project ID or project name
        :param int run_id:
        :param int test_case_result_id:
        :param int iteration_id:
        :param str action_path:
        :rtype: [TestActionResultModel]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        if test_case_result_id is not None:
            route_values['testCaseResultId'] = self._serialize.url('test_case_result_id', test_case_result_id, 'int')
        if iteration_id is not None:
            route_values['iterationId'] = self._serialize.url('iteration_id', iteration_id, 'int')
        if action_path is not None:
            route_values['actionPath'] = self._serialize.url('action_path', action_path, 'str')
        response = self._send(http_method='GET',
                              location_id='eaf40c31-ff84-4062-aafd-d5664be11a37',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('[TestActionResultModel]', self._unwrap_collection(response))

    def create_test_iteration_result_attachment(self, attachment_request_model, project, run_id, test_case_result_id, iteration_id, action_path=None):
        """CreateTestIterationResultAttachment.
        [Preview API]
        :param :class:`<TestAttachmentRequestModel> <test.v4_0.models.TestAttachmentRequestModel>` attachment_request_model:
        :param str project: Project ID or project name
        :param int run_id:
        :param int test_case_result_id:
        :param int iteration_id:
        :param str action_path:
        :rtype: :class:`<TestAttachmentReference> <test.v4_0.models.TestAttachmentReference>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        if test_case_result_id is not None:
            route_values['testCaseResultId'] = self._serialize.url('test_case_result_id', test_case_result_id, 'int')
        query_parameters = {}
        if iteration_id is not None:
            query_parameters['iterationId'] = self._serialize.query('iteration_id', iteration_id, 'int')
        if action_path is not None:
            query_parameters['actionPath'] = self._serialize.query('action_path', action_path, 'str')
        content = self._serialize.body(attachment_request_model, 'TestAttachmentRequestModel')
        response = self._send(http_method='POST',
                              location_id='2bffebe9-2f0f-4639-9af8-56129e9fed2d',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('TestAttachmentReference', response)

    def create_test_result_attachment(self, attachment_request_model, project, run_id, test_case_result_id):
        """CreateTestResultAttachment.
        [Preview API]
        :param :class:`<TestAttachmentRequestModel> <test.v4_0.models.TestAttachmentRequestModel>` attachment_request_model:
        :param str project: Project ID or project name
        :param int run_id:
        :param int test_case_result_id:
        :rtype: :class:`<TestAttachmentReference> <test.v4_0.models.TestAttachmentReference>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        if test_case_result_id is not None:
            route_values['testCaseResultId'] = self._serialize.url('test_case_result_id', test_case_result_id, 'int')
        content = self._serialize.body(attachment_request_model, 'TestAttachmentRequestModel')
        response = self._send(http_method='POST',
                              location_id='2bffebe9-2f0f-4639-9af8-56129e9fed2d',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TestAttachmentReference', response)

    def get_test_result_attachment_content(self, project, run_id, test_case_result_id, attachment_id, **kwargs):
        """GetTestResultAttachmentContent.
        [Preview API] Returns a test result attachment
        :param str project: Project ID or project name
        :param int run_id:
        :param int test_case_result_id:
        :param int attachment_id:
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        if test_case_result_id is not None:
            route_values['testCaseResultId'] = self._serialize.url('test_case_result_id', test_case_result_id, 'int')
        if attachment_id is not None:
            route_values['attachmentId'] = self._serialize.url('attachment_id', attachment_id, 'int')
        response = self._send(http_method='GET',
                              location_id='2bffebe9-2f0f-4639-9af8-56129e9fed2d',
                              version='4.0-preview.1',
                              route_values=route_values,
                              accept_media_type='application/octet-stream')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_test_result_attachments(self, project, run_id, test_case_result_id):
        """GetTestResultAttachments.
        [Preview API] Returns attachment references for test result.
        :param str project: Project ID or project name
        :param int run_id:
        :param int test_case_result_id:
        :rtype: [TestAttachment]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        if test_case_result_id is not None:
            route_values['testCaseResultId'] = self._serialize.url('test_case_result_id', test_case_result_id, 'int')
        response = self._send(http_method='GET',
                              location_id='2bffebe9-2f0f-4639-9af8-56129e9fed2d',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[TestAttachment]', self._unwrap_collection(response))

    def get_test_result_attachment_zip(self, project, run_id, test_case_result_id, attachment_id, **kwargs):
        """GetTestResultAttachmentZip.
        [Preview API] Returns a test result attachment
        :param str project: Project ID or project name
        :param int run_id:
        :param int test_case_result_id:
        :param int attachment_id:
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        if test_case_result_id is not None:
            route_values['testCaseResultId'] = self._serialize.url('test_case_result_id', test_case_result_id, 'int')
        if attachment_id is not None:
            route_values['attachmentId'] = self._serialize.url('attachment_id', attachment_id, 'int')
        response = self._send(http_method='GET',
                              location_id='2bffebe9-2f0f-4639-9af8-56129e9fed2d',
                              version='4.0-preview.1',
                              route_values=route_values,
                              accept_media_type='application/zip')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def create_test_run_attachment(self, attachment_request_model, project, run_id):
        """CreateTestRunAttachment.
        [Preview API]
        :param :class:`<TestAttachmentRequestModel> <test.v4_0.models.TestAttachmentRequestModel>` attachment_request_model:
        :param str project: Project ID or project name
        :param int run_id:
        :rtype: :class:`<TestAttachmentReference> <test.v4_0.models.TestAttachmentReference>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        content = self._serialize.body(attachment_request_model, 'TestAttachmentRequestModel')
        response = self._send(http_method='POST',
                              location_id='4f004af4-a507-489c-9b13-cb62060beb11',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TestAttachmentReference', response)

    def get_test_run_attachment_content(self, project, run_id, attachment_id, **kwargs):
        """GetTestRunAttachmentContent.
        [Preview API] Returns a test run attachment
        :param str project: Project ID or project name
        :param int run_id:
        :param int attachment_id:
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        if attachment_id is not None:
            route_values['attachmentId'] = self._serialize.url('attachment_id', attachment_id, 'int')
        response = self._send(http_method='GET',
                              location_id='4f004af4-a507-489c-9b13-cb62060beb11',
                              version='4.0-preview.1',
                              route_values=route_values,
                              accept_media_type='application/octet-stream')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_test_run_attachments(self, project, run_id):
        """GetTestRunAttachments.
        [Preview API] Returns attachment references for test run.
        :param str project: Project ID or project name
        :param int run_id:
        :rtype: [TestAttachment]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        response = self._send(http_method='GET',
                              location_id='4f004af4-a507-489c-9b13-cb62060beb11',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[TestAttachment]', self._unwrap_collection(response))

    def get_test_run_attachment_zip(self, project, run_id, attachment_id, **kwargs):
        """GetTestRunAttachmentZip.
        [Preview API] Returns a test run attachment
        :param str project: Project ID or project name
        :param int run_id:
        :param int attachment_id:
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        if attachment_id is not None:
            route_values['attachmentId'] = self._serialize.url('attachment_id', attachment_id, 'int')
        response = self._send(http_method='GET',
                              location_id='4f004af4-a507-489c-9b13-cb62060beb11',
                              version='4.0-preview.1',
                              route_values=route_values,
                              accept_media_type='application/zip')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_bugs_linked_to_test_result(self, project, run_id, test_case_result_id):
        """GetBugsLinkedToTestResult.
        [Preview API]
        :param str project: Project ID or project name
        :param int run_id:
        :param int test_case_result_id:
        :rtype: [WorkItemReference]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        if test_case_result_id is not None:
            route_values['testCaseResultId'] = self._serialize.url('test_case_result_id', test_case_result_id, 'int')
        response = self._send(http_method='GET',
                              location_id='6de20ca2-67de-4faf-97fa-38c5d585eb00',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[WorkItemReference]', self._unwrap_collection(response))

    def get_clone_information(self, project, clone_operation_id, include_details=None):
        """GetCloneInformation.
        [Preview API]
        :param str project: Project ID or project name
        :param int clone_operation_id:
        :param bool include_details:
        :rtype: :class:`<CloneOperationInformation> <test.v4_0.models.CloneOperationInformation>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if clone_operation_id is not None:
            route_values['cloneOperationId'] = self._serialize.url('clone_operation_id', clone_operation_id, 'int')
        query_parameters = {}
        if include_details is not None:
            query_parameters['$includeDetails'] = self._serialize.query('include_details', include_details, 'bool')
        response = self._send(http_method='GET',
                              location_id='5b9d6320-abed-47a5-a151-cd6dc3798be6',
                              version='4.0-preview.2',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('CloneOperationInformation', response)

    def clone_test_plan(self, clone_request_body, project, plan_id):
        """CloneTestPlan.
        [Preview API]
        :param :class:`<TestPlanCloneRequest> <test.v4_0.models.TestPlanCloneRequest>` clone_request_body:
        :param str project: Project ID or project name
        :param int plan_id:
        :rtype: :class:`<CloneOperationInformation> <test.v4_0.models.CloneOperationInformation>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'int')
        content = self._serialize.body(clone_request_body, 'TestPlanCloneRequest')
        response = self._send(http_method='POST',
                              location_id='edc3ef4b-8460-4e86-86fa-8e4f5e9be831',
                              version='4.0-preview.2',
                              route_values=route_values,
                              content=content)
        return self._deserialize('CloneOperationInformation', response)

    def clone_test_suite(self, clone_request_body, project, plan_id, source_suite_id):
        """CloneTestSuite.
        [Preview API]
        :param :class:`<TestSuiteCloneRequest> <test.v4_0.models.TestSuiteCloneRequest>` clone_request_body:
        :param str project: Project ID or project name
        :param int plan_id:
        :param int source_suite_id:
        :rtype: :class:`<CloneOperationInformation> <test.v4_0.models.CloneOperationInformation>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'int')
        if source_suite_id is not None:
            route_values['sourceSuiteId'] = self._serialize.url('source_suite_id', source_suite_id, 'int')
        content = self._serialize.body(clone_request_body, 'TestSuiteCloneRequest')
        response = self._send(http_method='POST',
                              location_id='751e4ab5-5bf6-4fb5-9d5d-19ef347662dd',
                              version='4.0-preview.2',
                              route_values=route_values,
                              content=content)
        return self._deserialize('CloneOperationInformation', response)

    def get_build_code_coverage(self, project, build_id, flags):
        """GetBuildCodeCoverage.
        [Preview API]
        :param str project: Project ID or project name
        :param int build_id:
        :param int flags:
        :rtype: [BuildCoverage]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if build_id is not None:
            query_parameters['buildId'] = self._serialize.query('build_id', build_id, 'int')
        if flags is not None:
            query_parameters['flags'] = self._serialize.query('flags', flags, 'int')
        response = self._send(http_method='GET',
                              location_id='77560e8a-4e8c-4d59-894e-a5f264c24444',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[BuildCoverage]', self._unwrap_collection(response))

    def get_code_coverage_summary(self, project, build_id, delta_build_id=None):
        """GetCodeCoverageSummary.
        [Preview API]
        :param str project: Project ID or project name
        :param int build_id:
        :param int delta_build_id:
        :rtype: :class:`<CodeCoverageSummary> <test.v4_0.models.CodeCoverageSummary>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if build_id is not None:
            query_parameters['buildId'] = self._serialize.query('build_id', build_id, 'int')
        if delta_build_id is not None:
            query_parameters['deltaBuildId'] = self._serialize.query('delta_build_id', delta_build_id, 'int')
        response = self._send(http_method='GET',
                              location_id='77560e8a-4e8c-4d59-894e-a5f264c24444',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('CodeCoverageSummary', response)

    def update_code_coverage_summary(self, coverage_data, project, build_id):
        """UpdateCodeCoverageSummary.
        [Preview API] http://(tfsserver):8080/tfs/DefaultCollection/_apis/test/CodeCoverage?buildId=10 Request: Json of code coverage summary
        :param :class:`<CodeCoverageData> <test.v4_0.models.CodeCoverageData>` coverage_data:
        :param str project: Project ID or project name
        :param int build_id:
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if build_id is not None:
            query_parameters['buildId'] = self._serialize.query('build_id', build_id, 'int')
        content = self._serialize.body(coverage_data, 'CodeCoverageData')
        self._send(http_method='POST',
                   location_id='77560e8a-4e8c-4d59-894e-a5f264c24444',
                   version='4.0-preview.1',
                   route_values=route_values,
                   query_parameters=query_parameters,
                   content=content)

    def get_test_run_code_coverage(self, project, run_id, flags):
        """GetTestRunCodeCoverage.
        [Preview API]
        :param str project: Project ID or project name
        :param int run_id:
        :param int flags:
        :rtype: [TestRunCoverage]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        query_parameters = {}
        if flags is not None:
            query_parameters['flags'] = self._serialize.query('flags', flags, 'int')
        response = self._send(http_method='GET',
                              location_id='9629116f-3b89-4ed8-b358-d4694efda160',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[TestRunCoverage]', self._unwrap_collection(response))

    def create_test_configuration(self, test_configuration, project):
        """CreateTestConfiguration.
        [Preview API]
        :param :class:`<TestConfiguration> <test.v4_0.models.TestConfiguration>` test_configuration:
        :param str project: Project ID or project name
        :rtype: :class:`<TestConfiguration> <test.v4_0.models.TestConfiguration>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(test_configuration, 'TestConfiguration')
        response = self._send(http_method='POST',
                              location_id='d667591b-b9fd-4263-997a-9a084cca848f',
                              version='4.0-preview.2',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TestConfiguration', response)

    def delete_test_configuration(self, project, test_configuration_id):
        """DeleteTestConfiguration.
        [Preview API]
        :param str project: Project ID or project name
        :param int test_configuration_id:
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if test_configuration_id is not None:
            route_values['testConfigurationId'] = self._serialize.url('test_configuration_id', test_configuration_id, 'int')
        self._send(http_method='DELETE',
                   location_id='d667591b-b9fd-4263-997a-9a084cca848f',
                   version='4.0-preview.2',
                   route_values=route_values)

    def get_test_configuration_by_id(self, project, test_configuration_id):
        """GetTestConfigurationById.
        [Preview API]
        :param str project: Project ID or project name
        :param int test_configuration_id:
        :rtype: :class:`<TestConfiguration> <test.v4_0.models.TestConfiguration>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if test_configuration_id is not None:
            route_values['testConfigurationId'] = self._serialize.url('test_configuration_id', test_configuration_id, 'int')
        response = self._send(http_method='GET',
                              location_id='d667591b-b9fd-4263-997a-9a084cca848f',
                              version='4.0-preview.2',
                              route_values=route_values)
        return self._deserialize('TestConfiguration', response)

    def get_test_configurations(self, project, skip=None, top=None, continuation_token=None, include_all_properties=None):
        """GetTestConfigurations.
        [Preview API]
        :param str project: Project ID or project name
        :param int skip:
        :param int top:
        :param str continuation_token:
        :param bool include_all_properties:
        :rtype: [TestConfiguration]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        if continuation_token is not None:
            query_parameters['continuationToken'] = self._serialize.query('continuation_token', continuation_token, 'str')
        if include_all_properties is not None:
            query_parameters['includeAllProperties'] = self._serialize.query('include_all_properties', include_all_properties, 'bool')
        response = self._send(http_method='GET',
                              location_id='d667591b-b9fd-4263-997a-9a084cca848f',
                              version='4.0-preview.2',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[TestConfiguration]', self._unwrap_collection(response))

    def update_test_configuration(self, test_configuration, project, test_configuration_id):
        """UpdateTestConfiguration.
        [Preview API]
        :param :class:`<TestConfiguration> <test.v4_0.models.TestConfiguration>` test_configuration:
        :param str project: Project ID or project name
        :param int test_configuration_id:
        :rtype: :class:`<TestConfiguration> <test.v4_0.models.TestConfiguration>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if test_configuration_id is not None:
            route_values['testConfigurationId'] = self._serialize.url('test_configuration_id', test_configuration_id, 'int')
        content = self._serialize.body(test_configuration, 'TestConfiguration')
        response = self._send(http_method='PATCH',
                              location_id='d667591b-b9fd-4263-997a-9a084cca848f',
                              version='4.0-preview.2',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TestConfiguration', response)

    def add_custom_fields(self, new_fields, project):
        """AddCustomFields.
        [Preview API]
        :param [CustomTestFieldDefinition] new_fields:
        :param str project: Project ID or project name
        :rtype: [CustomTestFieldDefinition]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(new_fields, '[CustomTestFieldDefinition]')
        response = self._send(http_method='POST',
                              location_id='8ce1923b-f4c7-4e22-b93b-f6284e525ec2',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[CustomTestFieldDefinition]', self._unwrap_collection(response))

    def query_custom_fields(self, project, scope_filter):
        """QueryCustomFields.
        [Preview API]
        :param str project: Project ID or project name
        :param str scope_filter:
        :rtype: [CustomTestFieldDefinition]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if scope_filter is not None:
            query_parameters['scopeFilter'] = self._serialize.query('scope_filter', scope_filter, 'str')
        response = self._send(http_method='GET',
                              location_id='8ce1923b-f4c7-4e22-b93b-f6284e525ec2',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[CustomTestFieldDefinition]', self._unwrap_collection(response))

    def query_test_result_history(self, filter, project):
        """QueryTestResultHistory.
        [Preview API]
        :param :class:`<ResultsFilter> <test.v4_0.models.ResultsFilter>` filter:
        :param str project: Project ID or project name
        :rtype: :class:`<TestResultHistory> <test.v4_0.models.TestResultHistory>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(filter, 'ResultsFilter')
        response = self._send(http_method='POST',
                              location_id='234616f5-429c-4e7b-9192-affd76731dfd',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TestResultHistory', response)

    def get_test_iteration(self, project, run_id, test_case_result_id, iteration_id, include_action_results=None):
        """GetTestIteration.
        :param str project: Project ID or project name
        :param int run_id:
        :param int test_case_result_id:
        :param int iteration_id:
        :param bool include_action_results:
        :rtype: :class:`<TestIterationDetailsModel> <test.v4_0.models.TestIterationDetailsModel>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        if test_case_result_id is not None:
            route_values['testCaseResultId'] = self._serialize.url('test_case_result_id', test_case_result_id, 'int')
        if iteration_id is not None:
            route_values['iterationId'] = self._serialize.url('iteration_id', iteration_id, 'int')
        query_parameters = {}
        if include_action_results is not None:
            query_parameters['includeActionResults'] = self._serialize.query('include_action_results', include_action_results, 'bool')
        response = self._send(http_method='GET',
                              location_id='73eb9074-3446-4c44-8296-2f811950ff8d',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('TestIterationDetailsModel', response)

    def get_test_iterations(self, project, run_id, test_case_result_id, include_action_results=None):
        """GetTestIterations.
        :param str project: Project ID or project name
        :param int run_id:
        :param int test_case_result_id:
        :param bool include_action_results:
        :rtype: [TestIterationDetailsModel]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        if test_case_result_id is not None:
            route_values['testCaseResultId'] = self._serialize.url('test_case_result_id', test_case_result_id, 'int')
        query_parameters = {}
        if include_action_results is not None:
            query_parameters['includeActionResults'] = self._serialize.query('include_action_results', include_action_results, 'bool')
        response = self._send(http_method='GET',
                              location_id='73eb9074-3446-4c44-8296-2f811950ff8d',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[TestIterationDetailsModel]', self._unwrap_collection(response))

    def get_linked_work_items_by_query(self, work_item_query, project):
        """GetLinkedWorkItemsByQuery.
        [Preview API]
        :param :class:`<LinkedWorkItemsQuery> <test.v4_0.models.LinkedWorkItemsQuery>` work_item_query:
        :param str project: Project ID or project name
        :rtype: [LinkedWorkItemsQueryResult]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(work_item_query, 'LinkedWorkItemsQuery')
        response = self._send(http_method='POST',
                              location_id='a4dcb25b-9878-49ea-abfd-e440bd9b1dcd',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[LinkedWorkItemsQueryResult]', self._unwrap_collection(response))

    def get_test_run_logs(self, project, run_id):
        """GetTestRunLogs.
        [Preview API]
        :param str project: Project ID or project name
        :param int run_id:
        :rtype: [TestMessageLogDetails]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        response = self._send(http_method='GET',
                              location_id='a1e55200-637e-42e9-a7c0-7e5bfdedb1b3',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[TestMessageLogDetails]', self._unwrap_collection(response))

    def get_result_parameters(self, project, run_id, test_case_result_id, iteration_id, param_name=None):
        """GetResultParameters.
        :param str project: Project ID or project name
        :param int run_id:
        :param int test_case_result_id:
        :param int iteration_id:
        :param str param_name:
        :rtype: [TestResultParameterModel]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        if test_case_result_id is not None:
            route_values['testCaseResultId'] = self._serialize.url('test_case_result_id', test_case_result_id, 'int')
        if iteration_id is not None:
            route_values['iterationId'] = self._serialize.url('iteration_id', iteration_id, 'int')
        query_parameters = {}
        if param_name is not None:
            query_parameters['paramName'] = self._serialize.query('param_name', param_name, 'str')
        response = self._send(http_method='GET',
                              location_id='7c69810d-3354-4af3-844a-180bd25db08a',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[TestResultParameterModel]', self._unwrap_collection(response))

    def create_test_plan(self, test_plan, project):
        """CreateTestPlan.
        :param :class:`<PlanUpdateModel> <test.v4_0.models.PlanUpdateModel>` test_plan:
        :param str project: Project ID or project name
        :rtype: :class:`<TestPlan> <test.v4_0.models.TestPlan>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(test_plan, 'PlanUpdateModel')
        response = self._send(http_method='POST',
                              location_id='51712106-7278-4208-8563-1c96f40cf5e4',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TestPlan', response)

    def delete_test_plan(self, project, plan_id):
        """DeleteTestPlan.
        :param str project: Project ID or project name
        :param int plan_id:
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'int')
        self._send(http_method='DELETE',
                   location_id='51712106-7278-4208-8563-1c96f40cf5e4',
                   version='4.0',
                   route_values=route_values)

    def get_plan_by_id(self, project, plan_id):
        """GetPlanById.
        :param str project: Project ID or project name
        :param int plan_id:
        :rtype: :class:`<TestPlan> <test.v4_0.models.TestPlan>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'int')
        response = self._send(http_method='GET',
                              location_id='51712106-7278-4208-8563-1c96f40cf5e4',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('TestPlan', response)

    def get_plans(self, project, owner=None, skip=None, top=None, include_plan_details=None, filter_active_plans=None):
        """GetPlans.
        :param str project: Project ID or project name
        :param str owner:
        :param int skip:
        :param int top:
        :param bool include_plan_details:
        :param bool filter_active_plans:
        :rtype: [TestPlan]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if owner is not None:
            query_parameters['owner'] = self._serialize.query('owner', owner, 'str')
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        if include_plan_details is not None:
            query_parameters['includePlanDetails'] = self._serialize.query('include_plan_details', include_plan_details, 'bool')
        if filter_active_plans is not None:
            query_parameters['filterActivePlans'] = self._serialize.query('filter_active_plans', filter_active_plans, 'bool')
        response = self._send(http_method='GET',
                              location_id='51712106-7278-4208-8563-1c96f40cf5e4',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[TestPlan]', self._unwrap_collection(response))

    def update_test_plan(self, plan_update_model, project, plan_id):
        """UpdateTestPlan.
        :param :class:`<PlanUpdateModel> <test.v4_0.models.PlanUpdateModel>` plan_update_model:
        :param str project: Project ID or project name
        :param int plan_id:
        :rtype: :class:`<TestPlan> <test.v4_0.models.TestPlan>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'int')
        content = self._serialize.body(plan_update_model, 'PlanUpdateModel')
        response = self._send(http_method='PATCH',
                              location_id='51712106-7278-4208-8563-1c96f40cf5e4',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TestPlan', response)

    def get_point(self, project, plan_id, suite_id, point_ids, wit_fields=None):
        """GetPoint.
        :param str project: Project ID or project name
        :param int plan_id:
        :param int suite_id:
        :param int point_ids:
        :param str wit_fields:
        :rtype: :class:`<TestPoint> <test.v4_0.models.TestPoint>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'int')
        if suite_id is not None:
            route_values['suiteId'] = self._serialize.url('suite_id', suite_id, 'int')
        if point_ids is not None:
            route_values['pointIds'] = self._serialize.url('point_ids', point_ids, 'int')
        query_parameters = {}
        if wit_fields is not None:
            query_parameters['witFields'] = self._serialize.query('wit_fields', wit_fields, 'str')
        response = self._send(http_method='GET',
                              location_id='3bcfd5c8-be62-488e-b1da-b8289ce9299c',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('TestPoint', response)

    def get_points(self, project, plan_id, suite_id, wit_fields=None, configuration_id=None, test_case_id=None, test_point_ids=None, include_point_details=None, skip=None, top=None):
        """GetPoints.
        :param str project: Project ID or project name
        :param int plan_id:
        :param int suite_id:
        :param str wit_fields:
        :param str configuration_id:
        :param str test_case_id:
        :param str test_point_ids:
        :param bool include_point_details:
        :param int skip:
        :param int top:
        :rtype: [TestPoint]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'int')
        if suite_id is not None:
            route_values['suiteId'] = self._serialize.url('suite_id', suite_id, 'int')
        query_parameters = {}
        if wit_fields is not None:
            query_parameters['witFields'] = self._serialize.query('wit_fields', wit_fields, 'str')
        if configuration_id is not None:
            query_parameters['configurationId'] = self._serialize.query('configuration_id', configuration_id, 'str')
        if test_case_id is not None:
            query_parameters['testCaseId'] = self._serialize.query('test_case_id', test_case_id, 'str')
        if test_point_ids is not None:
            query_parameters['testPointIds'] = self._serialize.query('test_point_ids', test_point_ids, 'str')
        if include_point_details is not None:
            query_parameters['includePointDetails'] = self._serialize.query('include_point_details', include_point_details, 'bool')
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        response = self._send(http_method='GET',
                              location_id='3bcfd5c8-be62-488e-b1da-b8289ce9299c',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[TestPoint]', self._unwrap_collection(response))

    def update_test_points(self, point_update_model, project, plan_id, suite_id, point_ids):
        """UpdateTestPoints.
        :param :class:`<PointUpdateModel> <test.v4_0.models.PointUpdateModel>` point_update_model:
        :param str project: Project ID or project name
        :param int plan_id:
        :param int suite_id:
        :param str point_ids:
        :rtype: [TestPoint]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'int')
        if suite_id is not None:
            route_values['suiteId'] = self._serialize.url('suite_id', suite_id, 'int')
        if point_ids is not None:
            route_values['pointIds'] = self._serialize.url('point_ids', point_ids, 'str')
        content = self._serialize.body(point_update_model, 'PointUpdateModel')
        response = self._send(http_method='PATCH',
                              location_id='3bcfd5c8-be62-488e-b1da-b8289ce9299c',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[TestPoint]', self._unwrap_collection(response))

    def get_points_by_query(self, query, project, skip=None, top=None):
        """GetPointsByQuery.
        [Preview API]
        :param :class:`<TestPointsQuery> <test.v4_0.models.TestPointsQuery>` query:
        :param str project: Project ID or project name
        :param int skip:
        :param int top:
        :rtype: :class:`<TestPointsQuery> <test.v4_0.models.TestPointsQuery>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        content = self._serialize.body(query, 'TestPointsQuery')
        response = self._send(http_method='POST',
                              location_id='b4264fd0-a5d1-43e2-82a5-b9c46b7da9ce',
                              version='4.0-preview.2',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('TestPointsQuery', response)

    def get_test_result_details_for_build(self, project, build_id, publish_context=None, group_by=None, filter=None, orderby=None):
        """GetTestResultDetailsForBuild.
        [Preview API]
        :param str project: Project ID or project name
        :param int build_id:
        :param str publish_context:
        :param str group_by:
        :param str filter:
        :param str orderby:
        :rtype: :class:`<TestResultsDetails> <test.v4_0.models.TestResultsDetails>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if build_id is not None:
            query_parameters['buildId'] = self._serialize.query('build_id', build_id, 'int')
        if publish_context is not None:
            query_parameters['publishContext'] = self._serialize.query('publish_context', publish_context, 'str')
        if group_by is not None:
            query_parameters['groupBy'] = self._serialize.query('group_by', group_by, 'str')
        if filter is not None:
            query_parameters['$filter'] = self._serialize.query('filter', filter, 'str')
        if orderby is not None:
            query_parameters['$orderby'] = self._serialize.query('orderby', orderby, 'str')
        response = self._send(http_method='GET',
                              location_id='efb387b0-10d5-42e7-be40-95e06ee9430f',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('TestResultsDetails', response)

    def get_test_result_details_for_release(self, project, release_id, release_env_id, publish_context=None, group_by=None, filter=None, orderby=None):
        """GetTestResultDetailsForRelease.
        [Preview API]
        :param str project: Project ID or project name
        :param int release_id:
        :param int release_env_id:
        :param str publish_context:
        :param str group_by:
        :param str filter:
        :param str orderby:
        :rtype: :class:`<TestResultsDetails> <test.v4_0.models.TestResultsDetails>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if release_id is not None:
            query_parameters['releaseId'] = self._serialize.query('release_id', release_id, 'int')
        if release_env_id is not None:
            query_parameters['releaseEnvId'] = self._serialize.query('release_env_id', release_env_id, 'int')
        if publish_context is not None:
            query_parameters['publishContext'] = self._serialize.query('publish_context', publish_context, 'str')
        if group_by is not None:
            query_parameters['groupBy'] = self._serialize.query('group_by', group_by, 'str')
        if filter is not None:
            query_parameters['$filter'] = self._serialize.query('filter', filter, 'str')
        if orderby is not None:
            query_parameters['$orderby'] = self._serialize.query('orderby', orderby, 'str')
        response = self._send(http_method='GET',
                              location_id='b834ec7e-35bb-450f-a3c8-802e70ca40dd',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('TestResultsDetails', response)

    def publish_test_result_document(self, document, project, run_id):
        """PublishTestResultDocument.
        [Preview API]
        :param :class:`<TestResultDocument> <test.v4_0.models.TestResultDocument>` document:
        :param str project: Project ID or project name
        :param int run_id:
        :rtype: :class:`<TestResultDocument> <test.v4_0.models.TestResultDocument>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        content = self._serialize.body(document, 'TestResultDocument')
        response = self._send(http_method='POST',
                              location_id='370ca04b-8eec-4ca8-8ba3-d24dca228791',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TestResultDocument', response)

    def get_result_retention_settings(self, project):
        """GetResultRetentionSettings.
        [Preview API]
        :param str project: Project ID or project name
        :rtype: :class:`<ResultRetentionSettings> <test.v4_0.models.ResultRetentionSettings>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        response = self._send(http_method='GET',
                              location_id='a3206d9e-fa8d-42d3-88cb-f75c51e69cde',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('ResultRetentionSettings', response)

    def update_result_retention_settings(self, retention_settings, project):
        """UpdateResultRetentionSettings.
        [Preview API]
        :param :class:`<ResultRetentionSettings> <test.v4_0.models.ResultRetentionSettings>` retention_settings:
        :param str project: Project ID or project name
        :rtype: :class:`<ResultRetentionSettings> <test.v4_0.models.ResultRetentionSettings>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(retention_settings, 'ResultRetentionSettings')
        response = self._send(http_method='PATCH',
                              location_id='a3206d9e-fa8d-42d3-88cb-f75c51e69cde',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('ResultRetentionSettings', response)

    def add_test_results_to_test_run(self, results, project, run_id):
        """AddTestResultsToTestRun.
        :param [TestCaseResult] results:
        :param str project: Project ID or project name
        :param int run_id:
        :rtype: [TestCaseResult]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        content = self._serialize.body(results, '[TestCaseResult]')
        response = self._send(http_method='POST',
                              location_id='4637d869-3a76-4468-8057-0bb02aa385cf',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[TestCaseResult]', self._unwrap_collection(response))

    def get_test_result_by_id(self, project, run_id, test_case_result_id, details_to_include=None):
        """GetTestResultById.
        :param str project: Project ID or project name
        :param int run_id:
        :param int test_case_result_id:
        :param str details_to_include:
        :rtype: :class:`<TestCaseResult> <test.v4_0.models.TestCaseResult>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        if test_case_result_id is not None:
            route_values['testCaseResultId'] = self._serialize.url('test_case_result_id', test_case_result_id, 'int')
        query_parameters = {}
        if details_to_include is not None:
            query_parameters['detailsToInclude'] = self._serialize.query('details_to_include', details_to_include, 'str')
        response = self._send(http_method='GET',
                              location_id='4637d869-3a76-4468-8057-0bb02aa385cf',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('TestCaseResult', response)

    def get_test_results(self, project, run_id, details_to_include=None, skip=None, top=None):
        """GetTestResults.
        :param str project: Project ID or project name
        :param int run_id:
        :param str details_to_include:
        :param int skip:
        :param int top:
        :rtype: [TestCaseResult]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        query_parameters = {}
        if details_to_include is not None:
            query_parameters['detailsToInclude'] = self._serialize.query('details_to_include', details_to_include, 'str')
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        response = self._send(http_method='GET',
                              location_id='4637d869-3a76-4468-8057-0bb02aa385cf',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[TestCaseResult]', self._unwrap_collection(response))

    def update_test_results(self, results, project, run_id):
        """UpdateTestResults.
        :param [TestCaseResult] results:
        :param str project: Project ID or project name
        :param int run_id:
        :rtype: [TestCaseResult]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        content = self._serialize.body(results, '[TestCaseResult]')
        response = self._send(http_method='PATCH',
                              location_id='4637d869-3a76-4468-8057-0bb02aa385cf',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[TestCaseResult]', self._unwrap_collection(response))

    def get_test_results_by_query(self, query, project):
        """GetTestResultsByQuery.
        [Preview API]
        :param :class:`<TestResultsQuery> <test.v4_0.models.TestResultsQuery>` query:
        :param str project: Project ID or project name
        :rtype: :class:`<TestResultsQuery> <test.v4_0.models.TestResultsQuery>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(query, 'TestResultsQuery')
        response = self._send(http_method='POST',
                              location_id='6711da49-8e6f-4d35-9f73-cef7a3c81a5b',
                              version='4.0-preview.4',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TestResultsQuery', response)

    def query_test_results_report_for_build(self, project, build_id, publish_context=None, include_failure_details=None, build_to_compare=None):
        """QueryTestResultsReportForBuild.
        [Preview API]
        :param str project: Project ID or project name
        :param int build_id:
        :param str publish_context:
        :param bool include_failure_details:
        :param :class:`<BuildReference> <test.v4_0.models.BuildReference>` build_to_compare:
        :rtype: :class:`<TestResultSummary> <test.v4_0.models.TestResultSummary>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if build_id is not None:
            query_parameters['buildId'] = self._serialize.query('build_id', build_id, 'int')
        if publish_context is not None:
            query_parameters['publishContext'] = self._serialize.query('publish_context', publish_context, 'str')
        if include_failure_details is not None:
            query_parameters['includeFailureDetails'] = self._serialize.query('include_failure_details', include_failure_details, 'bool')
        if build_to_compare is not None:
            if build_to_compare.id is not None:
                query_parameters['buildToCompare.id'] = build_to_compare.id
            if build_to_compare.definition_id is not None:
                query_parameters['buildToCompare.definitionId'] = build_to_compare.definition_id
            if build_to_compare.number is not None:
                query_parameters['buildToCompare.number'] = build_to_compare.number
            if build_to_compare.uri is not None:
                query_parameters['buildToCompare.uri'] = build_to_compare.uri
            if build_to_compare.build_system is not None:
                query_parameters['buildToCompare.buildSystem'] = build_to_compare.build_system
            if build_to_compare.branch_name is not None:
                query_parameters['buildToCompare.branchName'] = build_to_compare.branch_name
            if build_to_compare.repository_id is not None:
                query_parameters['buildToCompare.repositoryId'] = build_to_compare.repository_id
        response = self._send(http_method='GET',
                              location_id='000ef77b-fea2-498d-a10d-ad1a037f559f',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('TestResultSummary', response)

    def query_test_results_report_for_release(self, project, release_id, release_env_id, publish_context=None, include_failure_details=None, release_to_compare=None):
        """QueryTestResultsReportForRelease.
        [Preview API]
        :param str project: Project ID or project name
        :param int release_id:
        :param int release_env_id:
        :param str publish_context:
        :param bool include_failure_details:
        :param :class:`<ReleaseReference> <test.v4_0.models.ReleaseReference>` release_to_compare:
        :rtype: :class:`<TestResultSummary> <test.v4_0.models.TestResultSummary>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if release_id is not None:
            query_parameters['releaseId'] = self._serialize.query('release_id', release_id, 'int')
        if release_env_id is not None:
            query_parameters['releaseEnvId'] = self._serialize.query('release_env_id', release_env_id, 'int')
        if publish_context is not None:
            query_parameters['publishContext'] = self._serialize.query('publish_context', publish_context, 'str')
        if include_failure_details is not None:
            query_parameters['includeFailureDetails'] = self._serialize.query('include_failure_details', include_failure_details, 'bool')
        if release_to_compare is not None:
            if release_to_compare.id is not None:
                query_parameters['releaseToCompare.id'] = release_to_compare.id
            if release_to_compare.name is not None:
                query_parameters['releaseToCompare.name'] = release_to_compare.name
            if release_to_compare.environment_id is not None:
                query_parameters['releaseToCompare.environmentId'] = release_to_compare.environment_id
            if release_to_compare.environment_name is not None:
                query_parameters['releaseToCompare.environmentName'] = release_to_compare.environment_name
            if release_to_compare.definition_id is not None:
                query_parameters['releaseToCompare.definitionId'] = release_to_compare.definition_id
            if release_to_compare.environment_definition_id is not None:
                query_parameters['releaseToCompare.environmentDefinitionId'] = release_to_compare.environment_definition_id
            if release_to_compare.environment_definition_name is not None:
                query_parameters['releaseToCompare.environmentDefinitionName'] = release_to_compare.environment_definition_name
        response = self._send(http_method='GET',
                              location_id='85765790-ac68-494e-b268-af36c3929744',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('TestResultSummary', response)

    def query_test_results_summary_for_releases(self, releases, project):
        """QueryTestResultsSummaryForReleases.
        [Preview API]
        :param [ReleaseReference] releases:
        :param str project: Project ID or project name
        :rtype: [TestResultSummary]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(releases, '[ReleaseReference]')
        response = self._send(http_method='POST',
                              location_id='85765790-ac68-494e-b268-af36c3929744',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[TestResultSummary]', self._unwrap_collection(response))

    def query_test_summary_by_requirement(self, results_context, project, work_item_ids=None):
        """QueryTestSummaryByRequirement.
        [Preview API]
        :param :class:`<TestResultsContext> <test.v4_0.models.TestResultsContext>` results_context:
        :param str project: Project ID or project name
        :param [int] work_item_ids:
        :rtype: [TestSummaryForWorkItem]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if work_item_ids is not None:
            work_item_ids = ",".join(map(str, work_item_ids))
            query_parameters['workItemIds'] = self._serialize.query('work_item_ids', work_item_ids, 'str')
        content = self._serialize.body(results_context, 'TestResultsContext')
        response = self._send(http_method='POST',
                              location_id='cd08294e-308d-4460-a46e-4cfdefba0b4b',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('[TestSummaryForWorkItem]', self._unwrap_collection(response))

    def query_result_trend_for_build(self, filter, project):
        """QueryResultTrendForBuild.
        [Preview API]
        :param :class:`<TestResultTrendFilter> <test.v4_0.models.TestResultTrendFilter>` filter:
        :param str project: Project ID or project name
        :rtype: [AggregatedDataForResultTrend]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(filter, 'TestResultTrendFilter')
        response = self._send(http_method='POST',
                              location_id='fbc82a85-0786-4442-88bb-eb0fda6b01b0',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[AggregatedDataForResultTrend]', self._unwrap_collection(response))

    def query_result_trend_for_release(self, filter, project):
        """QueryResultTrendForRelease.
        [Preview API]
        :param :class:`<TestResultTrendFilter> <test.v4_0.models.TestResultTrendFilter>` filter:
        :param str project: Project ID or project name
        :rtype: [AggregatedDataForResultTrend]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(filter, 'TestResultTrendFilter')
        response = self._send(http_method='POST',
                              location_id='dd178e93-d8dd-4887-9635-d6b9560b7b6e',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[AggregatedDataForResultTrend]', self._unwrap_collection(response))

    def get_test_run_statistics(self, project, run_id):
        """GetTestRunStatistics.
        :param str project: Project ID or project name
        :param int run_id:
        :rtype: :class:`<TestRunStatistic> <test.v4_0.models.TestRunStatistic>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        response = self._send(http_method='GET',
                              location_id='0a42c424-d764-4a16-a2d5-5c85f87d0ae8',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('TestRunStatistic', response)

    def create_test_run(self, test_run, project):
        """CreateTestRun.
        :param :class:`<RunCreateModel> <test.v4_0.models.RunCreateModel>` test_run:
        :param str project: Project ID or project name
        :rtype: :class:`<TestRun> <test.v4_0.models.TestRun>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(test_run, 'RunCreateModel')
        response = self._send(http_method='POST',
                              location_id='cadb3810-d47d-4a3c-a234-fe5f3be50138',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TestRun', response)

    def delete_test_run(self, project, run_id):
        """DeleteTestRun.
        :param str project: Project ID or project name
        :param int run_id:
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        self._send(http_method='DELETE',
                   location_id='cadb3810-d47d-4a3c-a234-fe5f3be50138',
                   version='4.0',
                   route_values=route_values)

    def get_test_run_by_id(self, project, run_id):
        """GetTestRunById.
        :param str project: Project ID or project name
        :param int run_id:
        :rtype: :class:`<TestRun> <test.v4_0.models.TestRun>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        response = self._send(http_method='GET',
                              location_id='cadb3810-d47d-4a3c-a234-fe5f3be50138',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('TestRun', response)

    def get_test_runs(self, project, build_uri=None, owner=None, tmi_run_id=None, plan_id=None, include_run_details=None, automated=None, skip=None, top=None):
        """GetTestRuns.
        :param str project: Project ID or project name
        :param str build_uri:
        :param str owner:
        :param str tmi_run_id:
        :param int plan_id:
        :param bool include_run_details:
        :param bool automated:
        :param int skip:
        :param int top:
        :rtype: [TestRun]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if build_uri is not None:
            query_parameters['buildUri'] = self._serialize.query('build_uri', build_uri, 'str')
        if owner is not None:
            query_parameters['owner'] = self._serialize.query('owner', owner, 'str')
        if tmi_run_id is not None:
            query_parameters['tmiRunId'] = self._serialize.query('tmi_run_id', tmi_run_id, 'str')
        if plan_id is not None:
            query_parameters['planId'] = self._serialize.query('plan_id', plan_id, 'int')
        if include_run_details is not None:
            query_parameters['includeRunDetails'] = self._serialize.query('include_run_details', include_run_details, 'bool')
        if automated is not None:
            query_parameters['automated'] = self._serialize.query('automated', automated, 'bool')
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        response = self._send(http_method='GET',
                              location_id='cadb3810-d47d-4a3c-a234-fe5f3be50138',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[TestRun]', self._unwrap_collection(response))

    def query_test_runs(self, project, state, min_completed_date=None, max_completed_date=None, plan_id=None, is_automated=None, publish_context=None, build_id=None, build_def_id=None, branch_name=None, release_id=None, release_def_id=None, release_env_id=None, release_env_def_id=None, run_title=None, skip=None, top=None):
        """QueryTestRuns.
        :param str project: Project ID or project name
        :param str state:
        :param datetime min_completed_date:
        :param datetime max_completed_date:
        :param int plan_id:
        :param bool is_automated:
        :param str publish_context:
        :param int build_id:
        :param int build_def_id:
        :param str branch_name:
        :param int release_id:
        :param int release_def_id:
        :param int release_env_id:
        :param int release_env_def_id:
        :param str run_title:
        :param int skip:
        :param int top:
        :rtype: [TestRun]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if state is not None:
            query_parameters['state'] = self._serialize.query('state', state, 'str')
        if min_completed_date is not None:
            query_parameters['minCompletedDate'] = self._serialize.query('min_completed_date', min_completed_date, 'iso-8601')
        if max_completed_date is not None:
            query_parameters['maxCompletedDate'] = self._serialize.query('max_completed_date', max_completed_date, 'iso-8601')
        if plan_id is not None:
            query_parameters['planId'] = self._serialize.query('plan_id', plan_id, 'int')
        if is_automated is not None:
            query_parameters['IsAutomated'] = self._serialize.query('is_automated', is_automated, 'bool')
        if publish_context is not None:
            query_parameters['publishContext'] = self._serialize.query('publish_context', publish_context, 'str')
        if build_id is not None:
            query_parameters['buildId'] = self._serialize.query('build_id', build_id, 'int')
        if build_def_id is not None:
            query_parameters['buildDefId'] = self._serialize.query('build_def_id', build_def_id, 'int')
        if branch_name is not None:
            query_parameters['branchName'] = self._serialize.query('branch_name', branch_name, 'str')
        if release_id is not None:
            query_parameters['releaseId'] = self._serialize.query('release_id', release_id, 'int')
        if release_def_id is not None:
            query_parameters['releaseDefId'] = self._serialize.query('release_def_id', release_def_id, 'int')
        if release_env_id is not None:
            query_parameters['releaseEnvId'] = self._serialize.query('release_env_id', release_env_id, 'int')
        if release_env_def_id is not None:
            query_parameters['releaseEnvDefId'] = self._serialize.query('release_env_def_id', release_env_def_id, 'int')
        if run_title is not None:
            query_parameters['runTitle'] = self._serialize.query('run_title', run_title, 'str')
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        response = self._send(http_method='GET',
                              location_id='cadb3810-d47d-4a3c-a234-fe5f3be50138',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[TestRun]', self._unwrap_collection(response))

    def update_test_run(self, run_update_model, project, run_id):
        """UpdateTestRun.
        :param :class:`<RunUpdateModel> <test.v4_0.models.RunUpdateModel>` run_update_model:
        :param str project: Project ID or project name
        :param int run_id:
        :rtype: :class:`<TestRun> <test.v4_0.models.TestRun>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if run_id is not None:
            route_values['runId'] = self._serialize.url('run_id', run_id, 'int')
        content = self._serialize.body(run_update_model, 'RunUpdateModel')
        response = self._send(http_method='PATCH',
                              location_id='cadb3810-d47d-4a3c-a234-fe5f3be50138',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TestRun', response)

    def create_test_session(self, test_session, team_context):
        """CreateTestSession.
        [Preview API]
        :param :class:`<TestSession> <test.v4_0.models.TestSession>` test_session:
        :param :class:`<TeamContext> <test.v4_0.models.TeamContext>` team_context: The team context for the operation
        :rtype: :class:`<TestSession> <test.v4_0.models.TestSession>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        content = self._serialize.body(test_session, 'TestSession')
        response = self._send(http_method='POST',
                              location_id='1500b4b4-6c69-4ca6-9b18-35e9e97fe2ac',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TestSession', response)

    def get_test_sessions(self, team_context, period=None, all_sessions=None, include_all_properties=None, source=None, include_only_completed_sessions=None):
        """GetTestSessions.
        [Preview API]
        :param :class:`<TeamContext> <test.v4_0.models.TeamContext>` team_context: The team context for the operation
        :param int period:
        :param bool all_sessions:
        :param bool include_all_properties:
        :param str source:
        :param bool include_only_completed_sessions:
        :rtype: [TestSession]
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        query_parameters = {}
        if period is not None:
            query_parameters['period'] = self._serialize.query('period', period, 'int')
        if all_sessions is not None:
            query_parameters['allSessions'] = self._serialize.query('all_sessions', all_sessions, 'bool')
        if include_all_properties is not None:
            query_parameters['includeAllProperties'] = self._serialize.query('include_all_properties', include_all_properties, 'bool')
        if source is not None:
            query_parameters['source'] = self._serialize.query('source', source, 'str')
        if include_only_completed_sessions is not None:
            query_parameters['includeOnlyCompletedSessions'] = self._serialize.query('include_only_completed_sessions', include_only_completed_sessions, 'bool')
        response = self._send(http_method='GET',
                              location_id='1500b4b4-6c69-4ca6-9b18-35e9e97fe2ac',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[TestSession]', self._unwrap_collection(response))

    def update_test_session(self, test_session, team_context):
        """UpdateTestSession.
        [Preview API]
        :param :class:`<TestSession> <test.v4_0.models.TestSession>` test_session:
        :param :class:`<TeamContext> <test.v4_0.models.TeamContext>` team_context: The team context for the operation
        :rtype: :class:`<TestSession> <test.v4_0.models.TestSession>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        content = self._serialize.body(test_session, 'TestSession')
        response = self._send(http_method='PATCH',
                              location_id='1500b4b4-6c69-4ca6-9b18-35e9e97fe2ac',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TestSession', response)

    def delete_shared_parameter(self, project, shared_parameter_id):
        """DeleteSharedParameter.
        [Preview API]
        :param str project: Project ID or project name
        :param int shared_parameter_id:
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if shared_parameter_id is not None:
            route_values['sharedParameterId'] = self._serialize.url('shared_parameter_id', shared_parameter_id, 'int')
        self._send(http_method='DELETE',
                   location_id='8300eeca-0f8c-4eff-a089-d2dda409c41f',
                   version='4.0-preview.1',
                   route_values=route_values)

    def delete_shared_step(self, project, shared_step_id):
        """DeleteSharedStep.
        [Preview API]
        :param str project: Project ID or project name
        :param int shared_step_id:
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if shared_step_id is not None:
            route_values['sharedStepId'] = self._serialize.url('shared_step_id', shared_step_id, 'int')
        self._send(http_method='DELETE',
                   location_id='fabb3cc9-e3f8-40b7-8b62-24cc4b73fccf',
                   version='4.0-preview.1',
                   route_values=route_values)

    def get_suite_entries(self, project, suite_id):
        """GetSuiteEntries.
        [Preview API]
        :param str project: Project ID or project name
        :param int suite_id:
        :rtype: [SuiteEntry]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if suite_id is not None:
            route_values['suiteId'] = self._serialize.url('suite_id', suite_id, 'int')
        response = self._send(http_method='GET',
                              location_id='bf8b7f78-0c1f-49cb-89e9-d1a17bcaaad3',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[SuiteEntry]', self._unwrap_collection(response))

    def reorder_suite_entries(self, suite_entries, project, suite_id):
        """ReorderSuiteEntries.
        [Preview API]
        :param [SuiteEntryUpdateModel] suite_entries:
        :param str project: Project ID or project name
        :param int suite_id:
        :rtype: [SuiteEntry]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if suite_id is not None:
            route_values['suiteId'] = self._serialize.url('suite_id', suite_id, 'int')
        content = self._serialize.body(suite_entries, '[SuiteEntryUpdateModel]')
        response = self._send(http_method='PATCH',
                              location_id='bf8b7f78-0c1f-49cb-89e9-d1a17bcaaad3',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[SuiteEntry]', self._unwrap_collection(response))

    def add_test_cases_to_suite(self, project, plan_id, suite_id, test_case_ids):
        """AddTestCasesToSuite.
        :param str project: Project ID or project name
        :param int plan_id:
        :param int suite_id:
        :param str test_case_ids:
        :rtype: [SuiteTestCase]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'int')
        if suite_id is not None:
            route_values['suiteId'] = self._serialize.url('suite_id', suite_id, 'int')
        if test_case_ids is not None:
            route_values['testCaseIds'] = self._serialize.url('test_case_ids', test_case_ids, 'str')
        route_values['action'] = 'TestCases'
        response = self._send(http_method='POST',
                              location_id='a4a1ec1c-b03f-41ca-8857-704594ecf58e',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('[SuiteTestCase]', self._unwrap_collection(response))

    def get_test_case_by_id(self, project, plan_id, suite_id, test_case_ids):
        """GetTestCaseById.
        :param str project: Project ID or project name
        :param int plan_id:
        :param int suite_id:
        :param int test_case_ids:
        :rtype: :class:`<SuiteTestCase> <test.v4_0.models.SuiteTestCase>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'int')
        if suite_id is not None:
            route_values['suiteId'] = self._serialize.url('suite_id', suite_id, 'int')
        if test_case_ids is not None:
            route_values['testCaseIds'] = self._serialize.url('test_case_ids', test_case_ids, 'int')
        route_values['action'] = 'TestCases'
        response = self._send(http_method='GET',
                              location_id='a4a1ec1c-b03f-41ca-8857-704594ecf58e',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('SuiteTestCase', response)

    def get_test_cases(self, project, plan_id, suite_id):
        """GetTestCases.
        :param str project: Project ID or project name
        :param int plan_id:
        :param int suite_id:
        :rtype: [SuiteTestCase]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'int')
        if suite_id is not None:
            route_values['suiteId'] = self._serialize.url('suite_id', suite_id, 'int')
        route_values['action'] = 'TestCases'
        response = self._send(http_method='GET',
                              location_id='a4a1ec1c-b03f-41ca-8857-704594ecf58e',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('[SuiteTestCase]', self._unwrap_collection(response))

    def remove_test_cases_from_suite_url(self, project, plan_id, suite_id, test_case_ids):
        """RemoveTestCasesFromSuiteUrl.
        :param str project: Project ID or project name
        :param int plan_id:
        :param int suite_id:
        :param str test_case_ids:
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'int')
        if suite_id is not None:
            route_values['suiteId'] = self._serialize.url('suite_id', suite_id, 'int')
        if test_case_ids is not None:
            route_values['testCaseIds'] = self._serialize.url('test_case_ids', test_case_ids, 'str')
        route_values['action'] = 'TestCases'
        self._send(http_method='DELETE',
                   location_id='a4a1ec1c-b03f-41ca-8857-704594ecf58e',
                   version='4.0',
                   route_values=route_values)

    def create_test_suite(self, test_suite, project, plan_id, suite_id):
        """CreateTestSuite.
        :param :class:`<SuiteCreateModel> <test.v4_0.models.SuiteCreateModel>` test_suite:
        :param str project: Project ID or project name
        :param int plan_id:
        :param int suite_id:
        :rtype: [TestSuite]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'int')
        if suite_id is not None:
            route_values['suiteId'] = self._serialize.url('suite_id', suite_id, 'int')
        content = self._serialize.body(test_suite, 'SuiteCreateModel')
        response = self._send(http_method='POST',
                              location_id='7b7619a0-cb54-4ab3-bf22-194056f45dd1',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[TestSuite]', self._unwrap_collection(response))

    def delete_test_suite(self, project, plan_id, suite_id):
        """DeleteTestSuite.
        :param str project: Project ID or project name
        :param int plan_id:
        :param int suite_id:
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'int')
        if suite_id is not None:
            route_values['suiteId'] = self._serialize.url('suite_id', suite_id, 'int')
        self._send(http_method='DELETE',
                   location_id='7b7619a0-cb54-4ab3-bf22-194056f45dd1',
                   version='4.0',
                   route_values=route_values)

    def get_test_suite_by_id(self, project, plan_id, suite_id, include_child_suites=None):
        """GetTestSuiteById.
        :param str project: Project ID or project name
        :param int plan_id:
        :param int suite_id:
        :param bool include_child_suites:
        :rtype: :class:`<TestSuite> <test.v4_0.models.TestSuite>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'int')
        if suite_id is not None:
            route_values['suiteId'] = self._serialize.url('suite_id', suite_id, 'int')
        query_parameters = {}
        if include_child_suites is not None:
            query_parameters['includeChildSuites'] = self._serialize.query('include_child_suites', include_child_suites, 'bool')
        response = self._send(http_method='GET',
                              location_id='7b7619a0-cb54-4ab3-bf22-194056f45dd1',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('TestSuite', response)

    def get_test_suites_for_plan(self, project, plan_id, include_suites=None, skip=None, top=None, as_tree_view=None):
        """GetTestSuitesForPlan.
        :param str project: Project ID or project name
        :param int plan_id:
        :param bool include_suites:
        :param int skip:
        :param int top:
        :param bool as_tree_view:
        :rtype: [TestSuite]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'int')
        query_parameters = {}
        if include_suites is not None:
            query_parameters['includeSuites'] = self._serialize.query('include_suites', include_suites, 'bool')
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        if as_tree_view is not None:
            query_parameters['$asTreeView'] = self._serialize.query('as_tree_view', as_tree_view, 'bool')
        response = self._send(http_method='GET',
                              location_id='7b7619a0-cb54-4ab3-bf22-194056f45dd1',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[TestSuite]', self._unwrap_collection(response))

    def update_test_suite(self, suite_update_model, project, plan_id, suite_id):
        """UpdateTestSuite.
        :param :class:`<SuiteUpdateModel> <test.v4_0.models.SuiteUpdateModel>` suite_update_model:
        :param str project: Project ID or project name
        :param int plan_id:
        :param int suite_id:
        :rtype: :class:`<TestSuite> <test.v4_0.models.TestSuite>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if plan_id is not None:
            route_values['planId'] = self._serialize.url('plan_id', plan_id, 'int')
        if suite_id is not None:
            route_values['suiteId'] = self._serialize.url('suite_id', suite_id, 'int')
        content = self._serialize.body(suite_update_model, 'SuiteUpdateModel')
        response = self._send(http_method='PATCH',
                              location_id='7b7619a0-cb54-4ab3-bf22-194056f45dd1',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TestSuite', response)

    def get_suites_by_test_case_id(self, test_case_id):
        """GetSuitesByTestCaseId.
        :param int test_case_id:
        :rtype: [TestSuite]
        """
        query_parameters = {}
        if test_case_id is not None:
            query_parameters['testCaseId'] = self._serialize.query('test_case_id', test_case_id, 'int')
        response = self._send(http_method='GET',
                              location_id='09a6167b-e969-4775-9247-b94cf3819caf',
                              version='4.0',
                              query_parameters=query_parameters)
        return self._deserialize('[TestSuite]', self._unwrap_collection(response))

    def delete_test_case(self, project, test_case_id):
        """DeleteTestCase.
        [Preview API]
        :param str project: Project ID or project name
        :param int test_case_id:
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if test_case_id is not None:
            route_values['testCaseId'] = self._serialize.url('test_case_id', test_case_id, 'int')
        self._send(http_method='DELETE',
                   location_id='4d472e0f-e32c-4ef8-adf4-a4078772889c',
                   version='4.0-preview.1',
                   route_values=route_values)

    def create_test_settings(self, test_settings, project):
        """CreateTestSettings.
        :param :class:`<TestSettings> <test.v4_0.models.TestSettings>` test_settings:
        :param str project: Project ID or project name
        :rtype: int
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(test_settings, 'TestSettings')
        response = self._send(http_method='POST',
                              location_id='8133ce14-962f-42af-a5f9-6aa9defcb9c8',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('int', response)

    def delete_test_settings(self, project, test_settings_id):
        """DeleteTestSettings.
        :param str project: Project ID or project name
        :param int test_settings_id:
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if test_settings_id is not None:
            route_values['testSettingsId'] = self._serialize.url('test_settings_id', test_settings_id, 'int')
        self._send(http_method='DELETE',
                   location_id='8133ce14-962f-42af-a5f9-6aa9defcb9c8',
                   version='4.0',
                   route_values=route_values)

    def get_test_settings_by_id(self, project, test_settings_id):
        """GetTestSettingsById.
        :param str project: Project ID or project name
        :param int test_settings_id:
        :rtype: :class:`<TestSettings> <test.v4_0.models.TestSettings>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if test_settings_id is not None:
            route_values['testSettingsId'] = self._serialize.url('test_settings_id', test_settings_id, 'int')
        response = self._send(http_method='GET',
                              location_id='8133ce14-962f-42af-a5f9-6aa9defcb9c8',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('TestSettings', response)

    def create_test_variable(self, test_variable, project):
        """CreateTestVariable.
        [Preview API]
        :param :class:`<TestVariable> <test.v4_0.models.TestVariable>` test_variable:
        :param str project: Project ID or project name
        :rtype: :class:`<TestVariable> <test.v4_0.models.TestVariable>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(test_variable, 'TestVariable')
        response = self._send(http_method='POST',
                              location_id='be3fcb2b-995b-47bf-90e5-ca3cf9980912',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TestVariable', response)

    def delete_test_variable(self, project, test_variable_id):
        """DeleteTestVariable.
        [Preview API]
        :param str project: Project ID or project name
        :param int test_variable_id:
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if test_variable_id is not None:
            route_values['testVariableId'] = self._serialize.url('test_variable_id', test_variable_id, 'int')
        self._send(http_method='DELETE',
                   location_id='be3fcb2b-995b-47bf-90e5-ca3cf9980912',
                   version='4.0-preview.1',
                   route_values=route_values)

    def get_test_variable_by_id(self, project, test_variable_id):
        """GetTestVariableById.
        [Preview API]
        :param str project: Project ID or project name
        :param int test_variable_id:
        :rtype: :class:`<TestVariable> <test.v4_0.models.TestVariable>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if test_variable_id is not None:
            route_values['testVariableId'] = self._serialize.url('test_variable_id', test_variable_id, 'int')
        response = self._send(http_method='GET',
                              location_id='be3fcb2b-995b-47bf-90e5-ca3cf9980912',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('TestVariable', response)

    def get_test_variables(self, project, skip=None, top=None):
        """GetTestVariables.
        [Preview API]
        :param str project: Project ID or project name
        :param int skip:
        :param int top:
        :rtype: [TestVariable]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        response = self._send(http_method='GET',
                              location_id='be3fcb2b-995b-47bf-90e5-ca3cf9980912',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[TestVariable]', self._unwrap_collection(response))

    def update_test_variable(self, test_variable, project, test_variable_id):
        """UpdateTestVariable.
        [Preview API]
        :param :class:`<TestVariable> <test.v4_0.models.TestVariable>` test_variable:
        :param str project: Project ID or project name
        :param int test_variable_id:
        :rtype: :class:`<TestVariable> <test.v4_0.models.TestVariable>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if test_variable_id is not None:
            route_values['testVariableId'] = self._serialize.url('test_variable_id', test_variable_id, 'int')
        content = self._serialize.body(test_variable, 'TestVariable')
        response = self._send(http_method='PATCH',
                              location_id='be3fcb2b-995b-47bf-90e5-ca3cf9980912',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TestVariable', response)

    def add_work_item_to_test_links(self, work_item_to_test_links, project):
        """AddWorkItemToTestLinks.
        [Preview API]
        :param :class:`<WorkItemToTestLinks> <test.v4_0.models.WorkItemToTestLinks>` work_item_to_test_links:
        :param str project: Project ID or project name
        :rtype: :class:`<WorkItemToTestLinks> <test.v4_0.models.WorkItemToTestLinks>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(work_item_to_test_links, 'WorkItemToTestLinks')
        response = self._send(http_method='POST',
                              location_id='371b1655-ce05-412e-a113-64cc77bb78d2',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('WorkItemToTestLinks', response)

    def delete_test_method_to_work_item_link(self, project, test_name, work_item_id):
        """DeleteTestMethodToWorkItemLink.
        [Preview API]
        :param str project: Project ID or project name
        :param str test_name:
        :param int work_item_id:
        :rtype: bool
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if test_name is not None:
            query_parameters['testName'] = self._serialize.query('test_name', test_name, 'str')
        if work_item_id is not None:
            query_parameters['workItemId'] = self._serialize.query('work_item_id', work_item_id, 'int')
        response = self._send(http_method='DELETE',
                              location_id='7b0bdee3-a354-47f9-a42c-89018d7808d5',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('bool', response)

    def query_test_method_linked_work_items(self, project, test_name):
        """QueryTestMethodLinkedWorkItems.
        [Preview API]
        :param str project: Project ID or project name
        :param str test_name:
        :rtype: :class:`<TestToWorkItemLinks> <test.v4_0.models.TestToWorkItemLinks>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if test_name is not None:
            query_parameters['testName'] = self._serialize.query('test_name', test_name, 'str')
        response = self._send(http_method='POST',
                              location_id='7b0bdee3-a354-47f9-a42c-89018d7808d5',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('TestToWorkItemLinks', response)

    def query_test_result_work_items(self, project, work_item_category, automated_test_name=None, test_case_id=None, max_complete_date=None, days=None, work_item_count=None):
        """QueryTestResultWorkItems.
        [Preview API]
        :param str project: Project ID or project name
        :param str work_item_category:
        :param str automated_test_name:
        :param int test_case_id:
        :param datetime max_complete_date:
        :param int days:
        :param int work_item_count:
        :rtype: [WorkItemReference]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if work_item_category is not None:
            query_parameters['workItemCategory'] = self._serialize.query('work_item_category', work_item_category, 'str')
        if automated_test_name is not None:
            query_parameters['automatedTestName'] = self._serialize.query('automated_test_name', automated_test_name, 'str')
        if test_case_id is not None:
            query_parameters['testCaseId'] = self._serialize.query('test_case_id', test_case_id, 'int')
        if max_complete_date is not None:
            query_parameters['maxCompleteDate'] = self._serialize.query('max_complete_date', max_complete_date, 'iso-8601')
        if days is not None:
            query_parameters['days'] = self._serialize.query('days', days, 'int')
        if work_item_count is not None:
            query_parameters['$workItemCount'] = self._serialize.query('work_item_count', work_item_count, 'int')
        response = self._send(http_method='GET',
                              location_id='926ff5dc-137f-45f0-bd51-9412fa9810ce',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[WorkItemReference]', self._unwrap_collection(response))

