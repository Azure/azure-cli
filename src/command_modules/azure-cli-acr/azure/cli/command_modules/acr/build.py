# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import time
import os
from random import uniform
from io import BytesIO
import tempfile
import tarfile
from builtins import open as bltn_open
import requests
import colorama
from knack.log import get_logger
from knack.util import CLIError
from msrestazure.azure_exceptions import CloudError
from azure.common import AzureHttpError
from azure.cli.core.commands import LongRunningOperation
from azure.storage.blob import (
    BlockBlobService,
    AppendBlobService,
)
from azure.mgmt.containerregistry.v2018_02_01_preview.models import (
    QuickBuildRequest,
    PlatformProperties
)

from ._utils import validate_managed_registry
from ._client_factory import cf_acr_registries
from ._build_polling import get_build_with_polling


logger = get_logger(__name__)


BUILD_NOT_SUPPORTED = 'Builds are only supported for managed registries.'


def acr_build_show_logs(client,
                        build_id,
                        registry_name,
                        resource_group_name,
                        raise_error_on_failure=False):
    log_file_sas = None
    error_message = "Could not get build logs for build ID: {}.".format(build_id)
    try:
        build_log_result = client.get_log_link(
            resource_group_name=resource_group_name,
            registry_name=registry_name,
            build_id=build_id)
        log_file_sas = build_log_result.log_link
    except (AttributeError, CloudError) as e:
        logger.debug("%s Exception: %s", error_message, e)
        raise CLIError(error_message)

    if not log_file_sas:
        logger.debug("%s Empty SAS URL.", error_message)
        raise CLIError(error_message)

    account_name, endpoint_suffix, container_name, blob_name, sas_token = _get_blob_info(log_file_sas)

    _stream_logs(byte_size=1024,  # 1 KiB
                 timeout_in_seconds=1800,  # 30 minutes
                 blob_service=AppendBlobService(
                     account_name=account_name,
                     sas_token=sas_token,
                     endpoint_suffix=endpoint_suffix),
                 container_name=container_name,
                 blob_name=blob_name,
                 raise_error_on_failure=raise_error_on_failure)


def _stream_logs(byte_size,  # pylint: disable=too-many-locals, too-many-statements, too-many-branches
                 timeout_in_seconds,
                 blob_service,
                 container_name,
                 blob_name,
                 raise_error_on_failure):
    colorama.init()
    stream = BytesIO()
    metadata = {}
    start = 0
    end = byte_size - 1
    available = 0
    sleep_time = 1
    max_sleep_time = 15
    num_fails = 0
    num_fails_for_backoff = 3
    consecutive_sleep_in_sec = 0

    # Try to get the initial properties so there's no waiting.
    # If the storage call fails, we'll just sleep and try again after.
    try:
        props = blob_service.get_blob_properties(
            container_name=container_name, blob_name=blob_name)
        metadata = props.metadata
        available = props.properties.content_length
    except (AttributeError, AzureHttpError):
        pass

    while (_blob_is_not_complete(metadata) or start < available):
        while start < available:
            # Success! Reset our polling backoff.
            sleep_time = 1
            num_fails = 0
            consecutive_sleep_in_sec = 0

            try:
                old_byte_size = len(stream.getvalue())
                blob_service.get_blob_to_stream(
                    container_name=container_name,
                    blob_name=blob_name,
                    start_range=start,
                    end_range=end,
                    stream=stream)

                curr_bytes = stream.getvalue()
                new_byte_size = len(curr_bytes)
                amount_read = new_byte_size - old_byte_size
                start += amount_read
                end = start + byte_size - 1

                # Only scan what's newly read. If nothing is read, default to 0.
                min_scan_range = max(new_byte_size - amount_read - 1, 0)
                for i in range(new_byte_size - 1, min_scan_range, -1):
                    if curr_bytes[i - 1:i + 1] == b'\r\n':
                        flush = curr_bytes[:i]  # won't print \n
                        stream = BytesIO()
                        stream.write(curr_bytes[i + 1:])
                        print(flush.decode('utf-8', errors='ignore'))
                        break
            except AzureHttpError as ae:
                if ae.status_code != 404:
                    raise CLIError(ae)
            except KeyboardInterrupt:
                curr_bytes = stream.getvalue()
                if curr_bytes:
                    print(curr_bytes.decode('utf-8', errors='ignore'))
                return

        try:
            props = blob_service.get_blob_properties(
                container_name=container_name, blob_name=blob_name)
            metadata = props.metadata
            available = props.properties.content_length
        except AzureHttpError as ae:
            if ae.status_code != 404:
                raise CLIError(ae)
        except KeyboardInterrupt:
            if curr_bytes:
                print(curr_bytes.decode('utf-8', errors='ignore'))
            return
        except Exception as err:
            raise CLIError(err)

        if consecutive_sleep_in_sec > timeout_in_seconds:
            # Flush anything remaining in the buffer - this would be the case
            # if the file has expired and we weren't able to detect any \r\n
            curr_bytes = stream.getvalue()
            if curr_bytes:
                print(curr_bytes.decode('utf-8', errors='ignore'))

            logger.warning("Failed to find any new logs in %d seconds. Client will stop polling for additional logs.",
                           consecutive_sleep_in_sec)
            return

        # If no new data available but not complete, sleep before trying to process additional data.
        if (_blob_is_not_complete(metadata) and start >= available):
            num_fails += 1

            logger.debug("Failed to find new content %d times in a row", num_fails)
            if num_fails >= num_fails_for_backoff:
                num_fails = 0
                sleep_time = min(sleep_time * 2, max_sleep_time)
                logger.debug("Resetting failure count to %d", num_fails)

            # 1.0 <= x < 2.0
            rnd = uniform(1, 2)
            total_sleep_time = sleep_time + rnd
            consecutive_sleep_in_sec += total_sleep_time
            logger.debug("Base sleep time: %d, random delay: %d, total: %d, consecutive: %d",
                         sleep_time, rnd, total_sleep_time, consecutive_sleep_in_sec)
            time.sleep(total_sleep_time)

    # One final check to see if there's anything in the buffer to flush
    # E.g., metadata has been set and start == available, but the log file
    # didn't end in \r\n, so we were unable to flush out the final contents.
    curr_bytes = stream.getvalue()
    if curr_bytes:
        print(curr_bytes.decode('utf-8', errors='ignore'))

    build_status = _get_build_status(metadata).lower()
    logger.debug("Build status was: '%s'", build_status)

    if raise_error_on_failure:
        if build_status == 'internalerror' or build_status == 'failed':
            raise CLIError("Build failed")
        elif build_status == 'timedout':
            raise CLIError("Build timed out")
        elif build_status == 'canceled':
            raise CLIError("Build was canceled")


def _blob_is_not_complete(metadata):
    if not metadata:
        return True

    for key in metadata:
        if key.lower() == 'complete':
            return False

    return True


def _get_build_status(metadata):
    if metadata is None:
        return 'inprogress'

    for key in metadata:
        if key.lower() == 'complete':
            return metadata[key]

    return 'inprogress'


def _get_blob_info(blob_sas_url):
    match = re.search((r"http(s)?://(?P<account_name>.*?)\.blob\.(?P<endpoint_suffix>.*?)/(?P<container_name>.*?)/"
                       r"(?P<blob_name>.*?)\?(?P<sas_token>.*)"), blob_sas_url)
    account_name = match.group('account_name')
    endpoint_suffix = match.group('endpoint_suffix')
    container_name = match.group('container_name')
    blob_name = match.group('blob_name')
    sas_token = match.group('sas_token')

    if not account_name or not container_name or not blob_name or not sas_token:
        raise CLIError("Failed to parse the SAS URL: '{!s}'.".format(blob_sas_url))

    return account_name, endpoint_suffix, container_name, blob_name, sas_token


def acr_build(cmd,
              client,
              registry_name,
              source_location,
              image_names=None,
              resource_group_name=None,
              timeout=None,
              build_arg=None,
              secret_build_arg=None,
              docker_file_path='Dockerfile',
              no_push=False,
              no_logs=False,
              os_type='Linux'):
    _, resource_group_name = validate_managed_registry(
        cmd.cli_ctx, registry_name, resource_group_name, BUILD_NOT_SUPPORTED)

    client_registries = cf_acr_registries(cmd.cli_ctx)

    tar_file_path = os.path.join(tempfile.gettempdir(), 'source_archive_{}.tar.gz'.format(hash(os.times())))

    if os.path.exists(source_location):
        if not os.path.isdir(source_location):
            raise CLIError("Source location should be a local directory path or remote URL.")

        _check_local_docker_file(source_location, docker_file_path)

        try:
            source_location = _upload_source_code(
                client_registries, registry_name, resource_group_name, source_location, tar_file_path, docker_file_path)
        except Exception as err:
            raise CLIError(err)
        finally:
            try:
                logger.debug("Deleting the archived source code from '%s'.", tar_file_path)
                os.remove(tar_file_path)
            except OSError:
                pass
    else:
        source_location = _check_remote_source_code(source_location)
        logger.warning("Sending build context to ACR...")

    if no_push:
        is_push_enabled = False
    else:
        if image_names:
            is_push_enabled = True
        else:
            is_push_enabled = False
            logger.warning("'--image -t' is not provided. Skipping image push after build.")

    build_request = QuickBuildRequest(
        source_location=source_location,
        platform=PlatformProperties(os_type=os_type),
        docker_file_path=docker_file_path,
        image_names=image_names,
        is_push_enabled=is_push_enabled,
        timeout=timeout,
        build_arguments=(build_arg if build_arg else []) + (secret_build_arg if secret_build_arg else []))

    queued_build = LongRunningOperation(cmd.cli_ctx)(client_registries.queue_build(
        resource_group_name=resource_group_name,
        registry_name=registry_name,
        build_request=build_request))

    build_id = queued_build.build_id
    logger.warning("Queued a build with build ID: %s", build_id)
    logger.warning("Waiting for build agent...")

    if no_logs:
        return get_build_with_polling(client, build_id, registry_name, resource_group_name)

    return acr_build_show_logs(client, build_id, registry_name, resource_group_name, True)


def _check_local_docker_file(source_location, docker_file_path):
    if not os.path.isfile(os.path.join(source_location, docker_file_path)):
        raise CLIError("Unable to find '{}' in '{}'.".format(docker_file_path, source_location))


def _check_remote_source_code(source_location):
    lower_source_location = source_location.lower()

    # git
    if lower_source_location.startswith("git@") or lower_source_location.startswith("git://"):
        return source_location

    # http
    if lower_source_location.startswith("https://") or lower_source_location.startswith("http://") \
       or lower_source_location.startswith("github.com/"):
        if re.search(r"\.git(?:#.+)?$", lower_source_location) or "visualstudio.com" in lower_source_location:
            # git url must contain ".git" or be from VSTS
            return source_location
        elif not lower_source_location.startswith("github.com/"):
            # Others are tarball
            if requests.head(source_location).status_code < 400:
                return source_location
            else:
                raise CLIError("'{}' doesn't exist.".format(source_location))

    raise CLIError("'{}' is not a valid remote URL for git or tarball.".format(source_location))


def _upload_source_code(client, registry_name, resource_group_name, source_location, tar_file_path, docker_file_path):
    _pack_source_code(source_location, tar_file_path, docker_file_path)

    size = os.path.getsize(tar_file_path)
    unit = 'GiB'
    for S in ['Bytes', 'KiB', 'MiB', 'GiB']:
        if size < 1024:
            unit = S
            break
        size = size / 1024.0

    logger.debug("Uploading archived source code from '%s'.", tar_file_path)
    logger.warning("Sending build context ({0:.3f} {1}) to ACR...".format(size, unit))

    upload_url = None
    relative_path = None
    error_message = "Could not get build source upload URL."
    try:
        source_upload_location = client.get_build_source_upload_url(resource_group_name, registry_name)
        upload_url = source_upload_location.upload_url
        relative_path = source_upload_location.relative_path
    except (AttributeError, CloudError) as e:
        logger.debug("%s Exception: %s", error_message, e)
        raise CLIError(error_message)

    if not upload_url:
        logger.debug("%s Empty build source upload URL.", error_message)
        raise CLIError(error_message)

    account_name, endpoint_suffix, container_name, blob_name, sas_token = _get_blob_info(upload_url)
    BlockBlobService(account_name=account_name,
                     sas_token=sas_token,
                     endpoint_suffix=endpoint_suffix).create_blob_from_path(
                         container_name=container_name,
                         blob_name=blob_name,
                         file_path=tar_file_path)
    return relative_path


def _pack_source_code(source_location, tar_file_path, docker_file_path):
    logger.warning("Packing source code into tar file to upload...")

    ignore_list, ignore_list_size = _load_dockerignore_file(source_location)
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

        # always include docker file
        # file path comparision is case-sensitive
        if tarinfo.name == docker_file_path:
            logger.debug(".dockerignore: skip checking '%s'", docker_file_path)
            return False, parent_matching_rule_index

        for index, item in enumerate(ignore_list):
            # stop checking the remaining rules whose priorities are lower than the parent matching rule
            # at this point, current item should just inherit from parent
            if index >= parent_matching_rule_index:
                break
            if re.match(item.pattern, tarinfo.name):
                logger.debug(".dockerignore: rule '%s' matches '%s'.", item.rule, tarinfo.name)
                return item.ignore, index

        logger.debug(".dockerignore: no rule for '%s'. parent ignore '%s'", tarinfo.name, parent_ignored)
        # inherit from parent
        return parent_ignored, parent_matching_rule_index

    with tarfile.open(tar_file_path, "w:gz") as tar:
        # need to set arcname to empty string as the archive root path
        _archive_file_recursively(tar, source_location, arcname="",
                                  parent_ignored=False, parent_matching_rule_index=ignore_list_size,
                                  ignore_check=_ignore_check)


def _archive_file_recursively(tar, name, arcname, parent_ignored, parent_matching_rule_index, ignore_check):
    # create a TarInfo object from the file
    tarinfo = tar.gettarinfo(name, arcname)

    if tarinfo is None:
        raise CLIError("tarfile: unsupported type {}".format(name))

    # check if the file/dir is ignored
    ignored, matching_rule_index = ignore_check(tarinfo, parent_ignored, parent_matching_rule_index)

    if not ignored:
        # append the tar header and data to the archive
        if tarinfo.isreg():
            with bltn_open(name, "rb") as f:
                tar.addfile(tarinfo, f)
        else:
            tar.addfile(tarinfo)

    # even the dir is ignored, its child items can still be included, so continue to scan
    if tarinfo.isdir():
        for f in os.listdir(name):
            _archive_file_recursively(tar, os.path.join(name, f), os.path.join(arcname, f),
                                      parent_ignored=ignored, parent_matching_rule_index=matching_rule_index,
                                      ignore_check=ignore_check)


class IgnoreRule(object):  # pylint: disable=too-few-public-methods
    def __init__(self, rule):

        self.rule = rule
        self.ignore = True
        # ! makes exceptions to exclusions
        if rule.startswith('!'):
            self.ignore = False
            rule = rule[1:]  # remove !

        tokens = rule.split('/')
        for index, token in enumerate(tokens):
            # ** matches any number of directories
            if token == "**":
                tokens[index] = ".*"
            else:
                # * matches any sequence of non-seperator characters
                # ? matches any single non-seperator character
                # . matches dot character
                tokens[index] = token.replace(
                    "*", "[^/]*").replace("?", "[^/]").replace(".", "\\.")

        self.pattern = "^{}$".format("/".join(tokens))


def _load_dockerignore_file(source_location):
    # reference: https://docs.docker.com/engine/reference/builder/#dockerignore-file
    docker_ignore_file = os.path.join(source_location, ".dockerignore")
    if not os.path.exists(docker_ignore_file):
        return None, 0

    ignore_list = []

    # The ignore rule at the end has higher priority
    for line in reversed(open(docker_ignore_file).readlines()):
        rule = line.rstrip()

        # skip empty line and comment
        if not rule or rule.startswith('#'):
            continue

        # add ignore rule
        ignore_list.append(IgnoreRule(rule))

    return ignore_list, len(ignore_list)
