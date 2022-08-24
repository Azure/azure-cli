# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, ApiManagementPreparer)


class ApimApiReleaseScenarioTest(ScenarioTest):
    def setUp(self):
        self._initialize_variables()
        super(ApimApiReleaseScenarioTest, self).setUp()

    @ResourceGroupPreparer(name_prefix='cli_test_apim-', parameter_name_for_location='resource_group_location')
    @ApiManagementPreparer(parameter_name='apim_name', sku_name='Consumption')
    def test_apim_api_release(self, resource_group, apim_name):
        self._setup_an_api()
        self._setup_revision_of_the_api()

        # assert
        self._list_api_releases()
        self._create_api_release()
        self._then_show_api_release()
        self._then_update_api_release()
        self._delete_api_release()
        self._finally_api_release_count_should_match()

    def _list_api_releases(self):
        self.release_count = len(self.cmd('apim api release list -g "{rg}" -n "{apim}" --api-id "{api_id}"').get_output_in_json())

    def _create_api_release(self):
        self.cmd('apim api release create -g {rg} -n {apim} --api-id {api_id} --release-id {release_id} --api-revision {api_revision} --notes "{release_notes}"', checks=[
            self.check('name', '{release_id}'),
            self.check('notes', '{release_notes}')
        ])
        self.release_count += 1

    def _then_show_api_release(self):
        self.cmd('apim api release show -g {rg} -n {apim} --api-id "{api_id}" --release-id "{release_id}"')
        self.assertEqual(self.release_count, self._get_api_release_count())

    def _then_update_api_release(self):
        self.cmd('apim api release update -g "{rg}" -n "{apim}" --api-id "{api_id}" --release-id "{release_id}" --notes "{updated_release_notes}"', checks=[
            self.check('name', '{release_id}'),
            self.check('notes', '{updated_release_notes}')
        ])

    def _delete_api_release(self):
        self.cmd('apim api release delete -g "{rg}" -n "{apim}" --api-id "{api_id}" --release-id "{release_id}"')
        self.release_count -= 1
    
    def _finally_api_release_count_should_match(self):
        self.assertEqual(self.release_count, self._get_api_release_count())
    
    def _get_api_release_count(self):
        count = len(self.cmd('apim api release list -g "{rg}" -n "{apim}" --api-id "{api_id}"').get_output_in_json())
        return count

    def _setup_an_api(self):
        output = self.cmd('apim api create -n {apim} -g {rg} -a {api_id} --path {path} --display-name "{display_name}" --service-url {service_url}  --protocols {protocols}').get_output_in_json()
        self.kwargs.update({
            'source_api_id': output['id'].rpartition('/')[2]
        })

    def _setup_revision_of_the_api(self):
        self.cmd('apim api create -n {apim} -g {rg} -a "{revision_api_id}" --path {path} --source-api-id "{api_id}"')

    def _initialize_variables(self):
        self.initial_release_count = 0
        self.release_count = 0

        # api variables
        self.kwargs.update({
            'api_id': 'api-id',
            'path': 'api-path',
            'display_name': 'api display name',
            'service_url': 'http://echoapi.cloudapp.net/api',
            'protocols': 'http',
            'revision_api_id': 'api-id;rev=2',
            'api_revision': '2'
        })
        # release variables
        self.kwargs.update({
            'release_id': 'release-id',
            'release_notes': 'release notes for the release.',
            'updated_release_notes': 'updated release notes'
        })
