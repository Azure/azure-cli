# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import signal
import subprocess
import sys

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)

ARTIFACTTOOL_PAT_ENVKEY = 'AZURE_DEVOPS_EXT_ARTIFACTTOOL_PATVAR'
ARTIFACTTOOL_OVERRIDE_PATH_ENVKEY = 'AZURE_DEVOPS_EXT_ARTIFACTTOOL_OVERRIDE_PATH'


class ArtifactToolInvoker:
    def __init__(self):
        pass

    def download_universal(self, organization, project, feed, package_name, package_version,
                           path, file_filter, no_hardlinks=False):
        args = ["universal", "download", "--service", organization, "--patvar", ARTIFACTTOOL_PAT_ENVKEY,
                "--feed", feed, "--package-name", package_name, "--package-version", package_version,
                "--path", path]

        if project:
            args.extend(["--project", project])

        if file_filter:
            args.extend(["--filter", file_filter])

        if no_hardlinks:
            args.append("--no-hardlinks")

        return self._run_artifacttool(organization, args, "Downloading")

    def publish_universal(self, organization, project, feed, package_name, package_version, description, path):
        args = ["universal", "publish", "--service", organization, "--patvar", ARTIFACTTOOL_PAT_ENVKEY,
                "--feed", feed, "--package-name", package_name, "--package-version", package_version,
                "--path", path]

        if project:
            args.extend(["--project", project])

        if description:
            args.extend(["--description", description])

        return self._run_artifacttool(organization, args, "Publishing")

    def _run_artifacttool(self, organization, args, initial_progress_message):
        # Get the ArtifactTool binary path
        artifacttool_dir = _get_artifacttool_dir(organization)
        artifacttool_binary_path = os.path.join(artifacttool_dir, "artifacttool")

        # Populate the environment for the process with the PAT
        pat = _get_pat(organization)
        new_env = os.environ.copy()
        new_env[ARTIFACTTOOL_PAT_ENVKEY] = pat

        # Run ArtifactTool
        command_args = [artifacttool_binary_path] + args
        proc = _run_tool(command_args, new_env, initial_progress_message, _process_stderr)
        if proc:
            output = proc.stdout.read().decode('utf-8')
            try:
                return json.loads(output)
            except ValueError:
                if output:
                    logger.warning("Failed to parse the output of ArtifactTool as JSON. "
                                   "The output was:\n %s", output)
        return None


def _get_artifacttool_dir(organization):
    """Get the directory containing the ArtifactTool binary."""
    # Check if the path is overridden by the user via environment variable
    override_path = os.environ.get(ARTIFACTTOOL_OVERRIDE_PATH_ENVKEY)
    if override_path:
        logger.debug("ArtifactTool path was overridden to '%s' via %s",
                     override_path, ARTIFACTTOOL_OVERRIDE_PATH_ENVKEY)
        return override_path

    # Try to use the azure-devops extension's ArtifactToolUpdater if the extension is installed
    try:
        from azext_devops.dev.common.artifacttool_updater import ArtifactToolUpdater  # pylint: disable=import-outside-toplevel
        updater = ArtifactToolUpdater()
        return updater.get_latest_artifacttool(organization)
    except ImportError:
        logger.debug("azure-devops extension not found; falling back to local ArtifactTool cache.")

    # Fall back to looking for any existing ArtifactTool in the standard cache directory
    artifacttool_root = _get_artifacttool_root()
    if os.path.isdir(artifacttool_root):
        versions = [d for d in os.listdir(artifacttool_root)
                    if os.path.isdir(os.path.join(artifacttool_root, d))]
        if versions:
            # Sort by the version suffix (last underscore-separated segment) using semantic versioning.
            # Return a tuple (is_parsed, version_or_str) to ensure consistent type comparison when sorting:
            # parsed versions sort before unparseable strings, and unparseable strings sort lexicographically.
            def _version_key(dir_name):
                parts = dir_name.rsplit('_', 1)
                version_str = parts[-1] if len(parts) > 1 else dir_name
                try:
                    from packaging.version import Version  # pylint: disable=import-outside-toplevel
                    return (1, Version(version_str))
                except (ImportError, ValueError) as ex:
                    logger.debug("Could not parse version '%s' as semantic version: %s", version_str, ex)
                    return (0, version_str)

            latest = sorted(versions, key=_version_key)[-1]
            release_dir = os.path.join(artifacttool_root, latest)
            binary = os.path.join(release_dir, "artifacttool")
            if os.path.exists(binary):
                logger.debug("Using cached ArtifactTool from '%s'", release_dir)
                return release_dir

    raise CLIError(
        "ArtifactTool binary not found. Please install the azure-devops extension first: "
        "az extension add --name azure-devops. "
        "Alternatively, set the {} environment variable to the path of the ArtifactTool binary."
        .format(ARTIFACTTOOL_OVERRIDE_PATH_ENVKEY)
    )


def _get_artifacttool_root():
    """Return the root directory where ArtifactTool releases are stored."""
    from azure.cli.core._environment import get_config_dir  # pylint: disable=import-outside-toplevel
    az_config_dir = get_config_dir()
    return os.path.join(az_config_dir, 'azuredevops', 'cli', 'tools', 'artifacttool')


def _get_pat(organization):
    """Get a Personal Access Token or access token for the given organization."""
    try:
        from azext_devops.dev.common.services import _get_credentials  # pylint: disable=import-outside-toplevel
        credentials = _get_credentials(organization)
        return str(credentials.password)
    except ImportError:
        pass

    # Fall back to using the Azure CLI login token
    try:
        from azure.cli.core._profile import Profile  # pylint: disable=import-outside-toplevel
        from collections import OrderedDict  # pylint: disable=import-outside-toplevel

        profile = Profile()
        subscriptions = profile.load_cached_subscriptions(False)
        tenants = OrderedDict()

        # Add the default subscription's tenant first so it is tried first,
        # then add any remaining tenants from other subscriptions.
        for sub in subscriptions:
            if sub.get('isDefault'):
                tenants.setdefault((sub['tenantId'], sub['user']['name']), '')
        for sub in subscriptions:
            tenants.setdefault((sub['tenantId'], sub['user']['name']), '')

        for (tenant_id, _) in tenants:
            try:
                token = profile.get_raw_token(resource='499b84ac-1321-427f-aa17-267ca6975798',
                                              tenant=tenant_id)[0][1]
                if token:
                    return token
            except CLIError as ex:
                logger.debug("Failed to get token for tenant %s: %s", tenant_id, ex)
    except (ImportError, AttributeError, KeyError) as ex:
        logger.debug("Failed to get token from az login: %s", ex)

    # Check for PAT in environment variable
    pat_env_key = 'AZURE_DEVOPS_EXT_PAT'
    pat = os.environ.get(pat_env_key)
    if pat:
        return pat

    raise CLIError(
        "Unable to obtain credentials for Azure DevOps. "
        "Please run 'az login' to authenticate, or set the AZURE_DEVOPS_EXT_PAT environment variable."
    )


def _process_stderr(line, update_progress_callback):
    """Process a single line of stderr output from ArtifactTool."""
    try:
        json_line = json.loads(line)
    except ValueError:
        json_line = None
        logger.warning("Failed to parse structured output from ArtifactTool.")
        logger.warning("Log line: %s", line)
        return

    _log_message(json_line)
    _process_event(json_line, update_progress_callback)


def _log_message(json_line):
    """Log an ArtifactTool structured log line."""
    if json_line is not None and '@m' in json_line:
        log_level = json_line.get('@l', 'Information')
        message = json_line['@m']
        if log_level in {"Critical", "Error"}:
            ex = json_line.get('@x')
            if ex:
                message = "{}\n{}".format(message, ex)
            logger.error(message)
        elif log_level == "Warning":
            logger.warning(message)
        elif log_level == "Information":
            logger.info(message)
        else:
            logger.debug(message)


def _process_event(json_line, update_progress_callback):
    """Process an ArtifactTool event for progress reporting."""
    if json_line is not None and 'EventId' in json_line and 'Name' in json_line['EventId']:
        event_name = json_line['EventId']['Name']
        if event_name == "ProcessingFiles":
            processed_files = json_line['ProcessedFiles']
            total_files = json_line['TotalFiles']
            percent = 100 * float(processed_files) / float(total_files)
            update_progress_callback("Pre-upload processing: {}/{} files"
                                     .format(processed_files, total_files), percent)
        elif event_name == "Uploading":
            uploaded_bytes = json_line['UploadedBytes']
            total_bytes = json_line['TotalBytes']
            percent = 100 * float(uploaded_bytes) / float(total_bytes)
            update_progress_callback("Uploading: {}/{} bytes".format(uploaded_bytes, total_bytes), percent)
        elif event_name == "Downloading":
            downloaded_bytes = json_line['DownloadedBytes']
            total_bytes = json_line['TotalBytes']
            percent = 100 * float(downloaded_bytes) / float(total_bytes)
            update_progress_callback("Downloading: {}/{} bytes"
                                     .format(downloaded_bytes, total_bytes), percent)


def _run_tool(command_args, env, initial_progress_text, stderr_handler):
    """Run an external tool process and report progress."""
    try:
        import humanfriendly  # pylint: disable=import-outside-toplevel
        with humanfriendly.Spinner(  # pylint: disable=no-member
                label=initial_progress_text, total=100, stream=sys.stderr) as spinner:
            spinner.step()
            return _run_process(command_args, env, stderr_handler,
                                lambda text, pct: spinner.step(label=text, progress=pct))
    except ImportError:
        logger.debug("humanfriendly not available; running without progress spinner.")
        return _run_process(command_args, env, stderr_handler, lambda text, pct: None)


def _run_process(command_args, env, stderr_handler, update_progress_callback):
    """Run the process and handle stderr output."""
    proc_state = {'proc': None, 'terminating': False, 'args': command_args}

    def _sigint_handler(*_):
        proc_state['terminating'] = True
        if proc_state['proc']:
            logger.debug("Killing process %s", proc_state['proc'].pid)
            proc_state['proc'].kill()

    old_handler = signal.signal(signal.SIGINT, _sigint_handler)
    try:
        logger.debug("Running external command: %s", ' '.join(command_args))
        with open(os.devnull, 'w') as devnull:
            proc_state['proc'] = subprocess.Popen(
                command_args,
                shell=False,
                stdin=devnull,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env)

        proc = proc_state['proc']
        try:
            for bline in iter(proc.stderr.readline, b''):
                line = bline.decode('utf-8', 'ignore').strip()
                stderr_handler(line, update_progress_callback)
        except IOError as ex:
            if not proc_state['terminating']:
                raise ex

        proc.wait()
        if proc.returncode != 0 and not proc_state['terminating']:
            stderr_remaining = proc.stderr.read().decode('utf-8', 'ignore').strip()
            err_suffix = "\n{}".format(stderr_remaining) if stderr_remaining else ""
            raise CLIError(
                "Process {proc} with PID {pid} exited with return code {code}{err}"
                .format(proc=command_args, pid=proc.pid, code=proc.returncode, err=err_suffix)
            )
        return proc
    finally:
        signal.signal(signal.SIGINT, old_handler)
