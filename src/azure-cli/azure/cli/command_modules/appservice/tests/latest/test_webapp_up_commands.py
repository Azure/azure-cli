# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-few-public-methods

import unittest
import os
import requests

from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, JMESPathCheck, live_only)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
WINDOWS_ASP_LOCATION_WEBAPP = 'japanwest'
LINUX_ASP_LOCATION_WEBAPP = 'eastus2'


class WebAppUpE2ETests(ScenarioTest):
    @live_only()
    @ResourceGroupPreparer(random_name_length=24, name_prefix='clitest', location=LINUX_ASP_LOCATION_WEBAPP)
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
        self.assertEqual(result['sku'].lower(), 'premiumv2')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertEqual(result['runtime_version'].lower(), 'node|16-lts')
        self.assertEqual(result['os'].lower(), 'linux')

        # test the full E2E operation works
        full_result = self.cmd(
            'webapp up -n {} -g {} --plan {}'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['name'], full_result['name'])

        # Verify app is created
        # since we set local context, -n and -g are no longer required
        self.cmd('webapp show', checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('httpsOnly', True),
            JMESPathCheck('kind', 'app,linux'),
            JMESPathCheck('resourceGroup', resource_group)
        ])

        self.cmd('webapp config show', checks=[
            JMESPathCheck('linuxFxVersion', 'NODE|16-lts'),
            JMESPathCheck('tags.cli', 'None'),
        ])

        self.cmd('webapp config appsettings list', checks=[
            JMESPathCheck('[0].name', 'SCM_DO_BUILD_DURING_DEPLOYMENT'),
            JMESPathCheck('[0].value', 'True')
        ])

        self.cmd('appservice plan show', checks=[
            JMESPathCheck('properties.reserved', True),
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
    @ResourceGroupPreparer(random_name_length=24, name_prefix='clitest', location=LINUX_ASP_LOCATION_WEBAPP)
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
        self.assertEqual(result['sku'].lower(), 'standard')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertEqual(result['runtime_version'].lower(), 'python|3.7')
        self.assertEqual(result['os'].lower(), 'linux')

        # test the full E2E operation works
        full_result = self.cmd(
            'webapp up -n {} --sku  S1 -g {} --plan {}'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['name'], full_result['name'])

        # Verify app is created
        # since we set local context, -n and -g are no longer required
        self.cmd('webapp show', checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('httpsOnly', True),
            JMESPathCheck('kind', 'app,linux'),
            JMESPathCheck('resourceGroup', resource_group)
        ])

        self.cmd('webapp config show', checks=[
            JMESPathCheck('linuxFxVersion', 'PYTHON|3.7'),
            JMESPathCheck('tags.cli', 'None'),
        ])

        self.cmd('webapp config appsettings list', checks=[
            JMESPathCheck('[0].name', 'SCM_DO_BUILD_DURING_DEPLOYMENT'),
            JMESPathCheck('[0].value', 'True')
        ])

        # verify SKU and kind of ASP created
        self.cmd('appservice plan show', checks=[
            JMESPathCheck('properties.reserved', True),
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
    @ResourceGroupPreparer(random_name_length=24, name_prefix='clitest', location=WINDOWS_ASP_LOCATION_WEBAPP)
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
        self.assertEqual(result['sku'].lower(), 'free')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertEqual(result['runtime_version'].lower(), 'dotnetcore|3.1')
        self.assertEqual(result['os'].lower(), 'windows')
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
            JMESPathCheck('[0].name', 'SCM_DO_BUILD_DURING_DEPLOYMENT'),
            JMESPathCheck('[0].value', 'True')
        ])

        # verify SKU and kind of ASP created
        self.cmd('appservice plan show', checks=[
            JMESPathCheck('properties.reserved', False),
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
    @ResourceGroupPreparer(random_name_length=24, name_prefix='clitest', location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_webapp_up_dotnet6_e2e(self, resource_group):
        plan = self.create_random_name('up-dotnetplan', 24)
        webapp_name = self.create_random_name('up-dotnetapp', 24)
        zip_file_name = os.path.join(TEST_DIR, 'dotnet6-hello-up.zip')

        # create a temp directory and unzip the code to this folder
        import zipfile
        import tempfile
        temp_dir = tempfile.mkdtemp()
        zip_ref = zipfile.ZipFile(zip_file_name, 'r')
        zip_ref.extractall(temp_dir)
        current_working_dir = os.getcwd()

        # change the working dir to the dir where the code has been extracted to
        up_working_dir = temp_dir
        os.chdir(up_working_dir)

        # test dryrun operation
        result = self.cmd('webapp up -n {} --dryrun --os-type Linux'
                          .format(webapp_name)).get_output_in_json()
        self.assertEqual(result['sku'].lower(), 'free')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertEqual(result['runtime_version'].lower(), 'dotnetcore|3.1')
        self.assertEqual(result['os'].lower(), 'linux')
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
            JMESPathCheck('[0].name', 'SCM_DO_BUILD_DURING_DEPLOYMENT'),
            JMESPathCheck('[0].value', 'True')
        ])

        # verify SKU and kind of ASP created
        self.cmd('appservice plan show', checks=[
            JMESPathCheck('properties.reserved', False),
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
    @ResourceGroupPreparer(random_name_length=24, name_prefix='clitest', location=WINDOWS_ASP_LOCATION_WEBAPP)
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
        self.assertEqual(result['sku'].lower(), 'free')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertEqual(result['runtime_version'].lower(), '-')
        self.assertEqual(result['os'].lower(), 'windows')

        # test the full E2E operation works
        full_result = self.cmd(
            'webapp up -n {} -g {} --plan {} --html'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['name'], full_result['name'])

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
            JMESPathCheck('properties.reserved', False),
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
    @ResourceGroupPreparer(random_name_length=24, name_prefix='clitest', location=LINUX_ASP_LOCATION_WEBAPP)
    def test_webapp_up_invalid_name(self, resource_group):
        webapp_name = self.create_random_name('invalid_name', 40)
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

        from azure.cli.core.util import CLIError
        with self.assertRaises(CLIError):
            self.cmd('webapp up -n {} --dryrun'.format(webapp_name))
        with self.assertRaises(CLIError):
            self.cmd('webapp up -n {}'.format(webapp_name))

        # cleanup
        # switch back the working dir
        os.chdir(current_working_dir)
        # delete temp_dir
        import shutil
        shutil.rmtree(temp_dir)

    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=24, name_prefix='clitest', location=LINUX_ASP_LOCATION_WEBAPP)
    def test_webapp_up_name_exists_not_in_subscription(self, resource_group):
        # Make sure webapp_name is the name of an existing web app and is not in your subscription
        webapp_name = 'helloworld'
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

        from azure.cli.core.util import CLIError
        with self.assertRaises(CLIError):
            self.cmd('webapp up -n {} --dryrun'.format(webapp_name))
        with self.assertRaises(CLIError):
            self.cmd('webapp up -n {}'.format(webapp_name))

        # cleanup
        # switch back the working dir
        os.chdir(current_working_dir)
        # delete temp_dir
        import shutil
        shutil.rmtree(temp_dir)

    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=24, name_prefix='clitest', location=LINUX_ASP_LOCATION_WEBAPP)
    def test_webapp_up_name_exists_in_subscription(self, resource_group):
        plan = self.create_random_name('up-name-exists-plan', 40)
        webapp_name = self.create_random_name('up-name-exists-app', 40)
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

        # create a webapp with the same name
        self.cmd(
            'appservice plan create -g {} -n {} --sku S1 --is-linux'.format(resource_group, plan))
        self.cmd(
            'webapp create -g {} -n {} --plan {} -r "python|3.7"'.format(resource_group, webapp_name, plan))
        requests.get('http://{}.azurewebsites.net'.format(webapp_name), timeout=240)
        self.cmd('webapp up -n {}'.format(webapp_name))
        self.cmd('webapp list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', webapp_name),
            JMESPathCheck('[0].hostNames[0]', webapp_name +
                          '.azurewebsites.net')
        ])

        # test dryrun operation
        result = self.cmd('webapp up -n {} --sku S1 --dryrun'
                          .format(webapp_name)).get_output_in_json()
        self.assertEqual(result['sku'].lower(), 'standard')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertEqual(result['runtime_version'], 'python|3.7')
        self.assertEqual(result['os'].lower(), 'linux')

        # test the full E2E operation works
        full_result = self.cmd(
            'webapp up -n {} --sku S1 -g {} --plan {}'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['name'], full_result['name'])

        # cleanup
        # switch back the working dir
        os.chdir(current_working_dir)
        # delete temp_dir
        import shutil
        shutil.rmtree(temp_dir)

    @live_only()
    @ResourceGroupPreparer(random_name_length=24, name_prefix='clitest', location=LINUX_ASP_LOCATION_WEBAPP)
    def test_webapp_up_choose_os(self, resource_group):
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
            'webapp up -n {} -g {} --plan {} --os-type "linux" --dryrun'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['sku'].lower(), 'premiumv2')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertEqual(result['runtime_version'].lower(), 'node|16-lts')
        self.assertEqual(result['os'].lower(), 'linux')

        # test the full E2E operation works
        full_result = self.cmd(
            'webapp up -n {} -g {} --plan {} --os-type "linux"'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['name'], full_result['name'])

        # Verify app is created
        # since we set local context, -n and -g are no longer required
        self.cmd('webapp show', checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('httpsOnly', True),
            JMESPathCheck('kind', 'app,linux'),
            JMESPathCheck('resourceGroup', resource_group)
        ])

        self.cmd('webapp config show', checks=[
            JMESPathCheck('tags.cli', 'None')
        ])

        self.cmd('webapp config appsettings list', checks=[
            JMESPathCheck('[0].name', 'SCM_DO_BUILD_DURING_DEPLOYMENT'),
            JMESPathCheck('[0].value', 'True')
        ])

        self.cmd('appservice plan show', checks=[
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
    @ResourceGroupPreparer(random_name_length=24, name_prefix='clitest', location=LINUX_ASP_LOCATION_WEBAPP)
    def test_webapp_up_choose_runtime(self, resource_group):
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
        result = self.cmd(
            'webapp up -n {} -g {} --plan {} --runtime "PYTHON|3.7" --sku S1 --dryrun'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['sku'].lower(), 'standard')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertEqual(result['runtime_version'].lower(), 'python|3.7')
        self.assertEqual(result['os'].lower(), 'linux')

        # test the full E2E operation works
        full_result = self.cmd(
            'webapp up -n {} -g {} --plan {} --runtime "PYTHON|3.7" --sku "S1"'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['name'], full_result['name'])

        # Verify app is created
        # since we set local context, -n and -g are no longer required
        self.cmd('webapp show', checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('httpsOnly', True),
            JMESPathCheck('kind', 'app,linux'),
            JMESPathCheck('resourceGroup', resource_group)
        ])

        self.cmd('webapp config show', checks=[
            JMESPathCheck('linuxFxVersion', 'PYTHON|3.6'),
            JMESPathCheck('tags.cli', 'None')
        ])

        self.cmd('webapp config appsettings list', checks=[
            JMESPathCheck('[0].name', 'SCM_DO_BUILD_DURING_DEPLOYMENT'),
            JMESPathCheck('[0].value', 'True')
        ])

        self.cmd('appservice plan show', checks=[
            JMESPathCheck('properties.reserved', True),
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
    @ResourceGroupPreparer(random_name_length=24, name_prefix='clitest', location=LINUX_ASP_LOCATION_WEBAPP)
    def test_webapp_up_choose_os_and_runtime(self, resource_group):
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
            'webapp up -n {} -g {} --plan {} --os "linux" --runtime "node|12-lts" --sku "S1" --dryrun'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['sku'].lower(), 'standard')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertEqual(result['runtime_version'].lower(), 'node|12-lts')
        self.assertEqual(result['os'].lower(), 'linux')

        # test the full E2E operation works
        full_result = self.cmd(
            'webapp up -n {} -g {} --plan {} --os "linux" --runtime "node|12-lts" --sku "S1"'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['name'], full_result['name'])

        # Verify app is created
        # since we set local context, -n and -g are no longer required
        self.cmd('webapp show', checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('httpsOnly', True),
            JMESPathCheck('kind', 'app,linux'),
            JMESPathCheck('resourceGroup', resource_group)
        ])

        self.cmd('webapp config show', checks=[
            JMESPathCheck('tags.cli', 'None')
        ])

        self.cmd('webapp config appsettings list', checks=[
            JMESPathCheck('[0].name', 'SCM_DO_BUILD_DURING_DEPLOYMENT'),
            JMESPathCheck('[0].value', 'True')
        ])

        self.cmd('appservice plan show', checks=[
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
    @ResourceGroupPreparer(random_name_length=24, name_prefix='clitest', location=LINUX_ASP_LOCATION_WEBAPP)
    def test_webapp_up_runtime_delimiters(self, resource_group):
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
            'webapp up -n {} -g {} --plan {} --os "windows" --runtime "java|1.8|Java SE|8" --sku "S1" --dryrun'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['sku'].lower(), 'standard')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertEqual(result['runtime_version'].lower(), 'java|1.8|Java se|8')

        # test dryrun operation
        result = self.cmd(
            'webapp up -n {} -g {} --plan {} --os "windows" --runtime "java:1.8:Java SE:8" --sku "S1" --dryrun'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['sku'].lower(), 'standard')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertEqual(result['runtime_version'].lower(), 'java|1.8|Java se|8')

        # cleanup
        # switch back the working dir
        os.chdir(current_working_dir)
        # delete temp_dir
        import shutil
        shutil.rmtree(temp_dir)

    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=24, name_prefix='clitest', location=LINUX_ASP_LOCATION_WEBAPP)
    def test_linux_to_windows_fail(self, resource_group):
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
            'webapp up -n {} -g {} --plan {} --os "linux" --runtime "node|12-lts" --sku "S1" --dryrun'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['sku'].lower(), 'standard')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertEqual(result['runtime_version'].lower(), 'node|12-lts')
        self.assertEqual(result['os'].lower(), 'linux')

        # test the full E2E operation works
        full_result = self.cmd(
            'webapp up -n {} -g {} --plan {} --os "linux" --runtime "node|12-lts" --sku "S1"'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['name'], full_result['name'])

        # Verify app is created
        # since we set local context, -n and -g are no longer required
        self.cmd('webapp show', checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('httpsOnly', True),
            JMESPathCheck('kind', 'app,linux'),
            JMESPathCheck('resourceGroup', resource_group)
        ])

        from azure.cli.core.util import CLIError
        # changing existing linux app to windows should fail gracefully
        with self.assertRaises(CLIError):
            self.cmd('webapp up -n {} -g {} --plan {} --os "windows" --runtime "node|12LTS" --sku "S1"'.format(webapp_name, resource_group, plan))

        # cleanup
        # switch back the working dir
        os.chdir(current_working_dir)
        # delete temp_dir
        import shutil
        shutil.rmtree(temp_dir)

    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=24, name_prefix='clitest', location=WINDOWS_ASP_LOCATION_WEBAPP)
    def test_windows_to_linux_fail(self, resource_group):
        plan = self.create_random_name('up-nodeplan', 24)
        webapp_name = self.create_random_name('up-nodeapp', 24)
        zip_file_name = os.path.join(TEST_DIR, 'node-Express-up-windows.zip')

        # create a temp directory and unzip the code to this folder
        import zipfile
        import tempfile
        temp_dir = tempfile.mkdtemp()
        zip_ref = zipfile.ZipFile(zip_file_name, 'r')
        zip_ref.extractall(temp_dir)
        current_working_dir = os.getcwd()

        # change the working dir to the dir where the code has been extracted to
        up_working_dir = os.path.join(temp_dir, 'myExpressApp')
        os.chdir(temp_dir)

        # test dryrun operation
        result = self.cmd(
            'webapp up -n {} -g {} --plan {} --os "windows" --runtime "node|12LTS" --sku "S1" --dryrun'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['sku'].lower(), 'standard')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertEqual(result['runtime_version'].lower(), 'node|12LTS')
        self.assertEqual(result['os'].lower(), 'windows')

        # test the full E2E operation works
        full_result = self.cmd(
            'webapp up -n {} -g {} --plan {} --os "windows" --runtime "node|12LTS" --sku "S1"'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['name'], full_result['name'])

        # Verify app is created
        # since we set local context, -n and -g are no longer required
        self.cmd('webapp show', checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('httpsOnly', True),
            JMESPathCheck('kind', 'app'),
            JMESPathCheck('resourceGroup', resource_group)
        ])

        from azure.cli.core.util import CLIError
        # changing existing linux app to windows should fail gracefully
        with self.assertRaises(CLIError):
            self.cmd('webapp up -n {} -g {} --plan {} --os "linux" --runtime "node|12-LTS" --sku "S1"'.format(webapp_name, resource_group, plan))

        # cleanup
        # switch back the working dir
        os.chdir(current_working_dir)
        # delete temp_dir
        import shutil
        shutil.rmtree(temp_dir)

    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(random_name_length=24, name_prefix='clitest', location=LINUX_ASP_LOCATION_WEBAPP)
    def test_webapp_up_change_runtime_version(self, resource_group):
        plan = self.create_random_name('up-nodeplan', 24)
        webapp_name = self.create_random_name('up-nodeapp', 24)
        zip_file_name = os.path.join(TEST_DIR, 'node-Express-up.zip')

        # create a temp directory and unzip the code to this folder
        import zipfile
        import tempfile
        import time
        temp_dir = tempfile.mkdtemp()
        zip_ref = zipfile.ZipFile(zip_file_name, 'r')
        zip_ref.extractall(temp_dir)
        current_working_dir = os.getcwd()

        # change the working dir to the dir where the code has been extracted to
        up_working_dir = os.path.join(temp_dir, 'myExpressApp')
        os.chdir(up_working_dir)

        # test dryrun operation
        result = self.cmd(
            'webapp up -n {} -g {} --plan {} --os "linux" --runtime "node|12-LTS" --sku "S1" --dryrun'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['sku'].lower(), 'standard')
        self.assertTrue(result['name'].startswith(webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertEqual(result['runtime_version'].lower(), 'node|12-lts')
        self.assertEqual(result['os'].lower(), 'linux')

        # test the full E2E operation works
        full_result = self.cmd(
            'webapp up -n {} -g {} --plan {} --os "linux" --runtime "node|12-LTS" --sku "S1"'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['name'], full_result['name'])

        # Verify app is created
        # since we set local context, -n and -g are no longer required
        self.cmd('webapp show', checks=[
            JMESPathCheck('name', webapp_name),
            JMESPathCheck('httpsOnly', True),
            JMESPathCheck('kind', 'app,linux'),
            JMESPathCheck('resourceGroup', resource_group)
        ])

        # test changing runtime to newer version
        time.sleep(30)
        full_result = self.cmd(
            'webapp up -n {} -g {} --plan {} --os "linux" --runtime "node|16-lts" --sku "S1"'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['name'], full_result['name'])

        # verify newer version
        self.cmd('webapp config show', checks=[
            JMESPathCheck('linuxFxVersion', "NODE|16-lts"),
            JMESPathCheck('tags.cli', 'None')
        ])

        # test changing runtime to older version
        time.sleep(30)
        full_result = self.cmd(
            'webapp up -n {} -g {} --plan {} --os "linux" --runtime "node|12-lts" --sku "S1"'.format(webapp_name, resource_group, plan)).get_output_in_json()
        self.assertEqual(result['name'], full_result['name'])

        # verify older version
        self.cmd('webapp config show', checks=[
            JMESPathCheck('linuxFxVersion', "NODE|12-lts"),
            JMESPathCheck('tags.cli', 'None')
        ])

        # cleanup
        # switch back the working dir
        os.chdir(current_working_dir)
        # delete temp_dir
        import shutil
        shutil.rmtree(temp_dir)

    @live_only()
    @ResourceGroupPreparer(random_name_length=24, name_prefix='clitest', location=LINUX_ASP_LOCATION_WEBAPP)
    def test_webapp_up_generate_default_name(self, resource_group):
        plan = self.create_random_name('up-nodeplan', 24)
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
            'webapp up --dryrun').get_output_in_json()
        self.assertEqual(result['sku'].lower(), 'premiumv2')
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertEqual(result['runtime_version'].lower(), 'node|16-lts')
        self.assertEqual(result['os'].lower(), 'linux')

        # test the full E2E operation works
        self.cmd(
            'webapp up -g {} --plan {}'.format(resource_group, plan)).get_output_in_json()

        # Verify app is created
        # since we set local context, -n and -g are no longer required
        self.cmd('webapp show', checks=[
            JMESPathCheck('httpsOnly', True),
            JMESPathCheck('kind', 'app,linux'),
            JMESPathCheck('resourceGroup', resource_group)
        ])

        self.cmd('webapp config show', checks=[
            JMESPathCheck('linuxFxVersion', 'NODE|16-lts'),
            JMESPathCheck('tags.cli', 'None'),
        ])

        self.cmd('webapp config appsettings list', checks=[
            JMESPathCheck('[0].name', 'SCM_DO_BUILD_DURING_DEPLOYMENT'),
            JMESPathCheck('[0].value', 'True')
        ])

        self.cmd('appservice plan show', checks=[
            JMESPathCheck('properties.reserved', True),
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
    @ResourceGroupPreparer(random_name_length=24, name_prefix='clitest', location=LINUX_ASP_LOCATION_WEBAPP)
    def test_webapp_up_linux_windows_sharing_resource_group(self, resource_group):
        linux_plan = self.create_random_name('plan-linux', 24)
        linux_webapp_name = self.create_random_name('app-linux', 24)
        windows_plan = self.create_random_name('plan-windows', 26)
        windows_webapp_name = self.create_random_name('app-windows', 26)
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

        # test linux dryrun operation
        result = self.cmd('webapp up -n {} --sku  S1 --dryrun'
                          .format(linux_webapp_name)).get_output_in_json()
        self.assertEqual(result['sku'].lower(), 'standard')
        self.assertTrue(result['name'].startswith(linux_webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertEqual(result['runtime_version'].lower(), 'node|14lts')
        self.assertEqual(result['os'].lower(), 'linux')

        # test the full linux E2E operation works
        full_result = self.cmd(
            'webapp up -n {} --sku  S1 -g {} --plan {} --os-type linux'.format(linux_webapp_name, resource_group, linux_plan)).get_output_in_json()
        self.assertEqual(result['name'], full_result['name'])

        # Verify linux app is created
        # since we set local context, -n and -g are no longer required
        self.cmd('webapp show', checks=[
            JMESPathCheck('name', linux_webapp_name),
            JMESPathCheck('httpsOnly', True),
            JMESPathCheck('kind', 'app,linux'),
            JMESPathCheck('resourceGroup', resource_group)
        ])

        self.cmd('webapp config show', checks=[
            JMESPathCheck('linuxFxVersion', 'NODE|16-lts'),
            JMESPathCheck('tags.cli', 'None'),
        ])

        self.cmd('webapp config appsettings list', checks=[
            JMESPathCheck('[0].name', 'SCM_DO_BUILD_DURING_DEPLOYMENT'),
            JMESPathCheck('[0].value', 'True')
        ])

        # test windows dryrun operation
        result = self.cmd("webapp up -n {} --sku  S1 --dryrun -r 'node|10.14' --os-type windows --plan {}"
                          .format(windows_webapp_name, windows_plan)).get_output_in_json()
        self.assertEqual(result['sku'].lower(), 'standard')
        self.assertTrue(result['name'].startswith(windows_webapp_name))
        self.assertTrue(result['src_path'].replace(
            os.sep + os.sep, os.sep), up_working_dir)
        self.assertEqual(result['runtime_version'].lower(), 'node|14LTS')
        self.assertEqual(result['os'].lower(), 'windows')

        # test the full windows E2E operation works
        full_result = self.cmd(
            'webapp up -n {} --sku  S1 -g {} --plan {}'.format(windows_webapp_name, resource_group, windows_plan)).get_output_in_json()
        self.assertEqual(result['name'], full_result['name'])

        # Verify windows app is created
        self.cmd('webapp show -g {} -n {}'.format(resource_group, windows_webapp_name), checks=[
            JMESPathCheck('name', windows_webapp_name),
            JMESPathCheck('httpsOnly', True),
            JMESPathCheck('resourceGroup', resource_group)
        ])

        # verify windows SKU and kind of ASP created
        self.cmd('appservice plan show', checks=[
            JMESPathCheck('properties.reserved', True),
            JMESPathCheck('name', windows_plan),
            JMESPathCheck('sku.tier', 'Standard'),
            JMESPathCheck('sku.name', 'S1')
        ])


        # cleanup
        # switch back the working dir
        os.chdir(current_working_dir)
        # delete temp_dir
        import shutil
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()
