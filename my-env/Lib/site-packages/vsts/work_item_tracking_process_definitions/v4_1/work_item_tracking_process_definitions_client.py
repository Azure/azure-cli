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


class WorkItemTrackingClient(VssClient):
    """WorkItemTracking
    :param str base_url: Service URL
    :param Authentication creds: Authenticated credentials.
    """

    def __init__(self, base_url=None, creds=None):
        super(WorkItemTrackingClient, self).__init__(base_url, creds)
        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    resource_area_identifier = '5264459e-e5e0-4bd8-b118-0985e68a4ec5'

    def create_behavior(self, behavior, process_id):
        """CreateBehavior.
        [Preview API] Creates a single behavior in the given process.
        :param :class:`<BehaviorCreateModel> <work-item-tracking.v4_1.models.BehaviorCreateModel>` behavior:
        :param str process_id: The ID of the process
        :rtype: :class:`<BehaviorModel> <work-item-tracking.v4_1.models.BehaviorModel>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        content = self._serialize.body(behavior, 'BehaviorCreateModel')
        response = self._send(http_method='POST',
                              location_id='47a651f4-fb70-43bf-b96b-7c0ba947142b',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('BehaviorModel', response)

    def delete_behavior(self, process_id, behavior_id):
        """DeleteBehavior.
        [Preview API] Removes a behavior in the process.
        :param str process_id: The ID of the process
        :param str behavior_id: The ID of the behavior
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if behavior_id is not None:
            route_values['behaviorId'] = self._serialize.url('behavior_id', behavior_id, 'str')
        self._send(http_method='DELETE',
                   location_id='47a651f4-fb70-43bf-b96b-7c0ba947142b',
                   version='4.1-preview.1',
                   route_values=route_values)

    def get_behavior(self, process_id, behavior_id):
        """GetBehavior.
        [Preview API] Returns a single behavior in the process.
        :param str process_id: The ID of the process
        :param str behavior_id: The ID of the behavior
        :rtype: :class:`<BehaviorModel> <work-item-tracking.v4_1.models.BehaviorModel>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if behavior_id is not None:
            route_values['behaviorId'] = self._serialize.url('behavior_id', behavior_id, 'str')
        response = self._send(http_method='GET',
                              location_id='47a651f4-fb70-43bf-b96b-7c0ba947142b',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('BehaviorModel', response)

    def get_behaviors(self, process_id):
        """GetBehaviors.
        [Preview API] Returns a list of all behaviors in the process.
        :param str process_id: The ID of the process
        :rtype: [BehaviorModel]
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        response = self._send(http_method='GET',
                              location_id='47a651f4-fb70-43bf-b96b-7c0ba947142b',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('[BehaviorModel]', self._unwrap_collection(response))

    def replace_behavior(self, behavior_data, process_id, behavior_id):
        """ReplaceBehavior.
        [Preview API] Replaces a behavior in the process.
        :param :class:`<BehaviorReplaceModel> <work-item-tracking.v4_1.models.BehaviorReplaceModel>` behavior_data:
        :param str process_id: The ID of the process
        :param str behavior_id: The ID of the behavior
        :rtype: :class:`<BehaviorModel> <work-item-tracking.v4_1.models.BehaviorModel>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if behavior_id is not None:
            route_values['behaviorId'] = self._serialize.url('behavior_id', behavior_id, 'str')
        content = self._serialize.body(behavior_data, 'BehaviorReplaceModel')
        response = self._send(http_method='PUT',
                              location_id='47a651f4-fb70-43bf-b96b-7c0ba947142b',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('BehaviorModel', response)

    def add_control_to_group(self, control, process_id, wit_ref_name, group_id):
        """AddControlToGroup.
        [Preview API] Creates a control in a group
        :param :class:`<Control> <work-item-tracking.v4_1.models.Control>` control: The control
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :param str group_id: The ID of the group to add the control to
        :rtype: :class:`<Control> <work-item-tracking.v4_1.models.Control>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        content = self._serialize.body(control, 'Control')
        response = self._send(http_method='POST',
                              location_id='e2e3166a-627a-4e9b-85b2-d6a097bbd731',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Control', response)

    def edit_control(self, control, process_id, wit_ref_name, group_id, control_id):
        """EditControl.
        [Preview API] Updates a control on the work item form
        :param :class:`<Control> <work-item-tracking.v4_1.models.Control>` control: The updated control
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :param str group_id: The ID of the group
        :param str control_id: The ID of the control
        :rtype: :class:`<Control> <work-item-tracking.v4_1.models.Control>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        if control_id is not None:
            route_values['controlId'] = self._serialize.url('control_id', control_id, 'str')
        content = self._serialize.body(control, 'Control')
        response = self._send(http_method='PATCH',
                              location_id='e2e3166a-627a-4e9b-85b2-d6a097bbd731',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Control', response)

    def remove_control_from_group(self, process_id, wit_ref_name, group_id, control_id):
        """RemoveControlFromGroup.
        [Preview API] Removes a control from the work item form
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :param str group_id: The ID of the group
        :param str control_id: The ID of the control to remove
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        if control_id is not None:
            route_values['controlId'] = self._serialize.url('control_id', control_id, 'str')
        self._send(http_method='DELETE',
                   location_id='e2e3166a-627a-4e9b-85b2-d6a097bbd731',
                   version='4.1-preview.1',
                   route_values=route_values)

    def set_control_in_group(self, control, process_id, wit_ref_name, group_id, control_id, remove_from_group_id=None):
        """SetControlInGroup.
        [Preview API] Moves a control to a new group
        :param :class:`<Control> <work-item-tracking.v4_1.models.Control>` control: The control
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :param str group_id: The ID of the group to move the control to
        :param str control_id: The id of the control
        :param str remove_from_group_id: The group to remove the control from
        :rtype: :class:`<Control> <work-item-tracking.v4_1.models.Control>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        if control_id is not None:
            route_values['controlId'] = self._serialize.url('control_id', control_id, 'str')
        query_parameters = {}
        if remove_from_group_id is not None:
            query_parameters['removeFromGroupId'] = self._serialize.query('remove_from_group_id', remove_from_group_id, 'str')
        content = self._serialize.body(control, 'Control')
        response = self._send(http_method='PUT',
                              location_id='e2e3166a-627a-4e9b-85b2-d6a097bbd731',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('Control', response)

    def create_field(self, field, process_id):
        """CreateField.
        [Preview API] Creates a single field in the process.
        :param :class:`<FieldModel> <work-item-tracking.v4_1.models.FieldModel>` field:
        :param str process_id: The ID of the process
        :rtype: :class:`<FieldModel> <work-item-tracking.v4_1.models.FieldModel>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        content = self._serialize.body(field, 'FieldModel')
        response = self._send(http_method='POST',
                              location_id='f36c66c7-911d-4163-8938-d3c5d0d7f5aa',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('FieldModel', response)

    def update_field(self, field, process_id):
        """UpdateField.
        [Preview API] Updates a given field in the process.
        :param :class:`<FieldUpdate> <work-item-tracking.v4_1.models.FieldUpdate>` field:
        :param str process_id: The ID of the process
        :rtype: :class:`<FieldModel> <work-item-tracking.v4_1.models.FieldModel>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        content = self._serialize.body(field, 'FieldUpdate')
        response = self._send(http_method='PATCH',
                              location_id='f36c66c7-911d-4163-8938-d3c5d0d7f5aa',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('FieldModel', response)

    def add_group(self, group, process_id, wit_ref_name, page_id, section_id):
        """AddGroup.
        [Preview API] Adds a group to the work item form
        :param :class:`<Group> <work-item-tracking.v4_1.models.Group>` group: The group
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :param str page_id: The ID of the page to add the group to
        :param str section_id: The ID of the section to add the group to
        :rtype: :class:`<Group> <work-item-tracking.v4_1.models.Group>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        if page_id is not None:
            route_values['pageId'] = self._serialize.url('page_id', page_id, 'str')
        if section_id is not None:
            route_values['sectionId'] = self._serialize.url('section_id', section_id, 'str')
        content = self._serialize.body(group, 'Group')
        response = self._send(http_method='POST',
                              location_id='2617828b-e850-4375-a92a-04855704d4c3',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Group', response)

    def edit_group(self, group, process_id, wit_ref_name, page_id, section_id, group_id):
        """EditGroup.
        [Preview API] Updates a group in the work item form
        :param :class:`<Group> <work-item-tracking.v4_1.models.Group>` group: The updated group
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :param str page_id: The ID of the page the group is in
        :param str section_id: The ID of the section the group is in
        :param str group_id: The ID of the group
        :rtype: :class:`<Group> <work-item-tracking.v4_1.models.Group>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        if page_id is not None:
            route_values['pageId'] = self._serialize.url('page_id', page_id, 'str')
        if section_id is not None:
            route_values['sectionId'] = self._serialize.url('section_id', section_id, 'str')
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        content = self._serialize.body(group, 'Group')
        response = self._send(http_method='PATCH',
                              location_id='2617828b-e850-4375-a92a-04855704d4c3',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Group', response)

    def remove_group(self, process_id, wit_ref_name, page_id, section_id, group_id):
        """RemoveGroup.
        [Preview API] Removes a group from the work item form
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :param str page_id: The ID of the page the group is in
        :param str section_id: The ID of the section to the group is in
        :param str group_id: The ID of the group
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        if page_id is not None:
            route_values['pageId'] = self._serialize.url('page_id', page_id, 'str')
        if section_id is not None:
            route_values['sectionId'] = self._serialize.url('section_id', section_id, 'str')
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        self._send(http_method='DELETE',
                   location_id='2617828b-e850-4375-a92a-04855704d4c3',
                   version='4.1-preview.1',
                   route_values=route_values)

    def set_group_in_page(self, group, process_id, wit_ref_name, page_id, section_id, group_id, remove_from_page_id, remove_from_section_id):
        """SetGroupInPage.
        [Preview API] Moves a group to a different page and section
        :param :class:`<Group> <work-item-tracking.v4_1.models.Group>` group: The updated group
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :param str page_id: The ID of the page the group is in
        :param str section_id: The ID of the section the group is in
        :param str group_id: The ID of the group
        :param str remove_from_page_id: ID of the page to remove the group from
        :param str remove_from_section_id: ID of the section to remove the group from
        :rtype: :class:`<Group> <work-item-tracking.v4_1.models.Group>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        if page_id is not None:
            route_values['pageId'] = self._serialize.url('page_id', page_id, 'str')
        if section_id is not None:
            route_values['sectionId'] = self._serialize.url('section_id', section_id, 'str')
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        query_parameters = {}
        if remove_from_page_id is not None:
            query_parameters['removeFromPageId'] = self._serialize.query('remove_from_page_id', remove_from_page_id, 'str')
        if remove_from_section_id is not None:
            query_parameters['removeFromSectionId'] = self._serialize.query('remove_from_section_id', remove_from_section_id, 'str')
        content = self._serialize.body(group, 'Group')
        response = self._send(http_method='PUT',
                              location_id='2617828b-e850-4375-a92a-04855704d4c3',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('Group', response)

    def set_group_in_section(self, group, process_id, wit_ref_name, page_id, section_id, group_id, remove_from_section_id):
        """SetGroupInSection.
        [Preview API] Moves a group to a different section
        :param :class:`<Group> <work-item-tracking.v4_1.models.Group>` group: The updated group
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :param str page_id: The ID of the page the group is in
        :param str section_id: The ID of the section the group is in
        :param str group_id: The ID of the group
        :param str remove_from_section_id: ID of the section to remove the group from
        :rtype: :class:`<Group> <work-item-tracking.v4_1.models.Group>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        if page_id is not None:
            route_values['pageId'] = self._serialize.url('page_id', page_id, 'str')
        if section_id is not None:
            route_values['sectionId'] = self._serialize.url('section_id', section_id, 'str')
        if group_id is not None:
            route_values['groupId'] = self._serialize.url('group_id', group_id, 'str')
        query_parameters = {}
        if remove_from_section_id is not None:
            query_parameters['removeFromSectionId'] = self._serialize.query('remove_from_section_id', remove_from_section_id, 'str')
        content = self._serialize.body(group, 'Group')
        response = self._send(http_method='PUT',
                              location_id='2617828b-e850-4375-a92a-04855704d4c3',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters,
                              content=content)
        return self._deserialize('Group', response)

    def get_form_layout(self, process_id, wit_ref_name):
        """GetFormLayout.
        [Preview API] Gets the form layout
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :rtype: :class:`<FormLayout> <work-item-tracking.v4_1.models.FormLayout>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        response = self._send(http_method='GET',
                              location_id='3eacc80a-ddca-4404-857a-6331aac99063',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('FormLayout', response)

    def get_lists_metadata(self):
        """GetListsMetadata.
        [Preview API] Returns meta data of the picklist.
        :rtype: [PickListMetadataModel]
        """
        response = self._send(http_method='GET',
                              location_id='b45cc931-98e3-44a1-b1cd-2e8e9c6dc1c6',
                              version='4.1-preview.1')
        return self._deserialize('[PickListMetadataModel]', self._unwrap_collection(response))

    def create_list(self, picklist):
        """CreateList.
        [Preview API] Creates a picklist.
        :param :class:`<PickListModel> <work-item-tracking.v4_1.models.PickListModel>` picklist:
        :rtype: :class:`<PickListModel> <work-item-tracking.v4_1.models.PickListModel>`
        """
        content = self._serialize.body(picklist, 'PickListModel')
        response = self._send(http_method='POST',
                              location_id='0b6179e2-23ce-46b2-b094-2ffa5ee70286',
                              version='4.1-preview.1',
                              content=content)
        return self._deserialize('PickListModel', response)

    def delete_list(self, list_id):
        """DeleteList.
        [Preview API] Removes a picklist.
        :param str list_id: The ID of the list
        """
        route_values = {}
        if list_id is not None:
            route_values['listId'] = self._serialize.url('list_id', list_id, 'str')
        self._send(http_method='DELETE',
                   location_id='0b6179e2-23ce-46b2-b094-2ffa5ee70286',
                   version='4.1-preview.1',
                   route_values=route_values)

    def get_list(self, list_id):
        """GetList.
        [Preview API] Returns a picklist.
        :param str list_id: The ID of the list
        :rtype: :class:`<PickListModel> <work-item-tracking.v4_1.models.PickListModel>`
        """
        route_values = {}
        if list_id is not None:
            route_values['listId'] = self._serialize.url('list_id', list_id, 'str')
        response = self._send(http_method='GET',
                              location_id='0b6179e2-23ce-46b2-b094-2ffa5ee70286',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('PickListModel', response)

    def update_list(self, picklist, list_id):
        """UpdateList.
        [Preview API] Updates a list.
        :param :class:`<PickListModel> <work-item-tracking.v4_1.models.PickListModel>` picklist:
        :param str list_id: The ID of the list
        :rtype: :class:`<PickListModel> <work-item-tracking.v4_1.models.PickListModel>`
        """
        route_values = {}
        if list_id is not None:
            route_values['listId'] = self._serialize.url('list_id', list_id, 'str')
        content = self._serialize.body(picklist, 'PickListModel')
        response = self._send(http_method='PUT',
                              location_id='0b6179e2-23ce-46b2-b094-2ffa5ee70286',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('PickListModel', response)

    def add_page(self, page, process_id, wit_ref_name):
        """AddPage.
        [Preview API] Adds a page to the work item form
        :param :class:`<Page> <work-item-tracking.v4_1.models.Page>` page: The page
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :rtype: :class:`<Page> <work-item-tracking.v4_1.models.Page>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        content = self._serialize.body(page, 'Page')
        response = self._send(http_method='POST',
                              location_id='1b4ac126-59b2-4f37-b4df-0a48ba807edb',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Page', response)

    def edit_page(self, page, process_id, wit_ref_name):
        """EditPage.
        [Preview API] Updates a page on the work item form
        :param :class:`<Page> <work-item-tracking.v4_1.models.Page>` page: The page
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :rtype: :class:`<Page> <work-item-tracking.v4_1.models.Page>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        content = self._serialize.body(page, 'Page')
        response = self._send(http_method='PATCH',
                              location_id='1b4ac126-59b2-4f37-b4df-0a48ba807edb',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('Page', response)

    def remove_page(self, process_id, wit_ref_name, page_id):
        """RemovePage.
        [Preview API] Removes a page from the work item form
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :param str page_id: The ID of the page
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        if page_id is not None:
            route_values['pageId'] = self._serialize.url('page_id', page_id, 'str')
        self._send(http_method='DELETE',
                   location_id='1b4ac126-59b2-4f37-b4df-0a48ba807edb',
                   version='4.1-preview.1',
                   route_values=route_values)

    def create_state_definition(self, state_model, process_id, wit_ref_name):
        """CreateStateDefinition.
        [Preview API] Creates a state definition in the work item type of the process.
        :param :class:`<WorkItemStateInputModel> <work-item-tracking.v4_1.models.WorkItemStateInputModel>` state_model:
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :rtype: :class:`<WorkItemStateResultModel> <work-item-tracking.v4_1.models.WorkItemStateResultModel>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        content = self._serialize.body(state_model, 'WorkItemStateInputModel')
        response = self._send(http_method='POST',
                              location_id='4303625d-08f4-4461-b14b-32c65bba5599',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('WorkItemStateResultModel', response)

    def delete_state_definition(self, process_id, wit_ref_name, state_id):
        """DeleteStateDefinition.
        [Preview API] Removes a state definition in the work item type of the process.
        :param str process_id: ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :param str state_id: ID of the state
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        if state_id is not None:
            route_values['stateId'] = self._serialize.url('state_id', state_id, 'str')
        self._send(http_method='DELETE',
                   location_id='4303625d-08f4-4461-b14b-32c65bba5599',
                   version='4.1-preview.1',
                   route_values=route_values)

    def get_state_definition(self, process_id, wit_ref_name, state_id):
        """GetStateDefinition.
        [Preview API] Returns a state definition in the work item type of the process.
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :param str state_id: The ID of the state
        :rtype: :class:`<WorkItemStateResultModel> <work-item-tracking.v4_1.models.WorkItemStateResultModel>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        if state_id is not None:
            route_values['stateId'] = self._serialize.url('state_id', state_id, 'str')
        response = self._send(http_method='GET',
                              location_id='4303625d-08f4-4461-b14b-32c65bba5599',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('WorkItemStateResultModel', response)

    def get_state_definitions(self, process_id, wit_ref_name):
        """GetStateDefinitions.
        [Preview API] Returns a list of all state definitions in the work item type of the process.
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :rtype: [WorkItemStateResultModel]
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        response = self._send(http_method='GET',
                              location_id='4303625d-08f4-4461-b14b-32c65bba5599',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('[WorkItemStateResultModel]', self._unwrap_collection(response))

    def hide_state_definition(self, hide_state_model, process_id, wit_ref_name, state_id):
        """HideStateDefinition.
        [Preview API] Hides a state definition in the work item type of the process.
        :param :class:`<HideStateModel> <work-item-tracking.v4_1.models.HideStateModel>` hide_state_model:
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :param str state_id: The ID of the state
        :rtype: :class:`<WorkItemStateResultModel> <work-item-tracking.v4_1.models.WorkItemStateResultModel>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        if state_id is not None:
            route_values['stateId'] = self._serialize.url('state_id', state_id, 'str')
        content = self._serialize.body(hide_state_model, 'HideStateModel')
        response = self._send(http_method='PUT',
                              location_id='4303625d-08f4-4461-b14b-32c65bba5599',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('WorkItemStateResultModel', response)

    def update_state_definition(self, state_model, process_id, wit_ref_name, state_id):
        """UpdateStateDefinition.
        [Preview API] Updates a given state definition in the work item type of the process.
        :param :class:`<WorkItemStateInputModel> <work-item-tracking.v4_1.models.WorkItemStateInputModel>` state_model:
        :param str process_id: ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :param str state_id: ID of the state
        :rtype: :class:`<WorkItemStateResultModel> <work-item-tracking.v4_1.models.WorkItemStateResultModel>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        if state_id is not None:
            route_values['stateId'] = self._serialize.url('state_id', state_id, 'str')
        content = self._serialize.body(state_model, 'WorkItemStateInputModel')
        response = self._send(http_method='PATCH',
                              location_id='4303625d-08f4-4461-b14b-32c65bba5599',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('WorkItemStateResultModel', response)

    def add_behavior_to_work_item_type(self, behavior, process_id, wit_ref_name_for_behaviors):
        """AddBehaviorToWorkItemType.
        [Preview API] Adds a behavior to the work item type of the process.
        :param :class:`<WorkItemTypeBehavior> <work-item-tracking.v4_1.models.WorkItemTypeBehavior>` behavior:
        :param str process_id: The ID of the process
        :param str wit_ref_name_for_behaviors: Work item type reference name for the behavior
        :rtype: :class:`<WorkItemTypeBehavior> <work-item-tracking.v4_1.models.WorkItemTypeBehavior>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name_for_behaviors is not None:
            route_values['witRefNameForBehaviors'] = self._serialize.url('wit_ref_name_for_behaviors', wit_ref_name_for_behaviors, 'str')
        content = self._serialize.body(behavior, 'WorkItemTypeBehavior')
        response = self._send(http_method='POST',
                              location_id='921dfb88-ef57-4c69-94e5-dd7da2d7031d',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('WorkItemTypeBehavior', response)

    def get_behavior_for_work_item_type(self, process_id, wit_ref_name_for_behaviors, behavior_ref_name):
        """GetBehaviorForWorkItemType.
        [Preview API] Returns a behavior for the work item type of the process.
        :param str process_id: The ID of the process
        :param str wit_ref_name_for_behaviors: Work item type reference name for the behavior
        :param str behavior_ref_name: The reference name of the behavior
        :rtype: :class:`<WorkItemTypeBehavior> <work-item-tracking.v4_1.models.WorkItemTypeBehavior>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name_for_behaviors is not None:
            route_values['witRefNameForBehaviors'] = self._serialize.url('wit_ref_name_for_behaviors', wit_ref_name_for_behaviors, 'str')
        if behavior_ref_name is not None:
            route_values['behaviorRefName'] = self._serialize.url('behavior_ref_name', behavior_ref_name, 'str')
        response = self._send(http_method='GET',
                              location_id='921dfb88-ef57-4c69-94e5-dd7da2d7031d',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('WorkItemTypeBehavior', response)

    def get_behaviors_for_work_item_type(self, process_id, wit_ref_name_for_behaviors):
        """GetBehaviorsForWorkItemType.
        [Preview API] Returns a list of all behaviors for the work item type of the process.
        :param str process_id: The ID of the process
        :param str wit_ref_name_for_behaviors: Work item type reference name for the behavior
        :rtype: [WorkItemTypeBehavior]
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name_for_behaviors is not None:
            route_values['witRefNameForBehaviors'] = self._serialize.url('wit_ref_name_for_behaviors', wit_ref_name_for_behaviors, 'str')
        response = self._send(http_method='GET',
                              location_id='921dfb88-ef57-4c69-94e5-dd7da2d7031d',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('[WorkItemTypeBehavior]', self._unwrap_collection(response))

    def remove_behavior_from_work_item_type(self, process_id, wit_ref_name_for_behaviors, behavior_ref_name):
        """RemoveBehaviorFromWorkItemType.
        [Preview API] Removes a behavior for the work item type of the process.
        :param str process_id: The ID of the process
        :param str wit_ref_name_for_behaviors: Work item type reference name for the behavior
        :param str behavior_ref_name: The reference name of the behavior
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name_for_behaviors is not None:
            route_values['witRefNameForBehaviors'] = self._serialize.url('wit_ref_name_for_behaviors', wit_ref_name_for_behaviors, 'str')
        if behavior_ref_name is not None:
            route_values['behaviorRefName'] = self._serialize.url('behavior_ref_name', behavior_ref_name, 'str')
        self._send(http_method='DELETE',
                   location_id='921dfb88-ef57-4c69-94e5-dd7da2d7031d',
                   version='4.1-preview.1',
                   route_values=route_values)

    def update_behavior_to_work_item_type(self, behavior, process_id, wit_ref_name_for_behaviors):
        """UpdateBehaviorToWorkItemType.
        [Preview API] Updates a behavior for the work item type of the process.
        :param :class:`<WorkItemTypeBehavior> <work-item-tracking.v4_1.models.WorkItemTypeBehavior>` behavior:
        :param str process_id: The ID of the process
        :param str wit_ref_name_for_behaviors: Work item type reference name for the behavior
        :rtype: :class:`<WorkItemTypeBehavior> <work-item-tracking.v4_1.models.WorkItemTypeBehavior>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name_for_behaviors is not None:
            route_values['witRefNameForBehaviors'] = self._serialize.url('wit_ref_name_for_behaviors', wit_ref_name_for_behaviors, 'str')
        content = self._serialize.body(behavior, 'WorkItemTypeBehavior')
        response = self._send(http_method='PATCH',
                              location_id='921dfb88-ef57-4c69-94e5-dd7da2d7031d',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('WorkItemTypeBehavior', response)

    def create_work_item_type(self, work_item_type, process_id):
        """CreateWorkItemType.
        [Preview API] Creates a work item type in the process.
        :param :class:`<WorkItemTypeModel> <work-item-tracking.v4_1.models.WorkItemTypeModel>` work_item_type:
        :param str process_id: The ID of the process
        :rtype: :class:`<WorkItemTypeModel> <work-item-tracking.v4_1.models.WorkItemTypeModel>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        content = self._serialize.body(work_item_type, 'WorkItemTypeModel')
        response = self._send(http_method='POST',
                              location_id='1ce0acad-4638-49c3-969c-04aa65ba6bea',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('WorkItemTypeModel', response)

    def delete_work_item_type(self, process_id, wit_ref_name):
        """DeleteWorkItemType.
        [Preview API] Removes a work itewm type in the process.
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        self._send(http_method='DELETE',
                   location_id='1ce0acad-4638-49c3-969c-04aa65ba6bea',
                   version='4.1-preview.1',
                   route_values=route_values)

    def get_work_item_type(self, process_id, wit_ref_name, expand=None):
        """GetWorkItemType.
        [Preview API] Returns a work item type of the process.
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :param str expand:
        :rtype: :class:`<WorkItemTypeModel> <work-item-tracking.v4_1.models.WorkItemTypeModel>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        query_parameters = {}
        if expand is not None:
            query_parameters['$expand'] = self._serialize.query('expand', expand, 'str')
        response = self._send(http_method='GET',
                              location_id='1ce0acad-4638-49c3-969c-04aa65ba6bea',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('WorkItemTypeModel', response)

    def get_work_item_types(self, process_id, expand=None):
        """GetWorkItemTypes.
        [Preview API] Returns a list of all work item types in the process.
        :param str process_id: The ID of the process
        :param str expand:
        :rtype: [WorkItemTypeModel]
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        query_parameters = {}
        if expand is not None:
            query_parameters['$expand'] = self._serialize.query('expand', expand, 'str')
        response = self._send(http_method='GET',
                              location_id='1ce0acad-4638-49c3-969c-04aa65ba6bea',
                              version='4.1-preview.1',
                              route_values=route_values,
                              query_parameters=query_parameters)
        return self._deserialize('[WorkItemTypeModel]', self._unwrap_collection(response))

    def update_work_item_type(self, work_item_type_update, process_id, wit_ref_name):
        """UpdateWorkItemType.
        [Preview API] Updates a work item type of the process.
        :param :class:`<WorkItemTypeUpdateModel> <work-item-tracking.v4_1.models.WorkItemTypeUpdateModel>` work_item_type_update:
        :param str process_id: The ID of the process
        :param str wit_ref_name: The reference name of the work item type
        :rtype: :class:`<WorkItemTypeModel> <work-item-tracking.v4_1.models.WorkItemTypeModel>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name is not None:
            route_values['witRefName'] = self._serialize.url('wit_ref_name', wit_ref_name, 'str')
        content = self._serialize.body(work_item_type_update, 'WorkItemTypeUpdateModel')
        response = self._send(http_method='PATCH',
                              location_id='1ce0acad-4638-49c3-969c-04aa65ba6bea',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('WorkItemTypeModel', response)

    def add_field_to_work_item_type(self, field, process_id, wit_ref_name_for_fields):
        """AddFieldToWorkItemType.
        [Preview API] Adds a field to the work item type in the process.
        :param :class:`<WorkItemTypeFieldModel> <work-item-tracking.v4_1.models.WorkItemTypeFieldModel>` field:
        :param str process_id: The ID of the process
        :param str wit_ref_name_for_fields: Work item type reference name for the field
        :rtype: :class:`<WorkItemTypeFieldModel> <work-item-tracking.v4_1.models.WorkItemTypeFieldModel>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name_for_fields is not None:
            route_values['witRefNameForFields'] = self._serialize.url('wit_ref_name_for_fields', wit_ref_name_for_fields, 'str')
        content = self._serialize.body(field, 'WorkItemTypeFieldModel')
        response = self._send(http_method='POST',
                              location_id='976713b4-a62e-499e-94dc-eeb869ea9126',
                              version='4.1-preview.1',
                              route_values=route_values,
                              content=content)
        return self._deserialize('WorkItemTypeFieldModel', response)

    def get_work_item_type_field(self, process_id, wit_ref_name_for_fields, field_ref_name):
        """GetWorkItemTypeField.
        [Preview API] Returns a single field in the work item type of the process.
        :param str process_id: The ID of the process
        :param str wit_ref_name_for_fields: Work item type reference name for fields
        :param str field_ref_name: The reference name of the field
        :rtype: :class:`<WorkItemTypeFieldModel> <work-item-tracking.v4_1.models.WorkItemTypeFieldModel>`
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name_for_fields is not None:
            route_values['witRefNameForFields'] = self._serialize.url('wit_ref_name_for_fields', wit_ref_name_for_fields, 'str')
        if field_ref_name is not None:
            route_values['fieldRefName'] = self._serialize.url('field_ref_name', field_ref_name, 'str')
        response = self._send(http_method='GET',
                              location_id='976713b4-a62e-499e-94dc-eeb869ea9126',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('WorkItemTypeFieldModel', response)

    def get_work_item_type_fields(self, process_id, wit_ref_name_for_fields):
        """GetWorkItemTypeFields.
        [Preview API] Returns a list of all fields in the work item type of the process.
        :param str process_id: The ID of the process
        :param str wit_ref_name_for_fields: Work item type reference name for fields
        :rtype: [WorkItemTypeFieldModel]
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name_for_fields is not None:
            route_values['witRefNameForFields'] = self._serialize.url('wit_ref_name_for_fields', wit_ref_name_for_fields, 'str')
        response = self._send(http_method='GET',
                              location_id='976713b4-a62e-499e-94dc-eeb869ea9126',
                              version='4.1-preview.1',
                              route_values=route_values)
        return self._deserialize('[WorkItemTypeFieldModel]', self._unwrap_collection(response))

    def remove_field_from_work_item_type(self, process_id, wit_ref_name_for_fields, field_ref_name):
        """RemoveFieldFromWorkItemType.
        [Preview API] Removes a field in the work item type of the process.
        :param str process_id: The ID of the process
        :param str wit_ref_name_for_fields: Work item type reference name for fields
        :param str field_ref_name: The reference name of the field
        """
        route_values = {}
        if process_id is not None:
            route_values['processId'] = self._serialize.url('process_id', process_id, 'str')
        if wit_ref_name_for_fields is not None:
            route_values['witRefNameForFields'] = self._serialize.url('wit_ref_name_for_fields', wit_ref_name_for_fields, 'str')
        if field_ref_name is not None:
            route_values['fieldRefName'] = self._serialize.url('field_ref_name', field_ref_name, 'str')
        self._send(http_method='DELETE',
                   location_id='976713b4-a62e-499e-94dc-eeb869ea9126',
                   version='4.1-preview.1',
                   route_values=route_values)

