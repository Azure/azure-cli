# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .scenario_tests import live_only, record_only, get_sha1_hash

from .base import ScenarioTest, LiveScenarioTest, LocalContextScenarioTest
from .preparers import (StorageAccountPreparer, ResourceGroupPreparer, RoleBasedServicePrincipalPreparer,
                        KeyVaultPreparer, ManagedHSMPreparer, ManagedApplicationPreparer, VirtualNetworkPreparer,
                        VnetNicPreparer, LogAnalyticsWorkspacePreparer)
from .exceptions import CliTestError
from .checkers import (JMESPathCheck, JMESPathCheckExists, JMESPathCheckGreaterThan, NoneCheck, StringCheck,
                       StringContainCheck)
from .decorators import api_version_constraint
from .utilities import create_random_name, MSGraphUserReplacer
from .patches import MOCKED_USER_NAME

__all__ = ['ScenarioTest', 'LiveScenarioTest', 'ResourceGroupPreparer', 'StorageAccountPreparer',
           'RoleBasedServicePrincipalPreparer', 'KeyVaultPreparer', 'ManagedHSMPreparer',
           'ManagedApplicationPreparer', 'CliTestError', 'JMESPathCheck',
           'JMESPathCheckExists', 'NoneCheck', 'live_only', 'record_only', 'StringCheck', 'StringContainCheck',
           'get_sha1_hash', 'KeyVaultPreparer', 'JMESPathCheckGreaterThan', 'api_version_constraint',
           'create_random_name', 'MOCKED_USER_NAME', 'MSGraphUserReplacer', 'LocalContextScenarioTest',
           'VirtualNetworkPreparer', 'VnetNicPreparer', 'LogAnalyticsWorkspacePreparer']


__version__ = '0.1.0'
