# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, LiveScenarioTest, api_version_constraint,
    StorageAccountPreparer, JMESPathCheck, StringContainCheck, VirtualNetworkPreparer, KeyVaultPreparer)


class TestIdentity(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_identity_mgmt_')
    def test_identity_management(self, resource_group):
        self.kwargs.update({
            'identity': 'myidentity'
        })

        operations = self.cmd('identity list-operations').get_output_in_json()
        self.assertGreaterEqual(len(operations), 1)

        self.cmd('identity create -n {identity} -g {rg}', checks=[
            self.check('name', '{identity}'),
            self.check('resourceGroup', '{rg}'),
            self.check('isolationScope', 'None')
        ])

        self.cmd('identity update -n {identity} -g {rg} --isolation-scope Regional', checks=[
            self.check('name', '{identity}'),
            self.check('resourceGroup', '{rg}'),
            self.check('isolationScope', 'Regional')
        ])

        self.cmd('identity list-resources -g {rg} -n {identity}')

        self.cmd('identity list -g {rg}', checks=self.check('length(@)', 1))
        self.cmd('identity delete -n {identity} -g {rg}')

        self.cmd('identity create -n {identity} -g {rg} --isolation-scope Regional', checks=[
            self.check('name', '{identity}'),
            self.check('resourceGroup', '{rg}'),
            self.check('isolationScope', 'Regional')
        ])

        self.cmd('identity update -n {identity} -g {rg} --isolation-scope None', checks=[
            self.check('name', '{identity}'),
            self.check('resourceGroup', '{rg}'),
            self.check('isolationScope', 'None')
        ])

        self.cmd('identity delete -n {identity} -g {rg}')

    @ResourceGroupPreparer(name_prefix='cli_test_federated_identity_credential_', location='centraluseuap')
    def test_federated_identity_credential(self, resource_group):
        self.kwargs.update({
            'identity': 'ide',
            'fic1': 'fic1',
            'fic2': 'fic2',
            'fic3': 'fic3',
            'fic4': 'fic4',
            'subject1': 'system:serviceaccount:ns:svcaccount1',
            'subject2': 'system:serviceaccount:ns:svcaccount2',
            'subject3': 'system:serviceaccount:ns:svcaccount3',
            'subject4': 'system:serviceaccount:ns:svcaccount4',
            'issuer': 'https://login.microsoftonline.com/72f988bf-86f1-41af-91ab-2d7cd011db47/v2.0',
            'audience': 'api://AzureADTokenExchange',
            'cme_version': '1',
            'cme_value': "claims['sub'] eq 'foo'",
        })

        self.cmd('identity create -n {identity} -g {rg}')

        # create a federated identity credential using subject
        self.cmd('identity federated-credential create --name {fic1} --identity-name {identity} --resource-group {rg} '
                 '--subject {subject1} --issuer {issuer} --audiences {audience}',
                 checks=[
                     self.check('length(audiences)', 1),
                     self.check('audiences[0]', '{audience}'),
                     self.check('issuer', '{issuer}'),
                     self.check('subject', '{subject1}')
                 ])

        # create another federated identity credential using subject
        self.cmd('identity federated-credential create --name {fic2} --identity-name {identity} --resource-group {rg} '
                 '--subject {subject2} --issuer {issuer} --audiences {audience}',
                 checks=[
                     self.check('length(audiences)', 1),
                     self.check('audiences[0]', '{audience}'),
                     self.check('issuer', '{issuer}'),
                     self.check('subject', '{subject2}')
                 ])

        # create a federated identity credential using claims matching expression
        self.cmd('identity federated-credential create --name {fic3} --identity-name {identity} --resource-group {rg} '
                 '--claims-matching-expression-version {cme_version} '
                 '--claims-matching-expression-value "{cme_value}" '
                 '--issuer {issuer} --audiences {audience}',
                 checks=[
                     self.check('length(audiences)', 1),
                     self.check('audiences[0]', '{audience}'),
                     self.check('issuer', '{issuer}'),
                     self.check('claimsMatchingExpression.languageVersion', 1),
                     self.check('claimsMatchingExpression.value', "{cme_value}")
                 ])

        # show the federated identity credential with subject
        self.cmd('identity federated-credential show --name {fic1} --identity-name {identity} --resource-group {rg}',
                 checks=[
                     self.check('length(audiences)', 1),
                     self.check('audiences[0]', '{audience}'),
                     self.check('issuer', '{issuer}'),
                     self.check('subject', '{subject1}')
                 ])

        # show the federated identity credential with claims matching expression
        self.cmd('identity federated-credential show --name {fic3} --identity-name {identity} --resource-group {rg}',
                 checks=[
                     self.check('length(audiences)', 1),
                     self.check('audiences[0]', '{audience}'),
                     self.check('issuer', '{issuer}'),
                     self.check('claimsMatchingExpression.languageVersion', 1),
                     self.check('claimsMatchingExpression.value', "{cme_value}")
                 ])

        # list the federated identity credentials
        self.cmd('identity federated-credential list --identity-name {identity} --resource-group {rg}',
                 checks=[
                     self.check('type(@)', 'array'),
                     self.check('length(@)', 3),
                     self.check('length([0].audiences)', '1'),
                     self.check('[0].audiences[0]', '{audience}'),
                     self.check('[0].issuer', '{issuer}'),
                     self.check('[0].subject', '{subject1}'),
                     self.check('length([1].audiences)', '1'),
                     self.check('[1].audiences[0]', '{audience}'),
                     self.check('[1].issuer', '{issuer}'),
                     self.check('[1].subject', '{subject2}'),
                     self.check('length([2].audiences)', '1'),
                     self.check('[2].audiences[0]', '{audience}'),
                     self.check('[2].issuer', '{issuer}'),
                     self.check('[2].claimsMatchingExpression.languageVersion', 1),
                     self.check('[2].claimsMatchingExpression.value', "{cme_value}")
                 ])

        # update a federated identity credential with subject to a different subject
        self.kwargs['new_subject'] = 'system:serviceaccount:ns:newaccount'
        self.cmd('identity federated-credential update --name {fic1} --identity-name {identity} --resource-group {rg} '
                 '--subject {new_subject} --issuer {issuer} --audiences {audience}',
                 checks=[
                     self.check('name', '{fic1}'),
                     self.check('subject', '{new_subject}')
                 ])

        # update a federated identity credential with claims matching expression to a different expression
        self.kwargs['new_cme_value'] = "claims['sub'] eq 'updatedFoo'"
        self.cmd('identity federated-credential update --name {fic3} --identity-name {identity} --resource-group {rg} '
                 '--claims-matching-expression-version {cme_version} '
                 '--claims-matching-expression-value "{new_cme_value}" '
                 '--issuer {issuer} --audiences {audience}',
                 checks=[
                     self.check('name', '{fic3}'),
                     self.check('claimsMatchingExpression.languageVersion', 1),
                     self.check('claimsMatchingExpression.value', "{new_cme_value}")
                 ])

        # delete first federated identity credential
        self.cmd('identity federated-credential delete --name {fic1}'
                 ' --identity-name {identity} --resource-group {rg} --yes')
                 
        # verify remaining credentials after first deletion
        self.cmd('identity federated-credential list --identity-name {identity} --resource-group {rg}',
                 checks=[
                     self.check('type(@)', 'array'),
                     self.check('length(@)', 2),
                     self.check('[0].name', '{fic2}'),
                     self.check('[0].subject', '{subject2}'),
                     self.check('[1].name', '{fic3}'),
                     self.check('[1].claimsMatchingExpression.value', "{new_cme_value}")
                 ])

        # test default audiences value
        self.cmd('identity federated-credential create --name {fic4} --identity-name {identity} --resource-group {rg} '
                 '--subject {subject4} --issuer {issuer}',
                 checks=[
                     self.check('length(audiences)', 1),
                     self.check('audiences[0]', 'api://AzureADTokenExchange'),
                     self.check('issuer', '{issuer}'),
                     self.check('subject', '{subject4}')
                 ])
        
        # delete remaining federated identity credentials
        self.cmd('identity federated-credential delete --name {fic2}'
                 ' --identity-name {identity} --resource-group {rg} --yes')
        self.cmd('identity federated-credential delete --name {fic3}'
                 ' --identity-name {identity} --resource-group {rg} --yes')
        self.cmd('identity federated-credential delete --name {fic4}'
                 ' --identity-name {identity} --resource-group {rg} --yes')
        
        self.cmd('identity federated-credential list --identity-name {identity} --resource-group {rg}',
                 checks=[
                     self.check('type(@)', 'array'),
                     self.check('length(@)', 0)
                 ])
        