#-------------------------------------------------------------------------
# Copyright (c) Microsoft.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#--------------------------------------------------------------------------
from math import pow
from abc import ABCMeta

from .models import LocationMode

class _Retry(object):
    '''
    The base class for Exponential and Linear retries containing shared code.
    '''
    __metaclass__ = ABCMeta

    def __init__(self, max_attempts, retry_to_secondary):
        '''
        Constructs a base retry object.

        :param int max_attempts: 
            The maximum number of retry attempts.
        :param bool retry_to_secondary:
            Whether the request should be retried to secondary, if able. This should 
            only be enabled of RA-GRS accounts are used and potentially stale data 
            can be handled.
        '''
        self.max_attempts = max_attempts
        self.retry_to_secondary = retry_to_secondary

    def _should_retry(self, context):
        '''
        A function which determines whether or not to retry.

        :param ~azure.storage.models.RetryContext context: 
            The retry context. This contains the request, response, and other data 
            which can be used to determine whether or not to retry.
        :return: 
            A boolean indicating whether or not to retry the request.
        :rtype: bool
        '''
        # If max attempts are reached, do not retry.
        if (context.count >= self.max_attempts):
            return False

        status = None
        if context.response and context.response.status:
            status = context.response.status
        
        if status == None:
            '''
            If status is None, retry as this request triggered an exception. For 
            example, network issues would trigger this.
            '''
            return True
        elif status >= 200 and status < 300:
            '''
            This method is called after a successful response, meaning we failed 
            during the response body download or parsing. So, success codes should 
            be retried.
            '''
            return True
        elif status >= 300 and status < 500:
            '''
            An exception occured, but in most cases it was expected. Examples could 
            include a 309 Conflict or 412 Precondition Failed.
            '''
            if status == 404 and context.location_mode == LocationMode.SECONDARY:
                # Response code 404 should be retried if secondary was used.
                return True
            if status == 408:
                # Response code 408 is a timeout and should be retried.
                return True
            return False
        elif status >= 500:
            '''
            Response codes above 500 with the exception of 501 Not Implemented and 
            505 Version Not Supported indicate a server issue and should be retried.
            '''
            if status == 501 or status == 505:
                return False
            return True
        else:
            # If something else happened, it's unexpected. Retry.
            return True

    def _set_next_host_location(self, context):
        '''
        A function which sets the next host location on the request, if applicable. 

        :param ~azure.storage.models.RetryContext context: 
            The retry context containing the previous host location and the request 
            to evaluate and possibly modify.
        '''
        if len(context.request.host_locations) > 1:
            # If there's more than one possible location, retry to the alternative
            if context.location_mode == LocationMode.PRIMARY:
                context.location_mode = LocationMode.SECONDARY
            else:
                context.location_mode = LocationMode.PRIMARY

            context.request.host = context.request.host_locations.get(context.location_mode)

    def _retry(self, context, backoff):
        '''
        A function which determines whether and how to retry.

        :param ~azure.storage.models.RetryContext context: 
            The retry context. This contains the request, response, and other data 
            which can be used to determine whether or not to retry.
        :param function() backoff:
            A function which returns the backoff time if a retry is to be performed.
        :return: 
            An integer indicating how long to wait before retrying the request, 
            or None to indicate no retry should be performed.
        :rtype: int or None
        '''
        # If the context does not contain a count parameter, this request has not 
        # been retried yet. Add the count parameter to track the number of retries.
        if not hasattr(context, 'count'):
            context.count = 0

        # Determine whether to retry, and if so increment the count, modify the 
        # request as desired, and return the backoff.
        if self._should_retry(context):
            context.count += 1
            
            # If retry to secondary is enabled, attempt to change the host if the 
            # request allows it
            if self.retry_to_secondary:
                self._set_next_host_location(context)

            return backoff(context)

        return None


class ExponentialRetry(_Retry):
    '''
    Exponential retry.
    '''

    def __init__(self, initial_backoff=15, increment_power=3, max_attempts=3, 
                 retry_to_secondary=False):
        '''
        Constructs an Exponential retry object. The initial_backoff is used for 
        the first retry. Subsequent retries are retried after initial_backoff + 
        increment_power^retry_count seconds. For example, by default the first retry 
        occurs after 15 seconds, the second after (15+3^1) = 18 seconds, and the 
        third after (15+3^2) = 24 seconds.

        :param int initial_backoff: 
            The initial backoff interval, in seconds, for the first retry.
        :param int increment_power:
            The base, in seconds, to increment the initial_backoff by after the 
            first retry.
        :param int max_attempts: 
            The maximum number of retry attempts.
        :param bool retry_to_secondary:
            Whether the request should be retried to secondary, if able. This should 
            only be enabled of RA-GRS accounts are used and potentially stale data 
            can be handled.
        '''
        self.initial_backoff = initial_backoff
        self.increment_power = increment_power
        super(ExponentialRetry, self).__init__(max_attempts, retry_to_secondary)

    '''
    A function which determines whether and how to retry.

    :param ~azure.storage.models.RetryContext context: 
        The retry context. This contains the request, response, and other data 
        which can be used to determine whether or not to retry.
    :return: 
        An integer indicating how long to wait before retrying the request, 
        or None to indicate no retry should be performed.
    :rtype: int or None
    '''
    def retry(self, context):
        return self._retry(context, self._backoff)

    '''
    Calculates how long to sleep before retrying.

    :return: 
        An integer indicating how long to wait before retrying the request, 
        or None to indicate no retry should be performed.
    :rtype: int or None
    '''
    def _backoff(self, context):
        return self.initial_backoff + pow(self.increment_power, context.count)

class LinearRetry(_Retry):
    '''
    Linear retry.
    '''

    def __init__(self, backoff=15, max_attempts=3, retry_to_secondary=False):
        '''
        Constructs a Linear retry object.

        :param int backoff: 
            The backoff interval, in seconds, between retries.
        :param int max_attempts: 
            The maximum number of retry attempts.
        :param bool retry_to_secondary:
            Whether the request should be retried to secondary, if able. This should 
            only be enabled of RA-GRS accounts are used and potentially stale data 
            can be handled.
        '''
        self.backoff = backoff
        self.max_attempts = max_attempts
        super(LinearRetry, self).__init__(max_attempts, retry_to_secondary)

    '''
    A function which determines whether and how to retry.

    :param ~azure.storage.models.RetryContext context: 
        The retry context. This contains the request, response, and other data 
        which can be used to determine whether or not to retry.
    :return: 
        An integer indicating how long to wait before retrying the request, 
        or None to indicate no retry should be performed.
    :rtype: int or None
    '''
    def retry(self, context):
        return self._retry(context, self._backoff)

    '''
    Calculates how long to sleep before retrying.

    :return: 
        An integer indicating how long to wait before retrying the request, 
        or None to indicate no retry should be performed.
    :rtype: int or None
    '''
    def _backoff(self, context):
        return self.backoff

def no_retry(context):
    '''
    Specifies never to retry.

    :param ~azure.storage.models.RetryContext context: 
        The retry context.
    :return: 
        Always returns None to indicate never to retry.
    :rtype: None
    '''
    return None