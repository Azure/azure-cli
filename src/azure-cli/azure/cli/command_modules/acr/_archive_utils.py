# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import tarfile
import os
import re
import codecs
from io import open
import requests
from knack.log import get_logger
from knack.util import CLIError
from msrestazure.azure_exceptions import CloudError
from azure.cli.core.profiles import ResourceType, get_sdk
from ._azure_utils import get_blob_info
from ._constants import TASK_VALID_VSTS_URLS

logger = get_logger(__name__)


def upload_source_code(cmd, client,
                       registry_name,
                       resource_group_name,
                       source_location,
                       tar_file_path,
                       docker_file_path,
                       docker_file_in_tar):
    _pack_source_code(source_location,
                      tar_file_path,
                      docker_file_path,
                      docker_file_in_tar)

    size = os.path.getsize(tar_file_path)
    unit = 'GiB'
    for S in ['Bytes', 'KiB', 'MiB', 'GiB']:
        if size < 1024:
            unit = S
            break
        size = size / 1024.0

    logger.warning("Uploading archived source code from '%s'...", tar_file_path)
    upload_url = None
    relative_path = None
    try:
        source_upload_location = client.get_build_source_upload_url(
            resource_group_name, registry_name)
        upload_url = source_upload_location.upload_url
        relative_path = source_upload_location.relative_path
    except (AttributeError, CloudError) as e:
        raise CLIError("Failed to get a SAS URL to upload context. Error: {}".format(e.message))

    if not upload_url:
        raise CLIError("Failed to get a SAS URL to upload context.")

    account_name, endpoint_suffix, container_name, blob_name, sas_token = get_blob_info(upload_url)
    BlockBlobService = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE, 'blob#BlockBlobService')
    BlockBlobService(account_name=account_name,
                     sas_token=sas_token,
                     endpoint_suffix=endpoint_suffix).create_blob_from_path(
                         container_name=container_name,
                         blob_name=blob_name,
                         file_path=tar_file_path)
    logger.warning("Sending context ({0:.3f} {1}) to registry: {2}...".format(
        size, unit, registry_name))
    return relative_path


def _pack_source_code(source_location, tar_file_path, docker_file_path, docker_file_in_tar):
    logger.warning("Packing source code into tar to upload...")

    original_docker_file_name = os.path.basename(docker_file_path.replace("\\", os.sep))
    ignore_list, ignore_list_size = _load_dockerignore_file(source_location, original_docker_file_name)
    common_vcs_ignore_list = {'.git', '.gitignore', '.bzr', 'bzrignore', '.hg', '.hgignore', '.svn'}

    def _ignore_check(tarinfo, parent_ignored, parent_matching_rule_index):
        # ignore common vcs dir or file
        if tarinfo.name in common_vcs_ignore_list:
            logger.warning("Excluding '%s' based on default ignore rules", tarinfo.name)
            return True, parent_matching_rule_index

        if ignore_list is None:
            # if .dockerignore doesn't exists, inherit from parent
            # eg, it will ignore the files under .git folder.
            return parent_ignored, parent_matching_rule_index

        for index, item in enumerate(ignore_list):
            # stop checking the remaining rules whose priorities are lower than the parent matching rule
            # at this point, current item should just inherit from parent
            if index >= parent_matching_rule_index:
                break
            if re.match(item.pattern, tarinfo.name):
                logger.debug(".dockerignore: rule '%s' matches '%s'.",
                             item.rule, tarinfo.name)
                return item.ignore, index

        logger.debug(".dockerignore: no rule for '%s'. parent ignore '%s'",
                     tarinfo.name, parent_ignored)
        # inherit from parent
        return parent_ignored, parent_matching_rule_index

    with tarfile.open(tar_file_path, "w:gz") as tar:
        # need to set arcname to empty string as the archive root path
        _archive_file_recursively(tar,
                                  source_location,
                                  arcname="",
                                  parent_ignored=False,
                                  parent_matching_rule_index=ignore_list_size,
                                  ignore_check=_ignore_check)

        # Add the Dockerfile if it's specified.
        # In the case of run, there will be no Dockerfile.
        if docker_file_path:
            docker_file_tarinfo = tar.gettarinfo(
                docker_file_path, docker_file_in_tar)
            with open(docker_file_path, "rb") as f:
                tar.addfile(docker_file_tarinfo, f)


class IgnoreRule:  # pylint: disable=too-few-public-methods
    def __init__(self, rule):

        self.rule = rule
        self.ignore = True
        # ! makes exceptions to exclusions
        if rule.startswith('!'):
            self.ignore = False
            rule = rule[1:]  # remove !

        self.pattern = "^"
        tokens = rule.split('/')
        token_length = len(tokens)
        for index, token in enumerate(tokens, 1):
            # ** matches any number of directories
            if token == "**":
                self.pattern += ".*"  # treat **/ as **
            else:
                # * matches any sequence of non-seperator characters
                # ? matches any single non-seperator character
                # . matches dot character
                self.pattern += token.replace(
                    "*", "[^/]*").replace("?", "[^/]").replace(".", "\\.")
                if index < token_length:
                    self.pattern += "/"  # add back / if it's not the last
        self.pattern += "$"


def _load_dockerignore_file(source_location, original_docker_file_name):
    # reference: https://docs.docker.com/engine/reference/builder/#dockerignore-file
    docker_ignore_file = os.path.join(source_location, ".dockerignore")
    docker_ignore_file_override = None
    if original_docker_file_name != "Dockerfile":
        docker_ignore_file_override = os.path.join(
            source_location, "{}.dockerignore".format(original_docker_file_name))
        if os.path.exists(docker_ignore_file_override):
            logger.warning("Overriding .dockerignore with %s", docker_ignore_file_override)
            docker_ignore_file = docker_ignore_file_override

    if not os.path.exists(docker_ignore_file):
        return None, 0

    encoding = "utf-8"
    header = open(docker_ignore_file, "rb").read(len(codecs.BOM_UTF8))
    if header.startswith(codecs.BOM_UTF8):
        encoding = "utf-8-sig"

    ignore_list = []
    if docker_ignore_file == docker_ignore_file_override:
        ignore_list.append(IgnoreRule(".dockerignore"))

    for line in open(docker_ignore_file, 'r', encoding=encoding).readlines():
        rule = line.rstrip()

        # skip empty line and comment
        if not rule or rule.startswith('#'):
            continue

        # the ignore rule at the end has higher priority
        ignore_list = [IgnoreRule(rule)] + ignore_list

    return ignore_list, len(ignore_list)


def _archive_file_recursively(tar, name, arcname, parent_ignored, parent_matching_rule_index, ignore_check):
    # create a TarInfo object from the file
    tarinfo = tar.gettarinfo(name, arcname)

    if tarinfo is None:
        raise CLIError("tarfile: unsupported type {}".format(name))

    # check if the file/dir is ignored
    ignored, matching_rule_index = ignore_check(
        tarinfo, parent_ignored, parent_matching_rule_index)

    if not ignored:
        # append the tar header and data to the archive
        if tarinfo.isreg():
            with open(name, "rb") as f:
                tar.addfile(tarinfo, f)
        else:
            tar.addfile(tarinfo)

    # even the dir is ignored, its child items can still be included, so continue to scan
    if tarinfo.isdir():
        for f in os.listdir(name):
            _archive_file_recursively(tar, os.path.join(name, f), os.path.join(arcname, f),
                                      parent_ignored=ignored, parent_matching_rule_index=matching_rule_index,
                                      ignore_check=ignore_check)


def check_remote_source_code(source_location):
    lower_source_location = source_location.lower()

    # git
    if lower_source_location.startswith("git@") or lower_source_location.startswith("git://"):
        return source_location

    # http
    if lower_source_location.startswith("https://") or lower_source_location.startswith("http://") \
       or lower_source_location.startswith("github.com/"):
        isVSTS = any(url in lower_source_location for url in TASK_VALID_VSTS_URLS)
        if isVSTS or re.search(r"\.git(?:#.+)?$", lower_source_location):
            # git url must contain ".git" or be from VSTS/Azure DevOps.
            # This is because Azure DevOps doesn't follow the standard git server convention of putting
            # .git at the end of their URLs, so we have to special case them.
            return source_location
        if not lower_source_location.startswith("github.com/"):
            # Others are tarball
            if requests.head(source_location).status_code < 400:
                return source_location
            raise CLIError("'{}' doesn't exist.".format(source_location))

    # oci
    if lower_source_location.startswith("oci://"):
        return source_location
    raise CLIError("'{}' doesn't exist.".format(source_location))
