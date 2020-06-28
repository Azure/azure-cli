# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestRunBasic(Model):
    """TestRunBasic.

    :param created_by:
    :type created_by: IdentityRef
    :param created_date:
    :type created_date: datetime
    :param deleted_by:
    :type deleted_by: IdentityRef
    :param deleted_date:
    :type deleted_date: datetime
    :param finished_date:
    :type finished_date: datetime
    :param id:
    :type id: str
    :param load_generation_geo_locations:
    :type load_generation_geo_locations: list of :class:`LoadGenerationGeoLocation <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.LoadGenerationGeoLocation>`
    :param load_test_file_name:
    :type load_test_file_name: str
    :param name:
    :type name: str
    :param run_number:
    :type run_number: int
    :param run_source:
    :type run_source: str
    :param run_specific_details:
    :type run_specific_details: :class:`LoadTestRunDetails <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.LoadTestRunDetails>`
    :param run_type:
    :type run_type: object
    :param state:
    :type state: object
    :param url:
    :type url: str
    """

    _attribute_map = {
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'deleted_by': {'key': 'deletedBy', 'type': 'IdentityRef'},
        'deleted_date': {'key': 'deletedDate', 'type': 'iso-8601'},
        'finished_date': {'key': 'finishedDate', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'str'},
        'load_generation_geo_locations': {'key': 'loadGenerationGeoLocations', 'type': '[LoadGenerationGeoLocation]'},
        'load_test_file_name': {'key': 'loadTestFileName', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'run_number': {'key': 'runNumber', 'type': 'int'},
        'run_source': {'key': 'runSource', 'type': 'str'},
        'run_specific_details': {'key': 'runSpecificDetails', 'type': 'LoadTestRunDetails'},
        'run_type': {'key': 'runType', 'type': 'object'},
        'state': {'key': 'state', 'type': 'object'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, created_by=None, created_date=None, deleted_by=None, deleted_date=None, finished_date=None, id=None, load_generation_geo_locations=None, load_test_file_name=None, name=None, run_number=None, run_source=None, run_specific_details=None, run_type=None, state=None, url=None):
        super(TestRunBasic, self).__init__()
        self.created_by = created_by
        self.created_date = created_date
        self.deleted_by = deleted_by
        self.deleted_date = deleted_date
        self.finished_date = finished_date
        self.id = id
        self.load_generation_geo_locations = load_generation_geo_locations
        self.load_test_file_name = load_test_file_name
        self.name = name
        self.run_number = run_number
        self.run_source = run_source
        self.run_specific_details = run_specific_details
        self.run_type = run_type
        self.state = state
        self.url = url
