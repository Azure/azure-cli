# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import site
import logging
from six import StringIO

from azure.cli.core.util import CLIError
from azure.cli.core._config import az_config
import azure.cli.core.azlogging as azlogging
from azure.cli.core.prompting import prompt_y_n, NoTTYException

logger = azlogging.get_az_logger(__name__)

CLI_PACKAGE_NAME = 'azure-cli'
COMPONENT_PREFIX = 'azure-cli-'


def _deprecate_warning():
    logger.warning("The 'component' commands will be deprecated in the future.")
    logger.warning("az component and subcommands may not work unless the CLI is installed with pip.")
    try:
        ans = prompt_y_n("Are you sure you want to continue?", default='n')
        if not ans:
            raise CLIError('Operation cancelled.')
    except NoTTYException:
        pass


def list_components():
    """ List the installed components """
    _deprecate_warning()
    import pip
    return sorted([{'name': dist.key.replace(COMPONENT_PREFIX, ''), 'version': dist.version}
                   for dist in pip.get_installed_distributions(local_only=True)
                   if dist.key.startswith(COMPONENT_PREFIX)], key=lambda x: x['name'])


def _get_first_party_pypi_command_modules():
    try:
        import xmlrpclib
    except ImportError:
        import xmlrpc.client as xmlrpclib  # pylint: disable=import-error
    results = []
    client = xmlrpclib.ServerProxy('https://pypi.python.org/pypi')
    pypi_hits = client.search({'author': 'Microsoft Corporation', 'author_email': 'azpycli'})
    for hit in pypi_hits:
        if hit['name'].startswith(COMPONENT_PREFIX):
            comp_name = hit['name'].replace(COMPONENT_PREFIX, '')
            results.append({
                'name': comp_name,
                'summary': hit['summary'],
                'version': hit['version']
            })
    return results


def list_available_components():
    """ List publicly available components that can be installed """
    _deprecate_warning()
    import pip
    available_components = []
    installed_component_names = [dist.key.replace(COMPONENT_PREFIX, '') for dist in
                                 pip.get_installed_distributions(local_only=True) if
                                 dist.key.startswith(COMPONENT_PREFIX)]

    pypi_results = _get_first_party_pypi_command_modules()
    logger.debug('The following components are already installed %s', installed_component_names)
    logger.debug("Found %d result(s)", len(pypi_results))

    for pypi_res in pypi_results:
        if pypi_res['name'] not in installed_component_names:
            available_components.append(pypi_res)
    if not available_components:
        logger.warning('All available components are already installed.')
    return available_components


def remove(component_name):
    """ Remove a component """
    _deprecate_warning()
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
    pip.logger.handlers = []
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
        package_index_trusted_host = az_config.get('component', 'package_index_trusted_host',
                                                   fallback=None)
        if package_index_url:
            pkg_index_options += ['--extra-index-url', package_index_url]
        else:
            raise CLIError('AZURE_COMPONENT_PACKAGE_INDEX_URL environment variable not set and not '
                           'specified in config. AZURE_COMPONENT_PACKAGE_INDEX_TRUSTED_HOST may '
                           'also need to be set.\nIf executing az with sudo, you may want sudo\'s '
                           '-E and -H flags.')
        pkg_index_options += ['--trusted-host',
                              package_index_trusted_host] if package_index_trusted_host else []
    pip_args = ['install'] + options + package_list + pkg_index_options
    _run_pip(pip, pip_args)
    # Fix to make sure that we have empty __init__.py files for the azure site-packages folder.
    nspkg_pip_args = ['install'] + options + ['--force-reinstall', 'azure-nspkg', 'azure-mgmt-nspkg'] + pkg_index_options  # pylint: disable=line-too-long
    _run_pip(pip, nspkg_pip_args)


def _verify_additional_components(components, private, allow_third_party):
    # Don't verify as third party packages allowed or private server which we can't query
    if allow_third_party or private:
        return
    third_party = []
    first_party_component_names = [r['name']for r in _get_first_party_pypi_command_modules()]
    for c in components:
        if c not in first_party_component_names:
            third_party.append(c)
    if third_party:
        raise CLIError("The following component(s) '{}' are third party or not available. "
                       "Use --allow-third-party to install "
                       "third party packages.".format(', '.join(third_party)))


def update(private=False,
           pre=False,
           link=None,
           additional_components=None,
           allow_third_party=False):
    """ Update the CLI and all installed components """
    _deprecate_warning()
    import pip
    # Update the CLI itself
    package_list = [CLI_PACKAGE_NAME]
    # Update all the packages we currently have installed
    package_list += [dist.key for dist in pip.get_installed_distributions(local_only=True)
                     if dist.key.startswith(COMPONENT_PREFIX)]
    # Install/Update any new components the user requested
    if additional_components:
        _verify_additional_components(additional_components, private, allow_third_party)
        for c in additional_components:
            package_list += [COMPONENT_PREFIX + c]
    _install_or_update(package_list, link, private, pre)
