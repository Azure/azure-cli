# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from ..common._common_conversion import _to_str


class Share(object):
    '''
    File share class.
    
    :ivar str name:
        The name of the share.
    :ivar ShareProperties properties:
        System properties for the share.
    :ivar metadata:
        A dict containing name-value pairs associated with the share as metadata.
        This var is set to None unless the include=metadata param was included 
        for the list shares operation. If this parameter was specified but the 
        share has no metadata, metadata will be set to an empty dictionary.
    :vartype metadata: dict(str, str)
    :ivar str snapshot:
        A DateTime value that uniquely identifies the snapshot. The value of
        this header indicates the snapshot version, and may be used in
        subsequent requests to access the snapshot.
    '''

    def __init__(self, name=None, props=None, metadata=None, snapshot=None):
        self.name = name
        self.properties = props or ShareProperties()
        self.metadata = metadata
        self.snapshot = snapshot


class ShareProperties(object):
    '''
    File share's properties class.
    
    :ivar datetime last_modified:
        A datetime object representing the last time the share was modified.
    :ivar str etag:
        The ETag contains a value that you can use to perform operations
        conditionally.
    :ivar int quote:
        Returns the current share quota in GB.
    '''

    def __init__(self):
        self.last_modified = None
        self.etag = None
        self.quota = None


class Directory(object):
    '''
    Directory class.
    
    :ivar str name:
        The name of the directory.
    :ivar DirectoryProperties properties:
        System properties for the directory.
    :ivar metadata:
        A dict containing name-value pairs associated with the directory as metadata.
        This var is set to None unless the include=metadata param was included 
        for the list directory operation. If this parameter was specified but the 
        directory has no metadata, metadata will be set to an empty dictionary.
    :vartype metadata: dict(str, str)
    '''

    def __init__(self, name=None, props=None, metadata=None):
        self.name = name
        self.properties = props or DirectoryProperties()
        self.metadata = metadata


class DirectoryProperties(object):
    '''
    File directory's properties class.
    
    :ivar datetime last_modified:
        A datetime object representing the last time the directory was modified.
    :ivar str etag:
        The ETag contains a value that you can use to perform operations
        conditionally.
    :ivar bool server_encrypted:
        Set to true if the directory metadata is encrypted on the server.
    '''

    def __init__(self):
        self.last_modified = None
        self.etag = None
        self.server_encrypted = None


class File(object):
    '''
    File class.
    
    :ivar str name:
        The name of the file.
    :ivar content:
        File content.
    :vartype content: str or bytes
    :ivar FileProperties properties:
        System properties for the file.
    :ivar metadata:
        A dict containing name-value pairs associated with the file as metadata.
        This var is set to None unless the include=metadata param was included 
        for the list file operation. If this parameter was specified but the 
        file has no metadata, metadata will be set to an empty dictionary.
    :vartype metadata: dict(str, str)
    '''

    def __init__(self, name=None, content=None, props=None, metadata=None):
        self.name = name
        self.content = content
        self.properties = props or FileProperties()
        self.metadata = metadata


class FileProperties(object):
    '''
    File Properties.
    
    :ivar datetime last_modified:
        A datetime object representing the last time the file was modified.
    :ivar str etag:
        The ETag contains a value that you can use to perform operations
        conditionally.
    :ivar int content_length:
        The length of the content returned. If the entire blob was requested, 
        the length of blob in bytes. If a subset of the blob was requested, the 
        length of the returned subset.
    :ivar str content_range:
        Indicates the range of bytes returned in the event that the client 
        requested a subset of the blob.
    :ivar ~azure.storage.file.models.ContentSettings content_settings:
        Stores all the content settings for the file.
    :ivar ~azure.storage.file.models.CopyProperties copy:
        Stores all the copy properties for the file.
    ivar bool server_encrypted:
        Set to true if the file data and application metadata are completely encrypted.
    '''

    def __init__(self):
        self.last_modified = None
        self.etag = None
        self.content_length = None
        self.content_range = None
        self.content_settings = ContentSettings()
        self.copy = CopyProperties()
        self.server_encrypted = None


class Handle(object):
    """
    Represents a file handle.

    :ivar str handle_id:
        Used to identify handle.
    :ivar str path:
        Used to identify the name of the object for which the handle is open.
    :ivar str file_id:
        Uniquely identifies the file.
        This is useful when renames are happening as the file ID does not change.
    :ivar str parent_id:
        Uniquely identifies the parent directory.
        This is useful when renames are happening as the parent ID does not change.
    :ivar str session_id:
        Session ID in context of which the file handle was opened.
    :ivar str client_ip:
        Used to identify client that has opened the handle.
        The field is included only if client IP is known by the service.
    :ivar datetime open_time:
        Used to decide if handle may have been leaked.
    :ivar datetime last_reconnect_time:
        Used to decide if handle was reopened after client/server disconnect due to networking or other faults.
        The field is included only if disconnect event occurred and handle was reopened.
    """

    def __init__(self, handle_id=None, path=None, file_id=None, parent_id=None, session_id=None,
                 client_ip=None, open_time=None, last_reconnect_time=None):
        self.handle_id = handle_id
        self.path = path
        self.file_id = file_id
        self.parent_id = parent_id
        self.session_id = session_id
        self.client_ip = client_ip
        self.open_time = open_time
        self.last_reconnect_time = last_reconnect_time


class ContentSettings(object):
    '''
    Used to store the content settings of a file.

    :ivar str content_type:
        The content type specified for the file. If no content type was
        specified, the default content type is application/octet-stream. 
    :ivar str content_encoding:
        If content_encoding has previously been set
        for the file, that value is stored.
    :ivar str content_language:
        If content_language has previously been set
        for the file, that value is stored.
    :ivar str content_disposition:
        content_disposition conveys additional information about how to
        process the response payload, and also can be used to attach
        additional metadata. If content_disposition has previously been set
        for the file, that value is stored.
    :ivar str cache_control:
        If cache_control has previously been set for
        the file, that value is stored.
    :ivar str content_md5:
        If the content_md5 has been set for the file, this response
        header is stored so that the client can check for message content
        integrity.
    '''

    def __init__(
            self, content_type=None, content_encoding=None,
            content_language=None, content_disposition=None,
            cache_control=None, content_md5=None):
        self.content_type = content_type
        self.content_encoding = content_encoding
        self.content_language = content_language
        self.content_disposition = content_disposition
        self.cache_control = cache_control
        self.content_md5 = content_md5

    def _to_headers(self):
        return {
            'x-ms-cache-control': _to_str(self.cache_control),
            'x-ms-content-type': _to_str(self.content_type),
            'x-ms-content-disposition': _to_str(self.content_disposition),
            'x-ms-content-md5': _to_str(self.content_md5),
            'x-ms-content-encoding': _to_str(self.content_encoding),
            'x-ms-content-language': _to_str(self.content_language),
        }


class CopyProperties(object):
    '''
    File Copy Properties.
    
    :ivar str id:
        String identifier for the last attempted Copy File operation where this file
        was the destination file. This header does not appear if this file has never
        been the destination in a Copy File operation, or if this file has been
        modified after a concluded Copy File operation using Set File Properties or
        Put File.
    :ivar str source:
        URL up to 2 KB in length that specifies the source file used in the last attempted
        Copy File operation where this file was the destination file. This header does not
        appear if this file has never been the destination in a Copy File operation, or if
        this file has been modified after a concluded Copy File operation using
        Set File Properties or Put File.
    :ivar str status:
        State of the copy operation identified by Copy ID, with these values:
            success:
                Copy completed successfully.
            pending: 
                Copy is in progress. Check copy_status_description if intermittent,
                non-fatal errors impede copy progress but don't cause failure.
            aborted:
                Copy was ended by Abort Copy File.
            failed:
                Copy failed. See copy_status_description for failure details.
    :ivar str progress:
        Contains the number of bytes copied and the total bytes in the source in the last
        attempted Copy File operation where this file was the destination file. Can show
        between 0 and Content-Length bytes copied.
    :ivar datetime completion_time:
        Conclusion time of the last attempted Copy File operation where this file was the
        destination file. This value can specify the time of a completed, aborted, or
        failed copy attempt.
    :ivar str status_description:
        Only appears when x-ms-copy-status is failed or pending. Describes cause of fatal
        or non-fatal copy operation failure. 
    '''

    def __init__(self):
        self.id = None
        self.source = None
        self.status = None
        self.progress = None
        self.completion_time = None
        self.status_description = None


class FileRange(object):
    '''
    File Range.
    
    :ivar int start:
        Byte index for start of file range.
    :ivar int end:
        Byte index for end of file range.
    '''

    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end


class DeleteSnapshot(object):
    '''
    Required if the Share has associated snapshots. Specifies how to handle the snapshots.
    '''

    Include = 'include'
    '''
    Delete the share and all of its snapshots.
    '''


class FilePermissions(object):
    '''
    FilePermissions class to be used with 
    :func:`~azure.storage.file.fileservice.FileService.generate_file_shared_access_signature` API.

    :ivar FilePermissions FilePermissions.CREATE:
        Create a new file or copy a file to a new file.
    :ivar FilePermissions FilePermissions.DELETE: 
        Delete the file.
    :ivar FilePermissions FilePermissions.READ:
        Read the content, properties, metadata. Use the file as the source of a copy 
        operation.
    :ivar FilePermissions FilePermissions.WRITE: 
        Create or write content, properties, metadata. Resize the file. Use the file 
        as the destination of a copy operation within the same account.
    '''

    def __init__(self, read=False, create=False, write=False, delete=False,
                 _str=None):
        '''
        :param bool read:
            Read the content, properties, metadata. Use the file as the source of a copy 
            operation.
        :param bool create:
            Create a new file or copy a file to a new file.
        :param bool write: 
            Create or write content, properties, metadata. Resize the file. Use the file 
            as the destination of a copy operation within the same account.
        :param bool delete: 
            Delete the file.
        :param str _str: 
            A string representing the permissions.
        '''

        if not _str:
            _str = ''
        self.read = read or ('r' in _str)
        self.create = create or ('c' in _str)
        self.write = write or ('w' in _str)
        self.delete = delete or ('d' in _str)

    def __or__(self, other):
        return FilePermissions(_str=str(self) + str(other))

    def __add__(self, other):
        return FilePermissions(_str=str(self) + str(other))

    def __str__(self):
        return (('r' if self.read else '') +
                ('c' if self.create else '') +
                ('w' if self.write else '') +
                ('d' if self.delete else ''))


FilePermissions.CREATE = FilePermissions(create=True)
FilePermissions.DELETE = FilePermissions(delete=True)
FilePermissions.READ = FilePermissions(read=True)
FilePermissions.WRITE = FilePermissions(write=True)


class SharePermissions(object):
    '''
    SharePermissions class to be used with `azure.storage.file.FileService.generate_share_shared_access_signature`
    method and for the AccessPolicies used with `azure.storage.file.FileService.set_share_acl`. 

    :ivar SharePermissions FilePermissions.DELETE: 
        Delete any file in the share.
        Note: You cannot grant permissions to delete a share with a service SAS. Use 
        an account SAS instead.
    :ivar SharePermissions FilePermissions.LIST: 
        List files and directories in the share.
    :ivar SharePermissions FilePermissions.READ:
        Read the content, properties or metadata of any file in the share. Use any 
        file in the share as the source of a copy operation.
    :ivar SharePermissions FilePermissions.WRITE: 
        For any file in the share, create or write content, properties or metadata. 
        Resize the file. Use the file as the destination of a copy operation within 
        the same account.
        Note: You cannot grant permissions to read or write share properties or 
        metadata with a service SAS. Use an account SAS instead.
    '''

    def __init__(self, read=False, write=False, delete=False, list=False,
                 _str=None):
        '''
        :param bool read:
            Read the content, properties or metadata of any file in the share. Use any 
            file in the share as the source of a copy operation.
        :param bool write: 
            For any file in the share, create or write content, properties or metadata. 
            Resize the file. Use the file as the destination of a copy operation within 
            the same account.
            Note: You cannot grant permissions to read or write share properties or 
            metadata with a service SAS. Use an account SAS instead.
        :param bool delete: 
            Delete any file in the share.
            Note: You cannot grant permissions to delete a share with a service SAS. Use 
            an account SAS instead.
        :param bool list: 
            List files and directories in the share.
        :param str _str: 
            A string representing the permissions
        '''

        if not _str:
            _str = ''
        self.read = read or ('r' in _str)
        self.write = write or ('w' in _str)
        self.delete = delete or ('d' in _str)
        self.list = list or ('l' in _str)

    def __or__(self, other):
        return SharePermissions(_str=str(self) + str(other))

    def __add__(self, other):
        return SharePermissions(_str=str(self) + str(other))

    def __str__(self):
        return (('r' if self.read else '') +
                ('w' if self.write else '') +
                ('d' if self.delete else '') +
                ('l' if self.list else ''))


SharePermissions.DELETE = SharePermissions(delete=True)
SharePermissions.LIST = SharePermissions(list=True)
SharePermissions.READ = SharePermissions(read=True)
SharePermissions.WRITE = SharePermissions(write=True)
