# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import absolute_import

import json
import os
import platform
import requests
import subprocess
import sys

from . import __version__
from .support import Popen


class CredentialProvider(object):
    _NON_INTERACTIVE_VAR_NAME = "ARTIFACTS_KEYRING_NONINTERACTIVE_MODE"

    def __init__(self):
        if sys.platform.startswith("win"):
            tool_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "plugins",
                "plugins",
                "netcore",
                "CredentialProvider.Microsoft",
                "CredentialProvider.Microsoft.exe",
            )

            self.exe = [tool_path]
        else:
            tool_path_root = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "plugins",
                "plugins",
                "netcore",
                "CredentialProvider.Microsoft"
            )

            is_dotnet_runtime_required = False
            if os.path.exists(tool_path_root):
                # Ensure the plugins directory executable permissions are set so Python can execute
                # the Credential Provider plugin.
                try:
                    tool_path = os.path.join(tool_path_root, 'CredentialProvider.Microsoft')
                    if os.path.exists(tool_path):
                        os.chmod(tool_path, 0o755)
                except Exception as e:
                    raise RuntimeError(
                        "Failed to set executable permissions for the Credential Provider plugins directory "
                        + tool_path_root 
                        + ". Please ensure the directory has the correct access permissions (755). Error: "
                        + str(e)
                    )
                
                # If tool_path_root contains the runtimes directory, it means that the
                # binary is not self-contained and requires a .NET install to run.
                tool_path_runtimes = os.path.join(
                    tool_path_root,
                    "runtimes"
                )
                if os.path.exists(tool_path_runtimes):
                    is_dotnet_runtime_required = True

            if is_dotnet_runtime_required:
                tool_path = os.path.join(
                    tool_path_root,
                    "CredentialProvider.Microsoft.dll"
                )

                try:
                    # check to see if any dotnet runtimes are installed. Not checking specific versions.
                    output = subprocess.check_output(["dotnet", "--list-runtimes"]).decode().strip()
                    if(len(output) == 0):
                        raise Exception("No dotnet runtime found. Refer to https://learn.microsoft.com/dotnet/core/install/ for installation guidelines.")
                except Exception as e:
                    message = (
                        "Unable to find dependency dotnet, please manually install"
                        " the .NET runtime and ensure 'dotnet' is in your PATH. Error: "
                    )
                    raise Exception(message + str(e))
                
                self.exe = ["dotnet", "exec", tool_path]
            else:
                # for self-contained binaries, the executable is not the DLL
                if platform.system().lower() == "windows":
                    tool_path = os.path.join(
                        tool_path_root,
                        "CredentialProvider.Microsoft.exe"
                    )
                # linux and macOS
                else:
                    tool_path = os.path.join(
                        tool_path_root,
                        "CredentialProvider.Microsoft"
                    )
                
                self.exe = [tool_path]
            

        if not os.path.isfile(tool_path):
            raise RuntimeError("Unable to find credential provider in the expected path: " + tool_path)

    def get_credentials(self, url):
        # Public feed short circuit: return nothing if not getting credentials for the upload endpoint
        # (which always requires auth) and the endpoint is public (can authenticate without credentials).
        if not self._is_upload_endpoint(url) and self._can_authenticate(url, None):
            return None, None

        # Getting credentials with IsRetry=false; the credentials may come from the cache
        username, password = self._get_credentials_from_credential_provider(url, is_retry=False)

        # Do not attempt to validate if the credentials could not be obtained
        if username is None or password is None:
            return username, password

        # Make sure the credentials are still valid (i.e. not expired)
        if self._can_authenticate(url, (username, password)):
            return username, password

        # The cached credentials are expired; get fresh ones with IsRetry=true
        return self._get_credentials_from_credential_provider(url, is_retry=True)


    def _is_upload_endpoint(self, url):
        url = url[: -1] if url[-1] == "/" else url
        return url.endswith("pypi/upload")


    def _can_authenticate(self, url, auth):
        response = requests.get(url, auth=auth)

        return response.status_code < 500 and \
            response.status_code != 401 and \
            response.status_code != 403


    def _get_credentials_from_credential_provider(self, url, is_retry):
        non_interactive = self._NON_INTERACTIVE_VAR_NAME in os.environ and \
            os.environ[self._NON_INTERACTIVE_VAR_NAME] and \
            str(os.environ[self._NON_INTERACTIVE_VAR_NAME]).lower() == "true"

        proc = Popen(
            self.exe + [
                "-Uri", url,
                "-IsRetry", str(is_retry),
                "-NonInteractive", str(non_interactive),
                "-CanShowDialog", "True",
                "-OutputFormat", "Json"
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Read all standard error first, which may either display
        # errors from the credential provider or instructions
        # from it for Device Flow authentication.
        for stderr_line in iter(proc.stderr.readline, b''):
            line = stderr_line.decode("utf-8", "ignore")
            sys.stderr.write(line)
            sys.stderr.flush()

        proc.wait()

        if proc.returncode != 0:
            stderr = proc.stderr.read().decode("utf-8", "ignore")

            error_msg = "Failed to get credentials: process with PID {pid} exited with code {code}".format(
                pid=proc.pid, code=proc.returncode
            )
            if stderr.strip():
                error_msg += "; additional error message: {error}".format(error=stderr)
            else:
                error_msg += "; no additional error message available, see Credential Provider logs above for details."
            raise RuntimeError(error_msg)

        try:
            # stdout is expected to be UTF-8 encoded JSON, so decoding errors are not ignored here.
            payload = proc.stdout.read().decode("utf-8")
        except ValueError:
            raise RuntimeError("Failed to get credentials: the Credential Provider's output could not be decoded using UTF-8.")

        try:
            parsed = json.loads(payload)
            return parsed["Username"], parsed["Password"]
        except ValueError:
            raise RuntimeError("Failed to get credentials: the Credential Provider's output could not be parsed as JSON.")
