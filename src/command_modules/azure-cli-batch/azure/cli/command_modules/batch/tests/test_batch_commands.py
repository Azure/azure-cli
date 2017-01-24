import os
import unittest
import datetime
import isodate
from .. import _validators
from .. import _command_type

class TestObj(object):
    #pylint: disable=too-many-instance-attributes,too-few-public-methods
    pass

class TestBatchValidators(unittest.TestCase):
    #pylint: disable=attribute-defined-outside-init,no-member

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

    #def test_batch_certificate_reference_format(self):

    #    cert = _validators.certificate_reference_format("thumbprint_lkjsahakjg")
    #    self.assertEqual(ref, {'thumbprint': 'thumbprint_lkjsahakjg',
    #                           'thumbprint_algorithm': 'sha1'})

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
        ns.start_range = 11 #pylint: disable=redefined-variable-type
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
    #pylint: disable=attribute-defined-outside-init,protected-access

    def test_batch_build_prefix(self):
        resolved = _command_type._build_prefix('id', 'id', 'pool')
        self.assertEqual(resolved, 'id')

        resolved = _command_type._build_prefix('id', 'id', 'pool.start_task')
        self.assertEqual(resolved, 'start_task_id')

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

        path = "pool.start_task"
        self.assertEqual(_command_type.group_title(path), "Pool : Start Task")

        path = "pool.start_task.constraints"
        self.assertEqual(_command_type.group_title(path), "Pool : Start Task : Constraints")

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

    def test_batch_argument_tree(self):
        #pylint: disable=too-many-statements
        tree = _command_type.BatchArgumentTree(None)
        self.assertEqual(list(tree), [])

        tree.set_request_param("pool", "azure.batch.models.PoolAddParameter")
        self.assertEqual(tree._request_param, {'name': 'pool', 'model': 'PoolAddParameter'})

        self.assertEqual(tree.dequeue_argument("id"), {})
        self.assertFalse(tree.existing("id"))

        tree.queue_argument('id', 'pool', 'id', {}, 'str', ['vm_size', 'id'])
        tree.queue_argument('vm_size', 'pool', 'vm_size', {}, 'str', ['vm_size', 'id'])
        tree.queue_argument('target_dedicated', 'pool', 'target_dedicated', {}, 'int',
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
        ns.target_dedicated = 3
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
        self.assertEqual(sorted(siblings), ["id", "target_dedicated", "vm_size"])
        siblings = tree._get_siblings("pool.virtual_machine_configuration")
        self.assertEqual(sorted(siblings), ["node_agent_sku_id"])
        children = tree._get_children("pool.virtual_machine_configuration")
        self.assertEqual(sorted(children), ["node_agent_sku_id", "offer", "publisher", "version"])

        tree.dequeue_argument('node_agent_sku_id')
        self.assertEqual(len(list(tree)), 11)

