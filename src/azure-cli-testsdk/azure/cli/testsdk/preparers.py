# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import inspect
import functools

from .base import ScenarioTest, execute
from .exceptions import CliTestError
from .utilities import create_random_name
from .recording_processors import RecordingProcessor


# Core Utility

class AbstractPreparer(object):
    def __init__(self, name_prefix, name_len):
        self.name_prefix = name_prefix
        self.name_len = name_len
        self.resource_moniker = None
        self.resource_random_name = None
        self.test_class_instance = None

    def __call__(self, fn):
        def _preparer_wrapper(test_class_instance, **kwargs):
            if not isinstance(test_class_instance, ScenarioTest):
                raise CliTestError('The preparer decorator can be only used on the methods of '
                                   'class derived from {}'.format(ScenarioTest.__name__))
            self.test_class_instance = test_class_instance

            if test_class_instance.in_recording:
                resource_name = self.random_name
                if isinstance(self, RecordingProcessor):
                    test_class_instance.recording_processors.append(self)
            else:
                resource_name = self.moniker

            parameter_update = self.create_resource(resource_name, **kwargs)
            test_class_instance.addCleanup(lambda: self.remove_resource(resource_name, **kwargs))

            if parameter_update:
                kwargs.update(parameter_update)

            if not is_preparer_func(fn):
                # the next function is the actual test function. the kwargs need to be trimmed so
                # that parameters which are not required will not be passed to it.
                args, _, kw, _ = inspect.getargspec(fn)  # pylint: disable=deprecated-method
                if kw is None:
                    args = set(args)
                    for key in [k for k in kwargs.keys() if k not in args]:
                        del kwargs[key]

            fn(test_class_instance, **kwargs)

        setattr(_preparer_wrapper, '__is_preparer', True)
        functools.update_wrapper(_preparer_wrapper, fn)
        return _preparer_wrapper

    @property
    def moniker(self):
        if not self.resource_moniker:
            self.test_class_instance.test_resources_count += 1
            self.resource_moniker = '{}{:06}'.format(self.name_prefix,
                                                     self.test_class_instance.test_resources_count)
        return self.resource_moniker

    @property
    def random_name(self):
        if not self.resource_random_name:
            self.resource_random_name = create_random_name(self.name_prefix, self.name_len)
        return self.resource_random_name

    def create_resource(self, name, **kwargs):  # pylint: disable=unused-argument,no-self-use
        return {}

    def remove_resource(self, name, **kwargs):  # pylint: disable=unused-argument
        pass


# TODO: replaced by GeneralNameReplacer
class SingleValueReplacer(RecordingProcessor):
    # pylint: disable=no-member
    def process_request(self, request):
        request.uri = request.uri.replace(self.random_name, self.moniker)
        if request.body:
            body = str(request.body)
            if self.random_name in body:
                request.body = body.replace(self.random_name, self.moniker)

        return request

    def process_response(self, response):
        if response['body']['string']:
            response['body']['string'] = response['body']['string'].replace(self.random_name,
                                                                            self.moniker)

        self.replace_header(response, 'location', self.random_name, self.moniker)
        self.replace_header(response, 'azure-asyncoperation', self.random_name, self.moniker)

        return response


# Resource Group Preparer and its shorthand decorator

class ResourceGroupPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest.rg', parameter_name='resource_group',
                 parameter_name_for_location='resource_group_location', location='westus'):
        super(ResourceGroupPreparer, self).__init__(name_prefix, 90)
        self.location = location
        self.parameter_name = parameter_name
        self.parameter_name_for_location = parameter_name_for_location

    def create_resource(self, name, **kwargs):
        template = 'az group create --location {} --name {} --tag use=az-test'
        execute(template.format(self.location, name))
        return {self.parameter_name: name, self.parameter_name_for_location: self.location}

    def remove_resource(self, name, **kwargs):
        execute('az group delete --name {} --yes --no-wait'.format(name))


# Storage Account Preparer and its shorthand decorator

class StorageAccountPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self,  # pylint: disable=too-many-arguments
                 name_prefix='clitest', sku='Standard_LRS', location='westus',
                 parameter_name='storage_account', resource_group_parameter_name='resource_group',
                 skip_delete=True):
        super(StorageAccountPreparer, self).__init__(name_prefix, 24)
        self.location = location
        self.sku = sku
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete
        self.parameter_name = parameter_name

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        template = 'az storage account create -n {} -g {} -l {} --sku {}'
        execute(template.format(name, group, self.location, self.sku))
        return {self.parameter_name: name}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete:
            group = self._get_resource_group(**kwargs)
            execute('az storage account delete -n {} -g {} --yes'.format(name, group))

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a storage account a resource group is required. Please add ' \
                       'decorator @{} in front of this storage account preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))


# Utility

def is_preparer_func(fn):
    return getattr(fn, '__is_preparer', False)
