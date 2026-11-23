# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from azure.cli.core.mock import DummyCli
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class CognitiveServicesProjectArgumentTests(unittest.TestCase):

    def test_project_name_aliases_for_project_commands(self):
        """Verify project and project-connection commands expose both project-name options.

        For every command that accepts a project name, load its help and confirm it
        documents ``--project-name`` and ``-p``. Parse representative arguments with
        each spelling and check they populate the same project and account values.
        """
        prefix = ['cognitiveservices', 'account', 'project']
        cases = (
            ('create', ('--location', 'eastus')),
            ('delete', ()),
            ('show', ()),
            ('update', ()),
            ('connection create', ('--connection-name', 'my-conn', '--file', 'connection.json')),
            ('connection delete', ('--connection-name', 'my-conn')),
            ('connection show', ('--connection-name', 'my-conn')),
            ('connection list', ()),
            ('connection update', ('--connection-name', 'my-conn', '--set', 'properties.description=value')),
        )
        for suffix, extra_args in cases:
            with self.subTest(command=suffix):
                command = prefix + suffix.split()
                cli = DummyCli()
                output = io.StringIO()
                with mock.patch('azure.cli.core.extension.get_extensions', return_value=[]), \
                        redirect_stdout(output), redirect_stderr(output), self.assertRaises(SystemExit) as exc:
                    cli.invoke(command + ['--help'])

                self.assertEqual(exc.exception.code, 0, output.getvalue())
                self.assertRegex(output.getvalue(), r'(?m)^\s+--project-name\s+-p\b')
                parser = cli.invocation.parser.subparser_map[' '.join(command)]
                for option in ('--project-name', '-p'):
                    with self.subTest(option=option):
                        args = parser.parse_args(
                            ['-g', 'my-rg', '-n', 'my-account', option, 'my-project', *extra_args])
                        self.assertEqual(args.project_name, 'my-project')
                        self.assertEqual(args.account_name, 'my-account')

    def test_project_name_aliases_reach_sdk(self):
        """Verify either project-name option routes the selected project to the SDK.

        Invoke project update and project-connection create once with
        ``--project-name`` and once with ``-p``. Mock the management client and
        confirm each command succeeds and passes the expected project name and
        resource arguments to its SDK operation.
        """
        prefix = ['cognitiveservices', 'account', 'project']
        connection_file = os.path.join(
            TEST_DIR, 'data', 'cogsvc_connection_container_registry_managed_identity.yaml')
        cases = (
            (['update', '--description', 'changed'], 'projects', 'begin_update',
             ('my-rg', 'my-account', 'my-project')),
            (['connection', 'create', '--connection-name', 'my-conn', '--file', connection_file],
             'project_connections', 'create', ('my-rg', 'my-account', 'my-project', 'my-conn')),
        )
        for command, client_name, method_name, expected_args in cases:
            for option in ('--project-name', '-p'):
                with self.subTest(command=command, option=option):
                    cli = DummyCli()
                    output = io.StringIO()
                    with mock.patch(
                            'azure.cli.command_modules.cognitiveservices._client_factory.'
                            'get_cognitiveservices_management_client') as factory, \
                            mock.patch('azure.cli.core.extension.get_extensions', return_value=[]), \
                            redirect_stdout(output), redirect_stderr(output):
                        operation = getattr(getattr(factory.return_value, client_name), method_name)
                        operation.return_value = None
                        exit_code = cli.invoke(
                            prefix + command + ['-g', 'my-rg', '-n', 'my-account',
                                                option, 'my-project', '--output', 'none'])

                    self.assertEqual(exit_code, 0, output.getvalue())
                    operation.assert_called_once()
                    self.assertEqual(operation.call_args.args[:len(expected_args)], expected_args)


class CognitiveServicesProjectConnectionsTests(ScenarioTest):

    INPUT_DATA_PATH=os.path.join(TEST_DIR, 'data')
    
    @ResourceGroupPreparer()
    def test_project_connections_from_file(self, resource_group):

        sname = self.create_random_name(prefix='cog', length=12)
        pname = self.create_random_name(prefix='prj', length=12)
        connname = self.create_random_name(prefix='conn', length=12)
        customdomain = self.create_random_name(prefix='csclitest', length=16)
        
        conn_file = os.path.join(self.INPUT_DATA_PATH, 'cogsvc_connection_container_registry_managed_identity.yaml')
        self.kwargs.update({
            'sname': sname,
            'connname': connname,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus',
            'pname': pname,
            'customdomain': customdomain,
            'projdisplayname': 'CLI Test Project',            
            'connfile': conn_file
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes --assign-identity --allow-project-management true --custom-domain {customdomain}',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}'),
                         self.check('properties.allowProjectManagement', True),
                         self.check('properties.customSubDomainName', '{customdomain}')])

        prj = self.cmd('az cognitiveservices account project create -n {sname} -g {rg} -p {pname} --location {location} --assign-identity --display-name "{projdisplayname}"',
                            checks=[self.check('properties.provisioningState', 'Succeeded'),
                                    self.check('properties.displayName', '{projdisplayname}')]).get_output_in_json()

        acctprojs = self.cmd('az cognitiveservices account project list -n {sname} -g {rg}', checks=[
            self.check('length(@)', 1),
            self.check('[0].name', '{sname}/{pname}')
        ]).get_output_in_json()
        
        prj = self.cmd('az cognitiveservices account project update -n {sname} -g {rg} --project-name {pname} --description "{projdisplayname}"',
                            checks=[self.check('properties.provisioningState', 'Succeeded'),
                                    self.check('properties.description', '{projdisplayname}')]).get_output_in_json()

        acctconn = self.cmd('az cognitiveservices account project connection create -n {sname} -g {rg} -p {pname} --connection-name {connname} --file "{connfile}"',
                           checks=[
                               self.check('properties.authType', 'ManagedIdentity'),
                               self.check('properties.category', "ContainerRegistry"),
                               self.check('name', '{connname}')]).get_output_in_json()

        ret= self.cmd('az cognitiveservices account project connection list -n {sname} -g {rg} --project-name {pname}',
                                checks=[
                                    self.check('length(@)', 1)
                                ])
        self.assertEqual(ret.exit_code, 0)

        ret= self.cmd('az cognitiveservices account project connection show -n {sname} -g {rg} --project-name {pname} --connection-name {connname}')
        self.assertEqual(ret.exit_code, 0)
        
        # delete the cognitive services account
        ret= self.cmd('az cognitiveservices account project connection delete -n {sname} -g {rg} --project-name {pname} --connection-name {connname}')
        self.assertEqual(ret.exit_code, 0)
        ret= self.cmd('az cognitiveservices account project delete -n {sname} -g {rg} --project-name {pname}')
        self.assertEqual(ret.exit_code, 0)        
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
