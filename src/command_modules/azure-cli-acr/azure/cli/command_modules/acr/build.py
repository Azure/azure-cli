import re
import time
import sys
from datetime import datetime, timedelta
from io import BytesIO
import time
import colorama
from azure.common import AzureHttpError
from azure.storage.blob import AppendBlobService, ContainerPermissions
from .sdk.models import (
    QueueBuildRequest,
    DockerBuildParameters,
    PlatformProperties,
    Build,
    BuildArgument
)
from knack.util import CLIError
from ._utils import (
    get_resource_group_name_by_registry_name,
)
from azure.cli.core.commands import LongRunningOperation
import pytz


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

    match = __get_match(log_file_sas)
    account_name = match.group('account_name')
    container_name = match.group('container_name')
    blob_name = match.group('blob_name')
    sas_token = match.group('sas_token')

    if not account_name or not container_name or not blob_name or not sas_token:
        raise CLIError("Failed to parse the log URL: '{!s}'."
                       .format(log_file_sas))

    blob_service = AppendBlobService(account_name=account_name,
                                     sas_token=sas_token)

    byte_size = 1024*4
    timeout_in_minutes = 10
    timeout_in_seconds = timeout_in_minutes * 60
    now = time.time()
    __stream_logs(byte_size, timeout_in_seconds, blob_service,
                container_name, blob_name)


def __get_match(sas_url):
    return re.search(
        (r"http(s)?://(?P<account_name>.*?)\..*?/(?P<container_name>.*?)/"
            r"(?P<blob_name>.*?)\?(?P<sas_token>.*)"), sas_url)


def __stream_logs(byte_size,
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
        props = blobService.get_blob_properties(
            container_name=containerName, blob_name=blobName)
        metadata = props.metadata
        available = props.properties.content_length
        lastModified = props.properties.last_modified
    except:
        pass

    while (__blob_is_not_complete(metadata) or start < available):

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
        if ((last_modified is not None and __blob_is_not_complete(metadata)) or
                start < available):

            delta = datetime.utcnow().replace(tzinfo=pytz.utc) - last_modified

            if delta.seconds > timeout_in_seconds:
                print("No additional logs found. Timing out...")
                return

        # If no new data available but not complete, sleep before trying
        # to process additional data.
        if (__blob_is_not_complete(metadata) and start >= available):
            time.sleep(5)


def __blob_is_not_complete(metadata):
    if metadata is None:
        return True

    for key in metadata:
        if key.lower() == 'complete':
            return False

    return True


def acr_build_queue(cmd,
              client,
              registry_name,
              source_location,
              docker_file_path,
              image_name,
              resource_group_name=None,
              context_path=None,
              timeout=None,
              arguments=None,
              secret_arguments=None):

    resource_group_name = get_resource_group_name_by_registry_name(
        cmd.cli_ctx, registry_name, resource_group_name)
    build_parameters = DockerBuildParameters(docker_file_path)

    if context_path:
        build_parameters.context_path = context_path

    # [Server Bug] we should allow skiping image_name if users don't want to push
    is_push_enabled = True
    if image_name is None:
        is_push_enabled = False

    # hard-code platform to linux and cpu to 1
    platform = PlatformProperties("Linux")
    platform.cpu = 1

    # figure out how to pass build_arguments
    build_arguments = []
    if not (arguments is None):
        for name_value in arguments:
            name, value = name_value.split('=', 1)
            build_arguments.append(BuildArgument(name, value, False))

    if not (secret_arguments is None):
        for name_value in secret_arguments:
            name, value = name_value.split('=', 1)
            build_arguments.append(BuildArgument(name, value, True))

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

    if isinstance(result, Build):
        print("Successfully queued a build with build-id: {}. Starting to stream the logs...".format(result.build_id))
        return acr_build_show_logs(cmd, client, registry_name, result.build_id, resource_group_name)
    else:
        # Maybe just raise error?
        return result
