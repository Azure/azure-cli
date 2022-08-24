# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

import os
import unittest
from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, ApiManagementPreparer)


class ApimApiVersionSetScenarioTest(ScenarioTest):
    def setUp(self):
        self._initialize_variables()
        super(ApimApiVersionSetScenarioTest, self).setUp()

    @ResourceGroupPreparer(name_prefix='cli_test_apim-', parameter_name_for_location='resource_group_location')
    @ApiManagementPreparer(parameter_name='apim_name')
    def test_apim_api_versionset(self, resource_group, apim_name):
        initial_vs_count = len(self.cmd('apim api-version-set list -g "{rg}" -n "{apim}"').get_output_in_json())

        # create API version set
        self.cmd('apim api-version-set create -g "{rg}" -n "{apim}" --display-name "{display_name}" --id "{id}" --versioning-scheme "{versioning_scheme}" --description "{description}" --version-query-name "{version_query_name}"', checks=[
            self.check('displayName', '{display_name}'),
            self.check('description', '{description}'),
            self.check('versioningScheme', '{versioning_scheme}'),
            self.check('name', '{id}')
        ])

        # show API version set
        self.cmd('apim api-version-set show -g "{rg}" -n "{apim}" --version-set-id "{id}"')

        # update API version set
        self.cmd('apim api-version-set update -g "{rg}" -n "{apim}" --version-set-id "{id}" --display-name "{updated_display_name}"', checks=[
            self.check('displayName', '{updated_display_name}')
        ])

        # delete API version set
        self.cmd('apim api-version-set delete -g "{rg}" -n "{apim}" --version-set-id "{id}"')

        final_vs_count = len(self.cmd('apim api-version-set list -g "{rg}" -n "{apim}"').get_output_in_json())
        self.assertEqual(final_vs_count, initial_vs_count)

    def _initialize_variables(self):
        self.kwargs.update({
            'display_name': 'version set display name',
            'version_query_name': 'QueryName',
            'description': 'Version set description.',
            'id': 'version-set-id',
            'updated_display_name': 'Updated version set display name'
        })
