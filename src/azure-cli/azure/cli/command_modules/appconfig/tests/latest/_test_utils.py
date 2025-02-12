# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json

from azure.cli.testsdk.scenario_tests import RecordingProcessor
from azure.cli.testsdk.scenario_tests.utilities import is_json_payload
from azure.cli.core.util import shell_safe_json_parse

def _create_config_store(test, kwargs):
    if 'retention_days' not in kwargs:
        kwargs.update({
            'retention_days': 1
        })
    test.cmd('appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku} --retention-days {retention_days}')

class CredentialResponseSanitizer(RecordingProcessor):
    def process_response(self, response):
        if is_json_payload(response):
            try:
                json_data = shell_safe_json_parse(response["body"]["string"])

                if isinstance(json_data.get("value"), list):
                    for idx, credential in enumerate(json_data["value"]):
                        self._try_replace_secret(credential, idx)

                    response["body"]["string"] = json.dumps(json_data)
                
                elif isinstance(json_data, dict):
                    self._try_replace_secret(json_data)

                    response["body"]["string"] = json.dumps(json_data)

            except Exception:
                pass

        return response

    def _try_replace_secret(self, credential, idx = 0):
        if "connectionString" in credential:
            credential["id"] = "sanitized_id{}".format(idx + 1)
            credential["value"] = "sanitized_secret{}".format(idx + 1)

            endpoint = next(
                filter(lambda x: x.startswith("Endpoint="), credential["connectionString"].split(";")))[len("Endpoint="):]

            credential["connectionString"] = "Endpoint={};Id={};Secret={}".format(
                endpoint, credential["id"], credential["value"])