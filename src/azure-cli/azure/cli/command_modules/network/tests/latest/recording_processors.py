# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk.scenario_tests import RecordingProcessor


def byte_to_str(byte_or_str):
    return str(byte_or_str, 'utf-8') if isinstance(byte_or_str, bytes) else byte_or_str


class StorageAccountSASReplacer(RecordingProcessor):
    SAS_REPLACEMENT = 'se=2020-10-27&sp=w&sv=2018-11-09&sr=c'

    def __init__(self):
        self._sas_tokens = []

    def reset(self):
        self._sas_tokens = []

    def add_sas_token(self, sas_token):
        self._sas_tokens.append(sas_token)

    def process_request(self, request):
        for sas_token in self._sas_tokens:
            body_string = byte_to_str(request.body)
            if body_string and sas_token in body_string:
                request.body = body_string.replace(sas_token, self.SAS_REPLACEMENT)
        return request
