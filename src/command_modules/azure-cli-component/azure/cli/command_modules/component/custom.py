# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import site
import logging
from six import StringIO

from azure.cli.core._util import CLIError
from azure.cli.core._config import az_config
import azure.cli.core._logging as _logging

logger = _logging.get_az_logger(__name__)

CLI_PACKAGE_NAME = 'azure-cli'
COMPONENT_PREFIX = 'azure-cli-'

def _verify_not_dev():
    from azure.cli.core import __version__ as core_version
    dev_version = core_version.endswith('+dev')
    if dev_version:
        raise CLIError('This operation is not available in the developer version of the CLI.')

def list_components():
    """ List the installed components """
    _verify_not_dev()
    import pip
    return sorted([{'name': dist.key.replace(COMPONENT_PREFIX, ''), 'version': dist.version}
                   for dist in pip.get_installed_distributions(local_only=True)
                   if dist.key.startswith(COMPONENT_PREFIX)], key=lambda x: x['name'])

def list_available_components():
    """ List publicly available components that can be installed """
    _verify_not_dev()
    import pip
    available_components = []
    installed_component_names = [dist.key.replace(COMPONENT_PREFIX, '') \
                                for dist in pip.get_installed_distributions(local_only=True)
                                 if dist.key.startswith(COMPONENT_PREFIX)]
    try:
        import xmlrpclib
    except ImportError:
        import xmlrpc.client as xmlrpclib #pylint: disable=import-error
    client = xmlrpclib.ServerProxy('https://pypi.python.org/pypi')
    pypi_hits = client.search({'author': 'Microsoft Corporation', 'author_email': 'azpycli'})
    logger.debug('The following components are already installed %s', installed_component_names)
    logger.debug("Found %d result(s)", len(pypi_hits))
    for hit in pypi_hits:
        if hit['name'].startswith(COMPONENT_PREFIX):
            comp_name = hit['name'].replace(COMPONENT_PREFIX, '')
            if comp_name not in installed_component_names:
                available_components.append({
                    'name': comp_name,
                    'summary': hit['summary'],
                    'version': hit['version']
                })
    if not available_components:
        logger.warning('All available components are already installed.')
    return available_components

def remove(component_name):
    """ Remove a component """
    _verify_not_dev()
    if component_name in ['nspkg', 'core']:
        raise CLIError("This component cannot be removed, it is required for the CLI to function.")
    import pip
    full_component_name = COMPONENT_PREFIX + component_name
    found = bool([dist for dist in pip.get_installed_distributions(local_only=True)
                  if dist.key == full_component_name])
    if found:
        options = ['--isolated', '--yes']
        pip_args = ['uninstall'] + options + ['--disable-pip-version-check', full_component_name]
        _run_pip(pip, pip_args)
    else:
        raise CLIError("Component not installed.")

def _run_pip(pip, pip_exec_args):
    log_stream = StringIO()
    log_handler = logging.StreamHandler(log_stream)
    log_handler.setFormatter(logging.Formatter('%(name)s : %(message)s'))
    pip.logger.addHandler(log_handler)
    # Don't propagate to root logger as we catch the pip logs in our own log stream
    pip.logger.propagate = False
    logger.debug('Running pip: %s %s', pip, pip_exec_args)
    status_code = pip.main(pip_exec_args)
    log_output = log_stream.getvalue()
    logger.debug(log_output)
    log_stream.close()
    if status_code > 0:
        if '[Errno 13] Permission denied' in log_output:
            raise CLIError('Permission denied. Run command with --debug for more information.\n'
                           'If executing az with sudo, you may want sudo\'s -E and -H flags.')
        raise CLIError('An error occurred. Run command with --debug for more information.\n'
                       'If executing az with sudo, you may want sudo\'s -E and -H flags.')

def _installed_in_user():
    try:
        return __file__.startswith(site.getusersitepackages())
    except (TypeError, AttributeError):
        return False

def _install_or_update(package_list, link, private, pre):
    import pip
    options = ['--isolated', '--disable-pip-version-check', '--upgrade']
    if pre:
        options.append('--pre')
    if _installed_in_user():
        options.append('--user')
    pkg_index_options = ['--find-links', link] if link else []
    if private:
        package_index_url = az_config.get('component', 'package_index_url', fallback=None)
        package_index_trusted_host = az_config.get('component', 'package_index_trusted_host', fallback=None) #pylint: disable=line-too-long
        if package_index_url:
            pkg_index_options += ['--extra-index-url', package_index_url]
        else:
            raise CLIError('AZURE_COMPONENT_PACKAGE_INDEX_URL environment variable not set and not specified in config. ' #pylint: disable=line-too-long
                           'AZURE_COMPONENT_PACKAGE_INDEX_TRUSTED_HOST may also need to be set.\n'
                           'If executing az with sudo, you may want sudo\'s -E and -H flags.') #pylint: disable=line-too-long
        pkg_index_options += ['--trusted-host', package_index_trusted_host] if package_index_trusted_host else [] #pylint: disable=line-too-long
    pip_args = ['install'] + options + package_list + pkg_index_options
    _run_pip(pip, pip_args)

def update(private=False, pre=False, link=None, additional_components=None):
    """ Update the CLI and all installed components """
    _verify_not_dev()
    import pip
    # Update the CLI itself
    package_list = [CLI_PACKAGE_NAME]
    # Update all the packages we currently have installed
    package_list += [dist.key for dist in pip.get_installed_distributions(local_only=True)
                     if dist.key.startswith(COMPONENT_PREFIX)]
    # Install/Update any new components the user requested
    if additional_components:
        for c in additional_components:
            package_list += [COMPONENT_PREFIX + c]
    _install_or_update(package_list, link, private, pre)
