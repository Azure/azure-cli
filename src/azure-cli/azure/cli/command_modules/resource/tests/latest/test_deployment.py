# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import shutil
import time
import unittest

from azure.cli.core.parser import IncorrectUsageError
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               create_random_name, live_only)
from azure.cli.testsdk.constants import AUX_SUBSCRIPTION, AUX_TENANT
from knack.util import CLIError

class TemplateSpecsTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_template_specs_list', parameter_name='resource_group_one', location='westus')
    @ResourceGroupPreparer(name_prefix='cli_test_template_specs_list', location='westus')
    def test_list_template_spec(self, resource_group, resource_group_one, resource_group_location):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_spec_name = self.create_random_name('cli-test-list-template-spec', 60)
        self.kwargs.update({
            'template_spec_name': template_spec_name,
            'tf': os.path.join(curr_dir, 'simple_deploy.json').replace('\\', '\\\\'),
            'rg': resource_group,
            'rg1': resource_group_one,
            'resource_group_location': resource_group_location,
        })

        template_spec_in_rg = self.cmd('ts create -g {rg} -n {template_spec_name} -v 1.0 -l {resource_group_location} -f "{tf}"').get_output_in_json()
        template_spec_in_rg1_2 = self.cmd('ts create -g {rg1} -n {template_spec_name} -v 2.0 -l {resource_group_location} -f "{tf}"').get_output_in_json()
        template_spec_in_rg1_3 = self.cmd('ts create -g {rg1} -n {template_spec_name} -v 3.0 -l {resource_group_location} -f "{tf}"').get_output_in_json()

        self.kwargs['template_spec_id_rg'] = template_spec_in_rg['id'].replace('/versions/1.0', '')

        self.kwargs['template_spec_version_id_rg1_2'] = template_spec_in_rg1_2['id']
        self.kwargs['template_spec_version_id_rg1_3'] = template_spec_in_rg1_3['id']
        self.kwargs['template_spec_id_rg1'] = template_spec_in_rg1_2['id'].replace('/versions/2.0', '')

        self.cmd('ts list -g {rg1}', checks=[
                 self.check("length([?id=='{template_spec_id_rg}'])", 0),
                 self.check("length([?id=='{template_spec_id_rg1}'])", 1),
                 ])

        self.cmd('ts list -g {rg}', checks=[
                 self.check("length([?id=='{template_spec_id_rg}'])", 1),
                 self.check("length([?id=='{template_spec_id_rg1}'])", 0)
                 ])

        self.cmd('ts list -g {rg1} -n {template_spec_name}', checks=[
                 self.check('length([])', 2),
                 self.check("length([?id=='{template_spec_version_id_rg1_2}'])", 1),
                 self.check("length([?id=='{template_spec_version_id_rg1_3}'])", 1)
                 ])

        self.cmd('ts list', checks=[
                 self.check("length([?id=='{template_spec_id_rg}'])", 1),
                 self.check("length([?id=='{template_spec_id_rg1}'])", 1),
                 ])

        # clean up
        self.cmd('ts delete --template-spec {template_spec_id_rg} --yes')
        self.cmd('ts delete --template-spec {template_spec_id_rg1} --yes')

    @ResourceGroupPreparer(name_prefix='cli_test_template_specs', location='westus')
    def test_create_template_specs(self, resource_group, resource_group_location):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_spec_name = self.create_random_name('cli-test-create-template-spec', 60)
        self.kwargs.update({
            'template_spec_name': template_spec_name,
            'tf': os.path.join(curr_dir, 'template_spec_with_multiline_strings.json').replace('\\', '\\\\'),
            'resource_group_location': resource_group_location,
            'description': '"AzCLI test root template spec"',
            'version_description': '"AzCLI test version of root template spec"',
        })

        result = self.cmd('ts create -g {rg} -n {template_spec_name} -v 1.0 -l {resource_group_location} -f "{tf}" --description {description} --version-description {version_description}', checks=[
            self.check('mainTemplate.variables.provider', "[split(parameters('resource'), '/')[0]]"),
            self.check('mainTemplate.variables.resourceType', "[replace(parameters('resource'), concat(variables('provider'), '/'), '')]"),
            self.check('mainTemplate.variables.hyphenedName', ("[format('[0]-[1]-[2]-[3]-[4]-[5]', parameters('customer'), variables('environments')[parameters('environment')], variables('locations')[parameters('location')], parameters('group'), parameters('service'), if(equals(parameters('kind'), ''), variables('resources')[variables('provider')][variables('resourceType')], variables('resources')[variables('provider')][variables('resourceType')][parameters('kind')]))]")),
            self.check('mainTemplate.variables.removeOptionalsFromHyphenedName', "[replace(variables('hyphenedName'), '--', '-')]"),
            self.check('mainTemplate.variables.isInstanceCount', "[greater(parameters('instance'), -1)]"),
            self.check('mainTemplate.variables.hyphenedNameAfterInstanceCount', "[if(variables('isInstanceCount'), format('[0]-[1]', variables('removeOptionalsFromHyphenedName'), string(parameters('instance'))), variables('removeOptionalsFromHyphenedName'))]"),
            self.check('mainTemplate.variables.name', "[if(parameters('useHyphen'), variables('hyphenedNameAfterInstanceCount'), replace(variables('hyphenedNameAfterInstanceCount'), '-', ''))]")
        ]).get_output_in_json()

        with self.assertRaises(IncorrectUsageError) as err:
            self.cmd('ts create --name {template_spec_name} -g {rg} -l {resource_group_location} --template-file "{tf}"')
            self.assertTrue("please provide --template-uri if --query-string is specified" in str(err.exception))

        # clean up
        self.kwargs['template_spec_id'] = result['id'].replace('/versions/1.0', '')
        self.cmd('ts delete --template-spec {template_spec_id} --yes')

    @ResourceGroupPreparer(name_prefix='cli_test_template_specs', location='westus')
    def test_create_template_specs_with_artifacts(self, resource_group, resource_group_location):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_spec_name = self.create_random_name('cli-test-create-template-spec', 60)
        self.kwargs.update({
            'template_spec_name': template_spec_name,
            'tf': os.path.join(curr_dir, 'template_spec_with_artifacts.json').replace('\\', '\\\\'),
            'resource_group_location': resource_group_location,
            'display_name': self.create_random_name('create-spec', 20),
            'description': '"AzCLI test root template spec"',
            'version_description': '"AzCLI test version of root template spec"',
            'uf': os.path.join(curr_dir, 'sample_form_ui_definition_rg.json').replace('\\', '\\\\')
        })

        path = os.path.join(curr_dir, 'artifacts')
        if not os.path.exists(path):
            files = ['createKeyVault.json', 'createKeyVaultWithSecret.json', 'createResourceGroup.json']
            os.makedirs(path)
            for f in files:
                shutil.copy(os.path.join(curr_dir, f), path)

        result = self.cmd('ts create -g {rg} -n {template_spec_name} -v 1.0 -l {resource_group_location} -f "{tf}" --ui-form-definition "{uf}" -d {display_name} --description {description} --version-description {version_description}', checks=[
            self.check('linkedTemplates.length([])', 3),
            self.check_pattern('linkedTemplates[0].path', 'artifacts.createResourceGroup.json'),
            self.check_pattern('linkedTemplates[1].path', 'artifacts.createKeyVault.json'),
            self.check_pattern('linkedTemplates[2].path', 'artifacts.createKeyVaultWithSecret.json'),
            self.check('uiFormDefinition.view.properties.title', 'titleFooRG')
        ]).get_output_in_json()

        self.cmd('ts create -g {rg} -n {template_spec_name} -v 1.0 -f "{tf}" --yes', checks=[
            self.check('description', None),
            self.check('display_name', None),
        ])

        # clean up
        self.kwargs['template_spec_id'] = result['id'].replace('/versions/1.0', '')
        self.cmd('ts delete --template-spec {template_spec_id} --yes')

    @ResourceGroupPreparer(name_prefix='cli_test_template_specs', location='westus')
    def test_update_template_specs(self, resource_group, resource_group_location):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_spec_name = self.create_random_name('cli-test-update-template-spec', 60)
        self.kwargs.update({
            'template_spec_name': template_spec_name,
            'tf': os.path.join(curr_dir, 'simple_deploy.json').replace('\\', '\\\\'),
            'tf1': os.path.join(curr_dir, 'template_spec_with_artifacts.json').replace('\\', '\\\\'),
            'resource_group_location': resource_group_location,
            'display_name': self.create_random_name('create-spec', 20),
            'description': '"AzCLI test root template spec"',
            'version_description': '"AzCLI test version of root template spec"',
            'uf': os.path.join(curr_dir, 'sample_form_ui_definition_sub.json').replace('\\', '\\\\'),
            'uf1': os.path.join(curr_dir, 'sample_form_ui_definition_mg.json').replace('\\', '\\\\'),
        })

        result = self.cmd('ts create -g {rg} -n {template_spec_name} -v 1.0 -l {resource_group_location} -f "{tf}"', checks=[
                          self.check('name', '1.0'),
                          self.check('description', None),
                          self.check('display_name', None),
                          self.check('artifacts', None)]).get_output_in_json()
        self.kwargs['template_spec_version_id'] = result['id']
        self.kwargs['template_spec_id'] = result['id'].replace('/versions/1.0', '')

        self.cmd('ts update -s {template_spec_id} --display-name {display_name} --description {description} --yes', checks=[
            self.check('name', self.kwargs['template_spec_name']),
            self.check('description', self.kwargs['description'].replace('"', '')),
            self.check('displayName', self.kwargs['display_name'].replace('"', ''))
        ])

        self.cmd('ts update -s {template_spec_version_id} --version-description {version_description} --yes', checks=[
            self.check('name', '1.0'),
            self.check('description', self.kwargs['version_description'].replace('"', '')),
            self.check('linkedTemplates', None)
        ])

        path = os.path.join(curr_dir, 'artifacts')
        if not os.path.exists(path):
            files = ['createKeyVault.json', 'createKeyVaultWithSecret.json', 'createResourceGroup.json']
            os.makedirs(path)
            for f in files:
                shutil.copy(os.path.join(curr_dir, f), path)

        self.cmd('ts update -g {rg} -n {template_spec_name} -v 1.0 -f "{tf1}" --ui-form-definition "{uf1}" --yes', checks=[
            self.check('description', self.kwargs['version_description'].replace('"', '')),
            self.check('linkedTemplates.length([])', 3),
            self.check_pattern('linkedTemplates[0].path', 'artifacts.createResourceGroup.json'),
            self.check_pattern('linkedTemplates[1].path', 'artifacts.createKeyVault.json'),
            self.check_pattern('linkedTemplates[2].path', 'artifacts.createKeyVaultWithSecret.json'),
            self.check('uiFormDefinition.view.properties.title', 'titleFooMG')
        ])

        # clean up
        self.cmd('ts delete --template-spec {template_spec_id} --yes')

    @ResourceGroupPreparer(name_prefix='cli_test_template_specs', location='westus')
    def test_show_template_spec(self, resource_group, resource_group_location):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_spec_name = self.create_random_name('cli-test-get-template-spec', 60)
        self.kwargs.update({
            'template_spec_name': template_spec_name,
            'tf': os.path.join(curr_dir, 'simple_deploy.json').replace('\\', '\\\\'),
            'resource_group_location': resource_group_location,
        })

        result = self.cmd('ts create -g {rg} -n {template_spec_name} -v 1.0 -l {resource_group_location} -f "{tf}"', checks=[
                          self.check('name', '1.0')]).get_output_in_json()
        self.kwargs['template_spec_version_id'] = result['id']
        self.kwargs['template_spec_id'] = result['id'].replace('/versions/1.0', '')

        ts_parent = self.cmd('ts show -g {rg} --name {template_spec_name}').get_output_in_json()
        assert len(ts_parent) > 0
        self.assertTrue(ts_parent['versions'] is not None)
        ts_parent_by_id = self.cmd('ts show --template-spec {template_spec_id}').get_output_in_json()
        assert len(ts_parent_by_id) > 0
        assert len(ts_parent) == len(ts_parent_by_id)

        ts_version = self.cmd('ts show -g {rg} --name {template_spec_name} --version 1.0').get_output_in_json()
        assert len(ts_version) > 0
        ts_version_by_id = self.cmd('ts show --template-spec {template_spec_version_id}').get_output_in_json()
        assert len(ts_version_by_id) > 0
        assert len(ts_version_by_id) == len(ts_version_by_id)

        # clean up
        self.cmd('ts delete --template-spec {template_spec_id} --yes')

    @ResourceGroupPreparer(name_prefix='cli_test_template_specs', location='westus')
    def test_delete_template_spec(self, resource_group, resource_group_location):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_spec_name = self.create_random_name('cli-test-list-template-spec', 60)
        self.kwargs.update({
            'resource_group_location': resource_group_location,
            'template_spec_name': template_spec_name,
            'tf': os.path.join(curr_dir, 'simple_deploy.json').replace('\\', '\\\\'),
        })

        result = self.cmd('ts create -g {rg} -n {template_spec_name} -v 1.0 -l {resource_group_location} -f "{tf}"',
                          checks=self.check('name', '1.0')).get_output_in_json()

        self.kwargs['template_spec_version_id'] = result['id']
        self.kwargs['template_spec_id'] = result['id'].replace('/versions/1.0', '')

        self.cmd('ts show --template-spec {template_spec_version_id}')
        self.cmd('ts show --template-spec {template_spec_id}')

        self.cmd('ts delete --template-spec {template_spec_version_id} --yes')
        self.cmd('ts list -g {rg}',
                 checks=[
                     self.check("length([?id=='{template_spec_id}'])", 1),
                     self.check("length([?id=='{template_spec_version_id}'])", 0)])

        self.cmd('ts delete --template-spec {template_spec_id} --yes')
        self.cmd('ts list -g {rg}',
                 checks=self.check("length([?id=='{template_spec_id}'])", 0))

    @ResourceGroupPreparer(name_prefix='cli_test_template_specs', location='westus')
    def test_template_spec_create_and_update_with_tags(self, resource_group, resource_group_location):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_spec_name = self.create_random_name('cli-test-template-spec-tags', 60)
        self.kwargs.update({
            'template_spec_name': template_spec_name,
            'tf': os.path.join(curr_dir, 'simple_deploy.json').replace('\\', '\\\\'),
            'resource_group_location': resource_group_location,
            'display_name': self.create_random_name('create-spec', 20),
            'version_tags': {'cliName1': 'cliValue1', 'cliName4': 'cliValue4'}
        })

        # Tags should be applied to both the parent template spec and template spec version if neither existed:

        result = self.cmd('ts create -g {rg} -n {template_spec_name} -v 1.0 -l {resource_group_location} -f "{tf}" --tags cli-test=test').get_output_in_json()
        self.kwargs['template_spec_version_one_id'] = result['id']
        self.kwargs['template_spec_id'] = result['id'].replace('/versions/1.0', '')

        self.cmd('ts show --template-spec {template_spec_version_one_id}', checks=[self.check('tags', {'cli-test': 'test'})])
        self.cmd('ts show --template-spec {template_spec_id}', checks=[self.check('tags', {'cli-test': 'test'})])

        # New template spec version should inherit tags from parent template spec if tags are not specified:

        self.cmd('ts create -g {rg} -n {template_spec_name} -v 2.0 -l {resource_group_location} -f "{tf}"')
        self.kwargs['template_spec_version_two_id'] = result['id'].replace('/versions/1.0', '/versions/2.0')

        self.cmd('ts show --template-spec {template_spec_version_two_id}', checks=[self.check('tags', {'cli-test': 'test'})])

        # Tags should only apply to template spec version (and not the parent template spec) if parent already exist:

        self.cmd('ts create -g {rg} -n {template_spec_name} -v 3.0 -l {resource_group_location} -f "{tf}" --tags cliName1=cliValue1 cliName4=cliValue4')
        self.kwargs['template_spec_version_three_id'] = result['id'].replace('/versions/1.0', '/versions/3.0')

        self.cmd('ts show --template-spec {template_spec_version_three_id}', checks=[self.check('tags', '{version_tags}')])
        self.cmd('ts show --template-spec {template_spec_id}', checks=[self.check('tags', {'cli-test': 'test'})])

        # When updating a template spec, tags should only be removed if explicitely empty. Create should override.

        self.cmd('ts update -g {rg} -n {template_spec_name} -v 1.0 -f "{tf}" --yes')
        self.cmd('ts show --template-spec {template_spec_version_one_id}', checks=[self.check('tags', {'cli-test': 'test'})])

        self.cmd('ts update -g {rg} -n {template_spec_name} -v 1.0 -f "{tf}" --tags "" --yes')
        self.cmd('ts show --template-spec {template_spec_version_one_id}', checks=[self.check('tags', {})])

        self.cmd('ts update -g {rg} -n {template_spec_name} -v 2.0 -f "{tf}" --tags --yes')
        self.cmd('ts show --template-spec {template_spec_version_two_id}', checks=[self.check('tags', {})])

        self.cmd('ts create -g {rg} -n {template_spec_name} -v 3.0 -f "{tf}" --tags --yes')
        self.cmd('ts show --template-spec {template_spec_version_three_id}', checks=[self.check('tags', {})])
        self.cmd('ts show --template-spec {template_spec_id}', checks=[self.check('tags', {'cli-test': 'test'})])

        self.cmd('ts create -g {rg} -n {template_spec_name} --yes')
        self.cmd('ts show --template-spec {template_spec_id}', checks=[self.check('tags', {})])

        # clean up
        self.cmd('ts delete --template-spec {template_spec_id} --yes')


class TemplateSpecsExportTest(LiveScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_export_template_spec', location='westus')
    def test_template_spec_export_version(self, resource_group, resource_group_location):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        dir_name = self.create_random_name('TemplateSpecExport', 30)
        dir_name2 = self.create_random_name('TemplateSpecExport', 30)
        template_spec_name = self.create_random_name('cli-test-export-template-spec', 60)
        self.kwargs.update({
            'template_spec_name': template_spec_name,
            'tf': os.path.join(curr_dir, 'template_spec_with_artifacts.json').replace('\\', '\\\\'),
            'resource_group_location': resource_group_location,
            'output_folder': os.path.join(curr_dir, dir_name).replace('\\', '\\\\'),
            'output_folder2': os.path.join(curr_dir, dir_name2).replace('\\', '\\\\'),
        })
        path = os.path.join(curr_dir, 'artifacts')
        if not os.path.exists(path):
            files = ['createKeyVault.json', 'createKeyVaultWithSecret.json', 'createResourceGroup.json']
            os.makedirs(path)
            for f in files:
                shutil.copy(os.path.join(curr_dir, f), path)

        result = self.cmd('ts create -g {rg} -n {template_spec_name} -v 1.0 -l {resource_group_location} -f "{tf}"',
                          checks=self.check('name', '1.0')).get_output_in_json()

        self.kwargs['template_spec_version_id'] = result['id']

        os.makedirs(self.kwargs['output_folder'])
        output_path = self.cmd('ts export -g {rg} --name {template_spec_name} --version 1.0 --output-folder {output_folder}').get_output_in_json()

        template_file = os.path.join(output_path, (self.kwargs['template_spec_name'] + '.json'))
        artifactFile = os.path.join(output_path, 'artifacts' + os.sep + 'createResourceGroup.json')
        artifactFile1 = os.path.join(output_path, 'artifacts' + os.sep + 'createKeyVault.json')
        artifactFile2 = os.path.join(output_path, 'artifacts' + os.sep + 'createKeyVaultWithSecret.json')

        self.assertTrue(os.path.isfile(template_file))
        self.assertTrue(os.path.isfile(artifactFile))
        self.assertTrue(os.path.isfile(artifactFile1))
        self.assertTrue(os.path.isfile(artifactFile2))

        os.makedirs(self.kwargs['output_folder2'])
        output_path2 = self.cmd('ts export --template-spec {template_spec_version_id} --output-folder {output_folder2}').get_output_in_json()

        _template_file = os.path.join(output_path2, (self.kwargs['template_spec_name'] + '.json'))
        _artifactFile = os.path.join(output_path2, 'artifacts' + os.sep + 'createResourceGroup.json')
        _artifactFile1 = os.path.join(output_path2, 'artifacts' + os.sep + 'createKeyVault.json')
        _artifactFile2 = os.path.join(output_path2, 'artifacts' + os.sep + 'createKeyVaultWithSecret.json')

        self.assertTrue(os.path.isfile(_template_file))
        self.assertTrue(os.path.isfile(_artifactFile))
        self.assertTrue(os.path.isfile(_artifactFile1))
        self.assertTrue(os.path.isfile(_artifactFile2))

    @ResourceGroupPreparer(name_prefix='cli_test_export_template_spec', location="westus")
    def test_template_spec_export_error_handling(self, resource_group, resource_group_location):
        self.kwargs.update({
            'template_spec_name': 'CLITestTemplateSpecExport',
            'output_folder': os.path.dirname(os.path.realpath(__file__)).replace('\\', '\\\\')
        })
        # Because exit_code is 1, so the exception caught should be an AssertionError
        with self.assertRaises(AssertionError) as err:
            self.cmd('ts export -g {rg} --name {template_spec_name} --output-folder {output_folder}')
            self.assertTrue('Please specify the template spec version for export' in str(err.exception))


class DeploymentTestsWithQueryString(LiveScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_query_str_rg', location='eastus')
    @StorageAccountPreparer(name_prefix='testquerystr', location='eastus', kind='StorageV2')
    def test_resource_group_level_deployment_with_query_string(self, resource_group, resource_group_location, storage_account):

        container_name = self.create_random_name('querystr', 20)
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        tf = os.path.join(curr_dir, 'resource_group_level_linked_template.json')
        linked_template = os.path.join(curr_dir, 'storage_account_linked_template.json')

        self.kwargs.update({
            'resource_group': resource_group,
            'storage_account': storage_account,
            'container_name': container_name,
            'tf': tf,
            'linked_tf': linked_template
        })

        self.kwargs['storage_key'] = str(self.cmd('az storage account keys list -n {storage_account} -g {resource_group} --query "[0].value"').output)

        self.cmd('storage container create -n {container_name} --account-name {storage_account} --account-key {storage_key}')

        self.cmd('storage blob upload -c {container_name} -f "{tf}" -n mainTemplate --account-name {storage_account} --account-key {storage_key}')
        self.cmd('storage blob upload -c {container_name} -f "{linked_tf}" -n storage_account_linked_template.json --account-name {storage_account} --account-key {storage_key}')

        from datetime import datetime, timedelta
        self.kwargs['expiry'] = (datetime.utcnow() + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%MZ')

        self.kwargs['sas_token'] = self.cmd(
            'storage container generate-sas --account-name {storage_account} --account-key {storage_key} --name {container_name} --permissions rw --expiry {expiry}  -otsv').output.strip()

        self.kwargs['blob_url'] = self.cmd(
            'storage blob url -c {container_name} -n mainTemplate --account-name {storage_account} --account-key {storage_key}').output.strip()

        self.cmd('deployment group validate -g {resource_group} --template-uri {blob_url} --query-string "{sas_token}" --parameters projectName=qsproject', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment group create -g {resource_group} --template-uri {blob_url} --query-string "{sas_token}" --parameters projectName=qsproject', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_query_str_sub', location='eastus')
    @StorageAccountPreparer(name_prefix='testquerystrsub', location='eastus', kind='StorageV2')
    def test_subscription_level_deployment_with_query_string(self, resource_group, resource_group_location, storage_account):

        container_name = self.create_random_name('querystr', 20)
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        tf = os.path.join(curr_dir, 'subscription_level_linked_template.json')
        linked_tf = os.path.join(curr_dir, 'createResourceGroup.json')
        linked_tf1 = os.path.join(curr_dir, 'createKeyVault.json')
        linked_tf2 = os.path.join(curr_dir, 'createKeyVaultWithSecret.json')

        self.kwargs.update({
            'resource_group': resource_group,
            'resource_group_location': resource_group_location,
            'storage_account': storage_account,
            'container_name': container_name,
            'tf': tf,
            'linked_tf': linked_tf,
            'linked_tf1': linked_tf1,
            'linked_tf2': linked_tf2
        })

        self.kwargs['storage_key'] = str(self.cmd('az storage account keys list -n {storage_account} -g {resource_group} --query "[0].value"').output)

        self.cmd('storage container create -n {container_name} --account-name {storage_account} --account-key {storage_key}')

        self.cmd('storage blob upload -c {container_name} -f "{tf}" -n mainTemplate --account-name {storage_account} --account-key {storage_key}')
        self.cmd('storage blob upload -c {container_name} -f "{linked_tf}" -n createResourceGroup.json --account-name {storage_account} --account-key {storage_key}')
        self.cmd('storage blob upload -c {container_name} -f "{linked_tf1}" -n createKeyVault.json --account-name {storage_account} --account-key {storage_key}')
        self.cmd('storage blob upload -c {container_name} -f "{linked_tf2}" -n createKeyVaultWithSecret.json --account-name {storage_account} --account-key {storage_key}')

        from datetime import datetime, timedelta
        self.kwargs['expiry'] = (datetime.utcnow() + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%MZ')

        self.kwargs['sas_token'] = self.cmd(
            'storage container generate-sas --account-name {storage_account} --name {container_name} --permissions dlrw --expiry {expiry} --https-only -otsv').output.strip()

        self.kwargs['blob_url'] = self.cmd(
            'storage blob url -c {container_name} -n mainTemplate --account-name {storage_account}').output.strip()

        self.kwargs['key_vault'] = self.create_random_name('querystrKV', 20)

        self.cmd('deployment sub validate -l {resource_group_location} --template-uri {blob_url} --query-string "{sas_token}" --parameters keyVaultName="{key_vault}" rgName="{resource_group}" rgLocation="{resource_group_location}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment sub create -l {resource_group_location} --template-uri {blob_url} --query-string "{sas_token}" --parameters keyVaultName="{key_vault}" rgName="{resource_group}" rgLocation="{resource_group_location}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])


class DeploymentTestAtSubscriptionScope(ScenarioTest):
    def tearDown(self):
        self.cmd('policy assignment delete -n location-lock')
        self.cmd('policy definition delete -n policy2')
        self.cmd('group delete -n cli_test_subscription_level_deployment --yes')

    @AllowLargeResponse(4096)
    def test_subscription_level_deployment(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'subscription_level_template.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'subscription_level_parameters.json').replace('\\', '\\\\'),
            # params-uri below is the raw file url of the subscription_level_parameters.json above
            'params_uri': 'https://raw.githubusercontent.com/Azure/azure-cli/dev/src/azure-cli/azure/cli/command_modules/resource/tests/latest/subscription_level_parameters.json',
            'dn': self.create_random_name('azure-cli-subscription_level_deployment', 60),
            'dn2': self.create_random_name('azure-cli-subscription_level_deployment', 60),
            'storage-account-name': self.create_random_name('armbuilddemo', 20)
        })

        self.cmd('deployment sub validate --location WestUS --template-file "{tf}" --parameters @"{params}" --parameters storageAccountName="{storage-account-name}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment sub validate --location WestUS --template-file "{tf}" --parameters "{params_uri}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment sub create -n {dn} --location WestUS --template-file "{tf}" --parameters @"{params}" --parameters storageAccountName="{storage-account-name}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
        ])

        self.cmd('deployment sub list', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment sub list --filter "provisioningState eq \'Succeeded\'"', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment sub show -n {dn}', checks=[
            self.check('name', '{dn}')
        ])

        self.cmd('deployment sub export -n {dn}', checks=[
        ])

        operations = self.cmd('deployment operation sub list -n {dn}', checks=[
            self.check('length([])', 5)
        ]).get_output_in_json()

        self.kwargs.update({
            'oid1': operations[0]['operationId'],
            'oid2': operations[1]['operationId'],
            'oid3': operations[2]['operationId'],
            'oid4': operations[3]['operationId'],
            'oid5': operations[4]['operationId']
        })
        self.cmd('deployment operation sub show -n {dn} --operation-ids {oid1} {oid2} {oid3} {oid4} {oid5}', checks=[
            self.check('[].properties.provisioningOperation', '[\'Create\', \'Create\', \'Create\', \'Create\', \'EvaluateDeploymentOutput\']'),
            self.check('[].properties.provisioningState', '[\'Succeeded\', \'Succeeded\', \'Succeeded\', \'Succeeded\', \'Succeeded\']')
        ])
        self.cmd('deployment sub delete -n {dn}')

        self.cmd('deployment sub create -n {dn2} --location WestUS --template-file "{tf}" --parameters @"{params}" '
                 '--parameters storageAccountName="{storage-account-name}" --no-wait')

        self.cmd('deployment sub cancel -n {dn2}')

        self.cmd('deployment sub wait -n {dn2} --custom "provisioningState==Canceled"')

        self.cmd('deployment sub show -n {dn2}', checks=[
            self.check('properties.provisioningState', 'Canceled')
        ])

    @AllowLargeResponse(4096)
    def test_subscription_level_deployment_old_command(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_name = self.create_random_name('azure-cli-subscription_level_deployment', 60)
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'subscription_level_template.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'subscription_level_parameters.json').replace('\\', '\\\\'),
            # params-uri below is the raw file url of the subscription_level_parameters.json above
            'params_uri': 'https://raw.githubusercontent.com/Azure/azure-cli/dev/src/azure-cli/azure/cli/command_modules/resource/tests/latest/subscription_level_parameters.json',
            'dn': deployment_name,
            'dn2': self.create_random_name('azure-cli-subscription_level_deployment', 60),
            'storage-account-name': self.create_random_name('armbuilddemo', 20)
        })

        self.cmd('deployment validate --location WestUS --template-file "{tf}" --parameters @"{params}" --parameters storageAccountName="{storage-account-name}" ', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment validate --location WestUS --template-file "{tf}" --parameters "{params_uri}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment create -n {dn} --location WestUS --template-file "{tf}" --parameters @"{params}" --parameters storageAccountName="{storage-account-name}" ', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
        ])

        self.cmd('deployment list --query "[?name == \'{}\']"'.format(deployment_name), checks=[
            self.check('[0].name', '{dn}'),
        ])
        self.cmd('deployment list --filter "provisioningState eq \'Succeeded\'" --query "[?name == \'{}\']"'.format(deployment_name), checks=[
            self.check('[0].name', '{dn}')
        ])
        self.cmd('deployment show -n {dn}', checks=[
            self.check('name', '{dn}')
        ])

        self.cmd('deployment export -n {dn}', checks=[
        ])

        self.cmd('deployment operation list -n {dn}', checks=[
            self.check('length([])', 5)
        ])

        self.cmd('deployment create -n {dn2} --location WestUS --template-file "{tf}" --parameters @"{params}" '
                 '--parameters storageAccountName="{storage-account-name}" --no-wait')

        self.cmd('deployment cancel -n {dn2}')

        self.cmd('deployment show -n {dn2}', checks=[
            self.check('properties.provisioningState', 'Canceled')
        ])


class DeploymentTestAtResourceGroup(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_resource_group_deployment')
    def test_resource_group_deployment(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'simple_deploy.json').replace('\\', '\\\\'),
            'tf_multiline': os.path.join(curr_dir, 'simple_deploy_multiline.json').replace('\\', '\\\\'),
            'tf_invalid': os.path.join(curr_dir, 'simple_deploy_invalid.json').replace('\\', '\\\\'),
            'extra_param_tf': os.path.join(curr_dir, 'simple_extra_param_deploy.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'simple_deploy_parameters.json').replace('\\', '\\\\'),
            'params_invalid': os.path.join(curr_dir, 'simple_deploy_parameters_invalid.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-resource-group-deployment', 60),
            'dn2': self.create_random_name('azure-cli-resource-group-deployment', 60),
            'Japanese-characters-tf': os.path.join(curr_dir, 'Japanese-characters-template.json').replace('\\', '\\\\')
        })

        self.cmd('deployment group validate --resource-group {rg} --template-file "{tf}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment group validate --resource-group {rg} --template-file "{Japanese-characters-tf}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment group validate --resource-group {rg} --template-file "{tf_multiline}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group validate --resource-group {rg} --template-file "{extra_param_tf}" --parameters @"{params}" --no-prompt true')
            self.assertTrue("Deployment template validation failed" in str(err.exception))

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group validate --resource-group {rg} --template-file "{extra_param_tf}" --parameters @"{params}"')
            self.assertTrue("Missing input parameters" in str(err.exception))

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group validate --resource-group {rg} --template-file "{extra_param_tf}" --parameters @"{params}" --no-prompt false')
            self.assertTrue("Missing input parameters" in str(err.exception))

        self.cmd('deployment group create --resource-group {rg} -n {dn} --template-file "{tf}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
        ])

        self.cmd('deployment group create --resource-group {rg} -n {dn} --template-file "{tf_multiline}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
        ])

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group create --resource-group {rg} -n {dn2} --template-file "{extra_param_tf}" --parameters @"{params}" --no-prompt true')
            self.assertTrue("Deployment template validation failed" in str(err.exception))

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group create --resource-group {rg} -n {dn2} --template-file "{extra_param_tf}" --parameters @"{params}"')
            self.assertTrue("Missing input parameters" in str(err.exception))

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group create --resource-group {rg} -n {dn2} --template-file "{extra_param_tf}" --parameters @"{params}" --no-prompt false')
            self.assertTrue("Missing input parameters" in str(err.exception))

        json_invalid_info = "Failed to parse '{}', please check whether it is a valid JSON format"

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group validate -g {rg} -f "{tf_invalid}" -p @"{params}"')
            self.assertTrue(json_invalid_info.format('{tf_invalid}') == err.exception)

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group validate -g {rg} -f "{tf}" -p @"{params_invalid}"')
            self.assertTrue(json_invalid_info.format('{params_invalid}') in err.exception)

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group create -g {rg} -n {dn} -f "{tf_invalid}" -p @"{params}"')
            self.assertTrue(json_invalid_info.format('{tf_invalid}') == err.exception)

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group create -g {rg} -n {dn} -f "{tf}" -p @"{params_invalid}"')
            self.assertTrue(json_invalid_info.format('{params_invalid}') in err.exception)

        self.cmd('deployment group list --resource-group {rg}', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment group list --resource-group {rg} --filter "provisioningState eq \'Succeeded\'"', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment group show --resource-group {rg} -n {dn}', checks=[
            self.check('name', '{dn}')
        ])

        self.cmd('deployment group export --resource-group {rg} -n {dn}', checks=[
        ])

        operation_output = self.cmd('deployment operation group list --resource-group {rg} -n {dn}', checks=[
            self.check('length([])', 2)
        ]).get_output_in_json()

        self.kwargs.update({
            'operation_id': operation_output[0]['operationId']
        })
        self.cmd('deployment operation group show --resource-group {rg} -n {dn} --operation-id {operation_id}', checks=[
            self.check('[0].properties.provisioningOperation', 'Create'),
            self.check('[0].properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment group create --resource-group {rg} -n {dn2} --template-file "{tf}" --parameters @"{params}" --no-wait')

        self.cmd('deployment group cancel -n {dn2} -g {rg}')

        self.cmd('deployment group wait -n {dn2} -g {rg} --custom "provisioningState==Canceled"')

        self.cmd('deployment group show -n {dn2} -g {rg}', checks=[
            self.check('properties.provisioningState', 'Canceled')
        ])


class DeploymentTestAtManagementGroup(ScenarioTest):

    def test_management_group_deployment(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'management_group_level_template.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'management_group_level_parameters.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-management-group-deployment', 60),
            'mg': self.create_random_name('azure-cli-management', 30),
            'sub-rg': self.create_random_name('azure-cli-sub-resource-group', 60),
            'dn2': self.create_random_name('azure-cli-resource-group-deployment', 60),
            'storage-account-name': self.create_random_name('armbuilddemo', 20)
        })

        self.cmd('account management-group create --name {mg}', checks=[])

        self.cmd('deployment mg validate --management-group-id {mg} --location WestUS --template-file "{tf}" '
                 '--parameters @"{params}" --parameters targetMG="{mg}" --parameters nestedRG="{sub-rg}" '
                 '--parameters storageAccountName="{storage-account-name}"',
                 checks=[self.check('properties.provisioningState', 'Succeeded'), ])

        self.cmd('deployment mg create --management-group-id {mg} --location WestUS -n {dn} --template-file "{tf}" '
                 '--parameters @"{params}" --parameters targetMG="{mg}" --parameters nestedRG="{sub-rg}" '
                 '--parameters storageAccountName="{storage-account-name}"',
                 checks=[self.check('properties.provisioningState', 'Succeeded'), ])

        self.cmd('deployment mg list --management-group-id {mg}', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment mg list --management-group-id {mg} --filter "provisioningState eq \'Succeeded\'"', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment mg show --management-group-id {mg} -n {dn}', checks=[
            self.check('name', '{dn}')
        ])

        self.cmd('deployment mg export --management-group-id {mg} -n {dn}', checks=[
        ])

        operation_output = self.cmd('deployment operation mg list --management-group-id {mg} -n {dn}', checks=[
            self.check('length([])', 4)
        ]).get_output_in_json()

        self.kwargs.update({
            'oid1': operation_output[0]['operationId'],
            'oid2': operation_output[1]['operationId'],
            'oid3': operation_output[2]['operationId']
        })
        self.cmd('deployment operation mg show --management-group-id {mg} -n {dn} --operation-ids {oid1} {oid2} {oid3}', checks=[
            self.check('[].properties.provisioningOperation', '[\'Create\', \'Create\', \'Create\']'),
            self.check('[].properties.provisioningState', '[\'Succeeded\', \'Succeeded\', \'Succeeded\']')
        ])
        self.cmd('deployment mg delete --management-group-id {mg} -n {dn}')

        self.cmd('deployment mg create --management-group-id {mg} --location WestUS -n {dn2} --template-file "{tf}" '
                 '--parameters @"{params}" --parameters targetMG="{mg}" --parameters nestedRG="{sub-rg}" '
                 '--parameters storageAccountName="{storage-account-name}" --no-wait')

        self.cmd('deployment mg cancel -n {dn2} --management-group-id {mg}')

        self.cmd('deployment mg wait -n {dn2} --management-group-id {mg} --custom "provisioningState==Canceled"')

        self.cmd('deployment mg show -n {dn2} --management-group-id {mg}', checks=[
            self.check('properties.provisioningState', 'Canceled')
        ])

        # clean
        self.cmd('account management-group delete -n {mg}')


    def test_management_group_deployment_create_mode(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'management_group_level_template.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'management_group_level_parameters.json').replace('\\', '\\\\'),
            'mg': self.create_random_name('mg', 10),
            'dn': self.create_random_name('depname', 20),
            'sub-rg': self.create_random_name('sub-group', 20),
            'storage-account-name': self.create_random_name('armbuilddemo', 20)
        })

        self.cmd('account management-group create --name {mg}')
        self.cmd('deployment mg create --management-group-id {mg} --location WestUS -n {dn} --template-file "{tf}" '
                 '--parameters @"{params}" --parameters targetMG="{mg}" --parameters nestedRG="{sub-rg}" '
                 '--parameters storageAccountName="{storage-account-name}" --mode Incremental', checks=[
            self.check('name', '{dn}'),
            self.check('properties.mode', 'Incremental')
        ])

        self.cmd('account management-group delete -n {mg}')


class DeploymentTestAtTenantScope(ScenarioTest):

    def test_tenant_level_deployment(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'tenant_level_template.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-tenant-level-deployment', 60),
            'mg': self.create_random_name('azure-cli-management-group', 40),
            'dn2': self.create_random_name('azure-cli-resource-group-deployment', 60)
        })

        self.cmd('account management-group create --name {mg}', checks=[])

        self.cmd('deployment tenant validate --location WestUS --template-file "{tf}" --parameters targetMG="{mg}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment tenant create --location WestUS -n {dn} --template-file "{tf}" --parameters targetMG="{mg}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
        ])

        self.cmd('deployment tenant list', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment tenant list --filter "provisioningState eq \'Succeeded\'"', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment tenant show -n {dn}', checks=[
            self.check('name', '{dn}')
        ])

        self.cmd('deployment tenant export -n {dn}', checks=[
        ])

        operations = self.cmd('deployment operation tenant list -n {dn}', checks=[
            self.check('length([])', 4)
        ]).get_output_in_json()

        self.kwargs.update({
            'oid1': operations[0]['operationId'],
            'oid2': operations[1]['operationId'],
            'oid3': operations[2]['operationId'],
            'oid4': operations[3]['operationId'],
        })
        self.cmd('deployment operation tenant show -n {dn} --operation-ids {oid1} {oid2} {oid3} {oid4}', checks=[
            self.check('[].properties.provisioningOperation', '[\'Create\', \'Create\', \'Create\', \'EvaluateDeploymentOutput\']'),
            self.check('[].properties.provisioningState', '[\'Succeeded\', \'Succeeded\', \'Succeeded\', \'Succeeded\']')
        ])
        self.cmd('deployment tenant delete -n {dn}')

        self.cmd('deployment tenant create --location WestUS -n {dn2} --template-file "{tf}" --parameters targetMG="{mg}" --no-wait')

        self.cmd('deployment tenant cancel -n {dn2}')

        self.cmd('deployment tenant wait -n {dn2} --custom "provisioningState==Canceled"')

        self.cmd('deployment tenant show -n {dn2}', checks=[
            self.check('properties.provisioningState', 'Canceled')
        ])

        self.cmd('group delete -n cli_tenant_level_deployment --yes')
        self.cmd('account management-group delete -n {mg}')


class DeploymentTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_lite')
    def test_group_deployment_lite(self, resource_group):
        # ensures that a template that is missing "parameters" or "resources" still deploys
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'test-template-lite.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-deployment', 30)
        })

        self.cmd('group deployment create -g {rg} -n {dn} --template-file "{tf}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_deployment')
    def test_group_deployment(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'test-template.json').replace('\\', '\\\\'),
            'tf_invalid': os.path.join(curr_dir, 'simple_deploy_invalid.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'test-params.json').replace('\\', '\\\\'),
            'error_params': os.path.join(curr_dir, 'test-error-params.json').replace('\\', '\\\\'),
            'params_invalid': os.path.join(curr_dir, 'simple_deploy_parameters_invalid.json').replace('\\', '\\\\'),
            # params-uri below is the raw file url of the test_params.json above
            'params_uri': 'https://raw.githubusercontent.com/Azure/azure-cli/dev/src/azure-cli/azure/cli/command_modules/resource/tests/latest/test-params.json',
            'of': os.path.join(curr_dir, 'test-object.json').replace('\\', '\\\\'),
            'dn': 'azure-cli-deployment',
            'dn2': self.create_random_name('azure-cli-resource-group-deployment2', 60)
        })
        self.kwargs['subnet_id'] = self.cmd('network vnet create -g {rg} -n vnet1 --subnet-name subnet1').get_output_in_json()['newVNet']['subnets'][0]['id']

        self.cmd('group deployment validate -g {rg} --template-file "{tf}" --parameters @"{params}" --parameters subnetId="{subnet_id}" --parameters backendAddressPools=@"{of}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('group deployment validate -g {rg} --template-file "{tf}" --parameters "{params_uri}" --parameters subnetId="{subnet_id}" --parameters backendAddressPools=@"{of}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        with self.assertRaises(CLIError):
            self.cmd('group deployment validate -g {rg} --template-file "{tf}" --parameters @"{error_params}" --parameters subnetId="{subnet_id}" --parameters backendAddressPools=@"{of}"')

        self.cmd('group deployment create -g {rg} -n {dn} --template-file "{tf}" --parameters @"{params}" --parameters subnetId="{subnet_id}" --parameters backendAddressPools=@"{of}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}')
        ])
        self.cmd('network lb show -g {rg} -n test-lb',
                 checks=self.check('tags', {'key': 'super=value'}))

        self.cmd('group deployment list -g {rg}', checks=[
            self.check('[0].name', '{dn}'),
            self.check('[0].resourceGroup', '{rg}')
        ])
        self.cmd('group deployment list -g {rg} --filter "provisioningState eq \'Succeeded\'"', checks=[
            self.check('[0].name', '{dn}'),
            self.check('[0].resourceGroup', '{rg}')
        ])
        self.cmd('group deployment show -g {rg} -n {dn}', checks=[
            self.check('name', '{dn}'),
            self.check('resourceGroup', '{rg}')
        ])
        self.cmd('group deployment operation list -g {rg} -n {dn}', checks=[
            self.check('length([])', 2),
            self.check('[0].resourceGroup', '{rg}')
        ])

        json_invalid_info = "Failed to parse '{}', please check whether it is a valid JSON format"

        with self.assertRaises(CLIError) as err:
            self.cmd('group deployment validate -g {rg} -f "{tf_invalid}" -p @"{params}"')
            self.assertTrue(json_invalid_info.format('{tf_invalid}') == err.exception)

        with self.assertRaises(CLIError) as err:
            self.cmd('group deployment validate -g {rg} -f "{tf}" -p @"{params_invalid}"')
            self.assertTrue(json_invalid_info.format('{params_invalid}') in err.exception)

        with self.assertRaises(CLIError) as err:
            self.cmd('group deployment create -g {rg} -n {dn} -f "{tf_invalid}" -p @"{params}"')
            self.assertTrue(json_invalid_info.format('{tf_invalid}') == err.exception)

        with self.assertRaises(CLIError) as err:
            self.cmd('group deployment create -g {rg} -n {dn} -f "{tf}" -p @"{params_invalid}"')
            self.assertTrue(json_invalid_info.format('{params_invalid}') in err.exception)

        self.cmd('group deployment create -g {rg} -n {dn2} --template-file "{tf}" --parameters @"{params}" --parameters subnetId="{subnet_id}" --parameters backendAddressPools=@"{of}" --no-wait')

        self.cmd('group deployment cancel -n {dn2} -g {rg}')

        self.cmd('group deployment show -n {dn2} -g {rg}', checks=[
            self.check('properties.provisioningState', 'Canceled')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_with_large_params')
    @AllowLargeResponse()
    def test_group_deployment_with_large_params(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'large_tf': os.path.join(curr_dir, 'test-largesize-template.json').replace('\\', '\\\\'),
            'large_params': os.path.join(curr_dir, 'test-largesize-parameters.json').replace('\\', '\\\\'),
            'app_name': self.create_random_name('cli', 30)
        })

        self.cmd('group deployment validate -g {rg} --template-file "{large_tf}" --parameters @"{large_params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('group deployment validate -g {rg} --template-file "{large_tf}" --parameters "{large_params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('group deployment create -g {rg} --template-file "{large_tf}" --parameters @"{large_params}" --parameters function-app-name="{app_name}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('group deployment create -g {rg} --template-file "{large_tf}" --parameters "{large_params}" --parameters function-app-name="{app_name}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_on_error_deployment_lastsuccessful')
    def test_group_on_error_deployment_lastsuccessful(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'test-template-lite.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-deployment', 30),
            'onErrorType': 'LastSuccessful',
            'sdn': self.create_random_name('azure-cli-deployment', 30)
        })

        self.cmd('group deployment create -g {rg} -n {dn} --template-file "{tf}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}'),
            self.check('properties.onErrorDeployment', None)
        ])

        self.cmd('group deployment create -g {rg} -n {sdn} --template-file "{tf}" --rollback-on-error', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}'),
            self.check('properties.onErrorDeployment.deploymentName', '{dn}'),
            self.check('properties.onErrorDeployment.type', '{onErrorType}')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_on_error_deployment_specificdeployment')
    def test_group_on_error_deployment_specificdeployment(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'test-template-lite.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-deployment', 30),
            'onErrorType': 'SpecificDeployment',
            'sdn': self.create_random_name('azure-cli-deployment', 30)
        })

        self.cmd('group deployment create -g {rg} -n {dn} --template-file "{tf}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}'),
            self.check('properties.onErrorDeployment', None)
        ])

        self.cmd('group deployment create -g {rg} -n {sdn} --template-file "{tf}" --rollback-on-error {dn}', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}'),
            self.check('properties.onErrorDeployment.deploymentName', '{dn}'),
            self.check('properties.onErrorDeployment.type', '{onErrorType}')
        ])


class DeploymentLiveTest(LiveScenarioTest):
    @ResourceGroupPreparer()
    def test_group_deployment_progress(self, resource_group):
        from azure.cli.testsdk.utilities import force_progress_logging
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'test-template.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'test-params.json').replace('\\', '\\\\'),
            'of': os.path.join(curr_dir, 'test-object.json').replace('\\', '\\\\'),
            'dn': 'azure-cli-deployment2'
        })

        self.kwargs['subnet_id'] = self.cmd('network vnet create -g {rg} -n vnet1 --subnet-name subnet1').get_output_in_json()['newVNet']['subnets'][0]['id']

        with force_progress_logging() as test_io:
            self.cmd('group deployment create --verbose -g {rg} -n {dn} --template-file "{tf}" --parameters @"{params}" --parameters subnetId="{subnet_id}" --parameters backendAddressPools=@"{of}"')

        # very the progress
        lines = test_io.getvalue().splitlines()
        for line in lines:
            self.assertTrue(line.split(':')[0] in ['Accepted', 'Succeeded'])
        self.assertTrue('Succeeded: {} (Microsoft.Resources/deployments)'.format(self.kwargs['dn']), lines)


class DeploymentNoWaitTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_group_deployment_no_wait')
    def test_group_deployment_no_wait(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'simple_deploy.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'simple_deploy_parameters.json').replace('\\', '\\\\'),
            'dn': 'azure-cli-deployment'
        })

        self.cmd('group deployment create -g {rg} -n {dn} --template-file "{tf}" --parameters @"{params}" --no-wait',
                 checks=self.is_empty())

        self.cmd('group deployment wait -g {rg} -n {dn} --created',
                 checks=self.is_empty())

        self.cmd('group deployment show -g {rg} -n {dn}',
                 checks=self.check('properties.provisioningState', 'Succeeded'))


class DeploymentThruUriTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_uri')
    def test_group_deployment_thru_uri(self, resource_group):
        self.resource_group = resource_group
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        # same copy of the sample template file under current folder, but it is uri based now
        self.kwargs.update({
            'tf': 'https://raw.githubusercontent.com/Azure/azure-cli/dev/src/azure-cli/azure/cli/command_modules/resource/tests/latest/simple_deploy.json',
            'params': os.path.join(curr_dir, 'simple_deploy_parameters.json').replace('\\', '\\\\')
        })
        self.kwargs['dn'] = self.cmd('group deployment create -g {rg} --template-uri "{tf}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}'),
            self.check('properties.templateLink.uri', '{tf}'),
        ]).get_output_in_json()['name']

        self.cmd('group deployment show -g {rg} -n {dn}',
                 checks=self.check('name', '{dn}'))

        self.cmd('group deployment delete -g {rg} -n {dn}')
        self.cmd('group deployment list -g {rg}',
                 checks=self.is_empty())

        self.kwargs['dn'] = self.cmd('deployment group create -g {rg} --template-uri "{tf}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}'),
            self.check('properties.templateLink.uri', '{tf}'),
        ]).get_output_in_json()['name']

        self.cmd('deployment group show -g {rg} -n {dn}',
                 checks=self.check('name', '{dn}'))

        self.cmd('deployment group delete -g {rg} -n {dn}')
        self.cmd('deployment group list -g {rg}',
                 checks=self.is_empty())


class DeploymentWhatIfAtResourceGroupScopeTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_deployment_what_if')
    def test_resource_group_level_what_if(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'storage_account_deploy.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'storage_account_deploy_parameters.json').replace('\\', '\\\\'),
        })

        deployment_output = self.cmd('deployment group create --resource-group {rg} --template-file "{tf}"').get_output_in_json()
        self.kwargs['storage_account_id'] = deployment_output['properties']['outputs']['storageAccountId']['value']

        self.cmd('deployment group what-if --resource-group {rg} --template-file "{tf}" --parameters "{params}" --no-pretty-print', checks=[
            self.check('status', 'Succeeded'),
            self.check("changes[?resourceId == '{storage_account_id}'].changeType | [0]", 'Modify'),
            self.check("changes[?resourceId == '{storage_account_id}'] | [0].delta[?path == 'sku.name'] | [0].propertyChangeType", 'Modify'),
            self.check("changes[?resourceId == '{storage_account_id}'] | [0].delta[?path == 'sku.name'] | [0].before", 'Standard_LRS'),
            self.check("changes[?resourceId == '{storage_account_id}'] | [0].delta[?path == 'sku.name'] | [0].after", 'Standard_GRS')
        ])


class DeploymentWhatIfAtSubscriptionScopeTest(ScenarioTest):
    def test_subscription_level_what_if(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'policy_definition_deploy.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'policy_definition_deploy_parameters.json').replace('\\', '\\\\'),
        })

        deployment_output = self.cmd('deployment sub create --location westus --template-file "{tf}"').get_output_in_json()
        self.kwargs['policy_definition_id'] = deployment_output['properties']['outputs']['policyDefinitionId']['value']

        # Make sure the formatter works without exception
        self.cmd('deployment sub what-if --location westus --template-file "{tf}" --parameters "{params}"')

        self.cmd('deployment sub what-if --location westus --template-file "{tf}" --parameters "{params}" --no-pretty-print', checks=[
            self.check('status', 'Succeeded'),
            self.check("changes[?resourceId == '{policy_definition_id}'].changeType | [0]", 'Modify'),
            self.check("changes[?resourceId == '{policy_definition_id}'] | [0].delta[?path == 'properties.policyRule.if.equals'] | [0].propertyChangeType", 'Modify'),
            self.check("changes[?resourceId == '{policy_definition_id}'] | [0].delta[?path == 'properties.policyRule.if.equals'] | [0].before", 'northeurope'),
            self.check("changes[?resourceId == '{policy_definition_id}'] | [0].delta[?path == 'properties.policyRule.if.equals'] | [0].after", 'westeurope'),
        ])


class DeploymentWhatIfAtManagementGroupTest(ScenarioTest):
    def test_management_group_level_what_if(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'management_group_level_template.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'management_group_level_parameters.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-management-group-deployment', 60),
            'mg': self.create_random_name('azure-cli-management', 30),
            'sub-rg': self.create_random_name('azure-cli-sub-resource-group', 60),
            'storage-account-name': self.create_random_name('armbuilddemo', 20)
        })

        self.cmd('account management-group create --name {mg}', checks=[])

        self.cmd('deployment mg what-if --management-group-id {mg} --location WestUS --template-file "{tf}" --no-pretty-print '
                 '--parameters @"{params}" --parameters targetMG="{mg}" --parameters nestedRG="{sub-rg}" '
                 '--parameters storageAccountName="{storage-account-name}"',
                 checks=[
                     self.check('status', 'Succeeded'),
                     self.check("length(changes)", 4),
                     self.check("changes[0].changeType", "Create"),
                     self.check("changes[1].changeType", "Create"),
                     self.check("changes[2].changeType", "Create"),
                     self.check("changes[3].changeType", "Create"),
                 ])


class DeploymentWhatIfAtTenantScopeTest(ScenarioTest):
    def test_tenant_level_what_if(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'tenant_level_template.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-tenant-level-deployment', 60),
            'mg': self.create_random_name('azure-cli-management-group', 40),
        })

        self.cmd('account management-group create --name {mg}', checks=[])

        self.cmd('deployment tenant what-if --location WestUS --template-file "{tf}" --parameters targetMG="{mg}" --no-pretty-print', checks=[
            self.check('status', 'Succeeded'),
            self.check("length(changes)", 3),
            self.check("changes[0].changeType", "Modify"),
            self.check("changes[1].changeType", "Create"),
            self.check("changes[2].changeType", "Create"),
        ])


class DeploymentWhatIfTestWithTemplateSpecs(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_deployment_what_if_template_specs', location='westus')
    def test_resource_group_level_what_if_ts(self, resource_group, resource_group_location):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_spec_name = self.create_random_name('cli-test-deploy-what-if-rg-deploy', 60)
        self.kwargs.update({
            'template_spec_name': template_spec_name,
            'resource_group_location': resource_group_location,
            'tf': os.path.join(curr_dir, 'storage_account_deploy.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'storage_account_deploy_parameters.json').replace('\\', '\\\\'),
        })

        result = self.cmd('ts create -g {rg} -n {template_spec_name} -v 1.0 -l {resource_group_location} -f "{tf}"').get_output_in_json()
        self.kwargs['template_spec_version_id'] = result['id']

        deployment_output = self.cmd('deployment group create --resource-group {rg} --template-spec "{template_spec_version_id}"').get_output_in_json()
        self.kwargs['storage_account_id'] = deployment_output['properties']['outputs']['storageAccountId']['value']

        self.cmd('deployment group what-if --resource-group {rg} --template-spec "{template_spec_version_id}" --parameters "{params}" --no-pretty-print', checks=[
            self.check('status', 'Succeeded'),
            self.check("changes[?resourceId == '{storage_account_id}'].changeType | [0]", 'Modify'),
            self.check("changes[?resourceId == '{storage_account_id}'] | [0].delta[?path == 'sku.name'] | [0].propertyChangeType", 'Modify'),
            self.check("changes[?resourceId == '{storage_account_id}'] | [0].delta[?path == 'sku.name'] | [0].before", 'Standard_LRS'),
            self.check("changes[?resourceId == '{storage_account_id}'] | [0].delta[?path == 'sku.name'] | [0].after", 'Standard_GRS')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_what_if_template_specs', location='westus')
    def test_subscription_level_what_if_ts(self, resource_group, resource_group_location):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_spec_name = self.create_random_name('cli-test-deploy-what-if-sub-deploy', 60)
        self.kwargs.update({
            'template_spec_name': template_spec_name,
            'resource_group_location': resource_group_location,
            'tf': os.path.join(curr_dir, 'policy_definition_deploy.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'policy_definition_deploy_parameters.json').replace('\\', '\\\\'),
        })

        result = self.cmd('ts create -g {rg} -n {template_spec_name} -v 1.0 -l {resource_group_location} -f "{tf}"').get_output_in_json()
        self.kwargs['template_spec_version_id'] = result['id']

        deployment_output = self.cmd('deployment sub create --location westus --template-spec {template_spec_version_id}').get_output_in_json()
        self.kwargs['policy_definition_id'] = deployment_output['properties']['outputs']['policyDefinitionId']['value']

        self.cmd('deployment sub what-if --location westus --template-spec {template_spec_version_id} --parameters "{params}" --no-pretty-print', checks=[
            self.check('status', 'Succeeded'),
            self.check("changes[?resourceId == '{policy_definition_id}'].changeType | [0]", 'Modify'),
            self.check("changes[?resourceId == '{policy_definition_id}'] | [0].delta[?path == 'properties.policyRule.if.equals'] | [0].propertyChangeType", 'Modify'),
            self.check("changes[?resourceId == '{policy_definition_id}'] | [0].delta[?path == 'properties.policyRule.if.equals'] | [0].before", 'northeurope'),
            self.check("changes[?resourceId == '{policy_definition_id}'] | [0].delta[?path == 'properties.policyRule.if.equals'] | [0].after", 'westeurope'),
        ])


class DeploymentScriptsTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_deployment_scripts', location='brazilsouth')
    def test_list_all_deployment_scripts(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'deployment_script_name': self.create_random_name('script', 20),
            'deployment_name': self.create_random_name('ds', 20),
            'resource_group': resource_group,
            'template_file': os.path.join(curr_dir, 'deployment-scripts-deploy.json').replace('\\', '\\\\'),
        })

        count = 0
        self.cmd('deployment-scripts list',
                 checks=self.check("length([?name=='{deployment_script_name}'])", count))

        self.cmd('deployment group create -g {resource_group} -n {deployment_name} --template-file "{template_file}" --parameters scriptName={deployment_script_name}', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{resource_group}'),
        ])

        count += 1

        self.cmd('deployment-scripts list',
                 checks=self.check("length([?name=='{deployment_script_name}'])", count))

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_scripts', location='brazilsouth')
    def test_show_deployment_script(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'deployment_script_name': self.create_random_name('script', 20),
            'deployment_name': self.create_random_name('ds', 20),
            'resource_group': resource_group,
            'template_file': os.path.join(curr_dir, 'deployment-scripts-deploy.json').replace('\\', '\\\\'),
        })

        self.cmd('deployment group create -g {resource_group} -n {deployment_name} --template-file "{template_file}" --parameters scriptName={deployment_script_name}', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{resource_group}'),
        ])

        self.cmd("deployment-scripts show --resource-group {resource_group} --name {deployment_script_name}",
                 checks=self.check('name', '{deployment_script_name}'))

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_scripts', location='brazilsouth')
    def test_show_deployment_script_logs(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'deployment_script_name': self.create_random_name('script', 20),
            'deployment_name': self.create_random_name('ds', 20),
            'resource_group': resource_group,
            'template_file': os.path.join(curr_dir, 'deployment-scripts-deploy.json').replace('\\', '\\\\'),
        })

        self.cmd('deployment group create -g {resource_group} -n {deployment_name} --template-file "{template_file}" --parameters scriptName={deployment_script_name}', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{resource_group}'),
        ])

        deployment_script_logs = self.cmd("deployment-scripts show-log --resource-group {resource_group} --name {deployment_script_name}").get_output_in_json()

        self.assertTrue(deployment_script_logs['value'] is not None)

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_scripts', location='brazilsouth')
    def test_delete_deployment_script(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'deployment_script_name': self.create_random_name('script', 20),
            'deployment_name': self.create_random_name('ds', 20),
            'resource_group': resource_group,
            'template_file': os.path.join(curr_dir, 'deployment-scripts-deploy.json').replace('\\', '\\\\'),
        })

        self.cmd('deployment group create -g {resource_group} -n {deployment_name} --template-file "{template_file}" --parameters scriptName={deployment_script_name}', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{resource_group}'),
        ])

        # making sure it exists first
        self.cmd("deployment-scripts show --resource-group {resource_group} --name {deployment_script_name}",
                 checks=self.check('name', '{deployment_script_name}'))

        self.cmd("deployment-scripts delete --resource-group {resource_group} --name {deployment_script_name} --yes")

        self.cmd('deployment-scripts list',
                 checks=self.check("length([?name=='{deployment_script_name}'])", 0))

class DeploymentStacksTest(ScenarioTest):
    global location
    location = "westus2"
    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_deployment_stacks', location=location)
    def test_create_deployment_stack_subscription(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_stack_name = self.create_random_name('cli-test-create-deployment-stack-subscription', 60)
        template_spec_name = self.create_random_name('cli-test-template-spec', 60)
        resource_one = self.create_random_name('cli-test-resource-one', 60)
        resource_two = self.create_random_name('cli-test-resource-two', 60)
        resource_three = self.create_random_name('cli-test-resource-three', 60)
        resource_group_two = self.create_random_name('cli-test-cli_test_deployment_stacks-two', 60)

        self.kwargs.update({
            'name': deployment_stack_name,
            'location': location,
            'template-file': os.path.join(curr_dir, 'simple_template.json').replace('\\', '\\\\'),
            'template-file-spec': os.path.join(curr_dir, 'simple_template_spec.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),
            'template-file-rg': os.path.join(curr_dir, 'simple_template_resource_group.json').replace('\\', '\\\\'),
            'track-rg-file': os.path.join(curr_dir, 'tracked_resource_group.json').replace('\\', '\\\\'),
            'template-spec-name': template_spec_name,
            'template-spec-version': "v1",
            'resource-group': resource_group,
            'resource-group-two': resource_group_two,
            'resource-one': resource_one,
            'resource-two': resource_two,
            'resource-three': resource_three,
            'resource-type-specs': "Microsoft.Resources/templateSpecs"
        })
        # create template spec
        basic_template_spec = self.cmd('ts create --name {template-spec-name} --version {template-spec-version} --location "westus2" --template-file {template-file} --resource-group {resource-group}').get_output_in_json()
        template_spec_id = basic_template_spec['id']

        self.kwargs.update({'template-spec-id': template_spec_id})

        # create deployment stack with template file and parameter file
        self.cmd('stack sub create --name {name} --location {location} --template-file "{template-file}" --deny-settings-mode "none" --parameters "{parameter-file}" --description "stack deployment" --delete-all --deny-settings-excluded-principals "principal1 principal2" --deny-settings-excluded-actions "action1 action2" --deny-settings-apply-to-child-scopes --yes', checks=self.check('provisioningState', 'succeeded'))

        # cleanup
        self.cmd('stack sub delete --name {name} --yes')

        #create deployment stack with template spec and parameter file
        self.cmd('stack sub create --name {name} --location {location} --template-spec "{template-spec-id}" --deny-settings-mode "none" --parameters "{parameter-file}" --no-wait', checks=self.is_empty())

        time.sleep(20)

        # check if the stack was created successfully
        self.cmd('stack sub show --name {name}', checks=self.check('provisioningState', 'succeeded'))

        # cleanup
        self.cmd('stack sub delete --name {name} --yes')

        # deploy to rg
        self.cmd('stack sub create --name {name} --location {location} --template-file "{template-file}" --deployment-resource-group {resource-group} --deny-settings-mode "none" --parameters "{parameter-file}" --yes', checks=self.check('provisioningState', 'succeeded'))

        # cleanup
        self.cmd('stack sub delete --name {name} --yes')

        # create new resource group - test delete flag --delete-resources
        self.cmd('group create --location {location} --name {resource-group-two}')

        # create stack  with resource1
        self.cmd('stack sub create --name {name} --location {location} --deployment-resource-group {resource-group-two} --deny-settings-mode "none" --template-file "{template-file-spec}" --parameters "name={resource-one}" --yes', checks=self.check('provisioningState', 'succeeded'))

        # update stack with resource2 set to detach
        self.cmd('stack sub create --name {name} --location {location} --deployment-resource-group {resource-group-two} --deny-settings-mode "none" --template-file "{template-file-spec}" --parameters "name={resource-two}" --yes', checks=self.check('provisioningState', 'succeeded'))

        # check resource1 still exists in Azure
        self.cmd('resource show -n {resource-one} -g {resource-group-two} --resource-type {resource-type-specs}')

        # check resource2 exists in Azure
        self.cmd('resource show -n {resource-two} -g {resource-group-two} --resource-type {resource-type-specs}')

        # update stack with resource3 set to delete
        self.cmd('stack sub create --name {name} --location {location} --deployment-resource-group {resource-group-two} --template-file "{template-file-spec}" --deny-settings-mode "none" --parameters "name={resource-three}" --delete-resources --yes', checks=self.check('provisioningState', 'succeeded'))

        # check resource1 still exists in Azure
        self.cmd('resource show -n {resource-one} -g {resource-group-two} --resource-type {resource-type-specs}')

        # check resource3 exists in Azure
        self.cmd('resource show -n {resource-three} -g {resource-group-two} --resource-type {resource-type-specs}')

        # check resource2 does not exist in Azure - should have been purged
        self.cmd('resource list -g {resource-group-two}', checks=self.check("length([?name=='{resource-two}'])", 0))

        # delete resource group two
        self.cmd('group delete --name {resource-group-two} --yes')

        # cleanup
        self.cmd('stack sub delete --name {name} --yes')

        # test delete flag --delete-resource-groups - create stack  with resource1
        self.cmd('stack sub create --name {name} --location {location} --template-file "{template-file-rg}" --parameters "name={resource-one}" --deny-settings-mode "none" --yes', checks=self.check('provisioningState', 'succeeded'))

        # update stack with resource2 set to detach
        self.cmd('stack sub create --name {name} --location {location} --template-file "{template-file-rg}" --parameters "name={resource-two}" --deny-settings-mode "none" --yes', checks=self.check('provisioningState', 'succeeded'))

        # check resource1 still exists in Azure
        self.cmd('group show -n {resource-one}')

        # check resource2 exists in Azure
        self.cmd('group show -n {resource-two}')

        # update stack with resource3 set to delete
        self.cmd('stack sub create --name {name} --location {location} --template-file "{template-file-rg}" --parameters "name={resource-three}" --deny-settings-mode "none" --delete-resources --delete-resources --yes', checks=self.check('provisioningState', 'succeeded'))

        # check resource1 still exists in Azure
        self.cmd('group show -n {resource-one}')

        # check resource3 exists in Azure
        self.cmd('group show -n {resource-three}')

        # check resource2 does not exist in Azure - should have been purged
        self.cmd('resource list', checks=self.check("length([?name=='{resource-two}'])", 0))

        # cleanup
        self.cmd('stack sub delete --name {name} --yes')

        #new code
        # create new resource group - testing delete-all flag
        self.cmd('group create --location {location} --name {resource-group-two}')

        # create stack
        self.cmd('stack sub create --name {name} --location {location} --deployment-resource-group {resource-group-two} --template-file "{track-rg-file}" --deny-settings-mode "none" --parameters "rgname={resource-one}" "tsname={template-spec-name}" --yes', checks=self.check('provisioningState', 'succeeded'))

        # check template spec exists in Azure
        self.cmd('resource show -n {template-spec-name} -g {resource-group-two} --resource-type {resource-type-specs}')

        # check rg resource1 exists in Azure
        self.cmd('group show -n {resource-one}')

        # create stack with delete-all set
        self.cmd('stack sub create --name {name} --location {location} --deployment-resource-group {resource-group-two} --template-file "{template-file}" --deny-settings-mode "none" --delete-all --yes', checks=self.check('provisioningState', 'succeeded'))

        # confirm template spec has been removed from azure
        self.cmd('resource list -g {resource-group-two}',  checks=self.check("length([?name=='{template-spec-name}'])", 0))

        #confirm rg resource1 has been removed from azure
        self.cmd('group list', checks=self.check("length([?name=='{resource-one}'])", 0))

        # cleanup - delete resource group two
        self.cmd('group delete --name {resource-group-two} --yes')

    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_deployment_stacks', location=location)
    def test_create_deployment_stack_subscription_with_bicep(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_stack_name = self.create_random_name('cli-test-create-deployment-stack-subscription', 60)

        self.kwargs.update({
            'name': deployment_stack_name,
            'location': location,
            'template-file': os.path.join(curr_dir, 'simple_template.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),
            'bicep-file': os.path.join(curr_dir, 'data', 'bicep_simple_template.bicep').replace('\\', '\\\\'),
            'bicep-param-file':os.path.join(curr_dir, 'data', 'bicepparam', 'storage_account_params.bicepparam').replace('\\', '\\\\'),
            'resource-group': resource_group,
        })

        # create deployment stack with bicep file and rg scope
        self.cmd('stack sub create --name {name} --location {location} --template-file "{bicep-file}" --deny-settings-mode "none" --deployment-resource-group {resource-group} --yes', checks=self.check('provisioningState', 'succeeded'))

        # cleanup
        self.cmd('stack sub delete --name {name} --yes')

        # test bicep param file
        self.cmd('stack sub create --name {name} --location {location} --deployment-resource-group {resource-group} -p "{bicep-param-file}" --deny-settings-mode "none" --delete-all --yes', checks=self.check('provisioningState', 'succeeded'))

        self.cmd('stack sub delete --name {name} --yes')

    def test_show_deployment_stack_subscription(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_stack_name = self.create_random_name('cli-test-get-deployment-stack-subscription', 60)
        self.kwargs.update({
            'name': deployment_stack_name,
            'location': location,
            'template-file': os.path.join(curr_dir, 'simple_template.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),

        })

        created_deployment_stack = self.cmd('stack sub create --name {name} --location {location} --template-file "{template-file}" --deny-settings-mode "none" --parameters "{parameter-file}" --yes', checks=self.check('provisioningState', 'succeeded')).get_output_in_json()
        deployment_stack_id = created_deployment_stack['id']

        self.kwargs.update({'deployment-stack-id': deployment_stack_id})

        # show stack with stack name
        self.cmd('stack sub show --name {name}', checks=self.check('name', '{name}'))

        # show stack with stack id
        self.cmd('stack sub show --id {deployment-stack-id}', checks=self.check('name', '{name}'))

        # cleanup
        self.cmd('stack sub delete --name {name} --yes')

    @AllowLargeResponse(4096)
    def test_list_deployment_stack_subscription(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_stack_name = self.create_random_name('cli-test-list-deployment-stack-subscription', 60)

        self.kwargs.update({
            'name': deployment_stack_name,
            'location': location,
            'template-file': os.path.join(curr_dir, 'simple_template.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),

        })

        self.cmd('stack sub create --name {name} --location {location} --template-file "{template-file}" --parameters "{parameter-file}" --deny-settings-mode "none" --yes', checks=self.check('provisioningState', 'succeeded')).get_output_in_json()

        # list stacks
        list_deployment_stacks = self.cmd('stack sub list').get_output_in_json()

        self.assertTrue(len(list_deployment_stacks) > 0)
        self.assertTrue(list_deployment_stacks[0]['name'], '{name}')

         # cleanup
        self.cmd('stack sub delete --name {name} --yes')

    @AllowLargeResponse(4096)
    def test_delete_deployment_stack_subscription(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_stack_name = self.create_random_name('cli-test-delete-deployment-stack-subscription', 60)
        resource_one = self.create_random_name('cli-test-resource-one', 60)
        resource_two = self.create_random_name('cli-test-resource-two', 60)
        resource_three = self.create_random_name('cli-test-resource-three', 60)
        template_spec_name = self.create_random_name('cli-test-template-spec', 60)
        resource_group_two = self.create_random_name('cli-test-cli_test_deployment_stacks-two', 60)

        self.kwargs.update({
            'name': deployment_stack_name,
            'location': location,
            'template-file': os.path.join(curr_dir, 'simple_template.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),
            'template-file-spec': os.path.join(curr_dir, 'simple_template_spec.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),
            'bicep-file': os.path.join(curr_dir, 'data', 'bicep_simple_template.bicep').replace('\\', '\\\\'),
            'template-file-rg': os.path.join(curr_dir, 'simple_template_resource_group.json').replace('\\', '\\\\'),
            'track-rg-file': os.path.join(curr_dir, 'tracked_resource_group.json').replace('\\', '\\\\'),
            'template-spec-name': template_spec_name,
            'template-spec-version': "v1",
            'resource-one': resource_one,
            'resource-two': resource_two,
            'resource-three': resource_three,
            'resource-group-two': resource_group_two,
            'resource-type-specs': "Microsoft.Resources/templateSpecs"
        })

        # create stack
        self.cmd('stack sub create --name {name} --location {location} --template-file "{template-file}" --parameters "{parameter-file}" --deny-settings-mode "none" --yes', checks=self.check('provisioningState', 'succeeded')).get_output_in_json()

        # check stack to make sure it exists
        self.cmd('stack sub show --name {name}', checks=self.check('name', '{name}'))

        # delete stack with stack name
        self.cmd('stack sub delete --name {name} --yes')

        #confirm stack is deleted
        #self.cmd('stack sub list', checks=self.check("length([?name=='{name}'])", 0))

        #add delete with stack id
        created_stack = self.cmd('stack sub create --name {name} --location {location} --template-file "{template-file}" --parameters "{parameter-file}" --deny-settings-mode "none" --yes', checks=self.check('provisioningState', 'succeeded')).get_output_in_json()
        stack_id = created_stack['id']

        self.kwargs.update({'id': stack_id})

        # delete stack with id
        self.cmd('stack sub delete --id  {id} --yes')

        #confirm stack is deleted
        #self.cmd('stack sub list', checks=self.check("length([?name=='{name}'])", 0))

        # create new resource group - delete flag --delete-resources
        self.cmd('group create --location {location} --name {resource-group-two}')

        # create stack with resource1 to check if resources are being detached on delete
        self.cmd('stack sub create --name {name} --location {location} --deployment-resource-group {resource-group-two} --template-file "{template-file-spec}" --deny-settings-mode "none" --parameters "name={resource-one}" --yes', checks=self.check('provisioningState', 'succeeded'))

        # delete stack set to (default) detach
        self.cmd('stack sub delete --name {name} --yes')

        # check resource1 still exists in Azure
        self.cmd('resource show -n {resource-one} -g {resource-group-two} --resource-type {resource-type-specs}')

        # create stack with resource2 to check if resources are being purged on delete
        self.cmd('stack sub create --name {name} --location {location} --deployment-resource-group {resource-group-two} --template-file "{template-file-spec}" --deny-settings-mode "none" --parameters "name={resource-two}" --yes', checks=self.check('provisioningState', 'succeeded'))

        # delete stack with resource2 set to delete
        self.cmd('stack sub delete --name {name} --delete-resources --yes')

        #confirm resource2 has been removed from Azure
        self.cmd('resource list', checks=self.check("length([?name=='{resource-two}'])", 0))

        # cleanup - delete resource group two
        self.cmd('group delete --name {resource-group-two} --yes')

        # test delete flag --delete-resource-groups - create stack  with resource1
        self.cmd('stack sub create --name {name} --location {location} --template-file "{template-file-rg}" --parameters "name={resource-one}" --deny-settings-mode "none" --yes', checks=self.check('provisioningState', 'succeeded'))

        # delete stack with resource1 set to detach
        self.cmd('stack sub delete --name {name} --yes')

        # check resource1 still exists in Azure
        self.cmd('group show -n {resource-one}')

        # update stack with resource3 set to delete
        self.cmd('stack sub create --name {name} --location {location} --template-file "{template-file-rg}" --parameters "name={resource-two}" --deny-settings-mode "none" --delete-resources --delete-resource-groups --yes', checks=self.check('provisioningState', 'succeeded'))

        # delete stack with resource1 set to detach
        self.cmd('stack sub delete --name {name} --delete-resources --delete-resource-groups --yes')

        # check resource1 still exists in Azure
        self.cmd('group show -n {resource-one}')

        #confirm resource2 has been removed from Azure
        self.cmd('group list', checks=self.check("length([?name=='{resource-two}'])", 0))

        # cleanup
        self.cmd('group delete --name {resource-one} --yes')

        #new code
        # create new resource group - testing delete-all flag
        self.cmd('group create --location {location} --name {resource-group-two}')

        # create stack
        self.cmd('stack sub create --name {name} --location {location} --deployment-resource-group {resource-group-two} --template-file "{track-rg-file}" --deny-settings-mode "none" --parameters "rgname={resource-one}" "tsname={template-spec-name}" --yes', checks=self.check('provisioningState', 'succeeded'))

        # check template spec exists in Azure
        self.cmd('resource show -n {template-spec-name} -g {resource-group-two} --resource-type {resource-type-specs}')

        # check rg resource1 exists in Azure
        self.cmd('group show -n {resource-one}')

        # create stack with delete-all set
        self.cmd('stack sub delete --name {name} --delete-all --yes')

        # confirm template spec has been removed from azure
        self.cmd('resource list -g {resource-group-two}',  checks=self.check("length([?name=='{template-spec-name}'])", 0))

        #confirm rg resource1 has been removed from azure
        self.cmd('group list', checks=self.check("length([?name=='{resource-one}'])", 0))

        # cleanup - delete resource group two
        self.cmd('group delete --name {resource-group-two} --yes')

    def test_export_template_deployment_stack_subscription(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_stack_name = self.create_random_name('cli-test-get-deployment-stack-subscription', 60)
        self.kwargs.update({
            'name': deployment_stack_name,
            'location': location,
            'template-file': os.path.join(curr_dir, 'simple_template.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),

        })

        created_deployment_stack = self.cmd('stack sub create --name {name} --location {location} --template-file "{template-file}" --deny-settings-mode "none" --parameters "{parameter-file}" --yes', checks=self.check('provisioningState', 'succeeded')).get_output_in_json()
        deployment_stack_id = created_deployment_stack['id']

        self.kwargs.update({'deployment-stack-id': deployment_stack_id})

        # show stack with stack name
        self.cmd('stack sub export --name {name}')

        # show stack with stack id
        self.cmd('stack sub export --id {deployment-stack-id}')

        # show stack with stack name
        self.cmd('stack sub show --name {name}', checks=self.check('name', '{name}'))

        # cleanup
        self.cmd('stack sub delete --name {name} --yes')

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_stacks', location=location)
    def test_create_deployment_stack_resource_group(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_stack_name = self.create_random_name('cli-test-create-deployment-stack-resource-group', 60)
        template_spec_name = self.create_random_name('cli-test-template-spec', 60)
        resource_one = self.create_random_name('cli-test-resource-one', 60)
        resource_two = self.create_random_name('cli-test-resource-two', 60)
        resource_three = self.create_random_name('cli-test-resource-three', 60)
        resource_group_two = self.create_random_name('cli-test-cli_test_deployment_stacks-two', 60)

        self.kwargs.update({
            'name': deployment_stack_name,
            'resource-group': resource_group,
            'location': location,
            'template-file': os.path.join(curr_dir, 'simple_template.json').replace('\\', '\\\\'),
            'template-file-spec': os.path.join(curr_dir, 'simple_template_spec.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),
            'track-rg-file': os.path.join(curr_dir, 'tracked_resource_group.json').replace('\\', '\\\\'),
            'template-spec-name': template_spec_name,
            'template-spec-version': "v1",
            'template-file-rg': os.path.join(curr_dir, 'simple_template_resource_group.json').replace('\\', '\\\\'),
            'track-rg-file-only': os.path.join(curr_dir, 'tracked_resource_group_only.json').replace('\\', '\\\\'),
            'resource-group': resource_group,
            'resource-group-two': resource_group_two,
            'resource-one': resource_one,
            'resource-two': resource_two,
            'resource-three': resource_three,
            'resource-type-specs': "Microsoft.Resources/templateSpecs"
        })

        # create templete spec
        basic_template_spec = self.cmd('ts create --name {template-spec-name} --version {template-spec-version} --location {location} --template-file {template-file} --resource-group {resource-group}').get_output_in_json()
        template_spec_id = basic_template_spec['id']

        self.kwargs.update({'template-spec-id': template_spec_id})

        # create deployment stack with template file and parameter file
        self.cmd('stack group create --name {name} --resource-group {resource-group}  --template-file "{template-file}" --deny-settings-mode "none" --parameters "{parameter-file}" --yes --description "stack deployment" --delete-all --deny-settings-excluded-principals "principal1 principal2" --deny-settings-excluded-actions "action1 action2" --deny-settings-apply-to-child-scopes', checks=self.check('provisioningState', 'succeeded'))

        # cleanup
        self.cmd('stack group delete --name {name} --resource-group {resource-group} --yes')

        # create deployment stack with template spec and parameter file
        self.cmd('stack group create --name {name} --resource-group {resource-group}  --template-spec "{template-spec-id}" --deny-settings-mode "none" --parameters "{parameter-file}" --yes --no-wait', checks=self.is_empty())

        time.sleep(20)

        # check if the stack was created successfully
        self.cmd('stack group show --name {name} -g {resource-group}', checks=self.check('provisioningState', 'succeeded'))

        # cleanup
        self.cmd('stack group delete --name {name} --resource-group {resource-group} --yes')

        # test flag: delete--resources, create deployment stack
        self.cmd('stack group create --name {name} --resource-group {resource-group}  --template-file "{template-file-spec}" --deny-settings-mode "none" --parameters "name={resource-one}" --yes --delete-resources --delete-resource-groups', checks=self.check('provisioningState', 'succeeded'))

        # update stack, default actionOnUnmanage settings should be detached
        self.cmd('stack group create --name {name} --resource-group {resource-group}  --template-file "{template-file-spec}" --deny-settings-mode "none" --parameters "name={resource-two}" --yes', checks=self.check('provisioningState', 'succeeded'))

        # check that resource1 still exists in Azure
        self.cmd('resource show -n {resource-one} -g {resource-group} --resource-type {resource-type-specs}')

        # check that resource2 exists in Azure
        self.cmd('resource show -n {resource-two} -g {resource-group} --resource-type {resource-type-specs}')

        # update stack with resource3 with delete-resources flag
        self.cmd('stack group create --name {name} --resource-group {resource-group}  --template-file "{template-file-spec}" --deny-settings-mode "none" --parameters "name={resource-three}" --delete-resources --yes', checks=self.check('provisioningState', 'succeeded'))

        # check that resource3 exists in Azure
        self.cmd('resource show -n {resource-three} -g {resource-group} --resource-type {resource-type-specs}')

        # check resource2 does not exist in Azure - should have been purged
        self.cmd('stack group delete --name {name} --resource-group {resource-group} --yes')

        # create new resource group - testing delete-all flag
        self.cmd('group create --location {location} --name {resource-group-two}')

        # create stack
        self.cmd('stack group create --name {name} -g {resource-group-two} --template-file "{track-rg-file}" --deny-settings-mode "none" --parameters "rgname={resource-one}" "tsname={template-spec-name}" --yes', checks=self.check('provisioningState', 'succeeded'))

        # check template spec exists in Azure
        self.cmd('resource list -g {resource-group-two}', checks=self.check("length([?name=='{template-spec-name}'])", 1))

        # check rg resource1 exists in Azure
        self.cmd('group show -n {resource-one}')

        # create stack with delete-all set
        self.cmd('stack group create --name {name} -g {resource-group-two} --template-file "{template-file}" --deny-settings-mode "none" --delete-all --yes', checks=self.check('provisioningState', 'succeeded'))

        # confirm template spec has been removed from azure
        self.cmd('resource list -g {resource-group-two}',  checks=self.check("length([?name=='{template-spec-name}'])", 0))

        #confirm rg resource1 has been removed from azure
        self.cmd('group list', checks=self.check("length([?name=='{resource-one}'])", 0))

        # cleanup - delete resource group two
        self.cmd('stack group delete -g {resource-group-two} --name {name} --yes')

        # cleanup - delete resource group two
        self.cmd('group delete --name {resource-group-two} --yes')

        # create new resource group - testing delete-all flag
        self.cmd('group create --location {location} --name {resource-group-two}')

        # create stack
        self.cmd('stack group create --name {name} -g {resource-group-two} --template-file "{track-rg-file-only}" --deny-settings-mode "none" --parameters "rgname={resource-one}" --yes', checks=self.check('provisioningState', 'succeeded'))

        # check rg resource1 exists in Azure
        self.cmd('group show -n {resource-one}')

        # create stack with delete-all set
        self.cmd('stack group create --name {name} -g {resource-group-two} --template-file "{template-file}" --deny-settings-mode "none" --delete-all --yes', checks=self.check('provisioningState', 'succeeded'))

        #confirm rg resource1 has been removed from azure
        self.cmd('group list', checks=self.check("length([?name=='{resource-one}'])", 0))

        self.cmd('stack group delete -g {resource-group-two} --name {name} --yes')

        # cleanup - delete resource group two
        self.cmd('group delete --name {resource-group-two} --yes')

    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_deployment_stacks', location=location)
    def test_create_deployment_stack_resource_group_with_bicep(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_stack_name = self.create_random_name('cli-test-create-deployment-stack-resource-group', 60)

        self.kwargs.update({
            'name': deployment_stack_name,
            'location': location,
            'template-file': os.path.join(curr_dir, 'simple_template.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),
            'bicep-file': os.path.join(curr_dir, 'data', 'bicep_simple_template.bicep').replace('\\', '\\\\'),
            'bicep-param-file':os.path.join(curr_dir, 'data', 'bicepparam', 'storage_account_params.bicepparam').replace('\\', '\\\\'),
            'bicep-param-file-registry':os.path.join(curr_dir, 'data', 'bicepparam', 'params_registry.bicepparam').replace('\\', '\\\\'),
            'bicep-param-file-templatespec':os.path.join(curr_dir, 'data', 'bicepparam', 'params_templatespec.bicepparam').replace('\\', '\\\\'),
            'resource-group': resource_group,
        })

        # create deployment stack with bicep file
        self.cmd('stack group create --name {name} --resource-group {resource-group}  --template-file "{bicep-file}" --deny-settings-mode "none" --yes', checks=self.check('provisioningState', 'succeeded'))

        # cleanup
        self.cmd('stack group delete --name {name} --resource-group {resource-group} --yes')

        #test bicep param file
        self.cmd('stack group create --name {name} -g {resource-group} -p "{bicep-param-file}" --deny-settings-mode "none" --delete-all --yes', checks=self.check('provisioningState', 'succeeded'))

        self.cmd('stack group delete -g {resource-group} --name {name} --yes')

        # test bicep param file with registry
        self.cmd('stack group create --name {name} -g {resource-group} -p "{bicep-param-file-registry}" --deny-settings-mode "none" --delete-all --yes', checks=self.check('provisioningState', 'succeeded'))

        self.cmd('stack group delete -g {resource-group} --name {name} --yes')

        # test bicep param file with template spec
        self.cmd('stack group create --name {name} -g {resource-group} -p "{bicep-param-file-templatespec}" --deny-settings-mode "none" --delete-all --yes', checks=self.check('provisioningState', 'succeeded'))

        self.cmd('stack group delete -g {resource-group} --name {name} --yes')

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_stacks', location=location)
    def test_show_deployment_stack_resource_group(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_stack_name = self.create_random_name('cli-test-show-deployment-stack-resource-group', 60)

        self.kwargs.update({
            'name': deployment_stack_name,
            'resource-group': resource_group,
            'template-file': os.path.join(curr_dir, 'simple_template.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),
        })

        created_deployment_stack = self.cmd('stack group create --name {name} --resource-group {resource-group} --template-file "{template-file}" --deny-settings-mode "none" --parameters "{parameter-file}" --yes', checks=self.check('provisioningState', 'succeeded')).get_output_in_json()
        deployment_stack_id = created_deployment_stack['id']

        self.kwargs.update({'deployment-stack-id': deployment_stack_id})

        # show stack with stack name
        self.cmd('stack group show --name {name} --resource-group {resource-group}', checks=self.check('name', '{name}'))

        # show stack with stack id
        self.cmd('stack group show --id {deployment-stack-id}', checks=self.check('name', '{name}'))

        # cleanup
        self.cmd('stack group delete --name {name} --resource-group {resource-group} --yes')

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_stacks', location=location)
    def test_list_deployment_stack_resource_group(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_stack_name = self.create_random_name('cli-test-list-deployment-stack-resource-group', 60)

        self.kwargs.update({
            'name': deployment_stack_name,
            'resource-group': resource_group,
            'location': location,
            'template-file': os.path.join(curr_dir, 'simple_template.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),
        })

        self.cmd('stack group create --name {name} --resource-group {resource-group} --template-file "{template-file}" --deny-settings-mode "none" --parameters "{parameter-file}" --yes', checks=self.check('provisioningState', 'succeeded')).get_output_in_json()

        # list stacks in rg
        list_deployment_stacks_rg = self.cmd('stack group list --resource-group {resource-group}').get_output_in_json()

        self.assertTrue(len(list_deployment_stacks_rg) > 0)
        self.assertTrue(list_deployment_stacks_rg[0]['name'], '{name}')

         # cleanup
        self.cmd('stack group delete --name {name} --resource-group {resource-group} --yes')

    @AllowLargeResponse(4096)
    @ResourceGroupPreparer(name_prefix='cli_test_deployment_stacks', location=location)
    def test_delete_deployment_stack_resource_group(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_stack_name = self.create_random_name('cli-test-delete-deployment-stack-resource-group', 60)
        template_spec_name = self.create_random_name('cli-test-template-spec', 60)
        resource_one = self.create_random_name('cli-test-resource-one', 60)
        resource_two = self.create_random_name('cli-test-resource-two', 60)
        resource_group_two = self.create_random_name('cli-test-cli_test_deployment_stacks-two', 60)

        self.kwargs.update({
            'name': deployment_stack_name,
            'resource-group': resource_group,
            'location': location,
            'template-file': os.path.join(curr_dir, 'simple_template.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),
            'track-rg-file': os.path.join(curr_dir, 'tracked_resource_group.json').replace('\\', '\\\\'),
            'track-rg-file-only': os.path.join(curr_dir, 'tracked_resource_group_only.json').replace('\\', '\\\\'),
            'resource-group-two': resource_group_two,
            'resource-one': resource_one,
            'resource-two': resource_two,
            'template-file-spec': os.path.join(curr_dir, 'simple_template_spec.json').replace('\\', '\\\\'),
            'template-spec-name': template_spec_name,
            'template-spec-version': "v1",
            'resource-type-specs': "Microsoft.Resources/templateSpecs"
        })

        # create stack
        self.cmd('stack group create --name {name} --resource-group {resource-group} --template-file "{template-file}" --deny-settings-mode "none" --parameters "{parameter-file}" --delete-resources --delete-resource-groups --yes', checks=self.check('provisioningState', 'succeeded')).get_output_in_json()

        self.cmd('stack group show --name {name} --resource-group {resource-group}', checks=self.check('name', '{name}'))

        # delete stack
        self.cmd('stack group delete --name {name} --resource-group {resource-group} --yes')

        # confirm stack is deleted
        self.cmd('stack group list --resource-group {resource-group}', checks=self.check("length([?name=='{name}'])", 0))

        # create stack
        created_stack = self.cmd('stack group create --name {name} --resource-group {resource-group} --template-file "{template-file}" --deny-settings-mode "none" --parameters "{parameter-file}" --yes', checks=self.check('provisioningState', 'succeeded')).get_output_in_json()
        stack_id = created_stack['id']

        self.kwargs.update({'id':stack_id})

        self.cmd('stack group show --name {name} --resource-group {resource-group}', checks=self.check('name', '{name}'))

        # delete stack with stack id
        self.cmd('stack group delete --id {id} --resource-group {resource-group} --yes')

        # confirm stack is deleted
        self.cmd('stack group list --resource-group {resource-group}', checks=self.check("length([?name=='{name}'])", 0))

         # create new resource group - delete flag --delete-resources
        self.cmd('group create --location {location} --name {resource-group-two}')

        # create stack with resource1 to check if resources are being detached on delete
        self.cmd('stack group create --name {name} -g {resource-group-two} --template-file "{template-file-spec}" --deny-settings-mode "none" --parameters "name={resource-one}" --yes', checks=self.check('provisioningState', 'succeeded'))

        # delete stack set to (default) detach
        self.cmd('stack group delete -g {resource-group-two} --name {name} --yes')

        # check resource1 still exists in Azure
        self.cmd('resource show -n {resource-one} -g {resource-group-two} --resource-type {resource-type-specs}')

        # create stack with resource2 to check if resources are being detached on delete
        self.cmd('stack group create --name {name} -g {resource-group-two} --template-file "{template-file-spec}" --deny-settings-mode "none" --parameters "name={resource-two}" --yes', checks=self.check('provisioningState', 'succeeded'))

        # delete stack with resource2 set to delete
        self.cmd('stack group delete -g {resource-group-two} --name {name} --delete-resources --yes')

        # confirm resource2 has been removed from Azure
        self.cmd('resource list', checks=self.check("length([?name=='{resource-two}'])", 0))

        # cleanup - delete resource group two
        self.cmd('group delete --name {resource-group-two} --yes')

        # create new resource group - testing delete-all flag
        self.cmd('group create --location {location} --name {resource-group-two}')

        # create stack
        self.cmd('stack group create --name {name} -g {resource-group-two} --template-file "{track-rg-file}" --deny-settings-mode "none" --parameters "rgname={resource-one}" "tsname={template-spec-name}" --yes', checks=self.check('provisioningState', 'succeeded'))

        # check template spec exists in Azure
        self.cmd('resource list -g {resource-group-two}', checks=self.check("length([?name=='{template-spec-name}'])", 1))

        # check rg resource1 exists in Azure
        self.cmd('group show -n {resource-one}')

        # create stack with delete-all set
        self.cmd('stack group delete --name {name} -g {resource-group-two} --delete-all --yes')

        # confirm template spec has been removed from azure
        self.cmd('resource list -g {resource-group-two}',  checks=self.check("length([?name=='{template-spec-name}'])", 0))

        #confirm rg resource1 has been removed from azure
        self.cmd('group list', checks=self.check("length([?name=='{resource-one}'])", 0))

        # cleanup - delete resource group two
        self.cmd('group delete --name {resource-group-two} --yes')

        # create new resource group - testing delete-all flag
        self.cmd('group create --location {location} --name {resource-group-two}')

        # create stack
        self.cmd('stack group create --name {name} -g {resource-group-two} --template-file "{track-rg-file-only}" --deny-settings-mode "none" --parameters "rgname={resource-one}" --yes', checks=self.check('provisioningState', 'succeeded'))

        # check rg resource1 exists in Azure
        self.cmd('group show -n {resource-one}')

        # delete stack with delete-all set
        self.cmd('stack group delete --name {name} -g {resource-group-two} --delete-all --yes')

        # confirm rg resource1 has been removed from azure
        self.cmd('group list', checks=self.check("length([?name=='{resource-one}'])", 0))

        # cleanup - delete resource group two
        self.cmd('group delete --name {resource-group-two} --yes')

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_stacks', location=location)
    def test_export_template_deployment_stack_resource_group(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_stack_name = self.create_random_name('cli-test-show-deployment-stack-resource-group', 60)

        self.kwargs.update({
            'name': deployment_stack_name,
            'resource-group': resource_group,
            'template-file': os.path.join(curr_dir, 'simple_template.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),
        })

        created_deployment_stack = self.cmd('stack group create --name {name} --resource-group {resource-group} --template-file "{template-file}" --deny-settings-mode "none" --parameters "{parameter-file}" --yes', checks=self.check('provisioningState', 'succeeded')).get_output_in_json()
        deployment_stack_id = created_deployment_stack['id']

        self.kwargs.update({'deployment-stack-id': deployment_stack_id})

        # export stack with stack name
        self.cmd('stack group export --name {name} --resource-group {resource-group}')

        # export stack with stack id
        self.cmd('stack group export --id {deployment-stack-id}')

        # show stack with stack name
        self.cmd('stack group show --name {name} --resource-group {resource-group}', checks=self.check('name', '{name}'))

        # cleanup
        self.cmd('stack group delete --name {name} --resource-group {resource-group} --yes')

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_deployment_stacks', location=location)
    def test_create_deployment_stack_management_group(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_stack_name = self.create_random_name('cli-test-create-deployment-stack-subscription', 60)
        template_spec_name = self.create_random_name('cli-test-template-spec', 60)
        resource_one = self.create_random_name('cli-test-resource-one', 60)
        resource_two = self.create_random_name('cli-test-resource-two', 60)
        resource_three = self.create_random_name('cli-test-resource-three', 60)
        resource_group_two = self.create_random_name('cli-test-cli_test_deployment_stacks-two', 60)

        self.kwargs.update({
            'name': deployment_stack_name,
            'location': location,
            'subscription': self.get_subscription_id(),
            'template-file': os.path.join(curr_dir, 'simple_template.json').replace('\\', '\\\\'),
            'template-file-spec': os.path.join(curr_dir, 'simple_template_spec.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),
            'bicep-file': os.path.join(curr_dir, 'data', 'bicep_simple_template.bicep').replace('\\', '\\\\'),
            'bicep-param-file':os.path.join(curr_dir, 'data', 'bicepparam', 'storage_account_params.bicepparam').replace('\\', '\\\\'),
            'template-file-rg': os.path.join(curr_dir, 'simple_template_resource_group.json').replace('\\', '\\\\'),
            'track-rg-file': os.path.join(curr_dir, 'tracked_resource_group.json').replace('\\', '\\\\'),
            'template-spec-name': template_spec_name,
            'template-spec-version': "v1",
            'resource-group': resource_group,
            'resource-group-two': resource_group_two,
            'resource-one': resource_one,
            'resource-two': resource_two,
            'resource-three': resource_three,
            'resource-type-specs': "Microsoft.Resources/templateSpecs",
            'actual-mg': self.create_random_name('azure-cli-management', 30),
            'mg': "AzBlueprintAssignTest"
        })

        # create templete spec
        basic_template_spec = self.cmd('ts create --name {template-spec-name} --version {template-spec-version} --location {location} --template-file {template-file} --resource-group {resource-group}').get_output_in_json()
        template_spec_id = basic_template_spec['id']

        self.kwargs.update({'template-spec-id': template_spec_id})

        self.cmd('stack mg create --name {name} --management-group-id {mg} --location {location} --template-spec "{template-spec-id}" --deny-settings-mode "none" --parameters "{parameter-file}" --description "MG stack deployment" --deployment-subscription {subscription}', checks=self.check('provisioningState', 'succeeded'))

        # cleanup
        self.cmd('stack mg delete --name {name} --management-group-id {mg} --yes')

        # create deployment stack with template file and parameter file
        self.cmd('stack mg create --name {name} --management-group-id {mg} --location {location} --template-file "{template-file}" --deny-settings-mode "none" --parameters "{parameter-file}" --description "MG stack deployment" --delete-all --deny-settings-excluded-principals "principal1 principal2" --deny-settings-excluded-actions "action1 action2" --deny-settings-apply-to-child-scopes --no-wait', checks=self.is_empty())

        time.sleep(20)

        # check if the stack was created successfully
        self.cmd('stack mg show --name {name} --management-group-id {mg}', checks=self.check('provisioningState', 'succeeded'))

        # cleanup
        self.cmd('stack mg delete --name {name} --management-group-id {mg} --yes')

        # test delete flag --delete-resource-groups - create stack  with resource1
        self.cmd('stack mg create --name {name} --management-group-id {mg} --location {location} --template-file "{template-file-rg}" --deny-settings-mode "none" --parameters "name={resource-one}" --delete-resources --tags "tag1 tag2"', checks=self.check('provisioningState', 'succeeded'))

        # update stack with resource2 set to detach
        self.cmd('stack mg create --name {name} --management-group-id {mg} --location {location} --template-file "{template-file-rg}" --deny-settings-mode "none" --parameters "name={resource-two}"', checks=self.check('provisioningState', 'succeeded'))

        # check resource1 still exists in Azure
        self.cmd('group show -n {resource-one}')

        # check resource2 exists in Azure
        self.cmd('group show -n {resource-two}')

        # update stack with resource3 set to delete
        self.cmd('stack mg create --name {name} --management-group-id {mg} --location {location} --template-file "{template-file-rg}" --deny-settings-mode "none" --parameters "name={resource-three}" --delete-resources', checks=self.check('provisioningState', 'succeeded'))

        # check resource1 still exists in Azure
        self.cmd('group show -n {resource-one}')

        # check resource3 exists in Azure
        self.cmd('group show -n {resource-three}')

        # check resource2 does not exist in Azure - should have been purged
        self.cmd('resource list', checks=self.check("length([?name=='{resource-two}'])", 0))

        # cleanup
        self.cmd('stack mg delete --name {name} --management-group-id {mg} --yes')

    def test_show_deployment_stack_management_group(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_stack_name = self.create_random_name('cli-test-get-deployment-stack-subscription', 60)
        self.kwargs.update({
            'name': deployment_stack_name,
            'location': location,
            'template-file': os.path.join(curr_dir, 'simple_template.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),
            'mg': "AzBlueprintAssignTest",
            'actual-mg':self.create_random_name('azure-cli-management', 30)
        })


        created_deployment_stack = self.cmd('stack mg create --name {name} --management-group-id {mg} --location {location} --template-file "{template-file}" --deny-settings-mode "none"', checks=self.check('provisioningState', 'succeeded')).get_output_in_json()
        deployment_stack_id = created_deployment_stack['id']

        self.kwargs.update({'deployment-stack-id': deployment_stack_id})

        # show stack with stack name
        self.cmd('stack mg show --name {name} --management-group-id {mg}', checks=self.check('name', '{name}'))

        # show stack with stack id
        self.cmd('stack mg show --id {deployment-stack-id} --management-group-id {mg}', checks=self.check('name', '{name}'))

        # cleanup
        self.cmd('stack mg delete --name {name} --management-group-id {mg} --yes')

    def test_delete_deployment_stack_management_group(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_stack_name = self.create_random_name('cli-test-delete-deployment-stack-subscription', 60)
        resource_one = self.create_random_name('cli-test-resource-one', 60)
        resource_two = self.create_random_name('cli-test-resource-two', 60)
        resource_three = self.create_random_name('cli-test-resource-three', 60)
        template_spec_name = self.create_random_name('cli-test-template-spec', 60)
        resource_group_two = self.create_random_name('cli-test-cli_test_deployment_stacks-two', 60)

        self.kwargs.update({
            'name': deployment_stack_name,
            'location': location,
            'template-file': os.path.join(curr_dir, 'simple_template.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),
            'template-file-spec': os.path.join(curr_dir, 'simple_template_spec.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),
            'bicep-file': os.path.join(curr_dir, 'data\\bicep_simple_template.bicep').replace('\\', '\\\\'),
            'template-file-rg': os.path.join(curr_dir, 'simple_template_resource_group.json').replace('\\', '\\\\'),
            'track-rg-file': os.path.join(curr_dir, 'tracked_resource_group.json').replace('\\', '\\\\'),
            'template-spec-name': template_spec_name,
            'template-spec-version': "v1",
            'resource-one': resource_one,
            'resource-two': resource_two,
            'resource-three': resource_three,
            'resource-group-two': resource_group_two,
            'resource-type-specs': "Microsoft.Resources/templateSpecs",
            'mg': "AzBlueprintAssignTest",
            'actual-mg':self.create_random_name('azure-cli-management', 30)
        })

        # create stack
        self.cmd('stack mg create --name {name} --management-group-id {mg} --location {location} --template-file "{template-file}" --deny-settings-mode "none" --parameters "{parameter-file}" --yes', checks=self.check('provisioningState', 'succeeded')).get_output_in_json()

        # check stack to make sure it exists
        self.cmd('stack mg show --name {name} --management-group-id {mg}', checks=self.check('name', '{name}'))

        # delete stack with stack name
        self.cmd('stack mg delete --name {name} --management-group-id {mg} --yes')

        # add delete with stack id
        created_stack = self.cmd('stack mg create --name {name} --management-group-id {mg} --location {location} --template-file "{template-file}" --deny-settings-mode "none" --parameters "{parameter-file}" --yes', checks=self.check('provisioningState', 'succeeded')).get_output_in_json()
        stack_id = created_stack['id']

        self.kwargs.update({'id': stack_id})

        # delete stack with id
        self.cmd('stack mg delete --id  {id} --management-group-id {mg} --yes')

        # test delete flag --delete-resource-groups - create stack  with resource1
        self.cmd('stack mg create --name {name} --management-group-id {mg} --location {location} --template-file "{template-file-rg}" --deny-settings-mode "none" --parameters "name={resource-one}" --yes', checks=self.check('provisioningState', 'succeeded'))

        # delete stack with resource1 set to detach
        self.cmd('stack mg delete --name {name} --management-group-id {mg} --yes')

        # check resource1 still exists in Azure
        self.cmd('group show -n {resource-one}')

        # update stack with resource3 set to delete
        self.cmd('stack mg create --name {name} --management-group-id {mg} --location {location} --template-file "{template-file-rg}" --deny-settings-mode "none" --parameters "name={resource-two}" --delete-resources --delete-resource-groups --yes', checks=self.check('provisioningState', 'succeeded'))

        # delete stack with resource1 set to detach
        self.cmd('stack mg delete --name {name} --management-group-id {mg} --delete-resources --delete-resource-groups --yes')

        # check resource1 still exists in Azure
        self.cmd('group show -n {resource-one}')

        #confirm resource2 has been removed from Azure
        self.cmd('group list', checks=self.check("length([?name=='{resource-two}'])", 0))

        # cleanup
        self.cmd('group delete --name {resource-one} --yes')

    def test_export_template_deployment_stack_management_group(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_stack_name = self.create_random_name('cli-test-get-deployment-stack-subscription', 60)
        self.kwargs.update({
            'name': deployment_stack_name,
            'location': location,
            'template-file': os.path.join(curr_dir, 'simple_template.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),
            'mg': "AzBlueprintAssignTest",
            'actual-mg':self.create_random_name('azure-cli-management', 30)
        })

        created_deployment_stack = self.cmd('stack mg create --name {name} --management-group-id {mg} --location {location} --template-file "{template-file}" --deny-settings-mode "none" --parameters "{parameter-file}" --yes', checks=self.check('provisioningState', 'succeeded')).get_output_in_json()
        deployment_stack_id = created_deployment_stack['id']

        self.kwargs.update({'deployment-stack-id': deployment_stack_id})

        # show stack with stack name
        self.cmd('stack mg export --name {name} --management-group-id {mg}')

        # show stack with stack id
        self.cmd('stack mg export --id {deployment-stack-id} --management-group-id {mg}')

        # show stack with stack name
        self.cmd('stack mg show --name {name} --management-group-id {mg}', checks=self.check('name', '{name}'))

        # cleanup
        self.cmd('stack mg delete --name {name} --management-group-id {mg} --yes')

    @AllowLargeResponse(4096)
    def test_list_deployment_stack_management_group(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        deployment_stack_name = self.create_random_name('cli-test-list-deployment-stack-subscription', 60)

        self.kwargs.update({
            'name': deployment_stack_name,
            'location': location,
            'template-file': os.path.join(curr_dir, 'simple_template.json').replace('\\', '\\\\'),
            'parameter-file': os.path.join(curr_dir, 'simple_template_params.json').replace('\\', '\\\\'),
            'mg': "AzBlueprintAssignTest",
            'actual-mg':self.create_random_name('azure-cli-management', 30)
        })

        self.cmd('stack mg create --name {name} --management-group-id {mg} --location {location} --template-file "{template-file}" --deny-settings-mode "none" --parameters "{parameter-file}" --yes', checks=self.check('provisioningState', 'succeeded')).get_output_in_json()

        # list stacks
        list_deployment_stacks = self.cmd('stack mg list --management-group-id {mg}').get_output_in_json()

        self.assertTrue(len(list_deployment_stacks) > 0)
        self.assertTrue(list_deployment_stacks[0]['name'], '{name}')

         # cleanup
        self.cmd('stack mg delete --name {name} --management-group-id {mg} --yes')

class DeploymentTestAtSubscriptionScopeTemplateSpecs(ScenarioTest):

    @AllowLargeResponse(4096)
    @ResourceGroupPreparer(name_prefix='cli_test_template_specs_tenant_deploy', location='eastus')
    def test_subscription_level_deployment_ts(self, resource_group, resource_group_location):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_spec_name = self.create_random_name('cli-test-sub-lvl-ts-deploy', 60)
        self.kwargs.update({
            'template_spec_name': template_spec_name,
            'resource_group_location': resource_group_location,
            'tf': os.path.join(curr_dir, 'subscription_level_template.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'subscription_level_parameters.json').replace('\\', '\\\\'),
            # params-uri below is the raw file url of the subscription_level_parameters.json above
            'params_uri': 'https://raw.githubusercontent.com/Azure/azure-cli/dev/src/azure-cli/azure/cli/command_modules/resource/tests/latest/subscription_level_parameters.json',
            'dn': self.create_random_name('azure-cli-subscription_level_deployment', 60),
            'dn2': self.create_random_name('azure-cli-subscription_level_deployment', 60),
            'storage-account-name': self.create_random_name('armbuilddemo', 20)
        })

        result = self.cmd('ts create -g {rg} -n {template_spec_name} -v 1.0 -l {resource_group_location} -f "{tf}"',
                          checks=self.check('name', '1.0')).get_output_in_json()

        self.kwargs['template_spec_version_id'] = result['id']

        self.cmd('deployment sub validate --location WestUS --template-spec {template_spec_version_id} --parameters "{params_uri}"  --parameters storageAccountName="{storage-account-name}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment sub create -n {dn} --location WestUS --template-spec {template_spec_version_id} --parameters @"{params}" --parameters storageAccountName="{storage-account-name}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment sub show -n {dn}', checks=[
            self.check('name', '{dn}')
        ])

        self.cmd('deployment sub export -n {dn}', checks=[
        ])

        self.cmd('deployment operation sub list -n {dn}', checks=[
            self.check('length([])', 5)
        ])

        self.cmd('deployment sub create -n {dn2} --location WestUS --template-spec "{template_spec_version_id}" --parameters @"{params}" --no-wait')

        self.cmd('deployment sub cancel -n {dn2}')

        self.cmd('deployment sub show -n {dn2}', checks=[
            self.check('properties.provisioningState', 'Canceled')
        ])

        # clean up
        self.kwargs['template_spec_id'] = result['id'].replace('/versions/1.0', ' ')
        self.cmd('ts delete --template-spec {template_spec_id} --yes')


class DeploymentTestAtResourceGroupTemplateSpecs(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_template_specs_resource_group_deployment', location='westus')
    def test_resource_group_deployment_ts(self, resource_group, resource_group_location):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_spec_name = self.create_random_name('cli-test-resource-group-ts-deploy', 60)
        self.kwargs.update({
            'template_spec_name': template_spec_name,
            'resource_group_location': resource_group_location,
            'tf': os.path.join(curr_dir, 'simple_deploy.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'simple_deploy_parameters.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-resource-group-deployment', 60),
            'dn2': self.create_random_name('azure-cli-resource-group-deployment', 60),
        })

        result = self.cmd('ts create -g {rg} -n {template_spec_name} -v 1.0 -l {resource_group_location} -f "{tf}"',
                          checks=self.check('name', '1.0')).get_output_in_json()

        self.kwargs['template_spec_version_id'] = result['id']

        self.cmd('deployment group validate --resource-group {rg} --template-spec "{template_spec_version_id}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment group create --resource-group {rg} -n {dn} --template-spec "{template_spec_version_id}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
        ])

        self.cmd('deployment group list --resource-group {rg}', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment group list --resource-group {rg} --filter "provisioningState eq \'Succeeded\'"', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment group show --resource-group {rg} -n {dn}', checks=[
            self.check('name', '{dn}')
        ])

        self.cmd('deployment group export --resource-group {rg} -n {dn}', checks=[
        ])

        self.cmd('deployment operation group list --resource-group {rg} -n {dn}', checks=[
            self.check('length([])', 2)
        ])

        self.cmd('deployment group create --resource-group {rg} -n {dn2} --template-spec "{template_spec_version_id}" --parameters @"{params}" --no-wait')

        self.cmd('deployment group cancel -n {dn2} -g {rg}')

        self.cmd('deployment group show -n {dn2} -g {rg}', checks=[
            self.check('properties.provisioningState', 'Canceled')
        ])

class CrossRGDeploymentScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_cross_rg_alt', parameter_name='resource_group_cross')
    @ResourceGroupPreparer(name_prefix='cli_test_cross_rg_deploy')
    def test_group_deployment_crossrg(self, resource_group, resource_group_cross):
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'rg1': resource_group,
            'rg2': resource_group_cross,
            'tf': os.path.join(curr_dir, 'crossrg_deploy.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-crossrgdeployment', 40),
            'sa1': create_random_name(prefix='crossrg'),
            'sa2': create_random_name(prefix='crossrg')
        })

        self.cmd('group deployment validate -g {rg1} --template-file "{tf}" --parameters CrossRg={rg2} StorageAccountName1={sa1} StorageAccountName2={sa2}', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        with self.assertRaises(CLIError):
            self.cmd('group deployment validate -g {rg1} --template-file "{tf}" --parameters CrossRg=SomeRandomRG StorageAccountName1={sa1} StorageAccountName2={sa2}')

        self.cmd('group deployment create -g {rg1} -n {dn} --template-file "{tf}" --parameters CrossRg={rg2}', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg1}'),
        ])
        self.cmd('group deployment list -g {rg1}', checks=[
            self.check('[0].name', '{dn}'),
            self.check('[0].resourceGroup', '{rg1}')
        ])
        self.cmd('group deployment show -g {rg1} -n {dn}', checks=[
            self.check('name', '{dn}'),
            self.check('resourceGroup', '{rg1}')
        ])
        self.cmd('group deployment operation list -g {rg1} -n {dn}', checks=[
            self.check('length([])', 3),
            self.check('[0].resourceGroup', '{rg1}')
        ])


class CrossTenantDeploymentScenarioTest(LiveScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_cross_tenant_deploy', location='eastus')
    @ResourceGroupPreparer(name_prefix='cli_test_cross_tenant_deploy', location='eastus',
                           parameter_name='another_resource_group', subscription=AUX_SUBSCRIPTION)
    def test_group_deployment_cross_tenant(self, resource_group, another_resource_group):
        # Prepare Network Interface
        self.kwargs.update({
            'vm_rg': resource_group,
            'vnet': 'clivmVNET',
            'subnet': 'clivmSubnet',
            'nsg': 'clivmNSG',
            'ip': 'clivmPublicIp',
            'nic': 'clivmVMNic'
        })
        self.cmd('network vnet create -n {vnet} -g {vm_rg} --subnet-name {subnet}')
        self.cmd('network nsg create -n {nsg} -g {vm_rg}')
        self.cmd('network public-ip create -n {ip} -g {vm_rg} --allocation-method Dynamic')
        res = self.cmd('network nic create -n {nic} -g {vm_rg} --subnet {subnet} --vnet {vnet} --network-security-group {nsg} --public-ip-address {ip}').get_output_in_json()
        self.kwargs.update({
            'nic_id': res['NewNIC']['id']
        })

        # Prepare SIG in another tenant
        self.kwargs.update({
            'location': 'eastus',
            'vm': self.create_random_name('cli_crosstenantvm', 40),
            'gallery': self.create_random_name('cli_crosstenantgallery', 40),
            'image': self.create_random_name('cli_crosstenantimage', 40),
            'version': '1.1.2',
            'captured': self.create_random_name('cli_crosstenantmanagedimage', 40),
            'aux_sub': AUX_SUBSCRIPTION,
            'rg': another_resource_group,
            'aux_tenant': AUX_TENANT
        })

        self.cmd('sig create -g {rg} --gallery-name {gallery} --subscription {aux_sub}', checks=self.check('name', self.kwargs['gallery']))
        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --os-type linux -p publisher1 -f offer1 -s sku1 --subscription {aux_sub}',
                 checks=self.check('name', self.kwargs['image']))
        self.cmd('sig image-definition show -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --subscription {aux_sub}',
                 checks=self.check('name', self.kwargs['image']))

        self.cmd('vm create -g {rg} -n {vm} --image ubuntults --admin-username clitest1 --generate-ssh-key --subscription {aux_sub}')
        self.cmd(
            'vm run-command invoke -g {rg} -n {vm} --command-id RunShellScript --scripts "echo \'sudo waagent -deprovision+user --force\' | at -M now + 1 minutes" --subscription {aux_sub}')
        time.sleep(70)

        self.cmd('vm deallocate -g {rg} -n {vm} --subscription {aux_sub}')
        self.cmd('vm generalize -g {rg} -n {vm} --subscription {aux_sub}')
        self.cmd('image create -g {rg} -n {captured} --source {vm} --subscription {aux_sub}')
        res = self.cmd(
            'sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --gallery-image-version {version} --managed-image {captured} --replica-count 1 --subscription {aux_sub}').get_output_in_json()
        self.kwargs.update({
            'sig_id': res['id']
        })

        # Cross tenant deploy
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'crosstenant_vm_deploy.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('cli-crosstenantdeployment', 40),
            'dn1': self.create_random_name('cli-crosstenantdeployment1', 40),
            'dn2': self.create_random_name('cli-crosstenantdeployment2', 40),
            'dn3': self.create_random_name('cli-crosstenantdeployment3', 40)
        })

        self.cmd('group deployment validate -g {vm_rg} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id}', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('group deployment create -g {vm_rg} -n {dn} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-subs "{aux_sub}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{vm_rg}')
        ])
        self.cmd('group deployment list -g {vm_rg}', checks=[
            self.check('[0].name', '{dn}'),
            self.check('[0].resourceGroup', '{vm_rg}')
        ])
        self.cmd('group deployment show -g {vm_rg} -n {dn}', checks=[
            self.check('name', '{dn}'),
            self.check('resourceGroup', '{vm_rg}')
        ])

        self.cmd('group deployment create -g {vm_rg} -n {dn1} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-tenants "{aux_tenant}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{vm_rg}')
        ])
        self.cmd('group deployment list -g {vm_rg}', checks=[
            self.check('[0].name', '{dn1}'),
            self.check('[0].resourceGroup', '{vm_rg}')
        ])
        self.cmd('group deployment show -g {vm_rg} -n {dn1}', checks=[
            self.check('name', '{dn1}'),
            self.check('resourceGroup', '{vm_rg}')
        ])

        self.cmd('group deployment create -g {vm_rg} -n {dn2} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-subs "{aux_sub}" -j', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{vm_rg}')
        ])
        self.cmd('group deployment list -g {vm_rg}', checks=[
            self.check('[0].name', '{dn2}'),
            self.check('[0].resourceGroup', '{vm_rg}')
        ])
        self.cmd('group deployment show -g {vm_rg} -n {dn2}', checks=[
            self.check('name', '{dn2}'),
            self.check('resourceGroup', '{vm_rg}')
        ])

        self.cmd('group deployment create -g {vm_rg} -n {dn3} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-tenants "{aux_tenant}" -j', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{vm_rg}')
        ])
        self.cmd('group deployment list -g {vm_rg}', checks=[
            self.check('[0].name', '{dn3}'),
            self.check('[0].resourceGroup', '{vm_rg}')
        ])
        self.cmd('group deployment show -g {vm_rg} -n {dn3}', checks=[
            self.check('name', '{dn3}'),
            self.check('resourceGroup', '{vm_rg}')
        ])

        with self.assertRaises(AssertionError):
            self.cmd('group deployment create -g {vm_rg} -n {dn} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-tenants "{aux_tenant}" --aux-subs "{aux_sub}"')

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_group_cross_tenant', location='eastus')
    @ResourceGroupPreparer(name_prefix='cli_test_deployment_group_cross_tenant', location='eastus',
                           parameter_name='another_resource_group', subscription=AUX_SUBSCRIPTION)
    def test_deployment_group_cross_tenant(self, resource_group, another_resource_group):
        # Prepare Network Interface
        self.kwargs.update({
            'vm_rg': resource_group,
            'vnet': 'clivmVNET',
            'subnet': 'clivmSubnet',
            'nsg': 'clivmNSG',
            'ip': 'clivmPublicIp',
            'nic': 'clivmVMNic'
        })
        self.cmd('network vnet create -n {vnet} -g {vm_rg} --subnet-name {subnet}')
        self.cmd('network nsg create -n {nsg} -g {vm_rg}')
        self.cmd('network public-ip create -n {ip} -g {vm_rg} --allocation-method Dynamic')
        res = self.cmd('network nic create -n {nic} -g {vm_rg} --subnet {subnet} --vnet {vnet} --network-security-group {nsg} --public-ip-address {ip}').get_output_in_json()
        self.kwargs.update({
            'nic_id': res['NewNIC']['id']
        })

        # Prepare SIG in another tenant
        self.kwargs.update({
            'location': 'eastus',
            'vm': self.create_random_name('cli_crosstenantvm', 40),
            'gallery': self.create_random_name('cli_crosstenantgallery', 40),
            'image': self.create_random_name('cli_crosstenantimage', 40),
            'version': '1.1.2',
            'captured': self.create_random_name('cli_crosstenantmanagedimage', 40),
            'aux_sub': AUX_SUBSCRIPTION,
            'rg': another_resource_group,
            'aux_tenant': AUX_TENANT
        })

        self.cmd('sig create -g {rg} --gallery-name {gallery} --subscription {aux_sub}', checks=self.check('name', self.kwargs['gallery']))
        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --os-type linux -p publisher1 -f offer1 -s sku1 --subscription {aux_sub}',
                 checks=self.check('name', self.kwargs['image']))
        self.cmd('sig image-definition show -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --subscription {aux_sub}',
                 checks=self.check('name', self.kwargs['image']))

        self.cmd('vm create -g {rg} -n {vm} --image ubuntults --admin-username clitest1 --generate-ssh-key --subscription {aux_sub}')
        self.cmd(
            'vm run-command invoke -g {rg} -n {vm} --command-id RunShellScript --scripts "echo \'sudo waagent -deprovision+user --force\' | at -M now + 1 minutes" --subscription {aux_sub}')
        time.sleep(70)

        self.cmd('vm deallocate -g {rg} -n {vm} --subscription {aux_sub}')
        self.cmd('vm generalize -g {rg} -n {vm} --subscription {aux_sub}')
        self.cmd('image create -g {rg} -n {captured} --source {vm} --subscription {aux_sub}')
        res = self.cmd(
            'sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --gallery-image-version {version} --managed-image {captured} --replica-count 1 --subscription {aux_sub}').get_output_in_json()
        self.kwargs.update({
            'sig_id': res['id']
        })

        # Cross tenant deploy
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'crosstenant_vm_deploy.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('cli-crosstenantdeployment', 40),
            'dn1': self.create_random_name('cli-crosstenantdeployment1', 40),
            'dn2': self.create_random_name('cli-crosstenantdeployment2', 40),
            'dn3': self.create_random_name('cli-crosstenantdeployment3', 40)
        })

        self.cmd('deployment group validate -g {vm_rg} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id}', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment group create -g {vm_rg} -n {dn} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-subs "{aux_sub}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{vm_rg}')
        ])
        self.cmd('deployment group list -g {vm_rg}', checks=[
            self.check('[0].name', '{dn}'),
            self.check('[0].resourceGroup', '{vm_rg}')
        ])
        self.cmd('deployment group show -g {vm_rg} -n {dn}', checks=[
            self.check('name', '{dn}'),
            self.check('resourceGroup', '{vm_rg}')
        ])

        self.cmd('deployment group create -g {vm_rg} -n {dn1} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-tenants "{aux_tenant}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{vm_rg}')
        ])
        self.cmd('deployment group list -g {vm_rg}', checks=[
            self.check('[0].name', '{dn1}'),
            self.check('[0].resourceGroup', '{vm_rg}')
        ])
        self.cmd('deployment group show -g {vm_rg} -n {dn1}', checks=[
            self.check('name', '{dn1}'),
            self.check('resourceGroup', '{vm_rg}')
        ])

        self.cmd('deployment group create -g {vm_rg} -n {dn2} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-subs "{aux_sub}" -j', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{vm_rg}')
        ])
        self.cmd('deployment group list -g {vm_rg}', checks=[
            self.check('[0].name', '{dn2}'),
            self.check('[0].resourceGroup', '{vm_rg}')
        ])
        self.cmd('deployment group show -g {vm_rg} -n {dn2}', checks=[
            self.check('name', '{dn2}'),
            self.check('resourceGroup', '{vm_rg}')
        ])

        self.cmd('deployment group create -g {vm_rg} -n {dn3} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-tenants "{aux_tenant}" -j', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{vm_rg}')
        ])
        self.cmd('deployment group list -g {vm_rg}', checks=[
            self.check('[0].name', '{dn3}'),
            self.check('[0].resourceGroup', '{vm_rg}')
        ])
        self.cmd('deployment group show -g {vm_rg} -n {dn3}', checks=[
            self.check('name', '{dn3}'),
            self.check('resourceGroup', '{vm_rg}')
        ])

        with self.assertRaises(AssertionError):
            self.cmd('deployment group create -g {vm_rg} -n {dn} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-tenants "{aux_tenant}" --aux-subs "{aux_sub}"')

class DeploymentWithBicepScenarioTest(LiveScenarioTest):

    def setup(self):
        super.setup()
        self.cmd('az bicep uninstall')

    def tearDown(self):
        super().tearDown()
        self.cmd('az bicep uninstall')

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_with_bicep')
    def test_resource_group_level_deployment_with_bicep(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'storage_account_deploy.bicep').replace('\\', '\\\\'),
        })

        self.cmd('deployment group validate --resource-group {rg} --template-file "{tf}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment group what-if --resource-group {rg} --template-file "{tf}" --no-pretty-print', checks=[
            self.check('status', 'Succeeded'),
        ])

        self.cmd('deployment group create --resource-group {rg} --template-file "{tf}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_with_bicepparam')
    def test_resource_group_level_deployment_with_bicepparams(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'params': os.path.join(curr_dir, 'data\\bicepparam\\storage_account_params.bicepparam').replace('\\', '\\\\')
        })

        self.cmd('deployment group validate --resource-group {rg} --parameters {params}', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment group what-if --resource-group {rg} --parameters {params} --no-pretty-print', checks=[
            self.check('status', 'Succeeded'),
        ])

        self.cmd('deployment group create --resource-group {rg} --parameters {params}', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_with_bicepparam_registry')
    def test_resource_group_level_deployment_with_bicepparam_registry(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'params': os.path.join(curr_dir, 'data\\bicepparam\\params_registry.bicepparam').replace('\\', '\\\\')
        })

        self.cmd('deployment group validate --resource-group {rg} --parameters {params}', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment group what-if --resource-group {rg} --parameters {params} --no-pretty-print', checks=[
            self.check('status', 'Succeeded'),
        ])

        self.cmd('deployment group create --resource-group {rg} --parameters {params}', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_with_bicepparam_templatespec')
    def test_resource_group_level_deployment_with_bicepparam_templatespec(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'params': os.path.join(curr_dir, 'data\\bicepparam\\params_templatespec.bicepparam').replace('\\', '\\\\')
        })

        self.cmd('deployment group validate --resource-group {rg} --parameters {params}', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment group what-if --resource-group {rg} --parameters {params} --no-pretty-print', checks=[
            self.check('status', 'Succeeded'),
        ])

        self.cmd('deployment group create --resource-group {rg} --parameters {params}', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

    def test_resource_group_level_deployment_with_bicepparams_and_template_file(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'data\\bicepparam\\storage_account_template.bicep').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'data\\bicepparam\\storage_account_params.bicepparam').replace('\\', '\\\\')
        })

        self.cmd('deployment group validate --resource-group {rg} --template-file "{tf}" --parameters {params}', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment group what-if --resource-group {rg} --template-file "{tf}" --parameters {params} --no-pretty-print', checks=[
            self.check('status', 'Succeeded'),
        ])

        self.cmd('deployment group create --resource-group {rg} --template-file "{tf}" --parameters {params}', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

    def test_resource_deployment_with_bicepparam_and_incompatible_version(self):
        self.kwargs.update({
            'rg' : "exampleGroup",
            'tf': "./main.json",
            'params' : "./param.bicepparam"
        })

        self.cmd('az bicep install --version v0.13.1')

        minimum_supported_version = "0.14.85"
        with self.assertRaisesRegex(CLIError, f"Unable to compile .bicepparam file with the current version of Bicep CLI. Please upgrade Bicep CLI to { minimum_supported_version} or later."):
            self.cmd('deployment group create --resource-group {rg} --template-file "{tf}" --parameters {params}')

    def test_resource_deployment_with_bicepparam_and_json_template(self):
        self.kwargs.update({
            'rg' : "exampleGroup",
            'tf': "./main.json",
            'params' : "./param.bicepparam"
        })

        with self.assertRaisesRegex(CLIError, "Only a .bicep template is allowed with a .bicepparam file"):
            self.cmd('deployment group create --resource-group {rg} --template-file "{tf}" --parameters {params}')


    def test_resource_deployment_with_bicepparam_and_other_parameter_sources(self):
        self.kwargs.update({
            'rg' : "exampleGroup",
            'tf': "./main.bicepparam",
            'params1' : "./param1.bicepparam",
            'params2' : "./param2.json",
        })

        with self.assertRaisesRegex(CLIError, "Can not use --parameters argument more than once when using a .bicepparam file"):
            self.cmd('deployment group create --resource-group {rg} --template-file "{tf}" --parameters {params1} --parameters {params2}')

    def test_subscription_level_deployment_with_bicep(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'policy_definition_deploy_sub.bicep').replace('\\', '\\\\'),
        })

        self.cmd('deployment sub validate --location westus --template-file "{tf}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment sub what-if --location westus --template-file "{tf}" --no-pretty-print', checks=[
            self.check('status', 'Succeeded'),
        ])

        self.cmd('deployment sub create --location westus --template-file "{tf}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

    def test_management_group_level_deployment_with_bicep(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'policy_definition_deploy_mg.bicep').replace('\\', '\\\\'),
            'mg': self.create_random_name('azure-cli-management', 30)
        })

        self.cmd('account management-group create --name {mg}', checks=[])

        self.cmd('deployment mg validate --management-group-id {mg} --location WestUS --template-file "{tf}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment mg what-if --management-group-id {mg} --location WestUS --template-file "{tf}" --no-pretty-print', checks=[
            self.check('status', 'Succeeded')
        ])

        self.cmd('deployment mg create --management-group-id {mg} --location WestUS --template-file "{tf}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

    def test_tenent_level_deployment_with_bicep(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'role_definition_deploy_tenant.bicep').replace('\\', '\\\\')
        })

        self.cmd('deployment tenant validate --location WestUS --template-file "{tf}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment tenant what-if --location WestUS --template-file "{tf}" --no-pretty-print', checks=[
            self.check('status', 'Succeeded')
        ])

        self.cmd('deployment tenant create --location WestUS --template-file "{tf}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_template_specs', location='westus')
    def test_create_template_specs_bicep(self, resource_group, resource_group_location):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_spec_name = self.create_random_name('cli-test-create-template-spec', 60)
        self.kwargs.update({
            'template_spec_name': template_spec_name,
            'tf': os.path.join(curr_dir, 'storage_account_deploy.bicep').replace('\\', '\\\\'),
            'resource_group_location': resource_group_location,
            'description': '"AzCLI test root template spec from bicep"',
            'version_description': '"AzCLI test version of root template spec from bicep"',
        })

        result = self.cmd('ts create -g {rg} -n {template_spec_name} -v 1.0 -l {resource_group_location} -f "{tf}" --description {description} --version-description {version_description}', checks=[
            self.check('location', "westus"),
            self.check('mainTemplate.functions', []),
            self.check("name", "1.0")
        ]).get_output_in_json()

        with self.assertRaises(IncorrectUsageError) as err:
            self.cmd('ts create --name {template_spec_name} -g {rg} -l {resource_group_location} --template-file "{tf}"')
            self.assertTrue("please provide --template-uri if --query-string is specified" in str(err.exception))

        # clean up
        self.kwargs['template_spec_id'] = result['id'].replace('/versions/1.0', '')
        self.cmd('ts delete --template-spec {template_spec_id} --yes')

if __name__ == '__main__':
    unittest.main()
