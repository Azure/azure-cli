# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Tests for Azure CLI cognitiveservices agent commands.

IMPORTANT NOTE FOR LOCAL TESTING:
=====================================
Integration tests (CognitiveServicesAgentTests class) are decorated with @live_only()
and will be SKIPPED when run locally without the AZURE_TEST_RUN_LIVE environment variable.

Unit tests (CognitiveServicesAgentHelperTests class) do NOT require Azure resources and will
always run locally.

To run tests locally:
- Unit tests only (default): azdev test cognitiveservices.test_agent::CognitiveServicesAgentHelperTests
- All tests (unit only): azdev test cognitiveservices.test_agent
- Integration tests (live): AZURE_TEST_RUN_LIVE=True azdev test cognitiveservices.test_agent

Integration tests require:
- AZURE_TEST_RUN_LIVE=True environment variable
- Valid Azure subscription and service principal
- Live Cognitive Services accounts
- Live Azure Container Registry resources
- Network connectivity to Azure services

Expected test behavior:
- ✅ Unit tests (9): Always run and SHOULD PASS
- ⏭️  Integration tests (8): SKIPPED locally unless AZURE_TEST_RUN_LIVE=True
- ✅ Integration tests: PASS in CI/CD with live Azure resources

The @live_only() decorator ensures integration tests are automatically skipped in local
development without proper Azure infrastructure, eliminating confusing test failures.
"""

import unittest
import os
import tempfile
import shutil

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.decorators import serial_test
from azure.cli.testsdk.scenario_tests.decorators import live_only
from knack.util import CLIError

from azure.cli.command_modules.cognitiveservices.custom import _extract_version_from_image, _has_dockerfile, _is_docker_running
from azure.cli.command_modules.cognitiveservices._params import _environment_variables_type


class CognitiveServicesAgentHelperTests(unittest.TestCase):
    """Unit tests for agent helper functions."""
    
    def test_extract_version_from_image_valid(self):
        """Test version extraction from valid image URIs."""
        # Full ACR URI with version
        self.assertEqual(
            _extract_version_from_image('myregistry.azurecr.io/myagent:v1.0'),
            'v1.0'
        )
        
        # Short image name with version
        self.assertEqual(
            _extract_version_from_image('myagent:v2.5'),
            'v2.5'
        )
        
        # Version with special characters
        self.assertEqual(
            _extract_version_from_image('myregistry.azurecr.io/myagent:v1.0-beta'),
            'v1.0-beta'
        )
        
        # Numeric version
        self.assertEqual(
            _extract_version_from_image('myagent:123'),
            '123'
        )
        
        # Latest tag
        self.assertEqual(
            _extract_version_from_image('myregistry.azurecr.io/myagent:latest'),
            'latest'
        )
    
    def test_extract_version_from_image_invalid(self):
        """Test version extraction error handling."""
        # Missing tag
        with self.assertRaises(CLIError) as context:
            _extract_version_from_image('myregistry.azurecr.io/myagent')
        self.assertIn('must include a', str(context.exception).lower())
        
        # Empty tag
        with self.assertRaises(CLIError) as context:
            _extract_version_from_image('myagent:')
        self.assertIn('must include a', str(context.exception).lower())
    
    def test_environment_variables_type_valid(self):
        """Test environment variable parsing with valid inputs."""
        # Simple key=value
        result = _environment_variables_type('FOO=bar')
        self.assertEqual(result['key'], 'FOO')
        self.assertEqual(result['value'], 'bar')
        
        # Value with equals sign
        result = _environment_variables_type('CONNECTION_STRING=Server=localhost;Database=mydb')
        self.assertEqual(result['key'], 'CONNECTION_STRING')
        self.assertEqual(result['value'], 'Server=localhost;Database=mydb')
        
        # Empty value
        result = _environment_variables_type('EMPTY=')
        self.assertEqual(result['key'], 'EMPTY')
        self.assertEqual(result['value'], '')
        
        # Value with spaces
        result = _environment_variables_type('MESSAGE=Hello World')
        self.assertEqual(result['key'], 'MESSAGE')
        self.assertEqual(result['value'], 'Hello World')
        
        # Numeric value
        result = _environment_variables_type('PORT=8080')
        self.assertEqual(result['key'], 'PORT')
        self.assertEqual(result['value'], '8080')
    
    def test_environment_variables_type_invalid(self):
        """Test environment variable parsing error handling."""
        # Missing equals sign
        with self.assertRaises(ValueError) as context:
            _environment_variables_type('INVALID')
        self.assertIn("must be in 'key=value' format", str(context.exception))
        
        # Empty key
        with self.assertRaises(ValueError) as context:
            _environment_variables_type('=value')
        self.assertIn('key cannot be empty', str(context.exception))
    
    def test_has_dockerfile_exists(self):
        """Test _has_dockerfile when Dockerfile exists."""
        # Create temporary directory with a Dockerfile
        temp_dir = tempfile.mkdtemp()
        try:
            dockerfile_path = os.path.join(temp_dir, 'Dockerfile')
            with open(dockerfile_path, 'w') as f:
                f.write('FROM python:3.11\n')
            
            # Should return True when Dockerfile exists
            self.assertTrue(_has_dockerfile(temp_dir))
            self.assertTrue(_has_dockerfile(temp_dir, 'Dockerfile'))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_has_dockerfile_not_exists(self):
        """Test _has_dockerfile when Dockerfile doesn't exist."""
        # Create temporary directory without a Dockerfile
        temp_dir = tempfile.mkdtemp()
        try:
            # Should return False when Dockerfile doesn't exist
            self.assertFalse(_has_dockerfile(temp_dir))
            self.assertFalse(_has_dockerfile(temp_dir, 'Dockerfile'))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_has_dockerfile_custom_name(self):
        """Test _has_dockerfile with custom Dockerfile name."""
        # Create temporary directory with a custom-named Dockerfile
        temp_dir = tempfile.mkdtemp()
        try:
            dockerfile_path = os.path.join(temp_dir, 'Dockerfile.prod')
            with open(dockerfile_path, 'w') as f:
                f.write('FROM python:3.11\n')
            
            # Should return False for default name
            self.assertFalse(_has_dockerfile(temp_dir, 'Dockerfile'))
            
            # Should return True for custom name
            self.assertTrue(_has_dockerfile(temp_dir, 'Dockerfile.prod'))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_has_dockerfile_invalid_dir(self):
        """Test _has_dockerfile with invalid directory."""
        # Should return False for non-existent directory
        self.assertFalse(_has_dockerfile('/nonexistent/directory'))
        self.assertFalse(_has_dockerfile(None))
    
    def test_is_docker_running(self):
        """Test _is_docker_running (result depends on environment)."""
        # We can't reliably test this since it depends on Docker being installed
        # and running. Just verify it returns a boolean without errors.
        result = _is_docker_running()
        self.assertIsInstance(result, bool)
        
        # Log the result for debugging purposes in test output
        print(f"Docker running status: {result}")


class CognitiveServicesAgentTests(ScenarioTest):
    """
    Integration tests for az cognitiveservices agent commands.
    
    These tests validate the full lifecycle of hosted agents in Azure AI Foundry,
    including creation, management, and deletion operations.
    """
    
    # Test data directory for sample connection files, Dockerfiles, etc.
    TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
    TEST_DATA_DIR = os.path.join(TEST_DIR, 'data', 'agent')
    
    @live_only()
    @serial_test()
    @ResourceGroupPreparer(location='eastus')
    def test_agent_create_basic(self, resource_group):
        """
        Test basic agent creation with minimal required parameters.
        
        Validates:
        - Agent creation with full image URI
        - Default CPU and memory values
        - Agent version extracted from image tag
        """
        account_name = self.create_random_name(prefix='cs_agent_', length=20)
        project_name = self.create_random_name(prefix='proj_', length=15)
        agent_name = 'test-agent'
        image_uri = 'myregistry.azurecr.io/test-agent:v1.0'
        
        self.kwargs.update({
            'account': account_name,
            'project': project_name,
            'agent': agent_name,
            'image': image_uri,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus'
        })
        
        # Create Cognitive Services account
        self.cmd('az cognitiveservices account create -n {account} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[
                     self.check('name', '{account}'),
                     self.check('properties.provisioningState', 'Succeeded')
                 ])
        
        # Create agent with minimal parameters
        agent = self.cmd('az cognitiveservices agent create --skip-acr-check '
                        '-a {account} '
                        '--project-name {project} '
                        '--name {agent} '
                        '--image {image}',
                        checks=[
                            self.check('name', '{agent}'),
                            self.check('properties.definition.image', '{image}'),
                            self.check('properties.definition.cpu', '1'),
                            self.check('properties.definition.memory', '2Gi')
                        ]).get_output_in_json()
        
        # Verify agent was created
        self.assertIsNotNone(agent)
        self.assertEqual(agent['name'], agent_name)
        
        # Cleanup: Delete agent
        self.cmd('az cognitiveservices agent delete -a {account} --project-name {project} --name {agent} --agent-version v1.0 --yes')
        
        # Cleanup: Delete account
        self.cmd('az cognitiveservices account delete -n {account} -g {rg}')
    
    @live_only()
    @serial_test()
    @ResourceGroupPreparer(location='eastus')
    def test_agent_create_with_registry(self, resource_group):
        """
        Test agent creation using --registry parameter.
        
        Validates:
        - Short image name with separate registry parameter
        - Image URI construction
        """
        account_name = self.create_random_name(prefix='cs_agent_', length=20)
        project_name = self.create_random_name(prefix='proj_', length=15)
        agent_name = 'test-agent-registry'
        
        self.kwargs.update({
            'account': account_name,
            'project': project_name,
            'agent': agent_name,
            'image': 'test-agent:v1.0',
            'registry': 'myregistry',
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus'
        })
        
        # Create Cognitive Services account
        self.cmd('az cognitiveservices account create -n {account} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('properties.provisioningState', 'Succeeded')])
        
        # Create agent with registry parameter
        agent = self.cmd('az cognitiveservices agent create --skip-acr-check '
                        '-a {account} '
                        '--project-name {project} '
                        '--name {agent} '
                        '--image {image} '
                        '--registry {registry}',
                        checks=[
                            self.check('name', '{agent}')
                        ]).get_output_in_json()
        
        # Verify full image URI was constructed
        expected_image = 'myregistry.azurecr.io/test-agent:v1.0'
        self.assertEqual(agent['properties']['definition']['image'], expected_image)
        
        # Cleanup
        self.cmd('az cognitiveservices agent delete -a {account} --project-name {project} --name {agent} --agent-version v1.0 --yes')
        self.cmd('az cognitiveservices account delete -n {account} -g {rg}')
    
    @live_only()
    @serial_test()
    @ResourceGroupPreparer(location='eastus')
    def test_agent_create_with_resources(self, resource_group):
        """
        Test agent creation with custom CPU and memory allocation.
        
        Validates:
        - Custom CPU values
        - Custom memory values
        """
        account_name = self.create_random_name(prefix='cs_agent_', length=20)
        project_name = self.create_random_name(prefix='proj_', length=15)
        agent_name = 'test-agent-resources'
        
        self.kwargs.update({
            'account': account_name,
            'project': project_name,
            'agent': agent_name,
            'image': 'myregistry.azurecr.io/test-agent:v2.0',
            'cpu': '2',
            'memory': '4Gi',
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus'
        })
        
        # Create Cognitive Services account
        self.cmd('az cognitiveservices account create -n {account} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('properties.provisioningState', 'Succeeded')])
        
        # Create agent with custom resources
        self.cmd('az cognitiveservices agent create --skip-acr-check '
                '-a {account} '
                '--project-name {project} '
                '--name {agent} '
                '--image {image} '
                '--cpu {cpu} '
                '--memory {memory}',
                checks=[
                    self.check('name', '{agent}'),
                    self.check('properties.definition.cpu', '{cpu}'),
                    self.check('properties.definition.memory', '{memory}')
                ])
        
        # Cleanup
        self.cmd('az cognitiveservices agent delete -a {account} --project-name {project} --name {agent} --agent-version v2.0 --yes')
        self.cmd('az cognitiveservices account delete -n {account} -g {rg}')
    
    @live_only()
    @serial_test()
    @ResourceGroupPreparer(location='eastus')
    def test_agent_create_with_environment_variables(self, resource_group):
        """
        Test agent creation with environment variables.
        
        Validates:
        - Space-separated key=value format
        - Multiple environment variables
        """
        account_name = self.create_random_name(prefix='cs_agent_', length=20)
        project_name = self.create_random_name(prefix='proj_', length=15)
        agent_name = 'test-agent-env'
        
        self.kwargs.update({
            'account': account_name,
            'project': project_name,
            'agent': agent_name,
            'image': 'myregistry.azurecr.io/test-agent:v1.0',
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus'
        })
        
        # Create Cognitive Services account
        self.cmd('az cognitiveservices account create -n {account} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('properties.provisioningState', 'Succeeded')])
        
        # Create agent with environment variables
        agent = self.cmd('az cognitiveservices agent create --skip-acr-check '
                        '-a {account} '
                        '--project-name {project} '
                        '--name {agent} '
                        '--image {image} '
                        '--env MODEL_NAME=gpt-4 API_TIMEOUT=30 LOG_LEVEL=info').get_output_in_json()
        
        # Verify environment variables
        env_vars = agent['properties']['definition']['environmentVariables']
        self.assertIsNotNone(env_vars)
        
        # Convert list to dict for easier verification
        env_dict = {var['key']: var['value'] for var in env_vars}
        self.assertEqual(env_dict['MODEL_NAME'], 'gpt-4')
        self.assertEqual(env_dict['API_TIMEOUT'], '30')
        self.assertEqual(env_dict['LOG_LEVEL'], 'info')
        
        # Cleanup
        self.cmd('az cognitiveservices agent delete -a {account} --project-name {project} --name {agent} --agent-version v1.0 --yes')
        self.cmd('az cognitiveservices account delete -n {account} -g {rg}')
    
    @live_only()
    @serial_test()
    @ResourceGroupPreparer(location='eastus')
    def test_agent_create_with_scaling(self, resource_group):
        """
        Test agent creation with horizontal scaling configuration.
        
        Validates:
        - Min replicas setting
        - Max replicas setting
        """
        account_name = self.create_random_name(prefix='cs_agent_', length=20)
        project_name = self.create_random_name(prefix='proj_', length=15)
        agent_name = 'test-agent-scaling'
        
        self.kwargs.update({
            'account': account_name,
            'project': project_name,
            'agent': agent_name,
            'image': 'myregistry.azurecr.io/test-agent:v1.0',
            'min_replicas': '2',
            'max_replicas': '10',
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus'
        })
        
        # Create Cognitive Services account
        self.cmd('az cognitiveservices account create -n {account} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('properties.provisioningState', 'Succeeded')])
        
        # Create agent with scaling configuration
        self.cmd('az cognitiveservices agent create --skip-acr-check '
                '-a {account} '
                '--project-name {project} '
                '--name {agent} '
                '--image {image} '
                '--min-replicas {min_replicas} '
                '--max-replicas {max_replicas}',
                checks=[
                    self.check('name', '{agent}'),
                    self.check('properties.scalingConfiguration.minReplicas', '{min_replicas}'),
                    self.check('properties.scalingConfiguration.maxReplicas', '{max_replicas}')
                ])
        
        # Cleanup
        self.cmd('az cognitiveservices agent delete -a {account} --project-name {project} --name {agent} --agent-version v1.0 --yes')
        self.cmd('az cognitiveservices account delete -n {account} -g {rg}')
    
    @live_only()
    @serial_test()
    @ResourceGroupPreparer(location='eastus')
    def test_agent_create_complete(self, resource_group):
        """
        Test agent creation with all parameters specified.
        
        Validates:
        - All optional parameters work together
        - Full configuration scenario
        """
        account_name = self.create_random_name(prefix='cs_agent_', length=20)
        project_name = self.create_random_name(prefix='proj_', length=15)
        agent_name = 'test-agent-complete'
        
        self.kwargs.update({
            'account': account_name,
            'project': project_name,
            'agent': agent_name,
            'image': 'myregistry.azurecr.io/test-agent:v3.0',
            'cpu': '2',
            'memory': '4Gi',
            'min_replicas': '1',
            'max_replicas': '5',
            'protocol': 'streaming',
            'protocol_version': 'v1',
            'description': 'Complete test agent',
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus'
        })
        
        # Create Cognitive Services account
        self.cmd('az cognitiveservices account create -n {account} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('properties.provisioningState', 'Succeeded')])
        
        # Create agent with all parameters
        self.cmd('az cognitiveservices agent create --skip-acr-check '
                '-a {account} '
                '--project-name {project} '
                '--name {agent} '
                '--image {image} '
                '--cpu {cpu} '
                '--memory {memory} '
                '--min-replicas {min_replicas} '
                '--max-replicas {max_replicas} '
                '--protocol {protocol} '
                '--protocol-version {protocol_version} '
                '--description "{description}" '
                '--env MODEL=gpt-4 TIMEOUT=30',
                checks=[
                    self.check('name', '{agent}'),
                    self.check('properties.definition.cpu', '{cpu}'),
                    self.check('properties.definition.memory', '{memory}'),
                    self.check('properties.scalingConfiguration.minReplicas', '{min_replicas}'),
                    self.check('properties.scalingConfiguration.maxReplicas', '{max_replicas}'),
                    self.check('properties.definition.protocol.type', '{protocol}'),
                    self.check('properties.description', '{description}')
                ])
        
        # Cleanup
        self.cmd('az cognitiveservices agent delete -a {account} --project-name {project} --name {agent} --agent-version v3.0 --yes')
        self.cmd('az cognitiveservices account delete -n {account} -g {rg}')
    
    @live_only()
    @serial_test()
    @ResourceGroupPreparer(location='eastus')
    def test_agent_create_from_source(self, resource_group):
        """
        Test agent creation from source code with Dockerfile.
        
        Validates:
        - Source code build workflow
        - Dockerfile detection
        - Automatic image tagging
        - Remote build (ACR Task)
        """
        import tempfile
        import os
        
        account_name = self.create_random_name(prefix='cs_agent_', length=20)
        project_name = self.create_random_name(prefix='proj_', length=15)
        agent_name = 'test-agent-source'
        registry_name = self.create_random_name(prefix='testreg', length=15)
        
        self.kwargs.update({
            'account': account_name,
            'project': project_name,
            'agent': agent_name,
            'registry': registry_name,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus'
        })
        
        # Create Cognitive Services account
        self.cmd('az cognitiveservices account create -n {account} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('properties.provisioningState', 'Succeeded')])
        
        # Create ACR
        self.cmd('az acr create -n {registry} -g {rg} --sku Basic -l {location}',
                 checks=[self.check('provisioningState', 'Succeeded')])
        
        # Create temporary directory with Dockerfile and app code
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a simple Dockerfile
            dockerfile_path = os.path.join(temp_dir, 'Dockerfile')
            with open(dockerfile_path, 'w') as f:
                f.write('''FROM python:3.11-slim
WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]
''')
            
            # Create a simple Python app
            app_path = os.path.join(temp_dir, 'app.py')
            with open(app_path, 'w') as f:
                f.write('print("Hello from agent")\n')
            
            self.kwargs['source_dir'] = temp_dir
            
            # Create agent from source with remote build
            agent = self.cmd('az cognitiveservices agent create --skip-acr-check '
                            '-a {account} '
                            '--project-name {project} '
                            '--name {agent} '
                            '--source {source_dir} '
                            '--registry {registry} '
                            '--build-remote',
                            checks=[
                                self.check('name', '{agent}'),
                            ]).get_output_in_json()
            
            # Verify agent was created with generated image
            self.assertIsNotNone(agent)
            self.assertEqual(agent['name'], agent_name)
            
            # Verify image URI contains registry
            image_uri = agent['properties']['definition']['image']
            self.assertIn(registry_name, image_uri)
            self.assertIn('.azurecr.io', image_uri)
            
            # Extract version from image
            version = image_uri.split(':')[-1]
            
            # Cleanup: Delete agent
            self.kwargs['version'] = version
            self.cmd('az cognitiveservices agent delete -a {account} --project-name {project} --name {agent} --agent-version {version} --yes')
        finally:
            # Cleanup temp directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Cleanup: Delete ACR and account
        self.cmd('az acr delete -n {registry} -g {rg} --yes')
        self.cmd('az cognitiveservices account delete -n {account} -g {rg}')
    
    @live_only()
    @serial_test()
    @ResourceGroupPreparer(location='eastus')
    def test_agent_create_errors(self, resource_group):
        """
        Test error handling for invalid inputs.

        Validates:
        - Missing required image tag
        - Invalid CPU value
        - Invalid memory format
        - Conflicting --no-start with replica parameters
        """
        account_name = self.create_random_name(prefix='cs_agent_', length=20)
        project_name = self.create_random_name(prefix='proj_', length=15)
        agent_name = 'test-agent-errors'

        self.kwargs.update({
            'account': account_name,
            'project': project_name,
            'agent': agent_name,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus'
        })

        # Create Cognitive Services account
        self.cmd('az cognitiveservices account create -n {account} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('properties.provisioningState', 'Succeeded')])

        # Test 1: Missing image tag
        with self.assertRaisesRegex(CLIError, 'must include a tag'):
            self.cmd('az cognitiveservices agent create --skip-acr-check '
                    '-a {account} '
                    '--project-name {project} '
                    '--name {agent} '
                    '--image myregistry.azurecr.io/test-agent')

        # Test 2: Invalid CPU (negative)
        with self.assertRaisesRegex(CLIError, 'CPU.*positive'):
            self.cmd('az cognitiveservices agent create --skip-acr-check '
                    '-a {account} '
                    '--project-name {project} '
                    '--name {agent} '
                    '--image myregistry.azurecr.io/test-agent:v1.0 '
                    '--cpu -1')

        # Test 3: Invalid memory format
        with self.assertRaisesRegex(CLIError, 'Memory.*Gi.*Mi'):
            self.cmd('az cognitiveservices agent create --skip-acr-check '
                    '-a {account} '
                    '--project-name {project} '
                    '--name {agent} '
                    '--image myregistry.azurecr.io/test-agent:v1.0 '
                    '--memory 2GB')

        # Test 4: --no-start with --min-replicas
        with self.assertRaisesRegex(CLIError, 'Cannot use --no-start with --min-replicas'):
            self.cmd('az cognitiveservices agent create --skip-acr-check '
                    '-a {account} '
                    '--project-name {project} '
                    '--name {agent} '
                    '--image myregistry.azurecr.io/test-agent:v1.0 '
                    '--no-start --min-replicas 2')

        # Test 5: --no-start with --max-replicas
        with self.assertRaisesRegex(CLIError, 'Cannot use --no-start with.*--max-replicas'):
            self.cmd('az cognitiveservices agent create --skip-acr-check '
                    '-a {account} '
                    '--project-name {project} '
                    '--name {agent} '
                    '--image myregistry.azurecr.io/test-agent:v1.0 '
                    '--no-start --max-replicas 5')

        # Cleanup
        self.cmd('az cognitiveservices account delete -n {account} -g {rg}')


if __name__ == '__main__':
    unittest.main()
