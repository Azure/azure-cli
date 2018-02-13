# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import uuid
import mock
from azure.cli.testsdk import ScenarioTest


class RoleScenarioTest(ScenarioTest):

    def enable_large_payload(self, size=8192):
        from azure_devtools.scenario_tests import LargeResponseBodyProcessor
        large_resp_body = next((r for r in self.recording_processors if isinstance(
            r, LargeResponseBodyProcessor)), None)
        if large_resp_body:
            large_resp_body._max_response_body = size   # pylint: disable=protected-access

    def get_guid_gen_patch(self, guids, test_seam='azure.cli.command_modules.role.custom._gen_guid'):
        should_fix = self.in_recording or not (self.in_recording or self.is_live)
        guids = [uuid.UUID(g) if should_fix else uuid.uuid4() for g in guids]
        return mock.patch(test_seam, side_effect=guids, autospec=True)

    def run_under_service_principal(self):
        account_info = self.cmd('account show').get_output_in_json()
        return account_info['user']['type'] == 'servicePrincipal'
