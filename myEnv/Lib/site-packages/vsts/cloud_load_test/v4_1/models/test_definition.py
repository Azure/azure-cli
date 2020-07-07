# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .test_definition_basic import TestDefinitionBasic


class TestDefinition(TestDefinitionBasic):
    """TestDefinition.

    :param access_data:
    :type access_data: :class:`DropAccessData <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.DropAccessData>`
    :param created_by:
    :type created_by: IdentityRef
    :param created_date:
    :type created_date: datetime
    :param id:
    :type id: str
    :param last_modified_by:
    :type last_modified_by: IdentityRef
    :param last_modified_date:
    :type last_modified_date: datetime
    :param load_test_type:
    :type load_test_type: object
    :param name:
    :type name: str
    :param description:
    :type description: str
    :param load_generation_geo_locations:
    :type load_generation_geo_locations: list of :class:`LoadGenerationGeoLocation <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.LoadGenerationGeoLocation>`
    :param load_test_definition_source:
    :type load_test_definition_source: str
    :param run_settings:
    :type run_settings: :class:`LoadTestRunSettings <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.LoadTestRunSettings>`
    :param static_agent_run_settings:
    :type static_agent_run_settings: :class:`StaticAgentRunSetting <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.StaticAgentRunSetting>`
    :param test_details:
    :type test_details: :class:`LoadTest <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.LoadTest>`
    """

    _attribute_map = {
        'access_data': {'key': 'accessData', 'type': 'DropAccessData'},
        'created_by': {'key': 'createdBy', 'type': 'IdentityRef'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'str'},
        'last_modified_by': {'key': 'lastModifiedBy', 'type': 'IdentityRef'},
        'last_modified_date': {'key': 'lastModifiedDate', 'type': 'iso-8601'},
        'load_test_type': {'key': 'loadTestType', 'type': 'object'},
        'name': {'key': 'name', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'load_generation_geo_locations': {'key': 'loadGenerationGeoLocations', 'type': '[LoadGenerationGeoLocation]'},
        'load_test_definition_source': {'key': 'loadTestDefinitionSource', 'type': 'str'},
        'run_settings': {'key': 'runSettings', 'type': 'LoadTestRunSettings'},
        'static_agent_run_settings': {'key': 'staticAgentRunSettings', 'type': 'StaticAgentRunSetting'},
        'test_details': {'key': 'testDetails', 'type': 'LoadTest'}
    }

    def __init__(self, access_data=None, created_by=None, created_date=None, id=None, last_modified_by=None, last_modified_date=None, load_test_type=None, name=None, description=None, load_generation_geo_locations=None, load_test_definition_source=None, run_settings=None, static_agent_run_settings=None, test_details=None):
        super(TestDefinition, self).__init__(access_data=access_data, created_by=created_by, created_date=created_date, id=id, last_modified_by=last_modified_by, last_modified_date=last_modified_date, load_test_type=load_test_type, name=name)
        self.description = description
        self.load_generation_geo_locations = load_generation_geo_locations
        self.load_test_definition_source = load_test_definition_source
        self.run_settings = run_settings
        self.static_agent_run_settings = static_agent_run_settings
        self.test_details = test_details
