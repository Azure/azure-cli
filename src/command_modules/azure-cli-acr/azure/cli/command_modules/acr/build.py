# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import time
import sys
import os
import tarfile
import requests
from datetime import datetime, timedelta
from io import BytesIO
import time
import tempfile
import colorama
import pytz
from azure.common import AzureHttpError
from azure.storage.blob import (
    BlockBlobService,
    AppendBlobService,
    ContainerPermissions
)
from .sdk.models import (
    QueueBuildRequest,
    DockerBuildParameters,
    PlatformProperties,
    Build,
    BuildArgument,
    SourceUploadDefinition
)
from ._utils import get_resource_group_name_by_registry_name
from azure.cli.core.commands import LongRunningOperation
from knack.util import CLIError
from knack.log import get_logger

logger = get_logger(__name__)


def acr_build_show_logs(cmd,
                        client,
                        registry_name,
                        build_id,
                        resource_group_name=None):

    resource_group_name = get_resource_group_name_by_registry_name(
        cmd.cli_ctx, registry_name, resource_group_name)

    # Required and hardcoded for now. Refer to the "HACK" introduced in build_operations.py
    custom_headers = dict()
    custom_headers['logType'] = 'RawText'
    build_log_result = client.get_log_link(
        build_id=build_id, resource_group_name=resource_group_name,
        registry_name=registry_name, custom_headers=custom_headers)
    log_file_sas = build_log_result.log_link

    if not log_file_sas:
        return 'No logs found.'

    account_name, endpoint_suffix, container_name, blob_name, sas_token = _get_blob_info(log_file_sas)

    byte_size = 1024*4
    timeout_in_minutes = 10
    timeout_in_seconds = timeout_in_minutes * 60

    _stream_logs(byte_size, timeout_in_seconds,
                 AppendBlobService(account_name=account_name, sas_token=sas_token, endpoint_suffix=endpoint_suffix), container_name, blob_name)


def _get_match(sas_url):
    return re.search(
        (r"http(s)?://(?P<account_name>.*?)\.blob\.(?P<endpoint_suffix>.*?)/(?P<container_name>.*?)/"
            r"(?P<blob_name>.*?)\?(?P<sas_token>.*)"), sas_url)


def _stream_logs(byte_size,
                 timeout_in_seconds,
                 blob_service,
                 container_name,
                 blob_name):

    colorama.init()
    stream = BytesIO()
    metadata = dict()
    start = 0
    end = byte_size - 1
    available = 0
    last_modified = None

    # Try to get the initial properties so there's no waiting.
    # If the storage call fails, we'll just sleep and try again after.
    try:
        props = blob_service.get_blob_properties(
            container_name=container_name, blob_name=blob_name)
        metadata = props.metadata
        available = props.properties.content_length
        last_modified = props.properties.last_modified
    except:
        pass

    while (_blob_is_not_complete(metadata) or start < available):

        while start < available:
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

                # Only scan what's newly read. If nothing is read,
                # default to 0.
                min_scan_range = max(new_byte_size - amount_read - 1, 0)
                for i in range(new_byte_size - 1, min_scan_range, -1):
                    if curr_bytes[i-1:i+1] == b'\r\n':
                        flush = curr_bytes[:i]  # won't print \n
                        stream = BytesIO()
                        stream.write(curr_bytes[i+1:])
                        print(flush.decode('utf-8'))
                        break

            except AzureHttpError as ae:
                if ae.status_code != 404:
                    raise CLIError(ae)
            except KeyboardInterrupt:
                curr_bytes = stream.getvalue()
                if len(curr_bytes) > 0:
                    print(curr_bytes.decode('utf-8'))
                return

        try:
            props = blob_service.get_blob_properties(
                container_name=container_name, blob_name=blob_name)
            metadata = props.metadata
            available = props.properties.content_length
            last_modified = props.properties.last_modified

        except AzureHttpError as ae:
            if ae.status_code != 404:
                raise CLIError(ae)
        except KeyboardInterrupt:
            if len(curr_bytes) > 0:
                print(curr_bytes.decode('utf-8'))
            return
        except Exception as err:
            raise CLIError(err)

        # If we're still expecting data and we have a record for the last
        # modified date and the last modified date has timed out, exit
        if ((last_modified is not None and _blob_is_not_complete(metadata)) or
                start < available):

            delta = datetime.utcnow().replace(tzinfo=pytz.utc) - last_modified

            if delta.seconds > timeout_in_seconds:
                print("No additional logs found. Timing out...")
                return

        # If no new data available but not complete, sleep before trying
        # to process additional data.
        if (_blob_is_not_complete(metadata) and start >= available):
            time.sleep(5)


def _blob_is_not_complete(metadata):
    if metadata is None:
        return True

    for key in metadata:
        if key.lower() == 'complete':
            return False

    return True


def _get_blob_info(blob_sas_url):
    match = _get_match(blob_sas_url)
    account_name = match.group('account_name')
    endpoint_suffix = match.group('endpoint_suffix')
    container_name = match.group('container_name')
    blob_name = match.group('blob_name')
    sas_token = match.group('sas_token')

    if not account_name or not container_name or not blob_name or not sas_token:
        raise CLIError("Failed to parse the sas url: '{!s}'."
                       .format(blob_sas_url))

    return account_name, endpoint_suffix, container_name, blob_name, sas_token


def acr_queue(cmd,
              client,
              registry_name,
              image_name=None,
              docker_file_path=None,
              resource_group_name=None,
              source_location=None,
              timeout=None,
              build_args=None,
              secret_build_args=None,
              show_logs='true'):

    resource_group_name = get_resource_group_name_by_registry_name(
        cmd.cli_ctx, registry_name, resource_group_name)

    if docker_file_path is None:
        docker_file_path = "Dockerfile"

    build_parameters = DockerBuildParameters(docker_file_path)
    # context_path in tar build is always the source code root folder
    build_parameters.context_path = "."

    if source_location is None:
        source_location = "."

    if os.path.exists(source_location):
        if os.path.isdir(source_location):
            source_location = _upload_source_code(
                client, registry_name, resource_group_name, source_location)
        else:
            raise CLIError(
                "'--source-location' should be a local directory path or remote url.")
    else:
        source_location = _check_remote_source_code(source_location)

    is_push_enabled = True
    if image_name is None:
        is_push_enabled = False
        print("'--tag' is not provided. Skip image push after build.")
    else:
        image_name = _check_image_name(image_name)

    # hard-code platform to linux and cpu to 1
    platform = PlatformProperties("Linux")
    platform.cpu = 1

    build_arguments = []
    if not (build_args is None):
        for name_value in build_args:
            name, value = name_value.split('=', 1)
            build_arguments.append(BuildArgument(name, value, False))

    if not (secret_build_args is None):
        for name_value in secret_build_args:
            name, value = name_value.split('=', 1)
            build_arguments.append(BuildArgument(name, value, True))

    try:
        build_request = QueueBuildRequest(
            image_name=image_name,
            source_location=source_location,
            build_parameters=build_parameters,
            is_push_enabled=is_push_enabled,
            timeout=timeout,
            platform=platform,
            build_arguments=build_arguments)

        result = LongRunningOperation(cmd.cli_ctx)(client.queue(
            build_request=build_request, resource_group_name=resource_group_name, registry_name=registry_name))

        print("Successfully queued a build with build-id: {}.".format(result.build_id))

        if show_logs == 'true':
            print("Starting to stream the logs...")
            return acr_build_show_logs(cmd, client, registry_name, result.build_id, resource_group_name)
    except Exception as err:
        raise CLIError(err)


def _check_remote_source_code(source_location):

    # NOTE: acr_build doesn't support git repo url
    if source_location.lower().startswith("git://"):
        return source_location

    response = requests.head(source_location)
    if response.status_code < 400:
        return source_location
    else:
        raise CLIError("'{}' doesn't exist.".format(source_location))


def _check_image_name(image_name):

    # referenc: https://github.com/docker/distribution/tree/master/reference

    if not image_name:
        raise CLIError("'--tag' value should not be empty.")

    tokens = image_name.split(':')
    if(len(tokens) > 2):
        raise CLIError(
            "'--tag' value should be repository and optionally a tag in the 'repository:tag' format")

    # check repository
    repository = tokens[0]
    if len(repository) > 255:
        raise CLIError(
            "The repository of '--tag' value should be no more than 255 characters.")
    else:
        if re.match(r"^[a-z0-9]+(?:(?:(?:[._]|__|[-]*)[a-z0-9]+)+)?(?:(?:/[a-z0-9]+(?:(?:(?:[._]|__|[-]*)[a-z0-9]+)+)?)+)?$", repository) is None:
            raise CLIError(
                "The '--tag' value is not valid. Please check https://docs.docker.com/engine/reference/commandline/tag/.")

    # check tag
    if len(tokens) == 2:
        tag = tokens[1]
        if re.match(r"^[\w][\w.-]{0,127}$", tag) is None:
            raise CLIError(
                "The '--tag' value is not valid. Please check https://docs.docker.com/engine/reference/commandline/tag/.")

    return image_name


def _upload_source_code(client, registry_name, resource_group_name, source_location):

    tar_file_path = os.path.join(tempfile.gettempdir(),
                                 "source_archive_{}.tar.gz".format(hash(os.times())))

    try:
        logger.debug(
            "Starting to acquire the access token to upload the source code.")

        source_upload_location = client.get_source_upload_url(
            resource_group_name=resource_group_name, registry_name=registry_name)

        logger.debug(
            "Starting to archive the source code to '{}'.".format(tar_file_path))

        ignore_list = _load_dockerignore_file(source_location)

        def _filter_file(tarinfo):

            if ignore_list is None:
                return tarinfo

            for item in ignore_list:
                if re.match(item.pattern, tarinfo.name):
                    logger.debug(".dockerignore: rule '{}' matches '{}'.".format(
                        item.rule, tarinfo.name))
                    return None if item.ignore else tarinfo

            logger.debug(
                ".dockerignore: no rule for '{}'.".format(tarinfo.name))
            return tarinfo

        with tarfile.open(tar_file_path, "w:gz") as tar:
            # NOTE: Need to set arcname to empty string otherwise the child item name will have a prefix (eg, ../) which can block unpacking.
            tar.add(source_location, arcname="", filter=_filter_file)

        logger.debug(
            "Starting to upload the archived source code from '{}'.".format(tar_file_path))

        account_name, endpoint_suffix, container_name, blob_name, sas_token = _get_blob_info(
            source_upload_location.upload_url)

        BlockBlobService(account_name=account_name, sas_token=sas_token, endpoint_suffix=endpoint_suffix).create_blob_from_path(
            container_name=container_name, blob_name=blob_name, file_path=tar_file_path)

        return source_upload_location.relative_path
    except Exception as err:
        raise CLIError(err)
    finally:
        if os.path.exists(tar_file_path):
            logger.debug(
                "Starting to delete the archived source code from '{}'.".format(tar_file_path))
            os.remove(tar_file_path)


class IgnoreRule(object):
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
                tokens[index] = token.replace(
                    "*", "[^/]*").replace("?", "[^/]")

        self.pattern = "^{}$".format("/".join(tokens))


def _load_dockerignore_file(source_location):

    # reference: https://docs.docker.com/engine/reference/builder/#dockerignore-file
    docker_ignore_file = os.path.join(source_location, ".dockerignore")
    if not os.path.exists(docker_ignore_file):
        return None

    ignore_list = []

    # The ignore rule at the end has higher priority
    for line in reversed(open(docker_ignore_file).readlines()):
        rule = line.rstrip()

        # skip empty line and comment
        if not rule or rule.startswith('#'):
            continue

        # add ignore rule
        ignore_list.append(IgnoreRule(rule))

    return ignore_list
