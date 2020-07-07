# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Page(Model):
    """Page.

    :param contribution: Contribution for the page.
    :type contribution: :class:`WitContribution <work-item-tracking.v4_0.models.WitContribution>`
    :param id: The id for the layout node.
    :type id: str
    :param inherited: A value indicating whether this layout node has been inherited from a parent layout.  This is expected to only be only set by the combiner.
    :type inherited: bool
    :param is_contribution: A value indicating if the layout node is contribution are not.
    :type is_contribution: bool
    :param label: The label for the page.
    :type label: str
    :param locked: A value indicating whether any user operations are permitted on this page and the contents of this page
    :type locked: bool
    :param order: Order in which the page should appear in the layout.
    :type order: int
    :param overridden: A value indicating whether this layout node has been overridden by a child layout.
    :type overridden: bool
    :param page_type: The icon for the page.
    :type page_type: object
    :param sections: The sections of the page.
    :type sections: list of :class:`Section <work-item-tracking.v4_0.models.Section>`
    :param visible: A value indicating if the page should be hidden or not.
    :type visible: bool
    """

    _attribute_map = {
        'contribution': {'key': 'contribution', 'type': 'WitContribution'},
        'id': {'key': 'id', 'type': 'str'},
        'inherited': {'key': 'inherited', 'type': 'bool'},
        'is_contribution': {'key': 'isContribution', 'type': 'bool'},
        'label': {'key': 'label', 'type': 'str'},
        'locked': {'key': 'locked', 'type': 'bool'},
        'order': {'key': 'order', 'type': 'int'},
        'overridden': {'key': 'overridden', 'type': 'bool'},
        'page_type': {'key': 'pageType', 'type': 'object'},
        'sections': {'key': 'sections', 'type': '[Section]'},
        'visible': {'key': 'visible', 'type': 'bool'}
    }

    def __init__(self, contribution=None, id=None, inherited=None, is_contribution=None, label=None, locked=None, order=None, overridden=None, page_type=None, sections=None, visible=None):
        super(Page, self).__init__()
        self.contribution = contribution
        self.id = id
        self.inherited = inherited
        self.is_contribution = is_contribution
        self.label = label
        self.locked = locked
        self.order = order
        self.overridden = overridden
        self.page_type = page_type
        self.sections = sections
        self.visible = visible
