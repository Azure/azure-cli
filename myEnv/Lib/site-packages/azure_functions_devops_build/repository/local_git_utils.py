# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import re

# Backward Compatible with Python 2.7
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'w')
from subprocess import STDOUT, check_call, check_output, CalledProcessError
from ..exceptions import GitOperationException


def does_git_exist():
    try:
        check_call("git", stdout=DEVNULL, stderr=STDOUT)
    except CalledProcessError as cpe:
        # Git will return exit code 1 when it exist
        return cpe.returncode == 1
    except FileNotFoundError:
        return False
    return True


def does_local_git_repository_exist():
    return os.path.exists(".git")


def does_git_remote_exist(remote_name):
    command = ["git", "remote", "show"]
    try:
        output = check_output(command).decode("utf-8").split("\n")
    except CalledProcessError:
        raise GitOperationException(message=" ".join(command))

    return remote_name in output


def does_git_has_credential_manager():
    command = ["git", "config", "--list"]
    try:
        output = check_output(command).decode("utf-8").split("\n")
    except CalledProcessError:
        raise GitOperationException(message=" ".join(command))

    return "credential.helper=manager" in output


def git_init():
    command = ["git", "init"]
    try:
        check_call(command, stdout=DEVNULL, stderr=STDOUT)
    except CalledProcessError:
        raise GitOperationException(message=" ".join(command))


def git_add_remote(remote_name, remote_url):
    command = ["git", "remote", "add", remote_name, remote_url]
    try:
        check_call(command, stdout=DEVNULL, stderr=STDOUT)
    except CalledProcessError:
        raise GitOperationException(message=" ".join(command))


def git_remove_remote(remote_name):
    command = ["git", "remote", "remove", remote_name]
    try:
        check_call(command, stdout=DEVNULL, stderr=STDOUT)
    except CalledProcessError:
        raise GitOperationException(message=" ".join(command))


def git_stage_all():
    command = ["git", "add", "--all"]
    try:
        check_call(command, stdout=DEVNULL, stderr=STDOUT)
    except CalledProcessError:
        raise GitOperationException(message=" ".join(command))


def git_commit(message):
    command = ["git", "commit", "--allow-empty", "--message", message]
    try:
        check_call(command, stdout=DEVNULL, stderr=STDOUT)
    except CalledProcessError:
        raise GitOperationException(message=" ".join(command))


def git_push(remote_name, force=False):
    command = ["git", "push", remote_name, "--all"]

    if force:
        command.append("--force")

    try:
        check_call(command, stdout=DEVNULL, stderr=STDOUT)
    except CalledProcessError:
        raise GitOperationException(message=" ".join(command))


def _sanitize_git_remote_name(organization_name, project_name, repository_name):
    concatenated_remote_name = "{organization_name}_{project_name}_{repository_name}".format(
        organization_name=organization_name,
        project_name=project_name,
        repository_name=repository_name
    )
    sanitized_remote_name = re.sub(r"[^A-Za-z0-9_-]|\s", "-", concatenated_remote_name)
    return sanitized_remote_name


def construct_git_remote_name(organization_name, project_name, repository_name, remote_prefix):
    remote_name = "_{prefix}_{name}".format(
        prefix=remote_prefix,
        name=_sanitize_git_remote_name(organization_name, project_name, repository_name)
    )
    return remote_name


def construct_git_remote_url(organization_name, project_name, repository_name, domain_name="dev.azure.com"):
    url = "https://{domain}/{org}/{proj}/_git/{repo}".format(
        domain=domain_name,
        org=organization_name,
        proj=project_name,
        repo=repository_name
    )
    return url
