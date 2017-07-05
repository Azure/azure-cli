# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import datetime
import json
import logging as logs
import pkgutil
import re
import sys
import time
import timeit
import traceback
from collections import OrderedDict, defaultdict
from importlib import import_module

from knack.arguments import ArgumentRegistry, CLICommandArgument
from knack.commands import CLICommandsLoader
from knack.log import get_logger
from knack.prompting import prompt_y_n, NoTTYException
from knack.util import CLIError

import six
from six import string_types, reraise

import azure.cli.core.telemetry as telemetry
from azure.cli.core.profiles import ResourceType

logger = get_logger(__name__)

# 1 hour in milliseconds
DEFAULT_QUERY_TIME_RANGE = 3600000


CONFIRM_PARAM_NAME = 'yes'

BLACKLISTED_MODS = ['context', 'shell', 'documentdb']


class VersionConstraint(object):
    def __init__(self, loader, resource_type, min_api=None, max_api=None):
        self._type = resource_type
        self._min_api = min_api
        self._max_api = max_api
        self._loader = loader
        self._ctx = loader.ctx
        self._cloud = loader.ctx.cloud

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def register_cli_argument(self, *args, **kwargs):
        if self._cloud.supported_api_version(self._type, min_api=self._min_api, max_api=self._max_api):
            self._loader.register_cli_argument(*args, **kwargs)
        else:
            from knack.arguments import ignore_type
            kwargs = {}
            args = tuple([args[0], args[1], ignore_type])
            self._loader.register_cli_argument(*args, **kwargs)

    def register_extra_cli_argument(self, *args, **kwargs):
        if self._cloud.supported_api_version(self._type, min_api=self._min_api, max_api=self._max_api):
            self._loader.register_extra_cli_argument(*args, **kwargs)

    def cli_command(self, *args, **kwargs):
        if self._cloud.supported_api_version(self._type, min_api=self._min_api, max_api=self._max_api):
            self._loader.cli_command(*args, **kwargs)


class LongRunningOperation(object):  # pylint: disable=too-few-public-methods

    def __init__(self, cli_ctx, start_msg='', finish_msg='',
                 poller_done_interval_ms=1000.0, progress_controller=None):

        self.ctx = cli_ctx
        self.start_msg = start_msg
        self.finish_msg = finish_msg
        self.poller_done_interval_ms = poller_done_interval_ms
        self.progress_controller = progress_controller or cli_ctx.get_progress_controller()
        self.deploy_dict = {}
        self.last_progress_report = datetime.datetime.now()

    def _delay(self):
        time.sleep(self.poller_done_interval_ms / 1000.0)

    def _generate_template_progress(self, correlation_id):  # pylint: disable=no-self-use
        """ gets the progress for template deployments """
        from azure.cli.core.commands.client_factory import get_mgmt_service_client
        from azure.monitor import MonitorClient

        if correlation_id is not None:  # pylint: disable=too-many-nested-blocks
            formatter = "eventTimestamp ge {}"

            end_time = datetime.datetime.utcnow()
            start_time = end_time - datetime.timedelta(seconds=DEFAULT_QUERY_TIME_RANGE)
            odata_filters = formatter.format(start_time.strftime('%Y-%m-%dT%H:%M:%SZ'))

            odata_filters = "{} and {} eq '{}'".format(odata_filters, 'correlationId', correlation_id)

            activity_log = get_mgmt_service_client(MonitorClient).activity_logs.list(filter=odata_filters)

            results = []
            max_events = 50  # default max value for events in list_activity_log
            for index, item in enumerate(activity_log):
                if index < max_events:
                    results.append(item)
                else:
                    break

            if results:
                for event in results:
                    update = False
                    long_name = event.resource_id.split('/')[-1]
                    if long_name not in self.deploy_dict:
                        self.deploy_dict[long_name] = {}
                        update = True
                    deploy_values = self.deploy_dict[long_name]

                    checked_values = {
                        str(event.resource_type.value): 'type',
                        str(event.status.value): 'status value',
                        str(event.event_name.value): 'request',
                    }
                    try:
                        checked_values[str(event.properties.get('statusCode', ''))] = 'status'
                    except AttributeError:
                        pass

                    if deploy_values.get('timestamp', None) is None or \
                            event.event_timestamp > deploy_values.get('timestamp'):
                        for value in checked_values:
                            if deploy_values.get(checked_values[value], None) != value:
                                update = True
                            deploy_values[checked_values[value]] = value
                        deploy_values['timestamp'] = event.event_timestamp

                        # don't want to show the timestamp
                        json_val = deploy_values.copy()
                        json_val.pop('timestamp', None)
                        status_val = deploy_values.get('status value', None)
                        if status_val and status_val != 'Started':
                            result = deploy_values['status value'] + ': ' + long_name
                            result += ' (' + deploy_values.get('type', '') + ')'

                            if update:
                                logger.info(result)

    def __call__(self, poller):
        from msrest.exceptions import ClientException
        correlation_message = ''
        self.progress_controller.begin()
        correlation_id = None

        az_logger = self.ctx.logging
        # TODO: Need a good way to actually get this....
        is_verbose = True

        while not poller.done():
            self.progress_controller.add(message='Running')
            try:
                # pylint: disable=protected-access
                correlation_id = json.loads(
                    poller._response.__dict__['_content'].decode())['properties']['correlationId']

                correlation_message = 'Correlation ID: {}'.format(correlation_id)
            except:  # pylint: disable=bare-except
                pass

            current_time = datetime.datetime.now()
            if is_verbose and current_time - self.last_progress_report >= datetime.timedelta(seconds=10):
                self.last_progress_report = current_time
                try:
                    self._generate_template_progress(correlation_id)
                except Exception as ex:  # pylint: disable=broad-except
                    logger.warning('%s during progress reporting: %s', getattr(type(ex), '__name__', type(ex)), ex)
            try:
                self._delay()
            except KeyboardInterrupt:
                self.progress_controller.stop()
                logger.error('Long running operation wait cancelled.  %s', correlation_message)
                raise

        try:
            result = poller.result()
        except ClientException as client_exception:
            from azure.cli.core.commands.arm import handle_long_running_operation_exception
            self.progress_controller.stop()
            handle_long_running_operation_exception(client_exception)

        self.progress_controller.end()
        return result


# pylint: disable=too-few-public-methods
class DeploymentOutputLongRunningOperation(LongRunningOperation):
    def __call__(self, result):
        from msrest.pipeline import ClientRawResponse
        from msrestazure.azure_operation import AzureOperationPoller

        if isinstance(result, AzureOperationPoller):
            # most deployment operations return a poller
            result = super(DeploymentOutputLongRunningOperation, self).__call__(result)
            outputs = result.properties.outputs
            return {key: val['value'] for key, val in outputs.items()} if outputs else {}
        elif isinstance(result, ClientRawResponse):
            # --no-wait returns a ClientRawResponse
            return None

        # --validate returns a 'normal' response
        return result

def _load_module_command_loader(loader, args, mod):
    loader_name = '{}CommandsLoader'.format(mod.capitalize())
    module = import_module('azure.cli.command_modules.' + mod)
    module_loader = getattr(module, loader_name, None)
    if module_loader:
        module_loader = module_loader(ctx=loader.ctx)
        module_command_table = module_loader.load_command_table(args)
        loader.command_table.update(module_command_table)
        loader.loaders.append(module_loader)  # this will be used later by the load_arguments method
    else:
        #logger.warning("Command module '%s' missing %s...", mod, loader_name)
        pass

def get_command_table(loader, args, module_name=None):
    '''Loads command table(s)
    When `module_name` is specified, only commands from that module will be loaded.
    If the module is not found, all commands are loaded.
    '''
    if not isinstance(loader, CLICommandsLoader):
        raise TypeError("argument 'loader' expected type CLICommandsLoader. Actual '{}'".format(type(loader)))
    loaded = False
    if module_name and module_name not in BLACKLISTED_MODS:
        try:
            _load_module_command_loader(loader, args, mod)
            logger.debug("Successfully loaded command table from module '%s'.", module_name)
            loaded = True
        except ImportError:
            logger.debug("Loading all installed modules as module with name '%s' not found.", module_name)
        except Exception:  # pylint: disable=broad-except
            pass
    if not loaded:
        installed_command_modules = []
        try:
            mods_ns_pkg = import_module('azure.cli.command_modules')
            installed_command_modules = [modname for _, modname, _ in
                                         pkgutil.iter_modules(mods_ns_pkg.__path__)
                                         if modname not in BLACKLISTED_MODS]
        except ImportError:
            pass
        logger.debug('Installed command modules %s', installed_command_modules)
        cumulative_elapsed_time = 0
        for mod in installed_command_modules:
            try:
                start_time = timeit.default_timer()
                _load_module_command_loader(loader, args, mod)
                elapsed_time = timeit.default_timer() - start_time
                logger.debug("Loaded module '%s' in %.3f seconds.", mod, elapsed_time)
                cumulative_elapsed_time += elapsed_time
            except Exception as ex:  # pylint: disable=broad-except
                # Changing this error message requires updating CI script that checks for failed
                # module loading.
                logger.error("Error loading command module '%s'", mod)
                telemetry.set_exception(exception=ex, fault_type='module-load-error-' + mod,
                                        summary='Error loading module: {}'.format(mod))
                logger.debug(traceback.format_exc())
        logger.debug("Loaded all modules in %.3f seconds. "
                     "(note: there's always an overhead with the first module loaded)",
                     cumulative_elapsed_time)

    _update_command_definitions(loader)
    ordered_commands = OrderedDict(loader.command_table)
    return ordered_commands


def _load_client_exception_class():
    # Since loading msrest is expensive, we avoid it until we have to
    from msrest.exceptions import ClientException
    return ClientException


def _load_validation_error_class():
    # Since loading msrest is expensive, we avoid it until we have to
    from msrest.exceptions import ValidationError
    return ValidationError


def _load_azure_exception_class():
    # Since loading msrest is expensive, we avoid it until we have to
    from azure.common import AzureException
    return AzureException


def _is_paged(obj):
    # Since loading msrest is expensive, we avoid it until we have to
    import collections
    if isinstance(obj, collections.Iterable) \
            and not isinstance(obj, list) \
            and not isinstance(obj, dict):
        from msrest.paging import Paged
        return isinstance(obj, Paged)
    return False


def _is_poller(obj):
    # Since loading msrest is expensive, we avoid it until we have to
    if obj.__class__.__name__ == 'AzureOperationPoller':
        from msrestazure.azure_operation import AzureOperationPoller
        return isinstance(obj, AzureOperationPoller)
    return False

def _user_confirmed(confirmation, command_args):
    if callable(confirmation):
        return confirmation(command_args)
    try:
        if isinstance(confirmation, string_types):
            return prompt_y_n(confirmation)
        return prompt_y_n('Are you sure you want to perform this operation?')
    except NoTTYException:
        logger.warning('Unable to prompt for confirmation as no tty available. Use --yes.')
        return False


def _check_rp_not_registered_err(ex):
    try:
        response = json.loads(ex.response.content.decode())
        if response['error']['code'] == 'MissingSubscriptionRegistration':
            match = re.match(r".*'(.*)'", response['error']['message'])
            return match.group(1)
    except Exception:  # pylint: disable=broad-except
        pass
    return None


def _register_rp(rp):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    rcf = get_mgmt_service_client(ResourceType.MGMT_RESOURCE_RESOURCES)
    logger.warning("Resource provider '%s' used by the command is not "
                   "registered. We are registering for you", rp)
    rcf.providers.register(rp)
    while True:
        time.sleep(10)
        rp_info = rcf.providers.get(rp)
        if rp_info.registration_state == 'Registered':
            logger.warning("Registration succeeded.")
            break


def _update_command_definitions(loader):
    for command_name, command in loader.command_table.items():
        for argument_name in command.arguments:
            overrides = loader.argument_registry.get_cli_argument(command_name, argument_name)
            command.update_argument(argument_name, overrides)

    # Add any arguments explicitly registered for this command
    for argument_name, argument_definition in loader.extra_argument_registry[command_name].items():
        command.arguments[argument_name] = argument_definition
        command.update_argument(argument_name, loader.argument_registry.get_cli_argument(command_name, argument_name))

