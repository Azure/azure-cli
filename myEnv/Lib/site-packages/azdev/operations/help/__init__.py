# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from __future__ import print_function

import os
import sys
import json
import shutil
import tempfile

from subprocess import check_call, check_output, CalledProcessError

from knack.util import CLIError
from knack.log import get_logger

from azure.cli.core.extension.operations import list_available_extensions, list_extensions as list_cli_extensions  # pylint: disable=import-error
from azdev.utilities import (
    display, heading, subheading,
    get_cli_repo_path, get_path_table
)

from azdev.utilities.tools import require_azure_cli
from azdev.operations.extensions import list_extensions as list_dev_cli_extensions

DOC_MAP_NAME = 'doc_source_map.json'
HELP_FILE_NAME = '_help.py'
DOC_SOURCE_MAP_PATH = os.path.join('doc', 'sphinx', 'azhelpgen', DOC_MAP_NAME)

_logger = get_logger(__name__)


def check_document_map():

    heading('Verify Document Map')

    cli_repo = get_cli_repo_path()

    map_path = os.path.join(cli_repo, DOC_SOURCE_MAP_PATH)
    help_files_in_map = _get_help_files_in_map(map_path)
    help_files_not_found = _map_help_files_not_found(cli_repo, help_files_in_map)
    help_files_to_add_to_map = _help_files_not_in_map(cli_repo, help_files_in_map)

    subheading('Results')
    if help_files_not_found or help_files_to_add_to_map:
        error_lines = []
        error_lines.append('Errors whilst verifying {}!'.format(DOC_MAP_NAME))
        if help_files_not_found:
            error_lines.append('The following files are in {} but do not exist:'.format(DOC_MAP_NAME))
            error_lines += help_files_not_found
        if help_files_to_add_to_map:
            error_lines.append('The following files should be added to {}:'.format(DOC_MAP_NAME))
            error_lines += help_files_to_add_to_map
        error_msg = '\n'.join(error_lines)
        raise CLIError(error_msg)
    display('Verified {} OK.'.format(DOC_MAP_NAME))


def _get_help_files_in_map(map_path):
    with open(map_path) as json_file:
        json_data = json.load(json_file)
        return [os.path.normpath(x) for x in list(json_data.values())]


def _map_help_files_not_found(cli_repo, help_files_in_map):
    missing_files = []
    for path in help_files_in_map:
        if not os.path.isfile(os.path.normpath(os.path.join(cli_repo, path))):
            missing_files.append(path)
    return missing_files


def _help_files_not_in_map(cli_repo, help_files_in_map):
    not_in_map = []
    for _, path in get_path_table()['mod'].items():
        help_path = os.path.join(path, HELP_FILE_NAME)
        help_path = help_path.replace(cli_repo.lower() + os.sep, '')
        if help_path in help_files_in_map or not os.path.isfile(help_path):
            continue
        not_in_map.append(help_path)
    return not_in_map


def generate_cli_ref_docs(output_dir=None, output_type=None, all_profiles=None):
    # require that azure cli installed and warn the users if extensions are installed.
    require_azure_cli()
    output_dir = _process_ref_doc_output_dir(output_dir)

    _warn_if_exts_installed()

    heading('Generate CLI Reference Docs')
    display("Docs will be placed in {}.".format(output_dir))

    if all_profiles:
        # Generate documentation for all commands and for all CLI profiles
        _generate_ref_docs_for_all_profiles(output_type, output_dir)
    else:
        # Generate documentation for all comamnds
        _call_sphinx_build(output_type, output_dir)

    display("\nThe {} files are in {}".format(output_type, output_dir))


def generate_extension_ref_docs(output_dir=None, output_type=None):
    # require that azure cli installed
    require_azure_cli()
    output_dir = _process_ref_doc_output_dir(output_dir)

    heading('Generate CLI Extensions Reference Docs')
    display("Docs will be placed in {}.".format(output_dir))

    display("Generating Docs for public extensions. Installed extensions will not be affected...")
    _generate_ref_docs_for_public_exts(output_type, output_dir)

    display("\nThe {} files are in {}".format(output_type, output_dir))


def _process_ref_doc_output_dir(output_dir):
    # handle output_dir
    # if non specified, store in "_build" in the current working directory
    if not output_dir:
        _logger.warning("No output directory was specified. Will use a temporary directory to store reference docs.")
        output_dir = tempfile.mkdtemp(prefix="doc_output_")
    # ensure output_dir exists otherwise create it
    output_dir = os.path.abspath(output_dir)
    if not os.path.exists(output_dir):
        existing_path = os.path.dirname(output_dir)
        base_dir = os.path.basename(output_dir)
        if not os.path.exists(existing_path):
            raise CLIError("Cannot create output directory {} in non-existent path {}."
                           .format(base_dir, existing_path))

        os.mkdir(output_dir)
    return output_dir


def _generate_ref_docs_for_all_profiles(output_type, base_output_dir):
    original_profile = None
    profile = ""
    try:
        # store original profile and get all profiles.
        original_profile = _get_current_profile()
        profiles = _get_profiles()
        _logger.info("Original Profile: %s", original_profile)

        for profile in profiles:
            # set profile and call sphinx build cmd
            profile_output_dir = os.path.join(base_output_dir, profile)
            _set_profile(profile)
            _call_sphinx_build(output_type, profile_output_dir)

            display("\nFinished generating files for profile {} in dir {}\n".format(output_type, profile_output_dir))

        # always set the profile back to the original profile after generating all docs.
        _set_profile(original_profile)

    except (CLIError, KeyboardInterrupt, SystemExit) as e:
        _logger.error("Error when attempting to generate docs for profile %s.\n\t%s", profile, e)
        if original_profile:
            _logger.error("Will try to set the CLI's profile back to the original value: '%s'", original_profile)
            _set_profile(original_profile)
        # still re-raise the error.
        raise e


def _generate_ref_docs_for_public_exts(output_type, base_output_dir):
    # TODO: this shouldn't define the env key, but should reference it from a central place in the cli repo.
    ENV_KEY_AZURE_EXTENSION_DIR = 'AZURE_EXTENSION_DIR'

    extensions_url_tups = _get_available_extension_urls()
    if not extensions_url_tups:
        raise CLIError("Failed to retrieve public extensions.")

    temp_dir = tempfile.mkdtemp(prefix="temp_whl_ext_dir")
    _logger.debug("Created temp directory to store downloaded whl files: %s", temp_dir)

    try:
        for name, file_name, download_url in extensions_url_tups:
            # for every compatible public extensions
            # download the whl file
            whl_file_name = _get_whl_from_url(download_url, file_name, temp_dir)

            # install the whl file in a new temp directory
            installed_ext_dir = tempfile.mkdtemp(prefix="temp_extension_dir_", dir=temp_dir)
            _logger.debug("Created temp directory %s to use as the extension installation dir for %s extension.",
                          installed_ext_dir, name)
            pip_cmd = [sys.executable, '-m', 'pip', 'install', '--target',
                       os.path.join(installed_ext_dir, 'extension'),
                       whl_file_name, '--disable-pip-version-check', '--no-cache-dir']
            display('Executing "{}"'.format(' '.join(pip_cmd)))
            check_call(pip_cmd)

            # set the directory as the extension directory in the environment used to call sphinx-build
            env = os.environ.copy()
            env[ENV_KEY_AZURE_EXTENSION_DIR] = installed_ext_dir
            # generate documentation for installed extensions

            ext_output_dir = os.path.join(base_output_dir, name)
            os.makedirs(ext_output_dir)
            _call_sphinx_build(output_type, ext_output_dir, for_extensions_alone=True, call_env=env,
                               msg="\nGenerating ref docs for {}".format(name))
    finally:
        # finally delete the temp dir
        shutil.rmtree(temp_dir)
        _logger.debug("Deleted temp whl extension directory: %s", temp_dir)


def _call_sphinx_build(builder_name, output_dir, for_extensions_alone=False, call_env=None, msg=""):
    conf_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'refdoc')

    if for_extensions_alone:
        source_dir = os.path.abspath(os.path.join(conf_dir, 'extension_docs'))
    else:
        source_dir = os.path.abspath(os.path.join(conf_dir, 'cli_docs'))

    try:
        opts = ['-E', '-b', builder_name, '-c', conf_dir]
        args = [source_dir, output_dir]
        if for_extensions_alone:
            # apparently the configuration in extensions and core CLI differed in this way. This is only cosmetic
            # set smartquotes to false. Due to a bug, one has to use "0" instead "False"
            opts.extend(["-D", "smartquotes=0"])

        sphinx_cmd = ['sphinx-build'] + opts + args
        display("sphinx cmd: {}".format(" ".join(sphinx_cmd)))
        display(msg)
        # call sphinx-build
        check_call(sphinx_cmd, stdout=sys.stdout, stderr=sys.stderr, env=call_env)

    except CalledProcessError:
        raise CLIError("Doc generation failed.")


def _get_current_profile():
    try:
        return check_output(['az', 'cloud', 'show', '--query', '"profile"', '-otsv']).decode('utf-8').strip()
    except CalledProcessError as e:
        raise CLIError("Failed to get current profile due to err: {}".format(e))


def _set_profile(profile):
    try:
        _logger.warning("Setting the CLI profile to '%s'", profile)
        check_call(['az', 'cloud', 'update', '--profile', profile])
    except CalledProcessError as e:
        raise CLIError("Failed to set profile {} due to err:\n{}\n"
                       "Please check that your profile is set to the expected value.".format(profile, e))


def _get_profiles():
    try:
        profiles_str = check_output(["az", "cloud", "list-profiles", "-o", "tsv"]).decode('utf-8').strip()
    except CalledProcessError as e:
        raise CLIError("Failed to get profiles due to err: {}".format(e))

    return profiles_str.splitlines()


def _warn_if_exts_installed():
    cli_extensions, dev_cli_extensions = list_cli_extensions(), list_dev_cli_extensions()
    if cli_extensions:
        _logger.warning("One or more CLI Extensions are installed and will be included in ref doc output.")
    if dev_cli_extensions:
        _logger.warning(
            "One or more CLI Extensions are installed in development mode and will be included in ref doc output.")
    if cli_extensions or dev_cli_extensions:
        _logger.warning("Please uninstall the extension(s) if you want to generate Core CLI docs solely.")


# Todo, this would be unnecessary if list_available_extensions has a switch for including download urls....
def _get_available_extension_urls():
    """ Get download urls for all the CLI extensions compatible with the installed development CLI.

    :return: list of 3-tuples in the form of '(extension_name, extension_file_name, extensions_download_url)'
    """
    all_pub_extensions = list_available_extensions(show_details=True)
    compatible_extensions = list_available_extensions()

    name_url_tups = []

    for ext in compatible_extensions:
        old_length = len(name_url_tups)
        ext_name, ext_version = ext["name"], ext["version"]

        for ext_info in all_pub_extensions[ext_name]:
            if ext_version == ext_info["metadata"]["version"]:
                name_url_tups.append((ext_name, ext_info["filename"], ext_info["downloadUrl"]))
                break

        if old_length == len(name_url_tups):
            _logger.warning("'%s' has no versions compatible with the installed CLI's version", ext_name)

    return name_url_tups


def _get_whl_from_url(url, filename, tmp_dir, whl_cache=None):
    if not whl_cache:
        whl_cache = {}
    if url in whl_cache:
        return whl_cache[url]
    import requests
    r = requests.get(url, stream=True)
    assert r.status_code == 200, "Request to {} failed with {}".format(url, r.status_code)
    ext_file = os.path.join(tmp_dir, filename)
    with open(ext_file, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # ignore keep-alive new chunks
                f.write(chunk)
    whl_cache[url] = ext_file
    return ext_file
