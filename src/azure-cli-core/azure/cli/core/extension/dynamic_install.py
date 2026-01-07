# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import telemetry
from azure.cli.core.commands import AzCliCommandInvoker
from azure.cli.core.azclierror import CommandNotFoundError
from knack.log import get_logger

logger = get_logger(__name__)


def _get_extension_command_tree(cli_ctx):
    from azure.cli.core._session import EXT_CMD_TREE
    import os
    VALID_SECOND = 3600 * 24 * 10
    if not cli_ctx:
        return None
    EXT_CMD_TREE.load(os.path.join(cli_ctx.config.config_dir, 'extensionCommandTree.json'), VALID_SECOND)
    if not EXT_CMD_TREE.data:
        import posixpath
        import requests
        from azure.cli.core.util import should_disable_connection_verify
        try:
            azmirror_endpoint = cli_ctx.cloud.endpoints.azmirror_storage_account_resource_id if cli_ctx and \
                cli_ctx.cloud.endpoints.has_endpoint_set('azmirror_storage_account_resource_id') else None
            url = posixpath.join(azmirror_endpoint, 'extensions', 'extensionCommandTree.json') if \
                azmirror_endpoint else 'https://aka.ms/azExtCmdTree'
            response = requests.get(
                url,
                verify=(not should_disable_connection_verify()),
                timeout=10)
        except Exception as ex:  # pylint: disable=broad-except
            logger.info("Request failed for extension command tree: %s", str(ex))
            return None
        if response.status_code == 200:
            EXT_CMD_TREE.data = response.json()
            EXT_CMD_TREE.save_with_retry()
        else:
            logger.info("Error when retrieving extension command tree. Response code: %s", response.status_code)
            return None
    return EXT_CMD_TREE


def _get_all_extensions(cmd_chain, ext_set=None):
    """Find all the extension names in cmd_chain (dict of extension command subtree).
    An example of cmd_chain may look like (a command sub tree of the 'aks' command group):
    {
        "create": "aks-preview",
        "update": "aks-preview",
        "app": {
            "up": "deploy-to-azure"
        },
        "use-dev-spaces": "dev-spaces"
    }
    Then the resulting ext_set is {'aks-preview', 'deploy-to-azure', 'dev-spaces'}
    """
    ext_set = set() if ext_set is None else ext_set
    for key in cmd_chain:
        if isinstance(cmd_chain[key], str):
            ext_set.add(cmd_chain[key])
        else:
            _get_all_extensions(cmd_chain[key], ext_set)
    return ext_set


def _search_in_extension_commands(cli_ctx, command_str, allow_prefix_match=False):
    """Search the command in an extension commands dict which mimics a prefix tree.
    If the value of the dict item is a string, then the key represents the end of a complete command
    and the value is the name of the extension that the command belongs to.
    An example of the dict read from extensionCommandTree.json:
    {
        "aks": {
            "create": "aks-preview",
            "update": "aks-preview",
            "app": {
                "up": "deploy-to-azure"
            },
            "use-dev-spaces": "dev-spaces"
        },
        ...
    }
    """
    if not command_str:
        return None
    cmd_chain = _get_extension_command_tree(cli_ctx)
    if not cmd_chain:
        return None
    for part in command_str.split():
        try:
            if isinstance(cmd_chain[part], str):
                return cmd_chain[part]
            cmd_chain = cmd_chain[part]
        except KeyError:
            return None
    # command_str is prefix of one or more complete commands.
    if not allow_prefix_match:
        return None
    all_exts = _get_all_extensions(cmd_chain)
    return list(all_exts) if all_exts else None


def _get_extension_run_after_dynamic_install_config(cli_ctx):
    default_value = True
    run_after_extension_installed = cli_ctx.config.getboolean('extension',
                                                              'run_after_dynamic_install',
                                                              default_value) if cli_ctx else default_value
    return run_after_extension_installed


def _get_extension_allow_preview_install_config(cli_ctx):
    dynamic_install_allow_preview = None
    if cli_ctx:
        if cli_ctx.config.get('extension', 'dynamic_install_allow_preview', None) is None:
            logger.warning("Preview version of extension is disabled by default for extension installation, "
                           "enabled for modules without stable versions. ")
            logger.warning("Please run 'az config set extension.dynamic_install_allow_preview=true or false' "
                           "to config it specifically. ")
        else:
            dynamic_install_allow_preview = cli_ctx.config.getboolean('extension', 'dynamic_install_allow_preview')
    return dynamic_install_allow_preview


def try_install_extension(parser, args):
    # parser.cli_ctx is None when parser.prog is beyond 'az', such as 'az iot'.
    # use cli_ctx from cli_help which is not lost.
    cli_ctx = parser.cli_ctx or (parser.cli_help.cli_ctx if parser.cli_help else None)
    use_dynamic_install = _get_extension_use_dynamic_install_config(cli_ctx)
    if use_dynamic_install != 'no':
        # The function will exit if the parse error is caused by the extension for the command not installed
        _check_value_in_extensions(cli_ctx, parser, args, use_dynamic_install == 'yes_without_prompt')
    return use_dynamic_install


def _get_extension_use_dynamic_install_config(cli_ctx):
    from knack.prompting import verify_is_a_tty, NoTTYException
    try:
        verify_is_a_tty()
        # prompt when it's in tty
        default_value = 'yes_prompt'
    except NoTTYException:
        # without prompt when it's not in tty
        default_value = 'yes_without_prompt'
    use_dynamic_install = cli_ctx.config.get(
        'extension', 'use_dynamic_install', default_value).lower() if cli_ctx else default_value
    if use_dynamic_install not in ['no', 'yes_prompt', 'yes_without_prompt']:
        use_dynamic_install = default_value
    return use_dynamic_install


def _check_value_in_extensions(cli_ctx, parser, args, no_prompt):  # pylint: disable=too-many-statements, too-many-locals
    """Check if the command args can be found in extension commands.
       Exit command if the error is caused by an extension not installed.
       Otherwise return.
    """
    # Check if the command is from an extension
    from azure.cli.core.util import roughly_parse_command
    from azure.cli.core.azclierror import NoTTYError
    exit_code = 2
    command_str = roughly_parse_command(args[1:])
    allow_prefix_match = args[-1] == '-h' or args[-1] == '--help'
    ext_name = _search_in_extension_commands(cli_ctx, command_str, allow_prefix_match=allow_prefix_match)
    # ext_name is a list if the input command matches the prefix of one or more extension commands,
    # for instance: `az blueprint` when running `az blueprint -h`
    # ext_name is a str if the input command matches a complete command of an extension,
    # for instance: `az blueprint create`
    if isinstance(ext_name, list):
        if len(ext_name) > 1:
            from knack.prompting import prompt_choice_list, NoTTYException
            prompt_msg = "The command requires the latest version of one of the following " \
                "extensions. You need to pick one to install:"
            try:
                choice_idx = prompt_choice_list(prompt_msg, ext_name)
                ext_name = ext_name[choice_idx]
                no_prompt = True
            except NoTTYException:
                tty_err_msg = "{}{}\nUnable to prompt for selection as no tty available. Please update or " \
                    "install the extension with 'az extension add --upgrade -n <extension-name>'." \
                    .format(prompt_msg, ext_name)
                az_error = NoTTYError(tty_err_msg)
                az_error.print_error()
                az_error.send_telemetry()
                parser.exit(exit_code)
        else:
            ext_name = ext_name[0]
    if not ext_name:
        return

    # If a valid command has parser error, it may be caused by CLI running on a profile that is
    # not 'latest' and the command is not supported in that profile. If this command exists in an extension,
    # CLI will try to download the extension and rerun the command. But the parser will fail again and try to
    # install the extension and rerun the command infinitely. So we need to check if the latest version of the
    # extension is already installed and return if yes as the error is not caused by extension not installed.
    from azure.cli.core.extension import get_extension, ExtensionNotInstalledException
    from azure.cli.core.extension._resolve import resolve_from_index, NoExtensionCandidatesError
    from azure.cli.core.util import roughly_parse_command_with_casing
    extension_allow_preview = _get_extension_allow_preview_install_config(cli_ctx)
    try:
        ext = get_extension(ext_name)
    except ExtensionNotInstalledException:
        pass
    else:
        try:
            resolve_from_index(ext_name, cur_version=ext.version, cli_ctx=cli_ctx,
                               allow_preview=extension_allow_preview)
        except NoExtensionCandidatesError:
            return

    telemetry.set_command_details(command_str,
                                  parameters=AzCliCommandInvoker._extract_parameter_names(args),  # pylint: disable=protected-access
                                  extension_name=ext_name,
                                  command_preserve_casing=roughly_parse_command_with_casing(args))
    run_after_extension_installed = _get_extension_run_after_dynamic_install_config(cli_ctx)
    prompt_info = ""
    if no_prompt:
        logger.warning('The command requires the extension %s. It will be installed first.', ext_name)
        install_ext = True
    else:  # yes_prompt
        from knack.prompting import prompt_y_n, NoTTYException
        prompt_msg = 'The command requires the extension {}. Do you want to install it now?'.format(ext_name)
        if run_after_extension_installed:
            prompt_msg = '{} The command will continue to run after the extension is installed.' \
                .format(prompt_msg)
        NO_PROMPT_CONFIG_MSG = "Run 'az config set extension.use_dynamic_install=" \
            "yes_without_prompt' to allow installing extensions without prompt."
        try:
            install_ext = prompt_y_n(prompt_msg, default='y')
            if install_ext:
                prompt_info = " with prompt"
                logger.warning(NO_PROMPT_CONFIG_MSG)
        except NoTTYException:
            tty_err_msg = "The command requires the extension {}. " \
                          "Unable to prompt for extension install confirmation as no tty " \
                          "available. {}".format(ext_name, NO_PROMPT_CONFIG_MSG)
            az_error = NoTTYError(tty_err_msg)
            az_error.print_error()
            az_error.send_telemetry()
            parser.exit(exit_code)

    print_error = True
    if install_ext:
        from azure.cli.core.extension.operations import add_extension
        add_extension(cli_ctx=cli_ctx, extension_name=ext_name, upgrade=True, allow_preview=extension_allow_preview)
        if run_after_extension_installed:
            import subprocess
            import platform
            exit_code = subprocess.call(args, shell=platform.system() == 'Windows')
            # In this case, error msg is for telemetry recording purpose only.
            # From UX perspective, the command will rerun in subprocess. Whether it succeeds or fails,
            # mesages will be shown from the subprocess and this process should not print more message to
            # interrupt that.
            print_error = False
            error_msg = ("Extension {} dynamically installed{} and commands will be "
                         "rerun automatically.").format(ext_name, prompt_info)
        else:
            error_msg = 'Extension {} installed{}. Please rerun your command.' \
                .format(ext_name, prompt_info)
    else:
        error_msg = "The command requires the latest version of extension {ext_name}. " \
            "To install, run 'az extension add --upgrade -n {ext_name}'.".format(
                ext_name=ext_name)
    az_error = CommandNotFoundError(error_msg)
    if print_error:
        az_error.print_error()
    az_error.send_telemetry()
    parser.exit(exit_code)
