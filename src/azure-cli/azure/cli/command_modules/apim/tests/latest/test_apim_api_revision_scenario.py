# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

import os
from random import randint
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, ApiManagementPreparer)


class ApimApiRevisionScenarioTest(ScenarioTest):
    def setUp(self):
        self._initialize_variables()
        super(ApimApiRevisionScenarioTest, self).setUp()

    @ResourceGroupPreparer(name_prefix='cli_test_apim-', parameter_name_for_location='resource_group_location')
    @ApiManagementPreparer(parameter_name='apim_name', sku_name='Consumption')
    def test_apim_api_revision(self, resource_group, apim_name):
        self._setup_an_api()

        self.cmd('apim api revision list -g "{rg}" -n "{apim}" --api-id "{api_id}"')
        self.cmd('apim api revision create -g "{rg}" -n "{apim}" --api-id "{api_id}"  --api-revision {api_revision} --api-revision-description "{api_revision_description}"')

    def _setup_an_api(self):
        output = self.cmd('apim api create -n {apim} -g {rg} -a {api_id} --path {path} --display-name "{display_name}" --description "{description}"  --service-url {service_url}  --protocols {protocols} --header-name {subscription_key_header_name} --querystring-name {subscription_key_query_string_name}').get_output_in_json()
        self.kwargs.update({
            'source_api_id': output['id'].rpartition('/')[2]
        })

    def _initialize_variables(self):
        # api variables
        self.kwargs.update({
            'api_id': 'api-id',
            'path': 'api-path',
            'display_name': 'api display name',
            'description': 'api description',
            'service_url': 'http://echoapi.cloudapp.net/api',
            'protocols': 'http',
            'subscription_key_header_name': 'header1234',
            'subscription_key_query_string_name': 'query1234'
        })
        # revision variables
        self.kwargs.update({
            'api_revision': str(randint(1, 9)),
            'api_revision_description': 'description of the revision.'
        })