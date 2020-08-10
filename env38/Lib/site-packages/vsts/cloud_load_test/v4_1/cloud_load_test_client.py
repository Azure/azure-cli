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


class CloudLoadTestClient(VssClient):
    """CloudLoadTest
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(CloudLoadTestClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = '7ae6d0a6-cda5-44cf-a261-28c392bed25c'

    def create_agent_group(self, group):
        """CreateAgentGroup.
        :param :class:`<AgentGroup> <cloud-load-test.v4_1.models.AgentGroup>` group: Agent group to be created
        :rtype: :class:`<AgentGroup> <cloud-load-test.v4_1.models.AgentGroup>`
        """
        content = self._serialize.body(group, 'AgentGroup')
        response = self._send(http_method='POST',
                              location_id='ab8d91c1-12d9-4ec5-874d-1ddb23e17720',
                              version='4.1',
                              content=content)
        return self._deserialize('AgentGroup', response)

    def get_agent_groups(self, agent_group_id=None, machine_setup_input=None, machine_access_data=None, outgoing_request_urls=None, agent_group_name=None):
        """GetAgentGroups.
        :param str agent_group_id: The agent group indentifier
        :param bool machine_setup_input:
        :param bool machine_access_data:
        :param bool outgoing_request_urls:
        :param str agent_group_name: Name of the agent group
        :rtype: object
        """
        route_values = {}
        if agent_group_id is not None:
            route_values['agentGroupId'] = self._serialize.url('agent_group_id', agent_group_id, 'str')
        query_parameters = {}
        if machine_setup_input is not None:
            query_parameters['machineSetupInput'] = self._serialize.query('machine_setup_input', machine_setup_input, 'bool')
        if machine_access_data is not None:
            query_parameters['machineAccessData'] = self._serialize.query('machine_access_data', machine_access_data, 'bool')
        if outgoing_request_urls is not None:
            query_parameters['outgoingRequestUrls'] = self._serialize.query('outgoing_request_urls', outgoing_request_urls, 'bool')
        if agent_group_name is not None:
            query_parameters['agentGroupName'] = self._serialize.query('agent_group_name', agent_group_name, 'str')
        response = self._send(http_method='GET',
                              location_id='ab8d91c1-12d9-4ec5-874d-1ddb23e17720',
                              version='4.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('object', response)

    def delete_static_agent(self, agent_group_id, agent_name):
        """DeleteStaticAgent.
        :param str agent_group_id: The agent group identifier
        :param str agent_name: Name of the static agent
        :rtype: str
        """
        route_values = {}
        if agent_group_id is not None:
            route_values['agentGroupId'] = self._serialize.url('agent_group_id', agent_group_id, 'str')
        query_parameters = {}
        if agent_name is not None:
            query_parameters['agentName'] = self._serialize.query('agent_name', agent_name, 'str')
        response = self._send(http_method='DELETE',
                              location_id='87e4b63d-7142-4b50-801e-72ba9ff8ee9b',
                              version='4.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('str', response)

    def get_static_agents(self, agent_group_id, agent_name=None):
        """GetStaticAgents.
        :param str agent_group_id: The agent group identifier
        :param str agent_name: Name of the static agent
        :rtype: object
        """
        route_values = {}
        if agent_group_id is not None:
            route_values['agentGroupId'] = self._serialize.url('agent_group_id', agent_group_id, 'str')
        query_parameters = {}
        if agent_name is not None:
            query_parameters['agentName'] = self._serialize.query('agent_name', agent_name, 'str')
        response = self._send(http_method='GET',
                              location_id='87e4b63d-7142-4b50-801e-72ba9ff8ee9b',
                              version='4.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('object', response)

    def get_application(self, application_id):
        """GetApplication.
        :param str application_id: Filter by APM application identifier.
        :rtype: :class:`<Application> <cloud-load-test.v4_1.models.Application>`
        """
        route_values = {}
        if application_id is not None:
            route_values['applicationId'] = self._serialize.url('application_id', application_id, 'str')
        response = self._send(http_method='GET',
                              location_id='2c986dce-8e8d-4142-b541-d016d5aff764',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('Application', response)

    def get_applications(self, type=None):
        """GetApplications.
        :param str type: Filters the results based on the plugin type.
        :rtype: [Application]
        """
        query_parameters = {}
        if type is not None:
            query_parameters['type'] = self._serialize.query('type', type, 'str')
        response = self._send(http_method='GET',
                              location_id='2c986dce-8e8d-4142-b541-d016d5aff764',
                              version='4.1',
                              query_parameters=query_parameters)
        return self._deserialize('[Application]', self._unwrap_collection(response))

    def get_counters(self, test_run_id, group_names, include_summary=None):
        """GetCounters.
        :param str test_run_id: The test run identifier
        :param str group_names: Comma separated names of counter groups, such as 'Application', 'Performance' and 'Throughput'
        :param bool include_summary:
        :rtype: [TestRunCounterInstance]
        """
        route_values = {}
        if test_run_id is not None:
            route_values['testRunId'] = self._serialize.url('test_run_id', test_run_id, 'str')
        query_parameters = {}
        if group_names is not None:
            query_parameters['groupNames'] = self._serialize.query('group_names', group_names, 'str')
        if include_summary is not None:
            query_parameters['includeSummary'] = self._serialize.query('include_summary', include_summary, 'bool')
        response = self._send(http_method='GET',
                              location_id='29265ea4-b5a5-4b2e-b054-47f5f6f00183',
                              version='4.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[TestRunCounterInstance]', self._unwrap_collection(response))

    def get_application_counters(self, application_id=None, plugintype=None):
        """GetApplicationCounters.
        :param str application_id: Filter by APM application identifier.
        :param str plugintype: Currently ApplicationInsights is the only available plugin type.
        :rtype: [ApplicationCounters]
        """
        query_parameters = {}
        if application_id is not None:
            query_parameters['applicationId'] = self._serialize.query('application_id', application_id, 'str')
        if plugintype is not None:
            query_parameters['plugintype'] = self._serialize.query('plugintype', plugintype, 'str')
        response = self._send(http_method='GET',
                              location_id='c1275ce9-6d26-4bc6-926b-b846502e812d',
                              version='4.1',
                              query_parameters=query_parameters)
        return self._deserialize('[ApplicationCounters]', self._unwrap_collection(response))

    def get_counter_samples(self, counter_sample_query_details, test_run_id):
        """GetCounterSamples.
        :param :class:`<VssJsonCollectionWrapper> <cloud-load-test.v4_1.models.VssJsonCollectionWrapper>` counter_sample_query_details:
        :param str test_run_id: The test run identifier
        :rtype: :class:`<CounterSamplesResult> <cloud-load-test.v4_1.models.CounterSamplesResult>`
        """
        route_values = {}
        if test_run_id is not None:
            route_values['testRunId'] = self._serialize.url('test_run_id', test_run_id, 'str')
        content = self._serialize.body(counter_sample_query_details, 'VssJsonCollectionWrapper')
        response = self._send(http_method='POST',
                              location_id='bad18480-7193-4518-992a-37289c5bb92d',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('CounterSamplesResult', response)

    def get_load_test_run_errors(self, test_run_id, type=None, sub_type=None, detailed=None):
        """GetLoadTestRunErrors.
        :param str test_run_id: The test run identifier
        :param str type: Filter for the particular type of errors.
        :param str sub_type: Filter for a particular subtype of errors. You should not provide error subtype without error type.
        :param bool detailed: To include the details of test errors such as messagetext, request, stacktrace, testcasename, scenarioname, and lasterrordate.
        :rtype: :class:`<LoadTestErrors> <cloud-load-test.v4_1.models.LoadTestErrors>`
        """
        route_values = {}
        if test_run_id is not None:
            route_values['testRunId'] = self._serialize.url('test_run_id', test_run_id, 'str')
        query_parameters = {}
        if type is not None:
            query_parameters['type'] = self._serialize.query('type', type, 'str')
        if sub_type is not None:
            query_parameters['subType'] = self._serialize.query('sub_type', sub_type, 'str')
        if detailed is not None:
            query_parameters['detailed'] = self._serialize.query('detailed', detailed, 'bool')
        response = self._send(http_method='GET',
                              location_id='b52025a7-3fb4-4283-8825-7079e75bd402',
                              version='4.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('LoadTestErrors', response)

    def get_test_run_messages(self, test_run_id):
        """GetTestRunMessages.
        :param str test_run_id: Id of the test run
        :rtype: [Microsoft.VisualStudio.TestService.WebApiModel.TestRunMessage]
        """
        route_values = {}
        if test_run_id is not None:
            route_values['testRunId'] = self._serialize.url('test_run_id', test_run_id, 'str')
        response = self._send(http_method='GET',
                              location_id='2e7ba122-f522-4205-845b-2d270e59850a',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('[Microsoft.VisualStudio.TestService.WebApiModel.TestRunMessage]', self._unwrap_collection(response))

    def get_plugin(self, type):
        """GetPlugin.
        :param str type: Currently ApplicationInsights is the only available plugin type.
        :rtype: :class:`<ApplicationType> <cloud-load-test.v4_1.models.ApplicationType>`
        """
        route_values = {}
        if type is not None:
            route_values['type'] = self._serialize.url('type', type, 'str')
        response = self._send(http_method='GET',
                              location_id='7dcb0bb2-42d5-4729-9958-c0401d5e7693',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('ApplicationType', response)

    def get_plugins(self):
        """GetPlugins.
        :rtype: [ApplicationType]
        """
        response = self._send(http_method='GET',
                              location_id='7dcb0bb2-42d5-4729-9958-c0401d5e7693',
                              version='4.1')
        return self._deserialize('[ApplicationType]', self._unwrap_collection(response))

    def get_load_test_result(self, test_run_id):
        """GetLoadTestResult.
        :param str test_run_id: The test run identifier
        :rtype: :class:`<TestResults> <cloud-load-test.v4_1.models.TestResults>`
        """
        route_values = {}
        if test_run_id is not None:
            route_values['testRunId'] = self._serialize.url('test_run_id', test_run_id, 'str')
        response = self._send(http_method='GET',
                              location_id='5ed69bd8-4557-4cec-9b75-1ad67d0c257b',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('TestResults', response)

    def create_test_definition(self, test_definition):
        """CreateTestDefinition.
        :param :class:`<TestDefinition> <cloud-load-test.v4_1.models.TestDefinition>` test_definition: Test definition to be created
        :rtype: :class:`<TestDefinition> <cloud-load-test.v4_1.models.TestDefinition>`
        """
        content = self._serialize.body(test_definition, 'TestDefinition')
        response = self._send(http_method='POST',
                              location_id='a8f9b135-f604-41ea-9d74-d9a5fd32fcd8',
                              version='4.1',
                              content=content)
        return self._deserialize('TestDefinition', response)

    def get_test_definition(self, test_definition_id):
        """GetTestDefinition.
        :param str test_definition_id: The test definition identifier
        :rtype: :class:`<TestDefinition> <cloud-load-test.v4_1.models.TestDefinition>`
        """
        route_values = {}
        if test_definition_id is not None:
            route_values['testDefinitionId'] = self._serialize.url('test_definition_id', test_definition_id, 'str')
        response = self._send(http_method='GET',
                              location_id='a8f9b135-f604-41ea-9d74-d9a5fd32fcd8',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('TestDefinition', response)

    def get_test_definitions(self, from_date=None, to_date=None, top=None):
        """GetTestDefinitions.
        :param str from_date: Date after which test definitions were created
        :param str to_date: Date before which test definitions were crated
        :param int top:
        :rtype: [TestDefinitionBasic]
        """
        query_parameters = {}
        if from_date is not None:
            query_parameters['fromDate'] = self._serialize.query('from_date', from_date, 'str')
        if to_date is not None:
            query_parameters['toDate'] = self._serialize.query('to_date', to_date, 'str')
        if top is not None:
            query_parameters['top'] = self._serialize.query('top', top, 'int')
        response = self._send(http_method='GET',
                              location_id='a8f9b135-f604-41ea-9d74-d9a5fd32fcd8',
                              version='4.1',
                              query_parameters=query_parameters)
        return self._deserialize('[TestDefinitionBasic]', self._unwrap_collection(response))

    def update_test_definition(self, test_definition):
        """UpdateTestDefinition.
        :param :class:`<TestDefinition> <cloud-load-test.v4_1.models.TestDefinition>` test_definition:
        :rtype: :class:`<TestDefinition> <cloud-load-test.v4_1.models.TestDefinition>`
        """
        content = self._serialize.body(test_definition, 'TestDefinition')
        response = self._send(http_method='PUT',
                              location_id='a8f9b135-f604-41ea-9d74-d9a5fd32fcd8',
                              version='4.1',
                              content=content)
        return self._deserialize('TestDefinition', response)

    def create_test_drop(self, web_test_drop):
        """CreateTestDrop.
        :param :class:`<Microsoft.VisualStudio.TestService.WebApiModel.TestDrop> <cloud-load-test.v4_1.models.Microsoft.VisualStudio.TestService.WebApiModel.TestDrop>` web_test_drop: Test drop to be created
        :rtype: :class:`<Microsoft.VisualStudio.TestService.WebApiModel.TestDrop> <cloud-load-test.v4_1.models.Microsoft.VisualStudio.TestService.WebApiModel.TestDrop>`
        """
        content = self._serialize.body(web_test_drop, 'Microsoft.VisualStudio.TestService.WebApiModel.TestDrop')
        response = self._send(http_method='POST',
                              location_id='d89d0e08-505c-4357-96f6-9729311ce8ad',
                              version='4.1',
                              content=content)
        return self._deserialize('Microsoft.VisualStudio.TestService.WebApiModel.TestDrop', response)

    def get_test_drop(self, test_drop_id):
        """GetTestDrop.
        :param str test_drop_id: The test drop identifier
        :rtype: :class:`<Microsoft.VisualStudio.TestService.WebApiModel.TestDrop> <cloud-load-test.v4_1.models.Microsoft.VisualStudio.TestService.WebApiModel.TestDrop>`
        """
        route_values = {}
        if test_drop_id is not None:
            route_values['testDropId'] = self._serialize.url('test_drop_id', test_drop_id, 'str')
        response = self._send(http_method='GET',
                              location_id='d89d0e08-505c-4357-96f6-9729311ce8ad',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('Microsoft.VisualStudio.TestService.WebApiModel.TestDrop', response)

    def create_test_run(self, web_test_run):
        """CreateTestRun.
        :param :class:`<TestRun> <cloud-load-test.v4_1.models.TestRun>` web_test_run:
        :rtype: :class:`<TestRun> <cloud-load-test.v4_1.models.TestRun>`
        """
        content = self._serialize.body(web_test_run, 'TestRun')
        response = self._send(http_method='POST',
                              location_id='b41a84ff-ff03-4ac1-b76e-e7ea25c92aba',
                              version='4.1',
                              content=content)
        return self._deserialize('TestRun', response)

    def get_test_run(self, test_run_id):
        """GetTestRun.
        :param str test_run_id: Unique ID of the test run
        :rtype: :class:`<TestRun> <cloud-load-test.v4_1.models.TestRun>`
        """
        route_values = {}
        if test_run_id is not None:
            route_values['testRunId'] = self._serialize.url('test_run_id', test_run_id, 'str')
        response = self._send(http_method='GET',
                              location_id='b41a84ff-ff03-4ac1-b76e-e7ea25c92aba',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('TestRun', response)

    def get_test_runs(self, name=None, requested_by=None, status=None, run_type=None, from_date=None, to_date=None, detailed=None, top=None, runsourceidentifier=None, retention_state=None):
        """GetTestRuns.
        Returns test runs based on the filter specified. Returns all runs of the tenant if there is no filter.
        :param str name: Name for the test run. Names are not unique. Test runs with same name are assigned sequential rolling numbers.
        :param str requested_by: Filter by the user who requested the test run. Here requestedBy should be the display name of the user.
        :param str status: Filter by the test run status.
        :param str run_type: Valid values include: null, one of TestRunType, or "*"
        :param str from_date: Filter by the test runs that have been modified after the fromDate timestamp.
        :param str to_date: Filter by the test runs that have been modified before the toDate timestamp.
        :param bool detailed: Include the detailed test run attributes.
        :param int top: The maximum number of test runs to return.
        :param str runsourceidentifier:
        :param str retention_state:
        :rtype: object
        """
        query_parameters = {}
        if name is not None:
            query_parameters['name'] = self._serialize.query('name', name, 'str')
        if requested_by is not None:
            query_parameters['requestedBy'] = self._serialize.query('requested_by', requested_by, 'str')
        if status is not None:
            query_parameters['status'] = self._serialize.query('status', status, 'str')
        if run_type is not None:
            query_parameters['runType'] = self._serialize.query('run_type', run_type, 'str')
        if from_date is not None:
            query_parameters['fromDate'] = self._serialize.query('from_date', from_date, 'str')
        if to_date is not None:
            query_parameters['toDate'] = self._serialize.query('to_date', to_date, 'str')
        if detailed is not None:
            query_parameters['detailed'] = self._serialize.query('detailed', detailed, 'bool')
        if top is not None:
            query_parameters['top'] = self._serialize.query('top', top, 'int')
        if runsourceidentifier is not None:
            query_parameters['runsourceidentifier'] = self._serialize.query('runsourceidentifier', runsourceidentifier, 'str')
        if retention_state is not None:
            query_parameters['retentionState'] = self._serialize.query('retention_state', retention_state, 'str')
        response = self._send(http_method='GET',
                              location_id='b41a84ff-ff03-4ac1-b76e-e7ea25c92aba',
                              version='4.1',
                              query_parameters=query_parameters)
        return self._deserialize('object', response)

    def update_test_run(self, web_test_run, test_run_id):
        """UpdateTestRun.
        :param :class:`<TestRun> <cloud-load-test.v4_1.models.TestRun>` web_test_run:
        :param str test_run_id:
        """
        route_values = {}
        if test_run_id is not None:
            route_values['testRunId'] = self._serialize.url('test_run_id', test_run_id, 'str')
        content = self._serialize.body(web_test_run, 'TestRun')
        self._send(http_method='PATCH',
                   location_id='b41a84ff-ff03-4ac1-b76e-e7ea25c92aba',
                   version='4.1',
                   route_values=route_values,
                   content=content)

