# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64
from azure.cli.testsdk import (ScenarioTest, JMESPathCheck)

class ApiCollectionsTests(ScenarioTest):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=False, **kwargs)

    def test_security_api_collections(self):
        resource_group = "apicollectionstests"
        api_id = "echo-api-2"
        service_name = "demoapimservice2"

        nexttoken = base64.b64encode('{"next_link": null, "offset": 0}'.encode()).decode()

        self.cmd("az security api-collection create -g {} --api-id {} --service-name {}".format(resource_group, api_id, service_name), checks=[
            JMESPathCheck('name', api_id)
        ])

        self.cmd("az security api-collection wait --created -g {} --api-id {} --service-name {}".format(resource_group, api_id, service_name))

        collections = self.cmd("az security api-collection list -g {} --max-items 1 --next-token {}".format(resource_group, nexttoken)).get_output_in_json()
        assert len(collections) > 0

        collections = self.cmd("az security api-collection list -g {} --service-name {}".format(resource_group, service_name)).get_output_in_json()
        assert len(collections) > 0

        self.cmd("az security api-collection show -g {} --api-id {} --service-name {}".format(resource_group, api_id, service_name), checks=[
            JMESPathCheck('name', api_id),
            JMESPathCheck('provisioningState', 'Succeeded')
        ])

        self.cmd("az security api-collection delete --yes -g {} --name {} --service-name {}".format(resource_group, api_id, service_name))