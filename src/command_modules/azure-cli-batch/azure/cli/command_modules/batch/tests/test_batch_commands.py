# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
import datetime
import isodate
import mock

from msrest.exceptions import ValidationError, ClientRequestError
from azure.batch import models, operations, BatchServiceClient
from azure.batch.batch_auth import SharedKeyCredentials
from knack.util import CLIError

from azure.cli.command_modules.batch import _validators
from azure.cli.command_modules.batch import _command_type


class TestObj(object):  # pylint: disable=too-few-public-methods
    pass


class TestBatchValidators(unittest.TestCase):
    def __init__(self, methodName):
        super(TestBatchValidators, self).__init__(methodName)
        pass

    def test_batch_datetime_format(self):
        obj = _validators.datetime_format("2017-01-24T15:47:24Z")
        self.assertIsInstance(obj, datetime.datetime)

        with self.assertRaises(ValueError):
            _validators.datetime_format("test")

    def test_batch_duration_format(self):
        obj = _validators.duration_format("P3Y6M4DT12H30M5S")
        self.assertIsInstance(obj, isodate.Duration)

        with self.assertRaises(ValueError):
            _validators.duration_format("test")

    def test_batch_metadata_item_format(self):
        meta = _validators.metadata_item_format("name=value")
        self.assertEqual(meta, {'name': 'name', 'value': 'value'})

        with self.assertRaises(ValueError):
            _validators.metadata_item_format("test")

        with self.assertRaises(ValueError):
            _validators.metadata_item_format("name=value=other")

    def test_batch_environment_setting_format(self):
        env = _validators.environment_setting_format("name=value")
        self.assertEqual(env, {'name': 'name', 'value': 'value'})

        with self.assertRaises(ValueError):
            _validators.environment_setting_format("test")

        with self.assertRaises(ValueError):
            _validators.environment_setting_format("name=value=other")

    def test_batch_application_package_reference_format(self):
        ref = _validators.application_package_reference_format("app_1")
        self.assertEqual(ref, {'application_id': 'app_1'})

        ref = _validators.application_package_reference_format("app#1")
        self.assertEqual(ref, {'application_id': 'app', 'version': '1'})

        ref = _validators.application_package_reference_format("app#1#RC")
        self.assertEqual(ref, {'application_id': 'app', 'version': '1#RC'})

    def test_batch_certificate_reference_format(self):
        cert = _validators.certificate_reference_format("thumbprint_lkjsahakjg")
        self.assertEqual(cert, {'thumbprint': 'thumbprint_lkjsahakjg',
                                'thumbprint_algorithm': 'sha1'})

    def test_batch_task_id_ranges_format(self):
        id_range = _validators.task_id_ranges_format("5-10")
        self.assertEqual(id_range, {'start': 5, 'end': 10})

        with self.assertRaises(ValueError):
            _validators.task_id_ranges_format("5")

        with self.assertRaises(ValueError):
            _validators.task_id_ranges_format("test")

        with self.assertRaises(ValueError):
            _validators.environment_setting_format("5-")

        with self.assertRaises(ValueError):
            _validators.environment_setting_format("5-test")

        with self.assertRaises(ValueError):
            _validators.environment_setting_format("start-end")

    def test_batch_resource_file_format(self):
        meta = _validators.resource_file_format("file=source")
        self.assertEqual(meta, {'file_path': 'file', 'blob_source': 'source'})

        with self.assertRaises(ValueError):
            _validators.resource_file_format("file")

        with self.assertRaises(ValueError):
            _validators.resource_file_format("file=source=mode")

    def test_batch_validate_options(self):
        ns = TestObj()
        _validators.validate_options(ns)
        self.assertFalse(hasattr(ns, 'ocp_range'))

        ns.start_range = "100"
        ns.end_range = None
        _validators.validate_options(ns)
        self.assertFalse(hasattr(ns, 'start_range'))
        self.assertFalse(hasattr(ns, 'end_range'))
        self.assertEqual(ns.ocp_range, "bytes=100-")

        del ns.ocp_range
        ns.start_range = None
        ns.end_range = 150
        _validators.validate_options(ns)
        self.assertFalse(hasattr(ns, 'start_range'))
        self.assertFalse(hasattr(ns, 'end_range'))
        self.assertEqual(ns.ocp_range, "bytes=0-150")

        del ns.ocp_range
        ns.start_range = 11
        ns.end_range = 22
        _validators.validate_options(ns)
        self.assertFalse(hasattr(ns, 'start_range'))
        self.assertFalse(hasattr(ns, 'end_range'))
        self.assertEqual(ns.ocp_range, "bytes=11-22")

    def test_batch_validate_file_destination(self):
        ns = TestObj()
        _validators.validate_file_destination(ns)
        self.assertFalse(hasattr(ns, 'destination'))

        ns.destination = os.path.dirname(__file__)
        ns.file_name = "/wd/stdout.txt"
        _validators.validate_file_destination(ns)
        self.assertEqual(ns.destination, os.path.join(os.path.dirname(__file__), 'stdout.txt'))

        ns.destination = __file__
        with self.assertRaises(ValueError):
            _validators.validate_file_destination(ns)

        ns.destination = os.path.join(os.path.dirname(__file__), 'test.txt')
        _validators.validate_file_destination(ns)
        self.assertEqual(ns.destination, os.path.join(os.path.dirname(__file__), 'test.txt'))

        ns.destination = "X:\\test.txt"
        with self.assertRaises(ValueError):
            _validators.validate_file_destination(ns)


class TestBatchParser(unittest.TestCase):
    # pylint: disable=protected-access

    def test_batch_build_prefix(self):
        resolved = _command_type._build_prefix('id', 'id', 'pool')
        self.assertEqual(resolved, 'id')

        resolved = _command_type._build_prefix('id', 'id', 'pool.start_task')
        self.assertEqual(resolved, 'start_task_id')

        resolved = _command_type._build_prefix('id', 'id', 'job_schedule.job_specification')
        self.assertEqual(resolved, 'job_id')

        resolved = _command_type._build_prefix('properties_id', 'id', 'pool.start_task.properties')
        self.assertEqual(resolved, 'start_task_id')

        resolved = _command_type._build_prefix('start_task_id', 'id', 'pool.start_task.properties')
        self.assertEqual(resolved, 'pool_id')

        resolved = _command_type._build_prefix('pool_id', 'id', 'pool.start_task.properties')
        self.assertEqual(resolved, 'pool_id')

    def test_batch_find_param_type(self):
        model = TestObj()
        model.__doc__ = """
    :param name: The name of the environment variable.
    :type name: str
    :param value: The value of the environment variable.
"""
        self.assertEqual(_command_type.find_param_type(model, 'name'), 'str')

        model.__doc__ = """
        :param pool_get_options: Additional parameters for the operation
        :type pool_get_options: :class:`PoolGetOptions
         <azure.batch.models.PoolGetOptions>`
        :param dict custom_headers: headers that will be added to the request
"""
        self.assertEqual(_command_type.find_param_type(model, 'pool_get_options'),
                         ':class:`PoolGetOptions<azure.batch.models.PoolGetOptions>`')

        model.__doc__ = '''
    :param node_fill_type: How tasks should be distributed across compute
     nodes. Possible values include: 'spread', 'pack', 'unmapped'
    :type node_fill_type: str or :class:`ComputeNodeFillType
     <azure.batch.models.ComputeNodeFillType>`
    """
'''
        self.assertEqual(_command_type.find_param_type(model, 'node_fill_type'),
                         'str or :class:`ComputeNodeFillType' +
                         '<azure.batch.models.ComputeNodeFillType>`')

        model.__doc__ = """
    :param name: The name of the environment variable.
    :type name:str
    :raises: BatchException
"""
        self.assertEqual(_command_type.find_param_type(model, 'name'), 'str')

    def test_batch_find_param_help(self):
        model = TestObj()
        model.__doc__ = """
        :param pool_id: The id of the pool to get.
        :type pool_id: str
        :param pool_get_options: Additional parameters for the operation
        :type pool_get_options: :class:`PoolGetOptions
         <azure.batch.models.PoolGetOptions>`
"""
        self.assertEqual(_command_type.find_param_help(model, 'pool_id'),
                         'The id of the pool to get.')
        self.assertEqual(_command_type.find_param_help(model, 'pool_get_options'),
                         'Additional parameters for the operation')

        model.__doc__ = """
    :param node_fill_type: How tasks should be distributed across compute
     nodes. Possible values include: 'spread', 'pack', 'unmapped'
    :type node_fill_type: str or :class:`ComputeNodeFillType
     <azure.batch.models.ComputeNodeFillType>`
"""
        self.assertEqual(_command_type.find_param_help(model, 'node_fill_type'),
                         "How tasks should be distributed across compute nodes. " +
                         "Possible values include: 'spread', 'pack', 'unmapped'")

    def test_batch_find_return_type(self):
        model = TestObj()
        model.__doc__ = """
    :param node_fill_type: How tasks should be distributed across compute
     nodes. Possible values include: 'spread', 'pack', 'unmapped'
    :type node_fill_type: str or :class:`ComputeNodeFillType
     <azure.batch.models.ComputeNodeFillType>`
"""
        self.assertIsNone(_command_type.find_return_type(model))

        model.__doc__ = """
        :type callback: Callable[Bytes, response=None]
        :param operation_config: :ref:`Operation configuration
         overrides<msrest:optionsforoperations>`.
        :rtype: Generator
        :rtype: :class:`ClientRawResponse<msrest.pipeline.ClientRawResponse>`
         if raw=true
"""
        self.assertEqual(_command_type.find_return_type(model), 'Generator')

    def test_batch_class_name(self):
        type_str = ":class:`ComputeNodeFillType<azure.batch.models.ComputeNodeFillType>`"
        self.assertEqual(_command_type.class_name(type_str),
                         "azure.batch.models.ComputeNodeFillType")

        type_str = "str or :class:`ComputeNodeFillType<azure.batch.models.ComputeNodeFillType>`"
        self.assertEqual(_command_type.class_name(type_str),
                         "azure.batch.models.ComputeNodeFillType")

    def test_batch_operations_name(self):
        op_str = "PythonTestCase"
        self.assertEqual(_command_type.operations_name(op_str), "python_test_case")

        op_str = "PythonTestCaseOperations"
        self.assertEqual(_command_type.operations_name(op_str), "python_test_case")

        op_str = "Python"
        self.assertEqual(_command_type.operations_name(op_str), "python")

        op_str = "python"
        self.assertEqual(_command_type.operations_name(op_str), "python")

    def test_batch_full_name(self):
        arg_details = {'path': 'pool.start_task', 'root': 'id'}
        self.assertEqual(_command_type.full_name(arg_details), 'pool.start_task.id')

    def test_batch_group_title(self):
        path = "pool"
        self.assertEqual(_command_type.group_title(path), "Pool")

        path = "pool_patch_parameter"
        self.assertEqual(_command_type.group_title(path), "Pool")

        path = "pool_update_parameter"
        self.assertEqual(_command_type.group_title(path), "Pool")

        path = "pool_update_properties_parameter"
        self.assertEqual(_command_type.group_title(path), "Pool Update Properties")

        path = "pool.start_task"
        self.assertEqual(_command_type.group_title(path), "Pool: Start Task")

        path = "pool.start_task.constraints"
        self.assertEqual(_command_type.group_title(path), "Pool: Start Task: Constraints")

    def test_batch_arg_name(self):
        self.assertEqual(_command_type.arg_name("pool_id"), "--pool-id")
        self.assertEqual(_command_type.arg_name("id"), "--id")
        self.assertEqual(_command_type.arg_name("start_task_id"), "--start-task-id")

    def test_batch_format_options_name(self):
        op = "azure.batch.operations.pool_opterations#PoolOperations.get"
        self.assertEqual(_command_type.format_options_name(op), "pool_get_options")

        op = "azure.batch.operations.pool_opterations#PoolOperations.upgrade_os"
        self.assertEqual(_command_type.format_options_name(op), "pool_upgrade_os_options")

        op = "azure.batch.operations.pool_opterations#JobScheduleOperations.get"
        self.assertEqual(_command_type.format_options_name(op), "job_schedule_get_options")

    def test_batch_argument_tree(self):  # pylint: disable=too-many-statements
        tree = _command_type.BatchArgumentTree(None, None)
        self.assertEqual(list(tree), [])

        tree.set_request_param("pool", "azure.batch.models.PoolAddParameter")
        self.assertEqual(tree._request_param, {'name': 'pool', 'model': 'PoolAddParameter'})

        self.assertEqual(tree.dequeue_argument("id"), {})
        self.assertFalse(tree.existing("id"))

        tree.queue_argument('id', 'pool', 'id', {}, 'str', ['vm_size', 'id'])
        tree.queue_argument('vm_size', 'pool', 'vm_size', {}, 'str', ['vm_size', 'id'])
        tree.queue_argument('target_dedicated_nodes', 'pool', 'target_dedicated_nodes', {}, 'int',
                            ['vm_size', 'id'])
        tree.queue_argument('command_line', 'pool.start_task', 'command_line', {}, 'str',
                            ['command_line'])
        tree.queue_argument('run_elevated', 'pool.start_task', 'run_elevated', {}, 'bool',
                            ['command_line'])
        tree.queue_argument('node_agent_sku_id', 'pool.virtual_machine_configuration',
                            'node_agent_sku_id', {}, 'str',
                            ['node_agent_sku_id', 'image_reference.offer',
                             'image_reference.publisher'])
        tree.queue_argument('offer', 'pool.virtual_machine_configuration.image_reference',
                            'offer', {}, 'str', ['offer', 'publisher'])
        tree.queue_argument('publisher', 'pool.virtual_machine_configuration.image_reference',
                            'publisher', {}, 'str', ['offer', 'publisher'])
        tree.queue_argument('version', 'pool.virtual_machine_configuration.image_reference',
                            'version', {}, 'str', ['offer', 'publisher'])
        tree.queue_argument('subnet_id', 'pool.network_configuration', 'id', {}, 'str', ['id'])
        tree.queue_argument('os_family', 'pool.cloud_service_configuration', 'os_family', {},
                            'str', ['os_family'])
        tree.queue_argument('target_os_version', 'pool.cloud_service_configuration',
                            'target_os_version', {}, 'str', ['os_family'])

        self.assertEqual(len(list(tree)), 12)
        self.assertTrue(tree.existing('vm_size'))

        ns = TestObj()
        ns.id = None
        ns.vm_size = None
        ns.target_dedicated_nodes = 3
        ns.command_line = None
        ns.run_elevated = None
        ns.node_agent_sku_id = None
        ns.offer = None
        ns.publisher = None
        ns.version = None
        ns.subnet_id = None
        ns.os_family = None
        ns.target_os_version = None
        with self.assertRaises(ValueError):
            tree.parse(ns)
        ns.id = "test_pool"
        with self.assertRaises(ValueError):
            tree.parse(ns)
        ns.vm_size = "small"
        tree.parse(ns)
        ns.run_elevated = True
        with self.assertRaises(ValueError):
            tree.parse(ns)
        ns.command_line = "cmd"
        tree.parse(ns)
        ns.run_elevated = None
        tree.parse(ns)
        ns.offer = "offer"
        with self.assertRaises(ValueError):
            tree.parse(ns)
        ns.publisher = "publisher"
        with self.assertRaises(ValueError):
            tree.parse(ns)
        ns.node_agent_sku_id = "sku id"
        tree.parse(ns)

        with self.assertRaises(ValueError):
            tree.parse_mutually_exclusive(ns, False, ['pool.id', 'pool.vm_size'])
        ns.id = None
        tree.parse_mutually_exclusive(ns, False, ['pool.id', 'pool.vm_size'])
        ns.vm_size = None
        tree.parse_mutually_exclusive(ns, False, ['pool.id', 'pool.vm_size'])
        with self.assertRaises(ValueError):
            tree.parse_mutually_exclusive(ns, True, ['pool.id', 'pool.vm_size'])

        ns.id = None
        tree.parse_mutually_exclusive(ns, False, ['pool.id', 'pool.cloud_service_configuration'])
        with self.assertRaises(ValueError):
            tree.parse_mutually_exclusive(
                ns, True, ['pool.id', 'pool.cloud_service_configuration'])
        ns.id = "id"
        tree.parse_mutually_exclusive(
            ns, True, ['pool.id', 'pool.cloud_service_configuration'])
        ns.target_os_version = "4"
        with self.assertRaises(ValueError):
            tree.parse_mutually_exclusive(
                ns, True, ['pool.id', 'pool.cloud_service_configuration'])

        with self.assertRaises(ValueError):
            tree.parse_mutually_exclusive(
                ns, True, ['pool.virtual_machine_configuration',
                           'pool.cloud_service_configuration'])
        ns.target_os_version = None
        tree.parse_mutually_exclusive(
            ns, True, ['pool.virtual_machine_configuration',
                       'pool.cloud_service_configuration'])
        ns.publisher = None
        ns.offer = None
        ns.node_agent_sku_id = None
        tree.parse_mutually_exclusive(
            ns, False, ['pool.virtual_machine_configuration',
                        'pool.cloud_service_configuration'])
        with self.assertRaises(ValueError):
            tree.parse_mutually_exclusive(ns, True, ['pool.virtual_machine_configuration',
                                                     'pool.cloud_service_configuration'])

        siblings = tree._get_siblings("pool")
        self.assertEqual(sorted(siblings), ["id", "target_dedicated_nodes", "vm_size"])
        siblings = tree._get_siblings("pool.virtual_machine_configuration")
        self.assertEqual(sorted(siblings), ["node_agent_sku_id"])
        children = tree._get_children("pool.virtual_machine_configuration")
        self.assertEqual(sorted(children), ["node_agent_sku_id", "offer", "publisher", "version"])

        tree.dequeue_argument('node_agent_sku_id')
        self.assertEqual(len(list(tree)), 11)


class TestBatchLoader(unittest.TestCase):  # pylint: disable=protected-access

    def setUp(self):
        def get_client(*_):
            creds = SharedKeyCredentials('test1', 'ZmFrZV9hY29jdW50X2tleQ==')
            return BatchServiceClient(creds, 'https://test1.westus.batch.azure.com/')

        self.command_pool = _command_type.AzureBatchDataPlaneCommand(
            'batch_unit_tests',
            'batch_tests_pool',
            'azure.batch.operations.pool_operations#PoolOperations.add',
            get_client, None, 3, None, None, None)
        self.command_job = _command_type.AzureBatchDataPlaneCommand(
            'batch_unit_tests',
            'batch_tests_job',
            'azure.batch.operations.job_operations#JobOperations.add',
            get_client, None, 3,
            ['job.job_manager_task', 'job.job_preparation_task',
             'job.job_release_task'], None, None)
        self.command_task = _command_type.AzureBatchDataPlaneCommand(
            'batch_unit_tests',
            'batch_tests_task',
            'azure.batch.operations.task_operations#TaskOperations.add',
            get_client, None, 1, None, None, None)
        self.command_file = _command_type.AzureBatchDataPlaneCommand(
            'batch_unit_tests',
            'batch_tests_file',
            'azure.batch.operations.file_operations#FileOperations.get_from_task',
            get_client, None, 3, None, None, None)
        self.command_list = _command_type.AzureBatchDataPlaneCommand(
            'batch_unit_tests',
            'batch_tests_list',
            'azure.batch.operations.job_operations#JobOperations.list',
            get_client, None, 3, None, None, None)
        self.command_delete = _command_type.AzureBatchDataPlaneCommand(
            'batch_unit_tests',
            'batch_tests_delete',
            'azure.batch.operations.pool_operations#PoolOperations.delete',
            get_client, None, 3, None, None, None)
        self.command_conflicts = _command_type.AzureBatchDataPlaneCommand(
            'batch_unit_tests',
            'batch_tests_conflicts',
            'azure.batch.operations.job_schedule_operations#JobScheduleOperations.add',
            get_client, None, 4, None, None, None)
        return super(TestBatchLoader, self).setUp()

    def test_batch_build_parameters(self):
        kwargs = {
            'id': 'poolid',
            'vm_size': 'small',
            'os_family': '4',
            'run_elevated': True,
            'command_line': 'cmd',
            'wait_for_success': None
        }
        params = {
            'id': {'path': 'pool', 'root': 'id'},
            'vm_size': {'path': 'pool', 'root': 'vm_size'},
            'os_family': {'path': 'pool.cloud_service_configuration', 'root': 'os_family'},
            'run_elevated': {'path': 'pool.start_task', 'root': 'run_elevated'},
            'command_line': {'path': 'pool.start_task', 'root': 'command_line'},
            'wait_for_success': {'path': 'pool.start_task', 'root': 'wait_for_success'}
        }
        for arg, details in params.items():
            value = kwargs.pop(arg)
            if value is None:
                continue
            params = self.command_pool._build_parameters(
                details['path'],
                kwargs,
                details['root'],
                value)

        request = {'pool': {'id': 'poolid', 'vm_size': 'small',
                            'cloud_service_configuration': {'os_family': '4'},
                            'start_task': {'run_elevated': True, 'command_line': 'cmd'}}}
        self.assertEqual(kwargs, request)

    def test_batch_options(self):
        self.command_delete._load_options_model(
            operations.pool_operations.PoolOperations.delete)
        self.assertIsInstance(self.command_delete._options_model, models.PoolDeleteOptions)
        self.assertEqual(sorted(self.command_delete._options_attrs),
                         ['client_request_id',
                          'if_match',
                          'if_modified_since',
                          'if_none_match',
                          'if_unmodified_since',
                          'ocp_date',
                          'return_client_request_id',
                          'timeout'])
        kwargs = {
            'if_match': None,
            'if_modified_since': 'abc',
            'if_none_match': None,
            'if_unmodified_since': 'def',
            'client_request_id': 'ignored'
        }
        self.command_delete._build_options(kwargs)
        self.assertIsInstance(kwargs['pool_delete_options'], models.PoolDeleteOptions)
        self.assertEqual(kwargs['pool_delete_options'].if_modified_since, 'abc')
        self.assertEqual(kwargs['pool_delete_options'].if_unmodified_since, 'def')
        self.assertIsNone(kwargs['pool_delete_options'].client_request_id)
        self.assertEqual(kwargs['pool_delete_options'].timeout, 30)
        self.assertIsNone(kwargs['pool_delete_options'].ocp_date)
        options = list(self.command_delete._process_options())
        self.assertEqual(len(options), 4)

    def test_batch_cancel_operation(self):
        from azure.cli.core.commands import _user_confirmed as user

        self.assertFalse(self.command_job._cancel_operation({}, config, user))
        self.assertFalse(self.command_job._cancel_operation({'yes': True}, config, user))
        self.assertFalse(self.command_delete._cancel_operation({'yes': True}, config, user))

    def test_batch_should_flatten(self):
        self.assertFalse(self.command_task._should_flatten('task.depends_on'))
        self.assertTrue(self.command_task._should_flatten('task'))
        self.assertFalse(self.command_job._should_flatten(
            'job.job_manager_task.constraints.something'))
        self.assertTrue(self.command_job._should_flatten('job.job_manager_task.constraints'))

    def test_batch_get_model_attrs(self):
        attrs = list(self.command_job._get_attrs(models.ResourceFile, 'task.resource_files'))
        self.assertEqual(len(attrs), 3)
        attrs = list(self.command_job._get_attrs(models.JobManagerTask, 'job.job_manager_task'))
        self.assertEqual(len(attrs), 13)
        attrs = list(self.command_job._get_attrs(models.JobAddParameter, 'job'))
        self.assertEqual(len(attrs), 10)

    def test_batch_load_arguments(self):
        # pylint: disable=too-many-statements
        handler = operations.pool_operations.PoolOperations.add
        args = list(self.command_pool._load_transformed_arguments(handler))
        self.assertEqual(len(args), 34)
        self.assertFalse('yes' in [a for a, _ in args])
        self.assertTrue('json_file' in [a for a, _ in args])
        self.assertFalse('destination' in [a for a, _ in args])
        self.assertTrue('application_package_references' in [a for a, _ in args])
        self.assertTrue('start_task_environment_settings' in [a for a, _ in args])
        self.assertTrue('certificate_references' in [a for a, _ in args])
        self.assertTrue('metadata' in [a for a, _ in args])
        handler = operations.job_operations.JobOperations.add
        args = list(self.command_job._load_transformed_arguments(handler))
        self.assertEqual(len(args), 13)
        self.assertFalse('yes' in [a for a, _ in args])
        self.assertTrue('json_file' in [a for a, _ in args])
        self.assertFalse('destination' in [a for a, _ in args])
        handler = operations.task_operations.TaskOperations.add
        args = list(self.command_task._load_transformed_arguments(handler))
        self.assertEqual(len(args), 7)
        self.assertFalse('yes' in [a for a, _ in args])
        self.assertTrue('json_file' in [a for a, _ in args])
        self.assertFalse('destination' in [a for a, _ in args])
        handler = operations.file_operations.FileOperations.get_from_task
        args = list(self.command_file._load_transformed_arguments(handler))
        self.assertEqual(len(args), 8)
        self.assertFalse('yes' in [a for a, _ in args])
        self.assertFalse('json_file' in [a for a, _ in args])
        self.assertTrue('destination' in [a for a, _ in args])
        handler = operations.job_operations.JobOperations.list
        args = list(self.command_list._load_transformed_arguments(handler))
        self.assertEqual(len(args), 3)
        self.assertFalse('yes' in [a for a, _ in args])
        self.assertFalse('json_file' in [a for a, _ in args])
        self.assertFalse('destination' in [a for a, _ in args])
        handler = operations.pool_operations.PoolOperations.delete
        args = list(self.command_delete._load_transformed_arguments(handler))
        self.assertEqual(len(args), 6)
        self.assertTrue('yes' in [a for a, _ in args])
        self.assertFalse('json_file' in [a for a, _ in args])
        self.assertFalse('destination' in [a for a, _ in args])
        handler = operations.job_schedule_operations.JobScheduleOperations.add
        args = [a for a, _ in self.command_conflicts._load_transformed_arguments(handler)]
        self.assertEqual(len(args), 47)
        self.assertTrue('id' in args)
        self.assertTrue('job_manager_task_id' in args)
        self.assertTrue('job_manager_task_max_wall_clock_time' in args)
        self.assertTrue('job_max_wall_clock_time' in args)
        self.assertTrue('allow_low_priority_node' in args)
        self.assertFalse('yes' in args)
        self.assertTrue('json_file' in args)
        self.assertFalse('destination' in args)

    def test_batch_execute_command(self):
        def function_result(_, **__):
            # pylint: disable=function-redefined
            raise ValidationError('maximum', 'id', '100')

        def get_op_handler(_):
            return function_result

        handler = operations.pool_operations.PoolOperations.add
        args = list(self.command_pool._load_transformed_arguments(handler))
        with mock.patch.object(_command_type, 'get_op_handler', get_op_handler):
            with self.assertRaises(CLIError):
                self.command_pool.cmd.execute(kwargs={'id': 'pool_test', 'vm_size': 'small'})

        def function_result(_, **__):
            # pylint: disable=function-redefined
            raise ClientRequestError('Bad Response')

        with mock.patch.object(_command_type, 'get_op_handler', get_op_handler):
            with self.assertRaises(CLIError):
                self.command_pool.cmd.execute(kwargs={'id': 'pool_test', 'vm_size': 'small'})

        def function_result(_, **__):
            # pylint: disable=function-redefined
            error = models.BatchError()
            error.code = 'InvalidHeaderValue'
            error.message = models.ErrorMessage('en-US', 'The value for one of the HTTP '
                                                'headers is not in the correct format')
            error.values = [
                models.BatchErrorDetail('HeaderName', 'Content-Type'),
                models.BatchErrorDetail('HeaderValue', 'application/json')
            ]
            exp = models.BatchErrorException(lambda x, y: error, None)
            raise exp

        with mock.patch.object(_command_type, 'get_op_handler', get_op_handler):
            with self.assertRaises(CLIError):
                self.command_pool.cmd.execute(kwargs={'id': 'pool_test', 'vm_size': 'small'})

        def function_result(_, **__):
            # pylint: disable=function-redefined
            self.assertIsInstance(kwargs['pool'], models.PoolAddParameter)
            self.assertEqual(kwargs['pool'].id, 'pool_id')
            self.assertEqual(kwargs['pool'].vm_size, 'small')
            self.assertEqual(kwargs['pool'].start_task.command_line, 'cmd')
            self.assertTrue('id' not in kwargs)
            return "Pool Created"

        json_file = {'id': 'pool_id', 'vmSize': 'small', 'startTask': {'commandLine': 'cmd'}}
        kwargs = {a: None for a, _ in args}
        kwargs['json_file'] = json_file
        with mock.patch.object(_command_type, 'get_op_handler', get_op_handler):
            result = self.command_pool.cmd.execute(kwargs=kwargs)
            self.assertEqual(result, "Pool Created")
