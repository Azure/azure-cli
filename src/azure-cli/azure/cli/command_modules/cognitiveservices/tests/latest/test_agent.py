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
from unittest import mock
from urllib.parse import urlparse, parse_qs

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.decorators import serial_test
from azure.cli.testsdk.scenario_tests.decorators import live_only
from azure.cli.core.azclierror import (
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    RequiredArgumentMissingError
)

from azure.cli.command_modules.cognitiveservices.custom import (
    _validate_image_tag,
    _has_dockerfile,
    _is_docker_running,
    _is_fully_qualified_image,
    _validate_path_for_subprocess,
    _get_agent_container_status,
    AGENT_API_VERSION_PARAMS,
)
from azure.cli.command_modules.cognitiveservices._params import _environment_variables_type


class CognitiveServicesAgentHelperTests(unittest.TestCase):
    """Unit tests for agent helper functions."""

    def test_get_agent_container_status_builds_expected_request(self):
        """Test that agent status calls the default container endpoint and returns payload."""
        expected_payload = {"status": "Running"}

        client = mock.Mock()
        response = mock.Mock()
        response.json.return_value = expected_payload
        client.send_request.return_value = response

        result = _get_agent_container_status(client, "myAgent", "10")

        self.assertEqual(result, expected_payload)
        client.send_request.assert_called_once()
        response.raise_for_status.assert_called_once()

        request = client.send_request.call_args[0][0]
        self.assertEqual(getattr(request, "method", None), "GET")

        parsed = urlparse(getattr(request, "url", ""))
        self.assertEqual(
            parsed.path,
            "/agents/myAgent/versions/10/containers/default",
        )
        self.assertEqual(
            parse_qs(parsed.query).get("api-version"),
            [AGENT_API_VERSION_PARAMS["api-version"]],
        )
    
    def test_validate_image_tag_valid(self):
        """Test tag validation and extraction from valid image URIs."""
        # Full ACR URI with version
        self.assertEqual(
            _validate_image_tag('myregistry.azurecr.io/myagent:v1.0'),
            'v1.0'
        )
        
        # Short image name with version
        self.assertEqual(
            _validate_image_tag('myagent:v2.5'),
            'v2.5'
        )
        
        # Version with special characters
        self.assertEqual(
            _validate_image_tag('myregistry.azurecr.io/myagent:v1.0-beta'),
            'v1.0-beta'
        )
        
        # Numeric version
        self.assertEqual(
            _validate_image_tag('myagent:123'),
            '123'
        )
        
        # Latest tag (should warn but succeed)
        self.assertEqual(
            _validate_image_tag('myregistry.azurecr.io/myagent:latest'),
            'latest'
        )
    
    def test_validate_image_tag_invalid(self):
        """Test tag validation error handling."""
        # Missing tag
        with self.assertRaises(InvalidArgumentValueError) as context:
            _validate_image_tag('myregistry.azurecr.io/myagent')
        self.assertIn('must include a', str(context.exception).lower())
        
        # Empty tag
        with self.assertRaises(InvalidArgumentValueError) as context:
            _validate_image_tag('myagent:')
        self.assertIn('must include a', str(context.exception).lower())

    def test_is_fully_qualified_image(self):
        self.assertTrue(_is_fully_qualified_image('myregistry.azurecr.io/myagent:v1'))
        self.assertTrue(_is_fully_qualified_image('localhost:5000/myagent:v1'))
        self.assertFalse(_is_fully_qualified_image('myagent:v1'))
    
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
    
    def test_agent_create_timeout_parameter_default(self):
        """Test that agent_create accepts timeout parameter with default value."""
        # This test verifies the function signature includes timeout parameter
        from inspect import signature
        from azure.cli.command_modules.cognitiveservices.custom import agent_create
        
        sig = signature(agent_create)
        self.assertIn('timeout', sig.parameters)
        self.assertEqual(sig.parameters['timeout'].default, 600)
    
    def test_deploy_agent_version_timeout_parameter(self):
        """Test that _deploy_agent_version accepts timeout parameter."""
        from inspect import signature
        from azure.cli.command_modules.cognitiveservices.custom import _deploy_agent_version
        
        sig = signature(_deploy_agent_version)
        self.assertIn('timeout', sig.parameters)
        self.assertEqual(sig.parameters['timeout'].default, 600)
    
    def test_wait_for_agent_deployment_ready_timeout_parameter(self):
        """Test that _wait_for_agent_deployment_ready accepts timeout and cmd parameters."""
        from inspect import signature
        from azure.cli.command_modules.cognitiveservices.custom import _wait_for_agent_deployment_ready
        
        sig = signature(_wait_for_agent_deployment_ready)
        # Verify cmd parameter exists (needed for progress indicator)
        self.assertIn('cmd', sig.parameters)
        # Verify timeout parameter exists with correct default
        self.assertIn('timeout', sig.parameters)
        self.assertEqual(sig.parameters['timeout'].default, 600)

    def test_validate_path_for_subprocess_valid_paths(self):
        """Test that valid paths pass validation."""
        from azure.cli.command_modules.cognitiveservices.custom import _validate_path_for_subprocess
        
        # These should all pass without raising exceptions
        valid_paths = [
            '/home/user/project',
            '/tmp/build',
            'C:\\Users\\user\\project',
            './relative/path',
            '../parent/dir',
            '/path/with-dashes_and.dots',
        ]
        
        for path in valid_paths:
            try:
                _validate_path_for_subprocess(path, "test path")
            except Exception as e:
                self.fail(f"Valid path '{path}' failed validation: {e}")
    
    def test_validate_path_for_subprocess_dangerous_chars(self):
        """Test that paths with dangerous shell metacharacters are rejected."""
        from azure.cli.command_modules.cognitiveservices.custom import _validate_path_for_subprocess
        
        # These should all raise InvalidArgumentValueError
        dangerous_paths = [
            '/tmp; rm -rf /',
            '/tmp && malicious_command',
            '/tmp | cat /etc/passwd',
            '/tmp`whoami`',
            '/tmp$(whoami)',
            '/tmp<file',
            '/tmp>file',
            '/tmp&background',
            '/tmp\nmalicious',
        ]
        
        for path in dangerous_paths:
            with self.assertRaises(InvalidArgumentValueError, msg=f"Path '{path}' should have been rejected"):
                _validate_path_for_subprocess(path, "test path")
    
    def test_validate_path_for_subprocess_null_bytes(self):
        """Test that paths with null bytes are rejected."""
        from azure.cli.command_modules.cognitiveservices.custom import _validate_path_for_subprocess
        
        with self.assertRaises(InvalidArgumentValueError):
            _validate_path_for_subprocess('/tmp/test\0file', "test path")
    
    def test_validate_path_for_subprocess_empty_path(self):
        """Test that empty paths are rejected."""
        from azure.cli.command_modules.cognitiveservices.custom import _validate_path_for_subprocess
        
        with self.assertRaises(InvalidArgumentValueError):
            _validate_path_for_subprocess('', "test path")
        
        with self.assertRaises(InvalidArgumentValueError):
            _validate_path_for_subprocess(None, "test path")

    # =========================================================================
    # Tests for agent logs functionality
    # =========================================================================

    def test_stream_agent_logs_function_signature(self):
        """Test that _stream_agent_logs has correct parameters."""
        from inspect import signature
        from azure.cli.command_modules.cognitiveservices.custom import _stream_agent_logs
        
        sig = signature(_stream_agent_logs)
        self.assertIn('cmd', sig.parameters)
        self.assertIn('client', sig.parameters)
        self.assertIn('agent_name', sig.parameters)
        self.assertIn('agent_version', sig.parameters)
        self.assertIn('kind', sig.parameters)
        self.assertIn('tail', sig.parameters)
        self.assertIn('follow', sig.parameters)
        # Verify defaults
        self.assertEqual(sig.parameters['kind'].default, "console")
        self.assertEqual(sig.parameters['tail'].default, 50)
        self.assertEqual(sig.parameters['follow'].default, True)

    def test_agent_logs_show_function_signature(self):
        """Test that agent_logs_show has correct parameters."""
        from inspect import signature
        from azure.cli.command_modules.cognitiveservices.custom import agent_logs_show
        
        sig = signature(agent_logs_show)
        self.assertIn('cmd', sig.parameters)
        self.assertIn('client', sig.parameters)
        self.assertIn('account_name', sig.parameters)
        self.assertIn('project_name', sig.parameters)
        self.assertIn('agent_name', sig.parameters)
        self.assertIn('agent_version', sig.parameters)
        self.assertIn('kind', sig.parameters)
        self.assertIn('tail', sig.parameters)
        self.assertIn('follow', sig.parameters)
        # Verify follow defaults to False for non-streaming behavior
        self.assertEqual(sig.parameters['follow'].default, False)
        self.assertEqual(sig.parameters['kind'].default, "console")
        self.assertEqual(sig.parameters['tail'].default, 50)

    def test_agent_start_show_logs_parameter(self):
        """Test that agent_start accepts show_logs and timeout parameters."""
        from inspect import signature
        from azure.cli.command_modules.cognitiveservices.custom import agent_start
        
        sig = signature(agent_start)
        self.assertIn('cmd', sig.parameters)
        self.assertIn('show_logs', sig.parameters)
        self.assertIn('timeout', sig.parameters)
        self.assertEqual(sig.parameters['show_logs'].default, False)
        self.assertEqual(sig.parameters['timeout'].default, 600)

    def test_agent_create_show_logs_parameter(self):
        """Test that agent_create accepts show_logs parameter."""
        from inspect import signature
        from azure.cli.command_modules.cognitiveservices.custom import agent_create
        
        sig = signature(agent_create)
        self.assertIn('show_logs', sig.parameters)
        self.assertEqual(sig.parameters['show_logs'].default, False)

    def test_deploy_agent_version_show_logs_parameter(self):
        """Test that _deploy_agent_version accepts show_logs parameter."""
        from inspect import signature
        from azure.cli.command_modules.cognitiveservices.custom import _deploy_agent_version
        
        sig = signature(_deploy_agent_version)
        self.assertIn('show_logs', sig.parameters)
        self.assertEqual(sig.parameters['show_logs'].default, False)


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
        - Invalid --build-remote with --image (should only be used with --source)
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
        with self.assertRaisesRegex(InvalidArgumentValueError, 'must include a tag'):
            self.cmd('az cognitiveservices agent create --skip-acr-check '
                    '-a {account} '
                    '--project-name {project} '
                    '--name {agent} '
                    '--image myregistry.azurecr.io/test-agent')

        # Test 2: Invalid CPU (negative)
        with self.assertRaisesRegex(InvalidArgumentValueError, 'CPU.*positive'):
            self.cmd('az cognitiveservices agent create --skip-acr-check '
                    '-a {account} '
                    '--project-name {project} '
                    '--name {agent} '
                    '--image myregistry.azurecr.io/test-agent:v1.0 '
                    '--cpu -1')

        # Test 3: Invalid memory format
        with self.assertRaisesRegex(InvalidArgumentValueError, 'Memory.*Gi.*Mi'):
            self.cmd('az cognitiveservices agent create --skip-acr-check '
                    '-a {account} '
                    '--project-name {project} '
                    '--name {agent} '
                    '--image myregistry.azurecr.io/test-agent:v1.0 '
                    '--memory 2GB')

        # Test 4: --no-start with --min-replicas
        with self.assertRaisesRegex(InvalidArgumentValueError, 'Cannot use --no-start with --min-replicas'):
            self.cmd('az cognitiveservices agent create --skip-acr-check '
                    '-a {account} '
                    '--project-name {project} '
                    '--name {agent} '
                    '--image myregistry.azurecr.io/test-agent:v1.0 '
                    '--no-start --min-replicas 2')

        # Test 5: --no-start with --max-replicas
        with self.assertRaisesRegex(InvalidArgumentValueError, 'Cannot use --no-start with.*--max-replicas'):
            self.cmd('az cognitiveservices agent create --skip-acr-check '
                    '-a {account} '
                    '--project-name {project} '
                    '--name {agent} '
                    '--image myregistry.azurecr.io/test-agent:v1.0 '
                    '--no-start --max-replicas 5')

        # Test 6: Fully-qualified image plus --registry
        with self.assertRaisesRegex(InvalidArgumentValueError, 'omit --registry'):
            self.cmd('az cognitiveservices agent create --skip-acr-check '
                    '-a {account} '
                    '--project-name {project} '
                    '--name {agent} '
                    '--image myregistry.azurecr.io/test-agent:v1.0 '
                    '--registry myregistry')

        # Test 7: --build-remote with --image (should only be used with --source)
        with self.assertRaisesRegex(InvalidArgumentValueError, '--build-remote can only be used with --source'):
            self.cmd('az cognitiveservices agent create --skip-acr-check '
                    '-a {account} '
                    '--project-name {project} '
                    '--name {agent} '
                    '--image myregistry.azurecr.io/test-agent:v1.0 '
                    '--build-remote')

        # Cleanup
        self.cmd('az cognitiveservices account delete -n {account} -g {rg}')

    # =========================================================================
    # Integration tests for agent logs functionality
    # =========================================================================

    @live_only()
    @serial_test()
    @ResourceGroupPreparer(location='eastus')
    def test_agent_logs_show_basic(self, resource_group):
        """
        Test basic log streaming without --follow flag.

        Validates:
        - Log command executes without error
        - Default parameters (console type, 50 lines tail)
        - Command exits after fetching initial logs
        """
        account_name = self.create_random_name(prefix='cs_logs_', length=20)
        project_name = self.create_random_name(prefix='proj_', length=15)
        agent_name = 'test-logs-agent'

        self.kwargs.update({
            'account': account_name,
            'project': project_name,
            'agent': agent_name,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus',
            'image': 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'
        })

        # Create Cognitive Services account
        self.cmd('az cognitiveservices account create -n {account} -g {rg} '
                 '--kind {kind} --sku {sku} -l {location} --yes --manage-projects',
                 checks=[self.check('properties.provisioningState', 'Succeeded')])

        # Create agent with a sample image
        self.cmd('az cognitiveservices agent create --skip-acr-check '
                 '-a {account} --project-name {project} --name {agent} '
                 '--image {image}',
                 checks=[self.check('name', '{agent}')])

        # Fetch logs without follow (should return and exit)
        # This verifies the command runs successfully
        self.cmd('az cognitiveservices agent logs show '
                 '-a {account} -p {project} -n {agent} --agent-version 1')

        # Cleanup
        self.cmd('az cognitiveservices agent delete -a {account} -p {project} -n {agent}')
        self.cmd('az cognitiveservices account delete -n {account} -g {rg}')

    @live_only()
    @serial_test()
    @ResourceGroupPreparer(location='eastus')
    def test_agent_logs_show_with_options(self, resource_group):
        """
        Test log streaming with various options.

        Validates:
        - --type system option
        - --tail custom value
        - Different log type outputs
        """
        account_name = self.create_random_name(prefix='cs_logs_', length=20)
        project_name = self.create_random_name(prefix='proj_', length=15)
        agent_name = 'test-logs-opts'

        self.kwargs.update({
            'account': account_name,
            'project': project_name,
            'agent': agent_name,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus',
            'image': 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'
        })

        # Create Cognitive Services account
        self.cmd('az cognitiveservices account create -n {account} -g {rg} '
                 '--kind {kind} --sku {sku} -l {location} --yes --manage-projects',
                 checks=[self.check('properties.provisioningState', 'Succeeded')])

        # Create agent
        self.cmd('az cognitiveservices agent create --skip-acr-check '
                 '-a {account} --project-name {project} --name {agent} '
                 '--image {image}',
                 checks=[self.check('name', '{agent}')])

        # Test with --type system
        self.cmd('az cognitiveservices agent logs show '
                 '-a {account} -p {project} -n {agent} --agent-version 1 '
                 '--type system')

        # Test with --tail custom value
        self.cmd('az cognitiveservices agent logs show '
                 '-a {account} -p {project} -n {agent} --agent-version 1 '
                 '--tail 100')

        # Test with both options
        self.cmd('az cognitiveservices agent logs show '
                 '-a {account} -p {project} -n {agent} --agent-version 1 '
                 '--type console --tail 200')

        # Cleanup
        self.cmd('az cognitiveservices agent delete -a {account} -p {project} -n {agent}')
        self.cmd('az cognitiveservices account delete -n {account} -g {rg}')

    @live_only()
    @serial_test()
    @ResourceGroupPreparer(location='eastus')
    def test_agent_start_with_show_logs(self, resource_group):
        """
        Test agent start with --show-logs flag.

        Validates:
        - Agent can be stopped and started
        - --show-logs flag streams logs during startup
        """
        account_name = self.create_random_name(prefix='cs_start_', length=20)
        project_name = self.create_random_name(prefix='proj_', length=15)
        agent_name = 'test-start-logs'

        self.kwargs.update({
            'account': account_name,
            'project': project_name,
            'agent': agent_name,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus',
            'image': 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'
        })

        # Create Cognitive Services account
        self.cmd('az cognitiveservices account create -n {account} -g {rg} '
                 '--kind {kind} --sku {sku} -l {location} --yes --manage-projects',
                 checks=[self.check('properties.provisioningState', 'Succeeded')])

        # Create agent
        self.cmd('az cognitiveservices agent create --skip-acr-check '
                 '-a {account} --project-name {project} --name {agent} '
                 '--image {image}',
                 checks=[self.check('name', '{agent}')])

        # Stop the agent first
        self.cmd('az cognitiveservices agent stop '
                 '-a {account} -p {project} -n {agent} --agent-version 1')

        # Start with --show-logs
        self.cmd('az cognitiveservices agent start '
                 '-a {account} -p {project} -n {agent} --agent-version 1 '
                 '--show-logs --timeout 120')

        # Cleanup
        self.cmd('az cognitiveservices agent delete -a {account} -p {project} -n {agent}')
        self.cmd('az cognitiveservices account delete -n {account} -g {rg}')


if __name__ == '__main__':
    unittest.main()
