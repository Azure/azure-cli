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
from azure.cli.core.commands import LongRunningOperation
import pytz


def acr_show_logs(cmd, client, registry_name, build_id, resource_group_name=None):
    # Required and hardcoded for now. Refer to the "HACK" introduced in build_operations.py
    custom_headers = dict()
    custom_headers['logType'] = 'RawText'
    buildLogResult = client.get_log_link(
        build_id=build_id, resource_group_name=resource_group_name, registry_name=registry_name, custom_headers=custom_headers)
    logFileSas = buildLogResult.log_link

    if not logFileSas:
        return 'No logs found.'

    match = get_match(logFileSas)
    accountName = match.group('accountName')
    containerName = match.group('containerName')
    blobName = match.group('blobName')
    sasToken = match.group('sasToken')

    if not accountName:
        raise ValueError(
            "Unable to parse the account name from the log URL: '{!s}'."
            .format(logFileSas)
        )

    if not containerName:
        raise ValueError(
            "Unable to parse the container name from the log URL: '{!s}'."
            .format(logFileSas)
        )

    if not blobName:
        raise ValueError(
            "Unable to parse the blob name from the log URL: '{!s}'."
            .format(logFileSas)
        )

    if not sasToken:
        raise ValueError(
            "Unable to parse the SAS token from the log URL: '{!s}'."
            .format(logFileSas)
        )

    blobService = AppendBlobService(account_name=accountName,
                                    sas_token=sasToken)

    byteSize = 1024*4
    timeoutInMinutes = 10
    timeoutInSeconds = timeoutInMinutes * 60
    now = time.time()
    stream_logs(byteSize, timeoutInSeconds, blobService,
                containerName, blobName)


def get_match(sasURL):
    return re.search(
        (r"http(s)?://(?P<accountName>.*?)\..*?/(?P<containerName>.*?)/"
            r"(?P<blobName>.*?)\?(?P<sasToken>.*)"), sasURL)


def stream_logs(byteSize, timeoutInSeconds, blobService,
                containerName, blobName):

    colorama.init()
    stream = BytesIO()
    metadata = dict()
    start = 0
    end = byteSize - 1
    available = 0
    lastModified = None

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

    while (blob_is_not_complete(metadata) or start < available):

        while start < available:
            try:
                oldByteSize = len(stream.getvalue())
                blobService.get_blob_to_stream(
                    container_name=containerName,
                    blob_name=blobName,
                    start_range=start,
                    end_range=end,
                    stream=stream)

                currBytes = stream.getvalue()
                newByteSize = len(currBytes)
                amountRead = newByteSize - oldByteSize
                start += amountRead
                end = start + byteSize - 1

                # Only scan what's newly read. If nothing is read,
                # default to 0.
                minScanRange = max(newByteSize - amountRead - 1, 0)
                for i in range(newByteSize - 1, minScanRange, -1):
                    if currBytes[i-1:i+1] == b'\r\n':
                        flush = currBytes[:i]  # won't print \n
                        stream = BytesIO()
                        stream.write(currBytes[i+1:])
                        print(flush.decode('utf-8'))
                        break

            except AzureHttpError as ae:
                if ae.status_code != 404:
                    sys.exit(ae)
            except KeyboardInterrupt:
                currBytes = stream.getvalue()
                if len(currBytes) > 0:
                    print(currBytes.decode('utf-8'))
                sys.exit()
            except:
                raise

        try:
            props = blobService.get_blob_properties(
                container_name=containerName, blob_name=blobName)
            metadata = props.metadata
            available = props.properties.content_length
            lastModified = props.properties.last_modified

        except AzureHttpError as ae:
            if ae.status_code != 404:
                sys.exit(ae)
        except KeyboardInterrupt:
            if len(currBytes) > 0:
                print(currBytes.decode('utf-8'))
            sys.exit()
        except:
            raise

        # If we're still expecting data and we have a record for the last
        # modified date and the last modified date has timed out, exit
        if ((lastModified is not None and blob_is_not_complete(metadata)) or
                start < available):

            delta = datetime.utcnow().replace(tzinfo=pytz.utc) - lastModified

            if delta.seconds > timeoutInSeconds:
                print("No additional logs found. Timing out...")
                sys.exit()

        # If no new data available but not complete, sleep before trying
        # to process additional data.
        if (blob_is_not_complete(metadata) and start >= available):
            time.sleep(5)


def blob_is_not_complete(metadata):
    if metadata is None:
        return True

    for key in metadata:
        if key.lower() == 'complete':
            return False

    return True


def acr_queue(cmd, client, registry_name, resource_group_name, source_location, docker_file_path, image_name, context_path=None, timeout=None, arguments=None, secret_arguments=None):
    build_parameters = DockerBuildParameters(docker_file_path)

    if not (context_path is None):
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
        return acr_show_logs(cmd, client, registry_name, result.build_id, resource_group_name)
    else:
        # Maybe just raise error?
        return result
