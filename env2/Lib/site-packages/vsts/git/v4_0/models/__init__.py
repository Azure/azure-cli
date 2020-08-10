# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .associated_work_item import AssociatedWorkItem
from .attachment import Attachment
from .change import Change
from .comment import Comment
from .comment_iteration_context import CommentIterationContext
from .comment_position import CommentPosition
from .comment_thread import CommentThread
from .comment_thread_context import CommentThreadContext
from .comment_tracking_criteria import CommentTrackingCriteria
from .file_content_metadata import FileContentMetadata
from .git_annotated_tag import GitAnnotatedTag
from .git_async_ref_operation import GitAsyncRefOperation
from .git_async_ref_operation_detail import GitAsyncRefOperationDetail
from .git_async_ref_operation_parameters import GitAsyncRefOperationParameters
from .git_async_ref_operation_source import GitAsyncRefOperationSource
from .git_base_version_descriptor import GitBaseVersionDescriptor
from .git_blob_ref import GitBlobRef
from .git_branch_stats import GitBranchStats
from .git_cherry_pick import GitCherryPick
from .git_commit import GitCommit
from .git_commit_changes import GitCommitChanges
from .git_commit_diffs import GitCommitDiffs
from .git_commit_ref import GitCommitRef
from .git_conflict import GitConflict
from .git_deleted_repository import GitDeletedRepository
from .git_file_paths_collection import GitFilePathsCollection
from .git_fork_operation_status_detail import GitForkOperationStatusDetail
from .git_fork_ref import GitForkRef
from .git_fork_sync_request import GitForkSyncRequest
from .git_fork_sync_request_parameters import GitForkSyncRequestParameters
from .git_import_git_source import GitImportGitSource
from .git_import_request import GitImportRequest
from .git_import_request_parameters import GitImportRequestParameters
from .git_import_status_detail import GitImportStatusDetail
from .git_import_tfvc_source import GitImportTfvcSource
from .git_item import GitItem
from .git_item_descriptor import GitItemDescriptor
from .git_item_request_data import GitItemRequestData
from .git_merge_origin_ref import GitMergeOriginRef
from .git_object import GitObject
from .git_pull_request import GitPullRequest
from .git_pull_request_change import GitPullRequestChange
from .git_pull_request_comment_thread import GitPullRequestCommentThread
from .git_pull_request_comment_thread_context import GitPullRequestCommentThreadContext
from .git_pull_request_completion_options import GitPullRequestCompletionOptions
from .git_pull_request_iteration import GitPullRequestIteration
from .git_pull_request_iteration_changes import GitPullRequestIterationChanges
from .git_pull_request_merge_options import GitPullRequestMergeOptions
from .git_pull_request_query import GitPullRequestQuery
from .git_pull_request_query_input import GitPullRequestQueryInput
from .git_pull_request_search_criteria import GitPullRequestSearchCriteria
from .git_pull_request_status import GitPullRequestStatus
from .git_push import GitPush
from .git_push_ref import GitPushRef
from .git_push_search_criteria import GitPushSearchCriteria
from .git_query_branch_stats_criteria import GitQueryBranchStatsCriteria
from .git_query_commits_criteria import GitQueryCommitsCriteria
from .git_ref import GitRef
from .git_ref_favorite import GitRefFavorite
from .git_ref_update import GitRefUpdate
from .git_ref_update_result import GitRefUpdateResult
from .git_repository import GitRepository
from .git_repository_create_options import GitRepositoryCreateOptions
from .git_repository_ref import GitRepositoryRef
from .git_repository_stats import GitRepositoryStats
from .git_revert import GitRevert
from .git_status import GitStatus
from .git_status_context import GitStatusContext
from .git_suggestion import GitSuggestion
from .git_target_version_descriptor import GitTargetVersionDescriptor
from .git_template import GitTemplate
from .git_tree_diff import GitTreeDiff
from .git_tree_diff_entry import GitTreeDiffEntry
from .git_tree_diff_response import GitTreeDiffResponse
from .git_tree_entry_ref import GitTreeEntryRef
from .git_tree_ref import GitTreeRef
from .git_user_date import GitUserDate
from .git_version_descriptor import GitVersionDescriptor
from .global_git_repository_key import GlobalGitRepositoryKey
from .identity_ref import IdentityRef
from .identity_ref_with_vote import IdentityRefWithVote
from .import_repository_validation import ImportRepositoryValidation
from .item_content import ItemContent
from .item_model import ItemModel
from .reference_links import ReferenceLinks
from .resource_ref import ResourceRef
from .share_notification_context import ShareNotificationContext
from .source_to_target_ref import SourceToTargetRef
from .team_project_collection_reference import TeamProjectCollectionReference
from .team_project_reference import TeamProjectReference
from .vsts_info import VstsInfo
from .web_api_create_tag_request_data import WebApiCreateTagRequestData
from .web_api_tag_definition import WebApiTagDefinition

__all__ = [
    'AssociatedWorkItem',
    'Attachment',
    'Change',
    'Comment',
    'CommentIterationContext',
    'CommentPosition',
    'CommentThread',
    'CommentThreadContext',
    'CommentTrackingCriteria',
    'FileContentMetadata',
    'GitAnnotatedTag',
    'GitAsyncRefOperation',
    'GitAsyncRefOperationDetail',
    'GitAsyncRefOperationParameters',
    'GitAsyncRefOperationSource',
    'GitBaseVersionDescriptor',
    'GitBlobRef',
    'GitBranchStats',
    'GitCherryPick',
    'GitCommit',
    'GitCommitChanges',
    'GitCommitDiffs',
    'GitCommitRef',
    'GitConflict',
    'GitDeletedRepository',
    'GitFilePathsCollection',
    'GitForkOperationStatusDetail',
    'GitForkRef',
    'GitForkSyncRequest',
    'GitForkSyncRequestParameters',
    'GitImportGitSource',
    'GitImportRequest',
    'GitImportRequestParameters',
    'GitImportStatusDetail',
    'GitImportTfvcSource',
    'GitItem',
    'GitItemDescriptor',
    'GitItemRequestData',
    'GitMergeOriginRef',
    'GitObject',
    'GitPullRequest',
    'GitPullRequestChange',
    'GitPullRequestCommentThread',
    'GitPullRequestCommentThreadContext',
    'GitPullRequestCompletionOptions',
    'GitPullRequestIteration',
    'GitPullRequestIterationChanges',
    'GitPullRequestMergeOptions',
    'GitPullRequestQuery',
    'GitPullRequestQueryInput',
    'GitPullRequestSearchCriteria',
    'GitPullRequestStatus',
    'GitPush',
    'GitPushRef',
    'GitPushSearchCriteria',
    'GitQueryBranchStatsCriteria',
    'GitQueryCommitsCriteria',
    'GitRef',
    'GitRefFavorite',
    'GitRefUpdate',
    'GitRefUpdateResult',
    'GitRepository',
    'GitRepositoryCreateOptions',
    'GitRepositoryRef',
    'GitRepositoryStats',
    'GitRevert',
    'GitStatus',
    'GitStatusContext',
    'GitSuggestion',
    'GitTargetVersionDescriptor',
    'GitTemplate',
    'GitTreeDiff',
    'GitTreeDiffEntry',
    'GitTreeDiffResponse',
    'GitTreeEntryRef',
    'GitTreeRef',
    'GitUserDate',
    'GitVersionDescriptor',
    'GlobalGitRepositoryKey',
    'IdentityRef',
    'IdentityRefWithVote',
    'ImportRepositoryValidation',
    'ItemContent',
    'ItemModel',
    'ReferenceLinks',
    'ResourceRef',
    'ShareNotificationContext',
    'SourceToTargetRef',
    'TeamProjectCollectionReference',
    'TeamProjectReference',
    'VstsInfo',
    'WebApiCreateTagRequestData',
    'WebApiTagDefinition',
]
