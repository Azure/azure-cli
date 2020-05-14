# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-few-public-methods

import unittest
import os

from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, JMESPathCheck, live_only)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class WebAppUpE2ETests(ScenarioTest):
    @live_only()
    @ResourceGroupPreparer()
    def test_webapp_up_node_e2e(self, resource_group):
        plan = self.create_random_name('up-nodeplan', 24)
        webapp_name = self.create_random_name('up-nodeapp', 24)
        zip_file_name = os.path.join(TEST_DIR, 'node-Express-up.zip')

        # create a temp directory and unzip the code to this folder
        import zipfile
        import tempfile
        temp_dir = tempfile.mkdtemp()
        zip_ref = zipfile.ZipFile(zip_file_name, 'r')
        zip_ref.extractall(temp_dir)
        current_working_dir = os.getcwd()

        # change the working dir to the dir where the code has been extracted to
        up_working_dir = os.path.join(temp_dir, 'myExpressApp')
        os.chdir(up_working_dir)

        # test dryrun operation
        result = self.cmd(
            'webapp up -n {} --dryrun'.format(webapp_name)).get_output_in_json()
        self.assertTrue(result['sku'].lower() == 'premiumv2')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertTrue(result['runtime_version'] == 'node|10.14')
        self.assertTrue(result['os'].lower() == 'linux')

        # test the full E2E operation works
        full_result = self.cmd(
            'webapp up -n {} -g {} --plan {}'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertTrue(result['name'] == full_result['name'])

        # Verify app is created
        # since we set local context, -n and -g are no longer required
        self.cmd('webapp show', checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('httpsOnly', True),
            JMESPathCheck('kind', 'app,linux'),
            JMESPathCheck('resourceGroup', resource_group)
        ])

        self.cmd('webapp config show', checks=[
            JMESPathCheck('linuxFxVersion', result['runtime_version']),
            JMESPathCheck('tags.cli', 'None'),
        ])

        self.cmd('webapp config appsettings list', checks=[
            JMESPathCheck('[0].name', 'SCM_DO_BUILD_DURING_DEPLOYMENT'),
            JMESPathCheck('[0].value', 'True')
        ])

        self.cmd('appservice plan show', checks=[
            JMESPathCheck('reserved', True),
            JMESPathCheck('name', plan),
            JMESPathCheck('sku.tier', 'PremiumV2'),
            JMESPathCheck('sku.name', 'P1v2')
        ])

        # cleanup
        # switch back the working dir
        os.chdir(current_working_dir)
        # delete temp_dir
        import shutil
        shutil.rmtree(temp_dir)

    @live_only()
    @ResourceGroupPreparer()
    def test_webapp_up_python_e2e(self, resource_group):
        plan = self.create_random_name('up-pythonplan', 24)
        webapp_name = self.create_random_name('up-pythonapp', 24)
        zip_file_name = os.path.join(TEST_DIR, 'python-hello-world-up.zip')

        # create a temp directory and unzip the code to this folder
        import zipfile
        import tempfile
        temp_dir = tempfile.mkdtemp()
        zip_ref = zipfile.ZipFile(zip_file_name, 'r')
        zip_ref.extractall(temp_dir)
        current_working_dir = os.getcwd()

        # change the working dir to the dir where the code has been extracted to
        up_working_dir = os.path.join(temp_dir, 'python-docs-hello-world')
        os.chdir(up_working_dir)

        # test dryrun operation
        result = self.cmd('webapp up -n {} --sku  S1 --dryrun'
                          .format(webapp_name)).get_output_in_json()
        self.assertTrue(result['sku'].lower() == 'standard')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertTrue(result['runtime_version'] == 'python|3.7')
        self.assertTrue(result['os'].lower() == 'linux')

        # test the full E2E operation works
        full_result = self.cmd(
            'webapp up -n {} --sku  S1 -g {} --plan {}'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertTrue(result['name'] == full_result['name'])

        # Verify app is created
        # since we set local context, -n and -g are no longer required
        self.cmd('webapp show', checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('httpsOnly', True),
            JMESPathCheck('kind', 'app,linux'),
            JMESPathCheck('resourceGroup', resource_group)
        ])

        self.cmd('webapp config show', checks=[
            JMESPathCheck('linuxFxVersion', result['runtime_version']),
            JMESPathCheck('tags.cli', 'None'),
        ])

        self.cmd('webapp config appsettings list', checks=[
            JMESPathCheck('[0].name', 'SCM_DO_BUILD_DURING_DEPLOYMENT'),
            JMESPathCheck('[0].value', 'True')
        ])

        # verify SKU and kind of ASP created
        self.cmd('appservice plan show', checks=[
            JMESPathCheck('reserved', True),
            JMESPathCheck('name', plan),
            JMESPathCheck('sku.tier', 'Standard'),
            JMESPathCheck('sku.name', 'S1')
        ])

        # cleanup
        # switch back the working dir
        os.chdir(current_working_dir)
        # delete temp_dir
        import shutil
        shutil.rmtree(temp_dir)

    @live_only()
    @ResourceGroupPreparer()
    def test_webapp_up_dotnetcore_e2e(self, resource_group):
        plan = self.create_random_name('up-dotnetcoreplan', 24)
        webapp_name = self.create_random_name('up-dotnetcoreapp', 24)
        zip_file_name = os.path.join(TEST_DIR, 'dotnetcore-hello-up.zip')

        # create a temp directory and unzip the code to this folder
        import zipfile
        import tempfile
        temp_dir = tempfile.mkdtemp()
        zip_ref = zipfile.ZipFile(zip_file_name, 'r')
        zip_ref.extractall(temp_dir)
        current_working_dir = os.getcwd()

        # change the working dir to the dir where the code has been extracted to
        up_working_dir = os.path.join(temp_dir, 'hellodotnetcore')
        os.chdir(up_working_dir)

        # test dryrun operation
        result = self.cmd('webapp up -n {} --dryrun'
                          .format(webapp_name)).get_output_in_json()
        self.assertTrue(result['sku'].lower() == 'free')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertTrue(result['runtime_version'] == 'dotnetcore|2.2')
        self.assertTrue(result['os'].lower() == 'windows')
        self.assertNotEqual(result['location'], 'None')

        # test the full E2E operation works
        full_result = self.cmd(
            'webapp up -n {} -g {} --plan {}'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['name'], full_result['name'])
        self.assertEqual(result['location'], full_result['location'])

        # Verify app is created
        # since we set local context, -n and -g are no longer required
        self.cmd('webapp show', checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('httpsOnly', True),
            JMESPathCheck('kind', 'app'),
            JMESPathCheck('resourceGroup', resource_group)
        ])

        self.cmd('webapp config show', checks=[
            JMESPathCheck('tags.cli', 'None'),
            JMESPathCheck('windowsFxVersion', None)
        ])

        self.cmd('webapp config appsettings list', checks=[
            JMESPathCheck('[1].name', 'SCM_DO_BUILD_DURING_DEPLOYMENT'),
            JMESPathCheck('[1].value', 'True')
        ])

        # verify SKU and kind of ASP created
        self.cmd('appservice plan show', checks=[
            JMESPathCheck('reserved', False),
            JMESPathCheck('name', plan),
            JMESPathCheck('sku.tier', 'Free'),
            JMESPathCheck('sku.name', 'F1')
        ])

        # cleanup
        # switch back the working dir
        os.chdir(current_working_dir)
        # delete temp_dir
        import shutil
        shutil.rmtree(temp_dir)

    @live_only()
    @ResourceGroupPreparer()
    def test_webapp_up_statichtml_e2e(self, resource_group):
        plan = self.create_random_name('up-statichtmlplan', 24)
        webapp_name = self.create_random_name('up-statichtmlapp', 24)
        zip_file_name = os.path.join(
            TEST_DIR, 'html-static-hello-world-up.zip')

        # create a temp directory and unzip the code to this folder
        import zipfile
        import tempfile
        temp_dir = tempfile.mkdtemp()
        zip_ref = zipfile.ZipFile(zip_file_name, 'r')
        zip_ref.extractall(temp_dir)
        current_working_dir = os.getcwd()

        # change the working dir to the dir where the code has been extracted to
        up_working_dir = os.path.join(temp_dir, 'html-docs-hello-world-master')
        os.chdir(up_working_dir)

        # test dryrun operation
        result = self.cmd('webapp up -n {} --dryrun --html'
                          .format(webapp_name)).get_output_in_json()
        self.assertTrue(result['sku'].lower() == 'free')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertTrue(result['runtime_version'] == '-')
        self.assertTrue(result['os'].lower() == 'windows')

        # test the full E2E operation works
        full_result = self.cmd(
            'webapp up -n {} -g {} --plan {} --html'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertTrue(result['name'] == full_result['name'])

        # Verify app is created
        # since we set local context, -n and -g are no longer required
        self.cmd('webapp show', checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('httpsOnly', True),
            JMESPathCheck('kind', 'app'),
            JMESPathCheck('resourceGroup', resource_group)
        ])

        self.cmd('webapp config show', checks=[
            JMESPathCheck('tags.cli', 'None'),
            JMESPathCheck('windowsFxVersion', None)
        ])

        self.cmd('webapp config appsettings list', checks=[
            JMESPathCheck('[1].name', 'SCM_DO_BUILD_DURING_DEPLOYMENT'),
            JMESPathCheck('[1].value', 'True')
        ])

        # verify SKU and kind of ASP created
        self.cmd('appservice plan show', checks=[
            JMESPathCheck('reserved', False),
            JMESPathCheck('name', plan),
            JMESPathCheck('sku.tier', 'Free'),
            JMESPathCheck('sku.name', 'F1')
        ])

        # cleanup
        # switch back the working dir
        os.chdir(current_working_dir)
        # delete temp_dir
        import shutil
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()
