# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from io import BytesIO
import time
from random import uniform
import colorama
import requests
from knack.util import CLIError
from knack.log import get_logger
from msrestazure.azure_exceptions import CloudError
from azure.common import AzureHttpError
from azure.cli.core.profiles import ResourceType, get_sdk
from ._azure_utils import get_blob_info
from ._constants import ACR_RUN_DEFAULT_TIMEOUT_IN_SEC

logger = get_logger(__name__)

DEFAULT_CHUNK_SIZE = 1024 * 4


def stream_logs(cmd, client,
                run_id,
                registry_name,
                resource_group_name,
                timeout=ACR_RUN_DEFAULT_TIMEOUT_IN_SEC,
                no_format=False,
                raise_error_on_failure=False):
    log_file_sas = None
    artifact = False
    error_msg = "Could not get logs for ID: {}".format(run_id)

    try:
        response = client.get_log_sas_url(
            resource_group_name=resource_group_name,
            registry_name=registry_name,
            run_id=run_id)
        if not response.log_artifact_link:
            log_file_sas = response.log_link
        else:
            log_file_sas = response.log_artifact_link
            artifact = True
    except (AttributeError, CloudError) as e:
        logger.debug("%s Exception: %s", error_msg, e)
        raise CLIError(error_msg)

    if not log_file_sas:
        logger.debug("%s Empty SAS URL.", error_msg)
        raise CLIError(error_msg)

    if not artifact:
        account_name, endpoint_suffix, container_name, blob_name, sas_token = get_blob_info(
            log_file_sas)
        AppendBlobService = get_sdk(cmd.cli_ctx, ResourceType.DATA_STORAGE, 'blob#AppendBlobService')
        if not timeout:
            timeout = ACR_RUN_DEFAULT_TIMEOUT_IN_SEC
        _stream_logs(no_format,
                     DEFAULT_CHUNK_SIZE,
                     timeout,
                     AppendBlobService(
                         account_name=account_name,
                         sas_token=sas_token,
                         endpoint_suffix=endpoint_suffix),
                     container_name,
                     blob_name,
                     raise_error_on_failure)
    else:
        _stream_artifact_logs(log_file_sas,
                              no_format)


def _stream_logs(no_format,  # pylint: disable=too-many-locals, too-many-statements, too-many-branches
                 byte_size,
                 timeout_in_seconds,
                 blob_service,
                 container_name,
                 blob_name,
                 raise_error_on_failure):

    if not no_format:
        colorama.init()

    log_exist = False
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
        # Need to call "exists" API to prevent storage SDK logging BlobNotFound error
        log_exist = blob_service.exists(
            container_name=container_name, blob_name=blob_name)

        if log_exist:
            props = blob_service.get_blob_properties(
                container_name=container_name, blob_name=blob_name)
            metadata = props.metadata
            available = props.properties.content_length
        else:
            # Wait a little bit before checking the existence again
            time.sleep(1)
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
            if log_exist:
                props = blob_service.get_blob_properties(
                    container_name=container_name, blob_name=blob_name)
                metadata = props.metadata
                available = props.properties.content_length
            else:
                log_exist = blob_service.exists(
                    container_name=container_name, blob_name=blob_name)
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

            logger.debug(
                "Failed to find new content %d times in a row", num_fails)
            if num_fails >= num_fails_for_backoff:
                num_fails = 0
                sleep_time = min(sleep_time * 2, max_sleep_time)
                logger.debug("Resetting failure count to %d", num_fails)

            rnd = uniform(1, 2)  # 1.0 <= x < 2.0
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

    build_status = _get_run_status(metadata).lower()
    logger.debug("status was: '%s'", build_status)

    if raise_error_on_failure:
        if build_status in ('internalerror', 'failed'):
            raise CLIError("Run failed")
        if build_status == 'timedout':
            raise CLIError("Run timed out")
        if build_status == 'canceled':
            raise CLIError("Run was canceled")


def _stream_artifact_logs(log_file_sas,
                          no_format):

    if not no_format:
        colorama.init()

    try:
        response = requests.get(log_file_sas, timeout=3, verify=False, stream=True)
        response.raise_for_status()
    except KeyboardInterrupt:
        return
    except Exception as err:
        raise CLIError(err)

    for line in response.iter_lines():
        print(line.decode('utf-8', errors='ignore'))


def _blob_is_not_complete(metadata):
    if not metadata:
        return True
    for key in metadata:
        if key.lower() == 'complete':
            return False
    return True


def _get_run_status(metadata):
    if metadata is None:
        return 'inprogress'
    for key in metadata:
        if key.lower() == 'complete':
            return metadata[key]
    return 'inprogress'
