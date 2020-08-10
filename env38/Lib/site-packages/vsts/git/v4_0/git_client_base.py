# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest import Serializer, Deserializer
from ...vss_client import VssClient
from . import models


class GitClientBase(VssClient):
    """Git
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(GitClientBase, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = '4e080c62-fa21-4fbc-8fef-2a10a2b38049'

    def create_annotated_tag(self, tag_object, project, repository_id):
        """CreateAnnotatedTag.
        [Preview API] Create an annotated tag
        :param :class:`<GitAnnotatedTag> <git.v4_0.models.GitAnnotatedTag>` tag_object: Object containing details of tag to be created
        :param str project: Project ID or project name
        :param str repository_id: Friendly name or guid of repository
        :rtype: :class:`<GitAnnotatedTag> <git.v4_0.models.GitAnnotatedTag>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        content = self._serialize.body(tag_object, 'GitAnnotatedTag')
        response = self._send(http_method='POST',
                              location_id='5e8a8081-3851-4626-b677-9891cc04102e',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('GitAnnotatedTag', response)

    def get_annotated_tag(self, project, repository_id, object_id):
        """GetAnnotatedTag.
        [Preview API] Get an annotated tag
        :param str project: Project ID or project name
        :param str repository_id:
        :param str object_id: Sha1 of annotated tag to be returned
        :rtype: :class:`<GitAnnotatedTag> <git.v4_0.models.GitAnnotatedTag>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if object_id is not None:
            route_values['objectId'] = self._serialize.url('object_id', object_id, 'str')
        response = self._send(http_method='GET',
                              location_id='5e8a8081-3851-4626-b677-9891cc04102e',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('GitAnnotatedTag', response)

    def get_blob(self, repository_id, sha1, project=None, download=None, file_name=None):
        """GetBlob.
        Gets a single blob.
        :param str repository_id:
        :param str sha1:
        :param str project: Project ID or project name
        :param bool download:
        :param str file_name:
        :rtype: :class:`<GitBlobRef> <git.v4_0.models.GitBlobRef>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if sha1 is not None:
            route_values['sha1'] = self._serialize.url('sha1', sha1, 'str')
        query_parameters = {}
        if download is not None:
            query_parameters['download'] = self._serialize.query('download', download, 'bool')
        if file_name is not None:
            query_parameters['fileName'] = self._serialize.query('file_name', file_name, 'str')
        response = self._send(http_method='GET',
                              location_id='7b28e929-2c99-405d-9c5c-6167a06e6816',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('GitBlobRef', response)

    def get_blob_content(self, repository_id, sha1, project=None, download=None, file_name=None, **kwargs):
        """GetBlobContent.
        Gets a single blob.
        :param str repository_id:
        :param str sha1:
        :param str project: Project ID or project name
        :param bool download:
        :param str file_name:
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if sha1 is not None:
            route_values['sha1'] = self._serialize.url('sha1', sha1, 'str')
        query_parameters = {}
        if download is not None:
            query_parameters['download'] = self._serialize.query('download', download, 'bool')
        if file_name is not None:
            query_parameters['fileName'] = self._serialize.query('file_name', file_name, 'str')
        response = self._send(http_method='GET',
                              location_id='7b28e929-2c99-405d-9c5c-6167a06e6816',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              accept_media_type='application/octet-stream')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_blobs_zip(self, blob_ids, repository_id, project=None, filename=None, **kwargs):
        """GetBlobsZip.
        Gets one or more blobs in a zip file download.
        :param [str] blob_ids:
        :param str repository_id:
        :param str project: Project ID or project name
        :param str filename:
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if filename is not None:
            query_parameters['filename'] = self._serialize.query('filename', filename, 'str')
        content = self._serialize.body(blob_ids, '[str]')
        response = self._send(http_method='POST',
                              location_id='7b28e929-2c99-405d-9c5c-6167a06e6816',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content,
                              accept_media_type='application/zip')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_blob_zip(self, repository_id, sha1, project=None, download=None, file_name=None, **kwargs):
        """GetBlobZip.
        Gets a single blob.
        :param str repository_id:
        :param str sha1:
        :param str project: Project ID or project name
        :param bool download:
        :param str file_name:
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if sha1 is not None:
            route_values['sha1'] = self._serialize.url('sha1', sha1, 'str')
        query_parameters = {}
        if download is not None:
            query_parameters['download'] = self._serialize.query('download', download, 'bool')
        if file_name is not None:
            query_parameters['fileName'] = self._serialize.query('file_name', file_name, 'str')
        response = self._send(http_method='GET',
                              location_id='7b28e929-2c99-405d-9c5c-6167a06e6816',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              accept_media_type='application/zip')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_branch(self, repository_id, name, project=None, base_version_descriptor=None):
        """GetBranch.
        Retrieve statistics about a single branch.
        :param str repository_id: Friendly name or guid of repository
        :param str name: Name of the branch
        :param str project: Project ID or project name
        :param :class:`<GitVersionDescriptor> <git.v4_0.models.GitVersionDescriptor>` base_version_descriptor:
        :rtype: :class:`<GitBranchStats> <git.v4_0.models.GitBranchStats>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if name is not None:
            query_parameters['name'] = self._serialize.query('name', name, 'str')
        if base_version_descriptor is not None:
            if base_version_descriptor.version_type is not None:
                query_parameters['baseVersionDescriptor.versionType'] = base_version_descriptor.version_type
            if base_version_descriptor.version is not None:
                query_parameters['baseVersionDescriptor.version'] = base_version_descriptor.version
            if base_version_descriptor.version_options is not None:
                query_parameters['baseVersionDescriptor.versionOptions'] = base_version_descriptor.version_options
        response = self._send(http_method='GET',
                              location_id='d5b216de-d8d5-4d32-ae76-51df755b16d3',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('GitBranchStats', response)

    def get_branches(self, repository_id, project=None, base_version_descriptor=None):
        """GetBranches.
        Retrieve statistics about all branches within a repository.
        :param str repository_id: Friendly name or guid of repository
        :param str project: Project ID or project name
        :param :class:`<GitVersionDescriptor> <git.v4_0.models.GitVersionDescriptor>` base_version_descriptor:
        :rtype: [GitBranchStats]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if base_version_descriptor is not None:
            if base_version_descriptor.version_type is not None:
                query_parameters['baseVersionDescriptor.versionType'] = base_version_descriptor.version_type
            if base_version_descriptor.version is not None:
                query_parameters['baseVersionDescriptor.version'] = base_version_descriptor.version
            if base_version_descriptor.version_options is not None:
                query_parameters['baseVersionDescriptor.versionOptions'] = base_version_descriptor.version_options
        response = self._send(http_method='GET',
                              location_id='d5b216de-d8d5-4d32-ae76-51df755b16d3',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[GitBranchStats]', self._unwrap_collection(response))

    def get_branch_stats_batch(self, search_criteria, repository_id, project=None):
        """GetBranchStatsBatch.
        Retrieve statistics for multiple commits
        :param :class:`<GitQueryBranchStatsCriteria> <git.v4_0.models.GitQueryBranchStatsCriteria>` search_criteria:
        :param str repository_id: Friendly name or guid of repository
        :param str project: Project ID or project name
        :rtype: [GitBranchStats]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        content = self._serialize.body(search_criteria, 'GitQueryBranchStatsCriteria')
        response = self._send(http_method='POST',
                              location_id='d5b216de-d8d5-4d32-ae76-51df755b16d3',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[GitBranchStats]', self._unwrap_collection(response))

    def get_changes(self, commit_id, repository_id, project=None, top=None, skip=None):
        """GetChanges.
        Retrieve changes for a particular commit.
        :param str commit_id: The id of the commit.
        :param str repository_id: The id or friendly name of the repository. To use the friendly name, projectId must also be specified.
        :param str project: Project ID or project name
        :param int top: The maximum number of changes to return.
        :param int skip: The number of changes to skip.
        :rtype: :class:`<GitCommitChanges> <git.v4_0.models.GitCommitChanges>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if commit_id is not None:
            route_values['commitId'] = self._serialize.url('commit_id', commit_id, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if top is not None:
            query_parameters['top'] = self._serialize.query('top', top, 'int')
        if skip is not None:
            query_parameters['skip'] = self._serialize.query('skip', skip, 'int')
        response = self._send(http_method='GET',
                              location_id='5bf884f5-3e07-42e9-afb8-1b872267bf16',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('GitCommitChanges', response)

    def create_cherry_pick(self, cherry_pick_to_create, project, repository_id):
        """CreateCherryPick.
        [Preview API]
        :param :class:`<GitAsyncRefOperationParameters> <git.v4_0.models.GitAsyncRefOperationParameters>` cherry_pick_to_create:
        :param str project: Project ID or project name
        :param str repository_id:
        :rtype: :class:`<GitCherryPick> <git.v4_0.models.GitCherryPick>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        content = self._serialize.body(cherry_pick_to_create, 'GitAsyncRefOperationParameters')
        response = self._send(http_method='POST',
                              location_id='033bad68-9a14-43d1-90e0-59cb8856fef6',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('GitCherryPick', response)

    def get_cherry_pick(self, project, cherry_pick_id, repository_id):
        """GetCherryPick.
        [Preview API]
        :param str project: Project ID or project name
        :param int cherry_pick_id:
        :param str repository_id:
        :rtype: :class:`<GitCherryPick> <git.v4_0.models.GitCherryPick>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if cherry_pick_id is not None:
            route_values['cherryPickId'] = self._serialize.url('cherry_pick_id', cherry_pick_id, 'int')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        response = self._send(http_method='GET',
                              location_id='033bad68-9a14-43d1-90e0-59cb8856fef6',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('GitCherryPick', response)

    def get_cherry_pick_for_ref_name(self, project, repository_id, ref_name):
        """GetCherryPickForRefName.
        [Preview API]
        :param str project: Project ID or project name
        :param str repository_id:
        :param str ref_name:
        :rtype: :class:`<GitCherryPick> <git.v4_0.models.GitCherryPick>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if ref_name is not None:
            query_parameters['refName'] = self._serialize.query('ref_name', ref_name, 'str')
        response = self._send(http_method='GET',
                              location_id='033bad68-9a14-43d1-90e0-59cb8856fef6',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('GitCherryPick', response)

    def get_commit_diffs(self, repository_id, project=None, diff_common_commit=None, top=None, skip=None, base_version_descriptor=None, target_version_descriptor=None):
        """GetCommitDiffs.
        Get differences in committed items between two commits.
        :param str repository_id: Friendly name or guid of repository
        :param str project: Project ID or project name
        :param bool diff_common_commit:
        :param int top: Maximum number of changes to return
        :param int skip: Number of changes to skip
        :param :class:`<GitBaseVersionDescriptor> <git.v4_0.models.GitBaseVersionDescriptor>` base_version_descriptor:
        :param :class:`<GitTargetVersionDescriptor> <git.v4_0.models.GitTargetVersionDescriptor>` target_version_descriptor:
        :rtype: :class:`<GitCommitDiffs> <git.v4_0.models.GitCommitDiffs>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if diff_common_commit is not None:
            query_parameters['diffCommonCommit'] = self._serialize.query('diff_common_commit', diff_common_commit, 'bool')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if base_version_descriptor is not None:
            if base_version_descriptor.base_version_type is not None:
                query_parameters['baseVersionType'] = base_version_descriptor.base_version_type
            if base_version_descriptor.base_version is not None:
                query_parameters['baseVersion'] = base_version_descriptor.base_version
            if base_version_descriptor.base_version_options is not None:
                query_parameters['baseVersionOptions'] = base_version_descriptor.base_version_options
        if target_version_descriptor is not None:
            if target_version_descriptor.target_version_type is not None:
                query_parameters['targetVersionType'] = target_version_descriptor.target_version_type
            if target_version_descriptor.target_version is not None:
                query_parameters['targetVersion'] = target_version_descriptor.target_version
            if target_version_descriptor.target_version_options is not None:
                query_parameters['targetVersionOptions'] = target_version_descriptor.target_version_options
        response = self._send(http_method='GET',
                              location_id='615588d5-c0c7-4b88-88f8-e625306446e8',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('GitCommitDiffs', response)

    def get_commit(self, commit_id, repository_id, project=None, change_count=None):
        """GetCommit.
        Retrieve a particular commit.
        :param str commit_id: The id of the commit.
        :param str repository_id: The id or friendly name of the repository. To use the friendly name, projectId must also be specified.
        :param str project: Project ID or project name
        :param int change_count: The number of changes to include in the result.
        :rtype: :class:`<GitCommit> <git.v4_0.models.GitCommit>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if commit_id is not None:
            route_values['commitId'] = self._serialize.url('commit_id', commit_id, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if change_count is not None:
            query_parameters['changeCount'] = self._serialize.query('change_count', change_count, 'int')
        response = self._send(http_method='GET',
                              location_id='c2570c3b-5b3f-41b8-98bf-5407bfde8d58',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('GitCommit', response)

    def get_commits(self, repository_id, search_criteria, project=None, skip=None, top=None):
        """GetCommits.
        Retrieve git commits for a project
        :param str repository_id: The id or friendly name of the repository. To use the friendly name, projectId must also be specified.
        :param :class:`<GitQueryCommitsCriteria> <git.v4_0.models.GitQueryCommitsCriteria>` search_criteria:
        :param str project: Project ID or project name
        :param int skip:
        :param int top:
        :rtype: [GitCommitRef]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if search_criteria is not None:
            if search_criteria.ids is not None:
                query_parameters['searchCriteria.ids'] = search_criteria.ids
            if search_criteria.from_date is not None:
                query_parameters['searchCriteria.fromDate'] = search_criteria.from_date
            if search_criteria.to_date is not None:
                query_parameters['searchCriteria.toDate'] = search_criteria.to_date
            if search_criteria.item_version is not None:
                if search_criteria.item_version.version_type is not None:
                    query_parameters['searchCriteria.itemVersion.versionType'] = search_criteria.item_version.version_type
                if search_criteria.item_version.version is not None:
                    query_parameters['searchCriteria.itemVersion.version'] = search_criteria.item_version.version
                if search_criteria.item_version.version_options is not None:
                    query_parameters['searchCriteria.itemVersion.versionOptions'] = search_criteria.item_version.version_options
            if search_criteria.compare_version is not None:
                if search_criteria.compare_version.version_type is not None:
                    query_parameters['searchCriteria.compareVersion.versionType'] = search_criteria.compare_version.version_type
                if search_criteria.compare_version.version is not None:
                    query_parameters['searchCriteria.compareVersion.version'] = search_criteria.compare_version.version
                if search_criteria.compare_version.version_options is not None:
                    query_parameters['searchCriteria.compareVersion.versionOptions'] = search_criteria.compare_version.version_options
            if search_criteria.from_commit_id is not None:
                query_parameters['searchCriteria.fromCommitId'] = search_criteria.from_commit_id
            if search_criteria.to_commit_id is not None:
                query_parameters['searchCriteria.toCommitId'] = search_criteria.to_commit_id
            if search_criteria.user is not None:
                query_parameters['searchCriteria.user'] = search_criteria.user
            if search_criteria.author is not None:
                query_parameters['searchCriteria.author'] = search_criteria.author
            if search_criteria.item_path is not None:
                query_parameters['searchCriteria.itemPath'] = search_criteria.item_path
            if search_criteria.exclude_deletes is not None:
                query_parameters['searchCriteria.excludeDeletes'] = search_criteria.exclude_deletes
            if search_criteria.skip is not None:
                query_parameters['searchCriteria.$skip'] = search_criteria.skip
            if search_criteria.top is not None:
                query_parameters['searchCriteria.$top'] = search_criteria.top
            if search_criteria.include_links is not None:
                query_parameters['searchCriteria.includeLinks'] = search_criteria.include_links
            if search_criteria.include_work_items is not None:
                query_parameters['searchCriteria.includeWorkItems'] = search_criteria.include_work_items
            if search_criteria.history_mode is not None:
                query_parameters['searchCriteria.historyMode'] = search_criteria.history_mode
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        response = self._send(http_method='GET',
                              location_id='c2570c3b-5b3f-41b8-98bf-5407bfde8d58',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[GitCommitRef]', self._unwrap_collection(response))

    def get_push_commits(self, repository_id, push_id, project=None, top=None, skip=None, include_links=None):
        """GetPushCommits.
        Retrieve a list of commits associated with a particular push.
        :param str repository_id: The id or friendly name of the repository. To use the friendly name, projectId must also be specified.
        :param int push_id: The id of the push.
        :param str project: Project ID or project name
        :param int top: The maximum number of commits to return ("get the top x commits").
        :param int skip: The number of commits to skip.
        :param bool include_links:
        :rtype: [GitCommitRef]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if push_id is not None:
            query_parameters['pushId'] = self._serialize.query('push_id', push_id, 'int')
        if top is not None:
            query_parameters['top'] = self._serialize.query('top', top, 'int')
        if skip is not None:
            query_parameters['skip'] = self._serialize.query('skip', skip, 'int')
        if include_links is not None:
            query_parameters['includeLinks'] = self._serialize.query('include_links', include_links, 'bool')
        response = self._send(http_method='GET',
                              location_id='c2570c3b-5b3f-41b8-98bf-5407bfde8d58',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[GitCommitRef]', self._unwrap_collection(response))

    def get_commits_batch(self, search_criteria, repository_id, project=None, skip=None, top=None, include_statuses=None):
        """GetCommitsBatch.
        Retrieve git commits for a project
        :param :class:`<GitQueryCommitsCriteria> <git.v4_0.models.GitQueryCommitsCriteria>` search_criteria: Search options
        :param str repository_id: The id or friendly name of the repository. To use the friendly name, projectId must also be specified.
        :param str project: Project ID or project name
        :param int skip:
        :param int top:
        :param bool include_statuses:
        :rtype: [GitCommitRef]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        if include_statuses is not None:
            query_parameters['includeStatuses'] = self._serialize.query('include_statuses', include_statuses, 'bool')
        content = self._serialize.body(search_criteria, 'GitQueryCommitsCriteria')
        response = self._send(http_method='POST',
                              location_id='6400dfb2-0bcb-462b-b992-5a57f8f1416c',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('[GitCommitRef]', self._unwrap_collection(response))

    def get_deleted_repositories(self, project):
        """GetDeletedRepositories.
        [Preview API] Retrieve deleted git repositories.
        :param str project: Project ID or project name
        :rtype: [GitDeletedRepository]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        response = self._send(http_method='GET',
                              location_id='2b6869c4-cb25-42b5-b7a3-0d3e6be0a11a',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[GitDeletedRepository]', self._unwrap_collection(response))

    def get_forks(self, repository_name_or_id, collection_id, project=None, include_links=None):
        """GetForks.
        [Preview API] Retrieve all forks of a repository in the collection.
        :param str repository_name_or_id: ID or name of the repository.
        :param str collection_id: Team project collection ID.
        :param str project: Project ID or project name
        :param bool include_links:
        :rtype: [GitRepositoryRef]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_name_or_id is not None:
            route_values['repositoryNameOrId'] = self._serialize.url('repository_name_or_id', repository_name_or_id, 'str')
        if collection_id is not None:
            route_values['collectionId'] = self._serialize.url('collection_id', collection_id, 'str')
        query_parameters = {}
        if include_links is not None:
            query_parameters['includeLinks'] = self._serialize.query('include_links', include_links, 'bool')
        response = self._send(http_method='GET',
                              location_id='158c0340-bf6f-489c-9625-d572a1480d57',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[GitRepositoryRef]', self._unwrap_collection(response))

    def create_fork_sync_request(self, sync_params, repository_name_or_id, project=None, include_links=None):
        """CreateForkSyncRequest.
        [Preview API] Request that another repository's refs be fetched into this one.
        :param :class:`<GitForkSyncRequestParameters> <git.v4_0.models.GitForkSyncRequestParameters>` sync_params: Source repository and ref mapping.
        :param str repository_name_or_id: ID or name of the repository.
        :param str project: Project ID or project name
        :param bool include_links: True to include links
        :rtype: :class:`<GitForkSyncRequest> <git.v4_0.models.GitForkSyncRequest>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_name_or_id is not None:
            route_values['repositoryNameOrId'] = self._serialize.url('repository_name_or_id', repository_name_or_id, 'str')
        query_parameters = {}
        if include_links is not None:
            query_parameters['includeLinks'] = self._serialize.query('include_links', include_links, 'bool')
        content = self._serialize.body(sync_params, 'GitForkSyncRequestParameters')
        response = self._send(http_method='POST',
                              location_id='1703f858-b9d1-46af-ab62-483e9e1055b5',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('GitForkSyncRequest', response)

    def get_fork_sync_request(self, repository_name_or_id, fork_sync_operation_id, project=None, include_links=None):
        """GetForkSyncRequest.
        [Preview API] Get a specific fork sync operation's details.
        :param str repository_name_or_id: ID or name of the repository.
        :param int fork_sync_operation_id: OperationId of the sync request.
        :param str project: Project ID or project name
        :param bool include_links: True to include links.
        :rtype: :class:`<GitForkSyncRequest> <git.v4_0.models.GitForkSyncRequest>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_name_or_id is not None:
            route_values['repositoryNameOrId'] = self._serialize.url('repository_name_or_id', repository_name_or_id, 'str')
        if fork_sync_operation_id is not None:
            route_values['forkSyncOperationId'] = self._serialize.url('fork_sync_operation_id', fork_sync_operation_id, 'int')
        query_parameters = {}
        if include_links is not None:
            query_parameters['includeLinks'] = self._serialize.query('include_links', include_links, 'bool')
        response = self._send(http_method='GET',
                              location_id='1703f858-b9d1-46af-ab62-483e9e1055b5',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('GitForkSyncRequest', response)

    def get_fork_sync_requests(self, repository_name_or_id, project=None, include_abandoned=None, include_links=None):
        """GetForkSyncRequests.
        [Preview API] Retrieve all requested fork sync operations on this repository.
        :param str repository_name_or_id: ID or name of the repository.
        :param str project: Project ID or project name
        :param bool include_abandoned: True to include abandoned requests.
        :param bool include_links: True to include links.
        :rtype: [GitForkSyncRequest]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_name_or_id is not None:
            route_values['repositoryNameOrId'] = self._serialize.url('repository_name_or_id', repository_name_or_id, 'str')
        query_parameters = {}
        if include_abandoned is not None:
            query_parameters['includeAbandoned'] = self._serialize.query('include_abandoned', include_abandoned, 'bool')
        if include_links is not None:
            query_parameters['includeLinks'] = self._serialize.query('include_links', include_links, 'bool')
        response = self._send(http_method='GET',
                              location_id='1703f858-b9d1-46af-ab62-483e9e1055b5',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[GitForkSyncRequest]', self._unwrap_collection(response))

    def create_import_request(self, import_request, project, repository_id):
        """CreateImportRequest.
        [Preview API] Create an import request
        :param :class:`<GitImportRequest> <git.v4_0.models.GitImportRequest>` import_request:
        :param str project: Project ID or project name
        :param str repository_id:
        :rtype: :class:`<GitImportRequest> <git.v4_0.models.GitImportRequest>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        content = self._serialize.body(import_request, 'GitImportRequest')
        response = self._send(http_method='POST',
                              location_id='01828ddc-3600-4a41-8633-99b3a73a0eb3',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('GitImportRequest', response)

    def get_import_request(self, project, repository_id, import_request_id):
        """GetImportRequest.
        [Preview API] Retrieve a particular import request
        :param str project: Project ID or project name
        :param str repository_id:
        :param int import_request_id:
        :rtype: :class:`<GitImportRequest> <git.v4_0.models.GitImportRequest>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if import_request_id is not None:
            route_values['importRequestId'] = self._serialize.url('import_request_id', import_request_id, 'int')
        response = self._send(http_method='GET',
                              location_id='01828ddc-3600-4a41-8633-99b3a73a0eb3',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('GitImportRequest', response)

    def query_import_requests(self, project, repository_id, include_abandoned=None):
        """QueryImportRequests.
        [Preview API] Retrieve import requests for a repository
        :param str project: Project ID or project name
        :param str repository_id:
        :param bool include_abandoned:
        :rtype: [GitImportRequest]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if include_abandoned is not None:
            query_parameters['includeAbandoned'] = self._serialize.query('include_abandoned', include_abandoned, 'bool')
        response = self._send(http_method='GET',
                              location_id='01828ddc-3600-4a41-8633-99b3a73a0eb3',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[GitImportRequest]', self._unwrap_collection(response))

    def update_import_request(self, import_request_to_update, project, repository_id, import_request_id):
        """UpdateImportRequest.
        [Preview API] Update an import request
        :param :class:`<GitImportRequest> <git.v4_0.models.GitImportRequest>` import_request_to_update:
        :param str project: Project ID or project name
        :param str repository_id:
        :param int import_request_id:
        :rtype: :class:`<GitImportRequest> <git.v4_0.models.GitImportRequest>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if import_request_id is not None:
            route_values['importRequestId'] = self._serialize.url('import_request_id', import_request_id, 'int')
        content = self._serialize.body(import_request_to_update, 'GitImportRequest')
        response = self._send(http_method='PATCH',
                              location_id='01828ddc-3600-4a41-8633-99b3a73a0eb3',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('GitImportRequest', response)

    def get_item(self, repository_id, path, project=None, scope_path=None, recursion_level=None, include_content_metadata=None, latest_processed_change=None, download=None, version_descriptor=None):
        """GetItem.
        Get Item Metadata and/or Content for a single item. The download parameter is to indicate whether the content should be available as a download or just sent as a stream in the response. Doesn't apply to zipped content which is always returned as a download.
        :param str repository_id:
        :param str path:
        :param str project: Project ID or project name
        :param str scope_path:
        :param str recursion_level:
        :param bool include_content_metadata:
        :param bool latest_processed_change:
        :param bool download:
        :param :class:`<GitVersionDescriptor> <git.v4_0.models.GitVersionDescriptor>` version_descriptor:
        :rtype: :class:`<GitItem> <git.v4_0.models.GitItem>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if path is not None:
            query_parameters['path'] = self._serialize.query('path', path, 'str')
        if scope_path is not None:
            query_parameters['scopePath'] = self._serialize.query('scope_path', scope_path, 'str')
        if recursion_level is not None:
            query_parameters['recursionLevel'] = self._serialize.query('recursion_level', recursion_level, 'str')
        if include_content_metadata is not None:
            query_parameters['includeContentMetadata'] = self._serialize.query('include_content_metadata', include_content_metadata, 'bool')
        if latest_processed_change is not None:
            query_parameters['latestProcessedChange'] = self._serialize.query('latest_processed_change', latest_processed_change, 'bool')
        if download is not None:
            query_parameters['download'] = self._serialize.query('download', download, 'bool')
        if version_descriptor is not None:
            if version_descriptor.version_type is not None:
                query_parameters['versionDescriptor.versionType'] = version_descriptor.version_type
            if version_descriptor.version is not None:
                query_parameters['versionDescriptor.version'] = version_descriptor.version
            if version_descriptor.version_options is not None:
                query_parameters['versionDescriptor.versionOptions'] = version_descriptor.version_options
        response = self._send(http_method='GET',
                              location_id='fb93c0db-47ed-4a31-8c20-47552878fb44',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('GitItem', response)

    def get_item_content(self, repository_id, path, project=None, scope_path=None, recursion_level=None, include_content_metadata=None, latest_processed_change=None, download=None, version_descriptor=None, **kwargs):
        """GetItemContent.
        Get Item Metadata and/or Content for a single item. The download parameter is to indicate whether the content should be available as a download or just sent as a stream in the response. Doesn't apply to zipped content which is always returned as a download.
        :param str repository_id:
        :param str path:
        :param str project: Project ID or project name
        :param str scope_path:
        :param str recursion_level:
        :param bool include_content_metadata:
        :param bool latest_processed_change:
        :param bool download:
        :param :class:`<GitVersionDescriptor> <git.v4_0.models.GitVersionDescriptor>` version_descriptor:
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if path is not None:
            query_parameters['path'] = self._serialize.query('path', path, 'str')
        if scope_path is not None:
            query_parameters['scopePath'] = self._serialize.query('scope_path', scope_path, 'str')
        if recursion_level is not None:
            query_parameters['recursionLevel'] = self._serialize.query('recursion_level', recursion_level, 'str')
        if include_content_metadata is not None:
            query_parameters['includeContentMetadata'] = self._serialize.query('include_content_metadata', include_content_metadata, 'bool')
        if latest_processed_change is not None:
            query_parameters['latestProcessedChange'] = self._serialize.query('latest_processed_change', latest_processed_change, 'bool')
        if download is not None:
            query_parameters['download'] = self._serialize.query('download', download, 'bool')
        if version_descriptor is not None:
            if version_descriptor.version_type is not None:
                query_parameters['versionDescriptor.versionType'] = version_descriptor.version_type
            if version_descriptor.version is not None:
                query_parameters['versionDescriptor.version'] = version_descriptor.version
            if version_descriptor.version_options is not None:
                query_parameters['versionDescriptor.versionOptions'] = version_descriptor.version_options
        response = self._send(http_method='GET',
                              location_id='fb93c0db-47ed-4a31-8c20-47552878fb44',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              accept_media_type='application/octet-stream')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_items(self, repository_id, project=None, scope_path=None, recursion_level=None, include_content_metadata=None, latest_processed_change=None, download=None, include_links=None, version_descriptor=None):
        """GetItems.
        Get Item Metadata and/or Content for a collection of items. The download parameter is to indicate whether the content should be available as a download or just sent as a stream in the response. Doesn't apply to zipped content which is always returned as a download.
        :param str repository_id:
        :param str project: Project ID or project name
        :param str scope_path:
        :param str recursion_level:
        :param bool include_content_metadata:
        :param bool latest_processed_change:
        :param bool download:
        :param bool include_links:
        :param :class:`<GitVersionDescriptor> <git.v4_0.models.GitVersionDescriptor>` version_descriptor:
        :rtype: [GitItem]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if scope_path is not None:
            query_parameters['scopePath'] = self._serialize.query('scope_path', scope_path, 'str')
        if recursion_level is not None:
            query_parameters['recursionLevel'] = self._serialize.query('recursion_level', recursion_level, 'str')
        if include_content_metadata is not None:
            query_parameters['includeContentMetadata'] = self._serialize.query('include_content_metadata', include_content_metadata, 'bool')
        if latest_processed_change is not None:
            query_parameters['latestProcessedChange'] = self._serialize.query('latest_processed_change', latest_processed_change, 'bool')
        if download is not None:
            query_parameters['download'] = self._serialize.query('download', download, 'bool')
        if include_links is not None:
            query_parameters['includeLinks'] = self._serialize.query('include_links', include_links, 'bool')
        if version_descriptor is not None:
            if version_descriptor.version_type is not None:
                query_parameters['versionDescriptor.versionType'] = version_descriptor.version_type
            if version_descriptor.version is not None:
                query_parameters['versionDescriptor.version'] = version_descriptor.version
            if version_descriptor.version_options is not None:
                query_parameters['versionDescriptor.versionOptions'] = version_descriptor.version_options
        response = self._send(http_method='GET',
                              location_id='fb93c0db-47ed-4a31-8c20-47552878fb44',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[GitItem]', self._unwrap_collection(response))

    def get_item_text(self, repository_id, path, project=None, scope_path=None, recursion_level=None, include_content_metadata=None, latest_processed_change=None, download=None, version_descriptor=None, **kwargs):
        """GetItemText.
        Get Item Metadata and/or Content for a single item. The download parameter is to indicate whether the content should be available as a download or just sent as a stream in the response. Doesn't apply to zipped content which is always returned as a download.
        :param str repository_id:
        :param str path:
        :param str project: Project ID or project name
        :param str scope_path:
        :param str recursion_level:
        :param bool include_content_metadata:
        :param bool latest_processed_change:
        :param bool download:
        :param :class:`<GitVersionDescriptor> <git.v4_0.models.GitVersionDescriptor>` version_descriptor:
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if path is not None:
            query_parameters['path'] = self._serialize.query('path', path, 'str')
        if scope_path is not None:
            query_parameters['scopePath'] = self._serialize.query('scope_path', scope_path, 'str')
        if recursion_level is not None:
            query_parameters['recursionLevel'] = self._serialize.query('recursion_level', recursion_level, 'str')
        if include_content_metadata is not None:
            query_parameters['includeContentMetadata'] = self._serialize.query('include_content_metadata', include_content_metadata, 'bool')
        if latest_processed_change is not None:
            query_parameters['latestProcessedChange'] = self._serialize.query('latest_processed_change', latest_processed_change, 'bool')
        if download is not None:
            query_parameters['download'] = self._serialize.query('download', download, 'bool')
        if version_descriptor is not None:
            if version_descriptor.version_type is not None:
                query_parameters['versionDescriptor.versionType'] = version_descriptor.version_type
            if version_descriptor.version is not None:
                query_parameters['versionDescriptor.version'] = version_descriptor.version
            if version_descriptor.version_options is not None:
                query_parameters['versionDescriptor.versionOptions'] = version_descriptor.version_options
        response = self._send(http_method='GET',
                              location_id='fb93c0db-47ed-4a31-8c20-47552878fb44',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              accept_media_type='text/plain')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_item_zip(self, repository_id, path, project=None, scope_path=None, recursion_level=None, include_content_metadata=None, latest_processed_change=None, download=None, version_descriptor=None, **kwargs):
        """GetItemZip.
        Get Item Metadata and/or Content for a single item. The download parameter is to indicate whether the content should be available as a download or just sent as a stream in the response. Doesn't apply to zipped content which is always returned as a download.
        :param str repository_id:
        :param str path:
        :param str project: Project ID or project name
        :param str scope_path:
        :param str recursion_level:
        :param bool include_content_metadata:
        :param bool latest_processed_change:
        :param bool download:
        :param :class:`<GitVersionDescriptor> <git.v4_0.models.GitVersionDescriptor>` version_descriptor:
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if path is not None:
            query_parameters['path'] = self._serialize.query('path', path, 'str')
        if scope_path is not None:
            query_parameters['scopePath'] = self._serialize.query('scope_path', scope_path, 'str')
        if recursion_level is not None:
            query_parameters['recursionLevel'] = self._serialize.query('recursion_level', recursion_level, 'str')
        if include_content_metadata is not None:
            query_parameters['includeContentMetadata'] = self._serialize.query('include_content_metadata', include_content_metadata, 'bool')
        if latest_processed_change is not None:
            query_parameters['latestProcessedChange'] = self._serialize.query('latest_processed_change', latest_processed_change, 'bool')
        if download is not None:
            query_parameters['download'] = self._serialize.query('download', download, 'bool')
        if version_descriptor is not None:
            if version_descriptor.version_type is not None:
                query_parameters['versionDescriptor.versionType'] = version_descriptor.version_type
            if version_descriptor.version is not None:
                query_parameters['versionDescriptor.version'] = version_descriptor.version
            if version_descriptor.version_options is not None:
                query_parameters['versionDescriptor.versionOptions'] = version_descriptor.version_options
        response = self._send(http_method='GET',
                              location_id='fb93c0db-47ed-4a31-8c20-47552878fb44',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              accept_media_type='application/zip')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_items_batch(self, request_data, repository_id, project=None):
        """GetItemsBatch.
        Post for retrieving a creating a batch out of a set of items in a repo / project given a list of paths or a long path
        :param :class:`<GitItemRequestData> <git.v4_0.models.GitItemRequestData>` request_data:
        :param str repository_id:
        :param str project: Project ID or project name
        :rtype: [[GitItem]]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        content = self._serialize.body(request_data, 'GitItemRequestData')
        response = self._send(http_method='POST',
                              location_id='630fd2e4-fb88-4f85-ad21-13f3fd1fbca9',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[[GitItem]]', self._unwrap_collection(response))

    def create_attachment(self, upload_stream, file_name, repository_id, pull_request_id, project=None, **kwargs):
        """CreateAttachment.
        [Preview API] Create a new attachment
        :param object upload_stream: Stream to upload
        :param str file_name:
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        :rtype: :class:`<Attachment> <git.v4_0.models.Attachment>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if file_name is not None:
            route_values['fileName'] = self._serialize.url('file_name', file_name, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        content = self._client.stream_upload(upload_stream, callback=callback)
        response = self._send(http_method='POST',
                              location_id='965d9361-878b-413b-a494-45d5b5fd8ab7',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content,
                              media_type='application/octet-stream')
        return self._deserialize('Attachment', response)

    def delete_attachment(self, file_name, repository_id, pull_request_id, project=None):
        """DeleteAttachment.
        [Preview API]
        :param str file_name:
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if file_name is not None:
            route_values['fileName'] = self._serialize.url('file_name', file_name, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        self._send(http_method='DELETE',
                   location_id='965d9361-878b-413b-a494-45d5b5fd8ab7',
                   version='4.0-preview.1',
                   route_values=route_values)

    def get_attachment_content(self, file_name, repository_id, pull_request_id, project=None, **kwargs):
        """GetAttachmentContent.
        [Preview API]
        :param str file_name:
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if file_name is not None:
            route_values['fileName'] = self._serialize.url('file_name', file_name, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        response = self._send(http_method='GET',
                              location_id='965d9361-878b-413b-a494-45d5b5fd8ab7',
                              version='4.0-preview.1',
                              route_values=route_values,
                              accept_media_type='application/octet-stream')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def get_attachments(self, repository_id, pull_request_id, project=None):
        """GetAttachments.
        [Preview API]
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        :rtype: [Attachment]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        response = self._send(http_method='GET',
                              location_id='965d9361-878b-413b-a494-45d5b5fd8ab7',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[Attachment]', self._unwrap_collection(response))

    def get_attachment_zip(self, file_name, repository_id, pull_request_id, project=None, **kwargs):
        """GetAttachmentZip.
        [Preview API]
        :param str file_name:
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if file_name is not None:
            route_values['fileName'] = self._serialize.url('file_name', file_name, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        response = self._send(http_method='GET',
                              location_id='965d9361-878b-413b-a494-45d5b5fd8ab7',
                              version='4.0-preview.1',
                              route_values=route_values,
                              accept_media_type='application/zip')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

    def create_like(self, repository_id, pull_request_id, thread_id, comment_id, project=None):
        """CreateLike.
        [Preview API] Add a like on a comment.
        :param str repository_id:
        :param int pull_request_id:
        :param int thread_id:
        :param int comment_id:
        :param str project: Project ID or project name
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if thread_id is not None:
            route_values['threadId'] = self._serialize.url('thread_id', thread_id, 'int')
        if comment_id is not None:
            route_values['commentId'] = self._serialize.url('comment_id', comment_id, 'int')
        self._send(http_method='POST',
                   location_id='5f2e2851-1389-425b-a00b-fb2adb3ef31b',
                   version='4.0-preview.1',
                   route_values=route_values)

    def delete_like(self, repository_id, pull_request_id, thread_id, comment_id, project=None):
        """DeleteLike.
        [Preview API] Delete a like on a comment.
        :param str repository_id:
        :param int pull_request_id:
        :param int thread_id:
        :param int comment_id:
        :param str project: Project ID or project name
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if thread_id is not None:
            route_values['threadId'] = self._serialize.url('thread_id', thread_id, 'int')
        if comment_id is not None:
            route_values['commentId'] = self._serialize.url('comment_id', comment_id, 'int')
        self._send(http_method='DELETE',
                   location_id='5f2e2851-1389-425b-a00b-fb2adb3ef31b',
                   version='4.0-preview.1',
                   route_values=route_values)

    def get_likes(self, repository_id, pull_request_id, thread_id, comment_id, project=None):
        """GetLikes.
        [Preview API] Get likes for a comment.
        :param str repository_id:
        :param int pull_request_id:
        :param int thread_id:
        :param int comment_id:
        :param str project: Project ID or project name
        :rtype: [IdentityRef]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if thread_id is not None:
            route_values['threadId'] = self._serialize.url('thread_id', thread_id, 'int')
        if comment_id is not None:
            route_values['commentId'] = self._serialize.url('comment_id', comment_id, 'int')
        response = self._send(http_method='GET',
                              location_id='5f2e2851-1389-425b-a00b-fb2adb3ef31b',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[IdentityRef]', self._unwrap_collection(response))

    def get_pull_request_iteration_commits(self, repository_id, pull_request_id, iteration_id, project=None):
        """GetPullRequestIterationCommits.
        Get the commits for an iteration.
        :param str repository_id:
        :param int pull_request_id:
        :param int iteration_id: Iteration to retrieve commits for
        :param str project: Project ID or project name
        :rtype: [GitCommitRef]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if iteration_id is not None:
            route_values['iterationId'] = self._serialize.url('iteration_id', iteration_id, 'int')
        response = self._send(http_method='GET',
                              location_id='e7ea0883-095f-4926-b5fb-f24691c26fb9',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('[GitCommitRef]', self._unwrap_collection(response))

    def get_pull_request_commits(self, repository_id, pull_request_id, project=None):
        """GetPullRequestCommits.
        Retrieve pull request's commits
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        :rtype: [GitCommitRef]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        response = self._send(http_method='GET',
                              location_id='52823034-34a8-4576-922c-8d8b77e9e4c4',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('[GitCommitRef]', self._unwrap_collection(response))

    def get_pull_request_iteration_changes(self, repository_id, pull_request_id, iteration_id, project=None, top=None, skip=None, compare_to=None):
        """GetPullRequestIterationChanges.
        :param str repository_id:
        :param int pull_request_id:
        :param int iteration_id:
        :param str project: Project ID or project name
        :param int top:
        :param int skip:
        :param int compare_to:
        :rtype: :class:`<GitPullRequestIterationChanges> <git.v4_0.models.GitPullRequestIterationChanges>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if iteration_id is not None:
            route_values['iterationId'] = self._serialize.url('iteration_id', iteration_id, 'int')
        query_parameters = {}
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if compare_to is not None:
            query_parameters['$compareTo'] = self._serialize.query('compare_to', compare_to, 'int')
        response = self._send(http_method='GET',
                              location_id='4216bdcf-b6b1-4d59-8b82-c34cc183fc8b',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('GitPullRequestIterationChanges', response)

    def get_pull_request_iteration(self, repository_id, pull_request_id, iteration_id, project=None):
        """GetPullRequestIteration.
        :param str repository_id:
        :param int pull_request_id:
        :param int iteration_id:
        :param str project: Project ID or project name
        :rtype: :class:`<GitPullRequestIteration> <git.v4_0.models.GitPullRequestIteration>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if iteration_id is not None:
            route_values['iterationId'] = self._serialize.url('iteration_id', iteration_id, 'int')
        response = self._send(http_method='GET',
                              location_id='d43911ee-6958-46b0-a42b-8445b8a0d004',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('GitPullRequestIteration', response)

    def get_pull_request_iterations(self, repository_id, pull_request_id, project=None, include_commits=None):
        """GetPullRequestIterations.
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        :param bool include_commits:
        :rtype: [GitPullRequestIteration]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        query_parameters = {}
        if include_commits is not None:
            query_parameters['includeCommits'] = self._serialize.query('include_commits', include_commits, 'bool')
        response = self._send(http_method='GET',
                              location_id='d43911ee-6958-46b0-a42b-8445b8a0d004',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[GitPullRequestIteration]', self._unwrap_collection(response))

    def create_pull_request_iteration_status(self, status, repository_id, pull_request_id, iteration_id, project=None):
        """CreatePullRequestIterationStatus.
        [Preview API] Create a pull request status on the iteration. This method will have the same result as CreatePullRequestStatus with specified iterationId in the request body.
        :param :class:`<GitPullRequestStatus> <git.v4_0.models.GitPullRequestStatus>` status: Pull request status to create.
        :param str repository_id: ID of the repository the pull request belongs to.
        :param int pull_request_id: ID of the pull request.
        :param int iteration_id: ID of the pull request iteration.
        :param str project: Project ID or project name
        :rtype: :class:`<GitPullRequestStatus> <git.v4_0.models.GitPullRequestStatus>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if iteration_id is not None:
            route_values['iterationId'] = self._serialize.url('iteration_id', iteration_id, 'int')
        content = self._serialize.body(status, 'GitPullRequestStatus')
        response = self._send(http_method='POST',
                              location_id='75cf11c5-979f-4038-a76e-058a06adf2bf',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('GitPullRequestStatus', response)

    def get_pull_request_iteration_status(self, repository_id, pull_request_id, iteration_id, status_id, project=None):
        """GetPullRequestIterationStatus.
        [Preview API] Get the specific pull request iteration status by ID. The status ID is unique within the pull request across all iterations.
        :param str repository_id: ID of the repository the pull request belongs to.
        :param int pull_request_id: ID of the pull request.
        :param int iteration_id: ID of the pull request iteration.
        :param int status_id: ID of the pull request status.
        :param str project: Project ID or project name
        :rtype: :class:`<GitPullRequestStatus> <git.v4_0.models.GitPullRequestStatus>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if iteration_id is not None:
            route_values['iterationId'] = self._serialize.url('iteration_id', iteration_id, 'int')
        if status_id is not None:
            route_values['statusId'] = self._serialize.url('status_id', status_id, 'int')
        response = self._send(http_method='GET',
                              location_id='75cf11c5-979f-4038-a76e-058a06adf2bf',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('GitPullRequestStatus', response)

    def get_pull_request_iteration_statuses(self, repository_id, pull_request_id, iteration_id, project=None):
        """GetPullRequestIterationStatuses.
        [Preview API] Get all the statuses associated with a pull request iteration.
        :param str repository_id: ID of the repository the pull request belongs to.
        :param int pull_request_id: ID of the pull request.
        :param int iteration_id: ID of the pull request iteration.
        :param str project: Project ID or project name
        :rtype: [GitPullRequestStatus]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if iteration_id is not None:
            route_values['iterationId'] = self._serialize.url('iteration_id', iteration_id, 'int')
        response = self._send(http_method='GET',
                              location_id='75cf11c5-979f-4038-a76e-058a06adf2bf',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[GitPullRequestStatus]', self._unwrap_collection(response))

    def create_pull_request_label(self, label, repository_id, pull_request_id, project=None, project_id=None):
        """CreatePullRequestLabel.
        [Preview API]
        :param :class:`<WebApiCreateTagRequestData> <git.v4_0.models.WebApiCreateTagRequestData>` label:
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        :param str project_id:
        :rtype: :class:`<WebApiTagDefinition> <git.v4_0.models.WebApiTagDefinition>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        query_parameters = {}
        if project_id is not None:
            query_parameters['projectId'] = self._serialize.query('project_id', project_id, 'str')
        content = self._serialize.body(label, 'WebApiCreateTagRequestData')
        response = self._send(http_method='POST',
                              location_id='f22387e3-984e-4c52-9c6d-fbb8f14c812d',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('WebApiTagDefinition', response)

    def delete_pull_request_labels(self, repository_id, pull_request_id, label_id_or_name, project=None, project_id=None):
        """DeletePullRequestLabels.
        [Preview API]
        :param str repository_id:
        :param int pull_request_id:
        :param str label_id_or_name:
        :param str project: Project ID or project name
        :param str project_id:
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if label_id_or_name is not None:
            route_values['labelIdOrName'] = self._serialize.url('label_id_or_name', label_id_or_name, 'str')
        query_parameters = {}
        if project_id is not None:
            query_parameters['projectId'] = self._serialize.query('project_id', project_id, 'str')
        self._send(http_method='DELETE',
                   location_id='f22387e3-984e-4c52-9c6d-fbb8f14c812d',
                   version='4.0-preview.1',
                   route_values=route_values,
                   query_parameters=query_parameters)

    def get_pull_request_label(self, repository_id, pull_request_id, label_id_or_name, project=None, project_id=None):
        """GetPullRequestLabel.
        [Preview API]
        :param str repository_id:
        :param int pull_request_id:
        :param str label_id_or_name:
        :param str project: Project ID or project name
        :param str project_id:
        :rtype: :class:`<WebApiTagDefinition> <git.v4_0.models.WebApiTagDefinition>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if label_id_or_name is not None:
            route_values['labelIdOrName'] = self._serialize.url('label_id_or_name', label_id_or_name, 'str')
        query_parameters = {}
        if project_id is not None:
            query_parameters['projectId'] = self._serialize.query('project_id', project_id, 'str')
        response = self._send(http_method='GET',
                              location_id='f22387e3-984e-4c52-9c6d-fbb8f14c812d',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('WebApiTagDefinition', response)

    def get_pull_request_labels(self, repository_id, pull_request_id, project=None, project_id=None):
        """GetPullRequestLabels.
        [Preview API] Retrieve a pull request's Labels
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        :param str project_id:
        :rtype: [WebApiTagDefinition]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        query_parameters = {}
        if project_id is not None:
            query_parameters['projectId'] = self._serialize.query('project_id', project_id, 'str')
        response = self._send(http_method='GET',
                              location_id='f22387e3-984e-4c52-9c6d-fbb8f14c812d',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[WebApiTagDefinition]', self._unwrap_collection(response))

    def get_pull_request_query(self, queries, repository_id, project=None):
        """GetPullRequestQuery.
        Query for pull requests
        :param :class:`<GitPullRequestQuery> <git.v4_0.models.GitPullRequestQuery>` queries:
        :param str repository_id:
        :param str project: Project ID or project name
        :rtype: :class:`<GitPullRequestQuery> <git.v4_0.models.GitPullRequestQuery>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        content = self._serialize.body(queries, 'GitPullRequestQuery')
        response = self._send(http_method='POST',
                              location_id='b3a6eebe-9cf0-49ea-b6cb-1a4c5f5007b0',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('GitPullRequestQuery', response)

    def create_pull_request_reviewer(self, reviewer, repository_id, pull_request_id, reviewer_id, project=None):
        """CreatePullRequestReviewer.
        Adds a reviewer to a git pull request
        :param :class:`<IdentityRefWithVote> <git.v4_0.models.IdentityRefWithVote>` reviewer:
        :param str repository_id:
        :param int pull_request_id:
        :param str reviewer_id:
        :param str project: Project ID or project name
        :rtype: :class:`<IdentityRefWithVote> <git.v4_0.models.IdentityRefWithVote>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if reviewer_id is not None:
            route_values['reviewerId'] = self._serialize.url('reviewer_id', reviewer_id, 'str')
        content = self._serialize.body(reviewer, 'IdentityRefWithVote')
        response = self._send(http_method='PUT',
                              location_id='4b6702c7-aa35-4b89-9c96-b9abf6d3e540',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('IdentityRefWithVote', response)

    def create_pull_request_reviewers(self, reviewers, repository_id, pull_request_id, project=None):
        """CreatePullRequestReviewers.
        Adds reviewers to a git pull request
        :param [IdentityRef] reviewers:
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        :rtype: [IdentityRefWithVote]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        content = self._serialize.body(reviewers, '[IdentityRef]')
        response = self._send(http_method='POST',
                              location_id='4b6702c7-aa35-4b89-9c96-b9abf6d3e540',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[IdentityRefWithVote]', self._unwrap_collection(response))

    def delete_pull_request_reviewer(self, repository_id, pull_request_id, reviewer_id, project=None):
        """DeletePullRequestReviewer.
        Removes a reviewer from a git pull request
        :param str repository_id:
        :param int pull_request_id:
        :param str reviewer_id:
        :param str project: Project ID or project name
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if reviewer_id is not None:
            route_values['reviewerId'] = self._serialize.url('reviewer_id', reviewer_id, 'str')
        self._send(http_method='DELETE',
                   location_id='4b6702c7-aa35-4b89-9c96-b9abf6d3e540',
                   version='4.0',
                   route_values=route_values)

    def get_pull_request_reviewer(self, repository_id, pull_request_id, reviewer_id, project=None):
        """GetPullRequestReviewer.
        Retrieve a reviewer from a pull request
        :param str repository_id:
        :param int pull_request_id:
        :param str reviewer_id:
        :param str project: Project ID or project name
        :rtype: :class:`<IdentityRefWithVote> <git.v4_0.models.IdentityRefWithVote>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if reviewer_id is not None:
            route_values['reviewerId'] = self._serialize.url('reviewer_id', reviewer_id, 'str')
        response = self._send(http_method='GET',
                              location_id='4b6702c7-aa35-4b89-9c96-b9abf6d3e540',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('IdentityRefWithVote', response)

    def get_pull_request_reviewers(self, repository_id, pull_request_id, project=None):
        """GetPullRequestReviewers.
        Retrieve a pull request reviewers
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        :rtype: [IdentityRefWithVote]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        response = self._send(http_method='GET',
                              location_id='4b6702c7-aa35-4b89-9c96-b9abf6d3e540',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('[IdentityRefWithVote]', self._unwrap_collection(response))

    def update_pull_request_reviewers(self, patch_votes, repository_id, pull_request_id, project=None):
        """UpdatePullRequestReviewers.
        Resets multiple reviewer votes in a batch
        :param [IdentityRefWithVote] patch_votes:
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        content = self._serialize.body(patch_votes, '[IdentityRefWithVote]')
        self._send(http_method='PATCH',
                   location_id='4b6702c7-aa35-4b89-9c96-b9abf6d3e540',
                   version='4.0',
                   route_values=route_values,
                   content=content)

    def get_pull_request_by_id(self, pull_request_id):
        """GetPullRequestById.
        Get a pull request using its ID
        :param int pull_request_id: the Id of the pull request
        :rtype: :class:`<GitPullRequest> <git.v4_0.models.GitPullRequest>`
        """
        route_values = {}
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        response = self._send(http_method='GET',
                              location_id='01a46dea-7d46-4d40-bc84-319e7c260d99',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('GitPullRequest', response)

    def get_pull_requests_by_project(self, project, search_criteria, max_comment_length=None, skip=None, top=None):
        """GetPullRequestsByProject.
        Query pull requests by project
        :param str project: Project ID or project name
        :param :class:`<GitPullRequestSearchCriteria> <git.v4_0.models.GitPullRequestSearchCriteria>` search_criteria:
        :param int max_comment_length:
        :param int skip:
        :param int top:
        :rtype: [GitPullRequest]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if search_criteria is not None:
            if search_criteria.repository_id is not None:
                query_parameters['searchCriteria.repositoryId'] = search_criteria.repository_id
            if search_criteria.creator_id is not None:
                query_parameters['searchCriteria.creatorId'] = search_criteria.creator_id
            if search_criteria.reviewer_id is not None:
                query_parameters['searchCriteria.reviewerId'] = search_criteria.reviewer_id
            if search_criteria.status is not None:
                query_parameters['searchCriteria.status'] = search_criteria.status
            if search_criteria.target_ref_name is not None:
                query_parameters['searchCriteria.targetRefName'] = search_criteria.target_ref_name
            if search_criteria.source_repository_id is not None:
                query_parameters['searchCriteria.sourceRepositoryId'] = search_criteria.source_repository_id
            if search_criteria.source_ref_name is not None:
                query_parameters['searchCriteria.sourceRefName'] = search_criteria.source_ref_name
            if search_criteria.include_links is not None:
                query_parameters['searchCriteria.includeLinks'] = search_criteria.include_links
        if max_comment_length is not None:
            query_parameters['maxCommentLength'] = self._serialize.query('max_comment_length', max_comment_length, 'int')
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        response = self._send(http_method='GET',
                              location_id='a5d28130-9cd2-40fa-9f08-902e7daa9efb',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[GitPullRequest]', self._unwrap_collection(response))

    def create_pull_request(self, git_pull_request_to_create, repository_id, project=None, supports_iterations=None):
        """CreatePullRequest.
        Create a git pull request
        :param :class:`<GitPullRequest> <git.v4_0.models.GitPullRequest>` git_pull_request_to_create:
        :param str repository_id:
        :param str project: Project ID or project name
        :param bool supports_iterations:
        :rtype: :class:`<GitPullRequest> <git.v4_0.models.GitPullRequest>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if supports_iterations is not None:
            query_parameters['supportsIterations'] = self._serialize.query('supports_iterations', supports_iterations, 'bool')
        content = self._serialize.body(git_pull_request_to_create, 'GitPullRequest')
        response = self._send(http_method='POST',
                              location_id='9946fd70-0d40-406e-b686-b4744cbbcc37',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('GitPullRequest', response)

    def get_pull_request(self, repository_id, pull_request_id, project=None, max_comment_length=None, skip=None, top=None, include_commits=None, include_work_item_refs=None):
        """GetPullRequest.
        Retrieve a pull request
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        :param int max_comment_length:
        :param int skip:
        :param int top:
        :param bool include_commits:
        :param bool include_work_item_refs:
        :rtype: :class:`<GitPullRequest> <git.v4_0.models.GitPullRequest>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        query_parameters = {}
        if max_comment_length is not None:
            query_parameters['maxCommentLength'] = self._serialize.query('max_comment_length', max_comment_length, 'int')
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        if include_commits is not None:
            query_parameters['includeCommits'] = self._serialize.query('include_commits', include_commits, 'bool')
        if include_work_item_refs is not None:
            query_parameters['includeWorkItemRefs'] = self._serialize.query('include_work_item_refs', include_work_item_refs, 'bool')
        response = self._send(http_method='GET',
                              location_id='9946fd70-0d40-406e-b686-b4744cbbcc37',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('GitPullRequest', response)

    def get_pull_requests(self, repository_id, search_criteria, project=None, max_comment_length=None, skip=None, top=None):
        """GetPullRequests.
        Query for pull requests
        :param str repository_id:
        :param :class:`<GitPullRequestSearchCriteria> <git.v4_0.models.GitPullRequestSearchCriteria>` search_criteria:
        :param str project: Project ID or project name
        :param int max_comment_length:
        :param int skip:
        :param int top:
        :rtype: [GitPullRequest]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if search_criteria is not None:
            if search_criteria.repository_id is not None:
                query_parameters['searchCriteria.repositoryId'] = search_criteria.repository_id
            if search_criteria.creator_id is not None:
                query_parameters['searchCriteria.creatorId'] = search_criteria.creator_id
            if search_criteria.reviewer_id is not None:
                query_parameters['searchCriteria.reviewerId'] = search_criteria.reviewer_id
            if search_criteria.status is not None:
                query_parameters['searchCriteria.status'] = search_criteria.status
            if search_criteria.target_ref_name is not None:
                query_parameters['searchCriteria.targetRefName'] = search_criteria.target_ref_name
            if search_criteria.source_repository_id is not None:
                query_parameters['searchCriteria.sourceRepositoryId'] = search_criteria.source_repository_id
            if search_criteria.source_ref_name is not None:
                query_parameters['searchCriteria.sourceRefName'] = search_criteria.source_ref_name
            if search_criteria.include_links is not None:
                query_parameters['searchCriteria.includeLinks'] = search_criteria.include_links
        if max_comment_length is not None:
            query_parameters['maxCommentLength'] = self._serialize.query('max_comment_length', max_comment_length, 'int')
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        response = self._send(http_method='GET',
                              location_id='9946fd70-0d40-406e-b686-b4744cbbcc37',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[GitPullRequest]', self._unwrap_collection(response))

    def update_pull_request(self, git_pull_request_to_update, repository_id, pull_request_id, project=None):
        """UpdatePullRequest.
        Updates a pull request
        :param :class:`<GitPullRequest> <git.v4_0.models.GitPullRequest>` git_pull_request_to_update:
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        :rtype: :class:`<GitPullRequest> <git.v4_0.models.GitPullRequest>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        content = self._serialize.body(git_pull_request_to_update, 'GitPullRequest')
        response = self._send(http_method='PATCH',
                              location_id='9946fd70-0d40-406e-b686-b4744cbbcc37',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('GitPullRequest', response)

    def share_pull_request(self, user_message, repository_id, pull_request_id, project=None):
        """SharePullRequest.
        [Preview API]
        :param :class:`<ShareNotificationContext> <git.v4_0.models.ShareNotificationContext>` user_message:
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        content = self._serialize.body(user_message, 'ShareNotificationContext')
        self._send(http_method='POST',
                   location_id='696f3a82-47c9-487f-9117-b9d00972ca84',
                   version='4.0-preview.1',
                   route_values=route_values,
                   content=content)

    def create_pull_request_status(self, status, repository_id, pull_request_id, project=None):
        """CreatePullRequestStatus.
        [Preview API] Create a pull request status.
        :param :class:`<GitPullRequestStatus> <git.v4_0.models.GitPullRequestStatus>` status: Pull request status to create.
        :param str repository_id: ID of the repository the pull request belongs to.
        :param int pull_request_id: ID of the pull request.
        :param str project: Project ID or project name
        :rtype: :class:`<GitPullRequestStatus> <git.v4_0.models.GitPullRequestStatus>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        content = self._serialize.body(status, 'GitPullRequestStatus')
        response = self._send(http_method='POST',
                              location_id='b5f6bb4f-8d1e-4d79-8d11-4c9172c99c35',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('GitPullRequestStatus', response)

    def get_pull_request_status(self, repository_id, pull_request_id, status_id, project=None):
        """GetPullRequestStatus.
        [Preview API] Get the specific pull request status by ID. The status ID is unique within the pull request across all iterations.
        :param str repository_id: ID of the repository the pull request belongs to.
        :param int pull_request_id: ID of the pull request.
        :param int status_id: ID of the pull request status.
        :param str project: Project ID or project name
        :rtype: :class:`<GitPullRequestStatus> <git.v4_0.models.GitPullRequestStatus>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if status_id is not None:
            route_values['statusId'] = self._serialize.url('status_id', status_id, 'int')
        response = self._send(http_method='GET',
                              location_id='b5f6bb4f-8d1e-4d79-8d11-4c9172c99c35',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('GitPullRequestStatus', response)

    def get_pull_request_statuses(self, repository_id, pull_request_id, project=None):
        """GetPullRequestStatuses.
        [Preview API] Get all the statuses associated with a pull request.
        :param str repository_id: ID of the repository the pull request belongs to.
        :param int pull_request_id: ID of the pull request.
        :param str project: Project ID or project name
        :rtype: [GitPullRequestStatus]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        response = self._send(http_method='GET',
                              location_id='b5f6bb4f-8d1e-4d79-8d11-4c9172c99c35',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[GitPullRequestStatus]', self._unwrap_collection(response))

    def create_comment(self, comment, repository_id, pull_request_id, thread_id, project=None):
        """CreateComment.
        Create a pull request review comment
        :param :class:`<Comment> <git.v4_0.models.Comment>` comment:
        :param str repository_id:
        :param int pull_request_id:
        :param int thread_id:
        :param str project: Project ID or project name
        :rtype: :class:`<Comment> <git.v4_0.models.Comment>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if thread_id is not None:
            route_values['threadId'] = self._serialize.url('thread_id', thread_id, 'int')
        content = self._serialize.body(comment, 'Comment')
        response = self._send(http_method='POST',
                              location_id='965a3ec7-5ed8-455a-bdcb-835a5ea7fe7b',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Comment', response)

    def delete_comment(self, repository_id, pull_request_id, thread_id, comment_id, project=None):
        """DeleteComment.
        Delete a pull request comment by id for a pull request
        :param str repository_id:
        :param int pull_request_id:
        :param int thread_id:
        :param int comment_id:
        :param str project: Project ID or project name
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if thread_id is not None:
            route_values['threadId'] = self._serialize.url('thread_id', thread_id, 'int')
        if comment_id is not None:
            route_values['commentId'] = self._serialize.url('comment_id', comment_id, 'int')
        self._send(http_method='DELETE',
                   location_id='965a3ec7-5ed8-455a-bdcb-835a5ea7fe7b',
                   version='4.0',
                   route_values=route_values)

    def get_comment(self, repository_id, pull_request_id, thread_id, comment_id, project=None):
        """GetComment.
        Get a pull request comment by id for a pull request
        :param str repository_id:
        :param int pull_request_id:
        :param int thread_id:
        :param int comment_id:
        :param str project: Project ID or project name
        :rtype: :class:`<Comment> <git.v4_0.models.Comment>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if thread_id is not None:
            route_values['threadId'] = self._serialize.url('thread_id', thread_id, 'int')
        if comment_id is not None:
            route_values['commentId'] = self._serialize.url('comment_id', comment_id, 'int')
        response = self._send(http_method='GET',
                              location_id='965a3ec7-5ed8-455a-bdcb-835a5ea7fe7b',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('Comment', response)

    def get_comments(self, repository_id, pull_request_id, thread_id, project=None):
        """GetComments.
        Get all pull request comments in a thread.
        :param str repository_id:
        :param int pull_request_id:
        :param int thread_id:
        :param str project: Project ID or project name
        :rtype: [Comment]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if thread_id is not None:
            route_values['threadId'] = self._serialize.url('thread_id', thread_id, 'int')
        response = self._send(http_method='GET',
                              location_id='965a3ec7-5ed8-455a-bdcb-835a5ea7fe7b',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('[Comment]', self._unwrap_collection(response))

    def update_comment(self, comment, repository_id, pull_request_id, thread_id, comment_id, project=None):
        """UpdateComment.
        Update a pull request review comment thread
        :param :class:`<Comment> <git.v4_0.models.Comment>` comment:
        :param str repository_id:
        :param int pull_request_id:
        :param int thread_id:
        :param int comment_id:
        :param str project: Project ID or project name
        :rtype: :class:`<Comment> <git.v4_0.models.Comment>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if thread_id is not None:
            route_values['threadId'] = self._serialize.url('thread_id', thread_id, 'int')
        if comment_id is not None:
            route_values['commentId'] = self._serialize.url('comment_id', comment_id, 'int')
        content = self._serialize.body(comment, 'Comment')
        response = self._send(http_method='PATCH',
                              location_id='965a3ec7-5ed8-455a-bdcb-835a5ea7fe7b',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Comment', response)

    def create_thread(self, comment_thread, repository_id, pull_request_id, project=None):
        """CreateThread.
        Create a pull request review comment thread
        :param :class:`<GitPullRequestCommentThread> <git.v4_0.models.GitPullRequestCommentThread>` comment_thread:
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        :rtype: :class:`<GitPullRequestCommentThread> <git.v4_0.models.GitPullRequestCommentThread>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        content = self._serialize.body(comment_thread, 'GitPullRequestCommentThread')
        response = self._send(http_method='POST',
                              location_id='ab6e2e5d-a0b7-4153-b64a-a4efe0d49449',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('GitPullRequestCommentThread', response)

    def get_pull_request_thread(self, repository_id, pull_request_id, thread_id, project=None, iteration=None, base_iteration=None):
        """GetPullRequestThread.
        Get a pull request comment thread by id for a pull request
        :param str repository_id:
        :param int pull_request_id:
        :param int thread_id:
        :param str project: Project ID or project name
        :param int iteration:
        :param int base_iteration:
        :rtype: :class:`<GitPullRequestCommentThread> <git.v4_0.models.GitPullRequestCommentThread>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if thread_id is not None:
            route_values['threadId'] = self._serialize.url('thread_id', thread_id, 'int')
        query_parameters = {}
        if iteration is not None:
            query_parameters['$iteration'] = self._serialize.query('iteration', iteration, 'int')
        if base_iteration is not None:
            query_parameters['$baseIteration'] = self._serialize.query('base_iteration', base_iteration, 'int')
        response = self._send(http_method='GET',
                              location_id='ab6e2e5d-a0b7-4153-b64a-a4efe0d49449',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('GitPullRequestCommentThread', response)

    def get_threads(self, repository_id, pull_request_id, project=None, iteration=None, base_iteration=None):
        """GetThreads.
        Get all pull request comment threads.
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        :param int iteration:
        :param int base_iteration:
        :rtype: [GitPullRequestCommentThread]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        query_parameters = {}
        if iteration is not None:
            query_parameters['$iteration'] = self._serialize.query('iteration', iteration, 'int')
        if base_iteration is not None:
            query_parameters['$baseIteration'] = self._serialize.query('base_iteration', base_iteration, 'int')
        response = self._send(http_method='GET',
                              location_id='ab6e2e5d-a0b7-4153-b64a-a4efe0d49449',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[GitPullRequestCommentThread]', self._unwrap_collection(response))

    def update_thread(self, comment_thread, repository_id, pull_request_id, thread_id, project=None):
        """UpdateThread.
        Update a pull request review comment thread
        :param :class:`<GitPullRequestCommentThread> <git.v4_0.models.GitPullRequestCommentThread>` comment_thread:
        :param str repository_id:
        :param int pull_request_id:
        :param int thread_id:
        :param str project: Project ID or project name
        :rtype: :class:`<GitPullRequestCommentThread> <git.v4_0.models.GitPullRequestCommentThread>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        if thread_id is not None:
            route_values['threadId'] = self._serialize.url('thread_id', thread_id, 'int')
        content = self._serialize.body(comment_thread, 'GitPullRequestCommentThread')
        response = self._send(http_method='PATCH',
                              location_id='ab6e2e5d-a0b7-4153-b64a-a4efe0d49449',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('GitPullRequestCommentThread', response)

    def get_pull_request_work_items(self, repository_id, pull_request_id, project=None):
        """GetPullRequestWorkItems.
        Retrieve a pull request work items
        :param str repository_id:
        :param int pull_request_id:
        :param str project: Project ID or project name
        :rtype: [AssociatedWorkItem]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if pull_request_id is not None:
            route_values['pullRequestId'] = self._serialize.url('pull_request_id', pull_request_id, 'int')
        response = self._send(http_method='GET',
                              location_id='0a637fcc-5370-4ce8-b0e8-98091f5f9482',
                              version='4.0',
                              route_values=route_values)
        return self._deserialize('[AssociatedWorkItem]', self._unwrap_collection(response))

    def create_push(self, push, repository_id, project=None):
        """CreatePush.
        Push changes to the repository.
        :param :class:`<GitPush> <git.v4_0.models.GitPush>` push:
        :param str repository_id: The id or friendly name of the repository. To use the friendly name, a project-scoped route must be used.
        :param str project: Project ID or project name
        :rtype: :class:`<GitPush> <git.v4_0.models.GitPush>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        content = self._serialize.body(push, 'GitPush')
        response = self._send(http_method='POST',
                              location_id='ea98d07b-3c87-4971-8ede-a613694ffb55',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('GitPush', response)

    def get_push(self, repository_id, push_id, project=None, include_commits=None, include_ref_updates=None):
        """GetPush.
        Retrieve a particular push.
        :param str repository_id: The id or friendly name of the repository. To use the friendly name, projectId must also be specified.
        :param int push_id: The id of the push.
        :param str project: Project ID or project name
        :param int include_commits: The number of commits to include in the result.
        :param bool include_ref_updates:
        :rtype: :class:`<GitPush> <git.v4_0.models.GitPush>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if push_id is not None:
            route_values['pushId'] = self._serialize.url('push_id', push_id, 'int')
        query_parameters = {}
        if include_commits is not None:
            query_parameters['includeCommits'] = self._serialize.query('include_commits', include_commits, 'int')
        if include_ref_updates is not None:
            query_parameters['includeRefUpdates'] = self._serialize.query('include_ref_updates', include_ref_updates, 'bool')
        response = self._send(http_method='GET',
                              location_id='ea98d07b-3c87-4971-8ede-a613694ffb55',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('GitPush', response)

    def get_pushes(self, repository_id, project=None, skip=None, top=None, search_criteria=None):
        """GetPushes.
        Retrieves pushes associated with the specified repository.
        :param str repository_id: The id or friendly name of the repository. To use the friendly name, projectId must also be specified.
        :param str project: Project ID or project name
        :param int skip:
        :param int top:
        :param :class:`<GitPushSearchCriteria> <git.v4_0.models.GitPushSearchCriteria>` search_criteria:
        :rtype: [GitPush]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if skip is not None:
            query_parameters['$skip'] = self._serialize.query('skip', skip, 'int')
        if top is not None:
            query_parameters['$top'] = self._serialize.query('top', top, 'int')
        if search_criteria is not None:
            if search_criteria.from_date is not None:
                query_parameters['searchCriteria.fromDate'] = search_criteria.from_date
            if search_criteria.to_date is not None:
                query_parameters['searchCriteria.toDate'] = search_criteria.to_date
            if search_criteria.pusher_id is not None:
                query_parameters['searchCriteria.pusherId'] = search_criteria.pusher_id
            if search_criteria.ref_name is not None:
                query_parameters['searchCriteria.refName'] = search_criteria.ref_name
            if search_criteria.include_ref_updates is not None:
                query_parameters['searchCriteria.includeRefUpdates'] = search_criteria.include_ref_updates
            if search_criteria.include_links is not None:
                query_parameters['searchCriteria.includeLinks'] = search_criteria.include_links
        response = self._send(http_method='GET',
                              location_id='ea98d07b-3c87-4971-8ede-a613694ffb55',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[GitPush]', self._unwrap_collection(response))

    def get_refs(self, repository_id, project=None, filter=None, include_links=None, latest_statuses_only=None):
        """GetRefs.
        Queries the provided repository for its refs and returns them.
        :param str repository_id: The id or friendly name of the repository. To use the friendly name, projectId must also be specified.
        :param str project: Project ID or project name
        :param str filter: [optional] A filter to apply to the refs.
        :param bool include_links: [optional] Specifies if referenceLinks should be included in the result. default is false.
        :param bool latest_statuses_only:
        :rtype: [GitRef]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if filter is not None:
            query_parameters['filter'] = self._serialize.query('filter', filter, 'str')
        if include_links is not None:
            query_parameters['includeLinks'] = self._serialize.query('include_links', include_links, 'bool')
        if latest_statuses_only is not None:
            query_parameters['latestStatusesOnly'] = self._serialize.query('latest_statuses_only', latest_statuses_only, 'bool')
        response = self._send(http_method='GET',
                              location_id='2d874a60-a811-4f62-9c9f-963a6ea0a55b',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[GitRef]', self._unwrap_collection(response))

    def update_ref(self, new_ref_info, repository_id, filter, project=None, project_id=None):
        """UpdateRef.
        :param :class:`<GitRefUpdate> <git.v4_0.models.GitRefUpdate>` new_ref_info:
        :param str repository_id:
        :param str filter:
        :param str project: Project ID or project name
        :param str project_id:
        :rtype: :class:`<GitRef> <git.v4_0.models.GitRef>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if filter is not None:
            query_parameters['filter'] = self._serialize.query('filter', filter, 'str')
        if project_id is not None:
            query_parameters['projectId'] = self._serialize.query('project_id', project_id, 'str')
        content = self._serialize.body(new_ref_info, 'GitRefUpdate')
        response = self._send(http_method='PATCH',
                              location_id='2d874a60-a811-4f62-9c9f-963a6ea0a55b',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('GitRef', response)

    def update_refs(self, ref_updates, repository_id, project=None, project_id=None):
        """UpdateRefs.
        Creates or updates refs with the given information
        :param [GitRefUpdate] ref_updates: List of ref updates to attempt to perform
        :param str repository_id: The id or friendly name of the repository. To use the friendly name, projectId must also be specified.
        :param str project: Project ID or project name
        :param str project_id: The id of the project.
        :rtype: [GitRefUpdateResult]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if project_id is not None:
            query_parameters['projectId'] = self._serialize.query('project_id', project_id, 'str')
        content = self._serialize.body(ref_updates, '[GitRefUpdate]')
        response = self._send(http_method='POST',
                              location_id='2d874a60-a811-4f62-9c9f-963a6ea0a55b',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('[GitRefUpdateResult]', self._unwrap_collection(response))

    def create_favorite(self, favorite, project):
        """CreateFavorite.
        [Preview API] Creates a ref favorite
        :param :class:`<GitRefFavorite> <git.v4_0.models.GitRefFavorite>` favorite:
        :param str project: Project ID or project name
        :rtype: :class:`<GitRefFavorite> <git.v4_0.models.GitRefFavorite>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(favorite, 'GitRefFavorite')
        response = self._send(http_method='POST',
                              location_id='876f70af-5792-485a-a1c7-d0a7b2f42bbb',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('GitRefFavorite', response)

    def delete_ref_favorite(self, project, favorite_id):
        """DeleteRefFavorite.
        [Preview API]
        :param str project: Project ID or project name
        :param int favorite_id:
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if favorite_id is not None:
            route_values['favoriteId'] = self._serialize.url('favorite_id', favorite_id, 'int')
        self._send(http_method='DELETE',
                   location_id='876f70af-5792-485a-a1c7-d0a7b2f42bbb',
                   version='4.0-preview.1',
                   route_values=route_values)

    def get_ref_favorite(self, project, favorite_id):
        """GetRefFavorite.
        [Preview API]
        :param str project: Project ID or project name
        :param int favorite_id:
        :rtype: :class:`<GitRefFavorite> <git.v4_0.models.GitRefFavorite>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if favorite_id is not None:
            route_values['favoriteId'] = self._serialize.url('favorite_id', favorite_id, 'int')
        response = self._send(http_method='GET',
                              location_id='876f70af-5792-485a-a1c7-d0a7b2f42bbb',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('GitRefFavorite', response)

    def get_ref_favorites(self, project, repository_id=None, identity_id=None):
        """GetRefFavorites.
        [Preview API] Gets the refs favorites for a repo and an identity.
        :param str project: Project ID or project name
        :param str repository_id: The id of the repository.
        :param str identity_id: The id of the identity whose favorites are to be retrieved. If null, the requesting identity is used.
        :rtype: [GitRefFavorite]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if repository_id is not None:
            query_parameters['repositoryId'] = self._serialize.query('repository_id', repository_id, 'str')
        if identity_id is not None:
            query_parameters['identityId'] = self._serialize.query('identity_id', identity_id, 'str')
        response = self._send(http_method='GET',
                              location_id='876f70af-5792-485a-a1c7-d0a7b2f42bbb',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[GitRefFavorite]', self._unwrap_collection(response))

    def create_repository(self, git_repository_to_create, project=None, source_ref=None):
        """CreateRepository.
        Create a git repository
        :param :class:`<GitRepositoryCreateOptions> <git.v4_0.models.GitRepositoryCreateOptions>` git_repository_to_create:
        :param str project: Project ID or project name
        :param str source_ref:
        :rtype: :class:`<GitRepository> <git.v4_0.models.GitRepository>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if source_ref is not None:
            query_parameters['sourceRef'] = self._serialize.query('source_ref', source_ref, 'str')
        content = self._serialize.body(git_repository_to_create, 'GitRepositoryCreateOptions')
        response = self._send(http_method='POST',
                              location_id='225f7195-f9c7-4d14-ab28-a83f7ff77e1f',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('GitRepository', response)

    def delete_repository(self, repository_id, project=None):
        """DeleteRepository.
        Delete a git repository
        :param str repository_id:
        :param str project: Project ID or project name
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        self._send(http_method='DELETE',
                   location_id='225f7195-f9c7-4d14-ab28-a83f7ff77e1f',
                   version='4.0',
                   route_values=route_values)

    def get_repositories(self, project=None, include_links=None, include_all_urls=None):
        """GetRepositories.
        Retrieve git repositories.
        :param str project: Project ID or project name
        :param bool include_links:
        :param bool include_all_urls:
        :rtype: [GitRepository]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        query_parameters = {}
        if include_links is not None:
            query_parameters['includeLinks'] = self._serialize.query('include_links', include_links, 'bool')
        if include_all_urls is not None:
            query_parameters['includeAllUrls'] = self._serialize.query('include_all_urls', include_all_urls, 'bool')
        response = self._send(http_method='GET',
                              location_id='225f7195-f9c7-4d14-ab28-a83f7ff77e1f',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[GitRepository]', self._unwrap_collection(response))

    def get_repository(self, repository_id, project=None, include_parent=None):
        """GetRepository.
        :param str repository_id:
        :param str project: Project ID or project name
        :param bool include_parent:
        :rtype: :class:`<GitRepository> <git.v4_0.models.GitRepository>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if include_parent is not None:
            query_parameters['includeParent'] = self._serialize.query('include_parent', include_parent, 'bool')
        response = self._send(http_method='GET',
                              location_id='225f7195-f9c7-4d14-ab28-a83f7ff77e1f',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('GitRepository', response)

    def update_repository(self, new_repository_info, repository_id, project=None):
        """UpdateRepository.
        Updates the Git repository with the single populated change in the specified repository information.
        :param :class:`<GitRepository> <git.v4_0.models.GitRepository>` new_repository_info:
        :param str repository_id:
        :param str project: Project ID or project name
        :rtype: :class:`<GitRepository> <git.v4_0.models.GitRepository>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        content = self._serialize.body(new_repository_info, 'GitRepository')
        response = self._send(http_method='PATCH',
                              location_id='225f7195-f9c7-4d14-ab28-a83f7ff77e1f',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('GitRepository', response)

    def create_revert(self, revert_to_create, project, repository_id):
        """CreateRevert.
        [Preview API]
        :param :class:`<GitAsyncRefOperationParameters> <git.v4_0.models.GitAsyncRefOperationParameters>` revert_to_create:
        :param str project: Project ID or project name
        :param str repository_id:
        :rtype: :class:`<GitRevert> <git.v4_0.models.GitRevert>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        content = self._serialize.body(revert_to_create, 'GitAsyncRefOperationParameters')
        response = self._send(http_method='POST',
                              location_id='bc866058-5449-4715-9cf1-a510b6ff193c',
                              version='4.0-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('GitRevert', response)

    def get_revert(self, project, revert_id, repository_id):
        """GetRevert.
        [Preview API]
        :param str project: Project ID or project name
        :param int revert_id:
        :param str repository_id:
        :rtype: :class:`<GitRevert> <git.v4_0.models.GitRevert>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if revert_id is not None:
            route_values['revertId'] = self._serialize.url('revert_id', revert_id, 'int')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        response = self._send(http_method='GET',
                              location_id='bc866058-5449-4715-9cf1-a510b6ff193c',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('GitRevert', response)

    def get_revert_for_ref_name(self, project, repository_id, ref_name):
        """GetRevertForRefName.
        [Preview API]
        :param str project: Project ID or project name
        :param str repository_id:
        :param str ref_name:
        :rtype: :class:`<GitRevert> <git.v4_0.models.GitRevert>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if ref_name is not None:
            query_parameters['refName'] = self._serialize.query('ref_name', ref_name, 'str')
        response = self._send(http_method='GET',
                              location_id='bc866058-5449-4715-9cf1-a510b6ff193c',
                              version='4.0-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('GitRevert', response)

    def create_commit_status(self, git_commit_status_to_create, commit_id, repository_id, project=None):
        """CreateCommitStatus.
        :param :class:`<GitStatus> <git.v4_0.models.GitStatus>` git_commit_status_to_create:
        :param str commit_id:
        :param str repository_id:
        :param str project: Project ID or project name
        :rtype: :class:`<GitStatus> <git.v4_0.models.GitStatus>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if commit_id is not None:
            route_values['commitId'] = self._serialize.url('commit_id', commit_id, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        content = self._serialize.body(git_commit_status_to_create, 'GitStatus')
        response = self._send(http_method='POST',
                              location_id='428dd4fb-fda5-4722-af02-9313b80305da',
                              version='4.0',
                              route_values=route_values,
                              content=content)
        return self._deserialize('GitStatus', response)

    def get_statuses(self, commit_id, repository_id, project=None, top=None, skip=None, latest_only=None):
        """GetStatuses.
        :param str commit_id:
        :param str repository_id:
        :param str project: Project ID or project name
        :param int top:
        :param int skip:
        :param bool latest_only:
        :rtype: [GitStatus]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if commit_id is not None:
            route_values['commitId'] = self._serialize.url('commit_id', commit_id, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        query_parameters = {}
        if top is not None:
            query_parameters['top'] = self._serialize.query('top', top, 'int')
        if skip is not None:
            query_parameters['skip'] = self._serialize.query('skip', skip, 'int')
        if latest_only is not None:
            query_parameters['latestOnly'] = self._serialize.query('latest_only', latest_only, 'bool')
        response = self._send(http_method='GET',
                              location_id='428dd4fb-fda5-4722-af02-9313b80305da',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[GitStatus]', self._unwrap_collection(response))

    def get_suggestions(self, repository_id, project=None):
        """GetSuggestions.
        [Preview API] Retrieve a set of suggestions (including a pull request suggestion).
        :param str repository_id:
        :param str project: Project ID or project name
        :rtype: [GitSuggestion]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        response = self._send(http_method='GET',
                              location_id='9393b4fb-4445-4919-972b-9ad16f442d83',
                              version='4.0-preview.1',
                              route_values=route_values)
        return self._deserialize('[GitSuggestion]', self._unwrap_collection(response))

    def get_tree(self, repository_id, sha1, project=None, project_id=None, recursive=None, file_name=None):
        """GetTree.
        :param str repository_id:
        :param str sha1:
        :param str project: Project ID or project name
        :param str project_id:
        :param bool recursive:
        :param str file_name:
        :rtype: :class:`<GitTreeRef> <git.v4_0.models.GitTreeRef>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if sha1 is not None:
            route_values['sha1'] = self._serialize.url('sha1', sha1, 'str')
        query_parameters = {}
        if project_id is not None:
            query_parameters['projectId'] = self._serialize.query('project_id', project_id, 'str')
        if recursive is not None:
            query_parameters['recursive'] = self._serialize.query('recursive', recursive, 'bool')
        if file_name is not None:
            query_parameters['fileName'] = self._serialize.query('file_name', file_name, 'str')
        response = self._send(http_method='GET',
                              location_id='729f6437-6f92-44ec-8bee-273a7111063c',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('GitTreeRef', response)

    def get_tree_zip(self, repository_id, sha1, project=None, project_id=None, recursive=None, file_name=None, **kwargs):
        """GetTreeZip.
        :param str repository_id:
        :param str sha1:
        :param str project: Project ID or project name
        :param str project_id:
        :param bool recursive:
        :param str file_name:
        :rtype: object
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if repository_id is not None:
            route_values['repositoryId'] = self._serialize.url('repository_id', repository_id, 'str')
        if sha1 is not None:
            route_values['sha1'] = self._serialize.url('sha1', sha1, 'str')
        query_parameters = {}
        if project_id is not None:
            query_parameters['projectId'] = self._serialize.query('project_id', project_id, 'str')
        if recursive is not None:
            query_parameters['recursive'] = self._serialize.query('recursive', recursive, 'bool')
        if file_name is not None:
            query_parameters['fileName'] = self._serialize.query('file_name', file_name, 'str')
        response = self._send(http_method='GET',
                              location_id='729f6437-6f92-44ec-8bee-273a7111063c',
                              version='4.0',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              accept_media_type='application/zip')
        if "callback" in kwargs:
            callback = kwargs["callback"]
        else:
            callback = None
        return self._client.stream_download(response, callback=callback)

