# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

# class DynamicShellCompletionsTest(ScenarioTest):

#     @ResourceGroupPreparer()
#     def test_list_dynamic_completions(self, resource_group):
#         """ tests dynamic completions """
#         self.cmd('az vm list -g')

#     @ResourceGroupPreparer()
#     def test_enum_completions(self):
#         """ tests enum completions """
#         self.cmd('acs create --orchestrator-type')

#     @ResourceGroupPreparer()
#     def test_parsing_for_dynamic_completions(self):
#         """ tests the parsing for dynamic completions to restrict completions """
#         self.cmd('az vm show -g {} -n')

#     @ResourceGroupPreparer()
#     def test_files_completion(self):
#         """ tests files completion """
#         self.cmd('az keyvault secret download --file')
