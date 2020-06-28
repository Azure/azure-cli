# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .test_run_basic import TestRunBasic


class TestRun(TestRunBasic):
    """TestRun.

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
    :param abort_message:
    :type abort_message: :class:`TestRunAbortMessage <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.TestRunAbortMessage>`
    :param aut_initialization_error:
    :type aut_initialization_error: bool
    :param chargeable:
    :type chargeable: bool
    :param charged_vUserminutes:
    :type charged_vUserminutes: int
    :param description:
    :type description: str
    :param execution_finished_date:
    :type execution_finished_date: datetime
    :param execution_started_date:
    :type execution_started_date: datetime
    :param queued_date:
    :type queued_date: datetime
    :param retention_state:
    :type retention_state: object
    :param run_source_identifier:
    :type run_source_identifier: str
    :param run_source_url:
    :type run_source_url: str
    :param started_by:
    :type started_by: IdentityRef
    :param started_date:
    :type started_date: datetime
    :param stopped_by:
    :type stopped_by: IdentityRef
    :param sub_state:
    :type sub_state: object
    :param supersede_run_settings:
    :type supersede_run_settings: :class:`OverridableRunSettings <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.OverridableRunSettings>`
    :param test_drop:
    :type test_drop: :class:`TestDropRef <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.TestDropRef>`
    :param test_settings:
    :type test_settings: :class:`TestSettings <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.TestSettings>`
    :param warm_up_started_date:
    :type warm_up_started_date: datetime
    :param web_result_url:
    :type web_result_url: str
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
        'url': {'key': 'url', 'type': 'str'},
        'abort_message': {'key': 'abortMessage', 'type': 'TestRunAbortMessage'},
        'aut_initialization_error': {'key': 'autInitializationError', 'type': 'bool'},
        'chargeable': {'key': 'chargeable', 'type': 'bool'},
        'charged_vUserminutes': {'key': 'chargedVUserminutes', 'type': 'int'},
        'description': {'key': 'description', 'type': 'str'},
        'execution_finished_date': {'key': 'executionFinishedDate', 'type': 'iso-8601'},
        'execution_started_date': {'key': 'executionStartedDate', 'type': 'iso-8601'},
        'queued_date': {'key': 'queuedDate', 'type': 'iso-8601'},
        'retention_state': {'key': 'retentionState', 'type': 'object'},
        'run_source_identifier': {'key': 'runSourceIdentifier', 'type': 'str'},
        'run_source_url': {'key': 'runSourceUrl', 'type': 'str'},
        'started_by': {'key': 'startedBy', 'type': 'IdentityRef'},
        'started_date': {'key': 'startedDate', 'type': 'iso-8601'},
        'stopped_by': {'key': 'stoppedBy', 'type': 'IdentityRef'},
        'sub_state': {'key': 'subState', 'type': 'object'},
        'supersede_run_settings': {'key': 'supersedeRunSettings', 'type': 'OverridableRunSettings'},
        'test_drop': {'key': 'testDrop', 'type': 'TestDropRef'},
        'test_settings': {'key': 'testSettings', 'type': 'TestSettings'},
        'warm_up_started_date': {'key': 'warmUpStartedDate', 'type': 'iso-8601'},
        'web_result_url': {'key': 'webResultUrl', 'type': 'str'}
    }

    def __init__(self, created_by=None, created_date=None, deleted_by=None, deleted_date=None, finished_date=None, id=None, load_generation_geo_locations=None, load_test_file_name=None, name=None, run_number=None, run_source=None, run_specific_details=None, run_type=None, state=None, url=None, abort_message=None, aut_initialization_error=None, chargeable=None, charged_vUserminutes=None, description=None, execution_finished_date=None, execution_started_date=None, queued_date=None, retention_state=None, run_source_identifier=None, run_source_url=None, started_by=None, started_date=None, stopped_by=None, sub_state=None, supersede_run_settings=None, test_drop=None, test_settings=None, warm_up_started_date=None, web_result_url=None):
        super(TestRun, self).__init__(created_by=created_by, created_date=created_date, deleted_by=deleted_by, deleted_date=deleted_date, finished_date=finished_date, id=id, load_generation_geo_locations=load_generation_geo_locations, load_test_file_name=load_test_file_name, name=name, run_number=run_number, run_source=run_source, run_specific_details=run_specific_details, run_type=run_type, state=state, url=url)
        self.abort_message = abort_message
        self.aut_initialization_error = aut_initialization_error
        self.chargeable = chargeable
        self.charged_vUserminutes = charged_vUserminutes
        self.description = description
        self.execution_finished_date = execution_finished_date
        self.execution_started_date = execution_started_date
        self.queued_date = queued_date
        self.retention_state = retention_state
        self.run_source_identifier = run_source_identifier
        self.run_source_url = run_source_url
        self.started_by = started_by
        self.started_date = started_date
        self.stopped_by = stopped_by
        self.sub_state = sub_state
        self.supersede_run_settings = supersede_run_settings
        self.test_drop = test_drop
        self.test_settings = test_settings
        self.warm_up_started_date = warm_up_started_date
        self.web_result_url = web_result_url
