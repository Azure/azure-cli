# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Kubeconfig merge helpers, adapted from azure-cli's acs command module
# (azure/cli/command_modules/acs/custom.py) so that
# `az aro hcp cluster request-credential` merges into an existing kubeconfig
# the same way `az aks get-credentials` does.

import base64
import errno
import os
import platform
import stat
import tempfile

import yaml
from azure.cli.core.azclierror import FileOperationError
from knack.log import get_logger
from knack.prompting import NoTTYException, prompt_y_n
from knack.util import CLIError

logger = get_logger(__name__)


def load_kubernetes_configuration(filename):
    try:
        with open(filename, encoding="utf-8") as stream:
            return yaml.safe_load(stream)
    except OSError as ex:
        if getattr(ex, "errno", 0) == errno.ENOENT:
            raise CLIError("{} does not exist".format(filename)) from ex
        if getattr(ex, "errno", 0) in (errno.EACCES, errno.EPERM):
            raise FileOperationError(
                "Permission denied when trying to read {}. "
                "Please ensure you have read access to this file, or specify a different file path "
                "using the --file/-f argument.".format(filename)
            ) from ex
        raise
    except (yaml.parser.ParserError, UnicodeDecodeError) as ex:
        raise CLIError("Error parsing {} ({})".format(filename, str(ex))) from ex


def _handle_merge(existing, addition, key, replace):
    if not addition.get(key, False):
        return
    if key not in existing:
        raise FileOperationError(
            "No such key '{}' in existing config, please confirm whether it is a valid config file. "
            "May back up this config file, delete it and retry the command.".format(key)
        )
    if not existing.get(key):
        existing[key] = addition[key]
        return

    for i in addition[key]:
        for j in existing[key]:
            if not i.get("name", False) or not j.get("name", False):
                continue
            if i["name"] == j["name"]:
                if replace or i == j:
                    existing[key].remove(j)
                else:
                    msg = "A different object named {} already exists in your kubeconfig file.\nOverwrite?"
                    overwrite = False
                    try:
                        overwrite = prompt_y_n(msg.format(i["name"]))
                    except NoTTYException:
                        pass
                    if overwrite:
                        existing[key].remove(j)
                    else:
                        msg = "A different object named {} already exists in {} in your kubeconfig file."
                        raise CLIError(msg.format(i["name"], key))
        existing[key].append(i)


def merge_kubernetes_configurations(existing_file, addition_file, replace, context_name=None):
    existing = load_kubernetes_configuration(existing_file)
    addition = load_kubernetes_configuration(addition_file)

    if addition is None:
        raise CLIError("failed to load additional configuration from {}".format(addition_file))

    if context_name is not None:
        addition["contexts"][0]["name"] = context_name
        addition["contexts"][0]["context"]["cluster"] = context_name
        addition["clusters"][0]["name"] = context_name
        addition["current-context"] = context_name

    if existing is None:
        existing = addition
    else:
        _handle_merge(existing, addition, "clusters", replace)
        _handle_merge(existing, addition, "users", replace)
        _handle_merge(existing, addition, "contexts", replace)
        existing["current-context"] = addition["current-context"]

    # check that ~/.kube/config is only read- and writable by its owner
    if platform.system() != "Windows" and not os.path.islink(existing_file):
        existing_file_perms = "{:o}".format(stat.S_IMODE(os.lstat(existing_file).st_mode))
        if not existing_file_perms.endswith("600"):
            logger.warning(
                '%s has permissions "%s".\nIt should be readable and writable only by its owner.',
                existing_file,
                existing_file_perms,
            )

    # Refuse to write through a symlink
    if os.path.islink(existing_file):
        raise CLIError(
            'Kubeconfig path "{}" is a symbolic link. '
            "Refusing to write to prevent symlink-following attacks.".format(existing_file)
        )

    # Atomic write: write to a temp file in the same directory, then replace
    parent_dir = os.path.dirname(existing_file) or "."
    tmp_fd, tmp_path = tempfile.mkstemp(dir=parent_dir)
    try:
        with os.fdopen(tmp_fd, "w") as stream:
            yaml.safe_dump(existing, stream, default_flow_style=False)
        # Preserve existing file permissions if available, otherwise default to 0600
        if os.path.exists(existing_file):
            existing_mode = stat.S_IMODE(os.stat(existing_file).st_mode)
            os.chmod(tmp_path, existing_mode)
        else:
            os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, existing_file)
    except Exception as ex:  # pylint: disable=broad-except
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        if isinstance(ex, OSError) and getattr(ex, "errno", 0) in (errno.EACCES, errno.EPERM, errno.EROFS):
            raise FileOperationError(
                "Permission denied when trying to write to {}. "
                "Please ensure you have write access to this file, or specify a different file path "
                "using the --file/-f argument.".format(existing_file)
            ) from ex
        raise

    current_context = addition.get("current-context", "UNKNOWN")
    logger.warning('Merged "%s" as current context in %s', current_context, existing_file)


def print_or_merge_credentials(path, kubeconfig, overwrite_existing, context_name):
    """Merge an unencrypted kubeconfig into the file at the specified path, or print it to
    stdout if the path is "-".
    """
    # Special case for printing to stdout
    if path == "-":
        print(kubeconfig)
        return

    # ensure that at least an empty ~/.kube/config exists
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except OSError as ex:
            if ex.errno != errno.EEXIST:
                raise
    if not os.path.exists(path):
        with os.fdopen(os.open(path, os.O_CREAT | os.O_WRONLY, 0o600), "wt"):
            pass

    # merge the new kubeconfig into the existing one
    fd, temp_path = tempfile.mkstemp()
    additional_file = os.fdopen(fd, "w+t")
    try:
        additional_file.write(kubeconfig)
        additional_file.flush()
        merge_kubernetes_configurations(path, temp_path, overwrite_existing, context_name)
    except yaml.YAMLError as ex:
        logger.warning("Failed to merge credentials to kube config file: %s", ex)
    finally:
        additional_file.close()
        os.remove(temp_path)


def _generate_admin_credential_request():
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "system:customer-break-glass:system-admin"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "system:masters"),
    ])
    csr = x509.CertificateSigningRequestBuilder().subject_name(subject).sign(private_key, hashes.SHA256())

    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    csr_pem = csr.public_bytes(serialization.Encoding.PEM).decode("ascii")
    return private_key_pem, csr_pem


def _embed_private_key(kubeconfig, private_key_pem):
    config = yaml.safe_load(kubeconfig)
    user = next(item for item in config["users"] if item["name"] == "admin")

    user["user"]["client-key-data"] = base64.b64encode(private_key_pem).decode("ascii")
    user["user"].pop("client-key", None)
    return yaml.safe_dump(config, default_flow_style=False)
