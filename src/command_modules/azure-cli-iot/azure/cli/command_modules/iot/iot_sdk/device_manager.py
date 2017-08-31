# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import time
import os
import threading
import functools
import six
from iothub_client import (IoTHubMessage, IoTHubMessageDispositionResult, DeviceMethodReturnValue,
                           IoTHubClient, IoTHubTransportProvider, IoTHubClientConfirmationResult)

six.print_ = functools.partial(six.print_, flush=True)


class DeviceManager(object):
    def __init__(self, connection_string, protocol=IoTHubTransportProvider.MQTT):
        self.receive_context = 0
        self.twin_context = 0
        self.reported_state_context = 0
        self.method_context = 0
        self.connection_status_context = 0

        # messageTimeout - the maximum time in milliseconds until a message times out.
        # The timeout period starts at IoTHubClient.send_event_async.
        # By default, messages do not expire.
        self.default_msg_timeout = 10000

        self.protocol = protocol
        self.client = IoTHubClient(connection_string, self.protocol)
        self.client.set_option("messageTimeout", self.default_msg_timeout)
        self.default_receive_settle = IoTHubMessageDispositionResult.ACCEPTED

        # Due to current event handling mechanics
        self._keep_alive = True
        self.send_error = None
        self.lock = threading.Lock()
        self.receive_count = 0

        # HTTP options
        # Because it can poll "after 9 seconds" polls will happen effectively
        # at ~10 seconds.
        # Note that for scalabilty, the default value of minimumPollingTime
        # is 25 minutes. For more information, see:
        # https://azure.microsoft.com/documentation/articles/iot-hub-devguide/#messaging
        self.http_timeout = 241000
        self.http_min_poll_time = 9

        if self.protocol == IoTHubTransportProvider.HTTP:
            self.client.set_option("timeout", self.http_timeout)
            self.client.set_option("MinimumPollingTime", self.http_min_poll_time)
        if self.protocol == IoTHubTransportProvider.MQTT:
            pass
            # self.client.set_option("logtrace", 0)
            # self.client.set_device_method_callback(self.device_method_callback, self.method_context)
            # self.reported_state = "{\"newState\":\"standBy\"}"
            # self.client.send_reported_state(self.reported_state, len(self.reported_state),
            #                                 self.send_reported_state_callback, self.reported_state_context)
        if self.protocol == IoTHubTransportProvider.AMQP:
            self.client.set_connection_status_callback(self.connection_status_callback,
                                                       self.connection_status_context)

    def keep_alive(self):
        return self._keep_alive

    def received(self):
        return self.receive_count

    def configure_device_twin_callback(self):
        if self.protocol == IoTHubTransportProvider.MQTT:
            self.client.set_device_twin_callback(self.device_twin_callback, self.twin_context)

    def configure_receive_settle(self, settle=None):
        if settle is not None:
            if settle == "reject":
                self.default_receive_settle = IoTHubMessageDispositionResult.REJECTED
            elif settle == "abandon":
                self.default_receive_settle = IoTHubMessageDispositionResult.ABANDONED
            else:
                self.default_receive_settle = IoTHubMessageDispositionResult.ACCEPTED
            # Callback
            self.client.set_message_callback(self.receive_message_callback, self.receive_context)
            return self.default_receive_settle

    def receive_message_callback(self, message, context):
        with self.lock:
            self.receive_count += 1

        message_buffer = message.get_bytearray()
        size = len(message_buffer)
        six.print_("\n")
        six.print_("_Received Message_")
        six.print_("Size: %d " % size)
        six.print_("Data: %s " % (message_buffer[:size].decode('utf-8')))
        map_properties = message.properties()
        key_value_pair = map_properties.get_internals()
        six.print_("Properties: %s" % key_value_pair)
        six.print_("Message settled with: %s" % self.default_receive_settle)

        return self.default_receive_settle

    def send_message(self, data, props, message_id=None, correlation_id=None, send_context=0, print_context=None):
        msg = IoTHubMessage(bytearray(data, 'utf8'))
        if message_id is not None:
            msg.message_id = message_id
        if correlation_id is not None:
            msg.correlation_id = correlation_id

        if props:
            for k in props.keys():
                properties = msg.properties()
                properties.add_or_update(str(k), props[k])

        if print_context:
            # flush buffer
            six.print_()
            six.print_("\n" + print_context)

        self.client.send_event_async(msg, self.send_confirmation_callback_quiet, send_context)

        # This section is due to current IoT SDK event mechanics
        time_accum = 0
        wait_time = 1
        while time_accum < self.default_msg_timeout and self.keep_alive():
            time.sleep(wait_time)
            time_accum += wait_time

        if self.send_error:
            raise RuntimeError(self.send_error)

    def send_confirmation_callback(self, message, result, context):
        six.print_("Confirmation[%d] received for message with result = %s" % (context, result))
        map_properties = message.properties()
        key_value_pair = map_properties.get_internals()
        six.print_("Properties: %s" % key_value_pair)

    def send_confirmation_callback_quiet(self, message, result, context):
        if result is not IoTHubClientConfirmationResult.OK:
            self.send_error = "Send message error. Result: %s" % result
        self._keep_alive = False

    def connection_status_callback(self, result, reason, user_context):
        # Leaving the callback helps prevents amqp destroy output
        pass
        # six.print_("Connection status changed[%d] with:" % (user_context))
        # six.print_("reason: %d" % reason)
        # six.print_("result: %s" % result)

    def send_reported_state(self, reported_state, size, context):
        self.client.send_reported_state(
            reported_state, size,
            self.send_reported_state_callback, context)

    def send_reported_state_callback(self, status_code, context):
        six.print_("Confirmation for reported state received.")
        six.print_("Status code = [%d]" % (status_code))

    def upload_file_to_blob(self, file_path):
        six.print_("Processing file upload...")
        _file = open(file_path, 'r')
        content = _file.read()
        filename = os.path.basename(file_path)
        six.print_('File path: %s, File name: %s' % (file_path, filename))
        self.upload_to_blob(filename, content, len(content), 1001)

    def upload_to_blob(self, destinationfilename, source, size, usercontext):
        self.client.upload_blob_async(
            destinationfilename, source, size,
            self.blob_upload_conf_callback, usercontext)

    def blob_upload_conf_callback(self, result, context):
        six.print_("Blob upload confirmation received for message with result = %s" % (result))

    def device_twin_callback(self, update_state, payload, context):
        six.print_("Twin callback called")
        six.print_("Update Status = %s" % update_state)
        six.print_("Payload = %s" % payload)

    def device_method_callback(self, method_name, payload, context):
        six.print_("\n")
        six.print_("_Device Method called_")
        six.print_("MethodName = %s" % (method_name))
        six.print_("Payload = %s" % (payload))

        device_method_return_value = DeviceMethodReturnValue()
        device_method_return_value.response = "{\"Result\":\"This is an example result from the device\"}\n"
        device_method_return_value.status = 200
        return device_method_return_value
