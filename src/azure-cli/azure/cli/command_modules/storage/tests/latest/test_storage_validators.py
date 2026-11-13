# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock
from argparse import (Namespace, ArgumentError)
from io import StringIO

from knack import CLI

from azure.cli.core._config import GLOBAL_CONFIG_DIR, ENV_VAR_PREFIX
from azure.cli.core.cloud import get_active_cloud
from azure.cli.core.profiles import get_sdk, ResourceType

from azure.cli.command_modules.storage._validators import (get_permission_validator, get_datetime_type,
                                                           ipv4_range_type, resource_type_type_v2, services_type_v2,
                                                           process_blob_source_uri, get_char_options_validator,
                                                           get_source_file_or_blob_service_client_track2,
                                                           validate_encryption_source, validate_source_uri,
                                                           validate_source_url,
                                                           validate_encryption_services, as_user_validator,
                                                           get_not_none_validator, validate_upload_blob, 
                                                           validate_client_parameters)


class MockCLI(CLI):
    def __init__(self):
        super().__init__(cli_name='mock_cli', config_dir=GLOBAL_CONFIG_DIR,
                         config_env_var_prefix=ENV_VAR_PREFIX, commands_loader_cls=MockLoader)
        self.cloud = get_active_cloud(self)
        self.data = {"headers": [], "completer_active": False, "command": ""}


class MockLoader:
    def __init__(self, ctx):
        self.ctx = ctx

    def get_models(self, *attr_args, **_):
        from azure.cli.core.profiles import get_sdk
        return get_sdk(self.ctx, ResourceType.DATA_STORAGE_BLOB, *attr_args, mod='models')

class MockCmd:
    def __init__(self, ctx, arguments={}):
        self.cli_ctx = ctx
        self.loader = MockLoader(self.cli_ctx)
        self.arguments = arguments
        self.command_kwargs = {}

    def get_models(self, *attr_args, **kwargs):
        resource_type = kwargs.get('resource_type', self.command_kwargs.get('resource_type', None))
        return get_sdk(self.cli_ctx, resource_type, *attr_args)


class TestCmdModuleStorageValidators(unittest.TestCase):
    def setUp(self):
        self.io = StringIO()
        self.cli = MockCLI()
        self.loader = MockLoader(self.cli)

    def tearDown(self):
        self.io.close()

    def test_permission_validator(self):
        t_container_permissions = get_sdk(self.cli, ResourceType.DATA_STORAGE_BLOB, '_models#ContainerSasPermissions')

        ns1 = Namespace(permission='rwdl')
        ns2 = Namespace(permission='abc')
        get_permission_validator(t_container_permissions)(ns1)
        self.assertTrue(isinstance(ns1.permission, t_container_permissions))
        with self.assertRaises(ValueError):
            get_permission_validator(t_container_permissions)(ns2)

    def test_datetime_string_type(self):
        input = "2017-01-01T12:30Z"
        actual = get_datetime_type(True)(input)
        expected = "2017-01-01T12:30Z"
        self.assertEqual(actual, expected)

        input = "2017-01-01 12:30"
        with self.assertRaises(ValueError):
            get_datetime_type(True)(input)

    def test_datetime_type(self):
        import datetime
        input = "2017-01-01T12:30Z"
        actual = get_datetime_type(False)(input)
        expected = datetime.datetime(2017, 1, 1, 12, 30, 0)
        self.assertEqual(actual, expected)

        input = "2017-01-01 12:30"
        with self.assertRaises(ValueError):
            actual = get_datetime_type(False)(input)

    def test_ipv4_range_type(self):
        from knack.util import CLIError
        input = "111.22.3.111"
        actual = ipv4_range_type(input)
        expected = input
        self.assertEqual(actual, expected)

        input = "111.22.3.111-222.11.44.111"
        actual = ipv4_range_type(input)
        expected = input
        self.assertEqual(actual, expected)

        input = "111.22"
        with self.assertRaises(CLIError):
            actual = ipv4_range_type(input)

        input = "111.22.33.44-"
        with self.assertRaises(CLIError):
            actual = ipv4_range_type(input)

    def test_resource_types_type(self):
        input = "sso"
        actual = str(resource_type_type_v2(self.loader)(input))
        expected = "so"
        self.assertEqual(actual, expected)

        input = "blob"
        with self.assertRaises(ValueError):
            actual = resource_type_type_v2(self.loader)(input)

    def test_services_type(self):
        input = "ttfqbqtf"
        actual = str(services_type_v2()(input))
        expected = "bqtf"
        self.assertEqual(set(actual), set(expected))

        input = "everything"
        with self.assertRaises(ValueError):
            services_type_v2()(input)

    def test_storage_process_blob_source_uri_redundent_parameter(self):
        with self.assertRaises(ValueError):
            process_blob_source_uri(MockCmd(self.cli),
                                    Namespace(copy_source='https://example.com', source_sas='some_sas'))
        with self.assertRaises(ValueError):
            process_blob_source_uri(MockCmd(self.cli),
                                    Namespace(copy_source='https://example.com', source_account_name='account_name'))

    def test_storage_get_char_options_validator(self):
        with self.assertRaises(ValueError) as cm:
            get_char_options_validator('abc', 'no_such_property')(object())
        self.assertEqual('Missing options --no-such-property.', str(cm.exception))

        ns = Namespace(services='bcd')
        with self.assertRaises(ValueError) as cm:
            get_char_options_validator('abc', 'services')(ns)
        self.assertEqual('--services: only valid values are: a, b, c.', str(cm.exception))

        ns = Namespace(services='ab')
        get_char_options_validator('abc', 'services')(ns)

        result = getattr(ns, 'services')
        self.assertIs(type(result), set)
        self.assertEqual(result, set('ab'))

    def test_validate_source_uri(self):
        ns = Namespace(copy_source='https://other_name.file.core.windows.net/share2',
                       source_sas='some_sas_token')
        validate_source_uri(MockCmd(self.cli), ns)
        self.assertEqual(ns.copy_source, 'https://other_name.file.core.windows.net/share2?some_sas_token')

    @mock.patch('azure.cli.command_modules.storage._validators.validate_client_parameters')
    def test_validate_source_url_marks_structured_same_account_blob(self, _):
        ns = Namespace(
            source_url=None, source_sas=None, source_container='src', source_blob='input',
            source_snapshot=None, source_share=None, source_path=None, file_snapshot=None,
            source_account_name='account', source_account_key=None, token_credential=None,
            account_name='account', account_key='key', account_url='https://storage.internal.example',
            connection_string=None, sas_token=None, location_mode=None, connection_timeout=None,
            container_name='dst', share_name=None)

        validate_source_url(MockCmd(self.cli), ns)

        self.assertTrue(ns.source_is_validated_same_account)
        self.assertEqual(ns.source_url, 'https://account.blob.core.windows.net/src/input')

    def test_validate_source_url_does_not_mark_arbitrary_uri_as_same_account(self):
        source_url = 'https://account.blob.core.windows.net.attacker.example/src/input'
        ns = Namespace(
            source_url=source_url, source_sas=None, source_container=None, source_blob=None,
            source_snapshot=None, source_share=None, source_path=None, file_snapshot=None,
            source_account_name=None, source_account_key=None)
        validate_source_url(MockCmd(self.cli), ns)
        validate_source_url(MockCmd(self.cli), ns)

        self.assertFalse(ns.source_is_validated_same_account)
        self.assertEqual(ns.source_url, source_url)

    @mock.patch('azure.cli.command_modules.storage._validators.validate_client_parameters')
    @mock.patch('azure.cli.command_modules.storage.util.create_short_lived_file_sas_v2', return_value='sas')
    def test_validate_source_url_does_not_mark_structured_file_as_same_account(self, _, __):
        ns = Namespace(
            source_url=None, source_sas=None, source_container=None, source_blob=None,
            source_snapshot=None, source_share='src', source_path='input', file_snapshot=None,
            source_account_name='account', source_account_key=None, token_credential=None,
            account_name='account', account_key='key', sas_token=None,
            container_name='dst', share_name=None)

        validate_source_url(MockCmd(self.cli), ns)

        self.assertFalse(ns.source_is_validated_same_account)

    @mock.patch('azure.cli.command_modules.storage._validators.validate_client_parameters')
    def test_validate_source_url_requires_valid_account_name_for_same_account(self, _):
        from azure.cli.core.azclierror import InvalidArgumentValueError
        for account_name in (None, 'same@attacker.example:443/'):
            with self.subTest(account_name=account_name):
                ns = Namespace(
                    source_url=None, source_sas=None, source_container='src', source_blob='input',
                    source_snapshot=None, source_share=None, source_path=None, file_snapshot=None,
                    source_account_name=account_name, source_account_key=None, token_credential=None,
                    account_name=account_name, account_key='key', sas_token=None,
                    container_name='dst', share_name=None)

                if account_name is None:
                    validate_source_url(MockCmd(self.cli), ns)
                    self.assertFalse(ns.source_is_validated_same_account)
                else:
                    with self.assertRaisesRegex(InvalidArgumentValueError, 'Invalid source storage account name'):
                        validate_source_url(MockCmd(self.cli), ns)
                    self.assertIsNone(ns.source_url)

    def test_get_not_none_validator(self):
        from azure.cli.core.azclierror import InvalidArgumentValueError
        from knack.arguments import CLICommandArgument, CLIArgumentType

        container_name_type = CLIArgumentType(options_list=['--container-name', '-c'], help='The container name.')
        arg_type = CLIArgumentType(help='whatever arg')
        cmd = MockCmd(self.cli)
        cmd.arguments = {'container_name': CLICommandArgument(dest='container_name', argtype=container_name_type),
                         'arg': CLICommandArgument(dest='arg', argtype=arg_type)}

        validate_container_name = get_not_none_validator('container_name')
        with self.assertRaisesRegex(InvalidArgumentValueError, 'Argument --container-name/-c should be specified'):
            validate_container_name(cmd, Namespace(container_name=''))

        validate_arg = get_not_none_validator('arg')
        with self.assertRaisesRegex(InvalidArgumentValueError, 'Argument --arg should be specified'):
            validate_arg(cmd, Namespace(arg=None))

        validate_arg(cmd, Namespace(arg=0))
        validate_arg(cmd, Namespace(arg=False))

    def test_validate_upload_blob(self):
        from azure.cli.core.azclierror import InvalidArgumentValueError

        validate_upload_blob(Namespace(file_path=None, data=''))
        validate_upload_blob(Namespace(file_path=None, data='test data'))
        validate_upload_blob(Namespace(file_path='test.txt', data=None))

        with self.assertRaisesRegex(InvalidArgumentValueError, 'please only specify one of --file and --data'):
            validate_upload_blob(Namespace(file_path='test.txt', data=''))

        with self.assertRaisesRegex(InvalidArgumentValueError, 'please specify one of --file and --data'):
            validate_upload_blob(Namespace(file_path=None, data=None))


@mock.patch('azure.cli.command_modules.storage._validators.validate_client_parameters')
@mock.patch('azure.cli.command_modules.storage._validators._query_account_key', return_value='queried_key')
@mock.patch('azure.cli.command_modules.storage.util.create_short_lived_blob_sas_v2', return_value='blob_sas')
@mock.patch('azure.cli.command_modules.storage.util.create_short_lived_file_sas_v2', return_value='file_sas')
class TestCopySourceAccountNameValidation(unittest.TestCase):
    INVALID_NAMES = ('evil.example/x?', 'evil.example', 'user@evil.example', 'evil.example:443', 'evil\\x', 'ev il')

    def setUp(self):
        self.cli = MockCLI()

    @staticmethod
    def _blob_source_namespace(**kwargs):
        values = dict(copy_source=None, source_container='src', source_blob='input', source_snapshot=None,
                      source_account_name=None, source_account_key=None, source_sas=None,
                      account_name='destaccount', account_key='key', sas_token=None)
        values.update(kwargs)
        return Namespace(**values)

    @staticmethod
    def _source_namespace(**kwargs):
        values = dict(copy_source=None, source_url=None, source_container='src', source_blob='input',
                      source_snapshot=None, source_share=None, source_path=None, file_snapshot=None,
                      source_account_name=None, source_account_key=None, source_sas=None, token_credential=None,
                      account_name='destaccount', account_key='key', sas_token=None,
                      container_name='dst', share_name=None)
        values.update(kwargs)
        return Namespace(**values)

    def _validators(self):
        return ((process_blob_source_uri, self._blob_source_namespace, 'copy_source'),
                (validate_source_uri, self._source_namespace, 'copy_source'),
                (validate_source_url, self._source_namespace, 'source_url'))

    def test_rejects_invalid_source_account_names(self, *mocks):
        from azure.cli.core.azclierror import InvalidArgumentValueError
        query_account_key = mocks[2]
        for validator, make_namespace, result_attr in self._validators():
            for name in self.INVALID_NAMES:
                for kwargs in ({'source_account_name': name},
                               {'source_account_name': name, 'source_account_key': 'source_key'},
                               {'source_account_name': name, 'source_sas': 'sig=source'},
                               # same account: the name comes from --account-name or a connection string
                               {'account_name': name}):
                    with self.subTest(validator=validator.__name__, **kwargs):
                        ns = make_namespace(**kwargs)
                        with self.assertRaisesRegex(InvalidArgumentValueError,
                                                    'Invalid source storage account name') as ctx:
                            validator(MockCmd(self.cli), ns)
                        self.assertNotIn(name, str(ctx.exception))
                        self.assertIsNone(getattr(ns, result_attr))
        query_account_key.assert_not_called()

    def test_builds_source_url_for_valid_account_names(self, *_):
        for validator, make_namespace, result_attr in self._validators():
            for kwargs, account in (({'source_account_name': 'srcaccount', 'source_account_key': 'k'}, 'srcaccount'),
                                    ({'source_account_name': 'MySrc-Account', 'source_sas': 'sig=s'},
                                     'MySrc-Account'),
                                    ({}, 'destaccount')):
                with self.subTest(validator=validator.__name__, **kwargs):
                    ns = make_namespace(**kwargs)
                    validator(MockCmd(self.cli), ns)
                    self.assertTrue(getattr(ns, result_attr).startswith(
                        'https://{}.blob.{}/src/input'.format(account, self.cli.cloud.suffixes.storage_endpoint)))


@mock.patch('azure.cli.command_modules.storage._validators.validate_client_parameters')
class TestUnrecognizedStorageUrlValidation(unittest.TestCase):
    URLS = ('http://127.0.0.1:10000/devstoreaccount1/c?sig=topsecret',
            'https://acct.privatelink.blob.core.windows.net/c?sig=topsecret',
            'https://acct.z22.blob.storage.azure.net/c?sig=topsecret',
            'https://evil.example\\.file.core.windows.net/c?sig=topsecret',
            'https://acct.blob.core.windows.net./c?sig=topsecret')

    def setUp(self):
        self.cli = MockCLI()

    def _assert_rejected(self, validator, ns, arg_name):
        from azure.cli.core.azclierror import InvalidArgumentValueError
        with self.assertRaisesRegex(InvalidArgumentValueError,
                                    'The {} URL is not a recognized Azure Storage'.format(arg_name)) as ctx:
            validator(MockCmd(self.cli), ns)
        self.assertNotIn('topsecret', str(ctx.exception))
        self.assertNotIn('topsecret', str(ctx.exception.recommendations))
        self.assertIn(self.cli.cloud.suffixes.storage_endpoint, str(ctx.exception.recommendations))

    def test_blob_batch_container_url(self, validate_client):
        from azure.cli.command_modules.storage._validators import _process_blob_batch_container_parameters
        for url in self.URLS:
            with self.subTest(url=url):
                self._assert_rejected(_process_blob_batch_container_parameters,
                                      Namespace(source=url, account_name=None, sas_token=None), '--source')
                self._assert_rejected(
                    lambda cmd, ns: _process_blob_batch_container_parameters(cmd, ns, source=False),
                    Namespace(destination=url, account_name=None, sas_token=None), '--destination')
        validate_client.assert_not_called()

    def test_file_batch_urls(self, _):
        import tempfile
        from azure.cli.command_modules.storage._validators import (process_file_batch_source_parameters,
                                                                   process_file_upload_batch_parameters)
        with tempfile.TemporaryDirectory() as source_dir:
            for url in self.URLS:
                with self.subTest(url=url):
                    self._assert_rejected(process_file_batch_source_parameters,
                                          Namespace(source=url, account_name=None), '--source')
                    self._assert_rejected(process_file_upload_batch_parameters,
                                          Namespace(source=source_dir, destination=url, account_name=None),
                                          '--destination')

    def test_copy_source_uri(self, _):
        for url in self.URLS:
            with self.subTest(url=url):
                ns = Namespace(account_name='storagename', account_key='key', connection_string=None, sas_token=None,
                               source_account_key=None, source_account_name=None, source_container=None,
                               source_sas=None, source_share=None, source_uri=url, destination_container='c',
                               destination_share=None)
                self._assert_rejected(get_source_file_or_blob_service_client_track2, ns, '--source-uri')

    def test_recognized_urls_and_names_still_accepted(self, _):
        from azure.cli.command_modules.storage._validators import (_process_blob_batch_container_parameters,
                                                                   process_file_batch_source_parameters)
        ns = Namespace(source='https://MyAcct.blob.core.windows.net/c?sig=s', account_name=None, sas_token=None)
        _process_blob_batch_container_parameters(MockCmd(self.cli), ns)
        self.assertEqual((ns.account_name, ns.source_container_name, ns.sas_token), ('MyAcct', 'c', 'sig=s'))

        ns = Namespace(source='myshare', account_name=None)
        process_file_batch_source_parameters(MockCmd(self.cli), ns)
        self.assertEqual((ns.account_name, ns.share_name), (None, 'myshare'))


class TestClientParametersValidator(unittest.TestCase):
    def setUp(self):
        self.cli = MockCLI()
        self.local_url = 'http://localhost:10000/devstoreaccount1'
        self.legacy_url = 'http://legacy:10000/devstoreaccount1'

    def test_service_endpoint_env_var_used(self):
        # AZURE_STORAGE_SERVICE_ENDPOINT is the documented env var, should set account_url
        ns = self._create_namespace(auth_mode='key')
        self._validate(ns, AZURE_STORAGE_SERVICE_ENDPOINT=self.local_url)
        self.assertEqual(ns.account_url, self.local_url)

    def test_account_url_env_var_still_used(self):
        # AZURE_STORAGE_ACCOUNT_URL is the legacy env var, should keep working
        ns = self._create_namespace(auth_mode='key')
        self._validate(ns, AZURE_STORAGE_ACCOUNT_URL=self.legacy_url)
        self.assertEqual(ns.account_url, self.legacy_url)

    def test_service_endpoint_env_var_wins_over_account_url(self):
        # both env vars set, documented one takes precedence
        ns = self._create_namespace(auth_mode='key')
        self._validate(ns, AZURE_STORAGE_SERVICE_ENDPOINT=self.local_url,
                       AZURE_STORAGE_ACCOUNT_URL=self.legacy_url)
        self.assertEqual(ns.account_url, self.local_url)

    def test_no_endpoint_env_var(self):
        # no endpoint env var, account_url stays empty so client factory falls back to public cloud
        ns = self._create_namespace(auth_mode='key')
        self._validate(ns)
        self.assertIsNone(ns.account_url)

    def test_endpoint_argument_wins_over_env_var(self):
        # --blob-endpoint given explicitly, env var is ignored
        ns = self._create_namespace(auth_mode='key', account_url='https://flag.example.com')
        self._validate(ns, AZURE_STORAGE_SERVICE_ENDPOINT=self.local_url)
        self.assertEqual(ns.account_url, 'https://flag.example.com')

    def test_service_endpoint_env_var_used_without_auth_mode(self):
        # commands without --auth-mode go through the second lookup block in the validator
        ns = self._create_namespace()
        self._validate(ns, AZURE_STORAGE_SERVICE_ENDPOINT=self.local_url)
        self.assertEqual(ns.account_url, self.local_url)

    @mock.patch('azure.cli.command_modules.storage._validators._query_account_key', return_value='queried_key')
    def test_invalid_account_name_rejected_before_key_lookup(self, query_account_key):
        from azure.cli.core.azclierror import InvalidArgumentValueError
        name = 'https://myaccount.blob.core.windows.net/?sv=2025&sig=topsecret'
        for kwargs in ({'account_name': name}, {'account_name': name, 'auth_mode': 'key'},
                       {'connection_string': 'AccountName=' + name}):
            with self.subTest(**kwargs):
                with mock.patch.dict('os.environ', {}, clear=True), \
                        mock.patch('azure.cli.command_modules.storage._validators.logger') as logger, \
                        self.assertRaisesRegex(InvalidArgumentValueError, 'Invalid storage account name') as ctx:
                    validate_client_parameters(MockCmd(self.cli), self._create_namespace(**kwargs))
                self.assertNotIn('topsecret', str(ctx.exception))
                self.assertNotIn('topsecret', str(logger.mock_calls))
        query_account_key.assert_not_called()

    @mock.patch('azure.cli.command_modules.storage._validators._query_account_key', return_value='queried_key')
    def test_invalid_account_name_with_custom_endpoint_skips_key_lookup(self, query_account_key):
        from azure.cli.core.azclierror import InvalidArgumentValueError
        ns = self._create_namespace(account_name='odd.name', account_url='https://storage.contoso.example')
        with mock.patch.dict('os.environ', {}, clear=True), \
                self.assertRaisesRegex(InvalidArgumentValueError, 'There are no credentials provided'):
            validate_client_parameters(MockCmd(self.cli), ns)
        query_account_key.assert_not_called()

        # a custom endpoint with credentials is unaffected by the account name check
        ns = self._create_namespace(account_name='odd.name', account_url='https://storage.contoso.example',
                                    sas_token='?sig=s')
        with mock.patch.dict('os.environ', {}, clear=True):
            validate_client_parameters(MockCmd(self.cli), ns)
        self.assertEqual((ns.account_name, ns.sas_token), ('odd.name', 'sig=s'))
        query_account_key.assert_not_called()

    @mock.patch('azure.cli.command_modules.storage._validators._query_account_key', return_value='queried_key')
    def test_valid_account_name_still_queries_key(self, query_account_key):
        for name, expected in (('MyAccount', 'MyAccount'), ('myaccount-secondary', 'myaccount')):
            with self.subTest(name=name):
                ns = self._create_namespace(account_name=name)
                with mock.patch.dict('os.environ', {}, clear=True):
                    validate_client_parameters(MockCmd(self.cli), ns)
                self.assertEqual((ns.account_name, ns.account_key), (expected, 'queried_key'))
                query_account_key.assert_called_with(mock.ANY, expected)

    def _create_namespace(self, **kwargs):
        ns = Namespace(account_name=None, account_url=None, account_key=None, sas_token=None,
                       connection_string=None)
        for key in kwargs:
            setattr(ns, key, kwargs[key])
        return ns

    def _validate(self, ns, **env):
        env.update(AZURE_STORAGE_ACCOUNT='devstoreaccount1', AZURE_STORAGE_KEY='fake_key')
        with mock.patch.dict('os.environ', env, clear=True):
            validate_client_parameters(MockCmd(self.cli), ns)


class TestEncryptionValidators(unittest.TestCase):
    def setUp(self):
        self.cli = MockCLI()

    def test_validate_encryption_services(self):
        ns = Namespace(encryption_services=['blob'], _cmd=MockCmd(self.cli))
        validate_encryption_services(MockCmd(self.cli), ns)
        self.assertIsNotNone(ns.encryption_services.blob)
        self.assertTrue(ns.encryption_services.blob.enabled)
        self.assertIsNone(ns.encryption_services.file)

        ns = Namespace(encryption_services=['file'], _cmd=MockCmd(self.cli))
        validate_encryption_services(MockCmd(self.cli), ns)
        self.assertIsNotNone(ns.encryption_services.file)
        self.assertTrue(ns.encryption_services.file.enabled)
        self.assertIsNone(ns.encryption_services.blob)

        ns = Namespace(encryption_services=['blob', 'file'], _cmd=MockCmd(self.cli))
        validate_encryption_services(MockCmd(self.cli), ns)
        self.assertIsNotNone(ns.encryption_services.blob)
        self.assertTrue(ns.encryption_services.blob.enabled)
        self.assertIsNotNone(ns.encryption_services.file)
        self.assertTrue(ns.encryption_services.file.enabled)

    def test_validate_encryption_source(self):
        with self.assertRaises(ValueError):
            validate_encryption_source(
                Namespace(encryption_key_source='Microsoft.Keyvault', encryption_key_name=None,
                          encryption_key_version=None, encryption_key_vault=None, _cmd=MockCmd(self.cli)))

        with self.assertRaises(ValueError):
            validate_encryption_source(
                Namespace(encryption_key_source='Microsoft.Storage', encryption_key_name='key_name',
                          encryption_key_version='key_version', encryption_key_vault='https://example.com/key_uri'))


class TestGetSourceClientValidator(unittest.TestCase):
    def setUp(self):
        self.cli = MockCLI()

    def test_validate_with_container_name_blob(self):
        # source container name given, validator does not change namespace aside from ensuring source-client none
        ns = self._create_namespace(source_container='container2', destination_container='container1')
        get_source_file_or_blob_service_client_track2(MockCmd(self.cli), ns)
        self.assertIsNone(ns.source_client)
        self.assertEqual(ns.source_container, 'container2')
        self.assertEqual(ns.destination_container, 'container1')

    def test_validate_with_source_uri_blob(self):
        # source given in form of uri, source_container parsed from uri, source and dest account are the same
        ns = self._create_namespace(source_uri='https://storagename.blob.core.windows.net/container2',
                                    destination_container='container1')
        with mock.patch('azure.cli.command_modules.storage._validators._query_account_key', return_value="fake_key"):
            get_source_file_or_blob_service_client_track2(MockCmd(self.cli), ns)
        self.assertEqual(ns.source_container, 'container2')
        self.assertIsNotNone(ns.source_client)
        self.assertEqual(ns.destination_container, 'container1')

    def test_validate_with_different_source_uri_sas_blob(self):
        # source given in form of uri, source_container parsed from uri, source and dest account are different
        ns = self._create_namespace(source_uri='https://othername.blob.core.windows.net/container2?some_sas_token',
                                    destination_container='container1')
        get_source_file_or_blob_service_client_track2(MockCmd(self.cli), ns)
        self.assertEqual(ns.source_container, 'container2')
        self.assertIsNotNone(ns.source_client)
        self.assertEqual(ns.source_client.account_name, 'othername')

    def test_validate_with_share_name_file(self):
        # source share name given, validator does not change namespace aside from ensuring source-client none
        ns = self._create_namespace(source_share='share2', destination_share='share1')
        get_source_file_or_blob_service_client_track2(MockCmd(self.cli), ns)
        self.assertIsNone(ns.source_client)
        self.assertEqual(ns.source_share, 'share2')
        self.assertEqual(ns.destination_share, 'share1')

    def test_validate_with_source_uri_file(self):
        # source given in form of uri, source_share parsed from uri, source and dest account are the same
        ns = self._create_namespace(source_uri='https://storagename.file.core.windows.net/share2',
                                    destination_share='share1')
        with mock.patch('azure.cli.command_modules.storage._validators._query_account_key', return_value="fake_key"):
            get_source_file_or_blob_service_client_track2(MockCmd(self.cli), ns)
        self.assertEqual(ns.source_share, 'share2')
        self.assertIsNotNone(ns.source_client)

    def test_validate_with_different_source_uri_sas_file(self):
        # source given in form of uri, source_share parsed from uri, source and dest account are different
        ns = self._create_namespace(source_uri='https://othername.file.core.windows.net/share2?some_sas_token',
                                    destination_share='share1')
        get_source_file_or_blob_service_client_track2(MockCmd(self.cli), ns)
        self.assertEqual(ns.source_share, 'share2')
        self.assertIsNotNone(ns.source_client)
        self.assertEqual(ns.source_client.account_name, 'othername')

    def test_validate_invalid_source_account_name_before_key_lookup(self):
        from azure.cli.core.azclierror import InvalidArgumentValueError
        name = 'https://src.blob.core.windows.net/?sig=topsecret'
        ns = self._create_namespace(source_account_name=name, source_container='container2',
                                    destination_container='container1')
        with mock.patch('azure.cli.command_modules.storage._validators._query_account_key') as query_account_key, \
                self.assertRaisesRegex(InvalidArgumentValueError, 'Invalid source storage account name') as ctx:
            get_source_file_or_blob_service_client_track2(MockCmd(self.cli), ns)
        query_account_key.assert_not_called()
        self.assertNotIn('topsecret', str(ctx.exception))

    def test_validate_negatives(self):
        # bad argument combinations
        with self.assertRaises(ValueError):
            get_source_file_or_blob_service_client_track2(
                MockCmd(self.cli),
                self._create_namespace(source_uri='https://storage_name.file.core.windows.net/share2',
                                       source_account_name='some_name'))

        with self.assertRaises(ValueError):
            get_source_file_or_blob_service_client_track2(MockCmd(self.cli), self._create_namespace(source_uri='faulty_uri'))

        with self.assertRaises(ValueError):
            get_source_file_or_blob_service_client_track2(
                MockCmd(self.cli),
                self._create_namespace(source_container='container_name', source_share='share_name'))

    def test_as_user_validator(self):
        ns = self._create_namespace(as_user=None)
        as_user_validator(ns)

        ns = self._create_namespace(as_user=False)
        as_user_validator(ns)

        ns = self._create_namespace(as_user=True, expiry=None)
        with self.assertRaises(ArgumentError):
            as_user_validator(ns)

        ns = self._create_namespace(as_user=True, expiry='2019-01-01')
        with self.assertRaises(ArgumentError):
            as_user_validator(ns)

        ns = self._create_namespace(as_user=True, expiry='2019-01-01', token_credential=None)
        with self.assertRaises(ArgumentError):
            as_user_validator(ns)

        ns = self._create_namespace(as_user=True, expiry='2019-01-01', token_credential='token')
        as_user_validator(ns)

    def _create_namespace(self, **kwargs):
        ns = Namespace(account_key='my_storage_key', account_name='storage_name', connection_string=None, dryrun=False,
                       pattern='*', sas_token=None, source_account_key=None, source_account_name=None,
                       source_client=None, source_container=None, source_sas=None, source_share=None, source_uri=None,
                       destination_container=None, destination_share=None)

        for key in kwargs:
            setattr(ns, key, kwargs[key])
        return ns


class TestAzcopyEndpointValidation(unittest.TestCase):
    def setUp(self):
        self.cli = MockCLI()
        self.cmd = MockCmd(self.cli)
        patcher = mock.patch(
            'azure.cli.command_modules.storage.azcopy.util._generate_sas_token',
            return_value='sig=test-signature')
        self.generate = patcher.start()
        self.addCleanup(patcher.stop)
        config = mock.patch('azure.cli.command_modules.storage._validators.get_config_value',
                            side_effect=lambda cmd, section, key, default: default)
        config.start()
        self.addCleanup(config.stop)

    def _add_sas(self, url, **kwargs):
        from azure.cli.command_modules.storage._validators import _add_sas_for_url
        args = dict(account_name='victim', account_key='a2V5', sas_token=None,
                    service='blob', resource_types='co', permissions='wac')
        args.update(kwargs)
        return _add_sas_for_url(self.cmd, url, **args)

    def test_reject_untrusted_sas_destinations(self):
        from azure.cli.core.azclierror import InvalidArgumentValueError
        urls = [
            'https://victim.blob.core.windows.net.attacker.example/c',
            'https://victim.blob.core.windows.net@attacker.example/c',
            'https://attacker.example/https://victim.blob.core.windows.net/c',
            'https://another.blob.core.windows.net/c',
            'https://victim.blob.core.windows.net:8443/c',
            'https://victim.blob.core.windows.net:0/c',
            'http://victim.blob.core.windows.net/c',
            'https://user@victim.blob.core.windows.net/c',
            'https://victim.blob.core.windows.net\\@attacker.example/c',
            'https://victim.blob.core.windows.net\n.attacker.example/c',
            'https://victim.blob.core.windows.net/c#fragment',
            'https://victim.blob.core.windows.net:invalid/c',
            ' https://victim.blob.core.windows.net/c',
            'https://victim.blob.core.windows.net /c',
            'https://victim.blob.core.windows.net/my\tfolder/*',
            'https://victim.blob.core.windows.net/my\nfolder/*',
            'https://victim.blob.core.windows.net/my\rfolder/*',
        ]
        for url in urls:
            for sas in (None, 'sig=existing-secret'):
                with self.subTest(url=url, supplied_sas=bool(sas)):
                    with self.assertRaises(InvalidArgumentValueError) as error:
                        self._add_sas(url, sas_token=sas)
                    self.assertNotIn('existing-secret', str(error.exception))
        self.generate.assert_not_called()

    def test_accept_account_endpoints(self):
        for service in ('blob', 'dfs', 'file'):
            for account in ('victim', 'victim-secondary'):
                url = 'https://{}.{}.core.windows.net/c'.format(account, service)
                with self.subTest(url=url):
                    result = self._add_sas(url, service='file' if service == 'file' else 'blob')
                    self.assertEqual(result, url + '?sig=test-signature')
        url = 'https://VICTIM.BLOB.CORE.WINDOWS.NET:443/c'
        self.assertEqual(self._add_sas(url, sas_token='?sig=provided'), url + '?sig=provided')

    def test_accept_active_cloud_endpoint(self):
        self.cli.cloud = Namespace(suffixes=Namespace(storage_endpoint='storage.example.test'))
        url = 'https://victim.blob.storage.example.test/c'
        self.assertEqual(self._add_sas(url), url + '?sig=test-signature')

    def test_accept_normalized_account_origins(self):
        for url in (
                'https://VICTIM.blob.core.windows.net:443/c',
                'https://victim.blob.core.windows.net./c',
                'https://victim.blob.core.windows.net\u3002/c'):
            with self.subTest(url=url):
                self.assertEqual(self._add_sas(url), url + '?sig=test-signature')

    def test_accept_normalized_connection_origins(self):
        for endpoint, url in (
                ('https://xn--bcher-kva.example', 'https://b\u00fccher.example:443/c'),
                ('http://[::1]:10000/account', 'http://[0:0:0:0:0:0:0:1]:10000/account/c'),
                ('https://configured.example.test.', 'https://configured.example.test/c')):
            with self.subTest(endpoint=endpoint, url=url):
                connection = 'AccountName=victim;AccountKey=a2V5;BlobEndpoint=' + endpoint
                self.assertEqual(self._add_sas(url, connection_string=connection), url + '?sig=test-signature')

    def test_custom_connection_endpoint(self):
        from azure.cli.core.azclierror import InvalidArgumentValueError
        connection = ('DefaultEndpointsProtocol=https;AccountName=victim;AccountKey=a2V5;'
                      'BlobEndpoint=https://configured.example.test')
        url = 'https://configured.example.test/c'
        self.assertEqual(self._add_sas(url, connection_string=connection), url + '?sig=test-signature')
        with self.assertRaises(InvalidArgumentValueError):
            self._add_sas('https://configured.example.test.attacker.example/c',
                          connection_string=connection)

    def test_connection_string_suffix_and_explicit_http_endpoint(self):
        connection = ('DefaultEndpointsProtocol=https;AccountName=victim;AccountKey=a2V5;'
                      'EndpointSuffix=storage.example.test')
        url = 'https://victim.blob.storage.example.test/c'
        self.assertEqual(self._add_sas(url, connection_string=connection), url + '?sig=test-signature')
        connection = ('AccountName=victim;AccountKey=a2V5;'
                      'BlobEndpoint=http://127.0.0.1:10000/victim')
        url = 'http://127.0.0.1:10000/victim/c'
        self.assertEqual(self._add_sas(url, connection_string=connection), url + '?sig=test-signature')

    def _copy_namespace(self, **kwargs):
        args = dict(source='./source', destination='./destination',
                    destination_container=None, destination_blob=None,
                    destination_share=None, destination_file_path=None,
                    source_container=None, source_blob=None, source_share=None, source_file_path=None,
                    source_account_name=None, source_account_key=None, source_connection_string=None,
                    source_sas=None, account_name=None, account_key=None, connection_string=None,
                    sas_token=None, auth_mode=None, _cmd=self.cmd)
        args.update(kwargs)
        return Namespace(**args)

    def test_copy_wildcard_paths_with_spaces(self):
        from azure.cli.command_modules.storage._validators import validate_azcopy_credential
        for side in ('source', 'destination'):
            for service, resource, path in (
                    ('blob', 'container', 'blob'), ('file', 'share', 'file_path')):
                for sas in (None, 'sig=provided'):
                    with self.subTest(side=side, service=service, supplied_sas=bool(sas)):
                        ns = self._copy_namespace(
                            **{side: None, side + '_' + resource: 'container',
                               side + '_' + path: 'my folder/*'},
                            account_name='victim', account_key='a2V5', sas_token=sas,
                            source_account_name='victim', source_account_key='a2V5', source_sas=sas)
                        self.generate.reset_mock()
                        validate_azcopy_credential(self.cmd, ns)
                        expected = 'https://victim.{}.core.windows.net/container/my folder/*?{}'.format(
                            service, sas or 'sig=test-signature')
                        self.assertEqual(getattr(ns, side), expected)
                        if sas:
                            self.generate.assert_not_called()
                        else:
                            self.generate.assert_called_once_with(
                                self.cmd, 'victim', 'a2V5', service,
                                resource_types='sco' if side == 'source' else 'co',
                                permissions='rl' if side == 'source' else 'wac')

    def test_copy_untrusted_urls_never_receive_sas(self):
        from azure.cli.command_modules.storage._validators import validate_azcopy_credential
        for url in ('https://victim.blob.core.windows.net.attacker.example/c',
                    'https://attacker.example/https://victim.blob.core.windows.net/c',
                    'https://bucket.s3.amazonaws.com/c'):
            for side in ('source', 'destination'):
                with self.subTest(url=url, side=side):
                    ns = self._copy_namespace(
                        **{side: url}, account_name='victim', account_key='a2V5', sas_token='sig=secret',
                        source_account_name='victim', source_account_key='a2V5', source_sas='sig=secret')
                    with mock.patch(
                            'azure.cli.command_modules.storage._validators.validate_client_parameters') as validate:
                        validate_azcopy_credential(self.cmd, ns)
                    self.assertEqual(getattr(ns, side), url)
                    validate.assert_not_called()
        self.generate.assert_not_called()

    def test_copy_normalized_account_origins(self):
        from azure.cli.command_modules.storage._validators import validate_azcopy_credential
        for side in ('source', 'destination'):
            for url in ('https://VICTIM.blob.core.windows.net:443/c',
                        'https://victim.blob.core.windows.net./c',
                        'https://victim.blob.core.windows.net\u3002/c'):
                with self.subTest(side=side, url=url):
                    ns = self._copy_namespace(
                        **{side: url}, account_key='a2V5', source_account_key='a2V5')
                    validate_azcopy_credential(self.cmd, ns)
                    self.assertEqual(getattr(ns, side), url + '?sig=test-signature')

    def test_copy_keeps_explicit_credential_account(self):
        from azure.cli.command_modules.storage._validators import validate_azcopy_credential
        from azure.cli.core.azclierror import InvalidArgumentValueError
        for side in ('source', 'destination'):
            with self.subTest(side=side):
                ns = self._copy_namespace(
                    **{side: 'https://another.blob.core.windows.net/c'},
                    account_name='victim', account_key='a2V5',
                    source_account_name='victim', source_account_key='a2V5')
                with mock.patch('azure.cli.command_modules.storage._validators.validate_client_parameters'):
                    with self.assertRaises(InvalidArgumentValueError):
                        validate_azcopy_credential(self.cmd, ns)
                self.assertEqual(ns.account_name, 'victim')
        self.generate.assert_not_called()

    def test_copy_configured_endpoint(self):
        from azure.cli.command_modules.storage._validators import validate_azcopy_credential
        connection = ('AccountName=victim;AccountKey=a2V5;'
                      'BlobEndpoint=https://configured.example.test')
        for side in ('source', 'destination'):
            with self.subTest(side=side):
                ns = self._copy_namespace(
                    **{side: 'https://configured.example.test/c'}, connection_string=connection,
                    source_connection_string=connection)
                validate_azcopy_credential(self.cmd, ns)
                self.assertEqual(getattr(ns, side), 'https://configured.example.test/c?sig=test-signature')

    def test_copy_sas_only_connection_strings(self):
        from azure.cli.command_modules.storage._validators import validate_azcopy_credential
        for endpoint_key, host in (('BlobEndpoint', 'blob.example.test'), ('FileEndpoint', 'file.example.test')):
            connection = '{}=https://{};SharedAccessSignature=sig=provided'.format(endpoint_key, host)
            for side in ('source', 'destination'):
                for url, expected in (
                        ('https://{}/c'.format(host), 'https://{}/c?sig=provided'.format(host)),
                        ('https://bucket.s3.amazonaws.com/c', 'https://bucket.s3.amazonaws.com/c')):
                    with self.subTest(endpoint_key=endpoint_key, side=side, url=url):
                        ns = self._copy_namespace(**{side: url}, connection_string=connection,
                                                  source_connection_string=connection)
                        validate_azcopy_credential(self.cmd, ns)
                        self.assertEqual(getattr(ns, side), expected)
        self.generate.assert_not_called()

    def test_fs_directory_callers_validate_endpoint(self):
        from azure.cli.command_modules.storage._validators import (
            validate_fs_directory_upload_destination_url, validate_fs_directory_download_source_url)
        from azure.cli.core.azclierror import InvalidArgumentValueError
        connection = ('AccountName=victim;AccountKey=a2V5;'
                      'BlobEndpoint=https://configured.example.test')
        for validator, side, resource_types, permissions in (
                (validate_fs_directory_upload_destination_url, 'destination', 'co', 'rwdlac'),
                (validate_fs_directory_download_source_url, 'source', 'co', 'rl')):
            for endpoint, valid in (('https://configured.example.test/fs', True),
                                    ('https://configured.example.test.attacker.example/fs', False)):
                with self.subTest(side=side, endpoint=endpoint):
                    ns = Namespace(account_name='victim', account_key='a2V5', sas_token=None,
                                   connection_string=connection,
                                   **{side + '_fs': 'fs', side + '_path': None})
                    with mock.patch('azure.cli.command_modules.storage._validators.cf_adls_file_system',
                                    return_value=Namespace(url=endpoint)):
                        self.generate.reset_mock()
                        if valid:
                            validator(self.cmd, ns)
                            self.assertEqual(getattr(ns, side), endpoint + '?sig=test-signature')
                            self.generate.assert_called_once_with(
                                self.cmd, 'victim', 'a2V5', 'blob',
                                resource_types=resource_types, permissions=permissions)
                        else:
                            with self.assertRaises(InvalidArgumentValueError):
                                validator(self.cmd, ns)
                            self.generate.assert_not_called()

    def test_external_urls_do_not_receive_credentials(self):
        from azure.cli.command_modules.storage._validators import _add_sas_for_url
        url = 'https://bucket.s3.amazonaws.com/c'
        result = _add_sas_for_url(self.cmd, url, 'victim', 'a2V5', 'sig=secret', None, 'co', 'wac')
        self.assertEqual(result, url)
        self.generate.assert_not_called()


class TestAzcopyValidator(unittest.TestCase):
    def setUp(self):
        self.cli = MockCLI()

    @mock.patch('azure.cli.command_modules.storage._validators._query_account_key', return_value=None)
    def test_validate_azcopy_credential(self, _query_key):
        from azure.cli.command_modules.storage._validators import validate_azcopy_credential
        ns = Namespace(source='https://testaccount1.s3.amazonaws.com/test/dir',
                       destination='https://testaccount2.blob.core.windows.net/test/blob',
                       destination_container=None, destination_blob=None,
                       destination_share=None, destination_file_path=None,
                       source_container=None, source_blob=None,
                       source_share=None, source_file_path=None,
                       source_account_name=None, source_account_key=None,
                       source_connection_string=None, source_sas=None,
                       account_name=None, account_key=None,
                       connection_string=None, sas_token=None, auth_mode=None,
                       _cmd=MockCmd(self.cli))
        validate_azcopy_credential(MockCmd(self.cli), ns)
        self.assertIsNotNone(ns.source)
        self.assertIsNotNone(ns.destination)

        ns = Namespace(source='./dir',
                       destination=None,
                       destination_container='destcon', destination_blob=None,
                       destination_share=None, destination_file_path=None,
                       source_container=None, source_blob=None,
                       source_share=None, source_file_path=None,
                       source_account_name=None, source_account_key=None,
                       source_connection_string=None, source_sas=None,
                       account_name='destacc', account_key=None,
                       connection_string=None, sas_token=None, auth_mode=None,
                       _cmd=MockCmd(self.cli))
        validate_azcopy_credential(MockCmd(self.cli), ns)
        self.assertIsNotNone(ns.source)
        self.assertIsNotNone(ns.destination)

        ns = Namespace(source=None,
                       destination=None,
                       destination_container=None, destination_blob=None,
                       destination_share='destshare', destination_file_path='dir/file',
                       source_container=None, source_blob=None,
                       source_share='srcshare', source_file_path='dir/file',
                       source_account_name='srcacc', source_account_key='mockacckey',
                       source_connection_string=None, source_sas=None,
                       account_name='destacc', account_key='mockacckey',
                       connection_string=None, sas_token=None, auth_mode=None,
                       _cmd=MockCmd(self.cli))
        validate_azcopy_credential(MockCmd(self.cli), ns)
        self.assertIsNotNone(ns.source)
        self.assertIsNotNone(ns.destination)


if __name__ == '__main__':
    unittest.main()
