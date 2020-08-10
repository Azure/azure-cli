# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExtensionDraft(Model):
    """ExtensionDraft.

    :param assets:
    :type assets: list of :class:`ExtensionDraftAsset <gallery.v4_1.models.ExtensionDraftAsset>`
    :param created_date:
    :type created_date: datetime
    :param draft_state:
    :type draft_state: object
    :param extension_name:
    :type extension_name: str
    :param id:
    :type id: str
    :param last_updated:
    :type last_updated: datetime
    :param payload:
    :type payload: :class:`ExtensionPayload <gallery.v4_1.models.ExtensionPayload>`
    :param product:
    :type product: str
    :param publisher_name:
    :type publisher_name: str
    :param validation_errors:
    :type validation_errors: list of { key: str; value: str }
    :param validation_warnings:
    :type validation_warnings: list of { key: str; value: str }
    """

    _attribute_map = {
        'assets': {'key': 'assets', 'type': '[ExtensionDraftAsset]'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'draft_state': {'key': 'draftState', 'type': 'object'},
        'extension_name': {'key': 'extensionName', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'last_updated': {'key': 'lastUpdated', 'type': 'iso-8601'},
        'payload': {'key': 'payload', 'type': 'ExtensionPayload'},
        'product': {'key': 'product', 'type': 'str'},
        'publisher_name': {'key': 'publisherName', 'type': 'str'},
        'validation_errors': {'key': 'validationErrors', 'type': '[{ key: str; value: str }]'},
        'validation_warnings': {'key': 'validationWarnings', 'type': '[{ key: str; value: str }]'}
    }

    def __init__(self, assets=None, created_date=None, draft_state=None, extension_name=None, id=None, last_updated=None, payload=None, product=None, publisher_name=None, validation_errors=None, validation_warnings=None):
        super(ExtensionDraft, self).__init__()
        self.assets = assets
        self.created_date = created_date
        self.draft_state = draft_state
        self.extension_name = extension_name
        self.id = id
        self.last_updated = last_updated
        self.payload = payload
        self.product = product
        self.publisher_name = publisher_name
        self.validation_errors = validation_errors
        self.validation_warnings = validation_warnings
