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
from datetime import date

from ._common_conversion import (
    _sign_string,
    _to_str,
)
from ._serialization import (
    url_quote,
    _to_utc_datetime,
)
from ._constants import X_MS_VERSION

class SharedAccessSignature(object):
    '''
    Provides a factory for creating blob, queue, table, and file shares access 
    signature tokens with a common account name and account key.  Users can either 
    use the factory or can construct the appropriate service and use the 
    generate_*_shared_access_signature method directly.
    '''

    def __init__(self, account_name, account_key):
        '''
        :param str account_name:
            The storage account name used to generate the shared access signatures.
        :param str account_key:
            The access key to genenerate the shares access signatures.
        '''
        self.account_name = account_name
        self.account_key = account_key

    def generate_table(self, table_name, permission=None, 
                        expiry=None, start=None, id=None,
                        ip=None, protocol=None,
                        start_pk=None, start_rk=None, 
                        end_pk=None, end_rk=None):
        '''
        Generates a shared access signature for the table.
        Use the returned signature with the sas_token parameter of TableService.

        :param str table_name:
            Name of table.
        :param TablePermissions permission:
            The permissions associated with the shared access signature. The 
            user is restricted to operations allowed by the permissions. 
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has been 
            specified in an associated stored access policy.
        :param expiry:
            The time at which the shared access signature becomes invalid. 
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has 
            been specified in an associated stored access policy. Azure will always 
            convert values to UTC. If a date is passed in without timezone info, it 
            is assumed to be UTC.
        :type expiry: date or str
        :param start:
            The time at which the shared access signature becomes valid. If 
            omitted, start time for this call is assumed to be the time when the 
            storage service receives the request. Azure will always convert values 
            to UTC. If a date is passed in without timezone info, it is assumed to 
            be UTC.
        :type start: date or str
        :param str id:
            A unique value up to 64 characters in length that correlates to a 
            stored access policy. To create a stored access policy, use 
            set_blob_service_properties.
        :param str ip:
            Specifies an IP address or a range of IP addresses from which to accept requests.
            If the IP address from which the request originates does not match the IP address
            or address range specified on the SAS token, the request is not authenticated.
            For example, specifying sip=168.1.5.65 or sip=168.1.5.60-168.1.5.70 on the SAS
            restricts the request to those IP addresses.
        :param str protocol:
            Specifies the protocol permitted for a request made. The default value
            is https,http. See :class:`~azure.storage.models.Protocol` for possible values.
        :param str start_pk:
            The minimum partition key accessible with this shared access 
            signature. startpk must accompany startrk. Key values are inclusive. 
            If omitted, there is no lower bound on the table entities that can 
            be accessed.
        :param str start_rk:
            The minimum row key accessible with this shared access signature. 
            startpk must accompany startrk. Key values are inclusive. If 
            omitted, there is no lower bound on the table entities that can be 
            accessed.
        :param str end_pk:
            The maximum partition key accessible with this shared access 
            signature. endpk must accompany endrk. Key values are inclusive. If 
            omitted, there is no upper bound on the table entities that can be 
            accessed.
        :param str end_rk:
            The maximum row key accessible with this shared access signature. 
            endpk must accompany endrk. Key values are inclusive. If omitted, 
            there is no upper bound on the table entities that can be accessed.
        '''
        sas = _SharedAccessHelper()
        sas.add_base(permission, expiry, start, ip, protocol)
        sas.add_id(id)
        sas.add_table_access_ranges(table_name, start_pk, start_rk, end_pk, end_rk)
        sas.add_resource_signature(self.account_name, self.account_key, 'table', table_name)

        return sas.get_token()

    def generate_queue(self, queue_name, permission=None, 
                        expiry=None, start=None, id=None,
                        ip=None, protocol=None):
        '''
        Generates a shared access signature for the queue.
        Use the returned signature with the sas_token parameter of QueueService.

        :param str queue_name:
            Name of queue.
        :param QueuePermissions permission:
            The permissions associated with the shared access signature. The 
            user is restricted to operations allowed by the permissions.
            Permissions must be ordered read, add, update, process.
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has been 
            specified in an associated stored access policy.
        :param expiry:
            The time at which the shared access signature becomes invalid. 
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has 
            been specified in an associated stored access policy. Azure will always 
            convert values to UTC. If a date is passed in without timezone info, it 
            is assumed to be UTC.
        :type expiry: date or str
        :param start:
            The time at which the shared access signature becomes valid. If 
            omitted, start time for this call is assumed to be the time when the 
            storage service receives the request. Azure will always convert values 
            to UTC. If a date is passed in without timezone info, it is assumed to 
            be UTC.
        :type start: date or str
        :param str id:
            A unique value up to 64 characters in length that correlates to a 
            stored access policy. To create a stored access policy, use 
            set_blob_service_properties.
        :param str ip:
            Specifies an IP address or a range of IP addresses from which to accept requests.
            If the IP address from which the request originates does not match the IP address
            or address range specified on the SAS token, the request is not authenticated.
            For example, specifying sip=168.1.5.65 or sip=168.1.5.60-168.1.5.70 on the SAS
            restricts the request to those IP addresses.
        :param str protocol:
            Specifies the protocol permitted for a request made. The default value
            is https,http. See :class:`~azure.storage.models.Protocol` for possible values.
        '''
        sas = _SharedAccessHelper()
        sas.add_base(permission, expiry, start, ip, protocol)
        sas.add_id(id)
        sas.add_resource_signature(self.account_name, self.account_key, 'queue', queue_name)

        return sas.get_token()

    def generate_blob(self, container_name, blob_name, permission=None, 
                        expiry=None, start=None, id=None, ip=None, protocol=None,
                        cache_control=None, content_disposition=None,
                        content_encoding=None, content_language=None,
                        content_type=None):
        '''
        Generates a shared access signature for the blob.
        Use the returned signature with the sas_token parameter of any BlobService.

        :param str container_name:
            Name of container.
        :param str blob_name:
            Name of blob.
        :param BlobPermissions permission:
            The permissions associated with the shared access signature. The 
            user is restricted to operations allowed by the permissions.
            Permissions must be ordered read, write, delete, list.
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has been 
            specified in an associated stored access policy.
        :param expiry:
            The time at which the shared access signature becomes invalid. 
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has 
            been specified in an associated stored access policy. Azure will always 
            convert values to UTC. If a date is passed in without timezone info, it 
            is assumed to be UTC.
        :type expiry: date or str
        :param start:
            The time at which the shared access signature becomes valid. If 
            omitted, start time for this call is assumed to be the time when the 
            storage service receives the request. Azure will always convert values 
            to UTC. If a date is passed in without timezone info, it is assumed to 
            be UTC.
        :type start: date or str
        :param str id:
            A unique value up to 64 characters in length that correlates to a 
            stored access policy. To create a stored access policy, use 
            set_blob_service_properties.
        :param str ip:
            Specifies an IP address or a range of IP addresses from which to accept requests.
            If the IP address from which the request originates does not match the IP address
            or address range specified on the SAS token, the request is not authenticated.
            For example, specifying sip=168.1.5.65 or sip=168.1.5.60-168.1.5.70 on the SAS
            restricts the request to those IP addresses.
        :param str protocol:
            Specifies the protocol permitted for a request made. The default value
            is https,http. See :class:`~azure.storage.models.Protocol` for possible values.
        :param str cache_control:
            Response header value for Cache-Control when resource is accessed
            using this shared access signature.
        :param str content_disposition:
            Response header value for Content-Disposition when resource is accessed
            using this shared access signature.
        :param str content_encoding:
            Response header value for Content-Encoding when resource is accessed
            using this shared access signature.
        :param str content_language:
            Response header value for Content-Language when resource is accessed
            using this shared access signature.
        :param str content_type:
            Response header value for Content-Type when resource is accessed
            using this shared access signature.
        '''
        resource_path = container_name + '/' + blob_name

        sas = _SharedAccessHelper()
        sas.add_base(permission, expiry, start, ip, protocol)
        sas.add_id(id)
        sas.add_resource('b')
        sas.add_override_response_headers(cache_control, content_disposition, 
                                          content_encoding, content_language, 
                                          content_type)
        sas.add_resource_signature(self.account_name, self.account_key, 'blob', resource_path)

        return sas.get_token()

    def generate_container(self, container_name, permission=None, expiry=None, 
                        start=None, id=None, ip=None, protocol=None,
                        cache_control=None, content_disposition=None,
                        content_encoding=None, content_language=None,
                        content_type=None):
        '''
        Generates a shared access signature for the container.
        Use the returned signature with the sas_token parameter of any BlobService.

        :param str container_name:
            Name of container.
        :param ContainerPermissions permission:
            The permissions associated with the shared access signature. The 
            user is restricted to operations allowed by the permissions.
            Permissions must be ordered read, write, delete, list.
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has been 
            specified in an associated stored access policy.
        :param expiry:
            The time at which the shared access signature becomes invalid. 
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has 
            been specified in an associated stored access policy. Azure will always 
            convert values to UTC. If a date is passed in without timezone info, it 
            is assumed to be UTC.
        :type expiry: date or str
        :param start:
            The time at which the shared access signature becomes valid. If 
            omitted, start time for this call is assumed to be the time when the 
            storage service receives the request. Azure will always convert values 
            to UTC. If a date is passed in without timezone info, it is assumed to 
            be UTC.
        :type start: date or str
        :param str id:
            A unique value up to 64 characters in length that correlates to a 
            stored access policy. To create a stored access policy, use 
            set_blob_service_properties.
        :param str ip:
            Specifies an IP address or a range of IP addresses from which to accept requests.
            If the IP address from which the request originates does not match the IP address
            or address range specified on the SAS token, the request is not authenticated.
            For example, specifying sip=168.1.5.65 or sip=168.1.5.60-168.1.5.70 on the SAS
            restricts the request to those IP addresses.
        :param str protocol:
            Specifies the protocol permitted for a request made. The default value
            is https,http. See :class:`~azure.storage.models.Protocol` for possible values.
        :param str cache_control:
            Response header value for Cache-Control when resource is accessed
            using this shared access signature.
        :param str content_disposition:
            Response header value for Content-Disposition when resource is accessed
            using this shared access signature.
        :param str content_encoding:
            Response header value for Content-Encoding when resource is accessed
            using this shared access signature.
        :param str content_language:
            Response header value for Content-Language when resource is accessed
            using this shared access signature.
        :param str content_type:
            Response header value for Content-Type when resource is accessed
            using this shared access signature.
        '''
        sas = _SharedAccessHelper()
        sas.add_base(permission, expiry, start, ip, protocol)
        sas.add_id(id)
        sas.add_resource('c')
        sas.add_override_response_headers(cache_control, content_disposition, 
                                          content_encoding, content_language, 
                                          content_type)
        sas.add_resource_signature(self.account_name, self.account_key, 'blob', container_name)

        return sas.get_token()

    def generate_file(self, share_name, directory_name=None, file_name=None, 
                      permission=None, expiry=None, start=None, id=None,
                      ip=None, protocol=None, cache_control=None,
                      content_disposition=None, content_encoding=None, 
                      content_language=None, content_type=None):
        '''
        Generates a shared access signature for the file.
        Use the returned signature with the sas_token parameter of FileService.

        :param str share_name:
            Name of share.
        :param str directory_name:
            Name of directory. SAS tokens cannot be created for directories, so 
            this parameter should only be present if file_name is provided.
        :param str file_name:
            Name of file.
        :param FilePermissions permission:
            The permissions associated with the shared access signature. The 
            user is restricted to operations allowed by the permissions.
            Permissions must be ordered read, create, write, delete, list.
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has been 
            specified in an associated stored access policy.
        :param expiry:
            The time at which the shared access signature becomes invalid. 
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has 
            been specified in an associated stored access policy. Azure will always 
            convert values to UTC. If a date is passed in without timezone info, it 
            is assumed to be UTC.
        :type expiry: date or str
        :param start:
            The time at which the shared access signature becomes valid. If 
            omitted, start time for this call is assumed to be the time when the 
            storage service receives the request. Azure will always convert values 
            to UTC. If a date is passed in without timezone info, it is assumed to 
            be UTC.
        :type start: date or str
        :param str id:
            A unique value up to 64 characters in length that correlates to a 
            stored access policy. To create a stored access policy, use 
            set_file_service_properties.
        :param str ip:
            Specifies an IP address or a range of IP addresses from which to accept requests.
            If the IP address from which the request originates does not match the IP address
            or address range specified on the SAS token, the request is not authenticated.
            For example, specifying sip=168.1.5.65 or sip=168.1.5.60-168.1.5.70 on the SAS
            restricts the request to those IP addresses.
        :param str protocol:
            Specifies the protocol permitted for a request made. The default value
            is https,http. See :class:`~azure.storage.models.Protocol` for possible values.
        :param str cache_control:
            Response header value for Cache-Control when resource is accessed
            using this shared access signature.
        :param str content_disposition:
            Response header value for Content-Disposition when resource is accessed
            using this shared access signature.
        :param str content_encoding:
            Response header value for Content-Encoding when resource is accessed
            using this shared access signature.
        :param str content_language:
            Response header value for Content-Language when resource is accessed
            using this shared access signature.
        :param str content_type:
            Response header value for Content-Type when resource is accessed
            using this shared access signature.
        '''
        resource_path = share_name
        if directory_name is not None:
            resource_path += '/' + _to_str(directory_name)
        resource_path += '/' + _to_str(file_name)

        sas = _SharedAccessHelper()
        sas.add_base(permission, expiry, start, ip, protocol)
        sas.add_id(id)
        sas.add_resource('f')
        sas.add_override_response_headers(cache_control, content_disposition, 
                                          content_encoding, content_language, 
                                          content_type)
        sas.add_resource_signature(self.account_name, self.account_key, 'file', resource_path)

        return sas.get_token()

    def generate_share(self, share_name, permission=None, expiry=None, 
                       start=None, id=None, ip=None, protocol=None, 
                       cache_control=None, content_disposition=None, 
                       content_encoding=None, content_language=None, 
                       content_type=None):
        '''
        Generates a shared access signature for the share.
        Use the returned signature with the sas_token parameter of FileService.

        :param str share_name:
            Name of share.
        :param SharePermissions permission:
            The permissions associated with the shared access signature. The 
            user is restricted to operations allowed by the permissions.
            Permissions must be ordered read, create, write, delete, list.
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has been 
            specified in an associated stored access policy.
        :param expiry:
            The time at which the shared access signature becomes invalid. 
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has 
            been specified in an associated stored access policy. Azure will always 
            convert values to UTC. If a date is passed in without timezone info, it 
            is assumed to be UTC.
        :type expiry: date or str
        :param start:
            The time at which the shared access signature becomes valid. If 
            omitted, start time for this call is assumed to be the time when the 
            storage service receives the request. Azure will always convert values 
            to UTC. If a date is passed in without timezone info, it is assumed to 
            be UTC.
        :type start: date or str
        :param str id:
            A unique value up to 64 characters in length that correlates to a 
            stored access policy. To create a stored access policy, use 
            set_file_service_properties.
        :param str ip:
            Specifies an IP address or a range of IP addresses from which to accept requests.
            If the IP address from which the request originates does not match the IP address
            or address range specified on the SAS token, the request is not authenticated.
            For example, specifying sip=168.1.5.65 or sip=168.1.5.60-168.1.5.70 on the SAS
            restricts the request to those IP addresses.
        :param str protocol:
            Specifies the protocol permitted for a request made. The default value
            is https,http. See :class:`~azure.storage.models.Protocol` for possible values.
        :param str cache_control:
            Response header value for Cache-Control when resource is accessed
            using this shared access signature.
        :param str content_disposition:
            Response header value for Content-Disposition when resource is accessed
            using this shared access signature.
        :param str content_encoding:
            Response header value for Content-Encoding when resource is accessed
            using this shared access signature.
        :param str content_language:
            Response header value for Content-Language when resource is accessed
            using this shared access signature.
        :param str content_type:
            Response header value for Content-Type when resource is accessed
            using this shared access signature.
        '''
        sas = _SharedAccessHelper()
        sas.add_base(permission, expiry, start, ip, protocol)
        sas.add_id(id)
        sas.add_resource('s')
        sas.add_override_response_headers(cache_control, content_disposition, 
                                          content_encoding, content_language, 
                                          content_type)
        sas.add_resource_signature(self.account_name, self.account_key, 'file', share_name)

        return sas.get_token()

    def generate_account(self, services, resource_types, permission, expiry, start=None, 
                         ip=None, protocol=None):
        '''
        Generates a shared access signature for the account.
        Use the returned signature with the sas_token parameter of the service 
        or to create a new account object.

        :param Services services:
            Specifies the services accessible with the account SAS. You can 
            combine values to provide access to more than one service. 
        :param ResourceTypes resource_types:
            Specifies the resource types that are accessible with the account 
            SAS. You can combine values to provide access to more than one 
            resource type. 
        :param AccountPermissions permission:
            The permissions associated with the shared access signature. The 
            user is restricted to operations allowed by the permissions. 
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has been 
            specified in an associated stored access policy. You can combine 
            values to provide more than one permission.
        :param expiry:
            The time at which the shared access signature becomes invalid. 
            Required unless an id is given referencing a stored access policy 
            which contains this field. This field must be omitted if it has 
            been specified in an associated stored access policy. Azure will always 
            convert values to UTC. If a date is passed in without timezone info, it 
            is assumed to be UTC.
        :type expiry: date or str
        :param start:
            The time at which the shared access signature becomes valid. If 
            omitted, start time for this call is assumed to be the time when the 
            storage service receives the request. Azure will always convert values 
            to UTC. If a date is passed in without timezone info, it is assumed to 
            be UTC.
        :type start: date or str
        :param str ip:
            Specifies an IP address or a range of IP addresses from which to accept requests.
            If the IP address from which the request originates does not match the IP address
            or address range specified on the SAS token, the request is not authenticated.
            For example, specifying sip=168.1.5.65 or sip=168.1.5.60-168.1.5.70 on the SAS
            restricts the request to those IP addresses.
        :param str protocol:
            Specifies the protocol permitted for a request made. The default value
            is https,http. See :class:`~azure.storage.models.Protocol` for possible values.
        '''
        sas = _SharedAccessHelper()
        sas.add_base(permission, expiry, start, ip, protocol)
        sas.add_account(services, resource_types)
        sas.add_account_signature(self.account_name, self.account_key)

        return sas.get_token()

class _QueryStringConstants(object):
    SIGNED_SIGNATURE = 'sig'
    SIGNED_PERMISSION = 'sp'
    SIGNED_START = 'st'
    SIGNED_EXPIRY = 'se'
    SIGNED_RESOURCE = 'sr'
    SIGNED_IDENTIFIER = 'si'
    SIGNED_IP = 'sip'
    SIGNED_PROTOCOL = 'spr'
    SIGNED_VERSION = 'sv'
    SIGNED_CACHE_CONTROL = 'rscc'
    SIGNED_CONTENT_DISPOSITION = 'rscd'
    SIGNED_CONTENT_ENCODING = 'rsce'
    SIGNED_CONTENT_LANGUAGE = 'rscl'
    SIGNED_CONTENT_TYPE = 'rsct'
    TABLE_NAME = 'tn'
    START_PK = 'spk'
    START_RK = 'srk'
    END_PK = 'epk'
    END_RK = 'erk'
    SIGNED_RESOURCE_TYPES = 'srt'
    SIGNED_SERVICES = 'ss'

class _SharedAccessHelper():

    def __init__(self):
        self.query_dict = {}

    def _add_query(self, name, val):
        if val:
            self.query_dict[name] = _to_str(val)

    def add_base(self, permission, expiry, start, ip, protocol):
        if isinstance(start, date):
            start = _to_utc_datetime(start)

        if isinstance(expiry, date):
            expiry = _to_utc_datetime(expiry)

        self._add_query(_QueryStringConstants.SIGNED_START, start)
        self._add_query(_QueryStringConstants.SIGNED_EXPIRY, expiry)
        self._add_query(_QueryStringConstants.SIGNED_PERMISSION, permission)
        self._add_query(_QueryStringConstants.SIGNED_IP, ip)
        self._add_query(_QueryStringConstants.SIGNED_PROTOCOL, protocol)
        self._add_query(_QueryStringConstants.SIGNED_VERSION, X_MS_VERSION)

    def add_resource(self, resource):
        self._add_query(_QueryStringConstants.SIGNED_RESOURCE, resource)

    def add_id(self, id):
        self._add_query(_QueryStringConstants.SIGNED_IDENTIFIER, id)

    def add_account(self, services, resource_types):
        self._add_query(_QueryStringConstants.SIGNED_SERVICES, services)
        self._add_query(_QueryStringConstants.SIGNED_RESOURCE_TYPES, resource_types)

    def add_table_access_ranges(self, table_name, start_pk, start_rk, 
                                    end_pk, end_rk):
        self._add_query(_QueryStringConstants.TABLE_NAME, table_name)
        self._add_query(_QueryStringConstants.START_PK, start_pk)
        self._add_query(_QueryStringConstants.START_RK, start_rk)
        self._add_query(_QueryStringConstants.END_PK, end_pk)
        self._add_query(_QueryStringConstants.END_RK, end_rk)

    def add_override_response_headers(self, cache_control,
                                        content_disposition,
                                        content_encoding,
                                        content_language,
                                        content_type):
        self._add_query(_QueryStringConstants.SIGNED_CACHE_CONTROL, cache_control)
        self._add_query(_QueryStringConstants.SIGNED_CONTENT_DISPOSITION, content_disposition)
        self._add_query(_QueryStringConstants.SIGNED_CONTENT_ENCODING, content_encoding)
        self._add_query(_QueryStringConstants.SIGNED_CONTENT_LANGUAGE, content_language)
        self._add_query(_QueryStringConstants.SIGNED_CONTENT_TYPE, content_type)

    def add_resource_signature(self, account_name, account_key, service, path):
        def get_value_to_append(query):
            return_value = self.query_dict.get(query) or ''
            return return_value + '\n'

        if path[0] != '/':
            path = '/' + path

        canonicalized_resource = '/' + service + '/' + account_name + path + '\n'

        # Form the string to sign from shared_access_policy and canonicalized
        # resource. The order of values is important.
        string_to_sign = \
            (get_value_to_append(_QueryStringConstants.SIGNED_PERMISSION) +
                get_value_to_append(_QueryStringConstants.SIGNED_START) +
                get_value_to_append(_QueryStringConstants.SIGNED_EXPIRY) +
                canonicalized_resource +
                get_value_to_append(_QueryStringConstants.SIGNED_IDENTIFIER) +
                get_value_to_append(_QueryStringConstants.SIGNED_IP) +
                get_value_to_append(_QueryStringConstants.SIGNED_PROTOCOL) +
                get_value_to_append(_QueryStringConstants.SIGNED_VERSION))

        if service == 'blob' or service == 'file':
            string_to_sign += \
                (get_value_to_append(_QueryStringConstants.SIGNED_CACHE_CONTROL) +
                get_value_to_append(_QueryStringConstants.SIGNED_CONTENT_DISPOSITION) +
                get_value_to_append(_QueryStringConstants.SIGNED_CONTENT_ENCODING) +
                get_value_to_append(_QueryStringConstants.SIGNED_CONTENT_LANGUAGE) +
                get_value_to_append(_QueryStringConstants.SIGNED_CONTENT_TYPE))

        if service == 'table':
            string_to_sign += \
                (get_value_to_append(_QueryStringConstants.START_PK) +
                get_value_to_append(_QueryStringConstants.START_RK) +
                get_value_to_append(_QueryStringConstants.END_PK) +
                get_value_to_append(_QueryStringConstants.END_RK))

        # remove the trailing newline
        if string_to_sign[-1] == '\n':
            string_to_sign = string_to_sign[:-1]

        self._add_query(_QueryStringConstants.SIGNED_SIGNATURE, 
                        _sign_string(account_key, string_to_sign))

    def add_account_signature(self, account_name, account_key):
        def get_value_to_append(query):
            return_value = self.query_dict.get(query) or ''
            return return_value + '\n'

        string_to_sign = \
            (account_name + '\n' +
                get_value_to_append(_QueryStringConstants.SIGNED_PERMISSION) +
                get_value_to_append(_QueryStringConstants.SIGNED_SERVICES) +
                get_value_to_append(_QueryStringConstants.SIGNED_RESOURCE_TYPES) +
                get_value_to_append(_QueryStringConstants.SIGNED_START) +
                get_value_to_append(_QueryStringConstants.SIGNED_EXPIRY) +
                get_value_to_append(_QueryStringConstants.SIGNED_IP) +
                get_value_to_append(_QueryStringConstants.SIGNED_PROTOCOL) +
                get_value_to_append(_QueryStringConstants.SIGNED_VERSION))

        self._add_query(_QueryStringConstants.SIGNED_SIGNATURE, 
                        _sign_string(account_key, string_to_sign))

    def get_token(self):
        return '&'.join(['{0}={1}'.format(n, url_quote(v)) for n, v in self.query_dict.items() if v is not None])