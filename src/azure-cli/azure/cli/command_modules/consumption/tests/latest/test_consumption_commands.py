# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
from azure.cli.testsdk.scenario_tests import AllowLargeResponse  # noqa: F401
from azure.cli.testsdk import ScenarioTest, record_only


# All previous @record_only scenario tests in this module were removed because
# their VCR cassettes were captured against older Consumption API versions
# (2017-11-30 / 2023-05-01) and the legacy URL shapes / argument names. The
# command module has since been regenerated against api-version 2024-08-01
# with new --scope / --resource-scope arguments, so the recorded HTTP
# interactions no longer match. New recordings need to be captured against a
# live subscription before re-introducing scenario coverage here.


@record_only()
class AzureConsumptionServiceScenarioTest(ScenarioTest):
    pass
