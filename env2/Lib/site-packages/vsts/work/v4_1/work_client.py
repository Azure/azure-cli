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


class WorkClient(VssClient):
    """Work
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(WorkClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = '1d4f49f9-02b9-4e26-b826-2cdb6195f2a9'

    def get_backlog_configurations(self, team_context):
        """GetBacklogConfigurations.
        Gets backlog configuration for a team
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :rtype: :class:`<BacklogConfiguration> <work.v4_1.models.BacklogConfiguration>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        response = self._send(http_method='GET',
                              location_id='7799f497-3cb5-4f16-ad4f-5cd06012db64',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('BacklogConfiguration', response)

    def get_backlog_level_work_items(self, team_context, backlog_id):
        """GetBacklogLevelWorkItems.
        [Preview API] Get a list of work items within a backlog level
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str backlog_id:
        :rtype: :class:`<BacklogLevelWorkItems> <work.v4_1.models.BacklogLevelWorkItems>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if backlog_id is not None:
            route_values['backlogId'] = self._serialize.url('backlog_id', backlog_id, 'str')
        response = self._send(http_method='GET',
                              location_id='7c468d96-ab1d-4294-a360-92f07e9ccd98',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('BacklogLevelWorkItems', response)

    def get_backlog(self, team_context, id):
        """GetBacklog.
        [Preview API] Get a backlog level
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str id: The id of the backlog level
        :rtype: :class:`<BacklogLevelConfiguration> <work.v4_1.models.BacklogLevelConfiguration>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if id is not None:
            route_values['id'] = self._serialize.url('id', id, 'str')
        response = self._send(http_method='GET',
                              location_id='a93726f9-7867-4e38-b4f2-0bfafc2f6a94',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('BacklogLevelConfiguration', response)

    def get_backlogs(self, team_context):
        """GetBacklogs.
        [Preview API] List all backlog levels
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :rtype: [BacklogLevelConfiguration]
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        response = self._send(http_method='GET',
                              location_id='a93726f9-7867-4e38-b4f2-0bfafc2f6a94',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('[BacklogLevelConfiguration]', self._unwrap_collection(response))

    def get_column_suggested_values(self, project=None):
        """GetColumnSuggestedValues.
        Get available board columns in a project
        :param str project: Project ID or project name
        :rtype: [BoardSuggestedValue]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        response = self._send(http_method='GET',
                              location_id='eb7ec5a3-1ba3-4fd1-b834-49a5a387e57d',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('[BoardSuggestedValue]', self._unwrap_collection(response))

    def get_board_mapping_parent_items(self, team_context, child_backlog_context_category_ref_name, workitem_ids):
        """GetBoardMappingParentItems.
        [Preview API] Returns the list of parent field filter model for the given list of workitem ids
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str child_backlog_context_category_ref_name:
        :param [int] workitem_ids:
        :rtype: [ParentChildWIMap]
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        query_parameters = {}
        if child_backlog_context_category_ref_name is not None:
            query_parameters['childBacklogContextCategoryRefName'] = self._serialize.query('child_backlog_context_category_ref_name', child_backlog_context_category_ref_name, 'str')
        if workitem_ids is not None:
            workitem_ids = ",".join(map(str, workitem_ids))
            query_parameters['workitemIds'] = self._serialize.query('workitem_ids', workitem_ids, 'str')
        response = self._send(http_method='GET',
                              location_id='186abea3-5c35-432f-9e28-7a15b4312a0e',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[ParentChildWIMap]', self._unwrap_collection(response))

    def get_row_suggested_values(self, project=None):
        """GetRowSuggestedValues.
        Get available board rows in a project
        :param str project: Project ID or project name
        :rtype: [BoardSuggestedValue]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        response = self._send(http_method='GET',
                              location_id='bb494cc6-a0f5-4c6c-8dca-ea6912e79eb9',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('[BoardSuggestedValue]', self._unwrap_collection(response))

    def get_board(self, team_context, id):
        """GetBoard.
        Get board
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str id: identifier for board, either board's backlog level name (Eg:"Stories") or Id
        :rtype: :class:`<Board> <work.v4_1.models.Board>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if id is not None:
            route_values['id'] = self._serialize.url('id', id, 'str')
        response = self._send(http_method='GET',
                              location_id='23ad19fc-3b8e-4877-8462-b3f92bc06b40',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('Board', response)

    def get_boards(self, team_context):
        """GetBoards.
        Get boards
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :rtype: [BoardReference]
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        response = self._send(http_method='GET',
                              location_id='23ad19fc-3b8e-4877-8462-b3f92bc06b40',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('[BoardReference]', self._unwrap_collection(response))

    def set_board_options(self, options, team_context, id):
        """SetBoardOptions.
        Update board options
        :param {str} options: options to updated
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str id: identifier for board, either category plural name (Eg:"Stories") or guid
        :rtype: {str}
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if id is not None:
            route_values['id'] = self._serialize.url('id', id, 'str')
        content = self._serialize.body(options, '{str}')
        response = self._send(http_method='PUT',
                              location_id='23ad19fc-3b8e-4877-8462-b3f92bc06b40',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('{str}', self._unwrap_collection(response))

    def get_board_user_settings(self, team_context, board):
        """GetBoardUserSettings.
        [Preview API] Get board user settings for a board id
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str board: Board ID or Name
        :rtype: :class:`<BoardUserSettings> <work.v4_1.models.BoardUserSettings>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if board is not None:
            route_values['board'] = self._serialize.url('board', board, 'str')
        response = self._send(http_method='GET',
                              location_id='b30d9f58-1891-4b0a-b168-c46408f919b0',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('BoardUserSettings', response)

    def update_board_user_settings(self, board_user_settings, team_context, board):
        """UpdateBoardUserSettings.
        [Preview API] Update board user settings for the board id
        :param {str} board_user_settings:
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str board:
        :rtype: :class:`<BoardUserSettings> <work.v4_1.models.BoardUserSettings>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if board is not None:
            route_values['board'] = self._serialize.url('board', board, 'str')
        content = self._serialize.body(board_user_settings, '{str}')
        response = self._send(http_method='PATCH',
                              location_id='b30d9f58-1891-4b0a-b168-c46408f919b0',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('BoardUserSettings', response)

    def get_capacities(self, team_context, iteration_id):
        """GetCapacities.
        Get a team's capacity
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str iteration_id: ID of the iteration
        :rtype: [TeamMemberCapacity]
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if iteration_id is not None:
            route_values['iterationId'] = self._serialize.url('iteration_id', iteration_id, 'str')
        response = self._send(http_method='GET',
                              location_id='74412d15-8c1a-4352-a48d-ef1ed5587d57',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('[TeamMemberCapacity]', self._unwrap_collection(response))

    def get_capacity(self, team_context, iteration_id, team_member_id):
        """GetCapacity.
        Get a team member's capacity
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str iteration_id: ID of the iteration
        :param str team_member_id: ID of the team member
        :rtype: :class:`<TeamMemberCapacity> <work.v4_1.models.TeamMemberCapacity>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if iteration_id is not None:
            route_values['iterationId'] = self._serialize.url('iteration_id', iteration_id, 'str')
        if team_member_id is not None:
            route_values['teamMemberId'] = self._serialize.url('team_member_id', team_member_id, 'str')
        response = self._send(http_method='GET',
                              location_id='74412d15-8c1a-4352-a48d-ef1ed5587d57',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('TeamMemberCapacity', response)

    def replace_capacities(self, capacities, team_context, iteration_id):
        """ReplaceCapacities.
        Replace a team's capacity
        :param [TeamMemberCapacity] capacities: Team capacity to replace
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str iteration_id: ID of the iteration
        :rtype: [TeamMemberCapacity]
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if iteration_id is not None:
            route_values['iterationId'] = self._serialize.url('iteration_id', iteration_id, 'str')
        content = self._serialize.body(capacities, '[TeamMemberCapacity]')
        response = self._send(http_method='PUT',
                              location_id='74412d15-8c1a-4352-a48d-ef1ed5587d57',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[TeamMemberCapacity]', self._unwrap_collection(response))

    def update_capacity(self, patch, team_context, iteration_id, team_member_id):
        """UpdateCapacity.
        Update a team member's capacity
        :param :class:`<CapacityPatch> <work.v4_1.models.CapacityPatch>` patch: Updated capacity
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str iteration_id: ID of the iteration
        :param str team_member_id: ID of the team member
        :rtype: :class:`<TeamMemberCapacity> <work.v4_1.models.TeamMemberCapacity>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if iteration_id is not None:
            route_values['iterationId'] = self._serialize.url('iteration_id', iteration_id, 'str')
        if team_member_id is not None:
            route_values['teamMemberId'] = self._serialize.url('team_member_id', team_member_id, 'str')
        content = self._serialize.body(patch, 'CapacityPatch')
        response = self._send(http_method='PATCH',
                              location_id='74412d15-8c1a-4352-a48d-ef1ed5587d57',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TeamMemberCapacity', response)

    def get_board_card_rule_settings(self, team_context, board):
        """GetBoardCardRuleSettings.
        Get board card Rule settings for the board id or board by name
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str board:
        :rtype: :class:`<BoardCardRuleSettings> <work.v4_1.models.BoardCardRuleSettings>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if board is not None:
            route_values['board'] = self._serialize.url('board', board, 'str')
        response = self._send(http_method='GET',
                              location_id='b044a3d9-02ea-49c7-91a1-b730949cc896',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('BoardCardRuleSettings', response)

    def update_board_card_rule_settings(self, board_card_rule_settings, team_context, board):
        """UpdateBoardCardRuleSettings.
        Update board card Rule settings for the board id or board by name
        :param :class:`<BoardCardRuleSettings> <work.v4_1.models.BoardCardRuleSettings>` board_card_rule_settings:
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str board:
        :rtype: :class:`<BoardCardRuleSettings> <work.v4_1.models.BoardCardRuleSettings>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if board is not None:
            route_values['board'] = self._serialize.url('board', board, 'str')
        content = self._serialize.body(board_card_rule_settings, 'BoardCardRuleSettings')
        response = self._send(http_method='PATCH',
                              location_id='b044a3d9-02ea-49c7-91a1-b730949cc896',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('BoardCardRuleSettings', response)

    def get_board_card_settings(self, team_context, board):
        """GetBoardCardSettings.
        Get board card settings for the board id or board by name
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str board:
        :rtype: :class:`<BoardCardSettings> <work.v4_1.models.BoardCardSettings>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if board is not None:
            route_values['board'] = self._serialize.url('board', board, 'str')
        response = self._send(http_method='GET',
                              location_id='07c3b467-bc60-4f05-8e34-599ce288fafc',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('BoardCardSettings', response)

    def update_board_card_settings(self, board_card_settings_to_save, team_context, board):
        """UpdateBoardCardSettings.
        Update board card settings for the board id or board by name
        :param :class:`<BoardCardSettings> <work.v4_1.models.BoardCardSettings>` board_card_settings_to_save:
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str board:
        :rtype: :class:`<BoardCardSettings> <work.v4_1.models.BoardCardSettings>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if board is not None:
            route_values['board'] = self._serialize.url('board', board, 'str')
        content = self._serialize.body(board_card_settings_to_save, 'BoardCardSettings')
        response = self._send(http_method='PUT',
                              location_id='07c3b467-bc60-4f05-8e34-599ce288fafc',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('BoardCardSettings', response)

    def get_board_chart(self, team_context, board, name):
        """GetBoardChart.
        Get a board chart
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str board: Identifier for board, either board's backlog level name (Eg:"Stories") or Id
        :param str name: The chart name
        :rtype: :class:`<BoardChart> <work.v4_1.models.BoardChart>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if board is not None:
            route_values['board'] = self._serialize.url('board', board, 'str')
        if name is not None:
            route_values['name'] = self._serialize.url('name', name, 'str')
        response = self._send(http_method='GET',
                              location_id='45fe888c-239e-49fd-958c-df1a1ab21d97',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('BoardChart', response)

    def get_board_charts(self, team_context, board):
        """GetBoardCharts.
        Get board charts
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str board: Identifier for board, either board's backlog level name (Eg:"Stories") or Id
        :rtype: [BoardChartReference]
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if board is not None:
            route_values['board'] = self._serialize.url('board', board, 'str')
        response = self._send(http_method='GET',
                              location_id='45fe888c-239e-49fd-958c-df1a1ab21d97',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('[BoardChartReference]', self._unwrap_collection(response))

    def update_board_chart(self, chart, team_context, board, name):
        """UpdateBoardChart.
        Update a board chart
        :param :class:`<BoardChart> <work.v4_1.models.BoardChart>` chart:
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str board: Identifier for board, either board's backlog level name (Eg:"Stories") or Id
        :param str name: The chart name
        :rtype: :class:`<BoardChart> <work.v4_1.models.BoardChart>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if board is not None:
            route_values['board'] = self._serialize.url('board', board, 'str')
        if name is not None:
            route_values['name'] = self._serialize.url('name', name, 'str')
        content = self._serialize.body(chart, 'BoardChart')
        response = self._send(http_method='PATCH',
                              location_id='45fe888c-239e-49fd-958c-df1a1ab21d97',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('BoardChart', response)

    def get_board_columns(self, team_context, board):
        """GetBoardColumns.
        Get columns on a board
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str board: Name or ID of the specific board
        :rtype: [BoardColumn]
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if board is not None:
            route_values['board'] = self._serialize.url('board', board, 'str')
        response = self._send(http_method='GET',
                              location_id='c555d7ff-84e1-47df-9923-a3fe0cd8751b',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('[BoardColumn]', self._unwrap_collection(response))

    def update_board_columns(self, board_columns, team_context, board):
        """UpdateBoardColumns.
        Update columns on a board
        :param [BoardColumn] board_columns: List of board columns to update
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str board: Name or ID of the specific board
        :rtype: [BoardColumn]
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if board is not None:
            route_values['board'] = self._serialize.url('board', board, 'str')
        content = self._serialize.body(board_columns, '[BoardColumn]')
        response = self._send(http_method='PUT',
                              location_id='c555d7ff-84e1-47df-9923-a3fe0cd8751b',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[BoardColumn]', self._unwrap_collection(response))

    def get_delivery_timeline_data(self, project, id, revision=None, start_date=None, end_date=None):
        """GetDeliveryTimelineData.
        Get Delivery View Data
        :param str project: Project ID or project name
        :param str id: Identifier for delivery view
        :param int revision: Revision of the plan for which you want data. If the current plan is a different revision you will get an ViewRevisionMismatchException exception. If you do not supply a revision you will get data for the latest revision.
        :param datetime start_date: The start date of timeline
        :param datetime end_date: The end date of timeline
        :rtype: :class:`<DeliveryViewData> <work.v4_1.models.DeliveryViewData>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if id is not None:
            route_values['id'] = self._serialize.url('id', id, 'str')
        query_parameters = {}
        if revision is not None:
            query_parameters['revision'] = self._serialize.query('revision', revision, 'int')
        if start_date is not None:
            query_parameters['startDate'] = self._serialize.query('start_date', start_date, 'iso-8601')
        if end_date is not None:
            query_parameters['endDate'] = self._serialize.query('end_date', end_date, 'iso-8601')
        response = self._send(http_method='GET',
                              location_id='bdd0834e-101f-49f0-a6ae-509f384a12b4',
                              version='4.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('DeliveryViewData', response)

    def delete_team_iteration(self, team_context, id):
        """DeleteTeamIteration.
        Delete a team's iteration by iterationId
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str id: ID of the iteration
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if id is not None:
            route_values['id'] = self._serialize.url('id', id, 'str')
        self._send(http_method='DELETE',
                   location_id='c9175577-28a1-4b06-9197-8636af9f64ad',
                   version='4.1',
                   route_values=route_values)

    def get_team_iteration(self, team_context, id):
        """GetTeamIteration.
        Get team's iteration by iterationId
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str id: ID of the iteration
        :rtype: :class:`<TeamSettingsIteration> <work.v4_1.models.TeamSettingsIteration>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if id is not None:
            route_values['id'] = self._serialize.url('id', id, 'str')
        response = self._send(http_method='GET',
                              location_id='c9175577-28a1-4b06-9197-8636af9f64ad',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('TeamSettingsIteration', response)

    def get_team_iterations(self, team_context, timeframe=None):
        """GetTeamIterations.
        Get a team's iterations using timeframe filter
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str timeframe: A filter for which iterations are returned based on relative time. Only Current is supported currently.
        :rtype: [TeamSettingsIteration]
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        query_parameters = {}
        if timeframe is not None:
            query_parameters['$timeframe'] = self._serialize.query('timeframe', timeframe, 'str')
        response = self._send(http_method='GET',
                              location_id='c9175577-28a1-4b06-9197-8636af9f64ad',
                              version='4.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[TeamSettingsIteration]', self._unwrap_collection(response))

    def post_team_iteration(self, iteration, team_context):
        """PostTeamIteration.
        Add an iteration to the team
        :param :class:`<TeamSettingsIteration> <work.v4_1.models.TeamSettingsIteration>` iteration: Iteration to add
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :rtype: :class:`<TeamSettingsIteration> <work.v4_1.models.TeamSettingsIteration>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        content = self._serialize.body(iteration, 'TeamSettingsIteration')
        response = self._send(http_method='POST',
                              location_id='c9175577-28a1-4b06-9197-8636af9f64ad',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TeamSettingsIteration', response)

    def create_plan(self, posted_plan, project):
        """CreatePlan.
        Add a new plan for the team
        :param :class:`<CreatePlan> <work.v4_1.models.CreatePlan>` posted_plan: Plan definition
        :param str project: Project ID or project name
        :rtype: :class:`<Plan> <work.v4_1.models.Plan>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        content = self._serialize.body(posted_plan, 'CreatePlan')
        response = self._send(http_method='POST',
                              location_id='0b42cb47-cd73-4810-ac90-19c9ba147453',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Plan', response)

    def delete_plan(self, project, id):
        """DeletePlan.
        Delete the specified plan
        :param str project: Project ID or project name
        :param str id: Identifier of the plan
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if id is not None:
            route_values['id'] = self._serialize.url('id', id, 'str')
        self._send(http_method='DELETE',
                   location_id='0b42cb47-cd73-4810-ac90-19c9ba147453',
                   version='4.1',
                   route_values=route_values)

    def get_plan(self, project, id):
        """GetPlan.
        Get the information for the specified plan
        :param str project: Project ID or project name
        :param str id: Identifier of the plan
        :rtype: :class:`<Plan> <work.v4_1.models.Plan>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if id is not None:
            route_values['id'] = self._serialize.url('id', id, 'str')
        response = self._send(http_method='GET',
                              location_id='0b42cb47-cd73-4810-ac90-19c9ba147453',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('Plan', response)

    def get_plans(self, project):
        """GetPlans.
        Get the information for all the plans configured for the given team
        :param str project: Project ID or project name
        :rtype: [Plan]
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        response = self._send(http_method='GET',
                              location_id='0b42cb47-cd73-4810-ac90-19c9ba147453',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('[Plan]', self._unwrap_collection(response))

    def update_plan(self, updated_plan, project, id):
        """UpdatePlan.
        Update the information for the specified plan
        :param :class:`<UpdatePlan> <work.v4_1.models.UpdatePlan>` updated_plan: Plan definition to be updated
        :param str project: Project ID or project name
        :param str id: Identifier of the plan
        :rtype: :class:`<Plan> <work.v4_1.models.Plan>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        if id is not None:
            route_values['id'] = self._serialize.url('id', id, 'str')
        content = self._serialize.body(updated_plan, 'UpdatePlan')
        response = self._send(http_method='PUT',
                              location_id='0b42cb47-cd73-4810-ac90-19c9ba147453',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Plan', response)

    def get_process_configuration(self, project):
        """GetProcessConfiguration.
        [Preview API] Get process configuration
        :param str project: Project ID or project name
        :rtype: :class:`<ProcessConfiguration> <work.v4_1.models.ProcessConfiguration>`
        """
        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'str')
        response = self._send(http_method='GET',
                              location_id='f901ba42-86d2-4b0c-89c1-3f86d06daa84',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('ProcessConfiguration', response)

    def get_board_rows(self, team_context, board):
        """GetBoardRows.
        Get rows on a board
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str board: Name or ID of the specific board
        :rtype: [BoardRow]
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if board is not None:
            route_values['board'] = self._serialize.url('board', board, 'str')
        response = self._send(http_method='GET',
                              location_id='0863355d-aefd-4d63-8669-984c9b7b0e78',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('[BoardRow]', self._unwrap_collection(response))

    def update_board_rows(self, board_rows, team_context, board):
        """UpdateBoardRows.
        Update rows on a board
        :param [BoardRow] board_rows: List of board rows to update
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str board: Name or ID of the specific board
        :rtype: [BoardRow]
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if board is not None:
            route_values['board'] = self._serialize.url('board', board, 'str')
        content = self._serialize.body(board_rows, '[BoardRow]')
        response = self._send(http_method='PUT',
                              location_id='0863355d-aefd-4d63-8669-984c9b7b0e78',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('[BoardRow]', self._unwrap_collection(response))

    def get_team_days_off(self, team_context, iteration_id):
        """GetTeamDaysOff.
        Get team's days off for an iteration
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str iteration_id: ID of the iteration
        :rtype: :class:`<TeamSettingsDaysOff> <work.v4_1.models.TeamSettingsDaysOff>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if iteration_id is not None:
            route_values['iterationId'] = self._serialize.url('iteration_id', iteration_id, 'str')
        response = self._send(http_method='GET',
                              location_id='2d4faa2e-9150-4cbf-a47a-932b1b4a0773',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('TeamSettingsDaysOff', response)

    def update_team_days_off(self, days_off_patch, team_context, iteration_id):
        """UpdateTeamDaysOff.
        Set a team's days off for an iteration
        :param :class:`<TeamSettingsDaysOffPatch> <work.v4_1.models.TeamSettingsDaysOffPatch>` days_off_patch: Team's days off patch containting a list of start and end dates
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str iteration_id: ID of the iteration
        :rtype: :class:`<TeamSettingsDaysOff> <work.v4_1.models.TeamSettingsDaysOff>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if iteration_id is not None:
            route_values['iterationId'] = self._serialize.url('iteration_id', iteration_id, 'str')
        content = self._serialize.body(days_off_patch, 'TeamSettingsDaysOffPatch')
        response = self._send(http_method='PATCH',
                              location_id='2d4faa2e-9150-4cbf-a47a-932b1b4a0773',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TeamSettingsDaysOff', response)

    def get_team_field_values(self, team_context):
        """GetTeamFieldValues.
        Get a collection of team field values
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :rtype: :class:`<TeamFieldValues> <work.v4_1.models.TeamFieldValues>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        response = self._send(http_method='GET',
                              location_id='07ced576-58ed-49e6-9c1e-5cb53ab8bf2a',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('TeamFieldValues', response)

    def update_team_field_values(self, patch, team_context):
        """UpdateTeamFieldValues.
        Update team field values
        :param :class:`<TeamFieldValuesPatch> <work.v4_1.models.TeamFieldValuesPatch>` patch:
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :rtype: :class:`<TeamFieldValues> <work.v4_1.models.TeamFieldValues>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        content = self._serialize.body(patch, 'TeamFieldValuesPatch')
        response = self._send(http_method='PATCH',
                              location_id='07ced576-58ed-49e6-9c1e-5cb53ab8bf2a',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TeamFieldValues', response)

    def get_team_settings(self, team_context):
        """GetTeamSettings.
        Get a team's settings
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :rtype: :class:`<TeamSetting> <work.v4_1.models.TeamSetting>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        response = self._send(http_method='GET',
                              location_id='c3c1012b-bea7-49d7-b45e-1664e566f84c',
                              version='4.1',
                              route_values=route_values)
        return self._deserialize('TeamSetting', response)

    def update_team_settings(self, team_settings_patch, team_context):
        """UpdateTeamSettings.
        Update a team's settings
        :param :class:`<TeamSettingsPatch> <work.v4_1.models.TeamSettingsPatch>` team_settings_patch: TeamSettings changes
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :rtype: :class:`<TeamSetting> <work.v4_1.models.TeamSetting>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        content = self._serialize.body(team_settings_patch, 'TeamSettingsPatch')
        response = self._send(http_method='PATCH',
                              location_id='c3c1012b-bea7-49d7-b45e-1664e566f84c',
                              version='4.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('TeamSetting', response)

    def get_iteration_work_items(self, team_context, iteration_id):
        """GetIterationWorkItems.
        [Preview API] Get work items for iteration
        :param :class:`<TeamContext> <work.v4_1.models.TeamContext>` team_context: The team context for the operation
        :param str iteration_id: ID of the iteration
        :rtype: :class:`<IterationWorkItems> <work.v4_1.models.IterationWorkItems>`
        """
        project = None
        team = None
        if team_context is not None:
            if team_context.project_id:
                project = team_context.project_id
            else:
                project = team_context.project
            if team_context.team_id:
                team = team_context.team_id
            else:
                team = team_context.team

        route_values = {}
        if project is not None:
            route_values['project'] = self._serialize.url('project', project, 'string')
        if team is not None:
            route_values['team'] = self._serialize.url('team', team, 'string')
        if iteration_id is not None:
            route_values['iterationId'] = self._serialize.url('iteration_id', iteration_id, 'str')
        response = self._send(http_method='GET',
                              location_id='5b3ef1a6-d3ab-44cd-bafd-c7f45db850fa',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('IterationWorkItems', response)

