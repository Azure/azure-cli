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
            self.check('resourceGroup', '{rg}')
        ])
        self.cmd('identity list-resources -g {rg} -n {identity}')

        self.cmd('identity list -g {rg}', checks=self.check('length(@)', 1))
        self.cmd('identity delete -n {identity} -g {rg}')

    @ResourceGroupPreparer(name_prefix='cli_test_federated_identity_credential_', location='eastus2euap')
    def test_federated_identity_credential(self, resource_group):
        self.kwargs.update({
            'identity': 'ide',
            'fic1': 'fic1',
            'fic2': 'fic2',
            'subject1': 'system:serviceaccount:ns:svcaccount1',
            'subject2': 'system:serviceaccount:ns:svcaccount2',
            'subject3': 'system:serviceaccount:ns:svcaccount3',
            'issuer': 'https://oidc.prod-aks.azure.com/IssuerGUID',
            'audience': 'api://AzureADTokenExchange',
        })

        self.cmd('identity create -n {identity} -g {rg}')

        # create a federated identity credential
        self.cmd('identity federated-credential create --name {fic1} --identity-name {identity} --resource-group {rg} '
                 '--subject {subject1} --issuer {issuer} --audiences {audience}',
                 checks=[
                     self.check('length(audiences)', 1),
                     self.check('audiences[0]', '{audience}'),
                     self.check('issuer', '{issuer}'),
                     self.check('subject', '{subject1}')
                 ])

        # create a federated identity credential
        self.cmd('identity federated-credential create --name {fic2} --identity-name {identity} --resource-group {rg} '
                 '--subject {subject2} --issuer {issuer} --audiences {audience}',
                 checks=[
                     self.check('length(audiences)', 1),
                     self.check('audiences[0]', '{audience}'),
                     self.check('issuer', '{issuer}'),
                     self.check('subject', '{subject2}')
                 ])

        # show the federated identity credential
        self.cmd('identity federated-credential show --name {fic1} --identity-name {identity} --resource-group {rg}',
                 checks=[
                     self.check('length(audiences)', 1),
                     self.check('audiences[0]', '{audience}'),
                     self.check('issuer', '{issuer}'),
                     self.check('subject', '{subject1}')
                 ])

        # list the federated identity credential
        self.cmd('identity federated-credential list --identity-name {identity} --resource-group {rg}',
                 checks=[
                     self.check('type(@)', 'array'),
                     self.check('length(@)', 2),
                     self.check('length([0].audiences)', '1'),
                     self.check('[0].audiences[0]', '{audience}'),
                     self.check('[0].issuer', '{issuer}'),
                     self.check('[0].subject', '{subject1}'),
                     self.check('length([1].audiences)', '1'),
                     self.check('[1].audiences[0]', '{audience}'),
                     self.check('[1].issuer', '{issuer}'),
                     self.check('[1].subject', '{subject2}'),
                 ])

        # update a federated identity credential
        self.cmd('identity federated-credential update --name {fic1} --identity-name {identity} --resource-group {rg} '
                 '--subject {subject3} --issuer {issuer} --audiences {audience}',
                 checks=[
                     self.check('name', '{fic1}'),
                     self.check('subject', '{subject3}')
                 ])

        # delete a federated identity credential
        self.cmd('identity federated-credential delete --name {fic1}'
                 ' --identity-name {identity} --resource-group {rg} --yes')
        self.cmd('identity federated-credential list --identity-name {identity} --resource-group {rg}',
                 checks=[
                     self.check('type(@)', 'array'),
                     self.check('length(@)', 1),
                     self.check('[0].name', '{fic2}'),
                     self.check('length([0].audiences)', '1'),
                     self.check('[0].audiences[0]', '{audience}'),
                     self.check('[0].issuer', '{issuer}'),
                     self.check('[0].subject', '{subject2}'),
                 ])

        # delete a federated identity credential
        self.cmd('identity federated-credential delete --name {fic2}'
                 ' --identity-name {identity} --resource-group {rg} --yes')
        self.cmd('identity federated-credential list --identity-name {identity} --resource-group {rg}',
                 checks=[
                     self.check('type(@)', 'array'),
                     self.check('length(@)', 0)
                 ])
